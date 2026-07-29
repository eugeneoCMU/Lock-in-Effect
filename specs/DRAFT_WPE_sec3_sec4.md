# DRAFT — WP-E items 1 and 2: SS III absorptions and the SS IV compression

**Status: DRAFT ONLY. Nothing in `paper/v18/revised_paper_v18.tex` has been touched.**
Source of truth for every OLD string below: `paper/v18/revised_paper_v18.tex` as of this
branch (1,418 lines, one paragraph per line). Every OLD block was extracted
programmatically from that file and asserted at `tex.count(old) == 1`.

Authority: `PLAN_review2_fixes_2026-07-28.md` WP-E items 1 and 2, under the decision
record's "(6) in-paper results rework YES". Item 1's zero-months sub-piece is drafted as
the single pointer sentence the brief specifies, not as a re-landing: WP-H1 already sits
in Appendix~\ref{sec:robustness-seasonalfloor} (tex 1342) and the run ledger (tex 709).

Apply order: **III-1 -> III-2 -> III-3 -> III-4 -> IV-A -> IV-B -> IV-C -> IV-D -> REF-1..5.**
Each pair is independent (no OLD block overlaps another), but IV-B and IV-C are anchored on
`\end{figure}` lines and must be applied after IV-A so the surrounding text is what this
draft assumed.

---

## 0. What this rework does, in one paragraph each

**SS III (`sec:method`).** SS III.B (`sec:method-benchmark`) absorbs three things that were
being carried elsewhere: the 51.0% coverage derivation that had been living in the
`tab:headline` caption (III-1, with the caption reduced to a pointer in III-2); a governing
statement that the two untestable conditions on the expectations complement bind *every*
site that quotes its ratios, not just the sentence they appear in (III-3); and one sentence,
where the benchmark is defined, naming the clip mechanism behind the four exact-zero months
and the levels-only restriction that follows from it (III-4).

**SS IV (`sec:abm`).** Eight prose paragraphs and three subsections become **three prose
paragraphs and two subsections**: the round-28 stress-test lead (untouched, byte for byte),
one paragraph carrying the whole synthetic-population estimate including the burnout
falsification, and one Interpretation paragraph that states the cross-design result and puts
the SMD joint infeasibility forward as the clean falsification. Specification detail is
delegated to the four appendices that already carry it and to the replication package.

---

## 1. Pinned-span inventory (what had to survive, and where it now sits)

Method: every string constant in `tools/liveness_gates.py` and `tests/*.py` was extracted by
`ast` (this catches f-string segments too, which a grep does not), then intersected with the
SS III and SS IV line ranges. Everything below is a span whose **only** home in the
manuscript is inside the edited region, so losing it would have taken a gate down.

### 1a. Gate #100 `ABM_LEAD_SPANS` — all eight, plus the two orderings

The entire lead paragraph (tex 152) is **carried through byte-identical**. No pair in this
draft touches it. That preserves, in place:

| key | span | where in the draft |
| --- | --- | --- |
| `leads_with_scope` | `the first thing to report about it is what its own cross-design leg establishes about its scope` | SS IV paragraph 1, unchanged |
| `crossdesign_level` | `60.2\% averaged over fifty seeds` | SS IV paragraph 1, unchanged |
| `threshold_precommitted` | `above the 50\% threshold fixed before that run` | SS IV paragraph 1, unchanged |
| `reweighted` | `76.3\% once the sample is reweighted to the SOMA book's own coupon composition` | SS IV paragraph 1, unchanged |
| `bound_frozen_leg` | `the same reweight moves the frozen-calibration leg the other way, down to 12.6\%` | SS IV paragraph 1, unchanged |
| `bound_behavioral_synthetic` | `no leg here replaces a synthetic behavioral population with a real one` | SS IV paragraph 1, unchanged |
| `bound_verdict_wording` | `cannot, on that test alone, be cleanly attributed to modeling paradigm` | SS IV paragraph 1, unchanged |
| `verdict_confined` | `What this section falsifies is therefore a \emph{synthetic-population} household-choice specification` | SS IV paragraph 1, unchanged |

Also preserved because the lead is untouched: `ABM_LEAD_OPENER` (`This section is a stress
test`) occurring on **exactly one** line; the ordering assert (`60.2\%` before `no
specification tested here explains`); and the two `test_abm_lead_gate.py` benign-rewrite
fixtures (`because that result governs how everything below should be read`, `A second
qualifier travels with the verdict and is developed where it binds`), which fail the test
suite with "benign fixture is stale" if reworded.

`abm_lead_check` also requires `the third is a recovery level, which this design does not
identify` to be present in SS V (tex 310). Untouched by this draft.

### 1b. Round-23/27 `RELOCATED_TO_BODY` twins living in the edited region

| key | span | only home | disposition |
| --- | --- | --- | --- |
| `crossdesign_seed_body` | `60.2\% averaged over fifty seeds---above the 50\% threshold` | tex 152 (SS IV lead) | untouched |
| `surprise_share_allocated_body` | `they require the uniform-spread allocation, because the settlement-aware allocation puts the anticipated share at 75.6\%` | tex 146 (SS III.B) | untouched; III-3 inserts **after** it |
| `paradigm_attribution_hedged_body` | `be cleanly attributed to modeling paradigm rather than to calibration and data source` | tex 152 and 625 | untouched at both |

### 1c. `EXACTLY_ONE` and the kernel pins (SS IV.A production paragraph)

| pin | span | disposition |
| --- | --- | --- |
| `EXACTLY_ONE[1]` | `not kernel-free, and every figure reported here is the kernel-applied` | moved into new paragraph 2, count still exactly 1 |
| `KERNEL_TEX_PHRASE` | `kernel is retained in production` | moved into new paragraph 2 |

### 1d. ABM-null feasibility cross-check (gate body at `liveness_gates.py:4574-4581`)

Every one of these has its only home in tex 200 and every one is carried into new
paragraph 3:

`abm\_null\_feasibility` · `$-259.4$\%` · `$+116.3$\%` · `$+270.4$ and $-105.3$ points` ·
`admits no counterpart to the $\beta_1 = 0$ null` · `they disagree in sign, and neither is
interpretable` · `a feasibility probe, not a pre-committed estimate`.

### 1e. SS III f-string gate literals (gate body at `liveness_gates.py:3392-3395`)

