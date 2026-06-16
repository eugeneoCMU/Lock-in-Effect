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
BASELINE_START = "2017-01-01"  # earlier start to compute 2017-2019 baselines
QT_START = pd.Timestamp("2022-06-01")
QT_END = pd.Timestamp("2025-12-01")  # Fed officially ended QT in December 2025
QT_TARGET_B = -35.0  # $35B monthly roll-off target during active QT
POST_QT_TARGET_B = 0.0  # no balance-sheet shrink target after QT ends

# ---------------------------------------------------------------------------
# Dynamic Macroeconomic Friction parameters
# ---------------------------------------------------------------------------
BASE_FRICTION = 0.07            # 7% baseline transaction cost
SEARCH_PENALTY_CAP = 0.02       # max +200 bps when inventory is at its lowest
SENTIMENT_BASELINE = 85.0       # healthy consumer-sentiment baseline (UMCSENT)
SENTIMENT_PENALTY_PER_PT = 0.0005   # +5 bps per point below baseline
SENTIMENT_PENALTY_CAP = 0.015   # max +150 bps during peak fear


def compute_qt_target_series(index: pd.DatetimeIndex) -> pd.Series:
    """
    Build a time-dependent QT roll-off target aligned to the index:
      * before QT_START          -> NaN  (no target regime)
      * QT_START <= t < QT_END   -> -35B/month (active QT)
      * t >= QT_END              -> 0B/month  (QT ended Dec 2025)
    """
    target = pd.Series(np.nan, index=index)
    active = (index >= QT_START) & (index < QT_END)
    target[active] = QT_TARGET_B
    target[index >= QT_END] = POST_QT_TARGET_B
    return target

# ---------------------------------------------------------------------------
# ABM-calibrated CPR anchors — loaded dynamically from the ABM output CSV
# so that re-running the simulation automatically updates the dashboard.
# Fallback to hardcoded values if the CSV is not found (first run / offline).
# ---------------------------------------------------------------------------
_FALLBACK_RATES = np.array([3.0, 5.0, 8.0])
_FALLBACK_US    = np.array([39.2, 16.4, 4.56])
_FALLBACK_DK    = np.array([39.2, 35.1, 30.9])


def load_abm_anchors(csv_path: str = "abm_lockin_results.csv"):
    """
    Read the ABM results CSV and extract anchor CPRs at 3%, 5%, and 8%
    market rates. Returns (rates_pct, us_cpr_pct, danish_cpr_pct).
    """
    try:
        abm = pd.read_csv(csv_path)
        anchor_decimals = [0.03, 0.05, 0.08]
        rows = [abm.iloc[(abm["Market_Rate"] - r).abs().argsort().iloc[0]]
                for r in anchor_decimals]
        rates  = np.array([r["Market_Rate"] * 100 for r in rows])
        us_cpr = np.array([r["CPR_US"]      * 100 for r in rows])
        dk_cpr = np.array([r["CPR_Danish"]  * 100 for r in rows])
        print(f"ABM anchors loaded from {csv_path}: "
              f"US CPR @ 8% = {us_cpr[-1]:.2f}%, "
              f"Danish CPR @ 8% = {dk_cpr[-1]:.2f}%")
        return rates, us_cpr, dk_cpr
    except FileNotFoundError:
        print(f"{csv_path} not found — using fallback CPR anchors.")
        return _FALLBACK_RATES, _FALLBACK_US, _FALLBACK_DK


def compute_abm_cpr_vectors(mortgage_rate_pct: pd.Series,
                            anchor_rates=None, anchor_us=None,
                            anchor_dk=None) -> pd.DataFrame:
    """
    Map each month's 30-yr mortgage rate to ABM-calibrated annual CPRs via
    linear interpolation between the anchor points. np.interp clamps values
    outside the anchor range to the boundary values automatically.
    """
    if anchor_rates is None:
        anchor_rates = _FALLBACK_RATES
    if anchor_us is None:
        anchor_us = _FALLBACK_US
    if anchor_dk is None:
        anchor_dk = _FALLBACK_DK

    rates = mortgage_rate_pct.to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "US_CPR_Pct": np.interp(rates, anchor_rates, anchor_us),
            "Danish_CPR_Pct": np.interp(rates, anchor_rates, anchor_dk),
        },
        index=mortgage_rate_pct.index,
    )


