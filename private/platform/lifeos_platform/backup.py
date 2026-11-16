"""Consistent, encrypted, off-device backups of approved platform state, plus isolated restore.

* Snapshot: SQLite online-backup API -> integrity_check -> SHA-256 manifest (never a raw copy
  of a live database file).
* Encryption: gpg public-key encryption to an owner-held recipient key. The host only ever holds
  the public key; decryption (restore/drill) needs the owner's separately custodied private key.
* Destination: must already exist, be owner-only, carry the designated marker file, and live on
  a different filesystem than the data directory. Missing media fails visibly; nothing is ever
  silently written to the internal disk instead.
* Retention: 14 daily + 8 weekly archives; pruning only after the new archive is verified.
* Recovery gate: real local writes are allowed only after a successful restore drill from the
  designated destination (<= 92 days old) and a recent successful backup (<= 48 hours).
"""
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import tarfile
import tempfile

from . import VERSION
from .storage import SUPPORTED_VERSION, CookingSessions, schema_version_at

MARKER = '.lifeos-platform-backup-target'
NAME = re.compile(r'lifeos-platform-(\d{8}T\d{6}Z)\.tar\.gpg')
GATE_FILE = 'recovery-gate.json'
STATUS_FILE = 'backup-status.json'
DRILL_MAX_AGE = dt.timedelta(days=92)
BACKUP_MAX_AGE = dt.timedelta(hours=48)


class BackupError(Exception):
    pass


def _now():
    return dt.datetime.now(dt.timezone.utc)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _write_private_json(path, value):
    tmp = Path(str(path) + '.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(value, f, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def validate_destination(dest, data_dir, require_separate_device=True):
    dest, data_dir = Path(dest), Path(data_dir)
    try:
        s = os.lstat(dest)
    except FileNotFoundError:
        raise BackupError('backup destination missing (media not mounted?)') from None
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
        raise BackupError('backup destination must be an owner-only directory')
    marker = dest / MARKER
    if not marker.is_file() or marker.is_symlink():
        raise BackupError('backup destination is not designated (marker missing)')
    if require_separate_device and s.st_dev == os.stat(data_dir).st_dev:
        raise BackupError('backup destination is on the same filesystem as the data')
    return marker.read_text().strip()[:64]


def snapshot(db_path, workdir):
    """Consistent copy via the SQLite backup API, verified before it is packaged."""
    out = Path(workdir) / 'platform.sqlite3'
    src = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True, timeout=5)
    dst = sqlite3.connect(out)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    check = sqlite3.connect(f'file:{out}?mode=ro', uri=True)
    try:
        if check.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise BackupError('snapshot integrity check failed')
    finally:
        check.close()
    manifest = {'format': 1, 'created': _now().isoformat(timespec='seconds'), 'platform_version': VERSION,
                'schema_version': schema_version_at(out), 'files': {'platform.sqlite3': sha256_file(out)}}
    (Path(workdir) / 'manifest.json').write_text(json.dumps(manifest, sort_keys=True))
    return manifest


def _gpg(args, gnupghome, **kw):
    env = {'PATH': '/usr/bin:/bin', 'GNUPGHOME': str(gnupghome), 'LC_ALL': 'C'}
    return subprocess.run(['gpg', '--batch', '--no-tty', '--quiet', *args], env=env, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, **kw)


def create_backup(db_path, dest, data_dir, recipient_file, require_separate_device=True, now=None):
    """Snapshot -> tar -> encrypt to recipient public key -> fsync -> sidecar hash -> prune."""
    validate_destination(dest, data_dir, require_separate_device)
    now = now or _now()
    name = f'lifeos-platform-{now.strftime("%Y%m%dT%H%M%SZ")}.tar.gpg'
    final = Path(dest) / name
    if final.exists():
        raise BackupError('archive already exists')
    with tempfile.TemporaryDirectory(prefix='lifeos-backup-') as tmp:
        os.chmod(tmp, 0o700)
        manifest = snapshot(db_path, tmp)
        archive = Path(tmp) / 'archive.tar'
        with tarfile.open(archive, 'w') as tar:
            for member in ('manifest.json', 'platform.sqlite3'):
                tar.add(Path(tmp) / member, arcname=member)
        home = Path(tmp) / 'gnupg'
        home.mkdir(mode=0o700)
        partial = Path(dest) / (name + '.partial')
        _gpg(['--trust-model', 'always', '--recipient-file', str(recipient_file), '--output', str(partial),
              '--encrypt', str(archive)], home)
        with open(partial, 'rb') as f:
            os.fsync(f.fileno())
        os.chmod(partial, 0o600)
        digest = sha256_file(partial)
        os.replace(partial, final)
        _write_private_json(Path(dest) / (name + '.json'),
                            {'archive_sha256': digest, 'schema_version': manifest['schema_version'],
                             'created': manifest['created'], 'platform_version': VERSION})
    if sha256_file(final) != digest:
        raise BackupError('archive changed after write')
    pruned = prune(dest, now)
    return {'archive': name, 'sha256': digest, 'pruned': pruned}


