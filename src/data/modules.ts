import type { ModuleDefinition, SectionNavigation } from "../types/module";
// Curated public metadata only. Access classification is not runtime authorization.
export const modules = [{
  id: "wine", label: "Wine Production",
  contextURL: "https://app.notion.com/p/472be780ce1a8247b9ed8166a00fb5ad",
  launchURL: "https://hyrad.github.io/lifeos-wine-production/",
  access: "public-navigation", icon: "wine", tone: "rose",
}, { id: "health", label: "Health", contextURL: "https://app.notion.com/p/957be780ce1a825cb7e50128aad57075", launchURL: "https://hyrad-lifeos-health.newpeach71.chatgpt.site", access: "authenticated", icon: "health", tone: "mint" }] as const satisfies readonly ModuleDefinition[];
export const winePageURL = modules[0].launchURL;
export const moduleDestination = (module: ModuleDefinition) => module.launchURL ?? module.contextURL;
export const homeSections: readonly SectionNavigation[] = [
  { id: "today", label: "Overview" }, { id: "projects", label: "Projects" },
  { id: "surfaces", label: "Surfaces" }, { id: "domains", label: "Life domains" },
  { id: "system", label: "System overview" },
];

export const homePagePath = "/lifeos-home/";
