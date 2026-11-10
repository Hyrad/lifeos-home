import type { ApplicationRoute, Deployment, ModuleDefinition } from "../types/module";

export const winePageURL = "https://hyrad.github.io/lifeos-wine-production/";
export const journeyPageURL = "https://hyrad.github.io/journey-tracker/";
export const healthAppURL = "https://hyrad-lifeos-health.newpeach71.chatgpt.site";
export const notionLauncherURL = "https://app.notion.com/login";

// NAV-05 explicitly approved disclosure of these four exact addresses.
export const approvedNotionRoutes = {
  wine: { visibility: "public-safe", url: "https://app.notion.com/p/472be780ce1a8247b9ed8166a00fb5ad" },
  travel: { visibility: "public-safe", url: "https://app.notion.com/p/da5be780ce1a8235816401a81385ef36" },
  cookbook: { visibility: "public-safe", url: "https://app.notion.com/p/3f1be780ce1a81f68849e982dfcc4922" },
  shopping: { visibility: "public-safe", url: "https://app.notion.com/p/3f7be780ce1a81a999acce540ad4d095" },
} as const;

const reviewedOn = "2026-11-08";
export const privateRecord = { visibility: "authenticated-only" } as const;
export const publicationReview = { visibility: "publication-review" } as const;
const unverifiedRoute = { visibility: "pending-review" } as const;

export function routeAccessLabel(route: ApplicationRoute) {
  return {
    "public-safe": "Direct link available",
    "approved-authenticated-launch": "Sign-in required",
    "publication-review": "Direct link needs publication approval",
    "authenticated-only": "Private link requires authenticated delivery",
    "pending-review": "Destination unverified",
    "private-deployment": "Opens from the private LifeOS server",
  }[route.visibility];
}
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
      id: "lifeos", label: "LifeOS planning & governance", description: "Shared navigation and governance.",
      domain: "LifeOS", icon: "compass", tone: "mint", status: "active",
      canonical: { owner: "lifeos", role: "operator window", route: privateRecord },
      evidence: "LifeOS Home and shared module directory",
    },
    {
      ...directoryEntry,
      id: "wine", label: "Wine Production", description: "Winemaking guides and workspace.",
      domain: "Food & drink", icon: "wine", tone: "rose", status: "active",
      canonical: { owner: "area", role: "area", label: "Wine Making Area", route: approvedNotionRoutes.wine },
      application: { status: "live", installation: "standalone-manifest", route: { visibility: "public-safe", url: winePageURL } },
      placement: ["apps", "workstreams"],
      evidence: "LifeOS Home and live GitHub Pages site and manifest",
    },
    {
      ...directoryEntry,
      id: "travel", label: "Journey Tracker", description: "Explore the published travel tracker.",
      domain: "Travel", icon: "travel", tone: "blue", status: "active",
      canonical: { owner: "area", role: "area", label: "Travel Area", route: approvedNotionRoutes.travel },
      application: { status: "live", installation: "standalone-manifest", route: { visibility: "public-safe", url: journeyPageURL } },
      placement: ["apps", "workstreams"],
      evidence: "Travel owner and public tracker release, live site and manifest",
    },
    {
      ...directoryEntry,
      id: "health", label: "Health", description: "Personal wellbeing.",
      domain: "Wellbeing", icon: "health", tone: "mint", status: "active",
      canonical: { owner: "area", role: "area", label: "Health & Medical", route: privateRecord },
      application: { ...privateApp, route: { visibility: "approved-authenticated-launch", url: healthAppURL } },
      placement: ["apps", "workstreams"], related: ["fitness"],
      evidence: "Health owner and approved Home v0.2.1 app launch",
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
      canonical: { owner: "project", role: "workstream", label: "Music Creative Dashboard", route: publicationReview },
      application: privateApp,
      evidence: "Music owner and Creative Dashboard",
    },
    {
      ...directoryEntry,
      id: "game-shelf", label: "Game Shelf", description: "Personal game library.",
      domain: "Games", icon: "game", tone: "lilac", status: "active",
      canonical: { owner: "project", role: "development surface", label: "Game Shelf Development", route: publicationReview },
      application: { status: "blocked", installation: "unverified", route: unverifiedRoute },
      evidence: "Game Shelf owner and development surface",
    },
    {
      ...directoryEntry,
      id: "family-technology", label: "Family technology", description: "Family technology projects.",
      domain: "Home", icon: "family", tone: "rose", status: "active",
      canonical: { owner: "project", role: "workstream", route: privateRecord },
      application: { status: "unverified", installation: "unverified", route: unverifiedRoute },
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
      id: "cooking", label: "Cooking", description: "Kitchen companion: guided recipes, servings and timers.",
      domain: "Food & drink", icon: "food", tone: "amber", status: "active",
      canonical: { owner: "area", role: "reference", label: "Cooking / Cookbook", route: approvedNotionRoutes.cookbook, linkSection: "surfaces" },
      // LIFEOS-COOK-03: independent app, privately hosted (COOK-02) and accepted
      // on iPad. Launchable only from the private-server build; the public
      // build lists it without a link and never contains a hostname.
      application: {
        label: "LifeOS Cooking", status: "live", installation: "standalone-manifest",
        route: { visibility: "private-deployment", path: "/lifeos-cooking/" },
      },
      placement: ["apps", "workstreams"],
      related: ["shopping"], evidence: "Cuisine owner, Cookbook and LifeOS Cooking private deployment (COOK-02)",
    },
    {
      ...directoryEntry,
      id: "shopping", label: "Shopping", description: "Shopping surfaces.",
      domain: "Home", icon: "shopping", tone: "blue", status: "active",
      canonical: { owner: "area", role: "tracker", label: "Shopping Hub", route: approvedNotionRoutes.shopping, linkSection: "surfaces" },
      related: ["cooking"], evidence: "LifeOS Home and Shopping Hub",
    },
    {
      ...directoryEntry,
      id: "casino-academy", label: "CasinoAcademy", description: "Casino game education project.",
      domain: "Games", icon: "development", tone: "lilac", status: "planned",
      canonical: { owner: "project", role: "workstream", label: "CasinoAcademy Development", route: publicationReview },
      application: { ...privateApp, label: "Development Command Center" }, evidence: "CasinoAcademy owner and development workstream",
    },
    {
      id: "founder", label: "Founder workspace", description: "Personal founder workspace.",
      domain: "Personal", icon: "development", tone: "blue", status: "unverified",
      canonical: { owner: "unverified", role: "unverified", route: unverifiedRoute },
      application: { ...privateApp, route: unverifiedRoute },
      placement: ["workstreams"], evidence: "Shared module directory and mission handoff", verifiedOn: reviewedOn,
    },
  ],
} satisfies { version: number; modules: readonly ModuleDefinition[] };

