import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis, } from "recharts";
import { useTranslation } from "react-i18next";
import { EmptyState } from "../ui";
import { CATEGORY_COLOR, CATEGORY_ORDER, categoryI18nKey } from "../../lib/categories";
export function TrendChart({ data }) {
    const { t } = useTranslation();
    if (data.length < 2) {
        return (_jsx(EmptyState, { title: t("charts.trend.empty_title"), description: _jsxs(_Fragment, { children: [t("charts.trend.empty_hint"), _jsx("br", {}), _jsx("code", { children: "uv run seed-history --days 7" })] }) }));
    }
    return (_jsx(ResponsiveContainer, { width: "100%", height: 260, children: _jsxs(AreaChart, { data: data, margin: { top: 10, right: 16, bottom: 0, left: -10 }, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", vertical: false, stroke: "var(--border)" }), _jsx(XAxis, { dataKey: "date", tick: { fontSize: 11, fill: "var(--text-muted)" }, stroke: "var(--border)" }), _jsx(YAxis, { tick: { fontSize: 11, fill: "var(--text-muted)" }, stroke: "var(--border)", unit: "%", domain: [0, 100], allowDecimals: false }), _jsx(Tooltip, { contentStyle: {
                        background: "var(--card-elevated)",
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                        fontSize: 12,
                    } }), _jsx(Legend, { wrapperStyle: { fontSize: 12 }, iconType: "circle", iconSize: 8 }), CATEGORY_ORDER.map((c) => (_jsx(Area, { type: "monotone", stackId: "1", dataKey: c, name: t(categoryI18nKey(c)), stroke: CATEGORY_COLOR[c], fill: CATEGORY_COLOR[c], fillOpacity: 0.55 }, c)))] }) }));
}
