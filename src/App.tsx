import { useEffect, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronDown,
  ExternalLink,
  Link2,
  LockKeyhole,
  Search,
  ShieldCheck,
  Sparkles,
  Sun,
  X,
  Zap,
} from "lucide-react";
import {
  domains,
  navigationReviewed,
  projects,
  quickActions,
  sources,
  surfaces,
} from "./data/navigation";
import { ProjectCard } from "./components/ProjectCard";
import { AppShell } from "./components/AppShell";
import {
  External,
  IconBox,
  SectionHeading,
} from "./components/Shared";

function useLocalDate() {
  const [date, setDate] = useState(() => new Date());
  useEffect(() => {
    const timer = window.setInterval(() => setDate(new Date()), 60_000);
    const refresh = () => setDate(new Date());
    window.addEventListener("focus", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", refresh);
    };
  }, []);
  return date;
}

export default function App() {
  const date = useLocalDate();
  const [active, setActive] = useState(
    () => window.location.hash.slice(1) || "today",
  );
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(false);
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const matchingDomains = domains.filter((item) =>
    `${item.title} ${item.description}`
      .toLocaleLowerCase()
      .includes(normalizedQuery),
  );
  const visibleDomains =
    normalizedQuery || showAll ? matchingDomains : matchingDomains.slice(0, 8);
  useEffect(() => {
    const update = () => setActive(window.location.hash.slice(1) || "today");
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);

  return (
    <AppShell active={active} onNavigate={setActive}>
          <section
            className="welcome"
            id="today"
            aria-labelledby="welcome-title"
          >
            <div>
              <p className="eyebrow">
                <Sun size={15} aria-hidden="true" /> A LITTLE SPACE TO FOCUS
              </p>
              <h1 id="welcome-title">
                Make room for what matters<span>.</span>
              </h1>
              <p className="welcome-copy">
                Your projects, your everyday life, your next step. Start here.
              </p>
              <p className="home-identity">
                Surface type: Home / Operator Window · Domain: LifeOS
              </p>
            </div>
            <div className="date-block">
              <span>
                {new Intl.DateTimeFormat("en", { weekday: "long" }).format(
                  date,
                )}
              </span>
              <strong>
                {new Intl.DateTimeFormat("en", {
                  month: "long",
                  day: "numeric",
                }).format(date)}
              </strong>
              <small>{date.getFullYear()} · Your device’s date</small>
            </div>
          </section>

          <div className="overview-grid">
            <section className="today-panel" aria-labelledby="today-title">
              <div className="panel-heading">
                <span className="eyebrow">
                  <span className="mint-dot" /> YOUR STARTING POINT
                </span>
                <span className="quiet-badge">Private in Notion</span>
              </div>
              <div className="today-content">
                <div>
                  <h2 id="today-title">Today, with a little clarity.</h2>
                  <p>
                    Pick up your current tasks and choose what deserves your
                    attention.
                  </p>
                  <External href={sources.home} className="button primary">
                    Open today in Notion{" "}
                    <ArrowUpRight size={16} aria-hidden="true" />
                  </External>
                </div>
                <div className="orbit-art" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="orbit orbit-three" />
                  <span className="orbit-spark">
                    <Sparkles size={33} strokeWidth={1.2} />
                  </span>
                  <i className="planet one" />
                  <i className="planet two" />
                  <i className="planet three" />
                </div>
              </div>
              <div className="panel-foot">
                <LockKeyhole size={13} aria-hidden="true" /> Your task list
                stays in Notion. This page doesn’t read it.
              </div>
            </section>

            <section
              className="upcoming-panel panel"
              id="upcoming"
              aria-labelledby="upcoming-title"
            >
              <div className="panel-heading">
                <h2 id="upcoming-title">Upcoming</h2>
                <CalendarDays size={18} className="muted" aria-hidden="true" />
              </div>
              <div className="calendar-placeholder">
                <span className="calendar-symbol">
                  <CalendarDays
                    size={26}
                    strokeWidth={1.3}
                    aria-hidden="true"
                  />
                </span>
                <div>
                  <h3>Your plans live in Calendar.</h3>
                  <p>
                    Open your personal calendar for appointments and
                    commitments.
                  </p>
                </div>
              </div>
              <External href={sources.calendar} className="text-link">
                Open Google Calendar{" "}
                <ArrowUpRight size={15} aria-hidden="true" />
              </External>
              <p className="small-note">
                Calendar is not connected to this page.
              </p>
            </section>
          </div>

          <section
            className="section"
            id="projects"
            aria-labelledby="projects-title"
          >
            <SectionHeading
              id="projects-title"
              title="Active-project links"
              subtitle="Open a project for context, or its software and tools to get things done."
            >
              <External href={sources.projects} className="text-link secondary">
                All projects <ArrowUpRight size={14} aria-hidden="true" />
              </External>
            </SectionHeading>
            <div className="project-grid">
              {projects.map((item) => (
                <ProjectCard key={item.href} item={item} />
              ))}
            </div>
            <p className="source-note">
              <Link2 size={12} aria-hidden="true" />
              Navigation snapshot · reviewed {navigationReviewed} · Git-tracked
              identifies software, not live status. Private details stay at
              source.
            </p>
          </section>

          <section
            className="section"
            id="surfaces"
            aria-labelledby="surfaces-title"
          >
            <SectionHeading
              id="surfaces-title"
              title="Find your flow"
              subtitle="Familiar Surfaces. The original records, right where they belong."
            >
              <span className="section-kicker">SURFACES</span>
            </SectionHeading>
            <div className="surface-grid">
              {surfaces.map((item) => (
                <External
                  key={item.href}
                  href={item.href}
                  className="surface-card"
                >
                  <IconBox icon={item.icon} tone={item.tone} />
                  <div>
                    <h3>
                      {item.title} <ArrowUpRight size={14} aria-hidden="true" />
                    </h3>
                    <p>{item.description}</p>
                    <span className="surface-identity">
                      Surface type: {item.type} · Domain: {item.domain}
                    </span>
                  </div>
                </External>
              ))}
            </div>
          </section>

          <div className="lower-grid">
            <section
              className="section domains-section"
              id="domains"
              aria-labelledby="domains-title"
            >
              <SectionHeading
                id="domains-title"
                title="Life domains"
                subtitle="A place for every part of your personal life."
              />
              <div className="search-field">
                <Search size={16} aria-hidden="true" />
                <input
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Find a domain…"
                  aria-label="Find a life domain"
                />
                {query && (
                  <button
                    className="clear-search"
                    onClick={() => setQuery("")}
                    aria-label="Clear domain search"
                  >
                    <X size={15} aria-hidden="true" />
                  </button>
                )}
              </div>
              <div className="domain-grid">
                {visibleDomains.map((item) => (
                  <External
                    key={item.href}
                    href={item.href}
                    className="domain-card"
                  >
                    <IconBox icon={item.icon} tone={item.tone} small />
                    <span>{item.title}</span>
                    <ArrowUpRight
                      size={13}
                      className="outbound"
                      aria-hidden="true"
                    />
                  </External>
                ))}
              </div>
              <p className="sr-only" role="status" aria-live="polite">
                {visibleDomains.length} domains shown
              </p>
              {visibleDomains.length === 0 && (
                <div className="empty-search">
                  <p>No domain matches “{query}”.</p>
                  <button className="text-button" onClick={() => setQuery("")}>
                    Show all domains
                  </button>
                </div>
              )}
              {!normalizedQuery && (
                <button
                  className="show-more"
                  onClick={() => setShowAll((value) => !value)}
                  aria-expanded={showAll}
                >
                  {showAll ? "Show fewer domains" : "Explore all domains"}
                  <ChevronDown
                    size={15}
                    className={showAll ? "rotated" : ""}
                    aria-hidden="true"
                  />
                </button>
              )}
            </section>

            <section
              className="section actions-section"
              id="actions"
              aria-labelledby="actions-title"
            >
              <SectionHeading
                id="actions-title"
                title="Quick actions"
                subtitle="Catch a thought. Take the next step."
              />
              <div className="action-list">
                {quickActions.map((item) => (
                  <External
                    href={item.href}
                    key={item.title}
                    className="action-row"
                  >
                    <IconBox icon={item.icon} tone={item.tone} small />
                    <div>
                      <h3>{item.title}</h3>
                      <p>{item.description}</p>
                    </div>
                    <ArrowUpRight
                      size={15}
                      className="outbound"
                      aria-hidden="true"
                    />
                  </External>
                ))}
              </div>
              <p className="small-note action-note">
                <ExternalLink size={12} aria-hidden="true" />
                Shortcuts open the original app. Create and save there.
              </p>
            </section>
          </div>

          <section
            className="section system-section"
            id="system"
            aria-labelledby="system-title"
          >
            <SectionHeading
              id="system-title"
              title="System overview"
              subtitle="A clear view of what this page actually does."
            >
              <span className="quiet-badge">
                <ShieldCheck size={12} aria-hidden="true" />
                Public-safe navigation
              </span>
            </SectionHeading>
            <div className="system-grid">
              <div className="system-item">
                <span className="system-icon">
                  <Check size={16} aria-hidden="true" />
                </span>
                <div>
                  <h3>
                    Navigation{" "}
                    <span className="status-pill available">Available</span>
                  </h3>
                  <p>Curated links to existing personal destinations.</p>
                </div>
              </div>
              <div className="system-item">
                <span className="system-icon neutral">
                  <Link2 size={16} aria-hidden="true" />
                </span>
                <div>
                  <h3>
                    Live data <span className="status-pill">Not connected</span>
                  </h3>
                  <p>No task, calendar, or project data is fetched.</p>
                </div>
              </div>
              <div className="system-item">
                <span className="system-icon neutral">
                  <Zap size={16} aria-hidden="true" />
                </span>
                <div>
                  <h3>
                    Automation{" "}
                    <span className="status-pill">Not monitored</span>
                  </h3>
                  <p>This page doesn’t run or check automations.</p>
                </div>
              </div>
            </div>
            <div className="system-bottom">
              <span>
                <LockKeyhole size={13} aria-hidden="true" />
                Notion access is managed by Notion. Private destinations may
                require sign-in.
              </span>
              <External
                href={sources.governance}
                className="text-link secondary"
              >
                Surface governance <ArrowUpRight size={13} aria-hidden="true" />
              </External>
            </div>
          </section>


          <a className="back-top" href="#today">
            <ArrowDown size={13} className="rotated" aria-hidden="true" />
            Back to top
            <ArrowRight size={12} aria-hidden="true" />
          </a>
    </AppShell>
  );
}
