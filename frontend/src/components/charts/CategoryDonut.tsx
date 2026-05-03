import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState } from "../ui";
import {
  CATEGORY_BG,
  CATEGORY_COLOR,
  CATEGORY_FG,
  CATEGORY_ORDER,
  categoryI18nKey,
  type CategoryKey,
} from "../../lib/categories";
import { cn } from "../../lib/cn";
import type { ResultItem } from "../../lib/api";

interface CategoryDonutProps {
  results: ResultItem[];
}

/**
 * Horizontal stacked-bar + per-category rows.
 *
 * A 4-segment donut chart wastes screen space and can't show numbers
 * without overlapping; the bar+rows pattern reads at a glance even on
 * mobile and surfaces both raw counts and shares.
 */
export function CategoryDonut({ results }: CategoryDonutProps) {
  const { t } = useTranslation();

  const stats = useMemo(() => {
    const counts = new Map<CategoryKey, number>();
    for (const r of results) {
      if ((CATEGORY_ORDER as readonly string[]).includes(r.category)) {
        const c = r.category as CategoryKey;
        counts.set(c, (counts.get(c) ?? 0) + 1);
      }
    }
    const total = results.length || 0;
    return CATEGORY_ORDER.map((c) => {
      const count = counts.get(c) ?? 0;
      return {
        key: c,
        label: t(categoryI18nKey(c)),
        count,
        percent: total > 0 ? (count / total) * 100 : 0,
      };
    });
  }, [results, t]);

  const total = results.length;
  const dominant = [...stats].sort((a, b) => b.count - a.count)[0];

  if (total === 0) {
    return <EmptyState title={t("snapshot.no_snapshots")} />;
  }

  return (
    <div className="dist">
      <div className="dist__summary">
        <div className="dist__summary-value">{total}</div>
        <div className="dist__summary-label">
          {t("table.headers.domain")}
        </div>
        {dominant.count > 0 && (
          <span
            className="dist__summary-tag"
            style={{
              background: CATEGORY_BG[dominant.key],
              color: CATEGORY_FG[dominant.key],
            }}
          >
            <span
              className="dist__summary-dot"
              style={{ background: CATEGORY_COLOR[dominant.key] }}
              aria-hidden
            />
            {dominant.label} · {dominant.percent.toFixed(0)}%
          </span>
        )}
      </div>

      <div
        className="dist__bar"
        role="img"
        aria-label={stats
          .filter((s) => s.count > 0)
          .map((s) => `${s.label} ${s.count} (${s.percent.toFixed(0)}%)`)
          .join(", ")}
      >
        {stats
          .filter((s) => s.count > 0)
          .map((s) => (
            <div
              key={s.key}
              className="dist__bar-seg"
              style={{
                flexBasis: `${s.percent}%`,
                background: CATEGORY_COLOR[s.key],
              }}
              title={`${s.label}: ${s.count} (${s.percent.toFixed(0)}%)`}
            />
          ))}
      </div>

      <ul className="dist__rows">
        {stats.map((s) => (
          <li
            key={s.key}
            className={cn("dist__row", s.count === 0 && "dist__row--zero")}
          >
            <span
              className="dist__dot"
              style={{ background: CATEGORY_COLOR[s.key] }}
              aria-hidden
            />
            <span className="dist__label">{s.label}</span>
            <span className="dist__count">{s.count}</span>
            <span className="dist__percent">{s.percent.toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
