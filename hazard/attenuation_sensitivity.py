#!/usr/bin/env python3
"""
attenuation_sensitivity.py — survival-selection attenuation of the imported
Rothstein/Liebersohn elasticity (round-28 WP-I3; REVIEW2 / R1-W5: two
transport assumptions travel with the imported coefficient and the paper
names neither; this run prices the second one).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before
first execution; full drafting spec at specs/SPEC_round28_D_F1_I1_I3_J2_S8.md
SPEC I3, whose mapping, grid, gates, tolerances and landing are adopted
unchanged).

WHY. The elasticity in \\eqref{eq:pathB} is a proportional fall in a quarterly
ZIP-code moving probability estimated on a population NOT conditioned on
mortgage survival (tex 253, verbatim), and it is applied to a pool from which
34,734 of 75,000 sampled loans had already prepaid before the window opened
(tex 966). Under unobserved frailty the population-averaged covariate slope
in a depleted pool is ATTENUATED, not amplified. So the direction is signed
ex ante: a < 1, the marginal FALLS, and this is a DOWNWARD member.

ENGINE ENTRY (verified). floor_sweep._run_scored(loans, empirical, floor, pq)
at the two floors, varying p_q_shock_pct ONLY. No hazard patching: the
_ORIG_PREPAY gotcha does NOT bind here (the bind tally is active but harmless
and its column stays meaningful, since the floor is untouched).

THE INVERT-AND-PASS ROUTE (why delta is not scaled directly). microsim_engine
.run_qt_microsim computes beta1 = rothstein_beta1(p_q_shock_pct/100.0), and
literature_hazard.rothstein_beta1 (lines 32-44) is strictly monotone and
invertible on [0, 0.065]. Scaling delta is NOT scaling beta1:
beta1(0.055)/beta1(0.065) = 0.8418 against a delta ratio of 0.8462. For each
target attenuation a this script BISECTS for delta' with
rothstein_beta1(delta') = a * rothstein_beta1(0.065), passes
p_q_shock_pct = 100*delta', and asserts the identity to 1e-12 ON THE VALUE
THE ENGINE ACTUALLY RECOMPUTES, i.e. rothstein_beta1(pq/100.0) — because
(100*d)/100 is not bit-identical to d for every d (realized residuals
1.5e-15 to 4.4e-15, all inside 1e-12). At a = 1 the knob is PINNED to the
production delta 0.065 exactly, so the parity cell is bit-exact by
construction; the solver is still run independently at a = 1 and its
deviation from 0.065 reported (realized 5.3e-15, inside the spec's 1e-12).

THE MAPPING, AND ITS ONE FREE PARAMETER. The manuscript cites lesniewski2026's
selection identity twice (tex 194, 980) and calls its own Path A design "the
estimation counterpart of \\citepos{lesniewski2026} selection identity"
(tex 980). Under the gamma-frailty form of that identity — h_i = Z_i h_0
exp(beta x), Z ~ Gamma(mean 1, variance theta) — the population-averaged
covariate slope is attenuated by 1/(1+theta H_0) and S = (1+theta H_0)^(-1/
theta); eliminating H_0 gives

        a(theta) = S^theta,  S = the pre-window survival share of the pool.

S is MEASURED here: 40,234 / 75,000 = 0.5364533 (tex 966, verbatim: "of the
75,000 sampled loans, 34,734 prepaid and 32 defaulted before the QT window
opens, so 40,234 are active at the June 2022 start"). S is RECOMPUTED in this
script from its two integers, never hard-coded, and the resulting a-grid is
asserted against the drafted spec's literals to 1e-4:
    theta 0     -> a 1.000000  (production; no unobserved heterogeneity)
    theta 0.25  -> a 0.855821  (drafted literal 0.8558)
    theta 0.50  -> a 0.732430  (drafted literal 0.7325 — the drafted table
                                rounds 0.73243 UP; the recomputed value
                                governs, the 1e-4 assertion covers the gap)
    theta 1.00  -> a 0.536453  (unit-CV frailty; attenuation == survival share)
theta is NOT estimable in this design. The only object that speaks to it is
Path A's burnout coefficient, and tex 980 says of it, verbatim: "under both
schemes it is imprecise and not statistically distinguishable from zero, so I
treat it as a control rather than a finding". The run therefore reports a
theta-INDEXED CURVE with the free parameter named and visible, which is
strictly more defensible than an invented 0.8x/0.9x factor.

DESIGN. Cells: a in {1.00, 0.8558, 0.7325, 0.5365} x floors {4.0%, 4.991%},
CENTRAL leg only. The beta1 = 0 null is INVARIANT to a — rothstein_beta1(0)
== 0.0 exactly, asserted at the top on the floor_sweep.py:151 convention — so
each floor needs ONE null, which doubles as its parity cell. 10 engine runs.
Off-window floor consumed at runtime from oos_identification_results.json
headline_oos_marginal.clean_floor_point_pct, asserted == 4.991 to 1e-9
(the floor_form_offwindow convention); never hard-coded.

PARITY GATES (BLOCKING; 1e-6 $B is the bit-exact band, a miss in
(1e-6, 0.01] is a SOFT alarm disclosed and landed, > 0.01 is STOP):
  P1  inversion identity, all four a: |rothstein_beta1(pq/100) - a*beta1_mid|
      < 1e-12; at a = 1, delta' == 0.065 EXACTLY (pinned) and the independent
      solver agrees to 1e-12.                                    [STOP-2]
  P2  null @4.0%    748.1850239867648                            [STOP-1]
  P3  null @4.991%  724.9180585654117                            [STOP-1]
  P4  central a=1 @4.0%    818.5300844066606                     [STOP-2]
  P5  central a=1 @4.991%  767.5264524465003                     [STOP-2]
  P6  bind instrumentation: central@4.0 0.36269282595934704,
      null@4.0 0.14340654639824515, central@4.991 0.6881875607501289,
      n == 1,683,124 on every cell (floor_sweep.py:222-233).
  R1  restoration: lh.INVOLUNTARY_CPR_ANNUAL == 0.04 and lh.FLOOR_MODE ==
      "max" after every cell; nothing patched, so nothing to restore beyond
      what _run_scored's own finally does.

PRE-COMMITTED EXPECTATIONS (SOFT — reported, never blocking). The marginal
responds SUB-proportionally to beta1 under the max form, because attenuating
beta1 raises h_vol and so reduces floor censoring. Local elasticity from the
committed cells: at floor 5.334%, delta 5.5->6.5 moves the marginal
3.8915->4.2657pp for beta1 x1.189 => eps = 0.530; at floor 4.695%,
6.771->7.458 for x1.191 => eps = 0.553. Take eps ~ 0.54. Off-window
predictions from base +5.5716pp:
      a 0.8558 -> +5.12pp (+-0.25)
      a 0.7325 -> +4.71pp (+-0.30)
      a 0.5365 -> +3.98pp (+-0.40)
In-sample (base +9.1985pp) NO point prediction; the pre-committed ordering
check is eps_in-sample > eps_off-window (bind 36.3% vs 68.8% => less
censoring => closer to proportional).

STOP RULES (fixed ex ante):
  STOP-1  null cell at either floor misses its committed value by > $0.01B.
          status GATE_FAILURE; land nothing.
  STOP-2  a = 1.00 central misses its committed value by > $0.01B, OR the
          solved delta' at a = 1.00 is not 6.5 to 1e-12. status
          GATE_FAILURE; land nothing.
  STOP-3  marginal NON-MONOTONE in a at either floor (1e-9 $B tolerance).
          status CHECK_FAILURE; land nothing. A predicted cell outside its
          tolerance band by more than 2x is a SOFT alarm ONLY: report the
          realized eps, land the measured numbers, note the prediction miss.

LANDING RULE (fixed ex ante; every tex landing queues for Eugene):
  PASS -> the attenuation entries land in tab:uncertainty (tex 350-370),
      headline-marginal row. The brief's "new column" does not fit: the
      tabular is p{2.4cm}p{3.3cm}p{4.0cm}p{4.8cm} (tex 351), so a fifth
      column re-wraps the whole table. Two variants, Eugene picks: [posture]
      V1 (RECOMMENDED) append to the headline row's existing "Calibration
         range" cell — "survival-selection attenuation $+5.1$/$+4.7$/$+4.0$pp
         at $a = 0.86/0.73/0.54$, the frailty-identity mapping $a = S^{\\theta}$
         at $S = 40{,}234/75{,}000$ and $\\theta = 0.25/0.5/1$" — plus one
         tablenote giving the identity, the free parameter, and the sign.
      V2 a new \\addlinespace row "Attenuation sensitivity (transport)".
  UNCONDITIONAL (lands whatever the run returns — it is a DISCLOSURE, not a
      result): tex 253 gains the named transport assumption itself, "...and
      one further assumption: the elasticity is estimated on a population not
      conditioned on mortgage survival, and applied to a pool from which
      34,734 of 75,000 sampled loans had already prepaid before the window
      opened. The direction is signed --- attenuation, not amplification ---
      and Table~\\ref{tab:uncertainty} prices it."                [posture]
  NOT IN tab:assembly. [posture] These are a transport sensitivity on an
      IMPORTED coefficient, not a measured correction to this paper's own
      object, and the assembly's credibility rests on that distinction.
      Flagged because WP-I1 branch (a) pulls the other way and a reader will
      line the two up.

MUST NOT CHANGE: literature_hazard.rothstein_beta1; config.ROTHSTEIN_Q_DECLINE_*
and the 5.5-7.7 band's MEANING — the attenuation grid is a DIFFERENT AXIS
from the elasticity band and must never be presented as widening it; the
headline +5.6; [+2.8,+8.7]; the committed delta-band cells; config.py; any
.tex file.

Run:  cd hazard && python3 attenuation_sensitivity.py
      -> data/attenuation_sensitivity_results.json (frozen)
10 engine runs, ~27s each (~4.5 min) plus one macro fetch.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import polars as pl

import floor_sweep as fs
import literature_hazard as lh
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "attenuation_sensitivity_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

TOL = 1e-6          # bit-exact parity band ($B)
TOL_SOFT = 0.01     # (TOL, TOL_SOFT] = soft alarm; above = STOP
TOL_ID = 1e-12      # inversion identity
TOL_F = 1e-9        # floor / monotonicity tolerance

DELTA_MID = 0.065               # config.ROTHSTEIN_Q_DECLINE_MID — production
CENTRAL_PQ = 100.0 * DELTA_MID  # 6.5
NULL_PQ = 0.0
S_NUM, S_DEN = 40234, 75000     # tex 966, verbatim
THETAS = [0.0, 0.25, 0.50, 1.00]
A_GRID_DRAFTED = [1.0, 0.8558, 0.7325, 0.5365]  # drafted spec literals
A_GRID_TOL = 1e-4

ANCHORS = {          # committed, re-verified from the artifacts this session
    (0.04, NULL_PQ): 748.1850239867648,      # no_lockin_null_results.json
    (0.04, CENTRAL_PQ): 818.5300844066606,   # no_lockin_null_results.json
    (0.04991, NULL_PQ): 724.9180585654117,   # floor_form_offwindow max@4.991
    (0.04991, CENTRAL_PQ): 767.5264524465003,
}
BINDS = {(0.04, CENTRAL_PQ): 0.36269282595934704,
         (0.04, NULL_PQ): 0.14340654639824515,
         (0.04991, CENTRAL_PQ): 0.6881875607501289}
BIND_N = 1683124
# reported cross-check only (psa_level_sweep_results.json 4.991|100|0)
BIND_OFFWINDOW_NULL_REF = 0.35785836337667337

BASE_PP = {"4": 9.198459770709789, "4.991": 5.571558182909726}
EPS_REFERENCE = 0.54            # generator of the pre-committed predictions
PRED_OFFWINDOW = {0.25: (5.12, 0.25), 0.50: (4.71, 0.30), 1.00: (3.98, 0.40)}

FREE_PARAMETER_NOTE = (
    "theta is not estimated in this design; the only object that speaks to it "
    "is Path A's burnout coefficient, of which tex 980 says, verbatim: "
    "\"under both schemes it is imprecise and not statistically "
    "distinguishable from zero, so I treat it as a control rather than a "
    "finding\"."
)


def solve_delta_prime(a: float) -> float:
    """Invert rothstein_beta1: return delta' with beta1(delta') = a*beta1(mid).

    rothstein_beta1 is strictly decreasing on [0, DELTA_MID] (0 -> 0.0,
    DELTA_MID -> -0.06857052676484808), so plain bisection is exact to
    machine precision. a == 1.0 is PINNED to the production knob so the
    parity cell is bit-exact by construction (the solver is exercised
    separately at a = 1 by solver_check_at_a1()).
    """
    if a == 1.0:
        return DELTA_MID
    target = a * lh.rothstein_beta1(DELTA_MID)
    lo, hi = 0.0, DELTA_MID
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if lh.rothstein_beta1(mid) - target > 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def solver_check_at_a1() -> float:
    """Run the same bisection at a = 1 over a bracket that does NOT have the
    answer as an endpoint, and return |delta'_solved - 0.065|."""
    target = lh.rothstein_beta1(DELTA_MID)
    lo, hi = 0.0, 2.0 * DELTA_MID
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if lh.rothstein_beta1(mid) - target > 0.0:
            lo = mid
        else:
            hi = mid
    return abs(0.5 * (lo + hi) - DELTA_MID)


