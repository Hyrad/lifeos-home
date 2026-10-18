import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

// Run against a production preview or the deployed GitHub Pages site.
const url = process.env.CHECK_URL || "http://127.0.0.1:4173/lifeos-home/";
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
  page.on("requestfailed", (request) => failedRequests.push(request.url()));
  page.on("response", (response) => {
    if (response.status() >= 400)
      errors.push(`${response.status()}: ${response.url()}`);
  });
  page.on("request", (request) => {
    if (new URL(request.url()).origin !== new URL(url).origin)
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
    console.log(
      `${name}: layout, domain interactions, WCAG A/AA checks passed`,
    );
  }
  // Check actual keyboard focus from a fresh page, including skip-link behavior.
  await page.goto(url);
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
