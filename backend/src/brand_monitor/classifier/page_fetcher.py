"""Pluggable page-content fetcher used by the classifier.

Stage 2 needs the rendered HTML of a SERP-listed URL. The naive httpx
fast path works for ~80% of pages, but JS-only-rendered hijacker funnels
(e.g. star-casino.co) and Cloudflare-protected sites (e.g.
starcasino-nl.com) need a real browser. Rather than scattering ``if
playwright`` branches through the pipeline, we expose a single
``PageFetcher`` Protocol with three concrete implementations:

- :class:`HttpxPageFetcher` — fast, used by default
- :class:`PlaywrightPageFetcher` — JS-render, bypasses bot challenges
- :class:`CascadingPageFetcher` — composes both with smart fallback

The cascading fetcher is the production strategy: try fast first, fall
back to the slow path only when the response looks blocked or empty.
That keeps mean scan time low while still classifying the long-tail of
hijacker / leadgen pages correctly.

Adding a new backend (Browserless, ScrapingBee, residential-proxy
provider) is a single new class implementing the Protocol — no pipeline
changes required.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Protocol

import httpx
import structlog

from .constants import DEFAULT_HTTP_TIMEOUT_S, MAX_REDIRECTS, MAX_RESPONSE_BYTES
from .safety import host_is_safe

log = structlog.get_logger()

# Below this body length we assume the response was a bot challenge,
# error page, or hollow shell. Real content pages are several KB minimum.
MIN_USABLE_BODY_BYTES = 1500

# A real iGaming page typically has 30+ anchors (nav, footer, game tiles).
# An SPA shell that defers rendering to JS usually exposes fewer than this
# in static HTML — that's our trigger to escalate to Playwright. Tuned
# conservatively so genuinely thin static pages aren't double-fetched.
MIN_USABLE_ANCHORS = 8

# Markers that strongly suggest a JavaScript-only render: when the static
# HTML *looks* like content (passes size + status check) but actually only
# bootstraps a SPA, these tokens are almost always present.
SPA_MARKERS = (
    'id="__next"',
    "__NEXT_DATA__",
    'id="root"></div>',
    "data-reactroot",
    "ng-app=",
    "ng-version=",
    "<noscript>You need to enable JavaScript",
)

# Status codes that almost always mean "WAF rejected our request" rather
# than "page genuinely missing".
BLOCKED_STATUSES = frozenset({401, 403, 405, 429, 503})


@dataclass(frozen=True)
class FetchedPage:
    """Immutable result of a page fetch.

    Includes the source so downstream logging can tell httpx vs Playwright
    apart, and the final URL so redirect-aware code (e.g. canonicalization)
    works without re-following the chain.
    """

    url: str
    html: str
    status: int
    source: str


class PageFetcher(Protocol):
    """Interface every backend must implement. Async because real fetchers
    are I/O bound and we run them concurrently per snapshot."""

    async def fetch(self, url: str) -> FetchedPage | None:  # pragma: no cover - protocol
        ...


# --------------------------------------------------------------------- httpx


class HttpxPageFetcher:
    """Plain HTTP fetch with size cap + redirect cap.

    Reuses the caller-owned ``AsyncClient`` so headers / cookies / proxies
    configured at scan time apply uniformly.
    """

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch(self, url: str) -> FetchedPage | None:
        if not host_is_safe(url):
            log.warning("httpx_fetch_blocked_unsafe_host", url=url)
            return None
        try:
            async with self._client.stream(
                "GET", url, follow_redirects=False, timeout=DEFAULT_HTTP_TIMEOUT_S
            ) as r:
                hops = 0
                while r.is_redirect and hops < MAX_REDIRECTS:
                    next_url = r.headers.get("location")
                    if not next_url:
                        break
                    next_url = str(httpx.URL(r.url).join(next_url))
                    if not host_is_safe(next_url):
                        log.warning("httpx_redirect_blocked", url=next_url)
                        return None
                    await r.aclose()
                    r = await self._client.send(
                        self._client.build_request(
                            "GET", next_url, timeout=DEFAULT_HTTP_TIMEOUT_S
                        ),
                        stream=True,
                        follow_redirects=False,
                    )
                    hops += 1
                body = await self._read_capped(r)
                if body is None:
                    return None
                return FetchedPage(
                    url=str(r.url), html=body, status=r.status_code, source="httpx"
                )
        except httpx.RequestError as e:
            log.warning("httpx_fetch_error", url=url, error=str(e))
            return None
        except httpx.HTTPStatusError as e:
            log.warning("httpx_fetch_status_error", url=url, status=e.response.status_code)
            return None

    @staticmethod
    async def _read_capped(response: httpx.Response) -> str | None:
        chunks: list[bytes] = []
        total = 0
        async for chunk in response.aiter_bytes():
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                return None
            chunks.append(chunk)
        body = b"".join(chunks)
        encoding = response.encoding or "utf-8"
        try:
            return body.decode(encoding, errors="replace")
        except LookupError:
            return body.decode("utf-8", errors="replace")


# --------------------------------------------------------------------- playwright


class PlaywrightPageFetcher:
    """Real-browser fetch — bypasses Cloudflare/bot challenges and renders JS.

    Lazily imports playwright so test environments without it (or images
    without browser binaries) don't pay the import cost. Each call
    spawns + closes its own browser to keep memory bounded; for high
    throughput a future refactor would pool a single Browser instance.
    """

    def __init__(
        self,
        *,
        timeout_ms: int = 20_000,
        headless: bool = True,
        locale: str = "nl-NL",
    ) -> None:
        self._timeout_ms = timeout_ms
        self._headless = headless
        self._locale = locale

    async def fetch(self, url: str) -> FetchedPage | None:
        if not host_is_safe(url):
            log.warning("playwright_fetch_blocked_unsafe_host", url=url)
            return None
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log.warning("playwright_not_installed")
            return None
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=self._headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ],
                )
                try:
                    ctx = await browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        locale=self._locale,
                        extra_http_headers={
                            "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.7",
                        },
                    )
                    try:
                        from playwright_stealth import Stealth  # type: ignore

                        await Stealth().apply_stealth_async(ctx)
                    except Exception:  # noqa: BLE001
                        await ctx.add_init_script(
                            "Object.defineProperty(navigator, 'webdriver', "
                            "{ get: () => undefined });"
                        )
                    page = await ctx.new_page()
                    response = await page.goto(
                        url, wait_until="domcontentloaded", timeout=self._timeout_ms
                    )
                    # Give JS-rendered content a moment to populate the DOM.
                    await asyncio.sleep(1.2)
                    html = await page.content()
                    status = response.status if response else 200
                    return FetchedPage(
                        url=page.url, html=html, status=status, source="playwright"
                    )
                finally:
                    await browser.close()
        except Exception as e:  # noqa: BLE001 — Playwright raises a zoo of exceptions
            log.warning("playwright_fetch_error", url=url, error=str(e)[:200])
            return None


# --------------------------------------------------------------------- cascade


class CascadingPageFetcher:
    """Run the fast fetcher first; fall back to the slow one when needed.

    "Needed" means: fast fetch returned None, the response was a known
    blocked status, or the body was so short it's likely a stub. The
    slow fetcher is constructed lazily via a factory so we don't pay
    Playwright import cost when fast path always succeeds.
    """

    def __init__(
        self,
        fast: PageFetcher,
        slow_factory: Callable[[], PageFetcher],
        *,
        min_body_bytes: int = MIN_USABLE_BODY_BYTES,
        min_anchors: int = MIN_USABLE_ANCHORS,
    ) -> None:
        self._fast = fast
        self._slow_factory = slow_factory
        self._min_body = min_body_bytes
        self._min_anchors = min_anchors

    async def fetch(self, url: str) -> FetchedPage | None:
        page = await self._fast.fetch(url)
        usable, reason = self._evaluate(page)
        if usable and page is not None:
            return page
        log.info(
            "page_fetch_cascade_fallback",
            url=url,
            fast_status=page.status if page else None,
            fast_bytes=len(page.html) if page else 0,
            reason=reason,
        )
        slow = self._slow_factory()
        slow_page = await slow.fetch(url)
        return slow_page or page  # surface the fast attempt if slow fails too

    def _evaluate(self, page: FetchedPage | None) -> tuple[bool, str]:
        """Decide whether the fast fetch is good enough.

        Returns (usable, reason). Reasons explain *why* we escalated so
        the cascade-fallback log line is debuggable when content drift
        breaks a heuristic.
        """
        if page is None:
            return False, "fast_returned_none"
        if page.status in BLOCKED_STATUSES:
            return False, f"blocked_status_{page.status}"
        body_bytes = len(page.html.encode("utf-8", errors="ignore"))
        if body_bytes < self._min_body:
            return False, f"body_too_short_{body_bytes}"
        # JS-only shell detection. Cheap regex over the HTML rather than a
        # full BS4 parse: this runs on every page and we don't want the
        # cascade itself to dominate scan time.
        anchor_count = page.html.count("<a ")
        if anchor_count < self._min_anchors and any(
            marker in page.html for marker in SPA_MARKERS
        ):
            return False, f"spa_shell_anchors_{anchor_count}"
        # Even without explicit SPA markers, a near-empty `<body>` is a
        # tell. Some hand-rolled JS-only pages don't ship a framework.
        if anchor_count < self._min_anchors and body_bytes < 8_000:
            return False, f"thin_static_html_anchors_{anchor_count}"
        return True, "ok"


# --------------------------------------------------------------------- factory


def default_page_fetcher(client: httpx.AsyncClient) -> PageFetcher:
    """Production default: httpx fast path with Playwright JS-render fallback."""
    return CascadingPageFetcher(
        fast=HttpxPageFetcher(client),
        slow_factory=lambda: PlaywrightPageFetcher(),
    )


__all__ = [
    "BLOCKED_STATUSES",
    "CascadingPageFetcher",
    "FetchedPage",
    "HttpxPageFetcher",
    "MIN_USABLE_BODY_BYTES",
    "PageFetcher",
    "PlaywrightPageFetcher",
    "default_page_fetcher",
]
