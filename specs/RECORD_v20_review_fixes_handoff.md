# HANDOFF — v20 review-fix round (2026-08-11)

Everything a fresh session needs to continue. Read this first; it is written to be
sufficient on its own.

---

## 1. Where the work is

| | |
|---|---|
| Branch | `claude/v20-review-fixes`, cut from `claude/v20-panel-revision` |
| Worktree | `.claude/worktrees/describe-work-general-audience-dfa391` |
| Remote | `origin/claude/v20-review-fixes` — **pushed, in sync** |
| Repo visibility | **PRIVATE** as of 2026-08-11 (was public) |
| State | 14 commits, working tree clean |
| Verification | **129 liveness gates PASS, 1139 tests pass, 1 skipped** |

Manuscript: `paper/v18/revised_paper_v18.tex` (canonical) and
`revised_paper_v18_long_abstract.tex` (archived variant — line-aligned, differs
**only at line 31**, its abstract). Appendices: `paper/v18/replication_appendices.tex`.

Run: `python3 tools/liveness_gates.py` and `python3 -m pytest tests/ -q`.

---

## 2. Rules this round operated under — keep them

1. **Never execute anything under `abm/` or `hazard/`.** Those are pre-registered
   simulation runs; executing one breaks spec-before-run. Reading their JSON
   artifacts is fine and is how every number here was checked.
2. **Never trust an agent's claim.** Sub-agents were used heavily and were wrong
   often enough to matter (see §6). Every returned edit was re-verified mechanically
   and, where it asserted a fact about the paper, against the source.
3. **Run the protected-span check BEFORE editing, not after the suite goes red.**
   Gates and tests assert ~644 literal text spans in the manuscript and 119 in the
   appendices. Extract them with `ast` over `tools/liveness_gates.py` + `tests/*.py`,
   keep only strings ≥16 chars that occur in the target file, and refuse any edit
   that would destroy one. Skipping this cost a full revert once.
4. **Both `.tex` variants must stay in sync** except line 31.

---

## 3. What changed (all landed and verified)

**Content**
- **Paradigm reading WITHDRAWN.** §VII.C's pre-committed 50% threshold fired (59.3%
  committed draw, 60.2% over fifty seeds undercutting on all fifty, 76.3% at book
  composition). The paper now withdraws it outright instead of hedging about
  attribution. Pointers in §IV's lead and the conclusion. Pinned by
  `tests/test_paradigm_withdrawal_gate.py` (18 tests). The weaker "cannot attribute"
  verdict deliberately still stands beside it — withdrawal is not negation.
- **§VII.D repaired**: it was still treating "the aggregate-level paradigm claim" as
  *corroborated* three subsections after VII.C withdrew it. Found by auditing all 31
  remaining "paradigm" mentions.
- **§VII.A / Table 8 spec fork reconciled** — see §4, this is the big gotcha.
- **berger2026 qualified** at the conclusion, the Limitations block and the abstract
  ("unrefereed working paper, draft July 2026"), with the 1bp→20bp inter-draft drift
  recorded. lesniewski2026 verified still a preprint (arXiv v3, 19 Mar 2026).
- **Unsourced magnitude retired** — "hundreds of billions in unrecognized losses" had
  no source; sentence scoped to the mechanism.
- **Abstract**: 91.3% now names its basis in the same sentence; the "up to roughly
  half (23–80%)" contradiction fixed. 242 → 263 words; the response letter and two
  test literals track that count and must be updated together.
- **Negative R² defense** consolidated into one sentence at first mention.
- **Run index**: `tab:runindex` in `replication_appendices.tex` had fallen behind —
  21 of 68 cited runs were indexed nowhere. Added, coverage now 68/68, plus eight
  corrections to pre-existing rows (one asserted a reading the paper had withdrawn).
- 7 bibliography entries normalized to initials.

**Readability** (main text = lines before `\appendix`; em-dashes counted as
exact `---` sequences — the .tex has no literal U+2014)

| | before | after |
|---|---|---|
| em-dashes | 445 | 120 |
| "rather than" | 180 | 55 |
| sentences > 62 words | 161 | 10 |
| mean sentence length | 44.4 | 27.8 |
| sentences | 770 | 1253 |

Plus 17 `\subsubsection` navigation headings in §V.E, §V.B, §VII.F, §VI.D, and
`tools/editions/tex2md.py` taught the third heading level (WANT 42 → 59).

---

## 4. GOTCHAS — read before touching numbers

**The ABM spec fork.** Two production-adjacent runs, ~0.9pp apart. This is not an
error and must not be "fixed":

- `run-2026-07-04-15yr-foldin` (structural-only 15yr fold-in) = **the paper's
  production headline**. $90.98B frozen / 11.897%, seed mean $103.68B / 13.557%,
  r₀ −0.318, raw R² −6.984, CPR 11.677%. Every figure in Table 8's ABM row is this
  run. §IV.A calls it production; tab:danish note b names "the \$91.0 billion
  production headline".
- `run-2026-07-05-berger` == `run-2026-07-05-native15yr` (native-15yr behavioral
  gate). $84.51B / 11.050%, r₀ −0.315, raw R² −7.086, CPR 11.761%. This is what
  `latest_run_manifest.json` points at, which is why it *looks* like HEAD.

