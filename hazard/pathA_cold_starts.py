#!/usr/bin/env python3
"""
pathA_cold_starts.py — 50 dispersed starts on the PRODUCTION panel: is the
spec-v4 production point the optimum its own gates think it is? (round-28
WP-C6(iii); R1: the paper asserts the spec-v4 penalized likelihood is
"branch-unstable" without ever probing the production likelihood itself.)

PRE-COMMITTED SPEC (fixed BEFORE any run; drafting spec at
specs/SPEC_round28_C1_C2_C3_C6.md SPEC C6(iii); gates, tolerances, the 50-start
composition, the branch-classification rule, the expectation and the landing
branches adopted unchanged except where LABELED below).

DESTRUCTIVE-RUN HAZARD (spec C6.0). bootstrap_se.py is IMPORTED for its
functions and NEVER invoked as __main__ (running it today would overwrite the
committed spec-v3 hazard_bootstrap_draws.csv at the wrong spec — the draws path
is hard-coded at line 298 and --out only redirects the JSON). This script
resamples NOTHING, writes only to two NEW paths, and opens every committed
artifact read-only.

WHY THE PRODUCTION PANEL. The documented instability is on RESAMPLED panels
(tex 623, 981; ridge_reference_weighting.json .estimable_strata_mle.note calls
the reference-swap sensitivity "an optimizer-path artifact of penalized
cold-start refits, not information in the production point"). The production
panel is the better-conditioned case — the reference stratum
2017_200_740+_<=80 is NOT among the 20 zero-event strata (same note) — which is
what makes a probe here decisive about the adopted point.

A MATHEMATICAL FACT THE RESULT MUST BE READ THROUGH (verified in the installed
statsmodels 0.14.6 source, NOT assumed). GLM.fit_regularized with L1_wt=0.0
does not run coordinate descent at all: it dispatches to GLM._fit_ridge, which
minimizes

    f(b) = -loglike(b)/nobs + alpha * sum(b**2) / 2

by scipy.optimize.minimize(method="bfgs"). The Poisson log-likelihood with a
log link is concave in b, so f is STRICTLY convex for alpha > 0 and has exactly
ONE minimizer. There is therefore no second *mode* to find on this panel: any
start that reports a materially lower objective than the production fit is
evidence that the production fit is UNDER-CONVERGED, not evidence of a rival
optimum, and any "second optimum" language must be read as a statement about
the optimizer path. The verdict codes below are kept exactly as pre-committed;
this note fixes their interpretation, and it is why branch (iii-c) stops rather
than lands.

ENGINE. The spec names bootstrap_se.fit_betas. fit_betas returns only
params_head and cannot return the penalized objective (it discards the fitted
object and the FE block, bootstrap_se.py:151-167), so the fit is REIMPLEMENTED
here under gate G0 and the objective is RECOMPUTED post-fit from the same
sm.GLM model object with the formula above — i.e. the objective is the exact
function _fit_ridge minimized, evaluated on the returned parameter vector.
Panel via bootstrap_se.main()'s filters (lines 278-283): enrich_panel_with_macro
-> dropna -> exposure > 0 -> period < HOLDOUT_DATE. alpha = 1e-4, seasonal=True
(spec v4), no resampling. FE coefficients start at zero in every case, as
fit_betas line 136-137 sets them.

LABELED DEVIATIONS from the drafted spec (all forced by the code; none silent):
  1. TWO DESIGN CONVENTIONS, AND THE ANCHOR GATE ONLY EXISTS UNDER ONE.
     Production spec v4 was NOT fit through fit_betas: pathA_seasonal_adoption
     .py:116-123 pins it to seasonality_concave_gap.fit_with_month_dummies,
     whose standardizer is numpy ddof=0 (line 84), while fit_betas is pandas
     ddof=1 (lines 107-110). The two designs differ by sqrt(n/(n-1)) on the gap
     and friction columns, ~3.2e-5 on rate_gap_bps — four orders outside G1's
     1e-9. So the run is executed as two legs of 50 starts each:
       leg `prod_warm`      — ddof-0 design (THE production design), IRLS
                              prestep then ridge, i.e. fit_betas' warm branch
                              transplanted onto the production design. PRIMARY;
                              the verdict is read off this leg, and G1 is
                              evaluated here.
       leg `fitbetas_warm`  — ddof-1 design, bootstrap_se.fit_betas' construction
                              verbatim. SECONDARY, spec-literal; G1 recorded
                              with the ddof-adjusted comparison alongside.
     A third leg `prod_direct` (ddof-0, NO IRLS prestep) is available via
     --legs and is the sharper dispersion probe (see deviation 2); it is not in
     the default set only because of cost.
     A PREDICTION THIS PAIRING MEASURES: under `prod_warm` the true cold start
     IS the production construction and should return the artifact; under
     `fitbetas_warm` it is the re-assembly route pathA_seasonal_adoption.py:
     11-21 records as having FAILED Gate B with "near-uniform ~-0.30 month
     effects". The two legs together turn that docstring claim into a
     measurement.
  2. THE IRLS PRESTEP PARTLY DEFEATS THE DISPERSION. fit_betas' warm branch
     runs an unpenalized IRLS (Newton on a concave problem) from the dispersed
     head BEFORE the ridge step, so dispersed starts are pulled toward the
     common MLE region before the objective is ever touched. That is the
     production pipeline and so it is what the default legs measure; the
     `prod_direct` leg feeds the dispersed head straight to fit_regularized and
     is the literal reading of "dispersed start". Both are reported.
  3. G1's fit_method EQUALITY IS NOT ACHIEVABLE AS WRITTEN. hazard_coefficients
     .json records .fit_method = "ridge(alpha=0.0001)" — the string
     _fit_poisson_glm returns on the COLD path (hazard_fit.py:180). fit_betas'
     warm branch returns "ridge(alpha=0.0001, warm_start)" by construction
     (bootstrap_se.py:149). G1 therefore checks the alpha embedded in the
     string and records both strings verbatim; the artifact's own method string
     is additionally reported as evidence that the adopted v4 point is itself a
     COLD fit.
  4. SEED INDEXING. The spec says "seeds 1000+s" inside the bullet describing
     the 48 dispersed starts; s is read as the dispersed index 0..47 (seeds
     1000..1047), rung = s // 12. Every seed is recorded per start so the
     reading is auditable.
  5. sigma FLOOR. "floored at 0.05 absolute" is implemented as
     sigma = maximum(rung * |head_prod|, 0.05) elementwise — a flat absolute
     floor, not rung * 0.05.

FAILURE AND PROBE SEMANTICS (added after a --limit 3 timing probe surfaced two
defects; deviations 6-8):
  * The penalized objective is computed in numpy as
    y*eta - exp(eta) - gammaln(y+1) with the linear predictor scanned for
    overflow FIRST, not through GLM.loglike. At a non-converged parameter
    vector exp(eta) overflows and GLM.loglike returns inf - inf = NaN, which
    the first draft printed as "OK" and fed into the optimum census; a
    dispersed start reported obj = 2.15e+266 and the cold start obj = NaN, both
    counted as landings.
  * THE ANCHOR IS AN EVALUATION, NOT A REFIT. The reference objective is
    penalized_objective(design, frozen 317-vector) — hazard_coefficients.json's
    own coefficients read in the design's column order — so it cannot "fail to
    converge". A second probe showed why this matters: the fitted warm start
    reproduces the production point exactly and still draws "GLM ridge
    optimization may have failed, |grad|=0.014021", because that incomplete
    convergence is the STANDING character of the committed fit and is the very
    thing C6(iii) exists to measure; and on the ddof-0 design the unpenalized
    IRLS prestep blows the same start up (objective 2.04e13). Anchoring on
    either would make the run unable to adjudicate, forever. The fitted
    warm_production START is still run and reported (leg.warm_start_fit) — it
    measures whether the committed pipeline can walk back to its own adopted
    point — but it defines nothing.
  * A start is CONVERGED under the committed pipeline's OWN criterion, mirrored
    from pathA_resimulate_joint.py:337 (= bootstrap_se.fit_betas:153): finite
    params AND np.abs(macro).max() <= MAX_ABS_BETA, plus a finite penalized
    objective. OPTIMIZER WARNINGS ARE DIAGNOSTICS AND NEVER BY THEMSELVES A
    FAILURE. Everything else is a FAILURE and enters n_failed only — never the
    production-branch count, the distinct-optima census, or the better-optimum
    test. Per-start convergence flags, the IRLS iteration count, eta bounds and
    the warning text are printed and written to the draws CSV.
  * If the anchor EVALUATION is non-finite, that is a genuine hard failure: the
    leg stops with the reason attached (status GATE_FAILURE).
  * Every optimizer call is wrapped: a blown-up or raising IRLS prestep is
    recorded (fit_error) and the start is still scored and failed on the
    criterion above — it cannot crash the leg.
  * A run that did not complete all 50 starts of the primary leg (or in which
    the primary leg did not run at all) emits NO verdict code and exits
    PROBE_INCOMPLETE. Timing probes cannot produce MAJORITY/MINORITY verdicts.
  * Legs are reordered so the primary (production, ddof-0) leg runs first, so
    that --limit exercises the leg the blocking gate G1 lives on.

PARITY GATES (all BLOCKING; on failure status=GATE_FAILURE, artifact still
written, exit 1, nothing lands):
  G0 the reimplemented fit reproduces bootstrap_se.fit_betas field-for-field on
     the ddof-1 design at spec v4 (1e-12) and reproduces
     seasonality_concave_gap.fit_with_month_dummies on the ddof-0 design
     (1e-12). Added here, not in the spec — it is what licenses the
     reimplementation.
  G1 the production anchor on the primary leg: the design's columns map
     one-for-one onto the 317 committed coefficients of
     hazard_coefficients.json, the evaluation at that frozen vector is finite,
     and the artifact's ridge alpha is this run's alpha (deviation 3). The
     older form of G1 — the warm-start REFIT reproducing the committed macro
     coefficients to 1e-9 — is retained under
     G1_production_anchor.warm_start_refit_vs_anchor with its own pass flag but
     is NOT blocking (deviation 9).
  G2 n_train = 10,176 and n_strata = 296 (hazard_coefficients.json .n_train /
     .n_strata).
  G3 _month_dummy_matrix yields exactly 11 columns and the head length is 22.

PRE-COMMITTED EXPECTATION (R1's own: "majority land on production branch").
Concretely: >= 26/50 on the production branch, and — the sharper prediction —
the production branch has the best (lowest) penalized objective among all
distinct optima found. Branch classification, fixed ex ante: a start lands on
the production branch iff all three macro coefficients are within 0.02
(standardized units) of the spec-v4 production values (+0.6468566611612588,
-0.17126111626112517, -0.007112288418868083) AND the penalized objective is
within 1e-4 of the production fit's. The full triple and the objective are
reported for EVERY start; non-production landings are clustered by rounding the
triple to 3 decimals and reported with their objective and multiplicity.

LANDING RULE (ex ante; ALL tex landings queue for Eugene):
  (iii-a) MAJORITY_PRODUCTION and production has the best objective (expected):
          tex 981's "bootstrap replications under the spec v4 seasonal design
          are branch-unstable (…)" gains its scope made explicit and measured —
          "…branch-unstable on resampled panels (…); on the production panel
          itself N of 50 dispersed starts land on the production branch and no
          start reaches a better penalized optimum (run
          \\texttt{pathA\\_cold\\_starts})". Same clause echoes at tex 623. The
          exclusion sentence STAYS — it rests on the resampled instability,
          which this run does not touch.
  (iii-b) MINORITY_PRODUCTION but production still has the best objective: the
          production point is the optimum and the basin is small. Report the
          count honestly; the exclusion is STRENGTHENED, not weakened. Land in
          the same two sentences with the unfavorable number.
  (iii-c) BETTER_OPTIMUM_FOUND — a start reaches a strictly better penalized
          objective than production (lower by > 1e-4 with a materially
          different macro triple): STOP. REPORT TO EUGENE. LAND NOTHING. Path A
          is excluded from every headline figure, so NO headline number is at
          risk and nothing propagates — but the disclosure sentences would all
          need re-derivation, and that is an author decision, not a spec
          branch. Sites in scope if it fires: tex 290, 310, 390, 400, 680, 978,
          980, 981, 983, 987, 995-998, 1003, 1051, 1053, 1088, plus
          pathA_seasonal_adoption_results.json .gate_b_v4_target (trapped_b
          928.892970289881, r_lag0 -0.37817286723880483, peak_lag -2) and every
          gate asserting them.                                      [posture]
  (iii-d) The true cold start alone diverges but all dispersed starts converge
          to production: the EXPECTED signature of the Gate-B lesson. Report as
          confirmation of the warm-start device; no tex change beyond (iii-a)'s
          clause. Recorded as verdict.cold_start_diverged_alone.

MUST NOT CHANGE (spec C6.7): hazard/bootstrap_se.py,
hazard/bootstrap_resimulate.py, hazard/ridge_reference_weighting.py,
hazard/pathA_seasonal_adoption.py, hazard/pathA_v4_holdout.py,
hazard/seasonality_concave_gap.py, hazard/config.py (RIDGE_ALPHA,
RIDGE_ALPHA_GRID, AGE_SPLINE_KNOTS, HOLDOUT_DATE); hazard_bootstrap_draws.csv
and hazard_bootstrap_se.json; every committed artifact. Path A's $928.9B /
121.5% and its exclusion from every headline figure. No Path A result may enter
any headline number under any branch.

Run:  cd hazard
      python3 pathA_cold_starts.py --limit 3   # timing probe; runs the PRIMARY
                                               # leg first, exits
                                               # PROBE_INCOMPLETE, no verdict
      python3 pathA_cold_starts.py             # 2 legs x 50 starts, adjudicates
      python3 pathA_cold_starts.py --legs prod_direct
      -> data/pathA_cold_starts_results.json + data/pathA_cold_starts_draws.csv
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm
from scipy import special

from bootstrap_se import BETA_NAMES, MAX_ABS_BETA, fit_betas, production_start_head
from config import AGE_SPLINE_KNOTS, HAZARD_COEF_PATH, HOLDOUT_DATE, PANEL_PATH
from hazard_fit import (
    MONTH_COLS,
    _age_spline_basis,
    _fit_poisson_glm,
    _month_dummy_matrix,
    _orthogonalize_burnout,
    enrich_panel_with_macro,
)
from seasonality_concave_gap import fit_with_month_dummies

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "pathA_cold_starts_results.json"   # NEW
DRAWS_CSV = DATA_DIR / "pathA_cold_starts_draws.csv"         # NEW

ALPHA = 1e-4
N_STARTS = 50
N_DISPERSED = 48
SIGMA_LADDER = [0.25, 0.5, 1.0, 2.0]
PER_RUNG = 12
SEED_BASE = 1000
SIGMA_FLOOR = 0.05

BRANCH_MACRO_TOL = 0.02
BRANCH_OBJ_TOL = 1e-4
BETTER_OBJ_TOL = 1e-4
MAJORITY = 26
CLUSTER_DECIMALS = 3

TOL_G0 = 1e-12
TOL_G1 = 1e-9
N_TRAIN = 10176
N_STRATA = 296
HEAD_LEN_V4 = 22

# exp() overflows float64 above ~709.78; anything near it means the parameter
# vector is nowhere near a solution and the objective is meaningless.
ETA_OVERFLOW = 700.0
# statsmodels warning texts that mean the RIDGE solve did not converge. Scoped
# deliberately to the ridge/elastic-net step: an IRLS maxiter warning from the
# prestep is NOT a start failure — _fit_poisson_glm and fit_betas both tolerate
# a non-converged IRLS and only require finite params, and the prestep's status
# is carried separately as irls_converged.
NONCONVERGENCE_MARKERS = ("ridge optimization may have failed",
                          "Elastic net fitting did not converge")

PROD_V4 = {
    "rate_gap_bps": 0.6468566611612588,
    "burnout_orth": -0.17126111626112517,
    "friction": -0.007112288418868083,
}
AGE_NAMES = ["age_linear"] + [f"age_spline_{k}" for k in AGE_SPLINE_KNOTS]
HEAD_NAMES = ["const"] + AGE_NAMES + BETA_NAMES + MONTH_COLS

LEGS = {
    # name: (standardization convention, irls prestep)
    "prod_warm": ("ddof0", True),
    "fitbetas_warm": ("ddof1", True),
    "prod_direct": ("ddof0", False),
}
DEFAULT_LEGS = ["prod_warm", "fitbetas_warm"]
PRIMARY_LEG = "prod_warm"   # the production (ddof-0) design; G1 lives here


def _np(o):
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(f"not serializable: {type(o)}")


def _f(x):
    """float, or None when non-finite — keeps NaN/inf out of the artifact."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


