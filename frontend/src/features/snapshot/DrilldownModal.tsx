import { ExternalLink, Layers, Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge, Modal } from "../../components/ui";
import {
  CATEGORY_BG,
  CATEGORY_FG,
  categoryI18nKey,
  isCategory,
  subcategoryI18nKey,
} from "../../lib/categories";
import type { ResultItem } from "../../lib/api";
import { Favicon } from "../../components/ui";

interface DrilldownModalProps {
  result: ResultItem | null;
  onClose: () => void;
}

interface SignalsBag {
  affiliate_links?: number | string;
  brand_redirect_ratio?: number | string;
  competitor_redirect_ratio?: number | string;
  brand_mentions?: number | string;
  competitor_mentions?: number | string;
  schema_types?: string[];
  schema_review_target?: string | null;
  has_tracker?: boolean;
  // Pipeline-internal flags we don't want to surface as user-facing signals.
  llm_arbiter_failed?: boolean;
  llm_disabled?: boolean;
  llm_failure_reason?: string;
  llm_reasoning?: string;
  llm_model?: string;
  fetch_failed?: boolean;
  matched?: string;
  domain?: string;
}

export function DrilldownModal({ result, onClose }: DrilldownModalProps) {
  const { t } = useTranslation();
  if (!result) return null;
  const cat = isCategory(result.category) ? result.category : null;

  const signals = parseSignals(result);
  const reasoning = localizedReasoning(result, t);

  return (
    <Modal
      open={Boolean(result)}
      onClose={onClose}
      title={
        <span style={{ display: "inline-flex", alignItems: "center", gap: 12 }}>
          <Favicon domain={result.domain} size={28} />
          <span>{result.domain}</span>
        </span>
      }
      description={result.title}
      size="md"
    >
      <div className="drilldown">
        <div className="drilldown__tags">
          <Badge
            style={
              cat ? { background: CATEGORY_BG[cat], color: CATEGORY_FG[cat] } : undefined
            }
          >
            {t(categoryI18nKey(result.category))}
          </Badge>
          <Badge tone="muted">{t(subcategoryI18nKey(result.subcategory))}</Badge>
          <Badge tone="muted">
            <Layers size={11} style={{ marginRight: 4 }} />
            {t("drilldown.stage_label", { n: result.stage_used })}
          </Badge>
          <Badge tone="muted">
            <Sparkles size={11} style={{ marginRight: 4 }} />
            {t("drilldown.confidence_label", {
              pct: Math.round(result.confidence * 100),
            })}
          </Badge>
        </div>

        {reasoning && (
          <section className="drilldown__section">
            <h4 className="drilldown__section-title">{t("drilldown.reasoning_title")}</h4>
            <p className="drilldown__reasoning">{reasoning}</p>
          </section>
        )}

        <section className="drilldown__section">
          <h4 className="drilldown__section-title">{t("drilldown.signals_title")}</h4>
          <SignalsGrid signals={signals} />
        </section>

        <section className="drilldown__section">
          <h4 className="drilldown__section-title">{t("drilldown.url_title")}</h4>
          <a
            href={result.url}
            target="_blank"
            rel="noreferrer"
            className="drilldown__url"
          >
            <span>{result.url}</span>
            <ExternalLink size={14} />
          </a>
        </section>
      </div>
    </Modal>
  );
}

