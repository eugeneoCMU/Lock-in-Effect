#!/usr/bin/env python3
"""
Round-15 Q4: ABM external-gates variant — behavioral gates parameterized
from external micro estimates, NO involuntary-turnover-floor recalibration.

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------
Reviewer question (round 15, Q4): re-specify the ABM so the key behavioral
gates are parameterized directly from external micro estimates (e.g.,
Liebersohn & Rothstein mobility elasticities) and report whether recovery
rises without the turnover-floor recalibration artifact.

Two of the three named gates are ALREADY external and are left unchanged:
  DTI_MAX = 0.43                CFPB QM/ATR threshold (12 CFR 1026.43)
  LOSS_AVERSION_LAMBDA = 2.25   Kahneman-Tversky prospect-theory coefficient
The two author-calibrated elements are replaced with external anchors from
Liebersohn & Rothstein — the SAME source Path B's elasticity imports:

1. Mobility-desire scale: anchored to the L&R zero-gap moving level rather
   than the 4-5% involuntary-turnover floor at maximum lock-in.  Source
   (verbatim, Liebersohn & Rothstein 2024 draft, section 6): "In 2021q2,
   when the average rate gap was essentially zero, both the actual and
   counterfactual quarterly ZIP code mobility hazard in our sample were
   around 1.5 percent."  Annualized on the survival scale:
   1-(1-0.015)^4 = 5.87% per year.  The binary search pins the engine's
   ZERO-GAP U.S. CPR (market rate = cohort coupon) to this level; the
   floor plays no role anywhere in the calibration.
2. Wait-and-see freeze share: the production author value (20% of cleared
   movers freeze when the 6-month rate rise exceeds 150bp) is replaced by
   the L&R-implied magnitude at the same trigger: the quarterly mobility
   decline is 6.5% per 100bp of gap (ROTHSTEIN_Q_DECLINE_MID, the exact
   quantity Path B's beta1 transform consumes), so a +150bp rise sustained
   over the trigger's two quarters compounds to
   1-(1-0.065)^(1.5 x 2) = 18.26%.  The trigger threshold itself (150bp/
   6mo) is retained so exactly one number changes per gate.

Harness: the committed cross-design harness (real Freddie structural
covariates, synthetic behavioral draws, cross_design_test.run_variant) —
the same instrument that produced tab:crossdesign's (a) recalibrated 59.3%
and (b) frozen rows.  The external variant (c) extends that pair; its
result is directly comparable and is evaluated against the SAME
pre-registered bands (cross_design_test.PREREGISTRATION):
  >50% undercuts the paradigm reading; 10-35% corroborates; 35-50%
  ambiguous and reported as such.

Gates (must PASS before the variant is interpreted)
---------------------------------------------------
G1 harness parity: variant (a) recalibrated re-run through this script's
   scoring path (cached surface) must reproduce the committed
   cross_design_results.json share_pct within +-0.05pp.
G2 anchor hit: the external calibration's zero-gap CPR must land within
   [5.5%, 6.3%] of the 5.87% L&R anchor (binary-search tolerance).
Floor diagnostic (pre-registered reading): report the external variant's
   CPR at 8.0% market rate.  If it falls OUTSIDE the observed 4-5%
   involuntary-turnover band, the no-recalibration model violates the
   observed discount-cohort turnover moment — which is the documented
   reason the production calibration anchors there; this diagnostic is
   reported alongside whatever the recovery number is, whichever
   direction it moves.

Output: abm/data/abm_external_gates_results.json
Run:    cd abm && python3 abm_external_gates.py   (one surface build)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from cross_design_test import (
    PREREGISTRATION,
    RESULTS_JSON as CROSS_DESIGN_JSON,
    _build_engine,
    _population_sched_series,
    _surface_csv,
    run_variant,
)
from freddie_population import load_freddie_structural_sample
from paths import ABM_DIR

RESULTS_JSON = ABM_DIR / "data" / "abm_external_gates_results.json"

LR_ZERO_GAP_QUARTERLY = 0.015
LR_ZERO_GAP_ANNUAL = 1.0 - (1.0 - LR_ZERO_GAP_QUARTERLY) ** 4        # 5.87%
LR_FREEZE_PROB = 1.0 - (1.0 - 0.065) ** (1.5 * 2)                     # 18.26%
ANCHOR_BAND = (0.055, 0.063)
G1_TOL_PP = 0.05


def calibrate_mobility_scale_zero_gap(income: float, home_value: float,
                                      loans: pd.DataFrame,
                                      target: float = LR_ZERO_GAP_ANNUAL,
                                      max_iter: int = 40) -> tuple[float, float]:
    """Binary-search the mobility scale so ZERO-GAP U.S. CPR hits the
    L&R moving level. Zero gap = market rate at the population's mean
    coupon; the involuntary floor is never referenced."""
    wac = float(loans["coupon"].mean())
    lo, hi = 1_000.0, 500_000.0
    scale = cpr = None
    for _ in range(max_iter):
        scale = (lo + hi) / 2
        engine = _build_engine(scale, income, home_value, loans)
        cpr = engine.cpr_at(wac, "US")
        if abs(cpr - target) < 0.0005:
            break
        if cpr < target:
            lo = scale      # too few movers -> raise desire scale
        else:
            hi = scale
    print(f"Zero-gap calibration: scale {scale:,.0f} -> CPR(gap=0) {cpr:.2%} "
          f"(target {target:.2%})")
    return scale, cpr


def main() -> None:
    committed = json.loads(CROSS_DESIGN_JSON.read_text())

    print("Fetching macro/SOMA frames …")
    df0 = fed.fetch_data()
    soma_rolloff = fed.fetch_soma_mbs_monthly()
    income, home_value = abm.fetch_macro_from_fred()
    loans = load_freddie_structural_sample(abm.N_HOUSEHOLDS)

    # --- G1 harness parity: recalibrated variant, cached surface ----------
    a = run_variant("recalibrated",
                    committed["variants"]["recalibrated"]["mobility_scale"],
                    income, home_value, loans, df0, soma_rolloff)
    g1_diff = a["share_pct"] - committed["variants"]["recalibrated"]["share_pct"]
    g1_pass = abs(g1_diff) <= G1_TOL_PP
    print(f"G1 parity: recalibrated {a['share_pct']:.3f}% vs committed "
          f"{committed['variants']['recalibrated']['share_pct']:.3f}% "
          f"(diff {g1_diff:+.4f}pp) {'PASS' if g1_pass else 'FAIL'}")
    if not g1_pass:
        RESULTS_JSON.write_text(json.dumps(
            {"status": "GATE_FAILURE", "g1_diff_pp": g1_diff}, indent=2) + "\n")
        raise SystemExit("G1 parity failure — external variant not run.")

    # --- External gates ----------------------------------------------------
    prod_freeze = abm.WAIT_AND_SEE_PROB
    abm.WAIT_AND_SEE_PROB = LR_FREEZE_PROB
    try:
        scale_ext, cpr_zero = calibrate_mobility_scale_zero_gap(
            income, home_value, loans)
        g2_pass = ANCHOR_BAND[0] <= cpr_zero <= ANCHOR_BAND[1]
        print(f"G2 anchor: zero-gap CPR {cpr_zero:.2%} in "
              f"[{ANCHOR_BAND[0]:.1%}, {ANCHOR_BAND[1]:.1%}] "
              f"{'PASS' if g2_pass else 'FAIL'}")
        if not g2_pass:
            RESULTS_JSON.write_text(json.dumps(
                {"status": "GATE_FAILURE", "zero_gap_cpr": cpr_zero},
                indent=2) + "\n")
            raise SystemExit("G2 anchor failure — variant not interpreted.")

        ext = run_variant("external", scale_ext, income, home_value,
                          loans, df0, soma_rolloff, rebuild=True)
        engine = _build_engine(scale_ext, income, home_value, loans)
        floor_cpr = engine.cpr_at(0.08, "US")
    finally:
        abm.WAIT_AND_SEE_PROB = prod_freeze

    def classify(share):
        if share > PREREGISTRATION["undercuts_paradigm_above_pct"]:
            return "undercuts_paradigm"
        lo, hi = PREREGISTRATION["corroborates_band_pct"]
        if lo <= share <= hi:
            return "corroborates_paradigm_gap"
        return "ambiguous"

    payload = {
        "mode": "abm_external_gates",
        "spec": "round-15 Q4; external gates, no floor recalibration; cross-design harness",
        "external_parameters": {
            "dti_max": abm.DTI_MAX,
            "loss_aversion_lambda": abm.LOSS_AVERSION_LAMBDA,
            "wait_and_see_prob": LR_FREEZE_PROB,
            "wait_and_see_prob_production": prod_freeze,
            "wait_and_see_derivation": "1-(1-0.065)^(1.5x2); L&R 6.5%/qtr per 100bp at the production 150bp/6mo trigger",
            "zero_gap_anchor_annual": LR_ZERO_GAP_ANNUAL,
            "zero_gap_anchor_source": "L&R 2024: 'quarterly ZIP code mobility hazard ... around 1.5 percent' at zero gap (2021q2)",
            "mobility_scale_external": scale_ext,
            "mobility_scale_recalibrated_committed": committed["variants"]["recalibrated"]["mobility_scale"],
            "mobility_scale_frozen_committed": committed["variants"]["frozen"]["mobility_scale"],
        },
        "gates": {
            "G1_harness_parity": {"diff_pp": g1_diff, "pass": g1_pass},
            "G2_anchor": {"zero_gap_cpr": cpr_zero, "band": ANCHOR_BAND, "pass": g2_pass},
        },
        "results": {
            "external": ext,
            "recalibrated_replayed": a,
            "committed_pair": {k: committed["variants"][k]["share_pct"]
                               for k in ("recalibrated", "frozen")},
        },
        "floor_diagnostic": {
            "cpr_at_8pct_market": floor_cpr,
            "observed_floor_band": [0.04, 0.05],
            "violates_observed_floor": not (0.04 <= floor_cpr <= 0.05),
        },
        "preregistration": PREREGISTRATION,
        "classification_external": classify(ext["share_pct"]),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\nExternal variant: {ext['share_pct']:.1f}% of benchmark "
          f"(${ext['trapped_b']:.1f}B) -> {payload['classification_external']}")
    print(f"Floor diagnostic: CPR(8%) = {floor_cpr:.2%} "
          f"({'violates' if payload['floor_diagnostic']['violates_observed_floor'] else 'within'} "
          f"observed 4-5% band)")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
