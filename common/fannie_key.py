"""
Fannie Mae LPH Exchange API credential resolution — no secrets in committed source.

Resolution order (mirrors common/fred_key.py):
  1. FANNIE_CLIENT_ID / FANNIE_CLIENT_SECRET environment variables.
  2. Matching lines in a gitignored `.env` at the repo root.
  3. Raise, pointing the user at `.env.example`.

The client ID and secret are an OAuth2 client-credentials pair issued by
Fannie Mae's developer portal for the SingleFamilyLphExchangeAPI app; this
indirection keeps both out of version control without adding a dependency
on python-dotenv.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOTENV = _REPO_ROOT / ".env"


def _read_dotenv(key: str) -> str | None:
    if not _DOTENV.is_file():
        return None
    for raw in _DOTENV.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return None


@lru_cache(maxsize=1)
def get_fannie_credentials() -> tuple[str, str]:
    client_id = os.environ.get("FANNIE_CLIENT_ID") or _read_dotenv("FANNIE_CLIENT_ID")
    client_secret = os.environ.get("FANNIE_CLIENT_SECRET") or _read_dotenv("FANNIE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "FANNIE_CLIENT_ID / FANNIE_CLIENT_SECRET not found. Set both "
            "environment variables or copy .env.example to .env and fill "
            "them in from your Fannie Mae developer portal app registration "
            "(SingleFamilyLphExchangeAPI)."
        )
    return client_id, client_secret
