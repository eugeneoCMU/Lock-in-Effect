#!/usr/bin/env python3
"""tex -> md edition converter for revised_paper_v18 (rebuilt round 29).

The round-15/17 converters lived only in session scratchpads and were lost;
this rebuild lives in the repo so it cannot be lost again. Format target is
the established edition format (see any UPLOAD bundle's .md):

  # Title / ## Abstract / ## I. Introduction / ### III.A ... / ## A. <appendix>
  tables  -> **Table N: caption** + pipe table + *Notes:* paragraphs
  figures -> ![Figure N](pngname) + *Figure N: caption*
  eqs     -> $$ body \\tag{n} $$
  refs    -> resolved via the .aux (Section III.D, Table 10, Figure 1, (3))
  cites   -> resolved via references.bib (natbib authoryear style)
  footnotes -> [^n] inline, collected at document end
  bibliography omitted (editions carry resolved inline citations only)

Self-checks are HARD FAILS: element counts and a residual-LaTeX sweep outside
math must come out clean or the converter exits nonzero and writes nothing.

Usage: python3 tools/editions/tex2md.py <tex> <aux> <bib> <out.md>
"""
import re
import sys
from pathlib import Path

# V20 closing session: tab:crosswalk, tab:runindex, tab:verdicts and the
# app:ledger/app:verdicts section heads migrated to replication_appendices.tex,
# so the manuscript edition carries 3 fewer tables and 2 fewer headings.
WANT = {"tables": 24, "figures": 13, "equations": 8, "footnotes": 3,
        "headings": 42}


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


def balanced(s, i):
    """s[i] == '{'; return (content, index after closing brace)."""
    assert s[i] == "{"
    d, j = 1, i + 1
    while d:
        if s[j] == "{" and s[j-1] != "\\":
            d += 1
        elif s[j] == "}" and s[j-1] != "\\":
            d -= 1
        j += 1
    return s[i+1:j-1], j


