#!/usr/bin/env python3
"""
patha_sign_test.py — bias-respecting significance test for the Path A
rate-gap sign claim (referee round 21, finding MF-5 CONFIRMED).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention
of oos_identification.py / floor_form_offwindow.py / floor_form_test.py).

Referee objection (MF-5). The manuscript's Path A sign claim rests on the
bootstrap sign-share ("positive in 197 of 198 converged replications",
Section V.A / Table tab:bootstrap) — percentile-interval logic the manuscript
itself disclaims: both replicate distributions are heavily right-skewed with
estimated upward bias (+0.82 stratum-cluster scheme, +2.64 temporal
moving-block scheme), and the bias-reflecting basic 95% intervals include
zero under both schemes ([-2.76, +0.74] and [-10.84, +0.91]). A sign claim
needs a test of H0: beta_g <= 0 that respects the diagnosed bias. Table 6's
own note defers exactly this: "A BCa correction would require a 296-refit
jackknife for the acceleration constant and is left to the replication
package" (revised_paper_v18.tex:422). This script is that deliverable, plus
an independent permutation complement.

=======================================================================
STEP 0 — PINNED INPUTS (all consumed read-only; nothing committed is touched)
=======================================================================
SPEC-DRIFT WARNING (do not "fix" by pointing at HAZARD_COEF_PATH): the
production artifact at HEAD (hazard_coefficients.json) is spec v4
(seasonal); every committed Table-6 inferential object is spec v3. This
script pins:
  - hazard_coefficients_specv3.json      (spec-v3 fit; ridge_alpha 1e-4;
                                          n_train 10,176; n_strata 296)
  - hazard_bootstrap_se.json             (stratum-cluster scheme summary)
  - hazard_bootstrap_draws.csv           (198 converged stratum draws,
                                          production standardized units)
  - temporal_block_bootstrap.json        (temporal moving-block, length 6)
  - temporal_block_bootstrap_draws.csv   (196 converged temporal draws)
  - cohort_month_panel.parquet via temporal_block_bootstrap.load_train()
    (panel -> enrich_panel_with_macro -> dropna -> exposure>0 ->
     period < HOLDOUT_DATE 2024-01-01; training Jan 2021 - Dec 2023,
     36 months). Macro joins are live FRED series; parity gate G2 exists
    precisely to catch macro-vintage drift.
Refit machinery: bootstrap_se.fit_betas (spec-v3 design when seasonal=False:
age spline + standardized macro block + stratum FE, Poisson log link,
log-exposure offset, ridge alpha FIXED at 1e-4, warm-started IRLS via
start_head; per-sample standardization rescaled to production units by
bootstrap_se.rescale_to_production_units). NOTHING is refactored: the same
functions the committed bootstrap runs used (bootstrap_se.py:76-167,
temporal_block_bootstrap.py:44-49) are imported and called.

Observed statistic (production standardized units, from the spec-v3
artifact, unrounded):
    beta_g  = +0.6733519352905115   (manuscript +0.673)
    beta_b  = -0.13009048732147674  (manuscript -0.130)
    beta_f  = -0.037066025306261775 (manuscript -0.037)

=======================================================================
STEP 1 — PARITY GATES (run first; BLOCKING — on any FAIL the script writes
the gate report and exits; nothing downstream may be cited)
=======================================================================
G1  artifact vs manuscript point: spec-v3 rate gap +0.673 / burnout -0.130 /
    friction -0.037, each to +/-0.001 (unrounded values above to 1e-9
    against the artifact — wrong-artifact detector).
G2  fresh cold refit of spec v3 on the reconstructed training frame
    reproduces all three artifact betas to +/-0.001 (the committed point
    refit reproduced them to four decimals; a FAIL means environment or
    macro-vintage drift — STOP, report, do not build on it).
G2b warm-start idempotence: one warm-started refit (start_head = point fit
    head) on the UNTOUCHED training frame reproduces the point betas to
    +/-0.001 — validates the warm-start path every jackknife/permutation
    refit uses, and provides the per-refit timing probe.
G3  draws-vs-summary: percentile 95% endpoints of the rate-gap draws
    recomputed from each committed draws CSV match the committed JSON
    summaries to 1e-6 (stratum ci_95; temporal ci_95_percentile).
G4  basic-interval parity vs manuscript Table 6 (basic = [2*point - q97.5,
    2*point - q2.5], computed from the draws): stratum [-2.76, +0.74],
    temporal [-10.84, +0.91], each endpoint to +/-0.01.
G5  bias parity vs manuscript: mean(draws) - point = +0.82 (stratum) and
    +2.64 (temporal), each to +/-0.01.
G6  sign-share parity: exactly 1 of 198 stratum draws <= 0 and 1 of 196
    temporal draws <= 0 (the "197 of 198" sentence).
Wiring asserts (hard, assert-style): committed n_reps 200 both schemes;
draw counts 198/196; artifact ridge_alpha == 1e-4; stratum-summary
point_production_units == artifact coefficients to 1e-9; training frame has
10,176 cells / 296 strata / 36 months; market_rate constant within month.

=======================================================================
STEP 2 — BCa TEST of H0: beta_g <= 0 (both schemes)
=======================================================================
The bootstrap draws are NOT regenerated: the committed replicate draws are
the inferential sample (they exist as artifacts; regenerating them would
re-litigate Table 6, not test it). Per scheme:
  z0 = Phi^-1( #{beta* < beta_hat} / B )        (median-bias correction)
  a  = acceleration from a delete-one jackknife over that scheme's
       resampling units, refit warm-started via fit_betas, rescaled to
       production units:
         stratum scheme:  delete-one-STRATUM, 296 refits;
         temporal scheme: delete-one-MONTH,    36 refits;
       a = sum((tbar-t_i)^3) / (6 * [sum((tbar-t_i)^2)]^1.5).
  One-sided p by CI inversion (lower BCa bound hits 0):
       q  = Phi^-1( #{beta* <= 0} / B )   (clipped to [0.5/B, 1-0.5/B],
                                           as are the z0 counts)
       u  = (q - z0) / (1 + a*(q - z0))
       p  = Phi(u - z0)
  a = 0 recovers the z0-only bias-corrected (BC) p; a = z0 = 0 recovers the
  percentile p (sanity anchor).
RUNTIME BUDGET (fixed ex ante, per the review mandate): the G2b probe times
one warm refit. The 296-refit stratum jackknife runs iff that time is
<= 5.0 s/refit (~25 min); otherwise the stratum scheme falls back to the
BC (z0-only) p-value, and the results JSON carries the labeled limitation
"stratum acceleration SKIPPED (refit too slow); p is BC, not BCa". The
36-refit month jackknife runs iff <= 45.0 s/refit. Jackknife refits that
fail to converge are counted and excluded; if more than 5% of a scheme's
jackknife refits fail, that scheme's acceleration is invalid -> BC
fallback, same label. If the BCa denominator 1 + a*(q - z0) <= 0
(construction breakdown), that scheme falls back to BC, labeled.

=======================================================================
STEP 3 — PERMUTATION TEST (temporal-scheme complement; the only leg that
does not reuse the diagnosed-biased bootstrap distributions)
=======================================================================
Design: within the 36-month training window, permute the month ->
market-rate assignment (one MORTGAGE30US level per month; asserted constant
within month). Each permutation reassigns whole months' rates, recomputes
rate_gap_bps = (coupon_dec - market_rate_perm) * 1e4 row-wise, and refits
spec v3 via fit_betas (warm-started from the point fit, same failure
accounting), rescaling beta_g* to production units. Each month's
cross-section (outcomes, exposure, burnout, friction, loan_age, strata) is
kept fully intact — the permutation breaks ONLY the temporal alignment of
the rate-gap series with prepayment outcomes, which is exactly the
alignment the sign claim asserts is informative.
  N_PERM = 200 permutations, seed 42 (np.random.default_rng(42)); the
  identity permutation is not excluded (probability 1/36! ~ 3e-42).
  PRIMARY p (as mandated, with the standard Phipson-Smyth finite-sample
  correction): p_perm = (1 + #{ |beta_g*_j| >= beta_g_hat }) / (1 + M),
  M = converged permutations. The raw share and the strictly one-sided
  variant (1 + #{beta_g*_j >= beta_g_hat}) / (1 + M) are recorded as
  disclosed secondaries; the PRIMARY decides the verdict.
  DEGRADATION RULE: if M < 160 (80% of 200), the permutation leg is
  INVALID; the verdict is INCONCLUSIVE_PERMUTATION_DEGRADED and no
  T-branch is claimed.

=======================================================================
STEP 4 — EX-ANTE INTERPRETIVE THRESHOLDS (fixed before the run; no
discretion is exercised after it)
=======================================================================
Let p_boot(s) be the scheme-s p from STEP 2 (BCa where valid, else labeled
BC) and p_perm the STEP-3 primary. Decision level 0.05 (one-sided).
  bootstrap leg PASS := p_boot(stratum) <= 0.05 OR p_boot(temporal) <= 0.05
      (the mandate's "(either scheme)" reading, fixed here ex ante; the
      stricter both-schemes indicator is also reported, as disclosure only).
  permutation leg PASS := p_perm <= 0.05.
T1 (both legs PASS): the sign claim stands; the manuscript may keep "sign
   stability" language with this test cited (Table 6 note's deferred BCa is
   discharged).
T2 (exactly one leg PASSes): split verdict; the manuscript must weaken to
   "directionally consistent, significance construction-dependent", and
   Section V.B's "sign-triangulated by two in-sample estimates"
   (revised_paper_v18.tex:349) must be downgraded to "sign-consistent".
T3 (both legs FAIL): the manuscript must state that the in-sample estimate
   is not statistically distinguishable from zero under bias-respecting
   constructions, and that the elasticity's evidential basis is the
   external literature alone; drop "sign-triangulated by two in-sample
   estimates".

=======================================================================
SELF-CHECKS — HARD vs SOFT
=======================================================================
HARD: the parity gates and wiring asserts of STEP 1 (write-then-SystemExit
on failure; results must not be cited).
SOFT (reported, never blocking): the BC components are DETERMINISTIC given
the committed draws, so they are computed and disclosed here, ex ante,
rather than discovered by the run:
    stratum:  #{<0.6734}=53/198  -> z0 = -0.6199;  q = -2.5724;
              p_BC = 0.09132
    temporal: #{<0.6734}=24/196  -> z0 = -1.1628;  q = -2.5688;
              p_BC = 0.40394
Both BC p-values exceed 0.05 — the MF-5 diagnosis in p-value form. The run
adds ONLY quantities not already determined by committed artifacts: the two
acceleration constants (which move p_BC to p_BCa in either direction) and
the permutation p. The script checks its own z0/p_BC against these pinned
values to 1e-3 and reports SOFT PASS/DEVIATION.

RUNTIME: printed at start — the G2 cold refit and G2b warm probe are timed,
the total is extrapolated as t_warm * (200 + enabled jackknife refits) and
printed BEFORE any loop starts, with the jackknife enable/skip decisions.

Outputs (all regenerable, none overwrite committed artifacts):
  data/patha_sign_test_results.json            (primary)
  data/patha_sign_test_permutation_draws.csv   (per-permutation betas)
  data/patha_sign_test_jackknife_stratum.csv   (if jackknife ran)
  data/patha_sign_test_jackknife_month.csv     (if jackknife ran)

Run:  cd hazard && python3 patha_sign_test.py
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

from config import DATA_DIR
from bootstrap_se import BETA_NAMES, fit_betas, rescale_to_production_units
from temporal_block_bootstrap import load_train

SPECV3_COEF_PATH = DATA_DIR / "hazard_coefficients_specv3.json"
STRATUM_SUMMARY_JSON = DATA_DIR / "hazard_bootstrap_se.json"
STRATUM_DRAWS_CSV = DATA_DIR / "hazard_bootstrap_draws.csv"
TEMPORAL_SUMMARY_JSON = DATA_DIR / "temporal_block_bootstrap.json"
TEMPORAL_DRAWS_CSV = DATA_DIR / "temporal_block_bootstrap_draws.csv"
RESULTS_JSON = DATA_DIR / "patha_sign_test_results.json"
PERM_DRAWS_CSV = DATA_DIR / "patha_sign_test_permutation_draws.csv"
JACK_CSV = {
    "stratum": DATA_DIR / "patha_sign_test_jackknife_stratum.csv",
    "temporal": DATA_DIR / "patha_sign_test_jackknife_month.csv",
}

RIDGE_ALPHA_PINNED = 1e-4
SEED = 42
N_PERM = 200
ALPHA_LEVEL = 0.05

POINT_UNROUNDED = {
    "rate_gap_bps": 0.6733519352905115,
    "burnout_orth": -0.13009048732147674,
    "friction": -0.037066025306261775,
}
MANUSCRIPT_POINT = {"rate_gap_bps": 0.673, "burnout_orth": -0.130,
                    "friction": -0.037}
MANUSCRIPT_BASIC = {"stratum": (-2.76, 0.74), "temporal": (-10.84, 0.91)}
MANUSCRIPT_BIAS = {"stratum": 0.82, "temporal": 2.64}
EXPECTED_DRAWS = {"stratum": 198, "temporal": 196}
EXPECTED_N_LE0 = {"stratum": 1, "temporal": 1}

TOL_BETA = 1e-3
TOL_SUMMARY = 1e-6
TOL_BASIC = 0.01
TOL_BIAS = 0.01

# SOFT expectations — deterministic from committed draws (see header).
SOFT_BC = {
    "stratum": {"z0": -0.6199, "q": -2.5724, "p_bc": 0.09132},
    "temporal": {"z0": -1.1628, "q": -2.5688, "p_bc": 0.40394},
}
SOFT_TOL = 1e-3

STRATUM_JACK_BUDGET_S = 5.0
MONTH_JACK_BUDGET_S = 45.0
JACK_MAX_FAIL_SHARE = 0.05
PERM_MIN_CONVERGED = 160

N_TRAIN_EXPECTED = 10176
N_STRATA_EXPECTED = 296
N_MONTHS_EXPECTED = 36


def _gate(name: str, got: float, want: float, tol: float,
          report: dict) -> None:
    ok = abs(got - want) < tol
    report[name] = {"got": float(got), "want": float(want), "tol": tol,
                    "pass": bool(ok)}
    print(f"parity gate {name}: got {got:.7f} want {want:.7f} "
          f"[{'PASS' if ok else 'FAIL'}]")


def _soft(name: str, got: float, want: float, tol: float,
          report: dict) -> None:
    ok = abs(got - want) < tol
    report[name] = {"got": float(got), "want": float(want), "tol": tol,
                    "consistent": bool(ok)}
    print(f"soft check {name}: got {got:.5f} pinned {want:.5f} "
          f"[{'SOFT PASS' if ok else 'SOFT DEVIATION — re-examine'}]")


def _abort(payload: dict, msg: str) -> None:
    """House rule: write what is known for diagnosis, then stop."""
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1)
    raise SystemExit(f"PARITY FAILURE — do not build on this: {msg}")


def clipped_norm_ppf(count: int, total: int) -> tuple[float, float]:
    frac = float(np.clip(count / total, 0.5 / total, 1 - 0.5 / total))
    return float(norm.ppf(frac)), frac


def accel_from_jackknife(thetas: np.ndarray) -> float:
    d = thetas.mean() - thetas
    denom = (d ** 2).sum() ** 1.5
    if denom == 0.0:
        return 0.0
    return float((d ** 3).sum() / (6.0 * denom))


def bc_a_pvalue(draws: np.ndarray, point: float,
                a: float) -> dict:
    """One-sided p for H0: theta <= 0 by BCa lower-bound inversion.
    a=0 gives the BC (z0-only) p; a=z0=0 collapses to the percentile p."""
    B = len(draws)
    z0, frac_lt = clipped_norm_ppf(int((draws < point).sum()), B)
    q, frac_le0 = clipped_norm_ppf(int((draws <= 0).sum()), B)
    denom = 1.0 + a * (q - z0)
    out = {
        "B": B,
        "n_lt_point": int((draws < point).sum()),
        "n_le_zero": int((draws <= 0).sum()),
        "z0": z0,
        "q": q,
        "acceleration": a,
        "percentile_p": frac_le0,
        "breakdown": bool(denom <= 0),
    }
    if denom <= 0:
        out["p"] = float("nan")
        return out
    u = (q - z0) / denom
    out["p"] = float(norm.cdf(u - z0))
    return out


def jackknife_leg(scheme: str, train: pd.DataFrame, unit_col: str,
                  units: list, point_head: np.ndarray,
                  prod_scales: dict) -> dict:
    """Delete-one-unit jackknife over `units`; warm-started spec-v3 refits;
    beta_g in production units. Deterministic (no RNG)."""
    thetas, failed = [], 0
    kept_units = []
    t0 = time.perf_counter()
    for i, u in enumerate(units):
        sub = train[train[unit_col] != u]
        try:
            b = fit_betas(sub, RIDGE_ALPHA_PINNED, start_head=point_head,
                          seasonal=False)
            r = rescale_to_production_units(b, prod_scales)
            thetas.append(r["rate_gap_bps"])
            kept_units.append(str(u))
        except Exception as exc:
            failed += 1
            print(f"  jackknife[{scheme}] {i + 1}/{len(units)}: "
                  f"FAILED ({exc})")
        if (i + 1) % 25 == 0 or i + 1 == len(units):
            el = time.perf_counter() - t0
            print(f"  jackknife[{scheme}] {i + 1}/{len(units)} "
                  f"({el / (i + 1):.1f}s/refit, {el:.0f}s elapsed)")
    thetas_arr = np.asarray(thetas, dtype=np.float64)
    pd.DataFrame({unit_col: kept_units,
                  "rate_gap_bps": thetas_arr}).to_csv(
        JACK_CSV[scheme], index=False)
    fail_share = failed / len(units)
    valid = fail_share <= JACK_MAX_FAIL_SHARE and len(thetas) >= 2
    return {
        "scheme": scheme,
        "unit": unit_col,
        "n_units": len(units),
        "n_failed": failed,
        "fail_share": fail_share,
        "valid": bool(valid),
        "acceleration": accel_from_jackknife(thetas_arr) if valid else None,
        "csv": str(JACK_CSV[scheme].name),
        "runtime_s": time.perf_counter() - t0,
    }


def permutation_leg(train: pd.DataFrame, months: list,
                    base_rates: np.ndarray, point_head: np.ndarray,
                    prod_scales: dict, beta_hat: float) -> dict:
    """STEP 3: month -> market-rate permutation, spec-v3 refit per draw."""
    rng = np.random.default_rng(SEED)
    draws: dict[str, list[float]] = {n: [] for n in BETA_NAMES}
    n_failed = 0
    t0 = time.perf_counter()
    for j in range(N_PERM):
        perm = rng.permutation(len(months))
        rate_map = {m: base_rates[k] for m, k in zip(months, perm)}
        tp = train.copy()
        mr = tp["period"].map(rate_map)
        assert not mr.isna().any(), "month->rate map missed a period"
        tp["rate_gap_bps"] = (
            (tp["coupon_dec"].to_numpy() - mr.to_numpy()) * 10_000.0
        )
        try:
            b = fit_betas(tp, RIDGE_ALPHA_PINNED, start_head=point_head,
                          seasonal=False)
        except Exception as exc:
            n_failed += 1
            print(f"  perm {j + 1}/{N_PERM}: FAILED ({exc})")
            continue
        r = rescale_to_production_units(b, prod_scales)
        for n in BETA_NAMES:
            draws[n].append(r[n])
        pd.DataFrame(draws).to_csv(PERM_DRAWS_CSV, index=False)  # checkpoint
        if (j + 1) % 10 == 0 or j == 0:
            el = time.perf_counter() - t0
            print(f"  perm {j + 1}/{N_PERM}  "
                  f"({el / (j + 1):.1f}s/refit, {el:.0f}s elapsed)")
    g = np.asarray(draws["rate_gap_bps"], dtype=np.float64)
    M = len(g)
    n_abs_ge = int((np.abs(g) >= beta_hat).sum())
    n_ge = int((g >= beta_hat).sum())
    return {
        "n_perm": N_PERM,
        "n_converged": M,
        "n_failed": n_failed,
        "valid": bool(M >= PERM_MIN_CONVERGED),
        "beta_hat": beta_hat,
        "n_abs_ge_observed": n_abs_ge,
        "n_ge_observed": n_ge,
        "p_primary_abs": (1 + n_abs_ge) / (1 + M) if M else float("nan"),
        "p_secondary_onesided": (1 + n_ge) / (1 + M) if M else float("nan"),
        "raw_share_abs": n_abs_ge / M if M else float("nan"),
        "raw_share_onesided": n_ge / M if M else float("nan"),
        "perm_gap_mean": float(g.mean()) if M else float("nan"),
        "perm_gap_sd": float(g.std(ddof=1)) if M > 1 else float("nan"),
        "draws_csv": str(PERM_DRAWS_CSV.name),
        "runtime_s": time.perf_counter() - t0,
    }


def main() -> None:
    t_start = time.perf_counter()
    gate_report: dict = {}
    soft_report: dict = {}
    payload: dict = {
        "mode": "patha_sign_test",
        "finding": "round-21 MF-5",
        "seed": SEED,
        "ridge_alpha": RIDGE_ALPHA_PINNED,
        "alpha_level": ALPHA_LEVEL,
        "spec": (
            "H0: beta_g <= 0 tested two ways on the committed spec-v3 Path A "
            "fit: (1) BCa/BC p by CI inversion on the committed replicate "
            "draws (z0 from draws; acceleration from delete-one-stratum "
            "[296 refits, <=5s/refit budget] and delete-one-month [36 "
            "refits, <=45s/refit budget] jackknives, warm-started, BC "
            "fallback labeled); (2) month->market-rate permutation test, "
            "200 perms, seed 42, p = (1+#{|beta*|>=beta_hat})/(1+M). "
            "Parity gates G1-G6 block. Ex-ante thresholds: T1 both legs "
            "p<=0.05; T2 exactly one; T3 neither. Bootstrap leg passes if "
            "EITHER scheme's p <= 0.05 (fixed ex ante from the mandate "
            "wording; both-scheme indicator disclosed)."
        ),
        "manuscript_anchor": {
            "table": "tab:bootstrap (revised_paper_v18.tex:405-422)",
            "sign_sentence": "positive in 197 of 198 converged replications "
                             "(revised_paper_v18.tex:397)",
            "vb_phrase": "sign-triangulated by two in-sample estimates "
                         "(revised_paper_v18.tex:349)",
            "deferred_bca": "revised_paper_v18.tex:422",
        },
        "parity_gates": gate_report,
        "soft_checks": soft_report,
    }

    # ---- STEP 0/1: pinned artifacts + cheap gates (no refits yet) ----------
    prod = json.load(open(SPECV3_COEF_PATH))
    assert int(prod["spec_version"]) == 3, "wrong artifact: not spec v3"
    assert abs(float(prod["ridge_alpha"]) - RIDGE_ALPHA_PINNED) < 1e-12
    assert int(prod["n_train"]) == N_TRAIN_EXPECTED
    assert int(prod["n_strata"]) == N_STRATA_EXPECTED
    for n in BETA_NAMES:
        assert abs(float(prod["coefficients"][n]) - POINT_UNROUNDED[n]) < 1e-9
    beta_hat = POINT_UNROUNDED["rate_gap_bps"]
    prod_scales = {
        "gap_std": float(prod["rate_gap_bps_std"]),
        "burn_std": float(prod["burnout_demean_std"]),
        "fric_std": float(prod["friction_std"]),
    }

    strat_sum = json.load(open(STRATUM_SUMMARY_JSON))
    temp_sum = json.load(open(TEMPORAL_SUMMARY_JSON))
    assert int(strat_sum["n_reps"]) == 200 and int(temp_sum["n_reps"]) == 200
    assert int(strat_sum["spec_version"]) == 3
    for n in BETA_NAMES:
        assert abs(strat_sum["point_production_units"][n]
                   - POINT_UNROUNDED[n]) < 1e-9

    draws = {
        "stratum": pd.read_csv(STRATUM_DRAWS_CSV)["rate_gap_bps"].to_numpy(),
        "temporal": pd.read_csv(TEMPORAL_DRAWS_CSV)["rate_gap_bps"].to_numpy(),
    }
    committed_pctl = {
        "stratum": (float(strat_sum["ci_95"]["rate_gap_bps"]["lo"]),
                    float(strat_sum["ci_95"]["rate_gap_bps"]["hi"])),
        "temporal": tuple(
            float(v) for v in
            temp_sum["stats"]["rate_gap_bps"]["ci_95_percentile"]),
    }

    for n in BETA_NAMES:
        _gate(f"G1_{n}", float(prod["coefficients"][n]),
              MANUSCRIPT_POINT[n], TOL_BETA, gate_report)

    for s in ["stratum", "temporal"]:
        x = draws[s]
        assert len(x) == EXPECTED_DRAWS[s], (s, len(x))
        lo, hi = np.percentile(x, [2.5, 97.5])
        _gate(f"G3_pctl_lo_{s}", float(lo), committed_pctl[s][0],
              TOL_SUMMARY, gate_report)
        _gate(f"G3_pctl_hi_{s}", float(hi), committed_pctl[s][1],
              TOL_SUMMARY, gate_report)
        _gate(f"G4_basic_lo_{s}", 2 * beta_hat - float(hi),
              MANUSCRIPT_BASIC[s][0], TOL_BASIC, gate_report)
        _gate(f"G4_basic_hi_{s}", 2 * beta_hat - float(lo),
              MANUSCRIPT_BASIC[s][1], TOL_BASIC, gate_report)
        _gate(f"G5_bias_{s}", float(x.mean()) - beta_hat,
              MANUSCRIPT_BIAS[s], TOL_BIAS, gate_report)
        _gate(f"G6_n_le0_{s}", float((x <= 0).sum()),
              float(EXPECTED_N_LE0[s]), 0.5, gate_report)
        # SOFT: deterministic BC components vs header-pinned values.
        bc = bc_a_pvalue(x, beta_hat, a=0.0)
        _soft(f"z0_{s}", bc["z0"], SOFT_BC[s]["z0"], SOFT_TOL, soft_report)
        _soft(f"p_bc_{s}", bc["p"], SOFT_BC[s]["p_bc"], SOFT_TOL,
              soft_report)

    hard_fail = [k for k, v in gate_report.items() if not v["pass"]]
    if hard_fail:
        _abort(payload, str(hard_fail))

    # ---- Training frame + refit parity (G2, G2b) ---------------------------
    print("\nBuilding training frame (production filters, live macro join) …")
    train = load_train()
    assert len(train) == N_TRAIN_EXPECTED, len(train)
    assert train["stratum_id"].nunique() == N_STRATA_EXPECTED
    month_rate = train.groupby("period")["market_rate"].agg(
        ["min", "max", "size"])
    assert (month_rate["min"] == month_rate["max"]).all(), \
        "market_rate not constant within month"
    months = list(month_rate.index)
    base_rates = month_rate["min"].to_numpy(dtype=np.float64)
    assert len(months) == N_MONTHS_EXPECTED, len(months)

    print("G2: cold spec-v3 point refit (timed) …")
    t0 = time.perf_counter()
    point = fit_betas(train, RIDGE_ALPHA_PINNED, start_head=None,
                      seasonal=False)
    t_point = time.perf_counter() - t0
    for n in BETA_NAMES:
        _gate(f"G2_{n}", point[n], POINT_UNROUNDED[n], TOL_BETA, gate_report)

    print("G2b: warm-start idempotence probe (timed; the per-refit clock) …")
    t0 = time.perf_counter()
    warm = fit_betas(train, RIDGE_ALPHA_PINNED,
                     start_head=point["params_head"], seasonal=False)
    t_warm = time.perf_counter() - t0
    for n in BETA_NAMES:
        _gate(f"G2b_{n}", warm[n], point[n], TOL_BETA, gate_report)

    hard_fail = [k for k, v in gate_report.items() if not v["pass"]]
    if hard_fail:
        _abort(payload, str(hard_fail))

    # ---- Runtime estimate + jackknife enablement (fixed ex-ante budgets) ---
    run_stratum_jack = t_warm <= STRATUM_JACK_BUDGET_S
    run_month_jack = t_warm <= MONTH_JACK_BUDGET_S
    n_planned = (N_PERM
                 + (N_STRATA_EXPECTED if run_stratum_jack else 0)
                 + (N_MONTHS_EXPECTED if run_month_jack else 0))
    est_s = t_warm * n_planned
    strat_msg = ("ON" if run_stratum_jack else
                 "SKIPPED: refit > 5.0s budget — stratum p will be BC, "
                 "not BCa")
    month_msg = ("ON" if run_month_jack else
                 "SKIPPED: refit > 45.0s budget — temporal p will be BC, "
                 "not BCa")
    print(f"\nRUNTIME ESTIMATE: cold refit {t_point:.1f}s, warm refit "
          f"{t_warm:.1f}s -> {n_planned} planned refits "
          f"~{est_s / 60:.0f} min "
          f"(stratum jackknife {strat_msg}; month jackknife {month_msg})")
    payload["timing"] = {
        "t_cold_refit_s": t_point,
        "t_warm_refit_s": t_warm,
        "n_planned_refits": n_planned,
        "estimated_total_s": est_s,
        "stratum_jackknife_enabled": bool(run_stratum_jack),
        "month_jackknife_enabled": bool(run_month_jack),
    }

    # ---- STEP 2: acceleration constants (jackknives) -----------------------
    jack: dict[str, dict | None] = {"stratum": None, "temporal": None}
    if run_stratum_jack:
        print("\nSTEP 2a: delete-one-stratum jackknife (296 refits) …")
        jack["stratum"] = jackknife_leg(
            "stratum", train, "stratum_id",
            sorted(train["stratum_id"].unique()), point["params_head"],
            prod_scales)
    if run_month_jack:
        print("\nSTEP 2b: delete-one-month jackknife (36 refits) …")
        jack["temporal"] = jackknife_leg(
            "temporal", train, "period", months, point["params_head"],
            prod_scales)

    schemes: dict[str, dict] = {}
    for s in ["stratum", "temporal"]:
        j = jack[s]
        a_valid = j is not None and j["valid"]
        a = float(j["acceleration"]) if a_valid else 0.0
        res = bc_a_pvalue(draws[s], beta_hat, a=a)
        kind = "BCa" if (a_valid and not res["breakdown"]) else "BC"
        if kind == "BC" and (a_valid and res["breakdown"]):
            res_bc = bc_a_pvalue(draws[s], beta_hat, a=0.0)
            res["p"] = res_bc["p"]
        limitation = None
        if j is None:
            limitation = (f"{s} acceleration SKIPPED (warm refit exceeded "
                          "the ex-ante per-refit budget); p is BC (z0-only "
                          "bias-corrected), not BCa — labeled limitation "
                          "per the pre-committed spec")
        elif not j["valid"]:
            limitation = (f"{s} jackknife invalid (fail share "
                          f"{j['fail_share']:.3f} > 5%); BC fallback")
        elif res["breakdown"]:
            limitation = (f"{s} BCa denominator non-positive (construction "
                          "breakdown); BC fallback")
        schemes[s] = {**res, "jackknife": j, "p_kind": kind,
                      "limitation": limitation}
        print(f"scheme {s}: p_{kind} = {schemes[s]['p']:.5f}  "
              f"(z0 {res['z0']:+.4f}, q {res['q']:+.4f}, a {a:+.5f})"
              + (f"  [{limitation}]" if limitation else ""))
    payload["schemes"] = schemes

    # ---- STEP 3: permutation test ------------------------------------------
    print(f"\nSTEP 3: month->market-rate permutation test "
          f"({N_PERM} perms, seed {SEED}) …")
    perm = permutation_leg(train, months, base_rates, point["params_head"],
                           prod_scales, beta_hat)
    payload["permutation"] = perm
    print(f"permutation: p_primary = {perm['p_primary_abs']:.5f} "
          f"({perm['n_abs_ge_observed']} of {perm['n_converged']} converged "
          f"perms with |beta_g*| >= {beta_hat:+.4f}; one-sided secondary "
          f"{perm['p_secondary_onesided']:.5f})")

    # ---- STEP 4: ex-ante verdict -------------------------------------------
    p_strat = schemes["stratum"]["p"]
    p_temp = schemes["temporal"]["p"]
    boot_pass_either = bool(p_strat <= ALPHA_LEVEL or p_temp <= ALPHA_LEVEL)
    boot_pass_both = bool(p_strat <= ALPHA_LEVEL and p_temp <= ALPHA_LEVEL)
    perm_pass = bool(perm["valid"] and perm["p_primary_abs"] <= ALPHA_LEVEL)

    if not perm["valid"]:
        branch = "INCONCLUSIVE_PERMUTATION_DEGRADED"
        action = ("permutation leg failed the 80% convergence floor; no "
                  "T-branch is claimed — report and re-examine before any "
                  "manuscript change")
    elif boot_pass_either and perm_pass:
        branch = "T1"
        action = ("sign claim stands; manuscript may keep 'sign stability' "
                  "with this test cited (Table 6's deferred BCa discharged)")
    elif boot_pass_either or perm_pass:
        branch = "T2"
        action = ("split verdict: weaken to 'directionally consistent, "
                  "significance construction-dependent'; downgrade V.B "
                  "'sign-triangulated' (tex:349) to 'sign-consistent'")
    else:
        branch = "T3"
        action = ("state the in-sample estimate is not statistically "
                  "distinguishable from zero under bias-respecting "
                  "constructions; the elasticity's evidential basis is the "
                  "external literature alone; drop 'sign-triangulated by "
                  "two in-sample estimates'")

    payload["verdict"] = {
        "branch": branch,
        "p_bootstrap_stratum": p_strat,
        "p_bootstrap_stratum_kind": schemes["stratum"]["p_kind"],
        "p_bootstrap_temporal": p_temp,
        "p_bootstrap_temporal_kind": schemes["temporal"]["p_kind"],
        "p_permutation_primary": perm["p_primary_abs"],
        "bootstrap_leg_pass_either_scheme": boot_pass_either,
        "bootstrap_leg_pass_both_schemes_disclosure": boot_pass_both,
        "permutation_leg_pass": perm_pass,
        "manuscript_action": action,
    }
    payload["runtime_s"] = time.perf_counter() - t_start
    payload["parity_gates_all_pass"] = True

    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1)
    print("\n" + "=" * 64)
    print(f" VERDICT {branch}: {action}")
    print("=" * 64)
    print(f"p(stratum, {schemes['stratum']['p_kind']}) = {p_strat:.5f}   "
          f"p(temporal, {schemes['temporal']['p_kind']}) = {p_temp:.5f}   "
          f"p(permutation) = {perm['p_primary_abs']:.5f}")
    print(f"Results saved to {RESULTS_JSON}  "
          f"(runtime {payload['runtime_s']:,.0f}s)")


if __name__ == "__main__":
    main()
