# Foundation v0.1

Home release: 0.2.0. Home owns the navigation shell; modules own independent repositories, dependencies, versions and deployments. Notion remains authoritative durable memory. GitHub owns implementation truth.

## Module contract

src/types/module.ts defines stable ID, public label, approved context URL, optional launch URL, access classification and icon/tone keys. src/data/modules.ts is a curated registry, not runtime discovery or authorization. Missing launch URLs fall back to context. Preserve the distinction between a Project/Area and its software. Only previously approved Wine destinations are included.

## Interface conventions

AppShell composes existing shared primitives. ModuleNavigation renders registry links; mobile section navigation supports keyboard activation, Escape, focus return and native anchors. Semantic tokens live in src/styles/tokens.css. Consumers may adopt documented conventions independently; no cross-repository package or runtime dependency is introduced. Localization and theme preferences remain future work; do not translate React by rewriting DOM text or inject inline styles.

## Future private gateway (not activated)

Browser session → separately hosted server → per-module/resource authorization → scoped Notion adapter → filtered response. Keep credentials server-side. Deny unauthenticated and unauthorized requests; validate sessions server-side; limit methods/origins and requests; redact logs. CORS does not authorize users. Private responses use Cache-Control: no-store; no service-worker or localStorage persistence by default. Start read-only, without mirroring Notion databases. Provider and hosting require separate review. No authentication or backend was added by this release.

## Validation and release

Node 24 and pnpm 11.25.0: install --frozen-lockfile; test; build; test:boundary; preview and test:browser. CI performs these gates before publishing artifacts; pull requests cannot deploy. Browser checks include four viewport sizes, anchors/reload, keyboard, accessibility, network errors, Home/Wine navigation and legacy redirects. Automated scans require manual public-content review. The cross-site checks intentionally depend on the live Wine site and may expose its failures independently of Home.

## Migration and rollback

No data, storage, Notion schema, permission, URL or independent-module migration. Legacy wine entries preserve query/hash. Before any approved release record the then-current production commit/workflow. Roll back with a revert commit and normal Pages workflow; verify version, navigation and both legacy redirects at four sizes. Never force-push for rollback. Merge and deployment require review of the completed PR.

## iPhone installation extension

Authorized follow-up: installable Home Screen dashboard. Static manifest, 180px Apple touch icon and 192/512px PNG icons, standalone metadata and safe-area styling. Stable start URL, ID and scope are /lifeos-home/. No service worker or new persistence is introduced. Domain modules remain independently installable in later work; this change covers Home only. Production publication remains subject to the existing review gate.
