# Handoff — Round 21 (adversarial panel referee round) — 2026-07-20

Repo: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect`
Branch: `panel-revision-2026-07-18` — all round-21 work committed locally, **UNPUSHED** (public repo; push is Eugene's call).
Manuscript: `paper/v18/revised_paper_v18.tex` (106pp; grew from 99 — compression is optional, per Eugene).
Gates: `python3 tools/liveness_gates.py` → **80 gates ALL PASS** (72 + new #69–#76).
Tests: `python3 -m pytest tests/` → **295 pass** (hedge-gate mutation tests re-keyed to the new abstract sentence).
Build: `~/Downloads/texbuild/tectonic -X compile revised_paper_v18.tex --outdir build_r21 --keep-logs` → 0 undefined refs/cites.

## What this round was

A six-reviewer adversarial panel review (55 verified findings) of the built PDF, then execution
of the remediation plan. Every new run followed the spec-before-run convention (spec commit
precedes result commit; parity gates replay committed artifacts bit-exactly).

## New pre-committed runs, all executed, all parity gates PASS

| Run (hazard/) | Result | Consequence in tex |
|---|---|---|
| `floor_form_offwindow.py` | Additive-form marginal at off-window anchors: **+11.22/+11.21/+11.19pp** (vs +11.2485 at 4%). T1: the +9.2→+5.6 demotion is entirely max-form censoring. Designated form-conditional hull **[+3.89, +13.10]pp** | abstract, Table 1, Table 8, V.E, VII.I (gate #69) |
| `concave_marginal.py` | Concave marginal **+7.87pp** @4% (vs +9.20), **+5.06** @4.991 (vs +5.57). T1: transform IS load-bearing for the marginal | "not load-bearing" scoped to level; Tables 1/8 (gate #70) |
| `danish_offwindow_floor.py` | Rule-only gap at headline floor: **+$28.20B** (vs +$61.19B in-sample); ratio to marginal 0.662 | abstract dual-label; VI.C; conclusion (gate #71) |
| `ginnie_overlay_offwindow.py` | Overlay pair at headline floor: **83.95/79.51/+4.44pp**; marginal correction = pure conventional-share scaling (0.7975×), series-independent | V.B; Tables 1/8 (gate #72) |
| `floor_uncertainty.py` | Floor-read cluster bootstrap: off-window marginal 95% CI **[+2.97, +8.02]pp** — the BINDING layer (31 clusters!, n=137). Age-standardized floor **5.51%** (84% imputed) → band **open below +4.3** | VII.I sampling paragraph; Table 8 sampling cell corrected; abstract (gate #73) |
| `patha_sign_test.py` | **T3**: H0: β_g≤0 not rejected under any bias-respecting construction — BCa p **0.093** (stratum, 296-refit jackknife) / **0.412** (temporal); permutation p **0.241**. In-sample sign claim withdrawn; elasticity's evidential basis = external literature alone | V.B/V.D/V.F/Table 6 note rewritten; "sign-triangulated" retired to ZERO_COUNT (gate #74) |

## Tex work landed (commits `440e2e1..`)

- **Batch A** (claims scoping): V.F mechanism cap; VI residual sized at headline floor; VI.C/VIII
  household-choice conditionality; VI.A fragility attribution (0.6 of ~6 WAL-years); V.B
  two-estimands statement (+$20.9B window component, +$63.5B matched depth); holdout →
  input-stability check at all 4 sites; "no outcome-holdout months exist anywhere… without exception".
- **Batch B**: abstract allocation range (quarter-to-half), form-conditional headline, Danish
  dual-label; V.E/VII.I additive-off-window prose; conclusion 23–49%/38–80%.
- **Batch C**: exponential (not log-normal) mobility desire + ledger item; Section IV opening
  qualifiers inline; Table 1 ABM calibration-not-seed-noise; floor "involuntary" label scoped
  (total-turnover premise does the anchor/max-form work); TBA recast (due-on-sale/Garn–St.
  Germain, FHA/VA carve-out); Fannie agreement = pipeline determinism; +gao2017, +campbell2013.
- **Batch D**: floor_uncertainty into VII.I/Table 8/abstract; $33.31-vs-$32.6 wedge reconciled.
- **Phase-4 partial**: VII opening corrected (names the two result-changing checks; undershoot
  on shared basis); definitions block at end of Section I; Table 14 caption marks the 6% row
  as a disqualified-anchor grid point.
- **Mechanical minors** (first commit `440e2e1`): 10 copyedit fixes, all re-verified against tex.

## Open items (in priority order)

1. ~~R8 verdict~~ DONE (T3 applied, gate #74, commit `74774f6`).
2. ~~ABM spec appendix~~ DONE (`app:abmspec` inserted with code-line pins; three III.B
   code-vs-manuscript discrepancies fixed: full-term replacement loan, 240-month penalty
   switch referenced, annualized-intensity parenthetical; commit `63a009a`). Residual from its
   discrepancy list: the "nearly tripling" phrase at the loss-aversion recalibration (III.C)
   compares against the historical ~12,500 anchor, not the frozen 43,883 — verify the base
   before that phrase survives another round.
3. ~~R7~~ DONE (T1: reweighting to SOMA composition RAISES the recalibrated variant
   59.3→76.3% (re-draw 70.6), lowers frozen 20.9→12.6 (re-draw 36.0); undercut verdict
   survives strengthened; gate #76; commits `abb..`/`39ecb1b`).
4. ~~R9~~ DONE (T5 residual branch: realized cumulative gap gradient +4.20pp, CI
   [+3.59,+4.66], perm p 0.005 — signed and significant but 4.5× the implied +0.94, so
   confound-signature, not corroboration; power 0.68; no verb change; gate #75).
   Diagnosis of the excess gradient (credit/refi decomposition of the shallow buckets) is
   a natural future run if anyone presses on it.
5. **R10 small batch**: per-seed floor CPR disclosure (seed-loop position of the recalibration);
   β_B interaction bound; settlement-months benchmark variant; DTI non-monotonicity
   decomposition; production-spec scale rerun (or soften VIII.A "resolves").
6. **Compression** (eic S2): 102pp → target 55–65pp. One-canonical-location dedup (κ grid told
   4×, allocation analysis 4×, no-timing concession 10+×), VII.J to a half-page, ABM demoted to
   motivating diagnostic, abstract to ~200 words. The concision-round handoff
   (`HANDOFF_concision_round.md`) still applies — its gate-pinned-phrase warnings especially.
   Round 21 deliberately traded pages for correctness; the compression must not trade back.

## Constraints (unchanged from the concision handoff, plus)

- Fix the .tex, not the gate — except where a referee-justified revision changes pinned content;
  then tex+gates+tests move in ONE commit (this round did it for: kernel sentence EXACTLY_ONE,
  gate #68 span, hedge mutation tests).
- New gates #69–#73 pin the five new artifacts bit-exactly; if you re-run those scripts the
  artifacts must reproduce (all are deterministic, seed 42).
- The four commit-hash pre-commitment citations in the manuscript are untouched.
- `paper/**/*.tex`/`*.bib` tracked; derived files ignored. Repo is PUBLIC — no pushes.

Also removed this session (post-handoff): all nine reviewer-reactive framings (zero 'referee' mentions remain; commit `1c9d629`).
