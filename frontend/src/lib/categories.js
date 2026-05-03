/**
 * Single source of truth for category metadata: colors, sort order, i18n keys.
 *
 * Backend emits snake-case slugs (``official``, ``affiliate_to_brand``,
 * ``competitor_hijacking``, ``informational``); the UI maps them to
 * localized labels via i18n keys defined here.
 */
export const CATEGORY_ORDER = [
    "official",
    "affiliate_to_brand",
    "competitor_hijacking",
    "informational",
];
export const CATEGORY_COLOR = {
    official: "var(--category-official)",
    affiliate_to_brand: "var(--category-affiliate)",
    competitor_hijacking: "var(--category-hijacker)",
    informational: "var(--category-info)",
};
export const CATEGORY_BG = {
    official: "var(--category-official-bg)",
    affiliate_to_brand: "var(--category-affiliate-bg)",
    competitor_hijacking: "var(--category-hijacker-bg)",
    informational: "var(--category-info-bg)",
};
export const CATEGORY_FG = {
    official: "var(--category-official-fg)",
    affiliate_to_brand: "var(--category-affiliate-fg)",
    competitor_hijacking: "var(--category-hijacker-fg)",
    informational: "var(--category-info-fg)",
};
export function categoryI18nKey(c) {
    return `categories.${c}`;
}
export function subcategoryI18nKey(s) {
    return `subcategories.${s}`;
}
export function isCategory(v) {
    return CATEGORY_ORDER.includes(v);
}
