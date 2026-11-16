#!/usr/bin/python3
"""Live acceptance probes for a provisionally activated platform, run on the server itself.

Requests travel through the real Tailscale Serve handler (real tailscaled kernel identity, real
identity headers). Results are sanitized (status codes, booleans, short body hashes only).
Exit 0 only if every expectation holds. Remote-device (Mac/iPad/iPhone) acceptance is NOT
covered here and must be recorded separately from real devices.
"""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import ssl
import sys

SOCK = f'/run/user/{os.getuid()}/lifeos-platform/platform.sock'


def get(host, port, method, path, headers=None, body=None):
    c = http.client.HTTPSConnection(host, port, timeout=10, context=ssl.create_default_context())
    c.request(method, path, body=body, headers=headers or {})
    r = c.getresponse()
    data = r.read()
    out = (r.status, {k.lower(): v for k, v in r.getheaders()}, data)
    c.close()
    return out


def direct_socket(path):
    c = http.client.HTTPConnection('localhost', timeout=5)
    c.sock = socket.socket(socket.AF_UNIX); c.sock.connect(SOCK)
    c.request('GET', path, headers={'Host': 'localhost', 'Tailscale-User-Login': 'spoof@example.test',
                                    'X-Forwarded-For': '100.64.0.1', 'X-Forwarded-Proto': 'https'})
    r = c.getresponse(); r.read(); c.close()
    return r.status


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', required=True); p.add_argument('--port', type=int, required=True); p.add_argument('--evidence', required=True)
    a = p.parse_args()
    origin = f'https://{a.host}:{a.port}'
    api = {'X-LifeOS-Client': 'home', 'Sec-Fetch-Site': 'same-origin', 'Accept': 'application/json'}
    results, failures = [], []

    def expect(name, actual, expected, detail=None):
        ok = actual == expected if not callable(expected) else expected(actual)
        results.append({'check': name, 'ok': ok, 'actual': actual if isinstance(actual, (int, str, bool)) else str(actual)[:80],
                        **({'detail': detail} if detail else {})})
        if not ok:
            failures.append(name)

    s, h, _ = get(a.host, a.port, 'GET', '/')
    expect('portal root redirects to Home', (s, h.get('location')), (303, '/lifeos-home/'))
    for path in ['/lifeos-home/', '/lifeos-cooking/', '/lifeos-cooking/nested/deep-link']:
        s, h, body = get(a.host, a.port, 'GET', path)
        expect(f'direct link {path}', s, 200, hashlib.sha256(body).hexdigest()[:12])
        expect(f'CSP on {path}', "frame-ancestors 'none'" in h.get('content-security-policy', ''), True)
        expect(f'no CORS on {path}', 'access-control-allow-origin' not in h, True)
    s, _, body = get(a.host, a.port, 'GET', '/api/v1/platform/registry', api)
    expect('registry', s, 200)
    reg = json.loads(body) if s == 200 else {}
    statuses = {x['id']: x['status'] for x in reg.get('apps', [])}
    expect('registry home available from server device', statuses.get('home'), 'available')
    expect('registry cooking available from server device', statuses.get('cooking'), 'available')
    expect('registry leaks no host', a.host.encode() not in body, True)
    s, _, body = get(a.host, a.port, 'GET', '/api/v1/platform/health', api)
    expect('health', s, 200)
    health = json.loads(body) if s == 200 else {}
    expect('health sessions not writable without recovery gate', health.get('domains', {}).get('cooking-sessions') in ('read-only', 'disabled'), True)
    expect('health wine source not configured', health.get('domains', {}).get('wine-supplies'), 'not-configured')
    # Negative cases through the real ingress.
    expect('foreign Origin denied', get(a.host, a.port, 'GET', '/lifeos-home/', {'Origin': 'https://evil.example'})[0], 403)
    expect('cross-site fetch denied', get(a.host, a.port, 'GET', '/lifeos-home/', {'Sec-Fetch-Site': 'cross-site'})[0], 403)
    expect('API without client label denied', get(a.host, a.port, 'GET', '/api/v1/platform/registry', {'Sec-Fetch-Site': 'same-origin'})[0], 403)
    expect('wrong client label denied', get(a.host, a.port, 'GET', '/api/v1/platform/registry', {**api, 'X-LifeOS-Client': 'wine-private'})[0], 403)
    expect('Wine resource not activated', get(a.host, a.port, 'GET', '/api/v1/wine-supplies',
                                              {'X-LifeOS-Client': 'wine-private', 'Sec-Fetch-Site': 'same-origin'})[0], lambda s: s in (403, 503))
    expect('Wine UI not served while disabled', get(a.host, a.port, 'GET', '/lifeos-wine-production/')[0], 403)
    expect('session write blocked by recovery gate', get(a.host, a.port, 'PUT', '/api/v1/cooking/session',
                                                         {'X-LifeOS-Client': 'cooking', 'Sec-Fetch-Site': 'same-origin', 'Origin': origin,
                                                          'If-Match': '"r0"', 'Content-Type': 'application/json'}, b'{}')[0], lambda s: s in (403, 503))
    expect('traversal denied', get(a.host, a.port, 'GET', '/lifeos-home/%2e%2e/%2e%2e/platform.json')[0], 404)
    expect('unknown path 404 after auth', get(a.host, a.port, 'GET', '/lifeos-health/')[0], 404)
    s, _, _ = get(a.host, a.port, 'GET', '/lifeos-home/', {'Tailscale-User-Login': 'spoof@example.test'})
    expect('client-supplied identity header replaced by Serve (owner still recognized)', s, 200)
    s, _, _ = get(a.host, a.port, 'GET', '/lifeos-home/', {'X-Forwarded-For': '100.64.0.250'})
    expect('client-supplied forwarding header cannot select another identity', s, lambda s: s in (200, 403))
    expect('direct socket connection (not tailscaled) denied', direct_socket('/lifeos-home/'), 403)
    expect('direct socket API denied', direct_socket('/api/v1/platform/health'), 403)
    out = {'passed': len(results) - len(failures), 'failed': failures, 'results': results,
           'scope': 'server-local ingress only; remote devices not tested here'}
    p = Path(a.evidence) / 'acceptance.json'
    p.write_text(json.dumps(out, indent=1)); os.chmod(p, 0o600)
    print(json.dumps({'passed': out['passed'], 'failed': failures}))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
