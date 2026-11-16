"""Kernel-bound Tailscale proxy identity and Device API evidence.

Provenance: lines 31-308 of private/server/wine_private.py at Hyrad/lifeos-wine-production
commit 32307eff1b58c30d03b8a73fa3e9bdae462a2e6e (v1.207-private.4), copied unmodified below the
marker. Only `authenticate` and `Identity` (after the second marker) are new platform code; they
are the resource-independent half of Wine's original `authorize`.
"""
from contextlib import ExitStack
from dataclasses import dataclass
import datetime as dt
from email.utils import parsedate_to_datetime
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import select
import socket
import stat
import struct
import threading
import time
from urllib.parse import quote, urlencode, urlsplit

# ---- verbatim from wine_private.py@32307ef (lines 31-308) ----
class Failure(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def future(value):
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00')) > dt.datetime.now(dt.timezone.utc)
    except (ValueError, TypeError, AttributeError):
        return False


def protected_file(path):
    p = Path(path)
    s = p.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
        raise ValueError('Unsafe protected file')
    return p.read_text().strip()


def load_policy(path, allow_expired=False):
    p = json.loads(protected_file(path))
    required = {'origin', 'owner_login', 'device_ids', 'source_page', 'source_parent', 'authorization_expires_at'}
    if set(p) != required:
        raise ValueError('Incomplete policy')
    u = urlsplit(p['origin'])
    if u.scheme != 'https' or not u.hostname or not u.hostname.endswith('.ts.net') or u.path or u.query or u.fragment or u.username or u.password:
        raise ValueError('Invalid private origin')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+', p['owner_login']) or p['owner_login'] != p['owner_login'].lower():
        raise ValueError('Invalid owner')
    if not isinstance(p['device_ids'], list) or not p['device_ids'] or any(not re.fullmatch(r'n[A-Za-z0-9]+', v) for v in p['device_ids']):
        raise ValueError('Explicit device allowlist required')
    for k in ('source_page', 'source_parent'):
        if not re.fullmatch(r'[a-f0-9]{32}', p[k]):
            raise ValueError('Invalid source pin')
    if not allow_expired and not future(p['authorization_expires_at']):
        raise ValueError('Authorization expired')
    return p


def visible_root_id(kind):
    """Host root may be unmapped in systemd's per-user filesystem sandbox."""
    rows = Path('/proc/self/' + kind + '_map').read_text().splitlines()
    if not rows or len(rows) > 340:
        raise ValueError('Missing namespace evidence')
    for row in rows:
        inside, outside, length = map(int, row.split())
        if inside < 0 or outside < 0 or length <= 0:
            raise ValueError('Invalid namespace evidence')
        if outside == 0:
            return inside
    return int(Path('/proc/sys/kernel/overflow' + kind).read_text())


def pinned_localapi_socket():
    """Walk a fixed root-controlled path without symlinks, then dial its inode."""
    sock = None
    try:
        root_uid = visible_root_id('uid')
        flags = os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC
        with ExitStack() as files:
            fd = os.open('/', flags | os.O_DIRECTORY)
            files.callback(os.close, fd)
            for component in (None, 'run', 'tailscale'):
                if component is not None:
                    fd = os.open(component, flags | os.O_DIRECTORY, dir_fd=fd)
                    files.callback(os.close, fd)
                meta = os.fstat(fd)
                if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != root_uid or meta.st_mode & 0o022:
                    raise ValueError('Untrusted LocalAPI directory')
            fd = os.open('tailscaled.sock', flags, dir_fd=fd)
            files.callback(os.close, fd)
            meta = os.fstat(fd)
            if not stat.S_ISSOCK(meta.st_mode) or meta.st_uid != root_uid:
                raise ValueError('Untrusted LocalAPI socket')
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect('/proc/self/fd/' + str(fd))
        return sock
    except Exception:
        if sock is not None:
            sock.close()
        raise Failure(403, 'forbidden') from None


@dataclass(frozen=True)
class KernelPeer:
    credentials: tuple
    pidfd: int

    def check_live(self):
        pid, uid, gid = self.credentials
        if pid <= 0 or uid < 0 or gid < 0:
            raise ValueError('Invalid peer credentials')
        # A numeric PID alone can be reused. This handle comes from the socket,
        # not pidfd_open(PID), and remains tied to its original peer process.
        info = Path('/proc/self/fdinfo/' + str(self.pidfd)).read_text()
        lines = [line for line in info.splitlines() if line.startswith('Pid:')]
        if len(lines) != 1 or int(lines[0].split(':', 1)[1]) != pid:
            raise ValueError('Missing peer process evidence')
        poll = select.poll()
        poll.register(self.pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
        if poll.poll(0):
            raise ValueError('Peer process exited')


def kernel_peer(sock, resources):
    raw = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i'))
    credentials = struct.unpack('3i', raw)
    # Linux UAPI SO_PEERPIDFD=77; older Python builds do not name it. Unsupported
    # kernels fail closed. Never fall back to UID, comm, or a numeric PID lookup.
    fd = sock.getsockopt(socket.SOL_SOCKET, getattr(socket, 'SO_PEERPIDFD', 77))
    resources.callback(os.close, fd)
    os.set_inheritable(fd, False)
    peer = KernelPeer(credentials, fd)
    peer.check_live()
    return peer


class VerifiedProxy:
    """Per-request proof bound to the daemon on the protected LocalAPI inode."""
    def __init__(self, incoming):
        self.incoming_socket = incoming
        self.resources = ExitStack()
        self.incoming = self.daemon = self.conn = None
        self.closed = True

    def __enter__(self):
        try:
            self.closed = False
            self.incoming = kernel_peer(self.incoming_socket, self.resources)
            self.conn = http.client.HTTPConnection('local-tailscaled.sock', timeout=1)
            self.resources.callback(self.conn.close)
            self.conn.auto_open = 0  # Never reconnect to an unverified endpoint.
            self.conn.sock = pinned_localapi_socket()
            self.daemon = kernel_peer(self.conn.sock, self.resources)
            self.check_live()
            return self
        except Exception:
            self.closed = True
            self.resources.close()
            raise Failure(403, 'forbidden') from None

    def __exit__(self, *args):
        self.closed = True
        self.resources.close()

    def check_live(self):
        try:
            if self.closed:
                raise ValueError('Closed proxy proof')
            self.incoming.check_live()
            self.daemon.check_live()
            if self.incoming.credentials != self.daemon.credentials:
                raise ValueError('Proxy process mismatch')
        except Exception:
            raise Failure(403, 'forbidden') from None

    def whois(self, address):
        try:
            self.check_live()
            self.conn.request('GET', '/localapi/v0/whois?addr=' + quote(address, safe=''), headers={'Host': 'local-tailscaled.sock'})
            r = self.conn.getresponse()
            raw = r.read(131073)
            if r.status != 200 or len(raw) > 131072:
                raise ValueError('Whois unavailable')
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError('Invalid whois')
            self.check_live()
            return result
        except Exception:
            raise Failure(403, 'forbidden') from None


class DeviceAuthorization:
    """Fixed-host read-only status; credentials and renewable tokens stay in memory."""
    scope = 'devices:core:read'

    def __init__(self, client_id, secret, device_ids, transport=None):
        self.client_id, self.secret = client_id, secret
        self.device_ids = frozenset(device_ids)
        self.transport = transport
        self.token, self.token_until = None, 0
        self.token_lock = threading.Lock()

    def request(self, method, path, headers, body=None):
        # Only these two operations are possible; no device writes/list queries.
        if not ((method == 'POST' and path == '/api/v2/oauth/token') or
                (method == 'GET' and path.startswith('/api/v2/device/') and path.removeprefix('/api/v2/device/') in self.device_ids)):
            raise ValueError('Operation outside authorization boundary')
        conn = None
        try:
            if self.transport:
                status, response_headers, raw = self.transport(method, path, headers, body)
            else:
                deadline = time.monotonic() + 8
                conn = http.client.HTTPSConnection('api.tailscale.com', timeout=4)
                conn.request(method, path, body=body, headers=headers)
                response = conn.getresponse()
                status, response_headers = response.status, dict(response.getheaders())
                chunks, size = [], 0
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError()
                    if conn.sock is not None:
                        conn.sock.settimeout(min(4, remaining))
                    chunk = response.read1(min(65536, 131073 - size))
                    if not chunk:
                        break
                    chunks.append(chunk); size += len(chunk)
                    if size > 131072:
                        raise ValueError('Response limit')
                raw = b''.join(chunks)
            h = {k.lower(): v for k, v in response_headers.items()}
            date = parsedate_to_datetime(h.get('date', ''))
            if date.tzinfo is None or abs((dt.datetime.now(dt.timezone.utc) - date).total_seconds()) > 60 or int(h.get('age', '0')) != 0:
                raise ValueError('Stale response')
            if status != 200 or len(raw) > 131072:
                if status == 401:
                    self.token, self.token_until = None, 0
                raise ValueError('Authorization unavailable')
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('Malformed authorization')
            return data
        except Exception:
            raise Failure(503, 'device_authorization_unavailable') from None
        finally:
            if conn is not None:
                conn.close()

    def access_token(self):
        if not self.token_lock.acquire(timeout=4):
            raise Failure(503, 'device_authorization_unavailable')
        try:
            if self.token and time.monotonic() < self.token_until:
                return self.token
            self.token, self.token_until = None, 0
            body = urlencode({'grant_type': 'client_credentials', 'client_id': self.client_id,
                              'client_secret': self.secret, 'scope': self.scope})
            data = self.request('POST', '/api/v2/oauth/token', {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}, body)
            token, ttl = data.get('access_token'), data.get('expires_in')
            if data.get('token_type', '').lower() != 'bearer' or set(data.get('scope', '').split()) != {self.scope} or type(ttl) is not int or not 60 < ttl <= 3600:
                raise Failure(503, 'device_authorization_unavailable')
            if not isinstance(token, str) or not token.startswith('tskey-') or not 20 <= len(token) <= 4096 or not token.isascii() or any(c.isspace() for c in token):
                raise Failure(503, 'device_authorization_unavailable')
            self.token, self.token_until = token, time.monotonic() + ttl - 60
            return token
        finally:
            self.token_lock.release()

    def verify(self, node, user):
        try:
            stable = node['StableID']
            if stable not in self.device_ids:
                return False
            data = self.request('GET', '/api/v2/device/' + stable,
                                {'Authorization': 'Bearer ' + self.access_token(), 'Accept': 'application/json', 'Cache-Control': 'no-cache'})
            if data.get('authorized') is not True or data.get('nodeId') != stable or data.get('user', '').lower() != user['LoginName'].lower():
                return False
            if not isinstance(data.get('tags', []), list) or data.get('tags') or not isinstance(node.get('Key'), str) or not node['Key'] or data.get('nodeKey') != node['Key']:
                return False
            expected = [str(ipaddress.ip_interface(a).ip) for a in node['Addresses']]
            actual = [str(ipaddress.ip_address(a)) for a in data['addresses']]
            if len(actual) != len(set(actual)) or sorted(actual) != sorted(expected):
                return False
            expiry = dt.datetime.fromisoformat(data['expires'].replace('Z', '+00:00'))
            local_expiry = dt.datetime.fromisoformat(node['KeyExpiry'].replace('Z', '+00:00'))
            return expiry == local_expiry and future(data['expires']) and future(node['KeyExpiry'])
        except Exception:
            return False
# ---- end verbatim block ----


# ---- new platform code ----
CRITICAL_HEADERS = ('host', 'tailscale-user-login', 'x-forwarded-for', 'x-forwarded-host',
                    'x-forwarded-proto', 'origin', 'sec-fetch-site', 'x-lifeos-client')
STABLE_ID = re.compile(r'n[A-Za-z0-9]+')


@dataclass(frozen=True)
class Identity:
    """Owner identity proven for one request. `machine_authorized` is True (explicit LocalAPI
    evidence) or None (field omitted; a resource may then require fresh Device API evidence)."""
    login: str
    node: dict
    user: dict
    machine_authorized: object

    @property
    def stable_id(self):
        return self.node['StableID']


def authenticate(headers, origin, owner_login, known_devices, whois, api_client=None, write=False):
    """Resource-independent half of Wine's `authorize` (same order and same failure codes).

    known_devices: union of all resource allowlists; anything else is denied before any
    resource-specific step (so unknown devices never trigger a Device API call).
    api_client: when set, the request must carry exactly this X-LifeOS-Client value and a
    same-origin fetch context (Wine's API rule, generalized to every platform API).
    write: state-changing requests additionally require an exact Origin header.
    """
    if any(len(headers.get_all(k) or []) > 1 for k in CRITICAL_HEADERS):
        raise Failure(403, 'forbidden')
    h = {k.lower(): v for k, v in headers.items()}
    login = h.get('tailscale-user-login', '')
    if not login:
        raise Failure(401, 'authentication_required')
    if any(c.isspace() for c in login) or not login.isascii() or len(login) > 254 or login.lower() != owner_login:
        raise Failure(403, 'forbidden')
    if any('funnel' in k for k in h):
        raise Failure(403, 'forbidden')
    host = urlsplit(origin).netloc
    if h.get('host') != 'localhost' or h.get('x-forwarded-host') != host or h.get('x-forwarded-proto') != 'https':
        raise Failure(403, 'forbidden')
    if h.get('origin') not in (None, origin) or h.get('sec-fetch-site') not in (None, 'none', 'same-origin'):
        raise Failure(403, 'forbidden')
    if write and h.get('origin') != origin:
        raise Failure(403, 'forbidden')
    if api_client is not None and (h.get('x-lifeos-client') != api_client or h.get('sec-fetch-site') != 'same-origin'):
        raise Failure(403, 'forbidden')
    try:
        address = str(ipaddress.ip_address(h.get('x-forwarded-for', '')))
        w = whois(address)
        n, user = w['Node'], w['UserProfile']
        stable = n.get('StableID')
        if not isinstance(stable, str) or not STABLE_ID.fullmatch(stable) or stable not in known_devices:
            raise ValueError('Unknown node')
        if user.get('LoginName', '').lower() != login.lower() or n.get('Tags') or not future(n.get('KeyExpiry')):
            raise ValueError('Unauthorized node')
        if type(n.get('User')) is not int or n['User'] <= 0 or type(user.get('ID')) is not int or n['User'] != user['ID']:
            raise ValueError('Owner mismatch')
        addresses = [ipaddress.ip_network(a, strict=True) for a in n.get('Addresses', [])]
        if not any(a.prefixlen == a.max_prefixlen and ipaddress.ip_address(address) == a.network_address for a in addresses):
            raise ValueError('Address mismatch')
        if 'MachineAuthorized' in n:
            if n['MachineAuthorized'] is not True:
                raise ValueError('Explicitly unauthorized')
            machine = True
        else:
            machine = None
        if not future(n.get('KeyExpiry')):
            raise ValueError('Expired during verification')
    except Exception:
        raise Failure(403, 'forbidden') from None
    return Identity(login.lower(), n, user, machine)
