import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowRight, ArrowUp, Minus, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Badge, Card, CardBody, CardHeader, EmptyState, Favicon, Field, Select, type SelectOption } from "../../components/ui";
import {
  CATEGORY_BG,
  CATEGORY_FG,
  categoryI18nKey,
  isCategory,
} from "../../lib/categories";
import { fetchSnapshotDiff } from "../../lib/api";
import { formatDate } from "../../lib/format";
import type { BrandSnapshotSummary, DiffEntry, DiffMoved } from "../../lib/api";

interface DiffViewProps {
  snapshots: BrandSnapshotSummary[];
}

export function DiffView({ snapshots }: DiffViewProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "en";

  // Two views over the same data, sorted by snapshot id (autoincrement):
  // - ``ascending`` (#1 → #N) drives sensible defaults (a = oldest, b = newest).
  // - ``descending`` (#N → #1) is what each dropdown displays — newest # at top.
  const ascending = useMemo(
    () => [...snapshots].sort((x, y) => x.snapshot_id - y.snapshot_id),
    [snapshots],
  );
  const descending = useMemo(() => [...ascending].reverse(), [ascending]);
  const validIds = useMemo(
    () => new Set(ascending.map((s) => s.snapshot_id)),
    [ascending],
  );

  const [a, setA] = useState<number | null>(null);
  const [b, setB] = useState<number | null>(null);

  // Re-sync selected ids whenever the underlying snapshot list changes —
  // prevents the picker from holding a stale id (e.g. after a DB reset)
  // and 404-ing the diff request indefinitely.
  useEffect(() => {
    if (ascending.length < 2) {
      setA(null);
      setB(null);
      return;
    }
    setA((prev) =>
      prev !== null && validIds.has(prev) ? prev : ascending[0].snapshot_id,
    );
    setB((prev) =>
      prev !== null && validIds.has(prev)
        ? prev
        : ascending[ascending.length - 1].snapshot_id,
    );
  }, [ascending, validIds]);

  const diff = useQuery({
    queryKey: ["diff", a, b],
    queryFn: () => fetchSnapshotDiff(a as number, b as number),
    enabled:
      a !== null &&
      b !== null &&
      a !== b &&
      validIds.has(a) &&
      validIds.has(b),
    retry: false,
    staleTime: 60_000,
  });

  // If the diff request 404s (e.g. ids became invalid mid-flight), reset
  // selection to the first/last snapshot so the next render submits a
  // valid request instead of looping the failed one.
  useEffect(() => {
    if (!diff.isError) return;
    if (ascending.length >= 2) {
      setA(ascending[0].snapshot_id);
      setB(ascending[ascending.length - 1].snapshot_id);
    }
  }, [diff.isError, ascending]);

  const opts = (excluded: number | null): SelectOption[] =>
    descending
      .filter((s) => s.snapshot_id !== excluded)
      .map((s) => ({
        value: String(s.snapshot_id),
        label: `#${s.snapshot_id} · ${formatDate(s.captured_at, lang)} · ${s.keyword}`,
      }));

  return (
    <div className="diff">
      <Card>
        <CardHeader title={t("diff.title")} description={t("diff.intro")} />
        <CardBody>
          <div className="diff-controls">
            <Field label={t("diff.snapshot_a")}>
              <Select
                value={a ? String(a) : ""}
                onChange={(v) => setA(Number(v))}
                options={opts(b)}
                size="md"
              />
            </Field>
            <Field label={t("diff.snapshot_b")}>
              <Select
                value={b ? String(b) : ""}
                onChange={(v) => setB(Number(v))}
                options={opts(a)}
                size="md"
              />
            </Field>
          </div>
        </CardBody>
      </Card>

      {a === null || b === null || a === b ? (
        <Card>
          <CardBody>
            <EmptyState title={t("diff.select_two")} />
          </CardBody>
        </Card>
      ) : diff.isLoading ? (
        <Card>
          <CardBody>{t("common.loading")}</CardBody>
        </Card>
      ) : diff.data ? (
        <>
          <DiffSection
            title={t("diff.added")}
            tone="added"
            icon={<Plus size={12} />}
            entries={diff.data.added}
            empty={t("diff.empty_added")}
          />
          <DiffSection
            title={t("diff.removed")}
            tone="removed"
            icon={<Minus size={12} />}
            entries={diff.data.removed}
            empty={t("diff.empty_removed")}
          />
          <MovedSection title={t("diff.moved")} entries={diff.data.moved} empty={t("diff.empty_moved")} />
        </>
      ) : null}
    </div>
  );
}

function DiffSection({
  title,
  tone,
  icon,
  entries,
  empty,
}: {
  title: string;
  tone: "added" | "removed";
  icon: React.ReactNode;
  entries: DiffEntry[];
  empty: string;
}) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader title={<span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>{icon} {title}</span>} action={<Badge tone="muted">{entries.length}</Badge>} />
      <CardBody>
        {entries.length === 0 ? (
          <EmptyState title={empty} />
        ) : (
          <ul className="diff-section__list">
            {entries.map((e) => {
              const cat = isCategory(e.category) ? e.category : null;
              return (
                <li key={`${tone}-${e.domain}`} className="diff-row" data-tone={tone}>
                  <span className="diff-row__pos">#{e.position}</span>
                  <span style={{ display: "flex", gap: 8, alignItems: "center", minWidth: 0 }}>
                    <Favicon domain={e.domain} size={16} />
                    <span style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 500 }}>{e.domain}</div>
                      <div className="domain-table__title">{e.title}</div>
                    </span>
                  </span>
                  <Badge style={cat ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] } : undefined}>
                    {t(categoryI18nKey(e.category))}
                  </Badge>
                </li>
              );
            })}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function MovedSection({ title, entries, empty }: { title: string; entries: DiffMoved[]; empty: string }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader title={title} action={<Badge tone="muted">{entries.length}</Badge>} />
      <CardBody>
        {entries.length === 0 ? (
          <EmptyState title={empty} />
        ) : (
          <ul className="diff-section__list">
            {entries.map((e) => {
              const catFrom = isCategory(e.category_from) ? e.category_from : null;
              const catTo = isCategory(e.category_to) ? e.category_to : null;
              const moveIcon = e.position_to < e.position_from ? <ArrowUp size={12} color="var(--success)" /> : e.position_to > e.position_from ? <ArrowDown size={12} color="var(--danger)" /> : <ArrowRight size={12} />;
              return (
                <li key={`moved-${e.domain}`} className="diff-row" data-tone="moved">
                  <span className="diff-row__pos">{moveIcon}</span>
                  <span style={{ display: "flex", gap: 8, alignItems: "center", minWidth: 0 }}>
                    <Favicon domain={e.domain} size={16} />
                    <span style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 500 }}>{e.domain}</div>
                      <div className="domain-table__title">
                        {t("diff.from_to", { from: `#${e.position_from}`, to: `#${e.position_to}` })}
                      </div>
                    </span>
                  </span>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                    <Badge
                      style={
                        catFrom ? { background: CATEGORY_BG[catFrom], color: CATEGORY_FG[catFrom], opacity: 0.7 } : undefined
                      }
                    >
                      {t(categoryI18nKey(e.category_from))}
                    </Badge>
                    {catFrom !== catTo && <ArrowRight size={12} />}
                    {catFrom !== catTo && (
                      <Badge
                        style={
                          catTo
                            ? { background: CATEGORY_BG[catTo], color: CATEGORY_FG[catTo] }
                            : undefined
                        }
                      >
                        {t(categoryI18nKey(e.category_to))}
                      </Badge>
                    )}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
