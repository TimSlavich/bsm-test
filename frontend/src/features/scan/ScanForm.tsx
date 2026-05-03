import { Play } from "lucide-react";
import { useId } from "react";
import { useTranslation } from "react-i18next";

import { Button, Field, Input, Tooltip } from "../../components/ui";

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
}

export function ScanForm({ values, onChange, onSubmit, isRunning }: ScanFormProps) {
  const { t } = useTranslation();
  const ids = {
    brand: useId(),
    keyword: useId(),
    geo: useId(),
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
          htmlFor={ids.geo}
        >
          <Input
            id={ids.geo}
            value={values.geo}
            onChange={(e) => set("geo", e.target.value.toUpperCase().slice(0, 4))}
            maxLength={4}
            autoComplete="off"
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
