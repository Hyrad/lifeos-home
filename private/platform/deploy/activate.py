#!/usr/bin/python3
"""Provisional activation / rollback of ONLY the platform unit and its dedicated Serve handler.

  activate.py preflight --port 10002 --release DIR --evidence DIR
  activate.py activate  --port 10002 --release DIR --evidence DIR [--keep]
  activate.py rollback  --port 10002 --evidence DIR

Activation gates (all must pass, else nothing is changed or everything new is removed):
  * port absent from Serve config and from listeners; socket path unused; unit not installed
  * release hashes verify; runtime config validates (owner-only, explicit device policies)
  * after start: Serve config == baseline + exactly one new handler -> our socket
  * existing handler responses unchanged; acceptance probes (see `accept`) pass
Rollback removes the new port only after confirming it contains only our handler, then stops,
disables and removes only the platform unit, and verifies Serve equals the baseline again.
Without --keep, a successful acceptance run is still rolled back (evidence-only rehearsal).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

HOME = Path.home()
UNIT = 'lifeos-platform.service'
UNIT_DST = HOME / '.config/systemd/user' / UNIT
UNIT_SRC = Path(__file__).resolve().parent / UNIT
SOCK = Path(f'/run/user/{os.getuid()}/lifeos-platform/platform.sock')
ROOT = HOME / '.local/share/lifeos-platform'
CONFIG = HOME / '.config/lifeos-platform/platform.json'
STATE = HOME / '.local/state/lifeos-platform'


SUDO_SERVE = False  # set by --sudo-serve: Serve changes on hosts without a Tailscale operator user


def run(*args, check=True):
    return subprocess.run(args, capture_output=True, text=True, check=check, timeout=60)


def serve_change(*args):
    prefix = ('sudo', '-n') if SUDO_SERVE else ()
    return run(*prefix, 'tailscale', 'serve', *args)


def serve_json():
    raw = run('tailscale', 'serve', 'status', '--json').stdout
    return json.loads(raw or '{}'), hashlib.sha256(raw.encode()).hexdigest()


def host_of(cfg):
    return next(iter(cfg.get('Web', {})), ':').rsplit(':', 1)[0]


def without_port(cfg, port):
    cfg = json.loads(json.dumps(cfg))
    cfg.get('TCP', {}).pop(str(port), None)
    for k in [k for k in cfg.get('Web', {}) if k.endswith(f':{port}')]:
        cfg['Web'].pop(k)
    return cfg


def listening(port):
    return any(line.split()[3].endswith(f':{port}') for line in run('ss', '-ltnH').stdout.splitlines() if line.strip())


def record(evidence, name, value):
    Path(evidence).mkdir(parents=True, exist_ok=True, mode=0o700)
    p = Path(evidence) / name
    p.write_text(value if isinstance(value, str) else json.dumps(value, indent=1, sort_keys=True))
    os.chmod(p, 0o600)


def preflight(a):
    cfg, digest = serve_json()
    problems = []
    if Path(a.release).resolve().parent != (ROOT / 'releases').resolve():
        problems.append('release must be a staged directory under the platform releases root')
    if str(a.port) in cfg.get('TCP', {}) or any(k.endswith(f':{a.port}') for k in cfg.get('Web', {})):
        problems.append('port already configured in Serve')
    if listening(a.port):
        problems.append('port already listening')
    if SOCK.exists():
        problems.append('platform socket already exists')
    if UNIT_DST.exists():
        problems.append('platform unit already installed')
    if run(sys.executable, str(Path(__file__).parent / 'stage.py'), 'verify', '--release', a.release, check=False).returncode:
        problems.append('release verification failed')
    check = run('/usr/bin/python3', '-I', str(Path(a.release) / 'server/run.py'), 'check-config', '--config', str(CONFIG), check=False)
    if check.returncode:
        problems.append('runtime configuration invalid')
    record(a.evidence, 'serve-before.json', cfg)
    record(a.evidence, 'preflight.json', {'serve_sha256': digest, 'problems': problems, 'port': a.port,
                                          'release': Path(a.release).name, 'config_summary': json.loads(check.stdout or '{}')})
    return cfg, problems


def existing_routes(cfg, port):
    host = host_of(cfg)
    out = {}
    for hp, web in sorted(cfg.get('Web', {}).items()):
        if hp.endswith(f':{port}'):
            continue
        for path in sorted(web.get('Handlers', {})):
            url = f'https://{hp.replace(":443", "")}{path}'
            try:
                with urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=8) as r:
                    out[url.replace(host, 'HOST')] = [r.status, hashlib.sha256(r.read()).hexdigest()[:16]]
            except urllib.error.HTTPError as e:
                out[url.replace(host, 'HOST')] = [e.code, hashlib.sha256(e.read()).hexdigest()[:16]]
            except Exception as e:
                out[url.replace(host, 'HOST')] = ['error', type(e).__name__]
    return out


def install_and_start(a):
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(STATE, 0o700)
    current = ROOT / 'current'
    previous = os.readlink(current) if current.is_symlink() else None
    record(a.evidence, 'current-before.json', {'previous': previous})
    if current.is_symlink():
        current.unlink()
    current.symlink_to(Path('releases') / Path(a.release).name)
    UNIT_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(UNIT_SRC, UNIT_DST)
    run('systemctl', '--user', 'daemon-reload')
    run('systemctl', '--user', 'start', UNIT)
    for _ in range(50):
        if SOCK.exists():
            return
        time.sleep(0.1)
    raise RuntimeError('platform socket did not appear')


def add_handler(a, before):
    serve_change('--bg', f'--https={a.port}', f'unix:{SOCK}')
    after, _ = serve_json()
    if without_port(after, a.port) != before:
        raise RuntimeError('Serve configuration changed outside the new port')
    web = [v for k, v in after.get('Web', {}).items() if k.endswith(f':{a.port}')]
    if len(web) != 1 or web[0].get('Handlers') != {'/': {'Proxy': f'unix:{SOCK}'}}:
        raise RuntimeError('new handler is not exactly the platform socket')
    if after.get('AllowFunnel'):
        raise RuntimeError('Funnel enabled')
    return after


def rollback(a, before=None):
    steps = []
    cfg, _ = serve_json()
    web = {k: v for k, v in cfg.get('Web', {}).items() if k.endswith(f':{a.port}')}
    if web:
        if any(v.get('Handlers') != {'/': {'Proxy': f'unix:{SOCK}'}} for v in web.values()):
            raise SystemExit('ROLLBACK REFUSED: port contains a handler that is not the platform socket')
        serve_change(f'--https={a.port}', 'off')
        steps.append('serve handler removed')
    if UNIT_DST.exists():
        run('systemctl', '--user', 'stop', UNIT, check=False)
        run('systemctl', '--user', 'disable', UNIT, check=False)
        UNIT_DST.unlink()
        run('systemctl', '--user', 'daemon-reload')
        run('systemctl', '--user', 'reset-failed', UNIT, check=False)
        steps.append('unit stopped and removed')
    marker = Path(a.evidence) / 'current-before.json'
    if marker.exists():
        previous = json.loads(marker.read_text())['previous']
        current = ROOT / 'current'
        if current.is_symlink():
            current.unlink()
        if previous:
            current.symlink_to(previous)
        steps.append('current release link restored' if previous else 'current release link removed')
    final, digest = serve_json()
    baseline = before if before is not None else json.loads((Path(a.evidence) / 'serve-before.json').read_text())
    ok = final == baseline and not SOCK.exists()
    record(a.evidence, 'rollback.json', {'steps': steps, 'serve_equals_baseline': final == baseline,
                                         'serve_sha256': digest, 'socket_absent': not SOCK.exists()})
    if not ok:
        raise SystemExit('ROLLBACK INCOMPLETE: see rollback.json')
    return steps


def activate(a):
    before, problems = preflight(a)
    if problems:
        raise SystemExit('preflight failed: ' + '; '.join(problems))
    routes_before = existing_routes(before, a.port)
    record(a.evidence, 'routes-before.json', routes_before)
    try:
        install_and_start(a)
        after = add_handler(a, before)
        record(a.evidence, 'serve-after.json', after)
        time.sleep(1)
        result = run(sys.executable, str(Path(__file__).parent / 'accept.py'), '--port', str(a.port),
                     '--host', host_of(before), '--evidence', a.evidence, check=False)
        record(a.evidence, 'acceptance.log', result.stdout[-20000:] + result.stderr[-4000:])
        routes_after = existing_routes(before, a.port)
        record(a.evidence, 'routes-after.json', routes_after)
        if routes_after != routes_before:
            raise RuntimeError('existing routes changed')
        if result.returncode:
            raise RuntimeError('acceptance failed')
    except Exception as e:
        record(a.evidence, 'activation-failure.json', {'error': str(e)})
        steps = rollback(a, before)
        print(json.dumps({'result': 'ROLLED_BACK', 'reason': str(e), 'rollback': steps}))
        return 1
    if not a.keep:
        steps = rollback(a, before)
        print(json.dumps({'result': 'ACCEPTED_THEN_ROLLED_BACK', 'rollback': steps}))
        return 0
    print(json.dumps({'result': 'ACTIVE', 'port': a.port, 'release': Path(a.release).name}))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['preflight', 'activate', 'rollback'])
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--release')
    p.add_argument('--evidence', required=True)
    p.add_argument('--keep', action='store_true')
    p.add_argument('--sudo-serve', action='store_true', help='prefix only the two Serve changes with sudo -n (run `sudo -v` first)')
    a = p.parse_args()
    global SUDO_SERVE
    SUDO_SERVE = a.sudo_serve
    if a.cmd == 'preflight':
        _, problems = preflight(a)
        print(json.dumps({'problems': problems}))
        return 1 if problems else 0
    if a.cmd == 'rollback':
        print(json.dumps({'rollback': rollback(a)}))
        return 0
    return activate(a)


if __name__ == '__main__':
    sys.exit(main())
