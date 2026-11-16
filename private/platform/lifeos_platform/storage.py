"""Platform SQLite storage: explicit versioned migrations, transaction-safe writes, revision
conflicts. Only approved operational domains live here (currently: Cooking session resume).
Canonical recipes, shopping, tasks and other Notion-owned records are never stored.

Durability: rollback journal (DELETE) + synchronous=EXTRA, short explicit transactions, one
writer lock per process, finite busy timeout. No WAL (see PLATFORM-01 blueprint §3).
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import threading

from .identity import Failure

DB_NAME = 'platform.sqlite3'

# (version, description, statements). Additive only; never edit an applied migration.
MIGRATIONS = [
    (1, 'cooking session resume', [
        """CREATE TABLE cooking_session (
             slot TEXT PRIMARY KEY CHECK (slot = 'current'),
             revision INTEGER NOT NULL CHECK (revision > 0),
             body TEXT,  -- NULL = ended/expired tombstone; revision never restarts
             updated_at TEXT NOT NULL)""",
        """CREATE TABLE cooking_idempotency (
             key TEXT PRIMARY KEY,
             request_sha TEXT NOT NULL,
             status INTEGER NOT NULL,
             response TEXT NOT NULL,
             created_at TEXT NOT NULL)""",
    ]),
]
SUPPORTED_VERSION = MIGRATIONS[-1][0]
SESSION_TTL = dt.timedelta(hours=48)
IDEMPOTENCY_TTL = dt.timedelta(hours=24)


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _iso(t):
    return t.isoformat(timespec='seconds').replace('+00:00', 'Z')


def migration_checksum(version):
    _, desc, statements = next(m for m in MIGRATIONS if m[0] == version)
    return hashlib.sha256(json.dumps([desc, statements]).encode()).hexdigest()


def check_private_dir(path):
    s = os.lstat(path)
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
        raise ValueError('Unsafe data directory')


def connect(path):
    conn = sqlite3.connect(path, timeout=2.0, isolation_level=None, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=DELETE')
    conn.execute('PRAGMA synchronous=EXTRA')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA busy_timeout=2000')
    conn.execute('PRAGMA trusted_schema=OFF')
    return conn


def schema_version(conn):
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
    if not exists:
        return 0
    rows = conn.execute('SELECT version, checksum FROM schema_migrations ORDER BY version').fetchall()
    for i, (version, checksum) in enumerate(rows, start=1):
        if version != i or (version <= SUPPORTED_VERSION and checksum != migration_checksum(version)):
            raise ValueError('Migration history mismatch')
    return rows[-1][0] if rows else 0


def migrate(path, before_migrate=None):
    """Apply pending migrations atomically. Refuses newer-than-supported schemas (code rollback
    must never open an incompatible newer database). `before_migrate(path)` is called with the
    existing database before any change (e.g. a pre-migration snapshot); its failure aborts."""
    path = Path(path)
    fresh = not path.exists()
    old = os.umask(0o077)
    try:
        conn = connect(path)
    finally:
        os.umask(old)
    try:
        version = schema_version(conn)
        if version > SUPPORTED_VERSION:
            raise ValueError('Database schema is newer than this release')
        pending = [m for m in MIGRATIONS if m[0] > version]
        if pending and not fresh and before_migrate is not None:
            before_migrate(path)
        for number, description, statements in pending:
            conn.execute('BEGIN IMMEDIATE')
            try:
                conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, '
                             'description TEXT NOT NULL, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)')
                for sql in statements:
                    conn.execute(sql)
                conn.execute('INSERT INTO schema_migrations VALUES (?,?,?,?)',
                             (number, description, migration_checksum(number), _iso(_now())))
                conn.execute('COMMIT')
            except BaseException:
                conn.execute('ROLLBACK')
                raise
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Integrity check failed')
        return schema_version(conn)
    finally:
        conn.close()
        os.chmod(path, 0o600)


# ---- Cooking session domain ----
RECIPE_REF = re.compile(r'[a-z0-9][a-z0-9-]{0,79}')
ITEM_ID = re.compile(r'[A-Za-z0-9_-]{1,64}')
TIMER_ID = re.compile(r'[A-Za-z0-9-]{1,40}')
IDEMPOTENCY_KEY = re.compile(r'[A-Za-z0-9-]{8,64}')
SESSION_FIELDS = {'recipeRef', 'step', 'servings', 'completedIngredients', 'completedSteps', 'timers'}


def _ids(value):
    return (isinstance(value, list) and len(value) <= 300 and len(set(map(str, value))) == len(value)
            and all(isinstance(i, str) and ITEM_ID.fullmatch(i) for i in value))


def validate_session(body):
    """Typed, bounded session payload (matches lifeos-cooking's CookingSession, minus the recipe).
    Only a recipe *reference* is accepted: recipe content is never stored or edited here."""
    if not isinstance(body, dict) or set(body) != SESSION_FIELDS:
        raise Failure(422, 'invalid_session')
    ref, step, servings, timers = body['recipeRef'], body['step'], body['servings'], body['timers']
    ok = (isinstance(ref, str) and RECIPE_REF.fullmatch(ref)
          and type(step) is int and 0 <= step <= 500
          and type(servings) in (int, float) and 0.25 <= servings <= 100
          and _ids(body['completedIngredients']) and _ids(body['completedSteps'])
          and isinstance(timers, list) and len(timers) <= 20)
    if not ok:
        raise Failure(422, 'invalid_session')
    clean_timers = []
    for t in timers:
        if not isinstance(t, dict) or set(t) != {'id', 'deadline'} or not isinstance(t['id'], str) \
                or not TIMER_ID.fullmatch(t['id']) or type(t['deadline']) is not int \
                or not 0 < t['deadline'] < 32503680000000:
            raise Failure(422, 'invalid_session')
        clean_timers.append({'id': t['id'], 'deadline': t['deadline']})
    return {'recipeRef': ref, 'step': step, 'servings': servings,
            'completedIngredients': sorted(body['completedIngredients']),
            'completedSteps': sorted(body['completedSteps']), 'timers': clean_timers}


class CookingSessions:
    """Single 'current' cooking session with explicit revisions (If-Match) and idempotent retries.
    Never writes recipes, never marks a recipe as cooked, never touches Notion."""

    def __init__(self, path):
        if schema_version_at(path) != SUPPORTED_VERSION:
            raise ValueError('Database not migrated to supported schema')
        self.conn = connect(path)
        self.lock = threading.Lock()

    def close(self):
        self.conn.close()

    def _expire(self):
        """Write-path only: turn expired sessions into tombstones (revision kept) and drop old
        idempotency records. Never called on reads, so read-only mode never changes data."""
        cutoff = _iso(_now() - SESSION_TTL)
        self.conn.execute('UPDATE cooking_session SET body = NULL WHERE body IS NOT NULL AND updated_at < ?', (cutoff,))
        self.conn.execute('DELETE FROM cooking_idempotency WHERE created_at < ?', (_iso(_now() - IDEMPOTENCY_TTL),))

    def _row(self):
        """-> (revision, session or None). Expired sessions read as None without modification."""
        row = self.conn.execute('SELECT revision, body, updated_at FROM cooking_session WHERE slot = ?', ('current',)).fetchone()
        if row is None:
            return 0, None
        if row[1] is None or row[2] < _iso(_now() - SESSION_TTL):
            return row[0], None
        return row[0], {**json.loads(row[1]), 'revision': row[0], 'updatedAt': row[2]}

    def _current(self):
        return self._row()[1]

    def get(self):
        """-> (revision, session or None); a plain read transaction, no writes."""
        with self.lock:
            self.conn.execute('BEGIN')
            try:
                return self._row()
            finally:
                self.conn.execute('COMMIT')

    def write(self, expected_revision, body, idempotency_key=None):
        """expected_revision: 0 = create only if none exists; n = replace only revision n.
        body None = end the session. Returns (status, response dict)."""
        if type(expected_revision) is not int or expected_revision < 0:
            raise Failure(428, 'precondition_required')
        clean = None if body is None else validate_session(body)
        if idempotency_key is not None and not IDEMPOTENCY_KEY.fullmatch(idempotency_key):
            raise Failure(422, 'invalid_idempotency_key')
        request_sha = hashlib.sha256(json.dumps([expected_revision, clean], sort_keys=True).encode()).hexdigest()
        with self.lock:
            self.conn.execute('BEGIN IMMEDIATE')
            try:
                self._expire()
                if idempotency_key is not None:
                    prior = self.conn.execute('SELECT request_sha, status, response FROM cooking_idempotency WHERE key = ?',
                                              (idempotency_key,)).fetchone()
                    if prior is not None:
                        self.conn.execute('COMMIT')
                        if prior[0] != request_sha:
                            raise Failure(422, 'idempotency_key_reused')
                        return prior[1], json.loads(prior[2])
                current_revision, current = self._row()
                if current_revision != expected_revision:
                    status, response = 409, {'error': 'revision_conflict', 'revision': current_revision, 'session': current}
                elif clean is None:
                    revision = current_revision + 1 if current_revision else 0
                    if current_revision:
                        self.conn.execute('UPDATE cooking_session SET revision = ?, body = NULL, updated_at = ? WHERE slot = ?',
                                          (revision, _iso(_now()), 'current'))
                    status, response = 200, {'session': None, 'revision': revision}
                else:
                    revision, now = current_revision + 1, _iso(_now())
                    self.conn.execute('INSERT INTO cooking_session VALUES (?,?,?,?) ON CONFLICT(slot) DO UPDATE SET '
                                      'revision=excluded.revision, body=excluded.body, updated_at=excluded.updated_at',
                                      ('current', revision, json.dumps(clean, sort_keys=True), now))
                    status, response = 200, {'session': {**clean, 'revision': revision, 'updatedAt': now}, 'revision': revision}
                if idempotency_key is not None and status == 200:
                    self.conn.execute('INSERT INTO cooking_idempotency VALUES (?,?,?,?,?)',
                                      (idempotency_key, request_sha, status, json.dumps(response), _iso(_now())))
                self.conn.execute('COMMIT')
                return status, response
            except Failure:
                raise
            except BaseException:
                if self.conn.in_transaction:
                    self.conn.execute('ROLLBACK')
                raise


def schema_version_at(path):
    conn = sqlite3.connect(f'file:{Path(path)}?mode=ro', uri=True, timeout=2.0)
    try:
        return schema_version(conn)
    finally:
        conn.close()
