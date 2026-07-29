#!/usr/bin/env python3
"""
b5_joint_cell.py — the one genuinely never-run cell: the published-series
Ginnie overlay composed with the age-standardized floor read.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
ginnie_overlay_offwindow.py / floor_form_offwindow.py; author authorization
2026-07-28, landing rule approved verbatim in-session).

Panel finding (roadmap B5, re-review status NOT_ADDRESSED): the Ginnie overlay
(+4.44pp at the 4.991% headline floor) and the age-standardized floor read
(5.51%, implied marginal ~+3.8pp) each exist as separate committed cells and
"have never been run against each other; I report them separately and give no
composed point." The informal proportional composition (the overlay's 0.797
scaling carried to the age-standardized floor) "would put the marginal near
$+3.0$" — an arithmetic projection the manuscript explicitly declines to
report as an estimate. This script runs the joint cell.

CELL (fixed ex ante)
- Floor: the committed age-standardized read, taken from the artifact float
  floor_uncertainty_results.json -> part_b_age_standardization
  .adjusted_floor_pct (5.507748455937158%), max form — NOT the rounded 5.51.
- Legs: central (p_q 6.5) and null (p_q 0.0) via the floor_form_offwindow
  _run_scored convention (patch literature_hazard.FLOOR_MODE='max' and
  INVOLUNTARY_CPR_ANNUAL, restore production after each run; production
  RNG_SEED / N_LOANS / PSA conventions untouched).
- Overlay: machinery imported UNMODIFIED from ginnie_cpr_overlay
  (load_series, overlay_leg, GINNIE_SHARE, shared-basis constants); variants
  primary (Ginnie CPR) / crr_only / gse_placebo, the committed variant set.

PARITY GATES (halt and write GATE_FAILURE; variants and adjudication not run):
  G-A (engine reproduction): fresh max-form legs at 4.991% / p_q {6.5, 0}
      must reproduce the committed oos_identification trapped_b values to
      +/- 0.01 $B each (the round-26 band_low_extension tolerance for fresh
      engine runs against committed cells).
  G-B (overlay code path): the primary overlay marginal recomputed on the
      fresh 4.991% legs must reproduce the committed
      ginnie_overlay_offwindow primary marginal (+4.443419pp) to +/- 0.01pp.
  G-C (wiring identity): overlaying each age-standardized leg with its OWN
      annualized CPR series must reproduce that leg's raw trapped_b to
      1e-6 $B (own-series identity, the committed G1 form).

CONSISTENCY REPORT (not a gate): the conventional marginal measured at the
age-standardized floor, beside the manuscript's PCHIP-implied "near $+3.8$"
(ladder_agestd). Reported as measured-vs-implied delta; no threshold.

ADJUDICATION RULE (fixed ex ante; no discretion after the run):
  composed        = primary overlay marginal_pp at the age-standardized floor
  EXPECTATION_PP  = 3.0   (the manuscript's informal proportional composition)
  MATERIALITY_PP  = 1.0   (the concave_additive_marginal interaction
                           convention, as pre-committed in the plan)
  |composed - EXPECTATION_PP| <= MATERIALITY_PP
      -> verdict LANDS_AS_COMPOSED_LOWER_MEMBER: the composed point enters
         the manuscript as the assembly's measured lower member; the
         no-composed-point spans at the overlay paragraph, the seventh
         qualification, the derivation paragraph, tab:uncertainty,
         tab:assembly ("run pending" row), and the verdict-audit row are
         revised in ONE commit together with gate #98's ladder_composed and
         ASSEMBLY_TABLE composed-row spans, their batteries, and the response
         letter's "I publish no composed point" sentence.
  otherwise
      -> verdict ESCALATE_NO_LANDING: artifact + TECHNICAL entry only; no
         manuscript sentence changes; the disposition returns to the author.
  Interaction diagnostic (reported either way):
  composed - RATIO * conventional_agestd_marginal, where RATIO is the
  committed 4.991% overlay/conventional ratio (4.443419 / 5.571558).

Run:  cd hazard && python3 b5_joint_cell.py    (4 engine legs + overlays)
      -> data/b5_joint_cell_results.json, parquets under data/b5_joint_cell/
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import polars as pl

import literature_hazard
from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from ginnie_cpr_overlay import (
    BENCHMARK_B,
    GINNIE_SHARE,
    NETTING_B,
    load_series,
    overlay_leg,
)
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "b5_joint_cell"
RESULTS_JSON = DATA_DIR / "b5_joint_cell_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
OVERLAY_ARTIFACT = DATA_DIR / "ginnie_overlay_offwindow_results.json"
FLOOR_UNC_ARTIFACT = DATA_DIR / "floor_uncertainty_results.json"

PRODUCTION_FLOOR = 0.04
OFF_FLOOR_PCT = 4.991
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
GA_TOL_B = 0.01
GB_TOL_PP = 0.01
GC_TOL_B = 1e-6
EXPECTATION_PP = 3.0
MATERIALITY_PP = 1.0
LADDER_IMPLIED_PP = 3.8  # manuscript ladder_agestd, PCHIP-implied (report-only)


def shared(trapped_b: float) -> float:
    return (trapped_b - NETTING_B) / BENCHMARK_B * 100.0


def own_series(sim: pd.DataFrame) -> pd.Series:
    smm = sim["hazard_cpr_pct"] / 1200.0
    ann = (1.0 - (1.0 - smm) ** 12) * 100.0
    return pd.Series(ann.to_numpy(), index=sim.index.to_period("M"))


def _run_leg(loans: pl.DataFrame, empirical: pd.DataFrame, floor_pct: float,
             pq: float) -> tuple[pd.DataFrame, float]:
    literature_hazard.FLOOR_MODE = "max"
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor_pct / 100.0
    out_path = OUT_DIR / f"microsim_max_floor{floor_pct:.6f}pct_pq{pq:g}.parquet"
    try:
        run_qt_microsim(loan_sample=loans, output=out_path, p_q_shock_pct=pq)
    finally:
        literature_hazard.FLOOR_MODE = "max"
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)
    return sim, float(score["hazard_trapped_b"])


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    agestd_floor_pct = json.loads(FLOOR_UNC_ARTIFACT.read_text())[
        "part_b_age_standardization"]["adjusted_floor_pct"]

    oos = json.loads(OOS_ARTIFACT.read_text())
    row = next(r for r in oos["instrument1_marginal_table"]
               if abs(r["floor_annual_cpr_pct"] - OFF_FLOOR_PCT) < 1e-9)
    want_central = row["band"]["6.5"]["central_trapped_b"]
    want_null = row["null_trapped_b"]

    comm = json.loads(OVERLAY_ARTIFACT.read_text())
    comm_primary_pp = comm["overlay_offwindow"]["primary"]["marginal_pp"]
    comm_conventional_pp = comm["conventional_offwindow"]["marginal_pp"]
    ratio = comm_primary_pp / comm_conventional_pp

    series, idx = load_series()
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    report: dict = {}

    # --- G-A: engine reproduction at the committed 4.991% cell -------------
    par_central, par_central_b = _run_leg(loans, empirical, OFF_FLOOR_PCT, CENTRAL_PQ)
    par_null, par_null_b = _run_leg(loans, empirical, OFF_FLOOR_PCT, NULL_PQ)
    report["GA_central"] = {"got": par_central_b, "want": want_central,
                            "pass": abs(par_central_b - want_central) <= GA_TOL_B}
    report["GA_null"] = {"got": par_null_b, "want": want_null,
                         "pass": abs(par_null_b - want_null) <= GA_TOL_B}

    # --- G-B: overlay code path reproduces the committed overlay cell ------
    gb_c = overlay_leg(par_central, empirical,
                       pd.Series(series["cpr"]["ginnie"], index=idx), GINNIE_SHARE)
    gb_n = overlay_leg(par_null, empirical,
                       pd.Series(series["cpr"]["ginnie"], index=idx), GINNIE_SHARE)
    gb_pp = shared(gb_c["trapped_b"]) - shared(gb_n["trapped_b"])
    report["GB_overlay_4991"] = {"got_pp": gb_pp, "want_pp": comm_primary_pp,
                                 "pass": abs(gb_pp - comm_primary_pp) <= GB_TOL_PP}

    # --- target legs at the age-standardized floor -------------------------
    tgt_central, tgt_central_b = _run_leg(loans, empirical, agestd_floor_pct, CENTRAL_PQ)
    tgt_null, tgt_null_b = _run_leg(loans, empirical, agestd_floor_pct, NULL_PQ)

    # --- G-C: own-series identity on the target legs -----------------------
    gc_c = overlay_leg(tgt_central, empirical, own_series(tgt_central), GINNIE_SHARE)
    gc_n = overlay_leg(tgt_null, empirical, own_series(tgt_null), GINNIE_SHARE)
    report["GC_identity_central"] = {"diff_b": gc_c["trapped_b"] - tgt_central_b,
                                     "pass": abs(gc_c["trapped_b"] - tgt_central_b) <= GC_TOL_B}
    report["GC_identity_null"] = {"diff_b": gc_n["trapped_b"] - tgt_null_b,
                                  "pass": abs(gc_n["trapped_b"] - tgt_null_b) <= GC_TOL_B}

    for k, v in report.items():
        print(f"parity gate {k}: {v} [{'PASS' if v['pass'] else 'FAIL'}]")
    hard_fail = [k for k, v in report.items() if not v["pass"]]
    if hard_fail:
        RESULTS_JSON.write_text(json.dumps(
            {"status": "GATE_FAILURE", "gates": report}, indent=2,
            default=float) + "\n")
        raise SystemExit(f"PARITY FAILURE — adjudication not run: {hard_fail}")

    # --- conventional marginal at the age-standardized floor (C1 report) ---
    conventional_agestd_pp = shared(tgt_central_b) - shared(tgt_null_b)

    # --- variants on the target legs ---------------------------------------
    gse_mean = [(f + fr) / 2 for f, fr in
                zip(series["cpr"]["fannie"], series["cpr"]["freddie"])]
    variants = {
        "primary": pd.Series(series["cpr"]["ginnie"], index=idx),
        "crr_only": pd.Series(series["crr"]["ginnie"], index=idx),
        "gse_placebo": pd.Series(gse_mean, index=idx),
    }
    out = {}
    for name, s in variants.items():
        c = overlay_leg(tgt_central, empirical, s, GINNIE_SHARE)
        n = overlay_leg(tgt_null, empirical, s, GINNIE_SHARE)
        out[name] = {
            "central": {**c, "share_pct_shared": shared(c["trapped_b"])},
            "null": {**n, "share_pct_shared": shared(n["trapped_b"])},
            "marginal_b": c["trapped_b"] - n["trapped_b"],
            "marginal_pp": shared(c["trapped_b"]) - shared(n["trapped_b"]),
        }
        print(f"{name:>12}: marginal {out[name]['marginal_pp']:+5.2f}pp "
              f"(${out[name]['marginal_b']:+.2f}B)")

    composed = out["primary"]["marginal_pp"]
    deviation = composed - EXPECTATION_PP
    interaction = composed - ratio * conventional_agestd_pp
    verdict = ("LANDS_AS_COMPOSED_LOWER_MEMBER"
               if abs(deviation) <= MATERIALITY_PP else "ESCALATE_NO_LANDING")

    payload = {
        "mode": "b5_joint_cell",
        "pre_committed": True,
        "agestd_floor_pct": agestd_floor_pct,
        "parity_gates": report,
        "conventional_agestd": {
            "central_trapped_b": tgt_central_b,
            "null_trapped_b": tgt_null_b,
            "central_shared_pct": shared(tgt_central_b),
            "null_shared_pct": shared(tgt_null_b),
            "marginal_pp": conventional_agestd_pp,
            "ladder_implied_pp": LADDER_IMPLIED_PP,
            "measured_minus_implied_pp": conventional_agestd_pp - LADDER_IMPLIED_PP,
        },
        "overlay_agestd": out,
        "committed_ratio_4991": ratio,
        "adjudication": {
            "composed_pp": composed,
            "expectation_pp": EXPECTATION_PP,
            "materiality_pp": MATERIALITY_PP,
            "deviation_pp": deviation,
            "interaction_vs_proportional_pp": interaction,
            "verdict": verdict,
        },
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=1, default=float) + "\n")
    print(f"\ncomposed overlay x age-standardized marginal: {composed:+.3f}pp "
          f"(conventional at that floor {conventional_agestd_pp:+.3f}pp; "
          f"deviation from +3.0 expectation {deviation:+.3f}pp; "
          f"interaction vs proportional {interaction:+.3f}pp)\n"
          f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
