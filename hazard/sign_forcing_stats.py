#!/usr/bin/env python3
"""
Sign-forcing statistics for the lock-in marginal (July 2026 panel round).

§V demotes the marginal's SIGN from identified content to a consistency
check, on the ground that essentially the whole surviving book is out of the
money for essentially the whole window: a specification in which a more
negative rate gap suppresses prepayment cannot return a negative marginal at
any floor or band in the calibration box. The manuscript states that ground
with five figures --- exposure-weighted mean coupon 3.134%, 97.40% of
exposure at or below 4.79%, 99.53% at or below 5.09%, a window-minimum
30-year rate of 5.2311%, and forty covered window months --- which were
computed in session and written straight into the .tex without ever landing
in a committed artifact. This module promotes them.

SPEC
- Source: the committed hazard/data/cohort_month_panel.parquet, restricted
  to the QT window [2022-06-01, 2025-12-01). Exposure weights are
  exposure_upb; the panel is the closed 2017--2021 origination book.
- THE COUPON COLUMN IS DECIMAL-SCALED (0.0 through 0.075), not percent. A
  naive percent-scale threshold query (coupon <= 4.79) returns 100.00% of
  exposure and is meaningless. Every threshold below is applied in decimal
  and reported in percent.
- Market rate: MORTGAGE30US on the shared macro frame (macro.fetch_data),
  monthly mean, over the same window. The reported statistic is the window
  MINIMUM, because it is the tightest in-the-money threshold any window
  month offers.
- Coverage is recorded explicitly and is not repaired: the panel ends
  2025-09, two months short of the window's 2025-11 close, so 40 of 42
  window months are covered. The gap cannot overturn the reading --- the
  book is closed at 2017--2021 originations, so no higher-coupon loan can
  enter it and the out-of-the-money share can only hold or rise as the
  low-coupon cohorts season --- but the shares are shares of covered months.
- Gate: the five recomputed figures must reproduce the manuscript's printed
  3.134 / 97.40 / 99.53 / 5.2311 / 40 at the manuscript's own printing
  precision, or the manuscript text is wrong and must be corrected to what
  this artifact says.

Run:  cd hazard && python3 sign_forcing_stats.py
      -> data/sign_forcing_stats_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import polars as pl

from macro import fetch_data

DATA_DIR = Path(__file__).parent / "data"
PANEL = DATA_DIR / "cohort_month_panel.parquet"
OUT = DATA_DIR / "sign_forcing_stats_results.json"

QT_START = pd.Timestamp("2022-06-01")
QT_END = pd.Timestamp("2025-12-01")  # exclusive
WINDOW_MONTHS = 42

# Manuscript-printed values and their printing precision (§V).
MANUSCRIPT_ANCHORS = {
    "exposure_weighted_mean_coupon_pct": (3.134, 3),
    "exposure_share_le_4_79_pct": (97.40, 2),
    "exposure_share_le_5_09_pct": (99.53, 2),
    "window_min_mortgage30us_pct": (5.2311, 4),
    "covered_window_months": (40, 0),
}

# Thresholds as printed in the manuscript, in PERCENT (applied in decimal).
PRINTED_THRESHOLDS_PCT = (4.79, 5.09)


def main() -> None:
    panel = pl.read_parquet(PANEL)

    coupon_scale = {
        "min": float(panel["coupon"].min()),
        "max": float(panel["coupon"].max()),
        "distinct": sorted(float(x) for x in panel["coupon"].unique().to_list()),
        "reading": (
            "decimal-scaled; a percent-scale threshold query returns a "
            "misleading 100.00% of exposure"
        ),
    }

    w = panel.filter(
        (pl.col("period") >= QT_START) & (pl.col("period") < QT_END)
    )
    covered_months = int(w["period"].n_unique())
    exposure = float(w["exposure_upb"].sum())

    mean_coupon_pct = float(
        (w["coupon"] * w["exposure_upb"]).sum() / exposure * 100.0
    )

    def share_le(pct: float) -> float:
        thr = pct / 100.0
        sel = float(w.filter(pl.col("coupon") <= thr + 1e-12)["exposure_upb"].sum())
        return sel / exposure * 100.0

    macro = fetch_data()
    mw = macro[(macro.index >= QT_START) & (macro.index < QT_END)]
    rate = mw["MORTGAGE30US"]
    window_min_pct = float(rate.min())
    window_min_month = str(rate.idxmin().date())

    stats = {
        "exposure_weighted_mean_coupon_pct": mean_coupon_pct,
        "exposure_share_le_4_79_pct": share_le(4.79),
        "exposure_share_le_5_09_pct": share_le(5.09),
        "window_min_mortgage30us_pct": window_min_pct,
        "covered_window_months": covered_months,
    }

    gates = {}
    for key, (want, prec) in MANUSCRIPT_ANCHORS.items():
        got = stats[key]
        ok = round(got, prec) == round(want, prec)
        gates[key] = {
            "got": got,
            "got_at_printing_precision": round(got, prec),
            "manuscript_prints": want,
            "printing_precision_dp": prec,
            "pass": bool(ok),
        }
    gates["all_pass"] = bool(all(v["pass"] for v in gates.values()
                                 if isinstance(v, dict)))

    payload = {
        "mode": "sign_forcing_stats",
        "spec": (
            "Exposure-weighted coupon distribution of the closed 2017-2021 "
            "cohort panel over the QT window, against the window-minimum "
            "30-year market rate. Promotes the five §V sign-demotion "
            "statistics from in-session computation to a committed artifact. "
            "Coupon column is decimal-scaled and thresholds are applied in "
            "decimal. Coverage is disclosed, not repaired."
        ),
        "source": {
            "panel": str(PANEL.relative_to(DATA_DIR.parent.parent)),
            "market_rate": "MORTGAGE30US, monthly mean, macro.fetch_data()",
            "coupon_column_scale": coupon_scale,
        },
        "window": {
            "start": str(QT_START.date()),
            "end_exclusive": str(QT_END.date()),
            "window_months": WINDOW_MONTHS,
            "panel_covered_months": covered_months,
            "panel_first_covered": str(w["period"].min().date()),
            "panel_last_covered": str(w["period"].max().date()),
            "uncovered_months": WINDOW_MONTHS - covered_months,
            "coverage_note": (
                "the panel ends 2025-09, two months before the window's "
                "2025-11 close; the shares below are shares of the 40 "
                "covered months. The book is closed at 2017-2021 "
                "originations, so no higher-coupon loan can enter it and the "
                "out-of-the-money share can only hold or rise as the "
                "low-coupon cohorts season: the two uncovered months cannot "
                "overturn the reading, but they are not measured."
            ),
        },
        "exposure_upb_total": exposure,
        "statistics": stats,
        "printed_thresholds_pct": list(PRINTED_THRESHOLDS_PCT),
        "supplementary": {
            "exposure_share_le_window_min_pct": share_le(window_min_pct),
            "window_min_month": window_min_month,
            "window_max_mortgage30us_pct": float(rate.max()),
            "note": (
                "the share at or below the window MINIMUM is the "
                "economically binding cut: every window month's market rate "
                "is at least this, so this share is out of the money in "
                "every covered month. The 4.79 / 5.09 thresholds the "
                "manuscript prints are strictly tighter and sit between the "
                "panel's coupon grid points."
            ),
        },
        "gates": gates,
        "verdict": (
            "sign-forcing statistics reproduced from committed data"
            if gates["all_pass"]
            else "MANUSCRIPT MISMATCH — the printed figures do not reproduce"
        ),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print("=" * 78)
    print(" SIGN-FORCING STATISTICS")
    print("=" * 78)
    print(f"  window {QT_START.date()} .. {QT_END.date()} (exclusive), "
          f"{covered_months} of {WINDOW_MONTHS} months covered by the panel")
    for key, (want, prec) in MANUSCRIPT_ANCHORS.items():
        g = gates[key]
        print(f"  {key:<40}{g['got_at_printing_precision']:>12}  "
              f"(manuscript {want})  [{'PASS' if g['pass'] else 'FAIL'}]")
    print(f"\n  exposure at or below the window minimum "
          f"({window_min_pct:.4f}%): "
          f"{payload['supplementary']['exposure_share_le_window_min_pct']:.2f}%")
    print(f"\n  Saved: {OUT}")

    if not gates["all_pass"]:
        raise SystemExit("GATE FAILURE — manuscript figures do not reproduce")


if __name__ == "__main__":
    main()
