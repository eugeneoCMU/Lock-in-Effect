"""
Robustness Analysis — Data-Source & Cap-Schedule Sensitivity
============================================================
Complements the friction-parameter sweep in sensitivity_analysis.py by
varying the two remaining degrees of freedom that affect the headline
empirical shortfall:

  Panel B: Data-source sensitivity
    * SOMA API month-end values  (preferred, cleaner)
    * WSHOMCB FRED diffs         (noisier, includes TBA settlement artefacts)

  Panel C: Redemption-cap schedule assumptions
    * Ramp-up duration (2, 3, or 4 months at $17.5B)
    * Full-pace cap ($30B, $35B)
    * QT end date (Jun 2025, Sep 2025, Dec 2025)

For each scenario the empirical trapped liquidity, ABM trapped liquidity
(at baseline friction), the gap, the share explained, and CPR R² are
reported.

Run:
    python3 robustness_analysis.py
"""

import itertools

import numpy as np
import pandas as pd

import fed_mbs_extension_risk as fed

RESULTS_CSV = "robustness_results.csv"


# ---------------------------------------------------------------------------
# Panel B helpers
# ---------------------------------------------------------------------------
def empirical_trapped_from_metrics(metrics: pd.DataFrame) -> float:
    qt = metrics.loc[metrics.index >= fed.QT_START].dropna(
        subset=["Extension_Delta_Billions"]
    )
    return float(qt["Extension_Delta_Billions"].sum())


def abm_trapped_and_gof(metrics: pd.DataFrame) -> dict:
    qt = metrics.loc[metrics.index >= fed.QT_START].dropna(
        subset=["Extension_Delta_Billions"]
    )
    trapped_us = float(qt["US_Missed_Rolloff_Billions"].sum())
    gof = fed.cpr_goodness_of_fit(qt["Empirical_CPR_Pct"], qt["US_CPR_Pct"])
    return {
        "ABM_Trapped_US_B": trapped_us,
        "CPR_R2": gof["raw"]["r2"],
        "CPR_RMSE": gof["raw"]["rmse"],
        "CPR_R2_Smooth": gof["smoothed"]["r2"],
    }


# ---------------------------------------------------------------------------
# Panel C helpers — build a custom QT target series
# ---------------------------------------------------------------------------
def custom_qt_target(index: pd.DatetimeIndex,
                     ramp_months: int = 3,
                     ramp_cap: float = -17.5,
                     full_cap: float = -35.0,
                     qt_end: pd.Timestamp = fed.QT_END) -> pd.Series:
    target = pd.Series(np.nan, index=index)
    ramp_end = fed.QT_START + pd.DateOffset(months=ramp_months)
    ramp = (index >= fed.QT_START) & (index < ramp_end)
    full = (index >= ramp_end) & (index < qt_end)
    target[ramp] = ramp_cap
    target[full] = full_cap
    target[index >= qt_end] = 0.0
    return target


