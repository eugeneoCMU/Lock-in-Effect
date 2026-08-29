#!/usr/bin/env python3
"""RENDER-LAYER GATE — the check the 108 source gates structurally cannot make.

Every gate in tools/liveness_gates.py reads the .tex and the frozen artifacts.
None reads the built PDF. Round 31 found the consequence: ~919 text items across
9 pages sat OUTSIDE the physical sheet (the worst page carried 302 items of the
Appendix O adjudication ledger more than a full page below the bottom margin),
and the defect survived every round because every literal was present and
correctly derived IN THE SOURCE -- it simply never reached the page.

This gate fails when a glyph is positioned off the sheet, when a cross-reference
is unresolved, or when the split PDFs do not partition the canonical one.

It deliberately does NOT pin a page count. The count legitimately moves every
round (113 -> 129 -> 130 -> 157), so a literal would go red on every ordinary
landing and be retuned rather than believed. The third clause of this docstring
used to claim a page-count check anyway, backed by an EXPECTED_PAGES dict that
was defined once and read nowhere; both are gone. What IS checked are the two
invariants that do not churn and that nothing else guarded: the hand-cut split
must partition the canonical document exactly, and the variant must have the
same length as it.

Position is computed in DEVICE space. pypdf's text visitor hands back the text
matrix (tm) and the current transformation matrix (cm) separately; tm alone is
relative to the text object and is NOT the position on the page (an early probe
that used tm[5] reported every page as broken). The composition below is what
puts a glyph where the reader sees it:

    device_x = cm[0]*tm[4] + cm[2]*tm[5] + cm[4]
    device_y = cm[1]*tm[4] + cm[3]*tm[5] + cm[5]

Usage:
    python3 tools/render_gate.py [pdf ...]        # defaults to the built set
Exit status is nonzero if any check fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "paper" / "final" / "build_split"
DEFAULTS = [
    BUILD / "paper_final_v1.pdf",
    BUILD / "paper_final_v1_main.pdf",
    BUILD / "paper_final_v1_online_appendix.pdf",
    BUILD / "paper_final_v1_long_abstract.pdf",
]
# a glyph's origin may sit a hair outside the box through rounding; a descender
# at the very bottom margin is fine. 2pt is far below the 12pt line height, so
# a clipped LINE can never hide inside the tolerance.
EPS = 2.0


def device_xy(cm, tm) -> tuple[float, float]:
    """Where a glyph actually lands on the sheet, in PDF device space."""
    return (cm[0] * tm[4] + cm[2] * tm[5] + cm[4],
            cm[1] * tm[4] + cm[3] * tm[5] + cm[5])


def is_offpage(dx: float, dy: float, box: tuple[float, float, float, float],
               eps: float = None) -> bool:
    """True when (dx, dy) falls outside the printable box beyond tolerance."""
    e = EPS if eps is None else eps
    x0, y0, x1, y1 = box
    return dy < y0 - e or dy > y1 + e or dx < x0 - e or dx > x1 + e


def scan(pdf: Path) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    offpage: list[tuple[int, float, float, str]] = []
    for pno, page in enumerate(reader.pages, 1):
        box = page.cropbox if page.cropbox is not None else page.mediabox
        x0, y0 = float(box.left), float(box.bottom)
        x1, y1 = float(box.right), float(box.top)
        items: list[tuple[float, float, str]] = []

        def visit(text, cm, tm, font_dict, font_size, _items=items):
            if not text.strip():
                return
            dx, dy = device_xy(cm, tm)
            _items.append((dx, dy, text.strip()))

        page.extract_text(visitor_text=visit)
        for dx, dy, text in items:
            if is_offpage(dx, dy, (x0, y0, x1, y1)):
                offpage.append((pno, dx, dy, text[:70]))
    full = "\n".join(p.extract_text() for p in reader.pages)
    return {
        "pages": len(reader.pages),
        "offpage": offpage,
        "unresolved": full.count("??"),
    }


def main(argv: list[str]) -> int:
    pdfs = [Path(a) for a in argv[1:]] or DEFAULTS
    failures = 0
    for pdf in pdfs:
        if not pdf.exists():
            print(f"[FAIL] render gate: {pdf.name} MISSING — build it before "
                  f"claiming a clean render")
            failures += 1
            continue
        r = scan(pdf)
        bad_pages = sorted({p for p, *_ in r["offpage"]})
        ok = not r["offpage"] and r["unresolved"] == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] render gate: {pdf.name} "
              f"{r['pages']}pp, off-page items={len(r['offpage'])}"
              f"{f' on pages {bad_pages}' if bad_pages else ''}, "
              f"unresolved-refs={r['unresolved']}")
        for pno, dx, dy, text in r["offpage"][:8]:
            print(f"         p{pno} at ({dx:.1f}, {dy:.1f}): {text!r}")
        if len(r["offpage"]) > 8:
            print(f"         ... and {len(r['offpage']) - 8} more")
    # The split is cut BY HAND after every rebuild and nothing verified it.
    # These two invariants are structural rather than numeric, so they never
    # need retuning: pages must be conserved, and the variant must not drift
    # in length from the canonical file.
    if not argv[1:]:
        seen = {p.name: scan(p)["pages"] for p in DEFAULTS if p.exists()}
        canon = seen.get("paper_final_v1.pdf")
        parts = (seen.get("paper_final_v1_main.pdf"),
                 seen.get("paper_final_v1_online_appendix.pdf"))
        variant = seen.get("paper_final_v1_long_abstract.pdf")
        if canon is not None and all(x is not None for x in parts):
            split_ok = parts[0] + parts[1] == canon
            failures += 0 if split_ok else 1
            print(f"[{'PASS' if split_ok else 'FAIL'}] split partitions the "
                  f"canonical document: {parts[0]} + {parts[1]} = "
                  f"{parts[0] + parts[1]} against {canon}pp")
        if canon is not None and variant is not None:
            var_ok = variant == canon
            failures += 0 if var_ok else 1
            print(f"[{'PASS' if var_ok else 'FAIL'}] variant length matches the "
                  f"canonical document: {variant}pp against {canon}pp")

    print(f"\n{'ALL RENDER CHECKS PASS' if not failures else f'{failures} RENDER CHECK(S) FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
