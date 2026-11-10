# LifeOS Home v0.3.2 — LifeOS Cooking in Apps

v0.3.2 lists LifeOS Cooking as its own application. Everything else in Home is unchanged.

## What changed

- **Apps:** a distinct *LifeOS Cooking* entry. In the private deployment it opens the Cooking app from the same origin (`/lifeos-cooking/`). In the public GitHub Pages build it is listed with its status and *no link*, so the public site never shows a broken or private address.
- **Workstreams:** the Cooking row now offers *Open LifeOS Cooking app* in the private deployment, instead of indicating that no separate app exists.
- **Cooking description:** "Kitchen companion: guided recipes, servings and timers."
- The Cookbook link in Surfaces, all other apps, Workstreams, Projects and navigation are unchanged.
- Version 0.3.1 → 0.3.2.

The route is a same-origin path only. No hostname, port or private address is written into either build; the artifact boundary check enforces this.

## Verification

- Unit tests, including the public and private-server rendering of the Cooking entry.
- Typecheck and production builds (public and private-server).
- Public-artifact boundary check on both builds.
- Production browser checks across seven viewports, including Home → LifeOS Cooking → Home on the private deployment.

## Rollback

Private deployment: switch back to the retained v0.3.1 release. GitHub Pages: unchanged by this release until it is separately approved and merged.
