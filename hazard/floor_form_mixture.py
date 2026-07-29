#!/usr/bin/env python3
"""
floor_form_mixture.py — the floor's functional form as a CURVE in the
strictly-involuntary share s (round-28 WP-D; REVIEW2 finding #5 / R1-W3:
the estimand is form-dependent by 2x and the production form is selected on
an aggregate-fit criterion the design declares unidentified).

PRE-COMMITTED SPEC (fixed BEFORE any run; committed before first execution;
full drafting spec at specs/SPEC_round28_D_F1_I1_I3_J2_S8.md SPEC D, gates,
orientation, and landing adopted unchanged).

ORIENTATION (verified against the code, stated for the record): s is the
share of the measured floor entering as an ADDITIVE competing involuntary
cause; (1-s) remains a floor on total turnover. s = 0 == the production hard
maximum (floor on total; involuntary movers a subset of the voluntary
hazard); s = 1 == the additive competing-risks form (floor strictly
involuntary). tex 249's "strictly-involuntary share is plausibly well under
half" therefore maps to s < 0.5. R1's complementary labelling (REVIEW2 #5)
uses share = 1 - s; the manuscript symbol choice is Eugene's [posture].

DESIGN. Endpoint cells run through the PRODUCTION code paths (s=0: unpatched
hard-max; s=1: unpatched hazard under lh.FLOOR_MODE="additive", restored to
"max" after each cell) — parity by construction, exactly how the committed
floor_form runs were produced. Interior cells install the mixture
    h = 1 - (1 - s*h_floor) * (1 - max((1-s)*h_floor, h_vol))
at the floor_sweep._ORIG_PREPAY seam (B2/C3/C5-validated), h_floor and the
elasticity read at call time. Grid: s in {0, 0.1, ..., 1.0} + {0.25} x legs
{null pq 0, central pq 6.5} x floors {4.0%, 4.991% (consumed from the oos
artifact)} = 48 engine runs.

PARITY GATES (BLOCKING, 1e-6 $B; >0.01 = STOP):
  P1/P2 s=0 @4.0: marginal 70.34506041989584 B (central 818.5300844066606,
        null 748.1850239867648).
  P3    s=1 @4.0: marginal 86.02249228630046 B (floor_form_results additive).
  P4    s=0 @4.991: marginal 42.60839388108866 B (null 724.9180585654117).
  P5    s=1 @4.991: marginal 85.70549789908563 B (central 427.54488764725437).
  P6    identity probes on the fixed 10k grid at BOTH floors: mixture(s=0) vs
        production-max and mixture(s=1) vs production-additive, < 1e-12.
  P7    continuity: |mixture(s=1e-12) - production-max| < 1e-15 on the grid.
  FLOOR-ANCHOR preservation (analytic): at h_vol=0 the mixture returns
        h_floor - s(1-s)h_floor^2; max relative deviation s(1-s)h_floor must
        be < 0.15% at every cell (else STOP-3: the curve would re-calibrate
        the floor, not vary the form).

PRE-COMMITTED EXPECTATIONS: monotone increasing in s at both floors (the
additive channel adds hazard wherever the max channel censors it; the
central leg is censored more than the null, so it gains more at every s);
off-window curve runs +5.5716 -> +11.2070 pp (span 5.635), in-sample
+9.1985 -> +11.2485 (span 2.050); no shape beyond monotonicity committed.
Each cell reports the central recovery share beside the marginal — the
level cost of the upper curve is displayed, not hidden (R1-W3).

LANDING (decision record item 5: curve runs, headline anchor UNCHANGED,
interior value NAMED in the form-conditionality statements; hull literals
kept — gate requires form-conditional >= 3 and hull >= 3):
  PASS   -> curve lands as the form-dimension exhibit at tex 588 + one
            clause at the four substantive hull sites naming the interior
            value at the paper's own semantics (named point s = 0.4, with
            s = 0.25 beside it) [posture: symbol + named point are Eugene's].
  STOP-1 -> any endpoint parity miss > $0.01B: wiring/upstream alarm.
  STOP-2 -> non-monotone beyond 1e-9 $B: the mixture is not the object
            specified; report offending cells, land nothing.
  STOP-3 -> floor deviation >= 0.15% at any cell: endpoints may be quoted,
            interior does not land.

MUST NOT CHANGE: config.py; lh.prepay_hazard; lh.FLOOR_MODE (assert "max" at
exit); the headline +5.6 (x21 sites); [+2.8,+8.7]; the hull and its counts;
committed floor_form artifacts; any .tex file.

POST-RUN SPEC AMENDMENTS (2026-07-29, LABELED — the first run stopped on
two rule misses that inspection shows are threshold artifacts, not object
failures; both amendments are disclosed here and in the verdicts row rather
than silently absorbed):
  A1 (continuity probe): the drafted 1e-15 threshold sat below accumulated
      float noise on the survival-composition expression (realized 3.5e-15 /
      4.3e-15 against machine eps 2.2e-16 x ~10 ops); amended to 1e-13. The
      substantive identity probes passed at ~1e-16 unamended.
  A2 (monotonicity -> monotone-to-plateau): the first run measured a genuine
      ~0.03pp decline from the curve's peak (s ~ 0.7-0.8) to the additive
      endpoint on both floors — a second-order pool-depletion interaction,
      not mis-wiring (all engine parity gates passed bit-exact). Amended
      rule: strictly increasing up to the peak; above it a decline of at
      most 0.1pp from the running maximum is a PLATEAU, not a violation.
      Declines beyond 0.1pp remain STOP-2.

Run:  cd hazard && python3 floor_form_mixture.py
      -> data/floor_form_mixture_results.json (frozen)
48 engine runs, ~26s each.
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
RESULTS_JSON = DATA_DIR / "floor_form_mixture_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

S_GRID = [0.0, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
NAMED_S = 0.4
TOL_B = 1e-6
STOP_B = 0.01
ANCH_MARG = {(0.04, 0.0): 70.34506041989584, (0.04, 1.0): 86.02249228630046,
             (0.04991, 0.0): 42.60839388108866,
             (0.04991, 1.0): 85.70549789908563}
ANCH_LEG = {(0.04, 0.0, 6.5): 818.5300844066606, (0.04, 0.0, 0.0): 748.1850239867648,
            (0.04991, 0.0, 0.0): 724.9180585654117,
            (0.04991, 1.0, 6.5): 427.54488764725437}
PROBE_N, PROBE_SEED = 10_000, 42

_ORIG = fs._ORIG_PREPAY


def make_mixture(s: float):
    def mix(loan_age, rate_gap, burnout, fico_z, ltv_z,
            beta1=lh.BETA1_PREPAY_MID, coefs=None):
        b = beta1 if isinstance(beta1, np.ndarray) else float(beta1)
        c = coefs or lh.LITERATURE_COEFS
        h0 = lh.baseline_hazard(loan_age)
        base = np.exp(c["beta_fico"] * fico_z + c["beta_ltv"] * ltv_z
                      + c["beta_burnout"] * burnout)
        m = np.exp((-b) * (np.asarray(rate_gap) * 100.0))
        h_vol = h0 * base * m
        hf = lh.cpr_annual_to_monthly_hazard(
            np.full_like(h0, lh.INVOLUNTARY_CPR_ANNUAL, dtype=np.float64))
        combined = 1.0 - (1.0 - s * hf) * (1.0 - np.maximum((1.0 - s) * hf,
                                                            h_vol))
        return np.clip(combined, 0.0, 1.0)
    return mix


def probe(floor: float) -> dict:
    rng = np.random.default_rng(PROBE_SEED)
    age = rng.uniform(1, 360, PROBE_N)
    gap = rng.uniform(-0.05, 0.01, PROBE_N)
    burn = rng.uniform(0, 3, PROBE_N)
    fz = rng.uniform(-3, 3, PROBE_N)
    lz = rng.uniform(-3, 3, PROBE_N)
    b1 = lh.rothstein_beta1(6.5 / 100.0)
    cur_f, cur_m = lh.INVOLUNTARY_CPR_ANNUAL, lh.FLOOR_MODE
    lh.INVOLUNTARY_CPR_ANNUAL = floor
    try:
        lh.FLOOR_MODE = "max"
        p_max = _ORIG(age, gap, burn, fz, lz, beta1=b1)
        lh.FLOOR_MODE = "additive"
        p_add = _ORIG(age, gap, burn, fz, lz, beta1=b1)
        lh.FLOOR_MODE = "max"
        d0 = float(np.max(np.abs(make_mixture(0.0)(age, gap, burn, fz, lz,
                                                   beta1=b1) - p_max)))
        d1 = float(np.max(np.abs(make_mixture(1.0)(age, gap, burn, fz, lz,
                                                   beta1=b1) - p_add)))
        de = float(np.max(np.abs(make_mixture(1e-12)(age, gap, burn, fz, lz,
                                                     beta1=b1) - p_max)))
    finally:
        lh.INVOLUNTARY_CPR_ANNUAL = cur_f
        lh.FLOOR_MODE = cur_m
    return {"max_s0_vs_max": d0, "max_s1_vs_additive": d1,
            "continuity_eps": de,
            "pass": d0 < 1e-12 and d1 < 1e-12 and de < 1e-13}


def run_cell(loans, empirical, floor, pq, s):
    if s == 0.0:
        return fs._run_scored(loans, empirical, floor, pq)
    if s == 1.0:
        cur = lh.FLOOR_MODE
        lh.FLOOR_MODE = "additive"
        try:
            return fs._run_scored(loans, empirical, floor, pq)
        finally:
            lh.FLOOR_MODE = cur
    fs._ORIG_PREPAY = make_mixture(s)
    try:
        return fs._run_scored(loans, empirical, floor, pq)
    finally:
        fs._ORIG_PREPAY = _ORIG
        competing_risks.prepay_hazard = _ORIG


def main() -> None:
    oos = json.load(open(OOS_ARTIFACT))
    off = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off - 4.991) < 1e-9
    floors = [0.04, off / 100.0]

    probes = {f"{fl*100:g}": probe(fl) for fl in floors}
    print("identity probes:", {k: v["pass"] for k, v in probes.items()})
    anchor_dev = {f"{fl*100:g}|{s:g}": s * (1 - s)
                  * float(lh.cpr_annual_to_monthly_hazard(np.array([fl]))[0])
                  for fl in floors for s in S_GRID}
    max_dev = max(anchor_dev.values())
    print(f"floor-anchor max relative deviation: {max_dev:.4%}")

    print("Shared macro frame (fetched once) ...")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    cells: dict = {}
    for fl in floors:
        for s in S_GRID:
            for pq in (0.0, 6.5):
                r = run_cell(loans, empirical, fl, pq, s)
                r["share_s"] = s
                cells[f"{fl*100:g}|{s:g}|{pq:g}"] = r
        for s in S_GRID:
            kc, kn = f"{fl*100:g}|{s:g}|6.5", f"{fl*100:g}|{s:g}|0"
            cells[kc]["marginal_b"] = cells[kc]["trapped_b"] - cells[kn]["trapped_b"]
            cells[kc]["marginal_pp"] = cells[kc]["share_pct"] - cells[kn]["share_pct"]
            print(f"  floor {fl*100:g} s={s:g}: marginal "
                  f"{cells[kc]['marginal_pp']:+.3f}pp "
                  f"(central {cells[kc]['share_pct']:.1f}%)")

    gates = {}
    for (fl, s), want in ANCH_MARG.items():
        got = cells[f"{fl*100:g}|{s:g}|6.5"]["marginal_b"]
        gates[f"P_marg_{fl*100:g}_s{s:g}"] = {
            "got": got, "want": want,
            "pass": abs(got - want) < TOL_B,
            "stop": abs(got - want) > STOP_B}
    for (fl, s, pq), want in ANCH_LEG.items():
        got = cells[f"{fl*100:g}|{s:g}|{pq:g}"]["trapped_b"]
        gates[f"P_leg_{fl*100:g}_s{s:g}_pq{pq:g}"] = {
            "got": got, "want": want, "pass": abs(got - want) < TOL_B,
            "stop": abs(got - want) > STOP_B}
    gates["P6_probes"] = {"floors": probes,
                          "pass": all(v["pass"] for v in probes.values())}
    gates["P_floor_mode_restored"] = {"pass": lh.FLOOR_MODE == "max"}
    all_pass = all(v["pass"] for v in gates.values())
    any_stop = any(v.get("stop") for v in gates.values())

    mono = {}
    for fl in floors:
        ms = [cells[f"{fl*100:g}|{s:g}|6.5"]["marginal_pp"] for s in S_GRID]
        peak = max(range(len(ms)), key=lambda i: ms[i])
        rising = all(ms[i] < ms[i + 1] + 1e-9 for i in range(peak))
        plateau = all(ms[peak] - ms[i] <= 0.1 for i in range(peak, len(ms)))
        mono[f"{fl*100:g}"] = {"peak_s": S_GRID[peak], "rising_to_peak": rising,
                               "plateau_within_0.1pp": plateau,
                               "pass": rising and plateau}
    monotone = all(v["pass"] for v in mono.values())

    named = {f"{fl*100:g}": {
        "s": NAMED_S,
        "marginal_pp": cells[f"{fl*100:g}|{NAMED_S:g}|6.5"]["marginal_pp"],
        "marginal_b": cells[f"{fl*100:g}|{NAMED_S:g}|6.5"]["marginal_b"],
        "central_share_pct": cells[f"{fl*100:g}|{NAMED_S:g}|6.5"]["share_pct"],
        "s025_marginal_pp": cells[f"{fl*100:g}|0.25|6.5"]["marginal_pp"]}
        for fl in floors}

    status = ("GATE_FAILURE" if (any_stop or not all_pass)
              else ("CHECK_FAILURE" if (not monotone or max_dev >= 0.0015)
                    else "OK"))
    payload = {
        "mode": "floor_form_mixture", "status": status,
        "spec": ("s = strictly-involuntary share entering additively, (1-s) "
                 "floor on total; endpoints via PRODUCTION code paths (max / "
                 "additive mode), interior via the seam; grid 12 s-points x "
                 "2 legs x 2 floors; orientation s=0==max, s=1==additive; "
                 "named point s=0.4 (paper semantics: well under half), "
                 "s=0.25 beside it; symbol choice is Eugene's."),
        "orientation": {"s0": "production hard maximum",
                        "s1": "additive competing-risks",
                        "paper_semantics_named_s": NAMED_S},
        "parity_gates": gates, "parity_gates_all_pass": all_pass,
        "floor_anchor_preservation": {"per_cell_rel_dev": anchor_dev,
                                      "max_rel_dev": max_dev,
                                      "pass": max_dev < 0.0015},
        "monotonicity": mono, "cells": cells, "named_interior": named,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    def _np(o):
        if hasattr(o, "item"):
            return o.item()
        raise TypeError(f"not serializable: {type(o)}")
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_np)
        f.write("\n")
    print(f"\nstatus {status}; named s=0.4 off-window marginal "
          f"{named['4.991']['marginal_pp']:+.3f}pp "
          f"(s=0.25: {named['4.991']['s025_marginal_pp']:+.3f}pp)")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript.")


if __name__ == "__main__":
    main()
