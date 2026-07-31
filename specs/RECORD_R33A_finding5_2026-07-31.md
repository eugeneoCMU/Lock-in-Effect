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

## R33-B part 2 — pricing the wedge — **RUN, ADJUDICATED T2, LANDED**

Spec `specs/SPEC_R33B_book_sched_decomposition.md` was **committed before the run**
(`7e01122`), the runner before it executed. The engine could not be re-run here (no FRED
key, and the SOMA cohort table is frozen nowhere), but the swap does not need the engine:
trapped liquidity accumulates **net and unclipped**, and `sched_smm` enters the simulated
roll-off linearly, so the effect is an exact accounting decomposition.

`Σ h·sched_book` is committed directly (manifest `scheduled_amort_b.total = 260.0248`);
`Σ h·sched_pop` is `Ĥ · Σ sched_pop`, with the effective holdings scale recovered **two
independent ways** from two different SMM series — `Ĥ_sched = 2383.51`,
`Ĥ_curt = 2375.01`, agreeing to **0.36%** (parity gate P1, tolerance 2%).

**Result.** All parity gates passed and the direction prediction held (the book amortizes
at 3.12%/yr against the sample population's 2.36%/yr):

| leg | sample basis | **book basis** |
|---|---|---|
| committed draw | 59.30% | **50.95%** |
| fifty-seed mean | 60.21% | **51.85%** |
| 95% band | 55.10--66.05% | **46.74--57.69%** |
| fifty-seed min | 53.76% | **45.41%** |
| seeds below the 50% threshold | 0 of 50 | **16 of 50** |

Wedge **Δ = $63.88bn = 8.35 points of benchmark**, robust to the holdings bracket
($63.53--64.23bn) and to per-seed population age ($62.94--63.88bn). Independently, this
lands inside the $59--63bn / 7--9 point figure the referee reconstructed by a different
route.

**Branch T2 fired** exactly as pre-committed: mean ≥ 50% > min. So the threshold verdict
survives the basis change and **the unanimity claim does not**. Landed at all three
governing sites — §IV l.155, §VII.D l.659, §VII.D l.691 — each now stating the
sample-basis figure, the book-basis figure, and that sixteen of fifty seeds fall below
the threshold rather than none. `tab:runindex` row added. **GATE #115** + 13-test battery
that re-derives the 16-of-50 count from the seed artifact independently of the runner and
fails if the artifact ever lands on a different branch.

Secondary basis (single-pool book annuity at the June-2022 WAC 2.471%, mean age 28.0mo,
isolating composition at a fixed functional form): **Δ = $33.50bn / 4.38pp**. Reported in
the artifact, not verdict-bearing, and not quoted in the manuscript.

### The basis choice is the load-bearing judgement call in this landing

Branch **T2 fires on either basis**, so the verdict — threshold survives, unanimity does
not — is robust to it. The *count* is not:

| basis | Δ | book-basis mean | seeds below 50 |
|---|---|---|---|
| **primary** (production cohort-weighted, term-aware) | $63.88bn | 51.85% | **16 of 50** |
| secondary (single-pool book annuity, like-for-like form) | $33.50bn | 55.83% | **1 of 50** |

The manuscript quotes sixteen. The case for the primary basis is that it is the book's
actual mechanical leg and the one §VI.B means by "scheduled amortization is fixed by the
book's composition"; the case for the secondary is that it holds functional form fixed
and so isolates composition alone. This was pre-committed, but it is a choice, and it is
where a reader who disagrees will disagree.

### Seed-invariance of the count, checked rather than assumed

Limit 2 of the spec applies one Δ to all fifty seeds. Recomputing Δ **per seed** from each
cell's own population age gives **16 of 50 as well** (`seed_invariance_check.agree =
true`), so the headline count is not an artefact of the approximation. Applying the
*maximum* observed age uniformly to every seed would give 14 — but that is a worst-case
stress, not an estimator, and it is recorded as such rather than quoted. Gate #115's
battery asserts the two counts agree.

**Not done:** the engine's own re-score. It needs a FRED key and a pinned SOMA cohort
table. The decomposition is exact given the linearity, but it is not a re-simulation.

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
