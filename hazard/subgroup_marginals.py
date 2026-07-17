#!/usr/bin/env python3
"""
Round-18 R18-A (referee M1 + E2 + Q3), gate #48: subgroup decomposition of the
Path B lock-in marginal by FICO bucket, LTV bucket, and Census region.

SPEC (committed before execution; grids, gates, tolerances, and verdict
language all fixed ex ante — this docstring precedes the logic)
=====================================================================

Motivation
----------
The referee asks (three times: weakness M1, detailed comment E2, question Q3)
for the +9.2pp lock-in marginal to be decomposed across borrower/loan/geography
subgroups; "a stable +9.2pp across groups would bolster generality." The
committed engine `marginal_decomposition.py` already grids the marginal over
vintage x coupon (15 cells, all positive, committed artifact
`data/marginal_decomposition_results.json`). This run reuses that engine
UNCHANGED — same paired central/null legs, same standalone scorer, same seed,
same 75,000-loan committed sample — and extends the group-ablation grid to the
three dimensions the referee names but the committed run does not cover:
FICO bucket, LTV bucket, and region. No simulation logic is duplicated:
`run_leg` and the committed anchors are imported from `marginal_decomposition`,
and `_simulate_regime` / `score_extension_risk` are the same production paths.

Design (identical to the committed vintage x coupon run)
--------------------------------------------------------
Group-ablation: for each cell g of a grid, run the production US-regime microsim
with a PER-LOAN beta1 vector that zeroes the lock-in elasticity ONLY for loans
in g (all other loans keep the production beta1 = rothstein_beta1(0.065)). The
cell marginal is

    marginal_g = central_trapped - variant_g_trapped      (standalone scorer)

i.e. the trapped-liquidity dollars attributable to lock-in acting on cell g,
holding everything else at production. Same committed sample
(data/loan_sample.parquet, 75,000 loans), same RNG seed (config.RNG_SEED; US
regime index 0 => seed unshifted), PREPAY_MODE=fractional, same macro frame.

Grids (each grid independently partitions all 75,000 loans)
-----------------------------------------------------------
- fico_bucket (3 cells): "<680" / "680-740" / "740+"  — the sample's own
  fico_bucket field (config.FICO_BINS edges 680/740).
- ltv_bucket (2 cells): "<=80" / ">80"  — the sample's own ltv_bucket field
  (config.LTV_THRESHOLD = 80).
- region (4 cells): Census regions Northeast / Midwest / South / West, mapped
  from property_state via agents.STATE_TO_REGION with the SAME fallback the
  production pool uses (`.get(state, 3)` -> unmapped territories GU/PR/VI fold
  into West, exactly as agents.MicrosimPool.region_code is built). This keeps
  the region cells a bit-faithful partition of the production regional
  definition rather than inventing a new one.

Because each grid is a complete partition of the sample, each grid's cell
marginals sum (up to the interaction residual) to the same committed total.

Gates (parity gates are HARD asserts and run BEFORE any cell is read)
--------------------------------------------------------------------
G1 central parity: constant production-beta1 vector reproduces the committed
   central trapped 818.5300844066606 B (share 107.03%), |diff| <= 1e-6 B
   (bit-exact expected). Imported anchor CENTRAL_TRAPPED_B.
G2 null parity: all-zero vector reproduces the committed null trapped
   748.1850239867648 B (share 97.83%), same tolerance. Imported anchor
   NULL_TRAPPED_B. (This is the parity form the committed pattern asserts;
   the constant-vector-vs-scalar equivalence it verifies IS the CPR-path
   identity, since a constant per-loan vector drives the engine bit-identically
   to the scalar production path.)
   >>> If G1 or G2 fail, the run STOPS before any subgroup number is computed;
       tolerances are NOT loosened. <<<
G3 per-grid additivity (one verdict per grid, same tolerance class as the
   committed 1.03% vintage x coupon residual): sum_g marginal_g vs the committed
   total marginal +70.34506041989584 B (+9.198459770709789 pp). The design is
   not exactly additive — cohort burnout couples loans within a stratum across
   cells and the monthly WSHOMCB rescale couples the aggregate balance; the
   residual IS the interaction term. Ex-ante rule (imported ADDITIVITY_TOL_FRAC
   = 0.10):
     |residual| <= 10% of total  -> shares_readable (cells reported as shares of
        sum_g, residual disclosed);
     |residual|  > 10%            -> approximate_only (no share language).

Reporting quantities (fixed ex ante, per cell)
----------------------------------------------
  marginal_b        cell marginal in $B (full precision)
  marginal_pp       marginal_b / empirical_benchmark_b * 100 (same scorer
                    denominator as the committed run, 764.748... B)
  balance_share_pct raw cell balance / total balance * 100 (raw balance, as in
                    the committed run — not weight-adjusted)
  share_of_sum_pct  marginal_b / sum_g marginal_g * 100 (only meaningful when
                    the grid's G3 verdict is shares_readable)
  intensity         per-balance intensity = share_of_sum_pct / balance_share_pct
                    (the committed vintage x coupon run spans 0.84-1.5x)

Verdict language (pre-committed, covers BOTH outcomes) — per grid
-----------------------------------------------------------------
Two ex-ante conditions define a broad-based grid:
  (a) sign homogeneity: every cell marginal_b > 0; AND
  (b) intensity band: every cell's per-balance intensity in
      INTENSITY_BROAD_BAND = [0.5, 2.0]  (i.e. no subgroup's marginal share is
      disproportionate to its balance share by more than 2x in either
      direction; the committed vintage x coupon cells all fall in 0.84-1.5).
Verdict per grid:
  "broad_based"              if (a) and (b) hold  -> the marginal is carried
      broadly across the dimension in rough proportion to balance; generality
      of the +9.2pp is supported on this dimension.
  "materially_heterogeneous" otherwise -> at least one cell either contributes
      with the wrong sign or is disproportionate to its balance; the offending
      cells are named and the marginal is reported as concentrated/heterogeneous
      on this dimension (honest report, no share-language spin).
Overall verdict = "broad_based_all_dimensions" iff all three grids are
broad_based, else "heterogeneous_on:<grids>" naming the dimensions that are not.
Both branches are pre-written; whichever the data selects is reported verbatim.

Output
------
data/subgroup_marginals_results.json: spec echo, gates block (G1/G2 raw diffs +
PASS/FAIL; G3 per grid), per-grid cell tables, overall verdict, metadata.

Run:  cd hazard && python3 subgroup_marginals.py
Runtime estimate: (2 gate legs + 3+2+4 cell legs) = 11 engine legs x ~12 s
  ~= 2-4 min (cf. committed 17-leg run at 190.2 s).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import LOAN_SAMPLE_PATH, QT_START, RNG_SEED, ROTHSTEIN_Q_DECLINE_MID
from agents import STATE_TO_REGION
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, calculate_dynamic_friction, fetch_data, fetch_soma_mbs_monthly
from markov import load_transition_matrix

# Reuse the committed engine wrapper and anchors verbatim — no logic duplicated.
from marginal_decomposition import (
    ADDITIVITY_TOL_FRAC,
    CENTRAL_TRAPPED_B,
    NULL_TRAPPED_B,
    PARITY_TOL_B,
    TOTAL_MARGINAL_B,
    TOTAL_MARGINAL_PP,
    run_leg,
)

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "subgroup_marginals_results.json"

# Pre-committed verdict band (see docstring).
INTENSITY_BROAD_BAND = (0.5, 2.0)

REGION_LABELS = {0: "Northeast", 1: "Midwest", 2: "South", 3: "West"}
FICO_ORDER = ("<680", "680-740", "740+")
LTV_ORDER = ("≤80", ">80")  # "<=80" glyph as stored in the sample


def region_codes_for(states: list[str]) -> np.ndarray:
    """Faithful copy of agents.MicrosimPool.region_code construction."""
    return np.array([STATE_TO_REGION.get(str(s).strip(), 3) for s in states], dtype=int)


def build_grids(loans: pl.DataFrame):
    """Return {grid_name: [(cell_label, mask), ...]} — each grid a full partition."""
    n = len(loans)
    fico_b = loans["fico_bucket"].to_list()
    ltv_b = loans["ltv_bucket"].to_list()
    states = loans["property_state"].to_list()
    fico_arr = np.array(fico_b, dtype=object)
    ltv_arr = np.array(ltv_b, dtype=object)
    region_arr = region_codes_for(states)

    grids = {}
    grids["fico_bucket"] = [(lab, (fico_arr == lab)) for lab in FICO_ORDER]
    grids["ltv_bucket"] = [(lab, (ltv_arr == lab)) for lab in LTV_ORDER]
    grids["region"] = [(REGION_LABELS[c], (region_arr == c)) for c in (0, 1, 2, 3)]

    # Partition sanity: every grid must cover all n loans with no overlap.
    for name, cells in grids.items():
        stacked = np.vstack([m for _, m in cells])
        covered = stacked.sum(axis=0)
        assert covered.min() == 1 and covered.max() == 1, (
            f"grid {name} is not a clean partition: coverage min "
            f"{covered.min()} max {covered.max()}"
        )
        assert sum(int(m.sum()) for _, m in cells) == n
    return grids


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
    balance = loans["balance"].to_numpy()
    total_bal = balance.sum()

    # --- Gates G1/G2 (HARD; run and asserted BEFORE any subgroup leg) --------
    print("G1: constant production-beta1 vector vs committed central …")
    g1_trapped = run_leg(loans, macro, trans, holdings_b, np.full(n, beta1_prod), empirical)
    g1_diff = g1_trapped - CENTRAL_TRAPPED_B
    g1_pass = abs(g1_diff) <= PARITY_TOL_B
    print(f"  central {g1_trapped:.10f} B  diff {g1_diff:+.3e}  {'PASS' if g1_pass else 'FAIL'}")

    print("G2: all-zero vector vs committed null …")
    g2_trapped = run_leg(loans, macro, trans, holdings_b, np.zeros(n), empirical)
    g2_diff = g2_trapped - NULL_TRAPPED_B
    g2_pass = abs(g2_diff) <= PARITY_TOL_B
    print(f"  null {g2_trapped:.10f} B  diff {g2_diff:+.3e}  {'PASS' if g2_pass else 'FAIL'}")

    if not (g1_pass and g2_pass):
        payload = {
            "mode": "subgroup_marginals", "status": "GATE_FAILURE",
            "g1": {"trapped_b": g1_trapped, "diff_b": g1_diff, "pass": g1_pass},
            "g2": {"trapped_b": g2_trapped, "diff_b": g2_diff, "pass": g2_pass},
        }
        RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
        raise SystemExit("Parity gate failure — subgroup legs not run.")
    # Enforce before reading any subgroup number.
    assert g1_pass, "G1 central parity failed"
    assert g2_pass, "G2 null parity failed"

    # Same scorer denominator as the committed run for the pp conversion.
    bench = float(score_extension_risk(
        pd.read_parquet(DATA_DIR / "microsim_results.parquet"), empirical
    )["empirical_trapped_b"])

    grids = build_grids(loans)

    grid_results = {}
    gates_g3 = {}
    all_broad = True
    heterogeneous_dims = []

    for gname, cells in grids.items():
        print(f"\nGrid: {gname}")
        rows = []
        for lab, mask in cells:
            n_g = int(mask.sum())
            vec = np.full(n, beta1_prod)
            vec[mask] = 0.0
            trapped = run_leg(loans, macro, trans, holdings_b, vec, empirical)
            marg_b = CENTRAL_TRAPPED_B - trapped
            bshare = float(balance[mask].sum() / total_bal * 100)
            rows.append({
                "cell": lab,
                "n_loans": n_g,
                "balance_share_pct": bshare,
                "marginal_b": marg_b,
                "marginal_pp": marg_b / bench * 100,
            })
            print(f"  {lab:>10}: n={n_g:>6}  marginal {marg_b:+7.3f} B  bal_share {bshare:6.3f}%")

        sum_marg = sum(r["marginal_b"] for r in rows)
        residual = TOTAL_MARGINAL_B - sum_marg
        additivity_ok = abs(residual) <= ADDITIVITY_TOL_FRAC * TOTAL_MARGINAL_B
        for r in rows:
            r["share_of_sum_pct"] = (r["marginal_b"] / sum_marg * 100) if sum_marg else 0.0
            r["intensity"] = (
                r["share_of_sum_pct"] / r["balance_share_pct"]
                if r["balance_share_pct"] else 0.0
            )

        # Pre-committed verdict evaluation.
        sign_ok = all(r["marginal_b"] > 0 for r in rows)
        lo, hi = INTENSITY_BROAD_BAND
        band_ok = all(lo <= r["intensity"] <= hi for r in rows)
        broad = sign_ok and band_ok
        offenders = [
            r["cell"] for r in rows
            if not (r["marginal_b"] > 0 and lo <= r["intensity"] <= hi)
        ]
        verdict = "broad_based" if broad else "materially_heterogeneous"
        if not broad:
            all_broad = False
            heterogeneous_dims.append(gname)

        gates_g3[gname] = {
            "sum_cells_b": sum_marg,
            "committed_total_b": TOTAL_MARGINAL_B,
            "residual_b": residual,
            "residual_frac_of_total": residual / TOTAL_MARGINAL_B,
            "threshold_frac": ADDITIVITY_TOL_FRAC,
            "additivity_verdict": "shares_readable" if additivity_ok else "approximate_only",
            "pass": additivity_ok,
        }
        grid_results[gname] = {
            "cells": rows,
            "sum_cells_b": sum_marg,
            "residual_b": residual,
            "sign_homogeneous": sign_ok,
            "intensity_band": list(INTENSITY_BROAD_BAND),
            "intensity_band_ok": band_ok,
            "intensity_min": min(r["intensity"] for r in rows),
            "intensity_max": max(r["intensity"] for r in rows),
            "max_cell_share_pct": max(r["share_of_sum_pct"] for r in rows),
            "offending_cells": offenders,
            "verdict": verdict,
        }
        print(f"  sum {sum_marg:+.3f} B  residual {residual:+.3f} B "
              f"({residual/TOTAL_MARGINAL_B:+.2%})  additivity "
              f"{'OK' if additivity_ok else 'EXCEEDED'}  verdict {verdict}")

    overall = "broad_based_all_dimensions" if all_broad else (
        "heterogeneous_on:" + ",".join(heterogeneous_dims))

    payload = {
        "mode": "subgroup_marginals",
        "roadmap_item": "R18-A",
        "gate": 48,
        "spec": ("round-18 R18-A group-ablation; grids fico_bucket {<680,680-740,740+}, "
                 "ltv_bucket {<=80,>80}, region {Northeast,Midwest,South,West via "
                 "agents.STATE_TO_REGION, .get(state,3) fallback}"),
        "engine": ("production US regime, fractional mode, seed RNG_SEED, committed 75k "
                   "sample; run_leg + anchors imported from marginal_decomposition.py"),
        "basis": "standalone scorer; marginal basis-invariant per manuscript Sec V",
        "committed_anchors": {
            "central_trapped_b": CENTRAL_TRAPPED_B,
            "null_trapped_b": NULL_TRAPPED_B,
            "total_marginal_b": TOTAL_MARGINAL_B,
            "total_marginal_pp": TOTAL_MARGINAL_PP,
        },
        "gates": {
            "G1_central_parity": {"trapped_b": g1_trapped, "diff_b": g1_diff, "pass": g1_pass},
            "G2_null_parity": {"trapped_b": g2_trapped, "diff_b": g2_diff, "pass": g2_pass},
            "G3_additivity_per_grid": gates_g3,
        },
        "benchmark_b": bench,
        "grids": grid_results,
        "verdict_overall": overall,
        "verdict_intensity_band": list(INTENSITY_BROAD_BAND),
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\nOverall verdict: {overall}")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
