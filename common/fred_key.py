"""
FRED API key resolution — no secrets in committed source.

Resolution order:
  1. FRED_API_KEY environment variable.
  2. A `FRED_API_KEY=...` line in a gitignored `.env` at the repo root.
  3. Raise, pointing the user at `.env.example`.

FRED keys are free (https://fred.stlouisfed.org/docs/api/api_key.html); this
indirection keeps the project's key out of version control without adding a
dependency on python-dotenv.
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
def get_fred_api_key() -> str:
    key = os.environ.get("FRED_API_KEY") or _read_dotenv("FRED_API_KEY")
    if not key:
        raise RuntimeError(
            "FRED_API_KEY not found. Set the FRED_API_KEY environment variable "
            "or copy .env.example to .env and fill it in "
            "(get a free key at https://fred.stlouisfed.org/docs/api/api_key.html)."
        )
    return key
