import { AlertCircle, CheckCircle2, Search, Sparkles, Terminal } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge, Card, CardBody, CardHeader, Spinner } from "../../components/ui";
import {
  CATEGORY_BG,
  CATEGORY_FG,
  categoryI18nKey,
  isCategory,
  type CategoryKey,
} from "../../lib/categories";
import { cn } from "../../lib/cn";
import type { ScanState } from "./useScanStream";

interface ScanProgressProps {
  state: ScanState;
}

/**
 * Live cascade visualization. Reads the streaming event log and surfaces
 * (a) the current overall step, (b) per-domain classification rows as they
 * resolve, (c) terminal success / error state. Updates 30+ times per scan.
 */
export function ScanProgress({ state }: ScanProgressProps) {
  const { t } = useTranslation();

  const isRunning = state.status === "running";
  const isError = state.status === "error";
  const isComplete = state.status === "complete";

  const lastClassifying = [...state.events].reverse().find((e) => e.type === "classifying");
  const classifiedCount = state.events.filter((e) => e.type === "classified").length;
  const totalCount = state.events.find(
    (e): e is { type: "classify_phase_start"; total: number } =>
      e.type === "classify_phase_start",
  )?.total;
  const phasePct = totalCount && totalCount > 0 ? (classifiedCount / totalCount) * 100 : 0;

  const fetchedSource = state.events.find((e) => e.type === "serp_fetched");
  const completeEvent = state.events.find((e) => e.type === "complete");

  const headline = (() => {
    if (isError) return t("progress.error", { message: state.error ?? "" });
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

  return (
    <Card className="scan-progress">
      <CardHeader
        title={
          <span className="scan-progress__title">
            {isRunning && <Spinner size={14} />}
            {isComplete && <CheckCircle2 size={14} className="scan-progress__title-icon scan-progress__title-icon--ok" />}
            {isError && <AlertCircle size={14} className="scan-progress__title-icon scan-progress__title-icon--err" />}
            {t("progress.title")}
          </span>
        }
      />
      <CardBody>
        <p className="scan-progress__headline">{headline}</p>

        <div className="scan-progress__bar" aria-hidden>
          <div
            className={cn(
              "scan-progress__bar-fill",
              isError && "scan-progress__bar-fill--err",
              isComplete && "scan-progress__bar-fill--ok",
            )}
            style={{ width: `${isComplete ? 100 : phasePct}%` }}
          />
        </div>

        <ol className="scan-progress__phases">
          <Phase
            icon={<Search size={14} />}
            label={t("progress.serp_fetch_start")}
            done={state.events.some((e) => e.type === "serp_fetched")}
            active={state.events.some((e) => e.type === "serp_fetch_start") && !state.events.some((e) => e.type === "serp_fetched")}
          />
          <Phase
            icon={<Sparkles size={14} />}
            label={t("progress.classify_phase_start", { total: totalCount ?? "…" })}
            done={Boolean(totalCount && classifiedCount === totalCount)}
            active={Boolean(totalCount && classifiedCount < totalCount)}
            counter={totalCount ? `${classifiedCount}/${totalCount}` : undefined}
          />
          <Phase
            icon={<Terminal size={14} />}
            label={t("progress.persist_done", { snapshot_id: completeEvent?.type === "complete" ? completeEvent.snapshot_id : "…" })}
            done={state.events.some((e) => e.type === "persist_done")}
            active={false}
          />
        </ol>

        {state.events.filter((e) => e.type === "classified").length > 0 && (
          <ul className="scan-progress__feed" aria-live="polite">
            {state.events
              .filter((e): e is Extract<ScanState["events"][number], { type: "classified" }> => e.type === "classified")
              .slice(-12)
              .reverse()
              .map((e) => {
                const cat = isCategory(e.category) ? (e.category as CategoryKey) : null;
                return (
                  <li key={`${e.index}-${e.domain}`} className="scan-progress__row">
                    <span className="scan-progress__row-pos">#{e.index}</span>
                    <span className="scan-progress__row-domain">{e.domain}</span>
                    <Badge
                      style={cat ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] } : undefined}
                    >
                      {t(categoryI18nKey(e.category))}
                    </Badge>
                    <Badge tone="muted">{t("stages.stage_short", { n: e.stage_used })}</Badge>
                  </li>
                );
              })}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function Phase({
  icon,
  label,
  active,
  done,
  counter,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  done: boolean;
  counter?: string;
}) {
  return (
    <li
      className={cn("scan-progress__phase", active && "scan-progress__phase--active", done && "scan-progress__phase--done")}
    >
      <span className="scan-progress__phase-icon">{done ? <CheckCircle2 size={14} /> : icon}</span>
      <span className="scan-progress__phase-label">{label}</span>
      {counter && <span className="scan-progress__phase-counter">{counter}</span>}
    </li>
  );
}
