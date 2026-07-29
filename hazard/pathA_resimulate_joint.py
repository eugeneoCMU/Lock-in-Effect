#!/usr/bin/env python3
"""
pathA_resimulate_joint.py — Path A's refit-and-resimulate interval rebuilt on
the JOINT coefficient draw (round-28 WP-C6(ii); R1: the committed construction
holds the age spline at production while drawing only the macro block, which is
precisely the independence objected to).

PRE-COMMITTED SPEC (fixed BEFORE any run; drafting spec at
specs/SPEC_round28_C1_C2_C3_C6.md SPEC C6(ii); gates, tolerances, expectations
and landing branches adopted unchanged except where LABELED below).

DESTRUCTIVE-RUN HAZARD (spec C6.0 — read this before running anything).
bootstrap_se.py:298 passes draws_csv=BOOTSTRAP_DRAWS_CSV, HARD-CODED; --out
only redirects the JSON; and bootstrap_se.py:286 sets seasonal from the
PRODUCTION artifact, which is now spec v4. Running `python3
hazard/bootstrap_se.py` today would overwrite hazard/data/
hazard_bootstrap_draws.csv — the committed spec-v3 draw set that tab:bootstrap
(tex 1088) and bootstrap_resimulate_results.json both rest on — AND would do it
at the wrong spec. bootstrap_se.py and bootstrap_resimulate.py are therefore
IMPORTED here for their functions and NEVER invoked as __main__; every output
of this script goes to a NEW path (listed under ARTIFACTS below);
hazard_bootstrap_draws.csv, hazard_bootstrap_se.json,
bootstrap_resimulate_results.json, hazard_coefficients.json and
hazard_coefficients_specv3.json are opened READ-ONLY.

STRUCTURAL FINDING carried from the spec (C6.0b): R1's ask is not literally
executable at the FE level. resample_strata (bootstrap_se.py:55-70) relabels
every drawn stratum f"{sid}__b{k:03d}" so duplicated strata carry independent
fixed effects, and bootstrap_resimulate's own docstring says replication FEs do
not map back to production pools. C6(ii) is therefore two-tiered, and tier 1 is
the object that actually repairs the broken joint distribution.

ENGINE — two stages, both new, neither invoking bootstrap_se.main():
  Stage A (pathA_bootstrap_fullvec): run_bootstrap's logic (bootstrap_se.py:
  198-256) copied and extended to persist, per converged replicate, the FULL
  params_head (11 entries at v3 / 22 at v4), gap_std / burn_std / fric_std,
  fit_method, and — for tier 2 — the FE block with the stratum_id_src <->
  bootstrap-label map resample_strata already retains (line 67).
  resample_strata itself is imported verbatim so the RNG stream is consumed
  exactly as the committed run consumed it (one rng.choice per replication,
  failures included).
  Stage B: bootstrap_resimulate.py's loop (lines 64-91) copied, with the
  coefficient dict built from the replicate's full head instead of the 3 macro
  betas; its sim_mod.fetch_data patch (single FRED fetch) and its every-10-reps
  checkpoint are kept.

UNITS, AND THE TRAP IN THEM (spec C6(ii)). rescale_to_production_units exists
because the three macro regressors are standardized PER REPLICATE
(bootstrap_se.py:107-111, 186-195). The age spline and intercept are NOT
standardized (fit_betas:99, raw _age_spline_basis) and the month dummies are
raw 0/1 (hazard_fit._month_dummy_matrix). Therefore:
  * const + 7 age-spline coefficients + 11 month coefficients transfer
    DIRECTLY, UNRESCALED;
  * only the 3 macro coefficients are rescaled.
Do NOT rescale the age spline. Do NOT simulate with a replicate's own
standardization constants against production regressors: the prediction scales
consumed by simulate.simulate_qt_window come from the coefficient artifact
(hazard_fit.load_predict_scales), which stays at production in every tier.

LABELED DEVIATIONS from the drafted spec (all forced by the code; none silent):
  1. MONTH COEFFICIENTS DO NOT TRAVEL IN `coefs`. simulate.simulate_qt_window
     reads month_effects from the ARTIFACT PATH, not from the coefs dict
     (simulate.py:126, load_month_effects(coef_path)), and predict_hazard's
     linear predictor has no month terms at all. Per-replicate seasonality is
     therefore delivered by writing a TEMPORARY coefficient artifact (a copy of
     the spec's production artifact with .coefficients and .month_effects
     swapped, every prediction scale left at production) and passing
     coef_path=<temp>. The temp file lives at a new _pathA_joint_coefs.json and
     is deleted at the end.
  2. THE SPEC-V3 LEG MUST NOT USE THE DEFAULT coef_path. bootstrap_resimulate
     ran when HAZARD_COEF_PATH was still spec v3 (its committed point is
     915.067027857209 B, whereas the v4 production simulation is
     928.892970289881 B — pathA_seasonal_adoption_results.json). The default
     coef_path is now the v4 artifact, so reproducing the committed interval
     requires coef_path=hazard_coefficients_specv3.json explicitly. Using the
     default would silently score a different specification.
  3. STAGE A's v4 POINT FIT IS WARM-STARTED. run_bootstrap computes its
     warm-start head from a COLD point fit (bootstrap_se.py:208, no
     start_head), which at v4 is the ddof-1 seasonal cold fit that
     pathA_seasonal_adoption.py:11-21 records as landing "a different,
     incompletely converged penalized optimum" (its first attempt FAILED Gate
     B there). Propagating that head to 200 replications would make the v4 leg
     uninterpretable. The v4 point fit here is warm-started from
     production_start_head; the COLD v4 point fit is still computed and its
     macro triple recorded as `point_cold_v4`, because the gap between the two
     is itself a measurement of the branch-instability claim. The v3 leg is
     verbatim (cold), because P1 requires it.
  4. TIER 2's FE ARE RELATIVE TO A DIFFERENT ABSORBED LEVEL. Each replicate's
     FE are identified against whichever bootstrap label sorts first, not
     against the production reference 2017_200_740+_<=80, so the tier-2 map
     carries an unremoved level shift on top of the averaging rule. This is a
     further reason tier 2 is arbitrary; it is disclosed in the artifact and
     tier 2 enters NO manuscript number.
  5. G0 added (not in the spec): the extended fit function must reproduce
     bootstrap_se.fit_betas field-for-field on the production panel at both
     specs, since fit_betas returns neither the FE block nor the absorbed
     label and therefore could not be used directly.

AMENDMENT A7 (labeled, POST-RUN, 2026-07-29; appended to the drafting spec
after the first Stage-B v3 execution — adopted here verbatim). Stage B v3
realized verdict NARROWS (joint [689.0, 1217.6]B, width ratio 0.094), but
106/198 draws sat at EXACTLY the accounting ceiling $1217.6339B — the value
score_extension_risk returns when the simulated roll-off is identically zero,
i.e. minus the sum of the QT target series — and the saturated draws are the
rogue-optimizer-mode replicates (mean rate_gap +2.2317, burnout -0.1428,
friction +0.6748 with the sign flipped; the committed hazard_bootstrap_draws.csv
itself has rate_gap mean 1.4914, so the COMMITTED population is bimodal and the
rogue mode is the optimizer-path artifact the paper documents at the
reference-swap site). At QT gaps near -380bp a rate-gap coefficient of +2.2
drives the hazard to e^-8.4 ~ 0, hence saturation. The committed 3-beta
rendering of the SAME rogue draws produced the -$4,460B tail; the joint
rendering piles them on the ceiling instead: two renderings of one pathology,
and neither tail is a sampling statement about the estimand. A7 requires,
before ANY landing:
  A7(1) the aggregation must index only the specs that ran — a --specs 4 or
        --stage B invocation previously raised KeyError on
        gates["P3_point_head"]["spec3"]. It is now recovered from the persisted
        Stage-A summary when one exists, else marked PENDING, excluded from
        all_pass, and warned about on the console and in .parity_gates_pending.
  A7(2) a NEW BLOCKING Stage-B parity leg, run automatically at the start of
        every stage-B invocation BEFORE any replicate is scored: the PRODUCTION
        head pushed through stage_b's exact coefficient handoff must reproduce
        the committed 915.067027857209 B at v3 within $0.50B. On failure the
        whole Stage B construction is void — wiring, not finding — and the run
        aborts rather than spending 198 simulations. The v4 leg runs against
        928.892970289881 B and is recorded non-blocking (A7 mandates v3).
  A7(3) Stage B reported under BOTH decompositions — a mechanical-bound cut and
        a production-vs-rogue cut — with n, trapped_b and share_pct per cell
        and a cross-tab, the headline results block keeping the full-sample
        numbers. *** A7 AS DRAFTED SPECIFIED BOTH CUTS WRONG; the operative
        definitions are A7-C1 and A7-C2 below, and the field names are
        floor_b / n_at_floor / decompositions.{saturation,mode}. ***
  A7(4) the verdict is re-adjudicated on the pre-committed codes ON THE FULL
        SAMPLE (no code change) and carries verdict.floor_disclosure
        (mandatory) and verdict.production_mode_only (a labeled sub-population,
        never the quoted interval). The provisional NARROWS is NOT accepted as
        adjudicated.

A7 CORRECTIONS (labeled, POST-RERUN, 2026-07-29). The A7 rerun validated the
point-head parity leg at |Δ| = $0.0000B for BOTH specs — the coefficient handoff
is proven — but exposed two wrong constants in the A7 machinery itself:
  A7-C1 WRONG BOUND OBJECT. −Σ QT_Target came to $1417.50B and 0 of 198 draws
        sat there, VACUOUSLY: a pool with zero VOLUNTARY prepayment still
        amortizes scheduled principal (~$200B across the window). The bound the
        first run's 106 draws actually piled at ($1217.6339179089177, share
        159.22%) is the ZERO-VOLUNTARY-PREPAYMENT FLOOR. It is now MEASURED, not
        derived: one probe simulation through stage_b's own machinery with the
        head's rate-gap coefficient set to +50.0, so that at QT-era gaps every
        out-of-the-money month is driven past predict_hazard's lower clip. The
        probe's trapped_b IS the floor, by construction. −Σ targets is retained
        as a recorded audit number (target_sum_audit) and adjudicates nothing.
        Everything named "ceiling" is renamed "zero_voluntary_floor".
        Precision worth keeping: the pile-up is exact because predict_hazard
        CLIPS log_mu at −20, so every sufficiently rogue draw shares the
        identical exp(−20) hazard path — it is the clip, not underflow to zero.
  A7-C2 WRONG BRANCH RULE (the coordinator's own labeled spec error). The 0.02
        same-data optimizer-basin rule labelled 185 of 198 legitimate bootstrap
        draws "rogue": resampled panels scatter the macro coefficients by
        ~0.1–0.6 on their own, so a basin rule written for optimizer starts on
        ONE panel cannot classify draws across 200 panels. The population is
        bimodal in the rate gap and its two modes are the two documented
        attractors, so the cut is NEAREST KNOWN ATTRACTOR in rate_gap:
        production = COEF_PATH[spec].coefficients.rate_gap_bps (v3 value for
        spec-3 legs, v4 for spec-4 legs), rogue =
        ridge_reference_weighting.json .reference_swap.betas_swapped_ref
        .rate_gap_bps — both READ, never hard-coded — with the midpoint as
        cutpoint. Both attractors, the cutpoint and each cell's drawn-macro
        means are recorded. The 0.02-rule counts survive as
        legacy_same_data_basin_rule, labelled "same-data basin rule; too strict
        for resampled draws", non-adjudicating.
  A guard added with them: decompose reports the EMPIRICAL MODE of trapped_b
  (value and count) next to the probe floor and flags whether they coincide, so
  a probe that measures the wrong object announces itself instead of silently
  reporting zero saturated draws — the exact way A7-C1 slipped through.
  verdict.production_branch_only is renamed verdict.production_mode_only.

PARITY GATES:
  A7 (BLOCKING) point-head parity — see amendment A7(2) above. VALIDATED on the
     rerun at |Δ| = $0.0000B for spec v3 and spec v4.
  P1 (BLOCKING) Stage A at spec v3, seed 42, alpha=1e-4 reproduces
     hazard_bootstrap_draws.csv ROW-FOR-ROW to 1e-12 (198 rows) and
     hazard_bootstrap_se.json .se / .ci_95 / .frac_le_0 to 1e-9. Without P1
     nothing downstream is interpretable.
  P2 Stage B with the head FORCED to production except the 3 macro betas
     (reading the COMMITTED draws CSV) reproduces bootstrap_resimulate_results
     .json trapped_b.{mean, median, ci_95} to 1e-6.
  P3 the point head reproduces hazard_coefficients_specv3.json (v3) /
     hazard_coefficients.json (v4) macro coefficients to 1e-9. NOTE at v4 this
     is subject to the ddof-1 vs ddof-0 standardization fork documented in
     pathA_ridge_v4.py DEVIATION 1 (production v4 came from
     seasonality_concave_gap.fit_with_month_dummies, numpy ddof=0; fit_betas is
     pandas ddof=1): the v4 leg of P3 is recorded with both the literal and the
     x sqrt(n/(n-1)) adjusted comparison and is NON-BLOCKING at v4.
  G0 extended-fit parity against bootstrap_se.fit_betas (1e-12), BLOCKING.

PRE-COMMITTED EXPECTATION (R1's own: "verdict survives, interval possibly
widens — strengthening the exclusion"). Committed spec-v3 baseline
(bootstrap_resimulate_results.json): point 915.067027857209 B /
119.65598142932075 %; median 922.6022056753297 B; mean 598.8526094183436 B
(78.307156230137 %); 95% percentile [-4459.7936261770865, +1190.1355126947665]
B; frac_above_benchmark 0.8383838383838383. Drawing the age spline jointly with
the macro block adds baseline-shape variance to a 42-month forward compounding
already destabilized by 15 replications (tex 981), so the interval is expected
to WIDEN, the mean to fall, and the "no useful forward precision" verdict to
hold a fortiori. PRE-COMMITTED DIRECTION: |ci_95| width >= the committed width.
A narrowing is the surprise. Spec v4 replications are the ones the paper calls
branch-unstable (tex 623, 981): expect a HIGHER failure count than 2/200 and
report it as a finding either way.

LANDING RULE (ex ante; ALL tex landings queue for Eugene; Path A is excluded
from every headline figure — tex 290, 978, 1053 — so NOTHING propagates):
  (ii-a) SURVIVES_WIDER / SURVIVES_UNCHANGED (expected): tex 981's "Propagated
         coefficient uncertainty therefore leaves the forward simulation with
         no useful precision…" gains one clause naming the joint construction
         and the wider interval; the preceding sentences' numbers (median
         $922.6B, IQR $900.1--$1,130.6B, 95% $[-4,459.8, +1,190.1]$B, mean
         $598.9B / 78.3%, share interval [-583.2%, +155.6%], SE 201.9, 83.8%
         above benchmark) are restated at the joint values; tex 400's
         tab:estimators note is updated for provenance.
  (ii-b) NARROWS materially (>20% narrower): the joint construction is MORE
         favorable to Path A than the current one. DO NOT adopt it as the
         headline Path A interval. Report both, keep the wider committed
         interval as the quoted one, state that the joint construction is
         narrower.                                    [posture] flag to Eugene.
  (ii-c) V4_UNSTABLE — spec-v4 replications fail at a materially higher rate
         than 2/200: this is the "branch-unstable" claim at tex 623/981
         MEASURED rather than asserted. Land the measured failure count in tex
         981 in place of the qualitative claim. Good outcome; land it either
         way the interval goes.
  Verdict precedence: NARROWS > V4_UNSTABLE > SURVIVES_WIDER /
  SURVIVES_UNCHANGED. "Materially higher" is pre-committed at >= 10/200 (5%),
  and the exact count is reported regardless.

ARTIFACTS (all NEW paths):
  data/pathA_bootstrap_fullvec_draws_specv3.csv   data/…_specv4.csv
  data/pathA_bootstrap_fullvec_fe_specv3.npz      data/…_specv4.npz
  data/pathA_resimulate_joint_simdraws_spec{3,4}_tier{1,2}.csv  (checkpoints)
  data/pathA_resimulate_joint_p2_simdraws.csv                   (checkpoint)
  data/pathA_resimulate_joint_pointhead_spec{3,4}.csv           (A7(2) leg)
  data/pathA_resimulate_joint_floorprobe_spec{3,4}.csv          (A7-C1 probe)
  data/pathA_resimulate_joint_results.json

MUST NOT CHANGE (spec C6.7): hazard/bootstrap_se.py,
hazard/bootstrap_resimulate.py, hazard/ridge_reference_weighting.py,
hazard/pathA_seasonal_adoption.py, hazard/pathA_v4_holdout.py,
hazard/config.py; hazard_bootstrap_draws.csv and hazard_bootstrap_se.json above
all; hazard_coefficients.json, hazard_coefficients_specv3.json,
ridge_reference_weighting.json, bootstrap_resimulate_results.json,
pathA_v4_holdout_results.json, pathA_seasonal_adoption_results.json. Path A's
$928.9B / 121.5% and its exclusion from every headline figure. NO Path A result
may enter any headline number under any branch.

Run (stages are separable and every stage checkpoints; measure one leg before
committing to the full battery):
  cd hazard
  python3 pathA_resimulate_joint.py --stage A --specs 3            # P1 first
  python3 pathA_resimulate_joint.py --stage P2                     # 198 sims
  python3 pathA_resimulate_joint.py --stage A --specs 4
  python3 pathA_resimulate_joint.py --stage B --specs 3,4 --tiers 1,2
  python3 pathA_resimulate_joint.py --stage report
COST: Stage A is 2 x ~200 GLM fits; Stage B is ~198 forward simulations per
(spec x tier) leg plus 198 for P2 — budget it, use --limit to measure s/rep
first, and --resume to continue a checkpointed leg.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm

import simulate as sim_mod
from bootstrap_se import (
    BETA_NAMES,
    BOOTSTRAP_DRAWS_CSV,
    BOOTSTRAP_RESULTS_PATH,
    MAX_ABS_BETA,
    fit_betas,
    production_start_head,
    resample_strata,
    rescale_to_production_units,
)
from config import (
    AGE_SPLINE_KNOTS,
    HAZARD_COEF_PATH,
    HOLDOUT_DATE,
    MARKOV_MATRIX_PATH,
    PANEL_PATH,
)
from extension_risk import score_extension_risk
from hazard_fit import (
    _age_spline_basis,
    _fit_poisson_glm,
    _month_dummy_matrix,
    _orthogonalize_burnout,
    enrich_panel_with_macro,
)
from macro import (
    build_empirical_metrics,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
)
from markov import load_transition_matrix

DATA_DIR = Path(__file__).parent / "data"
V3_COEF_PATH = DATA_DIR / "hazard_coefficients_specv3.json"      # frozen
V4_COEF_PATH = Path(HAZARD_COEF_PATH)                            # frozen
COMMITTED_RESIM = DATA_DIR / "bootstrap_resimulate_results.json"  # frozen

FULLVEC_CSV = {3: DATA_DIR / "pathA_bootstrap_fullvec_draws_specv3.csv",
               4: DATA_DIR / "pathA_bootstrap_fullvec_draws_specv4.csv"}
FULLVEC_NPZ = {3: DATA_DIR / "pathA_bootstrap_fullvec_fe_specv3.npz",
               4: DATA_DIR / "pathA_bootstrap_fullvec_fe_specv4.npz"}
RESULTS_JSON = DATA_DIR / "pathA_resimulate_joint_results.json"
P2_CSV = DATA_DIR / "pathA_resimulate_joint_p2_simdraws.csv"
TMP_SIM = DATA_DIR / "_pathA_joint_tmp.parquet"
TMP_COEF = DATA_DIR / "_pathA_joint_coefs.json"


def simdraws_csv(spec: int, tier: int) -> Path:
    return DATA_DIR / f"pathA_resimulate_joint_simdraws_spec{spec}_tier{tier}.csv"


def pointhead_csv(spec: int) -> Path:
    return DATA_DIR / f"pathA_resimulate_joint_pointhead_spec{spec}.csv"


def floorprobe_csv(spec: int) -> Path:
    return DATA_DIR / f"pathA_resimulate_joint_floorprobe_spec{spec}.csv"


TOL_P1_ROWS = 1e-12
TOL_P1_SUMMARY = 1e-9
TOL_P2 = 1e-6
TOL_P3 = 1e-9
TOL_G0 = 1e-12

NARROW_THRESHOLD = 0.80         # (ii-b): >20% narrower
V4_FAILURE_MATERIAL = 10        # (ii-c): >= 10/200 is "materially higher"
COMMITTED_N_FAILED_V3 = 2

# --- amendment A7 (2026-07-29) ------------------------------------------------
# A7(2): the point-head parity leg. The committed forward-simulation points the
# production head must reproduce THROUGH stage_b's own handoff.
POINT_PARITY_TOL_B = 0.50
COMMITTED_POINT_B = {
    3: 915.067027857209,        # bootstrap_resimulate_results.json .point_trapped_b
    4: 928.892970289881,        # pathA_seasonal_adoption_results.json .v4_trapped_b
}
POINT_PARITY_BLOCKING_SPECS = (3,)   # A7 mandates v3; v4 recorded, non-blocking
# A7(3), as CORRECTED after the first A7 rerun (see A7-C1/A7-C2 in the header).
SATURATION_TOL_B = 1e-6              # |trapped − floor| < 1e-6 ⇒ saturated
FLOOR_PROBE_CONST = -1e6            # A7-C1b: clip-everywhere probe          # drives every OTM month past predict_hazard's clip
LEGACY_BASIN_TOL = 0.02              # retired same-data basin rule, diagnostic only
RIDGE_REF_JSON = DATA_DIR / "ridge_reference_weighting.json"   # frozen, read-only

AGE_NAMES = ["age_linear"] + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
MONTH_NAMES = [f"m_{m}" for m in range(2, 13)]
HEAD_NAMES = {3: ["const"] + AGE_NAMES + BETA_NAMES,
              4: ["const"] + AGE_NAMES + BETA_NAMES + MONTH_NAMES}
COEF_PATH = {3: V3_COEF_PATH, 4: V4_COEF_PATH}


def _np(o):
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(f"not serializable: {type(o)}")


# --------------------------------------------------------------------------
# Stage A — bootstrap_se.fit_betas + FE block + absorbed label
# --------------------------------------------------------------------------
def fit_betas_ext(train: pd.DataFrame, ridge_alpha: float,
                  start_head: np.ndarray | None = None,
                  seasonal: bool = False) -> dict:
    """bootstrap_se.fit_betas (lines 76-167) copied VERBATIM and extended to
    return the FE block, the FE column labels and the absorbed (reference)
    label. fit_betas itself returns none of those (it returns params_head
    only), which is why it cannot be called directly here; G0 gates this copy
    against it."""
    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean = (
        train.groupby("stratum_id")["burnout"]
        .transform(lambda s: s - s.mean())
        .to_numpy()
    )
    burnout_orth, _ = _orthogonalize_burnout(age_basis, burn_demean)

    friction_mean = float(train["friction"].mean())
    friction_std = float(train["friction"].std()) or 1.0
    gap_mean = float(train["rate_gap_bps"].mean())
    gap_std = float(train["rate_gap_bps"].std()) or 1.0
    burn_std = float(burnout_orth.std()) or 1.0

    dummies = pd.get_dummies(
        train["stratum_id"], prefix="fe_stratum", drop_first=True
    )
    fe_columns = list(dummies.columns)
    # pd.get_dummies(drop_first=True) drops the FIRST sorted level
    absorbed = sorted(train["stratum_id"].unique())[0]
    dummies = dummies.to_numpy(dtype=np.float64)

    blocks = [
        age_basis,
        (train["rate_gap_bps"].to_numpy() - gap_mean) / gap_std,
        burnout_orth / burn_std,
        (train["friction"].to_numpy() - friction_mean) / friction_std,
    ]
    if seasonal:
        blocks.append(_month_dummy_matrix(train["period"]))
    blocks.append(dummies)
    X = np.column_stack(blocks)
    X = sm.add_constant(X, has_constant="add")

    y_events = train["events"].to_numpy()
    offset = np.log(train["exposure"].to_numpy())
    k = age_basis.shape[1]

    if start_head is None:
        result, fit_method = _fit_poisson_glm(X, y_events, offset, ridge_alpha)
    else:
        start = np.zeros(X.shape[1])
        start[: len(start_head)] = start_head
        model = sm.GLM(y_events, X, family=sm.families.Poisson(), offset=offset)
        try:
            irls = model.fit(maxiter=100, start_params=start)
            warm = (irls.params if np.isfinite(np.asarray(irls.params)).all()
                    else start)
        except (ValueError, np.linalg.LinAlgError):
            warm = start
        result = model.fit_regularized(
            method="elastic_net", alpha=ridge_alpha, L1_wt=0.0,
            maxiter=100, start_params=warm,
        )
        fit_method = f"ridge(alpha={ridge_alpha}, warm_start)"

    params = np.asarray(result.params, dtype=np.float64).ravel()
    macro = params[1 + k: 4 + k]
    if not np.isfinite(params).all() or np.abs(macro).max() > MAX_ABS_BETA:
        raise RuntimeError(
            f"non-converged fit (max |macro beta| = {np.abs(macro).max():.3g})"
        )
    head_len = 4 + k + (11 if seasonal else 0)
    return {
        "rate_gap_bps": float(params[1 + k]),
        "burnout_orth": float(params[2 + k]),
        "friction": float(params[3 + k]),
        "gap_std": gap_std,
        "burn_std": burn_std,
        "fric_std": friction_std,
        "fit_method": fit_method,
        "params_head": params[:head_len].copy(),
        "fe_values": params[head_len:].copy(),
        "fe_columns": fe_columns,
        "absorbed_label": absorbed,
    }


def gate_g0(train: pd.DataFrame, alpha: float, head_v4: np.ndarray) -> dict:
    """fit_betas_ext must reproduce bootstrap_se.fit_betas field-for-field."""
    checks = {}
    for spec, kwargs in ((3, {"seasonal": False}),
                         (4, {"seasonal": True, "start_head": head_v4})):
        a = fit_betas(train, alpha, **kwargs)
        b = fit_betas_ext(train, alpha, **kwargs)
        d = max(
            [abs(a[n] - b[n]) for n in BETA_NAMES]
            + [abs(a["gap_std"] - b["gap_std"]),
               abs(a["burn_std"] - b["burn_std"]),
               abs(a["fric_std"] - b["fric_std"]),
               float(np.abs(np.asarray(a["params_head"])
                            - np.asarray(b["params_head"])).max())]
        )
        checks[f"spec{spec}"] = {
            "max_abs_diff": float(d),
            "fit_method_match": bool(a["fit_method"] == b["fit_method"]),
            "head_len": int(len(b["params_head"])),
            "pass": bool(d <= TOL_G0 and a["fit_method"] == b["fit_method"]),
        }
    return {"tol": TOL_G0, "checks": checks, "blocking": True,
            "pass": all(c["pass"] for c in checks.values())}


def load_train() -> pd.DataFrame:
    """bootstrap_se.main()'s training frame (lines 278-283), verbatim."""
    panel = pl.read_parquet(PANEL_PATH)
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    return pdf[pdf["period"] < HOLDOUT_DATE].copy()


