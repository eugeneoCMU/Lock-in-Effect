#!/usr/bin/env python3
"""R32 / C-79: the Danish leg with an interest-only share.

Run tag: danish_interest_only_share.  Spec: specs/SPEC_R32_c79_danish_interest_only_share.md,
committed before this script was written, and this script committed before it ran.

An IO (deferred-amortisation) share sigma on the DANISH leg zeroes that share's scheduled
amortization, so Danish roll-off falls and Danish trapped rises by the same amount:
    gap(sigma) = gap_par - sigma * sum_t sched_t          (first order)
plus an explicitly-computed second-order balance feedback (deferring amortization leaves a higher
surviving balance, so early prepayment dollars rise and partially offset).

The PRIMARY deliverable is the BREAK-EVEN share, which needs no external input.  The verified
Danmarks Nationalbank read is reported against it, and its fetch is non-fatal.

Writes ONLY hazard/data/danish_interest_only_share_results.json.
No engine runs.  Does NOT edit any .tex file.

Usage:  python3 tools/danish_interest_only_share_run.py
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
HAZ = ROOT / "hazard"
PARQUET = HAZ / "data" / "microsim_results_us_intercept.parquet"
POINT = HAZ / "data" / "danish_us_intercept_results.json"
BRACKET = HAZ / "data" / "buyback_credit_bracket_results.json"
OUT = HAZ / "data" / "danish_interest_only_share_results.json"

PINS = {
    PARQUET: "38041df75a57ff1e86f224e7085b5465e521f0b07b861ffcc9427139aa44b28a",
    POINT: "b810a1dae636617f9417c6a343c55d67ec6c8659b7a3dfcb55e134b804e1aca7",
    BRACKET: "dba71c544f9b116848731d12983258538e697813388f7632887e1eaa84c35881",
}

GAP_PAR_B = 61.18833737010482
SCHED_B = 198.66568741255054
E_B = 470.6532528541021
MEAN_DANISH_CPR_PCT = 5.613626373336359
WINDOW_MONTHS = 42

SIGMA_STAR_FIRST_ORDER = GAP_PAR_B / SCHED_B          # 0.307996504918
E3_BAND = (SIGMA_STAR_FIRST_ORDER, 0.400)             # spec section 5: sigma** lands in here
IO_SHARE_SOURCED = 0.45                               # Danmarks Nationalbank, 2020-02-04
SOURCE_URL = ("https://www.nationalbanken.dk/en/news-and-knowledge/publications-and-speeches/"
              "archive-publications/2020/expiring-interest-only-mortgages-have-implications-"
              "for-household-expenditure")
SOURCE_SENTENCE = "currently making up 45 per cent of outstanding mortgage volumes"
SOURCE_DATE = "2020-02-04"
GRID = [0.0, 0.10, 0.20, 0.30, 0.45, 0.50]


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_source() -> dict:
    """P2: BLOCKING on correctness, non-fatal on availability. If the page cannot be read the
    run records io_share_sourced=false and STILL lands the break-even, which needs no input."""
    try:
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception as exc:
        return {"sourced": False, "reason": f"{type(exc).__name__}: {exc}", "url": SOURCE_URL}
    if SOURCE_SENTENCE not in html:
        return {"sourced": False, "url": SOURCE_URL,
                "reason": (f"the verbatim sentence {SOURCE_SENTENCE!r} was NOT found on the "
                           f"page; the transcribed 45% is therefore NOT re-verified and is not "
                           f"used as a headline")}
    return {
        "sourced": True, "url": SOURCE_URL, "publication_date": SOURCE_DATE,
        "publisher": "Danmarks Nationalbank",
        "title": ("Expiring interest-only mortgages have implications for household "
                  "expenditure"),
        "verbatim": SOURCE_SENTENCE,
        "io_share": IO_SHARE_SOURCED,
        "limits": [
            "PRE-WINDOW: 2020-02 against a 2022-06..2025-11 evaluation window",
            ("DEFERRED AMORTISATION (afdragsfrihed), conventionally capped at ten years -- the "
             "share currently IN an interest-only period, NOT a permanent product feature"),
            ("population is whole-market outstanding mortgage volumes, not the owner-occupied "
             "30-year callable segment the transplant models"),
        ],
    }


def main() -> None:
    t0 = time.time()

    for path, want in PINS.items():
        got = sha(path)
        if got != want:
            stop("P0", f"{path.relative_to(ROOT)} sha256 {got} != pinned {want}")
    pre = {str(p.relative_to(ROOT)): sha(p) for p in PINS}

    # ---- P1 / E1: the anchor is exact --------------------------------------
    pt = json.loads(POINT.read_text())["point"]
    gap_par = pt["institutional_gap_shared_b"]
    if abs(gap_par - GAP_PAR_B) > 1e-12:
        stop("P1", f"gap_par {gap_par!r} != {GAP_PAR_B!r}")

    df = pd.read_parquet(PARQUET)
    if len(df) != WINDOW_MONTHS:
        stop("P3", f"parquet carries {len(df)} rows, expected {WINDOW_MONTHS}")
    sched = df["weighted_sched_b"].to_numpy(dtype=float)
    if not (sched > 0).all():
        stop("P3", f"scheduled path not positive in every month: min {sched.min()!r}")
    sched_tot = float(sched.sum())
    if abs(sched_tot - SCHED_B) > 1e-9:
        stop("P1", f"scheduled sum {sched_tot!r} != {SCHED_B!r}")

    # cross-check on the same columns: the buyback identity must re-derive
    dk_total = float(df["Danish_simulated_rolloff_b"].abs().sum())
    E = dk_total - sched_tot
    if abs(E - E_B) > 1e-9:
        stop("P1", f"buyback identity E {E!r} != {E_B!r} -- columns read differently")

    cpr_mean = float(df["CPR_Danish"].mean())
    if abs(cpr_mean - MEAN_DANISH_CPR_PCT) > 1e-12:
        stop("P3", f"mean CPR_Danish {cpr_mean!r} != {MEAN_DANISH_CPR_PCT!r}")

    comparator = verify_source()

    # ---- the two orders ----------------------------------------------------
    smm = 1.0 - (1.0 - df["CPR_Danish"].to_numpy(dtype=float) / 100.0) ** (1.0 / 12.0)

    def second_order(sigma: float) -> float:
        """Deferred balance accumulates at sigma*sched_t and prepays at the leg's own SMM_t.
        Returns the extra early roll-off in $bn (an OFFSET to the first-order effect)."""
        deferred = 0.0
        extra = 0.0
        for t in range(WINDOW_MONTHS):
            deferred += sigma * sched[t]        # this month's un-amortized principal
            prep = deferred * smm[t]            # ... prepays at the leg's own speed
            extra += prep
            deferred -= prep
        return extra

    def gap_of(sigma: float) -> tuple[float, float, float]:
        first = sigma * sched_tot
        offset = second_order(sigma)
        return gap_par - first, gap_par - first + offset, offset

    # break-even, second order: bisect on the corrected gap
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if gap_of(mid)[1] > 0:
            lo = mid
        else:
            hi = mid
    sigma_star_2 = 0.5 * (lo + hi)

    cells = {}
    for s in sorted(set(GRID + [round(SIGMA_STAR_FIRST_ORDER, 12), round(sigma_star_2, 12)])):
        g1, g2, off = gap_of(s)
        cells[f"sigma_{s:.6f}"] = {
            "io_share": s, "gap_first_order_b": g1, "second_order_offset_b": off,
            "gap_second_order_b": g2, "reverses_first_order": bool(g1 < 0),
            "reverses_second_order": bool(g2 < 0),
        }

    # ---- E2: monotone at both orders --------------------------------------
    seq = [gap_of(s) for s in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)]
    if not all(a[0] > b[0] for a, b in zip(seq, seq[1:])):
        stop("E2", "gap not strictly decreasing in sigma at first order")
    if not all(a[1] > b[1] for a, b in zip(seq, seq[1:])):
        stop("E2", "gap not strictly decreasing in sigma at second order")
    if abs(gap_of(0.0)[0] - gap_par) > 1e-12 or abs(gap_of(0.0)[1] - gap_par) > 1e-12:
        stop("E1", "sigma = 0 does not return gap_par exactly")

    e3 = E3_BAND[0] < sigma_star_2 <= E3_BAND[1]
    g1_45, g2_45, off_45 = gap_of(IO_SHARE_SOURCED)
    e4 = bool(g2_45 < 0)

    payload = {
        "mode": "danish_interest_only_share", "run_tag": "danish_interest_only_share",
        "spec": {
            "spec_file": "specs/SPEC_R32_c79_danish_interest_only_share.md",
            "chain": "gap(sigma) = gap_par - sigma * sum_t sched_t  (first order)",
            "danish_leg_only": ("the IO share is a feature of the DANISH product mix and applies "
                                "to the Danish leg only; applying it to both legs would EXACTLY "
                                "neutralize it, the same defect C-74 identifies in the Ginnie "
                                "overlay. The U.S. leg's effective zero IO share stays a "
                                "disclosed held-fixed feature."),
            "basis_note": ("sum weighted_sched_b is the U.S. leg's scheduled path -- the "
                           "manuscript's own proxy for the scheduled component, the same "
                           "convention buyback_credit_bracket.py uses to form E."),
            "direction_is_the_manuscripts_own": (
                ".tex:627 already states the IO share moves the shortfall 'in the opposite "
                "direction from the payoff rule', so this run gets NO CREDIT for the sign. What "
                "is new is the magnitude and the crossing."),
            "accounting_layer_only": ("the hazard is untouched; only the amortization path "
                                      "moves. A full re-simulation with a genuinely IO-amortizing "
                                      "book is out of scope (single-tenant engine, no Danish "
                                      "loan panel exists in this design)."),
            "no_engine_runs": True, "window_months": WINDOW_MONTHS,
        },
        "parity": {
            "P0_sha_pins": {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
            "P0b_artifacts_byte_identical": True,
            "P1_gap_par": gap_par, "P1_sched_total_b": sched_tot,
            "P1_buyback_identity_E_b": E,
            "P3_mean_danish_cpr_pct": cpr_mean,
            "P3_sched_positive_every_month": True,
            "P4_second_order_reported_separately": True,
        },
        "source": comparator,
        "break_even": {
            "first_order": SIGMA_STAR_FIRST_ORDER,
            "second_order": sigma_star_2,
            "note": ("the first-order break-even needs NO external input and is the primary "
                     "deliverable; the second-order one corrects it upward because deferring "
                     "amortization leaves a higher surviving balance that prepays at the leg's "
                     "own speed"),
        },
        "at_sourced_share": {
            "io_share": IO_SHARE_SOURCED,
            "gap_first_order_b": g1_45, "second_order_offset_b": off_45,
            "gap_second_order_b": g2_45, "reverses": e4,
        },
        "expectations": {
            "E1_anchor_exact": True, "E2_monotone_both_orders": True,
            "E3_band": list(E3_BAND), "E3_sigma_star_second_order": sigma_star_2,
            "E3_pass": bool(e3),
            "E4_sourced_share_reverses_under_face_accounting": e4,
        },
        "cells": cells,
        "runtime_s": round(time.time() - t0, 3),
    }

    for p in PINS:
        if sha(p) != pre[str(p.relative_to(ROOT))]:
            stop("P0b", f"{p.name} changed during the run")

    blob = json.dumps(payload, indent=2) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write")
    OUT.write_text(blob)

    if comparator["sourced"]:
        print(f"source VERIFIED: Danmarks Nationalbank {SOURCE_DATE} -- "
              f"\"{SOURCE_SENTENCE}\"")
    else:
        print(f"source NOT RE-VERIFIED: {comparator['reason'][:120]}")
        print("  -> the break-even still lands; it needs no external input")
    print(f"\n{'sigma':>9}{'gap 1st $bn':>14}{'2nd-order':>12}{'gap 2nd $bn':>14}  reverses")
    for k, c in cells.items():
        print(f"{c['io_share']:>9.4f}{c['gap_first_order_b']:>14.4f}"
              f"{c['second_order_offset_b']:>12.4f}{c['gap_second_order_b']:>14.4f}  "
              f"{'YES' if c['reverses_second_order'] else 'no'}")
    print(f"\nbreak-even IO share: first order {SIGMA_STAR_FIRST_ORDER:.6f}, "
          f"second order {sigma_star_2:.6f}")
    print(f"at the sourced 45%: gap = ${g2_45:+.4f}bn (second order), "
          f"offset ${off_45:.4f}bn")
    print(f"E3 {'PASS' if e3 else 'MISS'}   E4 {'PASS' if e4 else 'MISS'}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
