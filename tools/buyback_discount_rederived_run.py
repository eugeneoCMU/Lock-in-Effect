#!/usr/bin/env python3
"""R32 / C-75: the Danish buyback discount D, re-derived from the leg's own prepay path.

Run tag: buyback_discount_rederived.  Spec: specs/SPEC_R32_c75_buyback_discount.md, committed
before this script was written, and this script committed before it ran.

Prices each of the 42 window months' retired face at its OWN prepayment-consistent PV -- the book
aged to that month, coupon at the 2.49% WAC, discounted at that month's market rate, amortized at
the SMM implied by that month's Danish CPR -- from the committed microsim parquet, the same file
buyback_credit_bracket.py already reads for E.  The committed D_GRID = [0.32,0.34,0.36,0.38] is
asserted, never derived; this run derives it.

Writes ONLY hazard/data/buyback_discount_rederived_results.json.
No engine runs.  Does NOT edit any .tex file and does NOT rewrite the committed bracket artifact.

Usage:  python3 tools/buyback_discount_rederived_run.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HAZ = ROOT / "hazard"
if str(HAZ) not in sys.path:
    sys.path.insert(0, str(HAZ))

PARQUET = HAZ / "data" / "microsim_results_us_intercept.parquet"
POINT = HAZ / "data" / "danish_us_intercept_results.json"
BRACKET = HAZ / "data" / "buyback_credit_bracket_results.json"
WAL_SRC = HAZ / "wal_table.py"
BRK_SRC = HAZ / "buyback_credit_bracket.py"
OUT = HAZ / "data" / "buyback_discount_rederived_results.json"

# --- P0: sha256 pins (spec section 3) ---------------------------------------
PINS = {
    WAL_SRC: "26308a9ff7de7ca86f5753ba63129758cdf2b76907d84e5a6f30a16bfce70b32",
    BRK_SRC: "0cb900263d9d6a4f093e6aae1408b5cc55a52fee40771d008bf95a7127d2e7dc",
    PARQUET: "38041df75a57ff1e86f224e7085b5465e521f0b07b861ffcc9427139aa44b28a",
    POINT: "b810a1dae636617f9417c6a343c55d67ec6c8659b7a3dfcb55e134b804e1aca7",
    BRACKET: "dba71c544f9b116848731d12983258538e697813388f7632887e1eaa84c35881",
}

# Committed header constants of buyback_credit_bracket.py (spec section 3).
GAP_PAR_B = 61.18833737010482
US_SHARED_B = 748.9678825340305
DK_SHARED_B = 687.7795451639257
DK_TOTAL_ROLLOFF_B = 669.3189402666527
SCHED_B = 198.66568741255054
E_B = 470.6532528541021
D_GRID = [0.32, 0.34, 0.36, 0.38]
MEAN_DANISH_CPR_PCT = 5.613626373336359
D_CRIT = GAP_PAR_B / E_B          # 0.130007254808 -- verdict flips at or below this
WINDOW_MONTHS = 42

# Pre-committed expectation bands (spec section 5).
E3_GRID_FLOOR = 0.32              # every month must price BELOW the committed grid's floor
E4_BAND = (0.13, 0.32)            # face-weighted Dbar
P4_BAND = (0.32, 0.38)            # provenance anchor: zero-CPR 3.0% @ 6.8% inside committed span
P4_STATE = {"coupon": 0.03, "market": 0.068, "cpr": 0.0, "term": 360, "age": 0}


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cell_schedule(term_n: int, age: int, cpr: float, coupon: float):
    """The level-payment recursion of wal_table.cell_wal:72-89, mirrored EXACTLY, with the
    per-month principal and interest retained instead of collapsed to a WAL.

    Returns (principals, interests, n_rem, terminal_bal), 1-indexed by position.
    """
    smm = 1 - (1 - cpr) ** (1 / 12)
    r = coupon / 12
    n_rem = term_n - age
    if n_rem <= 0:
        return [], [], 0, 0.0
    bal = 1.0
    principals, interests = [], []
    for t in range(1, n_rem + 1):
        interests.append(bal * r)
        sched = bal * (r / (1 - (1 + r) ** (-(n_rem - t + 1))) - r)
        prepay = (bal - sched) * smm
        p = sched + prepay
        principals.append(p)
        bal -= p
        if bal <= 1e-9:
            break
    return principals, interests, n_rem, bal


def wal_from_schedule(principals, n_rem, terminal_bal) -> float:
    """cell_wal's own aggregation, from the retained vector. P1 asserts this == cell_wal."""
    num = sum((t + 1) * p for t, p in enumerate(principals)) + n_rem * terminal_bal
    paid = sum(principals) + terminal_bal
    if paid <= 0:
        return 0.0
    return num / paid / 12


