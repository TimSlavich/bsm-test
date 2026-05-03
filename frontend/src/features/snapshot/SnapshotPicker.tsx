import { useTranslation } from "react-i18next";

import { Field, Select, type SelectOption } from "../../components/ui";
import type { BrandSnapshotSummary } from "../../lib/api";

interface SnapshotPickerProps {
  snapshots: BrandSnapshotSummary[];
  selected: number | null;
  onSelect: (id: number) => void;
}

function shortLocaleDate(iso: string, lang: string): string {
  return new Intl.DateTimeFormat(lang, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function SnapshotPicker({ snapshots, selected, onSelect }: SnapshotPickerProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "en";

  // Sort by snapshot id DESC — the highest # is the most-recent record
  // (autoincrement) and is what users reach for 90% of the time.
  const sorted = [...snapshots].sort((a, b) => b.snapshot_id - a.snapshot_id);

  // Compact single-line label so the trigger (in a 280px sidebar) doesn't
  // wrap. Long absolute timestamp is shown on hover via the title attribute.
  // Plain inline spans (no nested flex) — keeps the baseline aligned with
  // the rest of the trigger button, no vertical jitter.
  const options: SelectOption[] = sorted.map((s) => ({
    value: String(s.snapshot_id),
    label: (
      <span
        title={new Date(s.captured_at).toLocaleString(lang)}
        style={{
          display: "block",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        <strong style={{ fontWeight: 600 }}>#{s.snapshot_id}</strong>
        <span style={{ color: "var(--text-muted)" }}>
          {"  ·  "}
          {shortLocaleDate(s.captured_at, lang)}
          {"  ·  "}
          {s.keyword}
        </span>
      </span>
    ),
  }));

  if (snapshots.length === 0) {
    return (
      <Field label={t("snapshot.picker_label")}>
        <span className="snapshot-picker__meta">{t("snapshot.no_snapshots")}</span>
      </Field>
    );
  }
  return (
    <Field label={t("snapshot.picker_label")}>
      <Select
        value={selected ? String(selected) : options[0]?.value ?? ""}
        onChange={(v) => onSelect(Number(v))}
        options={options}
        size="md"
      />
    </Field>
  );
}
