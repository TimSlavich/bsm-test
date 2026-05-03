"""Stage 2 — rules over extracted page signals + redirect destinations.

The defining rule is destination-of-redirect: partner sends users to the
brand, hijacker sends them elsewhere. Pages identical on the surface differ
only in where their affiliate links resolve.
"""

from __future__ import annotations

import re

from ..domain import canonical_domain
from ..seeds.starcasino import BrandSeed
from .signals import PageSignals
from .taxonomy import (
    SUBCATEGORY_TO_CATEGORY,
    Classification,
    ReasonCode,
    Subcategory,
)

HIGH_CONFIDENCE = 0.85
MED_CONFIDENCE = 0.70
LOW_CONFIDENCE = 0.55  # below pipeline.LLM_ESCALATION_THRESHOLD → routes to stage 3


def classify_destinations(
    destinations: list[str],
    brand: BrandSeed,
) -> tuple[float, float]:
    """Return ``(brand_ratio, competitor_ratio)`` of final redirect destinations."""
    if not destinations:
        return 0.0, 0.0
    total = len(destinations)
    brand_hits = sum(canonical_domain(d) in brand.official_domains for d in destinations)
    comp_hits = sum(canonical_domain(d) in brand.known_competitors for d in destinations)
    return brand_hits / total, comp_hits / total


# Word-boundary regex — substring "vs" in "versus" / "top" in "stop" used to
# false-positive against arbitrary URLs.
_PAT_COMPARISON = re.compile(r"\b(vs|comparison|vergelijk)\b", re.IGNORECASE)
_PAT_BONUS = re.compile(r"\b(bonus|promo|welcome|welkom)\b", re.IGNORECASE)
_PAT_LISTICLE = re.compile(r"\b(best|top|beste)\b", re.IGNORECASE)
_PAT_REVIEW = re.compile(r"\b(review|recensie)\b", re.IGNORECASE)
# Pages that *claim* to be the brand: "Officiële website", "Official site",
# "™" mark, registration/login copy that pretends to be the operator itself.
# These markers in the title/H1 of a NON-whitelisted domain are the
# tell-tale of a fake-official hijacker.
_PAT_OFFICIAL_CLAIM = re.compile(
    r"(officiële\s+website|official\s+(site|website)|"
    r"[™®]|inloggen\s+en\s+registratie|registratie\s+en\s+inloggen|"
    r"registreer\s+nu|aanmelden\s+bij)",
    re.IGNORECASE,
)
# Minimum brand mentions to consider mimicry — separates a casual mention
# from sustained impersonation copy.
MIMICRY_MIN_BRAND_MENTIONS = 5


def _detect_partner_subcategory(signals: PageSignals) -> Subcategory:
    title_h1 = f"{signals.title} {signals.h1_text}"
    if _PAT_COMPARISON.search(title_h1):
        return Subcategory.AFFILIATE_COMPARISON
    if _PAT_BONUS.search(title_h1):
        return Subcategory.AFFILIATE_BONUS_PROMO
    if _PAT_LISTICLE.search(title_h1):
        return Subcategory.AFFILIATE_LISTICLE
    if _PAT_REVIEW.search(title_h1):
        return Subcategory.AFFILIATE_DEDICATED_REVIEW
    return Subcategory.AFFILIATE_LISTICLE