# --------------------------------------------------------------------------
def load_train() -> pd.DataFrame:
    """bootstrap_se.main()'s training frame (lines 278-283), verbatim."""
    panel = pl.read_parquet(PANEL_PATH)
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    return pdf[pdf["period"] < HOLDOUT_DATE].copy()


def _moments(series: pd.Series, convention: str) -> tuple[float, float]:
    """'ddof1' = pandas (bootstrap_se.fit_betas:107-110); 'ddof0' = numpy on the
    extracted array (seasonality_concave_gap.fit_with_month_dummies:84, the
    construction that DEFINES spec v4 production)."""
    arr = series.to_numpy(dtype=np.float64)
    if convention == "ddof0":
        return float(arr.mean()), (float(arr.std()) or 1.0)
    return float(series.mean()), (float(series.std()) or 1.0)


def build_design(train: pd.DataFrame, convention: str) -> dict:
    """Spec-v4 design: const | age spline (7) | gap, burn, fric | months (11) |
    stratum FE (295) — the bootstrap_se.fit_betas column order, so macro sits
    at params[1+k : 4+k]."""
    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean = (train.groupby("stratum_id")["burnout"]
                   .transform(lambda s: s - s.mean()).to_numpy())
    burnout_orth, _ = _orthogonalize_burnout(age_basis, burn_demean)
    gm, gs = _moments(train["rate_gap_bps"], convention)
    fm, fs = _moments(train["friction"], convention)
    # the PRODUCTION (ddof-0) moments are always carried, whatever this design's
    # convention is: they are the units hazard_coefficients.json is written in,
    # and anchor_from_artifact needs the ratio to translate the frozen vector.
    _, gs0 = _moments(train["rate_gap_bps"], "ddof0")
    _, fs0 = _moments(train["friction"], "ddof0")
    bs = float(burnout_orth.std()) or 1.0
    months = _month_dummy_matrix(train["period"])
    dummies = pd.get_dummies(train["stratum_id"], prefix="fe_stratum",
                             drop_first=True)
    fe_columns = list(dummies.columns)
    X = np.column_stack([
        age_basis,
        (train["rate_gap_bps"].to_numpy() - gm) / gs,
        burnout_orth / bs,
        (train["friction"].to_numpy() - fm) / fs,
        months,
        dummies.to_numpy(dtype=np.float64),
    ])
    X = sm.add_constant(X, has_constant="add")
    y = train["events"].to_numpy()
    offset = np.log(train["exposure"].to_numpy())
    model = sm.GLM(y, X, family=sm.families.Poisson(), offset=offset)
    return {"X": X, "y": np.asarray(y, dtype=np.float64),
            "offset": np.asarray(offset, dtype=np.float64), "model": model,
            "gammaln_y1": special.gammaln(np.asarray(y, dtype=np.float64) + 1.0),
            "nobs": float(len(y)),
            "gm": gm, "gs": gs, "fm": fm, "fs": fs, "bs": bs,
            "gs_ddof0": gs0, "fs_ddof0": fs0,
            "k_age": age_basis.shape[1], "n_months": months.shape[1],
            "fe_columns": fe_columns, "col_names": HEAD_NAMES + fe_columns,
            "convention": convention,
            "reference_stratum": sorted(train["stratum_id"].unique())[0]}


