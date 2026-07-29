#!/usr/bin/env python3
"""
moving_share_bracket_offwindow.py — the construct-mismatch bracket re-run at
the headline off-window floor (round-28 WP-B2; REVIEW2 DA-C2 / R2-W3).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before
first execution; full drafting spec at specs/SPEC_round28_B2_C4_C5.md §B2).

WHY. The committed moving-share bracket (run moving_share_bracket) prices the
moving-probability -> total-hazard construct mismatch only at the in-sample
4.0% floor. The paper's headline marginal lives at the 4.991% off-window
floor, and tab:assembly's completeness claim was falsified partly on this
run's absence from that calibration (REVIEW2 finding #2). This run prices the
bracket where the headline lives. Machinery imported UNMODIFIED from
moving_share_bracket (mixture_prepay, probe_identity); scoring via
floor_sweep._run_scored, the production convention (committed 75k sample,
seed 42, default regime tuple, shared macro frame, raw-basis scorer,
value-preserving bind tally).

DESIGN. FLOOR consumed at runtime from oos_identification_results.json
headline_oos_marginal.clean_floor_point_pct, asserted == 4.991 to 1e-9
(floor_form_offwindow convention). CENTRAL_PQ 6.5. Cells: null (pq 0,
unpatched production path) + s in {0.25, 0.50, 1.00} via the mixture
installed at floor_sweep._ORIG_PREPAY (the bind-tally seam), BOTH names +
_share restored in a finally after each cell. probe_identity() executed with
INVOLUNTARY_CPR_ANNUAL set to the off-window floor (censoring region of the
headline calibration), restored after. The involuntary floor is NOT scaled
by s. Nothing in config.py changes.

PRE-COMMITTED PROJECTION (proportional scaling of the off-window s=1
marginal by the committed in-sample ratios r(0.5)=0.5354233883204735,
r(0.25)=0.27342932174024 from moving_share_bracket_results.json):
    s=0.50 -> +$22.81B, +2.983pp        s=0.25 -> +$11.65B, +1.523pp
(strict linear-in-s reference: +2.786pp / +1.393pp). SIGNED ex-ante
deviation prediction: the off-window ratios should land AT OR ABOVE the
in-sample ratios (higher floor -> larger bind region -> s-independent
contributions there), so the projections are lower bounds; signed at the
hazard level, approximate at the dollar aggregate. Materiality band +-1.0pp.

PARITY GATES (BLOCKING; bit-exact 1e-9 where a committed anchor exists):
  P1  s=1.00 mixture path at (4.991, 6.5) reproduces committed central
      trapped 767.5264524465003 / share 100.36328284662208; identity probe
      at the off-window floor: max|h_mix(s=1)-h_prod| < 1e-12 and
      max|h_mix(s=0)-h_prod(b1=0)| < 1e-12 on the fixed 10k grid.
  P2  null cell reproduces 724.9180585654117 / 94.79172466371236.
  P3  s=1 cell's floor_bind_share == 0.6881875607501289 over 1683124
      loan-months.
  P4  restoration: fs._ORIG_PREPAY, competing_risks.prepay_hazard,
      msb._share == 1.0, INVOLUNTARY_CPR_ANNUAL == 0.04 after every cell.
  C1  ordering 0 < m(0.25) < m(0.50) < m(1.00)+1e-9 on $B (wiring alarm).
  C2  ratio monotonicity r_ow(s) >= r_in(s), REPORTED not blocking; a
      violation is disclosed, never reinterpreted.

LANDING RULE (pre-committed pure function of m(0.5) in pp; classifier fixed
here, dispositions executed later under WP-B1 with Eugene's sign-off):
  A: m(0.5) > +3.0          rows land in rebuilt tab:assembly +
                            tab:uncertainty; no range-conditionality forced.
  B: +2.8 <= m(0.5) <= +3.0 as A, PLUS the range-conditionality statement is
                            forced (a measured correction reaches the binding
                            interval's floor).                      [posture]
  C: m(0.5) < +2.8          as A, PLUS the strongest form (a measured,
                            disclosed variation falls OUTSIDE the binding
                            interval).                              [posture]
Pre-fixed: m(0.25) projected +1.52pp is Branch-C territory BY CONSTRUCTION;
it is the bracket's deep stress, enters tab:assembly as the low member, and
does NOT on its own trigger the B/C statement — only m(0.5) does.
Shared-basis conversions use calibration_reconciliation basis_map.offset_pp,
asserted == 9.096091632702699.

MUST NOT CHANGE: the committed moving_share_bracket_results.json; the
headline +5.6pp/+$42.6B; in-sample bracket literals at tex 255 (gate #102);
the binding interval and all zero-slack literals; config.py; any .tex file.

Run:  cd hazard && python3 moving_share_bracket_offwindow.py
      -> data/moving_share_bracket_offwindow_results.json  (frozen)
4 engine runs, ~25s each.
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
import moving_share_bracket as msb
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "moving_share_bracket_offwindow_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
INSAMPLE_ARTIFACT = DATA_DIR / "moving_share_bracket_results.json"
CALIB_ARTIFACT = DATA_DIR / "calibration_reconciliation_results.json"

CENTRAL_PQ = 6.5
SHARES = [0.25, 0.50, 1.00]
TOL = 1e-9
WANT_CENTRAL_B = 767.5264524465003
WANT_CENTRAL_SHARE = 100.36328284662208
WANT_NULL_B = 724.9180585654117
WANT_NULL_SHARE = 94.79172466371236
WANT_BIND_SHARE = 0.6881875607501289
WANT_BIND_N = 1683124
WANT_OFFSET_PP = 9.096091632702699
PROJ = {"0.5": {"pp": 2.983, "b": 22.81}, "0.25": {"pp": 1.523, "b": 11.65}}
MATERIALITY_PP = 1.0

_ORIG = msb._ORIG_PREPAY


def landing_branch(m_half_pp: float) -> str:
    """Pre-committed classifier on the s=0.5 marginal (pp)."""
    if m_half_pp > 3.0:
        return "A"
    if m_half_pp >= 2.8:
        return "B"
    return "C"


def main() -> None:
    oos = json.load(open(OOS_ARTIFACT))
    head = oos["headline_oos_marginal"]
    assert abs(head["clean_floor_point_pct"] - 4.991) < TOL
    floor = head["clean_floor_point_pct"] / 100.0

    ins = json.load(open(INSAMPLE_ARTIFACT))
    r_in = {s: ins["cells"][s]["marginal_b"] / ins["cells"]["1"]["marginal_b"]
            for s in ("0.25", "0.5")}
    calib = json.load(open(CALIB_ARTIFACT))
    offset = calib["basis_map"]["offset_pp"]
    assert abs(offset - WANT_OFFSET_PP) < TOL

    # identity probe in the off-window censoring region
    cur = lh.INVOLUNTARY_CPR_ANNUAL
    lh.INVOLUNTARY_CPR_ANNUAL = floor
    try:
        ident = msb.probe_identity()
    finally:
        lh.INVOLUNTARY_CPR_ANNUAL = cur
    print(f"identity probe @4.991: s1 {ident['max_abs_diff_s1']:.2e} "
          f"s0 {ident['max_abs_diff_s0']:.2e} "
          f"[{'PASS' if ident['pass'] else 'FAIL'}]")

    print("Shared macro frame (fetched once) ...")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    null = fs._run_scored(loans, empirical, floor, 0.0)
    cells: dict = {}
    restoration_ok = True
    for s in SHARES:
        msb._share = s
        fs._ORIG_PREPAY = msb.mixture_prepay
        try:
            r = fs._run_scored(loans, empirical, floor, CENTRAL_PQ)
        finally:
            fs._ORIG_PREPAY = _ORIG
            competing_risks.prepay_hazard = _ORIG
            msb._share = 1.0
        restoration_ok = restoration_ok and (
            fs._ORIG_PREPAY is _ORIG
            and competing_risks.prepay_hazard is _ORIG
            and msb._share == 1.0
            and abs(lh.INVOLUNTARY_CPR_ANNUAL - 0.04) < TOL)
        r["share_s"] = s
        r["marginal_b"] = r["trapped_b"] - null["trapped_b"]
        r["marginal_pp"] = r["share_pct"] - null["share_pct"]
        r["share_pct_shared"] = r["share_pct"] - offset
        r["ratio_vs_s1"] = None
        cells[f"{s:g}"] = r
        print(f"  s={s:4.2f}: ${r['trapped_b']:7.2f}B "
              f"marginal ${r['marginal_b']:+6.2f}B ({r['marginal_pp']:+5.2f}pp)")
    for s in ("0.25", "0.5"):
        cells[s]["ratio_vs_s1"] = cells[s]["marginal_b"] / cells["1"]["marginal_b"]
    null["share_pct_shared"] = null["share_pct"] - offset

    gates = {
        "P1_s1_offwindow": {
            "got_b": cells["1"]["trapped_b"], "want_b": WANT_CENTRAL_B,
            "got_share": cells["1"]["share_pct"], "want_share": WANT_CENTRAL_SHARE,
            "identity_probe": ident,
            "pass": (abs(cells["1"]["trapped_b"] - WANT_CENTRAL_B) < TOL
                     and abs(cells["1"]["share_pct"] - WANT_CENTRAL_SHARE) < TOL
                     and ident["pass"])},
        "P2_null": {
            "got_b": null["trapped_b"], "want_b": WANT_NULL_B,
            "got_share": null["share_pct"], "want_share": WANT_NULL_SHARE,
            "pass": (abs(null["trapped_b"] - WANT_NULL_B) < TOL
                     and abs(null["share_pct"] - WANT_NULL_SHARE) < TOL)},
        "P3_bind": {
            "got_share": cells["1"]["floor_bind_share"], "want_share": WANT_BIND_SHARE,
            "got_n": cells["1"]["floor_bind_loan_months"], "want_n": WANT_BIND_N,
            "pass": (abs(cells["1"]["floor_bind_share"] - WANT_BIND_SHARE) < TOL
                     and cells["1"]["floor_bind_loan_months"] == WANT_BIND_N)},
        "P4_restoration": {"pass": restoration_ok},
    }
    all_pass = all(v["pass"] for v in gates.values())
    ms = [cells[f"{s:g}"]["marginal_b"] for s in SHARES]
    c1 = (0.0 < ms[0] < ms[1] < ms[2] + 1e-9) if all_pass else False
    c2 = {"r_ow_0.5": cells["0.5"]["ratio_vs_s1"], "r_in_0.5": r_in["0.5"],
          "r_ow_0.25": cells["0.25"]["ratio_vs_s1"], "r_in_0.25": r_in["0.25"],
          "pass": (cells["0.5"]["ratio_vs_s1"] >= r_in["0.5"] - 1e-9
                   and cells["0.25"]["ratio_vs_s1"] >= r_in["0.25"] - 1e-9)}
    for k, v in gates.items():
        print(f"  {k}: [{'PASS' if v['pass'] else 'FAIL'}]")
    print(f"  C1 ordering: [{'PASS' if c1 else 'FAIL'}]  "
          f"C2 ratio-monotone: [{'PASS' if c2['pass'] else 'VIOLATED-DISCLOSED'}]")

    proj = {}
    for s in ("0.5", "0.25"):
        dev = cells[s]["marginal_pp"] - PROJ[s]["pp"]
        proj[s] = {"projected_pp": PROJ[s]["pp"], "projected_b": PROJ[s]["b"],
                   "realized_pp": cells[s]["marginal_pp"],
                   "realized_b": cells[s]["marginal_b"],
                   "deviation_pp": dev,
                   "within_materiality_band_1pp": abs(dev) <= MATERIALITY_PP}
    branch = landing_branch(cells["0.5"]["marginal_pp"]) if (all_pass and c1) else None

    status = ("OK" if (all_pass and c1)
              else ("GATE_FAILURE" if not all_pass else "CHECK_FAILURE"))
    payload = {
        "mode": "moving_share_bracket_offwindow", "status": status,
        "spec": ("in-sample mixture machinery unmodified at the 4.991% "
                 "off-window floor; s in {0.25,0.5,1} + null; parity P1-P4 "
                 "bit-exact vs oos_identification anchors; C1 ordering "
                 "blocking, C2 ratio-monotonicity reported; projection "
                 "r_in-proportional with +-1pp band; landing branch "
                 "A/B/C fixed ex ante on m(0.5)."),
        "floor_annual_cpr_pct": 4.991,
        "floor_provenance": "oos_identification_results.json headline_oos_marginal.clean_floor_point_pct",
        "parity_gates": gates, "parity_gates_all_pass": all_pass,
        "c1_bracket_ordering_pass": c1, "c2_ratio_monotone": c2,
        "null": null, "cells": cells,
        "projection": proj, "landing_branch": branch,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"\nstatus {status}; landing branch {branch}; frozen -> {RESULTS_JSON}")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript.")


if __name__ == "__main__":
    main()
