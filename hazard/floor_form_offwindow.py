#!/usr/bin/env python3
"""
floor_form_offwindow.py — the missing cell of the {floor form} x {floor
provenance} design: the competing-risks (additive) floor form has never been
run at the off-window floor anchors.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
floor_sweep.py / floor_form_test.py / oos_identification.py).

Referee objection (round 21, panel finding MF-1 CONFIRMED): the manuscript's
headline lock-in marginal (+5.6pp / +$42.6B, band +4.3..+6.8) exists only
under the hard-max floor form, whose floor-sensitivity the manuscript itself
diagnoses as "censoring-driven rather than evidence about the elasticity"
(floor_form_test.py: additive marginal +11.25pp at the production floor and
nearly floor-invariant, +11.29..+11.21, across the 3-5% floors whose max-form
span failed the pre-committed stability gate). The entire in-window ->
off-window demotion (+9.2 -> +5.6) operates through raising the floor under
the max form, i.e. through exactly the censoring channel the form test calls
artifactual. The decisive joint cell — off-window floor x additive form — was
never run. This script runs it.

SPEC (fixed ex ante)
- Forms: "max" (fresh replay; doubles as parity/cross-check) and "additive"
  (survival scale: h = 1-(1-h_floor)(1-h_vol); elasticity never censored).
- Floors: {4.0 (production parity)} + the committed off-window clean band
  from oos_identification_results.json headline_oos_marginal:
  {4.695, 4.991, 5.334}% annual CPR (2018 rising-rate leg, age>=12,
  exposure-weighted; values consumed from the committed artifact at runtime,
  asserted equal to the three quoted here to 1e-9).
- Legs per (form, floor): beta1=0 null (p_q 0; band-invariant) + central
  band {5.5, 6.5, 7.7} (the committed Liebersohn-Rothstein band).
  Exception: at the 4.0% parity floor only p_q {0, 6.5} run (the committed
  parity pair); band cells at 4.0% are already committed in
  floor_sweep_results.json / floor_form_results.json.
- Production convention otherwise: committed 75k loan sample, RNG_SEED 42,
  ("US","Danish") regime tuple with per-regime seed offsets, one shared
  macro frame, raw-basis scoring via extension_risk.score_extension_risk,
  caches not consulted (fresh microsim runs into data/floor_form_offwindow/).

PARITY GATES (run first, block interpretation; tolerances +/-$0.01B dollars,
+/-0.01pp shares — the floor_sweep/floor_form/oos tolerances):
  G1 (max, 4.0%):      central/null/marginal vs no_lockin_null_results.json
                       (central $818.5300844B, null $748.1850240B,
                        marginal +$70.3450604B / +9.1985pp).
  G2 (additive, 4.0%): central/null/marginal vs floor_form_results.json
                       additive row at 4% (central $513.7266B, null
                       $427.7041B, marginal +$86.0225B / +11.2485pp).
  G3 (max, clean band): null and central@6.5 at each of {4.695, 4.991,
                       5.334}% vs the committed oos_identification_results
                       instrument1_marginal_table rows (marginals
                       +$51.7815060B / +$42.6083939B / +$32.6216403B).

EX-ANTE INTERPRETIVE THRESHOLDS (the referee's falsifiers, fixed before the
runs; the +/-1.0pp materiality convention of floor_form_test.py):
  T1 (form-conditional demotion): if the additive-form marginal at every
     clean-band floor (central 6.5) lies within +/-1.0pp of the additive-form
     marginal at the 4.0% production floor (+11.2485pp), then the off-window
     demotion is CONFIRMED to operate entirely through max-form censoring
     mechanics, and the manuscript MUST (a) state the headline marginal
     form-conditionally wherever it is quoted (abstract, Table 1, V.E,
     VII.I, Conclusion), and (b) report the additive off-window marginal
     beside the max-form +5.6.
  T2 (form-independent demotion): if any clean-band additive marginal moves
     by more than 1.0pp from the 4.0% additive value, the demotion carries
     form-independent content; the max-form headline stands, with the form
     caveat attached wherever the marginal is quoted, and the additive
     off-window band reported alongside.
  In EITHER branch the designated identified interval for the revision is
  the hull of the max-form off-window joint floor-x-band range and the
  additive-form off-window joint floor-x-band range, emitted below as
  designated_interval_pp. No further discretion is exercised after the runs.

Run:  cd hazard && python3 floor_form_offwindow.py
      -> data/floor_form_offwindow_results.json (+ per-run parquets under
         data/floor_form_offwindow/, regenerable, not committed)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import polars as pl

import literature_hazard
from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "floor_form_offwindow"
RESULTS_JSON = DATA_DIR / "floor_form_offwindow_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
FLOOR_FORM_ARTIFACT = DATA_DIR / "floor_form_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"

PRODUCTION_FLOOR = 0.04
CLEAN_BAND_QUOTED = [4.695, 4.991, 5.334]  # asserted vs committed artifact
BAND_PQ = [5.5, 6.5, 7.7]
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
TOL_B = 0.01
TOL_PP = 0.01
FORM_MATERIALITY_PP = 1.0


def _run_scored(
    loans: pl.DataFrame, empirical: pd.DataFrame, form: str, floor: float,
    pq: float,
) -> dict:
    """One microsim run at (form, floor, elasticity), production convention."""
    literature_hazard.FLOOR_MODE = form
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    out_path = OUT_DIR / (
        f"microsim_{form}_floor{floor * 100:g}pct_pq{pq:g}.parquet"
    )
    try:
        run_qt_microsim(loan_sample=loans, output=out_path, p_q_shock_pct=pq)
    finally:
        literature_hazard.FLOOR_MODE = "max"
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)
    return {
        "form": form,
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "mean_us_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
    }


def _gate(name: str, got: float, want: float, tol: float, report: dict) -> None:
    ok = abs(got - want) < tol
    report[name] = {"got": got, "want": want, "tol": tol, "pass": bool(ok)}
    print(f"parity gate {name}: got {got:.7f} want {want:.7f} "
          f"[{'PASS' if ok else 'FAIL'}]")


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)
    head = oos["headline_oos_marginal"]
    committed_band = [head["clean_floor_band_pct"][0],
                      head["clean_floor_point_pct"],
                      head["clean_floor_band_pct"][1]]
    for quoted, committed in zip(CLEAN_BAND_QUOTED, committed_band):
        assert abs(quoted - committed) < 1e-9, (quoted, committed)
    clean_floors = [f / 100.0 for f in committed_band]
    oos_rows = {
        round(r["floor_annual_cpr_pct"], 3): r
        for r in oos["instrument1_marginal_table"]
    }
    with open(NULL_ARTIFACT) as f:
        anchor = json.load(f)
    with open(FLOOR_FORM_ARTIFACT) as f:
        ff = json.load(f)
    add4 = next(r for r in ff["rows"]
                if r["form"] == "additive" and r["floor_annual_cpr_pct"] == 4.0)

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    gate_report: dict = {}
    rows = []

    # ---- G1: max form, production floor, parity pair ------------------------
    g1_null = _run_scored(loans, empirical, "max", PRODUCTION_FLOOR, NULL_PQ)
    g1_central = _run_scored(loans, empirical, "max", PRODUCTION_FLOOR,
                             CENTRAL_PQ)
    _gate("G1_central_b", g1_central["trapped_b"],
          anchor["central_trapped_b"], TOL_B, gate_report)
    _gate("G1_null_b", g1_null["trapped_b"],
          anchor["null_trapped_b"], TOL_B, gate_report)
    _gate("G1_marginal_b", g1_central["trapped_b"] - g1_null["trapped_b"],
          anchor["lockin_marginal_b"], TOL_B, gate_report)
    _gate("G1_marginal_pp", g1_central["share_pct"] - g1_null["share_pct"],
          anchor["lockin_marginal_share_pp"], TOL_PP, gate_report)

    # ---- G2: additive form, production floor, parity pair -------------------
    g2_null = _run_scored(loans, empirical, "additive", PRODUCTION_FLOOR,
                          NULL_PQ)
    g2_central = _run_scored(loans, empirical, "additive", PRODUCTION_FLOOR,
                             CENTRAL_PQ)
    _gate("G2_central_b", g2_central["trapped_b"],
          add4["central"]["trapped_b"], TOL_B, gate_report)
    _gate("G2_null_b", g2_null["trapped_b"],
          add4["null"]["trapped_b"], TOL_B, gate_report)
    _gate("G2_marginal_b", g2_central["trapped_b"] - g2_null["trapped_b"],
          add4["lockin_marginal_b"], TOL_B, gate_report)
    add_prod_marginal_pp = g2_central["share_pct"] - g2_null["share_pct"]
    _gate("G2_marginal_pp", add_prod_marginal_pp,
          add4["lockin_marginal_share_pp"], TOL_PP, gate_report)

    # ---- Off-window cells: both forms at the clean-band floors --------------
    for floor in clean_floors:
        fpct = round(floor * 100.0, 3)
        for form in ["max", "additive"]:
            null = _run_scored(loans, empirical, form, floor, NULL_PQ)
            band = {}
            pqs = [CENTRAL_PQ] if form == "max" else BAND_PQ
            for pq in pqs:
                central = _run_scored(loans, empirical, form, floor, pq)
                band[str(pq)] = {
                    "central_trapped_b": central["trapped_b"],
                    "central_share_pct": central["share_pct"],
                    "marginal_b": central["trapped_b"] - null["trapped_b"],
                    "marginal_pp": central["share_pct"] - null["share_pct"],
                }
            row = {
                "form": form,
                "floor_annual_cpr_pct": fpct,
                "null_trapped_b": null["trapped_b"],
                "null_share_pct": null["share_pct"],
                "band": band,
            }
            rows.append(row)
            m = band[str(CENTRAL_PQ)]
            print(f"{form:>8} floor {fpct:6.3f}%:  null "
                  f"${null['trapped_b']:7.1f}B  central@6.5 "
                  f"${m['central_trapped_b']:7.1f}B  marginal "
                  f"${m['marginal_b']:+7.2f}B ({m['marginal_pp']:+5.2f}pp)")
            # ---- G3: max-form cells must reproduce the committed oos runs --
            if form == "max":
                want = oos_rows[fpct]
                _gate(f"G3_null_b@{fpct}", null["trapped_b"],
                      want["null_trapped_b"], TOL_B, gate_report)
                _gate(f"G3_central_b@{fpct}",
                      m["central_trapped_b"],
                      want["band"]["6.5"]["central_trapped_b"], TOL_B,
                      gate_report)
                _gate(f"G3_marginal_b@{fpct}", m["marginal_b"],
                      want["band"]["6.5"]["marginal_b"], TOL_B, gate_report)
    runtime_s = time.perf_counter() - t0

    hard_fail = [k for k, v in gate_report.items() if not v["pass"]]

    # ---- Ex-ante interpretive thresholds T1/T2 ------------------------------
    add_rows = [r for r in rows if r["form"] == "additive"]
    max_rows = [r for r in rows if r["form"] == "max"]
    add_deltas = {
        r["floor_annual_cpr_pct"]:
            r["band"][str(CENTRAL_PQ)]["marginal_pp"] - add_prod_marginal_pp
        for r in add_rows
    }
    t1_holds = all(abs(d) <= FORM_MATERIALITY_PP for d in add_deltas.values())
    verdict = (
        "T1: additive-form marginal within +/-1.0pp of its production-floor "
        "value at every clean-band floor — the off-window demotion operates "
        "entirely through max-form censoring mechanics; state the headline "
        "form-conditionally and report the additive off-window marginal "
        "beside the max-form +5.6"
        if t1_holds else
        "T2: additive-form marginal moves by more than 1.0pp from its "
        "production-floor value inside the clean band — the demotion carries "
        "form-independent content; max-form headline stands with the form "
        "caveat, additive off-window band reported alongside"
    )

    max_joint = [b["marginal_pp"] for r in max_rows
                 for b in r["band"].values()]
    max_joint_committed = [
        oos_rows[r["floor_annual_cpr_pct"]]["band"][str(pq)]["marginal_pp"]
        for r in max_rows for pq in [5.5, 6.5, 7.7]
    ]
    add_joint = [b["marginal_pp"] for r in add_rows
                 for b in r["band"].values()]
    joint_all = max_joint_committed + add_joint
    designated = [min(joint_all), max(joint_all)]

    payload = {
        "mode": "floor_form_offwindow",
        "spec": (
            "forms {max, additive-survival-scale}; floors {4.0 parity} + "
            "committed off-window clean band {4.695, 4.991, 5.334}% annual "
            "CPR; legs: beta1=0 null + central band {5.5,6.5,7.7} per "
            "(additive, clean floor), central 6.5 per (max, clean floor) "
            "with max band cells consumed from the committed oos artifact; "
            "production convention otherwise; parity gates G1/G2/G3; ex-ante "
            "thresholds T1/T2 at +/-1.0pp; designated interval = hull of "
            "max-form and additive-form off-window joint floor-x-band ranges"
        ),
        "rows": rows,
        "parity_gates": gate_report,
        "parity_gates_all_pass": not hard_fail,
        "additive_marginal_pp_at_production_floor": add_prod_marginal_pp,
        "additive_marginal_pp_deltas_vs_production": add_deltas,
        "t1_form_conditional_demotion": bool(t1_holds),
        "interpretive_verdict": verdict,
        "max_form_offwindow_joint_range_pp_committed": [
            min(max_joint_committed), max(max_joint_committed)
        ],
        "additive_form_offwindow_joint_range_pp": [
            min(add_joint), max(add_joint)
        ],
        "designated_interval_pp": designated,
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"\nverdict: {verdict}")
    print(f"designated interval: [{designated[0]:+.2f}, {designated[1]:+.2f}]pp")
    print(f"gates all pass: {not hard_fail}   runtime {runtime_s:,.0f}s")
    if hard_fail:
        raise SystemExit(f"PARITY FAILURE — do not build on this: {hard_fail}")


if __name__ == "__main__":
    main()
