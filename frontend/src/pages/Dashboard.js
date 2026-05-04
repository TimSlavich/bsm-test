import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, InfoPopover, Select, Skeleton, } from "../components/ui";
import { CategoryDonut } from "../components/charts/CategoryDonut";
import { PositionLineup } from "../components/charts/PositionLineup";
import { StageBreakdown } from "../components/charts/StageBreakdown";
import { TrendChart } from "../components/charts/TrendChart";
import { ActivityFeed } from "../features/dashboard/ActivityFeed";
import { HealthCard } from "../features/dashboard/HealthCard";
import { ScanForm } from "../features/scan/ScanForm";
import { ScanProgress } from "../features/scan/ScanProgress";
import { useScanStream } from "../features/scan/useScanStream";
import { ValidationDialog } from "../features/scan/ValidationDialog";
import { DomainTable } from "../features/snapshot/DomainTable";
import { DrilldownModal } from "../features/snapshot/DrilldownModal";
import { SnapshotPicker } from "../features/snapshot/SnapshotPicker";
import { fetchSnapshotResults, fetchSnapshots, fetchTrend, validateScanInput, } from "../lib/api";
import { formatDate } from "../lib/format";
const DEFAULT_FORM = {
    brand_slug: "starcasino",
    keyword: "starcasino",
    geo: "NL",
    top_n: 10,
};
export function useDashboard() {
    const { t, i18n } = useTranslation();
    const lang = i18n.resolvedLanguage ?? "en";
    const qc = useQueryClient();
    const [form, setForm] = useState(DEFAULT_FORM);
    const { state: scanState, run: runScan } = useScanStream();
    const [drilldown, setDrilldown] = useState(null);
    const [selectedSnapshot, setSelectedSnapshot] = useState(null);
    const [trendDays, setTrendDays] = useState(14);
    const [scanProblems, setScanProblems] = useState([]);
    // Pre-flight validate, then open the SSE stream. EventSource can't
    // read 400 bodies, so problems must be surfaced via the validate
    // endpoint before we ever open the stream. Problems are shown in a
    // single friendly modal — no inline tech captions under each field.
    const handleSubmit = async () => {
        try {
            const problems = await validateScanInput(form);
            setScanProblems(problems);
            if (problems.length > 0)
                return;
            runScan(form);
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : "Validation request failed";
            toast.error(msg);
        }
    };
    // Clear errors as soon as the user edits the form.
    const handleFormChange = (next) => {
        setForm(next);
        if (scanProblems.length > 0)
            setScanProblems([]);
    };
    // Pass field codes to ScanForm only for the data-invalid border highlight;
    // the actual messages live in the modal so the form stays uncluttered.
    const invalidFields = scanProblems.reduce((acc, p) => ({ ...acc, [p.field]: "" }), {});
    const snapshotsQ = useQuery({
        queryKey: ["snapshots", form.brand_slug],
        queryFn: () => fetchSnapshots(form.brand_slug, 30),
        enabled: Boolean(form.brand_slug),
        staleTime: 15_000,
    });
    const trendQ = useQuery({
        queryKey: ["trend", form.brand_slug, trendDays],
        queryFn: () => fetchTrend(form.brand_slug, trendDays),
        enabled: Boolean(form.brand_slug),
        staleTime: 15_000,
    });
    const resultsQ = useQuery({
        queryKey: ["snapshot-results", selectedSnapshot],
        queryFn: () => selectedSnapshot ? fetchSnapshotResults(selectedSnapshot) : Promise.resolve([]),
        enabled: Boolean(selectedSnapshot),
        staleTime: 60_000,
    });
    // Reset selectedSnapshot when the brand changes — otherwise the picker
    // holds the previous brand's id and resultsQ 404s on a snapshot that
    // doesn't belong to the now-selected brand.
    useEffect(() => {
        setSelectedSnapshot(null);
    }, [form.brand_slug]);
    useEffect(() => {
        if (selectedSnapshot === null && snapshotsQ.data && snapshotsQ.data.length > 0) {
            setSelectedSnapshot(snapshotsQ.data[0].snapshot_id);
        }
    }, [snapshotsQ.data, selectedSnapshot]);
    useEffect(() => {
        if (scanState.status === "complete" && scanState.snapshotId !== null) {
            setSelectedSnapshot(scanState.snapshotId);
            qc.invalidateQueries({ queryKey: ["snapshots", form.brand_slug] });
            qc.invalidateQueries({ queryKey: ["trend", form.brand_slug] });
            qc.invalidateQueries({ queryKey: ["snapshot-results", scanState.snapshotId] });
            toast.success(t("progress.snapshot_captured", { id: scanState.snapshotId }));
        }
        else if (scanState.status === "error") {
            toast.error(t("progress.error", { message: scanState.error ?? "" }));
        }
    }, [scanState.status, scanState.snapshotId, scanState.error, qc, form.brand_slug, t]);
    const results = resultsQ.data ?? [];
    const activeSnapshot = snapshotsQ.data?.find((s) => s.snapshot_id === selectedSnapshot) ?? null;
    const latestSnapshot = snapshotsQ.data?.[0] ?? null;
    const hasSnapshots = (snapshotsQ.data?.length ?? 0) > 0;
    const trendOptions = useMemo(() => [
        { value: "7", label: t("charts.trend.range_7") },
        { value: "14", label: t("charts.trend.range_14") },
        { value: "30", label: t("charts.trend.range_30") },
        { value: "90", label: t("charts.trend.range_90") },
    ], [t]);
    const sidebar = (_jsxs(_Fragment, { children: [_jsxs("section", { className: "sidebar-section", children: [_jsx("h3", { className: "sidebar-section__title", children: t("actions.run_scan") }), _jsx(ScanForm, { values: form, onChange: handleFormChange, onSubmit: handleSubmit, isRunning: scanState.status === "running", errors: invalidFields })] }), _jsxs("section", { className: "sidebar-section", children: [_jsx("h3", { className: "sidebar-section__title", children: t("snapshot.picker_label") }), _jsx(SnapshotPicker, { snapshots: snapshotsQ.data ?? [], selected: selectedSnapshot, onSelect: setSelectedSnapshot })] })] }));
    const main = (_jsxs("div", { style: { display: "flex", flexDirection: "column", gap: 16 }, children: [scanState.status !== "idle" && _jsx(ScanProgress, { state: scanState }), !hasSnapshots && scanState.status === "idle" ? (_jsx(Card, { children: _jsx(CardBody, { children: _jsx(EmptyState, { icon: _jsx(Search, { size: 24 }), title: t("empty.title"), description: t("empty.body", { keyword: form.keyword, geo: form.geo }), action: _jsx(Button, { leftIcon: _jsx(Sparkles, { size: 14 }), size: "lg", onClick: handleSubmit, children: t("empty.cta") }) }) }) })) : (_jsxs(_Fragment, { children: [activeSnapshot && (_jsx("div", { className: "snapshot-meta", children: t("snapshot.showing", {
                            id: activeSnapshot.snapshot_id,
                            keyword: activeSnapshot.keyword,
                            geo: activeSnapshot.geo,
                            captured: formatDate(activeSnapshot.captured_at, lang),
                        }) })), _jsxs("div", { className: "grid grid--two", children: [_jsxs(Card, { children: [_jsx(CardHeader, { title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 6 }, children: [t("charts.distribution.title"), _jsx(InfoPopover, { title: t("charts.distribution.title"), children: t("charts.distribution.info") })] }) }), _jsx(CardBody, { children: resultsQ.isLoading ? (_jsx(Skeleton, { width: "100%", height: 220 })) : (_jsx(CategoryDonut, { results: results })) })] }), _jsxs(Card, { children: [_jsx(CardHeader, { title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 6 }, children: [t("charts.stage_breakdown.title"), _jsx(InfoPopover, { title: t("charts.stage_breakdown.title"), children: t("charts.stage_breakdown.info") })] }) }), _jsx(CardBody, { children: resultsQ.isLoading ? (_jsx(Skeleton, { width: "100%", height: 140 })) : (_jsx(StageBreakdown, { results: results })) })] })] }), _jsxs(Card, { children: [_jsx(CardHeader, { title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 6 }, children: [t("charts.sankey.title"), _jsx(InfoPopover, { title: t("charts.sankey.title"), children: t("charts.sankey.info") })] }) }), _jsx(CardBody, { children: resultsQ.isLoading ? (_jsx(Skeleton, { width: "100%", height: 140 })) : (_jsx(PositionLineup, { results: results })) })] }), _jsxs(Card, { children: [_jsx(CardHeader, { title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 6 }, children: [t("charts.trend.title"), _jsx(InfoPopover, { title: t("charts.trend.title"), children: t("charts.trend.info") })] }), action: _jsx(Select, { value: String(trendDays), onChange: (v) => setTrendDays(Number(v)), options: trendOptions, size: "sm", ariaLabel: t("charts.trend.title") }) }), _jsx(CardBody, { children: trendQ.isLoading ? (_jsx(Skeleton, { width: "100%", height: 260 })) : (_jsx(TrendChart, { data: trendQ.data ?? [] })) })] }), _jsxs(Card, { children: [_jsx(CardHeader, { title: _jsxs("span", { style: { display: "inline-flex", alignItems: "center", gap: 6 }, children: [t("table.headers.domain"), " ", _jsx(Badge, { tone: "muted", children: results.length })] }) }), _jsx(CardBody, { children: resultsQ.isLoading ? (_jsx(Skeleton, { width: "100%", height: 400 })) : (_jsx(DomainTable, { results: results, onRowClick: setDrilldown })) })] })] })), _jsx(DrilldownModal, { result: drilldown, onClose: () => setDrilldown(null) }), _jsx(ValidationDialog, { problems: scanProblems, onClose: () => setScanProblems([]) })] }));
    const rail = (_jsxs("div", { style: { display: "flex", flexDirection: "column", gap: 16 }, children: [_jsx(HealthCard, { latestSnapshot: latestSnapshot }), _jsx(ActivityFeed, { snapshots: snapshotsQ.data ?? [] })] }));
    return { sidebar, main, rail };
}
export function useDashboardSnapshots(brand) {
    return useQuery({
        queryKey: ["snapshots", brand],
        queryFn: () => fetchSnapshots(brand, 30),
        enabled: Boolean(brand),
        staleTime: 15_000,
    });
}
