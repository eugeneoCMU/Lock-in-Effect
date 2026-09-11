# RECORD — Manuscript compression

**Status:** active execution record, opened 2026-09-10.

## Objective

Reduce the publication-facing package from 147 pages (99-page main paper plus 48-page online appendix) to approximately 38--42 pages of main paper and 12--15 pages of online appendix. Preserve the remaining research in a standalone technical and replication supplement.

## Governing rule

Keep the research; shorten the argument. A unique assumption, limitation, adverse result, or uncertainty qualification cannot be deleted to meet a page target. Relocation precedes deletion.

## Baseline

- Branch: `codex/manuscript-compression`
- Isolated worktree: `.worktrees/manuscript-compression`
- Source: commit `5a8514e`
- Canonical combined PDF: 147 pages
- Main-paper split: 99 pages
- Online-appendix split: 48 pages
- Baseline tests: 1,168 passed, 2 expected skips, 0 failures
- Canonical sources: `paper/final/paper_final_v1.tex` and `paper/final/paper_final_v1_long_abstract.tex`

## Destination policy

### Main paper

Retain the benchmark, primary hazard estimand, central/null decomposition, binding uncertainty, governing floor/form sensitivity, unique identification and transport limitations, decisive validation checks, cap arithmetic, both Danish anchors, policy costs, and concise conclusion.

### Online appendix

Retain referee-facing derivations and checks: benchmark/accounting construction, hazard parameters, binding inference, core floor/form sensitivity, composition mapping, Path A directional validation, and concise cross-design details.

### Technical and replication supplement

Relocate full ABM mechanics, run inventories, inference ladders, diagnostic grids, timing and Theil decompositions, seasonal and depth diagnostics, WAL and fifteen-year mechanics, superseded-result ledgers, and adjudication history.

## Deletion standard

A block may be deleted only when:

1. its complete canonical statement survives at a named location;
2. it merely narrates an exhibit cell by cell;
3. it is obsolete and the current replacement is named; or
4. it is internal workflow narration preserved in this record or the supplement.

Every deletion and relocation will be added to the batch log before final verification.

## Batch log

### Batch 0 — isolation and baseline

Created the isolated worktree and established a clean test baseline. No manuscript content changed.

### Batch 1 — disposition inventory

The machine-readable inventory is `paper/final/compression_manifest.json`. It covers every labeled section and subsection in the canonical source. Initial dispositions are editorial destinations, not permission to remove text before the supplement exists.

## Verification log

| Stage | Command | Result |
|---|---|---|
| Baseline | `python3 -m pytest tests/ -q` | 1,168 passed; 2 skipped; 26 warnings |
| Manifest red | `python3 -m pytest tests/test_manuscript_compression.py -q` | Expected failure: manifest absent |

### Batch 2 — supplement scaffold

Created and built the standalone supplement shell with stable destinations for
each relocation family. This is a scaffold, not a completed relocation: no
main-paper or appendix text may be removed until its substantive content has
been copied into the named supplement section and logged here.

| Stage | Command | Result |
|---|---|---|
| Supplement red | `python3 -m pytest tests/test_manuscript_compression.py -q` | Expected failure: supplement absent |
| Supplement structure | `python3 -m pytest tests/test_manuscript_compression.py -q` | 8 passed |
| Supplement TeX | `python3 tools/tex_validate.py paper/final/technical_replication_supplement.tex --bib paper/final/references.bib` | CLEAN |
| Supplement build | `tectonic paper/final/technical_replication_supplement.tex` | 3-page scaffold built successfully |

### Batch 3 — publication-facing introduction and literature review

Replaced the rendered introduction and literature review with focused versions
organized around the cap-relative benchmark, primary hazard decomposition,
binding uncertainty, governing limitations, and closest literatures. The full
pre-compression text and former headline table remain frozen in the embedded
technical archive. During this staged pass, the old blocks remain disabled in
the canonical TeX so legacy claim gates continue to expose every protected
literal; they must be physically removed after their gates are re-scoped to the
new article or supplement.

The rendered canonical document fell from 147 to 134 pages at this checkpoint.
Both front-section word-budget tests now pass, as do all ten compression tests
and TeX structural validation. The liveness suite passes through every gate it
can execute in the isolated worktree and then reaches the known missing local
Freddie panel; the missing licensed-derived parquet is an environment boundary,
not a manuscript failure.

### Batch 4 — compact ABM cross-design section

Replaced the rendered standalone ABM results apparatus with a compact section
that retains the production seed result, adverse monthly-path fit, failed
burnout variant, real-covariate threshold crossing, withdrawal of the paradigm
interpretation, composition sensitivity, and reason no ABM marginal is
reported. Detailed mechanics remain in the frozen supplement archive pending
their organized relocation.

