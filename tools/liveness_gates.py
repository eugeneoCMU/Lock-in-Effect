#!/usr/bin/env python3
"""
Liveness gates: manuscript-vs-artifact checks as a runnable script
(pre-submission freeze item (iii) mechanized; see TECHNICAL.md §22).

Exit 0 iff ALL gates pass; each gate prints PASS/FAIL. Three gate classes:

1. Zero-count greps — phrases that must be ABSENT from the manuscript
   (retired claims, superseded numbers, and stale framing; each phrase's
   retirement is recorded in TECHNICAL.md §12.1/§22.4 or the run ledger).
2. Exactly-one greps — sentences that must be PRESENT exactly once
   (the ratified title and load-bearing provenance sentences).
3. Manuscript-vs-manifest cross-checks — a claim in the tex and a flag in
   a frozen run manifest must agree; failing when either side flips
   without the other (the defect class a review round caught in the
   Danish counterfactual's description).

Run:  python3 tools/liveness_gates.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "v16" / "revised_paper_v16.tex"
MANIFEST = ROOT / "abm" / "data" / "runs" / "run-2026-07-04-15yr-foldin" / "manifest.json"

ZERO_COUNT = [
    "production specification omits",
    "never route the same loan-month",
    "behavioral gate is future work",
    "Two items are bound",
    "10.26",
    "stranding an estimated",
    "roughly 13\\% of the benchmark",
    "That mortgage lock-in slowed",
]

EXACTLY_ONE = [
    "\\title{The Securitization Trade-Off",
    "frozen manifests say otherwise",
    "9.96\\% of home value",
    "supersede this tag",
]

KERNEL_TEX_PHRASE = "kernel is retained in production"


def main() -> int:
    tex = TEX.read_text()
    failures = 0

    for phrase in ZERO_COUNT:
        n = tex.count(phrase)
        ok = n == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] zero-count {phrase!r}: {n}")

    for phrase in EXACTLY_ONE:
        n = tex.count(phrase)
        ok = n == 1
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] exactly-one {phrase!r}: {n}")

    manifest = json.loads(MANIFEST.read_text())
    flag = bool(manifest.get("pipeline", {}).get("apply_settlement_lag_kernel"))
    phrase_present = KERNEL_TEX_PHRASE in tex
    ok = flag == phrase_present
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check settlement-lag kernel: "
        f"manifest apply_settlement_lag_kernel={flag}, "
        f"tex {KERNEL_TEX_PHRASE!r} present={phrase_present} "
        f"(must agree; either side flipping without the other fails)"
    )

    print(f"\n{'ALL GATES PASS' if failures == 0 else f'{failures} GATE(S) FAILED'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
