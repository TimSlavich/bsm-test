"""Cascading SERP fetcher: Google (Playwright stealth) → DuckDuckGo HTML → fixture file.

Production scale needs residential proxies for the Google path; without
them, Google quickly serves a reCAPTCHA wall. The DDG path is the
robustness fallback. The fixture path keeps CI deterministic offline.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

from ..domain import canonical_domain as _root

log = structlog.get_logger()


@dataclass
class SerpResult:
    position: int
    url: str
    domain: str
    title: str
    snippet: str


@dataclass
class FetchOutcome:
    """Audit-trail-friendly result: which strategy succeeded + its rows."""

    results: list["SerpResult"]
    source: str  # "google_playwright" | "duckduckgo_html" | "fixture" | "none"


USER_AGENTS = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
)


def build_search_url(keyword: str, geo: str = "NL", num: int = 20) -> str:
    geo_lower = geo.lower()
    return (
        f"https://www.google.{geo_lower}/search?"
        f"q={quote_plus(keyword)}&hl={geo_lower}&gl={geo}&num={num}&pws=0"
    )


def parse_serp_html(html: str, max_results: int = 20) -> list[SerpResult]:
    """Parse Google SERP HTML by anchoring on `<h3>` + parent `<a href>`.

    The h3-based pivot is robust to Google's frequent class-name churn —
    far more stable than CSS class selectors.
    """
    soup = BeautifulSoup(html, "lxml")
    results: list[SerpResult] = []
    seen: set[str] = set()
    position = 0

    for h3 in soup.find_all("h3"):
        a = h3.find_parent("a", href=True)
        if not a:
            continue
        href = a["href"]
        if not href.startswith("http"):
            continue
        # Drop Google's own hosts via equality/suffix, not substring
        # (substring would also drop e.g. "googlecomputed.example").
        host = _root(href)
        if host == "google.com" or host.endswith(".google.com"):
            continue
        if href in seen:
            continue
        seen.add(href)
        position += 1

        title = h3.get_text(strip=True)
        snippet = ""
        container = a.find_parent(["div", "article"])
        if container:
            for sel in ["[data-sncf]", "div[role=text]", "span"]:
                node = container.select_one(sel)
                if node and len(node.get_text(strip=True)) > 30:
                    snippet = node.get_text(" ", strip=True)
                    break

        results.append(
            SerpResult(
                position=position,
                url=href,
                domain=_root(href),
                title=title,
                snippet=snippet,
            )
        )
        if len(results) >= max_results:
            break

    return results


def parse_ddg_html(html: str) -> list[SerpResult]:
    """Parse DuckDuckGo HTML SERP. Unwraps the `/l/?uddg=…` redirect wrapper
    so callers see actual landing-page URLs."""
    soup = BeautifulSoup(html, "lxml")
    results: list[SerpResult] = []
    seen: set[str] = set()
    position = 0
    for a in soup.select("a.result__a"):
        href = a.get("href", "")
        if href.startswith("/"):
            href = f"https://duckduckgo.com{href}"
        parsed = urlparse(href)
        if "duckduckgo.com" in parsed.netloc and "uddg" in parsed.query:
            qs = parse_qs(parsed.query)
            if "uddg" in qs:
                href = qs["uddg"][0]
        if not href.startswith("http"):
            continue
        if href in seen:
            continue
        seen.add(href)
        position += 1
        title = a.get_text(strip=True)
        snippet = ""
        container = a.find_parent(class_="result")
        if container is not None:
            snip = container.select_one(".result__snippet")
            if snip:
                snippet = snip.get_text(" ", strip=True)
        results.append(
            SerpResult(
                position=position, url=href, domain=_root(href), title=title, snippet=snippet
            )
        )
    return results


class SerpFetcher:
    """Cascading fetcher: Google → DuckDuckGo → saved fixture."""

    def __init__(
        self,
        prefer_playwright: bool = True,
        fixture_path: str | Path | None = None,
    ) -> None:
        self.prefer_playwright = prefer_playwright
        self.fixture_path = Path(fixture_path) if fixture_path else None

    async def fetch(self, keyword: str, geo: str = "NL", num: int = 20) -> list[SerpResult]:
        """Backwards-compatible shape — returns rows only.

        Prefer :meth:`fetch_with_source` so the snapshot's audit trail
        records which strategy actually fired.
        """
        outcome = await self.fetch_with_source(keyword, geo, num)
        return outcome.results

    async def fetch_with_source(
        self, keyword: str, geo: str = "NL", num: int = 20
    ) -> FetchOutcome:
        log.info("serp_fetch_start", keyword=keyword, geo=geo, num=num)

        if self.prefer_playwright:
            url = build_search_url(keyword, geo, num)
            try:
                html = await self._fetch_playwright(url)
                if html and "did not match any documents" not in html:
                    parsed = parse_serp_html(html)
                    if parsed:
                        log.info("serp_source_used", source="google_playwright", n=len(parsed))
                        return FetchOutcome(parsed[:num], "google_playwright")
            except Exception as e:  # noqa: BLE001
                log.warning("google_playwright_failed", error=str(e))

        try:
            ddg = await self._fetch_duckduckgo(keyword, geo)
            if ddg:
                log.info("serp_source_used", source="duckduckgo_html", n=len(ddg))
                return FetchOutcome(ddg[:num], "duckduckgo_html")
        except Exception as e:  # noqa: BLE001
            log.warning("duckduckgo_failed", error=str(e))

        if self.fixture_path and self.fixture_path.exists():
            html = self.fixture_path.read_text(encoding="utf-8")
            parser = parse_ddg_html if "result__a" in html else parse_serp_html
            parsed = parser(html)
            log.info(
                "serp_source_used",
                source="fixture",
                path=str(self.fixture_path),
                n=len(parsed),
            )
            return FetchOutcome(parsed[:num], "fixture")

        log.error("serp_all_sources_failed", keyword=keyword)
        return FetchOutcome([], "none")

    async def _fetch_duckduckgo(self, keyword: str, geo: str) -> list[SerpResult]:
        kl = f"{geo.lower()}-{geo.lower()}"
        async with httpx.AsyncClient(
            headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept-Language": f"{geo.lower()}-{geo.upper()},{geo.lower()};q=0.9,en;q=0.7",
            },
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            r = await client.get(
                "https://html.duckduckgo.com/html/", params={"q": keyword, "kl": kl}
            )
            r.raise_for_status()
            return parse_ddg_html(r.text)

    async def _fetch_playwright(self, url: str) -> str | None:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log.warning("playwright_not_installed")
            return None
        try:
            from playwright_stealth import Stealth
        except ImportError:
            Stealth = None  # type: ignore[assignment]

        stealth = Stealth() if Stealth else None
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
            try:
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={"width": 1280, "height": 800},
                    locale="nl-NL",
                    timezone_id="Europe/Amsterdam",
                    extra_http_headers={
                        "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.7,en;q=0.5",
                    },
                )
                if stealth is not None:
                    await stealth.apply_stealth_async(context)
                else:
                    await context.add_init_script(
                        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
                    )

                # Pre-set Google's consent cookies — skips the consent.google.com
                # interstitial that breaks an unattended scrape.
                await context.add_cookies(
                    [
                        {"name": "CONSENT", "value": "YES+NL.nl+V14+BX", "domain": ".google.com", "path": "/"},
                        {"name": "CONSENT", "value": "YES+NL.nl+V14+BX", "domain": ".google.nl", "path": "/"},
                        {
                            "name": "SOCS",
                            "value": "CAESHAgBEhJnd3NfMjAyMzAxMTAtMF9SQzIaAm5sIAEaBgiAo7CdBg",
                            "domain": ".google.com",
                            "path": "/",
                        },
                    ]
                )

                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                for label in ("Alles accepteren", "Accept all", "Ik ga akkoord"):
                    try:
                        await page.get_by_role("button", name=label).first.click(timeout=2000)
                        break
                    except Exception:  # noqa: BLE001
                        continue
                await asyncio.sleep(1.2)
                html = await page.content()
                if (
                    "Our systems have detected unusual traffic" in html
                    or "captcha-form" in html
                    or "/sorry/index" in html
                ):
                    log.warning("captcha_or_consent_block_detected", chars=len(html))
                    return None
                return html
            finally:
                await browser.close()
