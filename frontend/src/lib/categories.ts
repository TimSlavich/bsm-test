/**
 * Single source of truth for category metadata: colors, sort order, i18n keys.
 *
 * Backend emits snake-case slugs (``official``, ``affiliate_to_brand``,
 * ``competitor_hijacking``, ``informational``); the UI maps them to
 * localized labels via i18n keys defined here.
 */

export type CategoryKey =
  | "official"
  | "affiliate_to_brand"
  | "competitor_hijacking"
  | "informational";

export type SubcategoryKey =
  | "official_apex"
  | "official_localized"
  | "official_promo_landing"
  | "official_owned_media"
  | "affiliate_dedicated_review"
  | "affiliate_listicle"
  | "affiliate_bonus_promo"
  | "affiliate_comparison"
  | "hijacker_direct_competitor"
  | "hijacker_affiliate_to_others"
  | "hijacker_blackhat_scam"
  | "info_news"
  | "info_forum_social"
  | "info_regulator"
  | "info_gambling_portal"
  | "info_other";

export const CATEGORY_ORDER: CategoryKey[] = [
  "official",
  "affiliate_to_brand",
  "competitor_hijacking",
  "informational",
];

export const CATEGORY_COLOR: Record<CategoryKey, string> = {
  official: "var(--category-official)",
  affiliate_to_brand: "var(--category-affiliate)",
  competitor_hijacking: "var(--category-hijacker)",
  informational: "var(--category-info)",
};

export const CATEGORY_BG: Record<CategoryKey, string> = {
  official: "var(--category-official-bg)",
  affiliate_to_brand: "var(--category-affiliate-bg)",
  competitor_hijacking: "var(--category-hijacker-bg)",
  informational: "var(--category-info-bg)",
};

export const CATEGORY_FG: Record<CategoryKey, string> = {
  official: "var(--category-official-fg)",
  affiliate_to_brand: "var(--category-affiliate-fg)",
  competitor_hijacking: "var(--category-hijacker-fg)",
  informational: "var(--category-info-fg)",
};

export function categoryI18nKey(c: string): string {
  return `categories.${c}` as const;
}

export function subcategoryI18nKey(s: string): string {
  return `subcategories.${s}` as const;
}

export function isCategory(v: string): v is CategoryKey {
  return CATEGORY_ORDER.includes(v as CategoryKey);
}
