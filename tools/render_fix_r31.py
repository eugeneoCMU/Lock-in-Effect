#!/usr/bin/env python3
"""R31 render repair: make over-tall tables breakable and over-wide tables wrap.

Two transformations, both text-preserving (every word/number/pin byte-identical;
only environments, column specs, and where notes sit change):

  CLASS A (rows exceed a page)  -> longtable with repeated header
  CLASS B (tablenotes push the float over) -> notes moved out of the float,
          immediately after it, as a breakable \footnotesize paragraph block
  CLASS C (cells run past the right margin) -> p{} column specs

Usage: render_fix.py <in.tex> <out.tex>   (pure function of the input file)
"""
import re
import sys

CLASS_A = ["tab:verdicts", "tab:runindex", "tab:headline", "tab:uncertainty"]
CLASS_B = ["tab:bases", "tab:estimators", "tab:danish",
           "tab:ladder", "tab:oosfloor"]
# label -> (old colspec, new colspec)
CLASS_C = {
    "tab:assembly": ("{@{}llll@{}}",
                     "{@{}p{3.1cm}p{2.6cm}p{2.4cm}p{7.7cm}@{}}"),
    "tab:danish": ("{@{}lrrrr@{}}",
                   "{@{}p{3.4cm}rrr>{\\raggedright\\arraybackslash}p{4.0cm}@{}}"),
}
CLASS_D = {"fig:marginalcells": ("[H]", "[tbp]")}
SIZES = ("\\scriptsize", "\\footnotesize", "\\small", "\\tiny")


def find_env(lines, label):
    """Return (start, end) line indices of the table float holding `label`."""
    li = next(i for i, l in enumerate(lines) if "\\label{" + label + "}" in l)
    start = max(i for i, l in enumerate(lines[:li + 1])
                if l.startswith("\\begin{table}"))
    end = min(i for i, l in enumerate(lines) if i >= li
              and l.startswith("\\end{table}"))
    return start, end


def parts(lines, start, end):
    """Decompose a table float into its structural pieces."""
    blk = lines[start:end + 1]
    def idx(pred, default=None):
        for k, l in enumerate(blk):
            if pred(l):
                return k
        return default
    p = {
        "caption": idx(lambda l: l.startswith("\\caption{")),
        "label": idx(lambda l: l.startswith("\\label{")),
        "size": idx(lambda l: l.strip() in SIZES),
        "tpt_b": idx(lambda l: l.startswith("\\begin{threeparttable}")),
        "tpt_e": idx(lambda l: l.startswith("\\end{threeparttable}")),
        "tab_b": idx(lambda l: l.startswith("\\begin{tabular}")),
        "tab_e": idx(lambda l: l.startswith("\\end{tabular}")),
        "top": idx(lambda l: l.startswith("\\toprule")),
        "mid": idx(lambda l: l.startswith("\\midrule")),
        "bot": idx(lambda l: l.startswith("\\bottomrule")),
        "notes_b": idx(lambda l: l.lstrip().startswith("\\begin{tablenotes}")),
        "notes_e": idx(lambda l: l.lstrip().startswith("\\end{tablenotes}")),
    }
    return blk, p


def notes_paragraph(blk, p, label):
    """Convert a tablenotes block into a breakable paragraph, text preserved."""
    body = " ".join(l.strip() for l in blk[p["notes_b"] + 1:p["notes_e"]])
    # \item may appear anywhere on a line, and several may share one line
    seg = re.split(r"\\item(?:\[([^\]]*)\])?\s*", body)
    chunks = [seg[0].strip()] if seg[0].strip() else []
    for k in range(1, len(seg), 2):
        marker = seg[k]
        text = seg[k + 1].strip() if k + 1 < len(seg) else ""
        chunks.append(((marker + " ") if marker else "") + text)
    lead = ("\\noindent{\\footnotesize \\emph{Notes to "
            "Table~\\ref{" + label + "}.} ")
    out = [lead + " \\quad ".join(c for c in chunks if c) + "\\par}"]
    assert "\\item" not in out[0], f"{label}: unconverted \\item survived"
    return out


def rebuild_A(blk, p, label):
    """table+tabular -> longtable (breakable), notes (if any) moved after."""
    spec = blk[p["tab_b"]][len("\\begin{tabular}"):].strip()
    size = blk[p["size"]].strip() if p["size"] is not None else "\\footnotesize"
    header = blk[p["mid"] - 1] if p["mid"] is not None else ""
    rows_b = (p["mid"] + 1) if p["mid"] is not None else (p["top"] + 1)
    rows = blk[rows_b:p["bot"]]
    cap = blk[p["caption"]]
    lab = blk[p["label"]]
    out = ["{" + size,
           "\\begin{longtable}" + spec,
           cap,
           lab + "\\\\",
           "\\toprule",
           header,
           "\\midrule",
           "\\endfirsthead",
           "\\toprule",
           header,
           "\\midrule",
           "\\endhead"]
    out += rows
    out += ["\\bottomrule", "\\end{longtable}", "}"]
    if p["notes_b"] is not None:
        out += [""] + notes_paragraph(blk, p, label)
    return out


def rebuild_B(blk, p, label):
    """Keep the float; lift the tablenotes out so they can break."""
    keep = [l for k, l in enumerate(blk)
            if not (p["notes_b"] <= k <= p["notes_e"])]
    return keep + [""] + notes_paragraph(blk, p, label)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src).read()
    lines = text.split("\n")

    # preamble: longtable must be available
    pi = next(i for i, l in enumerate(lines) if l.startswith("\\usepackage{array}"))
    if "\\usepackage{longtable}" not in text:
        lines.insert(pi + 1, "\\usepackage{longtable}")

    # class D: figure float specs that cannot fit where [H] pins them
    for label, (old, new) in CLASS_D.items():
        li = next(i for i, l in enumerate(lines) if "\\label{" + label + "}" in l)
        fs = max(i for i, l in enumerate(lines[:li + 1])
                 if l.startswith("\\begin{figure}"))
        assert lines[fs] == "\\begin{figure}" + old, (label, lines[fs])
        lines[fs] = "\\begin{figure}" + new

    # class C first (pure colspec swap, no structural change)
    joined = "\n".join(lines)
    for label, (old, new) in CLASS_C.items():
        s, e = find_env(joined.split("\n"), label)
        blk = joined.split("\n")[s:e + 1]
        hit = [k for k, l in enumerate(blk) if l.startswith("\\begin{tabular}" + old)]
        assert len(hit) == 1, f"{label}: colspec {old} not unique ({len(hit)})"
        ls = joined.split("\n")
        ls[s + hit[0]] = "\\begin{tabular}" + new
        joined = "\n".join(ls)
    lines = joined.split("\n")

    # classes A and B, processed bottom-up so indices stay valid
    jobs = [(label, "A") for label in CLASS_A] + [(label, "B") for label in CLASS_B]
    positioned = []
    for label, kind in jobs:
        s, e = find_env(lines, label)
        positioned.append((s, e, label, kind))
    for s, e, label, kind in sorted(positioned, reverse=True):
        blk, p = parts(lines, s, e)
        if kind == "B" and p["notes_b"] is None:
            continue
        new = rebuild_A(blk, p, label) if kind == "A" else rebuild_B(blk, p, label)
        lines[s:e + 1] = new

    open(dst, "w").write("\n".join(lines))
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
