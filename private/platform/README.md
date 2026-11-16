# LifeOS private platform (LIFEOS-PLATFORM-02)

One small Python service (stdlib only) that is the shared private front door for LifeOS apps on
the IdeaPad: **authentication + per-resource authorization + private asset routing + app APIs**
in one process behind one dedicated Tailscale Serve HTTPS handler. Implements the PLATFORM-01
blueprint recorded in the LifeOS Apps Ecosystem decision.

Nothing in this directory is part of the public GitHub Pages build. Real origins, owner login,
device StableIDs, Notion source pins, credentials, databases and backups live only in protected
runtime files outside Git and outside every release artifact.

## Layout

| Path | Purpose |
| --- | --- |
| `lifeos_platform/identity.py` | Wine v1.207-private.4 kernel/LocalAPI/Device-API proof (verbatim, provenance in header) + resource-independent `authenticate()` |
| `lifeos_platform/config.py` | Strict protected runtime config; per-resource device policies; live revocation |
| `lifeos_platform/server.py` | Unix-socket HTTP server: routing, assets, registry, health, Wine and Cooking-session APIs |
| `lifeos_platform/adapters/wine_supplies.py` | Wine's read-only Notion reader (verbatim) |
| `lifeos_platform/storage.py` | SQLite: versioned migrations, Cooking session resume (revisioned, idempotent) |
| `lifeos_platform/backup.py` | Consistent encrypted off-device backup, retention, isolated restore, recovery gate |
| `lifeos_platform/wine_compat.py` | Wine's original `authorize()` contract on the shared engine (regression facade) |
| `deploy/` | Immutable staging, unit template, provisional activation with automatic rollback, live acceptance |
| `tests/` | Wine's ported suites + platform suites (`python3 -m unittest discover -s tests`) |

## Request pipeline (every path, including assets, health and unknown URLs)

1. Size/path sanity (no `%`, `..`, `//`, oversized headers) → route classification (no filesystem).
2. **Kernel proof**: incoming socket peer (SO_PEERCRED + SO_PEERPIDFD) must be the same live process
   as the root-owned `/run/tailscale/tailscaled.sock` peer, pinned by an O_NOFOLLOW walk. Direct
   socket connections from any other local process are denied (403).
3. **Identity**: exact owner login, no Funnel, exact Host/X-Forwarded-Host/Proto, Origin and
   fetch-site checks, duplicate critical headers rejected; LocalAPI whois on the verified
   connection: login and numeric user agree, StableID is known, untagged, unexpired key, source
   address equals a node host prefix. Explicit `MachineAuthorized` must be `true`.
4. **Resource policy** (`home`, `cooking`, `wine`, `cooking-sessions`): enabled, unexpired, device
   on *that* resource's allowlist. If LocalAPI omitted `MachineAuthorized` (all remote peers on
   Tailscale 1.104.5), access requires fresh positive Device API evidence **and** owner approval of
   Device API use for that resource. Nothing is cached.
5. APIs additionally need their client label (`X-LifeOS-Client`) and same-origin fetch context;
   writes need an exact `Origin`, JSON content type, `If-Match` revision and bounded body.

Health, Game Shelf and admin/native actions cannot be configured on this origin at all.

## Application integration contract (`lifeos.registry/1`)

A LifeOS web app joins the shared origin by:

1. Building with a fixed base path (`/lifeos-<app>/`) and relative/same-origin URLs only; no
   hostnames, ports, tokens or private identifiers in its bundle.
2. Being reload-safe for nested client routes (the platform serves `index.html` for any
   extensionless path under the mount).
3. Linking back to `/lifeos-home/` in its private build (public builds keep public Home).
4. Calling APIs same-origin with `X-LifeOS-Client: <app>`, `redirect: "error"`, no CORS.
5. Getting a reviewed entry in `config.APPS`/`server.REGISTRY`, its own resource policy, and
   an owner-approved device allowlist. One authentication system is not one allowlist.

Apps keep their own repositories, versions and release cycles. The platform release pins the
exact app artifacts it serves (hash manifest). Apps needing stronger isolation (Health, native
Game Shelf actions) should reuse this authentication code on a **separate origin**: everything on
one origin is mutually trusted browser code.

## Data and recovery

* Notion remains authoritative for shopping, recipes, tasks and governance. The Wine adapter is a
  read-only projection of the one canonical weekly shopping Task; no local shopping copy exists.
* SQLite holds only Cooking session resume (`cooking_session`, 48 h retention). It stores a
  recipe *reference*, never recipe content, and never marks a recipe as cooked.
* Rollback journal + `synchronous=EXTRA`; explicit migrations with checksums; a release refuses
  a newer schema; pre-migration same-disk copy (rollback aid only, not disaster recovery).
* Backups: SQLite backup API → integrity check → manifest → gpg public-key encryption → designated
  separate-filesystem destination (marker file, owner-only) → 14 daily / 8 weekly retention.
* **Recovery gate**: real session writes stay disabled until a restore drill from the designated
  destination succeeded within 92 days and a backup succeeded within 48 h. Targets (not proof):
  RPO 24 h, RTO 4 h after replacement hardware and owner access, quarterly drill.

## Operations

```
deploy/stage.py create --root ~/.local/share/lifeos-platform --home <private dist> --cooking <release> [--wine <private dist>]
deploy/stage.py verify --release <release dir>
deploy/activate.py preflight|activate|rollback --port <unused port> --release <dir> --evidence <dir> [--keep]
python3 -I run.py check-config|migrate|backup|drill|recovery-status --config <file> ...
```

`activate.py` changes only the platform unit and one new Serve port, verifies the rest of Serve is
byte-for-byte unchanged and existing routes respond as before, runs `deploy/accept.py`, and
rolls back automatically on any failure. The unit is AF_UNIX-only with no IP access while Wine
live data and the Device API are disabled.