def main() -> None:
    t_wall = time.perf_counter()

    # ---- null invariance to a (floor_sweep.py:151 convention) --------------
    assert lh.rothstein_beta1(0.0) == 0.0, (
        "p_q shock 0 must give exactly beta1 = 0 — the null leg's invariance "
        "to the attenuation factor is what licenses one null per floor"
    )
    assert lh.FLOOR_MODE == "max", "production floor form required"
    b1_mid = lh.rothstein_beta1(DELTA_MID)
    assert b1_mid == lh.BETA1_PREPAY_MID

    # ---- the selection identity, recomputed --------------------------------
    S = S_NUM / S_DEN
    a_grid = [S ** th for th in THETAS]
    a_grid_dev = [abs(a - w) for a, w in zip(a_grid, A_GRID_DRAFTED)]
    assert max(a_grid_dev) < A_GRID_TOL, (
        f"recomputed a-grid {a_grid} departs from the drafted literals "
        f"{A_GRID_DRAFTED} by {max(a_grid_dev):.2e} > {A_GRID_TOL}"
    )

    inversion = {}
    for th, a in zip(THETAS, a_grid):
        d = solve_delta_prime(a)
        pq = 100.0 * d
        b1_eff = lh.rothstein_beta1(pq / 100.0)   # what the engine recomputes
        inversion[f"{th:g}"] = {
            "theta": th, "a": a, "a_drafted": A_GRID_DRAFTED[THETAS.index(th)],
            "delta_prime": d, "p_q_shock_pct": pq,
            "beta1_target": a * b1_mid, "beta1_engine": b1_eff,
            "residual": abs(b1_eff - a * b1_mid),
            "pass": abs(b1_eff - a * b1_mid) < TOL_ID,
        }
        print(f"  theta {th:<4g} a {a:.6f}  delta' {d:.15f}  pq {pq:.12f}  "
              f"beta1 {b1_eff:+.10f}  resid {inversion[f'{th:g}']['residual']:.2e}")
    a1_exact = inversion["0"]["delta_prime"] == DELTA_MID
    a1_solver_dev = solver_check_at_a1()
    p1_pass = (all(v["pass"] for v in inversion.values())
               and a1_exact and a1_solver_dev < TOL_ID)
    print(f"  P1 inversion: a=1 delta' exact {a1_exact}, independent solver "
          f"dev {a1_solver_dev:.2e} [{'PASS' if p1_pass else 'FAIL'}]")

    # ---- floors ------------------------------------------------------------
    oos = json.load(open(OOS_ARTIFACT))
    off = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off - 4.991) < TOL_F, f"off-window floor moved: {off}"
    floors = [0.04, off / 100.0]

    print("Shared macro frame (fetched once) ...")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)

    # ---- cells -------------------------------------------------------------
    t0 = time.perf_counter()
    nulls: dict = {}
    cells: dict = {}
    restoration_ok = True
    for floor in floors:
        fk = f"{floor * 100:g}"
        n = fs._run_scored(loans, empirical, floor, NULL_PQ)
        restoration_ok = restoration_ok and (
            abs(lh.INVOLUNTARY_CPR_ANNUAL - 0.04) < TOL_F
            and lh.FLOOR_MODE == "max")
        nulls[fk] = n
        print(f"  floor {fk}% null (beta1=0): ${n['trapped_b']:8.4f}B "
              f"({n['share_pct']:.4f}%)  bind {n['floor_bind_share']:.4f}")
        for th, a in zip(THETAS, a_grid):
            pq = inversion[f"{th:g}"]["p_q_shock_pct"]
            r = fs._run_scored(loans, empirical, floor, pq)
            restoration_ok = restoration_ok and (
                abs(lh.INVOLUNTARY_CPR_ANNUAL - 0.04) < TOL_F
                and lh.FLOOR_MODE == "max")
            r["a"] = a
            r["theta"] = th
            r["delta_prime"] = inversion[f"{th:g}"]["delta_prime"]
            r["null_trapped_b"] = n["trapped_b"]
            r["central_trapped_b"] = r["trapped_b"]
            r["marginal_b"] = r["trapped_b"] - n["trapped_b"]
            r["marginal_pp"] = r["share_pct"] - n["share_pct"]
            cells[f"{fk}|{a:.4f}"] = r
            print(f"    a {a:.4f} (theta {th:g}) pq {pq:.6f}: "
                  f"${r['trapped_b']:8.4f}B  marginal ${r['marginal_b']:+8.4f}B "
                  f"({r['marginal_pp']:+6.3f}pp)  bind {r['floor_bind_share']:.4f}")
    runtime_s = time.perf_counter() - t0

    # ---- parity gates ------------------------------------------------------
    def band(diff: float) -> tuple[bool, bool]:
        """(hard_pass, soft_alarm) on the spec's two-band convention."""
        return diff < TOL, TOL <= diff <= TOL_SOFT

    gates: dict = {"P1_inversion_identity": {
        "cells": inversion, "a1_delta_prime_exact": a1_exact,
        "a1_independent_solver_dev": a1_solver_dev, "pass": p1_pass}}
    soft_alarms: list = []
    stop_hard = False
    for (fl, pq), want in ANCHORS.items():
        fk = f"{fl * 100:g}"
        if pq == NULL_PQ:
            got, name = nulls[fk]["trapped_b"], f"P{2 if fl == 0.04 else 3}_null_{fk}"
        else:
            got, name = cells[f"{fk}|1.0000"]["trapped_b"], \
                f"P{4 if fl == 0.04 else 5}_central_a1_{fk}"
        d = abs(got - want)
        ok, soft = band(d)
        gates[name] = {"got": got, "want": want, "diff": d, "pass": ok,
                       "soft_alarm": soft}
        if soft:
            soft_alarms.append(f"{name} diff {d:.3e} in the ({TOL},{TOL_SOFT}] "
                               "band — upstream float/library drift, disclosed")
        if d > TOL_SOFT:
            stop_hard = True

    def bind_of(fl: float, pq: float) -> dict:
        fk = f"{fl * 100:g}"
        return nulls[fk] if pq == NULL_PQ else cells[f"{fk}|1.0000"]
    p6 = {"n_anchor": BIND_N, "cells": {}, "offwindow_null_share_got":
          nulls[f"{floors[1] * 100:g}"]["floor_bind_share"],
          "offwindow_null_share_ref": BIND_OFFWINDOW_NULL_REF,
          "offwindow_null_reported_only": True}
    p6_ok = True
    for (fl, pq), want in BINDS.items():
        c = bind_of(fl, pq)
        ok = abs(c["floor_bind_share"] - want) < TOL_F and \
            c["floor_bind_loan_months"] == BIND_N
        p6["cells"][f"{fl * 100:g}|{pq:g}"] = {
            "got_share": c["floor_bind_share"], "want_share": want,
            "got_n": c["floor_bind_loan_months"], "pass": ok}
        p6_ok = p6_ok and ok
    p6["pass"] = p6_ok
    gates["P6_bind_instrumentation"] = p6
    gates["R1_restoration"] = {"pass": restoration_ok,
                               "floor_after": lh.INVOLUNTARY_CPR_ANNUAL,
                               "floor_mode_after": lh.FLOOR_MODE}
    all_pass = all(v["pass"] for v in gates.values())
    for k, v in gates.items():
        print(f"  {k}: [{'PASS' if v['pass'] else 'FAIL'}]")

    # ---- monotonicity (STOP-3, hard) ---------------------------------------
    mono: dict = {}
    mono_all = True
    for floor in floors:
        fk = f"{floor * 100:g}"
        ordered = [cells[f"{fk}|{a:.4f}"]["marginal_b"] for a in a_grid]  # a desc
        ok = all(ordered[i] > ordered[i + 1] - TOL_F for i in range(len(ordered) - 1))
        # a_grid runs 1.00 -> 0.5365, so the marginal must FALL along it
        ok = all(ordered[i] - ordered[i + 1] > TOL_F for i in range(len(ordered) - 1))
        mono[fk] = {"a_grid_descending": a_grid,
                    "marginal_b_ordered": ordered,
                    "marginal_pp_ordered": [cells[f"{fk}|{a:.4f}"]["marginal_pp"]
                                            for a in a_grid],
                    "strictly_decreasing_in_falling_a": ok}
        mono_all = mono_all and ok
    mono["all_pass"] = mono_all

    # ---- realized elasticity + prediction check (SOFT) ----------------------
    eps: dict = {}
    for floor in floors:
        fk = f"{floor * 100:g}"
        m1 = cells[f"{fk}|1.0000"]["marginal_b"]
        per_a = {}
        for a in a_grid[1:]:
            ma = cells[f"{fk}|{a:.4f}"]["marginal_b"]
            per_a[f"{a:.4f}"] = (math.log(ma / m1) / math.log(a)
                                 if ma > 0 and m1 > 0 else None)
        vals = [v for v in per_a.values() if v is not None]
        eps[fk] = {"per_a": per_a,
                   "mean": sum(vals) / len(vals) if vals else None,
                   "reference_eps_used_for_predictions": EPS_REFERENCE}
    eps_order_ok = (eps["4"]["mean"] is not None
                    and eps["4.991"]["mean"] is not None
                    and eps["4"]["mean"] > eps["4.991"]["mean"])
    eps["ordering_check_insample_gt_offwindow"] = eps_order_ok

    pred: dict = {}
    pred_soft_miss = []
    fk_off = f"{floors[1] * 100:g}"
    for th, (want_pp, tol_pp) in PRED_OFFWINDOW.items():
        a = S ** th
        got = cells[f"{fk_off}|{a:.4f}"]["marginal_pp"]
        dev = got - want_pp
        inside = abs(dev) <= tol_pp
        outside2x = abs(dev) > 2.0 * tol_pp
        pred[f"{a:.4f}"] = {"theta": th, "a": a, "predicted_pp": want_pp,
                            "tolerance_pp": tol_pp, "realized_pp": got,
                            "deviation_pp": dev, "inside_band": inside,
                            "outside_2x_band": outside2x}
        if outside2x:
            pred_soft_miss.append(
                f"off-window a={a:.4f}: realized {got:+.3f}pp vs predicted "
                f"{want_pp:+.2f}pp (+-{tol_pp}) — SOFT alarm, measured "
                f"numbers land, prediction miss disclosed")
    soft_alarms.extend(pred_soft_miss)
    if not eps_order_ok:
        soft_alarms.append(
            "eps ordering violated (in-sample eps not above off-window eps) — "
            "REPORTED, never reinterpreted")

    # ---- status ------------------------------------------------------------
    if stop_hard or not all_pass:
        status = "GATE_FAILURE"
    elif not mono_all:
        status = "CHECK_FAILURE"
    else:
        status = "OK"

    payload = {
        "mode": "attenuation_sensitivity",
        "status": status,
        "spec": (
            "survival-selection attenuation of the imported elasticity via "
            "the invert-and-pass route: solve delta' with rothstein_beta1"
            "(delta') = a*rothstein_beta1(0.065), pass p_q_shock_pct = "
            "100*delta', assert the identity to 1e-12 on the engine's own "
            "recomputation; a = S^theta from the gamma-frailty selection "
            "identity (lesniewski2026, tex 194/980) at the MEASURED pre-window "
            "survival share S = 40234/75000 (tex 966), theta in {0,.25,.5,1}; "
            "central legs only at floors {4.0%, 4.991% consumed from the oos "
            "artifact}, one null per floor (beta1=0 is invariant to a); "
            "production convention otherwise (75k sample, seed 42, US+Danish "
            "regime tuple, shared macro frame, raw-basis scorer, bind tally); "
            "no hazard patching. Direction SIGNED ex ante: a<1, the marginal "
            "falls, a DOWNWARD member. Predictions off-window from eps~0.54; "
            "non-monotonicity is the only hard check-stop."),
        "selection_identity": {
            "form": "a = S^theta",
            "S_numerator": S_NUM,
            "S_denominator": S_DEN,
            "S": S,
            "ln_S": math.log(S),
            "source": "tex 966",
            "source_quote": (
                "of the 75,000 sampled loans, 34,734 prepaid and 32 defaulted "
                "before the QT window opens, so 40,234 are active at the June "
                "2022 start"),
            "identity_source": "lesniewski2026 selection identity, cited at "
                               "tex 194 and tex 980",
            "theta_grid": THETAS,
            "a_grid": a_grid,
            "a_grid_drafted_literals": A_GRID_DRAFTED,
            "a_grid_max_dev_vs_drafted": max(a_grid_dev),
            "free_parameter_note": FREE_PARAMETER_NOTE,
        },
        "direction_signed_ex_ante": (
            "a < 1 => the marginal falls; this is a DOWNWARD member. It "
            "discharges the second of R1-W5's two unnamed transport "
            "assumptions (the elasticity is a ZIP-level moving probability "
            "estimated on a population not conditioned on mortgage survival, "
            "tex 253, applied to a pool 46.3% depleted before the window)."),
        "floor_provenance": (
            "oos_identification_results.json headline_oos_marginal."
            "clean_floor_point_pct, asserted == 4.991"),
        "parity_gates": gates,
        "parity_gates_all_pass": all_pass,
        "soft_alarms": soft_alarms,
        "nulls": nulls,
        "cells": cells,
        "base_marginal_pp": BASE_PP,
        "realized_elasticity_eps": eps,
        "predicted_vs_realized": pred,
        "monotonicity": mono,
        "not_an_elasticity_band_widening": (
            "The attenuation grid is a DIFFERENT AXIS from the 5.5-7.7 "
            "Rothstein band and must never be presented as widening it."),
        "runtime_s": round(runtime_s, 1),
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
        row = " / ".join(f"{cells[f'{fk}|{a:.4f}']['marginal_pp']:+.3f}"
                         for a in a_grid)
        print(f"  floor {fk}%: marginal_pp at a = "
              f"{'/'.join(f'{a:.4f}' for a in a_grid)}  ->  {row}   "
              f"eps {eps[fk]['mean']:.3f}")
    if soft_alarms:
        print("  SOFT ALARMS (disclosed, not blocking):")
        for s in soft_alarms:
            print(f"    - {s}")
    print(f"frozen -> {RESULTS_JSON}")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript.")


if __name__ == "__main__":
    main()
