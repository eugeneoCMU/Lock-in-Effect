#!/usr/bin/env python3
"""
Round-15 Q3: heterogeneity decomposition of the Path B lock-in marginal
by coupon cohort x vintage (group-ablation design).

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------
Reviewer question (round 15, Q3): is the +9.2pp marginal absorbing other
nonlinearities tied to the rate gap (seasoning, coupon cohort)?  The
by-construction answer is in the manuscript (the null is a paired ablation
zeroing only beta1); this run adds the missing empirical complement: WHERE
the marginal lives, decomposed over the loan sample.

Design
------
Group-ablation: for each cell g of a vintage x coupon-bucket grid, run the
production US-regime microsim with a PER-LOAN beta1 vector that zeroes the
lock-in elasticity ONLY for loans in g (all other loans keep the production
beta1 = rothstein_beta1(0.065)).  The cell's marginal is

    marginal_g = central_trapped - variant_g_trapped      (standalone scorer)

i.e. the trapped-liquidity dollars attributable to lock-in acting on cell g,
holding everything else at production.  Identical 75,000-loan committed
sample (data/loan_sample.parquet), identical RNG seed (config.RNG_SEED; US
regime = index 0 => seed unshifted), PREPAY_MODE=fractional, identical macro
frame.  The engine amendment (competing_risks.monthly_step accepting a
per-loan beta1 vector, indexed by the active mask) is a pure generalization:
a constant vector is elementwise bit-identical to the scalar path, which
gates G1/G2 verify against the committed artifacts before any variant runs.

Grid (15 cells)
---------------
vintage in {2017, 2018, 2019, 2020, 2021}  x  coupon bucket in
{"<3.0%", "3.0-4.0%", ">=4.0%"} (note coupon stored as decimal in the
sample; bucket edges 0.03 / 0.04, left-closed on the middle bucket).

Gates (must PASS before variants are interpreted)
-------------------------------------------------
G1 central parity: vector path with the CONSTANT production beta1 vector
   reproduces the committed central exactly:
   trapped 818.5300844066606 B (share 107.0326190295068%), tolerance
   |diff| <= 1e-6 B (bit-exact expected; raw diff reported).
G2 null parity: all-zero vector reproduces the committed null exactly:
   trapped 748.1850239867648 B (share 97.83415925879702%), same tolerance.
G3 additivity: sum_g marginal_g vs the committed total marginal
   +70.34506041989584 B (+9.198459770709789 pp).  The design is not exactly
   additive (cohort burnout couples loans within a stratum across cells, and
   the monthly WSHOMCB rescale couples the aggregate balance); the residual
   IS the interaction term.  Ex-ante interpretation rule:
     |residual| <= 10% of the total marginal  ->  cells are read as shares
       of the marginal (shares computed against sum_g, residual disclosed);
     |residual|  > 10%                        ->  decomposition reported as
       approximate only; no share language in the manuscript.

Output
------
data/marginal_decomposition_results.json:
  gates (G1/G2 raw diffs + PASS/FAIL, G3 residual + verdict), per-cell rows
  {vintage, coupon_bucket, n_loans, balance_share_pct, marginal_b,
   marginal_pp, share_of_sum_pct}, run metadata.

Basis note: marginals are computed under the standalone scorer; the
manuscript's marginal is basis-invariant (the 9.1pp shared-layer netting is
common to both legs and cancels), so cell marginals carry to the shared
basis unchanged.

Run:  cd hazard && python3 marginal_decomposition.py
Runtime estimate: 17 engine legs x ~23 s ~= 7 min.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import LOAN_SAMPLE_PATH, QT_START, RNG_SEED, ROTHSTEIN_Q_DECLINE_MID
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, calculate_dynamic_friction, fetch_data, fetch_soma_mbs_monthly
from markov import load_transition_matrix
from microsim_engine import _simulate_regime

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "marginal_decomposition_results.json"

# Committed anchors (data/no_lockin_null_results.json) — quoted, not re-derived.
CENTRAL_TRAPPED_B = 818.5300844066606
NULL_TRAPPED_B = 748.1850239867648
TOTAL_MARGINAL_B = 70.34506041989584
TOTAL_MARGINAL_PP = 9.198459770709789
BENCHMARK_B = 764.7  # printed rounding; shares computed from scorer output
PARITY_TOL_B = 1e-6
ADDITIVITY_TOL_FRAC = 0.10

COUPON_EDGES = (0.03, 0.04)  # decimal; buckets <3.0%, [3.0,4.0)%, >=4.0%
COUPON_LABELS = ("<3.0%", "3.0-4.0%", ">=4.0%")


def coupon_bucket(coupon_dec: np.ndarray) -> np.ndarray:
    """0/1/2 bucket codes on the decimal coupon."""
    return np.digitize(coupon_dec, COUPON_EDGES)  # <0.03 ->0, [0.03,0.04) ->1, >=0.04 ->2


def run_leg(loans: pl.DataFrame, macro: pd.DataFrame, trans, holdings_b: float,
            beta1_vec: np.ndarray, empirical: pd.DataFrame) -> float:
    sim = _simulate_regime(loans, macro, "US", holdings_b, trans,
                           seed=RNG_SEED, beta1=beta1_vec)
    return float(score_extension_risk(sim, empirical)["hazard_trapped_b"])


def main() -> None:
    t0 = time.perf_counter()
    beta1_prod = rothstein_beta1(ROTHSTEIN_Q_DECLINE_MID)

    print("Building macro/empirical frames …")
    macro_raw = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro_raw, soma_rolloff=soma)
    macro = calculate_dynamic_friction(macro_raw)
    trans = load_transition_matrix()
    qt_start_idx = macro.index.get_indexer([QT_START], method="nearest")[0]
    holdings_b = float(macro.iloc[qt_start_idx]["WSHOMCB"]) / 1_000

    loans = pl.read_parquet(LOAN_SAMPLE_PATH)
    n = len(loans)
    vintage = loans["vintage"].to_numpy()
    coupon = loans["coupon"].to_numpy()  # decimal in the committed sample
    balance = loans["balance"].to_numpy()
    cbucket = coupon_bucket(coupon)

    # --- Gates G1/G2 -------------------------------------------------------
    print("G1: constant production-beta1 vector vs committed central …")
    g1_trapped = run_leg(loans, macro, trans, holdings_b,
                         np.full(n, beta1_prod), empirical)
    g1_diff = g1_trapped - CENTRAL_TRAPPED_B
    g1_pass = abs(g1_diff) <= PARITY_TOL_B
    print(f"  central {g1_trapped:.10f} B  diff {g1_diff:+.3e}  {'PASS' if g1_pass else 'FAIL'}")

    print("G2: all-zero vector vs committed null …")
    g2_trapped = run_leg(loans, macro, trans, holdings_b,
                         np.zeros(n), empirical)
    g2_diff = g2_trapped - NULL_TRAPPED_B
    g2_pass = abs(g2_diff) <= PARITY_TOL_B
    print(f"  null {g2_trapped:.10f} B  diff {g2_diff:+.3e}  {'PASS' if g2_pass else 'FAIL'}")

    if not (g1_pass and g2_pass):
        payload = {
            "mode": "marginal_decomposition", "status": "GATE_FAILURE",
            "g1": {"trapped_b": g1_trapped, "diff_b": g1_diff, "pass": g1_pass},
            "g2": {"trapped_b": g2_trapped, "diff_b": g2_diff, "pass": g2_pass},
        }
        RESULTS_JSON.write_text(json.dumps(payload, indent=2) + "\n")
        raise SystemExit("Parity gate failure — variants not run.")

    # Empirical benchmark for pp conversion (same scorer denominator).
    bench = float(score_extension_risk(
        pd.read_parquet(DATA_DIR / "microsim_results.parquet"), empirical
    )["empirical_trapped_b"])

    # --- 15 ablation cells --------------------------------------------------
    rows = []
    total_bal = balance.sum()
    for v in sorted(set(int(x) for x in vintage)):
        for b, lab in enumerate(COUPON_LABELS):
            mask = (vintage == v) & (cbucket == b)
            n_g = int(mask.sum())
            if n_g == 0:
                rows.append({"vintage": v, "coupon_bucket": lab, "n_loans": 0,
                             "balance_share_pct": 0.0, "marginal_b": 0.0,
                             "marginal_pp": 0.0})
                continue
            vec = np.full(n, beta1_prod)
            vec[mask] = 0.0
            trapped = run_leg(loans, macro, trans, holdings_b, vec, empirical)
            marg_b = CENTRAL_TRAPPED_B - trapped
            rows.append({
                "vintage": v, "coupon_bucket": lab, "n_loans": n_g,
                "balance_share_pct": float(balance[mask].sum() / total_bal * 100),
                "marginal_b": marg_b,
                "marginal_pp": marg_b / bench * 100,
            })
            print(f"  {v} {lab:>9}: n={n_g:>6}  marginal {marg_b:+7.3f} B")

    sum_marg = sum(r["marginal_b"] for r in rows)
    residual = TOTAL_MARGINAL_B - sum_marg
    additivity_ok = abs(residual) <= ADDITIVITY_TOL_FRAC * TOTAL_MARGINAL_B
    for r in rows:
        r["share_of_sum_pct"] = (r["marginal_b"] / sum_marg * 100) if sum_marg else 0.0

    payload = {
        "mode": "marginal_decomposition",
        "spec": "round-15 Q3 group-ablation; grid vintage x coupon {<3.0,3.0-4.0,>=4.0}%",
        "engine": "production US regime, fractional mode, seed RNG_SEED, committed 75k sample",
        "basis": "standalone scorer; marginal basis-invariant per manuscript Sec V",
        "gates": {
            "G1_central_parity": {"trapped_b": g1_trapped, "diff_b": g1_diff, "pass": g1_pass},
            "G2_null_parity": {"trapped_b": g2_trapped, "diff_b": g2_diff, "pass": g2_pass},
            "G3_additivity": {
                "sum_cells_b": sum_marg,
                "committed_total_b": TOTAL_MARGINAL_B,
                "residual_b": residual,
                "residual_frac_of_total": residual / TOTAL_MARGINAL_B,
                "threshold_frac": ADDITIVITY_TOL_FRAC,
                "verdict": "shares_readable" if additivity_ok else "approximate_only",
            },
        },
        "benchmark_b": bench,
        "cells": rows,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\nSum of cells {sum_marg:+.3f} B vs committed {TOTAL_MARGINAL_B:+.3f} B "
          f"(residual {residual:+.3f} B, {residual/TOTAL_MARGINAL_B:+.1%}) -> "
          f"{payload['gates']['G3_additivity']['verdict']}")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
