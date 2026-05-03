/**
 * Locale-aware formatters. Pass ``locale`` from i18n.language for correct
 * Ukrainian / English rendering of numbers and dates.
 */
export function formatPercent(value: number, locale: string, fractionDigits = 1): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value / 100);
}

export function formatNumber(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value);
}

/**
 * Defensive UTC normalizer: if the backend returns a naive ISO string
 * (no ``Z`` and no ``±HH:MM`` offset), the browser parses it as local time
 * and labels drift by the user's TZ offset. Append ``Z`` so it always
 * resolves to UTC. Pydantic's ``UtcDatetime`` already emits ``Z``, but
 * this guards against future endpoints that bypass it.
 */
function parseDate(iso: string | Date): Date {
  if (iso instanceof Date) return iso;
  const hasTz = iso.endsWith("Z") || /[+-]\d\d:?\d\d$/.test(iso);
  return new Date(hasTz ? iso : iso + "Z");
}

export function formatDate(iso: string | Date, locale: string): string {
  const d = parseDate(iso);
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

export function formatRelativeTime(iso: string | Date, locale: string): string {
  const d = parseDate(iso);
  const seconds = Math.round((d.getTime() - Date.now()) / 1000);
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  const abs = Math.abs(seconds);
  if (abs < 60) return rtf.format(seconds, "second");
  if (abs < 3600) return rtf.format(Math.round(seconds / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(seconds / 3600), "hour");
  return rtf.format(Math.round(seconds / 86400), "day");
}

/** Always 200 OK — the backend proxies third-party services and absorbs 404s. */
export function faviconFor(domain: string, size = 32): string {
  return `/api/favicons/${encodeURIComponent(domain)}?size=${size}`;
}