# ---------------------------------------------------------------------------
# Dynamic Macroeconomic Friction
# ---------------------------------------------------------------------------
def calculate_dynamic_friction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a per-month Dynamic_Friction column from two macro drivers:

      * Search friction  -> low housing inventory (ACTLISCOUUS) below its
        2017-2019 baseline adds up to +200 bps (proportional, capped).
      * Psychological friction -> consumer sentiment (UMCSENT) below 85 adds
        +5 bps per point, capped at +150 bps.

    Dynamic_Friction = 0.07 + search_penalty + sentiment_penalty,
    floating between 7.0% and 10.5%.
    """
    df = df.copy()
    baseline = df.attrs.get("inventory_baseline", df["ACTLISCOUUS"].mean())

    # Search penalty: scale so the lowest-inventory month hits the cap
    inventory_min = df["ACTLISCOUUS"].min()
    shortfall = (baseline - df["ACTLISCOUUS"]).clip(lower=0.0)
    denom = baseline - inventory_min
    if denom <= 0:
        search_penalty = pd.Series(0.0, index=df.index)
    else:
        search_penalty = (SEARCH_PENALTY_CAP * shortfall / denom).clip(
            upper=SEARCH_PENALTY_CAP
        )

    # Sentiment penalty: +5 bps per point below the healthy baseline
    sentiment_drop = (SENTIMENT_BASELINE - df["UMCSENT"]).clip(lower=0.0)
    sentiment_penalty = (sentiment_drop * SENTIMENT_PENALTY_PER_PT).clip(
        upper=SENTIMENT_PENALTY_CAP
    )

    df["Search_Penalty"] = search_penalty
    df["Sentiment_Penalty"] = sentiment_penalty
    df["Dynamic_Friction"] = BASE_FRICTION + search_penalty + sentiment_penalty
    return df


def load_cpr_surface(csv_path: str = "abm_cpr_surface.csv"):
    """
    Load the ABM 2D CPR surface and reshape into grids for interpolation.
    Returns (rates_pct, frictions, Z_US, Z_DK) or None if the file is absent.

    rates_pct  : 1D array of market rates in percent (ascending)
    frictions  : 1D array of friction levels in decimal (ascending)
    Z_US/Z_DK  : 2D arrays of CPR in percent, shape (len(rates), len(frictions))
    """
    try:
        surf = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"{csv_path} not found — falling back to 1D anchor CPRs.")
        return None

    rates = np.sort(surf["Market_Rate"].unique())
    frictions = np.sort(surf["Friction"].unique())
    piv_us = surf.pivot(index="Market_Rate", columns="Friction",
                        values="CPR_US").reindex(index=rates, columns=frictions)
    piv_dk = surf.pivot(index="Market_Rate", columns="Friction",
                        values="CPR_Danish").reindex(index=rates,
                                                     columns=frictions)
    rates_pct = rates * 100.0          # surface rates are decimals
    z_us = piv_us.to_numpy() * 100.0   # CPR decimal -> percent
    z_dk = piv_dk.to_numpy() * 100.0
    print(f"CPR surface loaded from {csv_path}: "
          f"{len(rates)} rates x {len(frictions)} friction levels")
    return rates_pct, frictions, z_us, z_dk


def interp_cpr_surface(rate_pct: pd.Series, friction: pd.Series,
                       surface) -> pd.DataFrame:
    """
    Bilinear interpolation on the (rate, friction) CPR surface, evaluated
    per month. Uses nested np.interp (rate axis, then friction axis) so no
    SciPy dependency is required. np.interp clamps out-of-range inputs.
    """
    rates_pct, frictions, z_us, z_dk = surface
    rate_arr = rate_pct.to_numpy(dtype=float)
    fric_arr = friction.to_numpy(dtype=float)

    us_out = np.empty(len(rate_arr))
    dk_out = np.empty(len(rate_arr))
    for i in range(len(rate_arr)):
        # Step 1: interpolate over rate for each friction column
        us_by_friction = np.array(
            [np.interp(rate_arr[i], rates_pct, z_us[:, j])
             for j in range(len(frictions))]
        )
        dk_by_friction = np.array(
            [np.interp(rate_arr[i], rates_pct, z_dk[:, j])
             for j in range(len(frictions))]
        )
        # Step 2: interpolate that result over friction
        us_out[i] = np.interp(fric_arr[i], frictions, us_by_friction)
        dk_out[i] = np.interp(fric_arr[i], frictions, dk_by_friction)

    return pd.DataFrame(
        {"US_CPR_Pct": us_out, "Danish_CPR_Pct": dk_out},
        index=rate_pct.index,
    )


# ---------------------------------------------------------------------------
# Section 1 – Data Ingestion & Cleaning
# ---------------------------------------------------------------------------
def fetch_data(api_key: str = FRED_API_KEY,
               start: str = START_DATE) -> pd.DataFrame:
    """
    Pull the Fed balance-sheet series plus the two macro-friction drivers,
    merge into a clean monthly frame, and stash the 2017-2019 inventory
    baseline in df.attrs for the dynamic-friction calculation.
    """
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

    # --- Macro-friction drivers (pulled from 2017 for baseline) -----------
    inventory = fred.get_series("ACTLISCOUUS",
                                observation_start=BASELINE_START)  # search friction
    sentiment = fred.get_series("UMCSENT",
                                observation_start=BASELINE_START)  # psych friction
    inventory_m = inventory.resample("ME").last()
    sentiment_m = sentiment.resample("ME").mean()

    # 2017-2019 inventory baseline (healthy, pre-pandemic supply)
    base_slice = inventory_m.loc["2017-01-01":"2019-12-31"]
    inventory_baseline = float(base_slice.mean())

    # Align friction drivers to the monthly Fed timeline; no NaNs allowed
    monthly["ACTLISCOUUS"] = inventory_m.reindex(monthly.index).ffill().bfill()
    monthly["UMCSENT"] = sentiment_m.reindex(monthly.index).ffill().bfill()

    monthly.attrs["inventory_baseline"] = inventory_baseline
    print(f"FRED friction drivers loaded: 2017-2019 inventory baseline = "
          f"{inventory_baseline:,.0f} listings")

    return monthly


# ---------------------------------------------------------------------------
# Section 2 – Quantitative Calculations
# ---------------------------------------------------------------------------
def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Derive roll-off, extension delta, and cumulative trapped liquidity."""
    df = df.copy()

    # Month-over-month change in MBS holdings, converted M -> B
    df["Actual_Monthly_Rolloff_Billions"] = df["WSHOMCB"].diff(periods=1) / 1_000

    # Time-dependent QT target: -35B during active QT, 0B after Dec 2025
    df["QT_Target_Billions"] = compute_qt_target_series(df.index)

    # Masks: QT active window (accumulation only happens here)
    qt_active = (df.index >= QT_START) & (df.index < QT_END)

    # Extension delta vs. the row-wise target (only meaningful after QT began)
    df["Extension_Delta_Billions"] = np.where(
        df.index >= QT_START,
        df["Actual_Monthly_Rolloff_Billions"] - df["QT_Target_Billions"],
        np.nan,
    )

    # Cumulative trapped liquidity: accumulate missed targets only while QT is
    # active; after QT ends (Dec 2025) the series flatlines at its peak.
    trapped = df["Extension_Delta_Billions"].where(
        df["Extension_Delta_Billions"] > 0, 0.0
    )
    trapped = trapped.where(qt_active, 0.0)  # no accumulation outside active QT
    df["Cumulative_Trapped_Liquidity"] = trapped.cumsum()
    # Keep NaN before QT era for clean plotting
    df.loc[df.index < QT_START, "Cumulative_Trapped_Liquidity"] = np.nan

    # --- Dynamic macroeconomic friction -----------------------------------
    # Build the per-month friction from inventory + sentiment first, so the
    # CPR surface can be sampled at each month's (rate, friction) coordinate.
    df = calculate_dynamic_friction(df)

    # --- ABM counterfactual: month-varying CPR paths ----------------------
    # Preferred path: 2D CPR surface interpolated on (rate, friction).
    # Fallback: 1D anchor interpolation at base friction if surface is absent.
    surface = load_cpr_surface()
    if surface is not None:
        cpr = interp_cpr_surface(df["MORTGAGE30US"], df["Dynamic_Friction"],
                                 surface)
    else:
        anchor_rates, anchor_us, anchor_dk = load_abm_anchors()
        cpr = compute_abm_cpr_vectors(df["MORTGAGE30US"],
                                      anchor_rates, anchor_us, anchor_dk)
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

    # Extension deltas vs. the row-wise QT target for both institutional regimes
    qt_mask = df.index >= QT_START
    df["US_Extension_Delta_Billions"] = np.where(
        qt_mask,
        df["US_Simulated_Monthly_Rolloff_Billions"] - df["QT_Target_Billions"],
        np.nan,
    )
    df["Danish_Extension_Delta_Billions"] = np.where(
        qt_mask,
        df["Danish_Simulated_Monthly_Rolloff_Billions"]
        - df["QT_Target_Billions"],
        np.nan,
    )

    # Positive shortfall only (months where the simulated path missed target)
    df["US_Missed_Rolloff_Billions"] = (
        df["US_Extension_Delta_Billions"].clip(lower=0)
    )
    df["Danish_Missed_Rolloff_Billions"] = (
        df["Danish_Extension_Delta_Billions"].clip(lower=0)
    )

    # Accumulate only during active QT; flatline after Dec 2025
    us_missed_active = df["US_Missed_Rolloff_Billions"].where(qt_active, 0.0)
    dk_missed_active = df["Danish_Missed_Rolloff_Billions"].where(qt_active, 0.0)
    df["US_Cumulative_Trapped_Liquidity_Billions"] = (
        us_missed_active.fillna(0.0).cumsum()
    )
    df["Danish_Cumulative_Trapped_Liquidity_Billions"] = (
        dk_missed_active.fillna(0.0).cumsum()
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
    # Bar color compares actual roll-off to the row-wise (time-dependent) target
    bar_colors = np.where(
        qt_df["Actual_Monthly_Rolloff_Billions"]
        <= qt_df["QT_Target_Billions"],
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
    # Stepped QT target: flat at -35 then steps up to 0 when QT ends (Dec 2025)
    ax2.plot(
        qt_df.index, qt_df["QT_Target_Billions"],
        color="#555555", linewidth=1.8, linestyle="--", drawstyle="steps-post",
        label="QT Target (-35B, then 0B after Dec 2025)",
    )
    # Mark the QT end date
    ax2.axvline(QT_END, color="#222222", linewidth=1.0, linestyle=":",
                alpha=0.6)
    ax2.set_ylabel("Monthly Roll-Off ($B)", fontsize=12)
    ax2.set_title(
        "Monthly MBS Roll-Off vs. QT Target — Actual and ABM-Calibrated "
        "Counterfactuals", fontsize=13,
    )
    ax2.grid(axis="y", alpha=0.3)

    # Dynamic_Friction overlay on a twin axis so the friction regime is visible
    ax2f = ax2.twinx()
    ax2f.plot(
        qt_df.index, qt_df["Dynamic_Friction"] * 100,
        color="#6a3d9a", linewidth=1.4, linestyle=":",
        label="Dynamic Friction (%)",
    )
    ax2f.set_ylabel("Dynamic Friction (%)", fontsize=11, color="#6a3d9a")
    ax2f.tick_params(axis="y", labelcolor="#6a3d9a")
    ax2f.set_ylim(6.5, 11.0)
    # Merge legends from both axes
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2f.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="lower left", fontsize=9)

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

    # Mark the QT end date — accumulation stops here (permanent trap)
    ax3.axvline(QT_END, color="#222222", linewidth=1.0, linestyle=":",
                alpha=0.6)
    ax3.text(QT_END, 0, " QT ends\n (Dec 2025)", fontsize=9,
             color="#222222", va="bottom", ha="left")

    ax3.set_ylabel("Cumulative Trapped Liquidity ($B)", fontsize=12)
    ax3.set_title(
        "Cumulative Trapped Liquidity — The Permanent Trap "
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

    qt_end_prev = (QT_END - pd.offsets.MonthBegin(1)).strftime("%B %Y")
    print("\n" + "=" * 65)
    print(" MBS EXTENSION RISK — SUMMARY STATISTICS")
    print("=" * 65)
    print(f"  Active QT Period:  {QT_START.strftime('%B %Y')} → {qt_end_prev}")
    print(f"  QT Target (active):  {QT_TARGET_B:+.0f} $B / month")
    print(f"  Post-QT Target (from {QT_END.strftime('%B %Y')}):"
          f"  {POST_QT_TARGET_B:+.0f} $B / month")
    print(f"  Avg Actual Roll-Off:      {avg_rolloff:+.2f} $B / month")
    print(f"  Total Aggregate Missed Roll-Off (Trapped Liquidity):"
          f"  ${total_trapped:,.1f}B")
    print("-" * 65)
    print(" ABM-CALIBRATED COUNTERFACTUALS (dynamic CPR paths)")
    print(f"  U.S. System Trapped Liquidity:    ${total_trapped_us:,.1f}B")
    print(f"  Danish System Trapped Liquidity:  ${total_trapped_dk:,.1f}B")
    print(f"  Institutional Gap (U.S. - Danish): ${institutional_gap:,.1f}B")
    if "Dynamic_Friction" in df.columns:
        fric = df["Dynamic_Friction"] * 100
        print("-" * 65)
        print(" DYNAMIC MACROECONOMIC FRICTION (inventory + sentiment)")
        print(f"  Friction range:  min {fric.min():.2f}%  |  "
              f"mean {fric.mean():.2f}%  |  max {fric.max():.2f}%")
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
