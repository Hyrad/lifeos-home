"""LifeOS private platform service: one Unix-socket HTTP endpoint behind Tailscale Serve.

Every request (assets, APIs, health, unknown paths) first proves the kernel identity of the
tailscaled proxy, then the owner/device identity, then resource-specific policy. Nothing is served
before authentication. Domains are isolated: a failing adapter/store returns an error for its own
routes only and never takes the gateway or other domains down.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import socketserver
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler

from . import VERSION
from . import identity as ident
from .adapters.wine_supplies import API_PATH as WINE_API, NotionReader
from .config import APPS, ConfigSource, authorize_resource
from .identity import Failure, VerifiedProxy, authenticate
from . import storage
from . import backup

CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
       "font-src 'self'; manifest-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'self'; "
       "form-action 'none'; frame-ancestors 'none'")
MIME = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml',
        '.png': 'image/png', '.webmanifest': 'application/manifest+json', '.ico': 'image/x-icon',
        '.woff2': 'font/woff2', '.webp': 'image/webp', '.json': 'application/json'}
REGISTRY_API = '/api/v1/platform/registry'
HEALTH_API = '/api/v1/platform/health'
SESSION_API = '/api/v1/cooking/session'
SAFE_PATH = re.compile(r'/[A-Za-z0-9._~/\-]*')
MAX_BODY = 16384

# Static, non-secret registry metadata. Runtime availability/version come from configuration.
REGISTRY = [
    {'id': 'home', 'name': 'LifeOS Home', 'icon': 'compass', 'owner': 'LifeOS Home (Hyrad/lifeos-home)',
     'capabilities': ['navigation', 'registry']},
    {'id': 'cooking', 'name': 'LifeOS Cooking', 'icon': 'food', 'owner': 'Cuisine area (lifeos-cooking)',
     'capabilities': ['recipe-snapshots', 'guided-cooking', 'timers', 'session-resume']},
    {'id': 'wine', 'name': 'Wine Production', 'icon': 'wine', 'owner': 'Wine Making area (Hyrad/lifeos-wine-production)',
     'capabilities': ['wine-supplies-read']},
]
EXTERNAL = [
    # Outside the shared origin by design: own lifecycle/backends or higher sensitivity.
    {'id': 'game-shelf', 'name': 'Game Shelf', 'icon': 'game', 'status': 'external',
     'reason': 'independent backend and JSON library; native actions stay on device'},
    {'id': 'health', 'name': 'Health', 'icon': 'health', 'status': 'external',
     'reason': 'sensitive domain outside the first shared-origin group'},
]


def log(event, **fields):
    """Structured, redacted: no paths, headers, identities, tokens or upstream data."""
    sys.stderr.write(json.dumps({'ts': round(time.time(), 3), 'event': event, **fields}, sort_keys=True) + '\n')


def device_ref(stable_id):
    return hashlib.sha256(stable_id.encode()).hexdigest()[:8] if stable_id else None


class PlatformServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    request_queue_size = 32

    def __init__(self, socket_path, config_path, notion_token=None, device_api=None, release=None):
        self.config = ConfigSource(config_path)
        cfg = self.config.get()
        self.device_api = device_api
        self.release = release or 'development'
        self.reader = None
        if cfg.wine_source and notion_token:
            self.reader = NotionReader(notion_token, *cfg.wine_source)
        self.sessions = None
        self.sessions_error = None
        if 'cooking-sessions' in cfg.resources and cfg.resources['cooking-sessions'].enabled:
            try:
                storage.check_private_dir(cfg.data_dir)
                db = cfg.data_dir / storage.DB_NAME
                storage.migrate(db, before_migrate=backup.copy_for_premigration)
                self.sessions = storage.CookingSessions(db)
            except Exception as e:  # domain isolation: the gateway still starts
                self.sessions_error = type(e).__name__
                log('domain_unavailable', domain='cooking-sessions', error=self.sessions_error)
        self.limit_lock = threading.Lock()
        self.limits = {}
        self.slots = threading.BoundedSemaphore(16)
        old = os.umask(0o077)
        try:
            super().__init__(socket_path, Handler)
        finally:
            os.umask(old)
        os.chmod(socket_path, 0o600)

    def server_close(self):
        super().server_close()
        if self.sessions:
            self.sessions.close()

    def get_request(self):
        conn, _ = self.socket.accept()
        return conn, ('unix', 0)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        super().process_request(request, client_address)

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def rate(self, key, limit):
        now = int(time.monotonic() // 60)
        with self.limit_lock:
            self.limits = {k: v for k, v in self.limits.items() if v[0] == now}
            window, count = self.limits.get(key, (now, 0))
            self.limits[key] = (window, count + 1)
            if count >= limit:
                raise Failure(429, 'rate_limited')

    def sessions_state(self, cfg):
        if self.sessions is None:
            return 'unavailable' if self.sessions_error else 'disabled'
        allowed, _ = backup.recovery_status(cfg.data_dir)
        return 'read-write' if cfg.sessions_writes_enabled and allowed else 'read-only'


def route(path):
    """-> (kind, resource, api_client, app) without touching the filesystem."""
    if path == WINE_API:
        return 'api', 'wine', 'wine-private', None
    if path == SESSION_API:
        return 'api', 'cooking-sessions', 'cooking', None
    if path in (REGISTRY_API, HEALTH_API):
        return 'api', 'home', 'home', None
    if path == '/':
        return 'redirect', 'home', None, 'home'
    for app, (mount, resource) in APPS.items():
        if path == mount[:-1]:
            return 'redirect', resource, None, app
        if path.startswith(mount):
            return 'asset', resource, None, app
    return 'other', None, None, None


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    timeout = 15
    server_version = 'LifeOS'
    sys_version = ''

    def log_message(self, *args):
        pass

    def respond(self, status, content, content_type='application/json; charset=utf-8', extra=None):
        self.status_sent = status
        self.send_response(status)
        headers = {'Content-Type': content_type, 'Content-Length': str(len(content)), 'Cache-Control': 'no-store, private',
                   'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Content-Security-Policy': CSP,
                   'Cross-Origin-Resource-Policy': 'same-origin', 'Cross-Origin-Opener-Policy': 'same-origin',
                   'Permissions-Policy': 'camera=(), microphone=(), geolocation=()', **(extra or {})}
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(content)

    def json(self, status, value, extra=None):
        self.respond(status, json.dumps(value, ensure_ascii=False).encode(), extra=extra)

    def handle_any(self):
        started, kind, resource, node = time.monotonic(), 'other', None, None
        self.status_sent = None
        try:
            raw_path = self.path
            if len(raw_path) > 2048 or sum(len(k) + len(v) for k, v in self.headers.items()) > 16384:
                raise Failure(431, 'request_too_large')
            path, _, query = raw_path.partition('?')
            if '%' in raw_path or '..' in path or '//' in path or not SAFE_PATH.fullmatch(path):
                raise Failure(404, 'not_found')
            kind, resource, api_client, app = route(path)
            cfg = self.server.config.get()
            write = self.command in ('PUT', 'DELETE', 'POST', 'PATCH')
            if (kind == 'api' and query) or (write and kind != 'api'):
                raise Failure(404 if query else 405, 'not_found' if query else 'method_not_allowed')
            with VerifiedProxy(self.connection) as proxy:
                identity = authenticate(self.headers, cfg.origin, cfg.owner_login, cfg.known_devices, proxy.whois,
                                        api_client=api_client, write=write)
                node = identity.stable_id
                if kind == 'other':
                    raise Failure(404, 'not_found')
                authorize_resource(identity, cfg, resource, self.server.device_api)
                proxy.check_live()
                self.dispatch(kind, resource, app, path, cfg, identity, proxy)
        except Failure as e:
            self.json(e.status, {'error': e.code})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            log('error', where='handler', error=type(e).__name__)
            if self.status_sent is None:
                self.json(503, {'error': 'service_unavailable'})
        finally:
            self.close_connection = True
            log('request', cls=kind, resource=resource, status=self.status_sent, dev=device_ref(node),
                ms=round((time.monotonic() - started) * 1000))

    def dispatch(self, kind, resource, app, path, cfg, identity, proxy):
        if kind == 'redirect':
            self.respond(308 if path != '/' else 303, b'', extra={'Location': APPS[app][0]})
            return
        if kind == 'asset':
            if self.command not in ('GET', 'HEAD'):
                raise Failure(405, 'method_not_allowed')
            self.serve_asset(cfg, app, path, proxy)
            return
        # APIs: per-domain isolation; failures are typed and never include internals.
        try:
            if path == WINE_API:
                self.wine(identity, proxy)
            elif path == SESSION_API:
                self.session(cfg, identity, proxy)
            elif path == REGISTRY_API:
                self.only_get()
                self.json(200, self.registry(cfg, identity))
            elif path == HEALTH_API:
                self.only_get()
                self.json(200, self.health(cfg))
        except Failure:
            raise
        except Exception as e:
            log('domain_error', domain=resource, error=type(e).__name__)
            raise Failure(503, 'domain_unavailable') from None

    def only_get(self):
        if self.command not in ('GET', 'HEAD'):
            raise Failure(405, 'method_not_allowed')

    def serve_asset(self, cfg, app, path, proxy):
        entry = cfg.apps.get(app)
        if entry is None:
            raise Failure(404, 'not_found')
        dist = entry['dist'].resolve()
        relative = path[len(APPS[app][0]):] or 'index.html'
        last = relative.rsplit('/', 1)[-1]
        if '.' not in last:
            relative = 'index.html'  # client-side deep link / nested route: reload-safe
        target = (dist / relative)
        try:
            resolved = target.resolve(strict=True)
        except (FileNotFoundError, RuntimeError, OSError):
            raise Failure(404, 'not_found') from None
        if (not resolved.is_relative_to(dist) or target.is_symlink() or not resolved.is_file()
                or resolved.suffix not in MIME or resolved.name.startswith('.')):
            raise Failure(404, 'not_found')
        raw = resolved.read_bytes()
        if len(raw) > 4 * 1048576:
            raise Failure(404, 'not_found')
        proxy.check_live()
        self.respond(200, raw, MIME[resolved.suffix])

    def wine(self, identity, proxy):
        self.only_get()
        if self.server.reader is None:
            raise Failure(503, 'source_not_configured')
        self.server.rate(('wine', identity.stable_id), 10)
        result = json.dumps(self.server.reader.read(), ensure_ascii=False).encode()
        if len(result) > 200000:
            raise Failure(502, 'source_limit')
        proxy.check_live()
        self.respond(200, result)

    def session(self, cfg, identity, proxy):
        store = self.server.sessions
        if store is None:
            raise Failure(503, 'sessions_unavailable')
        self.server.rate(('sessions', identity.stable_id), 120)
        if self.command in ('GET', 'HEAD'):
            value = store.get()
            proxy.check_live()
            self.json(200, {'session': value, 'writes': self.server.sessions_state(cfg)},
                      extra={'ETag': '"r%d"' % (value['revision'] if value else 0)})
            return
        if self.command not in ('PUT', 'DELETE'):
            raise Failure(405, 'method_not_allowed')
        if self.server.sessions_state(cfg) != 'read-write':
            raise Failure(503, 'writes_disabled_recovery_gate')
        match = re.fullmatch(r'"r(\d{1,9})"', self.headers.get('If-Match', ''))
        if not match:
            raise Failure(428, 'precondition_required')
        body = None
        if self.command == 'PUT':
            if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                raise Failure(415, 'unsupported_media_type')
            try:
                length = int(self.headers.get('Content-Length', ''))
            except ValueError:
                raise Failure(411, 'length_required') from None
            if not 0 < length <= MAX_BODY:
                raise Failure(413, 'payload_too_large')
            try:
                body = json.loads(self.rfile.read(length))
            except ValueError:
                raise Failure(400, 'invalid_json') from None
        status, response = store.write(int(match.group(1)), body, self.headers.get('Idempotency-Key'))
        proxy.check_live()
        rev = (response.get('session') or {}).get('revision', 0)
        self.json(status, response, extra={'ETag': '"r%d"' % rev})

    def registry(self, cfg, identity):
        apps = []
        for meta in REGISTRY:
            mount, resource = APPS[meta['id']]
            policy = cfg.resources.get(resource)
            entry = cfg.apps.get(meta['id'])
            if entry is None or policy is None or not policy.enabled:
                status = 'unavailable'
            elif identity.stable_id not in policy.devices:
                status = 'not-authorized-for-this-device'
            elif identity.machine_authorized is not True and not policy.device_api:
                status = 'blocked-device-evidence'
            else:
                status = 'available'
            apps.append({**meta, 'route': mount, 'policy': resource, 'status': status,
                         'version': entry['version'] if entry else None, 'home': APPS['home'][0]})
        return {'contract': 'lifeos.registry/1', 'apps': apps, 'external': EXTERNAL}

    def health(self, cfg):
        _, recovery = backup.recovery_status(cfg.data_dir) if cfg.data_dir else (False, {'restore_drill': 'not_configured'})
        return {'contract': 'lifeos.health/1', 'service': 'lifeos-platform', 'version': VERSION, 'release': self.server.release,
                'apps': {a: ('ready' if (e['dist'] / 'index.html').is_file() else 'missing') for a, e in cfg.apps.items()},
                'domains': {'wine-supplies': 'configured' if self.server.reader else 'not-configured',
                            'cooking-sessions': self.server.sessions_state(cfg)},
                'recovery': recovery}

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_TRACE = do_CONNECT = handle_any


def main(argv=None):
    import argparse
    from .identity import DeviceAuthorization, protected_file
    p = argparse.ArgumentParser(prog='lifeos-platform')
    p.add_argument('--config', required=True)
    p.add_argument('--socket', required=True)
    p.add_argument('--release', default=None)
    args = p.parse_args(argv)
    cfg = ConfigSource(args.config).get()
    creds = os.environ.get('CREDENTIALS_DIRECTORY')
    token = device_api = None
    if cfg.wine_source and cfg.resources.get('wine') and cfg.resources['wine'].enabled:
        if not creds:
            raise SystemExit('Wine enabled but no protected credential directory')
        token = protected_file(Path(creds) / 'notion-token')
        if not token.startswith(('ntn_', 'secret_')) or len(token) < 25 or any(c.isspace() for c in token):
            raise SystemExit('Invalid service credential')
    if cfg.device_api_devices:
        if not creds:
            raise SystemExit('Device API approved for a resource but no protected credential directory')
        device_api = DeviceAuthorization(protected_file(Path(creds) / 'tailscale-oauth-id'),
                                         protected_file(Path(creds) / 'tailscale-oauth-secret'), cfg.device_api_devices)
    sock = Path(args.socket)
    if sock.exists():
        raise SystemExit('Socket already exists; refuse replacement')
    release = args.release or Path(__file__).resolve().parents[2].name  # .../releases/<name>/server/lifeos_platform
    with PlatformServer(str(sock), args.config, token, device_api, release) as server:
        log('start', version=VERSION, release=server.release,
            resources=sorted(k for k, v in cfg.resources.items() if v.enabled))
        try:
            server.serve_forever()
        finally:
            sock.unlink(missing_ok=True)


__all__ = ['PlatformServer', 'Handler', 'route', 'main', 'ident']
