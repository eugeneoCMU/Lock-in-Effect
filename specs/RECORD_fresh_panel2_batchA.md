# RECORD — Fresh-Panel-2 Batch A (text-only fixes), 2026-08-29

Source: fresh-eyes ARS panel review of `paper/final/paper_final_v1.tex` (2026-08-29, workflow
`wf_c9ee855c-174`; full package in `~/Downloads/paper_final_v1_fresh_panel_review.md`). Raw panel
decision Major Revision 69.4; adversarial verification refuted 3 of its 6 top findings (f2
post-hoc-adjudication, f5 form-fork, f6 elasticity-unpriced) and partialized 2 (f3, f4). One
finding survived in full and drives this batch.

## f1 (CONFIRMED CRITICAL) — censoring-flag propagation

The binding interval's lower endpoint is grid-censored at the committed floor grid's 6.0% end
(tab:ladder notes: "all three run below the +2.3 printed"; artifact `lower_pp_edge.floor_pct >
6.0`, already derived by gate #115), but the flag lived only in the ladder note while
`[+2.3, +9.1]` printed unflagged at ~10 sites, and the ladder body flagged "lower edge censored"
on the two-way rung only. This batch PROPAGATES the existing, artifact-derived disclosure; it
adds no new claim. (Distinct from the C-22 rejection, which correctly refused a DUPLICATE of the
note itself.)

Landed, both variants (abstract site canonical-only — the long-abstract variant's abstract is
archived pre-N1 text, gate #99 canonical-scoped):

- abstract: ", the lower endpoint censored at the committed floor grid's edge" (abstract 263→273
  words; letter + gate #101 anchors re-synced, "263" added to the stale-count battery)
- intro first use (.tex:44), II first use (:105), tab:headline uncertainty cell (:71),
  §IV.D (:308 and the :336 adjudication sentence), tab:uncertainty headline row (:443),
  §VII.F (:722), conclusion (:735)
- tab:ladder body: "lower edge censored" added to the CR3–BM and restricted-inversion rows
  (the two-way row already carried it; the censored set is exactly these three, per the artifact
  and gate #115's `n_censored == 3`)
- replication_appendices crosswalk row left unchanged (pointer table, not a characterization)

## f3 (PARTIAL) — stale convolution recommendation withdrawn

`.tex:308` recommended the convolved pair as "the interval a reader who wants one number for
sampling error should use"; the convolution was computed on the demoted Webb rung and never
re-derived under the adjudicated layer, so as printed it is anti-conservative (6.19pp wide,
narrower than the 6.83pp binding interval a re-derivation must exceed). The clause now labels
the convolution "a lower bound on the re-derived pair" and points the one-number reader at the
binding interval itself. Lockstep: `CONVOLVED_LINE_SPANS["one_number_reading"]` in
`tools/liveness_gates.py` (gate #105; `test_convolved_line_gate.py` imports the span, no
separate edit). A re-derivation of `layer_convolution` on the restricted rung remains an open
RUN item (spec-before-run, Eugene-only) — landing it would allow restoring a one-number
recommendation.

## SC-20 — fig5 vocabulary

`figures/fig5_cross_design.png` had already been regenerated with "pre-committed 50% threshold"
(uncommitted working-tree fix to `figures/make_figures.py`); the copy the manuscript actually
includes (`paper/final/fig5_cross_design.png`) still said "pre-registered". Copied the
regenerated PNG into `paper/final/` (verified visually before copying).

## Verification

Full pytest suite: 1163 passed, 1 skipped (pre-existing), first run after edits.
`tools/liveness_gates.py`: ALL GATES PASS. AST pin scan (4,107 literals from gates+tests) run
over every edited span BEFORE editing; raw-text grep for f-string-built literals likewise; all
pinned literals preserved as substrings by construction. Dollar-parity and brace-balance checks
pass on both variants. Insertion counts reconcile: 5/4 "lower endpoint censored"
(canonical/variant), 4/4 "lower edge censored", 1/1 convolution redirection.

## Deliberately NOT done here

- No grid extension past 6.0% and no `layer_convolution` re-derivation (RUN items, Eugene-only).
- No tab:assembly admission rule (authorial wording, drafted separately for approval).
- No action on the refuted findings (f2, f5, f6) or the panel's unverified P2 batch.
- No commit: the working tree already carried a large staged-but-uncommitted reorganization
  (paper/v18 → paper/final rename wave) that these edits must not be entangled with silently.
- PDF not rebuilt (no tectonic on PATH); page counts and the split boundary are unverified
  until the next build.
