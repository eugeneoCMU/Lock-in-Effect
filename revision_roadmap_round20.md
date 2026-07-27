# Revision Roadmap — Round 20

**Date:** 2026-07-19
**Manuscript:** `paper/v17/revised_paper_v17.tex` (94pp)
**State at close:** 58 liveness gates PASS, 48 pytest tests pass, PDF 94pp, 0 undefined references, 0 undefined citations.
**Commit status:** nothing committed, nothing pushed.

---

## 1. What was attempted, and why

Five major flaws stood against v17 after the prior round. This round targeted two of them, chosen because both go to whether the paper measures what it claims rather than to how the measurement is framed.

**Flaw 1 — identification.** The rate-gap elasticity that drives the entire lock-in marginal was never estimated on this data. It was imported from Liebersohn and Rothstein and applied through the microsimulation. A paper whose headline is a dollar figure cannot leave its central structural parameter as a borrowed number without either measuring it or saying plainly that it is a calibration. The intent was to measure it: an instrumental-variables design on origination vintage, and a regression-discontinuity design on the FICO pricing notches, both run on the loan-level sample.

**Flaw 2 — timing.** No estimator in the paper beat a naive no-change forecast at monthly frequency, and every detrended contemporaneous correlation between simulated and empirical prepayment paths was negative. The intent was to determine whether a floor with calendar structure — a seasonalized involuntary-turnover floor — recovered the monthly variation that a flat floor missed.

**Pre-registration.** Three thresholds were frozen in the harness header before any run, and all three are inspectable at named lines: `L_R_AGREE_FACTOR = 2.5` at line 85 (the factor within which a measured elasticity had to agree with the imported one for the import to be corroborated), `RD_FIRST_STAGE_F_MIN = 10.0` at line 86 (the weak-instrument floor for the RD first stage), and `TIMING_RATE_SHARE_MIN = 0.15` at line 90 (the minimum Shapley share of monthly variation attributable to the rate channel for a timing claim to be earned). None was edited after execution.

**Scope of that verifiability — stated precisely, because an earlier draft of this roadmap got the direction wrong in both directions at different points.** The three thresholds are real and are readable at lines 85/86/90 as quoted; there is no basis for a caveat that they cannot be checked, and any such caveat is retracted. But the harness carrying them, `lockin_identification_and_timing.py`, is **not in the repository** — it exists only in this session's scratchpad. The line references are therefore verifiable *this session* and not from a clean checkout, and the threshold values should be read as **session-verifiable and unpersisted**. The timing rule scored downstream of that gate — `U2(first differences) < 1 AND detrended lag-0 r > 0` — is by contrast fully persisted: it was frozen ex ante in the module docstring of `hazard/b3_timing_rescore.py`, which is in the repo, before the legs ran.

Neither task was fixed in the intended direction. Both terminated in fallbacks that were specified in advance, and both fallbacks are what the paper now carries.

---

## 2. What happened, per task

### 2.1 Identification — `NOT_FEASIBLE`

The binding constraint is not missing raw files. It is **censoring by construction**. `hazard/loan_sample.py:56` applies `.filter(pl.col("reporting_period") < qt_ym)` with `qt_ym = QT_START = 2022-06`. Zero of 75,000 sampled observations survive at implied month ≥ 65; the ceiling is 2022-05. The only surviving monthly `MORTGAGE30US` series spans exactly 2022-06 through 2025-11. **The loan-level artifact and the market-rate artifact are exactly disjoint in time.** The Fannie side is identical: `loan_sample_fannie.parquet` has `loan_age` maximum 64.0. No design that needs a post-2022-05 outcome can be run on this data, because no such outcome exists in it.

Both designs were nonetheless run to termination, so that the failure would be recorded as a measurement rather than an assumption.

