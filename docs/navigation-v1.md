# LifeOS navigation v1

Home v0.3.0 keeps the public dashboard on GitHub Pages. Notion owns canonical personal records. Each application owns its source and runtime. The internal routing inventory belongs in the existing private LifeOS Home implementation checkpoint. Keep it out of this public repository, PR text, screenshots and builds.

## Public routing

| Module | Application on public Home | Canonical access |
| --- | --- | --- |
| Wine Production | Direct public app, standalone manifest | Private Notion workspace |
| Journey Tracker | Direct public app, standalone manifest | Private Notion workspace |
| Health, Music, CasinoAcademy | Private app links held in owner records | Private Notion workspace |
| Game Shelf | Private hosting gate | Private development Surface |
| Family technology, founder workspace | Launch routes withheld pending verification | Private access |
| Fitness, Cooking, Shopping, Game development, LifeOS Home records | Directory entries | Private Notion workspace |

Home itself retains its standalone manifest. Manifest metadata verifies declared intent. Device installation and external-link handling require Safari testing. Public Home offers two interactions from its entry screen to either public app, or to the generic Notion launcher. The launcher opens Notion and cannot target a private workspace or page. No individually linkable public canonical Workstream is approved in this release. The full two-interaction goal for private Workstreams requires a separate access-controlled entry point.

## Change a route

1. Verify the existing canonical owner and distinguish a typed Workstream from a documented role. Check actual app availability and its intended audience separately from Project status.
2. Obtain explicit publication approval for any new destination whose address or association is private. Keep its URL, IDs, evidence and installation state in the owner checkpoint until approved.
3. Update the public manifest in `src/data/modules.ts` and the applicable type in `src/types/module.ts`. Keep stable IDs. Use the route visibility discriminator, a truthful app status and installation classification, and a generic fallback for restricted routes. Keep the source evidence label and verification date public-safe.
4. For an approved URL, update the independent artifact allowlist in `scripts/check-public-boundary.mjs` and exercise the route in tests. Run `pnpm test`, `pnpm build`, `pnpm test:boundary` and `pnpm test:browser` against a preview. Review the exact artifact and Git diff, including files excluded from the build.

A future private directory needs authenticated, authorized delivery for every restricted route. The public projection never loads or contains the private inventory.

## Independent follow-ups

Each mission adds a visible **LifeOS Home** return link, a consistent top-level navigation entry, its own canonical route only in an audience that permits it, and only relevant related modules. Verify keyboard/touch behavior and installed Home Screen link handling on iPhone and iPad. Preserve existing authentication, ownership, data and offline or device-local behavior. Review source and release separately for each app.

| Priority | Application | Mission-specific acceptance |
| --- | --- | --- |
| 1 | Wine Production | Verify the existing Home backlink and independent manifest. Preserve guides, register, routes and old bookmarks. Keep private Notion destinations out of public assets. |
| 2 | Journey Tracker | Add or verify Home return in public and standalone shells. Keep the private trip owner link out of public assets. Preserve trip state, bilingual navigation, journal review and cache/version behavior. |
| 3 | Health | Verify existing Home backlink and owner-only canonical Health and Atlas entry points. Preserve health privacy, existing integrations and capture behavior. |
| 4 | Music | Add or verify Home return and owner-only Creative Dashboard link. Preserve local drafts, running timers and history. |
| 5 | CasinoAcademy | Verify the private development snapshot and repository target separately. Link the Development Workstream behind owner access and preserve release and gameplay acceptance gates. |
| 6 | Founder Companion | Verify the personal Site and personal record first. Add or verify Home return within the personal UI. Keep the business side and the live bridge outside scope. |
| 7 | Game Shelf | Wait for private hosting and mobile acceptance. Verify private Development Surface navigation while preserving the catalog and storage. |
| 8 | Family technology | Wait for verification of the authenticated application destination. Keep operational and family details behind owner access. |

## Reversal

Before merge, close the draft PR and keep its branch for review. After an authorized release, revert the squash commit with `git revert --no-commit <merge-sha>` or a merge commit with `git revert --no-commit -m 1 <merge-sha>` on a fresh branch from current `main`. A raw revert restores old private addresses. Retain the safe fallbacks, remove reintroduced addresses and retain the artifact boundary checks before committing a rollback. Run the build, scan, browser checks and legacy Wine redirects before opening a separate rollback PR. A main merge can deploy through the existing workflow and requires separate approval.
