import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  ArrowUpRight,
  Compass,
  Grid2X2,
  House,
  Layers3,
  ShieldCheck,
  Wine,
} from "lucide-react";
import { version } from "../../package.json";
import { sources } from "../data/navigation";
import { winePageURL } from "../data/modules";

export function External({
  href,
  children,
  className = "",
  ...rest
}: {
  href: string;
  children: ReactNode;
  className?: string;
  "aria-label"?: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      {...rest}
    >
      {children}
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}

export function IconBox({
  icon: Icon,
  tone = "mint",
  small = false,
}: {
  icon: LucideIcon;
  tone?: string;
  small?: boolean;
}) {
  return (
    <span className={`icon-box ${tone} ${small ? "small" : ""}`}>
      <Icon size={small ? 18 : 21} strokeWidth={1.65} aria-hidden="true" />
    </span>
  );
}

export function SectionHeading({
  id,
  title,
  subtitle,
  children,
}: {
  id: string;
  title: string;
  subtitle?: string;
  children?: ReactNode;
}) {
  return (
    <div className="section-heading">
      <div>
        <h2 id={id}>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

const navItems = [
  { id: "today", label: "Overview", icon: House },
  { id: "projects", label: "Projects", icon: Layers3 },
  { id: "surfaces", label: "Surfaces", icon: Grid2X2 },
  { id: "domains", label: "Life domains", icon: Compass },
  { id: "system", label: "System overview", icon: ShieldCheck },
];

export function Sidebar({
  active,
  onNavigate,
}: {
  active: string;
  onNavigate?: (id: string) => void;
}) {
  return (
    <aside className="sidebar" aria-label="LifeOS navigation">
      <a className="brand" href="#today">
        <span className="brand-mark">
          <Compass size={23} strokeWidth={1.5} aria-hidden="true" />
        </span>
        <span>
          Life<span className="brand-os">OS</span>
          <small>YOUR PERSONAL SPACE</small>
        </span>
      </a>
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Main navigation">
        {navItems.map(({ id, label, icon: Icon }) => (
          <a
            key={id}
            href={`#${id}`}
            className={active === id ? "nav-item selected" : "nav-item"}
            aria-current={active === id ? "location" : undefined}
            onClick={() => onNavigate?.(id)}
          >
            <Icon size={18} strokeWidth={1.7} aria-hidden="true" />
            {label}
            {active === id && <span className="nav-dot" />}
          </a>
        ))}
        <a href={winePageURL} className="nav-item">
          <Wine size={18} strokeWidth={1.7} aria-hidden="true" />
          Wine Production
        </a>
      </nav>
      <div className="sidebar-bottom">
        <div className="workspace-note">
          <span className="tiny-label">A PLACE FOR PERSONAL LIFE</span>
          <p>
            One starting point.
            <br />
            Everything in its place.
          </p>
          <External href={sources.home}>
            Open Notion Home <ArrowUpRight size={14} aria-hidden="true" />
          </External>
        </div>
        <div className="profile">
          <span className="profile-avatar">
            <Compass size={18} aria-hidden="true" />
          </span>
          <div>
            Personal workspace
            <small>
              LifeOS Home <span>v{version}</span>
            </small>
          </div>
        </div>
      </div>
    </aside>
  );
}
export function Topbar() {
  return (
    <header className="topbar">
      <div>
        <>
          <span className="breadcrumb">Personal workspace</span>
          <span className="breadcrumb-slash">/</span>
          <span>Home</span>
        </>
      </div>
      <div className="release-info">
        <span className="mode-badge">
          <span />
          Navigation edition
        </span>
        <span className="release-version" title="App version">
          v{version}
        </span>
      </div>
    </header>
  );
}
export function Footer() {
  return (
    <footer>
      <div className="footer-wordmark">
        <Compass size={15} aria-hidden="true" />
        LifeOS Home <span>v{version}</span>
      </div>
      <p>Personal life, with a little more intention.</p>
      <External href={sources.root}>
        Life Command Center <ArrowUpRight size={12} aria-hidden="true" />
      </External>
    </footer>
  );
}