**RD dies outcome-independently.** Maximum first-stage F across 42 cutoff × bandwidth specifications is 3.36–3.38, against a pre-registered floor of 10. Per-window sample sizes are 2,700–23,000, so this is not power-by-N; there is no first stage to be powered. I record a correction to a claim I made earlier in this round and stated wrongly: FICO **does** shift the note rate — OLS slope −0.395 bp per FICO point, t = −59.8, within-vintage −0.24 to −0.36 bp. What is absent is a *discontinuity*, not a relationship. Separately, the density step at FICO 680 (165 → 273 loans per FICO point) is **not** attributable to the stratified sampler: `loan_sample.py:110-141` allocates proportionally across 130 strata, and rounding bounds the induced distortion at roughly 65 loans against roughly 1,080 excess. The cause is unestablished; FICO heaping at a round threshold is the most likely explanation. **McCrary rejects in 5 of 7 windows at p < 0.05, and in 4 of 7 at p < 0.01.** Both counts are given with their thresholds because an earlier draft of this roadmap reported "p < 0.05 in 4 of 7," which pairs the p < 0.01 count with the p < 0.05 threshold and understates the rejection rate. The seven p-values are 0.0482, 0.0000, 0.0000, 0.0000, 0.0001, 0.2717, 0.4439 — five below 0.05, four below 0.01, and the fifth rejection (0.0482) clearing 0.05 only narrowly. These p-values are **session-computed and unpersisted**: no artifact under `hazard/data/` records them, and they did not come from the pre-registered harness, whose McCrary gate fails open (below).

**IV is degenerate, then merely weak, then still fails.** Under year-only vintage there are 5 support points, and a degree-4 polynomial annihilates the instrument exactly: residual df = 0, R² = 1.000000. Recovering origination *quarter* from the loan-id sequence number lifts this to 20 support points, at which the instrument is merely weak (degree 4: residual df 15, R² 0.9396). It fails regardless, for want of any outcome after 2022-05.

**The pre-registered harness must not be run, and did not produce these numbers.** `lockin_identification_and_timing.py` fails its own selftest, and carries two integrity defects I am recording because they bear on how the round's other results should be read. First, the McCrary gate **fails open**: `rddensity` exposes no `.pv`, the resulting `AttributeError` is swallowed by a bare `except`, `mccrary_p` is therefore always `None`, and `rd_credible` then evaluates `True`. Second, `hazard_to_delta` maps a *perfect* recovery of a planted 0.010 hazard effect to `implied_delta` 1.00 against a Liebersohn–Rothstein band ceiling of 0.1925 — roughly 5× outside — but `selftest()` never calls `triangulate()`, so the defect never surfaced. The selftest's own failures are diagnostic of the harness, not the data: IV `theta` returns `None` under rank deficiency because the selftest plants `dti = 35.0` and `log_upb = 12.0` as scalar constants beside an explicit constant term; RD returns τ = −0.0907 against a planted +0.010 because the notch windows `[c−20, c)` tile with cutoffs spaced 20 apart, so 6 of 7 cutoffs carry zero planted first stage.

**No recovery path exists.** The Google Drive mirror returns 404 on `files.get` and 403 on `files.list` — API keys reach only publicly-shared content. The "Fannie 3, 6 comparison" folder is TBA/pool-level, five CSVs under 4 KB, and its own README states the project runs on synthetic and sample data.

**The pre-committed fallback, now carried.** The elasticity is retained and labelled an **explicit calibration**, imported from Liebersohn and Rothstein, with its band propagated rather than a point imposed. This is what v17's abstract already said; what changes is that the paper can now state *why* no internal measurement replaces it, with the censoring boundary named and the two failed designs reported at their own numbers rather than omitted.

### 2.2 Timing — `CONCEDE_LEVELS_ONLY`

The B0 gate **passed** on the full 102-month panel: Shapley rate share 0.43567594956287653, against `TIMING_RATE_SHARE_MIN = 0.15`, robust to dropping the refinancing wave (0.2857) and under log-CPR (0.5055), with `final_verdict: TIMING_FIXABLE`. These are carried in `hazard/data/b0_variance_decomposition.json`.

