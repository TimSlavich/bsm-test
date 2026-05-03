import type { ReactNode } from "react";

interface AppShellProps {
  topbar: ReactNode;
  sidebar: ReactNode;
  main: ReactNode;
  rightRail?: ReactNode;
}

export function AppShell({ topbar, sidebar, main, rightRail }: AppShellProps) {
  return (
    <div className="shell" data-has-rail={rightRail ? "true" : undefined}>
      <div className="shell__topbar">{topbar}</div>
      <aside className="shell__sidebar">{sidebar}</aside>
      <main className="shell__main">{main}</main>
      {rightRail && <aside className="shell__rail">{rightRail}</aside>}
    </div>
  );
}
