#!/usr/bin/env python3
"""
danish_refi_finegrid.py — the production U.S.-intercept refinance-in-place
sweep on a FINE grid over 0--3% CPR (round-28 WP-F1; REVIEW2 finding #7 /
R3-W1; RULE-A' of SPEC_danish_redemption_validation makes the band
presentation MANDATORY — realized Danish deep-discount redemptions ran
26.4%/yr against the leg's ~0 pin).

PRE-COMMITTED SPEC (fixed BEFORE any run; committed before first execution;
full drafting spec at specs/SPEC_round28_D_F1_I1_I3_J2_S8.md SPEC F1, gates
and landing adopted unchanged; band variant V2 (0--3%) authorized by Eugene
2026-07-29).

DESIGN. hazard/danish_us_intercept.py's mechanics unchanged: the
us_intercept anchor (set_danish_moving_anchor), per-cell
set_us_transplant_refi(refi), run_qt_microsim (both regimes), shared-layer
scoring. SWEEP = 0.0000 to 0.0300 in 0.0025 steps (13 cells), plus ONE
extension cell at the realized-implied anchor 0.224 (22.4%/yr, the
WP-F2 artifact's extraordinary lower bound) — ARTIFACT-ONLY, never part of
the quoted band, retained to place the realized anchor against the PE
ceiling. The point run supplies the script's own G1/G2 parity gates.

PARITY GATES (BLOCKING):
  G1  US standalone leg == no_lockin_null central (script's own, < $0.01B).
  G2  US shared layer == 97.9% (< 0.25pp).
  G3  sweep cell refi=0 gap == 61.18833737010482 $B (1e-6; > 0.01 STOP-A:
      upstream data-revision alarm, land nothing).
  G4  sweep cell refi=0.03 gap == 256.8415840324639 $B (as G3, STOP-B).
  G5  gap strictly increasing over the 13 cells (1e-9).
  G6  mean Danish CPR at refi=0 == 5.613626373336359 (1e-6 pp).

PRE-COMMITTED EXPECTATIONS: slope ~ $65.2B per CPR point (from the committed
coarse grid); band 0--1% ~ [+$61.2B, ~+$126B]; band 0--3% = [+$61.2B,
+$256.8B] with the committed endpoints reproduced bit-exactly.

LANDING (V2 authorized): tab:danish row d carries the 0--3% band, not the 0%
point; the tex-464 ~0-pin sentence is replaced by the band + the realized-
data contradiction (RULE-A' disposition (iii), citing the frozen artifact
and window); fig:gapsweep's caption restates the GE best estimate as one
anchor among the swept range with the realized-implied anchor noted above
the plotted ceiling; the near-equality reading ("one object on two
accounting legs") is retired to an edge property. The realized anchor's
four confounds travel wherever it is used (gross conversions bundle in;
non-household collateral; environment- not book-matched; Danish-tax
realized vs U.S.-transplant GE object — the anchor is an UPPER anchor on
the transplant, not an estimate of it).

MUST NOT CHANGE: common/berger_calibration.py constants (incl. THETA_G_US —
the tax correction is WP-F3 wording, not a parameter change here); the
committed danish_us_intercept_results.json; abm/data/refi_sweep_results.json
(dk_level — a different anchor); fig4 PNG (regeneration would move the
dk_level curve too — deliberate, separate decision); U.S. leg committed
values; any .tex file (landing is a separate commit).

Run:  cd hazard && python3 danish_refi_finegrid.py
      -> data/danish_refi_finegrid_results.json (frozen)
1 point run + 14 sweep cells, ~27s each.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd  # noqa: F401
import polars as pl

from config import LOAN_SAMPLE_PATH  # noqa: F401

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
TMP_PARQUET = DATA_DIR / "_refi_finegrid_tmp.parquet"
RESULTS_JSON = DATA_DIR / "danish_refi_finegrid_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"

SWEEP = [round(0.0025 * i, 4) for i in range(13)]  # 0.0000 .. 0.0300
REALIZED_ANCHOR = 0.224
WANT_G3 = 61.18833737010482
WANT_G4 = 256.8415840324639
WANT_G6 = 5.613626373336359
TOL = 1e-6
STOP_B = 0.01


def main() -> None:
    print("Fetching hazard macro + empirical benchmark ...")
    macro_h = calculate_dynamic_friction(fetch_data())
    empirical = build_empirical_metrics(
        macro_h, soma_rolloff=fetch_soma_mbs_monthly())
    print("Fetching ABM macro + SOMA (shared accounting layer) ...")
    macro_abm = fed.fetch_data()
    soma_abm = fed.fetch_soma_mbs_monthly()
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    set_danish_moving_anchor("us_intercept")
    rows = []
    anchor_cell = None
    try:
        print("Point run (us_intercept anchor, both regimes) ...")
        res = run_qt_microsim(loan_sample=loans, macro=macro_h,
                              output=TMP_PARQUET)
        us, dk = res["US"], res["Danish"]
        us_score = score_extension_risk(us, empirical)
        anchor = json.load(open(NULL_ARTIFACT))
        g1 = abs(float(us_score["hazard_trapped_b"])
                 - float(anchor["central_trapped_b"])) < STOP_B
        shared = score_on_shared_layer(macro_abm, soma_abm,
                                       {"US": us, "Danish": dk})
        g2 = abs(float(shared["share_pct"]) - 97.9) < 0.25
        print(f"G1 US standalone [{'PASS' if g1 else 'FAIL'}]  "
              f"G2 US shared [{'PASS' if g2 else 'FAIL'}]")
        if not (g1 and g2):
            raise SystemExit("STOP-C: US-leg parity failed; run void.")

        for refi in SWEEP + [REALIZED_ANCHOR]:
            set_us_transplant_refi(refi)
            r = run_qt_microsim(loan_sample=loans, macro=macro_h,
                                output=TMP_PARQUET)
            sh = score_on_shared_layer(macro_abm, soma_abm,
                                       {"US": r["US"], "Danish": r["Danish"]})
            row = {"refi_inplace_cpr": refi,
                   "gap_hybrid_us_intercept_b": sh["institutional_gap_b"],
                   "danish_trapped_shared_b": sh["danish_trapped_b"],
                   "mean_danish_cpr_pct":
                       float(r["Danish"]["hazard_cpr_pct"].mean())}
            if refi == REALIZED_ANCHOR:
                anchor_cell = row
            else:
                rows.append(row)
            print(f"  refi={refi*100:5.2f}%  gap="
                  f"${sh['institutional_gap_b']:+9.1f}B  "
                  f"DK CPR {row['mean_danish_cpr_pct']:.2f}%")
    finally:
        set_us_transplant_refi(0.0)
        set_danish_moving_anchor("dk_level")
        if TMP_PARQUET.exists():
            TMP_PARQUET.unlink()

    gaps = [r["gap_hybrid_us_intercept_b"] for r in rows]
    gates = {
        "G1_us_standalone": {"pass": g1},
        "G2_us_shared": {"pass": g2},
        "G3_cell0": {"got": gaps[0], "want": WANT_G3,
                     "pass": abs(gaps[0] - WANT_G3) < TOL,
                     "stop": abs(gaps[0] - WANT_G3) > STOP_B},
        "G4_cell3pct": {"got": gaps[-1], "want": WANT_G4,
                        "pass": abs(gaps[-1] - WANT_G4) < TOL,
                        "stop": abs(gaps[-1] - WANT_G4) > STOP_B},
        "G5_monotone": {"pass": all(gaps[i] < gaps[i + 1] + 1e-9
                                    for i in range(len(gaps) - 1))},
        "G6_dk_cpr": {"got": rows[0]["mean_danish_cpr_pct"], "want": WANT_G6,
                      "pass": abs(rows[0]["mean_danish_cpr_pct"] - WANT_G6)
                              < TOL},
    }
    all_pass = all(v["pass"] for v in gates.values())
    status = "OK" if all_pass else "GATE_FAILURE"
    slope = (gaps[-1] - gaps[0]) / 3.0
    payload = {
        "mode": "danish_refi_finegrid", "status": status,
        "spec": ("us_intercept anchor, refi-in-place 0--3% in 0.25% steps "
                 "(13 cells) + one artifact-only cell at the realized-implied "
                 "anchor 22.4%/yr; band V2 authorized; committed-endpoint "
                 "parity G3/G4 bit-exact; landing per RULE-A' dispositions."),
        "anchor": "us_intercept", "grid_pct": [r * 100 for r in SWEEP],
        "parity_gates": gates, "parity_gates_all_pass": all_pass,
        "sweep": rows,
        "band_0_1_b": [gaps[0], gaps[4]],
        "band_0_3_b": [gaps[0], gaps[-1]],
        "slope_b_per_cpr_point": slope,
        "realized_implied_anchor": {
            "value_pct": 22.4,
            "source": "hazard/data/danish_external_validation/"
                      "results_refinement.json",
            "R_pct": 26.42, "allowance_pp": 4.0,
            "confounds": ["gross bond-level measure (conversions bundle in)",
                          "stock includes non-household collateral",
                          "environment-matched, not book-matched",
                          "Danish-tax realized vs U.S.-transplant GE object: "
                          "an upper anchor on the transplant, not an estimate"],
            "above_grid": True, "above_pe_ceiling": True},
        "cell_at_realized_anchor": anchor_cell,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    def _np(o):
        if hasattr(o, "item"):
            return o.item()
        raise TypeError(f"not serializable: {type(o)}")
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_np)
        f.write("\n")
    print(f"\nstatus {status}; band 0-3%: ${gaps[0]:+.1f}B .. ${gaps[-1]:+.1f}B; "
          f"slope ${slope:.1f}B/pt; realized-anchor cell "
          f"${anchor_cell['gap_hybrid_us_intercept_b']:+.1f}B")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript.")


if __name__ == "__main__":
    main()
