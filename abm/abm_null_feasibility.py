#!/usr/bin/env python3
"""
abm_null_feasibility.py — is there an ABM counterpart to Path B's beta_1 = 0 null?

HANDOFF_round22.md item 6.1 A. Liveness gate #94.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
This is a FEASIBILITY PROBE, not a pre-committed estimate, and it is labelled as such
everywhere it is cited. It carries NO acceptance rule, NO threshold and NO verdict code,
because the question it answers is whether an interpretable ABM null EXISTS -- a
non-existence claim, which no threshold could adjudicate. Nothing in the manuscript's
headline, ranges or uncertainty layers depends on any number below.

That distinction matters here. The candidate nulls were executed BEFORE this file was
written, while scoping the item. Had they produced an interpretable differential, the
honest course would have been to throw the numbers away and re-run under a spec committed
first (round-22 C1: a precondition articulated after a result is seen is not a
precondition). They did not: every candidate is off by one to three orders of magnitude
and the two defensible ones disagree in SIGN, so the conclusion is qualitative and no
acceptance rule was ever available to bend. The execution order is recorded here rather
than smoothed over.

THE QUESTION
------------
The manuscript identifies the lock-in channel as a DIFFERENTIAL, not a level:
  paper/v18/revised_paper_v18.tex L469  "The design does not identify the aggregate
  recovery level: the level is floor-dominated, and the beta_1 = 0 null ... already
  recovers 85.7% of the benchmark"
Path B therefore reports central - null = +5.6 points. The ABM has no null: its 13.6%
seed mean is a LEVEL, and the estimator contrast (Path B 91.3% vs ABM 13.6%) is a
contrast of levels the paper elsewhere says do not identify. An ABM null would make that
contrast apples-to-apples. This probe asks whether one can be built.

WHY PATH B HAS A NULL AND THE ABM DOES NOT
------------------------------------------
Path B, eq:pathB:      h = max( h_floor , h_0(a) * exp(beta_1 * g + ...) )
The elasticity is a SEPARABLE multiplicative term sitting over a floor that is measured
independently and survives its removal. Setting beta_1 = 0 leaves h_floor untouched, so
the null is still anchored to the observed involuntary-turnover floor and lands at a sane
85.7% of benchmark.

The ABM has no separate floor term. Its move rule (abm_lockin_simulation.py:449-468) is
    move  <=>  DTI veto  AND  desire > penalty*60 + txn_cost  AND  not freeze
and the 4-5% involuntary floor is not a term in it -- it is PRODUCED, by binary-searching
the mobility-desire scale theta so that the penalty-bearing rule returns 4-5% CPR at an
8% market rate (calibrate_mobility_scale, abm_lockin_simulation.py:649-685, evaluated on
the reference cohort at rate 0.08, friction 0.07, velocity 0.0). The lock-in penalty is
simultaneously the behavioural mechanism AND the thing that sets the level. Zeroing it
leaves nothing behind to hold the floor.

THE THREE LEGS
--------------
  CENTRAL          production rule, theta = 43,882.8125 (frozen manifest).
  NULL A           _mobility_penalty == 0, theta HELD at the production value.
                   The literal analogue of "switch off the elasticity, change nothing
                   else" -- and it destroys the floor calibration.
  NULL B           _mobility_penalty == 0, theta RE-DERIVED under the null so the 4-5%
                   floor anchor is restored (the dti_threshold_sweep floor-retention
                   discipline). Restores the floor -- by re-fitting the null to the very
                   quantity the differential is supposed to measure.
Both are defensible readings of "the ABM's beta_1 = 0 null". They disagree in sign.

SCOPE / WHAT THIS DOES NOT TOUCH
--------------------------------
- Writes only abm/data/abm_null_feasibility_results.json. Builds its surfaces in memory;
  it never writes abm/abm_cpr_surface.csv or any run manifest.
- No hazard/ code runs. No headline, range, floor or benchmark is re-derived.
- The Danish leg is inert here: under the production 'dk_level' anchor _cpr_vec never
  calls _mobility_penalty (abm_lockin_simulation.py:412-445), so CPR_Danish is invariant
  to the patch. G3 asserts that rather than assuming it.
- Macro inputs (median income, median home value) are PINNED to the frozen manifest so
  the surfaces are reproducible offline. The accounting layer still reads live FRED and
  SOMA, so dollar levels drift with upstream revisions; the finding is qualitative and
  three orders of magnitude clear of that drift, and G1 is a band, not a bit-exact tie.

Run:  cd abm && python3 abm_null_feasibility.py
Runtime: ~50 s (3 surface builds x 11 cohorts x 3,380 nodes + 3 scoring passes).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
import monte_carlo_simulation as mc
from paths import ABM_DIR, LATEST_RUN_MANIFEST

RESULTS_JSON = ABM_DIR / "data" / "abm_null_feasibility_results.json"

FLOOR_RATE = 0.08          # the calibration's evaluation rate
FLOOR_BAND = (0.04, 0.05)  # the involuntary-turnover floor the ABM is anchored to

GATES: dict = {}


def check(gate: str, ok: bool, detail) -> None:
    GATES[gate] = {"pass": bool(ok), "detail": detail}
    if not ok:
        RESULTS_JSON.write_text(json.dumps(
            {"status": "GATE_FAILURE", "gate": gate, "detail": detail,
             "gates_so_far": GATES,
             "generated_utc": datetime.now(timezone.utc).isoformat()}, indent=1))
        raise SystemExit(f"[GATE FAILURE] {gate}: {detail}")


_ORIG_PENALTY = abm.HousingMarketEngine._mobility_penalty


def _zero_penalty(self, payoff, new_pmt, rate):
    return np.zeros(self.n_households)


def _engine(scale: float, income: float, home_value: float) -> "abm.HousingMarketEngine":
    return abm.HousingMarketEngine(seed=abm.RNG_SEED, median_income=income,
                                   median_home_value=home_value, mobility_scale=scale)


def anchor_cpr(scale: float, ref: dict, income: float, home_value: float,
               penalty_off: bool) -> float:
    """CPR at the 8% calibration point, on the calibration's OWN reference cohort.

    Reading this off a freshly constructed engine without attach_cohort would measure
    the module-default 3.0% cohort instead of the reference cohort the calibration
    targets, and return a number that looks like a miscalibration but is not.
    """
    abm.HousingMarketEngine._mobility_penalty = (
        _zero_penalty if penalty_off else _ORIG_PENALTY)
    try:
        eng = _engine(scale, income, home_value)
        eng.attach_cohort(ref["coupon"], ref["months_elapsed"])
        return float(eng.cpr_at(FLOOR_RATE, "US"))
    finally:
        abm.HousingMarketEngine._mobility_penalty = _ORIG_PENALTY


def score(label: str, scale: float, penalty_off: bool, df0, soma, cohorts,
          income: float, home_value: float) -> dict:
    abm.HousingMarketEngine._mobility_penalty = (
        _zero_penalty if penalty_off else _ORIG_PENALTY)
    try:
        eng = _engine(scale, income, home_value)
        surf_df = abm.build_multi_cohort_surfaces(eng, cohorts)
        surface = mc.surface_df_to_surfaces(surf_df)
        m = fed.compute_metrics(df0.copy(), surface=surface, soma_rolloff=soma,
                                cohorts=cohorts, use_burnout=False,
                                apply_settlement_lag_kernel=True)
        hm = fed.export_headline_metrics(m)
        d = hm["dollars_b"]
        return {
            "label": label,
            "penalty_off": penalty_off,
            "mobility_scale": float(scale),
            "us_trapped_b": float(d["us_trapped"]),
            "share_explained_pct": float(d["share_explained_pct"]),
            "empirical_trapped_b": float(d["empirical_trapped"]),
            "mean_cpr_pct": float(hm["cpr_pct"]["us_abm"]["mean"]),
            "curtailment_b": float(hm["curtailment_b"]["total"]),
            "danish_trapped_b": float(d.get("danish_trapped", float("nan"))),
        }
    finally:
        abm.HousingMarketEngine._mobility_penalty = _ORIG_PENALTY


def main() -> None:
    t0 = time.time()
    man = json.loads(LATEST_RUN_MANIFEST.read_text())
    scale_prod = float(man["pipeline"]["mobility_scale"])
    income = float(man["pipeline"]["median_income"])
    home_value = float(man["pipeline"]["median_home_value"])

    check("G0_manifest_inputs",
          abs(scale_prod - 43882.8125) < 1e-9,
          {"run_tag": man.get("run_tag"), "mobility_scale": scale_prod,
           "median_income": income, "median_home_value": home_value})

    df0 = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()
    cohorts = fed.fetch_soma_mbs_cohorts()
    ref = abm.reference_cohort(cohorts)

    # --- the floor anchor, on the reference cohort, under each rule -----------------
    a_central = anchor_cpr(scale_prod, ref, income, home_value, penalty_off=False)
    a_null_a = anchor_cpr(scale_prod, ref, income, home_value, penalty_off=True)

    abm.HousingMarketEngine._mobility_penalty = _zero_penalty
    try:
        scale_null = float(abm.calibrate_mobility_scale(
            income, home_value, cohort_rate=ref["coupon"],
            cohort_months=ref["months_elapsed"]))
    finally:
        abm.HousingMarketEngine._mobility_penalty = _ORIG_PENALTY
    a_null_b = anchor_cpr(scale_null, ref, income, home_value, penalty_off=True)

    check("G1_central_anchor_in_floor_band",
          FLOOR_BAND[0] <= a_central <= FLOOR_BAND[1],
          {"anchor_cpr_at_8pct": a_central, "band": list(FLOOR_BAND),
           "reference_cohort": {"coupon": ref["coupon"],
                                "months_elapsed": ref["months_elapsed"]}})

    # The finding itself: removing the penalty at frozen theta destroys the anchor.
    check("G2_null_frozen_breaks_floor_anchor",
          a_null_a > 0.30,
          {"anchor_cpr_at_8pct": a_null_a, "central": a_central,
           "multiple_of_central": a_null_a / a_central})

    check("G4_null_reanchored_restores_floor",
          FLOOR_BAND[0] <= a_null_b <= FLOOR_BAND[1],
          {"anchor_cpr_at_8pct": a_null_b, "mobility_scale": scale_null})

    legs = {
        "central": score("CENTRAL (production rule)", scale_prod, False,
                         df0, soma, cohorts, income, home_value),
        "null_frozen": score("NULL A (penalty=0, theta frozen)", scale_prod, True,
                             df0, soma, cohorts, income, home_value),
        "null_reanchored": score("NULL B (penalty=0, theta re-derived)", scale_null, True,
                                 df0, soma, cohorts, income, home_value),
    }

    # The Danish leg must be untouched: under 'dk_level' it never sees the penalty.
    check("G3_danish_leg_invariant",
          abs(legs["central"]["danish_trapped_b"]
              - legs["null_frozen"]["danish_trapped_b"]) < 1e-9,
          {k: legs[k]["danish_trapped_b"] for k in legs})

    check("G5_common_layers_cancel",
          (legs["central"]["curtailment_b"] == legs["null_frozen"]["curtailment_b"]
           == legs["null_reanchored"]["curtailment_b"]),
          {k: legs[k]["curtailment_b"] for k in legs})

    bench = legs["central"]["empirical_trapped_b"]
    implied = {}
    for k in ("null_frozen", "null_reanchored"):
        dm = legs["central"]["us_trapped_b"] - legs[k]["us_trapped_b"]
        implied[k] = {"marginal_b": dm, "marginal_pp": dm / bench * 100.0}

    # The conclusion, asserted rather than narrated: the two defensible anchoring
    # conventions do not merely differ in size, they differ in SIGN.
    check("G6_candidate_nulls_disagree_in_sign",
          (implied["null_frozen"]["marginal_pp"] > 0
           > implied["null_reanchored"]["marginal_pp"]),
          {k: v["marginal_pp"] for k, v in implied.items()})

    payload = {
        "mode": "feasibility_probe",
        "pre_committed": False,
        "question": "Does an interpretable ABM counterpart to Path B's beta_1 = 0 null exist?",
        "conclusion": "NOT_FEASIBLE",
        "conclusion_detail": (
            "The ABM's lock-in penalty is not a separable term over a surviving floor: "
            "the 4-5% involuntary-turnover floor is produced BY calibrating theta against "
            "the penalty-bearing rule. Zeroing the penalty either destroys the floor "
            "(theta frozen) or requires re-fitting theta to restore it, which re-fits the "
            "null to the quantity the differential is meant to measure. The two defensible "
            "conventions return marginals of opposite sign, so no ABM differential is "
            "identified and the ABM contrast stays a contrast of levels."),
        "floor_anchor_cpr_at_8pct": {
            "central": a_central, "null_frozen": a_null_a, "null_reanchored": a_null_b,
            "target_band": list(FLOOR_BAND),
            "reference_cohort": {"coupon": ref["coupon"],
                                 "months_elapsed": ref["months_elapsed"],
                                 "term_months": ref.get("term_months")},
        },
        "mobility_scale": {"production": scale_prod, "reanchored_under_null": scale_null},
        "legs": legs,
        "implied_marginal": implied,
        "benchmark_b": bench,
        "pathb_comparison": {
            "pathb_marginal_pp_headline": 5.6,
            "note": ("Path B's null recovers 85.7% of benchmark because its floor survives "
                     "beta_1 = 0. Neither ABM null lands anywhere near a comparable level."),
        },
        "gates": GATES,
        "gates_all_pass": all(g["pass"] for g in GATES.values()),
        "runtime_s": time.time() - t0,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=1))

    print(f"\n{'leg':34s}{'theta':>13s}{'anchor@8%':>11s}{'meanCPR%':>10s}"
          f"{'trapped $B':>13s}{'share %':>10s}")
    for k, a in (("central", a_central), ("null_frozen", a_null_a),
                 ("null_reanchored", a_null_b)):
        v = legs[k]
        print(f"{v['label']:34s}{v['mobility_scale']:13.4f}{a:11.4f}"
              f"{v['mean_cpr_pct']:10.3f}{v['us_trapped_b']:13.2f}"
              f"{v['share_explained_pct']:10.3f}")
    for k, v in implied.items():
        print(f"  implied ABM marginal vs {k:16s} {v['marginal_b']:+11.2f}B "
              f"= {v['marginal_pp']:+8.2f}pp")
    print(f"\nCONCLUSION: {payload['conclusion']}   "
          f"({len(GATES)} gates, all pass = {payload['gates_all_pass']}, "
          f"{payload['runtime_s']:.0f}s)")
    print(f"wrote {RESULTS_JSON}")


if __name__ == "__main__":
    main()
