import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

import support  # noqa: F401  (sys.path)
from lifeos_platform import backup, storage
from lifeos_platform.identity import Failure

BODY = {'recipeRef': 'soupe', 'step': 1, 'servings': 2, 'completedIngredients': [], 'completedSteps': [], 'timers': []}


class Folder(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.dir = Path(t.name); os.chmod(self.dir, 0o700)
        self.db = self.dir / 'platform.sqlite3'


class MigrationTests(Folder):
    def test_fresh_migration_private_and_versioned(self):
        self.assertEqual(storage.migrate(self.db), storage.SUPPORTED_VERSION)
        self.assertEqual(self.db.stat().st_mode & 0o777, 0o600)
        self.assertEqual(storage.migrate(self.db), storage.SUPPORTED_VERSION)  # idempotent
        conn = sqlite3.connect(self.db)
        self.assertEqual(conn.execute('PRAGMA journal_mode').fetchone()[0], 'delete')
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {'schema_migrations', 'cooking_session', 'cooking_idempotency'})

    def test_newer_schema_refused_for_rollback_safety(self):
        storage.migrate(self.db)
        conn = sqlite3.connect(self.db)
        conn.execute("INSERT INTO schema_migrations VALUES (2, 'future', 'x', 'now')"); conn.commit(); conn.close()
        with self.assertRaises(ValueError):
            storage.migrate(self.db)
        with self.assertRaises(ValueError):
            storage.CookingSessions(self.db)

    def test_tampered_history_refused(self):
        storage.migrate(self.db)
        conn = sqlite3.connect(self.db)
        conn.execute("UPDATE schema_migrations SET checksum='tampered'"); conn.commit(); conn.close()
        with self.assertRaises(ValueError):
            storage.migrate(self.db)

    def test_failed_migration_rolls_back_atomically(self):
        bad = storage.MIGRATIONS + [(2, 'broken', ['CREATE TABLE ok_table (x)', 'THIS IS NOT SQL'])]
        storage.migrate(self.db)
        with patch.object(storage, 'MIGRATIONS', bad), patch.object(storage, 'SUPPORTED_VERSION', 2):
            with self.assertRaises(sqlite3.Error):
                storage.migrate(self.db)
        conn = sqlite3.connect(self.db)
        self.assertIsNone(conn.execute("SELECT 1 FROM sqlite_master WHERE name='ok_table'").fetchone())
        self.assertEqual(storage.schema_version(conn), 1)

    def test_premigration_hook_runs_for_existing_db_and_failure_aborts(self):
        storage.migrate(self.db)
        bad = storage.MIGRATIONS + [(2, 'add', ['CREATE TABLE extra (x)'])]
        with patch.object(storage, 'MIGRATIONS', bad), patch.object(storage, 'SUPPORTED_VERSION', 2):
            with self.assertRaises(RuntimeError):
                storage.migrate(self.db, before_migrate=lambda p: (_ for _ in ()).throw(RuntimeError('no backup')))
            self.assertEqual(storage.schema_version_at(self.db), 1)
            copies = []
            storage.migrate(self.db, before_migrate=lambda p: copies.append(backup.copy_for_premigration(p)))
            self.assertEqual(storage.schema_version_at(self.db), 2)
            self.assertEqual(storage.schema_version_at(copies[0]), 1)
            self.assertEqual(copies[0].stat().st_mode & 0o777, 0o600)

    def test_private_dir_check(self):
        storage.check_private_dir(self.dir)
        os.chmod(self.dir, 0o755)
        with self.assertRaises(ValueError):
            storage.check_private_dir(self.dir)


