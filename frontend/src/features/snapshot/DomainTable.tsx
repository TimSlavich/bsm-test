import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Badge, EmptyState, Favicon, Input } from "../../components/ui";
import {
  CATEGORY_BG,
  CATEGORY_COLOR,
  CATEGORY_FG,
  CATEGORY_ORDER,
  categoryI18nKey,
  isCategory,
  subcategoryI18nKey,
  type CategoryKey,
} from "../../lib/categories";
import { cn } from "../../lib/cn";
import type { ResultItem } from "../../lib/api";

interface DomainTableProps {
  results: ResultItem[];
  onRowClick?: (r: ResultItem) => void;
}

export function DomainTable({ results, onRowClick }: DomainTableProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<CategoryKey | "all">("all");

  const counts = useMemo(() => {
    const map = new Map<CategoryKey, number>();
    for (const r of results) {
      if (isCategory(r.category)) {
        map.set(r.category, (map.get(r.category) ?? 0) + 1);
      }
    }
    return map;
  }, [results]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return results.filter((r) => {
      if (filter !== "all" && r.category !== filter) return false;
      if (q && !r.domain.toLowerCase().includes(q) && !r.title.toLowerCase().includes(q))
        return false;
      return true;
    });
  }, [results, filter, search]);

  if (results.length === 0) {
    return null;
  }

  return (
    <div className="domain-table-wrap">
      <div className="domain-table-toolbar">
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t("table.search_placeholder")}
          leftIcon={<Search size={14} />}
        />
        <div className="domain-filter-chips">
          <button
            type="button"
            className="chip"
            data-active={filter === "all" || undefined}
            onClick={() => setFilter("all")}
          >
            {t("table.filter_all")}
            <span className="chip__count">{results.length}</span>
          </button>
          {CATEGORY_ORDER.map((c) => {
            const n = counts.get(c) ?? 0;
            return (
              <button
                key={c}
                type="button"
                className="chip"
                data-active={filter === c || undefined}
                onClick={() => setFilter(c)}
                disabled={n === 0}
                style={filter === c ? { background: CATEGORY_COLOR[c], borderColor: CATEGORY_COLOR[c] } : undefined}
              >
                <span className="chip__dot" style={{ background: CATEGORY_COLOR[c] }} />
                {t(categoryI18nKey(c))}
                <span className="chip__count">{n}</span>
              </button>
            );
          })}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title={t("table.no_match")} />
      ) : (
        <div style={{ maxHeight: 540, overflow: "auto" }}>
          <table className="domain-table">
            <thead>
              <tr>
                <th className="domain-table__pos">{t("table.headers.position")}</th>
                <th>{t("table.headers.domain")}</th>
                <th>{t("table.headers.subcategory")}</th>
                <th>{t("table.headers.category")}</th>
                <th>{t("table.headers.confidence")}</th>
                <th>{t("table.headers.stage")}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const cat = isCategory(r.category) ? (r.category as CategoryKey) : null;
                return (
                  <tr key={`${r.position}-${r.domain}`} onClick={() => onRowClick?.(r)}>
                    <td className="domain-table__pos">{r.position}</td>
                    <td>
                      <div className="domain-table__brand">
                        <Favicon domain={r.domain} size={18} />
                        <div style={{ minWidth: 0 }}>
                          <div className="domain-table__domain">{r.domain}</div>
                          <div className="domain-table__title">{r.title}</div>
                        </div>
                      </div>
                    </td>
                    <td>{t(subcategoryI18nKey(r.subcategory))}</td>
                    <td>
                      <Badge
                        style={
                          cat
                            ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] }
                            : undefined
                        }
                      >
                        {t(categoryI18nKey(r.category))}
                      </Badge>
                    </td>
                    <td className={cn("domain-table__conf")}>
                      {(r.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="domain-table__stage">
                      {t("stages.stage_short", { n: r.stage_used })}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
