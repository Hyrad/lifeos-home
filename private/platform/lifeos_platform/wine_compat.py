"""Wine v1.207-private.4 contract facade over the shared platform engine.

Exposes the names Wine's original private test-suite exercises, so those suites run unchanged
against the extracted platform code (regression evidence that extraction preserved behavior).
`authorize` here = platform `authenticate` + `authorize_resource` for one Wine resource.
"""
import http  # noqa: F401  (tests patch http.client through this module)
import time  # noqa: F401

from .adapters.wine_supplies import API_PATH, NotionReader, clean, item_fields, rich_text  # noqa: F401
from .config import Config, ResourcePolicy, authorize_resource
from .identity import (DeviceAuthorization, Failure, KernelPeer, VerifiedProxy, authenticate,  # noqa: F401
                       future, kernel_peer, load_policy, pinned_localapi_socket, protected_file, visible_root_id)

APP_PATH = '/lifeos-wine-production/'


def authorize(headers, policy, method, path, whois, device_api=None):
    if not future(policy['authorization_expires_at']):
        raise Failure(403, 'forbidden')
    devices = frozenset(policy['device_ids'])
    identity = authenticate(headers, policy['origin'], policy['owner_login'], devices, whois,
                            api_client='wine-private' if path == API_PATH else None)
    config = Config(policy['origin'], policy['owner_login'], policy['authorization_expires_at'],
                    {'wine': ResourcePolicy('wine', devices, True, True)}, {}, None, False, None)
    authorize_resource(identity, config, 'wine', device_api)
    if method not in ('GET', 'HEAD'):
        raise Failure(405, 'method_not_allowed')
    return identity.stable_id
