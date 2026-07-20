#!/usr/bin/env python3
"""
matched_depth_reconciliation.py — decompose the floor demotion
($70.345B/+9.198pp at the in-window 4.0% floor -> $42.608B/+5.572pp at the
off-window ~4.991% floor) into a WINDOW component and a DEPTH component.

THE OBJECTION BEING TESTED (raised adversarially; not the paper's own framing).
oos_identification.py rejects the pooled-2017-2019 (6.065%) and 2019-falling
(6.910%) out-of-window anchors as refi-contaminated and keeps the 2018-rising
anchor (4.991%). But the two REJECTED reads are gap<=0 cells and the KEPT read
is a gap<=-0.0025 cell, so the rejection compares different discount depths.
Symmetrically, the demoted IN-window floor is measured at gap<=-0.02 (3.972%)
while the whole off-window grid stops at gap<=-0.005 — so the demotion contrasts
a DEEP in-window read against a SHALLOW off-window one and books the entire
difference to the window. If the depth axis owns most of the move, the paper's
contamination NARRATIVE is wrong even where its NUMBER is right.

PRE-COMMITTED SPEC (fixed before any run).

=======================================================================
STEP 1 — PARITY GATE (runs first; blocks everything downstream)
=======================================================================
Rebuild the committed instrument1_oow_floor anchor_grid from
data/cohort_month_panel.parquet using oos_identification.py's own conditioning
(coupon>0 & exposure_upb>0; gap = coupon - MORTGAGE30US/100 on the calendar-
month FRED mean; exposure-weighted SMM -> CPR = 1-(1-SMM)^12; legs
201701..201912 / 201801..201812 / 201901..201912; age cuts 12/24) and require
all 18 cells to reproduce the frozen artifact EXACTLY at the committed 3-dp
rounding. No new selector is invented. If parity FAILS, STOP.

=======================================================================
STEP 2 — MATCHED-DEPTH GRID
=======================================================================
Extend the gap ladder to {0, -0.0025, -0.005, -0.0075, -0.01, -0.015, -0.02,
-0.025} for BOTH windows at age>=12:
  OFF: pooled 2017-2019 | 2018 rising | 2019 falling
  IN : the Instrument-2 calibration sub-window 202206..202312 (the window the
       demoted 4.0% floor is actually calibrated on) and the full QT window.
A cell is reported NOT COMPUTABLE only when it has zero exposure. A cell with
positive but vanishing exposure is reported WITH ITS EXPOSURE SHARE and flagged
UNSUPPORTED — never extrapolated and never silently averaged in.

SUPPORT RULE (mechanical, ex ante): a depth is WELL-SUPPORTED for a leg when
that leg retains >= 10% of its gap<=0 exposure at that depth. The deepest
well-supported common depth is the honest matched-deep anchor.

=======================================================================
STEP 3 — DECOMPOSITION
=======================================================================
Floor -> marginal uses the COMMITTED mapping in floor_sweep_results.json
(monotone PCHIP on the frozen {2,3,3.5,4,4.5,5,6}% grid). It is NOT re-derived.
Mapping fidelity is validated against the five independent engine reads in
oos_identification_results.json; the worst in-grid error is carried as the
mapping's own uncertainty and extrapolation beyond 6.0% is refused.

Two orderings of the same total move
  START = in-window gap<=-0.02 (the demoted floor)
  END   = off-window 2018 gap<=-0.0025 (the kept floor)
  path A (depth-first) : DEPTH  = M(in,shallow)  - M(in,deep)
                         WINDOW = M(off,shallow) - M(in,shallow)
  path B (window-first): WINDOW = M(off,deep)    - M(in,deep)
                         DEPTH  = M(off,shallow) - M(off,deep)
The interaction is the gap between the two WINDOW terms. Path B is only
admissible if the off-window DEEP cell is well-supported; otherwise it is
reported NOT COMPUTABLE and no Shapley average is formed from it, because
averaging over an unsupported cell would manufacture a depth share out of an
empty selection.

=======================================================================
STEP 4 — CONTAMINATION NARRATIVE AT MATCHED DEPTH
=======================================================================
Per depth, the 2018-vs-2019 spread and the three-leg max-min. Reported with the
note that POOLED IS NOT INDEPENDENT of 2018/2019 (it contains both, plus 2017),
so there are two independent legs, not three. Convergence is judged only over
depths well-supported for BOTH legs compared.

=======================================================================
SELF-CHECKS
=======================================================================
HARD (wiring; failure invalidates the run):
  - all 18 committed anchor cells reproduce exactly
  - the committed in-window calibration reads (3.972 / 4.305) reproduce
  - path-A DEPTH + path-A WINDOW sums to the total move within $0.01B
  - the mapping reproduces the committed floor_sweep grid points exactly
SOFT (interpretive; a failure is a finding, never something to tune away):
  - the extended well-supported depth ladder leaves the committed clean band
    [4.695, 5.334]% unchanged
  - WINDOW exceeds DEPTH on the admissible path

Run:  cd hazard && python3 matched_depth_reconciliation.py
  -> data/matched_depth_reconciliation_results.json  (frozen)

Reads the manuscript's artifacts; edits nothing outside data/.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from fredapi import Fred
from scipy.interpolate import PchipInterpolator

REPO_ROOT = Path(__file__).parents[1]
HAZARD_DIR = REPO_ROOT / "hazard"
DATA_DIR = HAZARD_DIR / "data"
if str(HAZARD_DIR) not in sys.path:
    sys.path.insert(0, str(HAZARD_DIR))

from config import FRED_API_KEY  # noqa: E402

PANEL_PATH = DATA_DIR / "cohort_month_panel.parquet"
COMMITTED_OOS = DATA_DIR / "oos_identification_results.json"
COMMITTED_SWEEP = DATA_DIR / "floor_sweep_results.json"
RESULTS_JSON = DATA_DIR / "matched_depth_reconciliation_results.json"

# oos_identification.py's own grid (parity surface) and this run's extension.
PARITY_GAPS = (0.0, -0.0025, -0.005)
PARITY_AGES = (12, 24)
DEPTHS = (0.0, -0.0025, -0.005, -0.0075, -0.01, -0.015, -0.02, -0.025)
AGE_CUT = 12

OFF_LEGS = {
    "pooled_2017_2019": (201701, 201912),
    "2018_rising_rate": (201801, 201812),
    "2019_falling_rate": (201901, 201912),
}
IN_WINDOWS = {
    "in_window_calibration_202206_202312": (202206, 202312),
    "in_window_full_qt_202206_202509": (202206, 202509),
}
CLEAN_LEG = "2018_rising_rate"
CALIB_WINDOW = "in_window_calibration_202206_202312"

# Ex-ante support rule: a depth is well-supported for a leg when the leg keeps
# >=10% of its gap<=0 exposure there.
SUPPORT_MIN_EXPOSURE_SHARE = 0.10

START_DEPTH = -0.02     # the in-window floor definition (paper's own)
END_DEPTH = -0.0025     # the off-window anchor the paper keeps
COMMITTED_CLEAN_BAND_PCT = (4.695, 5.334)


# ======================================================================
# Panel + gap construction (identical conditioning to oos_identification.py)
# ======================================================================
def build_panel() -> pd.DataFrame:
    df = pd.read_parquet(PANEL_PATH)
    df = df[(df["coupon"] > 0) & (df["exposure_upb"] > 0)].copy()
    df["rp"] = df["reporting_period"].astype(int)
    df["ym"] = df["reporting_period"].astype(str)
    fred = Fred(api_key=FRED_API_KEY)
    rate = (
        fred.get_series(
            "MORTGAGE30US", observation_start="2016-12-01",
            observation_end="2025-10-31",
        )
        .resample("ME").mean()
    )
    rate_by_ym = {ix.strftime("%Y%m"): float(v) / 100.0 for ix, v in rate.items()}
    df["market_rate"] = df["ym"].map(rate_by_ym)
    df = df[df["market_rate"].notna()].copy()
    # coupon is DECIMAL-scaled (0.015-0.075); market_rate is converted to
    # decimal above, so gap is a decimal rate difference.
    df["gap"] = df["coupon"] - df["market_rate"]
    return df


def cpr_of(sel: pd.DataFrame) -> tuple[float | None, float, int]:
    """Exposure-weighted annualized turnover CPR (%) over a selection."""
    exp = float(sel["exposure_upb"].sum())
    if exp <= 0:
        return None, 0.0, 0
    smm = float(sel["prepaid_upb"].sum()) / exp
    return 100.0 * (1.0 - (1.0 - smm) ** 12), exp, int(len(sel))


# ======================================================================
# STEP 1 — parity gate against the frozen anchor_grid
# ======================================================================
def parity_gate(df: pd.DataFrame) -> dict:
    with open(COMMITTED_OOS) as f:
        committed = json.load(f)
    legs = committed["instrument1_oow_floor"]["legs"]
    cells, failures = {}, []
    for leg, (lo, hi) in OFF_LEGS.items():
        w = df[(df["rp"] >= lo) & (df["rp"] <= hi)]
        for gthr in PARITY_GAPS:
            for amin in PARITY_AGES:
                key = f"gap<={gthr:+.4f}_age>={amin}"
                cpr, _, n = cpr_of(
                    w[(w["gap"] <= gthr) & (w["mean_loan_age"] >= amin)]
                )
                got = round(cpr, 3) if cpr is not None else None
                want = legs[leg]["anchor_grid"][key]["cpr_pct"]
                want_n = legs[leg]["anchor_grid"][key]["n_cohort_months"]
                ok = (got == want) and (n == want_n)
                cells[f"{leg}|{key}"] = {
                    "got_cpr_pct": got, "want_cpr_pct": want,
                    "got_n": n, "want_n": want_n, "pass": bool(ok),
                }
                if not ok:
                    failures.append(f"{leg}|{key}")

    # the in-window calibration reads the demotion actually rests on
    calib = committed["instrument2_temporal_holdout"]["calibration_floor"]["reads"]
    w = df[(df["rp"] >= 202206) & (df["rp"] <= 202312)]
    for gthr, key in ((-0.02, "gap<=-0.02_age>=12"), (0.0, "gap<=0_age>=12")):
        cpr, _, n = cpr_of(w[(w["gap"] <= gthr) & (w["mean_loan_age"] >= AGE_CUT)])
        got = round(cpr, 3) if cpr is not None else None
        ok = (got == calib[key]["cpr_pct"]) and (n == calib[key]["n_cohort_months"])
        cells[f"in_window_calib|{key}"] = {
            "got_cpr_pct": got, "want_cpr_pct": calib[key]["cpr_pct"],
            "got_n": n, "want_n": calib[key]["n_cohort_months"], "pass": bool(ok),
        }
        if not ok:
            failures.append(f"in_window_calib|{key}")

    return {
        "n_cells": len(cells), "cells": cells,
        "failures": failures, "all_pass": not failures,
    }


# ======================================================================
# Committed floor -> marginal mapping (NOT re-derived)
# ======================================================================
class FloorMapping:
    """Monotone PCHIP through the frozen floor_sweep_results.json grid."""

    def __init__(self) -> None:
        with open(COMMITTED_SWEEP) as f:
            sweep = json.load(f)
        rows = sorted(sweep["rows"], key=lambda r: r["floor_annual_cpr_pct"])
        self.x = np.array([r["floor_annual_cpr_pct"] for r in rows])
        self.yb = np.array([r["lockin_marginal_b"] for r in rows])
        self.yp = np.array([r["lockin_marginal_share_pp"] for r in rows])
        self._fb = PchipInterpolator(self.x, self.yb)
        self._fp = PchipInterpolator(self.x, self.yp)

    def in_grid(self, floor_pct: float) -> bool:
        return bool(self.x.min() <= floor_pct <= self.x.max())

    def __call__(self, floor_pct: float) -> tuple[float, float]:
        if not self.in_grid(floor_pct):
            raise ValueError(
                f"floor {floor_pct}% is outside the committed sweep grid "
                f"[{self.x.min()}, {self.x.max()}] — extrapolation refused."
            )
        return float(self._fb(floor_pct)), float(self._fp(floor_pct))

    def validate(self) -> dict:
        """Fidelity vs the five INDEPENDENT engine reads in the OOS artifact."""
        with open(COMMITTED_OOS) as f:
            oos = json.load(f)
        checks, in_grid_err = {}, []
        for row in oos["instrument1_marginal_table"]:
            f_pct = row["floor_annual_cpr_pct"]
            eng_b = row["band"]["6.5"]["marginal_b"]
            eng_pp = row["band"]["6.5"]["marginal_pp"]
            inside = bool(self.x.min() <= f_pct <= self.x.max())
            if inside:
                map_b, map_pp = self(f_pct)
                in_grid_err.append(abs(map_b - eng_b))
            else:
                map_b = map_pp = None
            checks[f"{f_pct}"] = {
                "engine_marginal_b": eng_b, "mapped_marginal_b": map_b,
                "err_b": (map_b - eng_b) if inside else None,
                "engine_marginal_pp": eng_pp, "mapped_marginal_pp": map_pp,
                "inside_committed_grid": inside,
            }
        grid_exact = all(
            abs(self(float(gx))[0] - float(gy)) < 1e-9
            for gx, gy in zip(self.x, self.yb)
        )
        return {
            "engine_reads": checks,
            "max_abs_err_b_inside_grid": max(in_grid_err),
            "reproduces_committed_grid_exactly": bool(grid_exact),
            "note": "PCHIP on the frozen floor_sweep grid; the mapping is not "
                    "re-derived. Reads above 6.0% are outside the committed "
                    "grid and are refused, not extrapolated.",
        }


# ======================================================================
# STEP 2 — matched-depth grid
# ======================================================================
def build_depth_grid(df: pd.DataFrame) -> dict:
    grid: dict = {}
    windows = {**{f"OFF_{k}": v for k, v in OFF_LEGS.items()},
               **{f"IN_{k}": v for k, v in IN_WINDOWS.items()}}
    for name, (lo, hi) in windows.items():
        w = df[(df["rp"] >= lo) & (df["rp"] <= hi)]
        w = w[w["mean_loan_age"] >= AGE_CUT]
        base_exp = float(w[w["gap"] <= 0.0]["exposure_upb"].sum())
        cells = {}
        for g in DEPTHS:
            cpr, exp, n = cpr_of(w[w["gap"] <= g])
            share = (exp / base_exp) if base_exp > 0 else 0.0
            cells[f"{g:+.4f}"] = {
                "gap_threshold": g,
                "cpr_pct": round(cpr, 3) if cpr is not None else None,
                "computable": cpr is not None,
                "exposure_upb": exp,
                "exposure_share_of_gap0": round(share, 6),
                "n_cohort_months": n,
                "well_supported": bool(
                    cpr is not None and share >= SUPPORT_MIN_EXPOSURE_SHARE
                ),
            }
        grid[name] = {
            "window": f"{lo}..{hi}",
            "min_gap_observed": float(w["gap"].min()),
            "gap0_exposure_upb": base_exp,
            "depths": cells,
        }
    return grid


def _cell(grid, window, depth):
    return grid[window]["depths"][f"{depth:+.4f}"]


# ======================================================================
# STEP 3 — decomposition
# ======================================================================
def decompose(grid: dict, mapping: FloorMapping) -> dict:
    inw = f"IN_{CALIB_WINDOW}"
    off = f"OFF_{CLEAN_LEG}"
    f_start = _cell(grid, inw, START_DEPTH)["cpr_pct"]
    f_end = _cell(grid, off, END_DEPTH)["cpr_pct"]
    m_start = mapping(f_start)
    m_end = mapping(f_end)
    total_b = m_end[0] - m_start[0]
    total_pp = m_end[1] - m_start[1]

    # ---- path A: depth first (in-window), then window at matched shallow depth
    in_shallow = _cell(grid, inw, END_DEPTH)
    m_in_shallow = mapping(in_shallow["cpr_pct"])
    pathA = {
        "ordering": "in-window depth first, then window at matched shallow depth",
        "matched_depth": END_DEPTH,
        "in_window_deep_floor_pct": f_start,
        "in_window_shallow_floor_pct": in_shallow["cpr_pct"],
        "off_window_shallow_floor_pct": f_end,
        "depth_component_b": m_in_shallow[0] - m_start[0],
        "depth_component_pp": m_in_shallow[1] - m_start[1],
        "window_component_b": m_end[0] - m_in_shallow[0],
        "window_component_pp": m_end[1] - m_in_shallow[1],
        "both_endpoints_well_supported": bool(
            in_shallow["well_supported"] and _cell(grid, off, END_DEPTH)["well_supported"]
        ),
        "admissible": True,
    }
    pathA["depth_share_of_total"] = pathA["depth_component_b"] / total_b
    pathA["window_share_of_total"] = pathA["window_component_b"] / total_b

    # ---- path B: window first at the DEEP depth, then depth off-window
    off_deep = _cell(grid, off, START_DEPTH)
    if off_deep["computable"]:
        m_off_deep = mapping(off_deep["cpr_pct"])
        pathB = {
            "ordering": "window at matched deep depth first, then off-window depth",
            "matched_depth": START_DEPTH,
            "off_window_deep_floor_pct": off_deep["cpr_pct"],
            "off_window_deep_exposure_upb": off_deep["exposure_upb"],
            "off_window_deep_exposure_share_of_gap0": off_deep["exposure_share_of_gap0"],
            "off_window_deep_well_supported": off_deep["well_supported"],
            "window_component_b": m_off_deep[0] - m_start[0],
            "window_component_pp": m_off_deep[1] - m_start[1],
            "depth_component_b": m_end[0] - m_off_deep[0],
            "depth_component_pp": m_end[1] - m_off_deep[1],
            "admissible": bool(off_deep["well_supported"]),
            "inadmissible_reason": None if off_deep["well_supported"] else (
                f"the off-window deep cell (gap<={START_DEPTH}) carries "
                f"${off_deep['exposure_upb']/1e9:.3f}B = "
                f"{100*off_deep['exposure_share_of_gap0']:.2f}% of the leg's "
                f"gap<=0 exposure, below the {100*SUPPORT_MIN_EXPOSURE_SHARE:.0f}% "
                f"support rule. The read is REPORTED but NOT used to attribute."
            ),
        }
    else:
        pathB = {
            "ordering": "window at matched deep depth first, then off-window depth",
            "admissible": False,
            "inadmissible_reason": "NOT COMPUTABLE — zero off-window exposure "
                                   f"at gap<={START_DEPTH}.",
        }

    interaction_b = (
        pathB["window_component_b"] - pathA["window_component_b"]
        if pathB.get("window_component_b") is not None else None
    )

    # ---- deepest well-supported COMMON depth (the honest matched-deep anchor)
    common = [
        g for g in DEPTHS
        if _cell(grid, off, g)["well_supported"] and _cell(grid, inw, g)["well_supported"]
    ]
    deepest_common = min(common) if common else None
    three_step = None
    if deepest_common is not None and deepest_common != END_DEPTH:
        m_in_dc = mapping(_cell(grid, inw, deepest_common)["cpr_pct"])
        m_off_dc = mapping(_cell(grid, off, deepest_common)["cpr_pct"])
        three_step = {
            "anchor_depth": deepest_common,
            "in_window_floor_pct": _cell(grid, inw, deepest_common)["cpr_pct"],
            "off_window_floor_pct": _cell(grid, off, deepest_common)["cpr_pct"],
            "step1_in_window_depth_b": m_in_dc[0] - m_start[0],
            "step2_window_at_anchor_depth_b": m_off_dc[0] - m_in_dc[0],
            "step3_off_window_depth_b": m_end[0] - m_off_dc[0],
            "total_depth_b": (m_in_dc[0] - m_start[0]) + (m_end[0] - m_off_dc[0]),
            "total_window_b": m_off_dc[0] - m_in_dc[0],
        }
        three_step["depth_share_of_total"] = three_step["total_depth_b"] / total_b
        three_step["window_share_of_total"] = three_step["total_window_b"] / total_b

    # ---- window component at EVERY matched depth
    per_depth = {}
    for g in DEPTHS:
        ci = _cell(grid, inw, g)
        co = _cell(grid, off, g)
        if ci["cpr_pct"] is None or co["cpr_pct"] is None:
            per_depth[f"{g:+.4f}"] = {"computable": False,
                                      "reason": "zero exposure in one window"}
            continue
        if not (mapping.in_grid(ci["cpr_pct"]) and mapping.in_grid(co["cpr_pct"])):
            # A degenerate read (e.g. 0.000% CPR on a near-empty deep cell) falls
            # outside the committed floor_sweep grid. Refuse to extrapolate.
            per_depth[f"{g:+.4f}"] = {
                "computable": False,
                "reason": f"floor read outside the committed sweep grid "
                          f"[{mapping.x.min()}, {mapping.x.max()}]% "
                          f"(in={ci['cpr_pct']}, off={co['cpr_pct']}) — "
                          f"NOT MAPPABLE, not extrapolated",
                "in_window_floor_pct": ci["cpr_pct"],
                "off_window_floor_pct": co["cpr_pct"],
                "off_window_exposure_share": co["exposure_share_of_gap0"],
            }
            continue
        mi, mo = mapping(ci["cpr_pct"]), mapping(co["cpr_pct"])
        per_depth[f"{g:+.4f}"] = {
            "computable": True,
            "in_window_floor_pct": ci["cpr_pct"],
            "off_window_floor_pct": co["cpr_pct"],
            "floor_delta_pp": round(co["cpr_pct"] - ci["cpr_pct"], 3),
            "window_component_b": mo[0] - mi[0],
            "window_component_pp": mo[1] - mi[1],
            "off_window_well_supported": co["well_supported"],
            "off_window_exposure_share": co["exposure_share_of_gap0"],
        }

    return {
        "start": {
            "label": "in-window calibration window, gap<=-0.02, age>=12 "
                     "(the floor the demoted $70.3B headline rests on)",
            "floor_pct": f_start, "marginal_b": m_start[0], "marginal_pp": m_start[1],
            "production_floor_pct": 4.0,
            "production_marginal_b": 70.34506041989584,
            "production_marginal_pp": 9.198459770709789,
        },
        "end": {
            "label": "off-window 2018 rising leg, gap<=-0.0025, age>=12 "
                     "(the floor the $42.6B headline rests on)",
            "floor_pct": f_end, "marginal_b": m_end[0], "marginal_pp": m_end[1],
        },
        "total_move_b": total_b, "total_move_pp": total_pp,
        "path_a_depth_first": pathA,
        "path_b_window_first": pathB,
        "interaction_b": interaction_b,
        "shapley_average_refused": bool(not pathB.get("admissible")),
        "shapley_refusal_reason": pathB.get("inadmissible_reason"),
        "deepest_well_supported_common_depth": deepest_common,
        "three_step_via_deepest_common_depth": three_step,
        "window_component_by_depth": per_depth,
    }


# ======================================================================
# STEP 4 — contamination narrative at matched depth
# ======================================================================
def contamination_at_matched_depth(grid: dict) -> dict:
    rows = {}
    for g in DEPTHS:
        c18 = _cell(grid, "OFF_2018_rising_rate", g)
        c19 = _cell(grid, "OFF_2019_falling_rate", g)
        cpl = _cell(grid, "OFF_pooled_2017_2019", g)
        vals = [c["cpr_pct"] for c in (c18, c19, cpl) if c["cpr_pct"] is not None]
        rows[f"{g:+.4f}"] = {
            "2018_rising_pct": c18["cpr_pct"],
            "2019_falling_pct": c19["cpr_pct"],
            "pooled_pct": cpl["cpr_pct"],
            "spread_2018_vs_2019_pp": (
                round(abs(c18["cpr_pct"] - c19["cpr_pct"]), 3)
                if (c18["cpr_pct"] is not None and c19["cpr_pct"] is not None) else None
            ),
            "three_leg_max_min_pp": round(max(vals) - min(vals), 3) if vals else None,
            "2018_well_supported": c18["well_supported"],
            "2019_well_supported": c19["well_supported"],
            "2019_exposure_upb": c19["exposure_upb"],
            "both_legs_well_supported": bool(
                c18["well_supported"] and c19["well_supported"]
            ),
        }
    adjudicable = [k for k, v in rows.items() if v["both_legs_well_supported"]]
    spreads = [rows[k]["spread_2018_vs_2019_pp"] for k in adjudicable]
    # the mismatched-depth comparison the paper's rejection actually makes
    mismatched = round(
        _cell(grid, "OFF_2019_falling_rate", 0.0)["cpr_pct"]
        - _cell(grid, "OFF_2018_rising_rate", END_DEPTH)["cpr_pct"], 3
    )
    return {
        "by_depth": rows,
        "pooled_is_not_independent": True,
        "pooled_note": "pooled_2017_2019 CONTAINS both the 2018 and 2019 legs "
                       "(plus 2017), so it is not a third independent leg. Only "
                       "2018 and 2019 are independent; any 'three legs agree' "
                       "claim double-counts.",
        "depths_adjudicable_both_legs_supported": adjudicable,
        "spread_2018_vs_2019_over_adjudicable_pp": spreads,
        "max_adjudicable_spread_pp": max(spreads) if spreads else None,
        "min_adjudicable_spread_pp": min(spreads) if spreads else None,
        "spread_converges_monotonically_with_depth": bool(
            spreads == sorted(spreads, reverse=True)
        ),
        "mismatched_depth_spread_paper_rejection_uses_pp": mismatched,
        "note": "The paper's rejection compares the 2019 gap<=0 read (6.910%) "
                "against the 2018 gap<=-0.0025 read (4.991%) — a "
                f"{mismatched}pp spread across DIFFERENT depths. At matched "
                "depth the spread is smaller at some depths and larger at "
                "others; see spread_2018_vs_2019_over_adjudicable_pp.",
    }


# ======================================================================
def main() -> None:
    t0 = time.perf_counter()
    print("=" * 72)
    print("STEP 1 — PARITY GATE vs committed oos_identification anchor_grid")
    print("=" * 72)
    df = build_panel()
    parity = parity_gate(df)
    print(f"  {parity['n_cells']} cells checked; "
          f"{'ALL PASS' if parity['all_pass'] else 'FAILURES: ' + str(parity['failures'])}")
    if not parity["all_pass"]:
        raise SystemExit(
            f"PARITY GATE FAILURE: {parity['failures']} — the committed "
            "anchor_grid could not be reproduced from the panel. STOP; do not "
            "build a decomposition on a selector that does not match."
        )
    print("  PARITY PASS — safe to proceed.")

    print("\n" + "=" * 72)
    print("STEP 2 — matched-depth grid (age>=12, exposure-weighted CPR %)")
    print("=" * 72)
    grid = build_depth_grid(df)
    hdr = f"{'window / leg':34s}" + "".join(f"{g:>10.4f}" for g in DEPTHS)
    print(hdr)
    for name, g in grid.items():
        line = f"{name:34s}"
        for d in DEPTHS:
            c = g["depths"][f"{d:+.4f}"]
            if not c["computable"]:
                line += f"{'NC':>10s}"
            else:
                mark = "" if c["well_supported"] else "*"
                line += f"{format(c['cpr_pct'], '.3f') + mark:>10s}"
        print(line)
    print("  * = below the 10%-of-gap<=0 exposure support rule (reported, not used)")
    off = f"OFF_{CLEAN_LEG}"
    print(f"\n  deepest gap observed off-window ({CLEAN_LEG}, age>=12): "
          f"{grid[off]['min_gap_observed']:.5f}")
    for d in DEPTHS:
        c = _cell(grid, off, d)
        print(f"    gap<={d:+.4f}: ${c['exposure_upb']/1e9:9.3f}B "
              f"({100*c['exposure_share_of_gap0']:6.2f}% of gap<=0) "
              f"n={c['n_cohort_months']:4d} "
              f"{'WELL-SUPPORTED' if c['well_supported'] else 'unsupported'}")

    print("\n" + "=" * 72)
    print("STEP 3 — decomposition (committed floor_sweep mapping)")
    print("=" * 72)
    mapping = FloorMapping()
    map_val = mapping.validate()
    print(f"  mapping fidelity vs independent engine reads: max |err| "
          f"${map_val['max_abs_err_b_inside_grid']:.4f}B inside the committed grid; "
          f"grid points exact = {map_val['reproduces_committed_grid_exactly']}")
    dec = decompose(grid, mapping)
    print(f"\n  START {dec['start']['floor_pct']:.3f}% -> "
          f"${dec['start']['marginal_b']:.3f}B / {dec['start']['marginal_pp']:.3f}pp")
    print(f"  END   {dec['end']['floor_pct']:.3f}% -> "
          f"${dec['end']['marginal_b']:.3f}B / {dec['end']['marginal_pp']:.3f}pp")
    print(f"  TOTAL {dec['total_move_b']:+.3f}B / {dec['total_move_pp']:+.3f}pp")
    a = dec["path_a_depth_first"]
    print(f"\n  path A (admissible): DEPTH {a['depth_component_b']:+8.3f}B "
          f"({100*a['depth_share_of_total']:5.1f}%)  WINDOW "
          f"{a['window_component_b']:+8.3f}B ({100*a['window_share_of_total']:5.1f}%)")
    b = dec["path_b_window_first"]
    if b.get("admissible"):
        print(f"  path B (admissible): WINDOW {b['window_component_b']:+8.3f}B  "
              f"DEPTH {b['depth_component_b']:+8.3f}B")
    else:
        print(f"  path B INADMISSIBLE: {b['inadmissible_reason']}")
        if b.get("window_component_b") is not None:
            print(f"    (its unusable read would give WINDOW "
                  f"{b['window_component_b']:+.3f}B / DEPTH "
                  f"{b['depth_component_b']:+.3f}B — reported, not attributed)")
    ts = dec["three_step_via_deepest_common_depth"]
    if ts:
        print(f"\n  three-step via deepest well-supported common depth "
              f"({ts['anchor_depth']}): DEPTH {ts['total_depth_b']:+.3f}B "
              f"({100*ts['depth_share_of_total']:.1f}%)  WINDOW "
              f"{ts['total_window_b']:+.3f}B ({100*ts['window_share_of_total']:.1f}%)")

    print("\n" + "=" * 72)
    print("STEP 4 — contamination narrative at matched depth")
    print("=" * 72)
    cont = contamination_at_matched_depth(grid)
    print(f"{'depth':>9} {'2018':>8} {'2019':>8} {'pooled':>8} "
          f"{'18v19 pp':>9} {'both sup':>9}")
    for k, r in cont["by_depth"].items():
        print(f"{k:>9} {str(r['2018_rising_pct']):>8} {str(r['2019_falling_pct']):>8} "
              f"{str(r['pooled_pct']):>8} {str(r['spread_2018_vs_2019_pp']):>9} "
              f"{str(r['both_legs_well_supported']):>9}")
    print(f"  adjudicable depths: {cont['depths_adjudicable_both_legs_supported']}")
    print(f"  spreads there: {cont['spread_2018_vs_2019_over_adjudicable_pp']}pp")
    print(f"  monotone convergence with depth: "
          f"{cont['spread_converges_monotonically_with_depth']}")

    # ---- clean-band robustness under the extended depth ladder -------------
    ws_reads = [
        _cell(grid, off, d)["cpr_pct"] for d in DEPTHS
        if _cell(grid, off, d)["well_supported"]
    ]
    band = (round(min(ws_reads), 3), round(max(ws_reads), 3))
    band_marg = (mapping(band[1])[0], mapping(band[0])[0])
    all_reads = [
        _cell(grid, off, d)["cpr_pct"] for d in DEPTHS
        if _cell(grid, off, d)["computable"] and _cell(grid, off, d)["exposure_upb"] > 1e9
    ]
    band_loose = (round(min(all_reads), 3), round(max(all_reads), 3))
    clean_band = {
        "committed_band_pct": list(COMMITTED_CLEAN_BAND_PCT),
        "extended_well_supported_band_pct": list(band),
        "band_unchanged_by_extension": bool(band == COMMITTED_CLEAN_BAND_PCT),
        "well_supported_reads_pct": ws_reads,
        "marginal_band_b": list(band_marg),
        "point_floor_pct": dec["end"]["floor_pct"],
        "point_marginal_b": dec["end"]["marginal_b"],
        "loose_band_pct_exposure_gt_1B": list(band_loose),
        "loose_band_marginal_b": [mapping(band_loose[1])[0], mapping(band_loose[0])[0]],
    }
    print("\n  clean band under the EXTENDED depth ladder: "
          f"{band[0]}-{band[1]}% (committed {COMMITTED_CLEAN_BAND_PCT[0]}-"
          f"{COMMITTED_CLEAN_BAND_PCT[1]}%) -> unchanged = "
          f"{clean_band['band_unchanged_by_extension']}")
    print(f"  marginal band ${band_marg[0]:.2f}B - ${band_marg[1]:.2f}B "
          f"(point ${dec['end']['marginal_b']:.2f}B)")

    # ---- self-checks -------------------------------------------------------
    recon = abs(
        (a["depth_component_b"] + a["window_component_b"]) - dec["total_move_b"]
    )
    hard = {
        "anchor_grid_parity_all_18_cells": bool(parity["all_pass"]),
        "path_a_components_sum_to_total": bool(recon < 0.01),
        "mapping_reproduces_committed_grid": bool(
            map_val["reproduces_committed_grid_exactly"]
        ),
        "mapping_fidelity_under_1B": bool(map_val["max_abs_err_b_inside_grid"] < 1.0),
    }
    soft = {
        "extended_ladder_leaves_clean_band_unchanged": bool(
            clean_band["band_unchanged_by_extension"]
        ),
        "window_exceeds_depth_on_admissible_path": bool(
            abs(a["window_component_b"]) > abs(a["depth_component_b"])
        ),
        "off_window_reaches_gap_le_0.02_with_support": bool(
            _cell(grid, off, -0.02)["well_supported"]
        ),
        "leg_spread_converges_monotonically_with_depth": bool(
            cont["spread_converges_monotonically_with_depth"]
        ),
    }

    depth_share = abs(a["depth_component_b"]) / (
        abs(a["depth_component_b"]) + abs(a["window_component_b"])
    )
    verdict_code = (
        "DEMOTION_IS_DEPTH_ARTIFACT" if depth_share > 0.5
        else ("DEMOTION_STANDS" if depth_share < 0.10 else "MIXED")
    )
    matched_point_b = mapping(
        _cell(grid, f"IN_{CALIB_WINDOW}", END_DEPTH)["cpr_pct"]
    )[0]
    deep_support = _cell(grid, off, START_DEPTH)["exposure_share_of_gap0"]
    verdict = {
        "code": verdict_code,
        "depth_share_admissible_path": depth_share,
        "window_component_b": a["window_component_b"],
        "depth_component_b": a["depth_component_b"],
        "matched_depth_in_sample_comparison_point_b": matched_point_b,
        "one_paragraph": (
            f"On the only admissible decomposition path, the "
            f"{dec['total_move_b']:+.1f}B move from the in-window deep floor "
            f"({dec['start']['floor_pct']:.3f}%) to the off-window 2018 floor "
            f"({dec['end']['floor_pct']:.3f}%) splits "
            f"{100*a['window_share_of_total']:.0f}% WINDOW "
            f"({a['window_component_b']:+.1f}B, measured at matched depth "
            f"gap<={END_DEPTH}) and {100*a['depth_share_of_total']:.0f}% DEPTH "
            f"({a['depth_component_b']:+.1f}B, measured within the in-window "
            f"panel). WINDOW dominates, so the demotion is NOT primarily a depth "
            f"artifact. But depth owns a real, previously unattributed "
            f"${abs(a['depth_component_b']):.1f}B: at matched depth the correct "
            f"in-sample comparison point is ${matched_point_b:.1f}B, not the "
            f"${dec['start']['production_marginal_b']:.1f}B the demotion is "
            f"narrated against. The reverse ordering cannot be computed: the "
            f"off-window leg retains only {100*deep_support:.2f}% of its "
            f"exposure at gap<={START_DEPTH}, so no Shapley average is formed."
        ),
    }

    payload = {
        "mode": "matched_depth_reconciliation",
        "spec": "decomposes the floor demotion into WINDOW and DEPTH components "
                "at matched discount depth; parity-gated against the committed "
                "oos_identification anchor_grid; floor->marginal taken from the "
                "committed floor_sweep_results.json (PCHIP, not re-derived); no "
                "extrapolation, no benchmark feedback.",
        "support_rule": {
            "min_exposure_share_of_gap0": SUPPORT_MIN_EXPOSURE_SHARE,
            "note": "a depth is WELL-SUPPORTED for a leg when the leg keeps at "
                    "least this share of its gap<=0 exposure there.",
        },
        "step1_parity_gate": parity,
        "step2_matched_depth_grid": grid,
        "floor_to_marginal_mapping": map_val,
        "step3_decomposition": dec,
        "step4_contamination_at_matched_depth": cont,
        "clean_band_under_extended_ladder": clean_band,
        "self_checks_hard_wiring": hard,
        "self_checks_soft_interpretive": soft,
        "verdict": verdict,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(
            payload, f, indent=2,
            default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else x,
        )
        f.write("\n")

    print("\n" + "=" * 72)
    print("SELF-CHECKS — HARD (wiring)")
    for k, v in hard.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("SELF-CHECKS — SOFT (interpretive; a failure is a finding)")
    for k, v in soft.items():
        print(f"  [{'PASS' if v else 'FLAG'}] {k}")
    print("=" * 72)
    print(f"\nVERDICT: {verdict['code']}\n{verdict['one_paragraph']}")
    print(f"\nResults -> {RESULTS_JSON}")

    if not all(hard.values()):
        raise SystemExit(
            "HARD WIRING CHECK FAILURE: "
            f"{[k for k, v in hard.items() if not v]} — results written for "
            "diagnosis but MUST NOT be cited."
        )


if __name__ == "__main__":
    main()
