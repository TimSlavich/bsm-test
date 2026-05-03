import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Toaster } from "sonner";
import { AppShell } from "./components/layout/AppShell";
import { Topbar } from "./components/layout/Topbar";
import { DiffView } from "./features/diff/DiffView";
import { MethodologyModal } from "./features/methodology/MethodologyModal";
import { SchedulerView } from "./features/scheduler/SchedulerView";
import { useDashboard, useDashboardSnapshots } from "./pages/Dashboard";
const DEFAULT_BRAND = "starcasino";
const queryClient = new QueryClient({
    defaultOptions: { queries: { refetchOnWindowFocus: false } },
});
function Inner() {
    const [view, setView] = useState("dashboard");
    const [methodologyOpen, setMethodologyOpen] = useState(false);
    const { i18n } = useTranslation();
    const dash = useDashboard();
    const snaps = useDashboardSnapshots(DEFAULT_BRAND);
    const main = (() => {
        if (view === "compare")
            return _jsx(DiffView, { snapshots: snaps.data ?? [] });
        if (view === "scheduler")
            return _jsx(SchedulerView, { brandSlug: DEFAULT_BRAND });
        return dash.main;
    })();
    return (_jsxs(_Fragment, { children: [_jsx(AppShell, { topbar: _jsx(Topbar, { view: view, onViewChange: setView, onOpenMethodology: () => setMethodologyOpen(true) }), sidebar: dash.sidebar, main: main, rightRail: view === "dashboard" ? dash.rail : null }), _jsx(MethodologyModal, { open: methodologyOpen, onClose: () => setMethodologyOpen(false) }), _jsx(Toaster, { position: "bottom-right", theme: (typeof document !== "undefined" &&
                    document.documentElement.getAttribute("data-theme")) ||
                    "light", richColors: true, closeButton: true }), _jsx("span", { hidden: true, lang: i18n.language })] }));
}
export default function App() {
    return (_jsx(QueryClientProvider, { client: queryClient, children: _jsx(Inner, {}) }));
}
