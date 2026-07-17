#!/usr/bin/env python3
"""
Fonseca second-literature-anchor band placement (R18-B optional leg).

SPEC — committed before any run (spec-before-run):

WHY
  Referee comment M2/Q5 asks the model to "test other credible estimates"
  beyond the single Liebersohn--Rothstein (L&R) elasticity band. This run
  propagates a second, independent U.S. literature estimate --- Fonseca &
  Liu (2024) --- through the SAME eq:beta1 survival-function transform and the
  SAME Path B microsimulation band-sweep machinery (floor_sweep._run_scored,
  the exact scorer behind fig6 / tab:floorband and the committed
  extension_risk_band_literature.json), and reports the implied lock-in
  marginal next to the L&R band's own endpoints. It changes nothing in the
  paper's headline calibration: it is a triangulation exhibit only.

PRE-COMMITTED FONSECA POINT AND ITS UNIT CONVERSION (fixed before the run)
  delta_fonseca = 0.09  (proportional decline, treated quarterly-equivalent),
  i.e. p_q_shock_pct = 9.0, fed through the identical parameterization the
  band sweep uses: beta1 = rothstein_beta1(p_q_shock_pct / 100).

  Provenance, from the manuscript's OWN words (READ-ONLY):
    - eq:beta1 footnote (revised_paper_v16.tex L442): "\citet{fonseca2024}
      report a related but distinct estimand (a roughly 9% reduction in moving
      rates per percentage point of mortgage-rate delta), which I cite as
      independent corroboration of the lock-in magnitude, not as a source of
      the band."
    - L219 (Berger moving-channel comparison): "a U.S. moving-hazard slope of
      0.57--1.20 percentage points per year per 100 basis points of coupon
      gap \citep{fonseca2024}."
    - references.bib: Fonseca, J. and Liu, L. (2024), "Mortgage lock-in,
      mobility, and labor reallocation," Journal of Finance 79(6), 3729--3772.

  The number the manuscript itself quotes as the Fonseca analogue of L&R's
  proportional decline is the "roughly 9% reduction in moving rates per
  percentage point." L&R's delta is a proportional decline in QUARTERLY
  MOBILITY probability per 100bp of rate gap; Fonseca's 9% is a proportional
  reduction in MOVING RATES per percentage point (pp) of mortgage-rate delta.
  A pp of mortgage-rate movement == 100bp, so the per-unit denominators align;
  the "roughly 9%" is a proportional (not absolute) decline, which is the
  exact input shape the transform expects. delta_fonseca = 0.09 is therefore
  the faithful, single-point reading. This is NOT genuinely ambiguous enough
  to force a two-point bracket, for two reasons stated ex ante:
    (a) The transform is near-frequency-invariant. In the small-P_q limit
        beta1 = -ln(1 - delta), which carries no measurement-frequency, so
        treating Fonseca's proportional moving-rate reduction as a
        quarterly-equivalent delta introduces only conversion-level (few
        percent) error, not band-level error --- the manuscript proves this
        insensitivity at L897 (central beta1 ranges only 0.0672 -> 0.0701
        over P_q in (0, 0.12], double the adopted proxy).
    (b) The alternative absolute-slope reading (0.57--1.20 pp/yr per 100bp,
        L219) CORROBORATES the 9% point rather than contradicting it: on a
        typical ~9-10% annual mover base, 0.57--1.20 pp/yr is a ~6-13%
        proportional reduction, which brackets 9%. So the point is not
        knife-edge. (Reported in the results as a cross-check, not run.)

  CAVEATS THE RESPONSE LETTER MUST CARRY (unchanged from the L&R import,
  plus the estimand mismatch):
    1. Estimand mismatch: L&R = proportional QUARTERLY-MOBILITY decline per
       100bp of RATE GAP; Fonseca = proportional MOVING-RATE reduction per pp
       of MORTGAGE-RATE DELTA. The manuscript calls these "related but
       distinct." The transplant asserts they are close enough to be fed
       through one transform; it does not assert they are the same estimand.
    2. Frequency: 9% is treated quarterly-equivalent; licensed by (a) above.
    3. Prepayment vs mobility: like the L&R import, a mobility-derived delta
       is applied to a PREPAYMENT hazard, so the anchor measures
       rate-attributable prepayment suppression --- an upper bound on the
       strictly-voluntary mobility contribution (paper V.C, L448).
    4. Corroboration-only: the paper cites Fonseca as independent
       corroboration, NOT as a source of the band; this run is a
       referee-requested second anchor, not a change to the headline L&R
       calibration.

HOW (machinery, production convention, nothing modified)
  - Reuse floor_sweep._run_scored UNCHANGED (imported): committed 75k loan
    sample, RNG_SEED=42, ("US","Danish") regime tuple, one shared macro frame
    fetched once, raw-basis scoring via extension_risk.score_extension_risk,
    bind instrumentation. Production involuntary floor = 4.0% annual CPR
    throughout (config.INVOLUNTARY_CPR_ANNUAL). beta1 enters via
    microsim_engine: beta1 = rothstein_beta1(p_q_shock_pct/100).
  - Five legs at the production 4.0% floor, one macro fetch:
        null      p_q = 0.0   (beta1 = 0 exactly)
        L&R 5.5   p_q = 5.5   (band low edge)
        L&R 6.5   p_q = 6.5   (band central --- the G1 parity leg)
        L&R 7.7   p_q = 7.7   (band high edge)
        Fonseca   p_q = 9.0   (delta_fonseca = 0.09)
  - Per-leg microsim parquets are written to an ISOLATED subdir
    (data/fonseca_band_anchor/, regenerable) so no existing floor_sweep
    parquet is touched.

GATES (hard-fail -> raise; do not interpret a failed run)
  G1  central parity: the L&R 6.5 leg reproduces the committed central
      $818.5300844066606B, null $748.1850239867648B, and lock-in marginal
      $70.34506041989584B (no_lockin_null_results.json), tol +/- $0.01B on
      levels and the marginal. (The band machinery's committed marginal is
      $70.34506041989584B; it equals the curtailment-demo-quoted
      $70.34506041989573B to 1.1e-13 B --- documented cross-run FP summation
      noise, both are "the committed +$70.345B central marginal".)
  G2  band-edge parity: the 5.5 and 7.7 legs reproduce
      extension_risk_band_literature.json ($809.9065834462376B /
      $827.6582704023259B), tol +/- $0.01B. (Confirms this run's machinery is
      the same one that produced the printed band, so Fonseca is placed on the
      identical scale.)
  G3  transform ordering: |beta1| strictly increasing across
      delta in {0.055, 0.065, 0.077, 0.09}, and |beta1_fonseca| > the L&R
      high edge |beta1(0.077)| (Fonseca is a stronger elasticity than the L&R
      band ceiling).
  G4  marginal ordering: lock-in marginal ($B and pp) strictly increasing in
      p_q across {0, 5.5, 6.5, 7.7, 9.0}; Fonseca marginal exceeds the L&R
      7.7 edge.
  G5  placement sanity: Fonseca marginal_pp lies inside the committed
      floor-and-band box [+2.11, +13.17] pp (box endpoints from the committed
      floor_band_cross_results.json --- (6% floor, 5.5) and (2% floor, 7.7)).

OUTPUT
  data/fonseca_band_anchor_results.json (spec echo, gates, all legs, key
  numbers, placement). No commits. Deterministic.

Run:  cd hazard && python3 fonseca_band_anchor.py
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import polars as pl

import floor_sweep
from config import LOAN_SAMPLE_PATH
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "fonseca_band_anchor_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
BAND_ARTIFACT = DATA_DIR / "extension_risk_band_literature.json"
BOX_ARTIFACT = DATA_DIR / "floor_band_cross_results.json"
ISOLATED_SWEEP_DIR = DATA_DIR / "fonseca_band_anchor"

PRODUCTION_FLOOR = 0.04  # config.INVOLUNTARY_CPR_ANNUAL

# Pre-committed grid (p_q_shock_pct == 100 * delta), production floor.
NULL_PQ = 0.0
LR_LOW_PQ = 5.5
LR_MID_PQ = 6.5     # G1 parity leg (delta = 0.065)
LR_HIGH_PQ = 7.7
FONSECA_PQ = 9.0    # delta_fonseca = 0.09  (pre-committed; see docstring)

# Committed central-leg marginal reproduced by the band machinery.
COMMITTED_MARGINAL_B = 70.34506041989584
TASK_QUOTED_MARGINAL_B = 70.34506041989573  # curtailment-demo value; == above to 1.1e-13 B
TOL_B = 0.01


def _leg(loans, empirical, pq: float, label: str) -> dict:
    """One production-convention microsim leg at the production 4% floor."""
    run = floor_sweep._run_scored(loans, empirical, PRODUCTION_FLOOR, pq)
    run["label"] = label
    run["beta1_signed"] = rothstein_beta1(pq / 100.0)
    run["beta1_abs"] = abs(run["beta1_signed"])
    return run


def main() -> None:
    ISOLATED_SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    # Isolate microsim parquets to our own subdir; touch no floor_sweep cache.
    floor_sweep.SWEEP_DIR = ISOLATED_SWEEP_DIR

    with open(NULL_ARTIFACT) as f:
        null_anchor = json.load(f)
    with open(BAND_ARTIFACT) as f:
        band_anchor = json.load(f)["results"]
    with open(BOX_ARTIFACT) as f:
        box = json.load(f)
    box_marginals = [c["marginal_pp"] for c in box["box_marginals_pp"]]
    box_lo, box_hi = min(box_marginals), max(box_marginals)

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    null = _leg(loans, empirical, NULL_PQ, "null")
    lr_low = _leg(loans, empirical, LR_LOW_PQ, "lr_low_5.5")
    lr_mid = _leg(loans, empirical, LR_MID_PQ, "lr_central_6.5")
    lr_high = _leg(loans, empirical, LR_HIGH_PQ, "lr_high_7.7")
    fonseca = _leg(loans, empirical, FONSECA_PQ, "fonseca_9.0")
    runtime_s = time.perf_counter() - t0

    null_b = null["trapped_b"]

    def marginal(run: dict) -> dict:
        return {
            "label": run["label"],
            "p_q_shock_pct": run["p_q_shock_pct"],
            "beta1_signed": run["beta1_signed"],
            "beta1_abs": run["beta1_abs"],
            "trapped_b": run["trapped_b"],
            "recovery_share_pct": run["share_pct"],
            "marginal_b": run["trapped_b"] - null_b,
            "marginal_pp": run["share_pct"] - null["share_pct"],
        }

    legs = {
        "null": marginal(null),
        "lr_low_5.5": marginal(lr_low),
        "lr_central_6.5": marginal(lr_mid),
        "lr_high_7.7": marginal(lr_high),
        "fonseca_9.0": marginal(fonseca),
    }
    for lab in ("null", "lr_low_5.5", "lr_central_6.5", "lr_high_7.7", "fonseca_9.0"):
        m = legs[lab]
        print(
            f"{lab:16s} p_q {m['p_q_shock_pct']:4.1f}  |b1| {m['beta1_abs']:.6f}  "
            f"${m['trapped_b']:8.3f}B ({m['recovery_share_pct']:7.3f}%)  "
            f"marginal ${m['marginal_b']:+7.3f}B ({m['marginal_pp']:+6.3f}pp)"
        )

    gates = {}

    # ---- G1 central parity ---------------------------------------------------
    g1_central = abs(lr_mid["trapped_b"] - null_anchor["central_trapped_b"]) < TOL_B
    g1_null = abs(null["trapped_b"] - null_anchor["null_trapped_b"]) < TOL_B
    g1_marg = abs(legs["lr_central_6.5"]["marginal_b"] - COMMITTED_MARGINAL_B) < TOL_B
    gates["G1_central_parity"] = {
        "central_trapped_b_got": lr_mid["trapped_b"],
        "central_trapped_b_want": null_anchor["central_trapped_b"],
        "null_trapped_b_got": null["trapped_b"],
        "null_trapped_b_want": null_anchor["null_trapped_b"],
        "marginal_b_got": legs["lr_central_6.5"]["marginal_b"],
        "marginal_b_want": COMMITTED_MARGINAL_B,
        "marginal_b_abs_err": abs(legs["lr_central_6.5"]["marginal_b"] - COMMITTED_MARGINAL_B),
        "bit_identical_to_committed": legs["lr_central_6.5"]["marginal_b"] == COMMITTED_MARGINAL_B,
        "equals_task_quoted_70.34506041989573_within": abs(
            legs["lr_central_6.5"]["marginal_b"] - TASK_QUOTED_MARGINAL_B
        ),
        "pass": bool(g1_central and g1_null and g1_marg),
    }

    # ---- G2 band-edge parity -------------------------------------------------
    g2_low = abs(lr_low["trapped_b"] - band_anchor["5.5"]["trapped_b"]) < TOL_B
    g2_high = abs(lr_high["trapped_b"] - band_anchor["7.7"]["trapped_b"]) < TOL_B
    gates["G2_band_edge_parity"] = {
        "low_5.5_got": lr_low["trapped_b"],
        "low_5.5_want": band_anchor["5.5"]["trapped_b"],
        "high_7.7_got": lr_high["trapped_b"],
        "high_7.7_want": band_anchor["7.7"]["trapped_b"],
        "pass": bool(g2_low and g2_high),
    }

    # ---- G3 transform ordering ----------------------------------------------
    b_seq = [
        abs(rothstein_beta1(d)) for d in (0.055, 0.065, 0.077, 0.09)
    ]
    g3_mono = all(a < b for a, b in zip(b_seq, b_seq[1:]))
    g3_above = fonseca["beta1_abs"] > lr_high["beta1_abs"]
    gates["G3_transform_ordering"] = {
        "beta1_abs_delta_0.055": b_seq[0],
        "beta1_abs_delta_0.065": b_seq[1],
        "beta1_abs_delta_0.077": b_seq[2],
        "beta1_abs_delta_0.090_fonseca": b_seq[3],
        "strictly_increasing": bool(g3_mono),
        "fonseca_above_lr_high_edge": bool(g3_above),
        "pass": bool(g3_mono and g3_above),
    }

    # ---- G4 marginal ordering ------------------------------------------------
    order = ["null", "lr_low_5.5", "lr_central_6.5", "lr_high_7.7", "fonseca_9.0"]
    marg_b_seq = [legs[k]["marginal_b"] for k in order]
    marg_pp_seq = [legs[k]["marginal_pp"] for k in order]
    g4_b = all(a < b for a, b in zip(marg_b_seq, marg_b_seq[1:]))
    g4_pp = all(a < b for a, b in zip(marg_pp_seq, marg_pp_seq[1:]))
    g4_fonseca = (
        legs["fonseca_9.0"]["marginal_b"] > legs["lr_high_7.7"]["marginal_b"]
        and legs["fonseca_9.0"]["marginal_pp"] > legs["lr_high_7.7"]["marginal_pp"]
    )
    gates["G4_marginal_ordering"] = {
        "marginal_b_sequence": marg_b_seq,
        "marginal_pp_sequence": marg_pp_seq,
        "strictly_increasing_b": bool(g4_b),
        "strictly_increasing_pp": bool(g4_pp),
        "fonseca_exceeds_lr_high": bool(g4_fonseca),
        "pass": bool(g4_b and g4_pp and g4_fonseca),
    }

    # ---- G5 placement sanity -------------------------------------------------
    fon_pp = legs["fonseca_9.0"]["marginal_pp"]
    g5 = box_lo <= fon_pp <= box_hi
    gates["G5_placement_in_box"] = {
        "fonseca_marginal_pp": fon_pp,
        "box_lo_pp": box_lo,
        "box_hi_pp": box_hi,
        "box_endpoints_source": "floor_band_cross_results.json (committed)",
        "inside_box": bool(g5),
        "pass": bool(g5),
    }

    all_pass = all(g["pass"] for g in gates.values())

    # Placement narrative vs the L&R production-floor band.
    lr_band_b = (legs["lr_low_5.5"]["marginal_b"], legs["lr_high_7.7"]["marginal_b"])
    lr_band_pp = (legs["lr_low_5.5"]["marginal_pp"], legs["lr_high_7.7"]["marginal_pp"])
    fon_b = legs["fonseca_9.0"]["marginal_b"]
    placement = {
        "fonseca_marginal_b": fon_b,
        "fonseca_marginal_pp": fon_pp,
        "fonseca_recovery_share_pct": legs["fonseca_9.0"]["recovery_share_pct"],
        "fonseca_trapped_b": legs["fonseca_9.0"]["trapped_b"],
        "lr_band_marginal_b_5.5_to_7.7": lr_band_b,
        "lr_band_marginal_pp_5.5_to_7.7": lr_band_pp,
        "lr_band_trapped_b_5.5_to_7.7": (
            legs["lr_low_5.5"]["trapped_b"], legs["lr_high_7.7"]["trapped_b"]
        ),
        "vs_lr_band": (
            "above_lr_high_edge" if fon_b > lr_band_b[1]
            else "inside_lr_band" if fon_b >= lr_band_b[0]
            else "below_lr_low_edge"
        ),
        "delta_above_lr_high_edge_b": fon_b - lr_band_b[1],
        "delta_above_lr_high_edge_pp": fon_pp - lr_band_pp[1],
        "vs_full_floor_band_box_pp": f"inside [{box_lo:.2f}, {box_hi:.2f}]"
        if g5 else f"OUTSIDE [{box_lo:.2f}, {box_hi:.2f}]",
        "slope_reading_crosscheck": (
            "Alternative Fonseca reading (0.57-1.20 pp/yr per 100bp, L219) on a "
            "~9-10% annual mover base is a ~6-13% proportional reduction, "
            "bracketing the 9% point used here; the point anchor is not "
            "knife-edge."
        ),
    }

    payload = {
        "mode": "fonseca_band_anchor",
        "roadmap_item": "R18-B optional leg (M2/Q5 second literature anchor)",
        "spec": (
            "delta_fonseca = 0.09 (p_q 9.0), pre-committed single point from the "
            "manuscript's own eq:beta1 footnote ('roughly 9% reduction in moving "
            "rates per pp of mortgage-rate delta'); fed through the SAME "
            "rothstein_beta1 transform and the SAME floor_sweep._run_scored band "
            "machinery at the production 4% floor; five legs (null, L&R "
            "5.5/6.5/7.7, Fonseca 9.0) in one macro fetch; corroboration-only, "
            "not a change to the headline L&R band. Unit caveats: L&R = "
            "proportional quarterly-mobility decline per 100bp rate gap vs "
            "Fonseca = proportional moving-rate reduction per pp mortgage-rate "
            "delta (manuscript: 'related but distinct'); 9% treated "
            "quarterly-equivalent, licensed by transform frequency-invariance "
            "(small-P_q beta1 = -ln(1-delta)); mobility-derived delta applied to "
            "a prepayment hazard = upper bound on the voluntary contribution."
        ),
        "delta_fonseca": 0.09,
        "beta1_fonseca_signed": fonseca["beta1_signed"],
        "beta1_fonseca_abs": fonseca["beta1_abs"],
        "beta1_lr_central_abs": lr_mid["beta1_abs"],
        "beta1_lr_band_abs_5.5_to_7.7": (lr_low["beta1_abs"], lr_high["beta1_abs"]),
        "legs": legs,
        "placement": placement,
        "gates": gates,
        "gates_all_pass": bool(all_pass),
        "committed_central_marginal_b": COMMITTED_MARGINAL_B,
        "benchmark_b": 764.7,
        "isolated_sweep_dir": str(ISOLATED_SWEEP_DIR),
        "runtime_s": round(runtime_s, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(
            payload, f, indent=2,
            default=lambda x: float(x)
            if isinstance(x, (np.floating, np.integer)) else x,
        )
        f.write("\n")

    print("\n--- gates ---")
    for name, g in gates.items():
        print(f"{name}: {'PASS' if g['pass'] else 'FAIL'}")
    print(
        f"\nFonseca (delta 0.09): beta1={fonseca['beta1_signed']:.6f} "
        f"(|{fonseca['beta1_abs']:.6f}|)  marginal ${fon_b:+.4f}B "
        f"({fon_pp:+.4f}pp)  recovery {legs['fonseca_9.0']['recovery_share_pct']:.3f}%"
    )
    print(
        f"placement vs L&R band: {placement['vs_lr_band']}  "
        f"(+{placement['delta_above_lr_high_edge_pp']:.3f}pp above the 7.7 edge); "
        f"{placement['vs_full_floor_band_box_pp']}"
    )
    print(f"Results saved to {RESULTS_JSON}")

    if not all_pass:
        raise SystemExit(
            "GATE FAILURE — results written for diagnosis but must not be cited: "
            + ", ".join(k for k, g in gates.items() if not g["pass"])
        )


if __name__ == "__main__":
    main()
