# LifeOS navigation v1

Home v0.3.0 keeps the public dashboard on GitHub Pages. Notion owns canonical personal records. Each application owns its source and runtime. The internal routing inventory belongs in the existing private LifeOS Home implementation checkpoint. Keep it out of this public repository, PR text, screenshots and builds.

## Web Home is the primary launcher

NAV-04 keeps the existing web app as the single primary interface. Notion remains authoritative for records and opens as a destination. The private Notion widget experiment is optional. Specialist apps retain their separate deployments.

| Class | Meaning in Home |
| --- | --- |
| A | Approved launch address. The destination may still require sign-in. |
| B | Candidate for explicit publication approval. The URL is absent from public source and builds. |
| C | Restricted address or association. Deliver the route only after authorization. |
| D | Destination missing or insufficiently verified. Show availability separately from route verification. |

Private classification, exact addresses, and source evidence are maintained in the existing owner checkpoint. A page requiring sign-in can still disclose metadata through a link, including workspace branding before authentication.

## NAV-05 approved Notion addresses

On 2026-11-08 Hyrad approved public disclosure of the exact Wine Making Area, Travel Area, Cookbook and Shopping Hub URLs. Workstreams links to the two Areas and offers separate Wine Production and Journey Tracker app launches. Surfaces holds the direct Cookbook and Shopping Hub links. The existing Wine project card and Wine and Travel domain cards also link to their approved Areas.

Notion controls content access and sign-in. Approval covers the exact URLs only. Child pages, query strings, fragments, saved views and other identifiers remain excluded. The build checker requires all four exact URLs and rejects unapproved destinations. See the private implementation checkpoint for the remaining gates.

## Public routing

| Module | Application on public Home | Canonical access |
| --- | --- | --- |
| Wine Production | Direct public app, standalone manifest | Approved Wine Making Area link |
| Journey Tracker | Direct public app, standalone manifest | Approved Travel Area link |
| Health | Previously approved exact launch URL. Owner sign-in required. | Private Notion workspace |
| Music, CasinoAcademy | Private app links held in owner records | Private Notion workspace |
| Game Shelf | Private hosting gate | Private development Surface |
| Family technology, founder workspace | Launch routes withheld pending verification | Private access |
| Cooking and Shopping | Directory entries | Approved Cookbook and Shopping Hub links in Surfaces |
| Fitness, Game development, LifeOS Home records | Directory entries | Private Notion workspace |

Home retains its standalone manifest. Device installation and external-link handling require Safari testing. Wine, Journey Tracker and Health launch within two Home interactions. Health's own sign-in is separate. The generic Notion launcher opens Notion, where the owner must find their workspace and the relevant record. The two-interaction goal for private Workstreams remains unmet.

## Navigation regression audit

Compared the PR base `2681425`, original draft `31d9ead`, and revised draft. The report names destinations without repeating restricted addresses.

| Entry | Base | Original draft | Revised draft |
| --- | --- | --- | --- |
| Health app | Direct desktop sidebar launch, owner sign-in | Removed | Same direct sidebar launch restored. Apps also exposes it on desktop and mobile with sign-in guidance. |
| Wine app | Direct sidebar and Project tool launch | Retained and added to Apps | Retained. Both legacy Wine paths still preserve query and hash. |
| Journey Tracker | Travel tracker tool opened the private Travel project | Direct public app in Apps and the Travel card | Direct public app retained in both places. The private project still needs manual discovery. |
| Google Calendar | Direct in Upcoming and Quick actions | Retained | Direct in Upcoming and Core LifeOS. The `#actions` bookmark remains valid. |
| Project card context | Direct Wine Area, Game Shelf Project, Caribbean cruise Project and Fitness Project | All open generic Notion | NAV-05 restores Wine Making Area. Manual discovery remains for the other project contexts. Game Shelf's former tool link also opened its Project. The tool shows that private hosting is pending. |
| Surfaces | Direct Cookbook, Shopping Hub and Grocery shopping | All open generic Notion | Cookbook and Shopping Hub open directly in NAV-05. Grocery shopping still requires manual discovery. |
| Life domains | Direct Food, Home, Finance, Travel, Family, Health, Fitness, Personal planning, Music, Entertainment, Purchases & equipment, Wine production, Camping, Bicolline, Learning and Gaming | All open generic Notion | NAV-05 restores the Wine and Travel Area links. Manual discovery remains for the other 14. Search and expand still work. The Health app and the private Health Area have separate routes. |
| Core Notion records | Direct Tasks, Projects, Notes & Memory, Reviews, Cookbook, and Shopping Hub across Home | Generic Notion fallback | Core LifeOS lists each record with its access state. A separate generic Notion link supports manual discovery. |
| Other Notion entry points | Today and sidebar opened Notion Home. Footer opened Life Command Center. Projects heading opened Projects. System overview opened Surface governance. | All open generic Notion | Manual discovery remains. The Workstreams directory describes the manual lookup. |
| Home navigation and install | Section anchors, manifest, icons and standalone scope | Retained with new Apps and Workstreams anchors | Retained. Physical Safari and Home Screen verification is pending. |

The earlier public edition included direct addresses for selected Notion records behind Notion access controls. The current classified inventory holds those routes for personal access. NAV-04 retained the approved Health app address. NAV-05 adds the four specifically approved Notion addresses above. Health reports, canonical records and other restricted Site addresses stay in owner records.

### Gated decision

Approve category B addresses individually after reviewing metadata on signed-out access. Category C requires authenticated delivery in the same Home UI. Public GitHub Pages can keep serving the current shell and cannot deliver restricted data itself. Existing owner-private Sites confirm a managed access option. A separately authorized pilot could use the same Home source and UI on an owner-private origin if unauthenticated requests for HTML, assets and route payloads are all denied. A change of origin needs a Home Screen reinstall and return-path acceptance.

If the current Pages origin must remain the installed entry, evaluate an owner-authenticated route endpoint consumed by Home. Validate identity and authorization server-side on every request, restrict browser origins, send private responses with `Cache-Control: no-store`, and keep restricted inventory outside the public repository and build. Verify login and return behavior in standalone Safari without assuming cross-site cookies. Keep route-only data and existing Notion permissions. No provider, session or hosting change is part of NAV-04.

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
