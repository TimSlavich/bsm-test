/**
 * Typed wrappers around the backend HTTP + SSE endpoints. The backend is
 * the source of truth for shapes; these types mirror the Pydantic schemas.
 */

export type ResultItem = {
  position: number;
  url: string;
  domain: string;
  title: string;
  category: string;
  subcategory: string;
  confidence: number;
  stage_used: number;
  reasoning: string;
  reason_code: string | null;
  signals: Record<string, unknown>;
};

export type ScanResponse = {
  snapshot_id: number;
  captured_at: string;
  brand_slug: string;
  keyword: string;
  geo: string;
  source: string;
  n_results: number;
  results: ResultItem[];
};

export type CategoryShare = {
  category: string;
  count: number;
  percent: number;
};

export type SnapshotSummary = {
  snapshot_id: number;
  captured_at: string;
  keyword: string;
  geo: string;
  n_results: number;
  distribution: CategoryShare[];
};

export type BrandSnapshotSummary = {
  snapshot_id: number;
  captured_at: string;
  keyword: string;
  geo: string;
  n_results: number;
};

export type TrendPoint = {
  date: string;
  snapshot_id: number;
  official: number;
  affiliate_to_brand: number;
  competitor_hijacking: number;
  informational: number;
};

export type SchedulerJobs = {
  enabled: boolean;
  jobs: { id: string; next_run_time: string | null; trigger: string }[];
};

export type DiffEntry = {
  domain: string;
  title: string;
  url: string;
  category: string;
  subcategory: string;
  position: number;
};

export type DiffMoved = {
  domain: string;
  title: string;
  url: string;
  category_from: string;
  category_to: string;
  subcategory_from: string;
  subcategory_to: string;
  position_from: number;
  position_to: number;
};

export type SnapshotDiff = {
  a: BrandSnapshotSummary;
  b: BrandSnapshotSummary;
  added: DiffEntry[];
  removed: DiffEntry[];
  moved: DiffMoved[];
  unchanged: DiffEntry[];
};

// Optional escape hatch for local dev when backend runs on a non-default
// host/port. Empty string falls through to the Vite/nginx /api proxy.
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function apiUrl(path: string): string {
  return API_BASE ? `${API_BASE}${path}` : path;
}

async function jget<T>(path: string): Promise<T> {
  const r = await fetch(apiUrl(path));
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<T>;
}

async function jpost<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<T>;
}

async function jput<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(apiUrl(path), {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<T>;
}

export async function triggerScan(input: {
  brand_slug: string;
  keyword: string;
  geo: string;
  top_n?: number;
}): Promise<ScanResponse> {
  return jpost<ScanResponse>("/api/scans", { top_n: 10, ...input });
}

export const fetchTrend = (brand: string, days = 14) =>
  jget<TrendPoint[]>(`/api/brands/${brand}/trend?days=${days}`);

export const fetchSnapshots = (brand: string, days = 30) =>
  jget<BrandSnapshotSummary[]>(`/api/brands/${brand}/snapshots?days=${days}`);

export const fetchSnapshotResults = (id: number) =>
  jget<ResultItem[]>(`/api/snapshots/${id}/results`);

export const fetchSnapshotSummary = (id: number) =>
  jget<SnapshotSummary>(`/api/snapshots/${id}`);

export const fetchSchedulerJobs = () => jget<SchedulerJobs>("/api/scheduler/jobs");

export const fetchSnapshotDiff = (a: number, b: number) =>
  jget<SnapshotDiff>(`/api/snapshots/diff?a=${a}&b=${b}`);

export const updateBrandWhitelists = (slug: string, body: unknown) =>
  jput(`/api/brands/${slug}/whitelists`, body);

// ── Scheduler keyword CRUD ─────────────────────────────────────────────

export type BrandKeyword = {
  id: number;
  brand_slug: string;
  keyword: string;
  geo: string;
  frequency_hours: number;
  active: boolean;
  last_scan_at: string | null;
  next_run_at: string | null;
};

export type KeywordCreate = {
  keyword: string;
  geo: string;
  frequency_hours: number;
  active: boolean;
};

export type KeywordUpdate = Partial<KeywordCreate>;

export const fetchBrandKeywords = (slug: string) =>
  jget<BrandKeyword[]>(`/api/brands/${slug}/keywords`);

export const createBrandKeyword = (slug: string, body: KeywordCreate) =>
  jpost<BrandKeyword>(`/api/brands/${slug}/keywords`, body);

export async function patchBrandKeyword(id: number, body: KeywordUpdate): Promise<BrandKeyword> {
  const r = await fetch(apiUrl(`/api/brands/keywords/${id}`), {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteBrandKeyword(id: number): Promise<void> {
  const r = await fetch(apiUrl(`/api/brands/keywords/${id}`), { method: "DELETE" });
  if (!r.ok) throw new Error(await r.text());
}

/** Open an EventSource for a live scan stream. Caller is responsible for
 * closing it when the scan is finished. */
export function openScanStream(input: {
  brand_slug: string;
  keyword: string;
  geo: string;
  top_n?: number;
}): EventSource {
  const params = new URLSearchParams({
    brand_slug: input.brand_slug,
    keyword: input.keyword,
    geo: input.geo,
    top_n: String(input.top_n ?? 10),
  });
  return new EventSource(apiUrl(`/api/scans/stream?${params.toString()}`));
}
