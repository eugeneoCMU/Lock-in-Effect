#!/usr/bin/env python3
"""
Cross-design test: real Freddie structural covariates → ABM (§15 Fix 1).

Scope: ONLY structural covariates (per-loan coupon, loan age, original LTV)
transfer from the Freddie 75k sample to ABM households. Behavioral draws
(income, home value, mobility desire, transaction cost, patience) stay
synthetic with the same distributions and seed as production. FICO and
state are carried but have no analogue in the ABM's decision gates. This
is NOT "fully real" agents, and per Section VII.A it does not fully
resolve the data-source confound without the symmetric companion test
(hazard framework on a synthetic population).

PRE-REGISTERED FALSIFICATION CRITERION (fixed before results were run):
  - If the real-covariate ABM recovers >50% of the empirical benchmark,
    household choice was plausibly the real bottleneck all along — this
    meaningfully undercuts the paradigm claim in Section VII.
  - If it stays within the 10-35% band spanned by the synthetic ABM's
    specifications, the paradigm gap survives real data — corroborating
    Section VIII.A's confound-resolution claim.
  - 35-50% is ambiguous and must be reported as such.

Calibration variants (both run; (a) primary, (b) robustness — mirrors the
paper's treatment of the Danish friction-mismatch caveat):
  (a) recalibrated — mobility-scale anchor re-searched against the real
      population so the 4-5% CPR floor at 8% market rate still holds;
  (b) frozen — production synthetic calibration applied unchanged; any
      shift may partly reflect calibration mismatch, and the (a)-(b)
      discrepancy measures how much earlier ABM results depended on
      synthetic-population calibration.

Usage:
    python3 cross_design_test.py                 # both variants, cached surfaces
    python3 cross_design_test.py --rebuild       # force surface rebuild
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from freddie_population import (
    attach_freddie_covariates,
    load_freddie_structural_sample,
    population_summary,
)
from paths import ABM_DIR

PREREGISTRATION = {
    "undercuts_paradigm_above_pct": 50.0,
    "corroborates_band_pct": [10.0, 35.0],
    "registered_before_results": True,
}

RESULTS_JSON = ABM_DIR / "data" / "cross_design_results.json"


def _surface_csv(variant: str) -> Path:
    return ABM_DIR / f"abm_cpr_surface_freddie_{variant}.csv"


def _build_engine(mobility_scale: float, income: float, home_value: float,
                  loans: pd.DataFrame) -> abm.HousingMarketEngine:
    """Synthetic behavioral draws (production seed) + Freddie mortgages."""
    engine = abm.HousingMarketEngine(
        median_income=income,
        median_home_value=home_value,
        mobility_scale=mobility_scale,
    )
    attach_freddie_covariates(engine, loans)
    return engine


def calibrate_mobility_scale_freddie(
    income: float,
    home_value: float,
    loans: pd.DataFrame,
    target_low: float = 0.04,
    target_high: float = 0.05,
    max_iter: int = 30,
) -> float:
    """
    Variant (a): binary-search the mobility-desire scale so the REAL
    population hits the 4-5% involuntary-turnover CPR floor at 8% market
    rate — the same anchor semantics as calibrate_mobility_scale(), but
    evaluated on Freddie structural covariates.
    """
    target_mid = (target_low + target_high) / 2
    lo, hi = 1_000.0, 500_000.0
    scale = abm.MOBILITY_DESIRE_SCALE
    cpr = float("nan")
    for _ in range(max_iter):
        scale = (lo + hi) / 2
        engine = _build_engine(scale, income, home_value, loans)
        cpr = engine.cpr_at(0.08, "US")
        if target_low <= cpr <= target_high:
            break
        if cpr < target_mid:
            lo = scale
        else:
            hi = scale
    print(f"Recalibrated mobility scale (freddie pop) = {scale:,.0f} "
          f"(CPR floor at 8.0% US = {cpr:.2%})")
    return scale


def _population_sched_series(index: pd.DatetimeIndex,
                             loans: pd.DataFrame) -> pd.Series:
    """Scheduled amortization implied by the real population's WAC and age."""
    wac = float(np.average(loans["coupon"]))
    mean_age = float(loans["loan_age"].mean())
    origin = fed.QT_START - pd.DateOffset(months=int(round(mean_age)))
    return fed.scheduled_amortization_series(
        index, coupon=wac, origin=origin, term=360,
    )


