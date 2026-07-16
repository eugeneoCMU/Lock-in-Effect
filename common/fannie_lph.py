"""
Typed wrappers for the three Single-Family Loan Performance History (LPH)
Exchange API endpoints, per Fannie Mae's published OpenAPI spec
(SingleFamilyLphExchangeAPI, server https://api.fanniemae.com).

IMPORTANT — this API does not return loan records. Every endpoint returns
one or more signed (pre-authenticated) S3 URLs pointing at the actual data
file(s); the file layout itself (columns, delimiters, zero-balance codes)
is documented separately by Fannie Mae and is NOT part of this OpenAPI spec,
so it is not modeled here. download_signed_file() fetches the raw bytes;
parsing them is prepare_fannie.py's job once that layout is available.

Endpoints (all GET, bearer via common/fannie_auth.get_access_token):
  /v1/sf-loan-performance-data/years/{year}/quarters/{quarter}
      quarter in {"Q1","Q2","Q3","Q4","All"}; data starts 2000 Q1.
  /v1/sf-loan-performance-data/primary-dataset
      Signed URL for the full primary dataset, 2000 Q1 through recent.
  /v1/sf-loan-performance-data/harp-dataset
      Signed URL for the full HARP (Home Affordable Refinance Program) dataset.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Literal

from common.fannie_auth import fannie_get

Quarter = Literal["Q1", "Q2", "Q3", "Q4", "All"]


def get_lph_urls_for_quarter(year: int, quarter: Quarter = "All") -> list[dict]:
    """
    Signed URL(s) for LPH data in a given year/quarter.

    Returns a list of {"s3Uri": str, "year": int, "quarter": str} dicts
    (the API's LphDetailResponse.lphResponse array, unwrapped).
    """
    resp = fannie_get(f"sf-loan-performance-data/years/{year}/quarters/{quarter}")
    return resp.get("lphResponse", [])


def get_primary_dataset_url() -> dict:
    """Signed URL for the full primary LPH dataset (2000 Q1-recent)."""
    return fannie_get("sf-loan-performance-data/primary-dataset")


def get_harp_dataset_url() -> dict:
    """Signed URL for the full HARP LPH dataset."""
    return fannie_get("sf-loan-performance-data/harp-dataset")


def download_signed_file(s3_uri: str, dest_path: Path, timeout: int = 300) -> Path:
    """
    Stream a signed S3 URL to disk. No Fannie auth header on this request —
    the URL itself is pre-authenticated (self-authenticating query string),
    same as any S3 presigned-URL download.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(s3_uri)
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest_path, "wb") as f:
        while chunk := resp.read(1 << 20):
            f.write(chunk)
    return dest_path
