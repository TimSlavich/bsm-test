/**
 * Theme management. Stores the user's preference in localStorage and toggles
 * the ``data-theme`` attribute on ``<html>``. CSS variable swap handles all
 * downstream restyling — no React re-render storm.
 */
const STORAGE_KEY = "brand-monitor.theme";
export function getStoredTheme() {
    if (typeof window === "undefined")
        return null;
    const v = window.localStorage.getItem(STORAGE_KEY);
    return v === "light" || v === "dark" ? v : null;
}
export function getSystemTheme() {
    if (typeof window === "undefined")
        return "light";
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
}
export function getInitialTheme() {
    return getStoredTheme() ?? getSystemTheme();
}
export function applyTheme(theme) {
    if (typeof document === "undefined")
        return;
    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem(STORAGE_KEY, theme);
}