`anticipated share at 75.6\%` and `clears by 13.2 points in-sample and 10.1 points` are
composed from the `calibration_reconciliation` artifact and have their only home in tex 146.
III-3 appends after them and does not touch the sentence they sit in.

### 1f. Count-threshold literals that pass through the edited region

Re-derived on the applied text (all are `>=` checks, none exact):

| literal | gate wants | before | after |
| --- | --- | --- | --- |
| `60.2\%` | >= 3 (gate #83 cross-design seeds) | 9 | 9 |
| `\texttt{coupon\_convention\_amortization}` | >= 2 (Theil cross-check) | 4 | 4 |
| `$+2.9$ to $+8.7$` | >= 4 (floor-uncertainty) | 8 | 8 |
| `$+3.0$ to $+8.0$` | >= 2 | 4 | 4 |
| `\texttt{smd\_two\_moment}` | >= 1 | 1 | 1 |
| `55.1--66.0\%` | present | 3 | 3 |

### 1g. Numbers

Zero numeric tokens of three or more characters that exist in the current manuscript are
absent from the applied text. Every committed number in SS III's caption and in SS IV's
deleted paragraphs was relocated, never dropped. The full list of relocations is section 4.

---
## 2. SS III replacement pairs
Each OLD block below is asserted `tex.count(old) == 1` against the current manuscript.

### III-1 — SS III.B absorbs the tab:headline caption's 51.0% coverage derivation and the overlay-bound sentence that travels with it
Anchor: tex line 142. OLD is 178 chars, expected count **1**.
**OLD**

```tex
both in Section~\ref{sec:pathb}; what each bound leaves open is stated in Section~\ref{sec:limitations}). The empirical CPR back-out nets cohort-weighted scheduled amortization; 
```
**NEW**

```tex
both in Section~\ref{sec:pathb}; what each bound leaves open is stated in Section~\ref{sec:limitations}). The two exclusions must be netted on the book's own joint cells rather than counted separately: 33.7\% of face lies in out-of-window vintages (the 2022 cohort 23.1\%, pre-2017 10.6\%), and the 20.4\% Ginnie face share cuts across vintage rather than nesting inside it, so the conventional-and-in-window intersection is 51.0\% of face on the book's own agency $\times$ vintage joint cells (bounded above by 51.8\% for cell truncation; 52.7\% under an independence approximation), and the Freddie 2017--2021 conventional universe on which Path B is estimated directly represents about \emph{half} of SOMA book face. Two-thirds is the vintage-only marginal and overstates coverage. Each exclusion is bounded by an external-speed overlay (Section~\ref{sec:pathb}): the Ginnie Mae share at \$20--\$47 billion by published observed speeds, the out-of-window vintages at \$11.7 billion by observed cohort speeds, each signed toward overstating trapped liquidity. The empirical CPR back-out nets cohort-weighted scheduled amortization; 
```

### III-2 — tab:headline caption trimmed to a pointer (the derivation now lives in SS III.B)
Anchor: tex line 65. OLD is 924 chars, expected count **1**.
**OLD**

```tex
The Path B recovery is estimated on the Freddie 2017--2021 conventional universe, which directly represents about \emph{half} of SOMA book face once both exclusions are netted rather than counted separately: 33.7\% lies in out-of-window vintages (the 2022 cohort 23.1\%, pre-2017 10.6\%), and the 20.4\% Ginnie face share cuts across vintage rather than nesting inside it, so the conventional-and-in-window intersection is 51.0\% of face on the book's own agency $\times$ vintage joint cells (bounded above by 51.8\% for cell truncation; 52.7\% under an independence approximation). Two-thirds is the vintage-only marginal and overstates coverage. Each exclusion is bounded by an external-speed overlay (Section~\ref{sec:pathb}): the Ginnie Mae share at \$20--\$47 billion by published observed speeds, the out-of-window vintages at \$11.7 billion by observed cohort speeds, each signed toward overstating trapped liquidity.
```
**NEW**

```tex
The Path B recovery is estimated on the Freddie 2017--2021 conventional universe; Section~\ref{sec:method-benchmark} derives that universe's coverage of SOMA book face on the book's own agency $\times$ vintage joint cells, and states the external-speed overlay that bounds each exclusion (Section~\ref{sec:pathb}).
```

### III-3 — SS III.B gains the governing expectations-conditioning statement
Anchor: tex line 146. OLD is 109 chars, expected count **1**.
**OLD**

```tex
and the ratios bound the lock-in share of a mixed surprise. One question of standing precedes this accounting
```
**NEW**

```tex
and the ratios bound the lock-in share of a mixed surprise. Both conditions are properties of the projection rather than of any one quotation of it, so they govern every site at which these ratios appear --- the introduction, this section, and the conclusion --- and each ratio is to be read as an allocation-conditional upper bound on lock-in's share of a mixed lock-in-and-rate-path surprise, not as a partition of that surprise. One question of standing precedes this accounting
```

### III-4 — SS III.B gains the one-sentence zero-months pointer where the benchmark is defined
Anchor: tex line 133. OLD is 224 chars, expected count **1**.
**OLD**

```tex
Figure~\ref{fig:benchmark} traces the construction: monthly roll-off against the phased cap, and the cumulative paths whose terminal gaps are the cap-relative benchmark and the expectations-based complement introduced below.
```
**NEW**

```tex
Figure~\ref{fig:benchmark} traces the construction: monthly roll-off against the phased cap, and the cumulative paths whose terminal gaps are the cap-relative benchmark and the expectations-based complement introduced below. The monthly series carries one artifact that no result in this paper reads as behavior: four months come in at exactly zero because the back-out's non-negativity clip pins any month whose reported roll-off falls below scheduled amortization and posts the displaced mass into the following month's reading, a month-boundary allocation artifact of the reporting series rather than a behavioral observation (run \texttt{h1\_zero\_months\_diagnosis}; Appendix~\ref{sec:robustness-seasonalfloor} traces the mechanism and shows that repairing the affected pairs flips this paper's frozen monthly-timing rule from pass to concede), which is one reason every claim made from this benchmark is a claim about levels.
```

---

## 3. SS IV: the compressed section, then the pairs that produce it

### 3a. Full new SS IV text

Figure environments are shown collapsed as `[... fig:X environment, unchanged ...]`; none of
their lines is edited by any pair below. Paragraph 1 is the round-28 lead, reproduced here
byte-identical so the section can be read as a whole --- **no pair touches it.**
```tex
\section{Agent-Based Model Results: A Synthetic-Population Stress Test}\label{sec:abm}

This section is a stress test of the household-choice hypothesis, not the paper's main estimate, and the first thing to report about it is what its own cross-design leg establishes about its scope, because that result governs how everything below should be read. Re-running the same decision rule on real Freddie Mac structural covariates, under the recalibration rule the model already applies elsewhere, recovers 59.3\% of the benchmark on the committed draw and 60.2\% averaged over fifty seeds---above the 50\% threshold fixed before that run at which this section's paradigm reading would be undercut, and undercutting on all fifty of them---rising to 76.3\% once the sample is reweighted to the SOMA book's own coupon composition. Three things bound that reading and travel with it wherever it appears: the same reweight moves the frozen-calibration leg the other way, down to 12.6\%; the covariates swapped in are structural only, since the loan records contain no analogue for mobility desire or loss aversion, so no leg here replaces a synthetic behavioral population with a real one; and the verdict the run supports is that the contrast cannot, on that test alone, be cleanly attributed to modeling paradigm rather than to calibration and data source (Section~\ref{sec:robustness-crossdesign}). What this section falsifies is therefore a \emph{synthetic-population} household-choice specification: no specification tested here explains the Federal Reserve's trapped liquidity, and why it does not is not cleanly separable from the population it was tested on. A second qualifier travels with the verdict and is developed where it binds: the multi-vintage stage moved against its own predicted direction and the inversion is undiagnosed (Appendix~\ref{sec:robustness-extensions}).

\subsection{The Synthetic-Population Estimate: Baseline, Production, Extensions, and the Burnout Falsification}\label{sec:abm-results}

Section~\ref{sec:identification} \emph{declines} that same cross-design recovery as evidence that the imported lock-in elasticity is too small, on the ground that a recovery level is not what that design identifies; read as a scope limit on this section's verdict, which is how it is used above, it survives that objection, and neither use licenses the other. The production estimate is the synthetic-population special case, and it is the case in which the test bites: every specification tested here --- rational baseline, behavioral extensions, and a burnout variant --- moves further from, or fails to close, the \$764.7 billion benchmark, so I report them once and move to the hazard framework of Section~\ref{sec:hazard}. A purely rational baseline projects a structural cash flow deficit of \$544.0 billion (71.1\% of benchmark). The production specification adds scheduled amortization, a live CUSIP-level parse of SOMA holdings, a corrected empirical CPR back-out, a settlement-lag kernel, and the previously excluded 15-year MBS book in cohort weighting and scheduled amortization (structural terms only); its headline quantity is the seed distribution, not any single draw, at a fifty-seed mean of \$103.7 billion, or 13.6\% of the benchmark, with the frozen seed-42 draw (\$91.0 billion, 11.9\%, near the 34th percentile) retained as the reproducibility anchor the run manifests freeze. The kernel is retained in production and both frozen run manifests record it as applied, but it is a documented timing null rather than a fit improvement: a pre-fold-in ablation left the peak cross-correlation unchanged at $r = +0.192$ at lag $-3$ with the kernel on or off, and the kernel-applied production run peaks at $+0.195$ at the same lag. The production specification is not kernel-free, and every figure reported here is the kernel-applied run's. Seed dispersion dominates the third digit: the seed-level standard deviation is \$24.5 billion, a $\pm$1~SD share band of 10.4--16.8\%; the 95\% CI of the mean, \$96.9--\$110.5 billion, prices only simulation noise in the mean itself; and the 34th percentile is pinned only to within roughly $\pm$7 percentage points from 50 draws, so the ABM's share is better read as on the order of 10--17\% than as a three-digit point estimate (Figure~\ref{fig:mc}). The path fit is worse than the level fit and no extension repairs it (Figure~\ref{fig:abmpaths}): simulated mean CPR runs at 11.68\% against an empirical 5.14\%, the raw path correlation is negative at lag 0 ($r = -0.318$) with no value inside a $\pm$3-month window exceeding the +0.19 at the three-month lead, and the path $R^2$ is $-6.984$ (throughout, $R^2$ is computed as $1-\mathrm{SSE}/\mathrm{SST}$ against a mean-only null, so a negative value indicates fit worse than a constant at the empirical mean). Layering in three literature-grounded behavioral extensions --- a debt-to-income constraint with asymmetric loss aversion and a rate-shock freeze, income-scaled curtailment, and multi-vintage coupon composition --- moves the model to 54.9\%, then 45.1\%, then 33.7\% of the benchmark (Figure~\ref{fig:waterfall}); the first move is a recalibration artifact rather than evidence for loss aversion, since holding a real-world turnover floor fixed under a steeper loss-aversion penalty mechanically inflates rate sensitivity, and none of the three touches the CPR path's central failure, each operating on the level of simulated mobility rather than its timing. A fourth variant fails more informatively: path-dependent prepayment ``burnout,'' implemented as closed-population survivor selection, collapsed simulated CPR to approximately zero and raised trapped liquidity to 147\% of the benchmark, because a closed population of 10,000 agents depletes its mobile mass during the low-rate 2020--2021 window before QT even begins --- an absorbing state incompatible with a real MBS pool that continuously receives new originations, and \citepos{lesniewski2026} selection identity in its degenerate limit. It is a negative finding, not used in production, and it is why burnout is treated at the cohort rather than the per-agent level in Section~\ref{sec:hazard}. Figure~\ref{fig:recovery} places these levels beside the other estimators. The decision rule, every behavioral parameter and its source, the macroeconomic-friction and structural extensions, the mechanism-level detail behind all three behavioral stages, and the 15-year fold-in are specified in Appendices~\ref{sec:method-abm}, \ref{sec:method-frictions}, \ref{app:abmspec}, \ref{sec:robustness-extensions} and~\ref{sec:robustness-pipeline} and are reproduced end to end by the replication package (Appendix~\ref{app:ledger}); this section reports results only.

[... fig:recovery environment, unchanged (tex 158-163) ...]

[... fig:waterfall environment, unchanged (tex 165-170) ...]

[... fig:abmpaths environment, unchanged (tex 176-181) ...]

[... fig:mc environment, unchanged (tex 183-188) ...]

\subsection{Interpretation}\label{sec:abm-interp}

Every ABM specification tested here either widens the gap to the benchmark or leaves it unchanged, its CPR path stays uncorrelated or negatively correlated with the empirical path throughout, and Section~\ref{sec:robustness}'s scale-sensitivity replication finds no size effect on the production specification, so what remains is either that household-level decision-making does not govern the majority of the shortfall, or that this specification is missing a mechanism. The cross-design leg reported at the head of this section bears directly on that either-or and does not settle it: handing the same rule real structural covariates moves the recovery from 13.6\% to 60.2\% averaged over fifty seeds, which is what a missing-population problem looks like rather than a missing-mechanism one, but the behavioral layer stays synthetic in both legs, so the alternative is narrowed rather than eliminated. The clean falsification is the one that bypasses that free parameter entirely: the simulated-minimum-distance two-moment fit (Section~\ref{sec:robustness-crossdesign}) returns joint infeasibility under a verdict vocabulary fixed before execution, its nearest admissible fit overshooting the benchmark at 107.1\%, and it does not run through the recalibration scale that qualifies the cross-design reading. Section~\ref{sec:hazard} tests the first branch directly on a different data source and modeling paradigm; whichever explanation holds, these results weigh against household mobility choices, rational or behavioral, as the primary price the Federal Reserve paid for secondary-market liquidity, and the institutional counterpart --- whether the par-payoff rule itself, rather than household behavior, drives the trap --- is examined as a securitization-policy alternative in Section~\ref{sec:abm-danish}. One asymmetry in that comparison should be stated rather than left for a reader to notice. Section~\ref{sec:identification} insists that this design identifies a differential and not a level, and the ABM is nonetheless compared with Path B on levels, because the ABM admits no counterpart to the $\beta_1 = 0$ null. The reason is structural. In \eqref{eq:pathB} the elasticity is a separable term sitting over a floor that is measured independently and survives the elasticity's removal, so the null is still anchored to observed involuntary turnover and lands at 85.7\% of the benchmark. The ABM has no such term: its 4--5\% involuntary floor is not a component of \eqref{eq:abmmove} but a \emph{product} of it, obtained by searching the mobility-desire scale $\theta$ until the penalty-bearing rule returns 4--5\% CPR at an 8\% market rate, so zeroing the penalty removes the floor along with the channel. With the production $\theta = 43{,}882.8$ held fixed, the resulting leg returns 40.7\% CPR at the calibration point against the production rule's 4.8\%, over-retires the book, and scores $-259.4$\% of the benchmark; re-deriving $\theta$ under the null restores the anchor to 4.7\% but scores $+116.3$\%, because the re-search fits the null to the very turnover level the differential is meant to measure. The two readings imply marginals of $+270.4$ and $-105.3$ points. They do not bracket a magnitude; they disagree in sign, and neither is interpretable. I therefore report no ABM differential, and the estimator contrast of Section~\ref{sec:hazard} remains a contrast of levels, with the qualification that entails (run \texttt{abm\_null\_feasibility}; a feasibility probe, not a pre-committed estimate, and nothing in this paper's ranges depends on it).
```

### 3b. The pairs

#### IV-A — SS IV paragraphs 2 and 3 -> the IV.A head plus the compressed paragraph 2
OLD is 1444 chars / 3 lines, expected count **1**.
**OLD**

```tex
One consistency point belongs here rather than three sections later, because the same number is put to two uses. Section~\ref{sec:identification} \emph{declines} this cross-design recovery as evidence that the imported lock-in elasticity is too small, on the ground that a recovery level is not what that design identifies and that the same reweight moves the frozen leg down. Read as a scope limit on this section's verdict, which is how it is used here, it says something narrower and survives that objection: it bounds the population over which a household-choice specification was shown to fail, and makes no claim about the size of the elasticity. The two uses are consistent, and neither licenses the other.

The production estimate below is the synthetic-population special case, and it is the case in which the test bites. Every specification tested there (rational baseline, behavioral extensions, and a burnout variant) moves further from, or fails to close, the \$764.7 billion benchmark, so I report them briefly and move to the structurally distinct hazard framework of Section~\ref{sec:hazard}, the estimator on which the paper's central decomposition rests and which recovers, at the aggregate level, nearly all of the benchmark the ABM cannot. Figure~\ref{fig:recovery} summarizes the estimator comparison developed in this section and the next, and Figure~\ref{fig:waterfall} traces the ABM's specification path stage by stage.
```
**NEW**

```tex
\subsection{The Synthetic-Population Estimate: Baseline, Production, Extensions, and the Burnout Falsification}\label{sec:abm-results}

Section~\ref{sec:identification} \emph{declines} that same cross-design recovery as evidence that the imported lock-in elasticity is too small, on the ground that a recovery level is not what that design identifies; read as a scope limit on this section's verdict, which is how it is used above, it survives that objection, and neither use licenses the other. The production estimate is the synthetic-population special case, and it is the case in which the test bites: every specification tested here --- rational baseline, behavioral extensions, and a burnout variant --- moves further from, or fails to close, the \$764.7 billion benchmark, so I report them once and move to the hazard framework of Section~\ref{sec:hazard}. A purely rational baseline projects a structural cash flow deficit of \$544.0 billion (71.1\% of benchmark). The production specification adds scheduled amortization, a live CUSIP-level parse of SOMA holdings, a corrected empirical CPR back-out, a settlement-lag kernel, and the previously excluded 15-year MBS book in cohort weighting and scheduled amortization (structural terms only); its headline quantity is the seed distribution, not any single draw, at a fifty-seed mean of \$103.7 billion, or 13.6\% of the benchmark, with the frozen seed-42 draw (\$91.0 billion, 11.9\%, near the 34th percentile) retained as the reproducibility anchor the run manifests freeze. The kernel is retained in production and both frozen run manifests record it as applied, but it is a documented timing null rather than a fit improvement: a pre-fold-in ablation left the peak cross-correlation unchanged at $r = +0.192$ at lag $-3$ with the kernel on or off, and the kernel-applied production run peaks at $+0.195$ at the same lag. The production specification is not kernel-free, and every figure reported here is the kernel-applied run's. Seed dispersion dominates the third digit: the seed-level standard deviation is \$24.5 billion, a $\pm$1~SD share band of 10.4--16.8\%; the 95\% CI of the mean, \$96.9--\$110.5 billion, prices only simulation noise in the mean itself; and the 34th percentile is pinned only to within roughly $\pm$7 percentage points from 50 draws, so the ABM's share is better read as on the order of 10--17\% than as a three-digit point estimate (Figure~\ref{fig:mc}). The path fit is worse than the level fit and no extension repairs it (Figure~\ref{fig:abmpaths}): simulated mean CPR runs at 11.68\% against an empirical 5.14\%, the raw path correlation is negative at lag 0 ($r = -0.318$) with no value inside a $\pm$3-month window exceeding the +0.19 at the three-month lead, and the path $R^2$ is $-6.984$ (throughout, $R^2$ is computed as $1-\mathrm{SSE}/\mathrm{SST}$ against a mean-only null, so a negative value indicates fit worse than a constant at the empirical mean). Layering in three literature-grounded behavioral extensions --- a debt-to-income constraint with asymmetric loss aversion and a rate-shock freeze, income-scaled curtailment, and multi-vintage coupon composition --- moves the model to 54.9\%, then 45.1\%, then 33.7\% of the benchmark (Figure~\ref{fig:waterfall}); the first move is a recalibration artifact rather than evidence for loss aversion, since holding a real-world turnover floor fixed under a steeper loss-aversion penalty mechanically inflates rate sensitivity, and none of the three touches the CPR path's central failure, each operating on the level of simulated mobility rather than its timing. A fourth variant fails more informatively: path-dependent prepayment ``burnout,'' implemented as closed-population survivor selection, collapsed simulated CPR to approximately zero and raised trapped liquidity to 147\% of the benchmark, because a closed population of 10,000 agents depletes its mobile mass during the low-rate 2020--2021 window before QT even begins --- an absorbing state incompatible with a real MBS pool that continuously receives new originations, and \citepos{lesniewski2026} selection identity in its degenerate limit. It is a negative finding, not used in production, and it is why burnout is treated at the cohort rather than the per-agent level in Section~\ref{sec:hazard}. Figure~\ref{fig:recovery} places these levels beside the other estimators. The decision rule, every behavioral parameter and its source, the macroeconomic-friction and structural extensions, the mechanism-level detail behind all three behavioral stages, and the 15-year fold-in are specified in Appendices~\ref{sec:method-abm}, \ref{sec:method-frictions}, \ref{app:abmspec}, \ref{sec:robustness-extensions} and~\ref{sec:robustness-pipeline} and are reproduced end to end by the replication package (Appendix~\ref{app:ledger}); this section reports results only.
```

#### IV-B — delete the old IV.A head and its production paragraph (absorbed by IV-A)
OLD is 2734 chars / 9 lines, expected count **1**.
**OLD**

```tex
\end{figure}

\subsection{The Synthetic-Population Estimate: Baseline, Production, and Behavioral Extensions}\label{sec:abm-results}

A purely rational baseline projects a structural cash flow deficit of \$544.0 billion (71.1\% of benchmark). The production ABM builds on this baseline in four ways: scheduled amortization, a live CUSIP-level parse of SOMA holdings, a corrected empirical CPR back-out, and a settlement-lag kernel. The kernel is retained in production, and both frozen run manifests record it as applied; it is a documented timing null rather than a fit improvement: a pre-fold-in ablation left the peak cross-correlation unchanged at $r = +0.192$ at lag $-3$ with the kernel on or off, and the kernel-applied production run peaks at $+0.195$ at the same lag. The production specification is not kernel-free, and every figure reported here is the kernel-applied run's. Together, these additions yield a production estimate whose headline quantity is the seed distribution, not any single draw: a fifty-seed mean of \$103.7 billion in trapped liquidity, or 13.6\% of the benchmark, with the frozen seed-42 replication draw (\$91.0 billion, 11.9\%, near the 34th percentile of the distribution) retained as the reproducibility anchor the run manifests freeze, after incorporating the previously excluded 15-year MBS book into cohort weighting and scheduled amortization (structural terms only; Appendix~\ref{sec:robustness-pipeline} documents the fold-in, why voluntary CPR for 15-year cohorts is drawn from the same-coupon 30-year surface in this frozen headline specification, and the native 15-year gate behind the Berger-run variant). The CPR path fit is equally weak (Figure~\ref{fig:abmpaths}). Simulated mean CPR runs at 11.68\% against an empirical 5.14\%, and the raw path correlation is negative at lag 0 ($r = -0.318$), with no value inside a $\pm$3-month window exceeding the +0.19 at the three-month lead. The path $R^2$ is $-6.984$: throughout, $R^2$ is computed as $1-\mathrm{SSE}/\mathrm{SST}$ against a mean-only null, so a negative value indicates fit worse than a constant at the empirical mean. (That fifty-seed distribution's seed-level standard deviation is \$24.5 billion---a $\pm$1~SD share band of 10.4--16.8\%---and the 95\% CI of the mean, \$96.9--\$110.5 billion, reflects only simulation noise in the mean itself, not seed dispersion; Figure~\ref{fig:mc} shows the distribution against the benchmark. The 34th percentile is itself pinned only to within roughly $\pm$7 percentage points from 50 draws, so the ABM's share is better read as on the order of 10--17\% than as a three-digit point estimate.)

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{fig10_abm_cpr_paths}
```
**NEW**

```tex
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{fig10_abm_cpr_paths}
```

#### IV-C — delete the extensions paragraph and the whole Burnout Falsification subsection (absorbed by IV-A)
OLD is 1580 chars / 9 lines, expected count **1**.
**OLD**

```tex
\end{figure}

Layering in three literature-grounded behavioral extensions---a debt-to-income constraint with asymmetric loss aversion and a rate-shock freeze, income-scaled curtailment, and multi-vintage coupon composition---moves the model to 54.9\%, then 45.1\%, then 33.7\% of the benchmark (Figure~\ref{fig:waterfall}). The first move is a recalibration artifact rather than evidence for loss aversion (holding a real-world turnover floor fixed under a steeper loss-aversion penalty mechanically inflates rate sensitivity), and none of the three touches the CPR path's central failure, since each operates on the level of simulated mobility rather than its timing; Appendix~\ref{sec:robustness-extensions} reports the mechanism-level detail for all three.

\subsection{Burnout Falsification}\label{sec:abm-burnout}

I tested whether path-dependent prepayment ``burnout,'' implemented as closed-population survivor selection, could explain the ABM's weak CPR fit. It failed: simulated CPR collapsed to approximately zero and trapped liquidity rose to 147\% of the benchmark, because a closed population of 10,000 agents depletes its mobile mass during the low-rate 2020--2021 window before QT even begins, an absorbing state incompatible with a real MBS pool that continuously receives new originations. This is \citepos{lesniewski2026} selection identity in its degenerate limit; a negative finding, not used in production, it motivates the cohort-level rather than per-agent treatment of burnout in Section~\ref{sec:hazard}.

\subsection{Interpretation}\label{sec:abm-interp}
```
**NEW**

```tex
\end{figure}

\subsection{Interpretation}\label{sec:abm-interp}
```

#### IV-D — Interpretation: two paragraphs -> compressed paragraph 3, with the ABM-null asymmetry retained as its own paragraph
OLD is 3783 chars / 3 lines, expected count **1**.
**OLD**

```tex
Every ABM specification tested here either widens the gap to the benchmark or leaves it unchanged, and its CPR path stays uncorrelated or negatively correlated with the empirical path throughout. Section~\ref{sec:robustness}'s scale-sensitivity replication finds no size effect on the production specification, so what remains is either that household-level decision-making does not govern the majority of the shortfall, or that this specification is missing a mechanism. The cross-design leg reported at the head of this section bears directly on that either-or and does not settle it: handing the same rule real structural covariates moves the recovery from 13.6\% to 60.2\% averaged over fifty seeds, which is what a missing-population problem looks like rather than a missing-mechanism one, but the behavioral layer stays synthetic in both legs, so the alternative is narrowed rather than eliminated. Section~\ref{sec:hazard}'s hazard framework, built on a different data source and modeling paradigm, tests the first branch directly. Whichever explanation holds, the ABM results already narrow the trade-off named in this paper's title: they weigh against household mobility choices, rational or behavioral, as the primary price the Federal Reserve paid for secondary-market liquidity, and point instead toward the loan-level and institutional channels Section~\ref{sec:hazard} takes up. The cleanest of the pre-committed falsifications bypasses that free parameter entirely: the simulated-minimum-distance two-moment fit (Section~\ref{sec:robustness-crossdesign}) returns joint infeasibility under a verdict vocabulary fixed before execution, its nearest admissible fit overshooting the benchmark at 107.1\%, and it does not run through the recalibration scale that qualifies the cross-design reading. The institutional counterpart---whether the par-payoff rule itself, rather than household behavior, drives the trap---is examined as a securitization-policy alternative in Section~\ref{sec:abm-danish}.

One asymmetry in that comparison should be stated rather than left for a reader to notice. Section~\ref{sec:identification} insists that this design identifies a differential and not a level, and the ABM is nonetheless compared with Path B on levels, because the ABM admits no counterpart to the $\beta_1 = 0$ null. The reason is structural. In \eqref{eq:pathB} the elasticity is a separable term sitting over a floor that is measured independently and survives the elasticity's removal, so the null is still anchored to observed involuntary turnover and lands at 85.7\% of the benchmark. The ABM has no such term: its 4--5\% involuntary floor is not a component of \eqref{eq:abmmove} but a \emph{product} of it, obtained by searching the mobility-desire scale $\theta$ until the penalty-bearing rule returns 4--5\% CPR at an 8\% market rate. Zeroing the penalty therefore removes the floor along with the channel. With the production $\theta = 43{,}882.8$ held fixed, the resulting leg returns 40.7\% CPR at the calibration point against the production rule's 4.8\%, over-retires the book, and scores $-259.4$\% of the benchmark; re-deriving $\theta$ under the null restores the anchor to 4.7\% but scores $+116.3$\%, because the re-search fits the null to the very turnover level the differential is meant to measure. The two readings imply marginals of $+270.4$ and $-105.3$ points. They do not bracket a magnitude; they disagree in sign, and neither is interpretable. I therefore report no ABM differential, and the estimator contrast of Section~\ref{sec:hazard} remains a contrast of levels, with the qualification that entails (run \texttt{abm\_null\_feasibility}; a feasibility probe, not a pre-committed estimate, and nothing in this paper's ranges depends on it).
```
**NEW**

```tex
Every ABM specification tested here either widens the gap to the benchmark or leaves it unchanged, its CPR path stays uncorrelated or negatively correlated with the empirical path throughout, and Section~\ref{sec:robustness}'s scale-sensitivity replication finds no size effect on the production specification, so what remains is either that household-level decision-making does not govern the majority of the shortfall, or that this specification is missing a mechanism. The cross-design leg reported at the head of this section bears directly on that either-or and does not settle it: handing the same rule real structural covariates moves the recovery from 13.6\% to 60.2\% averaged over fifty seeds, which is what a missing-population problem looks like rather than a missing-mechanism one, but the behavioral layer stays synthetic in both legs, so the alternative is narrowed rather than eliminated. The clean falsification is the one that bypasses that free parameter entirely: the simulated-minimum-distance two-moment fit (Section~\ref{sec:robustness-crossdesign}) returns joint infeasibility under a verdict vocabulary fixed before execution, its nearest admissible fit overshooting the benchmark at 107.1\%, and it does not run through the recalibration scale that qualifies the cross-design reading. Section~\ref{sec:hazard} tests the first branch directly on a different data source and modeling paradigm; whichever explanation holds, these results weigh against household mobility choices, rational or behavioral, as the primary price the Federal Reserve paid for secondary-market liquidity, and the institutional counterpart --- whether the par-payoff rule itself, rather than household behavior, drives the trap --- is examined as a securitization-policy alternative in Section~\ref{sec:abm-danish}. One asymmetry in that comparison should be stated rather than left for a reader to notice. Section~\ref{sec:identification} insists that this design identifies a differential and not a level, and the ABM is nonetheless compared with Path B on levels, because the ABM admits no counterpart to the $\beta_1 = 0$ null. The reason is structural. In \eqref{eq:pathB} the elasticity is a separable term sitting over a floor that is measured independently and survives the elasticity's removal, so the null is still anchored to observed involuntary turnover and lands at 85.7\% of the benchmark. The ABM has no such term: its 4--5\% involuntary floor is not a component of \eqref{eq:abmmove} but a \emph{product} of it, obtained by searching the mobility-desire scale $\theta$ until the penalty-bearing rule returns 4--5\% CPR at an 8\% market rate, so zeroing the penalty removes the floor along with the channel. With the production $\theta = 43{,}882.8$ held fixed, the resulting leg returns 40.7\% CPR at the calibration point against the production rule's 4.8\%, over-retires the book, and scores $-259.4$\% of the benchmark; re-deriving $\theta$ under the null restores the anchor to 4.7\% but scores $+116.3$\%, because the re-search fits the null to the very turnover level the differential is meant to measure. The two readings imply marginals of $+270.4$ and $-105.3$ points. They do not bracket a magnitude; they disagree in sign, and neither is interpretable. I therefore report no ABM differential, and the estimator contrast of Section~\ref{sec:hazard} remains a contrast of levels, with the qualification that entails (run \texttt{abm\_null\_feasibility}; a feasibility probe, not a pre-committed estimate, and nothing in this paper's ranges depends on it).
```

#### REF-1 — repoint \ref{sec:abm-burnout} (SS II, tex line 112)
OLD is 98 chars / 1 lines, expected count **1**.
**OLD**

```tex
the ABM probes by pre-committed falsification (Sections~\ref{sec:patha} and~\ref{sec:abm-burnout})
```
**NEW**

```tex
the ABM probes by pre-committed falsification (Sections~\ref{sec:patha} and~\ref{sec:abm-results})
```

#### REF-2 — repoint \ref{sec:abm-burnout} (SS V.A motivation, tex line 210)
OLD is 154 chars / 1 lines, expected count **1**.
**OLD**

```tex
with the closed-population survivor-selection failure of Section~\ref{sec:abm-burnout} motivating a cohort-level rather than per-loan treatment of burnout
```
**NEW**

```tex
with the closed-population survivor-selection failure of Section~\ref{sec:abm-results} motivating a cohort-level rather than per-loan treatment of burnout
```

#### REF-3 — repoint \ref{sec:abm-burnout} (SS V.B Path B, tex line 263)
OLD is 85 chars / 1 lines, expected count **1**.
**OLD**

```tex
not well-defined for a one-time, absorbing transition (Section~\ref{sec:abm-burnout})
```
**NEW**

```tex
not well-defined for a one-time, absorbing transition (Section~\ref{sec:abm-results})
```

#### REF-4 — repoint \ref{sec:abm-burnout} (SS VI.A fallout, tex line 438)
OLD is 81 chars / 1 lines, expected count **1**.
**OLD**

```tex
as Section~\ref{sec:abm-burnout}'s falsified survivor-selection experiment showed
```
**NEW**

```tex
as Section~\ref{sec:abm-results}'s falsified survivor-selection experiment showed
```

#### REF-5 — repoint \ref{sec:abm-burnout} (SS VI.B policy, tex line 458), with number agreement fixed
OLD is 142 chars / 1 lines, expected count **1**.
**OLD**

```tex
Sections~\ref{sec:abm-results} and~\ref{sec:abm-burnout} show that no synthetic-population household-choice specification tested here explains
```
**NEW**

```tex
Section~\ref{sec:abm-results} shows that no synthetic-population household-choice specification tested here explains
```

---

## 4. SS IV deletion ledger — every deleted fact and its surviving site

"Moved" = the fact is in the new SS IV text. "Delegated" = the fact is not in SS IV any more
and the appendix or replication package named is where it now lives. "Elsewhere" = the fact
was already stated at another site, which is cited.

### From tex 154 (the consistency paragraph, 114 words -> 1 sentence)

| deleted | disposition |
| --- | --- |
| `One consistency point belongs here rather than three sections later, because the same number is put to two uses.` | **Deleted as framing.** The substance (SS V.E declines the recovery; the scope-limit reading survives; neither use licenses the other) is the first sentence of new paragraph 2. |
| `it bounds the population over which a household-choice specification was shown to fail, and makes no claim about the size of the elasticity` | **Elsewhere.** The lead paragraph already confines the verdict (`verdict_confined` span, tex 152), and SS V states the declination at tex 310 in the words gate #100 pins. |

### From tex 156 (the hand-off paragraph, 103 words -> folded)

| deleted | disposition |
| --- | --- |
| `nearly all of the benchmark the ABM cannot` | **Elsewhere.** SS V's opening paragraph (tex 204) states the hazard framework's 91.3/97.9/112.4 recoveries against the ABM's 11.9/13.6 directly. |
| `Figure~\ref{fig:waterfall} traces the ABM's specification path stage by stage` | **Moved.** `fig:waterfall` is referenced from the extensions sentence of new paragraph 2; `fig:recovery` is referenced from its own sentence. Both figures stay in place; no figure loses its reference. |

### From tex 174 (the production paragraph, 372 words -> folded)

| deleted | disposition |
| --- | --- |
| the fold-in parenthetical: `Appendix~\ref{sec:robustness-pipeline} documents the fold-in, why voluntary CPR for 15-year cohorts is drawn from the same-coupon 30-year surface in this frozen headline specification, and the native 15-year gate behind the Berger-run variant` | **Delegated** to the closing sentence's appendix list. The three phrases survive elsewhere on their own: `same-coupon 30-year surface` at tex 397, 813, 1322; `native 15-year gate` at tex 168 (the `fig:waterfall` caption) and 493; `Berger-run` at tex 168 and 813. |
| `Figure~\ref{fig:mc} shows the distribution against the benchmark` | **Moved** (the `fig:mc` reference now closes the seed-dispersion sentence). |
| every number in the paragraph | **Moved**, all of them: `\$544.0` `71.1\%` `\$103.7` `13.6\%` `\$91.0` `11.9\%` `34th percentile` `+0.192` `lag $-3$` `+0.195` `\$24.5` `10.4--16.8\%` `\$96.9--\$110.5` `$\pm$7 percentage points` `10--17\%` `11.68\%` `5.14\%` `-0.318` `+0.19` `-6.984`. |

### From tex 190 (the extensions paragraph, 94 words -> one sentence)

| deleted | disposition |
| --- | --- |
| `Appendix~\ref{sec:robustness-extensions} reports the mechanism-level detail for all three.` | **Delegated**; `mechanism-level detail` and the `sec:robustness-extensions` reference both survive in the closing delegation sentence. |
| `54.9\%`, `45.1\%`, `33.7\%`, the recalibration-artifact mechanism | **Moved** verbatim in substance. |

### From tex 192-194 (the whole `Burnout Falsification` subsection)

| deleted | disposition |
| --- | --- |
| `\subsection{Burnout Falsification}\label{sec:abm-burnout}` | **Retired.** Its five `\ref` sites are repointed to `sec:abm-results` by REF-1..REF-5, and the burnout material is now inside that subsection, whose title names it. This also finishes A5's retirement of the "falsification" frame from SS IV's headings. |
| `147\%`, the closed-population mechanism, `\citepos{lesniewski2026}` selection identity, "not used in production", the cohort-level motivation | **Moved** into new paragraph 2. |

### From tex 198 + 200 (Interpretation, 537 words -> 517 in one paragraph)

| deleted | disposition |
| --- | --- |
| `Section~\ref{sec:hazard}'s hazard framework, built on a different data source and modeling paradigm, tests the first branch directly.` -> compressed to a clause | **Moved.** |
| `Whichever explanation holds, the ABM results already narrow the trade-off named in this paper's title` | **Elsewhere** for the title framing (tex 434 makes the same statement in SS VI). The unique clause `primary price the Federal Reserve paid for secondary-market liquidity` is **moved**, not dropped. |
| the paragraph break between Interpretation and the ABM-null asymmetry | **Merged.** No sentence of the asymmetry argument is dropped; all seven of its gate spans and all six of its numbers are in new paragraph 3. |

### Not deleted, deliberately

`fig:recovery`, `fig:waterfall`, `fig:abmpaths` and `fig:mc` all stay in SS IV and all four
stay referenced from its prose. Relocating `fig:abmpaths` and `fig:mc` to
Appendix~\ref{sec:method-abm} is the next available cut (roughly one page) and is flagged in
section 5 as a decision, not taken here.

---

## 5. Ambiguities, and the calls I made

1. **"~2-3pp" in the plan versus "~2-3 paragraphs" in the brief.** WP-E item 2 in
   `PLAN_review2_fixes_2026-07-28.md` reads "compresses to ~2-3pp", which in a length
   context reads as *pages*; the execution brief says *paragraphs*. I drafted to
   **paragraphs** (3 prose paragraphs) because that is the instruction I was given. The word
   cut is real but modest --- 1,583 -> 1,464 words of SS IV prose, 1,317 -> 1,198 after the
   frozen lead --- because SS IV is dense with committed numbers that cannot be dropped. The
   page cut comes mostly from losing five paragraph breaks and one subsection head. **If
   pages were the target, the lever is the two figures named above, not the prose.**

2. **Which subsection label to retire.** Compressing to three paragraphs cannot keep three
   subsection heads. `sec:abm-results` has 13 `\ref` sites, `sec:abm-burnout` has 5,
   `sec:abm-interp` has 1. I retired the cheapest (`sec:abm-burnout`) and repointed its five
   sites. The alternative --- keeping the label on the same subsection as `sec:abm-results`
   --- was rejected because tex 458 references both in one sentence and would have rendered
   "Sections 4.1 and 4.1".

3. **Whether SS III should *lose* the caption text or merely *gain* it.** The brief says
   "absorbs", so III-2 reduces the caption to a pointer rather than duplicating the
   derivation in two places. Every literal moves at constant whole-file count. If you would
   rather keep the caption self-contained, apply III-1 alone and drop III-2; nothing else in
   this draft depends on III-2.

4. **`66.2\%` and `33.7\%` are now adjacent** (tex 142 says 66.2% of face is in-window by
   vintage; the promoted derivation says 33.7% is out-of-window). They sum to 99.9. Both are
   committed values from different runs and I changed neither, but a reader now meets them
   in one paragraph, where before they were a page apart. **Flagging, not fixing** --- any
   reconciliation is a numbers question, not a wording one.

5. **The expectations-conditioning statement was already largely landed.** H3's restatement
   ("the ratios are upper bounds ... on a mixed surprise") is in tex 146 today. What was
   missing is that the conclusion (tex 605) and the introduction (tex 43) quote the ratios
   without those conditions travelling with them, and the conclusion's sentence is
   gate-pinned verbatim (`surprise_denominator_body`), so it cannot be hedged in place.
   III-3 therefore drafts the *governing* form --- the conditions bind every site --- which
   is the only fix available that does not touch a pinned span. **If you would rather hedge
   each site instead, that requires re-anchoring `RELOCATED_TO_BODY` and is out of this
   draft's scope.**

6. **The zero-months sentence claims nothing new.** It states the mechanism, cites the run
   tag and the appendix, and draws the levels-only consequence the appendix already draws at
   tex 1346. I did not repeat the four month names or the unclipped values; they stay in the
   appendix. If you want the months named at the benchmark's definition, that is a one-clause
   extension of III-4.

7. **`\subsection` retitled** to "The Synthetic-Population Estimate: Baseline, Production,
   Extensions, and the Burnout Falsification". Not gate-pinned; the retitle is what keeps the
   five repointed `\ref{sec:abm-results}` sites reading correctly for burnout.

---

## 6. Verification performed on the applied text (read-only, no gate suite run)

Applied all 13 pairs to a scratch copy and re-derived, in-process, the string half of every
gate rule that reads the manuscript. **The gate suite itself was not executed** (it reads run
artifacts and this is a no-execution task); what follows re-implements the shipped rules'
string logic against the applied text.

- Every string constant in `tools/liveness_gates.py` and `tests/*.py` that is present in the
  current manuscript is **still present**: 0 lost.
- Gate #100 `abm_lead_check`: 1 opener paragraph, 0 missing spans, ordering True,
  `ve_declines` True.
- Gate #98 `assembly_check`: 1 opener paragraph, 0 missing spans, 0 missing table spans.
- Gate #68 `abstract_hedge_check`: 248 words, 0 missing abstract hedges, **0 missing
  `RELOCATED_TO_BODY` spans**.
- Gate #99 `abstract_posture_check`: 0 missing, ordering True.
- Gates #102/#103/#104/#105/#106 span dicts: 0 missing.
- `EXACTLY_ONE`: all four still exactly 1. `KERNEL_TEX_PHRASE`: present.
- `LETTER_CURRENT_LITERALS`: all still in the manuscript (gate #101 unaffected; the abstract
  is untouched, so the 248-word recount does not move).
- Numeric tokens of length >= 3 that vanished: **none**.
- `\label`/`\ref`: no dangling refs; one label removed (`sec:abm-burnout`) with all five of
  its refs repointed and none left live; no duplicate labels.
- Figures: `fig:recovery` 2 refs, `fig:waterfall` 1, `fig:abmpaths` 1, `fig:mc` 1 --- every
  figure that stays is still referenced from SS IV prose.
- Blank-line hygiene: the count of runs of three or more newlines is unchanged (9 before, 9
  after), i.e. the deletions did not leave a doubled paragraph break.

Result of the compression, measured: SS IV prose **8 paragraphs -> 3**, **3 subsections ->
2**, **1,583 -> 1,464 words** (1,317 -> 1,198 excluding the frozen lead), manuscript
1,418 -> 1,406 lines.
