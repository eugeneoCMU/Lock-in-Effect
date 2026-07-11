#!/usr/bin/env python3
"""
Timing-phrase-family sweep (committed generator — round-8 remedy for the
round-7 lesson that sweep tools must be inspectable and record every hit).

Word-boundary regex over BOTH editions; EVERY family phrase on a line records
its own row (the round-6 one-row-per-line design silently dropped phrases that
shared a line); dispositions are evaluated on a ±200-char window around each
hit and carried between rounds by (source, phrase, context-core) key, with
unmatched hits emitted as NEW for hand-disposition.

Usage:
    python3 tools/timing_sweep.py --tex ~/Downloads/revised_paper_v15.tex \
        --docx-txt <plain-text extraction> --prev timing_sweep_log.md \
        --out timing_sweep_log.md --round 8
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FAMILY = ["timing", "lead", "path diagnostics", "nonnegative",
          "not outright negative", "materially better", "offset",
          "ahead", "trails", "moves first", "precedes", "lags"]

LEGEND = """LEGEND: round-5 dispositions recorded ACTIONS taken in that revision; rounds 6+ record
STEADY STATE (a RETAINED row may have been demoted in an earlier round).
Matcher: word-boundary regex; EVERY family phrase on a line records its own row — the
round-6 log's one-row-per-line design silently dropped 'trails' and 'moves first' when
they followed 'ahead' on the same source line (panel finding, confirmed); dispositions
are evaluated on a ±200-char window around each hit. The generator is committed at
tools/timing_sweep.py (round-8 remedy: the tool itself is now part of the record)."""


def core(ctx: str) -> str:
    return re.sub(r'[^a-z]', '', ctx.lower())[:40]


def hits_for(lines, src):
    out = []
    for ln, line in enumerate(lines, 1):
        for ph in FAMILY:
            # optional trailing 's' keeps plural/verb forms ('offsets',
            # 'leads') in scope, matching the round-4/5 logs' behavior; the
            # word boundary still rejects 'flags'-class false positives
            for m in re.finditer(r'(?<![A-Za-z])' + re.escape(ph) + r's?(?![A-Za-z])',
                                 line, re.IGNORECASE):
                a, b = max(0, m.start() - 55), min(len(line), m.end() + 55)
                ctx = ('…' if a > 0 else '') + line[a:b] + ('…' if b < len(line) else '')
                c = ctx.replace('|', '/')
                out.append({'src': src, 'line': ln, 'phrase': ph,
                            'context': c, 'key': (src, ph, core(c))})
    return out


def parse_prev(path):
    table = {}
    for row in Path(path).read_text().splitlines():
        m = re.match(r'\| (tex|docx) \| \d+ \| ([^|]+) \| ([^|]+) \| (.+) \|$', row)
        if not m:
            continue
        src, ph, ctx, disp = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
        table.setdefault((src, ph, core(ctx)), []).append(disp)
        # looser fallback: phrase + first 20 chars of context core
        table.setdefault((src, ph, core(ctx)[:20]), []).append(disp)
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tex', required=True)
    ap.add_argument('--docx-txt', required=True)
    ap.add_argument('--prev')
    ap.add_argument('--out', required=True)
    ap.add_argument('--round', required=True)
    ap.add_argument('--date', default='')
    args = ap.parse_args()

    tex_lines = Path(args.tex).read_text().splitlines()
    docx_lines = Path(args.docx_txt).read_text().splitlines()
    rows = hits_for(tex_lines, 'tex') + hits_for(docx_lines, 'docx')

    prev = parse_prev(args.prev) if args.prev else {}

    def disposition(r):
        for k in (r['key'], (r['key'][0], r['key'][1], r['key'][2][:20])):
            if k in prev:
                return prev[k][0]
        return 'NEW - needs disposition'

    out = [f"# Timing-phrase-family sweep log — round {args.round} ({args.date})", '',
           LEGEND, '',
           'Family: {' + ', '.join(FAMILY) + '}.', '',
           '| src | line | phrase | context | disposition |',
           '|---|---|---|---|---|']
    tally = {}
    for r in rows:
        d = disposition(r)
        tally[d.split(' - ')[0]] = tally.get(d.split(' - ')[0], 0) + 1
        out.append(f"| {r['src']} | {r['line']} | {r['phrase']} | {r['context']} | {d} |")
    out += ['', f"Total: {len(rows)} rows. Tally (computed from table rows): {tally}.", '']
    Path(args.out).write_text('\n'.join(out))
    print(f"{len(rows)} rows -> {args.out}; tally {tally}")


if __name__ == '__main__':
    main()
