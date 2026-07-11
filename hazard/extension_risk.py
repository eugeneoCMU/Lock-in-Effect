"""
Extension-risk scoring: hazard simulation vs $764.7B empirical benchmark.

Run order (empirical fit):
  ingest → hazard_fit → markov → simulate → extension_risk

Run order (literature microsim):
  loan_sample → microsim_engine → extension_risk --mode literature
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import (
    CPR_DIAGNOSTIC_PNG,
    EMPIRICAL_TRAPPED_B,
    EXTENSION_RISK_PNG,
    HAZARD_COEF_PATH,
    LOAN_SAMPLE_PATH,
    MICROSIM_RESULTS_PATH,
    PANEL_PATH,
    QT_START,
    SIM_RESULTS_PATH,
)
from macro import (
    assert_qt_window_only,
    build_empirical_metrics,
    cpr_cross_correlation,
    cpr_goodness_of_fit,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
)


def score_extension_risk(
    sim: pd.DataFrame,
    empirical_df: pd.DataFrame,
) -> dict:
    """Compare hazard-simulated roll-off to empirical QT extension deltas."""
    qt_emp = qt_active_frame(empirical_df)
    assert_qt_window_only(qt_emp.index)
    qt_sim = sim.reindex(qt_emp.index).dropna(subset=["simulated_rolloff_b"])
    assert_qt_window_only(qt_sim.index)
    qt_target = qt_emp["QT_Target_Billions"]

    emp_trapped = float(qt_emp["Extension_Delta_Billions"].sum())
    sim_trapped = float(
        (qt_sim["simulated_rolloff_b"] - qt_target).sum()
    )
    share = sim_trapped / emp_trapped * 100 if emp_trapped else np.nan

    gof = cpr_goodness_of_fit(
        qt_emp["Empirical_CPR_Pct"],
        qt_sim["hazard_cpr_pct"],
    )
    xcorr = cpr_cross_correlation(
        qt_emp["Empirical_CPR_Pct"],
        qt_sim["hazard_cpr_pct"],
    )
    best_lag = max(xcorr, key=lambda k: abs(xcorr[k])) if xcorr else 0
    peak_lag_r = xcorr.get(best_lag, 0.0) if xcorr else 0.0
    # Direction verified against synthetic data (v15 round, re-verified round
    # 8): under macro.cpr_cross_correlation's pairing, a NEGATIVE peak lag
    # means the simulated path TRAILS the empirical path (empirical moves
    # first). The settlement-delay reading printed here through round 7 was
    # inverted and is retracted in the manuscript (Appendix A erratum).
    lag_interp = (
        "Negative lag = simulated CPR trails SOMA empirical CPR "
        "(empirical moves first; direction verified on synthetic data). "
        "No settlement interpretation is attached (manuscript §V.C)."
    )

    results = {
        "empirical_trapped_b": emp_trapped,
        "hazard_trapped_b": sim_trapped,
        "share_explained_pct": share,
        "benchmark_b": EMPIRICAL_TRAPPED_B,
        "cpr_gof_raw": gof["raw"],
        "cpr_gof_smoothed": gof["smoothed"],
        "cross_correlation": xcorr,
        "best_lag": best_lag,
        "peak_lag_r": peak_lag_r,
        "lag_interpretation": lag_interp,
        "mode": "cohort_empirical",
    }
    return results


def plot_dashboard(
    sim: pd.DataFrame,
    empirical_df: pd.DataFrame,
    results: dict,
    save_path: Path = EXTENSION_RISK_PNG,
):
    fig, axes = plt.subplots(2, 1, figsize=(12, 9))

    qt_emp = qt_active_frame(empirical_df)
    qt_sim = sim.reindex(qt_emp.index)

    ax = axes[0]
    ax.bar(qt_emp.index, qt_emp["Extension_Delta_Billions"], alpha=0.5,
           label="Empirical extension delta", color="#888")
    miss = qt_emp["Extension_Delta_Billions"] - (
        qt_sim["simulated_rolloff_b"] - qt_emp["QT_Target_Billions"]
    )
    ax.bar(qt_emp.index, miss, alpha=0.7, label="Hazard trapped (missed)", color="#1f77b4")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("$B")
    mode = results.get("mode", "cohort")
    ax.set_title(
        f"Hazard Extension Risk ({mode}) — trapped {results['hazard_trapped_b']:.1f}B "
        f"({results['share_explained_pct']:.1f}% of {results['empirical_trapped_b']:.1f}B)"
    )
    ax.legend()

    ax2 = axes[1]
    ax2.plot(qt_emp.index, qt_emp["Empirical_CPR_Pct"], "o-", label="Empirical CPR", ms=4)
    ax2.plot(qt_sim.index, qt_sim["hazard_cpr_pct"], "s-", label="Hazard CPR", ms=4)
    ax2.set_ylabel("CPR %")
    ax2.set_title(
        f"CPR fit: R²={results['cpr_gof_raw']['r2']:.3f}, "
        f"r={results['cpr_gof_raw']['corr']:.3f}"
    )
    ax2.legend()
    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Dashboard saved to {save_path}")


def plot_cpr_diagnostic(
    sim: pd.DataFrame,
    empirical_df: pd.DataFrame,
    save_path: Path = CPR_DIAGNOSTIC_PNG,
):
    qt_emp = qt_active_frame(empirical_df)
    qt_sim = sim.reindex(qt_emp.index)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(qt_emp["Empirical_CPR_Pct"], qt_sim["hazard_cpr_pct"], alpha=0.7)
    lim = max(qt_emp["Empirical_CPR_Pct"].max(), qt_sim["hazard_cpr_pct"].max()) * 1.1
    ax.plot([0, lim], [0, lim], "k--", alpha=0.4)
    ax.set_xlabel("Empirical CPR %")
    ax.set_ylabel("Hazard CPR %")
    ax.set_title("Hazard vs Empirical CPR (QT window)")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"CPR diagnostic saved to {save_path}")


def print_summary(results: dict):
    print("\n" + "=" * 60)
    print(" HAZARD EXTENSION RISK — SUMMARY")
    print("=" * 60)
    print(f"  Mode:                                 {results.get('mode', 'cohort')}")
    print(f"  Empirical trapped (SOMA, active QT):  ${results['empirical_trapped_b']:.1f}B")
    print(f"  Hazard model trapped:                 ${results['hazard_trapped_b']:.1f}B")
    print(f"  Share explained:                      {results['share_explained_pct']:.1f}%")
    print(f"  ABM benchmark share (for comparison):   13.2%")
    print("-" * 60)
    g = results["cpr_gof_raw"]
    lag0_r = g["corr"]
    if results.get("cross_correlation"):
        bl = results["best_lag"]
        peak_r = results.get("peak_lag_r", results["cross_correlation"].get(bl, 0))
        print(
            f"  CPR r (lag 0): {lag0_r:+.3f}   |  "
            f"Peak lag {bl}: r={peak_r:+.3f}"
        )
        print(f"  CPR R²: {g['r2']:.3f}   RMSE: {g['rmse']:.2f}pp")
        print(f"  Settlement note:  {results.get('lag_interpretation', '')}")
    else:
        print(f"  CPR R²:   {g['r2']:.3f}   RMSE: {g['rmse']:.2f}pp   r (lag 0): {lag0_r:.3f}")
    print("=" * 60)

    if results.get("mode") != "literature_microsim" and HAZARD_COEF_PATH.exists():
        with open(HAZARD_COEF_PATH) as f:
            coef_data = json.load(f)
        c = coef_data.get("coefficients", {})
        print("\nPre-registered coefficient signs:")
        rate_key = "rate_gap_bps" if "rate_gap_bps" in c else "rate_gap"
        for name, expected in [(rate_key, ">0"), ("burnout_orth", "<0"), ("friction", "<0")]:
            val = c.get(name, np.nan)
            ok = (val > 0) if expected == ">0" else (val < 0)
            print(f"  β({name}) = {val:+.4f}  expected {expected}  {'OK' if ok else 'FAIL'}")


def run_empirical_pipeline(force_rebuild: bool = False, years: list[int] | None = None):
    from ingest import load_or_build_panel
    from hazard_fit import fit_hazard_glm
    from markov import estimate_transitions_from_panel
    from simulate import simulate_qt_window

    print("Step 1: Ingest …")
    panel = load_or_build_panel(force_rebuild=force_rebuild, years=years)

    print("\nStep 2: Fit hazard GLM …")
    fit_hazard_glm(panel)

    print("\nStep 3: Estimate Markov transitions …")
    estimate_transitions_from_panel(panel)

    print("\nStep 4: Simulate QT window …")
    sim = simulate_qt_window(panel)
    return sim


def run_literature_microsim(force_rebuild: bool = False):
    from loan_sample import load_or_build_loan_sample
    from microsim_engine import run_qt_microsim

    print("Step 1: Build loan sample …")
    loans = load_or_build_loan_sample(force_rebuild=force_rebuild)

    if not force_rebuild and MICROSIM_RESULTS_PATH.exists():
        print("\nStep 2: Using cached microsim results …")
        return pd.read_parquet(MICROSIM_RESULTS_PATH)

    print("\nStep 2: Run literature microsim (US + Danish) …")
    paths = run_qt_microsim(loan_sample=loans)
    return paths["US"]


ROTHSTEIN_BAND_PCT = (5.5, 6.5, 7.7)


def _band_cache_path(p_q_shock_pct: float) -> Path:
    """Central 6.5% run keeps the standard cache; band edges get their own."""
    if abs(p_q_shock_pct - 6.5) < 1e-9:
        return MICROSIM_RESULTS_PATH
    return MICROSIM_RESULTS_PATH.with_name(
        f"microsim_results_pq{p_q_shock_pct:.1f}.parquet"
    )


def run_literature_band(
    empirical: pd.DataFrame,
    band: tuple[float, ...] = ROTHSTEIN_BAND_PCT,
    force_rebuild: bool = False,
) -> dict:
    """
    Re-run the full literature microsim at each Rothstein band point and
    score each against the same empirical benchmark.  Same loan sample and
    RNG seeds throughout — only β₁ varies.
    """
    import time

    from loan_sample import load_or_build_loan_sample
    from microsim_engine import run_qt_microsim

    loans = load_or_build_loan_sample(force_rebuild=force_rebuild)

    band_results = {}
    for pq in band:
        cache = _band_cache_path(pq)
        t0 = time.perf_counter()
        if not force_rebuild and cache.exists():
            print(f"\n— P_q shock {pq:.1f}%: cached ({cache.name})")
            sim = pd.read_parquet(cache)
        else:
            print(f"\n— P_q shock {pq:.1f}%: running microsim …")
            run_qt_microsim(loan_sample=loans, output=cache, p_q_shock_pct=pq)
            sim = pd.read_parquet(cache)
        runtime_s = time.perf_counter() - t0

        r = score_extension_risk(sim, empirical)
        band_results[f"{pq:.1f}"] = {
            "p_q_shock_pct": pq,
            "trapped_b": r["hazard_trapped_b"],
            "share_pct": r["share_explained_pct"],
            "cpr_r_lag0": r["cross_correlation"].get(0),
            "best_lag": r["best_lag"],
            "peak_lag_r": r["peak_lag_r"],
            "runtime_s": round(runtime_s, 1),
        }
        print(
            f"  trapped ${r['hazard_trapped_b']:.1f}B "
            f"({r['share_explained_pct']:.1f}%)  "
            f"r(lag0)={r['cross_correlation'].get(0, float('nan')):+.3f}  "
            f"peak lag {r['best_lag']} r={r['peak_lag_r']:+.3f}  "
            f"[{runtime_s:.1f}s]"
        )

    vals = list(band_results.values())
    lo = min(vals, key=lambda v: v["trapped_b"])
    hi = max(vals, key=lambda v: v["trapped_b"])
    interval = (
        f"${lo['trapped_b']:.0f}B – ${hi['trapped_b']:.0f}B "
        f"({lo['share_pct']:.1f}%–{hi['share_pct']:.1f}% of benchmark)"
    )
    peak_lags = sorted({v["best_lag"] for v in vals})
    payload = {
        "mode": "literature_microsim_band",
        "band_pct": list(band),
        "empirical_trapped_b": float(
            qt_active_frame(empirical)["Extension_Delta_Billions"].sum()
        ),
        "benchmark_b": EMPIRICAL_TRAPPED_B,
        "results": band_results,
        "interval": interval,
        "peak_lag_stability": {
            "lags_observed": peak_lags,
            "stable": len(peak_lags) == 1,
        },
    }

    out = Path(__file__).parent / "data" / "extension_risk_band_literature.json"
    with open(out, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x)
    print(f"\nBand results saved to {out}")
    print(f"Sensitivity interval (Table 1 / §V.C): {interval}")
    if len(peak_lags) == 1:
        print(f"Peak lag stable at {peak_lags[0]} across the band.")
    else:
        print(f"WARNING: peak lag moves across the band: {peak_lags} — report this.")
    return payload


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Hazard extension-risk scoring")
    parser.add_argument(
        "--mode",
        choices=["empirical", "literature"],
        default="empirical",
        help="empirical: cohort GLM fit; literature: agent microsim",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild panel/loan sample from Freddie raw (ignore cache)",
    )
    parser.add_argument(
        "--band",
        action="store_true",
        help="Literature mode only: run the Rothstein sensitivity band "
             "(5.5%%, 6.5%%, 7.7%% quarterly mobility decline) and report "
             "the trapped-liquidity interval",
    )
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=None,
        help="Limit ingest to vintage years (e.g. --years 2020 2021)",
    )
    args = parser.parse_args()

    if args.rebuild:
        if args.mode == "literature":
            cache_paths = (LOAN_SAMPLE_PATH, MICROSIM_RESULTS_PATH)
        else:
            cache_paths = (PANEL_PATH, LOAN_SAMPLE_PATH, SIM_RESULTS_PATH, MICROSIM_RESULTS_PATH)
        for p in cache_paths:
            if p.exists():
                p.unlink()
                print(f"Removed cache: {p}")

    if args.band:
        if args.mode != "literature":
            parser.error("--band requires --mode literature")
        print("Scoring empirical benchmark …")
        macro = fetch_data()
        soma = fetch_soma_mbs_monthly()
        empirical = build_empirical_metrics(macro, soma_rolloff=soma)
        run_literature_band(empirical, force_rebuild=args.rebuild)
        return

    if args.mode == "literature":
        sim = run_literature_microsim(force_rebuild=args.rebuild)
    else:
        sim = run_empirical_pipeline(force_rebuild=args.rebuild, years=args.years)
        if SIM_RESULTS_PATH.exists():
            sim = pd.read_parquet(SIM_RESULTS_PATH)

    print("\nScoring vs empirical …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    if args.mode == "literature" and MICROSIM_RESULTS_PATH.exists():
        sim = pd.read_parquet(MICROSIM_RESULTS_PATH)

    results = score_extension_risk(sim, empirical)
    results["mode"] = "literature_microsim" if args.mode == "literature" else "cohort_empirical"
    print_summary(results)
    plot_dashboard(sim, empirical, results)
    plot_cpr_diagnostic(sim, empirical)

    out_dir = Path(__file__).parent / "data"
    payload = {k: v for k, v in results.items()
               if k not in ("cpr_gof_raw", "cpr_gof_smoothed")}
    mode_slug = results.get("mode", "cohort")
    for name in (f"extension_risk_results_{mode_slug}.json", "extension_risk_results.json"):
        out = out_dir / name
        with open(out, "w") as f:
            json.dump(payload, f, indent=2,
                      default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x)
        print(f"Results saved to {out}")


if __name__ == "__main__":
    main()
