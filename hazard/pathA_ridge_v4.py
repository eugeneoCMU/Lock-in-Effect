#!/usr/bin/env python3
"""
pathA_ridge_v4.py — the three committed Path A ridge-device checks, recomputed
at spec v4 (round-28 WP-C6(i); R1: App. app:ridge's verification artifacts were
"not recomputed at adoption", tex 980 / 983 / 1003 / 1051).

PRE-COMMITTED SPEC (fixed BEFORE any run; drafting spec at
specs/SPEC_round28_C1_C2_C3_C6.md SPEC C6(i); gates, tolerances, expectations
and landing branches adopted unchanged except where LABELED below).

DESTRUCTIVE-RUN HAZARD (spec C6.0, honored here). bootstrap_se.py and
ridge_reference_weighting.py are IMPORTED for their functions and are NEVER
invoked as __main__. hazard/data/hazard_bootstrap_draws.csv,
hazard_bootstrap_se.json, ridge_reference_weighting.json,
hazard_coefficients.json, hazard_coefficients_specv3.json and
pathA_v4_holdout_results.json are FROZEN. Everything this script writes goes to
ONE new path: data/pathA_ridge_v4_results.json.

ENGINE. ridge_reference_weighting.load_split is reused verbatim (import).
fit_full / holdout_rmse are REIMPLEMENTED here with (a) a `seasonal` flag that
inserts hazard_fit._month_dummy_matrix BETWEEN the macro block and the FE block
— the exact position bootstrap_se.fit_betas uses (bootstrap_se.py:117-126), so
the macro coefficients stay at params[1+k : 4+k] — and (b) a `convention` flag
for the gap/friction standardization (see DEVIATION 1). _month_dummy_matrix is
used rather than pd.get_dummies(period.dt.month) because its columns are fixed
at m_2..m_12 "regardless of which months appear in the sample"
(hazard_fit.py:36-43), which matters once the zero-event-drop variant removes
423 cells. Every seasonal fit is warm-started from
bootstrap_se.production_start_head (the Gate-B lesson in that function's
docstring, bootstrap_se.py:170-174).

LABELED DEVIATIONS from the drafted spec (all forced by the code; none silent):

  1. STANDARDIZATION CONVENTION — the spec's P2 ("the v4 production refit
     reproduces hazard_coefficients.json macro coefficients to 1e-9,
     warm-started") is NOT achievable through the fit_betas design, and the
     reason is structural, not numerical. Production spec v4 was NOT produced
     by fit_hazard_glm/fit_betas: pathA_seasonal_adoption.py:116-123 pins it to
     seasonality_concave_gap.fit_with_month_dummies, whose standardizer is
     `z = lambda v: (v - v.mean()) / (v.std() or 1.0)` on a NUMPY array
     (seasonality_concave_gap.py:84) — ddof=0 — while fit_full/fit_betas/
     fit_hazard_glm use `float(train[col].std())` on a pandas Series — ddof=1
     (ridge_reference_weighting.py:70-71, bootstrap_se.py:107-110). The burnout
     block uses numpy ddof=0 in BOTH. So the ddof-1 rate-gap and friction
     coefficients exceed the ddof-0 ones by the factor sqrt(n/(n-1)) =
     1.0000491 at n = 10,176: ~3.2e-5 on rate_gap_bps (0.6469), i.e. four
     orders of magnitude outside the spec's 1e-9. The adoption runner's own
     docstring records the same fork from the other side (its first attempt
     FAILED Gate B when the design was re-assembled with "pandas ddof-1
     standardization", pathA_seasonal_adoption.py:11-21). This script therefore
     reports P2 THREE ways — spec-literal (ddof-1 refit vs the artifact, 1e-9,
     expected to fail by ~3e-5), ddof-adjusted, and P2b, the achievable anchor:
     fit_with_month_dummies replayed verbatim must reproduce the artifact to
     1e-9. P2b is the BLOCKING form. The v3-replay and v4 blocks are otherwise
     both computed under the ddof-1 convention, so the v3 -> v4 comparison the
     spec asks for is within-convention and isolates the seasonal design.
  2. P3 (holdout RMSE) — the committed pathA_v4_holdout_results.json numbers
     come from scoring the FROZEN artifact (prediction only, no refit;
     pathA_v4_holdout.py:83-88), whereas C6(i)'s v4 holdout leg is a REFIT.
     Under deviation 1 those cannot agree to 1e-6. P3a (blocking) replays the
     frozen scoring through pathA_v4_holdout.score_frozen; P3b records the
     refit-vs-frozen gap as a diagnostic, non-blocking.
  3. G0a/G0b are additional internal gates, not in the spec: G0a asserts the
     reimplemented fit_full reproduces the imported one bit-for-bit at
     seasonal=False (this is what licenses reading any v4 difference as the
     seasonal design), G0b asserts the reimplementation at
     convention="ddof0", seasonal=True, cold reproduces fit_with_month_dummies.
     ridge_reference_weighting's mle_macro is a NESTED function (line 173) and
     cannot be imported; it is copied verbatim, and P1 is what proves the copy.

PARITY GATES (P1, P2b, P3a, P4 BLOCKING; on failure status=GATE_FAILURE, the
artifact is still written, exit 1, and NOTHING lands in the manuscript):
  P1  seasonal=False replay reproduces EVERY numeric/bool/string field of
      data/ridge_reference_weighting.json to 1e-12 ("note" strings are prose
      carried in the source and are skipped, counted, and listed).
  P2  v4 production refit vs hazard_coefficients.json macro coefficients:
      P2-literal (ddof-1 warm refit, 1e-9, expected FAIL — deviation 1),
      P2-ddof-adjusted (same, x sqrt(n/(n-1)) on gap/friction, 1e-6),
      P2b (fit_with_month_dummies replay, 1e-9, BLOCKING).
  P3  v4 holdout RMSEs vs pathA_v4_holdout_results.json .spec_v4
      (37.903228802264934 unweighted / 3.037942336998421 exposure-weighted):
      P3a frozen replay 1e-6 BLOCKING; P3b refit gap, diagnostic.
  P4  n_zero_event_strata == 20 and n_cells_dropped == 423 at v4 (the month
      dummies cannot change which strata have zero training events; asserted,
      not assumed).

PRE-COMMITTED EXPECTATION (R1's own: "survives ~unchanged"). Concretely: the
v4 drop-fit's macro coefficients reproduce the spec-v4 production values
(rate_gap_bps +0.6468566611612588, burnout_orth -0.17126111626112517, friction
-0.007112288418868083; tex 981) to within 0.005 in standardized units — looser
than v3's 0.002 because the 11 month dummies absorb time variation the friction
coefficient formerly carried (tex 981 says exactly that). Reference-invariance
of the unpenalized drop-fit holds to 1e-12 (algebra, not luck). Grid identity
holds to ~1e-16 (committed v3: 4.5102810375396984e-17).

LANDING RULE (ex ante; ALL tex landings queue for Eugene; Path A is excluded
from every headline figure — tex 290, 978, 1053 — so NOTHING propagates under
any branch):
  (i-a) SURVIVES — all three facts inside tolerance: "not recomputed at
        adoption" is deleted at its 4 occurrences (tex 980, 983, 1003, 1051)
        and replaced with "recomputed under spec v4 (run pathA_ridge_v4); the
        device is unchanged"; tex 1051's parenthetical becomes affirmative; the
        v4 numbers print beside the v3 ones in App. app:ridge.
  (i-b) MOVES — drop-fit macro moves > 0.005, or v4 reference-invariance fails:
        the concession STRENGTHENS. tex 980 gains "...at spec v3; at spec v4
        the same check moves the rate-gap coefficient by X.XXX, and the
        production point's independence of the device is established only at
        the prior specification."                        [posture] disclosure
        widening, not a number move.
  (i-c) GRID_IDENTITY_FAILS — the two grid alphas return materially different
        vectors at v4: the "numerical no-op" claim (tex 980, 1051) is
        spec-v3-only and must be scoped. Report; land the scoped version.
                                                                    [posture]
  Verdict precedence: GRID_IDENTITY_FAILS > MOVES > SURVIVES.

MUST NOT CHANGE (spec C6.7): hazard/bootstrap_se.py,
hazard/bootstrap_resimulate.py, hazard/ridge_reference_weighting.py,
hazard/pathA_seasonal_adoption.py, hazard/pathA_v4_holdout.py,
hazard/seasonality_concave_gap.py, hazard/config.py (RIDGE_ALPHA,
RIDGE_ALPHA_GRID, AGE_SPLINE_KNOTS, HOLDOUT_DATE) and every committed artifact.
Path A's $928.9B / 121.5% and its exclusion from every headline figure. No Path
A result may enter any headline number under any branch.

Run:  cd hazard && python3 pathA_ridge_v4.py
      -> data/pathA_ridge_v4_results.json
~13 GLM fits on 10,176 cells x ~318 columns.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import pathA_v4_holdout as v4h
import ridge_reference_weighting as rrw
from bootstrap_se import BETA_NAMES, fit_betas, production_start_head
from config import AGE_SPLINE_KNOTS, HAZARD_COEF_PATH, RIDGE_ALPHA_GRID
from hazard_fit import (
    _age_spline_basis,
    _burnout_orthogonalized,
    _fit_poisson_glm,
    _month_dummy_matrix,
    _orthogonalize_burnout,
    _stratum_dummy_matrix,
)
from ridge_reference_weighting import PROD_ALPHA, REF_SENTINEL, load_split
from seasonality_concave_gap import fit_with_month_dummies

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "pathA_ridge_v4_results.json"      # NEW path
COMMITTED_RIDGE = DATA_DIR / "ridge_reference_weighting.json"  # frozen, read-only
V4_HOLDOUT_ARTIFACT = DATA_DIR / "pathA_v4_holdout_results.json"  # frozen

TOL_P1 = 1e-12
TOL_P2 = 1e-9
TOL_P2_DDOF = 1e-6
TOL_P3 = 1e-6
TOL_G0 = 1e-12

DROPFIT_TOL_V4 = 0.005          # spec C6(i), looser than v3's 0.002
REF_INVARIANCE_TOL = 1e-12      # algebraic property of the unpenalized fit
GRID_IDENTITY_TOL = 1e-10       # committed v3 value is 4.51e-17

# spec-v4 production macro coefficients (data/hazard_coefficients.json, tex 981)
PROD_V4 = {
    "rate_gap_bps": 0.6468566611612588,
    "burnout_orth": -0.17126111626112517,
    "friction": -0.007112288418868083,
}
# committed spec-v4 holdout RMSEs (pathA_v4_holdout_results.json .spec_v4)
V4_RMSE_UNW = 37.903228802264934
V4_RMSE_EXPW = 3.037942336998421

N_ZERO_EVENT_STRATA = 20
N_CELLS_DROPPED = 423

MACRO_KEYS = ["rate_gap_bps", "burnout_orth", "friction"]


# --------------------------------------------------------------------------
# reimplemented engine (fit_full / holdout_rmse + seasonal + convention)
# --------------------------------------------------------------------------
def _moments(series: pd.Series, convention: str) -> tuple[float, float]:
    """Standardization moments.

    'ddof1' — pandas Series .mean()/.std(): the convention of
    ridge_reference_weighting.fit_full (lines 70-71), bootstrap_se.fit_betas
    (lines 107-110) and hazard_fit.fit_hazard_glm (lines 293-296); this is the
    spec-v3 production convention.
    'ddof0' — numpy .mean()/.std() on the extracted array: the convention of
    seasonality_concave_gap.fit_with_month_dummies (line 84), which DEFINES
    spec-v4 production (pathA_seasonal_adoption.py:116-123).
    """
    arr = series.to_numpy(dtype=np.float64)
    if convention == "ddof0":
        return float(arr.mean()), (float(arr.std()) or 1.0)
    if convention == "ddof1":
        return float(series.mean()), (float(series.std()) or 1.0)
    raise ValueError(f"unknown convention {convention!r}")


def fit_full_v(train: pd.DataFrame, alpha: float, seasonal: bool = False,
               convention: str = "ddof1",
               start_head: np.ndarray | None = None) -> dict:
    """ridge_reference_weighting.fit_full + seasonal flag + convention flag.

    Column order: const | age spline (k) | gap, burn, fric | months (11, only
    when seasonal) | stratum FE — the bootstrap_se.fit_betas order
    (bootstrap_se.py:117-126), so macro stays at params[1+k : 4+k].
    """
    reference = sorted(train["stratum_id"].unique())[0]
    dummies = pd.get_dummies(train["stratum_id"], prefix="fe_stratum",
                             drop_first=True)
    fe_columns = list(dummies.columns)
    age_basis = _age_spline_basis(train["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean = (train.groupby("stratum_id")["burnout"]
                   .transform(lambda s: s - s.mean()).to_numpy())
    stratum_burnout_mean = train.groupby("stratum_id")["burnout"].mean().to_dict()
    burnout_orth, burnout_age_adj = _orthogonalize_burnout(age_basis, burn_demean)
    fm, fs = _moments(train["friction"], convention)
    gm, gs = _moments(train["rate_gap_bps"], convention)
    bs = float(burnout_orth.std()) or 1.0          # numpy ddof=0 in BOTH sources

    blocks = [
        age_basis,
        (train["rate_gap_bps"].to_numpy() - gm) / gs,
        burnout_orth / bs,
        (train["friction"].to_numpy() - fm) / fs,
    ]
    if seasonal:
        blocks.append(_month_dummy_matrix(train["period"]))
    blocks.append(dummies.to_numpy(dtype=np.float64))
    X = np.column_stack(blocks)
    X = sm.add_constant(X, has_constant="add")

    y_events = train["events"].to_numpy()
    offset = np.log(train["exposure"].to_numpy())

    if start_head is None:
        result, method = _fit_poisson_glm(X, y_events, offset, alpha)
    else:
        # bootstrap_se.fit_betas' warm branch, verbatim (lines 135-149)
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
            method="elastic_net", alpha=alpha, L1_wt=0.0,
            maxiter=100, start_params=warm,
        )
        method = f"ridge(alpha={alpha}, warm_start)"

    params = np.asarray(result.params, dtype=np.float64).ravel()
    k = age_basis.shape[1]
    return {
        "result": result, "method": method, "reference": reference,
        "fe_columns": fe_columns, "burnout_age_adj": burnout_age_adj,
        "stratum_burnout_mean": stratum_burnout_mean,
        "fm": fm, "fs": fs, "gm": gm, "gs": gs, "bs": bs,
        "k_age": k, "seasonal": bool(seasonal), "convention": convention,
        "params": params,
        "macro": {n: float(params[1 + k + i]) for i, n in enumerate(MACRO_KEYS)},
    }


def holdout_rmse_v(holdout: pd.DataFrame, fit: dict) -> dict:
    """ridge_reference_weighting.holdout_rmse + the month block, inserted at
    the same position hazard_fit._holdout_metrics uses (lines 217-226)."""
    age_h = _age_spline_basis(holdout["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    burn_demean_h = holdout["burnout"].to_numpy() - holdout["stratum_id"].map(
        fit["stratum_burnout_mean"]).fillna(0).to_numpy()
    burn_h = _burnout_orthogonalized(burn_demean_h, age_h, fit["burnout_age_adj"])
    stratum_h = _stratum_dummy_matrix(holdout["stratum_id"], fit["reference"],
                                      fit["fe_columns"])
    blocks = [
        age_h,
        (holdout["rate_gap_bps"].to_numpy() - fit["gm"]) / fit["gs"],
        burn_h / fit["bs"],
        (holdout["friction"].to_numpy() - fit["fm"]) / fit["fs"],
    ]
    if fit["seasonal"]:
        blocks.append(_month_dummy_matrix(holdout["period"]))
    blocks.append(stratum_h)
    X_h = np.column_stack(blocks)
    X_h = np.asarray(sm.add_constant(X_h, has_constant="add"), dtype=np.float64)
    params = np.asarray(fit["result"].params, dtype=np.float64).ravel()
    pred_cpr = np.exp(np.clip(X_h.dot(params), -20, 0)) * 12 * 100
    obs_cpr = holdout["prepay_rate"].to_numpy() * 12 * 100
    w = holdout["exposure"].to_numpy(dtype=float)
    sq = (obs_cpr - pred_cpr) ** 2
    return {
        "rmse_unweighted_pp": float(np.sqrt(sq.mean())),
        "rmse_exposure_weighted_pp": float(np.sqrt((w * sq).sum() / w.sum())),
    }


def mle_macro_v3(tr: pd.DataFrame) -> dict:
    """COPIED VERBATIM from ridge_reference_weighting.main's nested mle_macro
    (lines 173-195) — nested, therefore not importable. P1 proves the copy."""
    dummies = pd.get_dummies(tr["stratum_id"], prefix="fe", drop_first=True)
    age = _age_spline_basis(tr["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    bd = (tr.groupby("stratum_id")["burnout"]
          .transform(lambda s: s - s.mean()).to_numpy())
    bo, _ = _orthogonalize_burnout(age, bd)
    X = np.column_stack([
        age,
        (tr["rate_gap_bps"] - tr["rate_gap_bps"].mean()) / tr["rate_gap_bps"].std(),
        bo / bo.std(),
        (tr["friction"] - tr["friction"].mean()) / tr["friction"].std(),
        dummies.to_numpy(float),
    ])
    X = sm.add_constant(X, has_constant="add")
    ka = age.shape[1]
    m = sm.GLM(tr["events"].to_numpy(), X, family=sm.families.Poisson(),
               offset=np.log(tr["exposure"].to_numpy()))
    r = m.fit(maxiter=300)
    p = np.asarray(r.params)
    return {"converged": bool(r.converged),
            "rate_gap_bps": float(p[1 + ka]),
            "burnout_orth": float(p[2 + ka]),
            "friction": float(p[3 + ka])}


def mle_macro_v4(tr: pd.DataFrame, start_head: np.ndarray | None) -> dict:
    """mle_macro_v3 + the 11-column month block between macro and FE.
    Unpenalized Poisson PML; warm-started from the production head (spec:
    'warm-start every seasonal fit')."""
    dummies = pd.get_dummies(tr["stratum_id"], prefix="fe", drop_first=True)
    age = _age_spline_basis(tr["loan_age"].to_numpy(), AGE_SPLINE_KNOTS)
    bd = (tr.groupby("stratum_id")["burnout"]
          .transform(lambda s: s - s.mean()).to_numpy())
    bo, _ = _orthogonalize_burnout(age, bd)
    X = np.column_stack([
        age,
        (tr["rate_gap_bps"] - tr["rate_gap_bps"].mean()) / tr["rate_gap_bps"].std(),
        bo / bo.std(),
        (tr["friction"] - tr["friction"].mean()) / tr["friction"].std(),
        _month_dummy_matrix(tr["period"]),
        dummies.to_numpy(float),
    ])
    X = sm.add_constant(X, has_constant="add")
    ka = age.shape[1]
    m = sm.GLM(tr["events"].to_numpy(), X, family=sm.families.Poisson(),
               offset=np.log(tr["exposure"].to_numpy()))
    if start_head is None:
        r = m.fit(maxiter=300)
    else:
        start = np.zeros(X.shape[1])
        start[: len(start_head)] = start_head
        r = m.fit(maxiter=300, start_params=start)
    p = np.asarray(r.params)
    return {"converged": bool(getattr(r, "converged", True)),
            "rate_gap_bps": float(p[1 + ka]),
            "burnout_orth": float(p[2 + ka]),
            "friction": float(p[3 + ka])}


# --------------------------------------------------------------------------
# P1 comparator
# --------------------------------------------------------------------------
def compare_to_committed(got, want, tol: float, path: str = "",
                         diffs: list | None = None,
                         skipped: list | None = None,
                         n_cmp: list | None = None):
    """Walk the COMMITTED structure; every leaf must be reproduced. 'note'
    leaves are source prose, recorded as skipped rather than compared."""
    diffs = [] if diffs is None else diffs
    skipped = [] if skipped is None else skipped
    n_cmp = [0] if n_cmp is None else n_cmp
    if isinstance(want, dict):
        for k, v in want.items():
            p = f"{path}.{k}" if path else k
            if k == "note":
                skipped.append(p)
                continue
            if not isinstance(got, dict) or k not in got:
                diffs.append({"field": p, "kind": "MISSING_IN_REPLAY"})
                continue
            compare_to_committed(got[k], v, tol, p, diffs, skipped, n_cmp)
    elif isinstance(want, bool):
        n_cmp[0] += 1
        if bool(got) != bool(want):
            diffs.append({"field": path, "kind": "BOOL",
                          "got": bool(got), "want": bool(want)})
    elif isinstance(want, (int, float)):
        n_cmp[0] += 1
        d = abs(float(got) - float(want))
        if not (d <= tol):
            diffs.append({"field": path, "kind": "NUM", "got": float(got),
                          "want": float(want), "abs_diff": d, "tol": tol})
    elif isinstance(want, str):
        n_cmp[0] += 1
        if str(got) != want:
            diffs.append({"field": path, "kind": "STR",
                          "got": str(got), "want": want})
    else:
        skipped.append(path)
    return diffs, skipped, n_cmp[0]


def _np(o):
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(f"not serializable: {type(o)}")


# --------------------------------------------------------------------------
def main() -> None:
    t0 = time.perf_counter()
    committed = json.loads(COMMITTED_RIDGE.read_text())
    prod = json.loads(Path(HAZARD_COEF_PATH).read_text())
    assert int(prod.get("spec_version", -1)) == 4, "production artifact is not spec v4"
    assert "month_effects" in prod, "production artifact has no month_effects"
    head_v4 = production_start_head(prod)          # 22 entries at v4
    assert len(head_v4) == 22, f"head length {len(head_v4)} != 22"

    print("Loading split (ridge_reference_weighting.load_split, verbatim) …")
    train, holdout = load_split()
    n_train, n_strata = int(len(train)), int(train["stratum_id"].nunique())
    print(f"  train {n_train:,} cells / {n_strata} strata | holdout {len(holdout):,}")

    gates: dict = {}

    # ---------------- spec v3 replay (P1) ---------------------------------
    print("\nspec v3 replay (imported fit_full / holdout_rmse / fit_betas) …")
    v3: dict = {"units": "annualized stratum-month CPR, percentage points"}
    grid3 = {}
    fits3 = {}
    for alpha in RIDGE_ALPHA_GRID:
        f = rrw.fit_full(train, alpha)
        fits3[alpha] = f
        grid3[f"alpha_{alpha:g}"] = rrw.holdout_rmse(holdout, f)
        print(f"  alpha={alpha:g} {grid3[f'alpha_{alpha:g}']}")
    ranks_unw = sorted(grid3, key=lambda k: grid3[k]["rmse_unweighted_pp"])
    ranks_w = sorted(grid3, key=lambda k: grid3[k]["rmse_exposure_weighted_pp"])
    v3["holdout_rmse_grid"] = grid3
    v3["alpha_ranking_invariant_to_weighting"] = bool(ranks_unw == ranks_w)
    v3["selected_alpha_unweighted"] = ranks_unw[0]
    v3["selected_alpha_weighted"] = ranks_w[0]

    base3 = fit_betas(train, PROD_ALPHA)
    last = sorted(train["stratum_id"].unique())[-1]
    swapped = train.copy()
    swapped.loc[swapped["stratum_id"] == last, "stratum_id"] = REF_SENTINEL + last
    alt3 = fit_betas(swapped, PROD_ALPHA)
    deltas3 = {n: float(alt3[n] - base3[n]) for n in BETA_NAMES}
    v3["reference_swap"] = {
        "production_reference": sorted(train["stratum_id"].unique())[0],
        "swapped_reference": last,
        "betas_production_ref": {n: base3[n] for n in BETA_NAMES},
        "betas_swapped_ref": {n: alt3[n] for n in BETA_NAMES},
        "deltas": deltas3,
        "max_abs_delta": float(max(abs(v) for v in deltas3.values())),
    }
    v3["grid_fit_identity"] = {
        "max_abs_param_diff": float(np.abs(
            np.asarray(fits3[1e-5]["result"].params)
            - np.asarray(fits3[1e-4]["result"].params)).max())
    }

    ev = train.groupby("stratum_id")["events"].sum()
    zero_ids = set(ev[ev == 0].index)
    est = train[~train["stratum_id"].isin(zero_ids)].copy()
    n_zero, n_dropped = len(zero_ids), int(train["stratum_id"].isin(zero_ids).sum())
    m1 = mle_macro_v3(est)
    sw2 = est.copy()
    last2 = sorted(sw2["stratum_id"].unique())[-1]
    sw2.loc[sw2["stratum_id"] == last2, "stratum_id"] = REF_SENTINEL + last2
    m2 = mle_macro_v3(sw2)
    v3["estimable_strata_mle"] = {
        "n_zero_event_strata": n_zero,
        "n_cells_dropped": n_dropped,
        "betas_production_ref": m1,
        "betas_swapped_ref": m2,
        "max_abs_delta": float(max(abs(m1[k] - m2[k]) for k in MACRO_KEYS)),
    }

    diffs, skipped, n_cmp = compare_to_committed(v3, committed, TOL_P1)
    gates["P1_specv3_replay"] = {
        "tol": TOL_P1, "n_fields_compared": n_cmp,
        "n_note_strings_skipped": len(skipped), "notes_skipped": skipped,
        "diffs": diffs, "pass": bool(not diffs),
    }
    print(f"  P1: {n_cmp} fields at {TOL_P1:g} — "
          f"{'PASS' if not diffs else f'FAIL ({len(diffs)} diffs)'}")

    # ---------------- G0: reimplementation fidelity -----------------------
    print("\nG0 reimplementation fidelity …")
    g0a = {}
    for alpha in RIDGE_ALPHA_GRID:
        mine = fit_full_v(train, alpha, seasonal=False, convention="ddof1")
        d = float(np.abs(mine["params"]
                         - np.asarray(fits3[alpha]["result"].params,
                                      dtype=np.float64).ravel()).max())
        g0a[f"alpha_{alpha:g}"] = {"max_abs_param_diff": d,
                                   "pass": bool(d <= TOL_G0)}
    gates["G0a_fit_full_reimpl"] = {"tol": TOL_G0, "checks": g0a,
                                    "pass": all(c["pass"] for c in g0a.values())}

    # G0b compares against fit_with_month_dummies, which builds its month block
    # with pd.get_dummies(period.dt.month, drop_first=True). That agrees with
    # _month_dummy_matrix only when all 12 calendar months appear in the
    # training window; assert it rather than assume it.
    months_present = sorted(pd.to_datetime(train["period"]).dt.month.unique())
    assert months_present == list(range(1, 13)), (
        f"training window does not span all 12 months: {months_present} — "
        "_month_dummy_matrix and fit_with_month_dummies would disagree")
    coefs_prodconstr, months_prodconstr, method_prodconstr = fit_with_month_dummies(
        train, PROD_ALPHA)
    mine_dd0 = fit_full_v(train, PROD_ALPHA, seasonal=True, convention="ddof0")
    d0 = max(abs(mine_dd0["macro"][n] - float(coefs_prodconstr[n]))
             for n in MACRO_KEYS)
    gates["G0b_prod_construction_reimpl"] = {
        "tol": TOL_G0, "max_abs_macro_diff": float(d0),
        "fit_method_reimpl": mine_dd0["method"],
        "fit_method_source": method_prodconstr,
        "pass": bool(d0 <= TOL_G0),
    }
    print(f"  G0a {'PASS' if gates['G0a_fit_full_reimpl']['pass'] else 'FAIL'} | "
          f"G0b max|Δmacro| {d0:.3g} "
          f"{'PASS' if gates['G0b_prod_construction_reimpl']['pass'] else 'FAIL'}")

    # ---------------- P2: production anchors ------------------------------
    n_fac = float(np.sqrt(n_train / (n_train - 1.0)))   # ddof1 / ddof0
    fit4_prod = fit_full_v(train, PROD_ALPHA, seasonal=True, convention="ddof1",
                           start_head=head_v4)
    p2_lit = {n: {"got": fit4_prod["macro"][n], "want": PROD_V4[n],
                  "abs_diff": abs(fit4_prod["macro"][n] - PROD_V4[n])}
              for n in MACRO_KEYS}
    for n in MACRO_KEYS:
        p2_lit[n]["pass"] = bool(p2_lit[n]["abs_diff"] <= TOL_P2)
    gates["P2_literal_ddof1_refit"] = {
        "tol": TOL_P2, "checks": p2_lit,
        "pass": all(c["pass"] for c in p2_lit.values()),
        "blocking": False,
        "note": ("DEVIATION 1: expected to FAIL by ~3e-5 on rate_gap_bps — the "
                 "ddof-1 refit and the ddof-0 production construction differ by "
                 "sqrt(n/(n-1)) on the gap and friction blocks. Recorded, not "
                 "blocking; P2b is the blocking anchor."),
    }
    p2_adj = {}
    for n in MACRO_KEYS:
        want = PROD_V4[n] * (n_fac if n != "burnout_orth" else 1.0)
        d = abs(fit4_prod["macro"][n] - want)
        p2_adj[n] = {"got": fit4_prod["macro"][n], "want_ddof_adjusted": want,
                     "abs_diff": d, "pass": bool(d <= TOL_P2_DDOF)}
    gates["P2_ddof_adjusted"] = {
        "tol": TOL_P2_DDOF, "ddof_factor": n_fac, "checks": p2_adj,
        "pass": all(c["pass"] for c in p2_adj.values()), "blocking": False,
    }
    p2b = {n: {"got": float(coefs_prodconstr[n]), "want": PROD_V4[n],
               "abs_diff": abs(float(coefs_prodconstr[n]) - PROD_V4[n])}
           for n in MACRO_KEYS}
    for n in MACRO_KEYS:
        p2b[n]["pass"] = bool(p2b[n]["abs_diff"] <= TOL_P2)
    month_drift = max(
        abs(float(months_prodconstr[m]) - float(prod["month_effects"][str(m)]))
        for m in range(1, 13))
    gates["P2b_production_construction"] = {
        "tol": TOL_P2, "checks": p2b, "month_effects_max_abs_drift": month_drift,
        "pass": bool(all(c["pass"] for c in p2b.values())
                     and month_drift <= TOL_P2),
        "blocking": True,
        "note": ("seasonality_concave_gap.fit_with_month_dummies replayed "
                 "verbatim — the construction pathA_seasonal_adoption pinned "
                 "production spec v4 to."),
    }
    print(f"\n  P2b (production construction) "
          f"{'PASS' if gates['P2b_production_construction']['pass'] else 'FAIL'}"
          f" | P2-literal ddof1 max|Δ| "
          f"{max(c['abs_diff'] for c in p2_lit.values()):.3g}")

    # ---------------- v4 blocks (ddof-1, within-convention vs v3) ---------
    print("\nspec v4 blocks (warm-started, ddof-1 convention) …")
    v4: dict = {"units": "annualized stratum-month CPR, percentage points",
                "convention": "ddof1 (fit_betas/fit_full); see DEVIATION 1"}
    grid4, fits4 = {}, {}
    for alpha in RIDGE_ALPHA_GRID:
        f = (fit4_prod if alpha == PROD_ALPHA
             else fit_full_v(train, alpha, seasonal=True, convention="ddof1",
                             start_head=head_v4))
        fits4[alpha] = f
        grid4[f"alpha_{alpha:g}"] = holdout_rmse_v(holdout, f)
        print(f"  alpha={alpha:g} {grid4[f'alpha_{alpha:g}']}")
    r_unw = sorted(grid4, key=lambda k: grid4[k]["rmse_unweighted_pp"])
    r_w = sorted(grid4, key=lambda k: grid4[k]["rmse_exposure_weighted_pp"])
    v4["holdout_rmse_grid"] = grid4
    v4["alpha_ranking_invariant_to_weighting"] = bool(r_unw == r_w)
    v4["selected_alpha_unweighted"] = r_unw[0]
    v4["selected_alpha_weighted"] = r_w[0]

    swapped4 = train.copy()
    swapped4.loc[swapped4["stratum_id"] == last, "stratum_id"] = REF_SENTINEL + last
    alt4 = fit_full_v(swapped4, PROD_ALPHA, seasonal=True, convention="ddof1",
                      start_head=head_v4)
    deltas4 = {n: float(alt4["macro"][n] - fit4_prod["macro"][n])
               for n in MACRO_KEYS}
    v4["reference_swap"] = {
        "production_reference": sorted(train["stratum_id"].unique())[0],
        "swapped_reference": last,
        "betas_production_ref": dict(fit4_prod["macro"]),
        "betas_swapped_ref": dict(alt4["macro"]),
        "deltas": deltas4,
        "max_abs_delta": float(max(abs(v) for v in deltas4.values())),
        "committed_v3_max_abs_delta": 1.2892293326075137,
    }
    v4["grid_fit_identity"] = {
        "max_abs_param_diff": float(np.abs(
            fits4[1e-5]["params"] - fits4[1e-4]["params"]).max()),
        "committed_v3_max_abs_param_diff": 4.5102810375396984e-17,
    }

    ev4 = train.groupby("stratum_id")["events"].sum()
    zero4 = set(ev4[ev4 == 0].index)
    n_zero4 = len(zero4)
    n_dropped4 = int(train["stratum_id"].isin(zero4).sum())
    est4 = train[~train["stratum_id"].isin(zero4)].copy()
    d1 = mle_macro_v4(est4, head_v4)
    sw4 = est4.copy()
    last4 = sorted(sw4["stratum_id"].unique())[-1]
    sw4.loc[sw4["stratum_id"] == last4, "stratum_id"] = REF_SENTINEL + last4
    d2 = mle_macro_v4(sw4, head_v4)
    dropfit_gap = {n: abs(d1[n] - PROD_V4[n]) for n in MACRO_KEYS}
    dropfit_gap_ddof0 = {
        n: abs(d1[n] / (n_fac if n != "burnout_orth" else 1.0) - PROD_V4[n])
        for n in MACRO_KEYS}
    v4["estimable_strata_mle"] = {
        "n_zero_event_strata": n_zero4,
        "n_cells_dropped": n_dropped4,
        "betas_production_ref": d1,
        "betas_swapped_ref": d2,
        "max_abs_delta": float(max(abs(d1[k] - d2[k]) for k in MACRO_KEYS)),
        "gap_vs_production_v4": dropfit_gap,
        "gap_vs_production_v4_ddof0_adjusted": dropfit_gap_ddof0,
        "max_gap_vs_production_v4": float(max(dropfit_gap.values())),
        "max_gap_vs_production_v4_ddof0_adjusted": float(
            max(dropfit_gap_ddof0.values())),
        "tolerance": DROPFIT_TOL_V4,
        "committed_v3_gap_note": ("v3: rate_gap 0.6727292125124604 (drop-fit) "
                                  "vs 0.6733519352905115 (production), within "
                                  "0.002"),
    }

    gates["P4_zero_event_carryover"] = {
        "n_zero_event_strata": {"got": n_zero4, "want": N_ZERO_EVENT_STRATA},
        "n_cells_dropped": {"got": n_dropped4, "want": N_CELLS_DROPPED},
        "v3_leg": {"n_zero_event_strata": n_zero, "n_cells_dropped": n_dropped},
        "pass": bool(n_zero4 == N_ZERO_EVENT_STRATA
                     and n_dropped4 == N_CELLS_DROPPED
                     and n_zero == N_ZERO_EVENT_STRATA
                     and n_dropped == N_CELLS_DROPPED),
    }

    # ---------------- P3: holdout RMSE ------------------------------------
    try:
        frozen = v4h.score_frozen(holdout, Path(HAZARD_COEF_PATH))
        p3a = {
            "rmse_unweighted_pp": {"got": frozen["rmse_unweighted_pp"],
                                   "want": V4_RMSE_UNW},
            "rmse_exposure_weighted_pp": {
                "got": frozen["rmse_exposure_weighted_pp"],
                "want": V4_RMSE_EXPW},
        }
        for c in p3a.values():
            c["abs_diff"] = abs(c["got"] - c["want"])
            c["pass"] = bool(c["abs_diff"] <= TOL_P3)
        p3a_pass = all(c["pass"] for c in p3a.values())
    except Exception as exc:                    # noqa: BLE001 — gate, not crash
        p3a = {"error": repr(exc)[:300]}
        p3a_pass = False
    gates["P3a_frozen_v4_replay"] = {
        "tol": TOL_P3, "checks": p3a, "blocking": True, "pass": bool(p3a_pass),
        "note": ("pathA_v4_holdout.score_frozen on the frozen production "
                 "artifact — prediction only, the construction the committed "
                 "numbers came from."),
    }
    refit_rmse = grid4[f"alpha_{PROD_ALPHA:g}"]
    p3b = {
        "rmse_unweighted_pp": {"got": refit_rmse["rmse_unweighted_pp"],
                               "want": V4_RMSE_UNW},
        "rmse_exposure_weighted_pp": {
            "got": refit_rmse["rmse_exposure_weighted_pp"],
            "want": V4_RMSE_EXPW},
    }
    for c in p3b.values():
        c["abs_diff"] = abs(c["got"] - c["want"])
        c["pass"] = bool(c["abs_diff"] <= TOL_P3)
    gates["P3b_v4_refit_vs_frozen"] = {
        "tol": TOL_P3, "checks": p3b, "blocking": False,
        "pass": all(c["pass"] for c in p3b.values()),
        "note": ("DEVIATION 2: a REFIT compared against a FROZEN-artifact "
                 "score. Diagnostic only."),
    }

    # ---------------- verdict ---------------------------------------------
    grid_ok = v4["grid_fit_identity"]["max_abs_param_diff"] <= GRID_IDENTITY_TOL
    refinv_ok = v4["estimable_strata_mle"]["max_abs_delta"] <= REF_INVARIANCE_TOL
    drop_ok = (v4["estimable_strata_mle"]["max_gap_vs_production_v4_ddof0_adjusted"]
               <= DROPFIT_TOL_V4)
    if not grid_ok:
        code, action = "GRID_IDENTITY_FAILS", (
            "(i-c) scope the 'numerical no-op' claim (tex 980, 1051) to spec "
            "v3; report; land the scoped version. [posture]")
    elif not (drop_ok and refinv_ok):
        code, action = "MOVES", (
            "(i-b) the concession STRENGTHENS: tex 980 gains the spec-v4 "
            "movement and 'independence of the device is established only at "
            "the prior specification'. Path A is excluded from every headline "
            "figure — nothing propagates. [posture]")
    else:
        code, action = "SURVIVES", (
            "(i-a) delete 'not recomputed at adoption' at tex 980, 983, 1003, "
            "1051; replace with 'recomputed under spec v4 (run "
            "pathA_ridge_v4); the device is unchanged'; tex 1051's "
            "parenthetical becomes affirmative; print the v4 numbers beside "
            "the v3 ones in App. app:ridge.")

    blocking = ["P1_specv3_replay", "P2b_production_construction",
                "P3a_frozen_v4_replay", "P4_zero_event_carryover",
                "G0a_fit_full_reimpl", "G0b_prod_construction_reimpl"]
    all_pass = all(bool(gates[g]["pass"]) for g in blocking)
    status = "OK" if all_pass else "GATE_FAILURE"

    payload = {
        "mode": "pathA_ridge_v4",
        "status": status,
        "spec": ("SPEC_round28_C1_C2_C3_C6.md C6(i): grid identity, "
                 "reference-stratum swap and zero-event drop-fit recomputed "
                 "under the spec v4 seasonal design; month block via "
                 "hazard_fit._month_dummy_matrix between macro and FE; every "
                 "seasonal fit warm-started from "
                 "bootstrap_se.production_start_head."),
        "labeled_deviations": [
            "1: standardization convention — spec v4 production is ddof-0 "
            "(seasonality_concave_gap.fit_with_month_dummies), the fit_betas "
            "engine is ddof-1; P2 reported literal / ddof-adjusted / P2b, and "
            "P2b is the blocking anchor.",
            "2: P3 — committed v4 RMSEs are a FROZEN-artifact score, C6(i)'s "
            "v4 holdout leg is a refit; P3a (frozen replay) blocks, P3b "
            "(refit gap) is diagnostic.",
            "3: G0a/G0b added — reimplementation fidelity against the imported "
            "fit_full and against fit_with_month_dummies; mle_macro copied "
            "verbatim because it is nested and unimportable.",
        ],
        "panel": {"n_train": n_train, "n_strata": n_strata,
                  "n_holdout": int(len(holdout)),
                  "ddof_factor_sqrt_n_over_nm1": n_fac},
        "parity_gates": gates,
        "parity_gates_all_pass": all_pass,
        "spec_v3_replay": v3,
        "spec_v4": v4,
        "production_construction_replay": {
            "macro": {n: float(coefs_prodconstr[n]) for n in MACRO_KEYS},
            "month_effects": {str(m): float(v)
                              for m, v in sorted(months_prodconstr.items())},
            "fit_method": method_prodconstr,
        },
        "facts_vs_committed_v3": {
            "grid_identity_v3": committed["grid_fit_identity"]["max_abs_param_diff"],
            "grid_identity_v4": v4["grid_fit_identity"]["max_abs_param_diff"],
            "reference_swap_max_abs_delta_v3":
                committed["reference_swap"]["max_abs_delta"],
            "reference_swap_max_abs_delta_v4":
                v4["reference_swap"]["max_abs_delta"],
            "dropfit_reference_invariance_v3":
                committed["estimable_strata_mle"]["max_abs_delta"],
            "dropfit_reference_invariance_v4":
                v4["estimable_strata_mle"]["max_abs_delta"],
        },
        "verdict": {
            "code": code,
            "grid_identity_holds": bool(grid_ok),
            "reference_invariance_holds": bool(refinv_ok),
            "dropfit_within_tolerance": bool(drop_ok),
            "tolerances": {"dropfit": DROPFIT_TOL_V4,
                           "reference_invariance": REF_INVARIANCE_TOL,
                           "grid_identity": GRID_IDENTITY_TOL},
            "manuscript_action": action,
            "propagation": ("none — Path A is excluded from every headline "
                            "figure (tex 290, 978, 1053)"),
        },
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_np)
        f.write("\n")

    print("\n" + "=" * 66)
    print(f" pathA_ridge_v4 — status {status} — verdict {code}")
    print("=" * 66)
    print(f"  grid identity v4 {v4['grid_fit_identity']['max_abs_param_diff']:.3g} "
          f"(v3 {committed['grid_fit_identity']['max_abs_param_diff']:.3g})")
    print(f"  reference swap  v4 max|Δ| {v4['reference_swap']['max_abs_delta']:.4f} "
          f"(v3 {committed['reference_swap']['max_abs_delta']:.4f})")
    print(f"  drop-fit v4 max gap vs production "
          f"{v4['estimable_strata_mle']['max_gap_vs_production_v4_ddof0_adjusted']:.5f}"
          f" (tol {DROPFIT_TOL_V4})")
    print(f"  Saved: {RESULTS_JSON}")
    if status != "OK":
        raise SystemExit("GATE_FAILURE — nothing lands in the manuscript.")


if __name__ == "__main__":
    sys.exit(main())
