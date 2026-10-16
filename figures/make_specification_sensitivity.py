"""Plot reported paired-run sensitivities from paper_final_v1.tex.

These values are transcription of existing results, not new simulations.
Each row changes one assumption relative to the hard-maximum, off-window
anchor unless its label says otherwise. Ranges are specification sweeps.
"""

from pathlib import Path

import matplotlib.pyplot as plt


POINTS = [
    (r"Moving share $\mu=0.25$", 1.8, "#27647a"),
    (r"Moving share $\mu=0.50$", 3.4, "#27647a"),
    ("Ginnie speed overlay", 4.4, "#536f87"),
    ("Concave rate response", 5.1, "#536f87"),
    (r"Hard-maximum anchor, $\mu=1$", 5.6, "#bc6638"),
    ("Additive turnover form", 11.2, "#536f87"),
]
RANGES = [
    ("Off-window floor anchors", 4.3, 6.8, "#709aa0"),
    ("Floor by elasticity grid", 2.1, 13.2, "#9a9a9a"),
]


def main() -> None:
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=180)
    labels = [row[0] for row in POINTS + RANGES]
    for index, (_, value, color) in enumerate(POINTS):
        ax.scatter(value, index, s=82, color=color, zorder=3)
        ax.text(value + 0.24, index, f"+{value:.1f}", va="center", fontsize=10)
    for offset, (_, low, high, color) in enumerate(RANGES, start=len(POINTS)):
        ax.hlines(offset, low, high, color=color, linewidth=5, zorder=2)
        ax.scatter([low, high], [offset, offset], color=color, s=25, zorder=3)
        ax.text(high + 0.24, offset, f"+{low:.1f} to +{high:.1f}", va="center", fontsize=10)

    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 16.9)
    ax.set_xlabel("Paired lock-in marginal (percentage points of $764.7B cap gap)")
    ax.set_xticks([0, 2, 4, 6, 8, 10, 12, 14])
    ax.grid(axis="x", color="#e3e5e6", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=9)
    fig.tight_layout()
    fig.savefig(Path(__file__).with_name("fig13_specification_sensitivity.png"),
                bbox_inches="tight")


if __name__ == "__main__":
    main()
