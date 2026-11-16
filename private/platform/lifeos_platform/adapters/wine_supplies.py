"""Wine Supplies source adapter: fixed, read-only projection of the canonical weekly Notion
shopping Task (only unchecked items under the single winemaking H2).

Provenance: lines 360-560 of private/server/wine_private.py at Hyrad/lifeos-wine-production
commit 32307eff1b58c30d03b8a73fa3e9bdae462a2e6e, copied unmodified below the marker. GET-only
to api.notion.com with a pinned API version, no redirects/proxies, bounded time/pages/blocks.
No local purchase ledger or cache is kept: each refresh reads Notion anew.
"""
import http.client
import json
import re
import socket
import threading
import time
from urllib.parse import urlencode

from ..identity import Failure, stamp

API_PATH = '/api/v1/wine-supplies'
NOTION_VERSION = '2026-03-11'


# ---- verbatim from wine_private.py@32307ef (lines 360-560) ----
def clean(text):
    if not isinstance(text, str) or len(text) > 8000:
        raise Failure(502, 'source_invalid')
    text = re.sub(r'https?://[^\s<>]+|www\.[^\s<>]+', '[link omitted]', text, flags=re.I)
    text = re.sub(r'\b[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\b|\b[a-f0-9]{32}\b|(?:ntn_|secret_|ghp_|github_pat_)[A-Za-z0-9_]+', '[reference omitted]', text, flags=re.I)
    text = re.sub(r'<[^>]*>', '', text)
    text = ''.join(c if c.isprintable() else ' ' for c in text)
    return re.sub(r'\s+', ' ', text).strip()


def rich_text(parts):
    if not isinstance(parts, list) or len(parts) > 200:
        raise Failure(502, 'source_invalid')
    out = []
    for p in parts:
        if not isinstance(p, dict):
            raise Failure(502, 'source_invalid')
        value = p.get('plain_text')
        if value is None and p.get('type') == 'text':
            value = (p.get('text') or {}).get('content')
        if not isinstance(value, str):
            raise Failure(502, 'source_invalid')
        out.append(value)
    return clean(''.join(out))


AMOUNT = re.compile(r'(?P<approx>(?:environ|approximately|approx\.?|about|~|≈)\s*)?(?P<qty>\d+(?:[.,]\d+)?(?:\s*[–-]\s*\d+(?:[.,]\d+)?)?)\s*(?P<unit>kg|kilogrammes?|g|grammes?|ml|millilitres?|l|litres?|bouteilles?|bottles?|paquets?|packs?|unités?|units?|sachets?)\b', re.I)


def item_fields(text):
    if not text:
        raise Failure(502, 'source_invalid')
    pieces = re.split(r'\s+[—–]\s+|:\s*', text, maxsplit=1)
    name = pieces[0].strip()
    rest = pieces[1] if len(pieces) > 1 else text
    amount = AMOUNT.search(rest)
    qty = ((amount['approx'] or '') + amount['qty']).strip() if amount else ''
    unit = amount['unit'] if amount else ''
    condition = bool(re.search(r'\b(?:conditionnel(?:le)?|conditional|if|si)\b', text, re.I))
    review = not amount or len(pieces) == 1 or bool(re.search(r'\b(?:à confirmer|a confirmer|to confirm)\b', text, re.I))
    return {'name': name[:240], 'quantity': qty, 'unit': unit, 'purpose': rest,
            'classification': 'conditional' if condition else 'review' if review else 'confirmed',
            'condition': rest if condition else ''}


