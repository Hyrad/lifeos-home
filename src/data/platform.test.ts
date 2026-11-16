import { describe, expect, it, vi } from "vitest";
import { fetchPlatformRegistry, parseRegistry, registryEndpoint } from "./platform";
import { launchURL, modules } from "./modules";

const byId = (id: string) => modules.find(m => m.id === id)!;
const registry = (apps: unknown[]) => ({ contract: "lifeos.registry/1", apps, external: [] });

describe("platform registry", () => {
  it("accepts only known apps on their fixed same-origin mounts", () => {
    const parsed = parseRegistry(registry([
      { id: "cooking", route: "/lifeos-cooking/", status: "available", version: "0.2.0" },
      { id: "wine", route: "https://evil.example/", status: "available", version: "1" },
      { id: "health", route: "/lifeos-health/", status: "available", version: "1" },
      { id: "home", route: "/lifeos-home/", status: "bogus", version: "1" },
    ]))!;
    expect([...parsed.keys()]).toEqual(["cooking"]);
    expect(parsed.get("cooking")).toMatchObject({ route: "/lifeos-cooking/", version: "0.2.0" });
  });

  it("rejects other contracts and malformed payloads", () => {
    for (const value of [null, [], "x", { contract: "other", apps: [] }, { contract: "lifeos.registry/1", apps: {} }]) {
      expect(parseRegistry(value)).toBeUndefined();
    }
  });

  it("drops unsafe version strings", () => {
    const parsed = parseRegistry(registry([{ id: "cooking", route: "/lifeos-cooking/", status: "available", version: "<script>" }]))!;
    expect(parsed.get("cooking")!.version).toBeNull();
  });

  it("requests same-origin with the Home client label and never follows redirects", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(registry([])), { headers: { "content-type": "application/json" } }));
    await fetchPlatformRegistry(fetcher);
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toBe(registryEndpoint);
    expect(init).toMatchObject({ redirect: "error", cache: "no-store", headers: { "X-LifeOS-Client": "home" } });
  });

  it("falls back silently when the platform is absent or failing", async () => {
    expect(await fetchPlatformRegistry(vi.fn().mockResolvedValue(new Response("not found", { status: 404 })))).toBeUndefined();
    expect(await fetchPlatformRegistry(vi.fn().mockResolvedValue(new Response("<html>", { headers: { "content-type": "text/html" } })))).toBeUndefined();
    expect(await fetchPlatformRegistry(vi.fn().mockRejectedValue(new TypeError("offline")))).toBeUndefined();
  });
});

describe("launch decisions with the registry", () => {
  const reg = parseRegistry(registry([
    { id: "cooking", route: "/lifeos-cooking/", status: "not-authorized-for-this-device", version: "0.2.0" },
    { id: "wine", route: "/lifeos-wine-production/", status: "available", version: "1.207" },
  ]))!;

  it("uses the private Wine route on the platform when available", () => {
    expect(launchURL(byId("wine"), "private-server", reg)).toBe("/lifeos-wine-production/");
  });

  it("does not link a private app the platform says is unavailable for this device", () => {
    expect(launchURL(byId("cooking"), "private-server", reg)).toBeUndefined();
  });

  it("public builds ignore any registry and keep public-safe navigation", () => {
    expect(launchURL(byId("wine"), "public", reg)).toBe("https://hyrad.github.io/lifeos-wine-production/");
    expect(launchURL(byId("cooking"), "public", reg)).toBeUndefined();
  });

  it("without a registry, existing private-server behavior is unchanged", () => {
    expect(launchURL(byId("cooking"), "private-server")).toBe("/lifeos-cooking/");
    expect(launchURL(byId("wine"), "private-server")).toBe("https://hyrad.github.io/lifeos-wine-production/");
  });
});