function SignalsGrid({ signals }: { signals: SignalsBag }) {
  const { t } = useTranslation();

  const cards: { key: string; value: string; label: string; description?: string; tone?: "neutral" | "good" | "warn" | "bad" }[] = [];

  if (typeof signals.affiliate_links === "number") {
    cards.push({
      key: "affiliate_links",
      value: String(signals.affiliate_links),
      label: t("drilldown.metric.affiliate_links"),
      description: t("drilldown.metric.affiliate_links_desc"),
      tone: signals.affiliate_links === 0 ? "neutral" : "warn",
    });
  }
  if (typeof signals.brand_redirect_ratio === "number") {
    cards.push({
      key: "brand_redirect_ratio",
      value: pct(signals.brand_redirect_ratio),
      label: t("drilldown.metric.brand_redirect_ratio"),
      description: t("drilldown.metric.brand_redirect_ratio_desc"),
      tone: signals.brand_redirect_ratio >= 0.6 ? "good" : "neutral",
    });
  }
  if (typeof signals.competitor_redirect_ratio === "number") {
    cards.push({
      key: "competitor_redirect_ratio",
      value: pct(signals.competitor_redirect_ratio),
      label: t("drilldown.metric.competitor_redirect_ratio"),
      description: t("drilldown.metric.competitor_redirect_ratio_desc"),
      tone: signals.competitor_redirect_ratio >= 0.6 ? "bad" : "neutral",
    });
  }
  if (typeof signals.brand_mentions === "number") {
    cards.push({
      key: "brand_mentions",
      value: String(signals.brand_mentions),
      label: t("drilldown.metric.brand_mentions"),
      description: t("drilldown.metric.brand_mentions_desc"),
      tone: "neutral",
    });
  }
  if (typeof signals.competitor_mentions === "number") {
    cards.push({
      key: "competitor_mentions",
      value: String(signals.competitor_mentions),
      label: t("drilldown.metric.competitor_mentions"),
      description: t("drilldown.metric.competitor_mentions_desc"),
      tone: signals.competitor_mentions > 0 ? "warn" : "neutral",
    });
  }

  if (cards.length === 0 && !signals.schema_types?.length && !signals.schema_review_target) {
    return <p className="drilldown__muted">{t("drilldown.no_signals")}</p>;
  }

  return (
    <>
      {cards.length > 0 && (
        <div className="drilldown__metrics">
          {cards.map((c) => (
            <div key={c.key} className="metric" data-tone={c.tone}>
              <div className="metric__value">{c.value}</div>
              <div className="metric__label">{c.label}</div>
              {c.description && <div className="metric__desc">{c.description}</div>}
            </div>
          ))}
        </div>
      )}

      {(signals.schema_types?.length || signals.schema_review_target) && (
        <dl className="drilldown__meta">
          {signals.schema_types && signals.schema_types.length > 0 && (
            <>
              <dt>{t("drilldown.metric.schema_types")}</dt>
              <dd>
                {Array.from(new Set(signals.schema_types)).map((s) => (
                  <Badge key={s} tone="muted" style={{ marginRight: 6 }}>
                    {s}
                  </Badge>
                ))}
              </dd>
            </>
          )}
          {signals.schema_review_target && (
            <>
              <dt>{t("drilldown.metric.schema_review_target")}</dt>
              <dd>{signals.schema_review_target}</dd>
            </>
          )}
          {signals.has_tracker !== undefined && (
            <>
              <dt>{t("drilldown.metric.has_tracker")}</dt>
              <dd>
                {signals.has_tracker
                  ? t("drilldown.metric.yes")
                  : t("drilldown.metric.no")}
              </dd>
            </>
          )}
        </dl>
      )}
    </>
  );
}

function pct(n: number): string {
  return `${Math.round(n * 100)}%`;
}

function localizedReasoning(
  result: ResultItem,
  t: (key: string, opts?: Record<string, unknown>) => string,
): string {
  // Backend emits a stable ``reason_code`` enum identifying the rule that
  // produced the verdict. We map it to a localized template so the user
  // sees text in their language instead of the backend's English string.
  if (!result.reason_code) return "";
  const key = `drilldown.reason.${result.reason_code}`;
  const translated = t(key, { domain: result.domain });
  return translated === key ? "" : translated;
}

function asNumber(v: unknown): number | undefined {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return undefined;
}

function asStringArray(v: unknown): string[] | undefined {
  if (Array.isArray(v)) return v.filter((x): x is string => typeof x === "string");
  return undefined;
}

function parseSignals(result: ResultItem): SignalsBag {
  // Backend now ships structured signals on ``ResultItem.signals`` (mirrors
  // the ``DomainClassification.signals`` JSON column). Read fields with
  // defensive type coercion — the dict is heterogeneous by design.
  const raw = result.signals ?? {};
  const out: SignalsBag = {};
  out.affiliate_links = asNumber(raw.affiliate_links);
  out.brand_redirect_ratio = asNumber(raw.brand_redirect_ratio);
  out.competitor_redirect_ratio = asNumber(raw.competitor_redirect_ratio);
  out.brand_mentions = asNumber(raw.brand_mentions);
  out.competitor_mentions = asNumber(raw.competitor_mentions);
  out.schema_types = asStringArray(raw.schema_types);
  if (typeof raw.schema_review_target === "string") {
    out.schema_review_target = raw.schema_review_target;
  } else if (raw.schema_review_target === null) {
    out.schema_review_target = null;
  }
  if (typeof raw.has_tracker === "boolean") out.has_tracker = raw.has_tracker;
  return out;
}