def penalized_objective(design: dict, params, alpha: float = ALPHA) -> dict:
    """The exact function statsmodels GLM._fit_ridge minimizes:
       -loglike(b)/nobs + alpha * sum(b**2)/2
    (statsmodels 0.14.6, genmod/generalized_linear_model.py). RECOMPUTED
    post-fit — fit_regularized returns a RegularizedResults carrying only
    .params, so the objective cannot be read off the fit.

    GUARDED (probe defect 1). The Poisson term is evaluated as
        y*eta - exp(eta) - gammaln(y+1)
    directly in numpy rather than through GLM.loglike, for two reasons:
      * at a non-converged parameter vector exp(eta) overflows to +inf and
        GLM.loglike returns y*log(mu) - mu = inf - inf = NaN, which the caller
        previously printed as a finite-looking "OK" and fed into the optimum
        census;
      * GLM.loglike reads scale off the model object, and the same sm.GLM
        instance is mutated by every .fit()/.fit_regularized() call in the leg,
        so scoring through it is not state-independent.
    The linear predictor is scanned first and a non-finite / overflowing
    evaluation is REPORTED as such (finite=False + reason) instead of being
    silently returned as NaN. Mathematically identical to GLM.loglike wherever
    both are finite (log(exp(eta)) == eta; y=0 cells contribute 0 under both,
    matching statsmodels' xlogy convention)."""
    out = {"objective": float("nan"), "finite": False, "reason": "",
           "eta_max": None, "eta_min": None}
    b = np.asarray(params, dtype=np.float64).ravel()
    if not np.isfinite(b).all():
        out["reason"] = "non-finite parameter vector"
        return out
    eta = design["X"].dot(b) + design["offset"]
    if not np.isfinite(eta).all():
        out["reason"] = "non-finite linear predictor"
        return out
    out["eta_max"], out["eta_min"] = float(np.max(eta)), float(np.min(eta))
    if out["eta_max"] > ETA_OVERFLOW:
        out["reason"] = (f"exp overflow: max eta {out['eta_max']:.4g} > "
                         f"{ETA_OVERFLOW:g}")
        return out
    with np.errstate(over="ignore", invalid="ignore"):
        mu = np.exp(eta)
        llf = float(np.sum(design["y"] * eta - mu - design["gammaln_y1"]))
    if not np.isfinite(llf):
        out["reason"] = "non-finite log-likelihood"
        return out
    obj = float(-(llf / design["nobs"])
                + alpha * float(np.sum(b ** 2)) / 2.0)
    if not np.isfinite(obj):
        out["reason"] = "non-finite objective"
        return out
    out["objective"], out["finite"] = obj, True
    return out


