import type { ModuleDefinition } from "../types/module";

export const winePageURL = "https://hyrad.github.io/lifeos-wine-production/";
export const journeyPageURL = "https://hyrad.github.io/journey-tracker/";
export const notionLauncherURL = "https://app.notion.com/login";

const reviewedOn = "2026-11-08";
const privateRecord = { visibility: "authenticated-only" } as const;
const privateApp = {
  status: "live",
  installation: "unverified",
  route: privateRecord,
} as const;
const directoryEntry = {
  placement: ["workstreams"],
  fallback: "notion-launcher",
  verifiedOn: reviewedOn,
} as const;

// This is the public projection. The review inventory lives in the private
// LifeOS checkpoint. Restricted routes here carry a classification only.
export const navigationManifest = {
  version: 1,
  modules: [
    {
      ...directoryEntry,
      id: "lifeos", label: "LifeOS Home", description: "Shared navigation and governance.",
      domain: "LifeOS", icon: "compass", tone: "mint", status: "active",
      canonical: { owner: "lifeos", role: "operator window", route: privateRecord },
      evidence: "LifeOS Home and shared module directory",
    },
    {
      ...directoryEntry,
      id: "wine", label: "Wine Production", description: "Winemaking guides and workspace.",
      domain: "Food & drink", icon: "wine", tone: "rose", status: "active",
      canonical: { owner: "area", role: "operator window", route: privateRecord },
      application: { status: "live", installation: "standalone-manifest", route: { visibility: "public-safe", url: winePageURL } },
      placement: ["apps", "workstreams"],
      evidence: "LifeOS Home and live GitHub Pages site and manifest",
    },
    {
      ...directoryEntry,
      id: "travel", label: "Journey Tracker", description: "Explore the published travel tracker.",
      domain: "Travel", icon: "travel", tone: "blue", status: "active",
      canonical: { owner: "area", role: "planner", route: privateRecord },
      application: { status: "live", installation: "standalone-manifest", route: { visibility: "public-safe", url: journeyPageURL } },
      placement: ["apps", "workstreams"],
      evidence: "Travel owner and public tracker release, live site and manifest",
    },
    {
      ...directoryEntry,
      id: "health", label: "Health", description: "Personal wellbeing.",
      domain: "Wellbeing", icon: "health", tone: "mint", status: "active",
      canonical: { owner: "area", role: "area", route: privateRecord },
      application: privateApp, related: ["fitness"],
      evidence: "Health owner and shared module directory",
    },
    {
      ...directoryEntry,
      id: "fitness", label: "Fitness", description: "Movement and training.",
      domain: "Wellbeing", icon: "fitness", tone: "mint", status: "active",
      canonical: { owner: "project", role: "project", route: privateRecord },
      related: ["health"],
      evidence: "Shared module directory",
    },
    {
      ...directoryEntry,
      id: "music", label: "Music", description: "Creative development and practice.",
      domain: "Creative", icon: "music", tone: "amber", status: "active",
      canonical: { owner: "project", role: "workstream", route: privateRecord },
      application: privateApp,
      evidence: "Music owner and Creative Dashboard",
    },
    {
      ...directoryEntry,
      id: "game-shelf", label: "Game Shelf", description: "Personal game library.",
      domain: "Games", icon: "game", tone: "lilac", status: "active",
      canonical: { owner: "project", role: "development surface", route: privateRecord },
      application: { status: "blocked", installation: "unverified", route: { visibility: "pending-review" } },
      evidence: "Game Shelf owner and development surface",
    },
    {
      ...directoryEntry,
      id: "family-technology", label: "Family technology", description: "Family technology projects.",
      domain: "Home", icon: "family", tone: "rose", status: "active",
      canonical: { owner: "project", role: "workstream", route: privateRecord },
      application: { status: "unverified", installation: "unverified", route: { visibility: "pending-review" } },
      evidence: "Shared module directory",
    },
    {
      ...directoryEntry,
      id: "game-development", label: "Game development", description: "Game creation and learning.",
      domain: "Games", icon: "game", tone: "lilac", status: "planned",
      canonical: { owner: "project", role: "project", route: privateRecord },
      evidence: "Shared module directory",
    },
    {
      ...directoryEntry,
      id: "cooking", label: "Cooking", description: "Recipe and cooking references.",
      domain: "Food & drink", icon: "food", tone: "amber", status: "active",
      canonical: { owner: "area", role: "reference", route: privateRecord },
      related: ["shopping"], evidence: "Cuisine owner and Cookbook",
    },
    {
      ...directoryEntry,
      id: "shopping", label: "Shopping", description: "Shopping surfaces.",
      domain: "Home", icon: "shopping", tone: "blue", status: "active",
      canonical: { owner: "area", role: "tracker", route: privateRecord },
      related: ["cooking"], evidence: "LifeOS Home and Shopping Hub",
    },
    {
      ...directoryEntry,
      id: "casino-academy", label: "CasinoAcademy", description: "Casino game education project.",
      domain: "Games", icon: "development", tone: "lilac", status: "planned",
      canonical: { owner: "project", role: "workstream", route: privateRecord },
      application: privateApp, evidence: "CasinoAcademy owner and development workstream",
    },
    {
      id: "founder", label: "Founder workspace", description: "Personal founder workspace.",
      domain: "Personal", icon: "development", tone: "blue", status: "unverified",
      canonical: { owner: "unverified", role: "unverified", route: { visibility: "internal" } },
      application: { status: "unverified", installation: "unverified", route: { visibility: "pending-review" } },
      placement: ["workstreams"], evidence: "Shared module directory and mission handoff", verifiedOn: reviewedOn,
    },
  ],
} satisfies { version: number; modules: readonly ModuleDefinition[] };

export const modules: readonly ModuleDefinition[] = navigationManifest.modules;

export function publicLaunchURL(module: ModuleDefinition) {
  const app = module.application;
  return app?.status === "live" && app.route.visibility === "public-safe" ? app.route.url : undefined;
}

export const homeSections = [
  { id: "today", label: "Overview" }, { id: "apps", label: "Apps" },
  { id: "workstreams", label: "Workstreams" }, { id: "projects", label: "Projects" },
  { id: "surfaces", label: "Surfaces" }, { id: "domains", label: "Life domains" },
  { id: "system", label: "System overview" },
] as const;
