#!/usr/bin/env python3
"""
concave_marginal.py — the concave gap transform's effect on the MARGINAL,
which the committed concave run never measured.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
floor_form_test.py / oos_identification.py / floor_form_offwindow.py).

Referee objection (round 21, panel finding MF-2 CONFIRMED): the manuscript
tests the log-linear extrapolation of the imported elasticity only on the
LEVEL (seasonality_concave_gap.py Part 2: 107.033% -> 105.708%) and declares
"the log-linear extrapolation is not load-bearing." The identified object is
the marginal over the beta1=0 null, and no concave null leg was ever run: the
implied concave marginal (105.7 - 97.8 = +7.9pp against the production
+9.2pp) moves by 1.3pp, which exceeds the +/-1.0pp materiality convention the
manuscript itself applies to the floor-form test. This script runs the
concave null and the concave pair at the off-window point floor, so the
transform's effect on the marginal is measured rather than implied.

SPEC (fixed ex ante)
- Transform: the committed piecewise-concave gap transform of
  seasonality_concave_gap.py Part 2, applied by patching
  competing_risks.prepay_hazard (CONCAVE_KINK_PP = 2.0, CONCAVE_SLOPE2 = 0.5,
  identical constants), restored in a finally block.
- Floor form: production "max" throughout (the form dimension is
  floor_form_offwindow.py's remit, not this script's).
- Floors: {4.0 (production), 4.991 (committed off-window point floor from
  oos_identification_results.json)}.
- Legs per floor: concave central (p_q 6.5) + concave null (p_q 0).
- Parity legs (production transform, run fresh, US regime only, same as the
  committed concave run's convention): central + null at 4.0%.
- Production convention otherwise: committed 75k sample, RNG_SEED 42, US
  regime (the concave run's committed convention; the US leg is regime-tuple
  invariant and G1 verifies this against the committed two-regime anchors),
  one shared macro frame, raw-basis scoring.

PARITY GATES (tolerances +/-$0.01B unless stated):
  G1 (production transform @4%): central vs no_lockin_null_results.json
     $818.5300844B; null vs $748.1850240B. Doubles as the US-only-regime
     equivalence check.
  G2 (concave central @4%): vs the committed
     seasonality_concave_gap_results.json concave trapped_b (read at
     runtime; quoted 808.402B / 105.708%).
  G3 (transform-invariance of the null, ex-ante assertion): the concave
     null @4% must equal the production null to +/-$0.01B, because beta1=0
     makes the gap transform inert; failure indicates the patch leaks into
     a non-elasticity channel and BLOCKS interpretation.

EX-ANTE INTERPRETIVE THRESHOLDS (the +/-1.0pp materiality convention of
floor_form_test.py, applied symmetrically to this transform):
  T1: if |concave marginal @4% - production marginal (+9.198pp)| > 1.0pp,
      the transform is LOAD-BEARING for the marginal: the manuscript's "not
      load-bearing" sentence must be retracted or scoped explicitly to the
      level, the concave marginal reported in the uncertainty consolidation
      (Table 8) and the basis table (Table 10), and the transform dimension
      carried wherever the marginal's operative uncertainty is stated.
  T2: if within +/-1.0pp, the sentence stands as written, extended to note
      the marginal was checked directly.
  Either way the concave marginal at the off-window point floor (4.991%) is
  reported beside the max-form off-window marginal (+5.57pp) as the
  transform sensitivity of the headline. No further discretion after the run.

Run:  cd hazard && python3 concave_marginal.py
      -> data/concave_marginal_results.json (+ per-run parquets under
         data/concave_marginal/, regenerable, not committed)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import competing_risks
import literature_hazard
from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "concave_marginal"
RESULTS_JSON = DATA_DIR / "concave_marginal_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
CONCAVE_ARTIFACT = DATA_DIR / "seasonality_concave_gap_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

CONCAVE_KINK_PP = 2.0
CONCAVE_SLOPE2 = 0.5
PRODUCTION_FLOOR = 0.04
OFFWINDOW_POINT_FLOOR = 0.04991  # asserted vs committed artifact at runtime
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
TOL_B = 0.01
MATERIALITY_PP = 1.0


def _concave_wrapper(original_prepay):
    def concave_prepay(loan_age, rate_gap, burnout, fico_z, ltv_z, beta1,
                       coefs=None):
        g_pp = np.abs(rate_gap) * 100.0
        g_concave = np.minimum(g_pp, CONCAVE_KINK_PP) + CONCAVE_SLOPE2 * (
            np.maximum(g_pp - CONCAVE_KINK_PP, 0.0)
        )
        gap_t = np.sign(rate_gap) * g_concave / 100.0
        return original_prepay(loan_age, gap_t, burnout, fico_z, ltv_z,
                               beta1=beta1, coefs=coefs)
    return concave_prepay


def _run_scored(loans, macro, empirical, transform: str, floor: float,
                pq: float) -> dict:
    """One US-regime microsim run at (transform, floor, elasticity)."""
    original_prepay = competing_risks.prepay_hazard
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    out_path = OUT_DIR / (
        f"microsim_{transform}_floor{floor * 100:g}pct_pq{pq:g}.parquet"
    )
    try:
        if transform == "concave":
            competing_risks.prepay_hazard = _concave_wrapper(original_prepay)
        paths = run_qt_microsim(loan_sample=loans, macro=macro,
                                regimes=("US",), output=out_path,
                                p_q_shock_pct=pq)
        sim = paths["US"] if isinstance(paths, dict) else pd.read_parquet(out_path)
    finally:
        competing_risks.prepay_hazard = original_prepay
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
    score = score_extension_risk(sim, empirical)
    return {
        "transform": transform,
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "r_lag0": (None if score["cross_correlation"].get(0) is None
                   else float(score["cross_correlation"].get(0))),
        "peak_lag": (None if score.get("best_lag") is None
                     else int(score["best_lag"])),
    }


def _gate(name, got, want, tol, report):
    ok = abs(got - want) < tol
    report[name] = {"got": got, "want": want, "tol": tol, "pass": bool(ok)}
    print(f"parity gate {name}: got {got:.7f} want {want:.7f} "
          f"[{'PASS' if ok else 'FAIL'}]")


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(NULL_ARTIFACT) as f:
        anchor = json.load(f)
    with open(CONCAVE_ARTIFACT) as f:
        conc = json.load(f)
    conc_committed = conc["path_b_concave_gap"]["concave"]["trapped_b"] \
        if "path_b_concave_gap" in conc else conc["concave"]["trapped_b"]
    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)
    off_point = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off_point - OFFWINDOW_POINT_FLOOR * 100) < 1e-9
    off_row = next(r for r in oos["instrument1_marginal_table"]
                   if abs(r["floor_annual_cpr_pct"] - off_point) < 1e-9)
    offwindow_max_marginal_pp = off_row["band"]["6.5"]["marginal_pp"]

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    report: dict = {}

    prod_central = _run_scored(loans, macro, empirical, "production",
                               PRODUCTION_FLOOR, CENTRAL_PQ)
    prod_null = _run_scored(loans, macro, empirical, "production",
                            PRODUCTION_FLOOR, NULL_PQ)
    _gate("G1_central_b", prod_central["trapped_b"],
          anchor["central_trapped_b"], TOL_B, report)
    _gate("G1_null_b", prod_null["trapped_b"], anchor["null_trapped_b"],
          TOL_B, report)

    conc_central_4 = _run_scored(loans, macro, empirical, "concave",
                                 PRODUCTION_FLOOR, CENTRAL_PQ)
    _gate("G2_concave_central_b", conc_central_4["trapped_b"],
          conc_committed, TOL_B, report)
    conc_null_4 = _run_scored(loans, macro, empirical, "concave",
                              PRODUCTION_FLOOR, NULL_PQ)
    _gate("G3_null_transform_invariance", conc_null_4["trapped_b"],
          prod_null["trapped_b"], TOL_B, report)

    conc_central_off = _run_scored(loans, macro, empirical, "concave",
                                   OFFWINDOW_POINT_FLOOR, CENTRAL_PQ)
    conc_null_off = _run_scored(loans, macro, empirical, "concave",
                                OFFWINDOW_POINT_FLOOR, NULL_PQ)

    hard_fail = [k for k, v in report.items() if not v["pass"]]

    prod_marginal_pp = prod_central["share_pct"] - prod_null["share_pct"]
    conc_marginal_4_pp = conc_central_4["share_pct"] - conc_null_4["share_pct"]
    conc_marginal_off_pp = (conc_central_off["share_pct"]
                            - conc_null_off["share_pct"])
    delta_pp = conc_marginal_4_pp - prod_marginal_pp
    t1 = abs(delta_pp) > MATERIALITY_PP
    verdict = (
        "T1: the concave transform moves the marginal by more than 1.0pp — "
        "the log-linear extrapolation IS load-bearing for the identified "
        "marginal; retract or scope the 'not load-bearing' sentence to the "
        "level and carry the transform dimension in Tables 8/10"
        if t1 else
        "T2: concave marginal within 1.0pp of production — the 'not "
        "load-bearing' sentence stands, extended to note the marginal was "
        "checked directly"
    )

    payload = {
        "mode": "concave_marginal",
        "spec": ("concave transform (kink 2.0pp, slope2 0.5) central+null at "
                 "floors {4.0, 4.991}%; production-transform parity pair at "
                 "4.0%; US regime; max floor form; gates G1/G2/G3; ex-ante "
                 "T1/T2 at +/-1.0pp"),
        "legs": {
            "production_central_4": prod_central,
            "production_null_4": prod_null,
            "concave_central_4": conc_central_4,
            "concave_null_4": conc_null_4,
            "concave_central_4991": conc_central_off,
            "concave_null_4991": conc_null_off,
        },
        "parity_gates": report,
        "parity_gates_all_pass": not hard_fail,
        "production_marginal_pp": prod_marginal_pp,
        "concave_marginal_pp_at_4": conc_marginal_4_pp,
        "concave_marginal_b_at_4": (conc_central_4["trapped_b"]
                                    - conc_null_4["trapped_b"]),
        "concave_marginal_pp_at_offwindow_point": conc_marginal_off_pp,
        "concave_marginal_b_at_offwindow_point": (
            conc_central_off["trapped_b"] - conc_null_off["trapped_b"]),
        "offwindow_max_form_marginal_pp_committed": offwindow_max_marginal_pp,
        "transform_delta_pp_at_4": delta_pp,
        "t1_load_bearing": bool(t1),
        "interpretive_verdict": verdict,
        "runtime_s": time.perf_counter() - t0,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"\nproduction marginal {prod_marginal_pp:+.4f}pp | concave@4 "
          f"{conc_marginal_4_pp:+.4f}pp | concave@4.991 "
          f"{conc_marginal_off_pp:+.4f}pp")
    print(f"verdict: {verdict}")
    if hard_fail:
        raise SystemExit(f"PARITY FAILURE — do not build on this: {hard_fail}")


if __name__ == "__main__":
    main()
