import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AlertCircle, CheckCircle2, Search, Sparkles, Terminal } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Badge, Card, CardBody, CardHeader, Spinner } from "../../components/ui";
import { CATEGORY_BG, CATEGORY_FG, categoryI18nKey, isCategory, } from "../../lib/categories";
import { cn } from "../../lib/cn";
/**
 * Live cascade visualization. Reads the streaming event log and surfaces
 * (a) the current overall step, (b) per-domain classification rows as they
 * resolve, (c) terminal success / error state. Updates 30+ times per scan.
 */
export function ScanProgress({ state }) {
    const { t } = useTranslation();
    const isRunning = state.status === "running";
    const isError = state.status === "error";
    const isComplete = state.status === "complete";
    const lastClassifying = [...state.events].reverse().find((e) => e.type === "classifying");
    const classifiedCount = state.events.filter((e) => e.type === "classified").length;
    const totalCount = state.events.find((e) => e.type === "classify_phase_start")?.total;
    const phasePct = totalCount && totalCount > 0 ? (classifiedCount / totalCount) * 100 : 0;
    const fetchedSource = state.events.find((e) => e.type === "serp_fetched");
    const completeEvent = state.events.find((e) => e.type === "complete");
    const headline = (() => {
        if (isError)
            return t("progress.error", { message: state.error ?? "" });
        if (isComplete && completeEvent && completeEvent.type === "complete")
            return t("progress.complete", {
                snapshot_id: completeEvent.snapshot_id,
                n_results: completeEvent.n_results,
                source: completeEvent.source,
            });
        if (lastClassifying && lastClassifying.type === "classifying")
            return t("progress.classifying", {
                index: lastClassifying.index,
                total: lastClassifying.total,
                domain: lastClassifying.domain,
            });
        if (fetchedSource && fetchedSource.type === "serp_fetched")
            return t("progress.serp_fetched", { n: fetchedSource.n, source: fetchedSource.source });
        if (state.events.some((e) => e.type === "serp_fetch_start"))
            return t("progress.serp_fetch_start");
        return t("progress.scan_start");
    })();
    return (_jsxs(Card, { className: "scan-progress", children: [_jsx(CardHeader, { title: _jsxs("span", { className: "scan-progress__title", children: [isRunning && _jsx(Spinner, { size: 14 }), isComplete && _jsx(CheckCircle2, { size: 14, className: "scan-progress__title-icon scan-progress__title-icon--ok" }), isError && _jsx(AlertCircle, { size: 14, className: "scan-progress__title-icon scan-progress__title-icon--err" }), t("progress.title")] }) }), _jsxs(CardBody, { children: [_jsx("p", { className: "scan-progress__headline", children: headline }), _jsx("div", { className: "scan-progress__bar", "aria-hidden": true, children: _jsx("div", { className: cn("scan-progress__bar-fill", isError && "scan-progress__bar-fill--err", isComplete && "scan-progress__bar-fill--ok"), style: { width: `${isComplete ? 100 : phasePct}%` } }) }), _jsxs("ol", { className: "scan-progress__phases", children: [_jsx(Phase, { icon: _jsx(Search, { size: 14 }), label: t("progress.serp_fetch_start"), done: state.events.some((e) => e.type === "serp_fetched"), active: state.events.some((e) => e.type === "serp_fetch_start") && !state.events.some((e) => e.type === "serp_fetched") }), _jsx(Phase, { icon: _jsx(Sparkles, { size: 14 }), label: t("progress.classify_phase_start", { total: totalCount ?? "…" }), done: Boolean(totalCount && classifiedCount === totalCount), active: Boolean(totalCount && classifiedCount < totalCount), counter: totalCount ? `${classifiedCount}/${totalCount}` : undefined }), _jsx(Phase, { icon: _jsx(Terminal, { size: 14 }), label: t("progress.persist_done", { snapshot_id: completeEvent?.type === "complete" ? completeEvent.snapshot_id : "…" }), done: state.events.some((e) => e.type === "persist_done"), active: false })] }), state.events.filter((e) => e.type === "classified").length > 0 && (_jsx("ul", { className: "scan-progress__feed", "aria-live": "polite", children: state.events
                            .filter((e) => e.type === "classified")
                            .slice(-12)
                            .reverse()
                            .map((e) => {
                            const cat = isCategory(e.category) ? e.category : null;
                            return (_jsxs("li", { className: "scan-progress__row", children: [_jsxs("span", { className: "scan-progress__row-pos", children: ["#", e.index] }), _jsx("span", { className: "scan-progress__row-domain", children: e.domain }), _jsx(Badge, { style: cat ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] } : undefined, children: t(categoryI18nKey(e.category)) }), _jsx(Badge, { tone: "muted", children: t("stages.stage_short", { n: e.stage_used }) })] }, `${e.index}-${e.domain}`));
                        }) }))] })] }));
}
function Phase({ icon, label, active, done, counter, }) {
    return (_jsxs("li", { className: cn("scan-progress__phase", active && "scan-progress__phase--active", done && "scan-progress__phase--done"), children: [_jsx("span", { className: "scan-progress__phase-icon", children: done ? _jsx(CheckCircle2, { size: 14 }) : icon }), _jsx("span", { className: "scan-progress__phase-label", children: label }), counter && _jsx("span", { className: "scan-progress__phase-counter", children: counter })] }));
}
