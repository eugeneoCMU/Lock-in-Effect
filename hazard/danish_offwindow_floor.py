#!/usr/bin/env python3
"""
danish_offwindow_floor.py — the Danish rule-only counterfactual at the
off-window (headline) floor calibration, which no committed run provides.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
danish_us_intercept.py / oos_identification.py / floor_form_offwindow.py).

Referee objection (round 21, findings LG-8 / eic "trilemma" PARTIAL): the
manuscript's institutional-gap figure (+$61.2B, Table 11 row d) exists only at
the demoted in-sample 4% floor ("neither leg was re-run at the off-window
floor", Table 11 note c), yet the abstract quotes it beside the off-window
headline marginal — a calibration mix the run ledger retracts elsewhere. The
flagship institutional comparison and the headline floor never coexist in any
run. This script runs that cell.

SPEC (fixed ex ante)
- Anchor: us_intercept only (the production rule-only reading; the dk_level
  bracketing case is an anchor-semantics exhibit, not a floor exhibit, and is
  not re-run here).
- Floors: {4.0 (parity replay), 4.991 (committed off-window point floor,
  asserted vs oos_identification_results.json at runtime)}.
- Refi-in-place: Berger GE best estimate (~0) only. The 0-18% sweep is not
  re-run: its positivity under this anchor is forced by construction (the
  zero-gap anchor guarantees Danish CPR >= U.S. CPR and refi only adds
  Danish prepayment), a fact the manuscript already states as a wiring
  check, so re-sweeping at a new floor cannot be informative.
- Production convention otherwise: committed 75k sample, RNG_SEED 42,
  ("US","Danish") regime tuple, shared macro frame, standalone scoring via
  extension_risk.score_extension_risk and shared-layer scoring via
  shared_layer_scoring.score_on_shared_layer (the Table 11 convention).
- Floor patch: literature_hazard.INVOLUNTARY_CPR_ANNUAL, try/finally
  restored. Under the us_intercept anchor the Danish moving hazard is the
  production U.S. hazard at zero gap WITH the floor retained, so the floor
  patch propagates to both legs — which is exactly the "rule-only
  counterfactual at the headline calibration" the referee asks for.

PARITY GATES (tolerances +/-$0.01B unless stated):
  G1 (us_intercept @4.0%): us_trapped_shared_b / danish_trapped_shared_b /
     institutional_gap_shared_b vs the committed
     danish_us_intercept_results.json point (748.9678825 / 687.7795452 /
     +61.1883374).
  G2 (@4.991% U.S. leg, standalone): must reproduce the committed
     oos_identification central at that floor ($767.5264524B) — the U.S. leg
     is anchor-invariant, so this doubles as a cross-artifact wiring check.

EX-ANTE INTERPRETIVE FRAME (no discretion after the run):
  - The gap's POSITIVITY at this anchor is forced by construction (stated in
    VI.C); the informative quantity is the MAGNITUDE at the headline floor.
  - The revision must quote the off-window rule-only gap, floor-labeled, in
    the abstract/Table 11 wherever the Danish figure appears beside the
    off-window marginal, and state its ratio to the off-window marginal
    (+$42.61B) the way VI.C currently states the 44% excess at the in-sample
    point. Expected direction (not a gate): the gap shrinks with the
    marginal as the floor rises, since the two are one object on two
    accounting legs.

Run:  cd hazard && python3 danish_offwindow_floor.py
      -> data/danish_offwindow_floor_results.json (+ parquets under
         data/danish_offwindow_floor/, regenerable, not committed)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import polars as pl

from config import LOAN_SAMPLE_PATH

import literature_hazard
from common.berger_calibration import (
    set_danish_moving_anchor,
    set_us_transplant_refi,
)
from extension_risk import score_extension_risk
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
)
from microsim_engine import run_qt_microsim
from shared_layer_scoring import score_on_shared_layer

import fed_mbs_extension_risk as fed

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "danish_offwindow_floor"
RESULTS_JSON = DATA_DIR / "danish_offwindow_floor_results.json"
US_INTERCEPT_ARTIFACT = DATA_DIR / "danish_us_intercept_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

PRODUCTION_FLOOR = 0.04
OFFWINDOW_POINT_FLOOR = 0.04991
TOL_B = 0.01


def _gate(name, got, want, tol, report):
    ok = abs(got - want) < tol
    report[name] = {"got": got, "want": want, "tol": tol, "pass": bool(ok)}
    print(f"parity gate {name}: got {got:.7f} want {want:.7f} "
          f"[{'PASS' if ok else 'FAIL'}]")


def _run_pair(loans, macro_h, macro_abm, soma_abm, empirical,
              floor: float) -> dict:
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    out_path = OUT_DIR / f"microsim_us_intercept_floor{floor * 100:g}pct.parquet"
    try:
        results = run_qt_microsim(loan_sample=loans, macro=macro_h,
                                  output=out_path)
    finally:
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
    us, dk = results["US"], results["Danish"]
    us_score = score_extension_risk(us, empirical)
    dk_score = score_extension_risk(dk, empirical)
    shared = score_on_shared_layer(macro_abm, soma_abm,
                                   {"US": us, "Danish": dk})
    return {
        "floor_annual_cpr_pct": floor * 100.0,
        "us_trapped_standalone_b": float(us_score["hazard_trapped_b"]),
        "danish_trapped_standalone_b": float(dk_score["hazard_trapped_b"]),
        "us_trapped_shared_b": float(shared["us_trapped_b"]),
        "us_share_shared_pct": float(shared["share_pct"]),
        "danish_trapped_shared_b": float(shared["danish_trapped_b"]),
        "institutional_gap_shared_b": float(shared["institutional_gap_b"]),
        "mean_us_cpr_pct": float(us["hazard_cpr_pct"].mean()),
        "mean_danish_cpr_pct": float(dk["hazard_cpr_pct"].mean()),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(US_INTERCEPT_ARTIFACT) as f:
        committed = json.load(f)["point"]
    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)
    off_point = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off_point - OFFWINDOW_POINT_FLOOR * 100) < 1e-9
    off_row = next(r for r in oos["instrument1_marginal_table"]
                   if abs(r["floor_annual_cpr_pct"] - off_point) < 1e-9)
    oos_central_b = off_row["band"]["6.5"]["central_trapped_b"]
    oos_marginal_b = off_row["band"]["6.5"]["marginal_b"]

    print("Fetching hazard macro + empirical benchmark …")
    macro_h = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(
        macro_h, soma_rolloff=fetch_soma_mbs_monthly()
    )
    print("Fetching ABM macro + SOMA (shared accounting layer) …")
    macro_abm = fed.fetch_data()
    soma_abm = fed.fetch_soma_mbs_monthly()
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    report: dict = {}
    set_danish_moving_anchor("us_intercept")
    set_us_transplant_refi(0.0)
    try:
        parity = _run_pair(loans, macro_h, macro_abm, soma_abm, empirical,
                           PRODUCTION_FLOOR)
        _gate("G1_us_shared_b", parity["us_trapped_shared_b"],
              committed["us_trapped_shared_b"], TOL_B, report)
        _gate("G1_danish_shared_b", parity["danish_trapped_shared_b"],
              committed["danish_trapped_shared_b"], TOL_B, report)
        _gate("G1_gap_b", parity["institutional_gap_shared_b"],
              committed["institutional_gap_shared_b"], TOL_B, report)

        off = _run_pair(loans, macro_h, macro_abm, soma_abm, empirical,
                        OFFWINDOW_POINT_FLOOR)
        _gate("G2_us_standalone_b@4.991", off["us_trapped_standalone_b"],
              oos_central_b, TOL_B, report)
    finally:
        set_danish_moving_anchor("dk_level")
        set_us_transplant_refi(0.0)
    runtime_s = time.perf_counter() - t0

    hard_fail = [k for k, v in report.items() if not v["pass"]]
    gap_off = off["institutional_gap_shared_b"]
    ratio_vs_marginal = gap_off / oos_marginal_b

    payload = {
        "mode": "danish_offwindow_floor",
        "spec": ("us_intercept anchor; floors {4.0 parity, 4.991}; refi 0; "
                 "two-regime microsim; standalone + shared-layer scoring; "
                 "gates G1 (committed us_intercept point) and G2 (U.S. leg "
                 "reproduces committed oos central at 4.991)"),
        "parity_run_at_4": parity,
        "offwindow_run_at_4991": off,
        "parity_gates": report,
        "parity_gates_all_pass": not hard_fail,
        "rule_only_gap_offwindow_shared_b": gap_off,
        "offwindow_marginal_b_committed": oos_marginal_b,
        "gap_over_offwindow_marginal": ratio_vs_marginal,
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"\nrule-only gap at off-window floor: ${gap_off:+.2f}B "
          f"(shared layer); off-window marginal ${oos_marginal_b:+.2f}B; "
          f"ratio {ratio_vs_marginal:+.3f}")
    print(f"gates all pass: {not hard_fail}   runtime {runtime_s:,.0f}s")
    if hard_fail:
        raise SystemExit(f"PARITY FAILURE — do not build on this: {hard_fail}")


if __name__ == "__main__":
    main()