Three disclosures attach to that pass. An earlier draft of this roadmap said all three were "carried in the artifact." That was true of one, false of two, and on the second it inverted what the artifact actually records:

1. **The Shapley specification is not the frozen one.** *Carried in the artifact* — `method_prefixed_before_results` states the method, and `adjudicated_on` reads `'SHAPLEY rate share, FULL PANEL'`.
2. **On the persisted figure the QT window does not concede — it passes.** The artifact records `qt_window.shapley_rate_share = 0.308004956596408` with `verdict_vs_threshold = PASS`, roughly twice the 0.15 threshold. The 0.1216 QT concede reported earlier is the frozen `timing_step0` scoring from the pre-registered harness, a different computation from this decomposition; it appears in **no file in the repo** and is **session-computed and unpersisted**. It must not be quoted as the artifact's QT result, because the artifact's QT result points the other way.
3. **First-differencing (0.0877) is likewise session-computed and unpersisted.** No artifact records it. That it "fails" stands only as a session note.

**The QT verdict is nonetheless genuinely fragile — and for a reason the artifact does record, which the earlier framing missed entirely.** `robustness_and_disclosure.LAG_CONSTRUCTION_FRAGILITY` shows the QT verdict flipping on **lag construction alone**. Drawing the 0–3 month rate-gap lags from pre-window panel history (correct; no missing data) gives n = 40, Shapley rate share 0.308, **PASS**. Building the identical lags inside the window gives n = 37, Shapley rate share 0.0966, **CONCEDE**. The three months lost to in-window lagging are 2022-06, 2022-07 and 2022-08 — the three highest-CPR months in the window (7.569 / 6.168 / 6.240 percent) — so the construction choice deletes precisely the variation the rate block explains, and the seasonal $R^2$ rises from 0.7554 to 0.8746 as the rate $R^2$ falls from 0.4296 to 0.1190. The full panel is immune: it loses only 2017-01..03, panel-start ramp artifacts excluded regardless. The artifact notes the in-window leg reproduces the feasibility scout's QT numbers to 3–4 dp.

A referee should be told this plainly: the QT-window pass survives one defensible lag-construction choice and dies on the other, which is exactly why the pre-committed adjudication was fixed on the full panel rather than the QT window. It does not disturb the full-panel pass, which is the adjudicated one, and which no lag-construction variant flips.

Four floor legs were then run, each reproducing its parity anchors bitwise:

| leg | marginal ($B) | marginal (pp) |
|---|---|---|
| `flat_4.0` (production) | 70.345060 | 9.198460 |
| `flat_4.5` | 57.641550 | 7.537324 |
| `shape_only` | 65.448348 | 8.558156 |
| `prereg_4.5` | 54.304592 | 7.100976 |

Wiring is bitwise against production: `flat_4.0` reproduces central 818.5300844066606, null 748.1850239867648, marginal 70.34506041989584 and 9.198459770709789 pp; `flat_4.5` reproduces 57.641550459468476. An independent verifier ran the microsimulation unpatched and obtained bit-identical paths.

**The frozen timing rule was met as written, and nothing is claimed from the pass.** This is the round's headline finding and I state it without softening. The rule — `U2 < 1 AND detrended lag-0 r > 0` — is satisfied by both seasonal legs: `shape_only` at U2 0.994686, r +0.015858; `prereg_4.5` at U2 0.989630, r +0.069768. `frozen_rule_met_as_written = true` in `hazard/data/b3_timing_scores.json`. The rule was frozen before the runs, it passed, and it was not edited afterwards. Seven diagnostics computed *after* the pass show the rule has no discriminating power, and they are reported in full rather than used to reopen the rule:

1. **A β₁ = 0 null clears it, with a stronger correlation.** The `flat_4.0` and `flat_4.5` null legs — the mechanism removed entirely — score U2 0.9996906953295555 and r +0.11491905190190911. A criterion that a specification without the lock-in mechanism satisfies more strongly than the specification with it cannot evidence the mechanism. This alone is decisive.
2. **Wrong-month rotation placebo.** With `h_rot_k[m] = h[(m−k) mod 12]` — the true calendar profile moved to the wrong months, amplitude and dispersion held exactly — 1 of 11 non-identity rotations clears the rule for each seasonal leg, and rotation +5 **beats** the true profile on U2 (0.993449 against 0.994686). The pass rate across rotations is the placebo size of the rule.
3. **Benchmark artifacts carry the pass.** Four exact-zero benchmark months (2022-06, 2023-02, 2024-04, 2025-09) touch 7 of 41 first differences yet carry 0.8130 of RMS(d_emp)². Repairing them flips **the two seasonal legs** — `shape_only` and `prereg_4.5`, the only two that passed — from pass to concede, and turns `shape_only`'s correlation from +0.015858 to −0.133504. It flips **two** legs, not four: `hazard/data/b3_timing_scores.json` records `artifact_concentration.n_legs_flipping_to_concede = 2`, and the two constant-floor legs `flat_4.0` and `flat_4.5` carry `verdict_original = "CONCEDE"` with `flips_to_concede = false` — they were already conceding before the repair, so there is nothing there to flip. An earlier draft of this roadmap said "all four," which credited the repair with two verdict changes that never occurred.
4. **Correlations are indistinguishable from zero.** p = 0.921 and 0.661 on n = 42, against a 2/√42 band of ±0.309.
5. **Leave-one-out asymmetry.** `shape_only` flips on 5 of 42 single-month deletions; `prereg_4.5` flips on none.
6. **Frequency-band mismatch.** The seasonal legs place 79.7% and 89.4% of simulated detrended variance in the 12-month harmonic, where the benchmark carries 0.8% of its own.
7. **Scrambled calendars clear it.** 3 of 14 seeded permutations of the same twelve floor values satisfy the rule.

Every claim in the paper is therefore restricted to **levels**. The pre-committed fallback is the one carried.

**The four zeros are a bucketing artifact, and repairing them strengthens the paper's existing conclusion.** They arise in the SOMA back-out, where `resample('ME').last().diff()` mis-keys month boundaries; this is mechanically confirmed for 3 of the 4. 2022-06 is different — its own −$19.406B paydown on 06-29 netted against a +$20.12B settlement inflow on 06-15. Repairing them moves ABM U2 from 1.2256 to 2.9348, path A from 1.0096 to 1.3964, path B from 1.0029 to 1.0198: all still above 1, and more decisively so. Denominator inflation is 4.44–4.60×. An earlier 2.11× figure was a variance-versus-RMS units error and is superseded.

---

## 3. Two corrections to previously-reported results

This section is where the paper changed, as against merely failing to improve, and it is the section a referee should read first.

### 3.1 The seasonal floor's movement is floor dispersion, not seasonality

The −$4.8967 billion I attributed to a "shape effect" is not calendar structure. **14 seeded scrambles of the same twelve floor values retain 89.2% of the effect on average** (range 69.9%–102.8%), and 3 of the 14 clear the frozen timing rule. Calendar order is nearly irrelevant to the marginal.

The mechanism is `FLOOR_MODE = 'max'` (`hazard/config.py:52`) with `floor_bind_share` 0.363. Under `max(h_floor, h_vol)`, the floor is truncated away in low months and binds in high ones, so *any* dispersion in the floor raises the effective hazard one-sidedly — a Jensen-type effect that is indifferent to when the dispersion occurs. The convexity-matched flat level, 4.008957%, measures a marginal of $70.156383B against `flat_4.0`'s $70.345060B, so **level leakage is 3.9% of the shape effect and floor dispersion is 96.1%**.

