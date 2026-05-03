"""Pure signal extractors over already-fetched HTML.

No I/O — fetching belongs to ``pipeline.py``. Each function is independently
unit-testable on a static HTML fixture.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from ..domain import canonical_domain
from ..seeds.trackers import (
    AFFILIATE_PATH_PATTERNS,
    AFFILIATE_QUERY_PARAMS,
    TRACKER_DOMAINS,
)


@dataclass
class PageSignals:
    domain: str
    affiliate_links: list[str] = field(default_factory=list)
    has_tracker_in_links: bool = False
    schema_types: list[str] = field(default_factory=list)
    schema_review_target: str | None = None
    text_content: str = ""
    brand_mention_count: int = 0
    competitor_mention_counts: dict[str, int] = field(default_factory=dict)
    primary_cta_url: str | None = None
    h1_text: str = ""
    title: str = ""

    def total_competitor_mentions(self) -> int:
        return sum(self.competitor_mention_counts.values())


def is_affiliate_link(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if any(p in path for p in AFFILIATE_PATH_PATTERNS):
        return True
    qs = parse_qs(parsed.query)
    if any(p in qs for p in AFFILIATE_QUERY_PARAMS):
        return True
    return canonical_domain(url) in TRACKER_DOMAINS


def extract_affiliate_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    out: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href:
            continue
        if not href.startswith(("http://", "https://")):
            href = urljoin(base_url, href)
            if not href.startswith(("http://", "https://")):
                continue
        if is_affiliate_link(href):
            out.append(href)
    return out


def extract_schema_types(html: str) -> tuple[list[str], str | None]:
    """Return ``(@type list, Review.itemReviewed.name)`` from JSON-LD blocks."""
    soup = BeautifulSoup(html, "lxml")
    types: list[str] = []
    review_target: str | None = None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type")
            if isinstance(t, list):
                types.extend(t)
            elif isinstance(t, str):
                types.append(t)
            if item.get("@type") == "Review":
                target = item.get("itemReviewed")
                if isinstance(target, dict):
                    review_target = target.get("name")
                elif isinstance(target, str):
                    review_target = target
    return types, review_target


def count_keyword_in_text(text: str, keyword: str) -> int:
    if not keyword:
        return 0
    return len(re.findall(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE))


def extract_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def extract_primary_cta(html: str) -> str | None:
    """Heuristic: first ``<a>`` whose class hints at a primary CTA."""
    soup = BeautifulSoup(html, "lxml")
    cta_keywords = ("cta", "btn", "button", "primary", "play-now", "join", "sign-up", "signup")
    for a in soup.find_all("a", href=True):
        cls = " ".join(a.get("class") or []).lower()
        if any(k in cls for k in cta_keywords):
            return a["href"]
    return None


def extract_signals(
    html: str,
    base_url: str,
    brand_name: str,
    competitor_names: Iterable[str],
) -> PageSignals:
    soup = BeautifulSoup(html, "lxml")

    text = extract_clean_text(html)
    affiliate_links = extract_affiliate_links(html, base_url)
    has_tracker = any(canonical_domain(link) in TRACKER_DOMAINS for link in affiliate_links)
    schema_types, review_target = extract_schema_types(html)

    title = (soup.find("title").string or "").strip() if soup.find("title") else ""
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""

    brand_count = count_keyword_in_text(text, brand_name)
    competitor_counts: dict[str, int] = {}
    for c in competitor_names:
        # Drop TLD so "hollandcasino" matches in copy regardless of host.
        bare = c.split(".")[0]
        if bare and bare != brand_name.lower():
            competitor_counts[bare] = count_keyword_in_text(text, bare)

    return PageSignals(
        domain=canonical_domain(base_url),
        affiliate_links=affiliate_links,
        has_tracker_in_links=has_tracker,
        schema_types=schema_types,
        schema_review_target=review_target,
        text_content=text[:5000],
        brand_mention_count=brand_count,
        competitor_mention_counts=competitor_counts,
        primary_cta_url=extract_primary_cta(html),
        h1_text=h1_text,
        title=title,
    )
