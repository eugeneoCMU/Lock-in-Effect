#!/usr/bin/env python3
"""
Floor functional-form test (pre-committed; spec fixed in this header before
any run executed).

Referee objection: eq. (3) applies the involuntary-turnover floor as a hard
max, so wherever the floor binds the lock-in elasticity is inert by
construction (the crowding-out mechanism the calibration-box section names),
and the paper sweeps the floor's LEVEL across seven points but never its
FORM. This test reruns the production central and beta1=0 null legs under the
competing-risks form (additive on the survival scale):

    h = 1 - (1 - h_floor)(1 - h_vol)      [additive]    vs
    h = max(h_floor, h_vol)               [production max]

Under the additive form the elasticity is never censored by the floor. At the
floor's empirical anchor the two forms nearly coincide (deep-discount 2023-24
cohorts: h_vol ~ 0 there, so both forms deliver ~the floor), so the anchor
interpretation survives either form; the forms diverge where the voluntary
hazard is moderate.

SPEC (fixed ex ante):
- Forms: "max" (production; doubles as parity gate) and "additive".
- Floors: {3, 4, 5}% annual CPR (the empirically plausible range; 4% is
  production).
- Two legs per (form, floor): central p_q shock 6.5, null 0.0. Production
  convention otherwise: committed 75k loan sample, RNG_SEED 42, ("US",
  "Danish") regime tuple with per-regime seed offsets, one shared macro
  frame, raw-basis scoring via extension_risk.score_extension_risk.
- Parity gate: the max-form pair at the 4% production floor must reproduce
  the committed no_lockin_null_results.json anchors (central $818.530B /
  107.033%, null $748.185B / 97.834%, marginal +$70.345B / +9.198pp) to
  +/- $0.01B and +/- 0.01pp.
- Interpretive threshold, stated ex ante (the referee's own falsifier): if
  the additive-form marginal at the 4% floor lands within +/- 1.0pp of the
  max-form +9.198pp, the hard-max form is immaterial to the identified
  lock-in contribution; if it moves by more, the manuscript must report the
  form-dependence alongside the level-dependence wherever the marginal is
  quoted.

Run:  cd hazard && python3 floor_form_test.py
      -> data/floor_form_results.json (+ per-run parquets under
         data/floor_form/, regenerable, not committed)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import literature_hazard
from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
FORM_DIR = DATA_DIR / "floor_form"
RESULTS_JSON = DATA_DIR / "floor_form_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"

FORMS = ["max", "additive"]
FLOORS = [0.03, 0.04, 0.05]
PRODUCTION_FLOOR = 0.04
CENTRAL_PQ = 6.5
NULL_PQ = 0.0


def _run_scored(
    loans: pl.DataFrame, empirical: pd.DataFrame, form: str, floor: float,
    pq: float,
) -> dict:
    """One microsim run at (form, floor, elasticity), production convention."""
    literature_hazard.FLOOR_MODE = form
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    out_path = FORM_DIR / f"microsim_{form}_floor{floor * 100:g}pct_pq{pq:g}.parquet"
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


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0
    FORM_DIR.mkdir(parents=True, exist_ok=True)

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(
            f"{LOAN_SAMPLE_PATH} missing — build it via the production "
            "pipeline first (extension_risk.py --mode literature)."
        )
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    rows = []
    for form in FORMS:
        for floor in FLOORS:
            null = _run_scored(loans, empirical, form, floor, NULL_PQ)
            central = _run_scored(loans, empirical, form, floor, CENTRAL_PQ)
            row = {
                "form": form,
                "floor_annual_cpr_pct": floor * 100.0,
                "null": null,
                "central": central,
                "lockin_marginal_b": central["trapped_b"] - null["trapped_b"],
                "lockin_marginal_share_pp": (
                    central["share_pct"] - null["share_pct"]
                ),
            }
            rows.append(row)
            print(
                f"{form:>8} floor {floor * 100:3.0f}%:  "
                f"null ${null['trapped_b']:7.1f}B ({null['share_pct']:6.1f}%)  "
                f"central ${central['trapped_b']:7.1f}B "
                f"({central['share_pct']:6.1f}%)  marginal "
                f"${row['lockin_marginal_b']:+6.1f}B "
                f"({row['lockin_marginal_share_pp']:+5.2f}pp)"
            )
    runtime_s = time.perf_counter() - t0

    # ---- Parity gate: max form at production floor --------------------------
    prod = next(
        r for r in rows
        if r["form"] == "max" and r["floor_annual_cpr_pct"] == 4.0
    )
    with open(NULL_ARTIFACT) as f:
        anchor = json.load(f)
    gates = {
        "central_trapped_b": (
            prod["central"]["trapped_b"], anchor["central_trapped_b"]
        ),
        "null_trapped_b": (prod["null"]["trapped_b"], anchor["null_trapped_b"]),
        "lockin_marginal_b": (
            prod["lockin_marginal_b"], anchor["lockin_marginal_b"]
        ),
        "lockin_marginal_share_pp": (
            prod["lockin_marginal_share_pp"], anchor["lockin_marginal_share_pp"]
        ),
    }
    gate_report = {}
    for name, (got, want) in gates.items():
        ok = abs(got - want) < 0.01
        gate_report[name] = {"got": got, "want": want, "pass": bool(ok)}
        print(f"parity gate {name}: got {got:.4f} want {want:.4f} "
              f"[{'PASS' if ok else 'FAIL'}]")
    hard_fail = [k for k, v in gate_report.items() if not v["pass"]]

    # ---- Ex-ante interpretive threshold --------------------------------------
    add_prod = next(
        r for r in rows
        if r["form"] == "additive" and r["floor_annual_cpr_pct"] == 4.0
    )
    form_delta_pp = (
        add_prod["lockin_marginal_share_pp"] - prod["lockin_marginal_share_pp"]
    )
    verdict = (
        "additive-form marginal within +/-1pp of the max-form marginal at the "
        "production floor — the hard-max form is immaterial to the identified "
        "lock-in contribution"
        if abs(form_delta_pp) <= 1.0
        else "additive-form marginal moves by more than 1pp — report the "
        "form-dependence alongside the level-dependence wherever the marginal "
        "is quoted"
    )

    payload = {
        "mode": "floor_form_test",
        "spec": (
            "forms {max, additive-survival-scale}; floors {3,4,5}% annual "
            "CPR; central (p_q 6.5) + null (p_q 0) per (form, floor); "
            "production convention otherwise (75k sample, seed 42, "
            "US+Danish regime tuple, shared macro frame); raw-basis scoring; "
            "parity gates vs no_lockin_null_results.json at (max, 4%); "
            "ex-ante threshold: additive marginal within +/-1pp of max at 4%"
        ),
        "rows": rows,
        "parity_gates": gate_report,
        "parity_gates_all_pass": not hard_fail,
        "form_delta_pp_at_production_floor": form_delta_pp,
        "ex_ante_verdict": verdict,
        "runtime_s": round(runtime_s, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(
            payload, f, indent=2,
            default=lambda x: float(x)
            if isinstance(x, (np.floating, np.integer)) else x,
        )
        f.write("\n")

    print(f"\nform delta at production floor: {form_delta_pp:+.2f}pp")
    print(f"ex-ante verdict: {verdict}")
    if hard_fail:
        raise SystemExit(
            f"PARITY GATE FAILURE: {hard_fail} — results written to "
            f"{RESULTS_JSON} for diagnosis but must not be cited"
        )
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
