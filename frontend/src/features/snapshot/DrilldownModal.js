import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { ExternalLink, Layers, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Badge, Modal } from "../../components/ui";
import { CATEGORY_BG, CATEGORY_FG, categoryI18nKey, isCategory, subcategoryI18nKey, } from "../../lib/categories";
import { Favicon } from "../../components/ui";
export function DrilldownModal({ result, onClose }) {
    const { t } = useTranslation();
    if (!result)
        return null;
    const cat = isCategory(result.category) ? result.category : null;
    const signals = parseSignals(result);
    const reasoning = localizedReasoning(result, t);
    return (_jsx(Modal, { open: Boolean(result), onClose: onClose, title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 12 }, children: [_jsx(Favicon, { domain: result.domain, size: 28 }), _jsx("span", { children: result.domain })] }), description: result.title, size: "md", children: _jsxs("div", { className: "drilldown", children: [_jsxs("div", { className: "drilldown__tags", children: [_jsx(Badge, { style: cat ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] } : undefined, children: t(categoryI18nKey(result.category)) }), _jsx(Badge, { tone: "muted", children: t(subcategoryI18nKey(result.subcategory)) }), _jsxs(Badge, { tone: "muted", children: [_jsx(Layers, { size: 11, style: { marginRight: 4 } }), t("drilldown.stage_label", { n: result.stage_used })] }), _jsxs(Badge, { tone: "muted", children: [_jsx(Sparkles, { size: 11, style: { marginRight: 4 } }), t("drilldown.confidence_label", {
                                    pct: Math.round(result.confidence * 100),
                                })] })] }), reasoning && (_jsxs("section", { className: "drilldown__section", children: [_jsx("h4", { className: "drilldown__section-title", children: t("drilldown.reasoning_title") }), _jsx("p", { className: "drilldown__reasoning", children: reasoning })] })), _jsxs("section", { className: "drilldown__section", children: [_jsx("h4", { className: "drilldown__section-title", children: t("drilldown.signals_title") }), _jsx(SignalsGrid, { signals: signals })] }), _jsxs("section", { className: "drilldown__section", children: [_jsx("h4", { className: "drilldown__section-title", children: t("drilldown.url_title") }), _jsxs("a", { href: result.url, target: "_blank", rel: "noreferrer", className: "drilldown__url", children: [_jsx("span", { children: result.url }), _jsx(ExternalLink, { size: 14 })] })] })] }) }));
}
function SignalsGrid({ signals }) {
    const { t } = useTranslation();
    const cards = [];
    if (typeof signals.affiliate_links === "number") {
        cards.push({
            key: "affiliate_links",
            value: String(signals.affiliate_links),
            label: t("drilldown.metric.affiliate_links"),
            description: t("drilldown.metric.affiliate_links_desc"),
            tone: signals.affiliate_links === 0 ? "neutral" : "warn",
        });
    }
    if (typeof signals.brand_redirect_ratio === "number") {
        cards.push({
            key: "brand_redirect_ratio",
            value: pct(signals.brand_redirect_ratio),
            label: t("drilldown.metric.brand_redirect_ratio"),
            description: t("drilldown.metric.brand_redirect_ratio_desc"),
            tone: signals.brand_redirect_ratio >= 0.6 ? "good" : "neutral",
        });
    }
    if (typeof signals.competitor_redirect_ratio === "number") {
        cards.push({
            key: "competitor_redirect_ratio",
            value: pct(signals.competitor_redirect_ratio),
            label: t("drilldown.metric.competitor_redirect_ratio"),
            description: t("drilldown.metric.competitor_redirect_ratio_desc"),
            tone: signals.competitor_redirect_ratio >= 0.6 ? "bad" : "neutral",
        });
    }
    if (typeof signals.brand_mentions === "number") {
        cards.push({
            key: "brand_mentions",
            value: String(signals.brand_mentions),
            label: t("drilldown.metric.brand_mentions"),
            description: t("drilldown.metric.brand_mentions_desc"),
            tone: "neutral",
        });
    }
    if (typeof signals.competitor_mentions === "number") {
        cards.push({
            key: "competitor_mentions",
            value: String(signals.competitor_mentions),
            label: t("drilldown.metric.competitor_mentions"),
            description: t("drilldown.metric.competitor_mentions_desc"),
            tone: signals.competitor_mentions > 0 ? "warn" : "neutral",
        });
    }
    if (cards.length === 0 && !signals.schema_types?.length && !signals.schema_review_target) {
        return _jsx("p", { className: "drilldown__muted", children: t("drilldown.no_signals") });
    }
    return (_jsxs(_Fragment, { children: [cards.length > 0 && (_jsx("div", { className: "drilldown__metrics", children: cards.map((c) => (_jsxs("div", { className: "metric", "data-tone": c.tone, children: [_jsx("div", { className: "metric__value", children: c.value }), _jsx("div", { className: "metric__label", children: c.label }), c.description && _jsx("div", { className: "metric__desc", children: c.description })] }, c.key))) })), (signals.schema_types?.length || signals.schema_review_target) && (_jsxs("dl", { className: "drilldown__meta", children: [signals.schema_types && signals.schema_types.length > 0 && (_jsxs(_Fragment, { children: [_jsx("dt", { children: t("drilldown.metric.schema_types") }), _jsx("dd", { children: Array.from(new Set(signals.schema_types)).map((s) => (_jsx(Badge, { tone: "muted", style: { marginRight: 6 }, children: s }, s))) })] })), signals.schema_review_target && (_jsxs(_Fragment, { children: [_jsx("dt", { children: t("drilldown.metric.schema_review_target") }), _jsx("dd", { children: signals.schema_review_target })] })), signals.has_tracker !== undefined && (_jsxs(_Fragment, { children: [_jsx("dt", { children: t("drilldown.metric.has_tracker") }), _jsx("dd", { children: signals.has_tracker
                                    ? t("drilldown.metric.yes")
                                    : t("drilldown.metric.no") })] }))] }))] }));
}
function pct(n) {
    return `${Math.round(n * 100)}%`;
}
function localizedReasoning(result, t) {
    // Backend emits a stable ``reason_code`` enum identifying the rule that
    // produced the verdict. We map it to a localized template so the user
    // sees text in their language instead of the backend's English string.
    if (!result.reason_code)
        return "";
    const key = `drilldown.reason.${result.reason_code}`;
    const translated = t(key, { domain: result.domain });
    return translated === key ? "" : translated;
}
function asNumber(v) {
    if (typeof v === "number" && Number.isFinite(v))
        return v;
    if (typeof v === "string") {
        const n = Number(v);
        if (Number.isFinite(n))
            return n;
    }
    return undefined;
}
function asStringArray(v) {
    if (Array.isArray(v))
        return v.filter((x) => typeof x === "string");
    return undefined;
}
function parseSignals(result) {
    // Backend now ships structured signals on ``ResultItem.signals`` (mirrors
    // the ``DomainClassification.signals`` JSON column). Read fields with
    // defensive type coercion — the dict is heterogeneous by design.
    const raw = result.signals ?? {};
    const out = {};
    out.affiliate_links = asNumber(raw.affiliate_links);
    out.brand_redirect_ratio = asNumber(raw.brand_redirect_ratio);
    out.competitor_redirect_ratio = asNumber(raw.competitor_redirect_ratio);
    out.brand_mentions = asNumber(raw.brand_mentions);
    out.competitor_mentions = asNumber(raw.competitor_mentions);
    out.schema_types = asStringArray(raw.schema_types);
    if (typeof raw.schema_review_target === "string") {
        out.schema_review_target = raw.schema_review_target;
    }
    else if (raw.schema_review_target === null) {
        out.schema_review_target = null;
    }
    if (typeof raw.has_tracker === "boolean")
        out.has_tracker = raw.has_tracker;
    return out;
}
