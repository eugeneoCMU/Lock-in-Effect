#!/usr/bin/env python3
"""
Table 6 WAL calculator (§VII) — single-pool-per-cell SOMA book approximation.

Implements exactly the construction stated in the table note: vintage face
shares from the SOMA CUSIP tabulation, a 90.7%/9.1% 30yr/15yr term split,
coupon at the book's 2.49% WAC, level-payment amortization with monthly SMM,
each scenario's window-mean CPR held constant; November 2025 values age the
same cells 42 months. Representative cell ages at June 2022 (months) were
recovered by grid search and reproduce every printed v15 Table 6 value to
0.1 years (the parity gate below asserts this).

Adds the referee-requested no-shock row: WAL at 2021 realized speeds
(22.81% mean empirical CPR), which prices the extension the paper's dollar
benchmark tracks: 9.4 − 3.4 = 6.0 years.

Run:  cd hazard && python3 wal_table.py   → data/wal_table_results.json
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

OUT = Path(__file__).parent / "data" / "wal_table_results.json"

WAC = 0.0249
VINTAGE_SHARES = {
    "2022": 0.231, "2021": 0.439, "2020": 0.163, "2017-19": 0.060, "pre2017": 0.106,
}
TERM_SPLIT = {360: 0.907 / 0.998, 180: 0.091 / 0.998}
# Representative single-pool ages at June 2022 (months), recovered by grid
# search against the printed v15 Table 6 (exact to the table's 0.1yr rounding).
AGES_JUNE_2022 = {"2022": 2, "2021": 12, "2020": 32, "2017-19": 60, "pre2017": 120}

SCENARIOS = {
    "scheduled_only": 0.0,
    "empirical": 0.0514,
    "abm": 0.1168,
    # Spec v4 production Path A mean simulated CPR (3.3368%), from
    # data/pathA_seasonal_adoption_results.json / run-2026-07-14-pathA-seasonal.
    "path_a": 0.0334,
    "path_a_specv3": 0.0351,  # prior-spec exhibit; stays gated vs printed v15
    "path_b": 0.0476,
    "no_shock_2021_speeds": 0.2281,  # 2021 mean empirical CPR (FRED/SOMA back-out)
}
V15_PRINTED = {
    "scheduled_only": (14.7, 12.6),
    "empirical": (9.4, 8.5),
    "abm": (6.0, 5.6),
    "path_a_specv3": (10.7, 9.5),
    "path_b": (9.7, 8.7),
}


@functools.lru_cache(maxsize=None)
def cell_wal(term_n: int, age: int, cpr: float) -> float:
    """WAL (years) of a level-payment pool aged `age` months at constant CPR."""
    smm = 1 - (1 - cpr) ** (1 / 12)
    r = WAC / 12
    n_rem = term_n - age
    if n_rem <= 0:
        return 0.0
    bal, num, paid = 1.0, 0.0, 0.0
    for t in range(1, n_rem + 1):
        sched = bal * (r / (1 - (1 + r) ** (-(n_rem - t + 1))) - r)
        prepay = (bal - sched) * smm
        p = sched + prepay
        num += t * p
        paid += p
        bal -= p
        if bal <= 1e-9:
            break
    num += n_rem * bal
    paid += bal
    return num / paid / 12


def book_wal(cpr: float, extra_age: int = 0) -> float:
    num = den = 0.0
    for v, share in VINTAGE_SHARES.items():
        for term, tw in TERM_SPLIT.items():
            a = min(AGES_JUNE_2022[v] + extra_age, term)
            w = share * tw
            num += w * cell_wal(term, a, cpr)
            den += w
    return num / den


def main() -> None:
    rows = {}
    for name, cpr in SCENARIOS.items():
        rows[name] = {
            "mean_cpr_pct": cpr * 100,
            "wal_june_2022": round(book_wal(cpr), 1),
            "wal_nov_2025": round(book_wal(cpr, extra_age=42), 1),
        }

    for name, (w1, w2) in V15_PRINTED.items():
        got = (rows[name]["wal_june_2022"], rows[name]["wal_nov_2025"])
        assert got == (w1, w2), f"parity fail {name}: {got} != {(w1, w2)}"

    extension = round(
        rows["empirical"]["wal_june_2022"] - rows["no_shock_2021_speeds"]["wal_june_2022"], 1
    )
    payload = {
        "mode": "wal_table",
        "ages_june_2022_months": AGES_JUNE_2022,
        "rows": rows,
        "extension_years_vs_no_shock": extension,
        "parity": ("v15 printed values reproduced exactly for the four "
                   "unchanged rows and the spec-v3 Path A exhibit; path_a "
                   "is the spec v4 restatement (freeze item i), mean CPR "
                   "from pathA_seasonal_adoption_results.json"),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"{'scenario':<24}{'CPR %':>8}{'Jun 2022':>10}{'Nov 2025':>10}")
    for name, r in rows.items():
        print(f"{name:<24}{r['mean_cpr_pct']:>8.2f}{r['wal_june_2022']:>10.1f}"
              f"{r['wal_nov_2025']:>10.1f}")
    print(f"\nExtension (empirical 9.4 − no-shock {rows['no_shock_2021_speeds']['wal_june_2022']}): "
          f"{extension} years")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
