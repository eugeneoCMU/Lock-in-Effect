"""
Tests for hazard/bootstrap_se.py — stratum-level block bootstrap for
Path A hazard coefficient standard errors.

Run with: python3 -m pytest tests/test_bootstrap_se.py
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

# hazard/config.py resolves the FRED key at import time; a dummy value keeps
# these tests hermetic when no .env is present.
os.environ.setdefault("FRED_API_KEY", "test-dummy-key")


def _toy_train(n_strata: int = 8, n_months: int = 30, seed: int
= 7) -> pd.DataFrame:
    """Cohort-month cells with a known positive rate-gap effect (0.004/bps)."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_strata):
        stratum_gap = rng.normal(150, 40)
        for m in range(n_months):
            gap = stratum_gap + rng.normal(0, 30)
            age = 12 + m + s
            burnout = float(rng.uniform(0, 0.5))
            friction = float(rng.normal(0.08, 0.004))
            exposure = float(rng.uniform(1e6, 5e6))
            hazard = np.exp(-4.5 + 0.004 * (gap - 150.0))
            rows.append({
                "stratum_id": f"s{s:02d}",
                "loan_age": float(age),
                "rate_gap_bps": float(gap),
                "burnout": burnout,
                "friction": friction,
                "exposure": exposure,
                "events": float(np.clip(hazard, 0, 1) * exposure),
            })
    return pd.DataFrame(rows)


def test_resample_strata_relabels_and_preserves_cluster_rows():
    from bootstrap_se import resample_strata

    train = _toy_train()
    rng = np.random.default_rng(0)
    boot = resample_strata(train, rng)

    # Same number of cluster draws as original strata
    n_orig = train["stratum_id"].n_unique() if hasattr(train["stratum_id"], "n_unique") else train["stratum_id"].nunique()
    assert boot["stratum_id"].nunique() == n_orig

    # Each relabeled cluster is a full copy of one source stratum
    src_sizes = train.groupby("stratum_id").size()
    for label, grp in boot.groupby("stratum_id"):
        src = grp["stratum_id_src"].iloc[0]
        assert len(grp) == src_sizes[src]

    # Deterministic under the same seed
    boot2 = resample_strata(train, np.random.default_rng(0))
    pd.testing.assert_frame_equal(
        boot.reset_index(drop=True), boot2.reset_index(drop=True)
    )


def test_rescale_to_production_units():
    from bootstrap_se import rescale_to_production_units

    betas = {"rate_gap_bps": 0.5, "burnout_orth": -0.2, "friction": -0.04,
             "gap_std": 200.0, "burn_std": 0.10, "fric_std": 0.008}
    prod = {"gap_std": 100.0, "burn_std": 0.05, "fric_std": 0.004}
    out = rescale_to_production_units(betas, prod)
    # beta per raw unit x production std
    assert np.isclose(out["rate_gap_bps"], 0.5 / 200.0 * 100.0)
    assert np.isclose(out["burnout_orth"], -0.2 / 0.10 * 0.05)
    assert np.isclose(out["friction"], -0.04 / 0.008 * 0.004)


def test_bootstrap_smoke_recovers_positive_rate_gap():
    from bootstrap_se import run_bootstrap

    train = _toy_train()
    result = run_bootstrap(train, n_reps=4, ridge_alpha=1e-4, seed=1)

    for name in ["rate_gap_bps", "burnout_orth", "friction"]:
        ci = result["ci_95"][name]
        assert ci["lo"] <= ci["hi"]
        assert np.isfinite(ci["lo"]) and np.isfinite(ci["hi"])
    assert result["n_reps"] == 4
    # Strong planted positive signal: every replication should be positive
    assert result["ci_95"]["rate_gap_bps"]["lo"] > 0
