"""High-level scan orchestration: SERP fetch → classify → persist.

Dependency-injectable: callers may swap the ``SerpFetcher``, the http
client, or the per-URL classifier. Tests use this to wire deterministic
fixtures; production callers rely on the defaults.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..classifier.pipeline import ClassifierContext, classify
from ..classifier.taxonomy import Classification
from ..db.models import (
    Brand,
    DomainClassification,
    SerpResult,
    SerpSnapshot,
)
from ..seeds.starcasino import BRANDS, BrandSeed
from ..serp.fetcher import FetchOutcome, SerpFetcher
from ..serp.fetcher import SerpResult as SerpRow
from ..time import utc_now

log = structlog.get_logger()

# Each task does up to N HTTP fetches + possibly an LLM call. Keep low.
CLASSIFY_CONCURRENCY = 5


@dataclass
class ScanResult:
    snapshot_id: int
    captured_at: datetime
    keyword: str
    geo: str
    source: str
    results: list[dict]


ClassifyFn = Callable[[str], Awaitable[Classification]]
# Optional callback for live progress streaming (SSE). Called inline; must
# be cheap. The pair is (event_name, payload-dict).
ProgressCb = Callable[[str, dict], Awaitable[None]]


async def _noop_progress(_event: str, _data: dict) -> None:
    return None


async def _ensure_brand(session: AsyncSession, slug: str) -> tuple[Brand, BrandSeed]:
    """Load Brand from DB, inserting from the bundled seed on first sight.

    The returned ``BrandSeed`` is hydrated from the persisted row, so any
    runtime mutations made via the admin endpoints are visible to the
    classifier on the next scan without restart.
    """
    stmt = select(Brand).where(Brand.slug == slug)
    brand = (await session.execute(stmt)).scalar_one_or_none()
    if brand is None:
        if slug not in BRANDS:
            raise ValueError(f"Unknown brand slug '{slug}'. Known: {list(BRANDS)}")
        seed = BRANDS[slug]
        brand = Brand(
            slug=seed.slug,
            name=seed.name,
            geo=seed.geo,
            official_domains=list(seed.official_domains),
            known_partners=list(seed.known_partners),
            known_competitors=list(seed.known_competitors),
        )
        session.add(brand)
        await session.flush()
    monitored = BRANDS[slug].monitored_keywords if slug in BRANDS else ()
    return brand, BrandSeed.from_db_row(brand, monitored_keywords=monitored)


async def _persist_classification(
    session: AsyncSession, brand_id: int, domain: str, c: Classification
) -> DomainClassification:
    """Upsert via dialect-native ``INSERT … ON CONFLICT DO UPDATE``.

    Two concurrent scans hitting the same ``(brand_id, domain)`` would race
    the unique constraint without this; SQLite serializes globally so only
    Postgres feels the bug, but the upsert is correct on both.
    """
    bind = session.get_bind()
    if bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as upsert
    else:
        from sqlalchemy.dialects.sqlite import insert as upsert

    payload = {
        "brand_id": brand_id,
        "domain": domain,
        "category": c.category.value,
        "subcategory": c.subcategory.value,
        "confidence": c.confidence,
        "stage_used": c.stage_used,
        "signals": c.signals,
        "reasoning": c.reasoning,
        "reason_code": c.reason_code.value if c.reason_code else None,
        "classified_at": utc_now(),
    }
    stmt = upsert(DomainClassification).values(**payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["brand_id", "domain"],
        set_={
            k: stmt.excluded[k]
            for k in (
                "category",
                "subcategory",
                "confidence",
                "stage_used",
                "signals",
                "reasoning",
                "reason_code",
                "classified_at",
            )
        },
    ).returning(DomainClassification)

    result = await session.execute(stmt)
    return result.scalar_one()


async def _classify_all(
    rows: list[SerpRow], classify_fn: ClassifyFn, on_progress: ProgressCb
) -> list[Classification]:
    sem = asyncio.Semaphore(CLASSIFY_CONCURRENCY)
    total = len(rows)

    async def _one(idx: int, row: SerpRow) -> Classification:
        async with sem:
            await on_progress(
                "classifying",
                {"index": idx, "total": total, "domain": row.domain, "url": row.url},
            )
            verdict = await classify_fn(row.url)
            await on_progress(
                "classified",
                {
                    "index": idx,
                    "total": total,
                    "domain": row.domain,
                    "category": verdict.category.value,
                    "subcategory": verdict.subcategory.value,
                    "confidence": round(verdict.confidence, 3),
                    "stage_used": verdict.stage_used,
                },
            )
            return verdict

    return await asyncio.gather(*(_one(i, r) for i, r in enumerate(rows, start=1)))


async def run_scan(
    session: AsyncSession,
    brand_slug: str,
    keyword: str,
    geo: str = "NL",
    top_n: int = 10,
    *,
    fetcher: SerpFetcher | None = None,
    http_client: httpx.AsyncClient | None = None,
    classify_fn: ClassifyFn | None = None,
    on_progress: ProgressCb | None = None,
) -> ScanResult:
    emit = on_progress or _noop_progress
    brand, seed = await _ensure_brand(session, brand_slug)

    log.info("scan_start", brand=brand_slug, keyword=keyword, geo=geo, top_n=top_n)
    await emit(
        "scan_start",
        {"brand": brand_slug, "keyword": keyword, "geo": geo, "top_n": top_n},
    )

    fetcher = fetcher or SerpFetcher(prefer_playwright=True)
    await emit("serp_fetch_start", {"keyword": keyword, "geo": geo})
    outcome: FetchOutcome = await fetcher.fetch_with_source(keyword, geo, num=top_n + 5)
    serp_rows: list[SerpRow] = outcome.results[:top_n]
    await emit(
        "serp_fetched",
        {"source": outcome.source, "n": len(serp_rows), "rows": [r.__dict__ for r in serp_rows]},
    )

    snap = SerpSnapshot(
        brand_id=brand.id,
        keyword=keyword,
        geo=geo,
        source=outcome.source,
        raw_serp={"results": [r.__dict__ for r in serp_rows]},
    )
    session.add(snap)
    await session.flush()

    owns_client = http_client is None
    # Pose as a real Chrome on macOS — many SEO/leadgen sites (e.g.
    # starcasinoo.com) reject obvious bot UAs with 403, which makes the
    # classifier fall back to ``pipeline_fetch_failed`` for sites it could
    # otherwise inspect. Realistic Accept/Accept-Language headers help too.
    client = http_client or httpx.AsyncClient(
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
        },
        timeout=15.0,
    )
    try:
        if classify_fn is None:
            ctx = ClassifierContext(brand=seed, http_client=client)

            async def _default_classify(url: str) -> Classification:
                return await classify(url, ctx)

            classify_fn_local: ClassifyFn = _default_classify
        else:
            classify_fn_local = classify_fn

        await emit("classify_phase_start", {"total": len(serp_rows)})
        verdicts = await _classify_all(serp_rows, classify_fn_local, emit)
    finally:
        if owns_client:
            await client.aclose()

    output: list[dict] = []
    for row, verdict in zip(serp_rows, verdicts, strict=True):
        cls_row = await _persist_classification(session, brand.id, row.domain, verdict)
        session.add(
            SerpResult(
                snapshot_id=snap.id,
                position=row.position,
                url=row.url,
                domain=row.domain,
                title=row.title,
                snippet=row.snippet,
                classification_id=cls_row.id,
            )
        )
        output.append(
            {
                "position": row.position,
                "url": row.url,
                "domain": row.domain,
                "title": row.title,
                "category": verdict.category.value,
                "subcategory": verdict.subcategory.value,
                "confidence": round(verdict.confidence, 3),
                "stage_used": verdict.stage_used,
                "reasoning": verdict.reasoning,
                "reason_code": verdict.reason_code.value if verdict.reason_code else None,
            }
        )

    await session.flush()
    # Load the server-default captured_at — avoids returning a guessed
    # fallback that wouldn't match what's persisted.
    await session.refresh(snap, attribute_names=["captured_at"])
    log.info(
        "scan_done", snapshot_id=snap.id, n_results=len(output), source=outcome.source
    )
    await emit(
        "persist_done",
        {"snapshot_id": snap.id, "captured_at": snap.captured_at.isoformat()},
    )
    return ScanResult(
        snapshot_id=snap.id,
        captured_at=snap.captured_at,
        keyword=keyword,
        geo=geo,
        source=outcome.source,
        results=output,
    )
