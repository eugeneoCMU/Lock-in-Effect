#!/usr/bin/env python3
"""
1.3 — Permutation (null-model) test for Path A (cohort Poisson GLM with 295
stratum FE). Unlike Path B (which imports a fixed elasticity), Path A *learns*
its coefficients from data, so a permutation can change what the model learns,
not just what it predicts forward. This is the harder, more informative test.

Scope / design. Path A's estimation unit is the pre-aggregated cohort-month
panel, so the permutation necessarily operates at the stratum level rather than
the loan level (we cannot cheaply re-scan raw Freddie files per replicate). We
independently permute the four stratum-defining axes (vintage, coupon,
fico_bucket, ltv_bucket) across the ~297 strata, reassigning each stratum's
covariate *profile* while its outcome-side series (exposure, prepaid_upb,
burnout stock, mean loan age, period) stays in place. rate_gap_bps is recomputed
from the reassigned coupon inside the GLM fit; stratum FE relabel accordingly.
This tests whether the model's learned β(rate_gap), β(burnout), β(friction) and
its forward-simulated trapped/CPR depend on the real pairing of covariate
profile ↔ prepay outcomes.

Modes:
  independent    — four axes permuted independently across strata.
  profile-block  — whole 4-axis profile moved to a different stratum slot
                   (within-profile joint structure preserved, profile↔outcome
                   pairing broken) — isolates pairing from axis correlation.

Outputs: data/permutation_pathA_results.csv + _summary.json.

Usage: python3 permutation_test_pathA.py --n 50 [--mode independent|profile-block]
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import HAZARD_COEF_PATH, PANEL_PATH
from hazard_fit import fit_hazard_glm
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from simulate import simulate_qt_window
from extension_risk import score_extension_risk

DATA_DIR = HAZARD_COEF_PATH.parent
AXES = ["vintage", "coupon", "fico_bucket", "ltv_bucket"]


def _permute_panel(panel: pl.DataFrame, rng: np.random.Generator,
                   mode: str) -> pl.DataFrame:
    """Reassign stratum covariate profiles; outcome series stay in place."""
    pdf = panel.to_pandas()
    strata = pdf[AXES].drop_duplicates().reset_index(drop=True)
    m = len(strata)
    key_cols = strata.apply(lambda r: "|".join(map(str, r[AXES])), axis=1)
    old_key_to_row = {k: i for i, k in enumerate(key_cols)}

    if mode == "profile-block":
        pi = rng.permutation(m)
        new_profiles = {AXES[j]: strata[AXES[j]].to_numpy()[pi] for j in range(4)}
    else:  # independent
        new_profiles = {ax: strata[ax].to_numpy()[rng.permutation(m)]
                        for ax in AXES}

    row_keys = pdf[AXES].apply(lambda r: "|".join(map(str, r[AXES])), axis=1)
    idx = row_keys.map(old_key_to_row).to_numpy()
    out = pdf.copy()
    for ax in AXES:
        out[ax] = new_profiles[ax][idx]
    return pl.from_pandas(out)


def _fit_sim_score(panel: pl.DataFrame, empirical: pd.DataFrame,
                   coef_path: Path) -> dict:
    # Fit into the production coef path so simulate_qt_window (which reads
    # HAZARD_COEF_PATH for scales/burnout-adjust) uses THESE coefficients.
    # The caller backs up and restores the production file.
    diag = fit_hazard_glm(panel, output=coef_path)
    sim = simulate_qt_window(panel=panel)
    res = score_extension_risk(sim, empirical)
    c = diag["coefficients"]
    return {
        "beta_rate_gap": c.get("rate_gap_bps"),
        "beta_burnout": c.get("burnout_orth"),
        "beta_friction": c.get("friction"),
        "trapped_b": res["hazard_trapped_b"],
        "share_pct": res["share_explained_pct"],
        "cpr_r_lag0": res["cross_correlation"].get(0),
        "peak_lag": res["best_lag"],
        "n_strata": panel.select(AXES).unique().height,
    }


def _summ(real, perms, keys):
    s = {"n": len(perms), "real": real, "null": {}}
    for k in keys:
        v = np.array([p[k] for p in perms], float)
        r = real[k]
        n_ge = int((v >= r).sum()); n_le = int((v <= r).sum())
        s["null"][k] = {
            "mean": float(v.mean()), "std": float(v.std(ddof=1)),
            "min": float(v.min()), "max": float(v.max()),
            "real": r, "n_null_ge_real": n_ge,
            "p_exact_two_sided": (1 + 2 * min(n_ge, n_le)) / (len(v) + 1)
            if min(n_ge, n_le) * 2 <= len(v) else 1.0,
        }
    return s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=2024)
    ap.add_argument("--mode", choices=["independent", "profile-block"],
                    default="independent")
    args = ap.parse_args()

    results_csv = DATA_DIR / f"permutation_pathA_{args.mode}_results.csv"
    summary_json = DATA_DIR / f"permutation_pathA_{args.mode}_summary.json"
    tmp_coef = DATA_DIR / "_pathA_perm_coef.json"
    backup = DATA_DIR / "hazard_coefficients.backup.json"
    shutil.copy2(HAZARD_COEF_PATH, backup)

    keys = ["beta_rate_gap", "beta_burnout", "beta_friction",
            "trapped_b", "share_pct", "cpr_r_lag0"]
    try:
        panel = pl.read_parquet(PANEL_PATH)
        empirical = build_empirical_metrics(
            fetch_data(), soma_rolloff=fetch_soma_mbs_monthly())

        print("Real refit + sim + score …")
        real = _fit_sim_score(panel, empirical, HAZARD_COEF_PATH)
        real["replicate"] = "real"
        print(f"  real: β(gap)={real['beta_rate_gap']:+.3f} "
              f"β(burn)={real['beta_burnout']:+.3f} "
              f"trapped=${real['trapped_b']:.1f}B ({real['share_pct']:.1f}%) "
              f"r={real['cpr_r_lag0']:+.3f}")

        rows = [real]
        pd.DataFrame(rows).to_csv(results_csv, index=False)
        rng = np.random.default_rng(args.seed)
        perms = []
        for i in range(args.n):
            t0 = time.perf_counter()
            pp = _permute_panel(panel, rng, args.mode)
            r = _fit_sim_score(pp, empirical, HAZARD_COEF_PATH)
            r["replicate"] = i
            r["runtime_s"] = round(time.perf_counter() - t0, 1)
            perms.append(r); rows.append(r)
            pd.DataFrame(rows).to_csv(results_csv, index=False)
            print(f"  perm {i+1:>3}/{args.n} [{args.mode}]: "
                  f"β(gap)={r['beta_rate_gap']:+.3f} "
                  f"β(burn)={r['beta_burnout']:+.3f} "
                  f"trapped=${r['trapped_b']:.1f}B r={r['cpr_r_lag0']:+.3f} "
                  f"[{r['runtime_s']}s]")

        summary = _summ(real, perms, keys)
        summary["mode"] = args.mode
        json.dump(summary, open(summary_json, "w"), indent=2)

        print("\n" + "=" * 70)
        print(f" PATH A PERMUTATION [{args.mode}] — real vs null (n={args.n})")
        print("=" * 70)
        for k in keys:
            d = summary["null"][k]
            print(f" {k:<14}: real {d['real']:+.3f} | null {d['mean']:+.3f}"
                  f"±{d['std']:.3f} [{d['min']:+.3f},{d['max']:+.3f}] "
                  f"p={d['p_exact_two_sided']:.3f}")
        print(f"\n Results: {results_csv}")
    finally:
        shutil.copy2(backup, HAZARD_COEF_PATH)  # restore production coefficients
        for p in (tmp_coef, backup):
            if p.exists():
                p.unlink()
        # restore production simulation_results.parquet from the real panel
        simulate_qt_window(panel=pl.read_parquet(PANEL_PATH))
        print("Restored production hazard_coefficients.json + simulation.")


if __name__ == "__main__":
    main()
