import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useTranslation } from "react-i18next";
import { Favicon, EmptyState } from "../ui";
import { CATEGORY_BG, CATEGORY_COLOR, CATEGORY_FG, categoryI18nKey, isCategory, } from "../../lib/categories";
/**
 * A horizontal strip of N cells, one per SERP position. Each cell is
 * colour-coded by the category that domain landed in, so the user can
 * read "who owns each rank" at a glance — much clearer than a Sankey
 * for a top-10 dataset.
 */
export function PositionLineup({ results }) {
    const { t } = useTranslation();
    if (results.length === 0) {
        return _jsx(EmptyState, { title: t("snapshot.no_snapshots") });
    }
    const sorted = [...results].sort((a, b) => a.position - b.position);
    return (_jsxs("div", { className: "lineup", children: [_jsx("div", { className: "lineup__row", children: sorted.map((r) => {
                    const cat = isCategory(r.category) ? r.category : null;
                    const bg = cat ? CATEGORY_BG[cat] : "var(--bg-subtle)";
                    const fg = cat ? CATEGORY_FG[cat] : "var(--text-muted)";
                    const accent = cat ? CATEGORY_COLOR[cat] : "var(--text-subtle)";
                    return (_jsxs("div", { className: "lineup__cell", style: { background: bg, color: fg }, title: `#${r.position} · ${r.domain} · ${t(categoryI18nKey(r.category))}`, children: [_jsxs("div", { className: "lineup__pos", children: ["#", r.position] }), _jsx(Favicon, { domain: r.domain, size: 20, className: "lineup__favicon" }), _jsx("div", { className: "lineup__domain", children: r.domain }), _jsx("div", { className: "lineup__bar", style: { background: accent } })] }, r.position));
                }) }), _jsx(Legend, {})] }));
}
function Legend() {
    const { t } = useTranslation();
    const items = [
        { key: "official", label: t("categories.official") },
        { key: "affiliate_to_brand", label: t("categories.affiliate_to_brand") },
        { key: "competitor_hijacking", label: t("categories.competitor_hijacking") },
        { key: "informational", label: t("categories.informational") },
    ];
    return (_jsx("div", { className: "lineup__legend", "aria-hidden": true, children: items.map((it) => (_jsxs("span", { className: "lineup__legend-item", children: [_jsx("span", { className: "lineup__legend-dot", style: { background: CATEGORY_COLOR[it.key] } }), it.label] }, it.key))) }));
}
