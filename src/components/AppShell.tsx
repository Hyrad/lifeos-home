import type { ReactNode } from "react";
import { Sidebar, Topbar, Footer } from "./Shared";
import { MobileSectionNavigation } from "./ModuleNavigation";
export function AppShell({ active, onNavigate, children }: {
  active: string; onNavigate: (id: string) => void; children: ReactNode;
}) {
  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <Sidebar active={active} onNavigate={onNavigate} />
    <div className="app-shell"><Topbar />
      <MobileSectionNavigation active={active} onNavigate={onNavigate} />
      <main id="main" tabIndex={-1}>{children}<Footer /></main>
    </div>
  </>;
}
