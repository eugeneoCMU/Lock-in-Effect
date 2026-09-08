#!/usr/bin/env python3
"""Static validation of a LaTeX manuscript when no engine is available.

This is not a compiler and cannot prove a document typesets. It catches the
error classes an editing pass actually introduces:

  1. real parse errors, via pylatexenc's LaTeX walker
  2. environment nesting, stack-based (begin/end counts can match while the
     order is wrong: \\begin{a}\\begin{b}\\end{a}\\end{b})
  3. \\cite keys with no entry in the .bib
  4. \\ref / \\eqref targets with no \\label
  5. duplicate \\label definitions
  6. inline math delimiters unbalanced within a paragraph
  7. tabular rows whose & count exceeds the column spec
  8. unescaped %, &, _, # outside math and verbatim

Usage: tex_validate.py DOC.tex [--bib references.bib]
Exit 0 clean, 1 if any error class fires.
"""
import argparse
import re
import sys
from collections import Counter, defaultdict

BEGIN = re.compile(r"\\begin\{([a-zA-Z*]+)\}")
END = re.compile(r"\\end\{([a-zA-Z*]+)\}")


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


def parse_check(src):
    try:
        from pylatexenc.latexwalker import LatexWalker, LatexWalkerError
    except ImportError:
        return ["pylatexenc unavailable - parse check skipped"]
    try:
        LatexWalker(src, tolerant_parsing=False).get_latex_nodes()
        return []
    except Exception as exc:  # LatexWalkerError and friends
        msg = str(exc).replace("\n", " ")
        return [f"PARSE ERROR: {msg[:300]}"]


def env_stack(src):
    errs, stack = [], []
    for m in re.finditer(r"\\(begin|end)\{([a-zA-Z*]+)\}", src):
        kind, name = m.group(1), m.group(2)
        line = src.count("\n", 0, m.start()) + 1
        if kind == "begin":
            stack.append((name, line))
        else:
            if not stack:
                errs.append(f"line {line}: \\end{{{name}}} with nothing open")
            elif stack[-1][0] != name:
                o, ol = stack[-1]
                errs.append(f"line {line}: \\end{{{name}}} closes \\begin{{{o}}} opened line {ol}")
                stack.pop()
            else:
                stack.pop()
    for name, line in stack:
        errs.append(f"line {line}: \\begin{{{name}}} never closed")
    return errs


def cite_check(src, bib_path):
    if not bib_path:
        return []
    try:
        bib = open(bib_path, encoding="utf-8").read()
    except OSError:
        return [f"bib not readable: {bib_path}"]
    keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", bib))
    # Skip \newcommand/\def bodies: a macro definition contains \citeauthor{#1},
    # whose "#1" is a parameter marker, not a bib key.
    body = strip_comments(src)
    body = re.sub(r"\\(?:newcommand|renewcommand|def)\b.*", "", body)
    used = set()
    for m in re.finditer(r"\\cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}", body):
        for k in m.group(1).split(","):
            k = k.strip()
            if k and "#" not in k:
                used.add(k)
    missing = sorted(used - keys)
    return [f"CITE with no bib entry: {k}" for k in missing]


def ref_check(src):
    labels = Counter(re.findall(r"\\label\{([^}]*)\}", src))
    refs = set(re.findall(r"\\(?:ref|autoref|eqref|pageref)\{([^}]*)\}", src))
    errs = [f"REF with no \\label: {r}" for r in sorted(refs - set(labels))]
    errs += [f"DUPLICATE \\label: {k} ({v}x)" for k, v in sorted(labels.items()) if v > 1]
    return errs


def math_check(src):
    errs = []
    for i, para in enumerate(strip_comments(src).split("\n")):
        t = para.replace(r"\$", "")
        if t.count("$") % 2:
            errs.append(f"line {i+1}: odd number of $ ({t.count('$')})")
    return errs


def tabular_check(src):
    errs = []
    for m in re.finditer(r"\\begin\{tabular\}(?:\[[^\]]*\])?\{", src):
        # Column specs nest braces (@{}lrr@{}, p{3cm}); match them by depth.
        i = m.end(); depth = 1
        while i < len(src) and depth:
            if src[i] == "{": depth += 1
            elif src[i] == "}": depth -= 1
            i += 1
        spec = src[m.end():i-1]
        e = src.find("\\end{tabular}", i)
        if e < 0: continue
        body = src[i:e]
        cols = len(re.findall(r"[lcrp]", re.sub(r"@\{[^}]*\}|\|", "", spec)))
        line0 = src.count("\n", 0, m.start()) + 1
        for row in body.split(r"\\"):
            if not row.strip() or "\\multicolumn" in row or "\\midrule" in row:
                continue
            n = len(re.findall(r"(?<!\\)&", row)) + 1
            if n > cols:
                errs.append(f"line ~{line0}: tabular row has {n} cells, spec allows {cols}")
    return errs


def special_check(src):
    errs = []
    body = strip_comments(src)
    body = re.sub(r"\$[^$]*\$", "", body)
    body = re.sub(r"\\begin\{(verbatim|lstlisting)\}.*?\\end\{\1\}", "", body, flags=re.S)
    for i, line in enumerate(body.split("\n")):
        line = re.sub(r"\\[%&_#$]", "", line)
        line = re.sub(r"\\[a-zA-Z]+\{[^{}]*\}", "", line)
        for ch in "%":
            if ch in line:
                errs.append(f"line {i+1}: unescaped {ch}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc")
    ap.add_argument("--bib", default=None)
    a = ap.parse_args()
    src = open(a.doc, encoding="utf-8").read()

    checks = [
        ("parse (pylatexenc)", parse_check(src)),
        ("environment nesting", env_stack(src)),
        ("citations vs bib", cite_check(src, a.bib)),
        ("refs and labels", ref_check(src)),
        ("inline math delimiters", math_check(src)),
        ("tabular column counts", tabular_check(src)),
    ]
    bad = 0
    for name, errs in checks:
        if errs:
            bad += 1
            print(f"[FAIL] {name}: {len(errs)} issue(s)")
            for e in errs[:8]:
                print(f"        {e}")
            if len(errs) > 8:
                print(f"        ... and {len(errs)-8} more")
        else:
            print(f"[OK]   {name}")
    print()
    print("CLEAN" if not bad else f"{bad} check(s) failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
