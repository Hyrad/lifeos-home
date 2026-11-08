import { describe, expect, it } from "vitest";
import { modules, navigationManifest, publicLaunchURL } from "./modules";

describe("public navigation manifest", () => {
  it("versions the contract and requires stable IDs, display fields and evidence", () => {
    expect(navigationManifest.version).toBe(1);
    const ids = new Set(modules.map(module => module.id));
    expect(ids.size).toBe(modules.length);
    for (const module of modules) {
      expect(module.id).toMatch(/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/);
      for (const field of [module.label, module.description, module.domain, module.icon, module.evidence]) {
        expect(field.trim()).not.toBe("");
      }
      expect(module.verifiedOn).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(module.placement.length).toBeGreaterThan(0);
      expect(module.canonical.owner).toBeTruthy();
      expect(module.canonical.role).toBeTruthy();
      for (const related of module.related ?? []) {
        expect(related).not.toBe(module.id);
        expect(ids.has(related)).toBe(true);
      }
    }
  });

  it("has HTTPS public app launches only and never serializes restricted URLs", () => {
    const allowed = [
      "https://hyrad.github.io/lifeos-wine-production/",
      "https://hyrad.github.io/journey-tracker/",
    ];
    const launches = [];
    for (const module of modules) {
      const launch = publicLaunchURL(module);
      expect(module.placement.includes("apps")).toBe(Boolean(launch));
      for (const route of [module.application?.route, module.canonical.route]) {
        if (route?.visibility === "public-safe") {
          const url = new URL(route.url);
          expect(url.protocol).toBe("https:");
          expect(url.username + url.password + url.search + url.hash).toBe("");
          expect(allowed).toContain(route.url);
        } else if (route) {
          expect(route).not.toHaveProperty("url");
        }
      }
      if (launch) launches.push(launch);
    }
    expect(launches).toEqual(allowed);
    expect(JSON.stringify(navigationManifest)).not.toMatch(/notion\.(?:so|com)\/p\/|chatgpt\.site|[a-f\d]{32}/i);
  });

  it("keeps a generic fallback for restricted and absent launch routes", () => {
    const health = modules.find(module => module.id === "health")!;
    const cooking = modules.find(module => module.id === "cooking")!;
    for (const module of [health, cooking]) {
      expect(publicLaunchURL(module)).toBeUndefined();
      expect(module.fallback).toBe("notion-launcher");
    }
  });
});
