"""Seed lists for category 4 (informational / neutral) detection.

These are non-brand-specific — domains that should be classified as
informational regardless of which brand we are monitoring.
"""

from __future__ import annotations

from ..classifier.taxonomy import Subcategory

# NL news outlets (most likely to mention iGaming brands organically)
NL_NEWS_DOMAINS: frozenset[str] = frozenset(
    {
        "nu.nl",
        "rtlnieuws.nl",
        "ad.nl",
        "telegraaf.nl",
        "nrc.nl",
        "volkskrant.nl",
        "nos.nl",
        "trouw.nl",
        "fd.nl",
        "parool.nl",
    }
)

# Forums and social platforms
FORUM_SOCIAL_DOMAINS: frozenset[str] = frozenset(
    {
        "reddit.com",
        "trustpilot.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
        "youtube.com",
        "quora.com",
        "tweakers.net",
    }
)

# Regulators (NL: Kansspelautoriteit; international ones encountered in iGaming SERP)
REGULATOR_DOMAINS: frozenset[str] = frozenset(
    {
        "kansspelautoriteit.nl",
        "ksa.nl",
        "mga.org.mt",          # Malta Gaming Authority
        "gamblingcommission.gov.uk",
        "adm.gov.it",          # AAMS / ADM Italy
    }
)

# Generic gambling info portals (review aggregators that don't run affiliate
# redirects — purely editorial). Used as soft signal, not strict whitelist.
# ``gamblingcommission.gov.uk`` is intentionally NOT here — it's a regulator,
# not a portal. Earlier the dict-merge below silently demoted the regulator
# classification because it was duplicated.
GAMBLING_INFO_PORTALS: frozenset[str] = frozenset(
    {
        "gamblingsites.com",
        "askgamblers.com",
        "casino.org",
        "wikipedia.org",
        "wiktionary.org",
    }
)


def _build_subcategory_map() -> dict[str, Subcategory]:
    """Build the domain→subcategory map and assert no duplicate keys.

    Earlier each set was merged via ``**dict.fromkeys(...)``; if two seeds
    contained the same domain, the second silently won. The assertion below
    surfaces that the moment a developer adds a duplicate.
    """
    sources = (
        (NL_NEWS_DOMAINS, Subcategory.INFO_NEWS),
        (FORUM_SOCIAL_DOMAINS, Subcategory.INFO_FORUM_SOCIAL),
        (REGULATOR_DOMAINS, Subcategory.INFO_REGULATOR),
        (GAMBLING_INFO_PORTALS, Subcategory.INFO_GAMBLING_PORTAL),
    )
    out: dict[str, Subcategory] = {}
    for domains, sub in sources:
        for d in domains:
            if d in out:
                raise ValueError(
                    f"Domain {d!r} duplicated across info-domain seed lists "
                    f"(already mapped to {out[d]!r}, attempted {sub!r})"
                )
            out[d] = sub
    return out


# Domain → subcategory mapping for stage-1 informational match
INFO_DOMAIN_TO_SUBCATEGORY: dict[str, Subcategory] = _build_subcategory_map()
