# Handoff — Round 21 (adversarial panel referee round) — 2026-07-20

Repo: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect`
Branch: `panel-revision-2026-07-18` — all round-21 work committed locally, **UNPUSHED** (public repo; push is Eugene's call).
Manuscript: `paper/v18/revised_paper_v18.tex` (102pp; grew from 99 — compression is still open, see below).
Gates: `python3 tools/liveness_gates.py` → **77 gates ALL PASS** (72 + new #69–#73).
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
| `patha_sign_test.py` | **RUNNING at handoff time** (background; BCa/BC + 200-perm test of H0: β_g≤0). BC-only p-values from committed draws: stratum 0.091, temporal 0.404 — expect T2/T3 | on completion: downgrade "sign stability"/"sign-triangulated" per its ex-ante T-branches; add gate #74 |

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

1. **R8 verdict** (`patha_sign_test.py`, running): apply its ex-ante T-branch to the tex
   ("sign-triangulated by two in-sample estimates" p.33-equivalent and "sign stability" Table 6
   note / V.F), then pin gate #74. Check `hazard/data/patha_sign_test_results.json`.
2. **ABM spec appendix** (MF-10): a drafting agent was producing `app:abmspec` LaTeX (decision
   equation, parameter table w/ units, order of operations) — verify its file:line claims
   against `abm/abm_lockin_simulation.py` before inserting; add its discrepancy list to the
   ledger if any.
3. **R7** (cross-design composition): rerun/reweight VII.D variants to the SOMA coupon/vintage
   mix (the VII.F analogue) or quantify the composition share of 11.9→59.3; fix the "isolates"
   sentence (currently only hedged, not quantified).
4. **R9** (episode confrontation): cumulative cross-cohort gap-gradient test vs realized speeds
   + power analysis of β₁=0.069 detectability; decides whether the abstract's re-anchored verb
   can strengthen back from "Re-anchoring…puts".
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
