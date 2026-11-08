import { readdir, readFile } from "node:fs/promises";
import assert from "node:assert/strict";

// Home v0.2.1 approved this exact address. The app still enforces owner access.
const approvedHealthLaunch = "https://hyrad-lifeos-health.newpeach71.chatgpt.site";
// NAV-05 approves these exact URLs, without query strings or fragments.
const approvedNotion = new Set([
  "https://app.notion.com/p/472be780ce1a8247b9ed8166a00fb5ad",
  "https://app.notion.com/p/da5be780ce1a8235816401a81385ef36",
  "https://app.notion.com/p/3f1be780ce1a81f68849e982dfcc4922",
  "https://app.notion.com/p/3f7be780ce1a81a999acce540ad4d095",
]);
const foundNotion = new Set();
const approved = new Set([
  ...approvedNotion,
  "https://app.notion.com/login",
  "https://calendar.google.com/",
  "https://hyrad.github.io/lifeos-wine-production/",
  "https://hyrad.github.io/journey-tracker/",
  approvedHealthLaunch,
]);
const standardURLs = new Set([
  "http://www.w3.org/1998/Math/MathML",
  "http://www.w3.org/1999/xlink",
  "http://www.w3.org/2000/svg",
  "http://www.w3.org/XML/1998/namespace",
  "https://react.dev/errors/",
]);
const secrets = /(?:sb_secret_|sb_service_role_|ghp_|github_pat_|sk_live_)[A-Za-z0-9_]+|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----/;
const privateReferences = /notion\.(?:com|so)\/p\/|\b[a-f0-9]{32}\b|\b[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\b|\.chatgpt\.site\b|\.ts\.net\b|\/(?:home|Users|workspace)\/[^\s"'<>]+|[A-Z]:\\Users\\|(?:https?:\/\/)(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)/i;

async function scan(path) {
  const text = await readFile(path, "utf8");
  assert.ok(!secrets.test(text), `Credential pattern in ${path}`);
  const remaining = text.replace(/https?:\/\/[^\s"'<>\x60\\)]+/g, (url) => {
    // Bundled framework code includes React errors and standard XML/SVG namespaces.
    assert.ok(approved.has(url) || standardURLs.has(url), `Unexpected URL in ${path}`);
    if (approvedNotion.has(url)) {
      foundNotion.add(url);
      return "";
    }
    return url === approvedHealthLaunch ? "" : url;
  });
  assert.ok(!privateReferences.test(remaining), `Private reference pattern in ${path}`);
  if (path.endsWith(".html")) {
    assert.match(text, /Content-Security-Policy/);
    assert.doesNotMatch(text, /<script(?![^>]*\bsrc=)[^>]*>|<style\b|\sstyle=/i);
  }
}

assert.deepEqual((await readdir("dist")).sort(), ["assets", "favicon.svg", "icons", "index.html", "manifest.webmanifest", "wine"]);
assert.deepEqual(await readdir("dist/wine"), ["index.html"]);
for (const file of await readdir("dist/assets")) {
  assert.match(file, /^[\w.-]+\.(js|css)$/, `Unexpected artifact: ${file}`);
  await scan(`dist/assets/${file}`);
}
for (const file of ["index.html", "wine/index.html", "manifest.webmanifest", "favicon.svg"]) {
  await scan(`dist/${file}`);
}

const manifest = JSON.parse(await readFile("dist/manifest.webmanifest", "utf8"));
assert.equal(manifest.display, "standalone");
assert.equal(manifest.start_url, "/lifeos-home/");
assert.equal(manifest.scope, "/lifeos-home/");
assert.deepEqual((await readdir("dist/icons")).sort(), ["apple-touch-icon.png", "icon-192.png", "icon-512.png"]);
for (const icon of manifest.icons) {
  assert.match(icon.src, /^icons\/icon-(192|512)\.png$/);
  const bytes = await readFile(`dist/${icon.src}`);
  assert.equal(bytes.subarray(1, 4).toString(), "PNG");
}
assert.deepEqual(foundNotion, approvedNotion, "Expected all four approved Notion routes in the build");
console.log("Public artifact checks passed; manual content review remains required.");