def _statsmodels_objective(design: dict, params, alpha: float = ALPHA):
    """Informational cross-check of penalized_objective against GLM.loglike.
    Non-gating; recorded once, at the anchor, so the finite objective the
    verdict rests on is shown to agree with statsmodels' own evaluation."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = design["model"]
            b = np.asarray(params, dtype=np.float64).ravel()
            val = float(-(model.loglike(b) / model.nobs)
                        + alpha * float(np.sum(b ** 2)) / 2.0)
        return val if np.isfinite(val) else None
    except Exception as exc:                    # noqa: BLE001 — informational
        return f"unavailable: {repr(exc)[:120]}"


def anchor_from_artifact(design: dict, prod: dict) -> dict:
    """THE ANCHOR IS AN EVALUATION, NOT A REFIT (second-probe defect 1).

    The reference objective the branch rule and the better-optimum test are
    measured against is the penalized objective AT THE FROZEN PRODUCTION
    PARAMETER VECTOR — all 317 coefficients of hazard_coefficients.json, read in
    this design's column order — not at whatever a warm-started refit happens to
    return. An evaluation cannot "fail to converge", so the standing character
    of the committed ridge fit (statsmodels warns |grad| ~ 0.014 on it, which is
    precisely what C6(iii) exists to measure) can no longer invalidate the
    anchor. If the EVALUATION is non-finite, that is a genuine hard failure.

    UNITS. The committed vector is in the ddof-0 units of
    seasonality_concave_gap.fit_with_month_dummies. On a ddof-1 design the same
    regressor column is scaled by s_ddof0 / s_ddof1, so the coefficient that
    leaves the linear predictor unchanged is b * (s_design / s_ddof0), applied
    to the rate-gap and friction entries only (the burnout block is numpy ddof-0
    in BOTH constructions, and const / age spline / months / FE are unstandardized).
    The translation is therefore exact for the log-likelihood and moves only the
    ridge penalty, by O(1e-9). On the ddof-0 design both factors are exactly 1.0.
    """
    coefs = prod["coefficients"]
    names = list(design["col_names"])
    missing = [n for n in names if n not in coefs]
    out = {"finite": False, "objective": float("nan"), "reason": "",
           "n_design_columns": len(names),
           "n_committed_coefficients": len(coefs),
           "missing_columns": missing[:5],
           "column_map_exact": bool(not missing and len(names) == len(coefs))}
    if missing or len(names) != len(coefs):
        out["reason"] = (f"design/artifact column mismatch: {len(names)} design "
                         f"columns vs {len(coefs)} committed coefficients, "
                         f"{len(missing)} missing")
        return out
    b = np.array([float(coefs[n]) for n in names], dtype=np.float64)
    fg = float(design["gs"] / design["gs_ddof0"])
    ff = float(design["fs"] / design["fs_ddof0"])
    b[names.index("rate_gap_bps")] *= fg
    b[names.index("friction")] *= ff
    obj = penalized_objective(design, b)
    k = design["k_age"]
    out.update({
        "params": b,
        "head": b[:HEAD_LEN_V4].copy(),
        "macro": {n: float(b[1 + k + i]) for i, n in enumerate(BETA_NAMES)},
        "unit_translation": {"rate_gap_bps_factor": fg, "friction_factor": ff,
                             "burnout_orth_factor": 1.0,
                             "exact_for_loglike": True},
        "objective": obj["objective"], "finite": obj["finite"],
        "reason": obj["reason"], "eta_max": obj["eta_max"],
        "eta_min": obj["eta_min"],
        "source": "hazard_coefficients.json .coefficients (frozen, 317 entries)",
    })
    return out


def _irls_iterations(irls) -> int | None:
    """Best-effort IRLS iteration count. GLMResults exposes it as
    fit_history['iteration']; _fit_ridge's BFGS step exposes nothing at all
    (RegularizedResults carries only .params), so the ridge leg reports None."""
    try:
        hist = getattr(irls, "fit_history", None)
        if isinstance(hist, dict):
            it = hist.get("iteration")
            if it is not None and np.isscalar(it):
                return int(it)
            dev = hist.get("deviance")
            if dev is not None:
                return int(len(dev))
        it = getattr(irls, "iteration", None)
        return int(it) if it is not None else None
    except Exception:                           # noqa: BLE001 — diagnostic only
        return None


def fit_from_start(design: dict, start_head: np.ndarray | None,
                   irls_prestep: bool, alpha: float = ALPHA) -> dict:
    """bootstrap_se.fit_betas' fit path (lines 133-156), reimplemented so the
    full parameter vector survives for the objective.

    CONVERGENCE POLICY = the committed pipeline's own criterion, mirrored from
    pathA_resimulate_joint.py:337 (itself bootstrap_se.fit_betas:153):
        finite params AND np.abs(macro).max() <= MAX_ABS_BETA
    plus a finite penalized objective. Optimizer warnings are RECORDED as
    diagnostics and are NEVER by themselves a failure (second-probe defect 2):
    statsmodels warns "GLM ridge optimization may have failed, |grad|=0.014" on
    the committed production fit itself — that incomplete convergence is the
    standing character of the adopted point and is exactly what this run exists
    to measure, so treating the warning as failure would disqualify the truth.
    Every optimizer call is wrapped so a blown-up IRLS prestep cannot crash the
    leg (second-probe defect 3): it is recorded and the start continues to be
    scored, failing on the criterion above."""
    X, y, offset, model = design["X"], design["y"], design["offset"], design["model"]
    irls_converged, irls_iters = None, None
    fit_error, result = "", None
    fit_method = ("cold(_fit_poisson_glm)" if start_head is None
                  else (f"ridge(alpha={alpha}, warm_start)" if irls_prestep
                        else f"ridge(alpha={alpha}, direct_start)"))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            if start_head is None:
                result, fit_method = _fit_poisson_glm(X, y, offset, alpha)
            else:
                start = np.zeros(X.shape[1])
                start[: len(start_head)] = start_head
                warm = start
                if irls_prestep:
                    try:
                        irls = model.fit(maxiter=100, start_params=start)
                        ok = np.isfinite(np.asarray(irls.params)).all()
                        irls_converged = (bool(getattr(irls, "converged", False))
                                          and ok)
                        irls_iters = _irls_iterations(irls)
                        warm = irls.params if ok else start
                    except Exception as exc:    # noqa: BLE001 — recorded, not fatal
                        irls_converged = False
                        fit_error = f"IRLS prestep raised: {repr(exc)[:160]}"
                result = model.fit_regularized(
                    method="elastic_net", alpha=alpha, L1_wt=0.0,
                    maxiter=100, start_params=warm,
                )
        except Exception as exc:                # noqa: BLE001 — recorded, not fatal
            fit_error = (fit_error + " | " if fit_error else "") + \
                        f"ridge solve raised: {repr(exc)[:160]}"
        messages = [str(w.message) for w in caught]
    optimizer_warning = "; ".join(m[:140] for m in messages)[:400]
    optimizer_converged = not any(mk in m for m in messages
                                  for mk in NONCONVERGENCE_MARKERS)

    if result is None:
        params = np.full(X.shape[1], np.nan)
    else:
        params = np.asarray(result.params, dtype=np.float64).ravel()
    k = design["k_age"]
    macro = params[1 + k: 4 + k]
    finite_params = bool(np.isfinite(params).all())
    max_abs_macro = float(np.abs(macro).max()) if finite_params else float("inf")
    beta_ok = finite_params and max_abs_macro <= MAX_ABS_BETA
    obj = penalized_objective(design, params, alpha)
    failure = ""
    if fit_error and not beta_ok:
        failure = fit_error
    elif not beta_ok:
        failure = (f"|macro beta| {max_abs_macro:.3g} > {MAX_ABS_BETA}"
                   if finite_params else "non-finite parameter vector")
    elif not obj["finite"]:
        failure = f"objective: {obj['reason']}"
    return {"params": params, "fit_method": fit_method,
            "fit_error": fit_error, "max_abs_macro": (
                max_abs_macro if np.isfinite(max_abs_macro) else None),
            "irls_converged": irls_converged, "irls_iterations": irls_iters,
            "optimizer_converged": bool(optimizer_converged),
            "optimizer_warning": optimizer_warning,
            "objective_finite": bool(obj["finite"]),
            "objective_reason": obj["reason"],
            "eta_max": obj["eta_max"], "eta_min": obj["eta_min"],
            # pathA_resimulate_joint.py:337 criterion + finite objective;
            # optimizer_converged is diagnostic ONLY (second-probe defect 2)
            "converged": bool(beta_ok and obj["finite"]),
            "failure": failure,
            "macro": {n: float(params[1 + k + i])
                      for i, n in enumerate(BETA_NAMES)},
            "head": params[:HEAD_LEN_V4].copy(),
            "objective": obj["objective"]}


def start_plan(head_prod: np.ndarray) -> list[dict]:
    """1 warm production anchor + 1 true cold start + 48 dispersed."""
    plan = [{"start_id": 0, "kind": "warm_production", "sigma_rung": None,
             "seed": None, "head": head_prod.copy()},
            {"start_id": 1, "kind": "cold", "sigma_rung": None, "seed": None,
             "head": None}]
    for s in range(N_DISPERSED):
        rung = SIGMA_LADDER[s // PER_RUNG]
        seed = SEED_BASE + s
        z = np.random.default_rng(seed).standard_normal(len(head_prod))
        sigma = np.maximum(rung * np.abs(head_prod), SIGMA_FLOOR)
        plan.append({"start_id": 2 + s, "kind": "dispersed",
                     "sigma_rung": rung, "seed": seed,
                     "head": head_prod + sigma * z})
    assert len(plan) == N_STARTS, len(plan)
    return plan


def run_leg(name: str, design: dict, head_prod: np.ndarray,
            limit: int | None) -> list[dict]:
    convention, prestep = LEGS[name]
    plan = start_plan(head_prod)
    if limit is not None:
        plan = plan[:limit]
    rows = []
    t0 = time.perf_counter()
    for st in plan:
        f = fit_from_start(design, st["head"], prestep)
        row = {"leg": name, "convention": convention, "irls_prestep": prestep,
               "start_id": st["start_id"], "kind": st["kind"],
               "sigma_rung": st["sigma_rung"], "seed": st["seed"],
               "converged": f["converged"],
               "optimizer_converged": f["optimizer_converged"],
               "objective_finite": f["objective_finite"],
               "irls_converged": f["irls_converged"],
               "irls_iterations": f["irls_iterations"],
               "eta_max": f["eta_max"], "eta_min": f["eta_min"],
               "max_abs_macro": f["max_abs_macro"],
               "failure": f["failure"], "fit_error": f["fit_error"],
               "optimizer_warning": f["optimizer_warning"],
               "fit_method": f["fit_method"],
               **f["macro"],
               "penalized_objective": f["objective"]}
        row["_head"] = f["head"]
        row["_params"] = f["params"]      # full vector; never written to CSV
        rows.append(row)
        obj_txt = (f"{f['objective']:.10f}" if f["objective_finite"]
                   else f"NONFINITE({f['objective_reason']})")
        print(f"  [{name}] start {st['start_id']:>2} {st['kind']:<15} "
              f"rung={str(st['sigma_rung']):>4} "
              f"gap={f['macro']['rate_gap_bps']:+.4f} "
              f"burn={f['macro']['burnout_orth']:+.4f} "
              f"fric={f['macro']['friction']:+.5f} "
              f"obj={obj_txt} "
              f"conv={f['converged']} "
              f"(opt={f['optimizer_converged']}, irls={f['irls_converged']}, "
              f"iters={f['irls_iterations']}) "
              f"{'OK' if f['converged'] else 'FAILED: ' + f['failure']} "
              f"({time.perf_counter() - t0:.0f}s elapsed)")
    return rows


def classify(rows: list[dict], anchor: dict) -> dict:
    """Census over CONVERGED starts only, against the EVALUATED anchor.

    `anchor` is anchor_from_artifact's evaluation at the frozen production
    parameter vector — NOT the fitted warm_production start. A start whose
    parameters left MAX_ABS_BETA or whose penalized objective is non-finite is a
    FAILURE: it enters n_failed and enters NEITHER the production-branch count,
    NOR the distinct-optima census, NOR the better-optimum test. Optimizer
    warnings do not make a start a failure (second-probe defect 2)."""
    a_head, a_obj = anchor.get("head"), anchor["objective"]
    anchor_valid = bool(anchor["finite"])
    anchor_reason = "" if anchor_valid else (
        anchor.get("reason") or "anchor evaluation is not finite")
    a_macro = anchor.get("macro", dict(PROD_V4))
    if a_head is None:
        a_head = np.full(HEAD_LEN_V4, np.nan)

    warm = next((r for r in rows if r["kind"] == "warm_production"), None)
    for r in rows:
        r["l2_distance_to_production"] = float(
            np.linalg.norm(np.asarray(r["_head"]) - np.asarray(a_head)))
        r["l2_macro_distance_to_production"] = float(np.linalg.norm(
            [r[n] - a_macro[n] for n in BETA_NAMES]))
        macro_close = all(abs(r[n] - PROD_V4[n]) <= BRANCH_MACRO_TOL
                          for n in BETA_NAMES)
        obj_close = (anchor_valid and np.isfinite(r["penalized_objective"])
                     and abs(r["penalized_objective"] - a_obj) <= BRANCH_OBJ_TOL)
        r["on_production_branch"] = bool(r["converged"] and macro_close
                                         and obj_close)

    ok = [r for r in rows if r["converged"]]
    failed = [r for r in rows if not r["converged"]]
    n_failed = len(failed)
    n_branch = sum(1 for r in ok if r["on_production_branch"])

    clusters: dict = defaultdict(list)
    for r in ok:
        if r["on_production_branch"]:
            continue
        key = tuple(round(float(r[n]), CLUSTER_DECIMALS) for n in BETA_NAMES)
        clusters[key].append(r)
    distinct = [{"triple": dict(zip(BETA_NAMES, k)),
                 "objective_min": float(min(x["penalized_objective"] for x in v)),
                 "objective_max": float(max(x["penalized_objective"] for x in v)),
                 "count": len(v),
                 "start_ids": [x["start_id"] for x in v]}
                for k, v in sorted(clusters.items(),
                                   key=lambda kv: min(x["penalized_objective"]
                                                      for x in kv[1]))]

    # (iii-c) test: converged starts scored against the EVALUATED anchor
    better = ([r for r in ok
               if r["penalized_objective"] < a_obj - BETTER_OBJ_TOL
               and any(abs(r[n] - a_macro[n]) > BRANCH_MACRO_TOL
                       for n in BETA_NAMES)]
              if anchor_valid else [])
    cold = next((r for r in rows if r["kind"] == "cold"), None)
    dispersed = [r for r in rows if r["kind"] == "dispersed"]
    cold_alone = bool(
        cold is not None and not cold["on_production_branch"]
        and dispersed and all(r["on_production_branch"] for r in dispersed))

    return {
        "n_starts": len(rows), "n_failed": n_failed,
        "n_converged": len(ok),
        "n_on_production_branch": n_branch,
        "anchor_valid": anchor_valid,
        "anchor_invalid_reason": anchor_reason,
        "anchor_kind": "evaluation_at_frozen_production_vector",
        "anchor_objective": _f(a_obj),
        "anchor_macro": {n: _f(a_macro[n]) for n in BETA_NAMES},
        "anchor_eta_max": _f(anchor.get("eta_max")),
        "anchor_unit_translation": anchor.get("unit_translation"),
        # the fitted warm_production START is kept because it is informative —
        # it measures whether the committed pipeline can walk back to its own
        # adopted point — but it no longer defines the anchor.
        "warm_start_fit": ({
            "converged": bool(warm["converged"]),
            "objective": _f(warm["penalized_objective"]),
            "macro": {n: _f(warm[n]) for n in BETA_NAMES},
            "objective_minus_anchor": (
                _f(warm["penalized_objective"] - a_obj)
                if anchor_valid else None),
            "max_abs_macro_gap_vs_anchor": _f(
                max(abs(warm[n] - a_macro[n]) for n in BETA_NAMES)),
            "optimizer_converged": bool(warm["optimizer_converged"]),
            "optimizer_warning": warm["optimizer_warning"],
            "irls_converged": warm["irls_converged"],
            "irls_iterations": warm["irls_iterations"],
            "failure": warm["failure"],
        } if warm is not None else None),
        "failures": [{"start_id": r["start_id"], "kind": r["kind"],
                      "sigma_rung": r["sigma_rung"], "reason": r["failure"],
                      "eta_max": _f(r["eta_max"]),
                      **{n: _f(r[n]) for n in BETA_NAMES}} for r in failed],
        "best_objective_found": (
            float(min(r["penalized_objective"] for r in ok)) if ok else None),
        "production_is_best_objective": bool(anchor_valid and not better),
        "better_optimum_starts": [{"start_id": r["start_id"],
                                   "kind": r["kind"],
                                   "objective": r["penalized_objective"],
                                   "objective_gap": a_obj - r["penalized_objective"],
                                   **{n: r[n] for n in BETA_NAMES}}
                                  for r in better],
        "distinct_optima": distinct,
        "cold_start_converged": (bool(cold["converged"]) if cold else None),
        "cold_start_on_production_branch": (bool(cold["on_production_branch"])
                                            if cold else None),
        "cold_start_macro": ({n: cold[n] for n in BETA_NAMES} if cold else None),
        "cold_start_objective": (
            (cold["penalized_objective"]
             if np.isfinite(cold["penalized_objective"]) else None)
            if cold else None),
        "cold_start_failure": (cold["failure"] if cold else None),
        "cold_start_diverged_alone": cold_alone,
        "by_rung": {str(rung): {
            "n": sum(1 for r in dispersed if r["sigma_rung"] == rung),
            "n_on_production_branch": sum(
                1 for r in dispersed
                if r["sigma_rung"] == rung and r["on_production_branch"]),
        } for rung in SIGMA_LADDER},
    }


# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", default=",".join(DEFAULT_LEGS),
                    help=f"comma-separated subset of {sorted(LEGS)}")
    ap.add_argument("--limit", type=int, default=None,
                    help="run only the first N starts per leg (timing probe)")
    args = ap.parse_args()
    legs = [l.strip() for l in args.legs.split(",") if l.strip()]
    for l in legs:
        assert l in LEGS, f"unknown leg {l!r}; choose from {sorted(LEGS)}"
    # PRIMARY FIRST (probe defect 3): under --limit only the leading starts of
    # each leg run, and the blocking gate G1 lives on the primary (production,
    # ddof-0) leg — so a timing probe must exercise that leg, not the
    # spec-literal one. Order is normalized here rather than left to --legs.
    legs = ([PRIMARY_LEG] if PRIMARY_LEG in legs else []) + \
           [l for l in legs if l != PRIMARY_LEG]
    t0 = time.perf_counter()

    prod = json.loads(Path(HAZARD_COEF_PATH).read_text())
    assert int(prod.get("spec_version", -1)) == 4, "production is not spec v4"
    head_prod = production_start_head(prod)

    print("Building the production training frame "
          "(bootstrap_se.main filters) …")
    train = load_train()
    n_train, n_strata = int(len(train)), int(train["stratum_id"].nunique())
    print(f"  train {n_train:,} cells | strata {n_strata}")

    gates: dict = {
        "G2_panel": {"n_train": {"got": n_train, "want": N_TRAIN},
                     "n_strata": {"got": n_strata, "want": N_STRATA},
                     "pass": bool(n_train == N_TRAIN and n_strata == N_STRATA)},
    }

    designs = {c: build_design(train, c)
               for c in {LEGS[l][0] for l in legs}}
    any_design = designs[LEGS[legs[0]][0]]
    # G0's ddof0 arm compares against fit_with_month_dummies, whose month block
    # is pd.get_dummies(period.dt.month, drop_first=True); that agrees with
    # _month_dummy_matrix only if all 12 calendar months appear. Assert it.
    months_present = sorted(pd.to_datetime(train["period"]).dt.month.unique())
    gates["G3_design_shape"] = {
        "n_month_dummies": {"got": int(any_design["n_months"]), "want": 11},
        "head_len": {"got": int(len(head_prod)), "want": HEAD_LEN_V4},
        "n_fe_columns": int(len(any_design["fe_columns"])),
        "fe_columns_match_artifact": bool(
            any_design["fe_columns"] == list(prod["fe_columns"])),
        "reference_stratum": {"got": any_design["reference_stratum"],
                              "want": prod["reference_stratum"]},
        "all_12_months_present": bool(months_present == list(range(1, 13))),
        "pass": bool(any_design["n_months"] == 11
                     and len(head_prod) == HEAD_LEN_V4
                     and any_design["fe_columns"] == list(prod["fe_columns"])
                     and any_design["reference_stratum"]
                     == prod["reference_stratum"]
                     and months_present == list(range(1, 13))),
    }

    # ---- G0: reimplementation fidelity ------------------------------------
    g0 = {}
    if "ddof1" in designs:
        a = fit_betas(train, ALPHA, start_head=head_prod, seasonal=True)
        b = fit_from_start(designs["ddof1"], head_prod, True)
        d = max([abs(a[n] - b["macro"][n]) for n in BETA_NAMES]
                + [float(np.abs(np.asarray(a["params_head"])
                                - b["head"]).max())])
        g0["ddof1_vs_fit_betas"] = {"max_abs_diff": float(d),
                                    "pass": bool(d <= TOL_G0)}
    units_check = None
    if "ddof0" in designs:
        coefs_pc, months_pc, method_pc = fit_with_month_dummies(train, ALPHA)
        b = fit_from_start(designs["ddof0"], None, True)   # cold == production path
        d = max(abs(b["macro"][n] - float(coefs_pc[n])) for n in BETA_NAMES)
        g0["ddof0_vs_fit_with_month_dummies"] = {
            "max_abs_macro_diff": float(d),
            "fit_method_reimpl": b["fit_method"],
            "fit_method_source": method_pc,
            "pass": bool(d <= TOL_G0)}
        # Diagnostic (NON-gating): is the FROZEN 317-vector still in this
        # design's units on today's inputs? Two independent readings — the
        # committed construction replayed now vs the artifact, and this
        # script's ddof-0 cold fit vs the artifact.
        names0 = list(designs["ddof0"]["col_names"])
        units_check = {
            "fit_with_month_dummies_vs_artifact_max_abs": float(max(
                abs(float(coefs_pc[n]) - float(prod["coefficients"][n]))
                for n in names0)),
            "ddof0_cold_refit_vs_artifact_max_abs": float(np.abs(
                b["params"] - np.array([float(prod["coefficients"][n])
                                        for n in names0])).max()),
            "n_columns": len(names0),
            "note": ("the anchor is evaluated at the frozen vector, so this "
                     "records whether that vector is still the ddof-0 design's "
                     "own solution on today's panel + FRED join; non-gating"),
        }
    gates["G0_reimplementation"] = {"tol": TOL_G0, "checks": g0,
                                    "pass": all(c["pass"] for c in g0.values())}

    # ---- evaluated anchors, one per design (NOT a refit) -------------------
    anchors = {c: anchor_from_artifact(d, prod) for c, d in designs.items()}
    for c, a in anchors.items():
        print(f"  anchor[{c}] evaluated at the frozen 317-vector: "
              f"objective={_f(a['objective'])} finite={a['finite']} "
              f"{a['reason']}")

    # ---- the legs ---------------------------------------------------------
    all_rows, verdicts = [], {}
    for leg in legs:
        convention, _ = LEGS[leg]
        print(f"\n=== leg {leg} (convention {convention}, "
              f"irls_prestep={LEGS[leg][1]}) ===")
        rows = run_leg(leg, designs[convention], head_prod, args.limit)
        verdicts[leg] = classify(rows, anchors[convention])
        all_rows.extend(rows)

    # ---- G1: the anchor ---------------------------------------------------
    primary = (PRIMARY_LEG if PRIMARY_LEG in verdicts
               else (legs[0] if legs and legs[0] in verdicts else None))
    primary_ran = primary is not None
    anchor_row = (next(r for r in all_rows
                       if r["leg"] == primary and r["kind"] == "warm_production")
                  if primary_ran else None)
    # An anchor EVALUATION that is non-finite is a genuine hard failure — but a
    # fitted start that merely warns is not (second-probe defects 1 and 2).
    anchor_bad = {l: x["anchor_invalid_reason"]
                  for l, x in verdicts.items() if not x["anchor_valid"]}
    fac = float(np.sqrt(n_train / (n_train - 1.0)))
    primary_anchor = anchors[LEGS[primary][0]] if primary_ran else {}

    # G1 BLOCKING CLAUSE: the anchor is an evaluation at the frozen vector, so
    # what must hold is (a) the design's columns map one-for-one onto the 317
    # committed coefficients, (b) the evaluation is finite, (c) the artifact's
    # ridge alpha is this run's alpha. The warm-start REFIT comparison is kept
    # and reported with its own pass flag but is NOT blocking: whether the
    # committed pipeline can walk back to its own adopted point is the object
    # of study here, not a precondition for measuring it.
    g1_refit = {}
    if primary_ran:
        for n in BETA_NAMES:
            got = float(anchor_row[n])
            want = float(primary_anchor.get("macro", PROD_V4)[n])
            g1_refit[n] = {"got": got, "want_anchor": want,
                           "want_artifact": PROD_V4[n],
                           "abs_diff_vs_anchor": abs(got - want),
                           "abs_diff_vs_artifact": abs(got - PROD_V4[n]),
                           "pass": bool(abs(got - want) <= TOL_G1)}
    alpha_ok = f"alpha={ALPHA}" in str(prod.get("fit_method"))
    gates["G1_production_anchor"] = {
        "leg": primary,
        "anchor_kind": "evaluation_at_frozen_production_vector",
        "column_map_exact": bool(primary_anchor.get("column_map_exact", False)),
        "n_design_columns": primary_anchor.get("n_design_columns"),
        "n_committed_coefficients": primary_anchor.get(
            "n_committed_coefficients"),
        "anchor_valid": bool(primary_anchor.get("finite", False)),
        "anchor_invalid_reason": (primary_anchor.get("reason", "")
                                  if primary_ran else "primary leg did not run"),
        "anchor_objective": _f(primary_anchor.get("objective")),
        "anchor_eta_max": _f(primary_anchor.get("eta_max")),
        "anchor_unit_translation": primary_anchor.get("unit_translation"),
        "anchor_objective_statsmodels_crosscheck": (
            _statsmodels_objective(designs[LEGS[primary][0]],
                                   primary_anchor["params"])
            if primary_ran and "params" in primary_anchor else None),
        "design_units_check": units_check,
        "warm_start_refit_vs_anchor": {
            "tol": TOL_G1, "checks": g1_refit, "blocking": False,
            "pass": bool(g1_refit and all(c["pass"] for c in g1_refit.values())),
            "fit_method_anchor_start": (anchor_row["fit_method"]
                                        if primary_ran else None),
            "optimizer_warning": (anchor_row["optimizer_warning"]
                                  if primary_ran else None),
            "note": ("the fitted warm_production start; statsmodels warns "
                     "|grad| ~ 0.014 on the committed ridge fit itself, which "
                     "is C6(iii)'s premise, so this is reported, not blocking."),
        },
        "ddof_factor": fac,
        "fit_method_artifact": prod.get("fit_method"),
        "alpha_matches": bool(alpha_ok),
        "pass": bool(primary_ran
                     and primary_anchor.get("column_map_exact", False)
                     and primary_anchor.get("finite", False)
                     and alpha_ok),
        "note": ("DEVIATION 3: the artifact's fit_method is the COLD string "
                 "'ridge(alpha=0.0001)'; fit_betas' warm branch returns "
                 "'…, warm_start' by construction, so G1 compares the alpha "
                 "and records both strings."),
    }

    # cross-leg consistency of the evaluated anchor (NON-gating): the unit
    # translation leaves the linear predictor unchanged, so the two legs'
    # anchors may differ only through the ridge penalty on the two rescaled
    # coefficients — O(1e-9) on a value of ~1.9e6.
    finite_anchors = [a["objective"] for a in anchors.values() if a["finite"]]
    anchor_cross_leg = {
        "objectives": {c: _f(a["objective"]) for c, a in anchors.items()},
        "max_abs_spread": (float(max(finite_anchors) - min(finite_anchors))
                           if len(finite_anchors) > 1 else None),
        "expected_spread_order": 1e-8,
        "note": ("same linear predictor by construction; only the penalty term "
                 "moves under the ddof translation"),
    }

    # ---- draws CSV --------------------------------------------------------
    csv_cols = ["leg", "convention", "irls_prestep", "start_id", "kind",
                "sigma_rung", "seed", "converged", "optimizer_converged",
                "objective_finite", "irls_converged", "irls_iterations",
                "eta_max", "eta_min", "max_abs_macro", "failure", "fit_error",
                "optimizer_warning",
                "fit_method", "rate_gap_bps", "burnout_orth", "friction",
                "penalized_objective", "on_production_branch",
                "l2_distance_to_production", "l2_macro_distance_to_production"]
    pd.DataFrame([{c: r.get(c) for c in csv_cols}
                  for r in all_rows]).to_csv(DRAWS_CSV, index=False)

    # ---- verdict (read off the primary leg, and ONLY if it fully ran) ------
    # (probe defect 2) a leg that ran 3 of 50 starts cannot adjudicate
    # MAJORITY/MINORITY, and a leg that did not run cannot adjudicate at all.
    v = verdicts.get(primary)
    full_run = bool(primary_ran and args.limit is None
                    and v["n_starts"] == N_STARTS)
    code = None
    if not full_run:
        why = ("the primary leg did not run" if not primary_ran else
               f"only {v['n_starts']} of {N_STARTS} starts ran"
               + (" (--limit)" if args.limit is not None else ""))
        action = (f"PROBE ONLY — {why}; no verdict is adjudicated and NOTHING "
                  "may be landed in the manuscript.")
    elif not v["production_is_best_objective"]:
        code, action = "BETTER_OPTIMUM_FOUND", (
            "(iii-c) STOP. REPORT TO EUGENE. LAND NOTHING. No headline number "
            "is at risk (Path A is excluded everywhere), but every Path A "
            "disclosure sentence would need re-derivation — an author "
            "decision, not a spec branch. [posture]")
    elif v["n_on_production_branch"] >= MAJORITY:
        code, action = "MAJORITY_PRODUCTION", (
            "(iii-a) scope tex 981's branch-unstable clause to RESAMPLED "
            "panels and add the measured production-panel count "
            f"({v['n_on_production_branch']} of {v['n_starts']}) plus 'no "
            "start reaches a better penalized optimum (run "
            "\\texttt{pathA\\_cold\\_starts})'; echo at tex 623. The exclusion "
            "sentence STAYS.")
    else:
        code, action = "MINORITY_PRODUCTION", (
            "(iii-b) the production point is the optimum and its basin is "
            "small. Land the honest count in the same two sentences; the "
            "exclusion is STRENGTHENED, not weakened.")

    all_pass = all(bool(gates[g]["pass"]) for g in gates)
    if anchor_bad:
        status = "GATE_FAILURE"
    elif not full_run:
        status = "PROBE_INCOMPLETE"
    else:
        status = "OK" if all_pass else "GATE_FAILURE"

    payload = {
        "mode": "pathA_cold_starts",
        "status": status,
        "spec": ("SPEC_round28_C1_C2_C3_C6.md C6(iii): 50 starts on the "
                 "PRODUCTION panel (1 warm production anchor, 1 true cold, 48 "
                 "dispersed on the sigma ladder {0.25,0.5,1.0,2.0} x "
                 "|head_prod| floored at 0.05, 12 per rung, seeds 1000+s), "
                 "spec v4 seasonal design, alpha=1e-4, FE starting at zero; "
                 "branch = macro triple within 0.02 AND penalized objective "
                 "within 1e-4 of the production fit's."),
        "convexity_note": ("statsmodels GLM.fit_regularized(L1_wt=0) dispatches "
                           "to GLM._fit_ridge, which BFGS-minimizes "
                           "-loglike/nobs + alpha*||b||^2/2. That objective is "
                           "strictly convex, so it has exactly one minimizer: "
                           "a materially lower objective is evidence of "
                           "UNDER-CONVERGENCE at the production point, not of "
                           "a rival mode. Verdict codes are as pre-committed; "
                           "this fixes their reading."),
        "labeled_deviations": [
            "1: two design conventions — production spec v4 is ddof-0 "
            "(seasonality_concave_gap.fit_with_month_dummies), fit_betas is "
            "ddof-1; the primary leg is the production design and G1 is "
            "evaluated there.",
            "2: the IRLS prestep partly defeats the dispersion; the "
            "prod_direct leg is the literal dispersed-start probe.",
            "3: G1's fit_method equality is not achievable as written — the "
            "artifact string is the COLD one; the alpha is compared instead.",
            "4: dispersed seeds are 1000+s for s in 0..47, rung = s // 12.",
            "5: the sigma floor is a flat absolute 0.05.",
            "6: the penalized objective is evaluated in numpy with an "
            "overflow scan on the linear predictor, not through GLM.loglike "
            "(which returns inf-inf = NaN at non-converged parameters and "
            "reads state off a model object this script mutates 50 times per "
            "leg); a non-finite objective makes the start a FAILURE, and a "
            "non-finite anchor hard-fails its leg.",
            "7: convergence is carried from the optimizer via captured "
            "warnings — GLM._fit_ridge discards scipy's success flag and only "
            "warns; non-converged starts are failures and enter neither the "
            "branch count nor the optimum census.",
            "8: legs are reordered so the primary (production, ddof-0) leg "
            "runs first, and a run that did not complete all 50 starts of the "
            "primary leg emits NO verdict code (status PROBE_INCOMPLETE).",
            "9: the anchor is an EVALUATION at the frozen 317-vector, not a "
            "refit; G1's blocking clause is column-map + finiteness + alpha, "
            "and the warm-start refit comparison is retained non-blocking. "
            "Anchoring on a refit made every anchor invalid: the fitted start "
            "reproduces production and still warns |grad|=0.014 (the committed "
            "fit's own standing character), and on the ddof-0 design the IRLS "
            "prestep blows it up.",
            "10: convergence is the committed pipeline's criterion "
            "(pathA_resimulate_joint.py:337) plus a finite objective; "
            "optimizer warnings are recorded, never failure.",
        ],
        "panel": {"n_train": n_train, "n_strata": n_strata,
                  "alpha": ALPHA, "ddof_factor": fac},
        "start_composition": {"n_starts": N_STARTS, "n_dispersed": N_DISPERSED,
                              "sigma_ladder": SIGMA_LADDER,
                              "per_rung": PER_RUNG, "seed_base": SEED_BASE,
                              "sigma_floor_abs": SIGMA_FLOOR},
        "branch_rule": {"macro_tol": BRANCH_MACRO_TOL,
                        "objective_tol": BRANCH_OBJ_TOL,
                        "cluster_decimals": CLUSTER_DECIMALS,
                        "majority_threshold": MAJORITY,
                        "production_v4_macro": PROD_V4},
        "parity_gates": gates,
        "parity_gates_all_pass": all_pass,
        "legs": {l: {"convention": LEGS[l][0], "irls_prestep": LEGS[l][1]}
                 for l in legs},
        "anchor": {c: {k: v for k, v in a.items()
                       if k not in ("params", "head")}
                   for c, a in anchors.items()},
        "anchor_cross_leg_consistency": anchor_cross_leg,
        "primary_leg": primary,
        "primary_leg_complete": bool(full_run),
        "legs_requested": legs,
        "legs_run": sorted(verdicts),
        "limit": args.limit,
        "anchor_invalid_legs": anchor_bad,
        "by_leg": verdicts,
        "draws_csv": DRAWS_CSV.name,
        "verdict": {
            "code": code,
            "adjudicated": bool(code is not None),
            "n_on_production_branch": (v["n_on_production_branch"] if v else None),
            "n_failed": (v["n_failed"] if v else None),
            "distinct_optima": (v["distinct_optima"] if v else None),
            "production_is_best_objective": (
                v["production_is_best_objective"] if v else None),
            "cold_start_diverged_alone": (
                v["cold_start_diverged_alone"] if v else None),
            "manuscript_action": action,
            "propagation": ("none — Path A is excluded from every headline "
                            "figure (tex 290, 978, 1053); under (iii-c) "
                            "nothing lands at all"),
        },
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_np)
        f.write("\n")

    def _fmt(x):
        return f"{x:.10f}" if isinstance(x, float) and np.isfinite(x) else str(x)

    print("\n" + "=" * 66)
    print(f" pathA_cold_starts — status {status} — verdict "
          f"{code if code else 'NOT ADJUDICATED (probe)'}")
    print("=" * 66)
    if v is not None:
        print(f"  primary leg {primary}: {v['n_on_production_branch']}/"
              f"{v['n_starts']} on the production branch, {v['n_failed']} failed"
              f" ({v['n_converged']} converged)")
        print(f"  anchor objective {_fmt(v['anchor_objective'])}  |  best found "
              f"{_fmt(v['best_objective_found'])}  |  production is best: "
              f"{v['production_is_best_objective']}")
        print(f"  distinct non-production optima: {len(v['distinct_optima'])}")
    else:
        print(f"  primary leg {PRIMARY_LEG} did not run "
              f"(legs run: {sorted(verdicts)})")
    print(f"  anchor objectives (evaluated at the frozen 317-vector): "
          f"{anchor_cross_leg['objectives']}  spread "
          f"{anchor_cross_leg['max_abs_spread']}")
    if v is not None and v.get("warm_start_fit"):
        w = v["warm_start_fit"]
        print(f"  warm_production START (informative, non-blocking): "
              f"obj {w['objective']}  Δ vs anchor "
              f"{w['objective_minus_anchor']}  max|Δmacro| "
              f"{w['max_abs_macro_gap_vs_anchor']}  converged {w['converged']}"
              + (f"  warning: {w['optimizer_warning'][:80]}"
                 if w["optimizer_warning"] else ""))
    for leg, reason in anchor_bad.items():
        print(f"  ANCHOR INVALID in leg {leg}: {reason}")
    print(f"  Saved: {RESULTS_JSON} + {DRAWS_CSV}")
    if code == "BETTER_OPTIMUM_FOUND":
        print("  *** (iii-c) STOP — report to Eugene, land nothing. ***")
    if anchor_bad:
        raise SystemExit(
            "GATE_FAILURE — the penalized objective EVALUATED at the frozen "
            f"production vector is not finite in leg(s) {sorted(anchor_bad)} "
            f"({anchor_bad}); this is an evaluation, not a fit, so it cannot be "
            "a convergence problem — check the design/artifact column map and "
            "the linear predictor. Nothing lands.")
    if status == "PROBE_INCOMPLETE":
        raise SystemExit(
            f"PROBE_INCOMPLETE — {action} Re-run without --limit and with the "
            f"{PRIMARY_LEG} leg to adjudicate.")
    if status != "OK":
        raise SystemExit("GATE_FAILURE — nothing lands in the manuscript.")


if __name__ == "__main__":
    sys.exit(main())
