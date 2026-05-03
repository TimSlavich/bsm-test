"""Favicon proxy.

Why a proxy: third-party favicon services (Google s2, DuckDuckGo) 404 for a
non-trivial slice of NL iGaming hosts, and those 404s land in the browser
DevTools console regardless of any client-side ``onError`` handler. We
absorb them server-side: the route always returns ``200 OK`` with either
the resolved icon bytes or a deterministic SVG fallback.

Sources are tried in order; the first one to return non-empty image bytes
wins. Resolved icons live in an in-memory LRU cache (24h TTL by default,
sufficient for prototype scale — favicons rarely change).
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from typing import NamedTuple

import httpx
import structlog
from fastapi import APIRouter, Path, Response

from ..domain import canonical_domain

router = APIRouter(prefix="/favicons", tags=["favicons"])
log = structlog.get_logger()

_CACHE_TTL_S = 60 * 60 * 24
_CACHE_MAX = 4096
_FETCH_TIMEOUT_S = 4.0
_MIN_VALID_BYTES = 64


class CachedFavicon(NamedTuple):
    body: bytes
    media_type: str
    expires_at: float


_cache: dict[str, CachedFavicon] = {}
_cache_lock = asyncio.Lock()


SOURCES: tuple[str, ...] = (
    # Google's s2 endpoint — best hit-rate for major domains.
    "https://www.google.com/s2/favicons?sz={size}&domain={domain}",
    # DuckDuckGo — different coverage; catches some that Google misses.
    "https://icons.duckduckgo.com/ip3/{domain}.ico",
    # Last-resort direct fetch.
    "https://{domain}/favicon.ico",
)


def _is_probably_image(body: bytes, media_type: str) -> bool:
    """Heuristic: filter out empty bodies and HTML error pages.

    Google's s2 sometimes returns a tiny generic globe SVG even when the
    real favicon is missing; we accept those (still better than nothing).
    What we reject is empty responses and ``text/html`` 200s.
    """
    if len(body) < _MIN_VALID_BYTES:
        return False
    if media_type.startswith("text/"):
        return False
    return True


def _svg_fallback(domain: str, size: int) -> bytes:
    """Deterministic letter-tile SVG. Colour from a hash of the domain."""
    initial = (domain[0] if domain else "?").upper()
    h = int(hashlib.md5(domain.encode("utf-8")).hexdigest()[:6], 16)
    hue = h % 360
    bg = f"hsl({hue}, 65%, 88%)"
    fg = f"hsl({hue}, 60%, 28%)"
    font_size = max(8, round(size * 0.6))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
        f'<rect width="{size}" height="{size}" rx="{round(size * 0.18)}" fill="{bg}"/>'
        f'<text x="50%" y="50%" text-anchor="middle" dominant-baseline="central" '
        f'font-family="system-ui, -apple-system, Segoe UI, sans-serif" '
        f'font-weight="700" font-size="{font_size}" fill="{fg}">{_escape(initial)}</text>'
        f"</svg>"
    ).encode("utf-8")


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def _try_source(client: httpx.AsyncClient, url: str) -> tuple[bytes, str] | None:
    try:
        r = await client.get(url, timeout=_FETCH_TIMEOUT_S, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    body = r.content or b""
    media = (r.headers.get("content-type") or "image/x-icon").split(";", 1)[0].strip()
    if not _is_probably_image(body, media):
        return None
    return body, media


async def _resolve(domain: str, size: int) -> tuple[bytes, str]:
    async with httpx.AsyncClient(headers={"User-Agent": "BrandMonitorBot/0.1"}) as client:
        for tmpl in SOURCES:
            url = tmpl.format(domain=domain, size=size)
            res = await _try_source(client, url)
            if res is not None:
                return res
    return _svg_fallback(domain, size), "image/svg+xml"


def _cache_get(key: str) -> CachedFavicon | None:
    item = _cache.get(key)
    if item is None:
        return None
    if item.expires_at < time.time():
        _cache.pop(key, None)
        return None
    return item


def _cache_put(key: str, body: bytes, media_type: str) -> None:
    if len(_cache) >= _CACHE_MAX:
        # Drop the oldest 5% — cheap eviction without an LRU library.
        for k in list(_cache.keys())[: max(1, _CACHE_MAX // 20)]:
            _cache.pop(k, None)
    _cache[key] = CachedFavicon(body, media_type, time.time() + _CACHE_TTL_S)


@router.get("/{domain}")
async def get_favicon(
    domain: str = Path(..., min_length=1, max_length=255),
    size: int = 32,
) -> Response:
    """Always returns 200. Body is either the resolved favicon or an SVG tile."""
    canon = canonical_domain(domain)
    if not canon:
        canon = domain.lower()
    size = max(16, min(size, 128))
    key = f"{canon}@{size}"

    async with _cache_lock:
        cached = _cache_get(key)

    if cached is None:
        body, media = await _resolve(canon, size)
        async with _cache_lock:
            _cache_put(key, body, media)
    else:
        body, media = cached.body, cached.media_type

    return Response(
        content=body,
        media_type=media,
        headers={
            # Long browser cache — the proxy already absorbs upstream churn.
            "Cache-Control": "public, max-age=86400, immutable",
        },
    )
