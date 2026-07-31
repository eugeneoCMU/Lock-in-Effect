"""The matched-depth grid check must compare exposure sums relatively.

`exposure_upb` cells sum to ~7.4e13, where one float64 ULP is ~0.016 and the
summation order depends on parquet chunking and threading. The check used an
absolute 1e-3 bound, so it could only pass on the machine that wrote the
artifact: two of the forty cells came back 0.016 off and the whole gate went
red, on a repo where every other gate was green. A permanently-red gate is a
gate nobody reads, so the tolerance is the defect, not the data.

Recomputation of the cells themselves stays exact: CPR to three decimals and
cohort-month counts must match bit-for-bit.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

MD_DEPTHS = (0.0, -0.0025, -0.005, -0.0075, -0.01, -0.015, -0.02, -0.025)
MD_AGE = 12.0
MD_LEGS = {
    "OFF_pooled_2017_2019": (201701, 201912),
    "OFF_2018_rising_rate": (201801, 201812),
    "OFF_2019_falling_rate": (201901, 201912),
    "IN_in_window_calibration_202206_202312": (202206, 202312),
    "IN_in_window_full_qt_202206_202509": (202206, 202509),
}
MD = json.loads((ROOT / "hazard" / "data"
                 / "matched_depth_reconciliation_results.json").read_text())
B0 = json.loads((ROOT / "hazard" / "data"
                 / "b0_variance_decomposition.json").read_text())


def _grid():
    rate = {r["period"].replace("-", ""): float(r["mortgage30us_pct"])
            for r in B0["series"]}
    mp = pd.read_parquet(
        ROOT / "hazard" / "data" / "cohort_month_panel.parquet",
        columns=["coupon", "reporting_period", "exposure_upb",
                 "prepaid_upb", "mean_loan_age"])
    mp["_rp"] = mp["reporting_period"].astype(int)
    mp = mp[(mp.coupon > 0) & (mp.exposure_upb > 0)].copy()
    mp["_mkt"] = mp["_rp"].astype(str).map(rate)
    mp = mp[mp._mkt.notna()].copy()
    mp["_gap"] = mp.coupon - mp._mkt / 100.0
    out = {}
    for leg, (lo, hi) in MD_LEGS.items():
        for t in MD_DEPTHS:
            s = mp[(mp._rp >= lo) & (mp._rp <= hi) & (mp._gap <= t)
                   & (mp.mean_loan_age >= MD_AGE)]
            e = float(s.exposure_upb.sum())
            cpr = (None if e <= 0 else
                   round((1 - (1 - float(s.prepaid_upb.sum()) / e) ** 12) * 100, 3))
            out[(leg, t)] = {"cpr": cpr, "upb": e, "n": int(len(s))}
    return out


GRID = _grid()


def test_cpr_and_counts_reproduce_exactly():
    for (leg, t), got in GRID.items():
        want = MD["step2_matched_depth_grid"][leg]["depths"][f"{t:+.4f}"]
        assert got["cpr"] == want["cpr_pct"], (leg, t)
        assert got["n"] == want["n_cohort_months"], (leg, t)


def test_exposure_matches_under_the_relative_rule():
    for (leg, t), got in GRID.items():
        want = MD["step2_matched_depth_grid"][leg]["depths"][f"{t:+.4f}"]
        tol = max(1e-3, 1e-12 * abs(got["upb"]))
        assert abs(want["exposure_upb"] - got["upb"]) <= tol, (leg, t)


def test_the_old_absolute_rule_was_the_defect():
    """Documents why the tolerance changed: at these magnitudes 1e-3 is below
    one ULP, so the old rule was unsatisfiable off the authoring machine."""
    worst = max(
        abs(MD["step2_matched_depth_grid"][leg]["depths"][f"{t:+.4f}"]
            ["exposure_upb"] - got["upb"])
        for (leg, t), got in GRID.items())
    biggest = max(g["upb"] for g in GRID.values())
    ulp = 2.0 ** -52 * biggest
    assert worst < 4 * ulp, "drift should be at ULP scale, not a data change"
    assert 1e-12 * biggest > ulp, "relative bound must clear one ULP"


def test_gate_reports_the_grid_as_reproduced():
    import subprocess
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "liveness_gates.py")],
                         capture_output=True, text=True).stdout
    assert "grid-recomputed-from-panel=True" in out
