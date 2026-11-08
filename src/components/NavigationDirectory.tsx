import {
  ArrowUpRight, Compass, Dumbbell, Gamepad2, HeartPulse, Layers3,
  Music2, Plane, ShoppingBag, Soup, Users, Wine,
} from "lucide-react";
import { modules, notionLauncherURL, publicLaunchURL } from "../data/modules";
import { External, IconBox, SectionHeading } from "./Shared";

const icons = {
  compass: Compass, wine: Wine, travel: Plane, health: HeartPulse,
  fitness: Dumbbell, music: Music2, game: Gamepad2, food: Soup,
  shopping: ShoppingBag, family: Users, development: Layers3,
};

export function NavigationDirectory() {
  return (
    <>
      <section className="section" id="apps" aria-labelledby="apps-title">
        <SectionHeading id="apps-title" title="Apps" subtitle="Launch a public LifeOS application." />
        <div className="surface-grid">
          {modules.filter(module => module.placement.includes("apps")).map(module => {
            const url = publicLaunchURL(module);
            if (!url) return null;
            return (
              <a className="surface-card" key={module.id} href={url}>
                <IconBox icon={icons[module.icon]} tone={module.tone} />
                <div>
                  <h3>Open {module.label} <ArrowUpRight size={14} aria-hidden="true" /></h3>
                  <p>{module.description}</p>
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
          subtitle="Find project records and working surfaces by module. Sign in to Notion and open LifeOS Home to reach your private records."
        />
        <External href={notionLauncherURL} className="button directory-notion">
          Open Notion <ArrowUpRight size={16} aria-hidden="true" />
        </External>
        <ul className="directory-list">
          {modules.filter(module => module.placement.includes("workstreams")).map(module => (
            <li key={module.id}>
              <IconBox icon={icons[module.icon]} tone={module.tone} small />
              <div>
                <h3>{module.label}</h3>
                {module.canonical.route.visibility === "public-safe" ? (
                  <External href={module.canonical.route.url} className="text-link" aria-label={`Open ${module.label} canonical record in Notion (opens in a new tab)`}>
                    Open canonical record <ArrowUpRight size={14} aria-hidden="true" />
                  </External>
                ) : (
                  <p>{module.fallback === "notion-launcher" ? `Private ${module.canonical.role}` : "Private access required"}</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
