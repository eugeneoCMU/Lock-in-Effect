"""
Friction Parameter Sensitivity Analysis
========================================
Sweeps the three Dynamic Macroeconomic Friction parameters and measures how
the headline trapped-liquidity and institutional-gap figures respond:

  * BASE_FRICTION        -- the 7% baseline transaction cost
  * SEARCH_PENALTY_CAP   -- max inventory-driven add-on (default +200 bps)
  * SENTIMENT_PENALTY_CAP-- max fear-driven add-on (default +150 bps)

For each of the 5 x 5 x 5 = 125 scenarios the macro metric pipeline is re-run
on the already-fetched FRED data (no extra API calls, one shared CPR surface),
and the aggregate trapped-liquidity results are recorded.

Run:
    python3 sensitivity_analysis.py
"""

import itertools

import numpy as np
import pandas as pd

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from paths import SENSITIVITY_RESULTS_CSV

# ---------------------------------------------------------------------------
# Sweep grid (baseline values are the current module constants)
# ---------------------------------------------------------------------------
BASE_GRID = [0.05, 0.06, 0.07, 0.08, 0.09]
SEARCH_CAP_GRID = [0.00, 0.01, 0.02, 0.03, 0.04]
SENTIMENT_CAP_GRID = [0.000, 0.0075, 0.015, 0.0225, 0.030]

BASELINE = (fed.BASE_FRICTION, fed.SEARCH_PENALTY_CAP, fed.SENTIMENT_PENALTY_CAP)

RESULTS_CSV = SENSITIVITY_RESULTS_CSV


def aggregate_trapped(df: pd.DataFrame) -> tuple:
    """
    Total ABM-calibrated trapped liquidity for each system over the active QT
    window, and the institutional gap.
    """
    qt_df = fed.qt_active_frame(df)
    trapped_us = qt_df["US_Missed_Rolloff_Billions"].sum()
    trapped_dk = qt_df["Danish_Missed_Rolloff_Billions"].sum()
    return trapped_us, trapped_dk, trapped_us - trapped_dk


def empirical_trapped(df: pd.DataFrame) -> float:
    """Actual SOMA/WSHOMCB roll-off vs QT cap — independent of the ABM."""
    qt_df = fed.qt_active_frame(df)
    return float(qt_df["Extension_Delta_Billions"].sum())


def run_single_scenario(df: pd.DataFrame, surface,
                        base: float, search_cap: float,
                        sentiment_cap: float,
                        soma_rolloff=None,
                        empirical_trapped: float = 0.0,
                        cohorts=None,
                        abm_params=None) -> dict:
    """Run the metric pipeline for one parameter triple; return a result row."""
    metrics = fed.compute_metrics(
        df,
        base_friction=base,
        search_penalty_cap=search_cap,
        sentiment_penalty_cap=sentiment_cap,
        surface=surface,
        soma_rolloff=soma_rolloff,
        cohorts=cohorts,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
        abm_params=abm_params,
    )
    trapped_us, trapped_dk, gap = aggregate_trapped(metrics)
    fric = metrics["Dynamic_Friction"] * 100

    qt_df = metrics.loc[metrics.index >= fed.QT_START].dropna(
        subset=["Extension_Delta_Billions"]
    )
    qt_df = qt_df.loc[fed.qt_active_mask(qt_df.index)]
    gof = fed.cpr_goodness_of_fit(
        qt_df["Empirical_CPR_Pct"], qt_df["US_CPR_Pct"]
    )

    vs_emp = trapped_us - empirical_trapped if empirical_trapped else np.nan
    share = trapped_us / empirical_trapped * 100 if empirical_trapped else np.nan

    return {
        "Base_Pct": base * 100,
        "Search_Cap_bps": search_cap * 10_000,
        "Sentiment_Cap_bps": sentiment_cap * 10_000,
        "Friction_Min_Pct": fric.min(),
        "Friction_Mean_Pct": fric.mean(),
        "Friction_Max_Pct": fric.max(),
        "Trapped_US_B": trapped_us,
        "Trapped_DK_B": trapped_dk,
        "Gap_B": gap,
        "Vs_Empirical_B": vs_emp,
        "Share_Explained_Pct": share,
        "CPR_R2": gof["raw"]["r2"],
        "CPR_RMSE": gof["raw"]["rmse"],
        "CPR_R2_Smooth": gof["smoothed"]["r2"],
        "CPR_RMSE_Smooth": gof["smoothed"]["rmse"],
    }


