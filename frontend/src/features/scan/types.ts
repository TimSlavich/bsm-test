/**
 * Shape of streaming events emitted by ``GET /api/scans/stream``. Keep in
 * sync with ``services/scan.py``'s ``emit(...)`` calls.
 */
export type ProgressEvent =
  | { type: "scan_start"; brand: string; keyword: string; geo: string; top_n: number }
  | { type: "serp_fetch_start"; keyword: string; geo: string }
  | {
      type: "serp_fetched";
      source: string;
      n: number;
      rows: { position: number; url: string; domain: string; title: string }[];
    }
  | { type: "classify_phase_start"; total: number }
  | { type: "classifying"; index: number; total: number; domain: string; url: string }
  | {
      type: "classified";
      index: number;
      total: number;
      domain: string;
      category: string;
      subcategory: string;
      confidence: number;
      stage_used: number;
    }
  | { type: "persist_done"; snapshot_id: number; captured_at: string }
  | {
      type: "complete";
      snapshot_id: number;
      captured_at: string;
      source: string;
      n_results: number;
    }
  | { type: "error"; message: string; type_name?: string };