def pv_from_schedule(principals, interests, n_rem, terminal_bal, y: float) -> float:
    """PV per unit of current balance at annual nominal rate y, monthly compounding."""
    d = 1.0 + y / 12.0
    pv = 0.0
    for t, (p, i) in enumerate(zip(principals, interests), start=1):
        pv += (p + i) / d ** t
    if terminal_bal > 0:
        pv += terminal_bal / d ** n_rem
    return pv


def main() -> None:
    t0 = time.time()

    # ---- P0: sha pins ------------------------------------------------------
    for path, want in PINS.items():
        got = sha(path)
        if got != want:
            stop("P0", f"{path.relative_to(ROOT)} sha256 {got} != pinned {want}")
    pre_hashes = {str(p.relative_to(ROOT)): sha(p) for p in (PARQUET, POINT, BRACKET)}

    # ---- P0a: AST import-safety on wal_table.py ----------------------------
    tree = ast.parse(WAL_SRC.read_text())
    binding = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
               ast.ClassDef, ast.Assign, ast.AnnAssign)
    for node in tree.body:
        if isinstance(node, binding):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue                                   # module docstring
        if isinstance(node, ast.If):
            test = ast.unparse(node.test)
            if test != "__name__ == '__main__'":
                stop("P0a", f"wal_table.py top-level If is not the main guard: {test}")
            continue
        stop("P0a", f"wal_table.py binds more than names at top level: {ast.dump(node)[:120]}")

    import wal_table as wt                                          # noqa: E402
    if wt.WAC != 0.0249:
        stop("P0a", f"wal_table.WAC moved: {wt.WAC}")

    # ---- P0b: byte-identical after import ----------------------------------
    for p in (PARQUET, POINT, BRACKET):
        if sha(p) != pre_hashes[str(p.relative_to(ROOT))]:
            stop("P0b", f"{p.name} changed on import")

    # ---- P1: machinery identity -------------------------------------------
    p1_cells, p1_max = [], 0.0
    for v, share in wt.VINTAGE_SHARES.items():
        for term, tw in wt.TERM_SPLIT.items():
            for cpr in (0.0, 0.0476, 0.0561, 0.1168, 0.2281):
                for extra in (0, 41):
                    age = min(wt.AGES_JUNE_2022[v] + extra, term)
                    pr, it, nr, tb = cell_schedule(term, age, cpr, wt.WAC)
                    got = wal_from_schedule(pr, nr, tb)
                    want = wt.cell_wal(term, age, cpr)
                    p1_max = max(p1_max, abs(got - want))
                    if abs(got - want) > 1e-12:
                        stop("P1", f"schedule WAL != cell_wal at ({term},{age},{cpr}): "
                                   f"{got!r} vs {want!r}")
    p1_cells = "all (vintage x term x 5 CPR x 2 ages)"

    v15 = {}
    for name, (w1, w2) in wt.V15_PRINTED.items():
        cpr = wt.SCENARIOS[name]
        got = (round(wt.book_wal(cpr), 1), round(wt.book_wal(cpr, extra_age=42), 1))
        v15[name] = {"got": list(got), "want": [w1, w2], "pass": got == (w1, w2)}
        if got != (w1, w2):
            stop("P1", f"V15_PRINTED parity fail {name}: {got} != {(w1, w2)}")

    # ---- P2: the committed constants, live ---------------------------------
    pt = json.loads(POINT.read_text())["point"]
    checks = {
        "gap_par": (pt["institutional_gap_shared_b"], GAP_PAR_B),
        "us_shared": (pt["us_trapped_shared_b"], US_SHARED_B),
        "dk_shared": (pt["danish_trapped_shared_b"], DK_SHARED_B),
        "mean_danish_cpr_pct": (pt["mean_danish_cpr_pct"], MEAN_DANISH_CPR_PCT),
    }
    for k, (got, want) in checks.items():
        if abs(got - want) > 1e-9:
            stop("P2", f"{k}: {got!r} != {want!r}")
    if abs((pt["us_trapped_shared_b"] - pt["danish_trapped_shared_b"]) - GAP_PAR_B) > 1e-9:
        stop("P2", "US - DK does not reproduce gap_par")

    df = pd.read_parquet(PARQUET)
    if len(df) != WINDOW_MONTHS:
        stop("P5", f"parquet carries {len(df)} rows, expected {WINDOW_MONTHS}")
    dk_total = float(df["Danish_simulated_rolloff_b"].abs().sum())
    sched_tot = float(df["weighted_sched_b"].sum())
    if abs(dk_total - DK_TOTAL_ROLLOFF_B) > 1e-9 or abs(sched_tot - SCHED_B) > 1e-9:
        stop("P2", f"parquet sums moved: dk {dk_total!r}, sched {sched_tot!r}")
    E = dk_total - sched_tot
    if abs(E - E_B) > 1e-9:
        stop("P2", f"E {E!r} != {E_B!r}")

    # monthly early face; E1 (STOP): positive everywhere and telescoping to E
    F = (df["Danish_simulated_rolloff_b"].abs() - df["weighted_sched_b"]).to_numpy(dtype=float)
    if not (F > 0).all():
        stop("E1", f"early face not positive in every month: min {F.min()!r}")
    if abs(F.sum() - E) > 1e-9:
        stop("E1", f"sum F_t {F.sum()!r} != E {E!r}")

    # ---- P5: CPR / rate path pins -----------------------------------------
    cpr_mean = float(df["CPR_Danish"].mean())
    if abs(cpr_mean - MEAN_DANISH_CPR_PCT) > 1e-12:
        stop("P5", f"mean CPR_Danish {cpr_mean!r} != {MEAN_DANISH_CPR_PCT!r}")

    # ---- P3: the committed chain reproduces bit-identically ----------------
    brk = json.loads(BRACKET.read_text())["verdict"]
    chain = {}
    for row in brk["cash_rows"]:
        d = row["D"]
        got = GAP_PAR_B - d * E
        chain[f"D_{d}"] = {"got": got, "committed": row["gap_cash_b"],
                           "exact": got == row["gap_cash_b"]}
        if got != row["gap_cash_b"]:
            stop("P3", f"chain not bit-identical at D={d}: {got!r} != {row['gap_cash_b']!r}")
    if [chain[f"D_{D_GRID[-1]}"]["got"], chain[f"D_{D_GRID[0]}"]["got"]] != \
            brk["gap_cash_range_b"]:
        stop("P3", "committed gap_cash_range_b not recovered")

    # ---- P4: provenance anchor (band check vs the COMMITTED grid span) -----
    s = P4_STATE
    pr, it, nr, tb = cell_schedule(s["term"], s["age"], s["cpr"], s["coupon"])
    p4_price = pv_from_schedule(pr, it, nr, tb, s["market"])
    p4_disc = 1.0 - p4_price
    if not (P4_BAND[0] <= p4_disc <= P4_BAND[1]):
        stop("P4", f"zero-CPR 3.0%@6.8% discount {p4_disc:.6f} outside the committed grid "
                   f"span {P4_BAND} -- the PV primitive does not reproduce the committed "
                   f"grid's provenance")

    # ---- E2 (STOP): PV monotonicity ---------------------------------------
    def disc(term, age, cpr, y):
        a, b, n, t_ = cell_schedule(term, age, cpr, wt.WAC)
        return 1.0 - pv_from_schedule(a, b, n, t_, y)

    ys = [0.05, 0.055, 0.06, 0.065, 0.07, 0.075]
    dy = [disc(360, 12, 0.0561, y) for y in ys]
    if not all(a < b for a, b in zip(dy, dy[1:])):
        stop("E2", f"discount not increasing in the market rate: {dy}")
    cs = [0.0, 0.02, 0.04, 0.0561, 0.08, 0.12]
    dc = [disc(360, 12, c, 0.066) for c in cs]
    if not all(a > b for a, b in zip(dc, dc[1:])):
        stop("E2", f"discount not decreasing in CPR: {dc}")

    # ---- the derivation ---------------------------------------------------
    months = []
    H = 0.0
    for i, (idx, row) in enumerate(df.iterrows()):
        cpr = float(row["CPR_Danish"]) / 100.0
        y = float(row["market_rate_pct"]) / 100.0
        num = den = 0.0
        for v, share in wt.VINTAGE_SHARES.items():
            for term, tw in wt.TERM_SPLIT.items():
                age = min(wt.AGES_JUNE_2022[v] + i, term)
                w = share * tw
                a, b, n, t_ = cell_schedule(term, age, cpr, wt.WAC)
                num += w * pv_from_schedule(a, b, n, t_, y)
                den += w
        price = num / den
        d_t = 1.0 - price
        H += d_t * float(F[i])
        months.append({
            "period": str(idx)[:10],
            "market_rate_pct": float(row["market_rate_pct"]),
            "cpr_danish_pct": float(row["CPR_Danish"]),
            "book_price": price,
            "discount_D": d_t,
            "early_face_b": float(F[i]),
            "haircut_b": d_t * float(F[i]),
            "below_committed_grid_floor": bool(d_t < E3_GRID_FLOOR),
        })

    dbar = H / E
    gap_cash = GAP_PAR_B - H
    gap_cash_chain = GAP_PAR_B - dbar * E
    if abs(gap_cash - gap_cash_chain) > 1e-9:
        stop("P3", f"haircut and chain disagree: {gap_cash!r} vs {gap_cash_chain!r}")

    d_all = [m["discount_D"] for m in months]
    e3 = all(d < E3_GRID_FLOOR for d in d_all)
    e4 = E4_BAND[0] <= dbar < E4_BAND[1]
    e5 = gap_cash < 0 and abs(gap_cash) < abs(brk["gap_cash_range_b"][1])
    verdict = "REVERSES" if gap_cash < 0 else ("SPANS_ZERO" if dbar > 0 else "NO_REVERSAL")

    payload = {
        "mode": "buyback_discount_rederived", "run_tag": "buyback_discount_rederived",
        "spec": {
            "spec_file": "specs/SPEC_R32_c75_buyback_discount.md",
            "method": ("each month's retired face priced at its own prepayment-consistent PV: "
                       "the book aged to that month on wal_table's single-pool tabulation, "
                       "coupon at the 2.49% WAC, level-payment with SMM from that month's "
                       "CPR_Danish, discounted at that month's market_rate_pct"),
            "basis_note": ("E nets the Danish leg's total roll-off against the U.S. leg's "
                           "scheduled path -- the manuscript's own netting convention, which "
                           "buyback_credit_bracket.py computes the same way. Reproduced here, "
                           "not repaired, so the re-derived D is the only thing that changes."),
            "grain_note": ("D_t is priced on the SOMA book's single-pool vintage tabulation "
                           "while F_t comes from the microsimulated Freddie panel's roll-off; "
                           "two populations, the seam inherited from the committed E."),
            "scheduled_carries_no_discount": True,
            "no_engine_runs": True,
            "window_months": WINDOW_MONTHS,
        },
        "parity": {
            "P0_sha_pins": {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
            "P0a_wal_table_import_safe": True,
            "P0b_artifacts_byte_identical_after_import": True,
            "P1_schedule_wal_equals_cell_wal": {"cells": p1_cells, "max_abs_diff": p1_max},
            "P1_v15_printed": v15,
            "P2_committed_constants": {k: {"got": g, "want": w} for k, (g, w) in checks.items()},
            "P2_E_b": E,
            "P3_chain_bit_identical": chain,
            "P4_provenance_anchor": {"state": P4_STATE, "price": p4_price,
                                     "discount": p4_disc, "committed_grid_span": list(P4_BAND)},
            "P5_mean_danish_cpr_pct": cpr_mean,
            "P5_market_rate_pct": {"min": float(df["market_rate_pct"].min()),
                                   "max": float(df["market_rate_pct"].max()),
                                   "mean": float(df["market_rate_pct"].mean())},
        },
        "committed_bracket": {
            "D_GRID": D_GRID,
            "gap_cash_range_b": brk["gap_cash_range_b"],
            "code": brk["code"],
            "provenance": ("asserted, never derived: buyback_credit_bracket.py:107 hard-codes "
                           "the grid and calls it 'the manuscript's committed proxy range'"),
        },
        "rederived": {
            "gap_face_b": GAP_PAR_B,
            "gap_face_note": "identity, not a computation; this run cannot and does not move it",
            "early_face_E_b": E,
            "haircut_b": H,
            "face_weighted_mean_discount": dbar,
            "gap_cash_b": gap_cash,
            "verdict_code": verdict,
            "D_crit": D_CRIT,
            "D_crit_note": ("gap_par / E; the verdict is REVERSES only above it. Stated in the "
                            "spec before the run so E4 is falsifiable rather than retrofitted."),
            "monthly_D_min": min(d_all), "monthly_D_max": max(d_all),
            "months_at_or_above_committed_floor": sum(1 for d in d_all if d >= E3_GRID_FLOOR),
        },
        "expectations": {
            "E1_monthly_face_positive_and_telescopes": True,
            "E2_pv_monotone": True,
            "E3_every_month_below_committed_grid_floor": e3,
            "E4_band": list(E4_BAND), "E4_dbar": dbar, "E4_pass": bool(e4),
            "E5_reverses_and_smaller": bool(e5),
        },
        "months": months,
        "runtime_s": round(time.time() - t0, 3),
    }

    # ---- P0b at exit ------------------------------------------------------
    for p in (PARQUET, POINT, BRACKET):
        if sha(p) != pre_hashes[str(p.relative_to(ROOT))]:
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

    print(f"P1 max |schedule WAL - cell_wal| = {p1_max:.2e}   V15 parity: all PASS")
    print(f"P4 provenance anchor: zero-CPR 3.0% @ 6.8% -> D = {p4_disc:.6f} "
          f"(committed span {P4_BAND[0]}-{P4_BAND[1]})")
    print(f"\n{'period':>12}{'mkt %':>8}{'CPR %':>8}{'D':>9}{'face $bn':>11}{'cut $bn':>10}")
    for m in months[::6] + [months[-1]]:
        print(f"{m['period']:>12}{m['market_rate_pct']:>8.3f}{m['cpr_danish_pct']:>8.3f}"
              f"{m['discount_D']:>9.4f}{m['early_face_b']:>11.3f}{m['haircut_b']:>10.3f}")
    print(f"\nD range over the 42 months: {min(d_all):.4f} .. {max(d_all):.4f} "
          f"({payload['rederived']['months_at_or_above_committed_floor']} at/above 0.32)")
    print(f"face-weighted Dbar = {dbar:.6f}   (committed grid 0.32-0.38, D_crit {D_CRIT:.6f})")
    print(f"haircut = ${H:.4f}bn   gap_cash = ${gap_cash:+.4f}bn   verdict {verdict}")
    print(f"committed range was {brk['gap_cash_range_b'][0]:+.3f} .. "
          f"{brk['gap_cash_range_b'][1]:+.3f}")
    print(f"E3 {'PASS' if e3 else 'MISS'}   E4 {'PASS' if e4 else 'MISS'}   "
          f"E5 {'PASS' if e5 else 'MISS'}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
