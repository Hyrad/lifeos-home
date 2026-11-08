# LifeOS Home

A responsive, dark-theme personal dashboard built with React, TypeScript, and Vite. The navigation edition opens approved applications and points users toward their existing private workspace.

**Live site:** https://hyrad.github.io/lifeos-home/

**Independent Wine Production site:** https://hyrad.github.io/lifeos-wine-production/

**Wine repository:** https://github.com/Hyrad/lifeos-wine-production

## Included

- **Apps** launches Wine Production, Journey Tracker and Health from Home in two interactions or fewer. Health requires its own owner sign-in.
- **Workstreams** lists modules and canonical record roles. The generic Notion entry opens Notion sign-in or the existing session so the owner can open their private LifeOS Home.
- Today, Projects, Upcoming, Surfaces, searchable Life domains, Quick actions and System overview retain their existing Home sections. Private links use the generic Notion entry point. Calendar and public app links still launch directly.
- Keyboard navigation, focus indicators, a skip link, reduced-motion support, responsive layouts and a device-local date.

See [navigation contract and rollout](docs/navigation-v1.md) for the public/private boundary, device acceptance, and specialist-app handoffs.

## Local development

Requires Node.js 24 LTS (minimum 22.13) and pnpm 11.25.0.

```sh
npm install --global pnpm@11.25.0
pnpm install --frozen-lockfile
pnpm dev
```

Open the printed local URL at `/lifeos-home/`.

```sh
pnpm test       # behavior and data-boundary checks
pnpm build      # strict TypeScript check and production build
pnpm preview   # preview dist at /lifeos-home/
```

For browser and accessibility checks, keep `pnpm preview` running in another terminal:

```sh
pnpm exec playwright install chromium
pnpm test:browser
```

Alternatively set `BROWSER_CHANNEL=chrome` to use an installed Chrome. `CHECK_URL` can point to the published Home URL. The check covers 320, 390, 768, 834, 1024, 1280, and 1440px. It tests the Apps and Workstreams entry points, domain interactions, Home → Wine → Home, Wine reloads and legacy routes, keyboard focus, overflow, automated WCAG A/AA rules, and network behavior. Screenshots are saved to ignored `test-results/`. Automated rules complement visual review; they are not a full accessibility audit.

## Privacy and separation

### Independent module boundary

Wine Production is independently maintained and deployed from [Hyrad/lifeos-wine-production](https://github.com/Hyrad/lifeos-wine-production). Home contains only its published URL and navigation card. No wine page components, guide/register/Drive allowlist, wine records, or wine application styles are built here. The visual card follows Home styles. Wine releases do not require a Home release.

The old `/lifeos-home/wine/` and `/lifeos-home/wine/index.html` addresses are compatibility redirects. They preserve query strings and section anchors through an external script compatible with the production content-security policy. A visible fallback link and JavaScript-disabled meta redirect are included. Old source remains in Git history as provenance; it is removed from the current application.

Treat source, build, and GitHub Pages as public, even with a private repository.

- No private tasks, appointments, personal financial/health records, family records, receipts, or source documents.
- No secrets, `.env` files, Notion API client, live integration, analytics, third-party fonts, or browser storage.
- Public source and build contain approved launch URLs and generic module labels. The exact Health app launch URL is approved for this use. Keep private Notion destinations and unapproved app URLs in the owner records.
- Personal-only: no business or employment records, links, or copied implementation systems.
- Restrictive HTML content security and no-referrer policies. External links use `noopener noreferrer`.

Frontend configuration is public. A later live-data edition needs a separately approved authentication and server design; GitHub Pages cannot protect embedded data.

## GitHub Pages

Vite's `base` is `/lifeos-home/`. GitHub Actions tests and builds pushes and pull requests. Only `main` pushes and manual runs deploy `dist/` through the `github-pages` environment. Pull requests never deploy.

Enable **Settings → Pages → Build and deployment → Source: GitHub Actions** once, or use the Pages API with `build_type: workflow`. Pages from a private repository requires account/plan support. Do not change repository visibility as a workaround without explicit approval.

The workflow uses the generated `GITHUB_TOKEN`: read-only contents in the build job; Pages and OIDC write permission only in deployment. No repository secret is needed. A successful Actions deployment and HTTP check verify publication; this README and dashboard labels do not.

## Files

```text
src/data/navigation.ts      Existing Home section labels and safe fallbacks
src/App.tsx                Dashboard and interactions
src/components/Shared.tsx  Shared page navigation, header, footer, and UI
src/data/modules.ts        Versioned public navigation projection
src/styles.css             Responsive dark theme
src/App.test.tsx           Behavioral and boundary tests
src/ModuleNavigation.test.tsx Independent module navigation checks
wine/index.html             Compatibility redirect for old bookmarks
wine/redirect.ts            Redirect preserves query and section anchor
.github/workflows/pages.yml Tests, build, deployment
```

Change Tasks, Projects, Areas, Notes, Reviews, Calendar, and automations in their original systems. This page is a convenience window, not a second personal database.

## Foundation v0.1

Home 0.2.0 introduced a typed public module registry, reusable shell, semantic tokens and accessible mobile section navigation. See [foundation conventions](docs/foundation-v0.1.md). Run `pnpm test:boundary` after building. CI now runs production browser checks before artifact upload. Independent modules retain their own releases.

## iPhone Home Screen app

After this release is deployed, open https://hyrad.github.io/lifeos-home/ in Safari. Choose Share → Add to Home Screen, enable Open as Web App, name it LifeOS, and tap Add. You can move its icon into a LifeOS folder alongside future independent modules. This is an installed web app, not an App Store package. iPhone installation and safe-area rendering still require device verification.

The manifest has a stable ID and scope restricted to /lifeos-home/. Icons derive from the existing LifeOS compass mark. Home opens in a standalone window; external Notion and module destinations retain their own access and browser behavior. This release has no service worker, offline guarantee, push notifications or private-data cache. Changes become available from the deployed site without an App Store update.
