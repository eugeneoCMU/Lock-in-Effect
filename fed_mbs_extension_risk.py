"""
Federal Reserve MBS Extension Risk Delta Analysis
===================================================
Quantifies how the high-interest-rate environment has caused "extension risk"
in the Fed's Mortgage-Backed Securities portfolio, trapping liquidity well
beyond the pace targeted by the Quantitative Tightening (QT) programme.

Data source: FRED (Federal Reserve Economic Data)
"""

import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from fredapi import Fred

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRED_API_KEY = "YOUR_FRED_API_KEY"
START_DATE = "2021-01-01"
QT_START = pd.Timestamp("2022-06-01")
QT_TARGET_B = -35.0  # $35B monthly roll-off target (negative = portfolio decline)

# ---------------------------------------------------------------------------
# ABM-calibrated CPR anchors (from abm_lockin_simulation.py, calibrated to
# the 4-5% involuntary-turnover floor). Rates in percent, CPRs in percent.
# Tails are clamped: <=3.0% uses the first anchor, >=8.0% uses the last.
# ---------------------------------------------------------------------------
CPR_ANCHOR_RATES = np.array([3.0, 5.0, 8.0])      # 30-yr mortgage rate (%)
CPR_ANCHOR_US = np.array([39.2, 16.4, 4.56])      # U.S. par-payoff system
CPR_ANCHOR_DANISH = np.array([39.2, 35.1, 30.9])  # Danish buyback system


def compute_abm_cpr_vectors(mortgage_rate_pct: pd.Series) -> pd.DataFrame:
    """
    Map each month's 30-yr mortgage rate to ABM-calibrated annual CPRs via
    linear interpolation between the anchor points. np.interp clamps values
    outside [3.0, 8.0] to the boundary anchors automatically.
    """
    rates = mortgage_rate_pct.to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "US_CPR_Pct": np.interp(rates, CPR_ANCHOR_RATES, CPR_ANCHOR_US),
            "Danish_CPR_Pct": np.interp(rates, CPR_ANCHOR_RATES,
                                        CPR_ANCHOR_DANISH),
        },
        index=mortgage_rate_pct.index,
    )


# ---------------------------------------------------------------------------
# Section 1 – Data Ingestion & Cleaning
# ---------------------------------------------------------------------------
def fetch_data(api_key: str = FRED_API_KEY,
               start: str = START_DATE) -> pd.DataFrame:
    """Pull WSHOMCB and MORTGAGE30US from FRED and merge into a clean frame."""
    fred = Fred(api_key=api_key)

    mbs = fred.get_series("WSHOMCB", observation_start=start)
    rate = fred.get_series("MORTGAGE30US", observation_start=start)

    mbs.name = "WSHOMCB"
    rate.name = "MORTGAGE30US"

    df = pd.merge(mbs, rate, how="outer", left_index=True, right_index=True)
    df.sort_index(inplace=True)
    df.ffill(inplace=True)
    df.dropna(inplace=True)

    # Resample to true calendar-month frequency so each month is counted once
    monthly = pd.DataFrame({
        "WSHOMCB": df["WSHOMCB"].resample("ME").last(),       # stock → end-of-month level
        "MORTGAGE30US": df["MORTGAGE30US"].resample("ME").mean(),  # rate → monthly average
    })
    monthly.dropna(inplace=True)

    return monthly


