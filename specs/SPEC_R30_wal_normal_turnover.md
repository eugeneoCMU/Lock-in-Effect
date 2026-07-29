# SPEC R30-D2 — the normal-turnover WAL row (`wal_normal_turnover`)

Pre-committed BEFORE the run (2026-07-29). Protocol: B5 / TECHNICAL §43 — spec and
landing rule committed first, parity gates that abort rather than warn, expectations
fixed ex ante, amendments labeled in this header.

**Amendment log:** none. (Any post-run change to §1–§4 is appended here as
`R30-D2-A<n>`, dated, with the reason, before the re-run.)

The round-28 `tab:wal` tablenote states the hole this closes: *"No row is printed at
a normal-turnover speed."* The table's only non-model benchmark is the 2021 realized
speed — 22.81% CPR, overwhelmingly refinancing, and refinancing is exactly what the
QT window's rate configuration shut off. Every duration statement in the paper is
therefore read against a refinancing-boom baseline. The paper already owns a
normal-turnover measurement; this run prices it in the table's own units. The run
adds one row and changes no committed number.

---

## 1. ANCHOR (pre-committed)

**Anchor: 4.991% annual CPR** — full precision from
`hazard/data/oos_identification_results.json`, key path
`instrument1_oow_floor.defensible_clean_floor.clean_mid_pct` (float `4.991`;
sibling `_floor_values.clean_mid` = `0.049909999999999996`).

**Why this read and no other.** It is the paper's only committed measurement of
turnover uncontaminated by the refinancing wave:

- It is the **2018 rising-rate leg** (`leg` = `"2018_rising_rate"`, `age_cut` =
  `">=12"`), chosen because 2018 is the only out-of-window period in which the rate
  configuration resembles the QT window's — borrowers out of the money, refinancing
  suppressed.
- It is the leg's `primary_point_selection` (`"gap<=-0.0025_age>=12"`) — the paper's
  **headline floor**, quoted at `4.991\%` 15× and at `4.99\%` 3× in the manuscript.
- The candidates it displaces are refi-contaminated and were **disqualified post hoc
  on two diagnostics** (seasoning, rate regime), a disqualification the paper already
  records in `tab:verdicts`: pooled 2017–2019 at **6.065%**
  (`contaminated_upper_anchors.pooled`, printed `6.07\%`) and 2019 at **6.91%**
  (`contaminated_upper_anchors.2019`). Using either would import into the WAL table
  the same contamination the 22.81% row already carries, only smaller.
- The ABM's 11.68%, the empirical 5.14%, and both Danish legs are model- or
  window-conditional; none is a turnover measurement.

**The band and its role.** The defensible clean floor is a **band, not a point**:
`reads_pct` = {`gap<=-0.0050_age>=12`: **4.695**, `gap<=-0.0025_age>=12`: **4.991**,
`gap<=+0.0000_age>=12`: **5.334**} — one read per depth of out-of-the-moneyness;
`clean_lo_pct`/`clean_mid_pct`/`clean_hi_pct` = 4.695/4.991/5.334. The band's role in
the landing is **framing, not printing**: exactly one row is printed, at the middle
(headline) read; the band ends are computed and committed to the artifact, and the
tablenote states that monotonicity in CPR puts them on either side of the printed
row **without printing their WALs** (see §4, OPTIONAL-B, and the precision hazard in
§2.P3). The row label names the anchor as the *off-window headline read* so the row
cannot be misread as a point estimate of turnover.

