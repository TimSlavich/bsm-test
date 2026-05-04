/**
 * Typed wrappers around the backend HTTP + SSE endpoints. The backend is
 * the source of truth for shapes; these types mirror the Pydantic schemas.
 */
// Optional escape hatch for local dev when backend runs on a non-default
// host/port. Empty string falls through to the Vite/nginx /api proxy.
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
function apiUrl(path) {
    return API_BASE ? `${API_BASE}${path}` : path;
}
async function jget(path) {
    const r = await fetch(apiUrl(path));
    if (!r.ok)
        throw new Error(await r.text());
    return r.json();
}
async function jpost(path, body) {
    const r = await fetch(apiUrl(path), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!r.ok)
        throw new Error(await r.text());
    return r.json();
}
async function jput(path, body) {
    const r = await fetch(apiUrl(path), {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!r.ok)
        throw new Error(await r.text());
    return r.json();
}
/** Supported geos served from the SERP fetcher's registry. */
export const fetchGeos = () => jget("/api/geos").then((r) => r.geos);
/** Pre-flight validation for scan inputs. Returns problems (empty = ok). */
export async function validateScanInput(input) {
    const r = await fetch(apiUrl("/api/scans/validate"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ top_n: 10, ...input }),
    });
    if (!r.ok)
        throw new Error(await r.text());
    const body = (await r.json());
    return body.problems ?? [];
}
export async function triggerScan(input) {
    return jpost("/api/scans", { top_n: 10, ...input });
}
export const fetchTrend = (brand, days = 14) => jget(`/api/brands/${brand}/trend?days=${days}`);
export const fetchSnapshots = (brand, days = 30) => jget(`/api/brands/${brand}/snapshots?days=${days}`);
export const fetchSnapshotResults = (id) => jget(`/api/snapshots/${id}/results`);
export const fetchSnapshotSummary = (id) => jget(`/api/snapshots/${id}`);
export const fetchSchedulerJobs = () => jget("/api/scheduler/jobs");
export const fetchSnapshotDiff = (a, b) => jget(`/api/snapshots/diff?a=${a}&b=${b}`);
export const updateBrandWhitelists = (slug, body) => jput(`/api/brands/${slug}/whitelists`, body);
export const fetchBrandKeywords = (slug) => jget(`/api/brands/${slug}/keywords`);
export const createBrandKeyword = (slug, body) => jpost(`/api/brands/${slug}/keywords`, body);
export async function patchBrandKeyword(id, body) {
    const r = await fetch(apiUrl(`/api/brands/keywords/${id}`), {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!r.ok)
        throw new Error(await r.text());
    return r.json();
}
export async function deleteBrandKeyword(id) {
    const r = await fetch(apiUrl(`/api/brands/keywords/${id}`), { method: "DELETE" });
    if (!r.ok)
        throw new Error(await r.text());
}
/** Open an EventSource for a live scan stream. Caller is responsible for
 * closing it when the scan is finished. */
export function openScanStream(input) {
    const params = new URLSearchParams({
        brand_slug: input.brand_slug,
        keyword: input.keyword,
        geo: input.geo,
        top_n: String(input.top_n ?? 10),
    });
    return new EventSource(apiUrl(`/api/scans/stream?${params.toString()}`));
}
