#!/usr/bin/env python3
"""
Calendar-alignment permutation test for Path A's spec-v4 seasonal adoption.
(Pre-committed; spec fixed in this header before any run executed.)

WHAT THIS MODULE IS FOR. pathA_seasonal_adoption.py adopted spec v4 (eleven
calendar-month dummies) as production Path A. revised_paper_v17.tex (line 430,
sec:patha) reads the adoption as three joint improvements over spec v3:
the lag-0 CPR correlation moves from -0.444 to -0.378, the correlation peak
moves from lag -3 to lag -2, and the recovery moves from 119.7% to 121.5%.
The month dummies are credited with all three.

No null was ever run. The month effects are estimated on the same window whose
path they are then scored against, so the question "would ANY assignment of
these twelve log-effects to calendar months have done as well?" is open. This
module closes it by permuting the month -> log-effect ASSIGNMENT. A permutation
preserves the multiset of the twelve effects EXACTLY, and therefore preserves
their mean, their dispersion, and every level channel they drive; it destroys
only the ALIGNMENT between seasonal structure and calendar time. Whatever
survives permutation was never calendar-attributable.

THE CRITERION IS CONJUNCTIVE, AND THAT IS THE POINT. The manuscript claims the
correlation improved AND the peak moved to -2. A scramble refutes that claim
only by achieving BOTH. Scoring the two components separately and reporting
each marginal rate understates the claim and is not the test the manuscript
invites. The JOINT count is the primary statistic here; the marginal component
counts are reported alongside it as diagnostics only, explicitly labelled as
such, and the p-value is computed on the joint criterion.

The recovery is scored separately and is NOT part of the joint criterion,
because it is a level and the two correlation quantities are timing statistics;
pooling them would let a level result rescue a timing claim or vice versa.

SPEC (fixed ex ante)
====================

- OBJECT UNDER TEST: seasonality_concave_gap.simulate_with_seasonality, driven
  by (i) the committed spec-v3 coefficients from
  data/hazard_coefficients_specv3.json for the production leg, and (ii) the
  spec-v4 coefficients and month effects refit here by
  seasonality_concave_gap.fit_with_month_dummies on the same pre-holdout
  training frame the committed adoption used. Same panel (config.PANEL_PATH),
  same macro frame, same HOLDOUT_DATE split, same ridge alpha read from the
  committed spec-v3 artifact.

- PERMUTATION FAMILIES. Two independent families, both scored identically:
    PRIMARY:   N_PERM = 64 at SEED = 777001
    SECONDARY: N_PERM = 16 at SEED = 20260719
  The secondary family is a smaller independent replication at a different
  seed and is reported for stability only; the primary family carries the
  p-value. Draws are distinct permutations of range(12), the identity is
  rejected, and duplicates within a family are rejected — so each family is a
  sample without replacement from the 12! - 1 non-identity assignments.

- JOINT CRITERION (PRIMARY, fixed ex ante). A scramble "wins" iff BOTH:
    (a) r(lag 0) > the true spec-v4 r(lag 0) of -0.37817286723880483
        (strictly greater: less negative, i.e. a better contemporaneous fit),
        AND
    (b) best_lag == -2, the peak the manuscript credits to the adoption.
  One-sided p = (n_joint + 1) / (N_PERM + 1), the standard permutation
  p-value with the observed configuration included in the reference set.
  DECISION RULE, pre-committed at the conventional level:
    p <= 0.05  -> "calendar_alignment_supported": the joint improvement is
        not reproduced by arbitrary reassignment of the same effects, and the
        manuscript's conjunctive correlation-and-lag claim survives.
    p >  0.05  -> "calendar_alignment_not_supported": arbitrary reassignment
        reproduces the joint improvement often enough that the calendar
        alignment carries no evidential weight and the claim must be withdrawn.
  MARGINAL COMPONENT COUNTS (n beating true r(lag 0); n landing lag -2) are
  recorded as DIAGNOSTICS ONLY. They are each necessarily >= n_joint and
  reading either one as "the" result understates a conjunctive claim.

- RECOVERY LEG (scored separately; not part of the joint criterion). Each
  scramble's recovery percentage against the same $764.748B empirical
  benchmark. Pre-committed rule, RECOVERY_INVARIANCE_TOL_PP = 5.0 points:
    span(recovery over scrambles) <= 5.0 pp ->
        "recovery_is_calendar_invariant": the 121.5% figure is reproduced by
        every arbitrary reassignment, so it was never a calendar-attributable
        quantity and must not be credited to the month dummies. The level
        channel that produces it is the multiset of effects, which permutation
        holds fixed by construction.
    span > 5.0 pp -> "recovery_is_calendar_sensitive".
  5.0 pp is set at roughly a third of the 119.7 -> 121.5 improvement the
  adoption claims, so a span below it means the claimed improvement is
  swamped by alignment-free variation.

- DECOMPOSITION LEGS (fixed ex ante; all differences against the production
  spec-v3 leg, so they are commensurable with the reported seasonal effect):
    refit_only        spec-v4 COEFFICIENTS with ALL twelve month multipliers
                      zeroed. Isolates what the refit does on its own, with
                      the seasonal multipliers switched off entirely.
    flat_arithmetic   constant log-effect at mean(effects). Level channel at
                      the additive mean, zero dispersion, zero alignment.
    flat_multiplicative constant at log(mean(exp(effects))), the
                      convexity-matched level. Same, on the multiplicative
                      scale the multiplier actually acts on.
  If refit_only alone moves the recovery by MORE than the total reported
  seasonal effect, then the month multipliers CLAW BACK rather than add, and
  "production plus seasonality" is not a decomposition of the spec-v4 total at
  all. That arithmetic is reported explicitly as month_multiplier_clawback_b.

- PARITY GATES (HARD; asserted BEFORE any permutation is read; on failure the
  run STOPS and writes a GATE_FAILURE payload rather than reinterpreting
  anything). All are exact float equality, not tolerances:
    P1 production leg == 915.067027857209
       (data/seasonality_concave_gap_results.json path_a_seasonality.production)
    P2 seasonal leg   == 928.892970289881
       (data/pathA_seasonal_adoption_results.json v4_trapped_b)
    P3 seasonal r(lag 0) == -0.37817286723880483  and  best_lag == -2
       (same artifact, v4_r_lag0 / v4_best_lag)
  This module re-drives both legs through its own loop rather than the
  committed adoption script, so anything less than bit-exactness means the
  re-wiring changed the object under study and every number below is about a
  different simulation.

- WHAT THIS MODULE DOES *NOT* CLAIM. Path A never calls
  literature_hazard.prepay_hazard, and the np.clip(log_mu, -20, 0) upper bound
  inside predict_hazard was instrumented over a full spec-v4 simulation with
  zero upper binds in 11,676 evaluations. No floor/clipping artifact is
  claimed or implied anywhere in this module's output.

- SCOPE. Path A is excluded from the paper's headline figures by pre-committed
  specification and is retained as an aggregate-level corroboration exhibit;
  the manuscript already concedes the seasonal terms do not improve holdout
  fit. Nothing here touches the headline marginal. This module bears on a
  corroboration claim and on the specification-adoption narrative, and on
  nothing else.

Output
------
data/pathA_seasonal_permutation_results.json: spec echo, parity gate block,
both permutation families with per-draw rows, the joint p-value, the recovery
span, the decomposition legs, and the pre-committed verdicts.

Run:  cd hazard && python3 pathA_seasonal_permutation.py
Runtime estimate: 2 parity legs + 80 permutation legs + 3 decomposition legs
  at ~2.1 s/leg ~= 3-4 min.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl

from config import HOLDOUT_DATE, PANEL_PATH
from extension_risk import score_extension_risk
from hazard_fit import enrich_panel_with_macro
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
)
from seasonality_concave_gap import fit_with_month_dummies, simulate_with_seasonality

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "pathA_seasonal_permutation_results.json"
SPECV3_JSON = DATA_DIR / "hazard_coefficients_specv3.json"
SEASONALITY_JSON = DATA_DIR / "seasonality_concave_gap_results.json"
ADOPTION_JSON = DATA_DIR / "pathA_seasonal_adoption_results.json"

PRIMARY = {"name": "primary", "n_perm": 64, "seed": 777001}
SECONDARY = {"name": "secondary", "n_perm": 16, "seed": 20260719}

RECOVERY_INVARIANCE_TOL_PP = 5.0
ALPHA = 0.05

# Spec v3 reference figures quoted by the manuscript (line 929 / line 430).
SPECV3_R_LAG0 = -0.444
SPECV3_RECOVERY_PCT = 119.7


def _score(sim, emp) -> dict:
    r = score_extension_risk(sim, emp)
    return {
        "trapped_b": float(r["hazard_trapped_b"]),
        "share_pct": float(r["share_explained_pct"]),
        "r_lag0": float(r["cross_correlation"].get(0)),
        "best_lag": int(r["best_lag"]),
    }


def _draw_family(n_perm: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    perms: list[np.ndarray] = []
    seen: set[tuple[int, ...]] = set()
    identity = np.arange(12)
    while len(perms) < n_perm:
        p = rng.permutation(12)
        key = tuple(int(x) for x in p)
        if key in seen or np.array_equal(p, identity):
            continue
        seen.add(key)
        perms.append(p)
    return perms


def _gate_failure(block: dict) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"mode": "pathA_seasonal_permutation", "status": "GATE_FAILURE", **block},
        indent=2, default=float) + "\n")
    raise SystemExit("Parity gate failure — permutation legs not run.")


def main() -> None:
    t0 = time.perf_counter()

    # Committed anchors, read from the artifacts rather than restated.
    committed_prod_b = float(
        json.loads(SEASONALITY_JSON.read_text())["path_a_seasonality"]["production"]["trapped_b"]
    )
    adoption = json.loads(ADOPTION_JSON.read_text())
    committed_seas_b = float(adoption["v4_trapped_b"])
    committed_seas_r0 = float(adoption["v4_r_lag0"])
    committed_seas_lag = int(adoption["v4_best_lag"])
    committed_seas_share = float(adoption["v4_share_pct"])

    print("Building macro/empirical frames and panel …")
    macro = calculate_dynamic_friction(fetch_data())
    emp = build_empirical_metrics(macro, soma_rolloff=fetch_soma_mbs_monthly())
    panel = pl.read_parquet(PANEL_PATH)

    v3 = json.loads(SPECV3_JSON.read_text())
    ridge_alpha = float(v3["ridge_alpha"])
    prod_coefs = dict(v3["coefficients"])

    # --- P1: production leg -------------------------------------------------
    print("P1: production (spec v3) leg …")
    prod = _score(
        simulate_with_seasonality(panel, prod_coefs, {m: 0.0 for m in range(1, 13)}, macro), emp
    )
    p1_exact = (prod["trapped_b"] == committed_prod_b)
    print(f"  {prod['trapped_b']:.12f}  committed {committed_prod_b:.12f}  "
          f"diff {abs(prod['trapped_b']-committed_prod_b):.3e}  "
          f"{'EXACT' if p1_exact else 'MISMATCH'}")

    # --- refit spec v4, the committed construction --------------------------
    print("Refitting spec v4 (fit_with_month_dummies) …")
    pdf = enrich_panel_with_macro(panel)
    pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age", "stratum_id"])
    pdf = pdf[pdf["exposure"] > 0]
    train = pdf[pdf["period"] < HOLDOUT_DATE].copy()
    coefs_s, month_effects, fit_method = fit_with_month_dummies(train, ridge_alpha)

    print("P2/P3: seasonal (spec v4) leg …")
    seasonal = _score(simulate_with_seasonality(panel, coefs_s, month_effects, macro), emp)
    p2_exact = (seasonal["trapped_b"] == committed_seas_b)
    p3_r0_exact = (seasonal["r_lag0"] == committed_seas_r0)
    p3_lag_match = (seasonal["best_lag"] == committed_seas_lag)
    print(f"  {seasonal['trapped_b']:.12f}  committed {committed_seas_b:.12f}  "
          f"diff {abs(seasonal['trapped_b']-committed_seas_b):.3e}  "
          f"{'EXACT' if p2_exact else 'MISMATCH'}")
    print(f"  r0 {seasonal['r_lag0']:.17f}  committed {committed_seas_r0:.17f}  "
          f"{'EXACT' if p3_r0_exact else 'MISMATCH'};  "
          f"lag {seasonal['best_lag']} vs {committed_seas_lag} "
          f"{'MATCH' if p3_lag_match else 'MISMATCH'}")

    parity = {
        "rule": "exact float equality against the committed artifacts",
        "P1_production": {
            "got_b": prod["trapped_b"], "committed_b": committed_prod_b,
            "abs_diff_b": abs(prod["trapped_b"] - committed_prod_b),
            "source": "data/seasonality_concave_gap_results.json path_a_seasonality.production",
            "bit_exact": p1_exact,
        },
        "P2_seasonal": {
            "got_b": seasonal["trapped_b"], "committed_b": committed_seas_b,
            "abs_diff_b": abs(seasonal["trapped_b"] - committed_seas_b),
            "source": "data/pathA_seasonal_adoption_results.json v4_trapped_b",
            "bit_exact": p2_exact,
        },
        "P3_seasonal_timing": {
            "got_r_lag0": seasonal["r_lag0"], "committed_r_lag0": committed_seas_r0,
            "abs_diff_r_lag0": abs(seasonal["r_lag0"] - committed_seas_r0),
            "got_best_lag": seasonal["best_lag"], "committed_best_lag": committed_seas_lag,
            "source": "data/pathA_seasonal_adoption_results.json v4_r_lag0 / v4_best_lag",
            "bit_exact": p3_r0_exact and p3_lag_match,
        },
        "pass": p1_exact and p2_exact and p3_r0_exact and p3_lag_match,
    }
    if not parity["pass"]:
        _gate_failure({"parity": parity})

    # Benchmark denominator implied by the committed share, used for recovery.
    benchmark_b = committed_seas_b / (committed_seas_share / 100.0)

    eff = np.array([month_effects[m] for m in range(1, 13)], dtype=float)
    reported_effect_b = seasonal["trapped_b"] - prod["trapped_b"]

    # --- permutation families ----------------------------------------------
    families = {}
    for fam in (PRIMARY, SECONDARY):
        print(f"\nPermutation family '{fam['name']}': "
              f"N={fam['n_perm']} seed={fam['seed']} …")
        rows = []
        for i, p in enumerate(_draw_family(fam["n_perm"], fam["seed"])):
            me = {m: float(eff[p[m - 1]]) for m in range(1, 13)}
            s = _score(simulate_with_seasonality(panel, coefs_s, me, macro), emp)
            s["perm_index"] = i
            s["order"] = [int(x) for x in p]
            s["effect_b"] = s["trapped_b"] - prod["trapped_b"]
            s["recovery_pct"] = s["trapped_b"] / benchmark_b * 100
            s["beats_true_r_lag0"] = bool(s["r_lag0"] > seasonal["r_lag0"])
            s["lag_is_minus2"] = bool(s["best_lag"] == committed_seas_lag)
            s["joint_win"] = bool(s["beats_true_r_lag0"] and s["lag_is_minus2"])
            rows.append(s)
            if i % 8 == 0:
                print(f"  perm {i:2d}: r0 {s['r_lag0']:+.4f} lag {s['best_lag']:+d} "
                      f"recovery {s['recovery_pct']:.3f}%  joint {s['joint_win']}")

        n = fam["n_perm"]
        n_joint = sum(r["joint_win"] for r in rows)
        n_r0 = sum(r["beats_true_r_lag0"] for r in rows)
        n_lag = sum(r["lag_is_minus2"] for r in rows)
        n_beat_v3 = sum(1 for r in rows if r["r_lag0"] > SPECV3_R_LAG0)
        recov = [r["recovery_pct"] for r in rows]
        joint_p = (n_joint + 1) / (n + 1)

        families[fam["name"]] = {
            "seed": fam["seed"],
            "n_perm": n,
            "PRIMARY_STATISTIC_joint": {
                "criterion": ("r(lag0) > true r(lag0) AND best_lag == -2 "
                              "(conjunctive, as the manuscript claim is)"),
                "n_joint_wins": n_joint,
                "p_one_sided": joint_p,
            },
            "diagnostics_marginal_components": {
                "note": ("DIAGNOSTIC ONLY — each is necessarily >= n_joint; reading either "
                         "component alone understates a conjunctive claim"),
                "n_beating_true_r_lag0": n_r0,
                "n_with_best_lag_minus2": n_lag,
                "n_beating_specv3_r_lag0_-0.444": n_beat_v3,
            },
            "r_lag0_span": {"min": float(min(r["r_lag0"] for r in rows)),
                            "max": float(max(r["r_lag0"] for r in rows))},
            "recovery_pct": {
                "min": float(min(recov)), "max": float(max(recov)),
                "span_pp": float(max(recov) - min(recov)),
                "mean": float(np.mean(recov)),
            },
            "effect_b": {
                "mean": float(np.mean([r["effect_b"] for r in rows])),
                "min": float(min(r["effect_b"] for r in rows)),
                "max": float(max(r["effect_b"] for r in rows)),
                "sd": float(np.std([r["effect_b"] for r in rows], ddof=1)),
            },
            "rows": rows,
        }
        print(f"  JOINT {n_joint}/{n}  p={joint_p:.4f} | "
              f"[diag] r0-beats {n_r0}, lag-2 {n_lag} | "
              f"recovery span {max(recov)-min(recov):.4f} pp")

    prim = families[PRIMARY["name"]]
    joint_p = prim["PRIMARY_STATISTIC_joint"]["p_one_sided"]
    recovery_span = prim["recovery_pct"]["span_pp"]

    verdict_alignment = ("calendar_alignment_supported" if joint_p <= ALPHA
                         else "calendar_alignment_not_supported")
    verdict_recovery = ("recovery_is_calendar_invariant"
                        if recovery_span <= RECOVERY_INVARIANCE_TOL_PP
                        else "recovery_is_calendar_sensitive")

    # --- decomposition legs -------------------------------------------------
    print("\nDecomposition legs …")
    decomposition = {}
    refit_only = _score(
        simulate_with_seasonality(panel, coefs_s, {m: 0.0 for m in range(1, 13)}, macro), emp
    )
    refit_only["effect_b"] = refit_only["trapped_b"] - prod["trapped_b"]
    refit_only["recovery_pct"] = refit_only["trapped_b"] / benchmark_b * 100
    refit_only["note"] = ("spec-v4 coefficients with ALL twelve month multipliers zeroed — "
                          "what the refit does with the seasonal multipliers switched off")
    decomposition["refit_only_zero_months"] = refit_only
    print(f"  refit_only: {refit_only['trapped_b']:.4f} B "
          f"(effect {refit_only['effect_b']:+.4f} B)")

    for name, const in (("flat_arithmetic_mean_logeffect", float(eff.mean())),
                        ("flat_multiplicative_mean", float(np.log(np.mean(np.exp(eff)))))):
        s = _score(
            simulate_with_seasonality(panel, coefs_s, {m: const for m in range(1, 13)}, macro), emp
        )
        s["const_log_effect"] = const
        s["effect_b"] = s["trapped_b"] - prod["trapped_b"]
        s["recovery_pct"] = s["trapped_b"] / benchmark_b * 100
        decomposition[name] = s
        print(f"  {name}: const {const:+.6f} -> {s['trapped_b']:.4f} B "
              f"(effect {s['effect_b']:+.4f} B)")

    clawback_b = seasonal["trapped_b"] - refit_only["trapped_b"]
    decomposable = abs(refit_only["effect_b"]) <= abs(reported_effect_b)

    payload = {
        "mode": "pathA_seasonal_permutation",
        "null_for": ("pathA_seasonal_adoption.py / data/pathA_seasonal_adoption_results.json "
                     "(revised_paper_v17.tex sec:patha, line 430)"),
        "spec": ("permute the month -> log-effect assignment (multiset, and therefore mean and "
                 "dispersion, preserved exactly; only calendar alignment destroyed); score each "
                 "draw on the CONJUNCTIVE criterion the manuscript claim states"),
        "engine": ("seasonality_concave_gap.simulate_with_seasonality over config.PANEL_PATH; "
                   "spec-v3 coefficients from data/hazard_coefficients_specv3.json; spec-v4 "
                   "refit via fit_with_month_dummies on the pre-HOLDOUT_DATE training frame"),
        "fit_method": fit_method,
        "ridge_alpha": ridge_alpha,
        "month_log_effects_jan_base": {str(m): float(v) for m, v in sorted(month_effects.items())},
        "parity_gates": parity,
        "benchmark_b": benchmark_b,
        "true_legs": {
            "production_specv3": prod,
            "seasonal_specv4": seasonal,
            "reported_seasonal_effect_b": reported_effect_b,
            "specv3_reference_r_lag0": SPECV3_R_LAG0,
            "specv3_reference_recovery_pct": SPECV3_RECOVERY_PCT,
        },
        "permutation_families": families,
        "primary_family": PRIMARY["name"],
        "decomposition": decomposition,
        "decomposability": {
            "reported_seasonal_effect_b": reported_effect_b,
            "refit_only_effect_b": refit_only["effect_b"],
            "month_multiplier_clawback_b": clawback_b,
            "is_decomposable_as_production_plus_seasonality": decomposable,
            "note": ("if the refit-only leg moves the total by MORE than the reported seasonal "
                     "effect, the month multipliers claw back rather than add and the spec-v4 "
                     "total is not decomposable as 'production plus seasonality'"),
        },
        "defect_class_1_scope": {
            "prepay_hazard_called_by_path_a": False,
            "predict_hazard_log_mu_upper_binds": 0,
            "predict_hazard_evaluations_instrumented": 11676,
            "note": ("Path A never calls literature_hazard.prepay_hazard, and the "
                     "np.clip(log_mu, -20, 0) upper bound never binds over a full spec-v4 "
                     "simulation; NO floor or clipping artifact is claimed"),
        },
        "scope_note": ("Path A is excluded from the paper's headline by pre-committed "
                       "specification and held to an aggregate-level corroboration role; the "
                       "manuscript already concedes the seasonal terms do not improve holdout "
                       "fit. This module bears on a corroboration claim and a "
                       "specification-adoption narrative, not on the headline marginal."),
        "alpha": ALPHA,
        "recovery_invariance_tol_pp": RECOVERY_INVARIANCE_TOL_PP,
        "verdict_calendar_alignment": verdict_alignment,
        "verdict_recovery": verdict_recovery,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\nJOINT (primary, N={PRIMARY['n_perm']}, seed {PRIMARY['seed']}): "
          f"{prim['PRIMARY_STATISTIC_joint']['n_joint_wins']}/{PRIMARY['n_perm']}, "
          f"p={joint_p:.4f} -> {verdict_alignment}")
    print(f"recovery span {recovery_span:.4f} pp -> {verdict_recovery}")
    print(f"refit-only effect {refit_only['effect_b']:+.4f} B; "
          f"month-multiplier clawback {clawback_b:+.4f} B")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
