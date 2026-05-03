import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useTranslation } from "react-i18next";
import { Field, Select } from "../../components/ui";
function shortLocaleDate(iso, lang) {
    return new Intl.DateTimeFormat(lang, {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(iso));
}
export function SnapshotPicker({ snapshots, selected, onSelect }) {
    const { t, i18n } = useTranslation();
    const lang = i18n.resolvedLanguage ?? "en";
    // Sort by snapshot id DESC — the highest # is the most-recent record
    // (autoincrement) and is what users reach for 90% of the time.
    const sorted = [...snapshots].sort((a, b) => b.snapshot_id - a.snapshot_id);
    // Compact single-line label so the trigger (in a 280px sidebar) doesn't
    // wrap. Long absolute timestamp is shown on hover via the title attribute.
    // Plain inline spans (no nested flex) — keeps the baseline aligned with
    // the rest of the trigger button, no vertical jitter.
    const options = sorted.map((s) => ({
        value: String(s.snapshot_id),
        label: (_jsxs("span", { title: new Date(s.captured_at).toLocaleString(lang), style: {
                display: "block",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                fontVariantNumeric: "tabular-nums",
            }, children: [_jsxs("strong", { style: { fontWeight: 600 }, children: ["#", s.snapshot_id] }), _jsxs("span", { style: { color: "var(--text-muted)" }, children: ["  ·  ", shortLocaleDate(s.captured_at, lang), "  ·  ", s.keyword] })] })),
    }));
    if (snapshots.length === 0) {
        return (_jsx(Field, { label: t("snapshot.picker_label"), children: _jsx("span", { className: "snapshot-picker__meta", children: t("snapshot.no_snapshots") }) }));
    }
    return (_jsx(Field, { label: t("snapshot.picker_label"), children: _jsx(Select, { value: selected ? String(selected) : options[0]?.value ?? "", onChange: (v) => onSelect(Number(v)), options: options, size: "md" }) }));
}
