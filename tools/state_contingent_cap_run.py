#!/usr/bin/env python3
"""R32 / C-81: the state-contingent cap's two-input table.

Run tag: state_contingent_cap_grid.  Spec: specs/SPEC_R32_c81_state_contingent_cap.md,
committed before this script was written, and this script committed before it ran.

SS VI.B raises indexing a redemption cap to "the share of the book sitting deeply below market
coupon" and stops.  This builds the missing function: (depth cut -> observable OTM share, and
depth cut -> committed floor read) x (floor band) -> achievable passive principal per month ->
the implied cap.

NO NEW ESTIMATION.  Every input is a committed artifact and the amortization is wal_table's
own.  The frozen calculator is imported (never edited, never executed as a program), and its
nine committed rows are re-derived THROUGH THE SAME PRIMITIVES THIS RUNNER USES and asserted
bit-identical before any new number is allowed to exist -- that parity gate is what certifies
the monthly-principal extraction is committed machinery and not a re-implementation.

Writes ONLY hazard/data/state_contingent_cap_grid_results.json.

Usage:  python3 tools/state_contingent_cap_run.py
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "hazard" / "wal_table.py"
FROZEN = ROOT / "hazard" / "data" / "wal_table_results.json"
COMPOSITION = ROOT / "hazard" / "data" / "composition_shift_results.json"
SIGNFORCE = ROOT / "hazard" / "data" / "sign_forcing_stats_results.json"
OOS = ROOT / "hazard" / "data" / "oos_identification_results.json"
OUT = ROOT / "hazard" / "data" / "state_contingent_cap_grid_results.json"

MODULE_SHA256 = "26308a9ff7de7ca86f5753ba63129758cdf2b76907d84e5a6f30a16bfce70b32"
FROZEN_SHA256 = "1aeaf45b47e6622d02dcf55470ca740902beb45292454726c9d859a9cc2bf18a"

WINDOW_MONTHS = 42
NOV_2025_EXTRA_AGE = 42

# Spec section 4: the committed depth cuts, in basis points of out-of-the-moneyness.
CUTS_BP = (0, 25, 50)
CUT_TO_FLOOR_KEY = {0: "clean_hi_pct", 25: "clean_mid_pct", 50: "clean_lo_pct"}
# Spec section 5: the mid-cut wild-cluster interval, as printed in SS VI.B.
BAND_PCT = (4.177, 5.800)
# Spec section 5, E2.
E2_RANGE_B_PER_MONTH = (14.0, 26.0)
# Spec section 5, declared-not-predicted observable.
DECLARED_OTM_SHARE_PCT = {0: 99.9082, 25: 99.5853, 50: 99.5853}


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_import_safe(src: str) -> None:
    """P0a: the calculator's module body may only bind names."""
    for node in ast.parse(src).body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign,
                             ast.AnnAssign, ast.FunctionDef)):
            continue
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue
        if isinstance(node, ast.If):
            t = node.test
            if (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name)
                    and t.left.id == "__name__" and len(t.comparators) == 1
                    and isinstance(t.comparators[0], ast.Constant)
                    and t.comparators[0].value == "__main__"):
                continue
        stop("P0a", f"{MODULE.name} line {node.lineno}: unexpected top-level "
                    f"{type(node).__name__} -- import is no longer side-effect-free")


