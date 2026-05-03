import { Activity, BookOpen, CalendarClock, GitCompare, LayoutDashboard } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { ReactNode } from "react";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { ThemeToggle } from "./ThemeToggle";

export type View = "dashboard" | "compare" | "scheduler";

interface TopbarProps {
  view: View;
  onViewChange: (v: View) => void;
  onOpenMethodology: () => void;
  rightSlot?: ReactNode;
}

export function Topbar({ view, onViewChange, onOpenMethodology, rightSlot }: TopbarProps) {
  const { t } = useTranslation();

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <span className="topbar__logo" aria-hidden>
          <Activity size={18} />
        </span>
        <div>
          <div className="topbar__title">{t("app.title")}</div>
          <div className="topbar__subtitle">{t("app.subtitle")}</div>
        </div>
      </div>

      <nav className="topbar__nav" aria-label="Primary">
        <button
          type="button"
          className="topbar__navlink"
          data-active={view === "dashboard" || undefined}
          onClick={() => onViewChange("dashboard")}
        >
          <LayoutDashboard size={14} />
          {t("nav.dashboard")}
        </button>
        <button
          type="button"
          className="topbar__navlink"
          data-active={view === "compare" || undefined}
          onClick={() => onViewChange("compare")}
        >
          <GitCompare size={14} />
          {t("nav.compare")}
        </button>
        <button
          type="button"
          className="topbar__navlink"
          data-active={view === "scheduler" || undefined}
          onClick={() => onViewChange("scheduler")}
        >
          <CalendarClock size={14} />
          {t("nav.scheduler")}
        </button>
        <button type="button" className="topbar__navlink" onClick={onOpenMethodology}>
          <BookOpen size={14} />
          {t("nav.methodology")}
        </button>
      </nav>

      <div className="topbar__right">
        {rightSlot}
        <LanguageSwitcher />
        <ThemeToggle />
      </div>
    </header>
  );
}
