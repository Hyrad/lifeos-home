"""Synthetic fixtures only: no real identities, devices, origins, tokens or personal data."""
import contextlib
import copy
import http.client
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
from email.message import Message
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lifeos_platform import server as srv  # noqa: E402

FUTURE = '2099-01-01T00:00:00Z'
ORIGIN = 'https://platform.test.ts.net:10002'
OWNER = 'owner@example.test'
PAGE, PARENT = 'a' * 32, 'b' * 32


def base_config(folder):
    folder = Path(folder)
    cfg = {
        'schema': 1, 'origin': ORIGIN, 'owner_login': OWNER, 'authorization_expires_at': FUTURE,
        'resources': {
            'home': {'devices': ['nMac', 'nPad'], 'device_api': False, 'enabled': True},
            'cooking': {'devices': ['nMac', 'nPad'], 'device_api': False, 'enabled': True},
            'wine': {'devices': ['nMac'], 'device_api': False, 'enabled': True},
            'cooking-sessions': {'devices': ['nPad'], 'device_api': False, 'enabled': True},
        },
        'apps': {name: {'dist': str(folder / 'apps' / name), 'version': '0.0.1-test'} for name in ('home', 'cooking', 'wine')},
        'wine_source': {'source_page': PAGE, 'source_parent': PARENT},
        'cooking_sessions': {'writes_enabled': True},
        'data_dir': str(folder / 'data'),
    }
    for name in ('home', 'cooking', 'wine'):
        d = folder / 'apps' / name
        (d / 'assets').mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(f'<h1>{name} synthetic</h1>')
        (d / 'assets' / 'app.js').write_text(f'console.log("{name}")')
    (folder / 'data').mkdir(mode=0o700, exist_ok=True)
    (folder / 'secret.txt').write_text('PRIVATE-OUTSIDE-DIST')
    return cfg


def write_config(path, cfg):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(cfg))
    tmp.chmod(0o600)
    os.replace(tmp, path)


def whois_for(device, address='100.64.0.1', machine=True):
    node = {'StableID': device, 'User': 123, 'KeyExpiry': FUTURE, 'Tags': [],
            'Addresses': [address + ('/128' if ':' in address else '/32')], 'Key': 'nodekey:synthetic'}
    if machine is not None:
        node['MachineAuthorized'] = machine
    return {'UserProfile': {'LoginName': OWNER, 'ID': 123}, 'Node': node}


def headers(client=None, **updates):
    d = {'Host': 'localhost', 'Tailscale-User-Login': OWNER, 'X-Forwarded-Host': 'platform.test.ts.net:10002',
         'X-Forwarded-Proto': 'https', 'X-Forwarded-For': '100.64.0.1', 'Sec-Fetch-Site': 'same-origin'}
    if client:
        d['X-LifeOS-Client'] = client
    d.update(updates)
    return {k: v for k, v in d.items() if v is not None}


class Harness:
    """Real PlatformServer on a real Unix socket. Only the tailscaled proof is substituted."""

    def __init__(self, test, cfg_update=None, token='synthetic-not-a-token', device_api=None, writes_gate=True):
        self.test = test
        self.stack = contextlib.ExitStack()
        test.addCleanup(self.stack.close)
        self.folder = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.cfg = base_config(self.folder)
        if cfg_update:
            cfg_update(self.cfg)
        self.config_path = self.folder / 'platform.json'
        write_config(self.config_path, self.cfg)
        if writes_gate:
            from lifeos_platform import backup
            self.stack.enter_context(patch.object(backup, 'recovery_status', return_value=(True, {'restore_drill': 'ok'})))
        self.device = 'nPad'
        self.machine = True
        self.proxy_live = True
        trusted = self.stack.enter_context(patch.object(srv, 'VerifiedProxy'))
        proof = trusted.return_value.__enter__.return_value
        proof.whois.side_effect = lambda address: whois_for(self.device, address, self.machine)

        def live():
            if not self.proxy_live:
                raise srv.Failure(403, 'forbidden')
        proof.check_live.side_effect = live
        self.proof = proof
        self.server = srv.PlatformServer(str(self.folder / 'platform.sock'), self.config_path, token, device_api, 'test-release')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.stack.callback(self.thread.join)
        self.stack.callback(self.server.server_close)
        self.stack.callback(self.server.shutdown)

    def request(self, method, path, h=None, body=None):
        c = http.client.HTTPConnection('unix', timeout=5)
        c.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.sock.connect(self.server.server_address)
        data = body if body is None or isinstance(body, bytes) else json.dumps(body).encode()
        c.request(method, path, body=data, headers=h if h is not None else headers())
        r = c.getresponse()
        result = (r.status, {k.lower(): v for k, v in r.getheaders()}, r.read())
        c.close()
        return result

    def update(self, fn):
        fn(self.cfg)
        write_config(self.config_path, self.cfg)


def mutate(d, **kw):
    d = copy.deepcopy(d)
    d.update(kw)
    return d