class NotionReader:
    def __init__(self, token, page, parent, transport=None):
        self.token, self.page, self.parent = token, page, parent
        self.transport = transport
        self.lock = threading.Lock()
        self.last_request = 0.0

    def _get(self, path, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Failure(504, 'upstream_timeout')
        if self.transport:
            return self.transport(path)
        # HTTPSConnection avoids environment proxies and redirects; only this fixed host.
        wait = 0.36 - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(min(wait, remaining))
        self.last_request = time.monotonic()
        conn = http.client.HTTPSConnection('api.notion.com', timeout=min(4, max(0.1, deadline - time.monotonic())))
        try:
            conn.request('GET', '/v1/' + path, headers={'Authorization': 'Bearer ' + self.token, 'Notion-Version': NOTION_VERSION, 'Accept': 'application/json'})
            r = conn.getresponse()
            chunks, size = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise Failure(504, 'upstream_timeout')
                if conn.sock is not None:
                    conn.sock.settimeout(min(4, remaining))
                chunk = r.read1(min(65536, 524289 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > 524288:
                    raise Failure(502, 'source_limit')
            raw = b''.join(chunks)
            if r.status in (401, 403, 404):
                raise Failure(503, 'source_access_unavailable')
            if r.status == 429:
                raise Failure(503, 'upstream_busy')
            if r.status != 200:
                raise Failure(502, 'upstream_unavailable')
            if len(raw) > 524288:
                raise Failure(502, 'source_limit')
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise Failure(502, 'source_invalid')
            return result
        except (TimeoutError, socket.timeout):
            raise Failure(504, 'upstream_timeout') from None
        except Failure:
            raise
        except Exception:
            raise Failure(502, 'upstream_unavailable') from None
        finally:
            conn.close()

    def read(self):
        if not self.lock.acquire(blocking=False):
            raise Failure(429, 'refresh_busy')
        try:
            return self._read()
        finally:
            self.lock.release()

    def _read(self):
        deadline = time.monotonic() + 12
        page = self._get('pages/' + self.page, deadline)
        parent = page.get('parent') or {}
        parent_id = parent.get(parent.get('type', ''), '')
        if str(page.get('id', '')).replace('-', '') != self.page or str(parent_id).replace('-', '') != self.parent or page.get('archived') or page.get('in_trash'):
            raise Failure(502, 'source_boundary')
        budget = {'pages': 0, 'blocks': 0}

        def children(block_id, depth=0):
            if not isinstance(block_id, str) or not re.fullmatch(r'[a-f0-9-]{32,36}', block_id):
                raise Failure(502, 'source_invalid')
            if depth > 3:
                raise Failure(502, 'source_limit')
            cursor, seen = None, set()
            while True:
                budget['pages'] += 1
                if budget['pages'] > 16:
                    raise Failure(502, 'source_limit')
                query = urlencode({'page_size': 100, **({'start_cursor': cursor} if cursor else {})})
                data = self._get('blocks/' + block_id + '/children?' + query, deadline)
                if not isinstance(data.get('results'), list) or type(data.get('has_more')) is not bool:
                    raise Failure(502, 'source_invalid')
                for b in data['results']:
                    budget['blocks'] += 1
                    if budget['blocks'] > 1000 or not isinstance(b, dict) or not isinstance(b.get('type'), str):
                        raise Failure(502, 'source_limit')
                    yield b
                if not data['has_more']:
                    return
                cursor = data.get('next_cursor')
                if not isinstance(cursor, str) or not re.fullmatch(r'[a-f0-9-]{32,36}', cursor) or cursor in seen:
                    raise Failure(502, 'source_invalid')
                seen.add(cursor)

        items, inside, found, ended = [], False, 0, False

        def collect(b, depth=0):
            kind = b['type']
            payload = b.get(kind)
            if not isinstance(payload, dict):
                raise Failure(502, 'source_invalid')
            if b.get('archived') or b.get('in_trash'):
                return
            if kind == 'to_do':
                if type(payload.get('checked')) is not bool:
                    raise Failure(502, 'source_invalid')
                if payload['checked']:
                    return
                text = rich_text(payload.get('rich_text'))
                # Child prose is part of this item's restriction; child checkboxes are separate items.
                nested = list(children(b['id'], depth + 1)) if b.get('has_children') else []
                notes = []
                for child in nested:
                    if child.get('type') in ('paragraph', 'bulleted_list_item', 'numbered_list_item'):
                        if child.get('has_children'):
                            raise Failure(502, 'source_invalid')
                        notes.append(rich_text((child.get(child['type']) or {}).get('rich_text')))
                items.append(item_fields(clean(' '.join([text, *notes]))))
                for child in nested:
                    if child.get('type') == 'to_do':
                        collect(child, depth + 1)
            elif b.get('has_children'):
                if kind not in ('toggle', 'bulleted_list_item', 'numbered_list_item'):
                    raise Failure(502, 'source_invalid')
                for child in children(b['id'], depth + 1):
                    collect(child, depth + 1)
            if len(items) > 100:
                raise Failure(502, 'source_limit')

        for b in children(self.page):
            kind = b['type']
            if kind in ('heading_1', 'heading_2'):
                heading = rich_text((b.get(kind) or {}).get('rich_text'))
                target = kind == 'heading_2' and re.fullmatch(r'À acheter\s*[—–-]\s*Vinification(?:\s*\([^)]*\))?', heading, re.I)
                if target:
                    found += 1
                    if found > 1:
                        raise Failure(502, 'section_ambiguous')
                    inside = True
                elif inside:
                    inside, ended = False, True
                continue
            if inside and not ended:
                collect(b)
        if found != 1:
            raise Failure(502, 'section_missing')
        if time.monotonic() > deadline:
            raise Failure(504, 'upstream_timeout')
        return {'items': items, 'fetchedAt': stamp()}
# ---- end verbatim block ----
