# RECORD — full-tree review and remediation, 2026-09-05/06

Executed against HEAD `1fc54d4` under the author instruction "fix all", from the
plan in `specs/PLAN_review_2026-09-05.md` (gitignored). No model run, no artifact
regenerated: every replacement literal here was read out of a committed artifact
or recomputed from one. Pushes remain Eugene-only and nothing was pushed.

## What the review was

Read-only sweep of the whole tree — manuscript by section, letter, replication
appendices, docs, gates, tests, figures, bibliography, repo hygiene, records, the
alt edition and the roadmap — by 22 finder agents, each finding then put to two
lens-diverse adversarial verifiers (textual/materiality, evidence/fix-safety).
206 raw findings, 186 after dedup, 106 survived both verifiers, 17 contested, 1
refuted, 62 unverified because verifier agents stalled. The orchestrator
re-derived every item before it was acted on; several agent claims did not
survive that and are recorded as refuted below.

## The build layer, which had never been checked

The two Batch-A/B records say the PDF could not be rebuilt, "no tectonic on
PATH". A working **tectonic 0.15.0** is at `~/Downloads/texbuild/tectonic`; it is
merely off `PATH`. Building it exposed a defect class the gate suite is
structurally blind to.

`tools/render_gate.py` tests each glyph's **origin** against the page box. A
table row that begins inside the text block and runs off the right-hand edge has
every origin legal, so the origin test passes it. Five tables were clipped by the
paper's edge in a build the gate called clean:

| Table | Page | Symptom |
|---|---|---|
| `tab:assembly` | 51 | float too large by 52pt; last row printed over the footer |
| `tab:params` | 114 | provenance column clipped off the sheet |
| `tab:ladder` | 137 | Status column clipped off the sheet **on the binding-layer row** |
| `tab:seasonalfloor` | 145 | caption, notes and last column past the margin |
| `tab:crossdesign` | 76 | last column at the sheet edge |

Fixed by converting `tab:assembly` to a `longtable` (it now breaks across pages
like `tab:headline`) and giving the other four explicit column widths. No table's
structure was pinned by any gate or test, verified by grep before editing.

**The gate hole is now closed.** `render_gate.py` gained `overrun()`, which reads
span bounding boxes via PyMuPDF and fails when text extends past the sheet;
`[SKIP]` rather than silent pass when PyMuPDF is absent, because a check that
goes quiet when its dependency is missing is how the first one failed. Run
against the pre-fix build it flags exactly pages 76, 114, 137 and 145 while the
origin check reports PASS on the same file. Three tests pin it, one of them
asserting that the origin check misses the page the extent check catches.

Two further latent defects surfaced only because a build finally existed:

- The **split PDFs** were "cut BY HAND after every rebuild and nothing verified
  it" (the gate's own comment). `tools/split_pdf.py` now finds the boundary from
  the text — the first page opening the "Online Appendix" banner — so the cut
  survives reflow, which a typed page number does not. Currently main 1–99 (99pp)
  + appendix 100–147 (48pp).
- The **variant-length check asserted equal page counts** for the canonical and
  the long-abstract edition. The archived long abstract runs 629 words against
  263, which costs exactly one page, so the check could never have passed. It had
  never run to discover that. Relaxed to one page of slack, with the reasoning in
  the source: body drift is already caught upstream by the CI line-31 diff and
  four equal-line-count tests, so what remains here is the abstract's own
  overflow.

Build now: canonical **147pp**, variant 148pp, render gate ALL CHECKS PASS, no
span past the sheet on any page of any of the four PDFs.

## Manuscript corrections

74 counted replacements, each applied to both variants (line 31 excepted, which
is canonical-only), each dry-run first and aborted on any count mismatch, with a
gate/test pin scan over every literal touched and its replacement. The editions
remain byte-identical apart from line 31; the abstract remains 263 words.

The substantive ones:

- **The `:336` replicate claim, which no longer needed a run.** It read "all but
  one above the $+8.7$ upper edge of the binding interval". +8.7 is the demoted
  Webb rung's edge; the binding edge has been +9.1 since N1. Batch B recorded this
  as needing the `h0_reanchor` replicate set — but that set is committed:
  `hazard/data/h0_reanchor_results.json` → `per_replicate`, 107 usable. 106 of 107
  lie above +8.7; **93 of 107 lie above +9.1**. The sentence now names both edges
  and both counts, and gate #129 recomputes them.
- **The midpoint placement was false.** "The headline sits just below its
  midpoint" was re-checked at N1's [+2.3, +9.1] (midpoint 5.70) and not re-checked
  when Batch B moved the lower endpoint. The midpoint is now 5.49 and the +5.57
  headline sits **above** it.
- **`tab:uncertainty`'s note still named the demoted construction** as the binding
  layer and described it as the unrestricted wild bootstrap. The binding layer is
  the restricted wild-cluster inversion; the unrestricted description now attaches
  to the Webb/Rademacher rungs, and the inversion's own construction (401 grid
  nulls on restricted residuals) is stated.
- **Four legs listed as "run in window only"** have committed off-window re-runs
  cited in the same section.
- **The selection rule's metric was unstated**, which made it read as
  self-contradicting: CR2 at Bell–McCaffrey prints narrower than the rung the rule
  selects. The rule ranks on the simulation's mean interval width in floor units
  (`fewcluster_coverage_results.json`: 0.001397 against 0.002318), where the
  ordering is the other way. Stated once at the rule and once in the ladder note.
