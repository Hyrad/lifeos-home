"""Operator CLI. Output is sanitized: no identities, tokens, paths of private sources or data."""
import argparse
import json
import sys
from pathlib import Path

from . import VERSION, backup, config, server, storage


def main(argv=None):
    p = argparse.ArgumentParser(prog='python3 -m lifeos_platform')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('serve'); s.add_argument('--config', required=True); s.add_argument('--socket', required=True); s.add_argument('--release')
    c = sub.add_parser('check-config'); c.add_argument('--config', required=True)
    m = sub.add_parser('migrate'); m.add_argument('--config', required=True)
    b = sub.add_parser('backup'); b.add_argument('--config', required=True); b.add_argument('--dest', required=True); b.add_argument('--recipient', required=True)
    d = sub.add_parser('drill'); d.add_argument('--config', required=True); d.add_argument('--dest', required=True); d.add_argument('--gnupghome', required=True)
    st = sub.add_parser('recovery-status'); st.add_argument('--config', required=True)
    sub.add_parser('version')
    a = p.parse_args(argv)
    if a.cmd == 'serve':
        return server.main(['--config', a.config, '--socket', a.socket] + (['--release', a.release] if a.release else []))
    if a.cmd == 'version':
        print(VERSION); return 0
    cfg = config.load(a.config)
    if a.cmd == 'check-config':
        print(json.dumps({'ok': True, 'resources': {k: {'enabled': v.enabled, 'devices': len(v.devices), 'device_api': v.device_api}
                                                   for k, v in cfg.resources.items()},
                          'apps': {k: {'index': (v['dist'] / 'index.html').is_file(), 'version': v['version']} for k, v in cfg.apps.items()},
                          'wine_source': cfg.wine_source is not None, 'sessions_writes_enabled': cfg.sessions_writes_enabled}))
        return 0
    if cfg.data_dir is None:
        print('no data_dir configured', file=sys.stderr); return 2
    storage.check_private_dir(cfg.data_dir)
    db = Path(cfg.data_dir) / storage.DB_NAME
    if a.cmd == 'migrate':
        print(json.dumps({'schema_version': storage.migrate(db, before_migrate=backup.copy_for_premigration)})); return 0
    if a.cmd == 'backup':
        r = backup.create_backup(db, a.dest, cfg.data_dir, a.recipient)
        backup.record_backup(cfg.data_dir, r)
        print(json.dumps({'archive': r['archive'], 'pruned': len(r['pruned'])})); return 0
    if a.cmd == 'drill':
        r = backup.drill(a.dest, cfg.data_dir, a.gnupghome)
        print(json.dumps({'restore_drill': 'ok', 'schema_version': r['schema_version']})); return 0
    if a.cmd == 'recovery-status':
        ok, status = backup.recovery_status(cfg.data_dir)
        print(json.dumps({'writes_allowed_by_recovery_gate': ok, **status})); return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
