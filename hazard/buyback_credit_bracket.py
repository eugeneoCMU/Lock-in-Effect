#!/usr/bin/env python3
"""
buyback_credit_bracket.py — pricing the Danish counterfactual's un-priced
market-value buyback credit as an incidence bracket (round-26 panel item B3;
R3-W2 Critical / DA-M5, editorial arbitration D1).

PRE-COMMITTED SPEC (fixed in this header BEFORE any execution; committed
before first run, artifact committed separately after).

Referee objection (round-26 panel, verified with corrected scope): the
conclusion asserts a Danish market-value repurchase rule "would have
relieved (2) and modestly improved (3), by the ~$61 billion", while the
manuscript itself records that the Danish leg credits every retired balance
at par, that the un-priced market-value credit exceeds the gap, and that
"its magnitude is not established" without par accounting. The manuscript
declined to restate the gap because the pipeline cannot distinguish a cash
haircut from a balance adjustment. This script prices BOTH incidences as a
bracket, using only committed artifacts and the manuscript's own proxy
discount range — the same arithmetic the manuscript already performs to
size the channel, carried one exact step further.

DESIGN (fixed ex ante). NO engine runs. All inputs are committed artifacts:
  - danish_us_intercept_results.json: the production rule-only pair,
    shared basis. gap_par = institutional_gap_shared_b = 61.18833737010482
    ($B; US 748.9678825340305 - DK 687.7795451639257).
  - microsim_results_us_intercept.parquet (committed): the pair's monthly
    paths. Danish total roll-off = sum |Danish_simulated_rolloff_b| =
    669.3189402666527; scheduled component (the manuscript's own proxy:
    the US leg's scheduled path, the convention behind its "netting the
    roughly $199 billion scheduled component") = sum weighted_sched_b =
    198.66568741255054. Early (buyback-priced) face
    E = 669.3189402666527 - 198.66568741255054 = 470.6532528541021.
  - Proxy discount grid D in {0.32, 0.34, 0.36, 0.38}: the manuscript's
    committed range (32-34% at the representative 3.0%-coupon/6.8%-market
    state; 36-38% at the book's 2.49% weighted-average coupon).

THE TWO INCIDENCES (the distinction the manuscript names and leaves
unresolved; this bracket resolves it into two labeled readings):
  FACE incidence (balance adjustment): trapped liquidity counts face
    retirement against the caps; a market-value buyback retires the same
    face for less cash, so the committed gap is unchanged:
        gap_face = gap_par = +$61.19B.  (Identity, not a computation.)
  CASH incidence (cash haircut): the object is cash returned against the
    caps; buyback-priced retirement returns price x face, so receipts fall
    by H(D) = D x E and, because trapped liquidity is a NET monthly sum
    against the redemption targets (the target cancels from differences;
    Section VII's floor-stability decomposition states the exactness), the
    gap falls by exactly H(D):
        gap_cash(D) = gap_par - D x E.
  Scheduled amortization is contractual cash at par under both rules and
  carries no discount; all early retirement (voluntary and involuntary) is
  buyback-priced under the rule-only transplant, whose semantics change
  only the payoff rule. The U.S. leg is par-payoff and is untouched.
  Scope: the in-sample production pair (the only committed pair with a
  monthly decomposition); the off-window +$28.2B cell is out of scope and
  the manuscript must scope any restatement accordingly.

PARITY / CONSISTENCY GATES (BLOCKING):
  P1  artifact gap equals the header constant to 1e-9, and equals
      US_shared - DK_shared to 1e-9.
  P2  parquet sums reproduce the header constants to 1e-9 (Danish total,
      scheduled), and the US-leg internal identity holds:
      sum weighted_settled_b + sum weighted_sched_b = sum
      |simulated_rolloff_b| to 1e-6 $B.
  P3  E reproduces the manuscript's "on the order of $470 billion" channel:
      469 <= E <= 472 (order-of-magnitude anchor; the manuscript's $470B
      is this quantity rounded).

EX-ANTE INTERPRETIVE RULE (verbatim; no discretion after the run):
  Report gap_face and gap_cash(D) on the committed grid.
  If gap_cash(D) < 0 at EVERY grid point: the bracket's manuscript action
  is to restate the counterfactual's cash-flow claim as
  INCIDENCE-CONDITIONAL wherever it is stated as signed relief — the gap
  stands at +$61.2B under face accounting and REVERSES, to the reported
  range, under cash accounting at the manuscript's own proxy discounts —
  and the conclusion's leg-(3) sentence must replace the signed
  "modestly improved (3)" reading with the bracket, i.e. leg (3)'s
  direction is incidence-dependent and not established by this design.
  If gap_cash(D) straddles zero across the grid: state the bracket as
  spanning zero, same restatement obligation.
  Either way the "trade-off is modest" magnitude reading survives (both
  incidences are small beside the $764.7B benchmark); what changes is the
  sign claim.

Run:  cd hazard && python3 buyback_credit_bracket.py
      -> data/buyback_credit_bracket_results.json  (frozen)
No engine runs; runtime under a second. Does NOT edit any .tex file.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "buyback_credit_bracket_results.json"
POINT_ARTIFACT = DATA_DIR / "danish_us_intercept_results.json"
PARQUET = DATA_DIR / "microsim_results_us_intercept.parquet"

GAP_PAR_B = 61.18833737010482
US_SHARED_B = 748.9678825340305
DK_SHARED_B = 687.7795451639257
DK_TOTAL_ROLLOFF_B = 669.3189402666527
SCHED_B = 198.66568741255054
D_GRID = [0.32, 0.34, 0.36, 0.38]


def main() -> None:
    t0 = time.perf_counter()
    art = json.load(open(POINT_ARTIFACT))
    pt = art["point"]
    df = pd.read_parquet(PARQUET)
    us = df[df["regime"] == "US"]

    dk_total = float(df["Danish_simulated_rolloff_b"].abs().sum())
    sched = float(us["weighted_sched_b"].sum())
    settled = float(us["weighted_settled_b"].sum())
    us_total = float(us["simulated_rolloff_b"].abs().sum())

    gates = {
        "P1_gap": {
            "got": pt["institutional_gap_shared_b"], "want": GAP_PAR_B,
            "identity": pt["us_trapped_shared_b"] - pt["danish_trapped_shared_b"],
            "pass": (abs(pt["institutional_gap_shared_b"] - GAP_PAR_B) < 1e-9
                     and abs(pt["us_trapped_shared_b"] - US_SHARED_B) < 1e-9
                     and abs(pt["danish_trapped_shared_b"] - DK_SHARED_B) < 1e-9
                     and abs((pt["us_trapped_shared_b"]
                              - pt["danish_trapped_shared_b"]) - GAP_PAR_B) < 1e-9)},
        "P2_parquet_sums": {
            "dk_total": dk_total, "want_dk_total": DK_TOTAL_ROLLOFF_B,
            "sched": sched, "want_sched": SCHED_B,
            "us_identity_gap_b": abs(settled + sched - us_total),
            "pass": (abs(dk_total - DK_TOTAL_ROLLOFF_B) < 1e-9
                     and abs(sched - SCHED_B) < 1e-9
                     and abs(settled + sched - us_total) < 1e-6)},
    }
    E = dk_total - sched
    gates["P3_channel_magnitude"] = {"E_b": E, "pass": 469.0 <= E <= 472.0}
    all_pass = all(g["pass"] for g in gates.values())
    for k, g in gates.items():
        print(f"  {k}: [{'PASS' if g['pass'] else 'FAIL'}]")
    if not all_pass:
        json.dump({"mode": "buyback_credit_bracket", "status": "GATE_FAILURE",
                   "gates": gates}, open(RESULTS_JSON, "w"), indent=2)
        raise SystemExit("GATE FAILURE — STOP.")

    rows = [{"D": d, "haircut_b": d * E, "gap_cash_b": GAP_PAR_B - d * E}
            for d in D_GRID]
    all_negative = all(r["gap_cash_b"] < 0 for r in rows)
    verdict = {
        "gap_face_b": GAP_PAR_B,
        "early_face_E_b": E,
        "cash_rows": rows,
        "gap_cash_range_b": [rows[-1]["gap_cash_b"], rows[0]["gap_cash_b"]],
        "all_grid_points_negative": all_negative,
        "code": "REVERSES" if all_negative else "SPANS_ZERO",
        "manuscript_action": (
            "Restate the counterfactual's cash-flow claim as incidence-"
            "conditional wherever stated as signed relief; the conclusion's "
            "leg-(3) sentence replaces the signed 'modestly improved (3)' "
            "reading with the bracket. The magnitude reading (trade-off is "
            "modest) survives; the sign claim becomes incidence-dependent."),
    }
    payload = {
        "mode": "buyback_credit_bracket", "status": "OK",
        "spec": ("incidence bracket on the production rule-only pair, "
                 "committed artifacts only: gap_face = gap_par (balance "
                 "adjustment); gap_cash(D) = gap_par - D*E, E = Danish "
                 "roll-off minus scheduled (the manuscript's own netting "
                 "convention), D in {0.32,0.34,0.36,0.38} (the manuscript's "
                 "committed proxy range); ex-ante rule in header."),
        "gates": gates, "gates_all_pass": True, "verdict": verdict,
        "runtime_s": round(time.perf_counter() - t0, 3),
    }
    json.dump(payload, open(RESULTS_JSON, "w"), indent=2)
    open(RESULTS_JSON, "a").write("\n")
    print(json.dumps(verdict, indent=2))
    print(f"\nfrozen -> {RESULTS_JSON}")


if __name__ == "__main__":
    main()