def load_calculator():
    spec = importlib.util.spec_from_file_location("_wal_table_readonly", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cell_schedule(wal, term_n: int, age: int, cpr: float, months: int):
    """Month-by-month principal for one cell, on wal_table's OWN recursion.

    This mirrors wal_table.cell_wal line for line; P1 asserts that a WAL rebuilt
    from this schedule reproduces the frozen calculator exactly, which is what
    makes "the same machinery" a checked claim rather than an assertion.
    """
    smm = 1 - (1 - cpr) ** (1 / 12)
    r = wal.WAC / 12
    n_rem = term_n - age
    if n_rem <= 0:
        return [], 0.0
    bal, num, paid = 1.0, 0.0, 0.0
    principal = []
    for t in range(1, n_rem + 1):
        sched = bal * (r / (1 - (1 + r) ** (-(n_rem - t + 1))) - r)
        prepay = (bal - sched) * smm
        p = sched + prepay
        if t <= months:
            principal.append(p)
        num += t * p
        paid += p
        bal -= p
        if bal <= 1e-9:
            break
    num += n_rem * bal
    paid += bal
    return principal, num / paid / 12


def book_wal_via_schedule(wal, cpr: float, extra_age: int = 0) -> float:
    num = den = 0.0
    for v, share in wal.VINTAGE_SHARES.items():
        for term, tw in wal.TERM_SPLIT.items():
            a = min(wal.AGES_JUNE_2022[v] + extra_age, term)
            w = share * tw
            num += w * cell_schedule(wal, term, a, cpr, 0)[1]
            den += w
    return num / den


def achievable_b_per_month(wal, cpr: float, face_b: float) -> float:
    """Book-weighted mean monthly principal over the window, in $bn."""
    num = den = 0.0
    for v, share in wal.VINTAGE_SHARES.items():
        for term, tw in wal.TERM_SPLIT.items():
            a = min(wal.AGES_JUNE_2022[v], term)
            w = share * tw
            sched, _ = cell_schedule(wal, term, a, cpr, WINDOW_MONTHS)
            paid = sum(sched)
            num += w * (paid / WINDOW_MONTHS)
            den += w
    return num / den * face_b


def main() -> None:
    t0 = time.time()

    for path, pin in ((MODULE, MODULE_SHA256), (FROZEN, FROZEN_SHA256)):
        got = sha256(path)
        if got != pin:
            stop("P0", f"{path} sha256 {got} != pinned {pin}")
    assert_import_safe(MODULE.read_text())
    before = {p: sha256(p) for p in (COMPOSITION, SIGNFORCE, OOS, FROZEN)}

    frozen = json.loads(FROZEN.read_text())
    comp = json.loads(COMPOSITION.read_text())
    sfs = json.loads(SIGNFORCE.read_text())
    oos = json.loads(OOS.read_text())
    wal = load_calculator()

    if any(sha256(p) != h for p, h in before.items()):
        stop("P0b", "a read artifact changed across the import; land nothing")

    # --- P1: the nine committed rows, re-derived THROUGH cell_schedule ---------
    recomputed = {
        name: {
            "mean_cpr_pct": cpr * 100,
            "wal_june_2022": round(book_wal_via_schedule(wal, cpr), 1),
            "wal_nov_2025": round(
                book_wal_via_schedule(wal, cpr, extra_age=NOV_2025_EXTRA_AGE), 1),
        }
        for name, cpr in wal.SCENARIOS.items()
    }
    if recomputed != frozen["rows"]:
        diff = {k: {"got": recomputed.get(k), "frozen": frozen["rows"].get(k)}
                for k in set(recomputed) | set(frozen["rows"])
                if recomputed.get(k) != frozen["rows"].get(k)}
        stop("P1", f"schedule-derived WALs do not reproduce the frozen rows: {diff}")

    # --- P2: floor reads, live ------------------------------------------------
    fl = oos["instrument1_oow_floor"]["defensible_clean_floor"]
    if fl["primary_point_selection"] != "gap<=-0.0025_age>=12":
        stop("P2", f"floor selection moved to {fl['primary_point_selection']!r}")
    if not fl["clean_lo_pct"] < fl["clean_mid_pct"] < fl["clean_hi_pct"]:
        stop("P2", "floor band not ordered")

    # --- P3: book composition + reference rate --------------------------------
    book = comp["soma_book"]["asof_june_2022"]
    shares = {float(k): v for k, v in book["coupon_shares"].items()}
    if abs(sum(shares.values()) - 1.0) > 1e-9:
        stop("P3", f"coupon shares sum to {sum(shares.values())!r}")
    face_b = book["total_mbs_face_b"]
    mkt = sfs["statistics"]["window_min_mortgage30us_pct"]

    # --- the grid -------------------------------------------------------------
    cells = {}
    for cut in CUTS_BP:
        thr = mkt - cut / 100.0
        otm = sum(v for c, v in shares.items() if c <= thr) * 100.0
        if round(otm, 4) != DECLARED_OTM_SHARE_PCT[cut]:
            stop("P3", f"declared OTM share for {cut}bp moved: {otm} != "
                       f"{DECLARED_OTM_SHARE_PCT[cut]}")
        f = fl[CUT_TO_FLOOR_KEY[cut]]
        a = achievable_b_per_month(wal, f / 100.0, face_b)
        cells[f"cut_{cut}bp"] = {
            "depth_cut_bp": cut, "coupon_threshold_pct": thr,
            "otm_share_pct": otm, "floor_pct": f,
            "achievable_b_per_month": a, "implied_cap_b_per_month": a,
        }

    band = {f"floor_{p}pct": {
        "floor_pct": p,
        "achievable_b_per_month": achievable_b_per_month(wal, p / 100.0, face_b),
    } for p in BAND_PCT}

    # --- E1 (STOP-class): monotone in the floor -------------------------------
    a_lo = cells["cut_50bp"]["achievable_b_per_month"]
    a_mid = cells["cut_25bp"]["achievable_b_per_month"]
    a_hi = cells["cut_0bp"]["achievable_b_per_month"]
    b_lo = band[f"floor_{BAND_PCT[0]}pct"]["achievable_b_per_month"]
    b_hi = band[f"floor_{BAND_PCT[1]}pct"]["achievable_b_per_month"]
    if not (a_lo < a_mid < a_hi and b_lo < a_mid < b_hi):
        stop("E1", f"achievable principal not monotone in the floor: cuts "
                   f"({a_lo}, {a_mid}, {a_hi}), band ({b_lo}, {b_hi})")

    # --- E2 / E3: predictions, reported not enforced --------------------------
    e2 = all(E2_RANGE_B_PER_MONTH[0] <= c["achievable_b_per_month"] <= E2_RANGE_B_PER_MONTH[1]
             for c in cells.values())
    spread_cuts = a_hi - a_lo
    spread_band = b_hi - b_lo
    e3 = spread_cuts < spread_band

    payload = {
        "mode": "state_contingent_cap_grid",
        "run_tag": "state_contingent_cap_grid",
        "spec": {
            "spec_file": "specs/SPEC_R32_c81_state_contingent_cap.md",
            "question": ("the missing function from the indexing observable to a cap "
                         "level: OTM share x turnover-floor band -> achievable passive "
                         "principal -> implied cap"),
            "no_new_estimation": True,
            "depth_cuts_bp": list(CUTS_BP),
            "depth_cuts_rationale": ("the committed floor reads exist only at gap <= 0 / "
                                     "-0.0025 / -0.005; 200/300/400bp would need new reads"),
            "calculator": "hazard/wal_table.py (imported; main() never called)",
            "calculator_sha256": MODULE_SHA256,
            "book_face_b": face_b,
            "book_as_of": book["as_of"],
            "reference_market_rate_pct": mkt,
            "window_months": WINDOW_MONTHS,
            "band_pct": list(BAND_PCT),
        },
        "parity": {
            "nine_rows_bit_identical_via_schedule": True,
            "read_artifacts_untouched": True,
            "import_side_effect_free": True,
            "coupon_shares_sum_to_one": True,
        },
        "observable_declared_not_predicted": {
            "note": ("computed at scoping time, before the spec was written; recorded as a "
                     "measurement, not as a pre-committed expectation"),
            "otm_share_pct": {str(k): v for k, v in DECLARED_OTM_SHARE_PCT.items()},
            "near_degenerate": True,
            "why_25_and_50_coincide": "book coupons sit on a 0.5% grid; no bucket between the thresholds",
        },
        "expectations": {
            "E1_monotone_in_floor": True,
            "E2_range_b_per_month": list(E2_RANGE_B_PER_MONTH), "E2_pass": e2,
            "E3_claim": "spread across depth cuts < spread across the mid-cut floor band",
            "E3_spread_across_cuts_b_per_month": spread_cuts,
            "E3_spread_across_band_b_per_month": spread_band,
            "E3_pass": e3,
        },
        "cells": cells,
        "band": band,
        "scope_limit": (
            "The observable is the SOMA book's bucketed coupon distribution; the floor read "
            "is estimated on the Freddie loan-level panel's gaps. Two populations, two "
            "grains. The 0.5% coupon bucketing is why the 25 and 50 bp cuts coincide."
        ),
        "runtime_s": round(time.time() - t0, 3),
    }

    if any(sha256(p) != h for p, h in before.items()):
        stop("P0b", "a read artifact changed during the run; land nothing")

    blob = json.dumps(payload, indent=2) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write")
    OUT.write_text(blob)

    print(f"{'cut':>6}{'thr %':>9}{'OTM %':>10}{'floor %':>10}{'$bn/month':>12}")
    for k, c in cells.items():
        print(f"{c['depth_cut_bp']:>4}bp{c['coupon_threshold_pct']:>9.4f}"
              f"{c['otm_share_pct']:>10.4f}{c['floor_pct']:>10.3f}"
              f"{c['achievable_b_per_month']:>12.2f}")
    print(f"\nband  floor {BAND_PCT[0]}% -> {b_lo:.2f}   floor {BAND_PCT[1]}% -> {b_hi:.2f}")
    print(f"E2 all cells in {list(E2_RANGE_B_PER_MONTH)}: {'PASS' if e2 else 'MISS'}")
    print(f"E3 cut-spread {spread_cuts:.2f} < band-spread {spread_band:.2f}: "
          f"{'PASS' if e3 else 'MISS'}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
