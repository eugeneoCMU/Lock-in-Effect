"""The equal-weighted cohort fallback must be opt-in and recorded.

`compute_metrics` used to catch ANY exception from the live SOMA cohort fetch
and silently substitute `cohorts_from_surface`, which is equal-weighted. Cohort
weights set the scheduled-amortization series, which enters both the simulated
roll-off and the empirical CPR back-out, so the substitution moves every figure
derived from them while printing one line to stdout.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "abm"))
os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

import fed_mbs_extension_risk as fed  # noqa: E402


@pytest.fixture
def broken_fetch(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("SOMA API unreachable")
    monkeypatch.setattr(fed, "fetch_soma_mbs_cohorts", _boom)


def _minimal_frame():
    """Only the columns `compute_metrics` touches before the cohort block."""
    idx = pd.date_range("2022-06-30", periods=3, freq="ME")
    return pd.DataFrame(
        {"MORTGAGE30US": [5.0, 5.1, 5.2],
         "ACTLISCOUUS": [600_000.0, 610_000.0, 620_000.0],
         "WSHOMCB": [2_700_000.0, 2_690_000.0, 2_680_000.0],
         "DSPIC96": [16_000.0, 16_050.0, 16_100.0],
         "UMCSENT": [58.0, 59.0, 60.0]},
        index=idx,
    )


def test_fallback_is_not_silent_by_default(broken_fetch):
    """A failed fetch must raise rather than substitute an equal-weight book."""
    surface = {(0.02, 360): None, (0.03, 360): None}
    with pytest.raises(RuntimeError) as excinfo:
        fed.compute_metrics(_minimal_frame(), surface=surface)
    msg = str(excinfo.value)
    assert "equal-weighted" in msg
    assert "allow_surface_cohort_fallback" in msg


def test_fallback_requires_explicit_opt_in():
    """The parameter exists and defaults to False."""
    import inspect
    sig = inspect.signature(fed.compute_metrics)
    p = sig.parameters["allow_surface_cohort_fallback"]
    assert p.default is False


def test_surface_fallback_is_equal_weighted():
    """The reason the silent path was dangerous, pinned as a fact."""
    surface = {(0.02, 360): None, (0.03, 360): None, (0.04, 360): None}
    cohorts = fed.cohorts_from_surface(surface)
    weights = {c["weight"] for c in cohorts}
    assert len(weights) == 1, "fallback is equal-weighted by construction"
    assert abs(sum(c["weight"] for c in cohorts) - 1.0) < 1e-12
