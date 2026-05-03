import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Toaster } from "sonner";

import { AppShell } from "./components/layout/AppShell";
import { Topbar, type View } from "./components/layout/Topbar";
import { DiffView } from "./features/diff/DiffView";
import { MethodologyModal } from "./features/methodology/MethodologyModal";
import { SchedulerView } from "./features/scheduler/SchedulerView";
import { useDashboard, useDashboardSnapshots } from "./pages/Dashboard";

const DEFAULT_BRAND = "starcasino";

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } },
});

function Inner() {
  const [view, setView] = useState<View>("dashboard");
  const [methodologyOpen, setMethodologyOpen] = useState(false);
  const { i18n } = useTranslation();

  const dash = useDashboard();
  const snaps = useDashboardSnapshots(DEFAULT_BRAND);

  const main = (() => {
    if (view === "compare") return <DiffView snapshots={snaps.data ?? []} />;
    if (view === "scheduler") return <SchedulerView brandSlug={DEFAULT_BRAND} />;
    return dash.main;
  })();

  return (
    <>
      <AppShell
        topbar={
          <Topbar
            view={view}
            onViewChange={setView}
            onOpenMethodology={() => setMethodologyOpen(true)}
          />
        }
        sidebar={dash.sidebar}
        main={main}
        rightRail={view === "dashboard" ? dash.rail : null}
      />
      <MethodologyModal open={methodologyOpen} onClose={() => setMethodologyOpen(false)} />
      <Toaster
        position="bottom-right"
        theme={
          (typeof document !== "undefined" &&
            (document.documentElement.getAttribute("data-theme") as "light" | "dark")) ||
          "light"
        }
        richColors
        closeButton
      />
      {/* keep a no-op ref to i18n so a switch re-renders Suspense fallbacks */}
      <span hidden lang={i18n.language} />
    </>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Inner />
    </QueryClientProvider>
  );
}
