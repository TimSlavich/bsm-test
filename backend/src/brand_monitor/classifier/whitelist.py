"""Stage 1 — fast, deterministic, no I/O.

Hits a static set of brand-specific lists (official / partner / competitor)
or the global informational seed (news / forum / regulator / portal).
Returns ``None`` to defer to stage 2.
"""

from __future__ import annotations

import re

from ..domain import canonical_domain
from ..seeds.info_domains import INFO_DOMAIN_TO_SUBCATEGORY
from ..seeds.starcasino import BrandSeed
from .taxonomy import (
    SUBCATEGORY_TO_CATEGORY,
    Classification,
    ReasonCode,
    Subcategory,
)

WHITELIST_CONFIDENCE = 0.95

root_domain = canonical_domain  # historical alias

_PROMO_PATH_PAT = re.compile(
    r"(?:^|/)(promo|welcome|bonus|landing|jackpot)(?:/|$)", re.IGNORECASE
)
# A whitelisted official entry on these hosts means brand-owned media
# (the dispatcher only enters this branch when the host is itself in
# ``brand.official_domains``, so seeding e.g. ``youtube.com`` is the
# explicit opt-in).
_OWNED_MEDIA_HOSTS = frozenset(
    {"youtube.com", "twitter.com", "x.com", "facebook.com", "linkedin.com"}
)

# Word-boundary patterns — substring "vs" used to match "/services/" etc.
_REVIEW_PAT = re.compile(r"\b(review|recensie)s?\b|/recensies?/", re.IGNORECASE)
_BONUS_PAT = re.compile(r"\b(bonus|promo|welkomstbonus|stortingsbonus)\b", re.IGNORECASE)
_COMPARE_PAT = re.compile(r"\b(vs|comparison|vergelijk|vergelijken)\b", re.IGNORECASE)


def _detect_partner_subcategory_from_url(url: str) -> Subcategory:
    if _REVIEW_PAT.search(url):
        return Subcategory.AFFILIATE_DEDICATED_REVIEW
    if _BONUS_PAT.search(url):
        return Subcategory.AFFILIATE_BONUS_PROMO
    if _COMPARE_PAT.search(url):
        return Subcategory.AFFILIATE_COMPARISON
    return Subcategory.AFFILIATE_LISTICLE


def _detect_official_subcategory(url: str, domain: str, brand: BrandSeed) -> Subcategory:
    path = url.split(domain, 1)[-1].lower() if domain in url else ""
    if _PROMO_PATH_PAT.search(path):
        return Subcategory.OFFICIAL_PROMO_LANDING
    if domain in _OWNED_MEDIA_HOSTS:
        return Subcategory.OFFICIAL_OWNED_MEDIA
    # Apex if the host ends with the brand's geo TLD, else a localized
    # variant. Plain endswith — see ``domain.canonical_domain`` for why
    # tldextract isn't used.
    geo_tld = "." + brand.geo.lower()
    if domain.endswith(geo_tld):
        return Subcategory.OFFICIAL_APEX
    return Subcategory.OFFICIAL_LOCALIZED


def classify_whitelist(url: str, brand: BrandSeed) -> Classification | None:
    """Return a whitelist verdict, or ``None`` to defer to the next stage."""
    domain = canonical_domain(url)

    if domain in brand.official_domains:
        sub = _detect_official_subcategory(url, domain, brand)
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[sub],
            subcategory=sub,
            confidence=WHITELIST_CONFIDENCE,
            stage_used=1,
            signals={"matched": "official_domain", "domain": domain},
            reasoning=f"Domain {domain} is in brand.official_domains",
            reason_code=ReasonCode.WHITELIST_OFFICIAL,
        )

    if domain in brand.known_partners:
        sub = _detect_partner_subcategory_from_url(url)
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[sub],
            subcategory=sub,
            confidence=WHITELIST_CONFIDENCE,
            stage_used=1,
            signals={"matched": "known_partner", "domain": domain},
            reasoning=f"Domain {domain} is in brand.known_partners",
            reason_code=ReasonCode.WHITELIST_PARTNER,
        )

    if domain in brand.known_competitors:
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[Subcategory.HIJACKER_DIRECT_COMPETITOR],
            subcategory=Subcategory.HIJACKER_DIRECT_COMPETITOR,
            confidence=WHITELIST_CONFIDENCE,
            stage_used=1,
            signals={"matched": "known_competitor", "domain": domain},
            reasoning=f"Domain {domain} is in brand.known_competitors",
            reason_code=ReasonCode.WHITELIST_COMPETITOR,
        )

    if domain in INFO_DOMAIN_TO_SUBCATEGORY:
        sub = INFO_DOMAIN_TO_SUBCATEGORY[domain]
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[sub],
            subcategory=sub,
            confidence=WHITELIST_CONFIDENCE,
            stage_used=1,
            signals={"matched": "info_seed", "domain": domain},
            reasoning=f"Domain {domain} is in informational seed list",
            reason_code=ReasonCode.WHITELIST_INFO_SEED,
        )

    return None
