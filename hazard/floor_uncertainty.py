#!/usr/bin/env python3
"""
floor_uncertainty.py — sampling uncertainty of the floor reads (MF-4) and
age-composition adjustment of the off-window floor (MF-3).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
floor_sweep.py / oos_identification.py / matched_depth_reconciliation.py /
floor_form_offwindow.py).

Referee objections (round 21):
  MF-4: the floor is an ESTIMATED quantity — an exposure-weighted CPR on a
        finite panel — yet no sampling uncertainty is ever computed for any
        floor read; every quoted floor (5.334/4.991/4.695 off-window,
        3.972 in-window) is treated as if measured without error.
  MF-3: the off-window floor is measured on mechanically YOUNG loans (the 2018
        rising-rate leg's OTM cohorts are all recently-originated, max age
        17.5 months), and the resulting seasoning bias is never propagated to
        the floor or the marginal.

DESIGN (fixed ex ante). NO microsim engine runs anywhere in this script. The
floor -> marginal mapping is the COMMITTED monotone PCHIP through the frozen
floor_sweep_results.json grid {2, 3, 3.5, 4, 4.5, 5, 6}%, rebuilt exactly as
matched_depth_reconciliation.py rebuilds it (its FloorMapping class is
imported, not reimplemented), validated against the independent engine reads
in oos_identification_results.json, and never extrapolated. All floor reads
use the panel conditioning of oos_identification.py via the imported
matched_depth_reconciliation.build_panel (coupon>0 & exposure_upb>0;
gap = coupon - MORTGAGE30US/100 on the calendar-month FRED mean; exposure-
weighted SMM -> CPR = 1-(1-SMM)^12, via matched_depth_reconciliation.cpr_of;
out_of_window_floor.py's inline cpr_of is the same computation decimal-scaled).

=======================================================================
PART A — SAMPLING UNCERTAINTY OF THE FLOOR READS (MF-4)
=======================================================================
Cluster bootstrap over the cohort-month panel used for each committed floor
read. Clusters = the panel's 4-way strata (vintage x coupon x fico_bucket x
ltv_bucket; stratum.build_stratum_id — the unit that repeats over reporting
months, so within-cluster serial dependence is preserved; same cluster unit
as bootstrap_se.py's stratum block bootstrap). 1000 replicates; a fresh
np.random.default_rng(42) per read (per-read determinism, independent of read
order). Each replicate draws C clusters with replacement (C = number of
strata in the selection) and recomputes the exposure-weighted CPR from the
resampled cluster sums.

Floor reads bootstrapped (point estimates parity-gated FIRST, see gates):
  R1  2018 leg (201801..201812), gap<=+0.0000, age>=12   committed 5.334%
  R2  2018 leg,                  gap<=-0.0025, age>=12   committed 4.991%
  R3  2018 leg,                  gap<=-0.0050, age>=12   committed 4.695%
  R4  in-window production anchor: the Instrument-2 calibration read of
      oos_identification.py — window 202206..202312, gap<=-0.02, age>=12,
      committed 3.972% (h_cal; the in-window floor anchor the demotion
      decomposition uses; sits next to the 4.0% production floor).
  R5  SUPPLEMENTARY: out_of_window_floor.py's in-window 2023-24 deep-OTM
      validation read — window 202301..202412, gap<=-0.02, age>=12,
      committed 3.840%. (The finding's "2023-24 deep-OTM 3.972%" phrasing
      conflates two committed reads: 3.972% lives on the 202206..202312
      calibration window, 3.840% on 202301..202412. Both are bootstrapped;
      R4 is the primary in-window anchor, R5 pins the PART B population.)

For each read: bootstrap SE, percentile 95% CI [2.5, 97.5], and the CI
propagated through the committed PCHIP map -> 95% CI of the lock-in marginal
($B and pp) at the central elasticity (6.5). Replicate floors falling outside
the committed sweep grid [2.0, 6.0]% are NOT extrapolated: they are excluded
from the mapped CI, counted, and the CI flagged truncated if any occur.

EX-ANTE FRAMING (MF-4): compare the sampling 95% CI (pp, at the R2 anchor,
committed point +5.5716pp = manuscript +5.57 at 4.991%) against the
manuscript's depth-cut band +4.3..+6.8pp (committed +4.2657..+6.7711pp,
width 2.5054pp). WHICHEVER IS WIDER IS THE BINDING UNCERTAINTY AND THE
MANUSCRIPT MUST SAY WHICH. No further discretion after the run.

=======================================================================
PART B — AGE-COMPOSITION ADJUSTMENT OF THE OFF-WINDOW FLOOR (MF-3)
=======================================================================
Age buckets: {[0,12), [12,24), [24,36), [36,inf)}.
  B1  2018-leg reads by age bucket at gap<=-0.0025 (the committed point
      anchor's own depth). Known ex ante: the 2018 leg has NO age>=24 OTM
      cohort-months (committed note in oos_identification_results.json), so
      the [24,36) and [36,inf) buckets are expected empty and imputed.
  B2  In-window 2023-24 deep-OTM discount-cohort turnover (202301..202412,
      gap<=-0.02 — refi-free by rate configuration and seasoned) by the same
      buckets: its age gradient is the involuntary-age gradient the
      adjustment needs. Exposure weights w_k over the buckets from the same
      population.
  B3  Age-standardized off-window floor
          F_adj = sum_k w_k * read2018_k
      with EXPLICITLY-LABELED imputation for buckets where the 2018 leg has
      no OTM exposure:
          read2018_k := read2018_oldest_populated
                        * ( CPR_inwindow_k / CPR_inwindow_oldest_populated )
      (in-window ratio scaling of the oldest populated 2018 bucket). If the
      in-window CPR of the oldest populated 2018 bucket is itself not
      computable or zero, fall back to FLAT imputation (read2018_oldest,
      no scaling), flagged. Buckets with zero in-window weight contribute
      nothing and need no imputation. The imputed share of weight is printed
      and frozen in the artifact.
  B4  Map F_adj through the committed PCHIP map -> adjusted marginal
      ($B and pp at 6.5). If F_adj falls outside the committed grid the
      mapping is REFUSED (never extrapolated) and the threshold verdict is
      stated on the floor value alone.

EX-ANTE THRESHOLDS (verbatim):
  T1 if the age-standardized floor lands above 5.334% (the committed band
     top), the clean band is one-sided-open downward and the manuscript's
     +4.3 lower bound is not conservative — the revision must state the band
     as open below +4.3 (or extend it to the adjusted read).
  T2 if it lands inside [4.695, 5.334], the band stands with the adjustment
     reported as within-band.
  T3 if below 4.695%, the seasoning-bias concern is refuted and reported as
     such.

=======================================================================
PARITY GATES (BLOCKING; run before any bootstrap/adjustment; on any failure
the JSON is written with status GATE_FAILURE and the run stops)
=======================================================================
  G1a/b/c  R1/R2/R3 point reads vs the committed 2018-leg anchor_grid cells
           in oos_identification_results.json {5.334, 4.991, 4.695}%:
           |got - committed| <= 0.001pp AND n_cohort_months equal
           (committed n = 155/137/125).
  G2       R4 point read vs the committed Instrument-2 calibration read
           3.972% (n=2838): |got - committed| <= 0.01pp AND n equal.
  G3       R5 point read vs the committed out_of_window_floor_results.json
           in_window_deep_OTM_validation gap<=-0.02_age>=12 read 3.840%
           (n=3984): |got - committed| <= 0.01pp AND n equal.
  G4       PCHIP mapping: reproduces the committed floor_sweep grid points
           exactly (<1e-9) AND max |mapped - engine| <= $0.69B over the
           committed oos_identification instrument1 rows inside the grid
           (the matched_depth_reconciliation fidelity, committed $0.687B).
All committed values are consumed from the frozen artifacts at runtime and
asserted equal (1e-9) to the constants quoted in this header before gating.

Run:  cd hazard && python3 floor_uncertainty.py
      -> data/floor_uncertainty_results.json  (frozen)
No engine runs; no caches; runtime is seconds (one FRED MORTGAGE30US fetch).
Does NOT change config.py production defaults. Does NOT edit any .tex file.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Selection/aggregation and PCHIP machinery are IMPORTED from
# matched_depth_reconciliation (build_panel / cpr_of / FloorMapping), not
# reimplemented: build_panel carries oos_identification.py's exact panel
# conditioning, cpr_of is out_of_window_floor.py's aggregation percent-scaled,
# and FloorMapping is the committed floor_sweep PCHIP with extrapolation
# refused. Importing the module executes only imports and constants (main()
# is __main__-guarded).
import matched_depth_reconciliation as mdr
from stratum import build_stratum_id

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "floor_uncertainty_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
OOW_ARTIFACT = DATA_DIR / "out_of_window_floor_results.json"

N_REPS = 1000
SEED = 42
CENTRAL_PQ = "6.5"

# ---- committed anchors quoted ex ante (asserted vs artifacts at runtime) ----
CLEAN_BAND_QUOTED = {  # 2018 rising-rate leg, age>=12 (cpr_pct, n_cohort_months)
    "gap<=+0.0000_age>=12": (5.334, 155),
    "gap<=-0.0025_age>=12": (4.991, 137),
    "gap<=-0.0050_age>=12": (4.695, 125),
}
INWINDOW_CALIB_QUOTED = (3.972, 2838)     # oos Instrument-2, 202206..202312
INWINDOW_2324_QUOTED = (3.840, 3984)      # out_of_window_floor, 202301..202412
POINT_MARGINAL_QUOTED_B = 42.60839388108866    # at 4.991%, central 6.5
POINT_MARGINAL_QUOTED_PP = 5.571558182909726
DEPTH_CUT_BAND_QUOTED_PP = (4.265670450690081, 6.771052540089784)  # 5.334/4.695
MAPPING_MAX_ERR_B = 0.69                  # matched_depth committed $0.687B

TOL_CLEAN_PP = 0.001
TOL_INWINDOW_PP = 0.01

LEG_2018 = (201801, 201812)
CALIB_WINDOW = (202206, 202312)
INW_2324 = (202301, 202412)

AGE_BUCKETS_B = [(0.0, 12.0), (12.0, 24.0), (24.0, 36.0), (36.0, float("inf"))]

COMMITTED_BAND_BOT_PCT = 4.695
COMMITTED_BAND_TOP_PCT = 5.334


def _bucket_label(lo: float, hi: float) -> str:
    return f"[{lo:g},{hi:g})" if np.isfinite(hi) else f"[{lo:g},inf)"


def _select(df: pd.DataFrame, rp_lo: int, rp_hi: int, gap_thr: float,
            age_min: float) -> pd.DataFrame:
    return df[(df["rp"] >= rp_lo) & (df["rp"] <= rp_hi)
              & (df["gap"] <= gap_thr) & (df["mean_loan_age"] >= age_min)]


def cluster_bootstrap_cpr(sel: pd.DataFrame, n_reps: int = N_REPS,
                          seed: int = SEED) -> tuple[np.ndarray, int]:
    """Cluster bootstrap of the exposure-weighted annual CPR (%) over a
    selection. Clusters = 4-way strata; each replicate draws C clusters with
    replacement and recomputes CPR from the resampled cluster sums."""
    g = sel.groupby("stratum", sort=True)[["prepaid_upb", "exposure_upb"]].sum()
    pre = g["prepaid_upb"].to_numpy(dtype=np.float64)
    exp = g["exposure_upb"].to_numpy(dtype=np.float64)
    n_clusters = len(g)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_clusters, size=(n_reps, n_clusters))
    smm = pre[idx].sum(axis=1) / exp[idx].sum(axis=1)
    draws = 100.0 * (1.0 - (1.0 - smm) ** 12)
    return draws, n_clusters


def _map_draws(mapping: mdr.FloorMapping, draws: np.ndarray) -> dict:
    """Map floor draws (%) through the committed PCHIP; out-of-grid draws are
    excluded and counted, never extrapolated."""
    in_grid = np.array([mapping.in_grid(float(d)) for d in draws])
    mapped = [mapping(float(d)) for d in draws[in_grid]]
    n_out = int((~in_grid).sum())
    if not mapped:
        return {"computable": False, "n_draws_outside_grid": n_out}
    b = np.array([m[0] for m in mapped])
    pp = np.array([m[1] for m in mapped])
    return {
        "computable": True,
        "n_draws_outside_grid": n_out,
        "truncated_at_grid_edge": bool(n_out > 0),
        "ci95_b": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
        "ci95_pp": [float(np.percentile(pp, 2.5)), float(np.percentile(pp, 97.5))],
        "se_b": float(np.std(b, ddof=1)),
        "se_pp": float(np.std(pp, ddof=1)),
    }


def _gate(name: str, got: float, want: float, tol_pp: float,
          got_n: int, want_n: int, report: dict) -> None:
    ok = (abs(got - want) <= tol_pp) and (got_n == want_n)
    report[name] = {
        "got_cpr_pct": got, "want_cpr_pct": want, "tol_pp": tol_pp,
        "got_n": got_n, "want_n": want_n, "pass": bool(ok),
    }
    print(f"  {name}: got {got:.4f}% (n={got_n}) want {want}% (n={want_n}) "
          f"tol ±{tol_pp}pp [{'PASS' if ok else 'FAIL'}]")


def _fail_out(gate_report: dict, extra: dict | None = None) -> None:
    payload = {"mode": "floor_uncertainty", "status": "GATE_FAILURE",
               "parity_gates": gate_report}
    if extra:
        payload.update(extra)
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda x: float(x)
                  if isinstance(x, (np.floating, np.integer)) else x)
        f.write("\n")
    raise SystemExit(
        "PARITY GATE FAILURE: "
        f"{[k for k, v in gate_report.items() if isinstance(v, dict) and not v.get('pass', True)]}"
        f" — environment problem; STOP. Diagnostics in {RESULTS_JSON}. "
        "Do NOT build on a broken baseline."
    )


def main() -> None:
    t0 = time.perf_counter()

    # ---- committed artifacts, asserted vs quoted constants -----------------
    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)
    with open(OOW_ARTIFACT) as f:
        oow = json.load(f)
    grid18 = oos["instrument1_oow_floor"]["legs"]["2018_rising_rate"]["anchor_grid"]
    for cell, (q_cpr, q_n) in CLEAN_BAND_QUOTED.items():
        assert abs(grid18[cell]["cpr_pct"] - q_cpr) < 1e-9, (cell, q_cpr)
        assert grid18[cell]["n_cohort_months"] == q_n, (cell, q_n)
    calib = oos["instrument2_temporal_holdout"]["calibration_floor"]["reads"][
        "gap<=-0.02_age>=12"]
    assert abs(calib["cpr_pct"] - INWINDOW_CALIB_QUOTED[0]) < 1e-9
    assert calib["n_cohort_months"] == INWINDOW_CALIB_QUOTED[1]
    deep2324 = oow["in_window_deep_OTM_validation"]["gap<=-0.02_age>=12"]
    assert abs(deep2324["cpr_pct"] - INWINDOW_2324_QUOTED[0]) < 1e-9
    assert deep2324["n_cohort_months"] == INWINDOW_2324_QUOTED[1]
    head = oos["headline_oos_marginal"]
    assert abs(head["clean_marginal_b_point_at_6.5"] - POINT_MARGINAL_QUOTED_B) < 1e-9
    assert abs(head["clean_marginal_pp_point_at_6.5"] - POINT_MARGINAL_QUOTED_PP) < 1e-9
    oos_rows = {round(r["floor_annual_cpr_pct"], 3): r
                for r in oos["instrument1_marginal_table"]}
    assert abs(oos_rows[5.334]["band"][CENTRAL_PQ]["marginal_pp"]
               - DEPTH_CUT_BAND_QUOTED_PP[0]) < 1e-9
    assert abs(oos_rows[4.695]["band"][CENTRAL_PQ]["marginal_pp"]
               - DEPTH_CUT_BAND_QUOTED_PP[1]) < 1e-9

    # ---- panel (oos_identification conditioning) + stratum labels ----------
    print("=" * 72)
    print("PANEL — matched_depth_reconciliation.build_panel (FRED MORTGAGE30US)")
    print("=" * 72)
    df = mdr.build_panel()
    df["stratum"] = [
        build_stratum_id(v, c, fb, lb)
        for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                df["fico_bucket"], df["ltv_bucket"])
    ]
    print(f"  {len(df)} cohort-months, {df['stratum'].nunique()} strata")

    # ---- the five read selections ------------------------------------------
    reads_spec = {
        "R1_2018_gap<=+0.0000_age>=12": (*LEG_2018, 0.0, 12,
                                         *CLEAN_BAND_QUOTED["gap<=+0.0000_age>=12"],
                                         TOL_CLEAN_PP),
        "R2_2018_gap<=-0.0025_age>=12": (*LEG_2018, -0.0025, 12,
                                         *CLEAN_BAND_QUOTED["gap<=-0.0025_age>=12"],
                                         TOL_CLEAN_PP),
        "R3_2018_gap<=-0.0050_age>=12": (*LEG_2018, -0.005, 12,
                                         *CLEAN_BAND_QUOTED["gap<=-0.0050_age>=12"],
                                         TOL_CLEAN_PP),
        "R4_inwindow_calib_202206_202312_gap<=-0.02_age>=12": (
            *CALIB_WINDOW, -0.02, 12, *INWINDOW_CALIB_QUOTED, TOL_INWINDOW_PP),
        "R5_inwindow_2023_24_gap<=-0.02_age>=12": (
            *INW_2324, -0.02, 12, *INWINDOW_2324_QUOTED, TOL_INWINDOW_PP),
    }
    selections: dict[str, pd.DataFrame] = {}
    points: dict[str, tuple[float, float, int]] = {}
    for name, (lo, hi, gthr, amin, _, _, _) in reads_spec.items():
        sel = _select(df, lo, hi, gthr, amin)
        selections[name] = sel
        cpr, exp, n = mdr.cpr_of(sel)
        points[name] = (cpr, exp, n)

    # ---- PARITY GATES (blocking; before any bootstrap/adjustment) ----------
    print("\n" + "=" * 72)
    print("PARITY GATES (blocking)")
    print("=" * 72)
    gate_report: dict = {}
    gate_names = {"R1_2018_gap<=+0.0000_age>=12": "G1a",
                  "R2_2018_gap<=-0.0025_age>=12": "G1b",
                  "R3_2018_gap<=-0.0050_age>=12": "G1c",
                  "R4_inwindow_calib_202206_202312_gap<=-0.02_age>=12": "G2",
                  "R5_inwindow_2023_24_gap<=-0.02_age>=12": "G3"}
    for name, (lo, hi, gthr, amin, want_cpr, want_n, tol) in reads_spec.items():
        cpr, _, n = points[name]
        _gate(gate_names[name], cpr if cpr is not None else float("nan"),
              want_cpr, tol, n, want_n, gate_report)

    mapping = mdr.FloorMapping()
    map_val = mapping.validate()
    g4_ok = bool(map_val["reproduces_committed_grid_exactly"]
                 and map_val["max_abs_err_b_inside_grid"] <= MAPPING_MAX_ERR_B)
    gate_report["G4_pchip_mapping"] = {
        "reproduces_committed_grid_exactly": map_val["reproduces_committed_grid_exactly"],
        "max_abs_err_b_inside_grid": map_val["max_abs_err_b_inside_grid"],
        "tol_b": MAPPING_MAX_ERR_B, "pass": g4_ok,
    }
    print(f"  G4_pchip_mapping: grid exact = "
          f"{map_val['reproduces_committed_grid_exactly']}, max |mapped-engine| "
          f"${map_val['max_abs_err_b_inside_grid']:.4f}B (tol ${MAPPING_MAX_ERR_B}B) "
          f"[{'PASS' if g4_ok else 'FAIL'}]")

    if not all(v["pass"] for v in gate_report.values()):
        _fail_out(gate_report)
    print("  ALL GATES PASS — safe to proceed.")

    # ========================================================================
    # PART A — cluster-bootstrap sampling uncertainty (MF-4)
    # ========================================================================
    print("\n" + "=" * 72)
    print(f"PART A — cluster bootstrap ({N_REPS} reps, seed {SEED}, "
          f"clusters = 4-way strata)")
    print("=" * 72)
    part_a_reads: dict = {}
    for name, (lo, hi, gthr, amin, want_cpr, _, _) in reads_spec.items():
        sel = selections[name]
        cpr, exp, n = points[name]
        draws, n_clusters = cluster_bootstrap_cpr(sel)
        ci = [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]
        se = float(np.std(draws, ddof=1))
        point_map = (mapping(cpr) if mapping.in_grid(cpr) else None)
        mapped = _map_draws(mapping, draws)
        part_a_reads[name] = {
            "selection": f"rp {lo}..{hi}, gap<={gthr:+.4f}, age>={amin}",
            "committed_cpr_pct": want_cpr,
            "point_cpr_pct": cpr,
            "exposure_upb": exp,
            "n_cohort_months": n,
            "n_clusters": n_clusters,
            "bootstrap": {
                "n_reps": N_REPS, "seed": SEED,
                "se_pp": se, "ci95_pct": ci,
                "draws_min_pct": float(draws.min()),
                "draws_max_pct": float(draws.max()),
            },
            "mapped_marginal_at_6.5": {
                "point_b": (point_map[0] if point_map else None),
                "point_pp": (point_map[1] if point_map else None),
                **mapped,
            },
        }
        print(f"  {name}:")
        print(f"    floor {cpr:.4f}%  SE {se:.3f}pp  95% CI "
              f"[{ci[0]:.3f}, {ci[1]:.3f}]%  ({n_clusters} clusters, n={n})")
        if mapped["computable"]:
            print(f"    -> marginal @6.5: 95% CI "
                  f"[{mapped['ci95_b'][0]:+.2f}, {mapped['ci95_b'][1]:+.2f}]$B / "
                  f"[{mapped['ci95_pp'][0]:+.3f}, {mapped['ci95_pp'][1]:+.3f}]pp"
                  f"{'  (TRUNCATED: ' + str(mapped['n_draws_outside_grid']) + ' draws outside grid)' if mapped['truncated_at_grid_edge'] else ''}")

    # ---- MF-4 ex-ante framing: sampling CI vs depth-cut band ---------------
    anchor = part_a_reads["R2_2018_gap<=-0.0025_age>=12"]
    samp_ci_pp = anchor["mapped_marginal_at_6.5"].get("ci95_pp")
    samp_width = (samp_ci_pp[1] - samp_ci_pp[0]) if samp_ci_pp else float("nan")
    band_width = DEPTH_CUT_BAND_QUOTED_PP[1] - DEPTH_CUT_BAND_QUOTED_PP[0]
    sampling_binds = bool(samp_width > band_width)
    mf4 = {
        "offwindow_point_marginal_pp_committed": POINT_MARGINAL_QUOTED_PP,
        "offwindow_point_marginal_b_committed": POINT_MARGINAL_QUOTED_B,
        "sampling_ci95_pp": samp_ci_pp,
        "sampling_ci95_width_pp": samp_width,
        "depth_cut_band_pp_committed": list(DEPTH_CUT_BAND_QUOTED_PP),
        "depth_cut_band_manuscript": "+4.3..+6.8",
        "depth_cut_band_width_pp": band_width,
        "binding_uncertainty": ("sampling" if sampling_binds else "depth_cut_band"),
        "manuscript_action": (
            "The sampling CI is WIDER than the depth-cut band: sampling error "
            "is the binding uncertainty on the off-window marginal, and the "
            "manuscript must quote the bootstrap CI alongside — and as wider "
            "than — the +4.3..+6.8 depth-cut band wherever +5.57pp appears."
            if sampling_binds else
            "The depth-cut band is WIDER than the sampling CI: the depth cut "
            "remains the binding uncertainty, the manuscript keeps +4.3..+6.8 "
            "as the quoted interval, and reports the (narrower) sampling CI "
            "as subordinate wherever +5.57pp appears."
        ),
    }
    print(f"\n  MF-4: sampling CI width {samp_width:.3f}pp vs depth-cut band "
          f"width {band_width:.3f}pp -> binding = {mf4['binding_uncertainty']}")

    # ========================================================================
    # PART B — age-composition adjustment (MF-3)
    # ========================================================================
    print("\n" + "=" * 72)
    print("PART B — age-standardized off-window floor (gap<=-0.0025, 2018 leg; "
          "weights from in-window 2023-24 deep-OTM)")
    print("=" * 72)
    leg18 = df[(df["rp"] >= LEG_2018[0]) & (df["rp"] <= LEG_2018[1])
               & (df["gap"] <= -0.0025)]
    inw = df[(df["rp"] >= INW_2324[0]) & (df["rp"] <= INW_2324[1])
             & (df["gap"] <= -0.02)]

    reads18, reads_in, weights = {}, {}, {}
    inw_total_exp = float(inw["exposure_upb"].sum())
    for lo, hi in AGE_BUCKETS_B:
        lab = _bucket_label(lo, hi)
        b18 = leg18[(leg18["mean_loan_age"] >= lo) & (leg18["mean_loan_age"] < hi)]
        cpr18, exp18, n18 = mdr.cpr_of(b18)
        reads18[lab] = {"cpr_pct": cpr18, "exposure_upb": exp18,
                        "n_cohort_months": n18}
        bin_ = inw[(inw["mean_loan_age"] >= lo) & (inw["mean_loan_age"] < hi)]
        cprin, expin, nin = mdr.cpr_of(bin_)
        reads_in[lab] = {"cpr_pct": cprin, "exposure_upb": expin,
                         "n_cohort_months": nin}
        weights[lab] = (expin / inw_total_exp) if inw_total_exp > 0 else 0.0

    # oldest 2018-populated bucket (by bucket order)
    oldest_lab = None
    for lo, hi in AGE_BUCKETS_B:
        lab = _bucket_label(lo, hi)
        if reads18[lab]["cpr_pct"] is not None:
            oldest_lab = lab
    if oldest_lab is None:
        _fail_out(gate_report, {
            "part_b_error": "no 2018-leg OTM exposure in ANY age bucket at "
                            "gap<=-0.0025 — the adjustment is not computable"})
    r18_oldest = reads18[oldest_lab]["cpr_pct"]
    rin_oldest = reads_in[oldest_lab]["cpr_pct"]

    bucket_table, adj_floor, imputed_weight = [], 0.0, 0.0
    for lo, hi in AGE_BUCKETS_B:
        lab = _bucket_label(lo, hi)
        w = weights[lab]
        r18 = reads18[lab]["cpr_pct"]
        rin = reads_in[lab]["cpr_pct"]
        if w == 0.0:
            used, source = None, "no_in_window_weight (contributes nothing)"
        elif r18 is not None:
            used, source = r18, "observed_2018"
        elif rin_oldest is not None and rin_oldest > 0 and rin is not None:
            used = r18_oldest * (rin / rin_oldest)
            source = (f"IMPUTED: 2018 read in oldest populated bucket "
                      f"{oldest_lab} ({r18_oldest:.3f}%) x in-window ratio "
                      f"{rin:.3f}/{rin_oldest:.3f}")
            imputed_weight += w
        else:
            used = r18_oldest
            source = (f"IMPUTED FLAT FALLBACK: in-window CPR of {oldest_lab} "
                      "not computable/zero — 2018 oldest-bucket read used "
                      "unscaled")
            imputed_weight += w
        if used is not None:
            adj_floor += w * used
        bucket_table.append({
            "bucket": lab, "in_window_weight": w,
            "in_window_cpr_pct": rin,
            "read_2018_cpr_pct": r18,
            "read_used_pct": used, "source": source,
        })
        print(f"  {lab:>10s}: w={w:7.4f}  in-window CPR="
              f"{rin if rin is not None else float('nan'):7.3f}%  2018 read="
              f"{r18 if r18 is not None else float('nan'):7.3f}%  used="
              f"{used if used is not None else float('nan'):7.3f}%  ({source})")

    print(f"\n  age-standardized off-window floor: {adj_floor:.4f}%")
    print(f"  IMPUTED SHARE OF WEIGHT: {imputed_weight:.4f} "
          f"({100 * imputed_weight:.2f}% of in-window exposure weight)")

    if mapping.in_grid(adj_floor):
        adj_b, adj_pp = mapping(adj_floor)
        adj_marginal = {"computable": True, "marginal_b": adj_b,
                        "marginal_pp": adj_pp}
        print(f"  -> adjusted marginal @6.5: {adj_b:+.2f}$B / {adj_pp:+.3f}pp")
    else:
        adj_marginal = {
            "computable": False, "marginal_b": None, "marginal_pp": None,
            "reason": f"adjusted floor {adj_floor:.4f}% outside the committed "
                      f"sweep grid [{mapping.x.min()}, {mapping.x.max()}]% — "
                      "extrapolation refused; verdict stated on the floor "
                      "value alone",
        }
        print(f"  -> adjusted marginal NOT MAPPED: {adj_marginal['reason']}")

    # ---- ex-ante threshold verdict (T1/T2/T3, verbatim from the header) ----
    if adj_floor > COMMITTED_BAND_TOP_PCT:
        t_code, t_text = "T1", (
            "the age-standardized floor lands above 5.334% (the committed "
            "band top): the clean band is one-sided-open downward and the "
            "manuscript's +4.3 lower bound is not conservative — the revision "
            "must state the band as open below +4.3 (or extend it to the "
            "adjusted read)."
        )
    elif adj_floor >= COMMITTED_BAND_BOT_PCT:
        t_code, t_text = "T2", (
            "the age-standardized floor lands inside [4.695, 5.334]: the band "
            "stands with the adjustment reported as within-band."
        )
    else:
        t_code, t_text = "T3", (
            "the age-standardized floor lands below 4.695%: the seasoning-"
            "bias concern is refuted and reported as such."
        )
    print(f"\n  THRESHOLD VERDICT: {t_code} — {t_text}")

    # ---- soft checks (findings, never crashes) -----------------------------
    older_empty = all(reads18[_bucket_label(lo, hi)]["cpr_pct"] is None
                      for lo, hi in AGE_BUCKETS_B[2:])
    r2_point = points["R2_2018_gap<=-0.0025_age>=12"][0]
    b1224 = reads18[_bucket_label(12.0, 24.0)]["cpr_pct"]
    soft_checks = {
        "2018_leg_age24plus_empty_as_committed": bool(older_empty),
        "2018_bucket_12_24_equals_R2_anchor_when_older_empty": bool(
            older_empty and b1224 is not None
            and abs(b1224 - r2_point) < 1e-9
        ),
        "in_window_weights_sum_to_1": bool(
            abs(sum(weights.values()) - 1.0) < 1e-9
        ),
    }
    for k, v in soft_checks.items():
        print(f"  [{'PASS' if v else 'FLAG'}] {k}")

    # ---- freeze -------------------------------------------------------------
    runtime_s = round(time.perf_counter() - t0, 1)
    verdict_para = (
        f"MF-4: the binding uncertainty on the off-window marginal is "
        f"{mf4['binding_uncertainty'].upper()} — sampling 95% CI "
        f"[{samp_ci_pp[0]:+.2f}, {samp_ci_pp[1]:+.2f}]pp (width "
        f"{samp_width:.2f}pp) vs depth-cut band +4.27..+6.77pp (width "
        f"{band_width:.2f}pp) at the +5.57pp anchor. "
        f"MF-3: the age-standardized off-window floor is {adj_floor:.3f}% "
        f"(imputed weight share {100 * imputed_weight:.1f}%), verdict {t_code}: "
        f"{t_text}"
    )
    payload = {
        "mode": "floor_uncertainty",
        "status": "OK",
        "spec": (
            "MF-4 cluster bootstrap (clusters = 4-way strata via "
            "stratum.build_stratum_id; 1000 reps; fresh default_rng(42) per "
            "read) of the committed floor reads {5.334, 4.991, 4.695 "
            "(2018 leg, age>=12), 3.972 (in-window calib 202206..202312), "
            "3.840 (in-window 2023-24 deep-OTM)}%, each propagated through "
            "the committed floor_sweep PCHIP map at central elasticity 6.5 "
            "(extrapolation refused); MF-3 age-standardization of the 2018 "
            "gap<=-0.0025 read onto the in-window 2023-24 deep-OTM age "
            "distribution with labeled ratio imputation; parity gates "
            "G1a-c/G2/G3/G4 blocking; ex-ante thresholds T1/T2/T3 and the "
            "MF-4 wider-band rule; NO engine runs, PCHIP mapping only."
        ),
        "parity_gates": gate_report,
        "parity_gates_all_pass": True,
        "mapping_fidelity": map_val,
        "part_a_sampling_uncertainty": {
            "cluster_unit": "4-way stratum (vintage x coupon-bps x "
                            "fico_bucket x ltv_bucket; stratum.build_stratum_id)",
            "n_reps": N_REPS, "seed": SEED,
            "seeding": "fresh np.random.default_rng(42) per read",
            "reads": part_a_reads,
            "mf4_binding_uncertainty": mf4,
        },
        "part_b_age_standardization": {
            "age_buckets": [_bucket_label(lo, hi) for lo, hi in AGE_BUCKETS_B],
            "off_window_selection": "2018 leg (201801..201812), gap<=-0.0025",
            "in_window_selection": "202301..202412, gap<=-0.02 (deep-OTM, "
                                   "refi-free by rate configuration, seasoned)",
            "leg_2018_reads_by_bucket": reads18,
            "in_window_2023_24_by_bucket": reads_in,
            "in_window_weights": weights,
            "oldest_populated_2018_bucket": oldest_lab,
            "bucket_table": bucket_table,
            "adjusted_floor_pct": adj_floor,
            "imputed_weight_share": imputed_weight,
            "adjusted_marginal_at_6.5": adj_marginal,
            "committed_clean_band_pct": [COMMITTED_BAND_BOT_PCT,
                                         COMMITTED_BAND_TOP_PCT],
            "threshold_verdict": {"code": t_code, "text": t_text},
        },
        "soft_checks": soft_checks,
        "verdict": {"one_paragraph": verdict_para},
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda x: float(x)
                  if isinstance(x, (np.floating, np.integer)) else x)
        f.write("\n")

    print("\n" + "=" * 72)
    print(f"VERDICT: {verdict_para}")
    print(f"\nResults -> {RESULTS_JSON}")
    print(f"Runtime: {runtime_s}s")


if __name__ == "__main__":
    main()
