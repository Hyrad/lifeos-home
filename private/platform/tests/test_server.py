import json
import os
import threading
import unittest
from unittest.mock import Mock, patch

from support import ORIGIN, Harness, headers, srv, whois_for, write_config, base_config  # noqa: F401


class RealSocketTests(unittest.TestCase):
    """No substituted proof: an ordinary local process is not tailscaled and must be denied."""

    def test_unprivileged_direct_socket_denied_for_assets_and_apis(self):
        if os.getuid() == 0:
            self.skipTest('Requires unprivileged test runner')
        import tempfile, http.client, socket
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            cfg = base_config(folder)
            write_config(Path(folder) / 'platform.json', cfg)
            with srv.PlatformServer(str(Path(folder) / 's'), Path(folder) / 'platform.json', 'x') as server:
                t = threading.Thread(target=server.serve_forever, daemon=True); t.start()
                try:
                    for path in ['/lifeos-home/', '/lifeos-cooking/assets/app.js', '/api/v1/wine-supplies',
                                 '/api/v1/platform/health', '/api/v1/cooking/session', '/nope']:
                        c = http.client.HTTPConnection('unix', timeout=3)
                        c.sock = socket.socket(socket.AF_UNIX); c.sock.connect(server.server_address)
                        c.request('GET', path, headers=headers('home'))
                        r = c.getresponse(); body = r.read(); c.close()
                        self.assertEqual(r.status, 403, path)
                        self.assertEqual(json.loads(body), {'error': 'forbidden'})
                        self.assertNotIn(b'synthetic', body)
                        self.assertIsNone(r.getheader('Access-Control-Allow-Origin'))
                    self.assertEqual(os.stat(server.server_address).st_mode & 0o777, 0o600)
                finally:
                    server.shutdown(); t.join()


class RoutingAndAssetTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness(self)

    def test_portal_redirect_and_mount_redirects(self):
        status, h, _ = self.h.request('GET', '/')
        self.assertEqual((status, h['location']), (303, '/lifeos-home/'))
        status, h, _ = self.h.request('GET', '/lifeos-cooking')
        self.assertEqual((status, h['location']), (308, '/lifeos-cooking/'))

    def test_direct_bookmarks_and_nested_reload_serve_app_shell(self):
        for path, name in [('/lifeos-home/', b'home'), ('/lifeos-cooking/', b'cooking'),
                           ('/lifeos-cooking/recipes/ratatouille', b'cooking'), ('/lifeos-cooking/session?step=2', b'cooking'),
                           ('/lifeos-wine-production/', b'wine')]:
            self.h.device = 'nMac' if 'wine' in path else 'nPad'
            status, h, body = self.h.request('GET', path, headers())
            with self.subTest(path=path):
                self.assertEqual(status, 200)
                self.assertIn(name + b' synthetic', body)
                self.assertIn("frame-ancestors 'none'", h['content-security-policy'])
                self.assertIn('no-store', h['cache-control'])

    def test_assets_typed_and_traversal_or_secret_denied(self):
        status, h, body = self.h.request('GET', '/lifeos-home/assets/app.js')
        self.assertEqual((status, h['content-type']), (200, 'text/javascript'))
        for path in ['/lifeos-home/../secret.txt', '/lifeos-home/%2e%2e/secret.txt', '/lifeos-home/assets/missing.js',
                     '/lifeos-home/.hidden.js', '/lifeos-home//etc/passwd', '/lifeos-home/assets/app.exe', '/platform.json',
                     '/lifeos-health/', '/game-shelf/', '/lifeos-home/.vite/manifest.json']:
            status, _, body = self.h.request('GET', path)
            with self.subTest(path=path):
                self.assertEqual(status, 404)
                self.assertNotIn(b'PRIVATE', body)

    def test_symlink_inside_dist_is_not_followed(self):
        link = self.h.folder / 'apps' / 'home' / 'leak.js'
        link.symlink_to(self.h.folder / 'secret.txt')
        status, _, body = self.h.request('GET', '/lifeos-home/leak.js')
        self.assertEqual(status, 404); self.assertNotIn(b'PRIVATE', body)

    def test_write_methods_on_assets_refused(self):
        for method in ['POST', 'PUT', 'DELETE']:
            self.assertEqual(self.h.request(method, '/lifeos-home/', body=b'{}')[0], 405)


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness(self)

    def test_assets_require_authentication_too(self):
        self.assertEqual(self.h.request('GET', '/lifeos-home/', headers(**{'Tailscale-User-Login': None}))[0], 401)
        self.assertEqual(self.h.request('GET', '/lifeos-home/', headers(**{'Tailscale-User-Login': 'other@example.test'}))[0], 403)
        self.h.device = 'nStranger'
        self.assertEqual(self.h.request('GET', '/lifeos-home/')[0], 403)
        self.assertEqual(self.h.request('GET', '/does-not-exist')[0], 403)  # unknown paths do not reveal 404 pre-auth

    def test_resource_policies_are_independent(self):
        # nPad: home+cooking+sessions, not wine. nMac: home+cooking+wine, not sessions.
        self.h.device = 'nPad'
        self.assertEqual(self.h.request('GET', '/lifeos-wine-production/')[0], 403)
        self.assertEqual(self.h.request('GET', '/api/v1/wine-supplies', headers('wine-private'))[0], 403)
        self.assertEqual(self.h.request('GET', '/api/v1/cooking/session', headers('cooking'))[0], 200)
        self.h.device = 'nMac'
        self.assertEqual(self.h.request('GET', '/lifeos-wine-production/')[0], 200)
        self.assertEqual(self.h.request('GET', '/api/v1/cooking/session', headers('cooking'))[0], 403)

    def test_omitted_machine_evidence_denied_without_approved_device_api(self):
        self.h.machine = None
        for path, client in [('/lifeos-home/', None), ('/api/v1/platform/registry', 'home')]:
            self.assertEqual(self.h.request('GET', path, headers(client))[0], 403)
        self.h.machine = False
        self.assertEqual(self.h.request('GET', '/lifeos-home/')[0], 403)

    def test_device_api_used_only_for_approved_resource(self):
        api = Mock(); api.verify.return_value = True
        h = Harness(self, lambda c: c['resources']['cooking'].update(device_api=True), device_api=api)
        h.machine = None
        self.assertEqual(h.request('GET', '/lifeos-cooking/')[0], 200)
        self.assertEqual(api.verify.call_count, 1)
        self.assertEqual(h.request('GET', '/lifeos-home/')[0], 403)  # home not approved for Device API
        self.assertEqual(api.verify.call_count, 1)
        api.verify.return_value = False
        self.assertEqual(h.request('GET', '/lifeos-cooking/')[0], 403)  # never cached

    def test_api_requires_client_label_and_same_origin(self):
        self.assertEqual(self.h.request('GET', '/api/v1/platform/registry', headers())[0], 403)
        self.assertEqual(self.h.request('GET', '/api/v1/platform/registry', headers('wine-private'))[0], 403)
        self.assertEqual(self.h.request('GET', '/api/v1/platform/registry', headers('home', **{'Sec-Fetch-Site': None}))[0], 403)
        self.assertEqual(self.h.request('GET', '/api/v1/platform/registry', headers('home', Origin='https://evil.example'))[0], 403)
        self.assertEqual(self.h.request('GET', '/api/v1/platform/registry?x=1', headers('home'))[0], 404)
        self.assertEqual(self.h.request('GET', '/api/v1/platform/registry', headers('home'))[0], 200)

    def test_forwarding_host_origin_and_funnel_violations(self):
        for change in [{'Host': 'evil'}, {'X-Forwarded-Host': 'other.ts.net'}, {'X-Forwarded-Proto': 'http'},
                       {'Origin': 'https://platform.test.ts.net:10000'}, {'Sec-Fetch-Site': 'cross-site'},
                       {'Tailscale-Funnel-Request': '1'}, {'X-Forwarded-For': '100.64.0.9, 100.64.0.1'}]:
            with self.subTest(change=change):
                self.assertEqual(self.h.request('GET', '/lifeos-home/', headers(**change))[0], 403)

    def test_disabled_or_expired_policy_and_revocation_without_restart(self):
        self.assertEqual(self.h.request('GET', '/lifeos-cooking/')[0], 200)
        self.h.update(lambda c: c['resources']['cooking'].update(enabled=False))
        self.assertEqual(self.h.request('GET', '/lifeos-cooking/')[0], 403)
        self.assertEqual(self.h.request('GET', '/lifeos-home/')[0], 200)
        self.h.update(lambda c: c.update(authorization_expires_at='2020-01-01T00:00:00Z'))
        self.assertEqual(self.h.request('GET', '/lifeos-home/')[0], 403)

    def test_broken_or_unsafe_config_fails_closed(self):
        self.h.config_path.chmod(0o644)
        self.assertEqual(self.h.request('GET', '/lifeos-home/')[0], 503)
        self.h.config_path.chmod(0o600)
        self.assertEqual(self.h.request('GET', '/lifeos-home/')[0], 200)
        self.h.config_path.write_text('{"schema": 1')
        self.assertEqual(self.h.request('GET', '/lifeos-home/')[0], 503)

    def test_proxy_death_before_response_returns_no_private_bytes(self):
        self.h.proxy_live = False
        for path, client in [('/lifeos-home/', None), ('/api/v1/platform/health', 'home')]:
            status, _, body = self.h.request('GET', path, headers(client))
            self.assertEqual(status, 403); self.assertNotIn(b'synthetic', body)


