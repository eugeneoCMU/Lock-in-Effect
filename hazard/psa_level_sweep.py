#!/usr/bin/env python3
"""
psa_level_sweep.py — the baseline seasoning ramp swept in LEVEL on the paired
legs (round-28 WP-C3; REVIEW2 finding #4 / R1-W1(b): the 100 PSA convention is
entered with provenance "industry seasoning convention" and never swept, while
the layer ranking excludes the baseline dimension).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before
first execution; full drafting spec at specs/SPEC_round28_C1_C2_C3_C6.md
SPEC C3, whose gates and expectations are adopted unchanged).

LABELED DEVIATION from the drafted spec: the drafted spec proposed the
regime_split_marginal template (local hazard copy patched over
competing_risks.prepay_hazard). This script instead uses the floor_sweep
._ORIG_PREPAY seam exactly as moving_share_bracket / _offwindow do — the
construction whose parity discipline was re-validated bit-exactly this round
at both floors (B2). The variant hazard is a faithful copy of the production
formula (mixture_prepay's structure at full response) with
h0 = lh.h0_psa(loan_age, psa_speed=PSA), floor and FLOOR_MODE read from
lh globals at call time. Gotcha-1 (PSA_SPEED default binds at def time) is
avoided by construction: the speed is passed explicitly per cell. Gotcha-2
(the seam) is handled with the B2 restore discipline (BOTH names + state).

CELLS: PSA in {75, 100, 125, 150} x legs {null pq=0, central pq=6.5} x
floors {4.0%, 4.991%} = 16 engine runs, PSA-100 cells UNPATCHED (production
path, parity by construction) + one patched PSA-100 central at 4.0% (G1b
wiring identity). Off-window floor consumed from oos_identification
headline_oos_marginal.clean_floor_point_pct, asserted == 4.991.

PARITY GATES (BLOCKING):
  G1  PSA100@4.0: central 818.5300844066606 / null 748.1850239867648;
      marginal +9.198459770709789pp; all < 1e-9.
  G1b patched PSA-100 central @4.0 == unpatched bit-exactly (< 1e-9 $B), and
      max|h0_psa(age,100) - baseline_hazard(age)| == 0.0 on age 0..360.
  G2  PSA100@4.991: central 767.5264524465003 / null 724.9180585654117;
      marginal +5.571558182909726pp.
  G3  ANTI-GOTCHA: every off-anchor PSA cell's central trapped_b differs from
      its PSA-100 counterpart by > $1B (a no-op patch = GATE_FAILURE, never
      "no sensitivity").
  G4  bind anchors at PSA100: central@4.0 0.36269282595934704, central@4.991
      0.6881875607501289, null@4.0 0.14340654639824515, n 1683124.
  G5  monotonicity (REPORTED, routes to STOP branch): marginal_pp strictly
      increasing in PSA at each floor; central bind share strictly
      decreasing.

PRE-COMMITTED EXPECTATIONS (drafted spec C3.3, adopted): in-sample marginals
PSA75 +2.5..+3.5 / PSA125 +12.5..+13.5 / PSA150 +15..+17; off-window
PSA75 +1.5..+2.5 / PSA125 +8.5..+10 / PSA150 +11..+14. Both floors' sweep
widths expected to exceed the floor-read interval's 5.9268pp width ~2x.

LANDING RULE (fixed ex ante; ALL tex landings queue for Eugene — branch (a)
rewrites gate #98's posture_binding_layer span per the drafted replacement in
SPEC C3.4):
  (a) W_psa(off-window) > 5.9268pp  -> layer-ranking sentence restated ("the
      widest disclosed layer is the baseline level... the widest layer WITH A
      COVERAGE PROPERTY is the floor read's"), tab:uncertainty rows gain the
      sweep ranges.                                                [posture]
  (b) W_psa <= 5.9268pp             -> tablenote clause only.
  (c) non-monotone or negative marginal at any cell -> STOP, land nothing
      (contradicts the tex-301 mechanism sentence / sign-forcing argument).

MUST NOT CHANGE: config.py (PSA_SPEED stays 100); literature_hazard.py;
committed artifacts; regime-split literals $+5.0$ to $+12.1$ (a different
perturbation — cell-for-cell comparison is disclaimed in the artifact);
any .tex file.

Run:  cd hazard && python3 psa_level_sweep.py
      -> data/psa_level_sweep_results.json (frozen)
17 engine runs, ~25s each.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl

import competing_risks
import floor_sweep as fs
import literature_hazard as lh
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "psa_level_sweep_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

PSAS = [75.0, 100.0, 125.0, 150.0]
FLOORS = [0.04, None]  # None -> off-window floor from artifact
TOL = 1e-9
ANCHORS = {
    (0.04, 0.0): 748.1850239867648, (0.04, 6.5): 818.5300844066606,
    (0.04991, 0.0): 724.9180585654117, (0.04991, 6.5): 767.5264524465003,
}
BINDS = {(0.04, 6.5): 0.36269282595934704, (0.04991, 6.5): 0.6881875607501289,
         (0.04, 0.0): 0.14340654639824515}
BIND_N = 1683124
W_FLOOR_READ = 8.723086701307457 - 2.796265669289897
EXPECT = {(0.04, 75.0): (2.5, 3.5), (0.04, 125.0): (12.5, 13.5),
          (0.04, 150.0): (15.0, 17.0), (0.04991, 75.0): (1.5, 2.5),
          (0.04991, 125.0): (8.5, 10.0), (0.04991, 150.0): (11.0, 14.0)}

_ORIG = fs._ORIG_PREPAY


def make_psa_prepay(psa: float):
    """Faithful production-formula copy with the ramp speed passed explicitly
    (mixture_prepay's structure at full response; floor/mode read at call
    time). At psa=100 this is algebraically the production hazard."""
    def psa_prepay(loan_age, rate_gap, burnout, fico_z, ltv_z,
                   beta1=lh.BETA1_PREPAY_MID, coefs=None):
        b = beta1 if isinstance(beta1, np.ndarray) else float(beta1)
        c = coefs or lh.LITERATURE_COEFS
        h0 = lh.h0_psa(loan_age, psa_speed=psa)
        base = np.exp(c["beta_fico"] * fico_z + c["beta_ltv"] * ltv_z
                      + c["beta_burnout"] * burnout)
        m = np.exp((-b) * (np.asarray(rate_gap) * 100.0))
        h_vol = h0 * base * m
        h_floor = lh.cpr_annual_to_monthly_hazard(
            np.full_like(h0, lh.INVOLUNTARY_CPR_ANNUAL, dtype=np.float64))
        if lh.FLOOR_MODE == "additive":
            combined = 1.0 - (1.0 - h_floor) * (1.0 - h_vol)
        else:
            combined = np.maximum(h_floor, h_vol)
        return np.clip(combined, 0.0, 1.0)
    return psa_prepay


def run_cell(loans, empirical, floor, pq, psa):
    if psa == 100.0:
        return fs._run_scored(loans, empirical, floor, pq)
    fs._ORIG_PREPAY = make_psa_prepay(psa)
    try:
        return fs._run_scored(loans, empirical, floor, pq)
    finally:
        fs._ORIG_PREPAY = _ORIG
        competing_risks.prepay_hazard = _ORIG


def main() -> None:
    oos = json.load(open(OOS_ARTIFACT))
    off = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off - 4.991) < TOL
    floors = [0.04, off / 100.0]

    age = np.arange(0, 361, dtype=np.float64)
    ident0 = float(np.max(np.abs(lh.h0_psa(age, psa_speed=100.0)
                                 - lh.baseline_hazard(age))))
    print(f"h0 identity at PSA100: {ident0:.2e}")

    print("Shared macro frame (fetched once) ...")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    cells: dict = {}
    for floor in floors:
        for psa in PSAS:
            for pq in (0.0, 6.5):
                r = run_cell(loans, empirical, floor, pq, psa)
                r["psa"] = psa
                cells[f"{floor*100:g}|{psa:g}|{pq:g}"] = r
                print(f"  floor {floor*100:g} PSA {psa:g} pq {pq:g}: "
                      f"${r['trapped_b']:7.2f}B bind {r['floor_bind_share']:.3f}")
    # G1b wiring identity: patched PSA-100 central at 4.0%
    fs._ORIG_PREPAY = make_psa_prepay(100.0)
    try:
        g1b = fs._run_scored(loans, empirical, 0.04, 6.5)
    finally:
        fs._ORIG_PREPAY = _ORIG
        competing_risks.prepay_hazard = _ORIG

    for floor in floors:
        for psa in PSAS:
            key_c, key_n = f"{floor*100:g}|{psa:g}|6.5", f"{floor*100:g}|{psa:g}|0"
            cells[key_c]["marginal_b"] = cells[key_c]["trapped_b"] - cells[key_n]["trapped_b"]
            cells[key_c]["marginal_pp"] = cells[key_c]["share_pct"] - cells[key_n]["share_pct"]

    gates = {}
    for (fl, pq), want in ANCHORS.items():
        got = cells[f"{fl*100:g}|100|{pq:g}"]["trapped_b"]
        gates[f"G12_anchor_{fl*100:g}_{pq:g}"] = {
            "got": got, "want": want, "pass": abs(got - want) < TOL}
    gates["G1b_wiring_identity"] = {
        "got": g1b["trapped_b"], "want": cells["4|100|6.5"]["trapped_b"],
        "h0_identity_max_abs": ident0,
        "pass": abs(g1b["trapped_b"] - cells["4|100|6.5"]["trapped_b"]) < TOL
                and ident0 == 0.0}
    g3 = all(abs(cells[f"{fl*100:g}|{p:g}|6.5"]["trapped_b"]
                 - cells[f"{fl*100:g}|100|6.5"]["trapped_b"]) > 1.0
             for fl in floors for p in (75.0, 125.0, 150.0))
    gates["G3_antigotcha"] = {"pass": g3}
    g4 = all(abs(cells[f"{fl*100:g}|100|{pq:g}"]["floor_bind_share"] - want) < TOL
             and cells[f"{fl*100:g}|100|{pq:g}"]["floor_bind_loan_months"] == BIND_N
             for (fl, pq), want in BINDS.items())
    gates["G4_bind_anchors"] = {"pass": g4}
    all_pass = all(v["pass"] for v in gates.values())

    mono = all(
        all(cells[f"{fl*100:g}|{PSAS[i]:g}|6.5"]["marginal_pp"]
            < cells[f"{fl*100:g}|{PSAS[i+1]:g}|6.5"]["marginal_pp"]
            for i in range(3))
        and all(cells[f"{fl*100:g}|{PSAS[i]:g}|6.5"]["floor_bind_share"]
                > cells[f"{fl*100:g}|{PSAS[i+1]:g}|6.5"]["floor_bind_share"]
                for i in range(3))
        for fl in floors)
    positive = all(cells[f"{fl*100:g}|{p:g}|6.5"]["marginal_pp"] > 0
                   for fl in floors for p in PSAS)

    ranges = {}
    for fl in floors:
        ms = [cells[f"{fl*100:g}|{p:g}|6.5"]["marginal_pp"] for p in PSAS]
        ranges[f"{fl*100:g}"] = {"lo_pp": min(ms), "hi_pp": max(ms),
                                 "width_pp": max(ms) - min(ms)}
    expect_check = {f"{fl*100:g}|{p:g}": {
        "band": EXPECT[(round(fl, 5), p)],
        "realized": cells[f"{fl*100:g}|{p:g}|6.5"]["marginal_pp"],
        "inside": EXPECT[(round(fl, 5), p)][0]
                  <= cells[f"{fl*100:g}|{p:g}|6.5"]["marginal_pp"]
                  <= EXPECT[(round(fl, 5), p)][1]}
        for fl in floors for p in (75.0, 125.0, 150.0)}

    w_off = ranges["4.991"]["width_pp"]
    verdict = ("NON_MONOTONE_OR_NEGATIVE" if not (mono and positive)
               else "PSA_WIDER" if w_off > W_FLOOR_READ else "PSA_NARROWER")
    status = ("OK" if (all_pass and mono and positive)
              else ("GATE_FAILURE" if not all_pass else "CHECK_FAILURE"))
    payload = {
        "mode": "psa_level_sweep", "status": status,
        "spec": ("baseline ramp level 75/100/125/150 PSA, paired legs, both "
                 "floors, floor_sweep seam (labeled deviation from drafted "
                 "template, B2-validated); PSA-100 unpatched; G1b patched-100 "
                 "wiring identity; landing (a)/(b)/(c) fixed ex ante; "
                 "regime-split cell-for-cell comparison disclaimed (different "
                 "perturbation: mid-window break vs whole-window level)."),
        "parity_gates": gates, "parity_gates_all_pass": all_pass,
        "monotone": mono, "all_marginals_positive": positive,
        "cells": cells, "ranges": ranges,
        "comparison": {"floor_read_width_pp": W_FLOOR_READ,
                       "psa_over_floor_read_at_headline": w_off / W_FLOOR_READ,
                       "regime_split_h0_range_pp": [4.965583563905398,
                                                    12.123711475343967]},
        "expectation_check": expect_check,
        "verdict": verdict, "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"\nstatus {status}; verdict {verdict}; "
          f"widths in-sample {ranges['4']['width_pp']:.2f}pp / "
          f"off-window {w_off:.2f}pp vs floor-read {W_FLOOR_READ:.2f}pp")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript.")


if __name__ == "__main__":
    main()
