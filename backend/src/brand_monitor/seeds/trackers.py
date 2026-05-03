"""Affiliate tracker / network domain fingerprints.

Used by stage-2 algorithm classifier to detect affiliate redirect chains.
If a redirect chain passes through one of these domains, we know the
destination is monetized affiliate (vs. organic redirect).
"""

from __future__ import annotations

# Known affiliate-network and tracker domains in iGaming
TRACKER_DOMAINS: frozenset[str] = frozenset(
    {
        # Voluum
        "voluum.com",
        "trk.voluum.com",
        # Affilka (by SoftSwiss — major iGaming affiliate platform)
        "affilka.com",
        "affilkapartners.com",
        # MyAffiliates
        "myaffiliates.com",
        "ma-tracker.com",
        # Bemobi
        "bemob.com",
        "bemobtrcks.com",
        # Income Access
        "incomeaccess.com",
        "ia.network",
        # Cake (NetRefer)
        "netrefer.com",
        # Generic CPA/affiliate networks
        "trackier.com",
        "tracking.iqaffiliates.com",
        "go.aff-online.com",
    }
)

# URL path patterns that strongly indicate an affiliate redirect link
AFFILIATE_PATH_PATTERNS: tuple[str, ...] = (
    "/go/",
    "/out/",
    "/visit/",
    "/redirect/",
    "/aff/",
    "/promo/go",
    "/click/",
    "/r/",
    "/track/",
    # Same-host obfuscated affiliate gateways. Some NL leadgen sites
    # (e.g. star-casino.co) hide the destination behind base64-style
    # internal endpoints — they look like a normal page route but 30x to
    # an external operator. Treat them as affiliate links so the redirect
    # chain gets resolved.
    "/many-game/",
    "/play/",
    "/bezoek/",
    "/spelen/",
    "/casino-go/",
    "/affiliate/",
)

# Query parameters indicating affiliate tagging
AFFILIATE_QUERY_PARAMS: frozenset[str] = frozenset(
    {
        "ref",
        "aff",
        "affid",
        "affiliateid",
        "affiliate",
        "btag",
        "promo",
        "campaign",
        "subid",
        "clickid",
    }
)