def run_cap_scenario(df: pd.DataFrame, surface, soma_rolloff,
                     ramp_months: int, full_cap: float,
                     qt_end: pd.Timestamp,
                     cohorts=None) -> dict:
    """
    Re-run compute_metrics with a custom cap schedule by monkey-patching the
    QT target after computation.  Only the target series and the downstream
    deltas change; the CPR surface is unaffected.
    """
    metrics = fed.compute_metrics(df, soma_rolloff=soma_rolloff, surface=surface,
                                  cohorts=cohorts)

    custom = custom_qt_target(metrics.index,
                              ramp_months=ramp_months,
                              full_cap=full_cap,
                              qt_end=qt_end)
    metrics["QT_Target_Billions"] = custom

    qt_active = (metrics.index >= fed.QT_START) & (metrics.index < qt_end)
    qt_mask = metrics.index >= fed.QT_START

    # Recompute empirical extension delta
    metrics["Extension_Delta_Billions"] = np.where(
        qt_mask,
        metrics["Actual_Monthly_Rolloff_Billions"] - custom,
        np.nan,
    )
    trapped_emp = metrics.loc[qt_mask, "Extension_Delta_Billions"].dropna().sum()

    # Recompute ABM extension deltas
    metrics["US_Extension_Delta_Billions"] = np.where(
        qt_mask,
        metrics["US_Simulated_Monthly_Rolloff_Billions"] - custom,
        np.nan,
    )
    us_delta = pd.Series(
        metrics["US_Extension_Delta_Billions"].fillna(0.0)
    ).where(qt_active, 0.0)
    trapped_abm = float(us_delta.sum())

    gof = fed.cpr_goodness_of_fit(
        metrics.loc[qt_mask, "Empirical_CPR_Pct"].dropna(),
        metrics.loc[qt_mask, "US_CPR_Pct"].dropna(),
    )

    share = trapped_abm / trapped_emp * 100 if trapped_emp else np.nan

    return {
        "Ramp_Months": ramp_months,
        "Full_Cap_B": abs(full_cap),
        "QT_End": qt_end.strftime("%Y-%m"),
        "Empirical_Trapped_B": trapped_emp,
        "ABM_Trapped_US_B": trapped_abm,
        "Vs_Empirical_B": trapped_abm - trapped_emp,
        "Share_Explained_Pct": share,
        "CPR_R2": gof["raw"]["r2"],
        "CPR_RMSE": gof["raw"]["rmse"],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Fetching FRED data …")
    df = fed.fetch_data()

    print("Loading CPR surface …")
    surface = fed.load_cpr_surface()
    if surface is None:
        raise SystemExit(
            "abm_cpr_surface.csv not found — run abm_lockin_simulation.py first."
        )

    cohorts = None
    if isinstance(surface, dict):
        print("Fetching SOMA MBS coupon cohorts once …")
        cohorts = fed.fetch_soma_mbs_cohorts()

    # ==================================================================
    # PANEL B — Data-source sensitivity
    # ==================================================================
    print("\n--- Panel B: Data-source sensitivity ---")

    print("Fetching SOMA roll-off …")
    soma_rolloff = fed.fetch_soma_mbs_monthly()

    panel_b = []
    for source_label, rolloff in [("SOMA", soma_rolloff), ("WSHOMCB", None)]:
        metrics = fed.compute_metrics(df, soma_rolloff=rolloff, surface=surface,
                                      cohorts=cohorts)
        emp = empirical_trapped_from_metrics(metrics)
        abm = abm_trapped_and_gof(metrics)
        share = abm["ABM_Trapped_US_B"] / emp * 100 if emp else np.nan
        row = {
            "Source": source_label,
            "Empirical_Trapped_B": emp,
            **abm,
            "Share_Explained_Pct": share,
        }
        panel_b.append(row)
        print(f"  {source_label:>8}:  empirical=${emp:,.1f}B  "
              f"ABM=${abm['ABM_Trapped_US_B']:,.1f}B  "
              f"share={share:.1f}%  R²={abm['CPR_R2']:.3f}")

    # ==================================================================
    # PANEL C — Cap-schedule sensitivity
    # ==================================================================
    print("\n--- Panel C: Cap-schedule sensitivity ---")

    ramp_grid = [2, 3, 4]
    cap_grid = [-30.0, -35.0]
    end_grid = [pd.Timestamp("2025-06-01"),
                pd.Timestamp("2025-09-01"),
                pd.Timestamp("2025-12-01")]

    combos = list(itertools.product(ramp_grid, cap_grid, end_grid))
    print(f"Sweeping {len(combos)} cap scenarios …")

    panel_c = []
    for ramp, cap, end in combos:
        row = run_cap_scenario(df, surface, soma_rolloff, ramp, cap, end,
                               cohorts=cohorts)
        panel_c.append(row)

    panel_c_df = pd.DataFrame(panel_c)

    print(f"\n{'Ramp':>5} {'Cap$B':>6} {'QTEnd':>8} "
          f"{'Emp$B':>8} {'ABM$B':>8} {'Share%':>7} {'R²':>6}")
    print("-" * 55)
    for _, r in panel_c_df.iterrows():
        baseline = (r["Ramp_Months"] == 3
                     and r["Full_Cap_B"] == 35.0
                     and r["QT_End"] == "2025-12")
        marker = " <<<" if baseline else ""
        print(f"{r['Ramp_Months']:>5} {r['Full_Cap_B']:>6.0f} {r['QT_End']:>8} "
              f"{r['Empirical_Trapped_B']:>8.1f} "
              f"{r['ABM_Trapped_US_B']:>8.1f} "
              f"{r['Share_Explained_Pct']:>6.1f}% "
              f"{r['CPR_R2']:>6.3f}{marker}")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    print(" ROBUSTNESS SUMMARY")
    print("=" * 60)
    soma_row = panel_b[0]
    wshomcb_row = panel_b[1]
    print(f" Panel B — Data source:")
    print(f"   SOMA:     emp=${soma_row['Empirical_Trapped_B']:,.1f}B  "
          f"share={soma_row['Share_Explained_Pct']:.1f}%")
    print(f"   WSHOMCB:  emp=${wshomcb_row['Empirical_Trapped_B']:,.1f}B  "
          f"share={wshomcb_row['Share_Explained_Pct']:.1f}%")
    print(f" Panel C — Cap schedule ({len(combos)} scenarios):")
    print(f"   Empirical range:  ${panel_c_df['Empirical_Trapped_B'].min():,.1f}B"
          f"  →  ${panel_c_df['Empirical_Trapped_B'].max():,.1f}B")
    print(f"   Share range:      {panel_c_df['Share_Explained_Pct'].min():.1f}%"
          f"  →  {panel_c_df['Share_Explained_Pct'].max():.1f}%")
    print(f"   CPR R² range:     {panel_c_df['CPR_R2'].min():.3f}"
          f"  →  {panel_c_df['CPR_R2'].max():.3f}")
    print("=" * 60)

    # Save
    all_rows = []
    for r in panel_b:
        all_rows.append({"Panel": "B_DataSource", **r})
    for r in panel_c:
        all_rows.append({"Panel": "C_CapSchedule", **r})
    pd.DataFrame(all_rows).to_csv(RESULTS_CSV, index=False)
    print(f"\nFull results saved to {RESULTS_CSV}")


if __name__ == "__main__":
    main()
