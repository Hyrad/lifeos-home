# LifeOS Home

A responsive, dark-theme personal dashboard built with React, TypeScript, and Vite. Version 1.1.0 is a **navigation edition**: open a destination and continue in its original app.

**Live site:** https://hyrad.github.io/lifeos-home/

**Wine Production:** https://hyrad.github.io/lifeos-home/wine/

## Included

- Today: opens the existing private Notion Home without copying tasks.
- Active-project links: selected destinations with broad public labels, not live progress.
- Upcoming: opens Google Calendar without embedding private events.
- Existing Surfaces: Cookbook, Shopping Hub, Grocery Shopping.
- Searchable life domains, expandable on all devices.
- Quick actions that open the original apps. Create and save there.
- System overview with explicit disconnected/unmonitored labels.
- Wine Production workspace: one Home card and a dedicated page with six activity sections, shared navigation, and a route back to Home.

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

### Wine Production publication scope

The wine module's allowlist is `src/data/wine.ts`. On 2026-10-18 the user explicitly approved public exposure of three additional entry-point URLs: the canonical wine register, Wine Batch Management guide, and Wine Production Drive folder. The Wine Making Area and shared Tasks entry point were already part of the dashboard's navigation. Individual batch records, dated actions, inventory, original media, postmortems and exploratory-idea deep links are excluded. History opens the original register; Ideas opens the existing Wine Making Area. Neither is a fabricated filtered view.

The three Notion destinations were fetched within the Life Command Center boundary. Drive metadata confirmed the Wine Production folder is directly beneath the canonical Life OS Drive root. This verifies its identity and placement; it does not assert public accessibility or inspect/change sharing permissions. No original files were moved, no source records reconciled, and no additional Notion Surface or database created.

The site builds actual HTML entry points for `/lifeos-home/` and `/lifeos-home/wine/`, so direct visits, refresh, and `/wine/index.html` work on GitHub Pages without SPA fallback routing. Shared components and the package version keep both pages consistent. The module remains in the current repository for this first navigation release.

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
src/WinePage.tsx           Wine Production navigation page
src/components/Shared.tsx  Shared page navigation, header, footer, and UI
src/data/wine.ts           Approved wine entry points and activity sections
src/styles.css             Responsive dark theme
src/wine.css               Wine page and Home card styling
src/App.test.tsx           Behavioral and boundary tests
src/WinePage.test.tsx       Module navigation and approved-link tests
.github/workflows/pages.yml Tests, build, deployment
```

Change Tasks, Projects, Areas, Notes, Reviews, Calendar, and automations in their original systems. This page is a convenience window, not a second personal database.
