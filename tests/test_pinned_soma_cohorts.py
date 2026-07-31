"""The production SOMA cohort book is pinned, and the pin is the right book.

Cohort weights set the scheduled-amortization series, which enters both the
simulated roll-off and the empirical CPR back-out. That book used to be frozen
nowhere -- the manifest recorded only `n_cohorts`, `cohort_wac_pct` and a
reference cohort, and `fetch_soma_mbs_cohorts` always re-fetched the *latest*
book -- so the production scheduled series could not be rebuilt offline.

The NY Fed API serves historical as-of dates, so the book was recovered rather
than merely snapshotted. These tests pin the recovery: the committed book must
be internally consistent, and it must reproduce the frozen manifest's
scheduled-amortization series, which no other as-of does.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "abm"))
os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

import fed_mbs_extension_risk as fed  # noqa: E402

AS_OF = "2026-07-01"
PIN = json.loads((ROOT / "abm" / "data"
                  / f"soma_cohorts_{AS_OF}.json").read_text())
MANIFEST = json.loads((ROOT / "abm" / "data" / "runs"
                       / "run-2026-07-04-15yr-foldin"
                       / "manifest.json").read_text())


def test_pin_is_internally_consistent():
    rows = PIN["cohorts"]
    assert len(rows) == PIN["n_cohorts"] == 11
    assert abs(sum(c["weight"] for c in rows) - 1.0) < 1e-9
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(blob.encode()).hexdigest() == PIN["sha256_of_cohorts"]


def test_pin_validated_against_the_frozen_manifest():
    v = PIN["validation"]
    assert v["all_pass"]
    for name, c in v["checks"].items():
        assert c["pass"], name


def test_pin_reproduces_the_manifest_scheduled_series():
    """The decisive check, holdings-free: only the run's own cohort book
    reproduces the manifest's cohort-weighted scheduled-amortization mean."""
    n = MANIFEST["metrics"]["qt_window"]["n_months"]
    win = pd.date_range(fed.QT_START, periods=n, freq="ME")
    ser = pd.Series(0.0, index=win)
    for c in PIN["cohorts"]:
        ser = ser + c["weight"] * fed.scheduled_amortization_series(
            win, coupon=c["coupon"], origin=pd.Timestamp(c["origin_date"]),
            term=c["term_months"])
    got = float(ser.mean()) * 100.0
    want = MANIFEST["metrics"]["scheduled_amort_b"]["smm_mean_pct"]
    assert abs(got - want) < 1e-9, (got, want)
    assert abs(got * 12
               - MANIFEST["metrics"]["scheduled_amort_b"]["annualized_pct"]) < 1e-8


def test_a_wrong_as_of_would_not_reproduce_it():
    """Guards the claim that the parity check discriminates between books:
    perturbing the heaviest cohort's seasoning breaks it."""
    n = MANIFEST["metrics"]["qt_window"]["n_months"]
    win = pd.date_range(fed.QT_START, periods=n, freq="ME")
    rows = [dict(c) for c in PIN["cohorts"]]
    top = max(rows, key=lambda c: c["weight"])
    top["origin_date"] = str(
        (pd.Timestamp(top["origin_date"]) - pd.DateOffset(months=1)).date())
    ser = pd.Series(0.0, index=win)
    for c in rows:
        ser = ser + c["weight"] * fed.scheduled_amortization_series(
            win, coupon=c["coupon"], origin=pd.Timestamp(c["origin_date"]),
            term=c["term_months"])
    got = float(ser.mean()) * 100.0
    want = MANIFEST["metrics"]["scheduled_amort_b"]["smm_mean_pct"]
    assert abs(got - want) > 1e-9, "parity check is not discriminating"


def test_loader_returns_engine_ready_cohorts():
    cohorts = fed.load_pinned_cohorts(AS_OF)
    assert len(cohorts) == 11
    for c in cohorts:
        assert isinstance(c["origin_date"], pd.Timestamp)
        assert isinstance(c["months_elapsed"], int)
        assert c["term_months"] in (180, 360)
    assert abs(sum(c["weight"] for c in cohorts) - 1.0) < 1e-9


def test_loader_fails_loudly_for_an_unpinned_as_of():
    with pytest.raises(FileNotFoundError) as e:
        fed.load_pinned_cohorts("1999-01-01")
    assert "pin_soma_cohorts.py" in str(e.value)


def test_fetch_accepts_an_explicit_as_of():
    """Reproducibility hinges on the fetch not always meaning 'latest'."""
    import inspect
    assert "as_of" in inspect.signature(fed.fetch_soma_mbs_cohorts).parameters