`production_scale_test` ran the **native gate**, so its 12.66% is the
native-gate/fold-in offset its own `R3_cross_spec_reference` block says it exists to
expose. §VII.A now states this; Table 8 was correct all along.

**The run index already existed.** Do not build a second one. `tab:runindex` and
`tab:crosswalk` live in `replication_appendices.tex`. Tests such as
`test_the_runindex_row_is_undeletable` assert a tag appears **exactly twice** — prose
citation plus index row — reading manuscript and appendices *concatenated*. An
attempt to convert 116 inline citations to `run~Rn` pointers broke 6 gates and 40
tests and was reverted whole.

**No TeX on this machine.** No tectonic/pdflatex/MacTeX/docker/brew. Nothing in this
round is compiled. Installing tectonic would unblock the paper PDF and let the
poster's LaTeX be verified.

**The archived long-abstract variant** keeps its own older abstract by design — the
gates describe it as an archive that must not be rewritten to suit a new pin.

---

## 5. Still open

1. **Build the PDF.** Nothing is compiled. Expect pagination to have moved a lot
   (171 sentence splits + 17 new headings): the 1–89 / 90–130 two-PDF split point
   needs recutting, and the md/txt editions need the `.aux` a build produces.
2. **`replication_appendices.tex` says "the replication package is the public
   repository at <url>"** — false while the repo is private. Make it true again
   before submission, or reword.
3. **The conference application answer** still says "The transmission ran through the
   loans, not the households", contradicting the retraction. It is **not in the
   repo** — it was submitted to NRCP (accepted 20 July 2026) and Eugene holds it
   elsewhere. Nothing to edit locally; the live surface is the poster.
4. **32 of 44 local branches remain unpushed.** Only `claude/v20-review-fixes` is
   backed up. Private now, so pushing the rest is safe.
5. Ten main-text sentences remain over 62 words: two are direct quotations
   (na2024, perli2024), one is a post-equation notation gloss, the rest cost meaning
   to split. 55 "rather than" remain, 34 inside gate-pinned spans.

---

## 6. The poster (separate deliverable)

`~/Desktop/nrcp-poster/` — NRCP 2026, Penn, **October 2–3**, poster session,
**24in × 36in**. Self-contained; nothing in the repo depends on it.

| file | role |
|---|---|
| `poster_content.py` | **the only file to edit.** Plain sentences, no markup |
| `build_poster.py` | → `nrcp_poster.html` (self-contained, figures inlined base64) |
| `build_poster_tex.py` | → `nrcp_poster.tex` + `figures/` (pdflatex, run twice) |

One content file feeds both renderers. `*stars*` make a highlight; typography
(em dashes, en-dashed ranges, ×, R², minus signs) is automatic from plain ASCII.

Eleven sections tagged with five standard labels only — Introduction, Methods,
Results, Discussion, Limitations. No section numbers. No bold in the prose (kept
only in figure-caption lead-ins and the byline).

**Poster-specific gotchas**
- The HTML is sized in `cqw` container units against `aspect-ratio: 24/36`, so it
  prints identically at any render size. Verify layout by serving it locally and
  measuring column heights in a browser — overflow is invisible in the source and
  bit twice.
- Output is forced to pure ASCII entities; without that every em dash renders as
  `â€"` because the artifact wrapper owns `<head>`.
- Figure PNGs are copied to hyphenated names for LaTeX — underscores in
  `\includegraphics` are a compile error.
- `build_poster_tex.py` self-checks braces, `\begin`/`\end` balance, and **digits in
  defined command names** (`\newcommand{\ftw0}` is a hard error; the guard is
  mutation-tested).
- The LaTeX is **uncompiled**. Four errors were found by inspection and fixed
  (`\ftw0`, filename underscores, `\statnum\color{...}` arity, an overfull stat box).
  Vertical fit is unverified; if the page overflows, lower `\bodysize` from
  `\fontsize{23}{29}`.
- Poster figures come from the repo's `figures/`, which regenerates byte-identically
  from committed artifacts. Eugene's old `~/Desktop/poster images/` exports were a
  superseded palette; current set is Okabe-Ito colourblind-safe (blue = loan-level
  survival, vermillion = household choice, purple = cross-design). Superseded copies
  preserved in `poster images/superseded-2026-07-25/`.

---

## 7. Sub-agent record

Four workflows, ~180 agents, ~13.5M subagent tokens. Draft-then-adversarially-verify
throughout; every survivor re-checked mechanically before landing.

- em-dash pass: 289 drafted, 66 rejected, 223 applied
- "rather than" pass: 141 sites classified, 137 accepted, 3 rejected, 5 justified keeps
- long-sentence pass: 177 drafted, 6 rejected, 171 applied
- run-index glosses: 68 written; **9 of 10 checkers died on a usage limit**, so the
  glosses shipped on my own verification, and the later re-run found a
  build-breaking defect in them (unescaped `%`). Verification is not optional.

Weekly agent capacity resets ~9pm Pacific; this session exhausted and then regained it.
