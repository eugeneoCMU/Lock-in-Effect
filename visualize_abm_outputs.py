"""
Visualize the Agent-Based Model CSV outputs.

Generates two standalone PNG charts from the ABM result files:
  * abm_lockin_results_viz.png   <- abm_lockin_results.csv   (1D S-curve)
  * abm_cpr_surface_viz.png      <- abm_cpr_surface.csv       (2D rate x friction heatmaps)

Run:
    python3 visualize_abm_outputs.py
"""

import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RESULTS_CSV = "abm_lockin_results.csv"
SURFACE_CSV = "abm_cpr_surface.csv"
RESULTS_PNG = "abm_lockin_results_viz.png"
SURFACE_PNG = "abm_cpr_surface_viz.png"

ORIGINAL_RATE = 0.03  # 2020-21 pandemic origination coupon, for reference line

US_COLOR = "#1f77b4"
DK_COLOR = "#d62728"


# ---------------------------------------------------------------------------
# Loading & validation
# ---------------------------------------------------------------------------
def load_csv(path: str, required: list[str]) -> pd.DataFrame:
    """Read a CSV and confirm the required columns are present."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        sys.exit(
            f"ERROR: '{path}' not found. Run abm_lockin_simulation.py first "
            f"to generate the ABM CSV outputs."
        )

    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(
            f"ERROR: '{path}' is missing required column(s): {missing}. "
            f"Found columns: {list(df.columns)}"
        )
    if df.empty:
        sys.exit(f"ERROR: '{path}' contains no data rows.")
    return df


# ---------------------------------------------------------------------------
# Plot 1: S-curve (abm_lockin_results.csv)
# ---------------------------------------------------------------------------
def plot_results_scurve(df: pd.DataFrame, save_path: str = RESULTS_PNG):
    """1D S-curve of CPR vs. market rate for both mortgage systems."""
    df = df.sort_values("Market_Rate")
    rate_pct = df["Market_Rate"] * 100
    us_pct = df["CPR_US"] * 100
    dk_pct = df["CPR_Danish"] * 100

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(rate_pct, us_pct, color=US_COLOR, linewidth=2.5,
            marker="o", markersize=6, label="U.S. System (par payoff)")
    ax.plot(rate_pct, dk_pct, color=DK_COLOR, linewidth=2.5,
            marker="s", markersize=6,
            label="Danish System (market-price buyback)")

    # Shade the lock-in gap between the two systems
    ax.fill_between(rate_pct, us_pct, dk_pct, color="grey", alpha=0.12,
                    label="Lock-In Gap (Danish - U.S.)")

    # Reference line at the original mortgage coupon
    ax.axvline(x=ORIGINAL_RATE * 100, color="grey", linestyle=":",
               linewidth=1.5, alpha=0.8)
    ax.text(ORIGINAL_RATE * 100 + 0.05, 2, "Original coupon (3.0%)",
            color="grey", fontsize=10)

    ax.set_xlabel("Current Market Interest Rate (%)", fontsize=12)
    ax.set_ylabel("Mobility Rate / CPR (%)", fontsize=12)
    ax.set_title(
        "The Lock-In Effect: Household Mobility vs. Rate Shocks\n"
        "U.S. Par-Payoff Rule vs. Danish Market-Price Buyback Rule",
        fontsize=14, fontweight="bold",
    )
    ax.set_xlim(rate_pct.min() - 0.2, rate_pct.max() + 0.2)
    y_top = max(40, max(us_pct.max(), dk_pct.max()) + 5)
    ax.set_ylim(0, y_top)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=11, loc="upper right")

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"S-curve chart saved to {save_path}")


# ---------------------------------------------------------------------------
# Plot 2: CPR surface (abm_cpr_surface.csv)
# ---------------------------------------------------------------------------
def _pivot_surface(df: pd.DataFrame, value_col: str):
    """Pivot the long surface frame into a (friction x rate) grid."""
    rates = np.sort(df["Market_Rate"].unique())
    frictions = np.sort(df["Friction"].unique())
    grid = (
        df.pivot(index="Friction", columns="Market_Rate", values=value_col)
          .reindex(index=frictions, columns=rates)
    )
    return rates, frictions, grid.to_numpy()


def plot_cpr_surface(df: pd.DataFrame, save_path: str = SURFACE_PNG):
    """Side-by-side heatmaps of the 2D CPR surface (rate x friction)."""
    rates, frictions, z_us = _pivot_surface(df, "CPR_US")
    _, _, z_dk = _pivot_surface(df, "CPR_Danish")

    rate_pct = rates * 100
    fric_pct = frictions * 100

    # Shared color scale so the two systems are directly comparable
    vmin = 0.0
    vmax = max(np.nanmax(z_us), np.nanmax(z_dk)) * 100

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
    extent = [rate_pct.min(), rate_pct.max(), fric_pct.min(), fric_pct.max()]

    panels = [
        (axes[0], z_us * 100, "U.S. System (par payoff)"),
        (axes[1], z_dk * 100, "Danish System (market-price buyback)"),
    ]

    mesh = None
    for ax, z_pct, title in panels:
        mesh = ax.imshow(
            z_pct, origin="lower", aspect="auto", extent=extent,
            cmap="viridis", vmin=vmin, vmax=vmax,
        )
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Market Interest Rate (%)", fontsize=11)
        # Annotate each cell with its CPR value for readability
        for i, fr in enumerate(fric_pct):
            for j, rt in enumerate(rate_pct):
                ax.text(rt, fr, f"{z_pct[i, j]:.0f}",
                        ha="center", va="center", fontsize=6,
                        color="white" if z_pct[i, j] < vmax * 0.6 else "black")

    axes[0].set_ylabel("Dynamic Friction (%)", fontsize=11)

    cbar = fig.colorbar(mesh, ax=axes, fraction=0.046, pad=0.04)
    cbar.set_label("Conditional Prepayment Rate (CPR, %)", fontsize=11)

    fig.suptitle(
        "ABM CPR Surface: Mobility Across Rate and Friction Regimes",
        fontsize=15, fontweight="bold",
    )
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"CPR surface chart saved to {save_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading ABM CSV outputs …")
    results = load_csv(RESULTS_CSV, ["Market_Rate", "CPR_US", "CPR_Danish"])
    surface = load_csv(
        SURFACE_CSV, ["Market_Rate", "Friction", "CPR_US", "CPR_Danish"]
    )

    print("Rendering visualizations …")
    plot_results_scurve(results)
    plot_cpr_surface(surface)

    print("Done — both charts generated.")


if __name__ == "__main__":
    main()
