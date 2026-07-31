# RECORD — R33 landings (A, B-part-1, findings 5/6/7/8) — 2026-07-31

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

## R33-B part 1 — the empirical-CPR referent (MAJOR) — **LANDED (disclosure only)**

§III.B said "Two implementations of this back-out exist in the pipeline." **There are
three.** The cross-design family passes `sched_smm_override = _population_sched_series`
(`cross_design_test.py:114-122`), a single-pool annuity keyed to the *simulated*
population's own weighted coupon and mean age, so its empirical referent is a function
of the population it simulates:

| run | referent | artifact |
|---|---|---|
| production | **5.14%** | `run-2026-07-04-15yr-foldin` (5.13881153921074) |
| cross-design | **5.83%** | `cross_design_results.json` (5.829007141082971) |
| reweighted | **5.64%** | `cross_design_reweight_results.json` (5.644629967368196) |

The dollar benchmark is unaffected — `empirical_trapped_b` is bit-identical
(764.7482532227002) in every run — so this is a path-referent defect, not a level one.
Landed: the corrected three-implementation sentence in §III.B; the cross-design row of
`tab:estimators` now names its own 5.83% back-out; the correlation-column note states
that those rows are not on a common CPR referent while every dollar column is.
**GATE #111** + 10-test battery (referents read live, distinctness enforced, common
dollar benchmark policed).

**Part 2 (the re-score) is NOT landed** and must not be run before its landing rule is
committed. Note the blocker found while checking feasibility: the production
cohort-weighted schedule is *not reproducible offline* (see the repo defect below), so
the re-score must be built on the committed June-2022 SOMA book tabulation in
`composition_shift_results.json`, not on a re-fetch.

## Finding 8 — the null's balance path (MAJOR) — **PARTIALLY CONFIRMED; LANDED**

**Adjudication.** The mechanism is already conceded at the cited site: the note says the
engine "renormalises the simulated pool to realized Fed holdings every month" and that a
leg's balance path "cannot drift from the realized one." What was missing is the
*consequence for the null*, which is asymmetric: the central leg is scored on the
realized path it is calibrated to reproduce, while the β₁=0 null is scored on that same
lock-in-affected path rather than the faster-declining one its own higher prepayment
would have produced. A self-consistent null would carry lower balances into the later
months → smaller roll-off → larger trapped → **smaller marginal**. So the reported
marginal is an upper bound on the compounding-consistent one.

The direction is deterministic from the accounting (null traps less ⇒ null rolls off
more), and **gate #112 ties it to the artifact** so it cannot silently invert. The
magnitude is deliberately not stated: pricing it needs a counterfactual-balance run of
the kind only the Danish legs perform, which is not attempted.

## Finding 7 — `tab:danish` vs its own manifests (MINOR) — **CONFIRMED; LANDED**

Two of four rows disagreed with the frozen manifests they descend from:

| row | was | now | manifest |
|---|---|---|---|
| (a) Mechanism-extrapolated ABM | 47.10% | **47.14%** | `run-2026-07-04-15yr-foldin` 47.13724 |
| (b) Berger ABM, Danish-level | 3.40% | **3.36%** | `run-2026-07-05-berger` 3.36057 |

Prose propagation was narrower than alleged: l.596's "3.39--3.40\%" carried row (b)'s
error and is now "3.36--3.39\%"; the one-decimal "47.1\%" mentions elsewhere were always
consistent with 47.14. The inference the sentence supports (Danish legs sit *below* the
4% floor) is unaffected, and marginally strengthened. **GATE #113** derives both cells
from the manifests, so neither can drift again.

## Finding 6 — the "within 45%" claim (MINOR) — **CONFIRMED; LANDED**

§V.E said "No synthetic-population household-choice specification I tested lands within
45\% of it." By the paper's own use of that phrase (distance from 100%: it calls 59.3%
"within 45\%" and 76.3% "within 24\%"), **§IV.A's rational baseline at 71.1% does land
within 45%**, and it is a synthetic-population household-choice specification the paper
tested. Scoped to the corrected production family (11.1--13.2%), with the counterexample
named in place rather than 350 lines away at the existing caveat. **GATE #114**, which
also goes red if the baseline ever moves outside 45 points and the caveat becomes moot.

Margin worth recording: the next bridge stage, behavioral gates at 54.9%, misses the
45-point bar by **a tenth of a point**.

## Repo defect — silent equal-weight cohort fallback — **FIXED**

`compute_metrics` caught *any* exception from the live SOMA cohort fetch and silently
substituted `cohorts_from_surface`, which is **equal-weighted**, printing one line to
stdout. Cohort weights set the scheduled-amortization series, which enters both the
simulated roll-off and the empirical CPR back-out, so the substitution moves every figure
derived from them. Now: fails loud by default, opt in with
`allow_surface_cohort_fallback=True`, and the run records `cohort_provenance` /
`n_cohorts` in `df.attrs`. Every production caller already passes `cohorts=` explicitly,
so nothing in the repo depended on the silent path. `tests/test_cohort_provenance.py`.

Still open (not fixed here): the 11-cohort table is frozen nowhere, so the production
scheduled-amortization series cannot be rebuilt offline from anything committed.

## Typesetting — verified by build, not asserted

`tab:bases` gained a column, so the table was rebuilt and measured rather than assumed.
Baseline (`origin/main`) already carried a **21.1pt overfull hbox** at that table; the
naive both-bases column took it to **78.0pt**. Repaired by splitting the error column
into two narrow columns under a `\multicolumn` group, shortening the four row labels
("in-sample calibration" → "in-sample"), and setting that one table in `\scriptsize`.

| | baseline | now |
|---|---|---|
| pages (main / long-abstract) | 130 / 131 | **130 / 131** |
| overfull hbox | 24 | **23** |
| overfull vbox | 5 | 5 |
| undefined refs / citations | 0 / 0 | 0 / 0 |
| `tab:bases` overfull | 21.1pt | **none** |

Multiset diff of every overfull box against baseline: one removed (the `tab:bases`
21.1pt), **none added**. Built with tectonic 0.15.0; `monte_carlo_trapped_liquidity` is
not in the repo, so a placeholder was used for the layout check only — the measurements
above are otherwise from the real sources.

## Environment note

On this cloud checkout the pre-existing `matched-depth reconciliation` cross-check fails
with `grid-recomputed-from-panel=False` both before and after these edits (it recomputes
from a gitignored panel; not introduced here). All six new gates pass on both editions,
and the full suite is **523 passed**.
