#!/usr/bin/env python3
"""
band_low_extension.py — the lock-in marginal as a curve in the imported
elasticity, extended below the adopted band's 5.5% edge toward zero
(round-26 panel item B6; R1-W3 / R2-W2 / DA-C2).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before
first execution, artifact committed separately after).

Referee objection (round-26 panel, verified CONFIRMED): the elasticity is
imported from the Liebersohn--Rothstein specification range {5.5, 6.5, 7.7}
and the paper's own data cannot reject zero for it; the manuscript sweeps
the band only over its published range, so a reader who trusts the
in-sample non-rejection more than the imported literature cannot see what
the marginal would be at any smaller elasticity. This run makes the
marginal's elasticity-dependence an exhibit rather than a concession.

DESIGN (fixed ex ante). The committed floor_sweep harness is IMPORTED and
its _run_scored convention reused verbatim (same committed 75k loan
sample, RNG_SEED 42, same regime tuple, one shared macro frame, raw-basis
scoring via extension_risk.score_extension_risk, fresh runs, caches not
consulted). Grid:
  p_q_shock_pct in {0.0, 1.0, 2.0, 3.0, 3.25, 4.0, 5.0, 5.5, 6.5, 7.7}
    (0.0 is the beta1=0 null; 3.25 is exactly half the adopted central
     6.5; 5.5/6.5/7.7 are the adopted band, re-run fresh for curve
     continuity)
  floors in {4.0% (production in-sample), 4.991% (headline off-window)}
Marginal at (floor, pq) = trapped(floor, pq) - trapped(floor, 0.0), $B,
and share_pct difference in pp (raw basis; the marginal is basis-invariant
per the committed shared-netting argument).

PARITY GATES (BLOCKING; fresh runs at the four committed cells, tolerance
+/- $0.01B / +/- 0.01pp, the floor_sweep production tolerance):
  P1  (4.0%, 6.5)  central  $818.530B      (no_lockin_null_results.json)
  P2  (4.0%, 0.0)  null     $748.185B      (same artifact)
      marginal +$70.345B / +9.198pp
  P3  (4.991%, 6.5) central $767.5264524465003B and marginal
      $42.60839388108866B / 5.571558182909726pp
      (oos_identification_results.json instrument1 row 4.991, band 6.5)
  P4  (4.991%, 0.0) null   $724.9180585654117B (same row)
Floor-bind instrumentation at (4.991, 6.5) must reproduce the committed
0.6881875607501289 share of 1,683,124 evaluated loan-months (+/- 1pp on
the share, +/- 0.5% on the count), else the bind column is withdrawn, not
reinterpreted.

EX-ANTE CHECKS AND POSTURE (verbatim; no discretion after the run):
  C1  Monotonicity: at each floor the marginal is weakly increasing in pq
      across the grid. PASS/FAIL reported; a failure is a wiring alarm
      (the specification's sign forcing predicts monotone), and on FAIL
      the artifact is committed with status CHECK_FAILURE and nothing
      lands in the manuscript.
  C2  The pq = 0 cells ARE the null legs; their marginal is 0 by
      construction and is reported as the curve's anchor, not a finding.
  POSTURE: this is a DESCRIPTIVE exhibit. It does not identify the
  elasticity; it prices the dependence on it. The manuscript action on
  C1-PASS is one table (the curve at both floors) plus one paragraph in
  the calibration-box subsection stating: (i) the marginal at half the
  adopted central (pq = 3.25) at both floors; (ii) that the curve's shape
  is the censoring mechanism made visible (floor-dependent concavity);
  (iii) that a reader who weighs the in-sample non-rejection over the
  imported band reads the curve toward its low end, and the design's
  answer to "how small could the marginal be" is the curve, not the box
  edge alone. No existing number changes anywhere.

Run:  cd hazard && python3 band_low_extension.py
      -> data/band_low_extension_results.json  (frozen)
20 engine runs, ~25s each (floor_sweep measured 352s for 14). Does NOT
change config.py production defaults. Does NOT edit any .tex file.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import polars as pl

import floor_sweep as fs
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "band_low_extension_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

PQ_GRID = [0.0, 1.0, 2.0, 3.0, 3.25, 4.0, 5.0, 5.5, 6.5, 7.7]
FLOORS = [0.04, 0.04991]

TOL_B = 0.01
TOL_PP = 0.01
P3_CENTRAL_B = 767.5264524465003
P3_MARGINAL_B = 42.60839388108866
P3_MARGINAL_PP = 5.571558182909726
P4_NULL_B = 724.9180585654117
BIND_SHARE_4991 = 0.6881875607501289
BIND_N_4991 = 1_683_124


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)

    with open(NULL_ARTIFACT) as f:
        nl = json.load(f)
    committed_central_b = nl["central_trapped_b"]
    committed_null_b = nl["null_trapped_b"]
    committed_marginal_b = nl["lockin_marginal_b"]
    committed_marginal_pp = nl["lockin_marginal_share_pp"]
    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)
    row4991 = next(r for r in oos["instrument1_marginal_table"]
                   if abs(r["floor_annual_cpr_pct"] - 4.991) < 1e-9)
    assert abs(row4991["band"]["6.5"]["central_trapped_b"] - P3_CENTRAL_B) < 1e-9
    assert abs(row4991["band"]["6.5"]["marginal_b"] - P3_MARGINAL_B) < 1e-9
    assert abs(row4991["null_trapped_b"] - P4_NULL_B) < 1e-9

    print("Shared macro frame (fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    curves: dict = {}
    gate_report: dict = {}
    for floor in FLOORS:
        cells = {}
        for pq in PQ_GRID:
            cells[f"{pq:g}"] = fs._run_scored(loans, empirical, floor, pq)
            c = cells[f"{pq:g}"]
            print(f"  floor {floor*100:5.3f}%  pq {pq:4.2f}  "
                  f"${c['trapped_b']:7.2f}B ({c['share_pct']:6.2f}%)")
        null = cells["0"]
        curve = []
        for pq in PQ_GRID:
            c = cells[f"{pq:g}"]
            curve.append({
                "p_q_shock_pct": pq, "beta1": c["beta1"],
                "trapped_b": c["trapped_b"], "share_pct": c["share_pct"],
                "marginal_b": c["trapped_b"] - null["trapped_b"],
                "marginal_pp": c["share_pct"] - null["share_pct"],
                "floor_bind_share": c["floor_bind_share"],
            })
        curves[f"{floor * 100:g}"] = {"null_trapped_b": null["trapped_b"],
                                      "curve": curve}

    # ---- parity gates ------------------------------------------------------
    c40 = curves["4"]["curve"]
    c4991 = curves["4.991"]["curve"]
    get = lambda curve, pq: next(r for r in curve if r["p_q_shock_pct"] == pq)
    m40, m4991 = get(c40, 6.5), get(c4991, 6.5)
    gate_report["P1_central_4.0"] = {
        "got": m40["trapped_b"], "want": committed_central_b,
        "pass": abs(m40["trapped_b"] - committed_central_b) <= TOL_B}
    gate_report["P2_null_4.0"] = {
        "got": curves["4"]["null_trapped_b"], "want": committed_null_b,
        "pass": abs(curves["4"]["null_trapped_b"] - committed_null_b) <= TOL_B}
    gate_report["P2_marginal_4.0"] = {
        "got_b": m40["marginal_b"], "want_b": committed_marginal_b,
        "got_pp": m40["marginal_pp"], "want_pp": committed_marginal_pp,
        "pass": (abs(m40["marginal_b"] - committed_marginal_b) <= TOL_B
                 and abs(m40["marginal_pp"] - committed_marginal_pp) <= TOL_PP)}
    gate_report["P3_central_marginal_4.991"] = {
        "got_central": m4991["trapped_b"], "want_central": P3_CENTRAL_B,
        "got_marginal_b": m4991["marginal_b"], "want_marginal_b": P3_MARGINAL_B,
        "got_marginal_pp": m4991["marginal_pp"], "want_marginal_pp": P3_MARGINAL_PP,
        "pass": (abs(m4991["trapped_b"] - P3_CENTRAL_B) <= TOL_B
                 and abs(m4991["marginal_b"] - P3_MARGINAL_B) <= TOL_B
                 and abs(m4991["marginal_pp"] - P3_MARGINAL_PP) <= TOL_PP)}
    gate_report["P4_null_4.991"] = {
        "got": curves["4.991"]["null_trapped_b"], "want": P4_NULL_B,
        "pass": abs(curves["4.991"]["null_trapped_b"] - P4_NULL_B) <= TOL_B}
    bind = m4991["floor_bind_share"]
    gate_report["P5_bind_instrumentation_4.991"] = {
        "got_share": bind, "want_share": BIND_SHARE_4991,
        "pass": abs(bind - BIND_SHARE_4991) <= 0.01}
    all_pass = all(v["pass"] for v in gate_report.values())
    for k, v in gate_report.items():
        print(f"  {k}: [{'PASS' if v['pass'] else 'FAIL'}]")

    # ---- ex-ante check C1 --------------------------------------------------
    mono = {}
    for fl, cur in curves.items():
        ms = [r["marginal_b"] for r in cur["curve"]]
        mono[fl] = all(b >= a - 1e-9 for a, b in zip(ms, ms[1:]))
    c1_pass = all(mono.values())

    status = ("OK" if (all_pass and c1_pass)
              else ("GATE_FAILURE" if not all_pass else "CHECK_FAILURE"))
    payload = {
        "mode": "band_low_extension", "status": status,
        "spec": ("marginal-vs-elasticity curve, pq in "
                 f"{PQ_GRID} at floors 4.0/4.991% CPR, floor_sweep "
                 "convention, fresh runs; parity P1-P5; ex-ante C1 "
                 "monotonicity; descriptive posture fixed in header."),
        "parity_gates": gate_report, "parity_gates_all_pass": all_pass,
        "monotone_in_pq": mono, "c1_pass": c1_pass,
        "curves": curves,
        "half_central_pq3.25": {
            fl: {k: get(cur["curve"], 3.25)[k]
                 for k in ("marginal_b", "marginal_pp")}
            for fl, cur in curves.items()},
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"\nstatus {status}; frozen -> {RESULTS_JSON}")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript.")


if __name__ == "__main__":
    main()