The combined rendering fell from 134 to 131 pages. The compression, ABM-lead,
and paradigm-withdrawal test set passes (51 tests), TeX validation is clean,
and both manuscript variants received identical body edits.

### Batch 5 — hazard empirical spine

Replaced the rendered 35-page hazard apparatus with a compact statement of the
loan-level design, transported elasticity, turnover floor, central/null
estimand, binding floor uncertainty, calibration and form ranges, six governing
limitations, Fannie robustness scope, Path A exclusion, and interpretation.
The complete prior apparatus remains in the frozen supplement archive.

The combined rendering is 98 pages, with the online appendix opening on page
51: 50 pages of article and references plus 48 pages of appendix at this
intermediate checkpoint. Temporary compatibility labels keep later, not-yet-
rewritten sections buildable; they must be eliminated as those sections are
compressed and their references are rewritten.

### Batch 2a — frozen preservation archive

Copied the complete canonical pre-compression TeX source into
`technical_replication_archive.tex` and embedded it in the standalone technical
supplement with `docmute`. The resulting 152-page supplement now contains the
three-page destination guide followed by the entire 147-page source manuscript
(with pagination reflow from the wrapper). This is a preservation floor: later
organized relocations may improve the supplement, but no substantive source text
depends on the shortened manuscript for survival.

| Stage | Command | Result |
|---|---|---|
| Archive supplement build | `tectonic paper/final/technical_replication_supplement.tex` | Built successfully; 152 pages |
| Compression structure | `python3 -m pytest tests/test_manuscript_compression.py -q` | 8 passed |

### Batch 6 — discussion, robustness, and conclusion

Replaced the rendered discussion, policy analysis, robustness catalogue, and
conclusion with focused sections that retain the runoff-composition caveat,
cap-design feasibility conditions, Danish and cash-window counterfactuals,
central floor/form sensitivities, cross-design population distinction,
benchmark checks, headline quantities, binding interval, and governing
limitations. The complete prior sections remain preserved in the frozen
technical archive.

Both manuscript variants pass TeX structural validation and the 210-test
targeted manuscript suite. Fresh builds produce 66 pages for the canonical
version and 67 for the long-abstract version. The online appendix begins on
page 19 and page 20, respectively, so the article body is now compact while the
48-page appendix remains the next compression target. This is an intermediate
checkpoint, not a final length or content decision.

### Batch 7 — online-appendix triage

Replaced the rendered 48-page online appendix with a three-page synthesis that
retains the accounting benchmark, sample boundary, hazard estimand, floor and
functional-form uncertainty, ABM diagnostic role, composition and policy
mappings, timing concession, and Path A exclusion. The full former appendix is
preserved in the frozen technical supplement and remains disabled in the
canonical files only during this staged pass.

The canonical build is now 20 pages: 17 pages through references and a
three-page online appendix. This deliberately exposes the next editorial task:
restore the essential main-paper exhibits and enough reproducibility detail to
reach a defensible article-plus-appendix package, rather than padding toward the
page target. Both variants pass TeX structural validation, and the updated
compression-manifest suite passes all 11 tests.

### Batch 8 — essential publication exhibits and gate cleanup

Restored three decision-relevant exhibits to the active paper: the ABM-versus-
benchmark CPR path, the Path B elasticity calibration band, and the
vintage-by-coupon marginal decomposition. Removed temporary compatibility
labels from active prose and rewrote its remaining cross-references to semantic
section destinations, leaving the legacy table labels only in the preserved
source pending final physical cleanup.

The complete repository suite passes at this checkpoint: 1,179 tests passed,
2 skipped, with 26 existing dependency and numerical-fit warnings. TeX
structural validation remains clean.

### Batch 9 — physically compact submission sources

Added `paper_final_v1_submission.tex` and
`paper_final_v1_submission_long_abstract.tex` as physically compact,
publication-facing sources. They contain no disabled migration blocks and are
659 lines each; the compatibility canonical sources retain the historical
liveness corpus so the pre-existing claim gates continue to audit the frozen
record. The submission sources compile to 21 and 22 pages, respectively,
including a three-page online appendix. The standalone 152-page technical
supplement preserves the complete pre-compression manuscript.

A full-page contact-sheet review and enlarged inspection of the title page,
architecture, ABM path, hazard figures, references, and every appendix page
found no clipping, overlap, missing glyphs, or unreadable figures. That review
did catch and correct a malformed cash-window value and a duplicate appendix
pointer. The overfull ABM section heading was shortened; the rebuilt submission
has no overfull-box, undefined-reference, or duplicate-label warnings.