# ---------------------------------------------------------------------------
# Section 2 – Quantitative Calculations
# ---------------------------------------------------------------------------
def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Derive roll-off, extension delta, and cumulative trapped liquidity."""
    df = df.copy()

    # Month-over-month change in MBS holdings, converted M -> B
    df["Actual_Monthly_Rolloff_Billions"] = df["WSHOMCB"].diff(periods=1) / 1_000

    # Extension delta: only meaningful after QT began
    df["Extension_Delta_Billions"] = np.where(
        df.index >= QT_START,
        df["Actual_Monthly_Rolloff_Billions"] - QT_TARGET_B,
        np.nan,
    )

    # Cumulative trapped liquidity: sum of positive deltas (missed targets)
    trapped = df["Extension_Delta_Billions"].copy()
    trapped = trapped.where(trapped > 0, 0.0)  # zero out months target was met
    df["Cumulative_Trapped_Liquidity"] = trapped.cumsum()
    # Keep NaN before QT era for clean plotting
    df.loc[df.index < QT_START, "Cumulative_Trapped_Liquidity"] = np.nan

    # --- ABM counterfactual: dynamic CPR paths ----------------------------
    # Interpolate each month's calibrated CPR from the 30-yr mortgage rate
    cpr = compute_abm_cpr_vectors(df["MORTGAGE30US"])
    df["US_CPR_Pct"] = cpr["US_CPR_Pct"]
    df["Danish_CPR_Pct"] = cpr["Danish_CPR_Pct"]

    # Simulated monthly roll-off: holdings * monthly prepayment intensity.
    # Negative sign = portfolio decline, comparable to the -35 QT target.
    holdings_b = df["WSHOMCB"] / 1_000
    df["US_Simulated_Monthly_Rolloff_Billions"] = (
        -holdings_b * (df["US_CPR_Pct"] / 100 / 12)
    )
    df["Danish_Simulated_Monthly_Rolloff_Billions"] = (
        -holdings_b * (df["Danish_CPR_Pct"] / 100 / 12)
    )

    # Extension deltas vs. the QT target for both institutional regimes
    qt_mask = df.index >= QT_START
    df["US_Extension_Delta_Billions"] = np.where(
        qt_mask,
        df["US_Simulated_Monthly_Rolloff_Billions"] - QT_TARGET_B,
        np.nan,
    )
    df["Danish_Extension_Delta_Billions"] = np.where(
        qt_mask,
        df["Danish_Simulated_Monthly_Rolloff_Billions"] - QT_TARGET_B,
        np.nan,
    )

    # Positive shortfall only (months where the simulated path missed -35)
    df["US_Missed_Rolloff_Billions"] = (
        df["US_Extension_Delta_Billions"].clip(lower=0)
    )
    df["Danish_Missed_Rolloff_Billions"] = (
        df["Danish_Extension_Delta_Billions"].clip(lower=0)
    )

    # Cumulative trapped liquidity per system (NaN before QT era)
    df["US_Cumulative_Trapped_Liquidity_Billions"] = (
        df["US_Missed_Rolloff_Billions"].fillna(0.0).cumsum()
    )
    df["Danish_Cumulative_Trapped_Liquidity_Billions"] = (
        df["Danish_Missed_Rolloff_Billions"].fillna(0.0).cumsum()
    )
    df.loc[~qt_mask, "US_Cumulative_Trapped_Liquidity_Billions"] = np.nan
    df.loc[~qt_mask, "Danish_Cumulative_Trapped_Liquidity_Billions"] = np.nan

    return df


# ---------------------------------------------------------------------------
# Section 3 – Visualization
# ---------------------------------------------------------------------------
def plot_dashboard(df: pd.DataFrame, save_path: str = "mbs_extension_risk_dashboard.png"):
    """Three-panel publication-quality dashboard."""
    qt_mask = df.index >= QT_START
    qt_df = df.loc[qt_mask].dropna(subset=["Actual_Monthly_Rolloff_Billions"])

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(14, 14), sharex=True,
        gridspec_kw={"height_ratios": [3, 2, 2]},
    )
    fig.suptitle(
        "Federal Reserve MBS Portfolio — Extension Risk Delta Dashboard",
        fontsize=16, fontweight="bold", y=0.97,
    )

    # ---- Subplot 1: Portfolio & Interest Rates (dual axis) ----------------
    color_mbs = "#1f77b4"
    ax1.plot(
        df.index, df["WSHOMCB"] / 1_000,
        color=color_mbs, linewidth=1.8, label="Fed MBS Holdings ($B)",
    )
    ax1.set_ylabel("Fed MBS Holdings ($B)", color=color_mbs, fontsize=12)
    ax1.tick_params(axis="y", labelcolor=color_mbs)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    ax1_r = ax1.twinx()
    color_rate = "#d62728"
    ax1_r.plot(
        df.index, df["MORTGAGE30US"],
        color=color_rate, linewidth=1.5, linestyle="--",
        label="30-Yr Mortgage Rate (%)",
    )
    ax1_r.set_ylabel("30-Yr Mortgage Rate (%)", color=color_rate, fontsize=12)
    ax1_r.tick_params(axis="y", labelcolor=color_rate)

    # QT era shading
    ax1.axvspan(QT_START, df.index[-1], color="grey", alpha=0.12, label="QT Era")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_r.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)
    ax1.set_title("Total Fed MBS Holdings & 30-Year Mortgage Rate", fontsize=13)
    ax1.grid(axis="y", alpha=0.3)

    # ---- Subplot 2: Extension Delta bar chart -----------------------------
    bar_colors = np.where(
        qt_df["Actual_Monthly_Rolloff_Billions"] <= QT_TARGET_B,
        "#2ca02c",   # green — target met
        "#e8722a",   # orange — target missed (extension risk)
    )
    ax2.bar(
        qt_df.index, qt_df["Actual_Monthly_Rolloff_Billions"],
        width=20, color=bar_colors, edgecolor="none", alpha=0.85,
        label="Actual Monthly Roll-Off ($B)",
    )
    # ABM-calibrated counterfactual roll-off paths
    ax2.plot(
        qt_df.index, qt_df["US_Simulated_Monthly_Rolloff_Billions"],
        color="#1f77b4", linewidth=2.0,
        label="ABM U.S. CPR Simulated Roll-Off ($B)",
    )
    ax2.plot(
        qt_df.index, qt_df["Danish_Simulated_Monthly_Rolloff_Billions"],
        color="#d62728", linewidth=2.0, linestyle="--",
        label="ABM Danish CPR Simulated Roll-Off ($B)",
    )
    ax2.axhline(
        y=QT_TARGET_B, color="#555555", linewidth=1.5, linestyle="--",
        label=f"QT Target ({QT_TARGET_B:+.0f} $B/mo)",
    )
    ax2.set_ylabel("Monthly Roll-Off ($B)", fontsize=12)
    ax2.legend(loc="lower left", fontsize=9)
    ax2.set_title(
        "Monthly MBS Roll-Off vs. QT Target — Actual and ABM-Calibrated "
        "Counterfactuals", fontsize=13,
    )
    ax2.grid(axis="y", alpha=0.3)

    # ---- Subplot 3: Cumulative Trapped Liquidity (US vs Danish) -----------
    cum_us = df.loc[qt_mask, "US_Cumulative_Trapped_Liquidity_Billions"].dropna()
    cum_dk = df.loc[
        qt_mask, "Danish_Cumulative_Trapped_Liquidity_Billions"
    ].dropna()

    ax3.fill_between(cum_us.index, 0, cum_us.values,
                     color="#8B0000", alpha=0.55,
                     label="U.S. System (ABM-calibrated)")
    ax3.plot(cum_us.index, cum_us.values, color="#8B0000", linewidth=1.5)
    ax3.fill_between(cum_dk.index, 0, cum_dk.values,
                     color="#e8722a", alpha=0.45,
                     label="Danish System (ABM-calibrated)")
    ax3.plot(cum_dk.index, cum_dk.values, color="#e8722a", linewidth=1.5,
             linestyle="--")

    # Annotate both terminal endpoints
    ax3.annotate(
        f"U.S.: ${cum_us.iloc[-1]:,.1f}B trapped",
        xy=(cum_us.index[-1], cum_us.iloc[-1]),
        xytext=(-210, -20), textcoords="offset points",
        fontsize=11, fontweight="bold", color="#8B0000",
        arrowprops=dict(arrowstyle="->", color="#8B0000", lw=1.5),
    )
    ax3.annotate(
        f"Danish: ${cum_dk.iloc[-1]:,.1f}B trapped",
        xy=(cum_dk.index[-1], cum_dk.iloc[-1]),
        xytext=(-210, 60), textcoords="offset points",
        fontsize=11, fontweight="bold", color="#e8722a",
        arrowprops=dict(arrowstyle="->", color="#e8722a", lw=1.5),
    )

    ax3.set_ylabel("Cumulative Trapped Liquidity ($B)", fontsize=12)
    ax3.set_title(
        'Cumulative Trapped Liquidity'
        "(U.S. vs. Danish Counterfactual)", fontsize=13,
    )
    ax3.legend(loc="upper left", fontsize=10)
    ax3.grid(axis="y", alpha=0.3)

    # Shared x-axis formatting
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    fig.autofmt_xdate(rotation=45)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.show()
    print(f"\nDashboard saved to {save_path}")


# ---------------------------------------------------------------------------
# Section 4 – Summary Statistics
# ---------------------------------------------------------------------------
def print_summary(df: pd.DataFrame):
    """Print key aggregate metrics to stdout."""
    qt_df = df.loc[df.index >= QT_START].dropna(
        subset=["Extension_Delta_Billions"]
    )

    total_trapped = qt_df.loc[
        qt_df["Extension_Delta_Billions"] > 0, "Extension_Delta_Billions"
    ].sum()

    avg_rolloff = qt_df["Actual_Monthly_Rolloff_Billions"].mean()

    total_trapped_us = qt_df["US_Missed_Rolloff_Billions"].sum()
    total_trapped_dk = qt_df["Danish_Missed_Rolloff_Billions"].sum()
    institutional_gap = total_trapped_us - total_trapped_dk

    print("\n" + "=" * 65)
    print(" MBS EXTENSION RISK — SUMMARY STATISTICS")
    print("=" * 65)
    print(f"  QT Period:  {QT_START.strftime('%B %Y')} → present")
    print(f"  QT Target:  {QT_TARGET_B:+.0f} $B / month")
    print(f"  Avg Actual Roll-Off:      {avg_rolloff:+.2f} $B / month")
    print(f"  Total Aggregate Missed Roll-Off (Trapped Liquidity):"
          f"  ${total_trapped:,.1f}B")
    print("-" * 65)
    print(" ABM-CALIBRATED COUNTERFACTUALS (dynamic CPR paths)")
    print(f"  U.S. System Trapped Liquidity:    ${total_trapped_us:,.1f}B")
    print(f"  Danish System Trapped Liquidity:  ${total_trapped_dk:,.1f}B")
    print(f"  Institutional Gap (U.S. - Danish): ${institutional_gap:,.1f}B")
    print("=" * 65 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Fetching data from FRED …")
    df = fetch_data()

    print("Computing extension-risk metrics …")
    df = compute_metrics(df)

    print("Generating dashboard …")
    plot_dashboard(df)

    print_summary(df)


if __name__ == "__main__":
    main()