Level and shape do not additively separate: the interaction carries 30.85% of total path-wise monthly movement. Any level/shape decomposition of this floor must carry its interaction residual; quoting level and shape without it misstates both.

### 3.2 The committed `floor_cyclical` κ grid was mislabelled as bounding cyclicality

**This corrects a result that appeared in earlier versions of the paper.** The κ grid was reported as bracketing the marginal's sensitivity to floor *cyclicality*. It does not. It brackets sensitivity to within-run floor *dispersion* under the hard maximum.

The verdict recorded in `hazard/data/floor_cyclical_permutation_results.json` is its `verdict` field, quoted here in full:

> RANGE IS PREDOMINANTLY ORDER-FREE: the committed kappa grid bounds the marginal's sensitivity to within-run floor DISPERSION under the hard maximum, not its co-movement with the rate cycle; a genuine but small cyclicality component survives

An earlier draft of this roadmap rendered this as "Verdict: `ARTIFACT_PARTIAL`, three verifiers, zero refutations." No part of that traces to the repo. `ARTIFACT_PARTIAL` is a session-level shorthand and is not a field in any artifact; the "three verifiers, zero refutations" tally was session bookkeeping with no artifact backing. Both are withdrawn as attributions — verifier counts are not artifact fields and are not cited as such anywhere in this roadmap.

Parity is bit-exact on all seven committed cells (68.078268 / 70.928467 / 71.579067 / 70.345060 / 67.684635 / 62.607698 / 54.256434 $B), with an independent second gate: additive-mode κ = 0 reproduces 86.022492 $B, matching `floor_form_results.json` additive @ 4%.

- **84.96% of the committed range span survives destroying time order.** 72 permutations, twelve per non-zero κ, span +7.198683 to +9.123154 pp against the committed +7.094679 to +9.359821 pp.
- **98.03% of the span is eliminated by the combination rule alone.** Under `FLOOR_MODE = 'additive'` the identical κ grid collapses to +11.220844 to +11.265427 pp — a span of 0.044583 pp. The additive grid moves *less* across the whole of κ than the constant-floor 3–5% level sweep moves under additive (0.084506 pp).
- **Endpoint decomposition.** The low endpoint (κ = +0.5) departs −$16.0886B from production: level −$2.1413B (13.3%), order-free dispersion −$11.4211B (71.0%), genuine time-order −$2.5263B (15.7%) — 84.3% order-free. The high endpoint is not an endpoint: κ = −0.1 departs +$1.2340B, +0.161 pp, and *is* essentially production.

**A false invariant is corrected.** I previously stated that the window mean is pinned at the production 4% across the grid. That fails at |κ| = 0.5, where the ≥ 0 clip binds: realized means are 4.000519% and 4.082786%, and the convexity-matched flat for κ = +0.5 is 4.097653%. These are exactly the cells that set the low end of the bracket, so the invariant failed where it mattered most.

**Cyclicality is real and small — I do not overclaim its absence.** The true marginal lies outside the full 12-draw permutation range at all six non-zero κ (0 of 72 draws bracket it), the order components are monotone and sign-consistent (+5.289 / +4.766 / +2.691 $B at κ = −0.5 / −0.25 / −0.1; −1.420 / −1.751 / −2.526 $B at +0.1 / +0.25 / +0.5), and the component is capped at **$5.29 billion** in any cell. There is a co-movement effect. It is bounded, and it is not what the range was measuring.

**The headline is not exposed.** A neighbour-exposure audit was run over every module that touches the floor. `hazard/floor_sweep.py:124`, `hazard/floor_form_test.py:80` and `hazard/oos_identification.py:258` each set a **scalar constant floor per run**, so within-run dispersion is identically zero and a time-order permutation is a literal no-op. The v17 headline — the off-window floor marginal of **+5.57 pp / $42.6 billion** — is not exposed to this confound. The two exposed modules are `seasonal_floor_timing` and `floor_cyclical` itself, both of which are now written up as dispersion results.

**Sites changed for this correction:**

