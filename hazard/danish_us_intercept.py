#!/usr/bin/env python3
"""
Danish counterfactual, U.S.-intercept transplant (rule-only anchor) —
pre-committed; spec fixed in this header before any run executed.

Referee objection to the production (dk_level) Danish legs: they import
Denmark's descriptive moving LEVEL (3.2%/yr unconditional), producing Danish
mean CPRs (3.39-3.40%, Table 1) below the paper's own 4% involuntary-turnover
floor. U.S. life-event turnover (death, divorce, forced relocation) cannot
fall because the payoff rule changed, so the level-import conflates the rule
with the country: it assumes U.S. households adopt Danish baseline mobility
along with the Danish payoff rule. The identified Berger et al. fact is the
SLOPE (moving is flat in the coupon gap under market-value payoff), not the
level.

This run keeps the flatness fact and anchors the level at the U.S. zero-gap
intercept: the production Path B hazard evaluated at zero rate gap (PSA
baseline, burnout, FICO/LTV, involuntary floor all retained; only the
rate-gap suppression switched off), plus the same U.S.-transplant
refi-in-place channel (Berger GE best estimate ~0, swept as before). By
construction this respects the floor and makes the Danish leg responsive to
the floor sweep, which the dk_level import was not.

SPEC (fixed ex ante):
- Anchor: us_intercept (common.berger_calibration.set_danish_moving_anchor).
- Production convention otherwise: committed 75k loan sample, RNG_SEED 42,
  ("US", "Danish") regime tuple with per-regime seed offsets, shared macro
  frame, central elasticity p_q 6.5 on the U.S. leg.
- Parity gates: the U.S. leg is untouched by the anchor and must reproduce
  the committed central artifacts exactly (standalone $818.530B / 107.033%,
  +/- $0.01B); the shared-layer U.S. leg must reproduce the published 97.9%
  (+/- 0.25pp, the shared_layer_scoring gate).
- Reported: standalone and shared-layer Danish trapped, institutional gap
  (US - DK, shared layer, the Table 1 convention), Danish mean CPR; and the
  refi-in-place sweep {0 .. 18%} of the shared-layer gap under this anchor
  (the fig:gapsweep input). Directional expectation, stated ex ante: the
  zero-gap intercept exceeds the locked-in U.S. hazard wherever the gap
  suppression binds, so Danish CPR >= U.S. CPR month-by-month, the gap is
  positive at refi 0, and additional refi only raises Danish prepayment, so
  the gap should be positive at every sweep point with no sign crossing.

Run:  cd hazard && python3 danish_us_intercept.py
      -> data/danish_us_intercept_results.json
         (+ microsim parquet data/microsim_results_us_intercept.parquet)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import LOAN_SAMPLE_PATH  # noqa: F401 — also puts repo root on sys.path

from common.berger_calibration import (
    set_danish_moving_anchor,
    set_us_transplant_refi,
)
from extension_risk import score_extension_risk
from macro import (
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
)
from microsim_engine import run_qt_microsim
from shared_layer_scoring import score_on_shared_layer

import fed_mbs_extension_risk as fed

DATA_DIR = Path(__file__).parent / "data"
OUT_PARQUET = DATA_DIR / "microsim_results_us_intercept.parquet"
TMP_PARQUET = DATA_DIR / "_us_intercept_sweep_tmp.parquet"
RESULTS_JSON = DATA_DIR / "danish_us_intercept_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"

PE_CEILING = 0.18
SWEEP = [round(x, 3) for x in np.linspace(0.0, PE_CEILING, 7)]
PUBLISHED_US_SHARED_PCT = 97.9


def main() -> None:
    print("Fetching hazard macro + empirical benchmark …")
    macro_h = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(
        macro_h, soma_rolloff=fetch_soma_mbs_monthly()
    )
    print("Fetching ABM macro + SOMA (shared accounting layer) …")
    macro_abm = fed.fetch_data()
    soma_abm = fed.fetch_soma_mbs_monthly()

    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    set_danish_moving_anchor("us_intercept")
    try:
        print("Running microsim under the us_intercept anchor (both regimes) …")
        results = run_qt_microsim(
            loan_sample=loans, macro=macro_h, output=OUT_PARQUET,
        )
        us, dk = results["US"], results["Danish"]

        # --- Parity gates -------------------------------------------------
        us_score = score_extension_risk(us, empirical)
        with open(NULL_ARTIFACT) as f:
            anchor = json.load(f)
        us_got = float(us_score["hazard_trapped_b"])
        us_want = float(anchor["central_trapped_b"])
        us_ok = abs(us_got - us_want) < 0.01
        print(f"parity gate US standalone: got {us_got:.4f} want "
              f"{us_want:.4f} [{'PASS' if us_ok else 'FAIL'}]")

        shared = score_on_shared_layer(
            macro_abm, soma_abm, {"US": us, "Danish": dk},
        )
        sh_got = float(shared["share_pct"])
        sh_ok = abs(sh_got - PUBLISHED_US_SHARED_PCT) < 0.25
        print(f"parity gate US shared layer: got {sh_got:.2f}% want "
              f"{PUBLISHED_US_SHARED_PCT}% [{'PASS' if sh_ok else 'FAIL'}]")

        dk_score = score_extension_risk(dk, empirical)
        point = {
            "us_trapped_shared_b": shared["us_trapped_b"],
            "us_share_shared_pct": shared["share_pct"],
            "danish_trapped_shared_b": shared["danish_trapped_b"],
            "institutional_gap_shared_b": shared["institutional_gap_b"],
            "danish_trapped_standalone_b": float(dk_score["hazard_trapped_b"]),
            "mean_us_cpr_pct": float(us["hazard_cpr_pct"].mean()),
            "mean_danish_cpr_pct": float(dk["hazard_cpr_pct"].mean()),
        }
        print(f"US leg (shared):     ${point['us_trapped_shared_b']:.1f}B "
              f"({point['us_share_shared_pct']:.1f}%)")
        print(f"Danish leg (shared): ${point['danish_trapped_shared_b']:.1f}B")
        print(f"Institutional gap:   ${point['institutional_gap_shared_b']:+.1f}B")
        print(f"Mean CPR US/DK:      {point['mean_us_cpr_pct']:.2f}% / "
              f"{point['mean_danish_cpr_pct']:.2f}%")

        # --- Refi-in-place sweep under this anchor -------------------------
        rows = []
        for refi in SWEEP:
            set_us_transplant_refi(refi)
            res_r = run_qt_microsim(
                loan_sample=loans, macro=macro_h, output=TMP_PARQUET,
            )
            shared_r = score_on_shared_layer(
                macro_abm, soma_abm,
                {"US": res_r["US"], "Danish": res_r["Danish"]},
            )
            rows.append({
                "refi_inplace_cpr": refi,
                "gap_hybrid_us_intercept_b": shared_r["institutional_gap_b"],
                "danish_trapped_shared_b": shared_r["danish_trapped_b"],
                "mean_danish_cpr_pct": float(
                    res_r["Danish"]["hazard_cpr_pct"].mean()
                ),
            })
            print(f"  refi={refi * 100:5.1f}%  gap="
                  f"${shared_r['institutional_gap_b']:+8.1f}B  "
                  f"DK CPR {rows[-1]['mean_danish_cpr_pct']:.2f}%")
    finally:
        set_us_transplant_refi(0.0)
        set_danish_moving_anchor("dk_level")
        if TMP_PARQUET.exists():
            TMP_PARQUET.unlink()
    runtime_s = time.perf_counter() - t0

    gaps = [r["gap_hybrid_us_intercept_b"] for r in rows]
    sign_robust = all(g > 0 for g in gaps) or all(g < 0 for g in gaps)

    payload = {
        "mode": "danish_us_intercept",
        "spec": (
            "us_intercept anchor: Danish moving = production U.S. hazard at "
            "zero rate gap (floor, burnout, FICO/LTV retained) + "
            "U.S.-transplant refi channel; production convention otherwise "
            "(75k sample, seed 42, US+Danish tuple, shared macro frame); "
            "shared-accounting-layer gap, Table 1 convention (US - DK); "
            "parity gates on the untouched U.S. leg; refi sweep 0-18%"
        ),
        "point": point,
        "sweep": rows,
        "sweep_sign_robust": bool(sign_robust),
        "parity_gates": {
            "us_standalone_b": {"got": us_got, "want": us_want,
                                "pass": bool(us_ok)},
            "us_shared_pct": {"got": sh_got,
                              "want": PUBLISHED_US_SHARED_PCT,
                              "pass": bool(sh_ok)},
        },
        "parity_gates_all_pass": bool(us_ok and sh_ok),
        "runtime_s": round(runtime_s, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(
            payload, f, indent=2,
            default=lambda x: float(x)
            if isinstance(x, (np.floating, np.integer)) else x,
        )
        f.write("\n")

    print(f"\nsweep sign-robust: {sign_robust}")
    if not (us_ok and sh_ok):
        raise SystemExit(
            "PARITY GATE FAILURE — results written for diagnosis "
            "but must not be cited"
        )
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
