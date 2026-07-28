#!/usr/bin/env python3
"""
moving_share_bracket.py — bracketing the construct mismatch: the imported
moving-probability elasticity applied to only a share s of the voluntary
hazard (round-26 panel item B6b; R1-W3 construct-mismatch limb).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before
first execution, artifact committed separately after).

Referee objection (round-26 panel, verified CONFIRMED): the Liebersohn--
Rothstein elasticity is estimated on a MOVING probability, but eq:pathB
applies it to the TOTAL voluntary prepayment hazard (moving + refinancing
+ cash-out), an unsigned specification assumption the manuscript discloses
at its calibration and never prices. This run prices it as a bracket.

DESIGN (fixed ex ante). Variant hazard, patched INSIDE floor_sweep's
instrumentation seam: fs._run_scored installs its bind-tally wrapper over
competing_risks.prepay_hazard, and that wrapper delegates to
floor_sweep._ORIG_PREPAY — so the variant is installed there
(fs._ORIG_PREPAY = mixture) for the s-cells and restored after, keeping
the bind tally live and consistent with the variant hazard. Variant:
    h_vol(s) = h0(t) * exp(beta_x'X + beta_b*burnout)
                     * ((1 - s) + s * exp(-beta1 * 100 * rate_gap))
followed by the production floor combination unchanged (hard maximum at
FLOOR_MODE's production setting; the floor is involuntary turnover and is
NOT scaled by s). s = 1 is algebraically the production hazard; s = 0 is
algebraically the beta1 = 0 null. s is a BRACKETING parameter for the
share of the voluntary hazard that carries the moving elasticity — not an
estimate of the moving share; no loan-purpose field exists in the ingested
data to estimate one (data-granularity ceiling, committed).

Cells (production floor 4.0%, central elasticity 6.5, committed 75k
sample, floor_sweep._run_scored convention, fresh runs):
    null (pq = 0.0)  — the marginal's base, and parity cell P2
    s = 1.00 (mixture code path) — parity cell P1
    s = 0.50 — the bracket's central stress
    s = 0.25 — the deep stress
Reported per cell: trapped $B, share %, marginal over the null ($B, pp).

PARITY GATES (BLOCKING):
  P1  s=1.00 via the MIXTURE code path reproduces the committed central
      $818.530B within +/- $0.01B (no_lockin_null_results.json
      central_trapped_b), and the algebraic identity
      max |h_mixture(s=1) - h_production| < 1e-12 holds on a 10,000-point
      probe grid (rng 42) spanning loan_age 1..360, rate_gap -0.05..+0.01,
      burnout 0..3, fico_z/ltv_z -3..3.
  P2  the null cell reproduces $748.185B within +/- $0.01B
      (null_trapped_b), and max |h_mixture(s=0) - h_production(beta1=0)|
      < 1e-12 on the same probe grid.

EX-ANTE CHECKS AND POSTURE (verbatim; no discretion after the run):
  C1  Bracket ordering: 0 < marginal(0.25) < marginal(0.50) <
      marginal(1.00) within numerical tolerance 1e-9 on $B. A violation is
      a wiring alarm; on FAIL the artifact is committed with status
      CHECK_FAILURE and nothing lands in the manuscript.
  POSTURE: descriptive bracket. The manuscript action on C1-PASS is one
  or two sentences at the calibration's construct-mismatch disclosure
  quoting marginal(0.50) and marginal(0.25) beside the production
  marginal, stating that the mapping assumption is priced by the bracket
  and signed (applying the elasticity to less of the hazard can only
  shrink the marginal). No existing number changes anywhere.

Run:  cd hazard && python3 moving_share_bracket.py
      -> data/moving_share_bracket_results.json  (frozen)
4 engine runs, ~25s each. Does NOT change config.py production defaults.
Does NOT edit any .tex file.
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
RESULTS_JSON = DATA_DIR / "moving_share_bracket_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"

FLOOR = 0.04
CENTRAL_PQ = 6.5
SHARES = [0.25, 0.50, 1.00]
TOL_B = 0.01
PROBE_N = 10_000
PROBE_SEED = 42

_ORIG_PREPAY = competing_risks.prepay_hazard
_share: float = 1.0


def mixture_prepay(loan_age, rate_gap, burnout, fico_z, ltv_z,
                   beta1=lh.BETA1_PREPAY_MID, coefs=None):
    """h_vol with the gap response applied to share _share of the hazard;
    floor combination reproduced from the production form unchanged."""
    b = beta1 if isinstance(beta1, np.ndarray) else float(beta1)
    c = coefs or lh.LITERATURE_COEFS
    h0 = lh.baseline_hazard(loan_age)
    base = np.exp(c["beta_fico"] * fico_z + c["beta_ltv"] * ltv_z
                  + c["beta_burnout"] * burnout)
    m = np.exp((-b) * (np.asarray(rate_gap) * 100.0))
    h_vol = h0 * base * ((1.0 - _share) + _share * m)
    h_floor = lh.cpr_annual_to_monthly_hazard(
        np.full_like(h0, lh.INVOLUNTARY_CPR_ANNUAL, dtype=np.float64))
    if lh.FLOOR_MODE == "additive":
        combined = 1.0 - (1.0 - h_floor) * (1.0 - h_vol)
    else:
        combined = np.maximum(h_floor, h_vol)
    return np.clip(combined, 0.0, 1.0)


def probe_identity() -> dict:
    """max |mixture - production| at s=1 (production beta1) and s=0
    (against production at beta1=0), on a fixed random probe grid."""
    global _share
    rng = np.random.default_rng(PROBE_SEED)
    age = rng.uniform(1, 360, PROBE_N)
    gap = rng.uniform(-0.05, 0.01, PROBE_N)
    burn = rng.uniform(0, 3, PROBE_N)
    fz = rng.uniform(-3, 3, PROBE_N)
    lz = rng.uniform(-3, 3, PROBE_N)
    b1 = lh.rothstein_beta1(CENTRAL_PQ / 100.0)
    _share = 1.0
    d1 = float(np.max(np.abs(
        mixture_prepay(age, gap, burn, fz, lz, beta1=b1)
        - _ORIG_PREPAY(age, gap, burn, fz, lz, beta1=b1))))
    _share = 0.0
    d0 = float(np.max(np.abs(
        mixture_prepay(age, gap, burn, fz, lz, beta1=b1)
        - _ORIG_PREPAY(age, gap, burn, fz, lz, beta1=0.0))))
    _share = 1.0
    return {"max_abs_diff_s1": d1, "max_abs_diff_s0": d0,
            "pass": d1 < 1e-12 and d0 < 1e-12}


def main() -> None:
    global _share
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    with open(NULL_ARTIFACT) as f:
        nl = json.load(f)

    ident = probe_identity()
    print(f"identity probe: s1 {ident['max_abs_diff_s1']:.2e} "
          f"s0 {ident['max_abs_diff_s0']:.2e} "
          f"[{'PASS' if ident['pass'] else 'FAIL'}]")

    print("Shared macro frame (fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    # null: production code path (no patch), pq = 0
    null = fs._run_scored(loans, empirical, FLOOR, 0.0)
    cells: dict = {}
    for s in SHARES:
        _share = s
        # fs._run_scored re-patches competing_risks.prepay_hazard with its
        # bind-tally wrapper, which delegates to fs._ORIG_PREPAY — that is
        # the seam the variant must occupy. Restore BOTH names afterwards
        # (the tally wrapper's finally writes fs._ORIG_PREPAY back into
        # competing_risks.prepay_hazard, so it too holds the mixture then).
        fs._ORIG_PREPAY = mixture_prepay
        try:
            # same (floor, pq) parquet name across shares: each run scores
            # its own freshly written output, and the per-run parquets are
            # regenerable and uncommitted, so overwriting is harmless
            r = fs._run_scored(loans, empirical, FLOOR, CENTRAL_PQ)
        finally:
            fs._ORIG_PREPAY = _ORIG_PREPAY
            competing_risks.prepay_hazard = _ORIG_PREPAY
            _share = 1.0
        r["share_s"] = s
        r["marginal_b"] = r["trapped_b"] - null["trapped_b"]
        r["marginal_pp"] = r["share_pct"] - null["share_pct"]
        cells[f"{s:g}"] = r
        print(f"  s={s:4.2f}: ${r['trapped_b']:7.2f}B "
              f"marginal ${r['marginal_b']:+6.2f}B ({r['marginal_pp']:+5.2f}pp)")

    gate_report = {
        "P1_s1_central": {
            "got": cells["1"]["trapped_b"], "want": nl["central_trapped_b"],
            "identity_probe": ident,
            "pass": (abs(cells["1"]["trapped_b"] - nl["central_trapped_b"])
                     <= TOL_B and ident["pass"])},
        "P2_null": {
            "got": null["trapped_b"], "want": nl["null_trapped_b"],
            "pass": abs(null["trapped_b"] - nl["null_trapped_b"]) <= TOL_B},
    }
    all_pass = all(v["pass"] for v in gate_report.values())
    ms = [cells[f"{s:g}"]["marginal_b"] for s in SHARES]
    c1_pass = (0.0 < ms[0] < ms[1] < ms[2] + 1e-9) if all_pass else False
    for k, v in gate_report.items():
        print(f"  {k}: [{'PASS' if v['pass'] else 'FAIL'}]")
    print(f"  C1 bracket ordering: [{'PASS' if c1_pass else 'FAIL'}]")

    status = ("OK" if (all_pass and c1_pass)
              else ("GATE_FAILURE" if not all_pass else "CHECK_FAILURE"))
    payload = {
        "mode": "moving_share_bracket", "status": status,
        "spec": ("gap response applied to share s of the voluntary hazard, "
                 "floor unscaled, s in {0.25, 0.5, 1.0} + null at production "
                 "floor 4.0% / central 6.5; parity P1 (s=1 mixture vs "
                 "committed central + 1e-12 identity probe) and P2 (null); "
                 "ex-ante C1 bracket ordering; descriptive posture."),
        "parity_gates": gate_report, "parity_gates_all_pass": all_pass,
        "c1_bracket_ordering_pass": c1_pass,
        "null": null, "cells": cells,
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
