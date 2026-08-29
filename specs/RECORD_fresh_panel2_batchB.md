# RECORD — Fresh-Panel-2 Batch B (grid extension + convolution re-derivation), 2026-08-29

Executed per `specs/PLAN_fresh_panel2_batchB.md` (gitignored, pre-decision) under the
author instruction "work on it???" (this chat), which adopted both SPECs with every
recommended option. The tracked, frozen objects:
`SPEC_fresh_panel2_B1_grid_extension_2026-08-29.md` (adopted with A2 7.00-knot, A3
two-anchor bands, A4 R1 decensor, A5 box-edge sentence as drafted, A6 provenance-marked
tab:oosfloor rows) and `SPEC_fresh_panel2_B2_convolution_rederivation_2026-08-29.md`
(construction α; pre-run amendment FP2-B2-A1, nested-CI quantile rule). Both committed
before their runs.

## Phase 0 — commits

The three-layer tree was landed as: (1) the v18→final reorg as staged; (2) Batch A +
the accumulated working state (path re-syncs, prior round mods), message enumerating
the layers; (3) the adopted specs. All local, nothing pushed.

## B1 — floor-grid extension (run `floor_grid_extension`, artifact frozen)

Rows (paired legs, δ=6.5 central / β₁=0 null): 6.25% → +1.7326pp/$13.25B,
6.50% → +1.2836/$9.82B, 6.75% → +0.9272/$7.09B, 7.00% → +0.6534/$5.00B.
Gates: **P1** 6.0% parity pair bit-exact against the committed row (every numeric
field). **P2** monotone, positive. **P3** extended PCHIP at 6.91% within $0.0050B of
the independent committed engine read (tolerance $0.69B). **P4** pieces below 5.0%
bit-invariant (probe incl. the binding upper endpoint 4.0335 → +9.109324, unchanged);
max movement over the 31 committed uncensored (5,6)-interval endpoints 0.0343pp
(bound 0.0902). **All five ex-ante prediction bands HIT** (two-way +2.2169,
CR3–BM +2.0093, month-Rademacher +1.9536, restricted +1.8710, R1 wcr +1.0270).

v2/v3 regenerated under `FloorMapping(extended=True)` (opt-in; default bit-preserving
for all other consumers). v2's SMM and floor-unit CIs bit-identical (N1 provably not
reopened); **binding interval decensors to [+1.8710, +9.1093]pp / [$14.31B, $69.66B]**;
zero truncation remains anywhere except v3's deliberate 7.5% probe (now clamping at
7.0). v2's P2 percentile parity re-scoped to the committed map; P4 replay re-scoped to
floor-unit equality (mapped leaves are the adopted map's, gated in the extension
artifact); v3's sha pins re-pinned to the amended v2/mdr and regenerated v2 artifact.

## B2 — convolution re-derived on the restricted rung (run
`layer_convolution_restricted`, supersedes `layer_convolution_results.json`; the C2
artifact survives in git history)

Floor layer = nested-CI confidence distribution of the committed restricted Webb
inversion (A1 rule), tied bit-exactly to the committed retained set (247) and CI
endpoints (gate Q2). **Convolved primary [+1.7081, +9.3831]pp / [$13.06B, $71.76B]**,
width 7.675pp > binding 7.238pp (Q3), truncation count 0 → the Batch-A "lower bound on
the re-derived pair" label RETIRES and the one-number recommendation returns, pointing
at the re-derived pair. **All three ex-ante prediction bands MISSED** (lower +1.71 vs
[1.2,1.7]; upper +9.38 vs [9.6,10.0]; width 7.68 vs [8.3,8.7]) — each in the
conservative direction (the convolution moved less off the binding interval than
predicted); recorded as misses in the artifact and in the verdict appendix.

## Phase 3 — landing (both variants; abstract canonical-only per gate #99)

- Binding interval re-printed at every site: 9 prose + 4 bracket instances per file
  ($+1.9$ to $+9.1$ / $[+1.9, +9.1]$), zero old-literal stragglers (grep-verified).
