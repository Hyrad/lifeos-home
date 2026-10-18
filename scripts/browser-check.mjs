import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

// Run against a production preview or the deployed GitHub Pages site.
const url = process.env.CHECK_URL || "http://127.0.0.1:4173/lifeos-home/";
const { version } = JSON.parse(
  await readFile(new URL("../package.json", import.meta.url), "utf8"),
);
const wineURL = "https://hyrad.github.io/lifeos-wine-production/";
const allowedOrigins = new Set([new URL(url).origin, new URL(wineURL).origin]);
const browser = await chromium.launch({
  headless: true,
  ...(process.env.BROWSER_CHANNEL
    ? { channel: process.env.BROWSER_CHANNEL }
    : {}),
});
await mkdir("test-results", { recursive: true });
try {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  const errors = [];
  const failedRequests = [];
  const externalRequests = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("requestfailed", (request) => failedRequests.push(request.url()));
  page.on("response", (response) => {
    if (response.status() >= 400)
      errors.push(`${response.status()}: ${response.url()}`);
  });
  page.on("request", (request) => {
    if (!allowedOrigins.has(new URL(request.url()).origin))
      externalRequests.push(request.url());
  });
  for (const [name, width, height] of [
    ["desktop", 1440, 1080],
    ["tablet", 820, 1180],
    ["phone", 390, 844],
    ["small-phone", 320, 720],
  ]) {
    await page.setViewportSize({ width, height });
    const response = await page.goto(url, { waitUntil: "networkidle" });
    assert.equal(response.status(), 200, `${name}: page response`);
    await page
      .getByRole("heading", { name: "Make room for what matters." })
      .waitFor();
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      true,
      `${name}: horizontal overflow`,
    );
    const accessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    assert.deepEqual(
      accessibility.violations.map((item) => ({
        id: item.id,
        impact: item.impact,
        nodes: item.nodes.map((node) => node.target),
      })),
      [],
      `${name}: accessibility violations`,
    );
    await page.screenshot({ path: `test-results/${name}.png`, fullPage: true });
    assert.equal(
      await page.locator(".release-version").textContent(),
      `v${version}`,
    );
    const input = page.getByRole("searchbox", { name: "Find a life domain" });
    await input.fill(" MUSIC ");
    assert.equal(await page.locator("#domains .domain-card").count(), 1);
    assert.match(
      await page.locator("#domains .domain-card").innerText(),
      /Music/,
    );
    await page.getByRole("button", { name: "Clear domain search" }).click();
    await page.getByRole("button", { name: "Explore all domains" }).click();
    assert.equal(await page.locator("#domains .domain-card").count(), 16);
    await page.getByRole("button", { name: "Show fewer domains" }).click();
    assert.equal(await page.locator("#domains .domain-card").count(), 8);
    await input.fill("no result");
    await page.getByRole("button", { name: "Show all domains" }).click();
    assert.equal(await input.inputValue(), "");
    // Follow the actual Home card, then verify the standalone page and reload.
    await page.locator(`#projects a[href="${wineURL}"]`).click();
    await page
      .getByRole("heading", { level: 1, name: "Wine Production." })
      .waitFor();
    assert.equal(new URL(page.url()).pathname, new URL(wineURL).pathname);
    assert.equal(await page.locator(".wine-card").count(), 6);
    assert.match(
      await page.locator(".release-version").textContent(),
      /^v\d+\.\d+\.\d+$/,
    );
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
      `${name}: wine page overflow`,
    );
    const wineAccessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    assert.deepEqual(
      wineAccessibility.violations.map((item) => ({
        id: item.id,
        nodes: item.nodes.map((node) => node.target),
      })),
      [],
      `${name}: wine accessibility`,
    );
    await page.screenshot({
      path: `test-results/wine-${name}.png`,
      fullPage: true,
    });
    await page.reload({ waitUntil: "networkidle" });
    await page
      .getByRole("heading", { level: 1, name: "Wine Production." })
      .waitFor();
    await page.getByRole("link", { name: "Back to LifeOS Home" }).click();
    await page
      .getByRole("heading", { name: "Make room for what matters." })
      .waitFor();
    console.log(
      `${name}: Home and Wine layout, navigation/reload, interactions, WCAG A/AA checks passed`,
    );
  }
  // Check actual keyboard focus from a fresh page, including skip-link behavior.
  for (const oldPath of ["wine/", "wine/index.html"]) {
    const legacy = new URL(oldPath, url);
    legacy.search = "?from=legacy";
    legacy.hash = "methods";
    await page.goto(legacy.href, { waitUntil: "networkidle" });
    await page.waitForURL(wineURL + "?from=legacy#methods");
    await page
      .getByRole("heading", { level: 1, name: "Wine Production." })
      .waitFor();
    assert.equal(new URL(page.url()).hash, "#methods");
  }
  await page.goto(url, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "Make room for what matters." }).waitFor();
  await page.keyboard.press("Tab");
  assert.equal(
    await page
      .getByRole("link", { name: "Skip to content" })
      .evaluate((element) => element === document.activeElement),
    true,
  );
  await page.keyboard.press("Enter");
  assert.equal(
    await page
      .locator("main")
      .evaluate((element) => element === document.activeElement),
    true,
  );
  assert.deepEqual(errors, [], "Browser errors or bad responses");
  assert.deepEqual(failedRequests, [], "Failed requests");
  assert.deepEqual(
    externalRequests,
    [],
    "Unexpected third-party or private API requests",
  );
  console.log(
    "Keyboard checks passed. No browser errors, failed requests, or external requests.",
  );
} finally {
  await browser.close();
}
