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

  it("exposes only approved app launch URLs and keeps canonical records private", () => {
    const allowed = [
      "https://hyrad.github.io/lifeos-wine-production/",
      "https://hyrad.github.io/journey-tracker/",
      "https://hyrad-lifeos-health.newpeach71.chatgpt.site",
    ];
    const launches = [];
    for (const module of modules) {
      const launch = publicLaunchURL(module);
      expect(module.placement.includes("apps")).toBe(Boolean(launch));
      expect(module.canonical.route).not.toHaveProperty("url");
      for (const route of [module.application?.route, module.canonical.route]) {
        if (route?.visibility === "public-safe" || route?.visibility === "approved-authenticated-launch") {
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
    const health = modules.find(module => module.id === "health");
    expect(health?.application).toMatchObject({
      status: "live",
      route: { visibility: "approved-authenticated-launch", url: allowed[2] },
    });
    expect(JSON.stringify(navigationManifest).replaceAll(allowed[2], "")).not.toMatch(/notion\.(?:so|com)\/p\/|chatgpt\.site|[a-f\d]{32}/i);
  });

  it("distinguishes publication review, authenticated delivery, and unknown launch routes", () => {
    const routes = Object.fromEntries(modules.map(module => [module.id, module]));
    expect(routes.music.canonical.route).toEqual({ visibility: "publication-review" });
    expect(routes.music.application).toMatchObject({ status: "live", route: { visibility: "authenticated-only" } });
    expect(routes["family-technology"].canonical.route).toEqual({ visibility: "authenticated-only" });
    expect(routes["family-technology"].application).toMatchObject({ status: "unverified", route: { visibility: "pending-review" } });
    expect(routes["game-shelf"].application).toMatchObject({ status: "blocked", route: { visibility: "pending-review" } });
    expect(routes.founder.application).toMatchObject({ status: "live", route: { visibility: "pending-review" } });
  });

  it("keeps a generic fallback for restricted and absent launch routes", () => {
    const music = modules.find(module => module.id === "music")!;
    const cooking = modules.find(module => module.id === "cooking")!;
    for (const module of [music, cooking]) {
      expect(publicLaunchURL(module)).toBeUndefined();
      expect(module.fallback).toBe("notion-launcher");
    }
  });
});
