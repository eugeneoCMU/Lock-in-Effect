"""
Regression tests for the loan-sample cache path.

1. A loan_sample.parquet cache hit in load_or_build_loan_sample must never
   touch the Freddie raw-file/download path.
2. ensure_raw_freddie_files must use the API-key auth entry point
   (common.google_drive.authenticate), not the removed service-account helper.

Run with: python3 -m pytest tests/test_loan_sample_cache.py
"""

import os
import sys
from pathlib import Path

import polars as pl

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

# hazard/config.py resolves the FRED key at import time; a dummy value keeps
# these tests hermetic when no .env is present.
os.environ.setdefault("FRED_API_KEY", "test-dummy-key")


def test_cache_hit_never_touches_download_path(tmp_path, monkeypatch):
    import loan_sample
    import prepare_freddie

    cached = tmp_path / "loan_sample.parquet"
    pl.DataFrame({"loan_id": ["A1"], "balance": [100_000.0]}).write_parquet(cached)
    monkeypatch.setattr(loan_sample, "LOAN_SAMPLE_PATH", cached)

    def _boom(*args, **kwargs):
        raise AssertionError("download path must not run on a cache hit")

    monkeypatch.setattr(prepare_freddie, "ensure_raw_files", _boom)

    df = loan_sample.load_or_build_loan_sample(force_rebuild=False)
    assert df["loan_id"].to_list() == ["A1"]


def test_ensure_raw_freddie_files_uses_api_key_auth(tmp_path, monkeypatch):
    from common import data_loader

    monkeypatch.setattr(data_loader, "authenticate", lambda: object())
    monkeypatch.setattr(data_loader, "_get_data_folder_id", lambda: "folder123")

    def _not_in_drive(service, folder_id, filename, cache_dir):
        raise FileNotFoundError(filename)

    monkeypatch.setattr(data_loader, "get_or_download", _not_in_drive)

    # Must not raise NameError (authenticate_service_account was removed in
    # 506ca2b); with no files in Drive it returns an empty pair list.
    pairs = data_loader.ensure_raw_freddie_files([2020], cache_dir=tmp_path)
    assert pairs == []
