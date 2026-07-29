#!/usr/bin/env python3
"""
scaled_null_housing_activity.py — the housing-activity-scaled baseline
variant (round-28 WP-J2; REVIEW2 finding #9 / R2-W2: tab:specbox's "Time
effects" row carries no housing-activity term, so the non-rate component of
the 2021-22 mobility collapse is neither modelled nor priced).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before
first execution; full drafting spec at specs/SPEC_round28_D_F1_I1_I3_J2_S8.md
SPEC J2, whose mapping choice, calibration condition, gates, bracket and
landing are adopted unchanged; two labeled deviations and one labeled
addition are stated below).

ENGINE ENTRY (verified in source, re-read this session).
literature_hazard.prepay_hazard:99 calls `baseline_hazard(loan_age)` as a
MODULE-LEVEL name, resolved in literature_hazard's namespace at CALL time;
baseline_hazard:73-76 dispatches to h0_psa(age_months); h0_psa:64 computes
cpr_ann = 0.06*(psa_speed/100)*min(age,30)/30 — LINEAR in psa_speed in
annual-CPR space — before cpr_annual_to_monthly_hazard. Patching the module
attribute literature_hazard.PSA_SPEED does NOT work (the default binds at def
time); patching

    literature_hazard.baseline_hazard = lambda age, mode=None: \\
        lh.h0_psa(age, psa_speed=100.0*phi)

DOES. At phi = 1.0, 100.0*1.0 is exactly config.PSA_SPEED = 100.0, so the
patched call is bit-identical to production and parity is exact BY
CONSTRUCTION — which is why the phi = 1 cells are run PATCHED: they are the
wiring test, not a shortcut around it.

The _ORIG_PREPAY gotcha does NOT bind: nothing patches prepay_hazard itself,
and fs._ORIG_PREPAY and the bind tally both pick the scaled baseline up
automatically. That is correct, and it means the bind column stays meaningful
and WILL move (as expected: a lower h0 is censored by the floor more often).

DISCLOSE: competing_risks.py:148 calls prepay_hazard on the Danish
us_intercept branch too, so the Danish leg simulated in the same run also
carries the scaled baseline. Only the U.S. leg is scored here.

MAPPING OPTIONS — enumerated, one picked (drafted spec's table, verbatim):
  M1 (PICKED) scale h0 (the PSA baseline) by phi in BOTH legs; floor
      untouched. The floor is an EMPIRICAL read of realized turnover on
      deep-discount cohorts (tex 249: "anchored to the same empirical
      observation as the ABM's mobility calibration ... turnover on deeply
      out-of-the-money discount cohorts during 2023--2024"), so it ALREADY
      embeds the non-rate suppression; scaling it would double-count. h0 is
      the PSA convention, a normal-market seasoning ramp with no
      housing-cycle content at all, and is exactly the object R2-W2 says is
      missing a housing-activity term.
  M2  scale the floor only — REJECTED: double-counts the floor's empirical
      content, and the floor is already swept in level (3-5%) and dispersion
      (kappa grid).
  M3  scale the NULL leg only — REJECTED: asymmetric, so central - null is no
      longer a beta1 contrast; it silently changes the estimand.
  M4  scale h0 AND floor — REJECTED: M1 + M2's defect. Stress cell only if
      Eugene asks.

CALIBRATION FROM THE PAPER'S OWN OBJECTS. tex 98 quotes aladangady2024
(verified verbatim): rate-gap lock-in explains 44% of the 2021-22 mobility
decline. The manuscript never converts that share into a magnitude and
carries no external decline magnitude, so phi is calibrated INTERNALLY by
requiring the non-rate channel to produce (0.56/0.44) = 1.272727x as much
trapped liquidity as the rate channel:

  find phi* with  trapped_null(phi*) - trapped_null(1)
                  = 1.272727 * [ trapped_central(1) - trapped_null(1) ]

FEASIBILITY, PRE-COMPUTED (so the run is not started on a hope) — and, since
WP-C3 landed first, MEASURED:
  required lift  in-sample $89.5301B / off-window $54.2289B;
  drafted headroom estimates ~$134B / ~$74B;
  MEASURED lift at phi = 0.75 from the committed psa_level_sweep_results.json
  (PSA 75 == phi 0.75, status OK, all gates PASS): $91.3345B in-sample and
  $54.6777B off-window — both ABOVE their required lifts, so a root exists in
  (0.75, 1.0) at BOTH floors. Root_expected = true, on measured evidence.

DIRECTION, DERIVED (do NOT assert it from the review's wording). Lowering h0
lowers h_vol in BOTH legs. The null is less censored than the central (bind
0.143 vs 0.363 at 4.0%), so the null's trapped balance RISES FASTER than the
central's as phi falls. Therefore marginal(phi) < marginal(1): the corrected
member lies BELOW the headline, and it falls monotonically as phi falls; at
phi -> 0 both legs collapse to the pure floor and the marginal -> 0. The
committed PSA sweep confirms this on realized data (phi 0.75: +3.32pp vs
+9.20pp in-sample; +0.86pp vs +5.57pp off-window).

  ** THE BRIEF'S "SIGNED UPWARD" NEEDS RECONCILING BEFORE ANY WORDING. **
  REVIEW2 finding #9 says "Direction: upward BIAS on the marginal"; PLAN
  WP-J2 says the variant enters the assembly as its "upward-bias entry".
  Both mean: the current marginal is biased upward, so the CORRECTED member
  sits BELOW it. The shorthand "signed upward" reads the opposite way. THE
  MECHANICS SAY DOWN. Manuscript wording must therefore say "documents an
  upward bias; the corrected member lies BELOW the headline" — never "an
  upward member". Eugene signs the sentence; the arithmetic is not
  negotiable.

DESIGN.
  Ladder (always run): phi in {1.00, 0.90, 0.80, 0.70} x legs {null pq 0,
    central pq 6.5} x floors {4.0%, 4.991% consumed from the oos artifact}.
    The phi = 1.00 pair at each floor is the parity cell.
  Root-find: BISECTION on phi in [0.3, 1.0], NULL LEG ONLY per evaluation,
    tolerance $0.05B, MAX 10 iterations; then ONE central run at phi* per
    floor.

  LABELED DEVIATION D1 (bracket seeding). Plain bisection from [0.3, 1.0]
  CANNOT reach the pre-committed $0.05B tolerance in 10 iterations: the
  measured slope is ~$365B per unit phi in-sample (~$219B off-window), and
  0.7/2^10 = 6.8e-4 of phi is ~$0.25B / ~$0.15B of residual. The bracket is
  therefore TIGHTENED FIRST from the ladder's own already-computed null legs
  (largest phi with f>0, smallest with f<0) — zero extra engine runs, a
  strict REFINEMENT of the specified bracket, and it is what makes the
  pre-committed tolerance attainable. If no ladder point gives f > 0, phi =
  0.3 is evaluated explicitly before NO-ROOT is declared. Convergence is
  REPORTED (root.converged + realized residual), never silently assumed.

  LABELED ADDITION X1 (cross-route validation, REPORTED not blocking). WP-C3
  already ran the SAME physical perturbation (PSA 75 == phi 0.75) through a
  DIFFERENT patch route — psa_level_sweep's make_psa_prepay, a reimplemented
  hazard installed at fs._ORIG_PREPAY. This script adds phi = 0.75 to the
  ladder (4 runs) and compares all four cells to the committed artifact. The
  two routes are NOT bit-identical by construction — production computes
  h0*exp(A+B), psa_level_sweep computes h0*exp(B)*exp(A) — so the check is
  soft: report the diff, alarm above $0.01B. Agreement validates BOTH
  constructions; disagreement is the single most informative wiring signal
  available this round. Set CROSS_ROUTE = False to drop it.

PARITY GATES (BLOCKING, bit-exact 1e-9 $B — STOP-1 is "miss by anything at
all", because at phi = 1 the patch MUST be a no-op):
  P1  phi=1 null @4.0%       748.1850239867648
  P2  phi=1 central @4.0%    818.5300844066606
  P3  phi=1 null @4.991%     724.9180585654117
  P4  phi=1 central @4.991%  767.5264524465003
  P5  phi=1 baseline identity probe: max|patched(age) - lh.h0_psa(age)| over
      age 0..360 == 0.0 EXACTLY (and == 0.0 against lh.baseline_hazard too).
  P6  bind anchors at phi=1: central@4.0 0.36269282595934704, null@4.0
      0.14340654639824515, central@4.991 0.6881875607501289, n == 1,683,124.
  P7  RESTORATION: lh.baseline_hazard IS the original function object after
      every cell and at exit; lh.INVOLUNTARY_CPR_ANNUAL == 0.04;
      lh.PSA_SPEED == 100.0; lh.FLOOR_MODE == "max"; lh.BASELINE_MODE ==
      "psa". (config.PSA_SPEED is never touched — the speed is passed
      explicitly per cell.)

DIRECTION CHECKS (pre-committed):
  monotone            marginal_pp strictly increasing in phi at each floor.
  all_below_production marginal(phi) < marginal(1) for every phi < 1,
                      including phi*.

LANDING RULE (fixed ex ante; every tex landing queues for Eugene).
  PASS (parity exact, root found at both floors, monotone) ->
    - tab:assembly (tex 313-334) gains a row:
      "Housing-activity-scaled baseline (Aladangady-anchored) | $+X.X$ |
       below | scaled-null variant; upward-bias entry
       (run \\texttt{scaled\\_null\\_housing\\_activity})".
    - tex 312 (the §V.C assembly paragraph) gains one sentence naming
      Aladangady's 44% as the anchor and the calibration condition as the
      mapping.
    - tex 98 gains a forward reference (the citation is currently catalogued
      and never used; R2's optional-dimension score dropped 11 points on
      exactly this).
    - tab:specbox "Time effects" gains the disclosure that the omitted
      housing-activity term is PRICED by this variant rather than modelled.
    - REQUIRED WORDING: "documents an upward bias; the corrected member lies
      BELOW the headline". Never "an upward member".
    [posture] WHOLE ITEM. This adds a member to tab:assembly, which is the
    object the retired-posture decision rests on (PLAN Decision record item
    1). Direction and wording drafted; Eugene signs.
  NO-ROOT (the calibration condition has no solution in phi in [0.3,1.0]) ->
    land the LADDER ONLY, as a sensitivity rather than a calibrated member:
    "scaling the seasoning baseline by 10/20/30% moves the marginal to
    $+X/+Y/+Z$ points", with the statement that the Aladangady share cannot
    be mapped into this design's units without an external decline
    magnitude. NO assembly row.                                  [posture]
  STOP-1  any phi = 1.00 cell misses its committed value by ANYTHING (1e-9):
    the baseline_hazard patch is not a no-op at phi = 1, i.e. the wiring is
    wrong. status GATE_FAILURE; land nothing.
  STOP-2  marginal non-monotone in phi, OR marginal(phi) > marginal(1) at any
    phi < 1: contradicts the derived direction, so the construction is not
    what was specified. status CHECK_FAILURE; land nothing.

BONUS / DUPLICATION NOTE: this construction is mechanically the PSA level
sweep WP-C3 wants. WP-C3 has ALREADY RUN (psa_level_sweep_results.json,
status OK). This script is therefore NOT a second implementation of that
sweep — it is the Aladangady-calibrated variant, and it reuses C3's output
only as the X1 cross-route check and the feasibility evidence above.

MUST NOT CHANGE: config.PSA_SPEED (stays 100); literature_hazard.h0_psa and
literature_hazard.baseline_hazard (patch and restore, NEVER edit); the floor
at either calibration; delta = 6.5; the headline +5.6; the committed null
values (they are the phi = 1 parity targets); tab:specbox's estimator
description (only its disclosure column gains a clause); config.py; any .tex
file.

Run:  cd hazard && python3 scaled_null_housing_activity.py
      -> data/scaled_null_housing_activity_results.json (frozen)
20 ladder runs + <=10 bisection nulls per floor + 2 centrals at phi*
(<= 42 engine runs, ~27s each, ~19 min) plus one macro fetch.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl

import floor_sweep as fs
import literature_hazard as lh
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "scaled_null_housing_activity_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
PSA_ARTIFACT = DATA_DIR / "psa_level_sweep_results.json"   # X1 only

TOL = 1e-9          # bit-exact parity ($B) — STOP-1 is any miss
TOL_X = 0.01        # X1 cross-route soft alarm band ($B)
CENTRAL_PQ = 6.5
NULL_PQ = 0.0

PHIS = [1.00, 0.90, 0.80, 0.70]
CROSS_ROUTE = True
XROUTE_PHI = 0.75

RATE_SHARE, NON_RATE_SHARE = 0.44, 0.56        # aladangady2024, tex 98
RATIO = NON_RATE_SHARE / RATE_SHARE            # 1.2727272727272727
RATIO_SPEC = 1.272727                          # drafted literal
BISECT_LO, BISECT_HI = 0.30, 1.00
ROOT_TOL_B = 0.05
MAX_ITERS = 10

ANCHORS = {(0.04, NULL_PQ): 748.1850239867648,
           (0.04, CENTRAL_PQ): 818.5300844066606,
           (0.04991, NULL_PQ): 724.9180585654117,
           (0.04991, CENTRAL_PQ): 767.5264524465003}
BINDS = {(0.04, CENTRAL_PQ): 0.36269282595934704,
         (0.04, NULL_PQ): 0.14340654639824515,
         (0.04991, CENTRAL_PQ): 0.6881875607501289}
BIND_N = 1683124
COMMITTED_MARGINAL_B = {"4": 70.34506041989584, "4.991": 42.60839388108866}
HEADROOM_DRAFTED_B = {"4": 134.0, "4.991": 74.0}
# X1 pins (psa_level_sweep_results.json, PSA 75 == phi 0.75)
XROUTE_PINS = {("4", NULL_PQ): 839.519553750622,
               ("4", CENTRAL_PQ): 864.9304552633807,
               ("4.991", NULL_PQ): 779.5957537746586,
               ("4.991", CENTRAL_PQ): 786.1422706212454}

CALIBRATION_CONDITION = (
    "find phi* such that trapped_null(phi*) - trapped_null(1) = "
    "(0.56/0.44) * [ trapped_central(1) - trapped_null(1) ]")

_ORIG_BASELINE = lh.baseline_hazard


def scaled_baseline(phi: float):
    """M1: scale the PSA seasoning ramp by phi. Resolved in literature_hazard's
    namespace at call time, so prepay_hazard picks it up; the floor is
    UNTOUCHED (M2/M4 rejected)."""
    return lambda age, mode=None: lh.h0_psa(age, psa_speed=100.0 * phi)


def run_cell(loans, empirical, floor: float, pq: float, phi: float) -> dict:
    """One scored microsim under the phi-scaled baseline, restored in finally."""
    lh.baseline_hazard = scaled_baseline(phi)
    try:
        r = fs._run_scored(loans, empirical, floor, pq)
    finally:
        lh.baseline_hazard = _ORIG_BASELINE
    r["phi"] = phi
    r["psa_speed_effective"] = 100.0 * phi
    r["null_mean_cpr_pct"] = r["mean_us_cpr_pct"]
    return r


def restoration_ok() -> bool:
    return (lh.baseline_hazard is _ORIG_BASELINE
            and abs(lh.INVOLUNTARY_CPR_ANNUAL - 0.04) < TOL
            and lh.PSA_SPEED == 100.0
            and lh.FLOOR_MODE == "max"
            and lh.BASELINE_MODE == "psa")


def main() -> None:
    t_wall = time.perf_counter()
    assert lh.rothstein_beta1(0.0) == 0.0
    assert abs(RATIO - RATIO_SPEC) < 1e-6, "ratio drifted from the drafted 1.272727"

    # ---- P5: baseline identity probe at phi = 1 (before any run) -----------
    age = np.arange(0, 361, dtype=np.float64)
    patched1 = scaled_baseline(1.0)
    p5_vs_h0 = float(np.max(np.abs(patched1(age) - lh.h0_psa(age))))
    p5_vs_base = float(np.max(np.abs(patched1(age) - _ORIG_BASELINE(age))))
    p5_pass = (p5_vs_h0 == 0.0 and p5_vs_base == 0.0)
    print(f"P5 baseline identity at phi=1: vs h0_psa {p5_vs_h0:.1e}, "
          f"vs baseline_hazard {p5_vs_base:.1e} [{'PASS' if p5_pass else 'FAIL'}]")

    # ---- floors ------------------------------------------------------------
    oos = json.load(open(OOS_ARTIFACT))
    off = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off - 4.991) < TOL, f"off-window floor moved: {off}"
    floors = [0.04, off / 100.0]

    # ---- feasibility precheck (before any engine run) ----------------------
    xr_committed = {}
    if PSA_ARTIFACT.exists():
        psa = json.load(open(PSA_ARTIFACT))
        for fk in ("4", "4.991"):
            for pq in (NULL_PQ, CENTRAL_PQ):
                xr_committed[(fk, pq)] = \
                    psa["cells"][f"{fk}|75|{pq:g}"]["trapped_b"]
    precheck = {}
    for fk in ("4", "4.991"):
        req = RATIO * COMMITTED_MARGINAL_B[fk]
        meas = (xr_committed.get((fk, NULL_PQ), None))
        lift075 = (meas - ANCHORS[(0.04 if fk == "4" else 0.04991, NULL_PQ)]
                   if meas is not None else None)
        precheck[fk] = {
            "required_lift_b": req,
            "headroom_estimate_b": HEADROOM_DRAFTED_B[fk],
            "measured_lift_at_phi_0p75_b": lift075,
            "measured_lift_source": "psa_level_sweep_results.json (PSA 75)",
            "root_expected": True,
            "root_bracketed_by_measurement": (
                lift075 is not None and lift075 > req)}
        print(f"feasibility floor {fk}%: required lift ${req:.4f}B, measured "
              f"lift at phi=0.75 "
              f"{'$%.4fB' % lift075 if lift075 is not None else 'n/a'} -> "
              f"root {'BRACKETED' if precheck[fk]['root_bracketed_by_measurement'] else 'expected'}")

    print("Shared macro frame (fetched once) ...")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    ladder_phis = sorted(set(PHIS + ([XROUTE_PHI] if CROSS_ROUTE else [])),
                         reverse=True)
    ladder: dict = {}
    null_cache: dict = {}          # (floor_key, phi) -> trapped_b
    resto = True

    for floor in floors:
        fk = f"{floor * 100:g}"
        for phi in ladder_phis:
            n = run_cell(loans, empirical, floor, NULL_PQ, phi)
            resto = resto and restoration_ok()
            c = run_cell(loans, empirical, floor, CENTRAL_PQ, phi)
            resto = resto and restoration_ok()
            null_cache[(fk, round(phi, 12))] = n
            row = {
                "phi": phi, "psa_speed_effective": 100.0 * phi,
                "null_trapped_b": n["trapped_b"],
                "central_trapped_b": c["trapped_b"],
                "null_share_pct": n["share_pct"],
                "central_share_pct": c["share_pct"],
                "marginal_b": c["trapped_b"] - n["trapped_b"],
                "marginal_pp": c["share_pct"] - n["share_pct"],
                "null_mean_cpr_pct": n["mean_us_cpr_pct"],
                "central_mean_cpr_pct": c["mean_us_cpr_pct"],
                "floor_bind_share": c["floor_bind_share"],
                "floor_bind_share_null": n["floor_bind_share"],
                "floor_bind_loan_months": c["floor_bind_loan_months"],
                "cross_route_cell": bool(CROSS_ROUTE and phi == XROUTE_PHI),
            }
            ladder[f"{fk}|{phi:g}"] = row
            print(f"  floor {fk}% phi {phi:4.2f} (PSA {100*phi:g}): "
                  f"null ${n['trapped_b']:8.4f}B central ${c['trapped_b']:8.4f}B "
                  f"marginal ${row['marginal_b']:+8.4f}B "
                  f"({row['marginal_pp']:+6.3f}pp) bind {row['floor_bind_share']:.4f}")

    # ---- parity gates ------------------------------------------------------
    gates: dict = {}
    for (fl, pq), want in ANCHORS.items():
        fk = f"{fl * 100:g}"
        got = ladder[f"{fk}|1"]["null_trapped_b" if pq == NULL_PQ
                                else "central_trapped_b"]
        idx = {(0.04, NULL_PQ): "P1", (0.04, CENTRAL_PQ): "P2",
               (0.04991, NULL_PQ): "P3", (0.04991, CENTRAL_PQ): "P4"}[(fl, pq)]
        gates[f"{idx}_phi1_{fk}_{pq:g}"] = {
            "got": got, "want": want, "diff": abs(got - want),
            "pass": abs(got - want) < TOL}
    gates["P5_baseline_identity"] = {
        "max_abs_vs_h0_psa": p5_vs_h0, "max_abs_vs_baseline_hazard": p5_vs_base,
        "age_grid": "0..360", "pass": p5_pass}
    p6 = {"n_anchor": BIND_N, "cells": {}}
    p6_ok = True
    for (fl, pq), want in BINDS.items():
        fk = f"{fl * 100:g}"
        row = ladder[f"{fk}|1"]
        got = row["floor_bind_share_null"] if pq == NULL_PQ else row["floor_bind_share"]
        ok = abs(got - want) < TOL and row["floor_bind_loan_months"] == BIND_N
        p6["cells"][f"{fk}|{pq:g}"] = {"got": got, "want": want, "pass": ok}
        p6_ok = p6_ok and ok
    p6["pass"] = p6_ok
    gates["P6_bind_anchors"] = p6
    gates["P7_restoration"] = {
        "baseline_hazard_is_original": lh.baseline_hazard is _ORIG_BASELINE,
        "floor_after": lh.INVOLUNTARY_CPR_ANNUAL, "psa_speed": lh.PSA_SPEED,
        "floor_mode": lh.FLOOR_MODE, "baseline_mode": lh.BASELINE_MODE,
        "pass": resto and restoration_ok()}
    all_pass = all(v["pass"] for v in gates.values())
    for k, v in gates.items():
        print(f"  {k}: [{'PASS' if v['pass'] else 'FAIL'}]")

    # ---- X1 cross-route check (REPORTED, not blocking) ---------------------
    xroute = {"enabled": bool(CROSS_ROUTE), "phi": XROUTE_PHI,
              "committed_source": "psa_level_sweep_results.json (PSA 75)",
              "bit_exact_not_expected": (
                  "production computes h0*exp(A+B); psa_level_sweep's "
                  "make_psa_prepay computes h0*exp(B)*exp(A) — the routes are "
                  "algebraically identical, not IEEE-754 identical"),
              "cells": {}, "max_abs_diff_b": None, "alarm": False}
    if CROSS_ROUTE and xr_committed:
        diffs = []
        for fk in ("4", "4.991"):
            row = ladder[f"{fk}|{XROUTE_PHI:g}"]
            for pq, key in ((NULL_PQ, "null_trapped_b"),
                            (CENTRAL_PQ, "central_trapped_b")):
                want = xr_committed[(fk, pq)]
                pin = XROUTE_PINS[(fk, pq)]
                d = abs(row[key] - want)
                diffs.append(d)
                xroute["cells"][f"{fk}|{pq:g}"] = {
                    "got": row[key], "want_committed": want, "pin": pin,
                    "provenance_pin_ok": abs(want - pin) < TOL, "diff_b": d}
        xroute["max_abs_diff_b"] = max(diffs)
        xroute["alarm"] = max(diffs) > TOL_X
        print(f"  X1 cross-route (phi {XROUTE_PHI} vs committed PSA 75): "
              f"max |diff| ${max(diffs):.3e}B "
              f"[{'ALARM' if xroute['alarm'] else 'CONSISTENT'}]")
    elif CROSS_ROUTE:
        xroute["skipped_reason"] = "psa_level_sweep_results.json absent"

    # ---- root-find ---------------------------------------------------------
    def null_row(floor: float, fk: str, phi: float) -> dict:
        key = (fk, round(phi, 12))
        if key not in null_cache:
            null_cache[key] = run_cell(loans, empirical, floor, NULL_PQ, phi)
        return null_cache[key]

    root: dict = {}
    no_root = False
    for floor in floors:
        fk = f"{floor * 100:g}"
        base_null = ladder[f"{fk}|1"]["null_trapped_b"]
        required = RATIO * (ladder[f"{fk}|1"]["central_trapped_b"] - base_null)

        def f_of(phi: float) -> float:
            return (null_row(floor, fk, phi)["trapped_b"] - base_null) - required

        # D1: tighten the drafted [0.3, 1.0] bracket from the ladder's own nulls
        lo, hi = BISECT_LO, BISECT_HI
        for phi in sorted(null_cache_phis(null_cache, fk)):
            v = f_of(phi)
            if v > 0.0 and phi > lo:
                lo = phi
            if v < 0.0 and phi < hi:
                hi = phi
        if lo == BISECT_LO and f_of(BISECT_LO) <= 0.0:
            no_root = True
            root[fk] = {"phi_star": None, "iterations": 0, "residual_b": None,
                        "no_root": True, "required_lift_b": required,
                        "bracket": [BISECT_LO, BISECT_HI],
                        "note": "f(0.3) <= 0: the calibration condition has no "
                                "solution in the pre-committed bracket"}
            print(f"  floor {fk}%: NO ROOT in [{BISECT_LO}, {BISECT_HI}]")
            continue

        it, resid, phi_star = 0, f_of(hi), hi
        converged = False
        for it in range(1, MAX_ITERS + 1):
            phi_star = 0.5 * (lo + hi)
            resid = f_of(phi_star)
            resto = resto and restoration_ok()
            print(f"    bisect {fk}% it {it:2d}: phi {phi_star:.6f} "
                  f"residual ${resid:+8.4f}B  bracket [{lo:.6f}, {hi:.6f}]")
            if abs(resid) <= ROOT_TOL_B:
                converged = True
                break
            if resid > 0.0:
                lo = phi_star
            else:
                hi = phi_star
        c = run_cell(loans, empirical, floor, CENTRAL_PQ, phi_star)
        resto = resto and restoration_ok()
        n_star = null_row(floor, fk, phi_star)
        root[fk] = {
            "phi_star": phi_star, "psa_speed_effective": 100.0 * phi_star,
            "iterations": it, "residual_b": resid, "converged": converged,
            "tolerance_b": ROOT_TOL_B, "max_iters": MAX_ITERS,
            "bracket_final": [lo, hi],
            "bracket_drafted": [BISECT_LO, BISECT_HI],
            "bracket_seeded_from_ladder": True,
            "required_lift_b": required,
            "realized_lift_b": n_star["trapped_b"] - base_null,
            "null_trapped_b": n_star["trapped_b"],
            "central_trapped_b": c["trapped_b"],
            "null_mean_cpr_pct": n_star["mean_us_cpr_pct"],
            "marginal_b": c["trapped_b"] - n_star["trapped_b"],
            "marginal_pp": c["share_pct"] - n_star["share_pct"],
            "floor_bind_share": c["floor_bind_share"],
            "no_root": False}

        print(f"  floor {fk}%: phi* {phi_star:.6f} (PSA {100*phi_star:.4f}) "
              f"marginal ${root[fk]['marginal_b']:+.4f}B "
              f"({root[fk]['marginal_pp']:+.3f}pp) "
              f"residual ${resid:+.4f}B converged {converged}")

    # ---- direction checks --------------------------------------------------
    direction = {"per_floor": {}}
    mono_all, below_all = True, True
    asc = sorted(ladder_phis)
    for floor in floors:
        fk = f"{floor * 100:g}"
        ms = [ladder[f"{fk}|{p:g}"]["marginal_pp"] for p in asc]
        mono = all(ms[i] < ms[i + 1] - 1e-9 for i in range(len(ms) - 1))
        m1 = ladder[f"{fk}|1"]["marginal_pp"]
        below = all(ladder[f"{fk}|{p:g}"]["marginal_pp"] < m1
                    for p in asc if p < 1.0)
        if root.get(fk, {}).get("marginal_pp") is not None:
            below = below and root[fk]["marginal_pp"] < m1
        direction["per_floor"][fk] = {
            "phi_ascending": asc, "marginal_pp_ordered": ms,
            "marginal_pp_at_phi1": m1, "monotone": mono,
            "all_below_production": below}
        mono_all, below_all = mono_all and mono, below_all and below
    direction["monotone"] = mono_all
    direction["all_below_production"] = below_all

    if not all_pass:
        status = "GATE_FAILURE"
    elif not (mono_all and below_all):
        status = "CHECK_FAILURE"
    elif no_root:
        status = "NO_ROOT"
    else:
        status = "OK"

    payload = {
        "mode": "scaled_null_housing_activity",
        "status": status,
        "spec": (
            "M1 mapping (PICKED): scale the PSA seasoning baseline h0 by phi "
            "in BOTH legs via lh.baseline_hazard = lambda age, mode=None: "
            "lh.h0_psa(age, psa_speed=100*phi), floor UNTOUCHED. The floor is "
            "an empirical read of realized deep-discount turnover (tex 249) "
            "and already embeds the non-rate suppression, so scaling it would "
            "double-count; h0 is the PSA convention with no housing-cycle "
            "content and is exactly the object R2-W2 says is missing. "
            "REJECTED: M2 scale the floor only (double-counts the floor's "
            "empirical content; already swept in level 3-5% and dispersion "
            "kappa); M3 scale the null leg only (asymmetric, so central-null "
            "is no longer a beta1 contrast — it silently changes the "
            "estimand); M4 scale h0 AND floor (M1+M2's defect; stress cell "
            "only on request). Ladder phi {1,.9,.8,.7} (+0.75 cross-route) x "
            "paired legs x floors {4.0%, 4.991% from the oos artifact}; "
            "phi=1 cells run PATCHED and are the wiring test (bit-exact by "
            "construction, 100.0*1.0 == config.PSA_SPEED). Root: bisection "
            "on phi, null leg only, tol $0.05B, <=10 iters, bracket seeded "
            "from the ladder (labeled deviation D1). Danish us_intercept "
            "branch (competing_risks.py:148) also carries the scaled "
            "baseline; only the U.S. leg is scored."),
        "anchor": {"source": "aladangady2024, tex 98", "rate_share": RATE_SHARE,
                   "non_rate_share": NON_RATE_SHARE, "ratio": RATIO,
                   "ratio_drafted_literal": RATIO_SPEC,
                   "tex_98_claim": ("rate-gap-driven lock-in explains only 44% "
                                    "of the actual decline in mortgage "
                                    "borrower mobility between 2021 and 2022")},
        "calibration_condition": CALIBRATION_CONDITION,
        "feasibility_precheck": precheck,
        "floor_provenance": ("oos_identification_results.json "
                             "headline_oos_marginal.clean_floor_point_pct, "
                             "asserted == 4.991"),
        "parity_gates": gates,
        "parity_gates_all_pass": all_pass,
        "cross_route_check_x1": xroute,
        "ladder": ladder,
        "root": root,
        "direction_check": {"monotone": mono_all,
                            "all_below_production": below_all,
                            "detail": direction},
        "direction_reconciliation": (
            "The mechanics say DOWN. Lowering h0 lowers h_vol in both legs; "
            "the null is less censored than the central (bind 0.143 vs 0.363 "
            "at 4.0%), so the null's trapped balance rises faster and "
            "marginal(phi) < marginal(1). REVIEW2 #9's 'upward bias' and "
            "PLAN WP-J2's 'upward-bias entry' both mean the CURRENT marginal "
            "is biased upward, so the corrected member sits BELOW it. "
            "Manuscript wording must say: 'documents an upward bias; the "
            "corrected member lies BELOW the headline' — never 'an upward "
            "member'."),
        "runtime_s": round(time.perf_counter() - t0, 1),
        "wall_s": round(time.perf_counter() - t_wall, 1),
    }

    def _np(o):
        if hasattr(o, "item"):
            return o.item()
        raise TypeError(f"not serializable: {type(o)}")

    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_np)
        f.write("\n")

    print(f"\nstatus {status}")
    for fk in ("4", "4.991"):
        r = root.get(fk, {})
        print(f"  floor {fk}%: ladder marginal_pp "
              + " / ".join(f"{ladder[f'{fk}|{p:g}']['marginal_pp']:+.3f}"
                           for p in sorted(ladder_phis))
              + (f"   phi* {r['phi_star']:.6f} -> {r['marginal_pp']:+.3f}pp"
                 if r.get("phi_star") else "   phi* NONE"))
    assert lh.baseline_hazard is _ORIG_BASELINE, "baseline_hazard NOT restored"
    print(f"frozen -> {RESULTS_JSON}")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript "
                         "(NO_ROOT lands the ladder only, per the branch map).")


def null_cache_phis(cache: dict, fk: str) -> list:
    return [p for (k, p) in cache.keys() if k == fk]


if __name__ == "__main__":
    main()