class SessionStoreTests(Folder):
    def setUp(self):
        super().setUp(); storage.migrate(self.db); self.s = storage.CookingSessions(self.db); self.addCleanup(self.s.close)

    def test_revision_conflicts_and_end(self):
        self.assertEqual(self.s.write(0, BODY)[0], 200)
        self.assertEqual(self.s.write(0, BODY)[0], 409)
        self.assertEqual(self.s.write(2, BODY)[0], 409)
        self.assertEqual(self.s.write(1, {**BODY, 'step': 2})[1]['session']['revision'], 2)
        self.assertEqual(self.s.write(2, None), (200, {'session': None, 'revision': 3}))
        self.assertEqual(self.s.get(), (3, None))

    def test_concurrent_writers_exactly_one_wins(self):
        self.s.write(0, BODY)
        others = [storage.CookingSessions(self.db) for _ in range(6)]
        results = []
        def go(store, i):
            results.append(store.write(1, {**BODY, 'step': i})[0])
        threads = [threading.Thread(target=go, args=(o, i)) for i, o in enumerate(others)]
        [t.start() for t in threads]; [t.join() for t in threads]; [o.close() for o in others]
        self.assertEqual(sorted(results), [200] + [409] * 5)
        self.assertEqual(self.s.get()[0], 2)

    def test_validation_rejects_recipe_content_and_bounds(self):
        for bad in [{**BODY, 'title': 'x'}, {**BODY, 'recipeRef': '../x'}, {**BODY, 'step': -1}, {**BODY, 'step': True},
                    {**BODY, 'servings': 0}, {**BODY, 'completedIngredients': ['i1', 'i1']}, {**BODY, 'completedSteps': [1]}, {**BODY, 'timers': [{'id': 'a', 'deadline': 'soon'}]},
                    {**BODY, 'timers': [{'id': 'a', 'deadline': 1}] * 21}, []]:
            with self.subTest(bad=bad), self.assertRaises(Failure):
                self.s.write(0, bad)
        self.assertEqual(self.s.get(), (0, None))

    def test_retention_purges_stale_session(self):
        self.s.write(0, BODY)
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=49)).isoformat(timespec='seconds').replace('+00:00', 'Z')
        self.s.conn.execute('UPDATE cooking_session SET updated_at=?', (old,))
        self.assertEqual(self.s.get(), (1, None))
        # Reads never modify data (read-only mode): the row is still physically present.
        self.assertIsNotNone(self.s.conn.execute('SELECT body FROM cooking_session').fetchone()[0])
        self.assertEqual(self.s.write(0, BODY)[0], 409)  # revisions never restart
        self.assertEqual(self.s.write(1, BODY)[1]['revision'], 2)

    def test_stale_client_cannot_overwrite_session_started_after_delete(self):
        self.s.write(0, BODY)                                    # tab A holds r1
        self.s.write(1, None)                                    # device B ends it -> r2 tombstone
        self.assertEqual(self.s.write(2, {**BODY, 'recipeRef': 'cake'})[0], 200)  # B starts cake -> r3
        self.assertEqual(self.s.write(1, {**BODY, 'step': 5})[0], 409)            # stale tab A
        self.assertEqual(self.s.get()[1]['recipeRef'], 'cake')


def make_key(home):
    os.chmod(home, 0o700)
    env = {'GNUPGHOME': str(home), 'PATH': '/usr/bin:/bin'}
    subprocess.run(['gpg', '--batch', '--passphrase', '', '--quick-gen-key', 'LifeOS fixture <fixture@example.test>',
                    'ed25519', 'cert', 'never'], env=env, check=True, capture_output=True)
    fpr = subprocess.run(['gpg', '--batch', '--with-colons', '--list-keys'], env=env, check=True, capture_output=True, text=True).stdout
    fpr = [l.split(':')[9] for l in fpr.splitlines() if l.startswith('fpr')][0]
    subprocess.run(['gpg', '--batch', '--passphrase', '', '--quick-add-key', fpr, 'cv25519', 'encr', 'never'], env=env, check=True, capture_output=True)
    pub = Path(home) / 'recipient.asc'
    pub.write_bytes(subprocess.run(['gpg', '--batch', '--armor', '--export', fpr], env=env, check=True, capture_output=True).stdout)
    return pub