export const modules: readonly ModuleDefinition[] = navigationManifest.modules;

export function publicLaunchURL(module: ModuleDefinition) {
  const app = module.application;
  if (app?.status !== "live") return undefined;
  if (app.route.visibility === "public-safe" || app.route.visibility === "approved-authenticated-launch") {
    return app.route.url;
  }
}

// Build-time deployment. GitHub Pages builds are "public" (the default); only
// the private LifeOS server release sets VITE_LIFEOS_DEPLOYMENT=private-server.
export function currentDeployment(): Deployment {
  return import.meta.env.VITE_LIFEOS_DEPLOYMENT === "private-server" ? "private-server" : "public";
}

/** Launch address for this deployment: approved URLs everywhere, same-origin private paths only on the server. */
export function launchURL(module: ModuleDefinition, deployment: Deployment = currentDeployment()) {
  const app = module.application;
  if (app?.status === "live" && app.route.visibility === "private-deployment") {
    return deployment === "private-server" ? app.route.path : undefined;
  }
  return publicLaunchURL(module);
}

/** Apps entries that cannot launch from this deployment but should stay discoverable. */
export function isPrivateServerApp(module: ModuleDefinition) {
  return module.application?.route.visibility === "private-deployment";
}

export const homeSections = [
  { id: "today", label: "Overview" }, { id: "apps", label: "Apps" },
  { id: "workstreams", label: "Workstreams" }, { id: "projects", label: "Projects" },
  { id: "actions", label: "Core LifeOS" }, { id: "domains", label: "Life domains" },
  { id: "surfaces", label: "Surfaces" },
  { id: "system", label: "System overview" },
] as const;
