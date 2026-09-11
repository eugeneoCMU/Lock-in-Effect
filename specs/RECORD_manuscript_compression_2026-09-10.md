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
