/**
 * React hook around an SSE scan. Returns: live event log, terminal status,
 * a ``run`` trigger, and a final ``snapshot_id`` once the scan completes.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { openScanStream } from "../../lib/api";
const INITIAL = { status: "idle", events: [], snapshotId: null, error: null };
export function useScanStream() {
    const [state, setState] = useState(INITIAL);
    const sourceRef = useRef(null);
    // Set when a terminal event (complete/error) has been processed, so the
    // browser's normal end-of-stream onerror doesn't flip a successful run
    // to "Connection lost". Chrome fires onerror around the same tick the
    // server closes — without this flag the race intermittently breaks UX.
    const terminatedRef = useRef(false);
    const close = useCallback(() => {
        sourceRef.current?.close();
        sourceRef.current = null;
    }, []);
    useEffect(() => () => close(), [close]);
    const run = useCallback((input) => {
        close();
        terminatedRef.current = false;
        setState({ status: "running", events: [], snapshotId: null, error: null });
        const es = openScanStream(input);
        sourceRef.current = es;
        const push = (evt) => {
            setState((s) => ({ ...s, events: [...s.events, evt] }));
        };
        const handlers = {
            scan_start: (e) => push({ type: "scan_start", ...JSON.parse(e.data) }),
            serp_fetch_start: (e) => push({ type: "serp_fetch_start", ...JSON.parse(e.data) }),
            serp_fetched: (e) => push({ type: "serp_fetched", ...JSON.parse(e.data) }),
            classify_phase_start: (e) => push({ type: "classify_phase_start", ...JSON.parse(e.data) }),
            classifying: (e) => push({ type: "classifying", ...JSON.parse(e.data) }),
            classified: (e) => push({ type: "classified", ...JSON.parse(e.data) }),
            persist_done: (e) => push({ type: "persist_done", ...JSON.parse(e.data) }),
            complete: (e) => {
                const data = JSON.parse(e.data);
                push({ type: "complete", ...data });
                setState((s) => ({ ...s, status: "complete", snapshotId: data.snapshot_id }));
                terminatedRef.current = true;
                close();
            },
            error: (e) => {
                const data = JSON.parse(e.data);
                push({ type: "error", message: data.message, type_name: data.type });
                setState((s) => ({ ...s, status: "error", error: data.message }));
                terminatedRef.current = true;
                close();
            },
        };
        for (const [name, fn] of Object.entries(handlers)) {
            es.addEventListener(name, fn);
        }
        es.onerror = () => {
            // Already past a terminal event — browser fires onerror on every
            // close, including the normal end-of-stream. Don't downgrade success.
            if (terminatedRef.current)
                return;
            if (sourceRef.current) {
                setState((s) => s.status === "running"
                    ? { ...s, status: "error", error: "Connection lost" }
                    : s);
                close();
            }
        };
    }, [close]);
    const reset = useCallback(() => {
        close();
        setState(INITIAL);
    }, [close]);
    return { state, run, reset, close };
}