- All nine Batch-A censoring flags OUT (abstract, :44, :71, :105, :308, :336, :443,
  :722, :735); the seven other-sense "censored" uses untouched.
- Ladder fully re-printed from the regenerated artifacts, including four
  rounding-boundary moves on uncensored rungs (CR1 t +3.2→+3.1, CR2 t +3.0→+2.9,
  CR3 t and CR1–BM +2.8→+2.7, Webb +2.9→+2.8; the CR1-BM/CR3 printed tie persists,
  unrounded literals updated); decensored rows CR3–BM +2.0/+9.6, restricted +1.9/+9.1,
  two-way +2.2/+9.3 ("both clustering dimensions at once" replaces the censor flag).
- Ladder note converted from censoring adjudication to extension record, E4-miss
  history preserved in past tense; E3 widths re-derived (5.23/5.36).
- Box-edge sentence landed VERBATIM as pre-committed in SPEC B1 §5.4 (before the
  number existed), at the :336 assembly site.
- Convolution sites: :308 redirect replaced by the returned one-number
  recommendation; tab:uncertainty pair, run tag, comonotone bound ($9.67$pp), and the
  0.32× width ratio updated.
- Flow terms: $0.42 → $0.35 to $1.66 billion per month (derived; gate #111).
- tab:oosfloor: four provenance-marked grid-extension rows + note d; the calibration
  box's committed grid and its +2.1/+13.2 literals untouched everywhere (structural:
  the extension is δ=6.5-only).
- Abstract 273 → 263 words (the censoring phrase out; nothing else moved); letter
  narrative + changes-section updated ("Two later changes supersede…"), gate #101 and
  its test anchors re-synced (263 live, 273 joins the stale-count battery).
- replication_appendices: crosswalk row re-printed; spec count 25 → 27
  (Twenty-seven); two verdict-appendix rows added (B1 enforced/hits, B2
  enforced/misses-reported).
- A4 admission rule landed at the assembly site, row-by-row verified first: the
  b5 joint cell IS a row, so the joint-cell clause was added, plus a directional
  clause for the gradient exhibit (13/13 rows covered).
- Gates re-synced in lockstep: #125 auto-tied; #115 rewritten to the zero-censoring
  world (decensored-set identity vs printed-wider, widest = CR3–BM, month-Rademacher
  past-edge scope, extension-artifact-derived literals); #107 Webb mapped-pin
  re-derived (floor-unit pins unchanged); #105 spans + artifact check on the B2
  schema; #111 call at (1.9, 9.1). Tests: month_twoway (0-censored semantics, two
  new perturbation traces), floor_ladder (floor-unit invariance + bounded pp
  movement), cap_monthly_units, headline_posture, response_letter, spec_count.

## Verification

Full pytest: **1166 passed, 1 skipped** (pre-existing). `tools/liveness_gates.py`:
**ALL GATES PASS**. `tools/tex_validate.py`: CLEAN on both manuscript variants
(appendices carry the pre-existing 41 cross-file label refs, by design). Every tex
edit applied via counted replacement (abort on count mismatch); pin scan run over
gates+tests before each edit family.

## Flagged, deliberately NOT done here

- **Pre-existing stale claim at :336** (predates this batch, out of spec scope):
  "all but one above the $+8.7$ upper edge of the binding interval quoted below" —
  +8.7 was the Webb-era upper edge; the binding upper edge has been +9.1 since N1.
  Re-deriving "all but one" needs the h0_reanchor replicate set. Eugene decision.
- The panel's unverified P2 batch (citations, Path A language, fig4/fig6, paragraph
  breaks) — verify-then-fix, not started.
- PDF not rebuilt: no tectonic/pdflatex on PATH. Page counts, the split boundary,
  and the off-sheet check are unverified until the next build.
- Nothing pushed (repo convention: pushes are Eugene-only).
- A4/A5 wording landed under the blanket "work on it" adoption; both are
  Eugene-revisable words, and the verdict-appendix convention preserves history
  either way.
