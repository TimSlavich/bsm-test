"""4 categories × 16 subcategories. Single source of truth for the classifier."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    OFFICIAL = "official"
    AFFILIATE_TO_BRAND = "affiliate_to_brand"
    COMPETITOR_HIJACKING = "competitor_hijacking"
    INFORMATIONAL = "informational"


class Subcategory(str, Enum):
    # 1. Official
    OFFICIAL_APEX = "official_apex"
    OFFICIAL_LOCALIZED = "official_localized"
    OFFICIAL_PROMO_LANDING = "official_promo_landing"
    OFFICIAL_OWNED_MEDIA = "official_owned_media"
    # 2. Affiliate-to-Brand
    AFFILIATE_DEDICATED_REVIEW = "affiliate_dedicated_review"
    AFFILIATE_LISTICLE = "affiliate_listicle"
    AFFILIATE_BONUS_PROMO = "affiliate_bonus_promo"
    AFFILIATE_COMPARISON = "affiliate_comparison"
    # 3. Competitor-Hijacking
    HIJACKER_DIRECT_COMPETITOR = "hijacker_direct_competitor"
    HIJACKER_AFFILIATE_TO_OTHERS = "hijacker_affiliate_to_others"
    HIJACKER_BLACKHAT_SCAM = "hijacker_blackhat_scam"
    # 4. Informational / Neutral
    INFO_NEWS = "info_news"
    INFO_FORUM_SOCIAL = "info_forum_social"
    INFO_REGULATOR = "info_regulator"
    INFO_GAMBLING_PORTAL = "info_gambling_portal"
    INFO_OTHER = "info_other"


SUBCATEGORY_TO_CATEGORY: dict[Subcategory, Category] = {
    Subcategory.OFFICIAL_APEX: Category.OFFICIAL,
    Subcategory.OFFICIAL_LOCALIZED: Category.OFFICIAL,
    Subcategory.OFFICIAL_PROMO_LANDING: Category.OFFICIAL,
    Subcategory.OFFICIAL_OWNED_MEDIA: Category.OFFICIAL,
    Subcategory.AFFILIATE_DEDICATED_REVIEW: Category.AFFILIATE_TO_BRAND,
    Subcategory.AFFILIATE_LISTICLE: Category.AFFILIATE_TO_BRAND,
    Subcategory.AFFILIATE_BONUS_PROMO: Category.AFFILIATE_TO_BRAND,
    Subcategory.AFFILIATE_COMPARISON: Category.AFFILIATE_TO_BRAND,
    Subcategory.HIJACKER_DIRECT_COMPETITOR: Category.COMPETITOR_HIJACKING,
    Subcategory.HIJACKER_AFFILIATE_TO_OTHERS: Category.COMPETITOR_HIJACKING,
    Subcategory.HIJACKER_BLACKHAT_SCAM: Category.COMPETITOR_HIJACKING,
    Subcategory.INFO_NEWS: Category.INFORMATIONAL,
    Subcategory.INFO_FORUM_SOCIAL: Category.INFORMATIONAL,
    Subcategory.INFO_REGULATOR: Category.INFORMATIONAL,
    Subcategory.INFO_GAMBLING_PORTAL: Category.INFORMATIONAL,
    Subcategory.INFO_OTHER: Category.INFORMATIONAL,
}


class ReasonCode(str, Enum):
    """Stable identifier for the rule that produced a Classification.

    Surfaced to the API in :class:`Classification.reason_code`; the frontend
    maps each code to a localized human-readable string. Keep these strings
    stable — clients rely on them.
    """

    # Stage 1 — whitelist
    WHITELIST_OFFICIAL = "whitelist_official"
    WHITELIST_PARTNER = "whitelist_partner"
    WHITELIST_COMPETITOR = "whitelist_competitor"
    WHITELIST_INFO_SEED = "whitelist_info_seed"
    # Stage 2 — algorithm rules
    ALG_SCHEMA_REVIEW_BRAND = "alg_schema_review_brand"
    ALG_NO_AFFILIATE_INFO = "alg_no_affiliate_info"
    ALG_NO_AFFILIATE_NEWS = "alg_no_affiliate_news"
    ALG_BRAND_REDIRECT_MAJORITY = "alg_brand_redirect_majority"
    ALG_COMPETITOR_REDIRECT_MAJORITY = "alg_competitor_redirect_majority"
    ALG_BRAND_MENTION_DOMINANCE = "alg_brand_mention_dominance"
    ALG_TEXT_BAIT_HIJACKER = "alg_text_bait_hijacker"
    ALG_FAKE_OFFICIAL_MIMICRY = "alg_fake_official_mimicry"
    ALG_AMBIGUOUS = "alg_ambiguous"
    # Pipeline
    PIPELINE_FETCH_FAILED = "pipeline_fetch_failed"
    PIPELINE_WHITELIST_ONLY = "pipeline_whitelist_only"
    # Stage 3
    LLM_ARBITER = "llm_arbiter"
    LLM_FALLBACK = "llm_fallback"


@dataclass(frozen=True)
class Classification:
    category: Category
    subcategory: Subcategory
    confidence: float  # 0.0 – 1.0
    stage_used: int  # 1, 2, or 3
    signals: dict[str, object]
    reasoning: str = ""
    reason_code: ReasonCode | None = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0,1], got {self.confidence}")
        if SUBCATEGORY_TO_CATEGORY[self.subcategory] != self.category:
            raise ValueError(
                f"subcategory {self.subcategory} does not belong to category {self.category}"
            )
        if self.stage_used not in (1, 2, 3):
            raise ValueError(f"stage_used must be 1, 2 or 3, got {self.stage_used}")


# Dashboard palette (kept consistent across charts).
CATEGORY_COLOR: dict[Category, str] = {
    Category.OFFICIAL: "#16a34a",            # green-600
    Category.AFFILIATE_TO_BRAND: "#2563eb",  # blue-600
    Category.COMPETITOR_HIJACKING: "#dc2626",  # red-600
    Category.INFORMATIONAL: "#71717a",       # zinc-500
}