class BackupRestoreTests(Folder):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory()
        cls.home = Path(cls.keys.name) / 'owner-gnupg'; cls.home.mkdir()
        cls.recipient = make_key(cls.home)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(['gpgconf', '--kill', 'all'], env={'GNUPGHOME': str(cls.home), 'PATH': '/usr/bin:/bin'})
        cls.keys.cleanup()

    def setUp(self):
        super().setUp()
        self.data = self.dir / 'data'; self.data.mkdir(mode=0o700)
        self.db = self.data / 'platform.sqlite3'
        storage.migrate(self.db)
        s = storage.CookingSessions(self.db); s.write(0, BODY); s.close()
        self.dest = self.dir / 'dest'; self.dest.mkdir(mode=0o700); (self.dest / backup.MARKER).write_text('fixture-destination')

    def backup(self, **kw):
        return backup.create_backup(self.db, self.dest, self.data, self.recipient, require_separate_device=False, **kw)

    def test_encrypted_backup_and_isolated_restore_roundtrip(self):
        r = self.backup()
        archive = self.dest / r['archive']
        self.assertNotIn(b'SQLite format', archive.read_bytes())
        self.assertNotIn(b'soupe', archive.read_bytes())
        self.assertEqual(archive.stat().st_mode & 0o777, 0o600)
        report = backup.restore(archive, self.dir / 'restored', self.home)
        self.assertEqual(report['schema_version'], storage.SUPPORTED_VERSION)
        self.assertTrue(report['session_present'])
        restored = storage.CookingSessions(self.dir / 'restored' / 'platform.sqlite3')
        self.assertEqual(restored.get()[1]['recipeRef'], 'soupe'); restored.close()

    def test_restore_without_owner_private_key_fails(self):
        r = self.backup()
        empty = self.dir / 'no-key'; empty.mkdir(mode=0o700)
        with self.assertRaises(subprocess.CalledProcessError):
            backup.restore(self.dest / r['archive'], self.dir / 'restored', empty)

    def test_missing_sidecar_refused_and_failed_encrypt_leaves_no_partial(self):
        r = self.backup()
        Path(str(self.dest / r['archive']) + '.json').unlink()
        with self.assertRaises(backup.BackupError):
            backup.restore(self.dest / r['archive'], self.dir / 'restored', self.home)
        bad = self.dir / 'not-a-key.asc'; bad.write_text('garbage')
        with self.assertRaises(subprocess.CalledProcessError):
            backup.create_backup(self.db, self.dest, self.data, bad, require_separate_device=False,
                                 now=dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc))
        self.assertEqual([p.name for p in self.dest.iterdir() if p.name.endswith('.partial')], [])

    def test_tampered_archive_detected(self):
        r = self.backup()
        a = self.dest / r['archive']; data = bytearray(a.read_bytes()); data[-5] ^= 1; a.write_bytes(bytes(data))
        with self.assertRaises(backup.BackupError):
            backup.restore(a, self.dir / 'restored', self.home)

    def test_destination_must_be_designated_private_and_separate(self):
        (self.dest / backup.MARKER).unlink()
        with self.assertRaises(backup.BackupError):
            self.backup()
        (self.dest / backup.MARKER).write_text('x'); os.chmod(self.dest, 0o755)
        with self.assertRaises(backup.BackupError):
            self.backup()
        os.chmod(self.dest, 0o700)
        with self.assertRaises(backup.BackupError):  # same filesystem as data
            backup.create_backup(self.db, self.dest, self.data, self.recipient)
        with self.assertRaises(backup.BackupError):
            backup.create_backup(self.db, self.dir / 'unmounted', self.data, self.recipient, require_separate_device=False)
        self.assertFalse((self.dir / 'unmounted').exists())

    def test_snapshot_consistent_while_writer_active(self):
        s = storage.CookingSessions(self.db)
        stop = threading.Event()
        def writer():
            rev = 1
            while not stop.is_set():
                if s.write(rev, {**BODY, 'step': rev % 400})[0] == 200:
                    rev += 1
        t = threading.Thread(target=writer); t.start()
        try:
            for _ in range(5):
                with tempfile.TemporaryDirectory() as tmp:
                    m = backup.snapshot(self.db, tmp)
                    self.assertEqual(m['files']['platform.sqlite3'], backup.sha256_file(Path(tmp) / 'platform.sqlite3'))
        finally:
            stop.set(); t.join(); s.close()

    def test_retention_14_daily_8_weekly(self):
        start = dt.datetime(2026, 1, 1, 3, tzinfo=dt.timezone.utc)
        for i in range(120):
            name = f'lifeos-platform-{(start + dt.timedelta(days=i)).strftime("%Y%m%dT%H%M%SZ")}.tar.gpg'
            (self.dest / name).write_bytes(b'x')
        (self.dest / 'unrelated.txt').write_text('keep')
        backup.prune(self.dest)
        kept = sorted(p.name for p in self.dest.iterdir() if backup.NAME.fullmatch(p.name))
        self.assertLessEqual(len(kept), 14 + 8); self.assertGreaterEqual(len(kept), 14)
        self.assertTrue((self.dest / 'unrelated.txt').exists())
        self.assertTrue(kept[-1].startswith('lifeos-platform-20260430'))

    def test_recovery_gate_requires_drill_and_recent_backup(self):
        self.assertEqual(backup.recovery_status(self.data)[0], False)
        r = self.backup(); backup.record_backup(self.data, r)
        self.assertEqual(backup.recovery_status(self.data)[0], False)  # backup alone is not proof
        with patch.object(backup, 'validate_destination', return_value='fixture-destination'):
            backup.drill(self.dest, self.data, self.home)
        ok, status = backup.recovery_status(self.data)
        self.assertTrue(ok); self.assertEqual(status['restore_drill'], 'ok')
        gate = json.loads((self.data / backup.GATE_FILE).read_text())
        gate['verified_at'] = '2020-01-01T00:00:00+00:00'; (self.data / backup.GATE_FILE).write_text(json.dumps(gate))
        self.assertEqual(backup.recovery_status(self.data)[1]['restore_drill'], 'stale')


if __name__ == '__main__':
    unittest.main()
