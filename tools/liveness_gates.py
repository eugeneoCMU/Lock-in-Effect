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
FANNIE_RESULTS = ROOT / "hazard" / "data" / "fannie_replication_results.json"

ZERO_COUNT = [
    "production specification omits",
    "never route the same loan-month",
    "behavioral gate is future work",
    "Two items are bound",
    "10.26",
    "stranding an estimated",
    "roughly 13\\% of the benchmark",
    "That mortgage lock-in slowed",
    "1.3 years too long",
]

EXACTLY_ONE = [
    "\\title{The Securitization Trade-Off",
    "frozen manifests say otherwise",
    "9.96\\% of home value",
    "supersede this tag",
]

KERNEL_TEX_PHRASE = "kernel is retained in production"

# --- Post-freeze consistency pass (2026-07-14) ------------------------------
# Superseded spec v3 figures that must stay out of the tex except where
# explicitly labeled, ledger-completeness checks, and figure-script
# hardcoded-literal gates (the defect class the pass existed to kill:
# figure generators must READ committed artifacts, never carry the numbers).

# "894.8" (the spec v3 composed Path A) may appear only within 120 chars of
# a "spec v3" label; the unlabeled form was the §VII.F defect.
SUPERSEDED_CONTEXTUAL = {"894.8": "spec v3"}

# The Appendix A run ledger must record the Path A spec v3 -> v4 supersession.
LEDGER_SECTION = "\\section{Superseded Figures and Run Ledger}"
LEDGER_REQUIRED = ["spec v3", "121.5"]

FIGURE_SCRIPTS = [
    "figures/make_figures.py",
    "figures/make_ccf_data.py",
    "abm/monte_carlo_simulation.py",
]

# Benchmark shares (% of the $764.7B benchmark) and headline dollar figures
# that have ever been displayed in a figure; none may be hardcoded in a
# figure script (values arrive via json/manifest reads).
SHARE_LITERALS = [
    "119.7", "894.8", "117.0", "110.6", "112.4", "121.5", "127.5",
    "107.0", "109.1", "97.9", "96.9", "106.0", "100.04", "88.7",
    "59.3", "20.9", "11.9", "11.1", "71.1", "54.9", "45.1", "33.7",
    "764.7", "915.0", "915.1", "928.9", "905.1", "818.5", "834.6",
    "974.7", "91.0", "84.5", "453.5", "159.5", "765.1",
]

# The retracted timing convention may not reappear in any figure script.
FIGURE_FORBIDDEN = ["model CPR leads", "model leads", "TBA settlement"]

# Freeze item (ii), LaTeX half: every cross-reference goes through \ref —
# a hardcoded "Table 7" / "Section V.C" literal would silently drift when
# floats renumber. Comments are stripped before matching.
HARDCODED_XREF = {
    "Table N literal": r"Table[~ ]\d",
    "Figure N literal": r"Figure[~ ]\d",
    "Section roman literal": r"Section[~ ][IVX]+(?:\.[A-Z])?(?![a-zA-Z}])",
    "Appendix letter literal": r"Appendix[~ ][AB](?![a-zA-Z}])",
    "Equation (N) literal": r"[Ee]quation[~ ]\(\d\)",
}


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

    import re
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    for label, pat in HARDCODED_XREF.items():
        n = len(re.findall(pat, tex_nc))
        ok = n == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] no-hardcoded-xref {label}: {n}")

    # --- Post-freeze pass gates ---------------------------------------------
    for phrase, label in SUPERSEDED_CONTEXTUAL.items():
        bad = 0
        start = 0
        while (idx := tex.find(phrase, start)) != -1:
            window = tex[max(0, idx - 120): idx + 120]
            if label not in window:
                bad += 1
            start = idx + len(phrase)
        ok = bad == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] superseded-unless-labeled "
              f"{phrase!r} (label {label!r}): {bad} unlabeled")

    lstart = tex.find(LEDGER_SECTION)
    lend = tex.find("\\section{", lstart + 1) if lstart != -1 else -1
    ledger = tex[lstart:lend] if lstart != -1 and lend != -1 else ""
    for needle in LEDGER_REQUIRED:
        ok = lstart != -1 and needle in ledger
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] ledger-contains {needle!r}")

    for rel in FIGURE_SCRIPTS:
        src = (ROOT / rel).read_text()
        hits = [lit for lit in SHARE_LITERALS
                if re.search(rf"(?<![\d.]){re.escape(lit)}(?!\d)", src)]
        ok = not hits
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] figure-script-no-share-literals "
              f"{rel}: {hits if hits else 0}")
        fhits = [p for p in FIGURE_FORBIDDEN if p in src]
        ok = not fhits
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] figure-script-no-retracted-timing "
              f"{rel}: {fhits if fhits else 0}")

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

    # Round-14 W4: the manuscript's Fannie replication sentences must agree
    # with the committed artifact — the envelope gate must actually have
    # passed, and the printed marginal must be the artifact's, rounded as
    # printed (+$XX.X billion / +X.XX points). Same manifest-vs-tex contract
    # as the settlement-lag gate: either side moving without the other fails.
    fannie = json.loads(FANNIE_RESULTS.read_text())
    env = fannie["gates"]["gate_envelope"]
    claims = tex.count("run \\texttt{fannie\\_replication}")
    marg_b = f"+\\${fannie['path_b']['lockin_marginal_b']:.1f}"
    marg_pp = f"+{fannie['path_b']['lockin_marginal_share_pp']:.2f}"
    ok = (bool(env["pass"]) and claims == 1
          and marg_b in tex and marg_pp in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check fannie replication: "
        f"artifact envelope pass={env['pass']}, tex run-citation count="
        f"{claims} (want 1), marginal literals {marg_b!r}/{marg_pp!r} "
        f"present={marg_b in tex}/{marg_pp in tex}"
    )

    print(f"\n{'ALL GATES PASS' if failures == 0 else f'{failures} GATE(S) FAILED'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