| site | change |
|---|---|
| `paper/v17/revised_paper_v17.tex:320-322` | Section V.C: the κ range is no longer read as cyclicality; decomposition, additive collapse and endpoint split added |
| `paper/v17/revised_paper_v17.tex:512` | `tab:uncertainty` row relabelled "cyclical floor" → **"within-run floor dispersion"** |
| `paper/v17/revised_paper_v17.tex:517` | tablenote stating the row does not bracket cyclicality, with the 85.0% / 98.0% figures and the $5.29B cap |
| `paper/v17/revised_paper_v17.tex:838-865` | new subsection `sec:robustness-seasonalfloor` + `tab:seasonalfloor` |
| `paper/v17/revised_paper_v17.tex:909`, `:931`, `:998` | next-steps, referee-artifact and module-inventory entries restated |
| `TECHNICAL.md` §24.1 | correction marker; original entry superseded |
| `TECHNICAL.md` §24.1a | new — full re-diagnosis of the `floor_cyclical` range |

---

## 4. Closed versus still open

### Closed, with evidence

- **Identification on this data.** Not "not yet attempted" but *not feasible*, for a reason that is structural and named: the loan-level sample and the market-rate series are disjoint in time by construction. Any future attempt requires re-ingesting loan-level data past 2022-05, which the current pipeline censors at source.
- **Monthly timing.** The frozen rule passes and is not claimed, on placebo evidence. No estimator here models monthly variation, and the paper says so rather than implying otherwise.
- **Floor-dispersion attribution.** What the seasonal floor and the κ grid actually measure is now established, decomposed, and bounded, with the headline's non-exposure verified module by module.

### Open, and **not** addressed by this round

I did not touch any of the following, and nothing in this round should be read as bearing on them:

- **The upper-bound-benchmark framing** (major flaw 3). The benchmark against which the marginal is scored remains an upper bound, and the consequences of that for the headline's interpretation are unaddressed.
- **Danish sign-fragility** (major flaw 5). The $61.2 billion institutional-gap equality holds against the *demoted* in-sample point, not against the v17 off-window headline. That mismatch is live and untouched.
- **The unmodelled equity/CLTV channel.** No equity or combined-LTV channel enters the hazard; borrowers' equity position is absent from the mechanism.
- **The Ginnie extrapolation.** The conventional-share overlay stands as built; its extrapolation to the SOMA book is not re-examined here.

Two further items carried from prior rounds also remain open and were not revisited: the vintage residual's proxy assumption (observed Fannie segment speeds standing in for the SOMA book's), and the 80% → 49% expectations-shortfall propagation.

---

## 5. Reproducibility

### New modules

| module | what it produces |
|---|---|
| `hazard/seasonal_floor_timing.py` | Four floor legs, the permutation and rotation placebo families, the convexity-matched flat control, the level/shape/interaction decomposition |
| `hazard/b3_timing_rescore.py` | Placebo scoring of the frozen timing rule: null legs, rotations, artifact concentration, leave-one-out, frequency bands |
| `hazard/floor_cyclical_permutation.py` | Bit-exact reproduction of all seven committed κ cells, 12 permutations per non-zero κ, additive-mode grid, flat-equivalent controls, endpoint decomposition, neighbour-exposure audit |

### New artifacts

