# LifeOS Home v0.3.1 — maintenance release

v0.3.1 records operational milestones reached after v0.3.0. The application is functionally unchanged: same navigation, modules, links, layout, content security policy and public-data boundary. The only change you can see is the version label.

## What changed in this repository

- Version 0.3.0 → 0.3.1 in `package.json`. Every on-screen version label reads this value.
- These release notes and a README pointer.

## Infrastructure milestones (outside this repository)

- **Persistent private hosting.** The production build also runs on the owner's personal server. A dedicated user-level service serves a frozen copy of the built `dist/` output on the loopback interface. Access is limited to the owner's private tailnet over HTTPS; nothing is exposed publicly. The service starts at boot, restarts after crashes, and is independent of terminal or assistant sessions. GitHub Pages remains the public deployment and fallback.
- **Tested deployment and rollback.** Each private release is an immutable, read-only copy of a tested build, with its commit and file hashes recorded. Switching releases, rolling back to the accepted build, and an emergency fallback to the previous preview method were all exercised.
- **Network security upgrade.** The server's Tailscale client was upgraded to 1.104.5, which includes the October 2026 security fixes. This is an infrastructure change only; no application code was involved.

Host names, addresses, ports and operating procedures are kept in the owner's private implementation checkpoint, not in this public repository.

## Verification for this release

The checks are the same as for v0.3.0, run against the v0.3.1 build:

- unit tests;
- typecheck and production build;
- public-artifact boundary check;
- production browser checks across seven viewports, covering layout, navigation and reload, interactions, keyboard and automated WCAG A/AA checks, and outbound-link intercepts.

The browser check confirms the displayed version matches `package.json`.

## Remaining acceptance gates

- Physical iPad verification of the private deployment after the network upgrade, and of this version label once v0.3.1 is promoted.
- Proof that the private service survives a full server reboot. It is configured to start at boot, but this has not been physically tested; a reboot needs separate owner approval.
- Owner review before merge, tagging, private promotion or a GitHub Pages deployment.

## Rollback

v0.3.1 changes only metadata, so rolling back means returning to the v0.3.0 build. On the private server, switch back to the retained v0.3.0 release. For GitHub Pages, revert the release commit through the normal pull-request workflow.
