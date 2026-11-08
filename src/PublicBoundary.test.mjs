import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { expect, it } from "vitest";

const scanner = resolve("scripts/check-public-boundary.mjs");

it.each([
  ["Notion record", "https://app.notion.com/p/0123456789abcdef0123456789abcdef", /Unexpected URL/],
  ["bare private ID", "0123456789abcdef0123456789abcdef", /Private reference pattern/],
  ["unapproved Sites host", "https://synthetic-private.chatgpt.site", /Unexpected URL/],
  ["Health deep link", "https://hyrad-lifeos-health.newpeach71.chatgpt.site/private", /Unexpected URL/],
])("rejects a %s in a production asset", (_label, value, message) => {
  const root = mkdtempSync(join(tmpdir(), "lifeos-boundary-"));
  try {
    const dist = join(root, "dist");
    for (const folder of ["assets", "icons", "wine"]) {
      mkdirSync(join(dist, folder), { recursive: true });
    }
    for (const file of ["favicon.svg", "index.html", "manifest.webmanifest", "wine/index.html"]) {
      writeFileSync(join(dist, file), "");
    }
    writeFileSync(join(dist, "assets", "test.js"), JSON.stringify(value));
    const result = spawnSync(process.execPath, [scanner], { cwd: root, encoding: "utf8" });
    expect(result.status).toBe(1);
    expect(result.stderr).toMatch(message);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
