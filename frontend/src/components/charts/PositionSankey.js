import { jsx as _jsx } from "react/jsx-runtime";
import { useMemo } from "react";
import { ResponsiveContainer, Sankey, Tooltip } from "recharts";
import { useTranslation } from "react-i18next";
import { EmptyState } from "../ui";
import { CATEGORY_COLOR, CATEGORY_ORDER, categoryI18nKey, isCategory, } from "../../lib/categories";
export function PositionSankey({ results }) {
    const { t } = useTranslation();
    const data = useMemo(() => {
        const positions = Array.from(new Set(results.map((r) => r.position))).sort((a, b) => a - b);
        const nodes = [
            ...positions.map((p) => ({ name: `#${p}` })),
            ...CATEGORY_ORDER.map((c) => ({ name: t(categoryI18nKey(c)), color: CATEGORY_COLOR[c] })),
        ];
        const posIdx = new Map(positions.map((p, i) => [p, i]));
        const catIdx = new Map(CATEGORY_ORDER.map((c, i) => [c, positions.length + i]));
        const links = [];
        for (const r of results) {
            const src = posIdx.get(r.position);
            if (src === undefined)
                continue;
            const tgt = isCategory(r.category) ? catIdx.get(r.category) : undefined;
            if (tgt === undefined)
                continue;
            links.push({
                source: src,
                target: tgt,
                value: 1,
                color: CATEGORY_COLOR[r.category],
            });
        }
        return { nodes, links };
    }, [results, t]);
    if (results.length === 0)
        return _jsx(EmptyState, { title: t("snapshot.no_snapshots") });
    return (_jsx(ResponsiveContainer, { width: "100%", height: Math.max(220, results.length * 24), children: _jsx(Sankey, { data: data, nodePadding: 16, nodeWidth: 10, margin: { top: 8, right: 80, bottom: 8, left: 32 }, link: { stroke: "var(--border)" }, children: _jsx(Tooltip, { contentStyle: {
                    background: "var(--card-elevated)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                } }) }) }));
}
