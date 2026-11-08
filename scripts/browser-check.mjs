import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

// Run against a production preview or the deployed GitHub Pages site.
const url = process.env.CHECK_URL || "http://127.0.0.1:4173/lifeos-home/";
const { version } = JSON.parse(
  await readFile(new URL("../package.json", import.meta.url), "utf8"),
);
const journeyURL = "https://hyrad.github.io/journey-tracker/";
const healthURL = "https://hyrad-lifeos-health.newpeach71.chatgpt.site";
const calendarURL = "https://calendar.google.com/";
const notionRecords = [
  ["Workstreams", "Open Wine Making Area", "https://app.notion.com/p/472be780ce1a8247b9ed8166a00fb5ad"],
  ["Workstreams", "Open Travel Area", "https://app.notion.com/p/da5be780ce1a8235816401a81385ef36"],
  ["Find your flow", "Open Cookbook", "https://app.notion.com/p/3f1be780ce1a81f68849e982dfcc4922"],
  ["Find your flow", "Open Shopping Hub", "https://app.notion.com/p/3f7be780ce1a81a999acce540ad4d095"],
];
const notionURL = "https://app.notion.com/login";
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
    ["small-phone", 320, 720],
    ["phone", 390, 844],
    ["tablet-portrait", 768, 1024],
    ["tablet-portrait-wide", 834, 1194],
    ["tablet-landscape", 1024, 768],
    ["desktop", 1280, 900],
    ["desktop-wide", 1440, 1080],
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
    if (width <= 700) {
      const toggle = page.getByRole("button", { name: "Quick navigation" });
      await toggle.click();
      await page.keyboard.press("Escape");
      assert.equal(await toggle.getAttribute("aria-expanded"), "false");
      assert.equal(await toggle.evaluate(el => el === document.activeElement), true);
      await toggle.click();
      await page.getByRole("navigation", { name: "Page sections" }).getByRole("link", { name: "Projects" }).click();
      assert.equal(new URL(page.url()).hash, "#projects");
      await page.reload({ waitUntil: "networkidle" });
      await page.getByRole("heading", { name: "Make room for what matters." }).waitFor();
    }
    const directoryNav = width <= 700
      ? page.locator(".mobile-nav-shortcuts")
      : page.getByRole("navigation", { name: "Main navigation" });
    for (const [section, anchor] of [["Apps", "apps"], ["Workstreams", "workstreams"], ["Projects", "projects"], ["Core LifeOS", "actions"], ["Life domains", "domains"]]) {
      const link = directoryNav.getByRole("link", { name: section, exact: true });
      assert.ok((await link.boundingBox()).height >= 44, `${name}: ${section} touch target`);
      await link.click();
      assert.equal(new URL(page.url()).hash, `#${anchor}`);
      assert.equal(await link.getAttribute("aria-current"), "location");
    }
    const apps = page.getByRole("region", { name: "Apps" });
    for (const [label, href] of [["Wine Production", wineURL], ["Journey Tracker", journeyURL], ["Health", healthURL]]) {
      const launch = apps.getByRole("link", { name: new RegExp(`^Open ${label}`) });
      assert.equal(await launch.getAttribute("href"), href);
      assert.equal(await launch.getAttribute("target"), null);
      assert.ok((await launch.boundingBox()).height >= 44, `${name}: ${label} touch target`);
    }
    assert.match(await apps.getByRole("link", { name: /^Open Health/ }).innerText(), /Sign-in required/);
    if (width > 700) {
      const health = directoryNav.getByRole("link", { name: "Health", exact: true });
      assert.equal(await health.getAttribute("href"), healthURL);
      assert.equal(await health.getAttribute("target"), null);
    }
    for (const calendar of [
      page.locator("#upcoming").getByRole("link", { name: /^Open Google Calendar/ }),
      page.locator("#actions").getByRole("link", { name: /^Calendar/ }),
    ]) {
      assert.equal(await calendar.getAttribute("href"), calendarURL);
      assert.equal(await calendar.getAttribute("target"), "_blank");
      assert.equal(await calendar.getAttribute("rel"), "noopener noreferrer");
    }
    const workstreams = page.getByRole("region", { name: "Workstreams" });
    const privateFallback = workstreams.getByRole("link", { name: /^Open Notion/ });
    assert.equal(await privateFallback.getAttribute("href"), notionURL);
    assert.equal(await privateFallback.getAttribute("rel"), "noopener noreferrer");
    assert.ok((await privateFallback.boundingBox()).height >= 44, `${name}: Notion touch target`);
    assert.deepEqual(await workstreams.getByRole("link").evaluateAll(links => links.map(link => link.getAttribute("href"))),
      [notionURL, notionRecords[0][2], wineURL, notionRecords[1][2], journeyURL, healthURL]);
    const core = page.getByRole("region", { name: "Core LifeOS" });
    assert.deepEqual(await core.getByRole("link").evaluateAll(links => links.map(link => link.getAttribute("href"))),
      [calendarURL, notionURL]);
    assert.equal(await core.locator(".core-record").count(), 6);
    assert.equal(await workstreams.getByRole("listitem").count(), 13);
    for (const [section, label, href] of notionRecords) {
      const link = page.getByRole("region", { name: section }).getByRole("link", { name: new RegExp(`^${label}`) });
      assert.equal(await link.getAttribute("href"), href);
      assert.equal(await link.getAttribute("target"), "_blank");
      assert.equal(await link.getAttribute("rel"), "noopener noreferrer");
      assert.ok((await link.boundingBox()).height >= 44, `${name}: ${label} touch target`);
    }
    const manifestURL = await page.locator('link[rel="manifest"]').getAttribute("href");
    const appManifest = await page.evaluate(async href => {
      const response = await fetch(href);
      if (!response.ok) throw new Error("Manifest unavailable");
      return response.json();
    }, manifestURL);
    assert.equal(appManifest.display, "standalone");
    assert.equal(appManifest.scope, "/lifeos-home/");
    for (const icon of appManifest.icons) {
      const response = await page.request.get(new URL(icon.src, new URL(manifestURL, url)).href);
      assert.equal(response.status(), 200);
      assert.match(response.headers()["content-type"], /image\/png/);
    }
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
    const projects = page.locator("#projects");
    assert.equal(await projects.getByRole("article").count(), 4);
    assert.equal(await projects.locator("a.tool-link").count(), 2);
    const game = projects.getByRole("article", {
      name: "Game Shelf workspace",
    });
    assert.equal(await game.locator(".project-kind").textContent(), "Project");
    assert.equal(
      await game.locator(".tool-kind").textContent(),
      "Software product",
    );
    assert.equal(await game.locator("a.tool-link").count(), 0);
    assert.match(await game.locator(".tool-action").innerText(), /Private hosting pending/);
    assert.equal(
      await projects.getByRole("article", { name: "Travel planning workspace" })
        .locator("a.tool-link").getAttribute("href"),
      journeyURL,
    );
    assert.equal(await projects.locator("a a").count(), 0);
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
    // Follow the Apps card, then verify the independent Wine page and reload.
    await apps.getByRole("link", { name: /^Open Wine Production/ }).click();
    await page
      .getByRole("heading", { level: 1, name: "Wine Production." })
      .waitFor();
    assert.equal(new URL(page.url()).pathname, new URL(wineURL).pathname);
    assert.equal(await page.locator(".wine-card").count(), 8);
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
  await page
    .getByRole("heading", { name: "Make room for what matters." })
    .waitFor();
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
  const appsShortcut = page.getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "Apps", exact: true });
  await page.keyboard.press("Tab");
  await appsShortcut.focus();
  assert.equal(await appsShortcut.evaluate(el => el.matches(":focus-visible") &&
    getComputedStyle(el).outlineStyle !== "none"), true);
  await page.keyboard.press("Enter");
  assert.equal(new URL(page.url()).hash, "#apps");
  assert.deepEqual(errors, [], "Browser errors or bad responses");
  assert.deepEqual(failedRequests, [], "Failed requests");
  assert.deepEqual(
    externalRequests,
    [],
    "Unexpected third-party or private API requests",
  );
  const launchPage = await context.newPage();
  await launchPage.setViewportSize({ width: 390, height: 844 });
  for (const [label, href] of [["Journey Tracker", journeyURL], ["Health", healthURL]]) {
    const expected = new URL(href).href;
    await launchPage.route(expected, route => route.fulfill({ status: 200, body: "Launch probe" }), { times: 1 });
    await launchPage.goto(url);
    await launchPage.getByRole("navigation", { name: "Primary sections" }).getByRole("link", { name: "Apps" }).click();
    await launchPage.getByRole("region", { name: "Apps" }).getByRole("link", { name: new RegExp(`^Open ${label}`) }).click();
    await launchPage.waitForURL(expected);
    assert.equal(await launchPage.locator("body").innerText(), "Launch probe");
  }
  await launchPage.goto(url);
  for (const [section, label, href] of notionRecords) {
    await context.route(href, route => route.fulfill({ status: 200, body: "Notion navigation probe" }), { times: 1 });
    const link = launchPage.getByRole("region", { name: section }).getByRole("link", { name: new RegExp(`^${label}`) });
    const [popup] = await Promise.all([launchPage.waitForEvent("popup"), link.click()]);
    await popup.waitForURL(href);
    assert.equal(await popup.locator("body").innerText(), "Notion navigation probe");
    await popup.close();
  }
  console.log("Four exact Notion outbound navigations passed with intercepted destination responses.");
  await launchPage.close();
  console.log("Journey Tracker and Health launch URLs passed with intercepted destination responses.");
  console.log(
    "Keyboard checks passed. No browser errors, failed requests, or external requests.",
  );
} finally {
  await browser.close();
}