def run_variant(
    variant: str,
    mobility_scale: float,
    income: float,
    home_value: float,
    loans: pd.DataFrame,
    df0: pd.DataFrame,
    soma_rolloff: pd.Series,
    rebuild: bool = False,
) -> dict:
    csv_path = _surface_csv(variant)
    if rebuild or not csv_path.exists():
        print(f"\n[{variant}] Building population-level 3D CPR surface …")
        engine = _build_engine(mobility_scale, income, home_value, loans)
        surf = engine.build_cpr_surface()
        surf.to_csv(csv_path, index=False)
        print(f"[{variant}] Surface saved to {csv_path}")
    else:
        print(f"\n[{variant}] Using cached surface {csv_path}")

    surface = fed.load_cpr_surface(csv_path)
    sched = _population_sched_series(df0.index, loans)
    df = fed.compute_metrics(
        df0.copy(),
        surface=surface,
        soma_rolloff=soma_rolloff,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
        sched_smm_override=sched,
    )
    m = fed.export_headline_metrics(df)
    qt = fed.qt_active_frame(df)
    xcorr = fed.cpr_cross_correlation(
        qt["Empirical_CPR_Pct"], qt["US_CPR_Pct"],
    )
    best_lag = max(xcorr, key=lambda k: abs(xcorr[k])) if xcorr else 0
    d = m["dollars_b"]
    return {
        "variant": variant,
        "mobility_scale": mobility_scale,
        "trapped_b": d["us_trapped"],
        "share_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "us_cpr_mean_pct": m["cpr_pct"]["us_abm"]["mean"],
        "empirical_cpr_mean_pct": m["cpr_pct"]["empirical"]["mean"],
        "cpr_r_lag0": xcorr.get(0),
        "cross_correlation": xcorr,
        "peak_lag": best_lag,
        "peak_lag_r": xcorr.get(best_lag),
    }


def classify(share_pct: float) -> str:
    hi = PREREGISTRATION["undercuts_paradigm_above_pct"]
    lo_band, hi_band = PREREGISTRATION["corroborates_band_pct"]
    if share_pct > hi:
        return "UNDERCUTS paradigm claim (>50% recovered by household choice)"
    if lo_band <= share_pct <= hi_band:
        return "CORROBORATES §VIII.A (within synthetic ABM's 10-35% band)"
    if hi_band < share_pct <= hi:
        return "AMBIGUOUS (35-50%): report as such"
    return "BELOW synthetic band (<10%): paradigm gap survives real data"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true",
                        help="Force surface rebuild for both variants")
    args = parser.parse_args()

    print("Loading Freddie structural sample …")
    loans = load_freddie_structural_sample(abm.N_HOUSEHOLDS)
    print(population_summary(loans))

    print("\nFetching macro data …")
    df0 = fed.fetch_data()
    soma_rolloff = fed.fetch_soma_mbs_monthly()
    income, home_value = abm.fetch_macro_from_fred()

    # Variant (b) frozen: the production synthetic calibration, unchanged.
    cohorts = fed.fetch_soma_mbs_cohorts()
    ref = abm.reference_cohort(cohorts)
    frozen_scale = abm.calibrate_mobility_scale(
        income, home_value,
        cohort_rate=ref["coupon"], cohort_months=ref["months_elapsed"],
    )

    # Variant (a) recalibrated against the real population's moments.
    recal_scale = calibrate_mobility_scale_freddie(income, home_value, loans)

    results = {}
    for variant, scale in (("recalibrated", recal_scale),
                           ("frozen", frozen_scale)):
        results[variant] = run_variant(
            variant, scale, income, home_value, loans,
            df0, soma_rolloff, rebuild=args.rebuild,
        )

    a, b = results["recalibrated"], results["frozen"]
    discrepancy_b = a["trapped_b"] - b["trapped_b"]

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope_note": (
            "Structural covariates only (coupon, loan age, orig LTV real; "
            "behavioral draws synthetic). Does NOT fully resolve the "
            "data-source confound without the symmetric companion test."
        ),
        "preregistration": PREREGISTRATION,
        "synthetic_control": {
            "run_tag": "run-2026-07-04-15yr-foldin",
            "trapped_b": 90.98,
            "share_pct": 11.90,
            "us_cpr_mean_pct": 11.68,
            "cpr_r_lag0": None,
        },
        "variants": results,
        "variant_discrepancy_b": discrepancy_b,
        "classification": {
            "recalibrated_primary": classify(a["share_pct"]),
            "frozen_robustness": classify(b["share_pct"]),
        },
    }

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w") as f:
        json.dump(report, f, indent=2,
                  default=lambda x: float(x) if hasattr(x, "item") else x)

    print("\n" + "=" * 68)
    print(" CROSS-DESIGN TEST — REAL FREDDIE COVARIATES → ABM")
    print("=" * 68)
    print(f" Benchmark (Step-3 revised): "
          f"${a['empirical_trapped_b']:.1f}B")
    for label, r in (("(a) recalibrated [primary]", a),
                     ("(b) frozen calibration [robustness]", b)):
        print(f"\n {label}:")
        print(f"   mobility_scale       {r['mobility_scale']:,.0f}")
        print(f"   trapped              ${r['trapped_b']:.1f}B "
              f"({r['share_pct']:.1f}% of benchmark)")
        print(f"   mean CPR             {r['us_cpr_mean_pct']:.2f}% "
              f"(empirical {r['empirical_cpr_mean_pct']:.2f}%)")
        print(f"   CPR r (lag 0)        {r['cpr_r_lag0']:+.3f}")
        print(f"   peak lag             {r['peak_lag']} "
              f"(r={r['peak_lag_r']:+.3f})")
        print(f"   → {classify(r['share_pct'])}")
    print(f"\n (a)−(b) discrepancy: ${discrepancy_b:+.1f}B "
          f"(calibration-dependence diagnostic)")
    print(f"\n Synthetic control (unchanged code path): "
          f"$91.0B / 11.9%")
    print(f" Report saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
