#!/usr/bin/python3
"""Stage an immutable platform release: server code + pinned private app artifacts + hash manifest.

Usage:
  stage.py create --root DIR --home DIST --cooking DIST [--wine DIST] --provenance JSON
  stage.py verify --release DIR

Never includes the runtime configuration, credentials, data or backups. Does not install units,
open listeners or modify Tailscale Serve.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {'platform.json', 'notion-token', 'tailscale-oauth-id', 'tailscale-oauth-secret', '.env'}
FORBIDDEN_SUFFIXES = ('.sqlite3', '.gpg', '.key', '.pem', '.map')
FORBIDDEN_TEXT = ('ntn_', 'secret_', 'tskey-', 'BEGIN PGP PRIVATE', 'BEGIN PRIVATE KEY')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree(root):
    root = Path(root)
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def scan(root):
    for p in Path(root).rglob('*'):
        if p.is_symlink():
            raise SystemExit(f'symlink refused: {p.name}')
        if p.is_file():
            if p.name in FORBIDDEN_NAMES or p.suffix in FORBIDDEN_SUFFIXES:
                raise SystemExit(f'forbidden file in artifact: {p.name}')
            data = p.read_bytes()
            for marker in FORBIDDEN_TEXT:
                if marker.encode() in data:
                    raise SystemExit(f'credential-like text in artifact: {p.name}')


def freeze(root):
    for p in sorted(Path(root).rglob('*'), reverse=True):
        os.chmod(p, 0o500 if p.is_dir() else 0o400)
    os.chmod(root, 0o500)


def create(a):
    git = subprocess.run(['git', '-C', str(HERE), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(['git', '-C', str(HERE), 'status', '--porcelain', '--', '.'], capture_output=True, text=True, check=True).stdout
    if dirty and not a.allow_dirty:
        raise SystemExit('platform source has uncommitted changes; commit first')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')
    releases = Path(a.root) / 'releases'
    releases.mkdir(parents=True, exist_ok=True, mode=0o700)
    final = releases / f'{stamp}-{git[:12]}'
    work = releases / (final.name + '.partial')
    work.mkdir(mode=0o700)
    try:
        server = work / 'server'
        shutil.copytree(HERE / 'lifeos_platform', server / 'lifeos_platform', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(HERE / 'run.py', server / 'run.py')
        apps = {'home': a.home, 'cooking': a.cooking, 'wine': a.wine}
        for name, src in apps.items():
            if src:
                if not (Path(src) / 'index.html').is_file():
                    raise SystemExit(f'{name}: index.html missing')
                shutil.copytree(src, work / 'apps' / name, symlinks=True)
        scan(work)
        provenance = json.loads(Path(a.provenance).read_text()) if a.provenance else {}
        manifest = {'format': 1, 'created': stamp, 'platform_commit': git, 'platform_dirty': bool(dirty),
                    'platform_version': (HERE / 'lifeos_platform' / '__init__.py').read_text().split('"')[1],
                    'provenance': provenance, 'files': tree(work)}
        (work / 'manifest.json').write_text(json.dumps(manifest, indent=1, sort_keys=True))
        freeze(work)
        os.rename(work, final)
    except BaseException:
        if work.exists():
            for p in work.rglob('*'):
                os.chmod(p, 0o700 if p.is_dir() else 0o600)
            os.chmod(work, 0o700)
            shutil.rmtree(work)
        raise
    print(json.dumps({'release': final.name, 'manifest_sha256': sha(final / 'manifest.json'), 'files': len(manifest['files'])}))


def verify(a):
    release = Path(a.release)
    manifest = json.loads((release / 'manifest.json').read_text())
    actual = {k: v for k, v in tree(release).items() if k != 'manifest.json'}
    if actual != manifest['files']:
        missing = set(manifest['files']) ^ set(actual) or {k for k in actual if actual[k] != manifest['files'].get(k)}
        raise SystemExit(f'release verification FAILED: {len(missing)} file(s) differ')
    writable = [p for p in release.rglob('*') if p.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)]
    if writable or release.stat().st_mode & 0o222:
        raise SystemExit('release verification FAILED: writable files')
    print(json.dumps({'release': release.name, 'verified_files': len(actual), 'manifest_sha256': sha(release / 'manifest.json')}))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('create')
    c.add_argument('--root', required=True); c.add_argument('--home', required=True); c.add_argument('--cooking', required=True)
    c.add_argument('--wine'); c.add_argument('--provenance'); c.add_argument('--allow-dirty', action='store_true')
    v = sub.add_parser('verify'); v.add_argument('--release', required=True)
    a = p.parse_args()
    create(a) if a.cmd == 'create' else verify(a)


if __name__ == '__main__':
    sys.exit(main())
