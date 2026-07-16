"""
Fannie Mae developer-portal OAuth2 client-credentials flow.

Two-step pattern documented at the Fannie Mae developer portal for the
SingleFamilyLphExchangeAPI app: exchange FANNIE_CLIENT_ID/FANNIE_CLIENT_SECRET
(common/fannie_key.py) for a short-lived bearer token at the PingOne
authorization server, then call the API with that token in the
`x-public-access-token` header (per-portal convention; NOT the more common
`Authorization: Bearer`). Tokens expire after one hour (`expires_in: 3600`
in the token response) and are refreshed automatically with a safety margin.

Uses only urllib (no `requests` dependency), matching hazard/macro.py and
abm/fed_mbs_extension_risk.py's existing FRED/SOMA request style.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from common.fannie_key import get_fannie_credentials

# Fannie Mae's PingOne environment for this API family, per the developer
# portal's own "Create Access Token" instructions. This is a tenant/environment
# identifier, not a secret, and applies to every consumer of the API.
TOKEN_URL = "https://auth.pingone.com/4c2b23f9-52b1-4f8f-aa1f-1d477590770c/as/token"
API_BASE_URL = "https://api.fanniemae.com/v1"

_TOKEN_REFRESH_MARGIN_S = 60  # refresh this many seconds before actual expiry
_cached_token: Optional[str] = None
_cached_token_expiry: float = 0.0


def _fetch_access_token() -> tuple[str, float]:
    client_id, client_secret = get_fannie_credentials()
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        method="POST",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"Fannie Mae token request failed ({exc.code} {exc.reason}): {body}"
        ) from exc
    token = payload["access_token"]
    expires_in = float(payload.get("expires_in", 3600))
    return token, time.time() + expires_in


def get_access_token(force_refresh: bool = False) -> str:
    """Return a valid bearer token, fetching or refreshing one as needed."""
    global _cached_token, _cached_token_expiry
    now = time.time()
    if (
        force_refresh
        or _cached_token is None
        or now >= _cached_token_expiry - _TOKEN_REFRESH_MARGIN_S
    ):
        _cached_token, _cached_token_expiry = _fetch_access_token()
    return _cached_token


def fannie_get(path: str, params: Optional[dict[str, Any]] = None,
                timeout: int = 30) -> Any:
    """
    GET https://api.fanniemae.com/v1/{path} with the current access token.

    `path` is a resource path from the SingleFamilyLphExchangeAPI OpenAPI spec
    (see common/fannie_lph.py for the three concrete endpoints). Retries once
    on a 401 by forcing a token refresh, in case the cached token expired
    mid-session.
    """
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params)

    def _do_request(token: str):
        req = urllib.request.Request(
            f"{API_BASE_URL}/{path.lstrip('/')}{query}",
            headers={
                "Content-Type": "application/json",
                "x-public-access-token": token,
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())

    try:
        return _do_request(get_access_token())
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return _do_request(get_access_token(force_refresh=True))
        body = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"Fannie Mae API request failed ({exc.code} {exc.reason}): {body}"
        ) from exc
