import { useTranslation } from "react-i18next";

import { Favicon, EmptyState } from "../ui";
import {
  CATEGORY_BG,
  CATEGORY_COLOR,
  CATEGORY_FG,
  categoryI18nKey,
  isCategory,
  type CategoryKey,
} from "../../lib/categories";
import type { ResultItem } from "../../lib/api";

interface PositionLineupProps {
  results: ResultItem[];
}

/**
 * A horizontal strip of N cells, one per SERP position. Each cell is
 * colour-coded by the category that domain landed in, so the user can
 * read "who owns each rank" at a glance — much clearer than a Sankey
 * for a top-10 dataset.
 */
export function PositionLineup({ results }: PositionLineupProps) {
  const { t } = useTranslation();
  if (results.length === 0) {
    return <EmptyState title={t("snapshot.no_snapshots")} />;
  }
  const sorted = [...results].sort((a, b) => a.position - b.position);

  return (
    <div className="lineup">
      <div className="lineup__row">
        {sorted.map((r) => {
          const cat = isCategory(r.category) ? (r.category as CategoryKey) : null;
          const bg = cat ? CATEGORY_BG[cat] : "var(--bg-subtle)";
          const fg = cat ? CATEGORY_FG[cat] : "var(--text-muted)";
          const accent = cat ? CATEGORY_COLOR[cat] : "var(--text-subtle)";
          return (
            <div
              key={r.position}
              className="lineup__cell"
              style={{ background: bg, color: fg }}
              title={`#${r.position} · ${r.domain} · ${t(categoryI18nKey(r.category))}`}
            >
              <div className="lineup__pos">#{r.position}</div>
              <Favicon domain={r.domain} size={20} className="lineup__favicon" />
              <div className="lineup__domain">{r.domain}</div>
              <div className="lineup__bar" style={{ background: accent }} />
            </div>
          );
        })}
      </div>
      <Legend />
    </div>
  );
}

function Legend() {
  const { t } = useTranslation();
  const items: { key: CategoryKey; label: string }[] = [
    { key: "official", label: t("categories.official") },
    { key: "affiliate_to_brand", label: t("categories.affiliate_to_brand") },
    { key: "competitor_hijacking", label: t("categories.competitor_hijacking") },
    { key: "informational", label: t("categories.informational") },
  ];
  return (
    <div className="lineup__legend" aria-hidden>
      {items.map((it) => (
        <span key={it.key} className="lineup__legend-item">
          <span className="lineup__legend-dot" style={{ background: CATEGORY_COLOR[it.key] }} />
          {it.label}
        </span>
      ))}
    </div>
  );
}
