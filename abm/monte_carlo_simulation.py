"""
Monte Carlo Simulation of Trapped Liquidity
===========================================
Tests whether the headline U.S. trapped-liquidity result is robust to
the Agent-Based Model's random 10,000-agent population draw.

For each of N_RUNS seeds the full pipeline is re-run:
    re-seed RNG -> rebuild ABM population -> build CPR surface
    -> macro compute_metrics -> aggregate U.S. trapped liquidity

The 50 resulting values form a distribution. We report the mean, standard
deviation, and 95% confidence interval of the mean, and plot a histogram
against the empirical SOMA-based shortfall (computed at runtime from actual
roll-off vs the phased QT cap).

Run:
    python3 monte_carlo_simulation.py
"""

import argparse
import random
import time

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from paths import MONTE_CARLO_HISTOGRAM_PNG, MONTE_CARLO_RESULTS_CSV

RESULTS_CSV = MONTE_CARLO_RESULTS_CSV
HISTOGRAM_PNG = MONTE_CARLO_HISTOGRAM_PNG

N_RUNS = 50


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def surface_df_to_surfaces(surf: pd.DataFrame):
    """
    Convert the ABM surface DataFrame into the format fed.compute_metrics
    expects: a dict keyed by (coupon, term_months) when Cohort_Coupon is
    present (matching fed.load_cpr_surface), else a single 2D/3D tuple.
    """
    if "Cohort_Coupon" in surf.columns:
        if "Cohort_Term" not in surf.columns:
            surf = surf.copy()
            surf["Cohort_Term"] = fed.PORTFOLIO_TERM
        surfaces = {}
        for (coupon, term), grp in surf.groupby(["Cohort_Coupon", "Cohort_Term"]):
            slab = grp.drop(columns=["Cohort_Coupon", "Cohort_Term"])
            key = (fed._round_coupon(coupon), int(term))
            surfaces[key] = fed._surface_tuple_from_dataframe(slab)
        return surfaces
    return fed._surface_tuple_from_dataframe(surf)


def restrict_grids_to_observed(fred_df: pd.DataFrame) -> None:
    """
    Shrink the ABM's surface grids to the contiguous sub-ranges that bracket
    every coordinate compute_metrics will query for this macro frame.

    Correctness: interp_cpr_surface uses nested np.interp over each grid
    array. For any query q, np.interp only reads the two nodes bracketing q,
    so a CONTIGUOUS subset of the original grid that still brackets all
    queries returns bit-identical interpolants. This is a pure speedup
    (~4-5x per seed), not an approximation. Asserts coverage before trimming.
    """
    macro = fed.calculate_dynamic_friction(fred_df.copy())
    macro["Rate_6M_Change"] = macro["MORTGAGE30US"].diff(6).fillna(0.0) / 100.0

    def contiguous_subrange(grid: np.ndarray, lo: float, hi: float) -> np.ndarray:
        grid = np.sort(np.asarray(grid))
        # Queries beyond the original grid clamp to its end nodes; keeping the
        # original boundary node preserves that clamping exactly.
        lo, hi = max(lo, float(grid[0])), min(hi, float(grid[-1]))
        i0 = max(int(np.searchsorted(grid, lo, side="right")) - 1, 0)
        i1 = min(int(np.searchsorted(grid, hi, side="left")) + 1, len(grid))
        sub = grid[i0:i1]
        assert sub[0] <= lo and sub[-1] >= hi, "subgrid must bracket queries"
        return sub

    rates = macro["MORTGAGE30US"] / 100.0
    abm.RATE_GRID = contiguous_subrange(
        abm.RATE_GRID, float(rates.min()), float(rates.max()))
    abm.FRICTION_GRID = contiguous_subrange(
        abm.FRICTION_GRID,
        float(macro["Dynamic_Friction"].min()),
        float(macro["Dynamic_Friction"].max()))
    abm.RATE_VELOCITY_GRID = contiguous_subrange(
        abm.RATE_VELOCITY_GRID,
        float(macro["Rate_6M_Change"].min()),
        float(macro["Rate_6M_Change"].max()))
    print(f"Grids restricted to observed ranges: "
          f"{len(abm.RATE_GRID)} rates x {len(abm.FRICTION_GRID)} frictions "
          f"x {len(abm.RATE_VELOCITY_GRID)} velocities "
          f"(interpolation-identical to the full grid)")


def us_trapped(metrics: pd.DataFrame) -> float:
    """Aggregate U.S. trapped liquidity over the active QT window."""
    qt = fed.qt_active_frame(metrics)
    return float(qt["US_Missed_Rolloff_Billions"].sum())


def run_single_iteration(seed: int, fred_df: pd.DataFrame,
                         mobility_scale: float,
                         income: float, home_value: float,
                         cohorts: list,
                         soma_rolloff=None) -> float:
    """One Monte Carlo draw: re-seed ABM, rebuild CPR surface, score trapped."""
    np.random.seed(seed)
    random.seed(seed)

    engine = abm.HousingMarketEngine(
        seed=seed,
        median_income=income,
        median_home_value=home_value,
        mobility_scale=mobility_scale,
    )
    surf_df = abm.build_multi_cohort_surfaces(engine, cohorts)
    surface = surface_df_to_surfaces(surf_df)

    metrics = fed.compute_metrics(
        fred_df, surface=surface, soma_rolloff=soma_rolloff,
        cohorts=cohorts,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
    )
    return us_trapped(metrics)


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
def empirical_trapped(metrics: pd.DataFrame) -> float:
    """Actual roll-off vs QT cap — independent of ABM parameters."""
    qt = fed.qt_active_frame(metrics)
    return float(qt["Extension_Delta_Billions"].sum())