def classify_algorithm(
    signals: PageSignals,
    redirect_destinations: list[str],
    brand: BrandSeed,
) -> Classification:
    """Apply rules in priority order. Always returns a valid Classification."""

    brand_ratio, comp_ratio = classify_destinations(redirect_destinations, brand)
    n_aff = len(signals.affiliate_links)

    reason_parts = [
        f"affiliate_links={n_aff}",
        f"brand_redirect_ratio={brand_ratio:.2f}",
        f"competitor_redirect_ratio={comp_ratio:.2f}",
        f"brand_mentions={signals.brand_mention_count}",
        f"competitor_mentions={signals.total_competitor_mentions()}",
        f"schema_types={signals.schema_types}",
    ]
    base_signals = {
        "n_affiliate_links": n_aff,
        "brand_redirect_ratio": brand_ratio,
        "competitor_redirect_ratio": comp_ratio,
        "brand_mentions": signals.brand_mention_count,
        "competitor_mentions_total": signals.total_competitor_mentions(),
        "schema_types": signals.schema_types,
        "schema_review_target": signals.schema_review_target,
        "has_tracker": signals.has_tracker_in_links,
    }

    # Rule 0 — schema.org Review.itemReviewed names the brand → strong partner.
    # Token-set intersection avoids false positives like "casino" in "casino x"
    # matching a generic seed.
    target = (signals.schema_review_target or "").lower()
    brand_tokens = {d.split(".", 1)[0].lower() for d in brand.official_domains}
    target_tokens = set(re.findall(r"[a-z0-9]+", target))
    if target and brand_tokens & target_tokens:
        sub = _detect_partner_subcategory(signals)
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[sub],
            subcategory=sub,
            confidence=HIGH_CONFIDENCE,
            stage_used=2,
            signals=base_signals,
            reasoning="Schema.org Review.itemReviewed targets brand; "
            + ", ".join(reason_parts),
            reason_code=ReasonCode.ALG_SCHEMA_REVIEW_BRAND,
        )

    # Rule 0.5 — fake-official mimicry. A NON-whitelisted domain (we got
    # past stage 1) is impersonating the brand. Two firing conditions:
    #
    #   (a) Explicit "Officiële website" / "™" / registration claim in
    #       title/H1, brand mentions ≥ MIN, AND no verifiable outbound
    #       (i.e. redirect chains return to the same site or 404). This
    #       catches the classic fake-official pattern.
    #
    #   (b) Heavy brand-name impersonation copy (≥ HEAVY_MENTIONS) on an
    #       isolated page with no schema and no resolvable affiliate
    #       destinations. Catches "Speel en Win met X Gratis Spins!"-style
    #       NL leadgen pages that don't say "Officiële" but repeat the
    #       brand name 30+ times to rank.
    #
    # ``unresolved_destinations`` deliberately allows n_aff > 0 — many
    # fake-officials publish obfuscated /many-game/ links that resolve to
    # 404 (or back to themselves), so we trust *resolution failure* as a
    # negative signal too, not just literal absence of aff links.
    title_h1 = f"{signals.title} {signals.h1_text}"
    unresolved_destinations = brand_ratio == 0 and comp_ratio == 0
    no_competitors_named = signals.total_competitor_mentions() == 0
    has_official_claim = bool(_PAT_OFFICIAL_CLAIM.search(title_h1))

    HEAVY_BRAND_MENTIONS = 30  # noqa: N806
    fires_a = (
        has_official_claim
        and signals.brand_mention_count >= MIMICRY_MIN_BRAND_MENTIONS
        and unresolved_destinations
        and no_competitors_named
    )
    fires_b = (
        signals.brand_mention_count >= HEAVY_BRAND_MENTIONS
        and not signals.schema_types
        and unresolved_destinations
        and no_competitors_named
    )
    if fires_a or fires_b:
        trigger = "official_claim+isolated" if fires_a else "heavy_mentions+isolated"
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[Subcategory.HIJACKER_BLACKHAT_SCAM],
            subcategory=Subcategory.HIJACKER_BLACKHAT_SCAM,
            confidence=HIGH_CONFIDENCE if fires_a else MED_CONFIDENCE,
            stage_used=2,
            signals=base_signals,
            reasoning=(
                f"Non-whitelisted domain impersonates brand ({trigger}); "
                + ", ".join(reason_parts)
            ),
            reason_code=ReasonCode.ALG_FAKE_OFFICIAL_MIMICRY,
        )

    # Rule 1 — no affiliate links → informational.
    if n_aff == 0:
        is_news = (
            "NewsArticle" in signals.schema_types or "Article" in signals.schema_types
        )
        if signals.brand_mention_count == 0:
            sub = Subcategory.INFO_OTHER
        elif is_news:
            sub = Subcategory.INFO_NEWS
        else:
            sub = Subcategory.INFO_OTHER
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[sub],
            subcategory=sub,
            confidence=MED_CONFIDENCE,
            stage_used=2,
            signals=base_signals,
            reasoning="No affiliate links → informational; "
            + ", ".join(reason_parts),
            reason_code=ReasonCode.ALG_NO_AFFILIATE_NEWS if is_news else ReasonCode.ALG_NO_AFFILIATE_INFO,
        )

    # Rule 2 — majority of redirects land on brand → partner.
    if brand_ratio >= 0.6:
        sub = _detect_partner_subcategory(signals)
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[sub],
            subcategory=sub,
            confidence=min(HIGH_CONFIDENCE, 0.5 + brand_ratio * 0.5),
            stage_used=2,
            signals=base_signals,
            reasoning="Majority of redirects go to brand; " + ", ".join(reason_parts),
            reason_code=ReasonCode.ALG_BRAND_REDIRECT_MAJORITY,
        )

    # Rule 3 — majority of redirects land on competitors → hijacker.
    if comp_ratio >= 0.6:
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[Subcategory.HIJACKER_AFFILIATE_TO_OTHERS],
            subcategory=Subcategory.HIJACKER_AFFILIATE_TO_OTHERS,
            confidence=min(HIGH_CONFIDENCE, 0.5 + comp_ratio * 0.5),
            stage_used=2,
            signals=base_signals,
            reasoning="Majority of redirects go to competitors; "
            + ", ".join(reason_parts),
            reason_code=ReasonCode.ALG_COMPETITOR_REDIRECT_MAJORITY,
        )

    # Rule 4 — mixed redirects but brand mentions dominate.
    if brand_ratio > 0 and signals.brand_mention_count > signals.total_competitor_mentions():
        sub = _detect_partner_subcategory(signals)
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[sub],
            subcategory=sub,
            confidence=MED_CONFIDENCE,
            stage_used=2,
            signals=base_signals,
            reasoning="Mixed redirects, but brand-mention dominance; "
            + ", ".join(reason_parts),
            reason_code=ReasonCode.ALG_BRAND_MENTION_DOMINANCE,
        )

    # Rule 5 — brand named but redirects go elsewhere → text-bait hijacker.
    if signals.brand_mention_count > 0 and brand_ratio == 0 and comp_ratio > 0:
        return Classification(
            category=SUBCATEGORY_TO_CATEGORY[Subcategory.HIJACKER_AFFILIATE_TO_OTHERS],
            subcategory=Subcategory.HIJACKER_AFFILIATE_TO_OTHERS,
            confidence=MED_CONFIDENCE,
            stage_used=2,
            signals=base_signals,
            reasoning="Brand mentioned but redirects go elsewhere → text-bait hijacker; "
            + ", ".join(reason_parts),
            reason_code=ReasonCode.ALG_TEXT_BAIT_HIJACKER,
        )

    # Fallback — ambiguous; LOW_CONFIDENCE will route this to stage 3.
    return Classification(
        category=SUBCATEGORY_TO_CATEGORY[Subcategory.INFO_OTHER],
        subcategory=Subcategory.INFO_OTHER,
        confidence=LOW_CONFIDENCE,
        stage_used=2,
        signals=base_signals,
        reasoning="Ambiguous signals — recommend LLM arbiter; "
        + ", ".join(reason_parts),
        reason_code=ReasonCode.ALG_AMBIGUOUS,
    )
