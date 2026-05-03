"""Canonical domain identifier — the single source of truth.

Returns the lower-cased hostname (sans optional ``www.``). We deliberately
do **not** use ``tldextract``: the Public Suffix List doesn't recognise NL
hosts under ``com.nl`` / ``co.nl`` / ``net.nl`` as effective TLDs, so an
eTLD+1 collapse would map ``starcasino.com.nl`` to ``com.nl`` and miss the
brand. The full hostname is the only identifier that matches both what
users type and what is stored alongside SERP rows.
"""

from __future__ import annotations

from urllib.parse import urlparse


def canonical_domain(url_or_host: str) -> str:
    """Return the lower-case hostname identifier (no scheme, port, userinfo, ``www.``).

    Examples
    --------
    >>> canonical_domain("https://starcasino.nl/casino")
    'starcasino.nl'
    >>> canonical_domain("https://www.starcasino.nl/x?a=1")
    'starcasino.nl'
    >>> canonical_domain("starcasino.com.nl")
    'starcasino.com.nl'
    >>> canonical_domain("STARCASINO.NL")
    'starcasino.nl'
    >>> canonical_domain("")
    ''
    """
    if not url_or_host:
        return ""
    parsed = urlparse(url_or_host if "://" in url_or_host else f"http://{url_or_host}")
    host = (parsed.netloc or url_or_host).lower().strip("/")
    if "@" in host:
        host = host.rsplit("@", 1)[1]
    if ":" in host:
        host = host.split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    return host
