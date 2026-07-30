#!/usr/bin/env python3
"""R32 / C-76: the lock-in marginal expressed in transaction counts.

Run tag: marginal_transaction_counts.  Spec: specs/SPEC_R32_c76_transaction_counts.md,
committed before this script was written, and this script committed before it ran.

Converts the central-minus-null differential into a count of foregone payoffs, brackets it by
the moving share, grosses it to the whole market, and sets it against the one existing-home-sale
level this account can source.  The 2022-2024 decline comparison is NOT computed; see the spec.

Writes ONLY hazard/data/marginal_transaction_counts_results.json.

Usage:  python3 tools/marginal_transaction_counts_run.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MSB = ROOT / "hazard" / "data" / "moving_share_bracket_offwindow_results.json"
SAMPLE = ROOT / "hazard" / "data" / "loan_sample.parquet"
COMPOSITION = ROOT / "hazard" / "data" / "composition_shift_results.json"
OUT = ROOT / "hazard" / "data" / "marginal_transaction_counts_results.json"

WINDOW_MONTHS = 42
SIGMA_RANGE = (0.20, 0.22)          # SOMA share of 1-4 family debt; a bracket, not a point
E2_RANGE = (150_000, 400_000)       # spec section 5
E3_MAX_SHARE = 0.10                 # spec section 5
FRED_SERIES = "EXHOSLUSM495S"

# Pinned from the committed artifact (spec section 3).
PIN_NULL_B = 724.9180585654117
PIN_CELLS_B = {"0.25": 738.8454578512792, "0.5": 750.6251898279331, "1": 767.5264524465003}
PIN_BENCH_B = 764.7482532227002


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def fred_2025_run_rate():
    """P4: source the one level available, or record failure and carry on."""
    key = None
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("FRED_API_KEY"):
                key = line.split("=", 1)[1].strip()
    if not key:
        return {"sourced": False, "reason": "no FRED_API_KEY"}
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={FRED_SERIES}"
           f"&api_key={key}&file_type=json&observation_start=2025-01-01")
    try:
        d = json.loads(urllib.request.urlopen(url, timeout=30).read())
    except Exception as exc:  # network/API failure is recorded, never fatal
        return {"sourced": False, "reason": f"{type(exc).__name__}: {exc}"}
    obs = [o for o in d["observations"] if o["value"] != "."]
    v25 = [(o["date"], float(o["value"])) for o in obs if o["date"].startswith("2025")]
    if not v25:
        return {"sourced": False, "reason": "no 2025 observations returned"}
    return {
        "sourced": True, "series_id": FRED_SERIES,
        "n_obs_2025": len(v25),
        "first_date": v25[0][0], "last_date": v25[-1][0],
        "run_rate_2025": sum(v for _, v in v25) / len(v25),
        "note": ("annualized SAAR monthly observations averaged over 2025; this account "
                 "returns no pre-2025 history for this series, which is why the 2022-2024 "
                 "decline comparison is not computed"),
    }


def main() -> None:
    t0 = time.time()

    msb = json.loads(MSB.read_text())
    comp = json.loads(COMPOSITION.read_text())

    # --- P1: cells and null, live, against the pinned digits ------------------
    null_b = msb["null"]["trapped_b"]
    if null_b != PIN_NULL_B:
        stop("P1", f"null moved: {null_b!r} != {PIN_NULL_B!r}")
    cells_b = {k: v["trapped_b"] for k, v in msb["cells"].items()}
    if cells_b != PIN_CELLS_B:
        stop("P1", f"cells moved: {cells_b!r}")
    order = [null_b] + [cells_b[k] for k in ("0.25", "0.5", "1")]
    if not all(a < b for a, b in zip(order, order[1:])):
        stop("P1", f"bracket not ordered: {order}")

    # --- P2: the denominator, and the wrong-divisor guard ---------------------
    df = pd.read_parquet(SAMPLE, columns=["balance"])
    all_mean = float(df.balance.mean())
    surv = df[df.balance > 0]
    surv_mean = float(surv.balance.mean())
    if not surv_mean > all_mean:
        stop("P2", f"surviving mean {surv_mean} !> all-loan mean {all_mean} -- the "
                   "wrong-divisor guard is not meaningful; investigate before landing")

    # --- P3: tie to the paper's own headline ---------------------------------
    marg_s1_b = cells_b["1"] - null_b
    marg_s1_pp = marg_s1_b / PIN_BENCH_B * 100
    if round(marg_s1_pp, 1) != 5.6 or round(marg_s1_b, 1) != 42.6:
        stop("P3", f"s=1 does not reproduce the headline: {marg_s1_pp:.4f}pp / "
                   f"${marg_s1_b:.4f}bn (want +5.6pp / $42.6bn at printing precision)")

    comparator = fred_2025_run_rate()

    cells = {}
    for s in ("0.25", "0.5", "1"):
        m_b = cells_b[s] - null_b
        book_ct = m_b * 1e9 / surv_mean
        ann_book = book_ct * 12.0 / WINDOW_MONTHS
        lo = ann_book / SIGMA_RANGE[1]
        hi = ann_book / SIGMA_RANGE[0]
        cell = {
            "moving_share": float(s),
            "marginal_b": m_b,
            "marginal_pp": m_b / PIN_BENCH_B * 100,
            "book_foregone_payoffs": book_ct,
            "book_foregone_payoffs_per_year": ann_book,
            "whole_market_per_year_lo": lo,
            "whole_market_per_year_hi": hi,
        }
        if comparator["sourced"]:
            cell["share_of_2025_run_rate_lo"] = lo / comparator["run_rate_2025"]
            cell["share_of_2025_run_rate_hi"] = hi / comparator["run_rate_2025"]
        cells[f"s_{s}"] = cell

    e1 = (cells["s_0.25"]["book_foregone_payoffs"]
          < cells["s_0.5"]["book_foregone_payoffs"]
          < cells["s_1"]["book_foregone_payoffs"])
    if not e1:
        stop("E1", "counts not increasing in the moving share; bracket wired backwards")

    s1 = cells["s_1"]
    e2 = E2_RANGE[0] <= s1["whole_market_per_year_hi"] <= E2_RANGE[1] or \
         E2_RANGE[0] <= s1["whole_market_per_year_lo"] <= E2_RANGE[1]
    e3 = (comparator["sourced"]
          and s1["share_of_2025_run_rate_hi"] < E3_MAX_SHARE)

    payload = {
        "mode": "marginal_transaction_counts",
        "run_tag": "marginal_transaction_counts",
        "spec": {
            "spec_file": "specs/SPEC_R32_c76_transaction_counts.md",
            "window_months": WINDOW_MONTHS,
            "denominator": "mean balance of SURVIVING loans (balance > 0) in the frozen sample",
            "denominator_surviving_mean": surv_mean,
            "denominator_all_loan_mean_REJECTED": all_mean,
            "denominator_note": ("the all-loan mean averages in prepaid loans at zero balance "
                                 "and would roughly double the implied count; a payoff retires "
                                 "a live balance"),
            "n_surviving": int(len(surv)),
            "soma_book_face_b": comp["soma_book"]["asof_june_2022"]["total_mbs_face_b"],
            "sigma_range": list(SIGMA_RANGE),
            "sigma_note": ("SOMA share of 1-4 family mortgage debt is NOT a committed artifact "
                           "of this repo, so the gross-up is a bracket, not a point"),
            "s1_is_upper_bound": ("s=1 is the production convention: all voluntary gap response "
                                  "is treated as the moving channel, so the count is an upper "
                                  "bound on the moving component"),
        },
        "parity": {
            "cells_and_null_match_committed": True,
            "bracket_ordered": True,
            "surviving_mean_exceeds_all_loan_mean": True,
            "s1_reproduces_headline_5p6pp_42p6b": True,
        },
        "comparator": comparator,
        "not_computed": {
            "share_of_2022_2024_decline": (
                "NOT COMPUTED. fonseca2026 (NBER 35237) verifies a 40% drop in U.S. existing "
                "home sales between 2022 and 2024, but as a percentage; this account returns no "
                "pre-2025 history for EXHOSLUSM495S, so the 2022 level cannot be sourced. "
                "Deriving it would require assuming 2024 ~ 2025, an assumption this run "
                "declines to make."),
        },
        "expectations": {
            "E1_counts_increase_in_s": e1,
            "E2_range": list(E2_RANGE),
            "E2_s1_whole_market_per_year": [s1["whole_market_per_year_lo"],
                                            s1["whole_market_per_year_hi"]],
            "E2_pass": e2,
            "E3_max_share": E3_MAX_SHARE,
            "E3_s1_share_of_2025_run_rate": s1.get("share_of_2025_run_rate_hi"),
            "E3_pass": bool(e3),
        },
        "cells": cells,
        "runtime_s": round(time.time() - t0, 3),
    }

    blob = json.dumps(payload, indent=2) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write")
    OUT.write_text(blob)

    print(f"denominator: surviving mean ${surv_mean:,.2f} "
          f"(all-loan mean ${all_mean:,.2f} REJECTED), n={len(surv):,}")
    print(f"{'s':>6}{'marginal $bn':>14}{'book payoffs':>14}{'/yr book':>11}"
          f"{'/yr market':>22}")
    for k, c in cells.items():
        print(f"{c['moving_share']:>6}{c['marginal_b']:>14.4f}"
              f"{c['book_foregone_payoffs']:>14,.0f}{c['book_foregone_payoffs_per_year']:>11,.0f}"
              f"{c['whole_market_per_year_lo']:>11,.0f}-{c['whole_market_per_year_hi']:>10,.0f}")
    if comparator["sourced"]:
        print(f"\ncomparator: {FRED_SERIES} 2025 run rate "
              f"{comparator['run_rate_2025']:,.0f}/yr "
              f"({comparator['n_obs_2025']} obs, {comparator['first_date']}.."
              f"{comparator['last_date']})")
        print(f"s=1 share of that run rate: "
              f"{s1['share_of_2025_run_rate_lo']*100:.2f}%-"
              f"{s1['share_of_2025_run_rate_hi']*100:.2f}%")
    else:
        print(f"\ncomparator NOT SOURCED: {comparator['reason']}")
    print(f"E2 {'PASS' if e2 else 'MISS'}   E3 {'PASS' if e3 else 'MISS'}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
