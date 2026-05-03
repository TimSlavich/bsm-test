import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  InfoPopover,
  Select,
  type SelectOption,
  Skeleton,
} from "../components/ui";
import { CategoryDonut } from "../components/charts/CategoryDonut";
import { PositionLineup } from "../components/charts/PositionLineup";
import { StageBreakdown } from "../components/charts/StageBreakdown";
import { TrendChart } from "../components/charts/TrendChart";
import { ActivityFeed } from "../features/dashboard/ActivityFeed";
import { HealthCard } from "../features/dashboard/HealthCard";
import { ScanForm, type ScanFormValues } from "../features/scan/ScanForm";
import { ScanProgress } from "../features/scan/ScanProgress";
import { useScanStream } from "../features/scan/useScanStream";
import { DomainTable } from "../features/snapshot/DomainTable";
import { DrilldownModal } from "../features/snapshot/DrilldownModal";
import { SnapshotPicker } from "../features/snapshot/SnapshotPicker";
import {
  fetchSnapshotResults,
  fetchSnapshots,
  fetchTrend,
  type ResultItem,
} from "../lib/api";
import { formatDate } from "../lib/format";

const DEFAULT_FORM: ScanFormValues = {
  brand_slug: "starcasino",
  keyword: "starcasino",
  geo: "NL",
  top_n: 10,
};

export interface DashboardSlots {
  sidebar: React.ReactNode;
  main: React.ReactNode;
  rail: React.ReactNode;
}

export function useDashboard(): DashboardSlots {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "en";
  const qc = useQueryClient();

  const [form, setForm] = useState<ScanFormValues>(DEFAULT_FORM);
  const { state: scanState, run: runScan } = useScanStream();
  const [drilldown, setDrilldown] = useState<ResultItem | null>(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState<number | null>(null);
  const [trendDays, setTrendDays] = useState<number>(14);

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
    queryFn: () =>
      selectedSnapshot ? fetchSnapshotResults(selectedSnapshot) : Promise.resolve([]),
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
    } else if (scanState.status === "error") {
      toast.error(t("progress.error", { message: scanState.error ?? "" }));
    }
  }, [scanState.status, scanState.snapshotId, scanState.error, qc, form.brand_slug, t]);

  const results = resultsQ.data ?? [];
  const activeSnapshot = snapshotsQ.data?.find((s) => s.snapshot_id === selectedSnapshot) ?? null;
  const latestSnapshot = snapshotsQ.data?.[0] ?? null;
  const hasSnapshots = (snapshotsQ.data?.length ?? 0) > 0;

  const trendOptions: SelectOption[] = useMemo(
    () => [
      { value: "7", label: t("charts.trend.range_7") },
      { value: "14", label: t("charts.trend.range_14") },
      { value: "30", label: t("charts.trend.range_30") },
      { value: "90", label: t("charts.trend.range_90") },
    ],
    [t],
  );

  const sidebar = (
    <>
      <section className="sidebar-section">
        <h3 className="sidebar-section__title">{t("actions.run_scan")}</h3>
        <ScanForm
          values={form}
          onChange={setForm}
          onSubmit={() => runScan(form)}
          isRunning={scanState.status === "running"}
        />
      </section>

      <section className="sidebar-section">
        <h3 className="sidebar-section__title">{t("snapshot.picker_label")}</h3>
        <SnapshotPicker
          snapshots={snapshotsQ.data ?? []}
          selected={selectedSnapshot}
          onSelect={setSelectedSnapshot}
        />
      </section>
    </>
  );

  const main = (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {scanState.status !== "idle" && <ScanProgress state={scanState} />}

      {!hasSnapshots && scanState.status === "idle" ? (
        <Card>
          <CardBody>
            <EmptyState
              icon={<Search size={24} />}
              title={t("empty.title")}
              description={t("empty.body", { keyword: form.keyword, geo: form.geo })}
              action={
                <Button leftIcon={<Sparkles size={14} />} size="lg" onClick={() => runScan(form)}>
                  {t("empty.cta")}
                </Button>
              }
            />
          </CardBody>
        </Card>
      ) : (
        <>
          {activeSnapshot && (
            <div className="snapshot-meta">
              {t("snapshot.showing", {
                id: activeSnapshot.snapshot_id,
                keyword: activeSnapshot.keyword,
                geo: activeSnapshot.geo,
                captured: formatDate(activeSnapshot.captured_at, lang),
              })}
            </div>
          )}

          <div className="grid grid--two">
            <Card>
              <CardHeader
                title={
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                    {t("charts.distribution.title")}
                    <InfoPopover title={t("charts.distribution.title")}>
                      {t("charts.distribution.info")}
                    </InfoPopover>
                  </span>
                }
              />
              <CardBody>
                {resultsQ.isLoading ? (
                  <Skeleton width="100%" height={220} />
                ) : (
                  <CategoryDonut results={results} />
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader
                title={
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                    {t("charts.stage_breakdown.title")}
                    <InfoPopover title={t("charts.stage_breakdown.title")}>
                      {t("charts.stage_breakdown.info")}
                    </InfoPopover>
                  </span>
                }
              />
              <CardBody>
                {resultsQ.isLoading ? (
                  <Skeleton width="100%" height={140} />
                ) : (
                  <StageBreakdown results={results} />
                )}
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardHeader
              title={
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                  {t("charts.sankey.title")}
                  <InfoPopover title={t("charts.sankey.title")}>
                    {t("charts.sankey.info")}
                  </InfoPopover>
                </span>
              }
            />
            <CardBody>
              {resultsQ.isLoading ? (
                <Skeleton width="100%" height={140} />
              ) : (
                <PositionLineup results={results} />
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title={
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                  {t("charts.trend.title")}
                  <InfoPopover title={t("charts.trend.title")}>
                    {t("charts.trend.info")}
                  </InfoPopover>
                </span>
              }
              action={
                <Select
                  value={String(trendDays)}
                  onChange={(v) => setTrendDays(Number(v))}
                  options={trendOptions}
                  size="sm"
                  ariaLabel={t("charts.trend.title")}
                />
              }
            />
            <CardBody>
              {trendQ.isLoading ? (
                <Skeleton width="100%" height={260} />
              ) : (
                <TrendChart data={trendQ.data ?? []} />
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title={
                <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                  {t("table.headers.domain")} <Badge tone="muted">{results.length}</Badge>
                </span>
              }
            />
            <CardBody>
              {resultsQ.isLoading ? (
                <Skeleton width="100%" height={400} />
              ) : (
                <DomainTable results={results} onRowClick={setDrilldown} />
              )}
            </CardBody>
          </Card>
        </>
      )}

      <DrilldownModal result={drilldown} onClose={() => setDrilldown(null)} />
    </div>
  );

  const rail = (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <HealthCard latestSnapshot={latestSnapshot} />
      <ActivityFeed snapshots={snapshotsQ.data ?? []} />
    </div>
  );

  return { sidebar, main, rail };
}

export function useDashboardSnapshots(brand: string) {
  return useQuery({
    queryKey: ["snapshots", brand],
    queryFn: () => fetchSnapshots(brand, 30),
    enabled: Boolean(brand),
    staleTime: 15_000,
  });
}