def parse_aux(aux_text):
    lab = {}
    for m in re.finditer(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}\{", aux_text):
        lab[m.group(1)] = m.group(2)
    return lab


def parse_bib(bib_text):
    """key -> (authorlabel, year) for natbib authoryear rendering."""
    out = {}
    for m in re.finditer(r"@\w+\{([^,]+),(.*?)(?=\n@|\Z)", bib_text, re.S):
        key, body = m.group(1).strip(), m.group(2)
        am = re.search(r"author\s*=\s*[{\"](.*?)[}\"]\s*,?\s*\n", body, re.S)
        ym = re.search(r"year\s*=\s*[{\"]?(\d{4})", body)
        year = ym.group(1) if ym else "n.d."
        if am:
            names = re.split(r"\s+and\s+", re.sub(r"\s+", " ", am.group(1)))
            lasts = []
            for n in names:
                n = n.strip().strip("{}")
                lasts.append(n.split(",")[0].strip() if "," in n
                             else n.split()[-1])
            if len(lasts) == 1:
                label = lasts[0]
            elif len(lasts) == 2:
                label = f"{lasts[0]} and {lasts[1]}"
            else:
                label = f"{lasts[0]} et al."
        else:
            label = key
        out[key] = (label, year)
    return out


class Conv:
    def __init__(self, tex, aux, bib):
        self.lab = parse_aux(aux)
        self.bib = parse_bib(bib)
        self.footnotes = []
        self.counts = {k: 0 for k in WANT}
        self.tex = strip_comments(tex)

    # ---- inline layer ------------------------------------------------------
    def cite(self, m):
        kind, opt, keys = m.group(1), m.group(2), m.group(3)
        pre = post = ""
        if opt:
            opts = re.findall(r"\[([^\]]*)\]", opt)
            if len(opts) == 2:
                pre, post = opts
            elif len(opts) == 1:
                post = opts[0]
        items = []
        for k in keys.split(","):
            k = k.strip()
            a, y = self.bib.get(k, (k, "?"))
            items.append((a, y))
        if kind == "citep":
            inner = "; ".join(f"{a}, {y}" for a, y in items)
            if pre:
                inner = f"{pre} {inner}"
            if post:
                inner = f"{inner}, {post}"
            return f"({inner})"
        if kind == "citet":
            a, y = items[0]
            return f"{a} ({y}{', ' + post if post else ''})"
        if kind == "citepos":
            a, y = items[0]
            return f"{a}'s ({y})"
        if kind == "citeauthor":
            return items[0][0]
        if kind == "citeyearpar":
            return f"({items[0][1]})"
        if kind == "citeyear":
            return items[0][1]
        if kind == "citealp":
            return "; ".join(f"{a}, {y}" for a, y in items)
        return m.group(0)

    def brace_cmd(self, text, cmd, fmt):
        pat = "\\" + cmd + "{"
        while True:
            i = text.find(pat)
            if i < 0:
                return text
            content, j = balanced(text, i + len(pat) - 1)
            text = text[:i] + fmt(content) + text[j:]

    def footnote_pull(self, text):
        while True:
            i = text.find("\\footnote{")
            if i < 0:
                return text
            content, j = balanced(text, i + len("\\footnote") )
            self.footnotes.append(self.inline(content))
            self.counts["footnotes"] += 1
            text = text[:i] + f"[^{len(self.footnotes)}]" + text[j:]

    def inline(self, text):
        """Brace-balanced commands transform on the whole text (they may span
        inline math); character-level transforms run outside math only."""
        s = text
        s = re.sub(r"\\(citepos|citeauthor|citeyearpar|citeyear|citealp|citep|citet)"
                   r"((?:\[[^\]]*\])*)\{([^}]*)\}", self.cite, s)
        s = s.replace("\\begingroup\\sloppy", "").replace("\\endgroup", "")
        s = re.sub(r"\\eqref\{([^}]*)\}",
                   lambda m: f"({self.lab.get(m.group(1), '??')})", s)
        s = re.sub(r"\\ref\{([^}]*)\}",
                   lambda m: self.lab.get(m.group(1), "??"), s)
        s = self.brace_cmd(s, "emph", lambda c: f"*{c}*")
        s = self.brace_cmd(s, "textbf", lambda c: f"**{c}**")
        s = self.brace_cmd(s, "textit", lambda c: f"*{c}*")
        s = self.brace_cmd(s, "texttt", lambda c: f"`{c}`")
        s = self.brace_cmd(s, "mbox", lambda c: c)
        s = self.brace_cmd(s, "label", lambda c: "")
        segs = re.split(r"((?<!\\)\$(?:\\.|[^$\\])*\$)", s)
        out = []
        for k, seg in enumerate(segs):
            if k % 2 == 1:          # math: untouched
                out.append(seg)
                continue
            p = seg
            p = p.replace("``", '"').replace("''", '"')
            p = re.sub(r"(?<!-)--(?!-)", "\u2013", p)
            p = p.replace("~", " ")
            p = p.replace("\\%", "%").replace("\\&", "&").replace("\\_", "_")
            p = p.replace("\\#", "#").replace("\\,", " ")
            p = p.replace("\\noindent", "").replace("\\par", "\n\n")
            p = p.replace("\\clearpage", "").replace("\\newpage", "")
            p = p.replace("\\appendix", "")
            out.append(p)
        return "".join(out)

    # ---- block layer -------------------------------------------------------
    def table_block(self, block):
        self.counts["tables"] += 1
        cap = ""
        i = block.find("\\caption{")
        if i >= 0:
            cap, _ = balanced(block, i + len("\\caption"))
        block = block.replace("}\\\\\n\\toprule", "}\n\\toprule")
        lm = re.search(r"\\label\{(tab:[^}]*)\}", block)
        num = self.lab.get(lm.group(1), "?") if lm else "?"
        # tabular body
        rows_md = []
        env = "tabular" if "\\begin{tabular}" in block else "longtable"
        ti = block.find("\\begin{" + env + "}")
        if ti >= 0:
            _, after_spec = balanced(block, ti + len("\\begin{" + env + "}"))
            body = block[after_spec:block.index("\\end{" + env + "}")]
            # longtable repeats its header for continuation pages; keep one copy
            if env == "longtable":
                if "\\endhead" in body:
                    body = body.split("\\endhead", 1)[1]
                    hdr = block[after_spec:block.index("\\endfirsthead")] \
                        if "\\endfirsthead" in block else ""
                    body = hdr + body
                for mk in ("\\endfirsthead", "\\endhead", "\\endfoot",
                           "\\endlastfoot"):
                    body = body.replace(mk, "")
            body = re.sub(r"\\(top|mid|bottom)rule", "", body)
            body = re.sub(r"\\cmidrule(\([^)]*\))?\{[^}]*\}", "", body)
            body = re.sub(r"\\addlinespace(\[[^\]]*\])?", "", body)
            rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
            ncol = 0
            parsed = []
            for r in rows:
                r = self.brace_cmd(r, "tnote", lambda c: f"^{c}")
                cells = [c.strip() for c in re.split(r"(?<!\\)&", r)]
                exp = []
                for c in cells:
                    mm = re.match(r"\\multicolumn\{(\d+)\}\{[^}]*\}", c)
                    if mm:
                        inner = re.sub(r"\\multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}",
                                       r"\2", c, flags=re.S)
                        exp.append(inner)
                        exp.extend([""] * (int(mm.group(1)) - 1))
                    else:
                        exp.append(c)
                parsed.append(exp)
                ncol = max(ncol, len(exp))
            for k, cells in enumerate(parsed):
                cells += [""] * (ncol - len(cells))
                line = "| " + " | ".join(
                    self.inline(c).replace("\n", " ").replace("|", "/")
                    for c in cells) + " |"
                rows_md.append(line)
                if k == 0:
                    rows_md.append("|" + "---|" * ncol)
        notes = []
        for im in re.finditer(r"\\item(?:\[[^\]]*\])?\s", block):
            pass
        tn = re.search(r"\\begin\{tablenotes\}.*?\\end\{tablenotes\}", block, re.S)
        if tn:
            for item in re.split(r"\\item\b", tn.group(0))[1:]:
                item = re.sub(r"\\end\{tablenotes\}.*", "", item, flags=re.S)
                item = re.sub(r"^\[[^\]]*\]", "", item.strip())
                txt = re.sub(r"\s+", " ", self.inline(item)).strip()
                if txt:
                    notes.append(f"*{txt}*" if "*" not in txt else txt)
        cap_md = re.sub(r"\s+", " ", self.inline(cap)).strip()
        out = [f"**Table {num}: {cap_md}**", ""]
        out += rows_md
        if notes:
            out += [""] + notes
        return "\n".join(out)

    def figure_block(self, block):
        self.counts["figures"] += 1
        cap = ""
        i = block.find("\\caption{")
        if i >= 0:
            cap, _ = balanced(block, i + len("\\caption"))
        lm = re.search(r"\\label\{(fig:[^}]*)\}", block)
        num = self.lab.get(lm.group(1), "?") if lm else "?"
        gm = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", block)
        png = gm.group(1) if gm else "?"
        cap_md = re.sub(r"\s+", " ", self.inline(cap)).strip()
        cap_line = (f"*Figure {num}: {cap_md}*" if "*" not in cap_md
                    else f"Figure {num}: {cap_md}")
        return f"![Figure {num}]({png})\n\n{cap_line}"

    def equation_block(self, block):
        self.counts["equations"] += 1
        lm = re.search(r"\\label\{(eq:[^}]*)\}", block)
        num = self.lab.get(lm.group(1), "?") if lm else "?"
        body = re.sub(r"\\label\{[^}]*\}", "", block).strip()
        return f"$$\n{body} \\tag{{{num}}}\n$$"

    def convert(self):
        t = self.tex
        title = re.search(r"\\title\{([^}]*)\}", t).group(1)
        body = t[t.index("\\begin{document}") + len("\\begin{document}"):
                 t.index("\\end{document}")]
        # cut bibliography block
        body = re.sub(r"\\bibliographystyle\{[^}]*\}\s*\\bibliography\{[^}]*\}",
                      "", body)
        body = re.sub(r"\\vspace\{[^}]*\}", "", body)
        body = body.replace("{\\footnotesize", "")
        body = "\n".join(ln for ln in body.split("\n") if ln.strip() != "}")
        body = self.footnote_pull(body)

        lines = body.split("\n")
        out = [f"# {title}", ""]
        appendix = False
        i = 0
        while i < len(lines):
            ln = lines[i]
            stripped = ln.strip()
            if stripped in ("\\maketitle", "\\newpage", "\\clearpage", ""):
                if stripped == "":
                    out.append("")
                i += 1
                continue
            if stripped == "\\appendix":
                appendix = True
                i += 1
                continue
            if stripped.startswith("\\begin{abstract}"):
                j = next(k for k in range(i, len(lines))
                         if "\\end{abstract}" in lines[k])
                inner = "\n".join(lines[i:j+1])
                inner = inner.replace("\\begin{abstract}", "").replace(
                    "\\end{abstract}", "")
                out += ["## Abstract", "", self.inline(inner).strip(), ""]
                i = j + 1
                continue
            for env, fn in (("longtable", self.table_block),
                            ("table", self.table_block),
                            ("figure", self.figure_block),
                            ("equation", self.equation_block)):
                if stripped.startswith(f"\\begin{{{env}}}"):
                    j = next(k for k in range(i, len(lines))
                             if f"\\end{{{env}}}" in lines[k])
                    out += [fn("\n".join(lines[i:j+1])), ""]
                    i = j + 1
                    break
            else:
                m = re.match(r"\\(section|subsection)\{", stripped)
                if m:
                    cmd = m.group(1)
                    titletxt, jj = balanced(stripped, stripped.index("{"))
                    lm = re.search(r"\\label\{([^}]*)\}", stripped[jj:])
                    num = self.lab.get(lm.group(1), "?") if lm else "?"
                    self.counts["headings"] += 1
                    if cmd == "section":
                        out += [f"## {num}. {self.inline(titletxt)}", ""]
                    else:
                        out += [f"### {num} {self.inline(titletxt)}", ""]
                    rest = stripped[jj:]
                    rest = re.sub(r"^\\label\{[^}]*\}", "", rest)
                    if rest.strip():
                        out += [self.inline(rest).strip(), ""]
                    i += 1
                    continue
                if stripped.startswith("\\paragraph{"):
                    ptitle, jj = balanced(stripped, stripped.index("{"))
                    rest = stripped[jj:]
                    out += [f"**{self.inline(ptitle)}** "
                            + self.inline(rest).strip(), ""]
                    i += 1
                    continue
                if stripped.startswith("\\begin{itemize}"):
                    j = next(k for k in range(i, len(lines))
                             if "\\end{itemize}" in lines[k])
                    blk = "\n".join(lines[i:j+1])
                    blk = blk.replace("\\begin{itemize}", "").replace(
                        "\\end{itemize}", "")
                    for item in re.split(r"\\item\b", blk)[1:]:
                        out.append("- " + self.inline(item).strip())
                    out.append("")
                    i = j + 1
                    continue
                out += [self.inline(stripped), ""]
                i += 1

        if self.footnotes:
            out.append("")
            for k, fn in enumerate(self.footnotes, 1):
                out.append(f"[^{k}]: {fn.strip()}")
                out.append("")
        md = "\n".join(out)
        md = re.sub(r"\n{3,}", "\n\n", md)
        return md

    def selfcheck(self, md):
        errs = []
        for k, want in WANT.items():
            if self.counts[k] != want:
                errs.append(f"{k}: {self.counts[k]} != want {want}")
        # residual latex outside math and code spans
        plain = re.sub(r"\$\$.*?\$\$", "", md, flags=re.S)
        plain = re.sub(r"(?<!\\)\$(?:\\.|[^$\\])*\$", "", plain)
        plain = re.sub(r"`[^`]*`", "", plain)
        for bad in (r"\\cite", r"\\ref\{", r"\\emph", r"\\textbf", r"\\texttt",
                    r"\\footnote", r"\\begin", r"\\end", r"\\label", r"\?\?",
                    r"\\vspace", r"\\footnotesize", r"\\noindent"):
            hits = re.findall(bad + r"[^ ]{0,30}", plain)
            if hits:
                errs.append(f"residual {bad}: {len(hits)} e.g. {hits[:2]}")
        return errs


def main():
    tex_p, aux_p, bib_p, out_p = map(Path, sys.argv[1:5])
    c = Conv(tex_p.read_text(), aux_p.read_text(), bib_p.read_text())
    md = c.convert()
    errs = c.selfcheck(md)
    if errs:
        print("SELF-CHECK FAILED:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    out_p.write_text(md)
    print(f"OK: {out_p} ({len(md.splitlines())} lines); counts={c.counts}")


if __name__ == "__main__":
    main()