def plot_histogram(values: np.ndarray, mean: float,
                   soma_target: float,
                   save_path: str = HISTOGRAM_PNG):
    """Histogram of trapped-liquidity draws vs. the MC mean and SOMA target."""
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.hist(values, bins=15, color="#4c72b0", alpha=0.75,
            edgecolor="white", label=f"MC draws (N={len(values)})")

    ax.axvline(mean, color="red", linestyle="--", linewidth=2.5,
               label=f"Monte Carlo mean (${mean:,.1f}B)")
    ax.axvline(soma_target, color="orange", linestyle="-", linewidth=2.5,
               label=f"SOMA empirical shortfall (${soma_target:,.1f}B)")

    ax.set_xlabel("U.S. Trapped Liquidity ($B)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title(
        "Monte Carlo Distribution of U.S. Trapped Liquidity\n"
        f"{len(values)} ABM population draws vs. SOMA-based empirical shortfall",
        fontsize=14, fontweight="bold",
    )
    ax.legend(fontsize=11, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Histogram saved to {save_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs=2, type=int, default=[0, N_RUNS],
                        metavar=("START", "STOP"),
                        help="half-open seed range for this chunk")
    parser.add_argument("--out", default=None,
                        help="chunk CSV path (default: production CSV)")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    seed_start, seed_stop = args.seeds
    out_csv = args.out or RESULTS_CSV

    print("Fetching empirical medians and FRED data once …")
    income, home_value = abm.fetch_macro_from_fred()
    fred_df = fed.fetch_data()

    print("Fetching SOMA MBS roll-off from NY Fed …")
    soma_rolloff = fed.fetch_soma_mbs_monthly()

    print("Fetching SOMA MBS coupon cohorts once …")
    cohorts = fed.fetch_soma_mbs_cohorts()

    restrict_grids_to_observed(fred_df)

    ref = abm.reference_cohort(cohorts)
    print("Calibrating mobility desire once (reused across all seeds) …")
    mobility_scale = abm.calibrate_mobility_scale(
        income, home_value,
        cohort_rate=ref["coupon"],
        cohort_months=ref["months_elapsed"],
    )
    abm_params_base = {
        "mobility_scale": mobility_scale,
        "median_income": income,
        "median_home_value": home_value,
    }

    baseline_metrics = fed.compute_metrics(
        fred_df, soma_rolloff=soma_rolloff, cohorts=cohorts,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
        abm_params=abm_params_base,
    )
    soma_target = empirical_trapped(baseline_metrics)
    print(f"Empirical trapped liquidity (SOMA): ${soma_target:,.1f}B")

    n_chunk = seed_stop - seed_start
    print(f"\nRunning seeds [{seed_start}, {seed_stop}) "
          f"(CPR surface rebuild per seed) …")
    rows = []
    t0 = time.perf_counter()
    for i in range(seed_start, seed_stop):
        iter_t0 = time.perf_counter()
        trapped = run_single_iteration(i, fred_df, mobility_scale,
                                       income, home_value,
                                       cohorts=cohorts,
                                       soma_rolloff=soma_rolloff)
        iter_elapsed = time.perf_counter() - iter_t0
        rows.append({"seed": i, "trapped_us_b": trapped,
                       "elapsed_sec": iter_elapsed})
        pd.DataFrame(rows).to_csv(out_csv, index=False)  # checkpoint
        print(f"  [{i - seed_start + 1:>2}/{n_chunk}] seed={i:>2}  "
              f"U.S. trapped = ${trapped:,.1f}B  "
              f"({iter_elapsed:.1f}s)")
    total_elapsed = time.perf_counter() - t0
    print(f"\nChunk runtime: {total_elapsed/60:.1f} min "
          f"({total_elapsed/max(n_chunk,1):.1f}s per seed avg)")

    results = pd.DataFrame(rows)
    results.to_csv(out_csv, index=False)
    print(f"\nResults saved to {out_csv}")
    if args.no_plot or n_chunk < N_RUNS:
        return

    values = results["trapped_us_b"].to_numpy()
    mean = float(values.mean())
    std = float(values.std(ddof=1))
    sem = std / np.sqrt(len(values))
    ci_low, ci_high = mean - 1.96 * sem, mean + 1.96 * sem

    print("\n" + "=" * 55)
    print(f" Monte Carlo (N={N_RUNS}) — U.S. Trapped Liquidity")
    print("=" * 55)
    print(f"  Mean:   ${mean:,.1f}B")
    print(f"  Std:    ${std:,.1f}B")
    print(f"  95% CI: [${ci_low:,.1f}B, ${ci_high:,.1f}B]")
    print(f"  SOMA empirical shortfall: ${soma_target:,.1f}B")
    print("=" * 55 + "\n")

    plot_histogram(values, mean, soma_target)


if __name__ == "__main__":
    main()
