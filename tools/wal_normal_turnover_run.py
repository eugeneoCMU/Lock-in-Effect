#!/usr/bin/env python3
"""Round-30 D2: SOMA portfolio WAL at the paper's off-window baseline turnover floor.

Run tag: wal_normal_turnover.  Spec: specs/SPEC_R30_wal_normal_turnover.md,
committed before this script ran.

Adds ONE scenario to the Table-6 calculator -- the paper's own off-window turnover
measurement -- so tab:wal carries a normal-turnover benchmark instead of only the
2021 refinancing-boom row.  Nothing about the calculator changes: the frozen module
is imported (never edited, never executed as a program), and its nine committed rows
are recomputed and asserted BIT-IDENTICAL to the frozen artifact before the new row
is allowed to exist.

Writes ONLY hazard/data/wal_normal_turnover_results.json.  The frozen artifact
hazard/data/wal_table_results.json is opened read-only, hashed before the import,
after the import and at exit, and is never written.

Usage:  python3 tools/wal_normal_turnover_run.py
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
OOS = ROOT / "hazard" / "data" / "oos_identification_results.json"
OUT = ROOT / "hazard" / "data" / "wal_normal_turnover_results.json"

# Pinned 2026-07-29 (spec R30-D2).  A changed calculator or a changed frozen
# artifact is a STOP, not a re-baseline: the parity gate is only meaningful
# against the exact bytes this spec was written against.
MODULE_SHA256 = "26308a9ff7de7ca86f5753ba63129758cdf2b76907d84e5a6f30a16bfce70b32"
FROZEN_SHA256 = "1aeaf45b47e6622d02dcf55470ca740902beb45292454726c9d859a9cc2bf18a"

NOV_2025_EXTRA_AGE = 42  # the aging every committed row already uses


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_import_safe(src: str) -> None:
    """P0a: the calculator's module body may only bind names.

    Importing it must not touch the filesystem.  Every top-level statement has to
    be the docstring, an import, a constant assignment, a function definition, or
    the `if __name__ == "__main__"` guard (whose body does not run on import).
    Decorators DO evaluate at import time; the sha256 pin is what keeps that safe.
    """
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
    """Import hazard/wal_table.py without registering it or running main().

    main() is the module's only writer and is never called.  The module is kept out
    of sys.modules so nothing else in this process can pick it up and run it.
    """
    spec = importlib.util.spec_from_file_location("_wal_table_readonly", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    t0 = time.time()

    # --- P0: the calculator and its frozen output are the pinned bytes --------
    mod_sha, frozen_sha = sha256(MODULE), sha256(FROZEN)
    if mod_sha != MODULE_SHA256:
        stop("P0", f"{MODULE} sha256 {mod_sha} != pinned {MODULE_SHA256}")
    if frozen_sha != FROZEN_SHA256:
        stop("P0", f"{FROZEN} sha256 {frozen_sha} != pinned {FROZEN_SHA256}")
    assert_import_safe(MODULE.read_text())

    frozen = json.loads(FROZEN.read_text())
    wal = load_calculator()

    # --- P0b: the import wrote nothing ---------------------------------------
    if sha256(FROZEN) != FROZEN_SHA256:
        stop("P0b", "the frozen artifact changed across the import -- the module "
                    "wrote on import; land nothing")

    # --- P1: the nine committed rows, recomputed bit-identically -------------
    recomputed = {
        name: {
            "mean_cpr_pct": cpr * 100,
            "wal_june_2022": round(wal.book_wal(cpr), 1),
            "wal_nov_2025": round(wal.book_wal(cpr, extra_age=NOV_2025_EXTRA_AGE), 1),
        }
        for name, cpr in wal.SCENARIOS.items()
    }
    if recomputed != frozen["rows"]:
        diff = {k: {"got": recomputed.get(k), "frozen": frozen["rows"].get(k)}
                for k in set(recomputed) | set(frozen["rows"])
                if recomputed.get(k) != frozen["rows"].get(k)}
        stop("P1", f"frozen rows not reproduced bit-identically: {diff}")

    extension = round(recomputed["empirical"]["wal_june_2022"]
                      - recomputed["no_shock_2021_speeds"]["wal_june_2022"], 1)
    rule_only = round(recomputed["path_b"]["wal_june_2022"]
                      - recomputed["danish_us_intercept"]["wal_june_2022"], 1)
    if extension != frozen["extension_years_vs_no_shock"]:
        stop("P1", f"extension {extension} != frozen "
                   f"{frozen['extension_years_vs_no_shock']}")
    if rule_only != frozen["rule_only_wal_shortening_years"]:
        stop("P1", f"rule-only shortening {rule_only} != frozen "
                   f"{frozen['rule_only_wal_shortening_years']}")

    # --- P2: the anchor, read live out of the committed floor artifact -------
    floor = (json.loads(OOS.read_text())["instrument1_oow_floor"]
             ["defensible_clean_floor"])
    lo_pct, mid_pct, hi_pct = (floor["clean_lo_pct"], floor["clean_mid_pct"],
                               floor["clean_hi_pct"])
    if floor["primary_point_selection"] != "gap<=-0.0025_age>=12":
        stop("P2", "floor primary selection moved to "
                   f"{floor['primary_point_selection']!r}")
    if not lo_pct < mid_pct < hi_pct:
        stop("P2", f"floor band not ordered: {lo_pct}/{mid_pct}/{hi_pct}")

    def row(cpr_pct: float) -> dict:
        cpr = cpr_pct / 100
        return {
            "cpr": cpr,
            "mean_cpr_pct": cpr_pct,
            "wal_june_2022": round(wal.book_wal(cpr), 1),
            "wal_nov_2025": round(wal.book_wal(cpr, extra_age=NOV_2025_EXTRA_AGE), 1),
            "raw_june_2022": wal.book_wal(cpr),
            "raw_nov_2025": wal.book_wal(cpr, extra_age=NOV_2025_EXTRA_AGE),
        }

    # Printed convention: 2-decimal percent, as all nine committed scenarios.
    rows = {
        "turnover_floor_oow_mid": row(round(mid_pct, 2)),
        "turnover_floor_oow_lo": row(round(lo_pct, 2)),
        "turnover_floor_oow_hi": row(round(hi_pct, 2)),
    }
    full_precision = {
        "turnover_floor_oow_mid": row(mid_pct),
        "turnover_floor_oow_lo": row(lo_pct),
        "turnover_floor_oow_hi": row(hi_pct),
    }
    agrees = {
        k: (rows[k]["wal_june_2022"] == full_precision[k]["wal_june_2022"]
            and rows[k]["wal_nov_2025"] == full_precision[k]["wal_nov_2025"])
        for k in rows
    }

    # --- P3: the PRINTED row must not depend on the rounding convention ------
    if not agrees["turnover_floor_oow_mid"]:
        stop("P3", "the printed row differs between the 2-decimal CPR "
                   f"({rows['turnover_floor_oow_mid']['wal_june_2022']}, "
                   f"{rows['turnover_floor_oow_mid']['wal_nov_2025']}) and the "
                   "full-precision CPR "
                   f"({full_precision['turnover_floor_oow_mid']['wal_june_2022']}, "
                   f"{full_precision['turnover_floor_oow_mid']['wal_nov_2025']}) "
                   "-- amend the spec to state the convention, then re-run")

    # --- E1: the printed row must sit inside its bracketing committed rows ---
    mid = rows["turnover_floor_oow_mid"]
    emp, pbb = frozen["rows"]["empirical"], frozen["rows"]["path_b"]
    e1_j = emp["wal_june_2022"] <= mid["wal_june_2022"] <= pbb["wal_june_2022"]
    e1_n = emp["wal_nov_2025"] <= mid["wal_nov_2025"] <= pbb["wal_nov_2025"]
    if not (e1_j and e1_n):
        stop("E1", f"printed pair ({mid['wal_june_2022']}, {mid['wal_nov_2025']}) "
                   f"falls outside the bracketing committed rows "
                   f"[{emp['wal_june_2022']}, {pbb['wal_june_2022']}] x "
                   f"[{emp['wal_nov_2025']}, {pbb['wal_nov_2025']}] -- the "
                   "calculator is not behaving monotonically between Path B and "
                   "the empirical path; land nothing")
    interior_j = emp["wal_june_2022"] < mid["wal_june_2022"] < pbb["wal_june_2022"]
    interior_n = emp["wal_nov_2025"] < mid["wal_nov_2025"] < pbb["wal_nov_2025"]

    payload = {
        "mode": "wal_normal_turnover",
        "run_tag": "wal_normal_turnover",
        "spec": {
            "spec_file": "specs/SPEC_R30_wal_normal_turnover.md",
            "question": ("the SOMA book's approximate WAL at the paper's own "
                         "off-window baseline-turnover-floor read"),
            "calculator": "hazard/wal_table.py (imported; main() never called)",
            "calculator_sha256": MODULE_SHA256,
            "frozen_companion": "hazard/data/wal_table_results.json",
            "frozen_companion_sha256": FROZEN_SHA256,
            "anchor_source": ("hazard/data/oos_identification_results.json:"
                              "instrument1_oow_floor.defensible_clean_floor"),
            "anchor_full_precision_pct": mid_pct,
            "anchor_band_full_precision_pct": {"lo": lo_pct, "mid": mid_pct,
                                               "hi": hi_pct},
            "anchor_primary_point_selection": floor["primary_point_selection"],
            "cpr_precision_convention": ("2-decimal percent, as all nine committed "
                                         "scenarios"),
            "nov_2025_extra_age_months": NOV_2025_EXTRA_AGE,
            "printed_row": "turnover_floor_oow_mid",
        },
        "parity": {
            "nine_rows_bit_identical": True,
            "extension_years_vs_no_shock": extension,
            "rule_only_wal_shortening_years": rule_only,
            "frozen_artifact_untouched": True,
            "import_side_effect_free": True,
            "printed_row_precision_insensitive": True,
        },
        "expectations": {
            "E1_bracket_rows": ["empirical", "path_b"],
            "E1_june_2022": [emp["wal_june_2022"], pbb["wal_june_2022"]],
            "E1_nov_2025": [emp["wal_nov_2025"], pbb["wal_nov_2025"]],
            "E1_pass": True,
            "E1_strict_interior_june_2022": interior_j,
            "E1_strict_interior_nov_2025": interior_n,
        },
        "rows": rows,
        "full_precision_rows": full_precision,
        "precision_agreement_2dp_vs_full": agrees,
        "runtime_s": round(time.time() - t0, 3),
    }

    if sha256(FROZEN) != FROZEN_SHA256:
        stop("P0b", "the frozen artifact changed during the run; land nothing")

    blob = json.dumps(payload, indent=2) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write; move the old "
                   "artifact aside deliberately, or amend the spec")
    OUT.write_text(blob)

    print(f"{'scenario':<26}{'CPR %':>8}{'Jun 2022':>10}{'Nov 2025':>10}{'2dp==full':>11}")
    for name, r in rows.items():
        print(f"{name:<26}{r['mean_cpr_pct']:>8.2f}{r['wal_june_2022']:>10.1f}"
              f"{r['wal_nov_2025']:>10.1f}{str(agrees[name]):>11}")
    print(f"\nE1 bracket June 2022 [{emp['wal_june_2022']}, {pbb['wal_june_2022']}], "
          f"Nov 2025 [{emp['wal_nov_2025']}, {pbb['wal_nov_2025']}] -- PASS "
          f"(strict interior: {interior_j}/{interior_n})")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
