import { describe, it, expect } from "vitest";
import { modules, moduleDestination } from "./modules";
describe("module contract", () => {
  it("has unique IDs and only approved public destinations", () => {
    expect(new Set(modules.map(m => m.id)).size).toBe(modules.length);
    for (const m of modules) {
      expect(["public-navigation", "authenticated"]).toContain(m.access);
      expect(new URL(m.contextURL).origin).toBe("https://app.notion.com");
      expect(["https://hyrad.github.io/lifeos-wine-production/", "https://hyrad-lifeos-health.newpeach71.chatgpt.site"]).toContain(moduleDestination(m));
    }
  });
  it("falls back to context when no launch URL exists", () => {
    const { launchURL: _, ...m } = modules[0];
    expect(moduleDestination(m)).toBe(m.contextURL);
  });
});
