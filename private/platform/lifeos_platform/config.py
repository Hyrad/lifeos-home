"""Protected runtime configuration and per-resource authorization policy.

The configuration file lives outside Git and outside every release artifact. It is owner-only
(0600, owned by the service user, not a symlink) and is re-validated whenever it changes, so
revocation/expiry applies without a restart. Unknown keys are rejected everywhere.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit

from .identity import Failure, future, protected_file

# The first shared-origin trust group. Health, Game Shelf and administrative resources are
# deliberately absent: they cannot be configured on this origin at all.
RESOURCES = ('home', 'cooking', 'wine', 'cooking-sessions')
APPS = {
    # app id: (mount path, resource)
    'home': ('/lifeos-home/', 'home'),
    'cooking': ('/lifeos-cooking/', 'cooking'),
    'wine': ('/lifeos-wine-production/', 'wine'),
}
PAGE_ID = re.compile(r'[a-f0-9]{32}')
DEVICE_ID = re.compile(r'n[A-Za-z0-9]+')


@dataclass(frozen=True)
class ResourcePolicy:
    name: str
    devices: frozenset
    device_api: bool  # owner approved use of the Device API provider for this resource
    enabled: bool


@dataclass(frozen=True)
class Config:
    origin: str
    owner_login: str
    expires_at: str
    resources: dict
    apps: dict  # app id -> {'dist': Path, 'version': str}
    wine_source: object  # None or (page, parent)
    sessions_writes_enabled: bool
    data_dir: object  # None or Path

    @property
    def known_devices(self):
        return frozenset().union(*(r.devices for r in self.resources.values() if r.enabled))

    @property
    def device_api_devices(self):
        return frozenset().union(*(r.devices for r in self.resources.values() if r.enabled and r.device_api))


def _exact(d, keys, optional=()):
    if not isinstance(d, dict) or not set(keys) <= set(d) or not set(d) <= set(keys) | set(optional):
        raise ValueError('Unexpected configuration shape')


def parse(raw):
    c = json.loads(raw)
    _exact(c, {'schema', 'origin', 'owner_login', 'authorization_expires_at', 'resources', 'apps'},
           {'wine_source', 'cooking_sessions', 'data_dir'})
    if c['schema'] != 1:
        raise ValueError('Unsupported configuration schema')
    u = urlsplit(c['origin'])
    if (u.scheme != 'https' or not u.hostname or not u.hostname.endswith('.ts.net') or u.path or u.query
            or u.fragment or u.username or u.password):
        raise ValueError('Invalid private origin')
    owner = c['owner_login']
    if not isinstance(owner, str) or not re.fullmatch(r'[^\s@]+@[^\s@]+', owner) or owner != owner.lower():
        raise ValueError('Invalid owner')
    if not isinstance(c['authorization_expires_at'], str):
        raise ValueError('Invalid expiry')
    resources = {}
    if not isinstance(c['resources'], dict) or not set(c['resources']) <= set(RESOURCES):
        raise ValueError('Unknown resource')
    for name, r in c['resources'].items():
        _exact(r, {'devices', 'device_api', 'enabled'})
        if (not isinstance(r['devices'], list) or not r['devices']
                or any(not isinstance(v, str) or not DEVICE_ID.fullmatch(v) for v in r['devices'])):
            raise ValueError('Explicit device allowlist required')
        if type(r['device_api']) is not bool or type(r['enabled']) is not bool:
            raise ValueError('Invalid resource flags')
        resources[name] = ResourcePolicy(name, frozenset(r['devices']), r['device_api'], r['enabled'])
    apps = {}
    if not isinstance(c['apps'], dict) or not set(c['apps']) <= set(APPS):
        raise ValueError('Unknown app')
    for name, a in c['apps'].items():
        _exact(a, {'dist', 'version'})
        dist = Path(a['dist'])
        if not dist.is_absolute() or not isinstance(a['version'], str) or not re.fullmatch(r'[0-9A-Za-z.+-]{1,40}', a['version']):
            raise ValueError('Invalid app entry')
        if APPS[name][1] not in resources:
            raise ValueError('App without resource policy')
        apps[name] = {'dist': dist, 'version': a['version']}
    wine_source = None
    if 'wine_source' in c:
        _exact(c['wine_source'], {'source_page', 'source_parent'})
        page, parent = c['wine_source']['source_page'], c['wine_source']['source_parent']
        if not all(isinstance(v, str) and PAGE_ID.fullmatch(v) for v in (page, parent)):
            raise ValueError('Invalid source pin')
        wine_source = (page, parent)
    writes = False
    if 'cooking_sessions' in c:
        _exact(c['cooking_sessions'], {'writes_enabled'})
        if type(c['cooking_sessions']['writes_enabled']) is not bool:
            raise ValueError('Invalid sessions flag')
        writes = c['cooking_sessions']['writes_enabled']
    data_dir = None
    if 'data_dir' in c:
        data_dir = Path(c['data_dir'])
        if not data_dir.is_absolute():
            raise ValueError('Invalid data directory')
    if resources.get('wine') and resources['wine'].enabled and wine_source is None:
        raise ValueError('Wine requires a pinned source')
    if resources.get('cooking-sessions') and resources['cooking-sessions'].enabled and data_dir is None:
        raise ValueError('Sessions require a data directory')
    return Config(c['origin'], owner, c['authorization_expires_at'], resources, apps, wine_source, writes, data_dir)


def load(path):
    return parse(protected_file(path))


class ConfigSource:
    """Re-reads and re-validates the protected file when its identity/mtime changes.
    Any failure denies every request (503) until a valid file is restored."""

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.key = None
        self.value = load(self.path)  # startup must succeed
        self.key = self._key()

    def _key(self):
        s = os.lstat(self.path)
        return (s.st_ino, s.st_mtime_ns, s.st_size, s.st_mode, s.st_uid)

    def get(self):
        try:
            with self.lock:
                key = self._key()
                if key != self.key:
                    self.value, self.key = load(self.path), key
                return self.value
        except Exception:
            with self.lock:
                self.key = None
            raise Failure(503, 'configuration_unavailable') from None


def authorize_resource(identity, config, resource_name, device_api):
    """Resource-specific half of Wine's `authorize`: allowlist, expiry and machine evidence."""
    try:
        policy = config.resources.get(resource_name)
        if policy is None or not policy.enabled:
            raise ValueError('Resource not enabled')
        if not future(config.expires_at):
            raise ValueError('Policy expired')
        if identity.stable_id not in policy.devices:
            raise ValueError('Device not approved for resource')
        if identity.machine_authorized is not True:
            if not policy.device_api or device_api is None or device_api.verify(identity.node, identity.user) is not True:
                raise ValueError('No positive machine authorization')
        if not future(config.expires_at) or not future(identity.node.get('KeyExpiry')):
            raise ValueError('Expired during verification')
    except Exception:
        raise Failure(403, 'forbidden') from None
    return identity.stable_id
