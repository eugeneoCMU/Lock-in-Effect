#!/usr/bin/env python3
"""R32 / C-94: SOMA portfolio WAL for the empirical path at the NOTE-RATE WAC basis.

Run tag: wal_note_rate_basis.  Spec: specs/SPEC_R32_c94_wal_note_rate_basis.md,
committed before this script was written, and this script committed before it ran.

tab:estimators already discloses three bases for the empirical SOMA CPR (5.14% ABM-basis
back-out, 5.52% hazard-basis, 5.79% at the note-rate WAC) while tab:wal's empirical row uses
5.14% alone, so the corrected amortization basis never becomes the comparator.  This adds ONE
scenario at the note-rate basis, read live out of the committed coupon-convention artifact.

Nothing about the calculator changes: the frozen module is imported (never edited, never
executed as a program), and its nine committed rows are recomputed and asserted BIT-IDENTICAL
to the frozen artifact before the new row is allowed to exist.

Writes ONLY hazard/data/wal_note_rate_basis_results.json.  Both read artifacts are opened
read-only, hashed before the import, after the import and at exit, and are never written.

Usage:  python3 tools/wal_note_rate_basis_run.py
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
BASIS = ROOT / "hazard" / "data" / "coupon_convention_amortization_results.json"
OUT = ROOT / "hazard" / "data" / "wal_note_rate_basis_results.json"

# Pinned 2026-07-30 (spec R32 C-94).  A changed calculator or a changed artifact is a
# STOP, not a re-baseline: the parity gate is only meaningful against the exact bytes
# this spec was written against.
MODULE_SHA256 = "26308a9ff7de7ca86f5753ba63129758cdf2b76907d84e5a6f30a16bfce70b32"
FROZEN_SHA256 = "1aeaf45b47e6622d02dcf55470ca740902beb45292454726c9d859a9cc2bf18a"
BASIS_SHA256 = "700489452b691f8ad0235ccb6a3af2c52089fca19fe267faf36ece0184926174"

# The two CPRs this run reads, at the precision the artifact carries them.  These are
# ASSERTIONS against the live read, not the source of the value.
NOTE_RATE_CPR_PCT = 5.785664704297843   # hazard_legs.delta_080  (0.80pp wedge, primary)
HAZARD_BASIS_CPR_PCT = 5.518089009047279  # hazard_legs.committed_0250

NOV_2025_EXTRA_AGE = 42  # the aging every committed row already uses

# Spec section 3, fixed before the run.
E1_JUNE = (8.8, 9.2)
E1_NOV = (7.9, 8.3)
E2_BASIS_EFFECT = (0.2, 0.6)


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_import_safe(src: str) -> None:
    """P0a: the calculator's module body may only bind names.

    Importing it must not touch the filesystem.  Every top-level statement has to be the
    docstring, an import, a constant assignment, a function definition, or the
    `if __name__ == "__main__"` guard (whose body does not run on import).  Decorators DO
    evaluate at import time; the sha256 pin is what keeps that safe.
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
    """Import hazard/wal_table.py without registering it or running main()."""
    spec = importlib.util.spec_from_file_location("_wal_table_readonly", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    t0 = time.time()

    # --- P0: the calculator and both artifacts are the pinned bytes ----------
    for path, pin in ((MODULE, MODULE_SHA256), (FROZEN, FROZEN_SHA256),
                      (BASIS, BASIS_SHA256)):
        got = sha256(path)
        if got != pin:
            stop("P0", f"{path} sha256 {got} != pinned {pin}")
    assert_import_safe(MODULE.read_text())

    frozen = json.loads(FROZEN.read_text())
    basis = json.loads(BASIS.read_text())
    wal = load_calculator()

    # --- P0b: the import wrote nothing ---------------------------------------
    if sha256(FROZEN) != FROZEN_SHA256 or sha256(BASIS) != BASIS_SHA256:
        stop("P0b", "a read artifact changed across the import -- the module wrote on "
                    "import; land nothing")

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

    # --- P2: the basis, read LIVE out of the committed artifact --------------
    legs = basis["hazard_legs"]
    note_pct = legs["delta_080"]["mean_cpr_pct"]
    haz_pct = legs["committed_0250"]["mean_cpr_pct"]
    if note_pct != NOTE_RATE_CPR_PCT:
        stop("P2", f"note-rate leg moved: {note_pct!r} != {NOTE_RATE_CPR_PCT!r}")
    if haz_pct != HAZARD_BASIS_CPR_PCT:
        stop("P2", f"hazard-basis leg moved: {haz_pct!r} != {HAZARD_BASIS_CPR_PCT!r}")
    if not note_pct > haz_pct:
        stop("P2", f"the g-fee+servicing wedge has the wrong sign: note-rate "
                   f"{note_pct} !> hazard-basis {haz_pct}")
    if legs["delta_080"]["coupon"] <= legs["committed_0250"]["coupon"]:
        stop("P2", "the note-rate leg's coupon does not exceed the pass-through leg's")

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
        "empirical_note_rate_basis": row(round(note_pct, 2)),
        "empirical_hazard_basis": row(round(haz_pct, 2)),
    }
    full_precision = {
        "empirical_note_rate_basis": row(note_pct),
        "empirical_hazard_basis": row(haz_pct),
    }
    agrees = {
        k: (rows[k]["wal_june_2022"] == full_precision[k]["wal_june_2022"]
            and rows[k]["wal_nov_2025"] == full_precision[k]["wal_nov_2025"])
        for k in rows
    }

    # --- P3: the PRINTED row must not depend on the rounding convention ------
    if not agrees["empirical_note_rate_basis"]:
        stop("P3", "the printed row differs between the 2-decimal CPR "
                   f"({rows['empirical_note_rate_basis']['wal_june_2022']}, "
                   f"{rows['empirical_note_rate_basis']['wal_nov_2025']}) and the "
                   "full-precision CPR "
                   f"({full_precision['empirical_note_rate_basis']['wal_june_2022']}, "
                   f"{full_precision['empirical_note_rate_basis']['wal_nov_2025']}) "
                   "-- amend the spec to state the convention, then re-run")

    # --- E3 (STOP-class): a higher constant CPR cannot lengthen WAL ----------
    nr, emp = rows["empirical_note_rate_basis"], frozen["rows"]["empirical"]
    if not (nr["wal_june_2022"] < emp["wal_june_2022"]
            and nr["wal_nov_2025"] < emp["wal_nov_2025"]):
        stop("E3", f"note-rate row ({nr['wal_june_2022']}, {nr['wal_nov_2025']}) is not "
                   f"strictly shorter than the 5.14% empirical row "
                   f"({emp['wal_june_2022']}, {emp['wal_nov_2025']}) -- the calculator is "
                   "not monotone in CPR; land nothing")

    # --- E1/E2: PREDICTIONS.  A miss is reported, it does not block landing --
    e1_j = E1_JUNE[0] <= nr["wal_june_2022"] <= E1_JUNE[1]
    e1_n = E1_NOV[0] <= nr["wal_nov_2025"] <= E1_NOV[1]
    basis_effect_june = round(emp["wal_june_2022"] - nr["wal_june_2022"], 1)
    basis_effect_nov = round(emp["wal_nov_2025"] - nr["wal_nov_2025"], 1)
    e2 = E2_BASIS_EFFECT[0] <= basis_effect_june <= E2_BASIS_EFFECT[1]
    # the stake C-94 asserts: same order as the reported 0.6-year Danish rule-only effect
    same_order_as_rule_only = basis_effect_june >= 0.5 * rule_only

    payload = {
        "mode": "wal_note_rate_basis",
        "run_tag": "wal_note_rate_basis",
        "spec": {
            "spec_file": "specs/SPEC_R32_c94_wal_note_rate_basis.md",
            "question": ("the SOMA book's approximate WAL for the empirical path at the "
                         "note-rate WAC, the corrected amortization basis"),
            "calculator": "hazard/wal_table.py (imported; main() never called)",
            "calculator_sha256": MODULE_SHA256,
            "frozen_companion": "hazard/data/wal_table_results.json",
            "frozen_companion_sha256": FROZEN_SHA256,
            "basis_source": ("hazard/data/coupon_convention_amortization_results.json:"
                             "hazard_legs"),
            "basis_source_sha256": BASIS_SHA256,
            "note_rate_leg": "delta_080 (0.80pp g-fee+servicing wedge, that run's primary)",
            "note_rate_cpr_full_precision_pct": note_pct,
            "hazard_basis_cpr_full_precision_pct": haz_pct,
            "cpr_precision_convention": ("2-decimal percent, as all nine committed "
                                         "scenarios"),
            "nov_2025_extra_age_months": NOV_2025_EXTRA_AGE,
            "printed_row": "empirical_note_rate_basis",
        },
        "parity": {
            "nine_rows_bit_identical": True,
            "extension_years_vs_no_shock": extension,
            "rule_only_wal_shortening_years": rule_only,
            "read_artifacts_untouched": True,
            "import_side_effect_free": True,
            "printed_row_precision_insensitive": True,
        },
        "expectations": {
            "E1_june_band": list(E1_JUNE), "E1_june_value": nr["wal_june_2022"],
            "E1_june_pass": e1_j,
            "E1_nov_band": list(E1_NOV), "E1_nov_value": nr["wal_nov_2025"],
            "E1_nov_pass": e1_n,
            "E2_band": list(E2_BASIS_EFFECT),
            "E2_basis_effect_june_2022_years": basis_effect_june,
            "E2_basis_effect_nov_2025_years": basis_effect_nov,
            "E2_pass": e2,
            "E2_same_order_as_rule_only_0p6": same_order_as_rule_only,
            "E3_strictly_shorter_than_5p14_row": True,
        },
        "comparators": {
            "empirical_abm_basis_committed": emp,
            "note_rate_minus_abm_basis_cpr_pp": round(note_pct - 5.14, 6),
        },
        "limitation": (
            "The 6.0-year extension is NOT recomputed on this basis. The no-shock row's "
            "22.81% is a 2021 FRED/SOMA back-out on the ABM basis and has no committed "
            "note-rate counterpart, so differencing a note-rate WAL against it would mix "
            "conventions inside one statistic -- the defect C-94 exists to remove. What "
            "this row licenses is the like-for-like basis sensitivity of the empirical "
            "row itself."
        ),
        "rows": rows,
        "full_precision_rows": full_precision,
        "precision_agreement_2dp_vs_full": agrees,
        "runtime_s": round(time.time() - t0, 3),
    }

    if sha256(FROZEN) != FROZEN_SHA256 or sha256(BASIS) != BASIS_SHA256:
        stop("P0b", "a read artifact changed during the run; land nothing")

    blob = json.dumps(payload, indent=2) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write; move the old artifact "
                   "aside deliberately, or amend the spec")
    OUT.write_text(blob)

    print(f"{'scenario':<28}{'CPR %':>8}{'Jun 2022':>10}{'Nov 2025':>10}{'2dp==full':>11}")
    for name, r in rows.items():
        print(f"{name:<28}{r['mean_cpr_pct']:>8.2f}{r['wal_june_2022']:>10.1f}"
              f"{r['wal_nov_2025']:>10.1f}{str(agrees[name]):>11}")
    print(f"\ncommitted empirical (5.14% ABM basis): "
          f"{emp['wal_june_2022']} / {emp['wal_nov_2025']}")
    print(f"E1 June {nr['wal_june_2022']} in {list(E1_JUNE)}: "
          f"{'PASS' if e1_j else 'MISS'};  "
          f"Nov {nr['wal_nov_2025']} in {list(E1_NOV)}: {'PASS' if e1_n else 'MISS'}")
    print(f"E2 basis effect June {basis_effect_june}yr in {list(E2_BASIS_EFFECT)}: "
          f"{'PASS' if e2 else 'MISS'}  (Nov {basis_effect_nov}yr; "
          f"same order as the {rule_only}yr rule-only effect: {same_order_as_rule_only})")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