def print_table(results: pd.DataFrame):
    """Pretty-print the full sweep, flagging the baseline scenario."""
    header = (
        f"{'Base%':>6} {'Search':>7} {'Sent':>6} "
        f"{'TrapUS$B':>10} {'Share%':>7} {'R²':>6} {'RMSE':>6} "
        f"{'TrapDK$B':>10} {'Gap$B':>10}"
    )
    print("\n" + "=" * len(header))
    print(" FRICTION PARAMETER SENSITIVITY  (sorted by U.S. trapped liquidity)")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    base_b, base_s, base_sent = BASELINE
    for _, r in results.iterrows():
        is_baseline = (
            np.isclose(r["Base_Pct"], base_b * 100)
            and np.isclose(r["Search_Cap_bps"], base_s * 10_000)
            and np.isclose(r["Sentiment_Cap_bps"], base_sent * 10_000)
        )
        marker = "  <<< BASELINE" if is_baseline else ""
        share = r.get("Share_Explained_Pct", np.nan)
        r2 = r.get("CPR_R2", np.nan)
        rmse = r.get("CPR_RMSE", np.nan)
        print(
            f"{r['Base_Pct']:>6.1f} {r['Search_Cap_bps']:>7.0f} "
            f"{r['Sentiment_Cap_bps']:>6.0f} "
            f"{r['Trapped_US_B']:>10.1f} {share:>6.1f}% {r2:>6.3f} "
            f"{rmse:>5.2f}p "
            f"{r['Trapped_DK_B']:>10.1f} "
            f"{r['Gap_B']:>10.1f}{marker}"
        )
    print("=" * len(header) + "\n")


def main():
    print("Fetching FRED data once …")
    df = fed.fetch_data()

    print("Fetching SOMA MBS roll-off from NY Fed …")
    soma_rolloff = fed.fetch_soma_mbs_monthly()

    print("Fetching SOMA MBS coupon cohorts …")
    cohorts = fed.fetch_soma_mbs_cohorts()
    ref = abm.reference_cohort(cohorts)
    income, home_value = abm.fetch_macro_from_fred()
    mobility_scale = abm.calibrate_mobility_scale(
        income, home_value,
        cohort_rate=ref["coupon"],
        cohort_months=ref["months_elapsed"],
    )
    abm_params = {
        "mobility_scale": mobility_scale,
        "median_income": income,
        "median_home_value": home_value,
    }

    baseline_metrics = fed.compute_metrics(
        df, soma_rolloff=soma_rolloff, cohorts=cohorts,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
        abm_params=abm_params,
    )
    emp_trapped = empirical_trapped(baseline_metrics)
    print(f"Empirical trapped liquidity (SOMA): ${emp_trapped:,.1f}B")

    combos = list(itertools.product(
        BASE_GRID, SEARCH_CAP_GRID, SENTIMENT_CAP_GRID
    ))
    print(f"Sweeping {len(combos)} scenarios …")

    rows = [
        run_single_scenario(df, None, base, search_cap, sentiment_cap,
                            soma_rolloff=soma_rolloff,
                            empirical_trapped=emp_trapped,
                            cohorts=cohorts,
                            abm_params=abm_params)
        for base, search_cap, sentiment_cap in combos
    ]

    results = pd.DataFrame(rows).sort_values(
        "Trapped_US_B", ascending=False
    ).reset_index(drop=True)

    print_table(results)

    results.to_csv(RESULTS_CSV, index=False)
    print(f"Full sweep saved to {RESULTS_CSV}")

    # Robustness summary
    base_b, base_s, base_sent = BASELINE
    base_row = results[
        np.isclose(results["Base_Pct"], base_b * 100)
        & np.isclose(results["Search_Cap_bps"], base_s * 10_000)
        & np.isclose(results["Sentiment_Cap_bps"], base_sent * 10_000)
    ].iloc[0]

    print("\n" + "=" * 60)
    print(" PANEL A: FRICTION-PARAMETER SENSITIVITY SUMMARY")
    print("=" * 60)
    print(f"  Empirical trapped liquidity:  ${emp_trapped:,.1f}B")
    print(f"  Baseline ABM trapped:         ${base_row['Trapped_US_B']:,.1f}B")
    print(f"  Baseline share explained:     {base_row['Share_Explained_Pct']:.1f}%")
    print(f"  ABM range across {len(combos)} scenarios:")
    print(f"    Trapped:   ${results['Trapped_US_B'].min():,.1f}B"
          f"  →  ${results['Trapped_US_B'].max():,.1f}B")
    print(f"    Share:     {results['Share_Explained_Pct'].min():.1f}%"
          f"  →  {results['Share_Explained_Pct'].max():.1f}%")
    print(f"    CPR R²:    {results['CPR_R2'].min():.3f}"
          f"  →  {results['CPR_R2'].max():.3f}")
    print(f"    CPR RMSE:  {results['CPR_RMSE'].min():.2f}pp"
          f"  →  {results['CPR_RMSE'].max():.2f}pp")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