**What the row does NOT claim.** It is not a forecast, not an estimator's implied
path, and not a counterfactual portfolio. It answers one question: what the same
calculator returns when fed the paper's own turnover measurement instead of a
refinancing-boom speed. The 2018 leg's mature-seasoning probe is **not computable**
(the artifact's own `note`: no `age>=24` OTM cohort-months exist in 2018), so the
read is clean by construction rather than by test — the manuscript already says this
and the landing adds no new claim about it.

**Rounding derivation for the printed literal.** `clean_mid_pct` 4.991 → **4.99%** at
the table's 2-decimal convention → CPR **0.0499** fed to the calculator. This is the
convention every one of the nine committed scenarios already uses (`wal_table.py`
docstring: *"CPRs are the committed window means at printed precision"*; e.g.
`path_b` = `0.0476` from 4.763…, `danish_us_intercept` = `0.0561` from
5.613626373336359). Fixed here ex ante; §2.P3 blocks the landing if the printed row
is sensitive to it.

---

## 2. GUARDED RUNNER

The coordinator saves the text below **verbatim** as `tools/wal_normal_turnover_run.py`
and runs `python3 tools/wal_normal_turnover_run.py` (no arguments; safe to invoke
with no flags — it has no flags, and re-running is a no-op when the artifact already
matches).

**Import strategy (the load-bearing safety property).** `hazard/wal_table.py` is
**imported, never executed as a program**. Verified against the file at
sha256 `26308a9ff7de7ca86f5753ba63129758cdf2b76907d84e5a6f30a16bfce70b32`:

- Its module body is 16 top-level statements — 1 docstring, 4 stdlib imports
  (`__future__`, `functools`, `json`, `pathlib.Path`), 7 constant assignments, 3
  function definitions, and `if __name__ == "__main__": main()` at line 147. No I/O,
  no RNG, no clock, no environment read at import time. (AST-verified; the runner
  re-verifies this itself at every run, so a future edit that adds import-time work
  aborts instead of running.)
- `main()` — the module's **only** writer, the only thing that touches
  `hazard/data/wal_table_results.json` — is never called.
- The module is loaded by absolute path via `importlib.util.spec_from_file_location`
  under a private name and is **not registered in `sys.modules`**, so nothing else in
  the process can pick it up and run it.
- Caveat handled by the sha256 pin: decorators *do* evaluate at import
  (`@functools.lru_cache(maxsize=None)` on `cell_wal`). The pin is what makes that
  acceptable; a changed module is a STOP, not a re-baseline.
- The frozen artifact is hashed **before the import, immediately after the import,
  and at exit**; any change aborts before anything is written (P0b). This is the
  belt-and-braces guard against the failure mode this repo has already seen once — a
  "read-only" probe that executed a run.

### Parity gates (BLOCKING — every one aborts the process and writes nothing)

| Gate | Assertion | On failure |
|---|---|---|
| **P0** | `hazard/wal_table.py` sha256 == `26308a9f…70b32`; `hazard/data/wal_table_results.json` sha256 == `1aeaf45b…f18a`; module body is side-effect-free by AST | STOP — the calculator or its frozen output moved; the spec is stale, amend before re-run |
| **P0b** | frozen artifact sha256 unchanged across the import, and again at exit | STOP — the module wrote on import; land nothing, alarm |
| **P1** | all **nine** committed scenarios recomputed and **exactly equal** (`==` on the dicts, float-identical `mean_cpr_pct` included) to `frozen["rows"]`; plus `extension_years_vs_no_shock` == 6.0 and `rule_only_wal_shortening_years` == 0.6 recomputed from those rows | STOP — the calculator no longer reproduces its own committed table; no new row may be derived from it |
| **P2** | the floor artifact still selects `gap<=-0.0025_age>=12` as `primary_point_selection`, and `clean_lo_pct < clean_mid_pct < clean_hi_pct` | STOP — the anchor moved |
| **P3** | the **printed** row is precision-insensitive: the 2-decimal CPR (0.0499) and the full-precision CPR (4.991/100) give the **same** rounded pair at both June 2022 and November 2025 | STOP — the printed row depends on the rounding convention; amend §1 to print the convention explicitly, then re-run |
| **E1** | see §3 | STOP |

P1 subsumes and strengthens the module's own `V15_PRINTED` parity (5 rows) by
checking all nine plus both derived statistics.

Precision agreement for the **band ends** is measured and recorded but is **not**
blocking — the band ends are not printed by default (§4, OPTIONAL-B).

### Script text

```python
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
```

### Artifact

`hazard/data/wal_normal_turnover_results.json` (new path; **zero** references
anywhere in the repo today, so it is invisible to every current gate and test until
§4.L5 adds one). Frozen on write: a re-run that reproduces it is a no-op, a re-run
that would change it aborts.

---

## 3. PRE-COMMITTED EXPECTATIONS

**E1 (BLOCKING).** The calculator is monotone decreasing in CPR, and the anchor
4.991% lies strictly between two committed rows — Path B at 4.76% → **9.7 / 8.7**
and the empirical path at 5.14% → **9.4 / 8.5** (both from
`hazard/data/wal_table_results.json`, `rows.path_b` and `rows.empirical`). The
printed pair must therefore satisfy

> **E1: W1 ∈ [9.4, 9.7] and W2 ∈ [8.5, 8.7]** — years, at the table's 0.1-year
> rounding.

The runner reads both endpoints **live** out of the frozen artifact rather than
hardcoding them, so E1 cannot drift away from the rows it brackets. A result outside
E1 is a **STOP**: it would mean the calculator is not monotone between these two
speeds, which falsifies the monotonicity claim the current tablenote already makes
and makes the whole table suspect. It is not a landing.

**E1′ (recorded, NOT blocking).** Linear interpolation between the two bracketing
rows at 4.991% — fraction (4.991 − 4.76)/(5.14 − 4.76) = 0.6079 — gives
9.7 − 0.6079 × 0.3 = **9.52** and 8.7 − 0.6079 × 0.2 = **8.58**, i.e. an expected
printed pair near **9.5 / 8.6**. WAL is convex in CPR, so the chord lies above the
function and the interpolated values are upper bounds: the admissible pairs under
E1 + convexity are W1 ∈ {9.4, 9.5}, W2 ∈ {8.5, 8.6}. §4's ledger is pre-counted for
all four of those combinations. A pair inside E1 but outside E1′ (W1 = 9.6 or 9.7,
W2 = 8.7) still lands, but the coordinator records the deviation in the TECHNICAL
entry — 0.1-year rounding noise at this spacing is expected, a 0.2-year deviation
from the chord is worth stating.

**Interiority (wording-conditional, not blocking).** If the printed pair ties a
bracketing row (W1 = 9.4 or 9.7, or W2 = 8.5 or 8.7), the "falls between" wording in
§4.L3 is false as written and the tie variant must be used instead. The runner
reports `E1_strict_interior_june_2022` / `_nov_2025` for exactly this decision.

**Disclosure.** The recon pass (R3) that preceded this spec reimplemented the
calculator in a scratchpad and reproduced all nine frozen rows bit-identically, so
P1 is expected to pass; it also reported a preliminary pair for the new row. That
preliminary is **not** a committed value and is deliberately not written into this
spec: the landing values are whatever `hazard/data/wal_normal_turnover_results.json`
contains after the run, and E1/E1′ above were derived only from the two committed
bracketing rows.

---

## 4. LANDING RULE (pre-committed)

Applies **only** if P0/P0b/P1/P2/P3 and E1 all pass. Both manuscript files carry the
`tab:wal` block byte-identically (verified: the 1800-byte block from `\label{tab:wal}`
is identical in the canonical and the long-abstract variant), so **every tex edit
below is applied to both**:

- `paper/v18/revised_paper_v18.tex`
- `paper/v18/revised_paper_v18_long_abstract.tex`

Write `⟨W1⟩` = `rows.turnover_floor_oow_mid.wal_june_2022` and `⟨W2⟩` =
`rows.turnover_floor_oow_mid.wal_nov_2025`, each formatted `:.1f`.

### L1 — the new `tab:wal` row

Insert **immediately after** the Danish-level row and **before** the No-shock row.
Placement is load-bearing: two sites call the no-shock row *the table's final row* —
the tablenote at line 576 (*"the final row is a refinancing-boom baseline"*) and the
WAL appendix at line 1336 (*"Relative to the no-shock world of the table's final
row"*) — and both stay true only if the new row is not last.

OLD (anchor, count **1** in each file):

```
Danish-level bracketing leg (3.39\%) & 10.8 & 9.6 \\
```

NEW:

```
Danish-level bracketing leg (3.39\%) & 10.8 & 9.6 \\
Baseline turnover floor, off-window headline read (4.99\%) & ⟨W1⟩ & ⟨W2⟩ \\
```

The label uses the round-29 rename (*baseline turnover floor*) and names the read so
the row cannot be taken for a point estimate of turnover. `4.99\%` is `clean_mid_pct`
4.991 at the table's 2-decimal convention (§1).

### L2 — the falsified tablenote sentence

OLD (count **1** in each file — this is the sentence the run falsifies):

```
No row is printed at a normal-turnover speed.
```

NEW:

```
The turnover-floor row is the normal-turnover counterpart.
```

### L3 — the falsified tablenote prediction

The note's closing sentence predicted the row rather than printing it; the prediction
is now redundant with the table itself.

OLD (count **1** in each file):

```
The printed rows nearest that band are Path B's 4.76\% and the empirical 5.14\%, and this calculator is monotone in CPR, so a row anchored at the band's mid read would fall between their 9.7 and 9.4 years.
```

NEW (**strict-interior variant** — use when `E1_strict_interior_june_2022` and
`E1_strict_interior_nov_2025` are both `true`):

```
The turnover-floor row prices the middle read --- the paper's headline floor --- through the identical calculator (run \texttt{wal\_normal\_turnover}): it falls between Path B's 4.76\% and the empirical 5.14\% rows, and monotonicity in CPR puts the band ends on either side of it.
```

NEW (**tie variant** — use when either interiority flag is `false`; `⟨TIE⟩` is
`Path B's` or `the empirical`, whichever row the printed value equals, and the
strict-interior clause is dropped rather than softened):

```
The turnover-floor row prices the middle read --- the paper's headline floor --- through the identical calculator (run \texttt{wal\_normal\_turnover}): at the table's 0.1-year rounding it prints ⟨TIE⟩ own years, and monotonicity in CPR puts the band ends on either side of it.
```

The middle sentence of the note — the one enumerating 4.70%, 4.99%, 5.33% against the
contaminated 6.07% and 6.91% anchors — is **not** touched and must stay byte-identical.

### L4 — run index

The manuscript's convention is that run tags live in `tab:runindex`. Insert as the
first row after `\midrule`, anchored on the `interp_spot_check` row (count **1** in
each file):

OLD:

```
\texttt{interp\_spot\_check} & CPR-surface interpolation spot-check (ABM specification, Appendix~\ref{sec:method-abm}) \\
```

NEW:

```
\texttt{wal\_normal\_turnover} & Portfolio WAL at the off-window turnover-floor read: the normal-turnover row of Table~\ref{tab:wal} (Appendix~\ref{sec:robustness-wal}) \\
\texttt{interp\_spot\_check} & CPR-surface interpolation spot-check (ABM specification, Appendix~\ref{sec:method-abm}) \\
```

`\ref{sec:robustness-wal}` is the WAL appendix's existing label (line 1332), verified
present.

### L5 — gate #107

Highest existing gate is **#106** (round-28 G2), so the new gate is **#107**. Add the
path constant beside `WALTAB_RESULTS` (line 58 of `tools/liveness_gates.py`):

```python
WALNT_RESULTS = ROOT / "hazard" / "data" / "wal_normal_turnover_results.json"
```

Factor the rule as a function so a mutation battery can exercise it (the #105/#106
convention), and call it from the gate block immediately after gate #44's Danish-WAL
block:

```python
def wal_normal_turnover_check(tex, wnt, oos):
    """Gate #107's rule, as a function so a battery can exercise it.

    Round-30 D2: the normal-turnover WAL row must be the committed artifact's, the
    artifact's anchor must still be the floor artifact's headline read, its parity
    against the frozen calculator must have passed, and the sentence the run
    falsified must not come back.
    """
    r = wnt["rows"]["turnover_floor_oow_mid"]
    lit_row = (f"({r['mean_cpr_pct']:.2f}\\%) & {r['wal_june_2022']:.1f} & "
               f"{r['wal_nov_2025']:.1f}")
    anchor = (oos["instrument1_oow_floor"]["defensible_clean_floor"])
    par = wnt["parity"]
    ok = (bool(par["nine_rows_bit_identical"])
          and bool(par["frozen_artifact_untouched"])
          and bool(par["printed_row_precision_insensitive"])
          and bool(wnt["expectations"]["E1_pass"])
          and wnt["spec"]["anchor_full_precision_pct"] == anchor["clean_mid_pct"]
          and tex.count("\\texttt{wal\\_normal\\_turnover}") >= 1
          and lit_row in tex
          and "No row is printed at a normal-turnover speed." not in tex)
    return ok, {"lit_row": lit_row, "present": lit_row in tex,
                "tag_citations": tex.count("\\texttt{wal\\_normal\\_turnover}"),
                "anchor_pct": wnt["spec"]["anchor_full_precision_pct"],
                "stale_sentence_gone":
                    "No row is printed at a normal-turnover speed." not in tex}
```

Four properties are pinned at once, and none of them introduces a literal into the
gate file: the printed row equals the artifact (value anti-drift), the artifact's
anchor equals the floor artifact's `clean_mid_pct` (**live cross-artifact tie** — no
`4.991` literal in the gate), the run actually passed its own parity and E1, and the
falsified sentence cannot be restored without failing. The composite
`(4.99\%) & ⟨W1⟩ & ⟨W2⟩` has **0** occurrences in either file today for every
admissible pair, so the new row is the unique landing site — verified across the full
5×4 grid of candidate pairs.

Gate #44 is untouched and cannot break: its literals are substring checks on the two
Danish rows and the rule-only shortening, none of which a new row disturbs.

### L6 — test battery

New file `tests/test_wal_normal_turnover_gate.py`, in the `test_convolved_line_gate.py`
style (mutations verified non-vacuous before they are applied):

1. `test_gate_passes_on_the_manuscript` — `wal_normal_turnover_check` passes on the
   canonical tex.
2. `test_variant_carries_the_row` — same on `revised_paper_v18_long_abstract.tex`.
3. `test_row_removal_fails` — deleting the printed row line fails the gate.
4. `test_stale_sentence_restored_fails` — re-inserting *"No row is printed at a
   normal-turnover speed."* fails the gate.
5. `test_perturbed_artifact_fails` — a copy of the artifact with `wal_june_2022`
   shifted by 0.1 fails against the unmodified tex (the anti-drift direction).
6. `test_anchor_drift_fails` — a copy with `spec.anchor_full_precision_pct` set to
   the band's `clean_lo_pct` fails (the cross-artifact tie is live).
7. `test_parity_false_fails` — a copy with `parity.nine_rows_bit_identical = false`
   fails (a landing may not survive its own parity failure).
8. `test_run_tag_indexed` — `\texttt{wal\_normal\_turnover}` appears in both files
   (the runindex row landed).

Expected suite count 451 → **459**.

### L7 — TECHNICAL

New section **§45**, *Round-30: the normal-turnover WAL row — run, LANDS* (highest
existing is §44). Records: the anchor and why the contaminated candidates were
rejected; P0/P0b/P1/P2/P3 outcomes with the sha256 pins; the E1 band, the measured
pair, and its deviation from the E1′ chord; the two falsified sentences retired; the
new gate and battery; the band ends recorded-but-not-printed and why (§OPTIONAL-B).

### L8 — verdicts table: **default NO**

`tab:verdicts` catalogues pre-committed rules whose adjudication required post-run
judgment. A clean E1 pass required none. Coordinator's call to add a row anyway; if
added, it is `Enforced` with direction neutral, and its literals must be counted
before insertion.

### OPTIONAL-B — printing the band ends: **default NO**

The band ends are computed and committed to the artifact but **not printed**, for a
measured reason: the low end is precision-fragile. At 2 decimals (4.70%) and at full
precision (4.695%) the November-2025 cell can differ by 0.1 years, so any printed
band-end pair would depend on a rounding convention rather than on a measurement.
The runner records `precision_agreement_2dp_vs_full` per row so this is auditable
rather than asserted. If the coordinator does print them, the pre-committed rule is:
**print a band-end figure only where `precision_agreement_2dp_vs_full` is `true` for
that row**, print June 2022 only, and re-run the ledger below for the added literals.
The default note text (L3) states the bracketing qualitatively and adds no band-end
literal.

### Zero-slack ledger

Whole-file counts, `paper/v18/revised_paper_v18.tex`. **The canonical and the variant
have identical counts for every pattern below, before and after** — verified by
simulating the complete L1–L4 edit set on both files. Columns are the four
E1′-admissible pairs; the coordinator keeps the column the run selects and discards
the rest.

| literal | before | 9.4/8.5 | 9.4/8.6 | 9.5/8.5 | 9.5/8.6 |
|---|---:|---:|---:|---:|---:|
| `9.4` | 18 | 18 | 18 | 17 | 17 |
| `9.5` | 19 | 19 | 19 | 20 | 20 |
| `9.6` | 7 | 7 | 7 | 7 | 7 |
| `9.7` | 12 | 11 | 11 | 11 | 11 |
| `8.5` | 26 | 27 | 26 | 27 | 26 |
| `8.6` | 11 | 11 | 12 | 11 | 12 |
| `8.7` | 45 | 45 | 45 | 45 | 45 |
| `4.99\%` | 3 | 4 | 4 | 4 | 4 |
| `(4.99\%)` | 0 | 1 | 1 | 1 | 1 |
| `4.76\%` | 9 | 9 | 9 | 9 | 9 |
| `5.14\%` | 7 | 7 | 7 | 7 | 7 |
| `headline floor` | 15 | 16 | 16 | 16 | 16 |
| `normal-turnover` | 2 | 3 | 3 | 3 | 3 |
| `turnover-floor` | 8 | 11 | 11 | 11 | 11 |
| `turnover floor` | 55 | 56 | 56 | 56 | 56 |
| `Baseline turnover floor` | 0 | 1 | 1 | 1 | 1 |
| `\texttt{wal\_normal\_turnover}` | 0 | 2 | 2 | 2 | 2 |
| `No row is printed` | 1 | 0 | 0 | 0 | 0 |

Two movements are counter-intuitive and are stated so they are not mistaken for
errors: **`9.7` falls 12 → 11** and, whenever W1 = 9.5, **`9.4` falls 18 → 17** —
both because the retired L3 sentence quoted *"their 9.7 and 9.4 years"*, and the new
sentence quotes neither. `4.76\%` and `5.14\%` are unchanged because L3's replacement
re-uses both.

Provenance of the two new value literals: `⟨W1⟩` = `rows.turnover_floor_oow_mid.
wal_june_2022`, `⟨W2⟩` = `rows.turnover_floor_oow_mid.wal_nov_2025`, both from
`hazard/data/wal_normal_turnover_results.json`, each already rounded to 0.1 years by
the calculator's own `round(..., 1)`; the artifact's `raw_june_2022` / `raw_nov_2025`
carry the unrounded values for audit. `4.99\%` derives from `clean_mid_pct` 4.991 in
`hazard/data/oos_identification_results.json` at the table's 2-decimal convention.

### Post-run substitution and recount procedure

1. Read `rows.turnover_floor_oow_mid` from the new artifact; format both values
   `:.1f`. Confirm the pair matches one of the four ledger columns; if it is inside
   E1 but outside E1′ (9.6/9.7 or 8.7), **re-run the ledger** for that pair before
   editing — do not extrapolate the table.
2. Read `expectations.E1_strict_interior_june_2022` / `_nov_2025` and pick the L3
   variant accordingly.
3. Apply L1–L4 to **both** tex files, verifying each OLD anchor is count 1 in that
   file immediately before the replacement.
4. Recount every row of the ledger in both files and confirm the selected column
   exactly, including the `9.7` and `9.4` decrements.
5. Confirm `(4.99\%) & ⟨W1⟩ & ⟨W2⟩` is count **1** in each file, and
   `No row is printed` count **0**.
6. Land L5–L7; run `python3 tools/liveness_gates.py` (expect 107 gates, all PASS) and
   the suite (expect 459).
7. Rebuild; confirm 129pp ± the one added row and 0 undefined references.

---

## 5. ABORT / AMENDMENT PROTOCOL

- **Any P-gate failure or an E1 miss stops the landing.** The runner writes nothing
  on any abort, so there is no partial artifact to clean up. No tex edit, no gate, no
  test, no TECHNICAL entry — the round-28 run-free tablenote stays exactly as it is,
  and it remains true, because it only ever claimed that no such row was printed.
- **P0 failure (sha mismatch) is not a re-baseline.** The pinned digests are the
  premise of P1's meaning. If the calculator or its frozen artifact legitimately
  changed, that is a separate round with its own spec; re-pinning inside this spec
  would convert the parity gate into a tautology.
- **P0b failure is an alarm, not a retry.** It means importing the calculator wrote
  to a frozen artifact. Stop, restore the artifact from git, and do not run anything
  else in that working tree until the cause is found.
- **P3 failure** is not a STOP-forever: it means the printed row depends on the CPR
  rounding convention, which must then be stated in the manuscript rather than left
  implicit. That requires an amendment (below), not a silent choice of convention.
- **E1 miss** is the most informative failure available here: it would falsify the
  monotonicity the existing tablenote asserts. Land nothing; open it as its own
  finding.
- **Amendments** are appended to the header log as `R30-D2-A<n>` with date, the
  reason, and the exact clause changed, and are committed **before** the re-run. The
  amended spec, not this one, governs the landing.

---

## 6. MUST NOT CHANGE

`hazard/wal_table.py`; `hazard/data/wal_table_results.json` (never opened for
writing, by this runner or anything it imports); `hazard/data/oos_identification_
results.json`; the nine committed `tab:wal` rows and their order; the table's caption,
its construction tablenote (line 575) and the enumerating middle sentence of the
turnover-benchmark note (line 576); gate #44; the no-shock row's position as the
table's last row and the two sites that call it *the final row* (`tab:wal` note and
the WAL appendix at line 1336); any committed marginal, floor read, or dollar figure —
this run prices an existing measurement in maturity units and moves no estimate.
