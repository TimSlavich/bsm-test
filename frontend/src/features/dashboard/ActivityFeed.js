import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { CheckCircle2, Search } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Card, CardBody, CardHeader, EmptyState } from "../../components/ui";
import { formatRelativeTime } from "../../lib/format";
export function ActivityFeed({ snapshots }) {
    const { t, i18n } = useTranslation();
    const lang = i18n.resolvedLanguage ?? "en";
    return (_jsxs(Card, { children: [_jsx(CardHeader, { title: t("activity.title") }), _jsx(CardBody, { children: snapshots.length === 0 ? (_jsx(EmptyState, { icon: _jsx(Search, { size: 20 }), title: t("activity.empty") })) : (_jsx("ul", { className: "activity", children: snapshots.slice(0, 8).map((s) => (_jsxs("li", { className: "activity__item", children: [_jsx("span", { className: "activity__icon", "aria-hidden": true, children: _jsx(CheckCircle2, { size: 12 }) }), _jsx("div", { className: "activity__title", children: t("activity.scan_completed", { id: s.snapshot_id, keyword: s.keyword }) }), _jsxs("div", { className: "activity__meta", children: [formatRelativeTime(s.captured_at, lang), " \u00B7 ", s.geo, " \u00B7", " ", t("snapshot.n_hits", { n: s.n_results })] })] }, s.snapshot_id))) })) })] }));
}
