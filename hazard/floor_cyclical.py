#!/usr/bin/env python3
"""
W2 cyclical-floor variant (pre-committed; spec fixed in this header before
any run executed — round-14 W2, NEEDS-NEW-RUN item).

Referee residual: eq. (3)'s involuntary-turnover floor is a single constant
(4% annual CPR), so involuntary turnover is treated as ACYCLICAL; the
marginal-over-null construction cancels the floor's LEVEL but not a floor
that co-varies with the rate cycle. The constant-floor sweep
(floor_sweep_results.json) brackets the level; this run brackets the
cyclicality.

SPEC (fixed ex ante):
- Floor law: floor_t = 0.04 * (1 + kappa * z_t), clipped at >= 0, where z_t
  is the QT-window-standardized 30-year mortgage rate (MORTGAGE30US from the
  shared macro frame, decimal, sample std ddof=1). The window MEAN of floor_t
  is 4% by construction for every kappa (production nested at kappa = 0, not
  re-leveled); if the clip ever binds, pinning is broken and the artifact
  records it (clip_bound flag per cell).
- Driver: the mortgage rate IS the observable rate-cycle driver named by the
  manuscript's future-work sentence; kappa > 0 means involuntary turnover
  RISES with rates, kappa < 0 means it falls (the lock-in-adverse direction:
  fewer forced moves exactly when voluntary refinancing is suppressed).
- Kappa grid: {-0.5, -0.25, -0.1, 0, +0.1, +0.25, +0.5} in standardized
  units (at the window's |z| <= ~2, kappa = 0.5 swings the floor roughly
  +/- 100% of its level — a deliberate stress envelope; the floor stays
  strictly positive so pinning holds exactly across the grid).
- Two legs per kappa: central p_q shock 6.5, null 0.0. Production convention
  otherwise: committed 75k Freddie loan sample, RNG_SEED 42, ("US","Danish")
  regime tuple with per-regime seed offsets, one shared macro frame,
  raw-basis scoring via extension_risk.score_extension_risk. Implementation
  wraps microsim_engine.monthly_step to set the month's floor from the
  market rate the engine already passes; kappa = 0 sets 0.04 every month,
  i.e. the production code path bit-for-bit.
- Parity gate: the kappa = 0 pair must reproduce the committed
  no_lockin_null_results.json anchors (central $818.530B / 107.033%, null
  $748.185B / 97.834%, marginal +$70.345B / +9.198pp) to +/- $0.01B and
  +/- 0.01pp. Withdraw-not-reinterpret on failure.
- Interpretive threshold, stated ex ante (the manuscript's own falsifier,
  sec:limitations): the constant-floor LEVEL sweep at p_q = 6.5 spans
  marginals +10.8pp (3% floor) to +5.5pp (5% floor). If every kappa cell's
  marginal stays inside the level-sweep envelope (read at runtime from the
  committed floor_sweep_results.json, p_q = 6.5 rows, floors 3-5%), then
  floor cyclicality is already bounded by the reported level sweep and the
  acyclical-floor concession stands as written; if any cell exits the
  envelope, the manuscript must report cyclical-floor sensitivity alongside
  the level sweep wherever the marginal is quoted.

Run:  cd hazard && python3 floor_cyclical.py
      -> data/floor_cyclical_results.json (+ per-run parquets under
         data/floor_cyclical/, regenerable, not committed)
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

DATA_DIR = Path(__file__).parent / "data"
CYCL_DIR = DATA_DIR / "floor_cyclical"
RESULTS_JSON = DATA_DIR / "floor_cyclical_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
SWEEP_ARTIFACT = DATA_DIR / "floor_sweep_results.json"

PRODUCTION_FLOOR = 0.04
KAPPA_GRID = [-0.5, -0.25, -0.1, 0.0, 0.1, 0.25, 0.5]
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
PARITY_TOL = 0.01


class CyclicalFloor:
    """floor_t = 0.04 * (1 + kappa * z_t), clipped >= 0.

    Window-mean-pinned at 4% ONLY where the non-negativity clip does not bind.
    The clip binds at |kappa| = 0.5, where realized window means are 4.0005%
    and 4.0828%; those cells set the grid's low end. See TECHNICAL.md 24.1a.
    """

    def __init__(self, window_rates: pd.Series, kappa: float,
                 base: float = PRODUCTION_FLOOR):
        self.kappa = float(kappa)
        self.base = float(base)
        self.mean = float(np.mean(window_rates))
        self.std = float(pd.Series(window_rates).std(ddof=1))
        self.clip_bound = False

    def floor_at(self, market_rate: float) -> float:
        if self.kappa == 0.0:
            return self.base
        z = (float(market_rate) - self.mean) / self.std
        raw = self.base * (1.0 + self.kappa * z)
        if raw < 0.0:
            self.clip_bound = True
            return 0.0
        return raw


def _qt_window_rates(macro: pd.DataFrame) -> pd.Series:
    from config import QT_END, QT_START

    idx = macro.index[(macro.index >= QT_START) & (macro.index < QT_END)]
    return macro.loc[idx, "MORTGAGE30US"] / 100.0


def _run_scored(loans, empirical, macro, kappa: float, pq: float) -> dict:
    """One microsim run at (kappa, elasticity), production convention
    otherwise. Wraps microsim_engine.monthly_step so each month's floor is
    set from the market rate the engine already passes; restores everything
    afterward."""
    import literature_hazard
    import microsim_engine
    from extension_risk import score_extension_risk
    from literature_hazard import rothstein_beta1

    cf = CyclicalFloor(_qt_window_rates(macro), kappa=kappa)
    orig_step = microsim_engine.monthly_step

    def _cyclical_step(pool, market_rate, trans=None, beta1=None):
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = cf.floor_at(market_rate)
        try:
            return orig_step(pool, market_rate, trans=trans, beta1=beta1)
        finally:
            literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR

    out_path = CYCL_DIR / f"microsim_kappa{kappa:+g}_pq{pq:g}.parquet"
    microsim_engine.monthly_step = _cyclical_step
    try:
        microsim_engine.run_qt_microsim(
            loan_sample=loans, macro=macro, output=out_path, p_q_shock_pct=pq
        )
    finally:
        microsim_engine.monthly_step = orig_step
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR

    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)
    return {
        "kappa": kappa,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "clip_bound": cf.clip_bound,
    }


def _level_sweep_envelope() -> tuple[float, float, list]:
    """Constant-floor sweep marginals (p_q = 6.5) over the 3-5% floors."""
    sweep = json.load(open(SWEEP_ARTIFACT))
    rows = [
        r for r in sweep["rows"]
        if 3.0 <= r["floor_annual_cpr_pct"] <= 5.0
    ]
    vals = [r["lockin_marginal_share_pp"] for r in rows]
    return min(vals), max(vals), rows


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    from config import LOAN_SAMPLE_PATH
    from literature_hazard import rothstein_beta1
    from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

    assert rothstein_beta1(0.0) == 0.0
    CYCL_DIR.mkdir(parents=True, exist_ok=True)

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing.")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    cells = []
    for kappa in KAPPA_GRID:
        null = _run_scored(loans, empirical, macro, kappa, NULL_PQ)
        central = _run_scored(loans, empirical, macro, kappa, CENTRAL_PQ)
        cell = {
            "kappa": kappa,
            "null": null,
            "central": central,
            "lockin_marginal_b": central["trapped_b"] - null["trapped_b"],
            "lockin_marginal_share_pp": (
                central["share_pct"] - null["share_pct"]
            ),
            "clip_bound": null["clip_bound"] or central["clip_bound"],
        }
        cells.append(cell)
        print(
            f"kappa {kappa:+.2f}:  null ${null['trapped_b']:7.1f}B "
            f"({null['share_pct']:6.1f}%)  central ${central['trapped_b']:7.1f}B "
            f"({central['share_pct']:6.1f}%)  marginal "
            f"${cell['lockin_marginal_b']:+6.1f}B "
            f"({cell['lockin_marginal_share_pp']:+5.2f}pp)"
            + ("  [CLIP BOUND — pinning broken]" if cell["clip_bound"] else "")
        )

    # ---- Parity gate: kappa = 0 ---------------------------------------------
    prod = next(c for c in cells if c["kappa"] == 0.0)
    anchor = json.load(open(NULL_ARTIFACT))
    gates = {
        "central_trapped_b": (prod["central"]["trapped_b"], anchor["central_trapped_b"]),
        "null_trapped_b": (prod["null"]["trapped_b"], anchor["null_trapped_b"]),
        "lockin_marginal_b": (prod["lockin_marginal_b"], anchor["lockin_marginal_b"]),
        "lockin_marginal_share_pp": (
            prod["lockin_marginal_share_pp"], anchor["lockin_marginal_share_pp"]
        ),
    }
    gate_report = {}
    for name, (got, want) in gates.items():
        ok = abs(got - want) < PARITY_TOL
        gate_report[name] = {"got": got, "want": want, "pass": bool(ok)}
        print(f"parity gate {name}: got {got:.4f} want {want:.4f} "
              f"[{'PASS' if ok else 'FAIL'}]")
    parity_pass = all(v["pass"] for v in gate_report.values())

    # ---- Ex-ante interpretive threshold --------------------------------------
    env_min, env_max, env_rows = _level_sweep_envelope()
    marginals = [c["lockin_marginal_share_pp"] for c in cells]
    all_inside = all(env_min <= m <= env_max for m in marginals)
    verdict = (
        "cyclicality bounded by the reported level sweep; acyclical-floor "
        "concession stands as written"
        if all_inside else
        "at least one kappa cell exits the level-sweep envelope; report "
        "cyclical-floor sensitivity alongside the level sweep"
    )

    payload = {
        "mode": "floor_cyclical",
        "spec": "hazard/floor_cyclical.py module docstring (fixed ex ante)",
        "git_commit": _git_head(),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # Corrected 2026-07-19: this string previously asserted "window-mean
        # pinned at 4%" unqualified, which is false where the non-negativity
        # clip binds. It describes the spec; it is not a result, nothing reads
        # it as a value, and no gate keys off it -- so it is corrected rather
        # than preserved. See TECHNICAL.md 24.1a and
        # test_clip_breaks_the_window_mean_pin_on_the_real_floor_law.
        "floor_law": "floor_t = 0.04 * (1 + kappa * z_t), z_t standardized "
                     "QT-window MORTGAGE30US (ddof=1), clipped >= 0, "
                     "window mean pinned at 4% EXCEPT where the clip binds "
                     "(|kappa|=0.5: realized 4.000519% at -0.5, 4.082786% at "
                     "+0.5); kappa=+0.5 sets the grid's low end",
        "kappa_grid": KAPPA_GRID,
        "cells": cells,
        "parity_gate_kappa0": gate_report,
        "parity_gate_pass": parity_pass,
        "level_sweep_envelope_pp": {"min": env_min, "max": env_max,
                                    "source": "floor_sweep_results.json, "
                                              "p_q 6.5, floors 3-5%"},
        "marginal_range_pp": {"min": min(marginals), "max": max(marginals)},
        "all_cells_inside_level_envelope": all_inside,
        "verdict": verdict,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=float)
        f.write("\n")

    if not parity_pass:
        raise SystemExit(
            "PARITY GATE FAILED at kappa=0 — results recorded but must be "
            "withdrawn, not reinterpreted."
        )
    print(f"\nVerdict: {verdict}")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
