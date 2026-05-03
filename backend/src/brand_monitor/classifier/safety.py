"""SSRF guard for outbound requests made by the classifier.

Both the page fetcher and the redirect resolver follow attacker-influenced
URLs (SERP-listed domains and the redirects they emit). A hostile page
can redirect to ``http://169.254.169.254/`` (cloud metadata) or
``http://localhost:6379`` to attack the worker. ``host_is_safe`` is the
single chokepoint — any new outbound code path must call it.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def host_is_safe(url: str) -> bool:
    """Reject non-http schemes and private/loopback/link-local hosts.

    Resolves the hostname and refuses any IP that isn't a public unicast
    address. Returns False on any parsing or DNS error so callers can
    treat the URL as unsafe by default.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    return True
