#!/usr/bin/env python3
"""Cut the built manuscript into the two-PDF submission package.

The render gate checks that the split partitions the canonical document
(main pages + appendix pages == canonical pages). Until this script existed
the cut was made by hand after every rebuild, which is exactly the step the
gate's own comment flags as unverified: a hand cut at a stale boundary still
partitions, so the arithmetic check passes while the banner sits on the wrong
side of the seam.

The boundary is found in the text, not typed in: the first page whose text
opens the "Online Appendix" banner starts the appendix half. That makes the
cut survive any reflow, which is the property a typed page number lacks.

Run:  python3 tools/split_pdf.py [BUILD_DIR]
      (default BUILD_DIR: paper/final/build_split)
Exit 0 iff both halves were written and their page counts sum to the whole.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNER = "Online Appendix"


def find_boundary(pdf_path: Path) -> int:
    """1-indexed page on which the Online Appendix banner opens."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    for i, page in enumerate(reader.pages, 1):
        head = (page.extract_text() or "")[:200]
        if head.lstrip().startswith(BANNER):
            return i
    raise SystemExit(f"{pdf_path.name}: no page opens with {BANNER!r}; "
                     "the appendix banner moved or the build is stale")


def main(argv: list[str]) -> int:
    from pypdf import PdfReader, PdfWriter

    build = Path(argv[1]) if argv[1:] else ROOT / "paper" / "final" / "build_split"
    src = build / "paper_final_v1.pdf"
    if not src.exists():
        raise SystemExit(f"{src} missing — build the manuscript first")

    cut = find_boundary(src)
    reader = PdfReader(str(src))
    total = len(reader.pages)

    for name, pages in (("paper_final_v1_main.pdf", range(0, cut - 1)),
                        ("paper_final_v1_online_appendix.pdf", range(cut - 1, total))):
        writer = PdfWriter()
        for p in pages:
            writer.add_page(reader.pages[p])
        with open(build / name, "wb") as fh:
            writer.write(fh)

    main_pp, app_pp = cut - 1, total - cut + 1
    ok = main_pp + app_pp == total
    print(f"[{'PASS' if ok else 'FAIL'}] split at the {BANNER!r} banner, page {cut}: "
          f"main 1-{cut - 1} ({main_pp}pp) + appendix {cut}-{total} ({app_pp}pp) "
          f"= {main_pp + app_pp} against {total}pp")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