- **Path A's Theil diagnostics contradicted the table in the same appendix**
  (26.5/63.0 prose against 30.6/58.8 in `tab:theil`). The table is on the corrected
  note-rate-WAC basis; the prose and `tab:pathadiag` now match it.
- Also: the off-window leg mislabelled 2017–2019 where the headline read is the
  2018 leg; the retracted within-stratum interval printed unlabelled beside live
  sampling intervals; 6.5% called the band's "midpoint" when the midpoint is 6.6%;
  the Definitions paragraph denying the headline marginal its own exception; the
  "production headline" label attached to the frozen seed-42 draw at three sites;
  the fig3 caption attributing all seven stage levels to run manifests when four
  are pre-manifest; "pre-registered" used in the sense the paper reserves; the
  hull's +3.5 lower edge unsourced in its own sentence; four self-referencing
  appendix cross-references; and a forward-looking hedge about a freeze that had
  already happened.

## Letter, appendices, figures, docs

- **Letter**: the supersession paragraph said the figures it retires are "above"
  when two of three sit below it; the three superseded figures are now tagged in
  place rather than deleted. A mutation test then caught that one tag had
  duplicated a pinned literal, which defeated gate #101's deletion check — the tag
  was re-worded rather than the test weakened.
- **Replication appendices**: `\externaldocument` still pointed at the manuscript
  deleted in the v18→final rename, so every cross-reference resolved wrong; the run
  index had no row for either August run and described the superseded convolution
  as current.
- **Figures**: fig4 still annotated the superseded ~1bp Berger anchor against the
  manuscript's ~20bp; fig1, fig2, fig3 and fig4 carried hard-coded section pointers
  that no longer resolve; fig6's axis named a quantity the caption calls δ; fig3's
  bar label called the frozen draw the headline; fig7 attributed Path A to the 75k
  sample. Regenerated from committed JSON only — no model run.
- **Docs**: `TECHNICAL.md` stopped at §55 and had a duplicate "§46" heading
  colliding with the real one; it gains §53a (renumbered) and §56 narrating N1,
  Batch A/B and the Path A standardization. `PAPER_ROADMAP.md` §11 still ended at
  [+2.3, +9.1]. README's gate count said 33 where it is 129, and both README and CI
  carried a fresh-clone test count stale by two batches — replaced with wording
  that hard-codes no count, since the count moves every round. Five superseded
  planning documents gained dated banners.

## New gates (all mutation-proved: red under perturbation, hash-verified restore)

| Gate | What it pins |
|---|---|
| #127 | the four `tab:oosfloor` grid-extension rows, each row rebuilt whole from the artifact so a floor paired with the wrong marginal cannot pass |
| #128 | "pre-registered" appears only inside the reservation sentence |
| #129 | the `:336` replicate counts, recomputed from `h0_reanchor_results.json` |

`ZERO_COUNT` also gained the intervals FP2 Batch B retired. Nothing had guarded
them: the batch re-printed every site by hand and verified by grep, and the grep
missed `:105`, caught a round later in `9f13504`. Deliberately **not** listed:
`$[+2.80, +8.99]$` — zero in both manuscript variants, but the run index and the
letter print it as the superseded pair they record, and this list is scanned over
the appendices too.

## Record corrections

`RECORD_fresh_panel2_batchB.md` gains a dated addendum (history not rewritten):
its "31 committed uncensored endpoints" is 30 in the artifact (31 is the cluster
count); "13/13 rows covered" against a 19-row `tab:assembly`; the prose/bracket
instance counts read as line counts; and "zero old-literal stragglers" missed
`:105`. `SPEC_fresh_panel2_B1` gains a matching amendment-log entry, line 84 left
verbatim as frozen pre-run text.

## Verification

| Check | Result |
|---|---|
| `pytest tests/` | **1173 passed, 0 skipped** (was 1166 + 1 skipped; the render-gate tests now run against a real build, plus 3 new) |
| `tools/liveness_gates.py` | **ALL GATES PASS** |
| `tools/render_gate.py` | **ALL RENDER CHECKS PASS** incl. the new extent check |
| `tools/tex_validate.py` | CLEAN on both variants and the letter |
| Editions | byte-identical apart from line 31; abstract 263 words |
| Build | canonical 147pp, variant 148pp, split 99 + 48 |

## Refuted during verification — do not re-raise

- `tab:bootstrap`'s mean/median cells "have no committed source" — `hazard/data/hazard_bootstrap_draws.csv` is tracked and is the source.
- The −0.438 vs −0.378 Path A correlation "conflict" — `tab:estimators` prints the peak-lag r, the text the lag-0 r; the artifact carries both and `test_printed_values_reconcile.py` pins the pair.
- "any of 150 starts" — 50 starts × 3 legs; correct as written.
- "The replication package is the public repository" — true; `gh repo view` reports PUBLIC, closing the handoff's private-visibility item.
- The `:297` timing correlations "appear in no committed artifact" — `rate_timing_scan_results.json` carries all five.
- `:810`'s "convexity-neutral below" — three sites exist, one below; no edit.

## Left for the author

Posture and scope, untouched: whether to push; the long-abstract variant, whose
abstract still names the Webb interval as binding while its body prints the
restricted inversion; the frozen `paper/alt_lead_version/` edition (banner added,
keep/re-sync/retire undecided); the assembly rule's "basis" term against the
paper's own basis-invariance claims; the panel's editorial P0s (abstract length,
main-text length, framing order, the page-long paragraphs at `:144`, `:336`,
`:594`); and the runs in `PLAN_review_2026-09-05.md` §D, chiefly the ten-seed
seed-noise rerun, whose layer has no committed artifact.