class WineApiTests(unittest.TestCase):
    """Re-implementation of Wine's PolicyAndHttpTests against the shared server."""

    def setUp(self):
        self.h = Harness(self)
        self.h.device = 'nMac'

    def test_success_contract_and_safe_errors(self):
        with patch.object(self.h.server.reader, 'read', return_value={'items': [], 'fetchedAt': '2030-01-01T00:00:00Z'}):
            status, h, body = self.h.request('GET', '/api/v1/wine-supplies', headers('wine-private'))
            self.assertEqual(status, 200); self.assertEqual(set(json.loads(body)), {'items', 'fetchedAt'})
        for failure in [srv.Failure(503, 'source_access_unavailable'), srv.Failure(504, 'upstream_timeout'),
                        RuntimeError('PRIVATE SECRET MUST NOT LEAK')]:
            with patch.object(self.h.server.reader, 'read', side_effect=failure):
                status, _, body = self.h.request('GET', '/api/v1/wine-supplies', headers('wine-private'))
                self.assertGreaterEqual(status, 500); self.assertNotIn(b'PRIVATE', body)
        self.assertEqual(self.h.request('GET', '/api/v1/wine-supplies?id=other', headers('wine-private'))[0], 404)
        self.assertEqual(self.h.request('POST', '/api/v1/wine-supplies', headers('wine-private', Origin=ORIGIN), b'{}')[0], 405)

    def test_rate_limit(self):
        with patch.object(self.h.server.reader, 'read', return_value={'items': [], 'fetchedAt': 'x'}):
            codes = [self.h.request('GET', '/api/v1/wine-supplies', headers('wine-private'))[0] for _ in range(11)]
        self.assertEqual(codes[:10], [200] * 10); self.assertEqual(codes[10], 429)

    def test_unconfigured_source_is_explicit_and_isolated(self):
        h = Harness(self, token=None); h.device = 'nMac'
        self.assertEqual(h.request('GET', '/api/v1/wine-supplies', headers('wine-private'))[0], 503)
        self.assertEqual(h.request('GET', '/lifeos-wine-production/')[0], 200)


class RegistryAndHealthTests(unittest.TestCase):
    def test_registry_per_device_status_without_identifiers(self):
        h = Harness(self)
        status, _, body = h.request('GET', '/api/v1/platform/registry', headers('home'))
        reg = json.loads(body)
        self.assertEqual(reg['contract'], 'lifeos.registry/1')
        apps = {a['id']: a for a in reg['apps']}
        self.assertEqual(apps['wine']['status'], 'not-authorized-for-this-device')
        self.assertEqual(apps['cooking']['status'], 'available')
        self.assertEqual(apps['cooking']['route'], '/lifeos-cooking/')
        self.assertTrue(all(a['home'] == '/lifeos-home/' for a in reg['apps']))
        self.assertEqual({e['id'] for e in reg['external']}, {'game-shelf', 'health'})
        for secret in [b'nPad', b'nMac', b'owner@', b'a' * 32, b'ts.net', b'/tmp', b'dist']:
            self.assertNotIn(secret, body)

    def test_health_sanitized(self):
        h = Harness(self)
        status, _, body = h.request('GET', '/api/v1/platform/health', headers('home'))
        d = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(d['apps'], {'home': 'ready', 'cooking': 'ready', 'wine': 'ready'})
        self.assertEqual(d['domains']['cooking-sessions'], 'read-write')
        for secret in [b'nPad', b'owner@', b'a' * 32, b'/tmp', b'synthetic-not-a-token']:
            self.assertNotIn(secret, body)


