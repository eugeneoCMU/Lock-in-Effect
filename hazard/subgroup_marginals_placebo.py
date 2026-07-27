#!/usr/bin/env python3
"""
Discriminating-power placebo for the group-ablation "broad-based" verdict.
(Pre-committed; spec fixed in this header before any run executed.)

WHAT THIS MODULE IS FOR. subgroup_marginals.py (gate #48) partitions the
+$70.345 billion Path B lock-in marginal over FICO, LTV and Census-region
grids, finds every cell positive with per-balance intensity inside the
pre-committed [0.5, 2.0] band, and returns "broad_based" on all three
dimensions. revised_paper_v17.tex reads that verdict as evidence that the
marginal is a book-wide property rather than a cohort-specific one.

The verdict rule was never run against a partition that carries NO economic
content. That is the null this module supplies: replace the economic grids
with RANDOM 3-way partitions of the same 75,000 loans, push each through the
IDENTICAL group-ablation engine and the IDENTICAL ex-ante verdict rule, and
count how many earn "broad_based". If a random partition earns it too, the
verdict on its own does not discriminate, and the manuscript is not entitled
to read "broad_based" as an empirical finding about the marginal.

The interesting quantity is therefore NOT the verdict — which is expected to
pass, since a random partition splits any additive quantity in proportion to
balance almost by construction — but the DIRECTION of the band comparison.
A random partition concentrates its intensities on 1.0. The committed
economic grids do not have to. Whichever way that comparison falls is
reported verbatim (see VERDICT LANGUAGE below); both branches are pre-written.

SPEC (fixed ex ante)
====================

- ENGINE, unchanged from subgroup_marginals.py / marginal_decomposition.py:
  group-ablation under the production US regime. For each cell g, run the
  microsim with a PER-LOAN beta1 vector holding production
  beta1 = rothstein_beta1(0.065) everywhere except loans in g, which are
  zeroed. The cell marginal is CENTRAL_TRAPPED_B - variant_trapped under the
  standalone scorer. Same committed 75,000-loan sample
  (data/loan_sample.parquet), same config.RNG_SEED, same PREPAY_MODE, same
  macro frame. `run_leg` and every anchor are IMPORTED from
  marginal_decomposition.py — no simulation logic is duplicated here, so the
  placebo cannot differ from the committed run in anything but the labels.

- PLACEBO PARTITIONS: N_PLACEBO = 12 independent random 3-way partitions.
  Cardinality 3 matches the FICO grid, the committed grid with the widest
  intensity span, so the comparison is not a cell-count artifact. Labels are
  drawn i.i.d. uniform over {0,1,2} per loan from numpy.default_rng(SEED),
  SEED = 20260720, drawn in sequence so partition k is reproducible from the
  seed alone. Balance-share heterogeneity across cells is therefore whatever
  the draw gives (roughly 33% each); no balancing is imposed, because the
  intensity statistic already normalizes by balance share.
  Degenerate draws (any empty cell) would be redrawn and logged; with n =
  75,000 and three cells this cannot occur in practice and is asserted, not
  assumed.

- SCORING, identical to subgroup_marginals.py in every respect:
    marginal_b        CENTRAL_TRAPPED_B - variant_trapped
    marginal_pp       marginal_b / benchmark_b * 100, benchmark_b the same
                      764.748... standalone denominator
    balance_share_pct raw cell balance / total balance * 100
    share_of_sum_pct  marginal_b / sum_g marginal_g * 100
    intensity         share_of_sum_pct / balance_share_pct
  and the SAME pre-committed verdict rule:
    (a) sign homogeneity: every cell marginal_b > 0; AND
    (b) intensity band: every cell's intensity in INTENSITY_BROAD_BAND =
        [0.5, 2.0]   (imported, not restated, from subgroup_marginals.py)
    -> "broad_based" iff (a) and (b), else "materially_heterogeneous".
  Additivity is scored against the same imported ADDITIVITY_TOL_FRAC = 0.10.

- PARITY GATES (HARD; asserted BEFORE any placebo number is computed; on
  failure the run STOPS and writes a GATE_FAILURE payload rather than
  reinterpreting anything):
  G1 central parity: constant production-beta1 vector reproduces the committed
     CENTRAL_TRAPPED_B = 818.5300844066606, |diff| <= PARITY_TOL_B = 1e-6
     (bit-exact expected).
  G2 null parity: all-zero vector reproduces the committed
     NULL_TRAPPED_B = 748.1850239867648, same tolerance.
  G3 committed-cell reproduction: the FICO grid of the committed
     data/subgroup_marginals_results.json is RE-RUN here through this
     module's own loop and must reproduce the committed per-cell marginal_b
     BIT-EXACTLY (exact float equality, not a tolerance). This is the gate
     that matters: it proves the placebo loop below is the same object as the
     committed run, so a difference in outcome is a difference in the
     PARTITION and not in the plumbing. FICO is chosen because it is the
     3-cell grid the placebo's cardinality matches.

- COMPARISON STATISTIC (fixed ex ante). For each placebo partition record
  (intensity_min, intensity_max) and the additivity residual as a fraction of
  the committed total. Report:
    n_broad_based / N_PLACEBO
    placebo_band_width   = max over partitions of (intensity_max -
                           intensity_min), and the median width
    committed_band_width = 1.260671020258831 - 0.8792234112930807, the span
                           of the union of the three committed grids
  DISCRIMINATION verdict, pre-committed:
    "verdict_does_not_discriminate" if n_broad_based == N_PLACEBO — a
        partition with no economic content earns the same verdict, so
        "broad_based" alone carries no evidential weight;
    "verdict_discriminates" if n_broad_based == 0;
    "verdict_partially_discriminates" otherwise, with the count reported.
  DIRECTION verdict, pre-committed and independent of the above:
    "committed_disperses_more_than_chance" if committed_band_width >
        max placebo band width — the economic groupings spread WIDER than a
        random split, i.e. the real cells carry MORE heterogeneity than
        chance, and that dispersion (not the verdict label) is the
        informative quantity;
    "committed_disperses_less_than_chance" if committed_band_width < min
        placebo band width — the economic groupings are tighter than chance,
        which would be the reading the manuscript's current language implies;
    "committed_within_chance_band" otherwise.
  Both directions are pre-written; whichever the data selects is reported
  verbatim, with no share-language spin either way.

Output
------
data/subgroup_marginals_placebo_results.json: spec echo, gates block
(G1/G2/G3 raw diffs + PASS/FAIL), per-partition cell tables and verdicts, the
band comparison, and both pre-committed verdict strings.

Run:  cd hazard && python3 subgroup_marginals_placebo.py
Runtime estimate: (2 gate legs + 3 G3 legs + 12*3 placebo legs) = 41 engine
  legs at ~12.8 s/leg ~= 9 min (cf. committed 11-leg run at 140.7 s).
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
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
)
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

# Reuse the committed verdict band — imported, never restated.
from subgroup_marginals import INTENSITY_BROAD_BAND, FICO_ORDER

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "subgroup_marginals_placebo_results.json"
COMMITTED_JSON = DATA_DIR / "subgroup_marginals_results.json"

N_PLACEBO = 12
N_CELLS = 3
SEED = 20260720


def score_partition(labels: np.ndarray, n_cells: int, loans, macro, trans,
                    holdings_b, empirical, balance, total_bal, bench,
                    beta1_prod, n, label_fmt) -> dict:
    """Run one partition through the committed group-ablation engine + rule."""
    rows = []
    for g in range(n_cells):
        mask = labels == g
        vec = np.full(n, beta1_prod)
        vec[mask] = 0.0
        trapped = run_leg(loans, macro, trans, holdings_b, vec, empirical)
        marg_b = CENTRAL_TRAPPED_B - trapped
        bshare = float(balance[mask].sum() / total_bal * 100)
        rows.append({
            "cell": label_fmt(g),
            "n_loans": int(mask.sum()),
            "balance_share_pct": bshare,
            "marginal_b": marg_b,
            "marginal_pp": marg_b / bench * 100,
        })

    sum_marg = sum(r["marginal_b"] for r in rows)
    residual = TOTAL_MARGINAL_B - sum_marg
    additivity_ok = abs(residual) <= ADDITIVITY_TOL_FRAC * TOTAL_MARGINAL_B
    for r in rows:
        r["share_of_sum_pct"] = (r["marginal_b"] / sum_marg * 100) if sum_marg else 0.0
        r["intensity"] = (
            r["share_of_sum_pct"] / r["balance_share_pct"] if r["balance_share_pct"] else 0.0
        )

    lo, hi = INTENSITY_BROAD_BAND
    sign_ok = all(r["marginal_b"] > 0 for r in rows)
    band_ok = all(lo <= r["intensity"] <= hi for r in rows)
    imin = min(r["intensity"] for r in rows)
    imax = max(r["intensity"] for r in rows)
    return {
        "cells": rows,
        "sum_cells_b": sum_marg,
        "residual_b": residual,
        "residual_frac_of_total": residual / TOTAL_MARGINAL_B,
        "additivity_verdict": "shares_readable" if additivity_ok else "approximate_only",
        "sign_homogeneous": sign_ok,
        "intensity_band_ok": band_ok,
        "intensity_min": imin,
        "intensity_max": imax,
        "intensity_band_width": imax - imin,
        "verdict": "broad_based" if (sign_ok and band_ok) else "materially_heterogeneous",
    }


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

    # --- Gates G1/G2 (HARD; before any placebo number) ----------------------
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
        RESULTS_JSON.write_text(json.dumps({
            "mode": "subgroup_marginals_placebo", "status": "GATE_FAILURE",
            "g1": {"trapped_b": g1_trapped, "diff_b": g1_diff, "pass": g1_pass},
            "g2": {"trapped_b": g2_trapped, "diff_b": g2_diff, "pass": g2_pass},
        }, indent=2, default=float) + "\n")
        raise SystemExit("Parity gate G1/G2 failure — placebo legs not run.")

    bench = float(score_extension_risk(
        pd.read_parquet(DATA_DIR / "microsim_results.parquet"), empirical
    )["empirical_trapped_b"])

    # --- Gate G3: bit-exact reproduction of the committed FICO grid ---------
    committed = json.loads(COMMITTED_JSON.read_text())
    committed_fico = committed["grids"]["fico_bucket"]["cells"]
    committed_by_cell = {c["cell"]: c for c in committed_fico}

    fico_arr = np.array(loans["fico_bucket"].to_list(), dtype=object)
    fico_labels = np.full(n, -1, dtype=int)
    for i, lab in enumerate(FICO_ORDER):
        fico_labels[fico_arr == lab] = i
    assert fico_labels.min() >= 0, "FICO grid is not a clean partition of the sample"

    print("G3: re-running the committed FICO grid through this module's loop …")
    g3 = score_partition(fico_labels, len(FICO_ORDER), loans, macro, trans, holdings_b,
                         empirical, balance, total_bal, bench, beta1_prod, n,
                         lambda g: FICO_ORDER[g])
    g3_cells = []
    g3_pass = True
    for r in g3["cells"]:
        want = committed_by_cell[r["cell"]]["marginal_b"]
        got = r["marginal_b"]
        exact = (got == want)  # exact float equality, not a tolerance
        g3_pass = g3_pass and exact
        g3_cells.append({"cell": r["cell"], "got_marginal_b": got,
                         "committed_marginal_b": want, "abs_diff_b": abs(got - want),
                         "bit_exact": exact})
        print(f"  {r['cell']:>10}: got {got:.12f}  want {want:.12f}  "
              f"diff {abs(got-want):.3e}  {'EXACT' if exact else 'MISMATCH'}")

    if not g3_pass:
        RESULTS_JSON.write_text(json.dumps({
            "mode": "subgroup_marginals_placebo", "status": "GATE_FAILURE",
            "G3_committed_cell_reproduction": {"cells": g3_cells, "pass": False},
        }, indent=2, default=float) + "\n")
        raise SystemExit("Parity gate G3 failure — placebo legs not run.")

    # --- Placebo partitions -------------------------------------------------
    rng = np.random.default_rng(SEED)
    partitions = []
    while len(partitions) < N_PLACEBO:
        labels = rng.integers(0, N_CELLS, size=n)
        counts = np.bincount(labels, minlength=N_CELLS)
        if counts.min() == 0:
            print("  degenerate draw (empty cell) — redrawn")
            continue
        partitions.append(labels)

    placebo_rows = []
    for k, labels in enumerate(partitions):
        res = score_partition(labels, N_CELLS, loans, macro, trans, holdings_b,
                              empirical, balance, total_bal, bench, beta1_prod, n,
                              lambda g: f"random_{g}")
        res["partition_index"] = k
        placebo_rows.append(res)
        print(f"  placebo {k:2d}: intensity {res['intensity_min']:.4f}-{res['intensity_max']:.4f} "
              f"(width {res['intensity_band_width']:.4f})  residual "
              f"{res['residual_frac_of_total']:+.4%}  verdict {res['verdict']}")

    n_broad = sum(1 for r in placebo_rows if r["verdict"] == "broad_based")
    widths = [r["intensity_band_width"] for r in placebo_rows]
    resid_fracs = [abs(r["residual_frac_of_total"]) for r in placebo_rows]
    placebo_imin = min(r["intensity_min"] for r in placebo_rows)
    placebo_imax = max(r["intensity_max"] for r in placebo_rows)

    # Committed band = union over the three committed grids.
    c_imin = min(g["intensity_min"] for g in committed["grids"].values())
    c_imax = max(g["intensity_max"] for g in committed["grids"].values())
    c_width = c_imax - c_imin
    c_resid = [abs(g["residual_frac_of_total"])
               for g in committed["gates"]["G3_additivity_per_grid"].values()]

    if n_broad == N_PLACEBO:
        discrimination = "verdict_does_not_discriminate"
    elif n_broad == 0:
        discrimination = "verdict_discriminates"
    else:
        discrimination = "verdict_partially_discriminates"

    if c_width > max(widths):
        direction = "committed_disperses_more_than_chance"
    elif c_width < min(widths):
        direction = "committed_disperses_less_than_chance"
    else:
        direction = "committed_within_chance_band"

    payload = {
        "mode": "subgroup_marginals_placebo",
        "null_for": "subgroup_marginals.py (gate #48) / data/subgroup_marginals_results.json",
        "spec": (f"{N_PLACEBO} random {N_CELLS}-way partitions of the committed 75k sample at "
                 f"seed {SEED}, each scored through the imported committed group-ablation "
                 f"engine (marginal_decomposition.run_leg) and the imported committed verdict "
                 f"rule (sign homogeneity AND intensity in {list(INTENSITY_BROAD_BAND)})"),
        "engine": ("production US regime, fractional mode, seed RNG_SEED, committed 75k sample; "
                   "run_leg + anchors imported from marginal_decomposition.py, verdict band "
                   "imported from subgroup_marginals.py"),
        "seed": SEED,
        "n_placebo": N_PLACEBO,
        "n_cells": N_CELLS,
        "committed_anchors": {
            "central_trapped_b": CENTRAL_TRAPPED_B,
            "null_trapped_b": NULL_TRAPPED_B,
            "total_marginal_b": TOTAL_MARGINAL_B,
            "total_marginal_pp": TOTAL_MARGINAL_PP,
        },
        "gates": {
            "G1_central_parity": {"trapped_b": g1_trapped, "diff_b": g1_diff, "pass": g1_pass},
            "G2_null_parity": {"trapped_b": g2_trapped, "diff_b": g2_diff, "pass": g2_pass},
            "G3_committed_fico_cell_reproduction": {
                "rule": "exact float equality against data/subgroup_marginals_results.json",
                "cells": g3_cells, "pass": g3_pass,
            },
        },
        "benchmark_b": bench,
        "placebo_partitions": placebo_rows,
        "summary": {
            "n_broad_based": n_broad,
            "n_partitions": N_PLACEBO,
            "placebo_intensity_min": placebo_imin,
            "placebo_intensity_max": placebo_imax,
            "placebo_band_width_min": min(widths),
            "placebo_band_width_median": float(np.median(widths)),
            "placebo_band_width_max": max(widths),
            "placebo_abs_residual_frac_min": min(resid_fracs),
            "placebo_abs_residual_frac_max": max(resid_fracs),
            "committed_intensity_min": c_imin,
            "committed_intensity_max": c_imax,
            "committed_band_width": c_width,
            "committed_abs_residual_frac_min": min(c_resid),
            "committed_abs_residual_frac_max": max(c_resid),
        },
        "verdict_discrimination": discrimination,
        "verdict_direction": direction,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\n{n_broad}/{N_PLACEBO} random partitions earn 'broad_based'.")
    print(f"placebo intensity {placebo_imin:.4f}-{placebo_imax:.4f} "
          f"(max width {max(widths):.4f}) vs committed {c_imin:.4f}-{c_imax:.4f} "
          f"(width {c_width:.4f})")
    print(f"discrimination: {discrimination}")
    print(f"direction:      {direction}")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
