export type Tone = "mint" | "blue" | "lilac" | "amber" | "rose";
export interface ModuleDefinition {
  id: string;
  label: string;
  contextURL: string;
  launchURL?: string;
  access: "public-navigation" | "authenticated";
  icon: "wine" | "health";
  tone: Tone;
}
export interface SectionNavigation { id: string; label: string }
