import { readdir, readFile } from "node:fs/promises";
import assert from "node:assert/strict";
const approved = new Set(["https://hyrad-lifeos-health.newpeach71.chatgpt.site","https://app.notion.com/p/010be780ce1a8245a0100137b44348c6", "https://app.notion.com/p/117be780ce1a835a806d811596443e06", "https://app.notion.com/p/2febe780ce1a827b8b8c01b176fe452b", "https://app.notion.com/p/3a2be780ce1a8135a18dfdaa04d3dd87", "https://app.notion.com/p/3afbe780ce1a81d6ab4fd3fe8b39936f", "https://app.notion.com/p/3afbe780ce1a83b883d18111ca195c69", "https://app.notion.com/p/3c3be780ce1a81038748f89a6bac3dd4", "https://app.notion.com/p/3cbbe780ce1a8113bfd6f89a48a2e9ec", "https://app.notion.com/p/3eabe780ce1a81a8b710d9cb3fbf53f0", "https://app.notion.com/p/3f1be780ce1a81c09529c394f5a44585", "https://app.notion.com/p/3f1be780ce1a81ccbd9ce0331175706f", "https://app.notion.com/p/3f1be780ce1a81f68849e982dfcc4922", "https://app.notion.com/p/3f4be780ce1a8159bc09ebca662327dc", "https://app.notion.com/p/3f7be780ce1a81a19cfae9bca16f0087", "https://app.notion.com/p/3f7be780ce1a81a999acce540ad4d095", "https://app.notion.com/p/45cbe780ce1a82f8a7fa0179e24fb240", "https://app.notion.com/p/472be780ce1a8247b9ed8166a00fb5ad", "https://app.notion.com/p/4cfbe780ce1a8219a6f3817ca535427f", "https://app.notion.com/p/567be780ce1a83aea7c281e54cd259e9", "https://app.notion.com/p/5a5be780ce1a83409023815e44656150", "https://app.notion.com/p/5e8be780ce1a820595e581ceaaaac644", "https://app.notion.com/p/67ebe780ce1a8295af7b01c412e18246", "https://app.notion.com/p/701be780ce1a83dc9ae981f19d5e3258", "https://app.notion.com/p/8afbe780ce1a824a8977012cbb213020", "https://app.notion.com/p/957be780ce1a825cb7e50128aad57075", "https://app.notion.com/p/cf8be780ce1a83a2800381b9afe723ef", "https://app.notion.com/p/da5be780ce1a8235816401a81385ef36", "https://app.notion.com/p/ed2be780ce1a82b1b9be8189523d730e", "https://app.notion.com/p/f10be780ce1a82a383fb810782020446", "https://calendar.google.com/", "https://hyrad.github.io/lifeos-wine-production/"]);
async function scan(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = `${dir}/${entry.name}`;
    if (entry.isDirectory()) { assert.equal(entry.name, "assets", `Unexpected directory ${path}`); await scan(path); continue; }
    assert.match(path, /^(dist\/(index\.html|wine\/index\.html|favicon\.svg)|dist\/assets\/[\w.-]+\.(js|css))$/, `Unexpected artifact ${path}`);
    const text = await readFile(path, "utf8");
    assert.doesNotMatch(text, /(?:sb_secret_|sb_service_role_|ghp_|github_pat_|sk_live_)[A-Za-z0-9_]+|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----/);
    // React includes standards/documentation URLs; these are not navigation destinations.
    for (const url of text.match(/https:\/\/[^\s"'<>`\\)]+/g) || []) {
      if (/^https:\/\/(?:react\.dev\/errors\/|app\.notion\.com\/p\/|hyrad\.github\.io\/|calendar\.google\.com\/)/.test(url)) {
        if (!url.startsWith("https://react.dev/errors/") && !/^https:\/\/app\.notion\.com\/p\/\$\{[a-zA-Z]+\}$/.test(url)) assert.ok(approved.has(url), `Unapproved destination ${url}`);
      } else assert.ok(url.startsWith("https://" ) && /^(https:\/\/(?:www\.w3\.org|developer\.mozilla\.org|react\.dev)\/)/.test(url), `Unexpected URL ${url}`);
    }
    if (path.endsWith(".html")) {
      assert.match(text, /Content-Security-Policy/);
      assert.doesNotMatch(text, /<script(?![^>]*\bsrc=)[^>]*>|<style\b|\sstyle=/i);
    }
  }
}
const navigation = await readFile("src/data/navigation.ts", "utf8");
for (const [, id] of navigation.matchAll(/notion\("([a-f0-9]+)"\)/g)) {
  assert.ok(approved.has(`https://app.notion.com/p/${id}`), `Unapproved context ID ${id}`);
}
// wine is an intentional compatibility entry.
await scan("dist/assets");
for (const path of ["dist/index.html", "dist/wine/index.html"]) {
 const t = await readFile(path, "utf8");
 assert.match(t, /Content-Security-Policy/);
 assert.doesNotMatch(t, /<script(?![^>]*\bsrc=)[^>]*>|<style\b|\sstyle=/i);
}
const root = await readdir("dist");
assert.deepEqual(root.sort(), ["assets", "favicon.svg", "icons", "index.html", "manifest.webmanifest", "wine"]);
assert.deepEqual(await readdir("dist/wine"), ["index.html"]);
console.log("Public artifact checks passed; manual content review remains required.");

const manifest = JSON.parse(await readFile("dist/manifest.webmanifest", "utf8"));
assert.equal(manifest.display, "standalone");
assert.equal(manifest.start_url, "/lifeos-home/");
assert.equal(manifest.scope, "/lifeos-home/");
assert.deepEqual((await readdir("dist/icons")).sort(), ["apple-touch-icon.png", "icon-192.png", "icon-512.png"]);
for (const icon of manifest.icons) {
 assert.match(icon.src, /^icons\/icon-(192|512)\.png$/);
 const bytes = await readFile(`dist/${icon.src}`);
 assert.equal(bytes.subarray(1,4).toString(), "PNG");
}