- `hazard/data/seasonal_floor_timing_results.json` — `parity_gates_all_pass: true`, `parity_gates_bitwise: true`
- `hazard/data/b3_timing_scores.json` — `verdict: CONCEDE_LEVELS_ONLY`, `frozen_rule_met_as_written: true`, `frozen_rule_has_discriminating_power: false`
- `hazard/data/floor_cyclical_permutation_results.json` — `parity_gate_bitexact_all_pass: true`, seed 20260719, runtime 805.7s
- `hazard/data/b0_variance_decomposition.json` — `final_verdict: TIMING_FIXABLE`, full-panel Shapley rate share 0.4357 `PASS`, `qt_window.shapley_rate_share` 0.3080 `PASS`, plus the `LAG_CONSTRUCTION_FRAGILITY` disclosure. **Provenance caveat:** this artifact was computed in-session and was sitting only in the scratchpad; it was promoted into `hazard/data/` this session so that §2.2's figures have a home in the repo rather than being quoted from nothing. Its generator (`b0_decomp.py`) has **not** been promoted — it remains a scratchpad script writing to a scratchpad path and fetching `MORTGAGE30US` from FRED at run time. So the artifact is inspectable but not yet regenerable from a clean checkout, and no liveness gate reads it. Promoting the generator in the house idiom (repo path, artifact under `hazard/data/`, gate binding it to the manuscript) is the obvious follow-up and is not done here.

### Parity anchors reproduced bit-exactly

| anchor | value |
|---|---|
| `flat_4.0` central trapped | 818.5300844066606 $B |
| `flat_4.0` null trapped | 748.1850239867648 $B |
| `flat_4.0` marginal | 70.34506041989584 $B / 9.198459770709789 pp |
| `flat_4.5` marginal | 57.641550459468476 $B |
| κ grid, all seven cells | 68.078268 / 70.928467 / 71.579067 / 70.345060 / 67.684635 / 62.607698 / 54.256434 $B |
| additive κ = 0 cross-tie | 86.02249228630046 $B against `floor_form_results.json` |

### Gates

Gates **#58** (seasonal floor timing) and **#59** (floor cyclicality attribution) are new. Total: **58 gates, all PASS**. **48 pytest tests pass.**

Both new gates were hardened against a defect the first drafts carried. As originally written they **read the modules' own headline aggregates** — for instance `fcp_h["n_kappa_cells_with_true_outside_permutation_range"] == 6` — so a module that miscomputed its own summary would have been confirmed rather than caught. Every such read is now replaced by a value the gate **recomputes from per-cell and per-draw primitives**, with the stored aggregate additionally required to equal the derived one, and the `.tex` literal compared against the *derived* value rather than the stored field. Gate #59 re-derives the committed, permuted, additive and flat-equivalent spans, the pooled n as a sum of per-cell counts, both headline shares as ratios of derived spans, the outside-range count by re-evaluating the range test per cell, max|time-order| over per-cell components, the clip-bound count, and the `grid_ranges` cross-consistency. Gate #58 re-derives the permutation retention mean/min/max from the 14 raw draw marginals, the clearing-permutation count and membership from re-evaluated verdicts, the best permutation U2, both rotation families' wrong-month pass counts (excluding the identity, re-running the rule), the pass rate, the "beats true on U2" map, and the true shape effect as `shape_only` minus `flat_4.0`. Per-cell identities must close arithmetically for every κ.

### Standing limitation

`paper/` is gitignored (`.gitignore:21`), so the manuscript is untracked and **has no git baseline**. The `.tex` cannot be diffed against a commit. Working practice this round was to back the file up to a scratchpad before editing and diff against that backup; that is a convention, not an enforced guarantee, and it does not survive a session boundary. Placing `paper/` under version control would retire this, and until it is retired, manuscript changes are verifiable only through the liveness gates' literal checks.

---

## 6. Response-letter section

*Draft for lifting into a letter, light editing expected.*

### On the imported elasticity (Referee comment: identification)

The referee is right that the rate-gap elasticity central to this paper's estimate was not measured on the data the paper uses. I attempted to measure it, by instrumental variables on origination vintage and by regression discontinuity at the FICO pricing notches, and I report that both designs fail — for a reason that is structural rather than incidental, and that I had not previously stated.

