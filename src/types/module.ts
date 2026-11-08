export type Tone = "mint" | "blue" | "lilac" | "amber" | "rose";
export type PublicationRoute =
  | { visibility: "public-safe"; url: string }
  | { visibility: "authenticated-only" | "internal" | "pending-review"; url?: never };

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
    role: "operator window" | "workstream" | "development surface" | "planner" | "project" | "area" | "reference" | "tracker" | "unverified";
    route: PublicationRoute;
  };
  application?: {
    status: "live" | "planned" | "blocked" | "unverified";
    installation: "standalone-manifest" | "browser-shortcut" | "unverified";
    route: PublicationRoute;
  };
  placement: readonly ("apps" | "workstreams")[];
  related?: readonly string[];
  fallback?: "notion-launcher";
  evidence: string;
  verifiedOn: string;
}
