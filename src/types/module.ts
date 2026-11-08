export type Tone = "mint" | "blue" | "lilac" | "amber" | "rose";
export type PublicationRoute =
  | { visibility: "public-safe"; url: string }
  | { visibility: "authenticated-only" | "publication-review" | "pending-review"; url?: never };

export type ApplicationRoute = PublicationRoute | { visibility: "approved-authenticated-launch"; url: string };

export interface ModuleDefinition {
  id: string;
  label: string;
  description: string;
  domain: string;
  icon: "compass" | "wine" | "travel" | "health" | "fitness" | "music" | "game" | "food" | "shopping" | "family" | "development";
  tone: Tone;
  status: "active" | "planned" | "blocked" | "retired" | "unverified";
  canonical: {
    owner: "area" | "project" | "lifeos" | "unverified";
    label?: string;
    role: "operator window" | "workstream" | "development surface" | "planner" | "project" | "area" | "reference" | "tracker" | "unverified";
    route: PublicationRoute;
  };
  application?: {
    label?: string;
    status: "live" | "planned" | "blocked" | "unverified";
    installation: "standalone-manifest" | "browser-shortcut" | "unverified";
    route: ApplicationRoute;
  };
  placement: readonly ("apps" | "workstreams")[];
  related?: readonly string[];
  fallback?: "notion-launcher";
  evidence: string;
  verifiedOn: string;
}
