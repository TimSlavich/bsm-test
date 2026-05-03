import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge, EmptyState, Favicon, Input } from "../../components/ui";
import { CATEGORY_BG, CATEGORY_COLOR, CATEGORY_FG, CATEGORY_ORDER, categoryI18nKey, isCategory, subcategoryI18nKey, } from "../../lib/categories";
import { cn } from "../../lib/cn";
export function DomainTable({ results, onRowClick }) {
    const { t } = useTranslation();
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("all");
    const counts = useMemo(() => {
        const map = new Map();
        for (const r of results) {
            if (isCategory(r.category)) {
                map.set(r.category, (map.get(r.category) ?? 0) + 1);
            }
        }
        return map;
    }, [results]);
    const filtered = useMemo(() => {
        const q = search.trim().toLowerCase();
        return results.filter((r) => {
            if (filter !== "all" && r.category !== filter)
                return false;
            if (q && !r.domain.toLowerCase().includes(q) && !r.title.toLowerCase().includes(q))
                return false;
            return true;
        });
    }, [results, filter, search]);
    if (results.length === 0) {
        return null;
    }
    return (_jsxs("div", { className: "domain-table-wrap", children: [_jsxs("div", { className: "domain-table-toolbar", children: [_jsx(Input, { value: search, onChange: (e) => setSearch(e.target.value), placeholder: t("table.search_placeholder"), leftIcon: _jsx(Search, { size: 14 }) }), _jsxs("div", { className: "domain-filter-chips", children: [_jsxs("button", { type: "button", className: "chip", "data-active": filter === "all" || undefined, onClick: () => setFilter("all"), children: [t("table.filter_all"), _jsx("span", { className: "chip__count", children: results.length })] }), CATEGORY_ORDER.map((c) => {
                                const n = counts.get(c) ?? 0;
                                return (_jsxs("button", { type: "button", className: "chip", "data-active": filter === c || undefined, onClick: () => setFilter(c), disabled: n === 0, style: filter === c ? { background: CATEGORY_COLOR[c], borderColor: CATEGORY_COLOR[c] } : undefined, children: [_jsx("span", { className: "chip__dot", style: { background: CATEGORY_COLOR[c] } }), t(categoryI18nKey(c)), _jsx("span", { className: "chip__count", children: n })] }, c));
                            })] })] }), filtered.length === 0 ? (_jsx(EmptyState, { title: t("table.no_match") })) : (_jsx("div", { style: { maxHeight: 540, overflow: "auto" }, children: _jsxs("table", { className: "domain-table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { className: "domain-table__pos", children: t("table.headers.position") }), _jsx("th", { children: t("table.headers.domain") }), _jsx("th", { children: t("table.headers.subcategory") }), _jsx("th", { children: t("table.headers.category") }), _jsx("th", { children: t("table.headers.confidence") }), _jsx("th", { children: t("table.headers.stage") })] }) }), _jsx("tbody", { children: filtered.map((r) => {
                                const cat = isCategory(r.category) ? r.category : null;
                                return (_jsxs("tr", { onClick: () => onRowClick?.(r), children: [_jsx("td", { className: "domain-table__pos", children: r.position }), _jsx("td", { children: _jsxs("div", { className: "domain-table__brand", children: [_jsx(Favicon, { domain: r.domain, size: 18 }), _jsxs("div", { style: { minWidth: 0 }, children: [_jsx("div", { className: "domain-table__domain", children: r.domain }), _jsx("div", { className: "domain-table__title", children: r.title })] })] }) }), _jsx("td", { children: t(subcategoryI18nKey(r.subcategory)) }), _jsx("td", { children: _jsx(Badge, { style: cat
                                                    ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] }
                                                    : undefined, children: t(categoryI18nKey(r.category)) }) }), _jsxs("td", { className: cn("domain-table__conf"), children: [(r.confidence * 100).toFixed(0), "%"] }), _jsx("td", { className: "domain-table__stage", children: t("stages.stage_short", { n: r.stage_used }) })] }, `${r.position}-${r.domain}`));
                            }) })] }) }))] }));
}
