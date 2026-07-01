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

import random

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
N_RUNS = 50

RESULTS_CSV = "monte_carlo_results.csv"
HISTOGRAM_PNG = "monte_carlo_trapped_liquidity.png"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def surface_df_to_tuple(surf: pd.DataFrame):
    """
    Convert the ABM's surface DataFrame (decimals) into the tuple format that
    fed.compute_metrics expects from load_cpr_surface: rates in percent,
    frictions in decimal, CPR grids in percent.
    """
    rates = np.sort(surf["Market_Rate"].unique())
    frictions = np.sort(surf["Friction"].unique())
    piv_us = surf.pivot(index="Market_Rate", columns="Friction",
                        values="CPR_US").reindex(index=rates, columns=frictions)
    piv_dk = surf.pivot(index="Market_Rate", columns="Friction",
                        values="CPR_Danish").reindex(index=rates,
                                                     columns=frictions)
    return (
        rates * 100.0,
        frictions,
        piv_us.to_numpy() * 100.0,
        piv_dk.to_numpy() * 100.0,
    )


def us_trapped(metrics: pd.DataFrame) -> float:
    """Aggregate U.S. trapped liquidity over the QT window (mirrors print_summary)."""
    qt = metrics.loc[metrics.index >= fed.QT_START].dropna(
        subset=["Extension_Delta_Billions"]
    )
    return float(qt["US_Missed_Rolloff_Billions"].sum())


def run_single_iteration(seed: int, fred_df: pd.DataFrame,
                         mobility_scale: float,
                         income: float, home_value: float,
                         soma_rolloff=None) -> float:
    """One Monte Carlo draw: re-seed, rebuild population + surface, score it."""
    np.random.seed(seed)
    random.seed(seed)

    engine = abm.HousingMarketEngine(
        seed=seed,
        median_income=income,
        median_home_value=home_value,
        mobility_scale=mobility_scale,
    )
    surface = surface_df_to_tuple(engine.build_cpr_surface())
    metrics = fed.compute_metrics(fred_df, surface=surface,
                                  soma_rolloff=soma_rolloff)
    return us_trapped(metrics)


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
def empirical_trapped(metrics: pd.DataFrame) -> float:
    """Actual roll-off vs QT cap — independent of ABM parameters."""
    qt = metrics.loc[metrics.index >= fed.QT_START].dropna(
        subset=["Extension_Delta_Billions"]
    )
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
    print("Fetching empirical medians and FRED data once …")
    income, home_value = abm.fetch_macro_from_fred()
    fred_df = fed.fetch_data()

    print("Fetching SOMA MBS roll-off from NY Fed …")
    soma_rolloff = fed.fetch_soma_mbs_monthly()

    # Compute the empirical benchmark at runtime (actual roll-off vs QT cap)
    baseline_metrics = fed.compute_metrics(fred_df, soma_rolloff=soma_rolloff)
    soma_target = empirical_trapped(baseline_metrics)
    print(f"Empirical trapped liquidity (SOMA): ${soma_target:,.1f}B")

    print("Calibrating mobility desire once (reused across all seeds) …")
    mobility_scale = abm.calibrate_mobility_scale(income, home_value)

    print(f"\nRunning {N_RUNS} Monte Carlo iterations "
          f"(full CPR-surface rebuild each) …")
    rows = []
    for i in range(N_RUNS):
        trapped = run_single_iteration(i, fred_df, mobility_scale,
                                       income, home_value,
                                       soma_rolloff=soma_rolloff)
        rows.append({"seed": i, "trapped_us_b": trapped})
        print(f"  [{i + 1:>2}/{N_RUNS}] seed={i:>2}  "
              f"U.S. trapped = ${trapped:,.1f}B")

    results = pd.DataFrame(rows)
    results.to_csv(RESULTS_CSV, index=False)
    print(f"\nResults saved to {RESULTS_CSV}")

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
