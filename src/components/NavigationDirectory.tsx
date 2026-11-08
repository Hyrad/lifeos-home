import {
  ArrowUpRight, Compass, Dumbbell, Gamepad2, HeartPulse, Layers3,
  Music2, Plane, ShoppingBag, Soup, Users, Wine,
} from "lucide-react";
import { modules, notionLauncherURL, publicLaunchURL, routeAccessLabel } from "../data/modules";
import { External, IconBox, SectionHeading } from "./Shared";

const icons = {
  compass: Compass, wine: Wine, travel: Plane, health: HeartPulse,
  fitness: Dumbbell, music: Music2, game: Gamepad2, food: Soup,
  shopping: ShoppingBag, family: Users, development: Layers3,
};

const appState = {
  live: "Live app",
  planned: "App planned",
  blocked: "App blocked",
  unverified: "App availability unverified",
};

export function NavigationDirectory() {
  return (
    <>
      <section className="section" id="apps" aria-labelledby="apps-title">
        <SectionHeading id="apps-title" title="Apps" subtitle="Open a LifeOS app. Some apps require sign-in." />
        <div className="surface-grid">
          {modules.filter(module => module.placement.includes("apps")).map(module => {
            const url = publicLaunchURL(module);
            if (!url) return null;
            return (
              <a className="surface-card" key={module.id} href={url}>
                <IconBox icon={icons[module.icon]} tone={module.tone} />
                <div>
                  <h3>Open {module.label} <ArrowUpRight size={14} aria-hidden="true" /></h3>
                  <p>{module.description} {module.application?.route.visibility === "approved-authenticated-launch" && "Sign-in required."}</p>
                </div>
              </a>
            );
          })}
        </div>
      </section>
      <section className="section" id="workstreams" aria-labelledby="workstreams-title">
        <SectionHeading
          id="workstreams-title"
          title="Workstreams"
          subtitle="Find canonical Notion records and launch approved apps. Records without a direct link require a separate lookup."
        />
        <External href={notionLauncherURL} className="button directory-notion">
          Open Notion to find records <ArrowUpRight size={16} aria-hidden="true" />
        </External>
        <ul className="directory-list">
          {modules.filter(module => module.placement.includes("workstreams")).map(module => {
            const { canonical, application } = module;
            const launch = publicLaunchURL(module);
            const appLabel = application?.label ?? module.label;
            return (
              <li key={module.id}>
                <IconBox icon={icons[module.icon]} tone={module.tone} small />
                <div>
                  <h3>{canonical.label ?? module.label}</h3>
                  {canonical.route.visibility === "public-safe" ? (
                    <External href={canonical.route.url} className="text-link">Open Notion {canonical.role}</External>
                  ) : (
                    <p>{canonical.role === "unverified"
                      ? "Canonical record unverified"
                      : `Notion ${canonical.role} · ${routeAccessLabel(canonical.route)}`}</p>
                  )}
                  {launch ? (
                    <>
                      <a href={launch} className="text-link">
                        Open {appLabel} app <ArrowUpRight size={14} aria-hidden="true" />
                      </a>
                      {application?.route.visibility === "approved-authenticated-launch" && <p>Sign-in required.</p>}
                    </>
                  ) : (
                    <p>{application
                      ? <>{application.label && `${application.label} · `}{appState[application.status]} · {routeAccessLabel(application.route)}</>
                      : "No separate app listed"}</p>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </section>
    </>
  );
}