def stage_a(train: pd.DataFrame, spec: int, n_reps: int, ridge_alpha: float,
            seed: int, prod_scales: dict, head_v4: np.ndarray) -> dict:
    """run_bootstrap's logic (bootstrap_se.py:198-256), copied and extended.
    The RNG stream is consumed identically: one resample_strata per rep,
    failures included."""
    seasonal = (spec == 4)
    names = HEAD_NAMES[spec]

    point_cold = fit_betas_ext(train, ridge_alpha, seasonal=seasonal)
    if seasonal:
        # DEVIATION 3: the v4 warm-started point fit supplies the head
        point = fit_betas_ext(train, ridge_alpha, seasonal=True,
                              start_head=head_v4)
    else:
        point = point_cold
    start_head = point["params_head"]
    print(f"  spec v{spec} point fit ({point['fit_method']}): "
          + ", ".join(f"{n}={point[n]:+.6f}" for n in BETA_NAMES))

    rng = np.random.default_rng(seed)
    rows, fe_store = [], {}
    n_failed = 0
    t0 = time.perf_counter()
    for i in range(n_reps):
        boot = resample_strata(train, rng)
        try:
            b = fit_betas_ext(boot, ridge_alpha, start_head=start_head,
                              seasonal=seasonal)
        except Exception as exc:
            n_failed += 1
            rows.append({"rep": i, "converged": False, "fit_method": "",
                         "failure": repr(exc)[:160]})
            print(f"  rep {i + 1}/{n_reps}: FAILED ({exc})")
            continue
        r = rescale_to_production_units(b, prod_scales)
        row = {"rep": i, "converged": True, "fit_method": b["fit_method"],
               "failure": "",
               "gap_std": b["gap_std"], "burn_std": b["burn_std"],
               "fric_std": b["fric_std"]}
        row.update({f"head_{n}": float(v)
                    for n, v in zip(names, b["params_head"])})
        row.update({f"resc_{n}": float(r[n]) for n in BETA_NAMES})
        rows.append(row)
        fe_store[f"fe_val_{i}"] = b["fe_values"]
        fe_store[f"fe_src_{i}"] = np.array(
            [c[len("fe_stratum_"):].split("__b")[0] for c in b["fe_columns"]],
            dtype=object)
        fe_store[f"absorbed_src_{i}"] = np.array(
            b["absorbed_label"].split("__b")[0], dtype=object)
        pd.DataFrame(rows).to_csv(FULLVEC_CSV[spec], index=False)  # checkpoint
        if (i + 1) % 10 == 0 or i == 0:
            el = time.perf_counter() - t0
            print(f"  rep {i + 1}/{n_reps}  "
                  f"({el / (i + 1):.1f}s/rep, {el:.0f}s elapsed)")

    df = pd.DataFrame(rows)
    df.to_csv(FULLVEC_CSV[spec], index=False)
    fe_store["production_strata"] = np.array(
        sorted(train["stratum_id"].unique()), dtype=object)
    np.savez_compressed(FULLVEC_NPZ[spec], **fe_store)

    ok = df[df["converged"]]
    draws = {n: ok[f"resc_{n}"].to_numpy(dtype=float) for n in BETA_NAMES}
    summary = {
        "spec_version": spec, "seasonal_design": seasonal,
        "n_reps": n_reps, "n_failed": n_failed, "n_converged": int(len(ok)),
        "ridge_alpha": ridge_alpha, "seed": seed, "cluster": "stratum",
        "alpha_reselected_per_rep": False,
        "production_scales": prod_scales,
        "point_head": {n: float(v) for n, v in zip(names, point["params_head"])},
        "point_fit_method": point["fit_method"],
        "point_native_units": {n: point[n] for n in BETA_NAMES},
        "point_production_units": rescale_to_production_units(point, prod_scales),
        "point_cold_native_units": {n: point_cold[n] for n in BETA_NAMES},
        "point_cold_fit_method": point_cold["fit_method"],
        "se": {n: float(np.std(draws[n], ddof=1)) for n in BETA_NAMES},
        "ci_95": {n: {"lo": float(np.percentile(draws[n], 2.5)),
                      "hi": float(np.percentile(draws[n], 97.5))}
                  for n in BETA_NAMES},
        "frac_le_0": {n: float(np.mean(draws[n] <= 0)) for n in BETA_NAMES},
        "draws_csv": str(FULLVEC_CSV[spec].name),
        "fe_npz": str(FULLVEC_NPZ[spec].name),
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    return summary


def gate_p1(spec3_summary: dict) -> dict:
    """Stage A at spec v3 vs the two committed artifacts."""
    committed_rows = pd.read_csv(BOOTSTRAP_DRAWS_CSV)
    assert list(committed_rows.columns) == BETA_NAMES, committed_rows.columns
    mine = pd.read_csv(FULLVEC_CSV[3])
    mine = mine[mine["converged"].astype(bool)].reset_index(drop=True)
    row_check = {"n_committed": int(len(committed_rows)),
                 "n_replayed": int(len(mine))}
    if len(mine) == len(committed_rows):
        d = max(float(np.abs(mine[f"resc_{n}"].to_numpy(dtype=float)
                             - committed_rows[n].to_numpy(dtype=float)).max())
                for n in BETA_NAMES)
        row_check["max_abs_row_diff"] = d
        row_check["pass"] = bool(d <= TOL_P1_ROWS)
    else:
        row_check["max_abs_row_diff"] = None
        row_check["pass"] = False

    committed_se = json.loads(Path(BOOTSTRAP_RESULTS_PATH).read_text())
    summary_diffs = []
    for n in BETA_NAMES:
        summary_diffs.append(abs(spec3_summary["se"][n] - committed_se["se"][n]))
        summary_diffs.append(abs(spec3_summary["ci_95"][n]["lo"]
                                 - committed_se["ci_95"][n]["lo"]))
        summary_diffs.append(abs(spec3_summary["ci_95"][n]["hi"]
                                 - committed_se["ci_95"][n]["hi"]))
        summary_diffs.append(abs(spec3_summary["frac_le_0"][n]
                                 - committed_se["frac_le_0"][n]))
    sd = float(max(summary_diffs))
    return {
        "blocking": True,
        "rows": {**row_check, "tol": TOL_P1_ROWS},
        "summary": {"max_abs_diff": sd, "tol": TOL_P1_SUMMARY,
                    "pass": bool(sd <= TOL_P1_SUMMARY)},
        "n_failed": {"got": spec3_summary["n_failed"],
                     "want": COMMITTED_N_FAILED_V3,
                     "pass": bool(spec3_summary["n_failed"]
                                  == COMMITTED_N_FAILED_V3)},
        "pass": bool(row_check["pass"] and sd <= TOL_P1_SUMMARY
                     and spec3_summary["n_failed"] == COMMITTED_N_FAILED_V3),
    }


# --------------------------------------------------------------------------
# Stage B — bootstrap_resimulate's loop with the joint head
# --------------------------------------------------------------------------
def tier2_fe_map(fe_src: np.ndarray, fe_val: np.ndarray, absorbed_src: str,
                 prod_strata: list, prod_coefs: dict) -> tuple[dict, float]:
    """Mean over the replicate's duplicate copies of each source stratum, the
    absorbed copy re-inserted at 0, production FE as the fallback for source
    strata not drawn in that replicate. THE RULE AND THE FALLBACK ARE
    ARBITRARY (spec C6(ii) tier 2) and so is the residual level shift
    (DEVIATION 4): the replicate FE are relative to a bootstrap-label
    reference, not the production reference."""
    acc: dict[str, list] = defaultdict(list)
    for s, v in zip(fe_src, fe_val):
        acc[str(s)].append(float(v))
    acc[str(absorbed_src)].append(0.0)
    out, undrawn = {}, 0
    for sid in prod_strata:
        if sid in acc:
            out[sid] = float(np.mean(acc[sid]))
        else:
            out[sid] = float(prod_coefs.get(f"fe_stratum_{sid}", 0.0))
            undrawn += 1
    return out, undrawn / max(len(prod_strata), 1)


def build_rep_coefs(base_coefs: dict, head: np.ndarray, spec: int,
                    rep_scales: dict, prod_scales: dict,
                    fe_map: dict | None) -> tuple[dict, dict]:
    """const + age spline (+ months at v4) transfer UNRESCALED; only the 3
    macro betas are rescaled (spec C6(ii) 'units, and the trap in them')."""
    names = HEAD_NAMES[spec]
    coefs = dict(base_coefs)
    for i, n in enumerate(names):
        if n in BETA_NAMES:
            continue
        coefs[n] = float(head[i])
    macro_native = {n: float(head[names.index(n)]) for n in BETA_NAMES}
    resc = rescale_to_production_units({**macro_native, **rep_scales},
                                       prod_scales)
    coefs.update({n: float(resc[n]) for n in BETA_NAMES})
    month_effects = {}
    if spec == 4:
        month_effects = {"1": 0.0}
        month_effects.update({m.split("_")[1]: float(coefs[m])
                              for m in MONTH_NAMES})
    if fe_map:
        for sid, v in fe_map.items():
            key = f"fe_stratum_{sid}"
            if key in coefs:          # the production reference has no column
                coefs[key] = float(v)
    return coefs, month_effects


def stage_b(spec: int, tier: int, heads: pd.DataFrame, base_art: dict,
            prod_scales: dict, panel, trans, empirical, out_csv: Path,
            fe_npz: Path | None, limit: int | None, resume: bool) -> dict:
    names = HEAD_NAMES[spec]
    prod_strata = None
    fe_arrays = None
    undrawn_shares = []
    if tier == 2:
        fe_arrays = np.load(fe_npz, allow_pickle=True)
        prod_strata = [str(s) for s in fe_arrays["production_strata"]]

    done = {}
    if resume and out_csv.exists():
        prev = pd.read_csv(out_csv)
        done = {int(r): row for r, row in zip(prev["rep"],
                                              prev.to_dict("records"))}
        print(f"  resuming: {len(done)} replications already scored")

    rows = list(done.values())
    t0 = time.perf_counter()
    todo = heads if limit is None else heads.head(limit)
    for j, (_, rep) in enumerate(todo.iterrows()):
        i = int(rep["rep"])
        if i in done:
            continue
        head = np.array([float(rep[f"head_{n}"]) for n in names])
        rep_scales = {"gap_std": float(rep["gap_std"]),
                      "burn_std": float(rep["burn_std"]),
                      "fric_std": float(rep["fric_std"])}
        fe_map = None
        if tier == 2:
            fe_map, share = tier2_fe_map(fe_arrays[f"fe_src_{i}"],
                                         fe_arrays[f"fe_val_{i}"],
                                         str(fe_arrays[f"absorbed_src_{i}"]),
                                         prod_strata,
                                         base_art["coefficients"])
            undrawn_shares.append(share)
        coefs, month_effects = build_rep_coefs(
            base_art["coefficients"], head, spec, rep_scales, prod_scales,
            fe_map)
        art = dict(base_art)
        art["coefficients"] = coefs
        if spec == 4:
            art["month_effects"] = month_effects
        else:
            art.pop("month_effects", None)
        TMP_COEF.write_text(json.dumps(art))
        sim = sim_mod.simulate_qt_window(panel=panel, coefs=coefs, trans=trans,
                                         output=TMP_SIM, coef_path=TMP_COEF)
        r = score_extension_risk(sim, empirical)
        rows.append({
            "rep": i,
            **{n: float(coefs[n]) for n in BETA_NAMES},
            "trapped_b": r["hazard_trapped_b"],
            "share_pct": r["share_explained_pct"],
            "cpr_r_lag0": r["cross_correlation"].get(0),
        })
        if (j + 1) % 10 == 0 or j == 0:
            el = time.perf_counter() - t0
            pd.DataFrame(rows).to_csv(out_csv, index=False)   # checkpoint
            print(f"  spec{spec} tier{tier} rep {i}: "
                  f"trapped ${r['hazard_trapped_b']:.1f}B "
                  f"({el / (j + 1):.1f}s/rep, {el:.0f}s elapsed)")

    df = pd.DataFrame(rows).sort_values("rep").reset_index(drop=True)
    df.to_csv(out_csv, index=False)
    return {"df": df, "mean_undrawn_share":
            (float(np.mean(undrawn_shares)) if undrawn_shares else None)}


def _block(a: np.ndarray) -> dict:
    a = np.asarray(a, dtype=float)
    return {"mean": float(a.mean()),
            "se": float(a.std(ddof=1)) if len(a) > 1 else None,
            "median": float(np.percentile(a, 50)),
            "iqr": [float(np.percentile(a, 25)), float(np.percentile(a, 75))],
            "ci_95": [float(np.percentile(a, 2.5)),
                      float(np.percentile(a, 97.5))]}


def summarize(df: pd.DataFrame) -> dict:
    trapped = df["trapped_b"].to_numpy(dtype=float)
    share = df["share_pct"].to_numpy(dtype=float)
    return {"n_reps": int(len(df)), "trapped_b": _block(trapped),
            "share_pct": _block(share),
            "frac_above_benchmark": float(np.mean(share > 100.0))}


def target_sum_audit(empirical) -> dict:
    """RECORDED AUDIT NUMBER ONLY — the sum of the QT target series.

    The first A7 implementation used −Σ QT_Target_Billions as the mechanical
    bound. That was the WRONG OBJECT (correction A7-C1): it came out $1417.50B
    and 0 of 198 draws sat there, vacuously, because a pool with zero VOLUNTARY
    prepayment still amortizes scheduled principal — roughly $200B of it across
    the window. The real bound is the zero-voluntary-prepayment FLOOR, measured
    by probe (zero_voluntary_floor_probe). This function is kept because the
    target sum is a useful audit of the target series itself; it adjudicates
    nothing."""
    qt_emp = qt_active_frame(empirical)
    tgt = qt_emp["QT_Target_Billions"]
    emp_trapped = float(qt_emp["Extension_Delta_Billions"].sum())
    neg_sum = float(-tgt.sum())
    return {
        "neg_sum_targets_b": neg_sum,
        "neg_sum_targets_share_pct": (neg_sum / emp_trapped * 100.0
                                      if emp_trapped else None),
        "sum_abs_targets_b": float(tgt.abs().sum()),
        "empirical_trapped_b": emp_trapped,
        "n_months": int(len(tgt)),
        "targets_all_nonpositive": bool((tgt <= 0).all()),
        "adjudicates": "nothing — audit only (correction A7-C1)",
    }


def zero_voluntary_floor_probe(spec: int, panel, trans, empirical,
                               prod_scales: dict, resume: bool) -> dict:
    """The ZERO-VOLUNTARY-PREPAYMENT FLOOR, measured THROUGH THE SAME HANDOFF
    (correction A7-C1).

    CORRECTION A7-C1b (labeled; the rate-gap route measured the wrong path).
    The first probe replaced the rate-gap coefficient with +50.0 and landed
    $1140.46B — BELOW the draws' pile at $1217.6339B, because early-window
    months have near-zero standardized gaps, so the rate-gap term alone
    cannot push log_mu under the -20 clip there and the probe still prepays
    early. The pile is the CLIP-EVERYWHERE path. The corrected probe forces
    that path unconditionally: the production head with its INTERCEPT
    replaced by -1e6, so log_mu < -20 in every month and every cohort, and
    hazard_fit.predict_hazard (`np.exp(np.clip(log_mu, -20, 0))`) returns the
    identical exp(-20) hazard everywhere — the exact path every fully-clipped
    draw realizes. The probe's trapped_b IS the floor, by construction, and
    the empirical-mode audit must now MATCH (it is a blocking expectation of
    this probe at spec v3, where 106 draws sit on the pile).

    WHY SATURATED DRAWS ARE EXACTLY EQUAL. It is the CLIP, not underflow, that
    makes the pile-up exact: every draw whose log-hazard sits below -20 on the
    same months gets the identical exp(-20) hazard there, hence the identical
    roll-off and the identical trapped figure. The first run's 106 draws
    matched to the last printed digit for that reason, and the probe reproduces
    the same clipped path."""
    base_art = json.loads(COEF_PATH[spec].read_text())
    names = HEAD_NAMES[spec]
    head = np.array([float(base_art["coefficients"][n]) for n in names])
    head[names.index("const")] = FLOOR_PROBE_CONST  # A7-C1b
    heads = pd.DataFrame([{
        "rep": 0,
        "gap_std": prod_scales["gap_std"],
        "burn_std": prod_scales["burn_std"],
        "fric_std": prod_scales["fric_std"],
        **{f"head_{n}": float(v) for n, v in zip(names, head)},
    }])
    out = stage_b(spec, 1, heads, base_art, prod_scales, panel, trans,
                  empirical, floorprobe_csv(spec), None, None, resume)
    floor_b = float(out["df"]["trapped_b"].iloc[0])
    audit = target_sum_audit(empirical)
    return {
        "spec_version": spec,
        "floor_b": floor_b,
        "floor_share_pct": float(out["df"]["share_pct"].iloc[0]),
        "probe_const_coefficient": FLOOR_PROBE_CONST,
        "route": ("stage_b(spec, tier=1) with the production head and "
                  "rate_gap_bps := +50.0; production scales, production FE, "
                  "months at production"),
        "scheduled_amortization_b": float(audit["neg_sum_targets_b"] - floor_b),
        "sum_of_targets_audit": audit,
        "mechanism": ("predict_hazard clips log_mu at -20, so every "
                      "sufficiently rogue draw shares the identical hazard "
                      "path and lands on this exact value"),
    }


def attractors_for(spec: int) -> dict:
    """The two KNOWN optimizer attractors in the rate-gap coefficient, both READ
    from committed artifacts (correction A7-C2).

    The retired rule — all three macros within 0.02 of the production point —
    is a SAME-DATA optimizer-basin rule. Applied to a cluster bootstrap it
    labels 185 of 198 legitimate draws "rogue", because resampled panels scatter
    the macro coefficients by ~0.1-0.6 on their own. The population is bimodal
    in the rate gap, and the two modes are the two documented optimizer
    attractors, so the cut is nearest-attractor with the midpoint as cutpoint."""
    prod = float(json.loads(COEF_PATH[spec].read_text())
                 ["coefficients"]["rate_gap_bps"])
    rogue = float(json.loads(RIDGE_REF_JSON.read_text())
                  ["reference_swap"]["betas_swapped_ref"]["rate_gap_bps"])
    return {
        "production_attractor_rate_gap": prod,
        "production_source": f"{COEF_PATH[spec].name} .coefficients.rate_gap_bps",
        "rogue_attractor_rate_gap": rogue,
        "rogue_source": ("ridge_reference_weighting.json .reference_swap"
                         ".betas_swapped_ref.rate_gap_bps"),
        "cutpoint": float((prod + rogue) / 2.0),
        "rule": ("nearest attractor in the drawn rate-gap coefficient; "
                 "cutpoint = midpoint of the two attractors"),
    }


def decompose(df: pd.DataFrame, floor_b: float, attractors: dict,
              prod_macro: dict) -> dict:
    """The two Stage-B decompositions, as CORRECTED (A7-C1, A7-C2).

    (a) saturated vs not — |trapped − zero-voluntary floor| < 1e-6, the
        mechanical cut, with the floor MEASURED by probe;
    (b) production-mode vs rogue-mode — nearest attractor in the drawn rate-gap
        coefficient.
    The cross-tab is the point: A7's claim is that the rogue-mode replicates are
    the saturated ones. An `empirical_mode` audit is reported alongside so that
    a probe which does NOT coincide with the actual pile-up says so loudly
    rather than silently reporting zero saturated draws — the exact failure the
    first A7 implementation had."""
    n = len(df)
    trapped = df["trapped_b"].to_numpy(dtype=float)
    sat = np.abs(trapped - float(floor_b)) < SATURATION_TOL_B
    gap = df["rate_gap_bps"].to_numpy(dtype=float)
    cut = float(attractors["cutpoint"])
    prod_mode = gap < cut

    legacy = np.ones(n, dtype=bool)
    for name in BETA_NAMES:
        legacy &= np.abs(df[name].to_numpy(dtype=float)
                         - float(prod_macro[name])) <= LEGACY_BASIN_TOL

    def cell(mask: np.ndarray) -> dict:
        sub = df[mask]
        out = {"n": int(mask.sum()),
               "share_of_draws": (float(mask.mean()) if n else None)}
        if len(sub):
            out["trapped_b"] = _block(sub["trapped_b"].to_numpy(dtype=float))
            out["share_pct"] = _block(sub["share_pct"].to_numpy(dtype=float))
            out["drawn_macro_means"] = {
                m: float(sub[m].mean()) for m in BETA_NAMES}
        return out

    vc = pd.Series(trapped).value_counts()
    mode_value = float(vc.index[0]) if len(vc) else None
    mode_count = int(vc.iloc[0]) if len(vc) else 0

    return {
        "saturation": {
            "rule": (f"|trapped_b − zero_voluntary_floor| < "
                     f"{SATURATION_TOL_B:g} B; the floor is MEASURED by probe "
                     "through stage_b's own handoff, never computed from a "
                     "formula"),
            "floor_b": float(floor_b),
            "at_floor": cell(sat), "below_floor": cell(~sat),
            "empirical_mode": {
                "value_b": mode_value, "count": mode_count,
                "probe_matches_empirical_mode": bool(
                    mode_value is not None
                    and abs(mode_value - float(floor_b)) < SATURATION_TOL_B),
                "note": ("if the probe floor and the empirical pile-up disagree "
                         "the saturation cut is measuring the wrong object — "
                         "this is the guard the first A7 run lacked"),
            },
        },
        "mode": {
            "rule": attractors["rule"],
            "attractors": attractors,
            "production_mode": cell(prod_mode), "rogue_mode": cell(~prod_mode),
        },
        "cross_tab_counts": {
            "production_mode_at_floor": int((prod_mode & sat).sum()),
            "production_mode_below_floor": int((prod_mode & ~sat).sum()),
            "rogue_mode_at_floor": int((~prod_mode & sat).sum()),
            "rogue_mode_below_floor": int((~prod_mode & ~sat).sum()),
        },
        "legacy_same_data_basin_rule": {
            "label": ("same-data basin rule; too strict for resampled draws — "
                      "RETIRED, non-adjudicating diagnostic (correction A7-C2)"),
            "tol": LEGACY_BASIN_TOL,
            "production_values": {m: float(prod_macro[m]) for m in BETA_NAMES},
            "n_within": int(legacy.sum()), "n_outside": int((~legacy).sum()),
        },
    }


def recover_stage_a_counts(spec: int) -> dict | None:
    """Replication counts recovered from the persisted Stage-A draw CSV.

    The spec-v4 Stage A completed and persisted its 200 rows but the run died in
    the aggregation (the A7(1) KeyError), so no stage_a.spec4 summary was ever
    written. The convergence counts survive in the CSV's `converged` column and
    are what verdict branch (ii-c) needs. `point_native_units` does NOT survive,
    so P3 for a recovered spec stays PENDING."""
    p = FULLVEC_CSV[spec]
    if not p.exists():
        return None
    d = pd.read_csv(p)
    if "converged" not in d.columns:
        return None
    c = d["converged"].astype(bool)
    return {
        "n_reps": int(len(d)), "n_converged": int(c.sum()),
        "n_failed": int((~c).sum()),
        "recovered_from": p.name,
        "counts_only": True,
        "note": ("counts only; the Stage-A summary was never written for this "
                 "spec (A7(1) aggregation crash). point_native_units is not "
                 "recoverable, so P3 for this spec stays PENDING."),
    }


def sim_context():
    print("Fetching macro + empirical benchmark (once) …")
    macro_raw = fetch_data()
    empirical = build_empirical_metrics(macro_raw,
                                        soma_rolloff=fetch_soma_mbs_monthly())
    sim_mod.fetch_data = lambda: macro_raw      # bootstrap_resimulate.py:51
    panel = pl.read_parquet(PANEL_PATH)
    trans = load_transition_matrix(MARKOV_MATRIX_PATH)
    return panel, trans, empirical


def run_p2(panel, trans, empirical, prod_scales: dict, limit, resume) -> dict:
    """Stage B with the head FORCED to production except the 3 macro betas,
    reading the COMMITTED draws CSV and the SPEC-V3 artifact (DEVIATION 2)."""
    base_art = json.loads(V3_COEF_PATH.read_text())
    draws = pd.read_csv(BOOTSTRAP_DRAWS_CSV)
    assert list(draws.columns) == BETA_NAMES, draws.columns
    names = HEAD_NAMES[3]
    head_prod = np.array([float(base_art["coefficients"][n]) for n in names])
    heads = []
    for i, rep in draws.iterrows():
        h = head_prod.copy()
        for n in BETA_NAMES:
            h[names.index(n)] = float(rep[n])
        row = {"rep": int(i), "gap_std": prod_scales["gap_std"],
               "burn_std": prod_scales["burn_std"],
               "fric_std": prod_scales["fric_std"]}
        row.update({f"head_{n}": float(v) for n, v in zip(names, h)})
        heads.append(row)
    out = stage_b(3, 1, pd.DataFrame(heads), base_art, prod_scales, panel,
                  trans, empirical, P2_CSV, None, limit, resume)
    got = summarize(out["df"])
    want = json.loads(COMMITTED_RESIM.read_text())
    checks = {
        "mean": {"got": got["trapped_b"]["mean"],
                 "want": want["trapped_b"]["mean"]},
        "median": {"got": got["trapped_b"]["median"],
                   "want": want["trapped_b"]["median"]},
        "ci_95_lo": {"got": got["trapped_b"]["ci_95"][0],
                     "want": want["trapped_b"]["ci_95"][0]},
        "ci_95_hi": {"got": got["trapped_b"]["ci_95"][1],
                     "want": want["trapped_b"]["ci_95"][1]},
    }
    for c in checks.values():
        c["abs_diff"] = abs(c["got"] - c["want"])
        c["pass"] = bool(c["abs_diff"] <= TOL_P2)
    return {"blocking": True, "tol": TOL_P2, "checks": checks,
            "n_reps": got["n_reps"],
            "pass": all(c["pass"] for c in checks.values()),
            "note": ("coef_path pinned to hazard_coefficients_specv3.json — "
                     "the default is now the v4 artifact (DEVIATION 2).")}


def stage_b_point_parity(spec: int, panel, trans, empirical, prod_scales: dict,
                         resume: bool) -> dict:
    """A7(2) — BLOCKING Stage-B wiring gate, run before any replicate is scored.

    Pushes the PRODUCTION head — the spec's own committed intercept, 7 age
    spline coefficients, 3 macro point estimates (+ 11 month coefficients at v4)
    with the PRODUCTION standardization scales — through stage_b's EXACT
    coefficient-handoff and resimulation machinery, and requires the committed
    forward-simulation point back within $0.50B. Because rep_scales are the
    production scales the rescale factors are identically 1, so this gate
    isolates the HANDOFF (which head entry lands on which coefficient name,
    months delivered through coef_path, FE and prediction scales held at
    production, temp-artifact assembly, simulate/score call) from the rescaling
    arithmetic, which P2 and P3 cover. If it fails, the whole Stage B
    construction is void — wiring, not finding — and nothing lands."""
    base_art = json.loads(COEF_PATH[spec].read_text())
    names = HEAD_NAMES[spec]
    head = np.array([float(base_art["coefficients"][n]) for n in names])
    heads = pd.DataFrame([{
        "rep": 0,
        "gap_std": prod_scales["gap_std"],
        "burn_std": prod_scales["burn_std"],
        "fric_std": prod_scales["fric_std"],
        **{f"head_{n}": float(v) for n, v in zip(names, head)},
    }])
    out = stage_b(spec, 1, heads, base_art, prod_scales, panel, trans,
                  empirical, pointhead_csv(spec), None, None, resume)
    got = float(out["df"]["trapped_b"].iloc[0])
    want = COMMITTED_POINT_B[spec]
    blocking = spec in POINT_PARITY_BLOCKING_SPECS
    ok = abs(got - want) <= POINT_PARITY_TOL_B
    return {
        "spec_version": spec, "blocking": bool(blocking),
        "got_trapped_b": got, "want_trapped_b": want,
        "abs_diff_b": abs(got - want), "tol_b": POINT_PARITY_TOL_B,
        "got_share_pct": float(out["df"]["share_pct"].iloc[0]),
        "head_source": (f"{COEF_PATH[spec].name} .coefficients, "
                        f"{len(names)} head entries"),
        "want_source": ("bootstrap_resimulate_results.json .point_trapped_b"
                        if spec == 3 else
                        "pathA_seasonal_adoption_results.json .v4_trapped_b"),
        "pass": bool(ok),
        "note": ("exercises the handoff, not the rescaling: rep_scales are the "
                 "production scales, so rescale_to_production_units is the "
                 "identity here by construction."),
    }


def gate_p3(summaries: dict) -> dict:
    out = {}
    for spec, s in summaries.items():
        art = json.loads(COEF_PATH[spec].read_text())
        n_train = int(art["n_train"])
        fac = float(np.sqrt(n_train / (n_train - 1.0)))
        checks = {}
        for n in BETA_NAMES:
            got = float(s["point_native_units"][n])
            want = float(art["coefficients"][n])
            adj = want * (fac if (spec == 4 and n != "burnout_orth") else 1.0)
            checks[n] = {"got": got, "want": want, "abs_diff": abs(got - want),
                         "want_ddof_adjusted": adj,
                         "abs_diff_ddof_adjusted": abs(got - adj),
                         "pass": bool(abs(got - want) <= TOL_P3)}
        out[f"spec{spec}"] = {
            "tol": TOL_P3, "checks": checks,
            "blocking": bool(spec == 3),
            "pass": all(c["pass"] for c in checks.values()),
            "note": ("" if spec == 3 else
                     "NON-BLOCKING at v4: production v4 was fit by "
                     "seasonality_concave_gap.fit_with_month_dummies with "
                     "numpy ddof=0 standardization while fit_betas uses pandas "
                     "ddof=1 — see pathA_ridge_v4.py DEVIATION 1; the "
                     "ddof-adjusted comparison is reported alongside."),
        }
    return out


# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", default="all",
                    choices=["A", "B", "P2", "report", "all"])
    ap.add_argument("--specs", default="3,4")
    ap.add_argument("--tiers", default="1,2")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--limit", type=int, default=None,
                    help="score only the first N replications (timing probe)")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    specs = [int(s) for s in args.specs.split(",") if s.strip()]
    tiers = [int(t) for t in args.tiers.split(",") if t.strip()]
    t_all = time.perf_counter()

    v3_art = json.loads(V3_COEF_PATH.read_text())
    v4_art = json.loads(V4_COEF_PATH.read_text())
    assert int(v3_art["spec_version"]) == 3 and int(v4_art["spec_version"]) == 4
    ridge_alpha = (args.alpha if args.alpha is not None
                   else float(v3_art["ridge_alpha"]))
    prod_scales = {"gap_std": float(v3_art["rate_gap_bps_std"]),
                   "burn_std": float(v3_art["burnout_demean_std"]),
                   "fric_std": float(v3_art["friction_std"])}
    for k, col in (("gap_std", "rate_gap_bps_std"),
                   ("burn_std", "burnout_demean_std"),
                   ("fric_std", "friction_std")):
        assert abs(prod_scales[k] - float(v4_art[col])) <= 1e-15, (
            "v3/v4 prediction scales diverged — the v4 artifact is supposed to "
            "inherit them (pathA_seasonal_adoption.py:128-131)")
    head_v4 = production_start_head(v4_art)
    assert len(head_v4) == 22, f"v4 head length {len(head_v4)} != 22"

    gates: dict = {}
    stage_a_summaries: dict = {}

    if args.stage in ("A", "all"):
        train = load_train()
        print(f"Training cells: {len(train):,} | "
              f"strata: {train['stratum_id'].nunique()}")
        assert len(train) == int(v4_art["n_train"]), "training split drift"
        gates["G0_fit_betas_ext_parity"] = gate_g0(train, ridge_alpha, head_v4)
        print(f"  G0 {'PASS' if gates['G0_fit_betas_ext_parity']['pass'] else 'FAIL'}")
        for spec in specs:
            print(f"\nStage A — spec v{spec}: {args.reps} reps, cluster=stratum, "
                  f"fixed alpha={ridge_alpha:g}, seed={args.seed}")
            stage_a_summaries[spec] = stage_a(train, spec, args.reps,
                                              ridge_alpha, args.seed,
                                              prod_scales, head_v4)
        if 3 in stage_a_summaries:
            gates["P1_stageA_specv3"] = gate_p1(stage_a_summaries[3])
            print(f"  P1 {'PASS' if gates['P1_stageA_specv3']['pass'] else 'FAIL'}")
        gates["P3_point_head"] = gate_p3(stage_a_summaries)

    results: dict = {}
    floors: dict = {}
    if args.stage in ("B", "P2", "all"):
        panel, trans, empirical = sim_context()
        if args.stage in ("P2", "all"):
            print("\nP2 — Stage B with the head forced to production "
                  "except the macro block …")
            gates["P2_stageB_replay"] = run_p2(panel, trans, empirical,
                                               prod_scales, args.limit,
                                               args.resume)
            print(f"  P2 {'PASS' if gates['P2_stageB_replay']['pass'] else 'FAIL'}")
        if args.stage in ("B", "all"):
            # ---- A7(2): point-head parity FIRST, before any replicate -------
            parity_specs = sorted(set(specs) | set(POINT_PARITY_BLOCKING_SPECS))
            print("\nA7 point-head parity (BLOCKING for spec v3) — the "
                  "production head through stage_b's own handoff …")
            pp = {}
            for spec in parity_specs:
                pp[f"spec{spec}"] = stage_b_point_parity(
                    spec, panel, trans, empirical, prod_scales, args.resume)
                c = pp[f"spec{spec}"]
                print(f"  spec v{spec}: got ${c['got_trapped_b']:.4f}B  "
                      f"want ${c['want_trapped_b']:.4f}B  "
                      f"|Δ| {c['abs_diff_b']:.4f}B (tol {c['tol_b']})  "
                      f"{'PASS' if c['pass'] else 'FAIL'}"
                      f"{'' if c['blocking'] else '  [non-blocking]'}")
            gates["A7_point_head_parity"] = {
                "blocking": True, "tol_b": POINT_PARITY_TOL_B, "legs": pp,
                "pass": all(c["pass"] for c in pp.values() if c["blocking"]),
                "note": ("amendment A7(2): if this fails the whole Stage B "
                         "construction is void — wiring, not finding."),
            }
            if not gates["A7_point_head_parity"]["pass"]:
                print("  A7 POINT-HEAD PARITY FAILED — Stage B aborted before "
                      "any replicate was scored; the construction is void.")
            else:
                for spec in specs:
                    if not FULLVEC_CSV[spec].exists():
                        print(f"  spec v{spec}: no Stage A draws — skipping")
                        continue
                    heads = pd.read_csv(FULLVEC_CSV[spec])
                    heads = heads[heads["converged"].astype(bool)]
                    base_art = json.loads(COEF_PATH[spec].read_text())
                    prod_macro = {n: float(base_art["coefficients"][n])
                                  for n in BETA_NAMES}
                    # A7-C1: the mechanical bound is MEASURED, once per spec,
                    # through the same handoff, before the replicates.
                    fl = zero_voluntary_floor_probe(spec, panel, trans,
                                                    empirical, prod_scales,
                                                    args.resume)
                    floors[f"spec{spec}"] = fl
                    att = attractors_for(spec)
                    print(f"  spec v{spec} zero-voluntary floor (probe, "
                          f"const:={FLOOR_PROBE_CONST:g}): "
                          f"${fl['floor_b']:.7f}B "
                          f"({fl['floor_share_pct']:.2f}%); scheduled "
                          f"amortization ${fl['scheduled_amortization_b']:.1f}B; "
                          f"attractors {att['production_attractor_rate_gap']:.4f}"
                          f" / {att['rogue_attractor_rate_gap']:.4f}, cutpoint "
                          f"{att['cutpoint']:.4f}")
                    for tier in tiers:
                        print(f"\nStage B — spec v{spec}, tier {tier} "
                              f"({len(heads)} replications) …")
                        out = stage_b(spec, tier, heads, base_art, prod_scales,
                                      panel, trans, empirical,
                                      simdraws_csv(spec, tier),
                                      FULLVEC_NPZ[spec] if tier == 2 else None,
                                      args.limit, args.resume)
                        # headline block keeps the FULL-SAMPLE numbers
                        s = summarize(out["df"])
                        s["mean_undrawn_share"] = out["mean_undrawn_share"]
                        s["floor_b"] = fl["floor_b"]
                        s["floor_share_pct"] = fl["floor_share_pct"]
                        dec = decompose(out["df"], fl["floor_b"], att,
                                        prod_macro)
                        s["n_at_floor"] = dec["saturation"]["at_floor"]["n"]
                        s["decompositions"] = dec
                        results.setdefault(f"spec{spec}",
                                           {})[f"tier{tier}"] = s
                        em = dec["saturation"]["empirical_mode"]
                        print(f"  spec{spec} tier{tier}: n={s['n_reps']}  "
                              f"at floor {s['n_at_floor']}  "
                              f"production-mode "
                              f"{dec['mode']['production_mode']['n']}  "
                              f"rogue-mode {dec['mode']['rogue_mode']['n']}  "
                              f"(rogue∧floor "
                              f"{dec['cross_tab_counts']['rogue_mode_at_floor']})"
                              f"  | empirical mode {em['count']} draws at "
                              f"{em['value_b']}, probe match "
                              f"{em['probe_matches_empirical_mode']}"
                              f"  | retired 0.02 rule would call "
                              f"{dec['legacy_same_data_basin_rule']['n_outside']}"
                              f" of {s['n_reps']} rogue")
        for tmp in (TMP_SIM, TMP_COEF):
            if tmp.exists():
                tmp.unlink()

    # ---------------- assemble / verdict -----------------------------------
    # Stages are separable, so this invocation MERGES into whatever a previous
    # invocation already established rather than clobbering it. --stage report
    # therefore just re-derives the verdict from the accumulated blocks.
    prior = {}
    if RESULTS_JSON.exists():
        try:
            prior = json.loads(RESULTS_JSON.read_text())
        except Exception:                       # noqa: BLE001 — corrupt prior
            prior = {}
    gates = {**prior.get("parity_gates", {}), **gates}
    stage_a_out = dict(prior.get("stage_a", {}))
    stage_a_out.update({f"spec{k}": v for k, v in stage_a_summaries.items()})
    merged_results = {k: dict(v) for k, v in prior.get("results", {}).items()}
    for k, v in results.items():
        merged_results.setdefault(k, {}).update(v)
    results = merged_results
    floors = {**prior.get("zero_voluntary_floor", {}), **floors}

    # Stage-A counts the aggregation needs but the summary may never have had:
    # recovered from the persisted draw CSVs (see recover_stage_a_counts).
    stage_a_recovered: dict = {}
    for _spec in (3, 4):
        if f"spec{_spec}" not in stage_a_out:
            rec = recover_stage_a_counts(_spec)
            if rec is not None:
                stage_a_recovered[f"spec{_spec}"] = rec

    # ---- A7(1): P3_point_head must not be indexed unconditionally ----------
    # A --specs 4 or --stage B invocation never builds the spec-3 leg. Recover
    # it from the persisted Stage-A summary when one exists; otherwise mark it
    # PENDING, exclude it from all_pass, and say so out loud.
    p3 = dict(gates.get("P3_point_head", {}))
    if "spec3" not in p3 and "spec3" in stage_a_out:
        try:
            p3.update(gate_p3({3: stage_a_out["spec3"]}))
            p3["spec3"]["recovered_from"] = "persisted stage_a.spec3"
        except Exception as exc:                # noqa: BLE001 — degrade, not crash
            p3["spec3"] = {"pass": None, "status": "PENDING", "blocking": True,
                           "reason": f"recovery failed: {repr(exc)[:160]}"}
    if "spec3" not in p3:
        p3["spec3"] = {
            "pass": None, "status": "PENDING", "blocking": True,
            "reason": ("stage A was not run for spec v3 in this or any prior "
                       "invocation recorded in this artifact"),
        }
    if p3:
        gates["P3_point_head"] = p3

    committed = json.loads(COMMITTED_RESIM.read_text())
    c_lo, c_hi = committed["trapped_b"]["ci_95"]
    c_width = float(c_hi - c_lo)
    primary = results.get("spec3", {}).get("tier1")
    width_ratio = None
    if primary is not None:
        j_lo, j_hi = primary["trapped_b"]["ci_95"]
        width_ratio = float((j_hi - j_lo) / c_width) if c_width else None

    v4_failed = stage_a_out.get("spec4", {}).get("n_failed")
    v4_failed_source = "stage_a.spec4"
    if v4_failed is None:
        v4_failed = stage_a_recovered.get("spec4", {}).get("n_failed")
        v4_failed_source = (stage_a_recovered.get("spec4", {})
                            .get("recovered_from", "unavailable"))
    v4_unstable = (v4_failed is not None and v4_failed >= V4_FAILURE_MATERIAL)

    if width_ratio is None:
        code, action = "INCOMPLETE", "run all stages before landing anything"
    elif width_ratio < NARROW_THRESHOLD:
        code, action = "NARROWS", (
            "(ii-b) DO NOT adopt the joint interval as the headline Path A "
            "interval. Report both; keep the wider committed interval as the "
            "quoted one; state that the joint construction is narrower. "
            "[posture] flag to Eugene.")
    elif v4_unstable:
        code, action = "V4_UNSTABLE", (
            "(ii-c) land the MEASURED spec-v4 failure count in tex 981 in "
            "place of the qualitative 'branch-unstable' claim (echo at tex "
            "623); land it either way the interval goes.")
    elif width_ratio >= 1.0:
        code, action = "SURVIVES_WIDER", (
            "(ii-a) tex 981's 'no useful precision' sentence gains one clause "
            "naming the joint construction and the wider interval; the "
            "preceding sentences' numbers are restated at the joint values; "
            "tex 400's tab:estimators note is updated for provenance.")
    else:
        code, action = "SURVIVES_UNCHANGED", (
            "(ii-a) as SURVIVES_WIDER, with the interval reported as "
            "materially unchanged.")

    # ---- A7(4): mandatory floor disclosure + production-mode-only read ------
    # The CODE above is adjudicated on the FULL SAMPLE and is unchanged. What
    # follows accompanies it; neither replaces it.
    dec_primary = (primary or {}).get("decompositions", {})
    n_floor = (primary or {}).get("n_at_floor")
    floor_b = (primary or {}).get(
        "floor_b", floors.get("spec3", {}).get("floor_b"))
    has_corrected = bool(dec_primary.get("mode")
                         and dec_primary.get("saturation", {}).get("at_floor"))
    if primary is None or not has_corrected or floor_b is None:
        floor_disclosure = ("not computable — the spec v3 / tier 1 Stage B leg "
                            "has not been scored with the CORRECTED A7 cuts "
                            "(zero-voluntary floor + nearest-attractor mode) in "
                            "this artifact; re-run --stage B --specs 3 "
                            "--tiers 1")
    elif n_floor:
        ct = dec_primary["cross_tab_counts"]
        floor_disclosure = (
            "MANDATORY DISCLOSURE (amendment A7, corrections A7-C1/A7-C2): the "
            f"narrowing is partly MECHANICAL. {n_floor} of "
            f"{primary['n_reps']} spec-v3 tier-1 draws sit at EXACTLY the "
            f"ZERO-VOLUNTARY-PREPAYMENT FLOOR ${floor_b:.7f}B — the trapped "
            "figure a pool returns when voluntary prepayment is switched off "
            "and only scheduled amortization rolls off, measured by probe "
            "through the same coefficient handoff, not a formula. The "
            "interval's upper edge and its median therefore sit at that floor, "
            "reached by the rogue-mode replicates "
            f"({ct['rogue_mode_at_floor']} of the "
            f"{dec_primary['mode']['rogue_mode']['n']} rogue-mode draws are "
            "saturated), and are not a sampling statement about the estimand. "
            "The committed 3-beta rendering of the same rogue draws produced "
            "the -$4,460B tail; the joint rendering piles them on the floor "
            "instead — two renderings of one optimizer pathology, not two "
            "findings.")
    else:
        floor_disclosure = (
            f"no draw sits at the zero-voluntary-prepayment floor "
            f"${floor_b:.7f}B; the interval is not mechanically bounded in "
            "this leg.")

    pm = dec_primary.get("mode", {}).get("production_mode")
    production_mode_only = None
    if pm and pm.get("n"):
        pm_lo, pm_hi = pm["trapped_b"]["ci_95"]
        att = dec_primary["mode"]["attractors"]
        production_mode_only = {
            "label": ("spec v3, tier 1, PRODUCTION-MODE DRAWS ONLY (drawn "
                      "rate-gap coefficient nearer the production attractor "
                      f"{att['production_attractor_rate_gap']:.6f} than the "
                      f"rogue attractor {att['rogue_attractor_rate_gap']:.6f}; "
                      f"cutpoint {att['cutpoint']:.6f}). Reported as a labeled "
                      "sub-population for diagnosis: it is NOT the "
                      "pre-committed estimand, NOT the quoted interval, and NOT "
                      "a substitute for the full-sample numbers above."),
            "n": pm["n"],
            "share_of_draws": pm["share_of_draws"],
            "ci_95_b": [pm_lo, pm_hi],
            "median_b": pm["trapped_b"]["median"],
            "mean_b": pm["trapped_b"]["mean"],
            "share_pct_ci_95": pm["share_pct"]["ci_95"],
            "width_b": float(pm_hi - pm_lo),
            "width_ratio_vs_committed": (float((pm_hi - pm_lo) / c_width)
                                         if c_width else None),
            "n_at_floor": dec_primary["cross_tab_counts"][
                "production_mode_at_floor"],
            "drawn_macro_means": pm.get("drawn_macro_means"),
        }
    if n_floor and code == "NARROWS":
        action = ("[posture] NOT ADJUDICABLE AS IT STANDS (amendment A7): the "
                  "NARROWS code is driven by floor saturation. " + action)

    # Blocking-gate roll-up over exactly the gates that exist. P3_point_head is
    # a per-spec container, so its blocking sub-legs are walked individually;
    # every other blocking gate contributes its own pass flag. A `pass` of None
    # means PENDING: excluded from all_pass, listed, and warned about.
    blocking: list[tuple[str, object]] = []
    for key, g in gates.items():
        if not isinstance(g, dict):
            continue
        if key == "P3_point_head":
            for sk, sg in g.items():
                if isinstance(sg, dict) and sg.get("blocking"):
                    blocking.append((f"{key}.{sk}", sg.get("pass")))
        elif g.get("blocking"):
            blocking.append((key, g.get("pass")))
    pending = [k for k, p in blocking if p is None]
    all_pass = all(bool(p) for _, p in blocking if p is not None)
    for k in pending:
        print(f"  WARNING: blocking gate {k} is PENDING (not evaluated in this "
              f"or any recorded invocation) — excluded from all_pass; the run "
              f"is NOT fully gated.")
    status = "OK" if all_pass else "GATE_FAILURE"

    payload = {
        "mode": "pathA_resimulate_joint",
        "status": status,
        "spec": ("SPEC_round28_C1_C2_C3_C6.md C6(ii): stage A persists the "
                 "FULL params_head + standardization scales + FE block per "
                 "replicate; stage B resimulates with const + age spline "
                 "(+ months at v4) transferred UNRESCALED and only the 3 macro "
                 "betas rescaled; tier 1 (FE at production) primary, tier 2 "
                 "(mean-over-duplicates map, production fallback) secondary "
                 "and non-manuscript."),
        "spec_versions": specs,
        "labeled_deviations": [
            "1: per-replicate month effects are delivered through a temporary "
            "coefficient artifact because simulate_qt_window reads "
            "month_effects from coef_path, not from coefs.",
            "2: the spec-v3 leg pins coef_path to "
            "hazard_coefficients_specv3.json; the default is now the v4 "
            "artifact and would silently score 928.9B instead of 915.1B.",
            "3: the v4 Stage-A point fit is warm-started; run_bootstrap's "
            "cold point fit is the known incompletely-converged v4 optimum. "
            "The cold triple is recorded as point_cold_native_units.",
            "4: tier-2 FE carry an unremoved level shift (bootstrap-label "
            "reference vs production reference) on top of the arbitrary "
            "averaging rule.",
            "5: G0 added — fit_betas_ext must reproduce bootstrap_se.fit_betas "
            "field-for-field; fit_betas returns neither the FE block nor the "
            "absorbed label.",
        ],
        "parity_gates": gates,
        "parity_gates_all_pass": all_pass,
        "construction": {
            "tier1": {"head_swapped": ["const", "age_spline", "macro"]
                                      + (["months"] if 4 in specs else []),
                      "fe": "production",
                      "rescaled": "macro only (rescale_to_production_units)"},
            "tier2": {"fe_map_rule": ("mean over stratum_id_src duplicates; "
                                      "production fallback for undrawn"),
                      "rule_is_arbitrary": True,
                      "level_shift_not_removed": True,
                      "enters_manuscript": False,
                      "mean_undrawn_share": {
                          k: v.get("tier2", {}).get("mean_undrawn_share")
                          for k, v in results.items()}},
        },
        "stage_a": stage_a_out,
        "results": results,
        "comparison_vs_committed": {
            "committed_ci_95_b": [c_lo, c_hi],
            "committed_width_b": c_width,
            "committed_point_trapped_b": committed["point_trapped_b"],
            "committed_frac_above_benchmark": committed["frac_above_benchmark"],
            "joint_ci_95_b": (primary["trapped_b"]["ci_95"]
                              if primary else None),
            "width_ratio": width_ratio,
            "narrow_threshold": NARROW_THRESHOLD,
        },
        "verdict": {
            "code": code,
            "adjudicated_on": "full sample (pre-committed codes, unchanged)",
            "v4_n_failed": v4_failed,
            "v4_n_failed_source": v4_failed_source,
            "v4_failure_material_threshold": V4_FAILURE_MATERIAL,
            "v4_unstable": bool(v4_unstable),
            "v4_expectation_fired": bool(v4_unstable),
            "floor_disclosure": floor_disclosure,
            "floor_driven": bool(n_floor),
            "production_mode_only": production_mode_only,
            "manuscript_action": action,
            "propagation": ("none — Path A is excluded from every headline "
                            "figure (tex 290, 978, 1053)"),
        },
        "runtime_s": round(time.perf_counter() - t_all, 1),
    }
    payload["zero_voluntary_floor"] = floors
    payload["stage_a_recovered"] = stage_a_recovered
    payload["parity_gates_pending"] = pending
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_np)
        f.write("\n")

    print("\n" + "=" * 66)
    print(f" pathA_resimulate_joint — status {status} — verdict {code}")
    print("=" * 66)
    if primary:
        print(f"  joint 95% CI  [{primary['trapped_b']['ci_95'][0]:.1f}, "
              f"{primary['trapped_b']['ci_95'][1]:.1f}]B  "
              f"width ratio {width_ratio:.3f} vs committed")
        print(f"  mean ${primary['trapped_b']['mean']:.1f}B  "
              f"median ${primary['trapped_b']['median']:.1f}B  "
              f"above benchmark {primary['frac_above_benchmark'] * 100:.1f}%")
        if primary.get("n_at_floor") is not None:
            print(f"  at zero-voluntary floor: {primary['n_at_floor']}/"
                  f"{primary['n_reps']} "
                  f"(${primary.get('floor_b') or float('nan'):.7f}B)")
        if production_mode_only:
            print(f"  production-mode draws only ({production_mode_only['n']}): "
                  f"[{production_mode_only['ci_95_b'][0]:.1f}, "
                  f"{production_mode_only['ci_95_b'][1]:.1f}]B  "
                  f"width ratio "
                  f"{production_mode_only['width_ratio_vs_committed']:.3f}"
                  f"  [labeled sub-population, NOT the quoted interval]")
    print(f"  spec-v4 Stage A failures: {v4_failed} "
          f"(threshold {V4_FAILURE_MATERIAL}; source {v4_failed_source})")
    print(f"  {floor_disclosure}")
    if pending:
        print(f"  PENDING blocking gates: {pending}")
    print(f"  Saved: {RESULTS_JSON}")
    if status != "OK":
        raise SystemExit("GATE_FAILURE — nothing lands in the manuscript.")


if __name__ == "__main__":
    sys.exit(main())