The loan-level sample is censored by construction at 2022-05: the sampling code filters to reporting periods strictly before the QT start of 2022-06, and no observation survives past that boundary. The only monthly market-rate series available spans 2022-06 through 2025-11. The two artifacts are exactly disjoint in time, so no design requiring a post-censoring outcome can be estimated here, whatever its instrument. This holds on the Fannie replication sample as well. Within that constraint, the discontinuity design also fails on its own terms: maximum first-stage F is 3.36–3.38 across 42 cutoff-by-bandwidth specifications, against a pre-registered floor of 10, on windows of 2,700 to 23,000 loans — there is no first stage rather than an underpowered one. FICO does shift the note rate (−0.395 bp per point, t = −59.8); it does not shift it discontinuously. The vintage instrument is degenerate at annual resolution and merely weak at quarterly, and fails regardless for want of an outcome.

The paper therefore retains the Liebersohn–Rothstein elasticity and labels it what it is: an **explicit calibration**, imported and propagated across its full band rather than imposed as a point. That labelling was already in v17's abstract. What is new is that the paper now states why no internal estimate replaces it, names the censoring boundary that forecloses one, and reports both failed designs at their own numbers rather than omitting them. I do not claim the elasticity is identified here. I claim it is imported, bounded, and honestly flagged, and that identifying it requires loan-level data this pipeline does not currently retain.

### On monthly timing (Referee comment: no estimator beats a naive forecast)

The referee's observation stood, and this round tested whether a floor with calendar structure repaired it. It does not, and the way it fails to is the more useful result.

I pre-committed a timing criterion before running — Theil's U2 on first differences below 1, and a positive detrended contemporaneous correlation — and both seasonalized legs **met it as written** (U2 0.9947 and 0.9896; r +0.016 and +0.070). I am not claiming the pass, and I want to be explicit that I am not retroactively rewriting the rule. It was frozen ex ante, it passed, and it stands recorded as having passed. What I ran afterwards was a placebo battery, and it strips the criterion of discriminating power. A β₁ = 0 null — the lock-in mechanism removed entirely — clears the same rule with a *stronger* correlation (U2 0.99969, r +0.115). A wrong-month calendar rotation clears it, and one rotation beats the true profile on U2. Scrambled calendars clear it in 3 of 14 draws. Four exact-zero benchmark months, artifacts of monthly bucketing in the SOMA back-out, carry 81.3% of the first-difference variance the criterion is scored against; repairing them flips both legs that passed — the two seasonal legs — to concede, the two constant-floor legs having been conceding already. The correlations are statistically indistinguishable from zero on 42 months. A criterion that a mechanism-free null satisfies more strongly than the mechanism itself cannot evidence the mechanism, and I decline to claim anything from having met it.

Accordingly, every claim in the paper is now restricted to **levels**. I make no monthly-frequency timing claim, and Section V states that the empirical path's variation at that frequency is seasonal rather than rate-driven and that no estimator here models it. Repairing the four artifact months in fact strengthens the paper's existing negative conclusion: U2 rises from 1.23 to 2.93 for the ABM, 1.01 to 1.40 for Path A, and 1.00 to 1.02 for Path B — all further above 1.

One correction follows from the same runs, and it changes a previously reported result rather than merely failing to improve one. The marginal movement I had attributed to the floor's calendar *shape* is not seasonality: scrambling the twelve monthly floor values retains 89.2% of the effect. It is a one-sided Jensen effect under the hard-maximum combination rule, in which floor dispersion lifts the effective hazard wherever the high cells bind, regardless of when. By the same mechanism, the κ grid I had reported as bounding floor *cyclicality* is bounding floor *dispersion*: 85.0% of its span survives destroying time order, and 98.0% of it vanishes under the additive combination rule. I have relabelled that row, corrected the section text, and corrected a stated invariant — that the window mean is pinned at 4% — which is false in exactly the two cells where the non-negativity clip binds, and which are the cells setting the bracket's low end. A genuine co-movement component does survive, monotone in |κ| and sign-consistent, bounded at $5.29 billion. The paper's headline is not exposed to any of this: every constant-floor run sets a scalar floor and therefore has identically zero within-run dispersion, which I verified module by module.
