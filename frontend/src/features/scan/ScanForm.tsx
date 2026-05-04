import { useQuery } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";

import { Button, Field, Input, Select, type SelectOption, Tooltip } from "../../components/ui";
import { fetchGeos } from "../../lib/api";

export interface ScanFormValues {
  brand_slug: string;
  keyword: string;
  geo: string;
  top_n: number;
}

interface ScanFormProps {
  values: ScanFormValues;
  onChange: (next: ScanFormValues) => void;
  onSubmit: () => void;
  isRunning: boolean;
  /** Per-field validation messages keyed by field name. Cleared by the
   * parent when the user edits any input. */
  errors?: Record<string, string>;
}

export function ScanForm({ values, onChange, onSubmit, isRunning, errors }: ScanFormProps) {
  const fieldError = (k: keyof ScanFormValues): string | undefined => errors?.[k];

  // Geo dropdown is fed from /api/geos (single source of truth for
  // the supported set — same registry the validator and SERP fetcher
  // use). Cached for the session; supported geos rarely change.
  const geosQ = useQuery({
    queryKey: ["geos"],
    queryFn: fetchGeos,
    staleTime: Infinity,
  });
  const geoOptions: SelectOption[] = (geosQ.data ?? [{ code: values.geo, name: values.geo }]).map(
    (g) => ({ value: g.code, label: `${g.code} — ${g.name}` }),
  );
  const { t } = useTranslation();
  const ids = {
    brand: useId(),
    keyword: useId(),
    top_n: useId(),
  };

  const set = <K extends keyof ScanFormValues>(k: K, v: ScanFormValues[K]) =>
    onChange({ ...values, [k]: v });

  return (
    <form
      className="scan-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <Field
        label={
          <>
            {t("scan_form.brand")}
            <Tooltip content={t("scan_form.tooltip_brand")} side="right">
              <span className="field__why" aria-hidden>
                ?
              </span>
            </Tooltip>
          </>
        }
        htmlFor={ids.brand}
        error={fieldError("brand_slug")}
      >
        <Input
          id={ids.brand}
          value={values.brand_slug}
          onChange={(e) => set("brand_slug", e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
      </Field>

      <Field
        label={
          <>
            {t("scan_form.keyword")}
            <Tooltip content={t("scan_form.tooltip_keyword")} side="right">
              <span className="field__why" aria-hidden>
                ?
              </span>
            </Tooltip>
          </>
        }
        htmlFor={ids.keyword}
        error={fieldError("keyword")}
      >
        <Input
          id={ids.keyword}
          value={values.keyword}
          onChange={(e) => set("keyword", e.target.value)}
          autoComplete="off"
        />
      </Field>

      <div className="scan-form__row">
        <Field
          label={
            <>
              {t("scan_form.geo")}
              <Tooltip content={t("scan_form.tooltip_geo")} side="right">
                <span className="field__why" aria-hidden>
                  ?
                </span>
              </Tooltip>
            </>
          }
          error={fieldError("geo")}
        >
          <Select
            value={values.geo}
            onChange={(v) => set("geo", v)}
            options={geoOptions}
            ariaLabel={t("scan_form.geo")}
          />
        </Field>

        <Field
          label={
            <>
              {t("scan_form.top_n")}
              <Tooltip content={t("scan_form.tooltip_top_n")} side="right">
                <span className="field__why" aria-hidden>
                  ?
                </span>
              </Tooltip>
            </>
          }
          htmlFor={ids.top_n}
          error={fieldError("top_n")}
        >
          <Input
            id={ids.top_n}
            type="number"
            min={1}
            max={20}
            value={values.top_n}
            onChange={(e) => set("top_n", Math.max(1, Math.min(20, Number(e.target.value) || 10)))}
          />
        </Field>
      </div>

      <Button type="submit" loading={isRunning} fullWidth leftIcon={<Play size={14} />} size="lg">
        {isRunning ? t("actions.scanning") : t("actions.run_scan")}
      </Button>
    </form>
  );
}
