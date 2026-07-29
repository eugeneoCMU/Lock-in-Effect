#!/usr/bin/env python3
"""md -> txt edition converter (rebuilt round 29; format matches the
established .txt editions: ## headings underlined with =, ### plain,
image lines dropped, bold/italic markers stripped, \\$ unescaped).

Usage: python3 tools/editions/md2txt.py <in.md> <out.txt>
"""
import re
import sys
from pathlib import Path


def convert(md):
    out = []
    for ln in md.split("\n"):
        if ln.startswith("!["):
            continue
        if ln.startswith("# ") and not ln.startswith("## "):
            out.append(ln[2:])
            continue
        if ln.startswith("## "):
            t = ln[3:]
            out.append(t)
            out.append("=" * len(t))
            continue
        if ln.startswith("### "):
            out.append(ln[4:])
            continue
        s = ln
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s, flags=re.S)
        s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", s)
        s = s.replace("\\$", "$")
        out.append(s)
    txt = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", txt)


def main():
    md_p, out_p = Path(sys.argv[1]), Path(sys.argv[2])
    txt = convert(md_p.read_text())
    assert "![" not in txt and "**" not in txt, "markdown residue in txt"
    out_p.write_text(txt)
    print(f"OK: {out_p} ({len(txt.splitlines())} lines)")


if __name__ == "__main__":
    main()
