import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button, Field, Input, Modal, Switch } from "../../components/ui";
import type { BrandKeyword, KeywordCreate } from "../../lib/api";

interface KeywordDialogProps {
  open: boolean;
  initial?: BrandKeyword | null;
  onClose: () => void;
  onSubmit: (values: KeywordCreate) => Promise<void> | void;
  busy?: boolean;
}

export function KeywordDialog({ open, initial, onClose, onSubmit, busy }: KeywordDialogProps) {
  const { t } = useTranslation();
  const ids = { kw: useId(), geo: useId(), freq: useId() };

  const [keyword, setKeyword] = useState("");
  const [geo, setGeo] = useState("NL");
  const [frequencyHours, setFrequencyHours] = useState(24);
  const [active, setActive] = useState(true);

  useEffect(() => {
    if (open) {
      setKeyword(initial?.keyword ?? "");
      setGeo(initial?.geo ?? "NL");
      setFrequencyHours(initial?.frequency_hours ?? 24);
      setActive(initial?.active ?? true);
    }
  }, [open, initial]);

  const isEdit = Boolean(initial);
  const canSubmit = keyword.trim().length > 0 && geo.length >= 2 && frequencyHours > 0;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? t("scheduler_view.edit_title") : t("scheduler_view.add_title")}
      size="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            {t("actions.cancel")}
          </Button>
          <Button
            onClick={() =>
              onSubmit({
                keyword: keyword.trim(),
                geo: geo.toUpperCase(),
                frequency_hours: frequencyHours,
                active,
              })
            }
            loading={busy}
            disabled={!canSubmit}
          >
            {isEdit ? t("actions.save") : t("actions.create")}
          </Button>
        </>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <Field label={t("scan_form.keyword")} htmlFor={ids.kw}>
          <Input
            id={ids.kw}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            autoFocus
          />
        </Field>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label={t("scan_form.geo")} htmlFor={ids.geo}>
            <Input
              id={ids.geo}
              value={geo}
              onChange={(e) => setGeo(e.target.value.toUpperCase().slice(0, 4))}
              maxLength={4}
            />
          </Field>
          <Field label={t("scheduler_view.headers.frequency")} htmlFor={ids.freq}>
            <Input
              id={ids.freq}
              type="number"
              min={1}
              max={720}
              value={frequencyHours}
              onChange={(e) => setFrequencyHours(Math.max(1, Math.min(720, Number(e.target.value) || 24)))}
              rightSlot="h"
            />
          </Field>
        </div>
        <Field label={t("scheduler_view.headers.active")}>
          <Switch checked={active} onChange={setActive} ariaLabel={t("scheduler_view.headers.active")} />
        </Field>
      </div>
    </Modal>
  );
}
