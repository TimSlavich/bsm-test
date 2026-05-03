import { useTranslation } from "react-i18next";

import { EmptyState } from "../ui";
import type { ResultItem } from "../../lib/api";

interface StageBreakdownProps {
  results: ResultItem[];
}

export function StageBreakdown({ results }: StageBreakdownProps) {
  const { t } = useTranslation();
  if (results.length === 0) return <EmptyState title={t("snapshot.no_snapshots")} />;

  const counts: Record<number, number> = {};
  for (const r of results) counts[r.stage_used] = (counts[r.stage_used] ?? 0) + 1;
  const total = results.length;

  return (
    <div className="stage-bars">
      {[1, 2, 3].map((stage) => {
        const c = counts[stage] ?? 0;
        const pct = total ? (c * 100) / total : 0;
        return (
          <div key={stage} className="stage-bar__row">
            <div className="stage-bar__head">
              <span>
                {t("stages.stage_short", { n: stage })} · {t(`stages.${stage}`)}
              </span>
              <span style={{ color: "var(--text-muted)" }}>
                {c} ({pct.toFixed(0)}%)
              </span>
            </div>
            <div className="stage-bar__track">
              <div className="stage-bar__fill" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
