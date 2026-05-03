import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { EmptyState } from "../ui";
import { CATEGORY_BG, CATEGORY_COLOR, CATEGORY_FG, CATEGORY_ORDER, categoryI18nKey, } from "../../lib/categories";
import { cn } from "../../lib/cn";
/**
 * Horizontal stacked-bar + per-category rows.
 *
 * A 4-segment donut chart wastes screen space and can't show numbers
 * without overlapping; the bar+rows pattern reads at a glance even on
 * mobile and surfaces both raw counts and shares.
 */
export function CategoryDonut({ results }) {
    const { t } = useTranslation();
    const stats = useMemo(() => {
        const counts = new Map();
        for (const r of results) {
            if (CATEGORY_ORDER.includes(r.category)) {
                const c = r.category;
                counts.set(c, (counts.get(c) ?? 0) + 1);
            }
        }
        const total = results.length || 0;
        return CATEGORY_ORDER.map((c) => {
            const count = counts.get(c) ?? 0;
            return {
                key: c,
                label: t(categoryI18nKey(c)),
                count,
                percent: total > 0 ? (count / total) * 100 : 0,
            };
        });
    }, [results, t]);
    const total = results.length;
    const dominant = [...stats].sort((a, b) => b.count - a.count)[0];
    if (total === 0) {
        return _jsx(EmptyState, { title: t("snapshot.no_snapshots") });
    }
    return (_jsxs("div", { className: "dist", children: [_jsxs("div", { className: "dist__summary", children: [_jsx("div", { className: "dist__summary-value", children: total }), _jsx("div", { className: "dist__summary-label", children: t("table.headers.domain") }), dominant.count > 0 && (_jsxs("span", { className: "dist__summary-tag", style: {
                            background: CATEGORY_BG[dominant.key],
                            color: CATEGORY_FG[dominant.key],
                        }, children: [_jsx("span", { className: "dist__summary-dot", style: { background: CATEGORY_COLOR[dominant.key] }, "aria-hidden": true }), dominant.label, " \u00B7 ", dominant.percent.toFixed(0), "%"] }))] }), _jsx("div", { className: "dist__bar", role: "img", "aria-label": stats
                    .filter((s) => s.count > 0)
                    .map((s) => `${s.label} ${s.count} (${s.percent.toFixed(0)}%)`)
                    .join(", "), children: stats
                    .filter((s) => s.count > 0)
                    .map((s) => (_jsx("div", { className: "dist__bar-seg", style: {
                        flexBasis: `${s.percent}%`,
                        background: CATEGORY_COLOR[s.key],
                    }, title: `${s.label}: ${s.count} (${s.percent.toFixed(0)}%)` }, s.key))) }), _jsx("ul", { className: "dist__rows", children: stats.map((s) => (_jsxs("li", { className: cn("dist__row", s.count === 0 && "dist__row--zero"), children: [_jsx("span", { className: "dist__dot", style: { background: CATEGORY_COLOR[s.key] }, "aria-hidden": true }), _jsx("span", { className: "dist__label", children: s.label }), _jsx("span", { className: "dist__count", children: s.count }), _jsxs("span", { className: "dist__percent", children: [s.percent.toFixed(0), "%"] })] }, s.key))) })] }));
}
