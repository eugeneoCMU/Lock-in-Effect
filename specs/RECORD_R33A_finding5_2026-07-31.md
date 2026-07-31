# RECORD — R33-A landed; finding 5 adjudicated and landed — 2026-07-31

Applied on `origin/main` tip `b493d78` (R30). The R32 continuation branch was never
pushed, so this landing targets the published main manuscript. Every number below was
re-verified against the committed artifacts on this checkout before the edit.

## R33-A — runoff-error basis (MAJOR, WORDING+CHECK) — **LANDED**

**Defect.** `tab:bases`'s cumulative-runoff-error column was standalone-only. §VII.D
(`sec:robustness-hybrid`) says the shared basis is what makes recoveries commensurable
with the benchmark. On the shared basis the headline off-window leg's miss is
**−$66.784bn / −10.2% of realized runoff, third of six**, not "+$2.8bn, 0.4%, the
smallest error of any leg here." Cross-artifact check:
`calibration_reconciliation.floor_table[2].miss_vs_benchmark_pp × B` =
`$66.78400264883bn`, bit-identical to the shared-basis error — so the note's "miss of
8.7 points" and "+$2.8 billion" were the same leg's same miss, 24× apart.

**Edits (both abstract variants).**
1. Error column prints `standalone / shared` pairs for all six legs.
2. Notes retire the false reassurance; state the ranking reversal and the identity with
   the 8.7-point miss; print both %R sextets.
3. Path A's `$164.1bn` statement carries the shared counterpart (`$94.6bn / 14.5%`).
4. `tab:crosswalk` gains a runoff-error row.
5. `tab:theil` note points at `tab:bases` for the shared-basis counterparts.

**Gate #109** + `tests/test_runoff_error_basis_gate.py` (10 tests). Live derivation from
`shared_layer_scoring` / `calibration_reconciliation` / `concave_marginal` /
`expectation_benchmark`; cross-artifact anchor; netting invariant; retired forms ABSENT;
marginals bit-preserved.

Marginal (+5.6pp / +$42.6bn, +9.2pp / +$70.3bn) untouched.

## Finding 5 — ABM waterfall provenance (MAJOR) — **SURVIVED adjudication; LANDED**

**Adjudication.** Caption claimed "Stage levels from the frozen run manifests." Frozen
manifests on disk only cover stages 5–7:

| stage | printed | source |
|---|---|---|
| 1–4 (71.1 / 54.9 / 45.1 / 33.7) | caption + body | `figures/fig3_stage_levels.json` only — **no run manifest** |
| 5 (13.2) | caption | `run-2026-07-04` (`share_explained_pct = 13.22976…`) |
| 6 (11.9) | caption | `run-2026-07-04-15yr-foldin` (11.89687…) |
| 7 (11.1) | caption | `run-2026-07-05-berger` (11.05026…) |

`figures/README.md` and `fig3_stage_levels.json`'s own note already admitted this; the
caption did not. Severity stays major (provenance claim in a caption that claims
provenance). Not refuted.

**Edit.** Caption now states the split provenance explicitly. `figures/README.md`
aligned (it had also under-counted stages, omitting the 13.2% production-corrections
leg).

**Gate #110** + `tests/test_waterfall_provenance_gate.py` (8 tests). Early stages tied to
`fig3_stage_levels.json`; late stages to the three manifests; retired caption ABSENT.

## Environment note

On this cloud checkout, the pre-existing `matched-depth reconciliation` cross-check
fails with `grid-recomputed-from-panel=False` both before and after these edits
(environment / panel recomputation, not introduced here). Gates #109 and #110 pass;
the new batteries are 18/18 green.
