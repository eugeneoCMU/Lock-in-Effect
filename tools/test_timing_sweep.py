#!/usr/bin/env python3
"""
Golden-fixture test for tools/timing_sweep.py (round-9 panel requirement).

Three matcher generations produced three defects: round 6 recorded only the
first family phrase per line; the round-6 extension false-positived on
'flags'; the round-8 rewrite silently dropped suffix-s forms ('offsets',
'leads'). Each defect class is a fixture line below with a hand-enumerated
expected hit set the matcher must reproduce EXACTLY — no more, no fewer.
This test is a freeze-gate item: it must pass at the pre-submission freeze
and after any change to the matcher.

Run:  python3 tools/test_timing_sweep.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from timing_sweep import hits_for  # noqa: E402

FIXTURE = [
    # 1. round-6 defect class: three family phrases share one line — all must record
    "the path moves three months ahead of the sim; the sim trails it, so the empirical moves first.",
    # 2. round-6 false-positive class: 'flags' must NOT match 'lags'; 'unleaded'/'mislead' must NOT match 'lead'
    "the pipeline flags unleaded entries and does not mislead anyone.",
    # 3. round-8 defect class: suffix-s forms must match
    "the discount offsets the spread while the empirical series leads the sim.",
    # 4. base forms, case-insensitive, two-word phrase
    "Timing is not a credential; the Path Diagnostics column records the lead at seven lags.",
    # 5. no family content at all
    "this sentence is deliberately empty of family phrases.",
    # 6. phrase at line start and line end
    "offset at the start; at the end comes the offset",
]

EXPECTED = {
    (1, "ahead"), (1, "trails"), (1, "moves first"),
    (3, "offset"), (3, "lead"),
    (4, "timing"), (4, "path diagnostics"), (4, "lead"), (4, "lags"),
    (6, "offset"), (6, "offset"),
}
# line 6 has two 'offset' hits — use a multiset
from collections import Counter  # noqa: E402

EXPECTED_MULTI = Counter([
    (1, "ahead"), (1, "trails"), (1, "moves first"),
    (3, "offset"), (3, "lead"),
    (4, "timing"), (4, "path diagnostics"), (4, "lead"), (4, "lags"),
    (6, "offset"), (6, "offset"),
])


def main() -> None:
    rows = hits_for(FIXTURE, "fixture")
    got = Counter((r["line"], r["phrase"]) for r in rows)
    missing = EXPECTED_MULTI - got
    spurious = got - EXPECTED_MULTI
    if missing or spurious:
        print("GOLDEN FIXTURE FAILED")
        if missing:
            print("  missing hits:", dict(missing))
        if spurious:
            print("  spurious hits:", dict(spurious))
        sys.exit(1)
    print(f"GOLDEN FIXTURE PASSED: {sum(got.values())} hits, "
          "exact match to the hand-enumerated set "
          "(multi-hit lines, suffix-s forms, 'flags'/'unleaded'/'mislead' rejected)")


if __name__ == "__main__":
    main()
