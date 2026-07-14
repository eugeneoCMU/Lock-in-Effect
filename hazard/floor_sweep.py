#!/usr/bin/env python3
"""
Involuntary-turnover floor sweep (pre-registered; spec committed before any run).

The manuscript concedes floor circularity: the 4% annual-CPR involuntary-
turnover floor is anchored to 2023-24 in-window discount-cohort turnover,
binds in ~36% of evaluated loan-months, and sets much of Path B's aggregate
level — so the clean verification content is the +9.2pp marginal over the
beta1=0 null, not the level. This sweep quantifies how both the level and
that marginal move with the floor.

SPEC (fixed ex ante):
- Grid: floor annual CPR in {2.0, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0}%.
  4.0% is production (config.INVOLUNTARY_CPR_ANNUAL); the paper's empirical
  anchor for the floor is the 4-5% observed on 2023-24 discount cohorts.
- Two runs per floor, identical to production in every other respect (same
  committed 75k loan sample -> 40,234 window-start survivors, RNG_SEED=42,
  same ("US","Danish") regime tuple with per-regime seed offsets, one shared
  macro frame fetched once):
    central: p_q_shock_pct = 6.5  (production ex-ante central elasticity)
    null:    p_q_shock_pct = 0.0  (beta1 = 0 exactly; no-lock-in null)
- Raw-basis scoring via extension_risk.score_extension_risk (the scorer
  behind the committed production artifacts). Reported per floor: null and
  central trapped $B / % of the $764.7B benchmark, lock-in marginal $B and
  pp, and the floor-bind share of evaluated U.S. loan-months (instrumented
  by a value-preserving wrapper around competing_risks.prepay_hazard, the
  same patch point as the committed seasonality_concave_gap.py variant).
- Parity gates at floor = 4.0% (fresh runs, caches not consulted), against
  the committed hazard/data/no_lockin_null_results.json: central
  $818.530B / 107.033%, null $748.185B / 97.834%, marginal +$70.345B /
  +9.198pp, tolerance +/- $0.01B and +/- 0.01pp (production Path B is
  fractional/deterministic). Bind instrumentation must reproduce the
  manuscript's ~36% of ~1,683,124 evaluated loan-months (+/- 1pp on the
  share, +/- 0.5% on the count) at 4.0%, else the bind column is withdrawn,
  not reinterpreted.
- Interpretive thresholds, stated ex ante: if the lock-in marginal moves by
  more than +/- 2.0pp across the empirically plausible 3-5% floor range,
  the manuscript's "clean verification content" sentence must be weakened;
  if it stays within that band, the floor-circularity concession stands as
  written and gains a quantified robustness note.

Run:  cd hazard && python3 floor_sweep.py
      -> data/floor_sweep_results.json (+ per-run parquets under
         data/floor_sweep/, regenerable, not committed)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import competing_risks
import literature_hazard
from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from literature_hazard import cpr_annual_to_monthly_hazard, rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
SWEEP_DIR = DATA_DIR / "floor_sweep"
RESULTS_JSON = DATA_DIR / "floor_sweep_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"

FLOORS = [0.02, 0.03, 0.035, 0.04, 0.045, 0.05, 0.06]
PRODUCTION_FLOOR = 0.04
CENTRAL_PQ = 6.5  # ROTHSTEIN_Q_DECLINE_MID * 100 — production central
NULL_PQ = 0.0

# Manuscript anchors for the bind-instrumentation gate (v16 §V.C / App. B:
# "binds in 36% of the 1,683,124 evaluated loan-months").
BIND_SHARE_ANCHOR = 0.36
BIND_N_ANCHOR = 1_683_124

_ORIG_PREPAY = competing_risks.prepay_hazard


class BindTally:
    """Counts U.S. loan-months where the involuntary floor lifts the hazard."""

    def __init__(self) -> None:
        self.bound = 0
        self.n = 0

    @property
    def share(self) -> float:
        return self.bound / self.n if self.n else float("nan")


def _tallying_prepay(tally: BindTally):
    """Value-preserving wrapper: returns exactly what production returns,
    and additionally tallies bind = (volitional hazard < floor hazard) by
    re-evaluating the original with the floor zeroed. prepay_hazard is only
    reached on the U.S. branch of competing_risks (the Danish branch routes
    through berger_calibration), so no regime flag is needed."""

    def wrapped(*args, **kwargs):
        out = _ORIG_PREPAY(*args, **kwargs)
        cur = literature_hazard.INVOLUNTARY_CPR_ANNUAL
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = 0.0
        try:
            h_vol = _ORIG_PREPAY(*args, **kwargs)
        finally:
            literature_hazard.INVOLUNTARY_CPR_ANNUAL = cur
        h_floor = float(
            cpr_annual_to_monthly_hazard(np.array([cur], dtype=np.float64))[0]
        )
        h_vol = np.asarray(h_vol)
        tally.bound += int((h_vol < h_floor).sum())
        tally.n += int(h_vol.size)
        return out

    return wrapped


def _run_scored(
    loans: pl.DataFrame, empirical: pd.DataFrame, floor: float, pq: float
) -> dict:
    """One microsim run at (floor, elasticity), production convention."""
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    tally = BindTally()
    competing_risks.prepay_hazard = _tallying_prepay(tally)
    out_path = SWEEP_DIR / f"microsim_floor{floor * 100:g}pct_pq{pq:g}.parquet"
    try:
        run_qt_microsim(loan_sample=loans, output=out_path, p_q_shock_pct=pq)
    finally:
        competing_risks.prepay_hazard = _ORIG_PREPAY
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)
    return {
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "cpr_r_lag0": float(score["cross_correlation"].get(0, float("nan"))),
        "best_lag": score["best_lag"],
        "peak_lag_r": float(score["peak_lag_r"]),
        "mean_us_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
        "floor_bind_share": tally.share,
        "floor_bind_loan_months": tally.n,
    }


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0, "p_q shock 0 must give exactly beta1=0"
    SWEEP_DIR.mkdir(parents=True, exist_ok=True)

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
    for floor in FLOORS:
        null = _run_scored(loans, empirical, floor, NULL_PQ)
        central = _run_scored(loans, empirical, floor, CENTRAL_PQ)
        row = {
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
            f"floor {floor * 100:4.1f}%:  null ${null['trapped_b']:7.1f}B "
            f"({null['share_pct']:6.1f}%)   central ${central['trapped_b']:7.1f}B "
            f"({central['share_pct']:6.1f}%)   marginal "
            f"${row['lockin_marginal_b']:+6.1f}B "
            f"({row['lockin_marginal_share_pp']:+5.1f}pp)   "
            f"bind {central['floor_bind_share'] * 100:4.1f}%"
        )
    runtime_s = time.perf_counter() - t0

    # ---- Parity gates at the production floor -------------------------------
    prod = next(r for r in rows if r["floor_annual_cpr_pct"] == 4.0)
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
    }
    gate_report = {}
    for name, (got, want) in gates.items():
        ok = abs(got - want) < 0.01
        gate_report[name] = {"got": got, "want": want, "pass": bool(ok)}
        status = "PASS" if ok else "FAIL"
        print(f"parity gate {name}: got {got:.4f} want {want:.4f} [{status}]")
    pp_got = prod["lockin_marginal_share_pp"]
    pp_want = anchor["lockin_marginal_share_pp"]
    ok = abs(pp_got - pp_want) < 0.01
    gate_report["lockin_marginal_share_pp"] = {
        "got": pp_got, "want": pp_want, "pass": bool(ok),
    }
    print(
        f"parity gate lockin_marginal_share_pp: got {pp_got:.4f} "
        f"want {pp_want:.4f} [{'PASS' if ok else 'FAIL'}]"
    )

    bind = prod["central"]
    bind_share_ok = abs(bind["floor_bind_share"] - BIND_SHARE_ANCHOR) <= 0.01
    bind_n_ok = (
        abs(bind["floor_bind_loan_months"] - BIND_N_ANCHOR) / BIND_N_ANCHOR
        <= 0.005
    )
    gate_report["bind_instrumentation"] = {
        "share_got": bind["floor_bind_share"],
        "share_anchor": BIND_SHARE_ANCHOR,
        "n_got": bind["floor_bind_loan_months"],
        "n_anchor": BIND_N_ANCHOR,
        "pass": bool(bind_share_ok and bind_n_ok),
    }
    print(
        f"bind gate: share {bind['floor_bind_share']:.3f} vs "
        f"{BIND_SHARE_ANCHOR} | n {bind['floor_bind_loan_months']:,} vs "
        f"{BIND_N_ANCHOR:,} [{'PASS' if bind_share_ok and bind_n_ok else 'FAIL'}]"
    )
    if not (bind_share_ok and bind_n_ok):
        # Pre-registered remedy: withdraw the column, do not reinterpret it.
        for r in rows:
            for leg in ("null", "central"):
                r[leg]["floor_bind_share"] = None
                r[leg]["floor_bind_loan_months"] = None
        print("bind instrumentation failed its gate — bind columns withdrawn")

    hard_fail = [
        k for k, v in gate_report.items()
        if k != "bind_instrumentation" and not v["pass"]
    ]

    # ---- Ex-ante interpretive threshold --------------------------------------
    plaus = [
        r["lockin_marginal_share_pp"]
        for r in rows
        if 3.0 <= r["floor_annual_cpr_pct"] <= 5.0
    ]
    marginal_range_pp = max(plaus) - min(plaus)
    verdict = (
        "marginal floor-dependent — weaken the verification-content sentence"
        if marginal_range_pp > 2.0
        else "marginal stable across 3-5% floors — concession stands as "
        "written; add quantified robustness note"
    )

    payload = {
        "mode": "floor_sweep",
        "spec": (
            "floors {2,3,3.5,4,4.5,5,6}% annual CPR; central (p_q 6.5) + "
            "null (p_q 0) per floor; production convention otherwise "
            "(75k sample, seed 42, US+Danish regime tuple, shared macro "
            "frame); raw-basis scoring; gates vs no_lockin_null_results.json "
            "at 4%; ex-ante threshold: marginal +/-2pp over 3-5% floors"
        ),
        "rows": rows,
        "parity_gates": gate_report,
        "parity_gates_all_pass": not hard_fail,
        "marginal_range_pp_3to5": marginal_range_pp,
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

    print(f"\nmarginal range over 3-5% floors: {marginal_range_pp:.2f}pp")
    print(f"ex-ante verdict: {verdict}")
    if hard_fail:
        raise SystemExit(
            f"PARITY GATE FAILURE: {hard_fail} — results written to "
            f"{RESULTS_JSON} for diagnosis but must not be cited"
        )
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
