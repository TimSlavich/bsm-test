import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowRight, ArrowUp, Minus, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge, Card, CardBody, CardHeader, EmptyState, Favicon, Field, Select } from "../../components/ui";
import { CATEGORY_BG, CATEGORY_FG, categoryI18nKey, isCategory, } from "../../lib/categories";
import { fetchSnapshotDiff } from "../../lib/api";
import { formatDate } from "../../lib/format";
export function DiffView({ snapshots }) {
    const { t, i18n } = useTranslation();
    const lang = i18n.resolvedLanguage ?? "en";
    // Two views over the same data, sorted by snapshot id (autoincrement):
    // - ``ascending`` (#1 → #N) drives sensible defaults (a = oldest, b = newest).
    // - ``descending`` (#N → #1) is what each dropdown displays — newest # at top.
    const ascending = useMemo(() => [...snapshots].sort((x, y) => x.snapshot_id - y.snapshot_id), [snapshots]);
    const descending = useMemo(() => [...ascending].reverse(), [ascending]);
    const validIds = useMemo(() => new Set(ascending.map((s) => s.snapshot_id)), [ascending]);
    const [a, setA] = useState(null);
    const [b, setB] = useState(null);
    // Re-sync selected ids whenever the underlying snapshot list changes —
    // prevents the picker from holding a stale id (e.g. after a DB reset)
    // and 404-ing the diff request indefinitely.
    useEffect(() => {
        if (ascending.length < 2) {
            setA(null);
            setB(null);
            return;
        }
        setA((prev) => prev !== null && validIds.has(prev) ? prev : ascending[0].snapshot_id);
        setB((prev) => prev !== null && validIds.has(prev)
            ? prev
            : ascending[ascending.length - 1].snapshot_id);
    }, [ascending, validIds]);
    const diff = useQuery({
        queryKey: ["diff", a, b],
        queryFn: () => fetchSnapshotDiff(a, b),
        enabled: a !== null &&
            b !== null &&
            a !== b &&
            validIds.has(a) &&
            validIds.has(b),
        retry: false,
        staleTime: 60_000,
    });
    // If the diff request 404s (e.g. ids became invalid mid-flight), reset
    // selection to the first/last snapshot so the next render submits a
    // valid request instead of looping the failed one.
    useEffect(() => {
        if (!diff.isError)
            return;
        if (ascending.length >= 2) {
            setA(ascending[0].snapshot_id);
            setB(ascending[ascending.length - 1].snapshot_id);
        }
    }, [diff.isError, ascending]);
    const opts = (excluded) => descending
        .filter((s) => s.snapshot_id !== excluded)
        .map((s) => ({
        value: String(s.snapshot_id),
        label: `#${s.snapshot_id} · ${formatDate(s.captured_at, lang)} · ${s.keyword}`,
    }));
    return (_jsxs("div", { className: "diff", children: [_jsxs(Card, { children: [_jsx(CardHeader, { title: t("diff.title"), description: t("diff.intro") }), _jsx(CardBody, { children: _jsxs("div", { className: "diff-controls", children: [_jsx(Field, { label: t("diff.snapshot_a"), children: _jsx(Select, { value: a ? String(a) : "", onChange: (v) => setA(Number(v)), options: opts(b), size: "md" }) }), _jsx(Field, { label: t("diff.snapshot_b"), children: _jsx(Select, { value: b ? String(b) : "", onChange: (v) => setB(Number(v)), options: opts(a), size: "md" }) })] }) })] }), a === null || b === null || a === b ? (_jsx(Card, { children: _jsx(CardBody, { children: _jsx(EmptyState, { title: t("diff.select_two") }) }) })) : diff.isLoading ? (_jsx(Card, { children: _jsx(CardBody, { children: t("common.loading") }) })) : diff.data ? (_jsxs(_Fragment, { children: [_jsx(DiffSection, { title: t("diff.added"), tone: "added", icon: _jsx(Plus, { size: 12 }), entries: diff.data.added, empty: t("diff.empty_added") }), _jsx(DiffSection, { title: t("diff.removed"), tone: "removed", icon: _jsx(Minus, { size: 12 }), entries: diff.data.removed, empty: t("diff.empty_removed") }), _jsx(MovedSection, { title: t("diff.moved"), entries: diff.data.moved, empty: t("diff.empty_moved") })] })) : null] }));
}
function DiffSection({ title, tone, icon, entries, empty, }) {
    const { t } = useTranslation();
    return (_jsxs(Card, { children: [_jsx(CardHeader, { title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 6 }, children: [icon, " ", title] }), action: _jsx(Badge, { tone: "muted", children: entries.length }) }), _jsx(CardBody, { children: entries.length === 0 ? (_jsx(EmptyState, { title: empty })) : (_jsx("ul", { className: "diff-section__list", children: entries.map((e) => {
                        const cat = isCategory(e.category) ? e.category : null;
                        return (_jsxs("li", { className: "diff-row", "data-tone": tone, children: [_jsxs("span", { className: "diff-row__pos", children: ["#", e.position] }), _jsxs("span", { style: { display: "flex", gap: 8, alignItems: "center", minWidth: 0 }, children: [_jsx(Favicon, { domain: e.domain, size: 16 }), _jsxs("span", { style: { minWidth: 0 }, children: [_jsx("div", { style: { fontWeight: 500 }, children: e.domain }), _jsx("div", { className: "domain-table__title", children: e.title })] })] }), _jsx(Badge, { style: cat ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] } : undefined, children: t(categoryI18nKey(e.category)) })] }, `${tone}-${e.domain}`));
                    }) })) })] }));
}
function MovedSection({ title, entries, empty }) {
    const { t } = useTranslation();
    return (_jsxs(Card, { children: [_jsx(CardHeader, { title: title, action: _jsx(Badge, { tone: "muted", children: entries.length }) }), _jsx(CardBody, { children: entries.length === 0 ? (_jsx(EmptyState, { title: empty })) : (_jsx("ul", { className: "diff-section__list", children: entries.map((e) => {
                        const catFrom = isCategory(e.category_from) ? e.category_from : null;
                        const catTo = isCategory(e.category_to) ? e.category_to : null;
                        const moveIcon = e.position_to < e.position_from ? _jsx(ArrowUp, { size: 12, color: "var(--success)" }) : e.position_to > e.position_from ? _jsx(ArrowDown, { size: 12, color: "var(--danger)" }) : _jsx(ArrowRight, { size: 12 });
                        return (_jsxs("li", { className: "diff-row", "data-tone": "moved", children: [_jsx("span", { className: "diff-row__pos", children: moveIcon }), _jsxs("span", { style: { display: "flex", gap: 8, alignItems: "center", minWidth: 0 }, children: [_jsx(Favicon, { domain: e.domain, size: 16 }), _jsxs("span", { style: { minWidth: 0 }, children: [_jsx("div", { style: { fontWeight: 500 }, children: e.domain }), _jsx("div", { className: "domain-table__title", children: t("diff.from_to", { from: `#${e.position_from}`, to: `#${e.position_to}` }) })] })] }), _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 6 }, children: [_jsx(Badge, { style: catFrom ? { background: CATEGORY_BG[catFrom], color: CATEGORY_FG[catFrom], opacity: 0.7 } : undefined, children: t(categoryI18nKey(e.category_from)) }), catFrom !== catTo && _jsx(ArrowRight, { size: 12 }), catFrom !== catTo && (_jsx(Badge, { style: catTo
                                                ? { background: CATEGORY_BG[catTo], color: CATEGORY_FG[catTo] }
                                                : undefined, children: t(categoryI18nKey(e.category_to)) }))] })] }, `moved-${e.domain}`));
                    }) })) })] }));
}