class SessionApiTests(unittest.TestCase):
    BODY = {'recipeRef': 'ratatouille', 'step': 2, 'servings': 4, 'completedIngredients': ['i0', 'i3'], 'completedSteps': ['s0'],
            'timers': [{'id': 'oven', 'deadline': 4102444800000}]}

    def setUp(self):
        self.h = Harness(self)

    def put(self, rev, body=None, **extra):
        return self.h.request('PUT', '/api/v1/cooking/session',
                              headers('cooking', Origin=ORIGIN, **{'If-Match': f'"r{rev}"', 'Content-Type': 'application/json', **extra}),
                              body if body is not None else self.BODY)

    def test_create_read_update_conflict_delete(self):
        status, h, body = self.h.request('GET', '/api/v1/cooking/session', headers('cooking'))
        self.assertEqual((status, json.loads(body)['session'], h['etag']), (200, None, '"r0"'))
        status, h, body = self.put(0)
        self.assertEqual((status, h['etag']), (200, '"r1"'))
        self.assertEqual(self.put(0)[0], 409)  # stale writer
        status, _, body = self.put(1, {**self.BODY, 'step': 3})
        self.assertEqual(json.loads(body)['session']['revision'], 2)
        status, _, body = self.put(1, {**self.BODY, 'step': 9})
        self.assertEqual(status, 409); self.assertEqual(json.loads(body)['session']['step'], 3)
        status, _, _ = self.h.request('DELETE', '/api/v1/cooking/session', headers('cooking', Origin=ORIGIN, **{'If-Match': '"r2"'}))
        self.assertEqual(status, 200)

    def test_write_preconditions(self):
        self.assertEqual(self.h.request('PUT', '/api/v1/cooking/session', headers('cooking', **{'If-Match': '"r0"', 'Content-Type': 'application/json'}), self.BODY)[0], 403)  # no Origin
        self.assertEqual(self.put(0, **{'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.h.request('PUT', '/api/v1/cooking/session', headers('cooking', Origin=ORIGIN, **{'Content-Type': 'application/json'}), self.BODY)[0], 428)
        self.assertEqual(self.put(0, {**self.BODY, 'recipe': {'title': 'x'}})[0], 422)
        self.assertEqual(self.put(0, b'x' * 20000)[0], 413)
        self.assertEqual(self.put(0, b'{not json')[0], 400)

    def test_idempotent_retry(self):
        a = self.put(0, **{'Idempotency-Key': 'retry-key-0001'})
        b = self.put(0, **{'Idempotency-Key': 'retry-key-0001'})
        self.assertEqual((a[0], b[0]), (200, 200)); self.assertEqual(json.loads(a[2]), json.loads(b[2]))
        self.assertEqual(self.put(0, {**self.BODY, 'step': 7}, **{'Idempotency-Key': 'retry-key-0001'})[0], 422)

    def test_writes_blocked_when_config_disables(self):
        h = Harness(self, lambda c: c['cooking_sessions'].update(writes_enabled=False))
        self.assertEqual(h.request('PUT', '/api/v1/cooking/session', headers('cooking', Origin=ORIGIN, **{'If-Match': '"r0"', 'Content-Type': 'application/json'}), self.BODY)[0], 503)


class RecoveryGateTests(unittest.TestCase):
    BODY = SessionApiTests.BODY

    def test_writes_blocked_without_recovery_gate(self):
        h = Harness(self, writes_gate=False)
        status, _, body = h.request('GET', '/api/v1/cooking/session', headers('cooking'))
        self.assertEqual(json.loads(body)['writes'], 'read-only')
        status, _, body = h.request('PUT', '/api/v1/cooking/session', headers('cooking', Origin=ORIGIN, **{'If-Match': '"r0"', 'Content-Type': 'application/json'}), self.BODY)
        self.assertEqual((status, json.loads(body)['error']), (503, 'writes_disabled_recovery_gate'))


class FaultIsolationTests(unittest.TestCase):
    def test_broken_session_store_does_not_affect_other_apps(self):
        def unsafe(c):
            c['data_dir'] = c['data_dir'] + '-missing'
        h = Harness(self, unsafe)
        self.assertEqual(h.request('GET', '/api/v1/cooking/session', headers('cooking'))[0], 503)
        self.assertEqual(h.request('GET', '/lifeos-cooking/')[0], 200)
        status, _, body = h.request('GET', '/api/v1/platform/health', headers('home'))
        self.assertEqual(json.loads(body)['domains']['cooking-sessions'], 'unavailable')

    def test_store_exception_is_contained(self):
        h = Harness(self)
        with patch.object(h.server.sessions, 'get', side_effect=RuntimeError('PRIVATE disk detail')):
            status, _, body = h.request('GET', '/api/v1/cooking/session', headers('cooking'))
        self.assertEqual(status, 503); self.assertNotIn(b'PRIVATE', body)
        self.assertEqual(h.request('GET', '/lifeos-home/')[0], 200)

    def test_oversized_request_rejected(self):
        h = Harness(self)
        self.assertEqual(h.request('GET', '/lifeos-home/' + 'a' * 2100)[0], 431)

    def test_logs_are_redacted(self):
        import io, contextlib
        h = Harness(self)
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            h.request('GET', '/lifeos-cooking/recipes/secret-recipe-name')
            h.request('GET', '/lifeos-home/', headers(**{'Tailscale-User-Login': 'other@example.test'}))
        out = buf.getvalue()
        for secret in ['secret-recipe-name', 'nPad', 'owner@', 'other@', '100.64.0.1']:
            self.assertNotIn(secret, out)
        self.assertIn('"event": "request"', out)


if __name__ == '__main__':
    unittest.main()
