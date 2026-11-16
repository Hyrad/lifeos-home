import { useEffect, useState } from "react";
import type { Deployment } from "../types/module";

// LIFEOS-PLATFORM-02: runtime registry from the shared private platform (same origin only).
// Public builds never call it. On the legacy static private server the endpoint is absent and
// Home silently keeps its static manifest, so behavior there is unchanged.
export const registryEndpoint = "/api/v1/platform/registry";

export type PlatformStatus = "available" | "unavailable" | "not-authorized-for-this-device" | "blocked-device-evidence";

export interface PlatformApp {
  id: string;
  route: string;
  status: PlatformStatus;
  version: string | null;
}

// Registry ids -> Home module ids, and the only same-origin mounts the platform may announce.
const knownApps: Record<string, { module: string; route: string }> = {
  home: { module: "lifeos", route: "/lifeos-home/" },
  cooking: { module: "cooking", route: "/lifeos-cooking/" },
  wine: { module: "wine", route: "/lifeos-wine-production/" },
};
const statuses: readonly PlatformStatus[] = ["available", "unavailable", "not-authorized-for-this-device", "blocked-device-evidence"];

export type PlatformRegistry = ReadonlyMap<string, PlatformApp>;

/** Strict parser: unknown apps, foreign routes or malformed fields are ignored, never trusted. */
export function parseRegistry(value: unknown): PlatformRegistry | undefined {
  if (!value || typeof value !== "object") return undefined;
  const { contract, apps } = value as { contract?: unknown; apps?: unknown };
  if (contract !== "lifeos.registry/1" || !Array.isArray(apps)) return undefined;
  const result = new Map<string, PlatformApp>();
  for (const app of apps) {
    if (!app || typeof app !== "object") continue;
    const { id, route, status, version } = app as Record<string, unknown>;
    const known = typeof id === "string" ? knownApps[id] : undefined;
    if (!known || route !== known.route || !statuses.includes(status as PlatformStatus)) continue;
    const safeVersion = typeof version === "string" && /^[0-9A-Za-z.+-]{1,40}$/.test(version) ? version : null;
    result.set(known.module, { id: id as string, route: known.route, status: status as PlatformStatus, version: safeVersion });
  }
  return result;
}

export async function fetchPlatformRegistry(fetcher: typeof fetch = fetch, signal?: AbortSignal) {
  try {
    const response = await fetcher(registryEndpoint, {
      method: "GET", headers: { "X-LifeOS-Client": "home", Accept: "application/json" },
      cache: "no-store", credentials: "same-origin", redirect: "error", signal,
    });
    if (!response.ok || !(response.headers.get("content-type") ?? "").startsWith("application/json")) return undefined;
    return parseRegistry(await response.json());
  } catch {
    return undefined;
  }
}

export function usePlatformRegistry(deployment: Deployment): PlatformRegistry | undefined {
  const [registry, setRegistry] = useState<PlatformRegistry>();
  useEffect(() => {
    if (deployment !== "private-server") return;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);
    fetchPlatformRegistry(fetch, controller.signal).then(value => { if (value) setRegistry(value); });
    return () => { clearTimeout(timer); controller.abort(); };
  }, [deployment]);
  return registry;
}

export function platformStatusLabel(status: PlatformStatus) {
  return {
    available: "Available on this device",
    unavailable: "Not enabled on the private server",
    "not-authorized-for-this-device": "Not authorized for this device",
    "blocked-device-evidence": "Waiting for device authorization",
  }[status];
}
