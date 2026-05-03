"""Three-stage classification pipeline orchestrator.

Stage 1 (whitelist) → Stage 2 (algorithm) → Stage 3 (LLM, only on low conf).
HTTP I/O is concentrated here so ``signals.py`` and ``algorithm.py`` stay
pure and unit-testable.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httpx
import structlog

from ..seeds.starcasino import BrandSeed
from .algorithm import classify_algorithm
from .constants import (
    DEFAULT_HTTP_TIMEOUT_S,
    LLM_ESCALATION_THRESHOLD,
    MAX_REDIRECTS,
    REDIRECT_CONCURRENCY,
)
from .llm import classify_llm
from .page_fetcher import PageFetcher, default_page_fetcher
from .safety import host_is_safe
from .signals import extract_signals, is_affiliate_link
from .taxonomy import Category, Classification, ReasonCode, Subcategory
from .whitelist import classify_whitelist

log = structlog.get_logger()


@dataclass
class ClassifierContext:
    """Per-scan dependencies. ``page_fetcher`` defaults to the cascading
    httpx → Playwright strategy; pass a custom one for tests or to plug
    in a different backend (Browserless, ScrapingBee, …) without
    touching pipeline code."""

    brand: BrandSeed
    http_client: httpx.AsyncClient
    page_fetcher: PageFetcher = field(init=False)
    fetch_pages: bool = True  # if False, skip stage 2/3 (whitelist-only)

    def __post_init__(self) -> None:
        # Built lazily from http_client so the scan service keeps owning
        # the connection pool. Override post-construction in tests by
        # reassigning ``ctx.page_fetcher``.
        self.page_fetcher = default_page_fetcher(self.http_client)


async def _follow_redirects(client: httpx.AsyncClient, url: str) -> str:
    """Resolve a URL's final destination via HEAD, falling back to GET on 405/501.

    Many CDNs refuse HEAD on tracker paths. On any error we return the
    original URL — affiliate-link counting must survive network noise.
    """
    if not host_is_safe(url):
        log.warning("redirect_follow_blocked_unsafe_host", url=url)
        return url
    try:
        r = await client.head(
            url,
            follow_redirects=False,
            timeout=DEFAULT_HTTP_TIMEOUT_S,
        )
        # Manual redirect chain so each hop is SSRF-checked.
        hops = 0
        while r.is_redirect and hops < MAX_REDIRECTS:
            next_url = r.headers.get("location")
            if not next_url:
                break
            next_url = str(httpx.URL(r.url).join(next_url))
            if not host_is_safe(next_url):
                log.warning("redirect_chain_blocked", url=next_url)
                return str(r.url)
            r = await client.head(next_url, follow_redirects=False, timeout=DEFAULT_HTTP_TIMEOUT_S)
            hops += 1
        if r.status_code in (405, 501):
            r = await client.get(str(r.url), follow_redirects=False, timeout=DEFAULT_HTTP_TIMEOUT_S)
        return str(r.url)
    except httpx.HTTPError as e:
        log.warning("redirect_follow_error", url=url, error=str(e))
        return url


async def _resolve_destinations(
    affiliate_links: list[str], client: httpx.AsyncClient
) -> list[str]:
    sem = asyncio.Semaphore(REDIRECT_CONCURRENCY)

    async def _one(link: str) -> str | None:
        if not is_affiliate_link(link):
            return None
        async with sem:
            return await _follow_redirects(client, link)

    # return_exceptions=True so a single bad URL never aborts the pipeline.
    results = await asyncio.gather(
        *(_one(link) for link in affiliate_links), return_exceptions=True
    )
    out: list[str] = []
    for r in results:
        if isinstance(r, BaseException):
            log.warning("resolve_destination_exception", error=str(r))
            continue
        if r is not None:
            out.append(r)
    return out


def _fallback_classification(url: str, stage: int, reason: ReasonCode) -> Classification:
    return Classification(
        category=Category.INFORMATIONAL,
        subcategory=Subcategory.INFO_OTHER,
        confidence=0.30,
        stage_used=stage,
        signals={"fetch_failed": True, "url": url},
        reasoning="Page fetch failed — fallback to INFO_OTHER",
        reason_code=reason,
    )


async def classify(url: str, ctx: ClassifierContext) -> Classification:
    """Run the 3-stage pipeline for one URL. Never raises (CLAUDE.md invariant)."""
    try:
        verdict = classify_whitelist(url, ctx.brand)
        if verdict is not None:
            log.info("classified_stage1", url=url, sub=verdict.subcategory)
            return verdict

        if not ctx.fetch_pages:
            return Classification(
                category=Category.INFORMATIONAL,
                subcategory=Subcategory.INFO_OTHER,
                confidence=0.30,
                stage_used=1,
                signals={"matched": "no_whitelist", "fetch_pages": False},
                reasoning="No whitelist match and page fetching disabled",
                reason_code=ReasonCode.PIPELINE_WHITELIST_ONLY,
            )

        page = await ctx.page_fetcher.fetch(url)
        if page is None or not page.html:
            return _fallback_classification(url, stage=2, reason=ReasonCode.PIPELINE_FETCH_FAILED)

        competitor_names = [d.split(".")[0] for d in ctx.brand.known_competitors]
        signals = extract_signals(page.html, url, ctx.brand.name, competitor_names)
        destinations = await _resolve_destinations(signals.affiliate_links, ctx.http_client)
        stage2 = classify_algorithm(signals, destinations, ctx.brand)
        log.info("classified_stage2", url=url, sub=stage2.subcategory, conf=stage2.confidence)

        if stage2.confidence < LLM_ESCALATION_THRESHOLD:
            stage3 = await classify_llm(url, signals, destinations, ctx.brand, stage2)
            # Invariant: never lower confidence from a higher stage. If the
            # LLM agrees with stage 2, keep whichever confidence is higher;
            # if it disagrees, take the LLM verdict but floor at stage2.confidence
            # only when the categories match (otherwise honour the LLM as-is).
            if stage3.subcategory == stage2.subcategory and stage3.confidence < stage2.confidence:
                stage3 = Classification(
                    category=stage3.category,
                    subcategory=stage3.subcategory,
                    confidence=stage2.confidence,
                    stage_used=stage3.stage_used,
                    signals=stage3.signals,
                    reasoning=stage3.reasoning,
                    reason_code=stage3.reason_code,
                )
            log.info(
                "classified_stage3", url=url, sub=stage3.subcategory, conf=stage3.confidence
            )
            return stage3

        return stage2
    except Exception as e:  # pragma: no cover - defensive
        # CLAUDE.md: pipeline.classify never raises. Log and degrade.
        log.exception("pipeline_unhandled", url=url, error=str(e))
        return _fallback_classification(url, stage=2, reason=ReasonCode.PIPELINE_FETCH_FAILED)
