# LifeOS Home

A responsive, dark-theme personal dashboard built with React, TypeScript, and Vite. Version 1.1.1 is a **navigation edition**: open a destination and continue in its original app.

**Live site:** https://hyrad.github.io/lifeos-home/

**Independent Wine Production site:** https://hyrad.github.io/lifeos-wine-production/

**Wine repository:** https://github.com/Hyrad/lifeos-wine-production

## Included

- Today: opens the existing private Notion Home without copying tasks.
- Active-project links: selected destinations with broad public labels, not live progress.
- Upcoming: opens Google Calendar without embedding private events.
- Existing Surfaces: Cookbook, Shopping Hub, Grocery Shopping.
- Searchable life domains, expandable on all devices.
- Quick actions that open the original apps. Create and save there.
- System overview with explicit disconnected/unmonitored labels.
- Wine Production entry: one Home card and sidebar link to the independent Wine Production site.

Includes keyboard navigation, focus indicators, a skip link, reduced-motion support, and responsive layouts. The device date refreshes while open. It is not a data freshness indicator.

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

Alternatively set `BROWSER_CHANNEL=chrome` to use an installed Chrome. `CHECK_URL` can point to the published Home URL. The check covers desktop (1440px), tablet (820px), phone (390px), and small phone (320px), domain interactions, Home → Wine → Home navigation, direct Wine page reloads, keyboard entry, overflow, automated WCAG A/AA rules, browser errors, and unexpected network requests. Screenshots are saved to ignored `test-results/`. Automated rules complement visual review; they are not a full accessibility audit.

## Canonical sources

- [Life Command Center](https://app.notion.com/p/3afbe780ce1a83b883d18111ca195c69): governance and bootstrap anchor.
- [Notion LifeOS Home](https://app.notion.com/p/3f1be780ce1a81ccbd9ce0331175706f): original navigation and destination links.
- [Surface governance](https://app.notion.com/p/3f1be780ce1a81c09529c394f5a44585): Home → Surface → canonical record. Existing ownership remains authoritative.

The public allowlist is `src/data/navigation.ts`, reviewed on 2026-10-18. Every Notion destination was found beneath the Life Command Center or on its existing Home. Domain labels can use familiar short names for existing Areas. Private project labels are deliberately generalized. No travel dates, health context, family names, record summaries, or private implementation details are copied.

Update links only after verifying them within the Life Command Center boundary. Change `navigationReviewed` only after an actual review. This site does not verify destination freshness, authentication, project activity, connection health, deployment health, or automation execution. Private destinations may require Notion access; this page grants none. Do not publish those pages to make links work.

## Privacy and separation

### Independent module boundary

Wine Production is independently maintained and deployed from [Hyrad/lifeos-wine-production](https://github.com/Hyrad/lifeos-wine-production). Home contains only its published URL and navigation card. No wine page components, guide/register/Drive allowlist, wine records, or wine application styles are built here. The visual card follows Home styles. Wine releases do not require a Home release.

The old `/lifeos-home/wine/` and `/lifeos-home/wine/index.html` addresses are compatibility redirects. They preserve query strings and section anchors through an external script compatible with the production content-security policy. A visible fallback link and JavaScript-disabled meta redirect are included. Old source remains in Git history as provenance; it is removed from the current application.

Treat source, build, and GitHub Pages as public, even with a private repository.

- No private tasks, appointments, personal financial/health records, family records, receipts, or source documents.
- No secrets, `.env` files, Notion API client, live integration, analytics, third-party fonts, or browser storage.
- Links expose destination IDs and generic categories, not their contents. Remove a link before publication if even that category or identifier is sensitive.
- Personal-only: no business or employment records, links, or copied implementation systems.
- Restrictive HTML content security and no-referrer policies. External links use `noopener noreferrer`.

Frontend configuration is public. A later live-data edition needs a separately approved authentication and server design; GitHub Pages cannot protect embedded data.

## GitHub Pages

Vite's `base` is `/lifeos-home/`. GitHub Actions tests and builds pushes and pull requests. Only `main` pushes and manual runs deploy `dist/` through the `github-pages` environment. Pull requests never deploy.

Enable **Settings → Pages → Build and deployment → Source: GitHub Actions** once, or use the Pages API with `build_type: workflow`. Pages from a private repository requires account/plan support. Do not change repository visibility as a workaround without explicit approval.

The workflow uses the generated `GITHUB_TOKEN`: read-only contents in the build job; Pages and OIDC write permission only in deployment. No repository secret is needed. A successful Actions deployment and HTTP check verify publication; this README and dashboard labels do not.

## Files

```text
src/data/navigation.ts      Public labels and destination allowlist
src/App.tsx                Dashboard and interactions
src/components/Shared.tsx  Shared page navigation, header, footer, and UI
src/data/modules.ts        Independent module URLs
src/styles.css             Responsive dark theme
src/App.test.tsx           Behavioral and boundary tests
src/ModuleNavigation.test.tsx Independent module navigation checks
wine/index.html             Compatibility redirect for old bookmarks
wine/redirect.ts            Redirect preserves query and section anchor
.github/workflows/pages.yml Tests, build, deployment
```

Change Tasks, Projects, Areas, Notes, Reviews, Calendar, and automations in their original systems. This page is a convenience window, not a second personal database.
