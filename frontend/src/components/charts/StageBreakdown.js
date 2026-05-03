import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useTranslation } from "react-i18next";
import { EmptyState } from "../ui";
export function StageBreakdown({ results }) {
    const { t } = useTranslation();
    if (results.length === 0)
        return _jsx(EmptyState, { title: t("snapshot.no_snapshots") });
    const counts = {};
    for (const r of results)
        counts[r.stage_used] = (counts[r.stage_used] ?? 0) + 1;
    const total = results.length;
    return (_jsx("div", { className: "stage-bars", children: [1, 2, 3].map((stage) => {
            const c = counts[stage] ?? 0;
            const pct = total ? (c * 100) / total : 0;
            return (_jsxs("div", { className: "stage-bar__row", children: [_jsxs("div", { className: "stage-bar__head", children: [_jsxs("span", { children: [t("stages.stage_short", { n: stage }), " \u00B7 ", t(`stages.${stage}`)] }), _jsxs("span", { style: { color: "var(--text-muted)" }, children: [c, " (", pct.toFixed(0), "%)"] })] }), _jsx("div", { className: "stage-bar__track", children: _jsx("div", { className: "stage-bar__fill", style: { width: `${pct}%` } }) })] }, stage));
        }) }));
}
