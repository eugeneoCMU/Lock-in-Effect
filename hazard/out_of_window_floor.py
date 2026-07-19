"""
out_of_window_floor.py  —  Out-of-window involuntary-turnover floor anchor.

PRE-COMMITTED SPEC (fixed in this header before the run; ex-ante convention of
Section VII.I / Appendix A). Addresses the panel's R1-Obj2 / R3-Obj3 and the
Section VIII.A "no untouched evaluation months" limitation on the floor
dimension: the production 4% involuntary-turnover floor is calibrated IN-WINDOW
(2023-24 discount-cohort turnover). This run asks whether PRE-EPISODE, OUT-OF-
WINDOW data (2017-2019, before both the QT window and the 2020-21 refi wave)
independently corroborate ~4% CPR.

DATA
  - hazard/data/cohort_month_panel.parquet (committed; the Path A panel, which
    carries reporting months back to 2017-01 even though Path A trains 2021+).
  - MORTGAGE30US monthly mean via FRED (the paper's own macro pipeline).

DEFINITIONS (identical to the paper)
  - rate gap = coupon - market_rate (decimal), = rate_gap_us; NEGATIVE when the
    borrower is locked in / out-of-the-money / a discount cohort (coupon < mkt).
  - SMM(cohort-month) = prepaid_upb / exposure_upb.
  - Exposure-weighted CPR over a selection S:
        SMM_bar = sum_S prepaid_upb / sum_S exposure_upb ;  CPR = 1-(1-SMM_bar)^12.

SELECTION
  - Primary/headline (out-of-window): reporting 2017-01..2019-12, gap <= 0
    (out of the money), mean_loan_age >= 12 (past first-year origination noise),
    coupon > 0, exposure_upb > 0.
  - Robustness grid (all reported): gap thresholds {<=0, <=-0.0025, <=-0.005};
    age cuts {>=12, >=24}.
  - METHOD VALIDATION (in-window): the identical procedure on 2023-01..2024-12
    deeply-OTM discount cohort-months (gap <= -0.02) must reproduce ~4-5% CPR,
    else the method is not measuring what the paper's floor measures.

ACCEPTANCE GATE (pre-committed)
  Let F = out-of-window primary CPR (2017-2019, gap<=0, age>=12).
  - CORROBORATES         if F in [3.5%, 4.5%].
  - CONSISTENT (looser)  if F in [3.0%, 5.0%] but outside [3.5, 4.5].
  - DOES-NOT-CORROBORATE if F outside [3.0%, 5.0%]  -> concession framing:
        the floor stays disclosed as in-window-only; items 1/4 fully embrace
        "sign-and-box, not a magnitude".
  PRE-REGISTERED CAVEAT: 2017-2019 OTM cohorts are younger and less deeply
  discounted than 2023-24 (rates only rose to 4.87% in this episode), so a
  reading BELOW 4% is AMBIGUOUS (loan immaturity on the PSA ramp), not
  disconfirming; a reading NEAR or ABOVE 4% is corroborating.

DOWNSTREAM
  Item 2 changes the floor's PROVENANCE, not (necessarily) its value: if the
  out-of-window CPR is ~4%, the production floor stays 4% but gains an
  out-of-window justification. The Section VII.I box already reports the
  marginal at 3/3.5/4/4.5/5% floors, so no marginal re-run is needed unless
  the out-of-window number points away from 4%.
"""
from __future__ import annotations
import json
import sys
import numpy as np
import pandas as pd

PANEL = "hazard/data/cohort_month_panel.parquet"
OUT = "hazard/data/out_of_window_floor_results.json"


def cpr_of(sel: pd.DataFrame) -> tuple[float, float, int]:
    """Exposure-weighted annual CPR, total exposure, n cohort-months."""
    exp = sel["exposure_upb"].sum()
    if exp <= 0:
        return float("nan"), 0.0, 0
    smm = sel["prepaid_upb"].sum() / exp
    cpr = 1.0 - (1.0 - smm) ** 12
    return float(cpr), float(exp), int(len(sel))