def prune(dest, now=None, daily=14, weekly=8):
    """Keep the newest archive of each of the last `daily` days and of the last `weekly` ISO weeks.
    Only files matching the archive name pattern are ever considered."""
    archives = sorted((NAME.fullmatch(p.name).group(1), p) for p in Path(dest).iterdir() if NAME.fullmatch(p.name))
    keep, days, weeks = set(), [], []
    for stamp_, p in reversed(archives):
        t = dt.datetime.strptime(stamp_, '%Y%m%dT%H%M%SZ')
        day, week = t.date(), t.isocalendar()[:2]
        if day not in days and len(days) < daily:
            days.append(day); keep.add(p)
        if week not in weeks and len(weeks) < weekly:
            weeks.append(week); keep.add(p)
    removed = []
    for _, p in archives:
        if p not in keep:
            p.unlink()
            sidecar = Path(str(p) + '.json')
            if sidecar.exists():
                sidecar.unlink()
            removed.append(p.name)
    return removed


def restore(archive, target, gnupghome):
    """Decrypt and verify into an isolated new directory; never touches the live database."""
    archive, target = Path(archive), Path(target)
    sidecar = Path(str(archive) + '.json')
    if sidecar.exists() and json.loads(sidecar.read_text())['archive_sha256'] != sha256_file(archive):
        raise BackupError('archive hash mismatch')
    target.mkdir(mode=0o700)
    plain = _gpg(['--decrypt', str(archive)], gnupghome).stdout
    with tarfile.open(fileobj=io.BytesIO(plain)) as tar:
        members = tar.getmembers()
        if sorted(m.name for m in members) != ['manifest.json', 'platform.sqlite3'] or not all(m.isreg() for m in members):
            raise BackupError('unexpected archive contents')
        for m in members:
            data = tar.extractfile(m).read()
            fd = os.open(target / m.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
    manifest = json.loads((target / 'manifest.json').read_text())
    db = target / 'platform.sqlite3'
    if manifest.get('format') != 1 or manifest['files']['platform.sqlite3'] != sha256_file(db):
        raise BackupError('restored file hash mismatch')
    conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    try:
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise BackupError('restored database integrity failure')
    finally:
        conn.close()
    version = schema_version_at(db)
    if version != manifest['schema_version'] or version > SUPPORTED_VERSION:
        raise BackupError('restored schema incompatible with this release')
    store = CookingSessions(db)  # application-level read through the real domain API
    try:
        store.conn.execute('PRAGMA query_only=ON')
        session = store._current()
    finally:
        store.close()
    return {'schema_version': version, 'session_present': session is not None, 'manifest': manifest}


def latest_archive(dest):
    names = sorted(p.name for p in Path(dest).iterdir() if NAME.fullmatch(p.name))
    if not names:
        raise BackupError('no archive at destination')
    return Path(dest) / names[-1]


def record_backup(data_dir, result):
    _write_private_json(Path(data_dir) / STATUS_FILE, {'last_success': _now().isoformat(timespec='seconds'),
                                                       'archive_sha256': result['sha256']})


def drill(dest, data_dir, gnupghome, record=True):
    """Quarterly restore drill from the designated destination into an isolated temp directory."""
    destination_id = validate_destination(dest, data_dir)
    archive = latest_archive(dest)
    with tempfile.TemporaryDirectory(prefix='lifeos-drill-') as tmp:
        report = restore(archive, Path(tmp) / 'restore', gnupghome)
    if record:
        _write_private_json(Path(data_dir) / GATE_FILE, {'verified_at': _now().isoformat(timespec='seconds'),
                                                         'archive_sha256': sha256_file(archive),
                                                         'destination': destination_id})
    return report


def recovery_status(data_dir):
    """Returns (writes_allowed: bool, sanitized status dict)."""
    out = {'restore_drill': 'missing', 'last_backup': 'missing'}
    ok = True
    for key, name, max_age, field in [('restore_drill', GATE_FILE, DRILL_MAX_AGE, 'verified_at'),
                                      ('last_backup', STATUS_FILE, BACKUP_MAX_AGE, 'last_success')]:
        try:
            p = Path(data_dir) / name
            s = os.lstat(p)
            if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
                raise ValueError('unsafe')
            age = _now() - dt.datetime.fromisoformat(json.loads(p.read_text())[field])
            out[key] = 'ok' if dt.timedelta(0) <= age <= max_age else 'stale'
            out[key + '_age_hours'] = round(age.total_seconds() / 3600, 1)
        except Exception:
            pass
        ok = ok and out[key] == 'ok'
    return ok, out


def copy_for_premigration(db_path):
    """Same-disk pre-migration safety copy (rollback aid only; NOT disaster recovery)."""
    target = Path(db_path).with_name(f'premigration-{_now().strftime("%Y%m%dT%H%M%SZ")}.sqlite3')
    src, dst = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True), sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close(); src.close()
    os.chmod(target, 0o600)
    return target


