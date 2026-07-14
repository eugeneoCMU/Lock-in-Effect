#!/usr/bin/env python3
"""
Floor x elasticity-band cross (pre-registered; spec committed before any run).

Completes the calibration box left open by the floor sweep (floor_sweep.py,
ad52db6/d0ef130): that sweep ran the central elasticity (p_q 6.5) and the
beta1=0 null across seven floors, but the Rothstein band has two more edges
(5.5 / 7.7), and the box maximum for the lock-in marginal is expected at the
(2% floor, 7.7%) corner — the cell the abstract's ceiling sentence needs.

SPEC (fixed ex ante):
- Grid: band edges p_q_shock_pct in {5.5, 7.7} x floors
  {2.0, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0}% annual CPR (14 runs). The central
  (6.5) row and the null rows are NOT rerun: they are committed in
  data/floor_sweep_results.json (d0ef130) and the null is elasticity-
  independent (beta1(0)=0 regardless of the band), so each band cell's
  marginal is scored against the committed same-floor null.
- Machinery: floor_sweep._run_scored reused UNCHANGED (same production
  convention: committed 75k sample, seed 42, US+Danish regime tuple, one
  shared macro frame, raw-basis scoring, bind instrumentation).
- Output: data/floor_band_cross_results.json — a separate artifact; the
  pre-registered floor-sweep artifact is not touched.
- Parity gates (hard-fail): the (4.0%, 5.5) and (4.0%, 7.7) cells must
  reproduce the committed data/extension_risk_band_literature.json values
  ($809.9066B / $827.6583B; that artifact's 6.5 cell is bit-identical to
  the floor sweep's central at 4.0%, so the conventions are known-aligned);
  tolerance +/- $0.01B.
- Ex-ante expectations, with remedy stated before the run:
  (i)  box maximum at the (2.0%, 7.7) corner, roughly 12-14pp of benchmark;
  (ii) within each band row, the marginal decreases monotonically in the
       floor (the floor crowds out the elasticity wherever it binds);
  (iii) at each floor, the marginal increases monotonically in the band
       (5.5 < 6.5 < 7.7).
  If (ii) or (iii) breaks: investigate rather than cite — the artifact is
  flagged investigate_do_not_cite and the violation printed; only the
  parity gates hard-fail the run.

Run:  cd hazard && python3 floor_band_cross.py
      -> data/floor_band_cross_results.json (+ per-run parquets under
         data/floor_sweep/, regenerable, gitignored)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl

import floor_sweep
from config import LOAN_SAMPLE_PATH
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "floor_band_cross_results.json"
SWEEP_ARTIFACT = DATA_DIR / "floor_sweep_results.json"
BAND_ARTIFACT = DATA_DIR / "extension_risk_band_literature.json"

FLOORS = [0.02, 0.03, 0.035, 0.04, 0.045, 0.05, 0.06]
BAND_EDGES = [5.5, 7.7]
CENTRAL_PQ = 6.5
CORNER = (2.0, 7.7)  # expected box maximum (floor %, p_q)
CORNER_EXPECTED_PP = (12.0, 14.0)


def main() -> None:
    with open(SWEEP_ARTIFACT) as f:
        sweep = json.load(f)
    nulls = {
        r["floor_annual_cpr_pct"]: r["null"] for r in sweep["rows"]
    }
    centrals = {
        r["floor_annual_cpr_pct"]: r["central"] for r in sweep["rows"]
    }
    with open(BAND_ARTIFACT) as f:
        band_anchor = json.load(f)["results"]

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    cells = []
    for pq in BAND_EDGES:
        for floor in FLOORS:
            run = floor_sweep._run_scored(loans, empirical, floor, pq)
            fl_pct = floor * 100.0
            null = nulls[fl_pct]
            cell = {
                "floor_annual_cpr_pct": fl_pct,
                "p_q_shock_pct": pq,
                "run": run,
                "lockin_marginal_b": run["trapped_b"] - null["trapped_b"],
                "lockin_marginal_share_pp": (
                    run["share_pct"] - null["share_pct"]
                ),
            }
            cells.append(cell)
            print(
                f"floor {fl_pct:4.1f}%  p_q {pq}:  ${run['trapped_b']:7.1f}B "
                f"({run['share_pct']:6.1f}%)   marginal "
                f"${cell['lockin_marginal_b']:+6.1f}B "
                f"({cell['lockin_marginal_share_pp']:+5.1f}pp)   "
                f"bind {run['floor_bind_share'] * 100:4.1f}%"
            )
    runtime_s = time.perf_counter() - t0

    # ---- Parity gates: (4.0, 5.5) and (4.0, 7.7) vs committed band artifact
    gate_report = {}
    hard_fail = []
    for pq in BAND_EDGES:
        got = next(
            c for c in cells
            if c["floor_annual_cpr_pct"] == 4.0 and c["p_q_shock_pct"] == pq
        )["run"]["trapped_b"]
        want = band_anchor[str(pq)]["trapped_b"]
        ok = abs(got - want) < 0.01
        gate_report[f"trapped_b_4pct_pq{pq}"] = {
            "got": got, "want": want, "pass": bool(ok),
        }
        print(
            f"parity gate (4.0%, {pq}): got {got:.4f} want {want:.4f} "
            f"[{'PASS' if ok else 'FAIL'}]"
        )
        if not ok:
            hard_fail.append(f"(4.0, {pq})")

    # ---- Ex-ante monotonicity checks -----------------------------------------
    violations = []
    for pq in BAND_EDGES:  # (ii) marginal decreasing in floor within each row
        row = [
            c["lockin_marginal_share_pp"] for c in cells
            if c["p_q_shock_pct"] == pq
        ]  # cells appended in FLOORS order
        if not all(a > b for a, b in zip(row, row[1:])):
            violations.append(f"marginal not decreasing in floor at p_q {pq}")
    for floor in FLOORS:  # (iii) marginal increasing in band at each floor
        fl_pct = floor * 100.0
        null = nulls[fl_pct]
        lo = next(
            c["lockin_marginal_share_pp"] for c in cells
            if c["floor_annual_cpr_pct"] == fl_pct
            and c["p_q_shock_pct"] == 5.5
        )
        mid = centrals[fl_pct]["share_pct"] - null["share_pct"]
        hi = next(
            c["lockin_marginal_share_pp"] for c in cells
            if c["floor_annual_cpr_pct"] == fl_pct
            and c["p_q_shock_pct"] == 7.7
        )
        if not (lo < mid < hi):
            violations.append(
                f"marginal not increasing in band at floor {fl_pct}% "
                f"({lo:.2f} / {mid:.2f} / {hi:.2f})"
            )

    # ---- Box maximum ----------------------------------------------------------
    all_marginals = [
        {
            "floor": fl_pct, "p_q": pq,
            "marginal_pp": (
                centrals[fl_pct]["share_pct"] - nulls[fl_pct]["share_pct"]
                if pq == CENTRAL_PQ
                else next(
                    c["lockin_marginal_share_pp"] for c in cells
                    if c["floor_annual_cpr_pct"] == fl_pct
                    and c["p_q_shock_pct"] == pq
                )
            ),
        }
        for fl_pct in [f * 100.0 for f in FLOORS]
        for pq in [5.5, CENTRAL_PQ, 7.7]
    ]
    box_max = max(all_marginals, key=lambda m: m["marginal_pp"])
    corner_hit = (box_max["floor"], box_max["p_q"]) == CORNER
    in_expected = (
        CORNER_EXPECTED_PP[0] <= box_max["marginal_pp"] <= CORNER_EXPECTED_PP[1]
    )
    if not corner_hit:
        violations.append(
            f"box maximum at ({box_max['floor']}%, {box_max['p_q']}), "
            f"not the expected {CORNER}"
        )

    payload = {
        "mode": "floor_band_cross",
        "spec": (
            "band edges {5.5,7.7} x floors {2,3,3.5,4,4.5,5,6}%; central row "
            "and nulls from committed floor_sweep_results.json (d0ef130); "
            "gates vs extension_risk_band_literature.json at the 4% floor; "
            "ex ante: box max at (2%,7.7) ~12-14pp, marginal monotone "
            "decreasing in floor and increasing in band; violations flag "
            "investigate_do_not_cite"
        ),
        "cells": cells,
        "box_marginals_pp": all_marginals,
        "box_max": box_max,
        "box_max_at_expected_corner": bool(corner_hit),
        "box_max_in_expected_range_12_14pp": bool(in_expected),
        "box_ceiling_fraction_of_benchmark": box_max["marginal_pp"] / 100.0,
        "monotonicity_violations": violations,
        "investigate_do_not_cite": bool(violations),
        "parity_gates": gate_report,
        "parity_gates_all_pass": not hard_fail,
        "runtime_s": round(runtime_s, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(
            payload, f, indent=2,
            default=lambda x: float(x)
            if isinstance(x, (np.floating, np.integer)) else x,
        )
        f.write("\n")

    print(
        f"\nbox maximum: {box_max['marginal_pp']:.2f}pp at "
        f"({box_max['floor']}%, p_q {box_max['p_q']}) — "
        f"{'the expected corner' if corner_hit else 'NOT the expected corner'}"
        f"; expected range 12-14pp "
        f"{'hit' if in_expected else 'missed'}"
    )
    for v in violations:
        print(f"EX-ANTE EXPECTATION VIOLATED: {v}")
    if violations:
        print("flagged investigate_do_not_cite — do not cite until diagnosed")
    if hard_fail:
        raise SystemExit(
            f"PARITY GATE FAILURE: {hard_fail} — results written to "
            f"{RESULTS_JSON} for diagnosis but must not be cited"
        )
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