def main() -> int:
    df = pd.read_parquet(PANEL)
    df = df[(df["coupon"] > 0) & (df["exposure_upb"] > 0)].copy()
    df["rp"] = df["reporting_period"].astype(int)
    df["ym"] = df["reporting_period"].astype(str)

    # --- market rate via the paper's macro source ---
    sys.path.insert(0, "hazard")
    import config
    from fredapi import Fred
    fred = Fred(api_key=config.FRED_API_KEY)
    rate = fred.get_series("MORTGAGE30US", observation_start="2016-12-01",
                           observation_end="2025-10-31").resample("ME").mean()
    rate_by_ym = {ix.strftime("%Y%m"): float(v) / 100.0 for ix, v in rate.items()}
    df["market_rate"] = df["ym"].map(rate_by_ym)
    df = df[df["market_rate"].notna()].copy()
    df["gap"] = df["coupon"] - df["market_rate"]  # rate_gap_us; <0 = locked in

    def window(lo: int, hi: int) -> pd.DataFrame:
        return df[(df["rp"] >= lo) & (df["rp"] <= hi)]

    oow = window(201701, 201912)   # out-of-window
    inw = window(202301, 202412)   # in-window validation (2023-24 discount)

    results: dict = {"spec": "out_of_window_floor pre-committed; gap<=0 OTM, "
                     "exposure-wtd CPR", "grids": {}}

    # ---- robustness grid, both windows ----
    for name, w in [("out_of_window_2017_2019", oow),
                    ("in_window_2023_2024", inw)]:
        grid = {}
        for gthr in (0.0, -0.0025, -0.005):
            for amin in (12, 24):
                sel = w[(w["gap"] <= gthr) & (w["mean_loan_age"] >= amin)]
                cpr, exp, n = cpr_of(sel)
                grid[f"gap<={gthr:+.4f}_age>={amin}"] = {
                    "cpr_pct": round(100 * cpr, 3) if cpr == cpr else None,
                    "exposure_upb": exp, "n_cohort_months": n}
        results["grids"][name] = grid

    # ---- deeply-OTM in-window validation (gap<=-0.02), matching "deeply OTM" ----
    for amin in (12, 24):
        sel = inw[(inw["gap"] <= -0.02) & (inw["mean_loan_age"] >= amin)]
        cpr, exp, n = cpr_of(sel)
        results.setdefault("in_window_deep_OTM_validation", {})[f"gap<=-0.02_age>={amin}"] = {
            "cpr_pct": round(100 * cpr, 3) if cpr == cpr else None,
            "exposure_upb": exp, "n_cohort_months": n}

    # ---- headline + gate ----
    F = results["grids"]["out_of_window_2017_2019"]["gap<=+0.0000_age>=12"]["cpr_pct"]
    if F is None:
        verdict = "NO_DATA"
    elif 3.5 <= F <= 4.5:
        verdict = "CORROBORATES"
    elif 3.0 <= F <= 5.0:
        verdict = "CONSISTENT_LOOSER"
    else:
        verdict = "DOES_NOT_CORROBORATE"
    results["headline_out_of_window_floor_cpr_pct"] = F
    results["gate_verdict"] = verdict
    results["production_floor_pct"] = 4.0

    with open(OUT, "w") as fh:
        json.dump(results, fh, indent=2)

    # ---- console report ----
    print("=" * 68)
    print("OUT-OF-WINDOW INVOLUNTARY-TURNOVER FLOOR ANCHOR")
    print("=" * 68)
    print("\nMETHOD VALIDATION (in-window 2023-24 deeply-OTM, must be ~4-5%):")
    for k, v in results["in_window_deep_OTM_validation"].items():
        print(f"  {k}: CPR={v['cpr_pct']}%  (exp={v['exposure_upb']:.3e}, n={v['n_cohort_months']})")
    print("\nIN-WINDOW 2023-24 grid (gap<=0 parallel to out-of-window):")
    for k, v in results["grids"]["in_window_2023_2024"].items():
        print(f"  {k}: CPR={v['cpr_pct']}%  (exp={v['exposure_upb']:.3e}, n={v['n_cohort_months']})")
    print("\nOUT-OF-WINDOW 2017-2019 grid:")
    for k, v in results["grids"]["out_of_window_2017_2019"].items():
        print(f"  {k}: CPR={v['cpr_pct']}%  (exp={v['exposure_upb']:.3e}, n={v['n_cohort_months']})")
    print(f"\nHEADLINE out-of-window floor (gap<=0, age>=12): {F}%")
    print(f"Production floor: 4.0%   GATE VERDICT: {verdict}")
    print(f"\nsaved -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
