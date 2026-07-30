# R32 CONDITION INVENTORY — EDITORIAL SYNTHESIS (Phase 2)

Source: `REVIEW3_v18_panel_2026-07-29.md` lines 1079–1326.
Verification baseline: **commit a785f3d** (the pre-R32 manuscript the panel reviewed), 1429 lines, mirrored to
`scratchpad/r32/baseline_a785f3d_v18.tex`. **All `.tex:NNN` line numbers below refer to this baseline.**

> **MOVING-TARGET NOTICE — R1 AND R2 LANDED DURING THIS PASS.** The worktree was mid-edit while I verified,
> and by the end of the pass two commits had landed on top of a785f3d:
> · **66df169** "R32 C-R1 (Task 1): abstract repairs" — R1(a)(b)(c), `.tex:31` in both abstract files.
> · **c2e505e** "R32 C-R2 (Task 2): basis-mix repair at the form-fork sentence — one basis, named" — `.tex:709`.
> The tree is clean again at c2e505e. **Both landings verified against the artifacts (see C-SY-32/33 and C-SY-14/34);
> neither is to be re-applied.** Line numbering is unaffected: the file is still 1429 lines, only lines 31 and 709
> differ from a785f3d, and I re-checked byte-identity at every anchor line this inventory cites
> (24, 146, 244, 269, 319, 361, 404, 417, 457, 546, 741, 758 — all `same`), so every `.tex:NNN` below remains valid at c2e505e.
> Two follow-ons survive the R1 landing and are the coordinator's next wording items — see **C-SY-33**.

Table-number ↔ label map (recovered from `paper/v18/build_split/revised_paper_v18.aux`, authoritative):
T1 `tab:headline` · T3 `tab:params` · T5 `tab:assembly` · T6 `tab:oosfloor` · T7 `tab:lowband` ·
T8 `tab:uncertainty` · T9 `tab:ladder` · T12 `tab:wal` · T13 `tab:danish` · T25 `tab:composition` · T27 `tab:verdicts`.

Section-letter ↔ label map: §I `sec:intro` (38) · §III.B `sec:method-benchmark` (135) · §V.B `sec:pathb` (217) ·
§V.D `sec:patha` (311) · §V.E `sec:identification` (317) · §V.F `sec:hazard-interp` (469) · §VI.A `sec:discussion-fallout` (534) ·
§VI.B `sec:discussion-capdesign` (544) · §VI.D `sec:abm-danish` (582) · §VII.F `sec:robustness-floor` (703) ·
§VIII `sec:conclusion` (719) · App. E `app:params` (1011) · App. F `app:patha-detail` (1089) · App. G `app:ridge` (1168) ·
App. I `app:composition` (1265) · App. O `app:verdicts` (1393).

---

## PART A — ARBITRATED CONSENSUS CONDITIONS (X1–X9)

### C-SY-01
raiser: Synthesis
synth_ref: X1 / DA:C2 / R5 / R1(c)
raisers_upstream: R1:M5, R2:M7, DA:C2, R3 (rigor basis) — 4 of 5
severity: CRITICAL (DA, uniform) -> **CRITICAL at abstract + T1, MAJOR in body** (§2.3 arbitration; severity SPLIT by site)
class: RUN (+ WORDING at the two Critical sites)
panel_lines: 1097, 1165–1169, 1236, 1266–1267, 1287
condition: The 100-PSA baseline seasoning ramp is a convention, not an estimate, and at the headline floor it carries the marginal +0.86 → +15.63pp (width 14.770) against the binding interval's 5.823 — ratio 2.492×. The abstract and T1 must stop presenting +2.9/+8.7 as an unqualified bound; the body already discloses it.
location: abstract `.tex:31`; T1 `tab:headline` uncertainty cell (`.tex:67`); T8 `tab:uncertainty` headline row (`.tex:422–468`, already carries `75--150` and `15.6`); §V.E `.tex:417`
verified: **true** — `psa_level_sweep_results.json` `ranges["4.991"]` = `{lo_pp: 0.8560355409769471, hi_pp: 15.626488479897219, width_pp: 14.770452938920272}`; `expectation_check` is 0-for-3 off-window (`4.991|75` realized 0.856 vs band [1.5,2.5]; `4.991|125` 11.419 vs [8.5,10.0]; `4.991|150` 15.626 vs [11.0,14.0]) and 3-for-3 inside at floor 4.0. Body candour confirmed: `.tex:417` prints "binding among the layers with a coverage property" and T8 prints the `75--150` row.
fix: (i) WORDING — abstract + T1 adopt §V.E's qualified formulation (see C-SY-33, already applied in the working tree). (ii) RUN — **R5**: re-anchor h₀ on Path A's *estimated* seasoning spline, knots {12,24,36,60,84,120}, and report the paired-leg marginal there; machinery = the `psa_level_sweep` harness with h₀ supplied by Path A instead of the PSA table; writes a new artifact alongside `psa_level_sweep_results.json`. Synthesis states no pre-committed band, only that this "flips the sign of that trade" (line 1236) — so the spec must pre-commit a band before running.

### C-SY-02
raiser: Synthesis
synth_ref: X2 / R11
raisers_upstream: all five
severity: MAJOR (no change)
class: STRUCTURE
panel_lines: 1098, 1226, 1293
condition: The four longest prose paragraphs are 14,732 / 11,312 / 10,696 / 8,051 chars; the 14,732-char one opens the subsection referees are directed to first. Paragraph architecture must be split so the qualification load is readable.
location: 14,732 = `.tex:219–231` (§V.B `sec:pathb`); 11,312 = `.tex:319–323` (§V.E `sec:identification`); 10,696 = `.tex:1099–1100`; 8,051 = `.tex:269` (§V.B)
verified: **partly** — all four character counts reproduce **exactly** under blank-line-delimited paragraph measurement on the HEAD baseline. The synthesis attributes 10,696 to **App. G**; it is in fact **App. F** (`app:patha-detail`, 1089–1167; App. G `app:ridge` starts at 1168). Magnitudes exact, third location label off by one appendix.
fix: R11 — split §V.B at its five seams (specification / floor semantics / elasticity import and its three transports / aggregation bounds / ablations); move the competing-risks taxonomy to App. E; split §V.E (`.tex:319–323`) and the App. F monolith (`.tex:1099–1100`); fold §VI.C (`sec:discussion-policy`, 578) into §VI.B. No content deleted.

### C-SY-03
raiser: Synthesis
synth_ref: X3
raisers_upstream: EIC:W5, DA:M1+M2, R1:M5-fix, R3:M5 — 4 of 5, three independently
severity: MAJOR (no change)
class: WORDING (posture decision)
panel_lines: 1099, 1225, 1235, 1267
condition: +5.6pp is defended as "an anchor convention rather than a central tendency" and then used as a result. Either drop the point and print the range, or state and defend an anchor rule that survives the paper's own five well-supported reads.
location: disclaimer at `.tex:79` (§I); +5.6 printed at `.tex:31` (abstract), 46, 58, 79, 92, 110 (§I), 211, 323 ×3, 333 ×2, 342, 345, 368, 433, 524, 625, 635, 711
verified: **partly** — the disclaimer string "anchor convention rather than a central tendency" is at `.tex:79`, and +5.6 appears at all the listed prose/table sites. **The "Table 12" citation is FALSE**: T12 is `tab:wal` (Approximate SOMA portfolio WAL by prepayment scenario); its two `5.6` occurrences are WAL **years** ("Production ABM (11.68%) & 6.0 & 5.6"), not +5.6pp. The tables that do print +5.6pp are T1, T5 (`.tex:333–345`), T6 (`.tex:368`) and T8 (`.tex:433`).
fix: Choose one posture and carry it to every one of the sites above. Note the synthesis's own §4 verdict (line 1235): half-retiring the posture while keeping +5.6 was **net negative** on coherence. Do not cite T12 in any repair note.

### C-SY-04
raiser: Synthesis
synth_ref: X4 / R15
raisers_upstream: EIC:W1, DA:m1, R3 (coherence)
severity: **Minor -> Minor-Major** (arbitration widened it; §5 keeps it out of the three Major-holding reasons)
class: WORDING (title) + REFERENCE (internal coherence)
panel_lines: 1100, 1297
condition: The title and abstract assert a "Shortfall" that §III.B expressly declines to call a policy miss, while §VI.B then computes the cap as "1.7 to 1.9 times as high as the Federal Reserve's own contemporaneous projection".
location: title `.tex:24` ("Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"); §III.B `.tex:146`; §VI.B `.tex:546`
verified: **true** — `.tex:146` contains verbatim "not by itself evidence that a stated policy objective was missed"; `.tex:546` contains "the \$35 billion cap was set roughly 1.7 to 1.9 times as high as the Federal Reserve's own contemporaneous projection of achievable runoff".
fix: R15 — retitle to the claim the paper establishes, e.g. "…Redemption-Cap Shortfall" or "Mortgage Lock-In and the Composition of the Federal Reserve's Agency-MBS Runoff". 5 min; required for submission, optional for the talk.

### C-SY-05
raiser: Synthesis
synth_ref: X5 / R12
raisers_upstream: R1, R2, R3:M2, DA — 4 of 5
severity: MAJOR (no change)
class: RUN (R12) / CHECK
panel_lines: 1101, 1294
condition: No outcome holdout exists anywhere; the behavioral margin is never tested against an external outcome moment. T6's note a is a temporal holdout of the *floor calibration*, not of an outcome.
location: global concession at `.tex:741` (§VIII); T6 note a at `.tex:381`
verified: **true** — `.tex:741` states verbatim "no outcome-holdout months exist anywhere in this paper" and calls the T6 note-a construction "The nearest construction"; `.tex:381` note a reads "Temporal holdout. The 3.97% floor is calibrated on … the window's first nineteen months … the central-minus-null marginal is $+\$45.1$ billion". The compared object is the model's own marginal, so the synthesis's characterisation (an input-stability check) is right in substance; the exact phrase "input-stability check" does not appear in the manuscript.
fix: R12 — report the marginal in **transaction counts** with the moving-share bracket applied, set against realized mortgage-financed transaction volume, and state the verdict whichever way it falls. 1 script. This is the paper's first outcome-side external check and the only unit in which the household leg becomes commensurable with the institutional one.

### C-SY-06 — **ARBITRATION-UPGRADED CRITICAL #1**
raiser: Synthesis
synth_ref: X6 / Z2 / R1(b) / R2 / DA:N1(refuted)
raisers_upstream: EIC:W6/W7, R1:M6, R3:M2/M6, DA:A1 — 4 of 5
severity: **MAJOR -> CRITICAL (§2.1, on the synthesizer's own arbitration)**
class: WORDING (abstract + §VII.F clause) — no run needed
panel_lines: 1102, 1143–1152, 1252, 1283
condition: The abstract's lead finding ("switch the lock-in response off and the model still accounts for 85.7% of it") is a **max-form** result. Under the additive form the β₁=0 null recovers only 35.6% shared / 44.7% standalone — a *minority*. The headline **qualitative** claim ("mostly mechanical") is form-conditional and unlabelled; a null at 35.6% does not decompose the object at all.
location: abstract `.tex:31`; §VII.F `.tex:709`; §VI.B `.tex:546` (which prints 88.7%/85.7% with no form label)
verified: **true** — `floor_form_mixture_results.json` `cells["4.991|1|0"]`: `trapped_b = 341.83938974816874`, `share_pct = 44.69959732600039`; `cells["4.991|1|6.5"]`: `trapped_b = 427.54488764725437`, `share_pct = 55.90661839965657`, `marginal_b = 85.70549789908563`, `marginal_pp = 11.207021073656186`. Null = 427.545 − 85.705 = 341.839 ✓. Shared basis = (341.839 − 69.562)/764.748 = **35.6035%** ✓ (derivation in `## COORDINATOR DERIVATIONS` §2). Form fork roughly doubles the marginal: 5.5716 (s=0) → 11.2070 (s=1) = 2.011× ✓.
fix: **The highest-leverage sentence-level repair in the report.** One clause in the abstract labelling 85.7% as a max-form result and giving 35.6% (shared) in the same clause, plus one sentence in §VII.F. Already applied in the working tree — see C-SY-33.

### C-SY-07 — **ARBITRATION-UPGRADED CRITICAL #2** (upheld from DA, narrowed)
raiser: Synthesis
synth_ref: X7 / DA:C1 / Z3 / R3 / R7
raisers_upstream: R1:M2/M4, DA:C1, EIC (evidence rationale), R2:M3 (opposite sign) — 4 of 5
severity: **CRITICAL — DA:C1 upheld and called "the panel's most consequential finding"; DA's "confining them to a note" characterisation NARROWED as imprecise (§2.2)**
class: CHECK + WORDING (disclosure), with R7 as the RUN leg
panel_lines: 1103, 1153–1163, 1251, 1272–1273, 1285
condition: The floor read's evidential base is 137 cohort-months in 31 clusters (5.87 effective, h_max 0.332), all aged 12–24 in six months of 2018 on one vintage, broadcast as a constant to a book aging 2→162 months; and two independently measured corrections (age-standardized 5.51%, Fannie 5.52%) both sit above the clean band's top of 5.334%. Turnover rises steeply with seasoning, so the read is signed toward understating the null and overstating the marginal.
location: `.tex:323` (§V.E, quotes 4.991 and 4.695); T6 `tab:oosfloor` caption `.tex:361`; T8 `tab:uncertainty` `.tex:422–468`; §VII.F `.tex:709–714`
verified: **true** — `floor_inference_correction_v2_results.json` `reads["R2_2018_gap<=-0.0025_age>=12"]`: `n_cohort_months = 137`, `n_clusters = 31`, `h_max = 0.3323311750696546`, `G_star_css = 5.871713810074106`, `point_cpr_pct = 4.990624060575566`. `oos_identification_results.json` pooled-2017–2019 leg: age≥12 6.065% vs age≥24 **10.995%**; at matched depth −0.0025, 5.185% vs **8.92%**; `ramp_rise_is_psa_confounded: true`. 2018 leg `contamination.verdict = "CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE"`, `mature_test_computable: false` (the age≥24 cell has 0 cohort-months). `b5_joint_cell_results.json`: `agestd_floor_pct = 5.507748455937158`, `overlay_agestd.primary.marginal_pp = 2.928173869093058`, `adjudication.verdict = "LANDS_AS_COMPOSED_LOWER_MEMBER"`. DA's narrowing is correct: T8 does print both corrections (`5.51`, `5.52` both present in `.tex:422–468`).
fix: R3 (disclosure, no runs) + R7 (two runs). See C-SY-35 and C-SY-39. The synthesis's plainly-stated editorial finding (line 1163) is a WORDING condition in its own right: **the marginal's mass sits in the lower half of [+2.9, +8.7], and +5.6 is above the centre of the measured evidence, not at it.**

### C-SY-08
raiser: Synthesis
synth_ref: X8 / R14
raisers_upstream: R1:M7, R3:M2, DA (evidence), R2:M4 (adjacent) — 4 of 5
severity: MAJOR (no change)
class: RUN (analytic, no engine run) / CHECK
panel_lines: 1104, 1296
condition: The imported Liebersohn elasticity carries zero propagated uncertainty into the reported interval, and the one internal test of its implied magnitude misses by 4.5×.
location: `.tex:315` and `.tex:331` (§V.D/§V.E); `.tex:1170` (App. G)
verified: **partly** — the 4.5× miss is verified verbatim in the manuscript (`.tex:315`: "the realized gradient is roughly $4.5\times$ the model's, and the excess carries everything else that travels with coupon across cohorts"). The synthesis itself records X8 as "Artifact figures as reported by R1; **not independently re-run**" (line 1104), so the zero-propagation half rests on R1's read, not on the synthesizer's.
fix: R14 — recompute the analytic implied cross-sectional gradient at the 4.991% headline floor **and under the additive form**, at 75/100/125 PSA. Analytic; no engine run; under an hour. Would be the first *realized-data* evidence bearing on the form fork (C-SY-06).

### C-SY-09
raiser: Synthesis
synth_ref: X9 / Z7 / R9
raisers_upstream: EIC:W8, R2:M5/M6, R3:M3, DA:m2/A5 — all five
severity: MAJOR (no change)
class: RUN (1 calculation) + WORDING
panel_lines: 1105, 1171–1175, 1291
condition: The Danish leg is the weakest quantitative leg: one unrefereed source, a single-authored tax override, and a band reported as a point in T1.
location: T1 `tab:headline` Danish cell (`.tex:67`); §VI.D `sec:abm-danish` `.tex:582–622`; T13 `tab:danish` `.tex:605`; abstract `.tex:31` (omits it entirely)
verified: **true** — see C-SY-16 (Z7) for the priced magnitude and C-SY-46 (§8.6) for the exact scope of the "headlines the minimum" claim.
fix: R9 — see C-SY-41.

---

## PART B — TWO-REVIEWER CONDITIONS (Y1–Y3)

### C-SY-10
raiser: Synthesis
synth_ref: Y1 / R12
raisers_upstream: R3:M1, DA:S1 (EIC partial)
severity: MAJOR (no change)
class: STRUCTURE + RUN
panel_lines: 1111, 1294
condition: The bottom line sets a measured institutional quantity against an unmeasured household one, and T1 has no household row.
location: T1 `tab:headline` `.tex:60–95`
verified: **true** (structural) — T1's rows are institutional/benchmark quantities; no household-outcome row exists.
fix: R12's transaction-count metric is the unit in which a household row becomes commensurable. Add the row only once R12 lands; do not add an unquantified placeholder.

### C-SY-11
raiser: Synthesis
synth_ref: Y2
raisers_upstream: R3:M6, DA (framing), R2 (adjacent)
severity: MAJOR (no change)
class: WORDING
panel_lines: 1112, 1234
condition: "Mechanical" mislabels a null whose level is read off realized, partly behavioral turnover. The R29 rename to "baseline turnover floor" fixed the *wrong word* — no reviewer credits it, and two still attack "mechanical".
location: §V.B `.tex:227` (the floor-semantics concession); every site printing "mechanical baseline" / "mechanical model" / "mostly mechanical", incl. §VI.B `.tex:546` and the abstract `.tex:31`
verified: **true** — §V.B `.tex:227` concedes verbatim: "It floors total turnover, not a strictly involuntary component of it: deep-discount-cohort turnover at this level includes discretionary life-cycle moves and cash-out refinancings alongside strictly involuntary events". The working-tree abstract already hedges once ("itself read from realized, partly behavioral turnover"), so the concession exists at two sites but the noun "mechanical" is unchanged.
fix: Rename the *object*, not the floor: replace "mechanical baseline/model" with a term that does not assert non-behavioral content (e.g. "rate-insensitive baseline", "β₁=0 baseline"). Cheap; addresses the word two reviewers actually attacked.

### C-SY-12
raiser: Synthesis
synth_ref: Y3 / DA:M5
raisers_upstream: DA:M5, R1 (adjacent)
severity: **MAJOR (DA) -> MODERATE (§2.7 arbitration)** — "Partially upheld"; the remedy is a stated inclusion rule, not a disclosure
class: CHECK (assembly rule)
panel_lines: 1113, 1185–1187
condition: Survival-selection attenuation (+5.1/+4.6/+3.7 at a = 0.86/0.73/0.54) is signed downward ex ante and excluded from the T5 assembly. DA's logic is sound — the imported coefficient is attenuated in the survival-selected pool it is applied to — but T8 already prints the full grid, the frailty identity, the measured S, and the exclusion rationale in the same cell.
location: T8 `tab:uncertainty` `.tex:422–468`; T5 `tab:assembly` `.tex:338`
verified: **true** — the exclusion rationale is printed alongside the grid. Note the survival count: `attenuation_sensitivity_results.json` gives **40,234**, while `loan_sample.parquet` has **40,077** rows with `balance > 0` (see C-SY-48).
fix: State an explicit **inclusion rule** for the T5 assembly (what qualifies a signed correction for inclusion vs. disclosure-only) and apply it consistently. Do not simply move the attenuation grid into T5.

---

## PART C — SINGLE-REVIEWER HIGH-VALUE CONDITIONS (Z1–Z19)

### C-SY-13 — **ARBITRATION-UPGRADED CRITICAL #3**
raiser: Synthesis
synth_ref: Z1 / R6 / §2.5 / Carroll answer 2
raisers_upstream: R2:M1 only (one reviewer)
severity: **-> CRITICAL (§5, on the synthesizer's own arbitration; "worse than any single reviewer's rigor deduction credited"; R2's own label not stated in this section)**
class: RUN (R6) + STRUCTURE (disclose the sampler)
panel_lines: 1119, 1179, 1246, 1250, 1269–1270, 1288
condition: The 75,000-loan pool is not a probability sample of the SOMA book. `loan_sample.py:97` allocates equally per origination-quarter file, giving ~15,000 loans per vintage 2017–2021; every `weight` is 1.0; 2022 is absent. The sampler's allocation rule is nowhere in the manuscript. Under the max form the marginal is zero wherever the baseline sits below the floor, so vintage weighting is the **censoring geometry**, not a second-order composition detail.
location: `hazard/loan_sample.py:97` and `:169`; App. I `app:composition` `.tex:1265–1300`; T25 `tab:composition` `.tex:1272`; App. E `app:params` `.tex:1011`; §V.B `.tex:269`
verified: **partly — real, but the "factor of ten" framing is count-basis only and the aggregation basis narrows it materially.**
  · Code exact: `hazard/loan_sample.py:97` = `per_file = max(1000, pool_target // max(len(pairs), 1))`; `:169` = `pl.lit(1.0).alias("weight")`.
  · `loan_sample.parquet`: 75,000 rows; vintage counts 2017:15,002 / 2018:14,999 / 2019:15,001 / 2020:14,997 / 2021:15,001 = **20.00% each**; `weight` has exactly one distinct value, 1.0; vintage range 2017–2021 (2022 absent).
  · `composition_shift_results.json` `committed_anchors.vintage_shares`: 2017-19 **0.06**, 2020 0.163, 2021 **0.439**, 2022 0.231.
  · **Two corrections to the synthesis's numbers.** (a) "2021 at 22% of the draw" is the **orig-UPB-weighted** share (22.32%), not the count share (20.00%) — the same unlabelled-basis slip the synthesis convicts R2 of in §8.7. (b) §V.B `.tex:269` states verbatim that "Aggregation from the 75,000-loan sample to the SOMA book **applies balance weights**", and on current balance the draw is 2017:8.69% / 2018:6.83% / 2019:11.53% / 2020:30.65% / 2021:**42.31%**. So the *effective exposure* weights are 2017-19 = **27.05% vs 6.0% of book face (≈4.5×, not 10×)** and 2021 = 42.31% vs 43.9% of face (**nearly matched**). The synthesis's own §7-R6 rationale survives this — balance weighting "rescales aggregate output and cannot test a per-loan censoring effect" (line 1270) — but the *magnitude* rhetoric ("differs by a factor of ten", "sixty percent of the pool is 6.0% of the book") describes counts and must not be restated as an exposure fact.
fix: R6 — post-stratify the existing 75,000 loans onto the SOMA **coupon × vintage-group** cells and re-derive the marginal; machinery = the existing `cross_design_reweight` harness; writes a new post-stratified artifact. Plus: state the sampler's allocation rule in App. E and add the draw's own composition row to T25 — reporting **both** count and balance-weighted shares, since only the latter enters the aggregation. Synthesis states no pre-committed band. Required before submission; the Carroll slide (three columns: draw / estimation universe / book face) is the pre-talk deliverable.

### C-SY-14
raiser: Synthesis
synth_ref: Z2 / X6 / R2
raisers_upstream: R1:M6(i) only
severity: MAJOR — "same defect class Appendix A retracted"
class: WORDING (arithmetic-basis repair)
panel_lines: 1120, 1151, 1284
condition: The sentence that adjudicates the form fork mixes bases: it compares a **shared** 91.3% with a **standalone** 55.9%. Like-for-like is 100.4→55.9 (standalone) or 91.3→46.8 (shared). The mixed pair understates the additive form's level cost by ~9 points.
location: §VII.F `.tex:709` — the line contains `91.3\% to 55.9\%` and `44.7`
verified: **true** — `floor_form_mixture_results.json` at floor 4.991: max form (s=0) central `share_pct = 100.36328284662208` standalone → **91.2672%** shared; additive (s=1) central `share_pct = 55.90661839965657` standalone → **46.8105%** shared. Both like-for-like pairs check to 1 dp. The synthesis's partial defence also checks: `.tex:709` does print "55.9% … against a 44.7% null", standalone against standalone, so the additive null's level is not hidden.
fix: **LANDED in commit c2e505e — no further action.** `.tex:709` now reads "the central leg's **standalone-scorer** recovery falls from **100.4\%** to 55.9\%, the level cost the additive end pays", and the mixed `91.3\% to 55.9\%` string is gone (grep count 0). This is exactly the recommended standalone-standalone pair, consistent with the 44.7% null already on the line. Verified against `floor_form_mixture_results.json` `cells["4.991|0|6.5"].share_pct = 100.36328284662208`. The alternative shared pair (91.3 → 46.8, null 35.6) is no longer needed.

### C-SY-15
raiser: Synthesis
synth_ref: Z3 / X7 / R3
raisers_upstream: R1:M2 only
severity: MAJOR
class: WORDING (disclosure + caption correction)
panel_lines: 1121, 1273, 1285
condition: The floor read's support is undisclosed. "2018 + age≥12" selects **vintage 2017 only**, in **six reporting periods** (201807–201812; 2/48/48/49/49/49 rows), all cohort-months aged 12–24, while T6's caption says "(2017–2019 performance)".
location: T6 `tab:oosfloor` caption `.tex:361`; §VII.F `.tex:709–714`; the Definitions block
verified: **true, exactly** — `cohort_month_panel.parquet` filtered to `reporting_period` in 2018 and `mean_loan_age >= 12` returns **245 rows, all `vintage == 2017`**, periods `{201807:2, 201808:48, 201809:48, 201810:49, 201811:49, 201812:49}`, `mean_loan_age` 12.00–17.50. T6's caption at `.tex:361` contains verbatim "measured \emph{outside} the June 2022--November 2025 evaluation window (2017--2019 performance)". The headline read is the gap≤−0.0025 subset of these: 137 cohort-months (`oos_identification_results.json` 2018 leg, `cpr_pct = 4.991`).
fix: R3 — one disclosure sentence at every quoting site, and correct T6's caption **for the three defensible rows only** (the caption's "except the final row" carve-out already exists and must be preserved). State: vintage 2017 only, six reporting periods 201807–201812, all cohort-months aged 12–24 (observed max 17.5), mature test not computable, age-transport error signed against the headline. 1–2 hours, no runs. Do **not** say the floor is "measured on 2017–2019 performance" anywhere.

### C-SY-16
raiser: Synthesis
synth_ref: Z4 / R7(a)
raisers_upstream: R1:M3 only
severity: MAJOR
class: RUN
panel_lines: 1122, 1155–1159, 1289
condition: The read months are the descending half of the committed calendar profile. Weighting the profile by the read's own month counts gives **3.830%** against the **4.000%** pinned mean, so the annual-equivalent floor is ≈**5.21%** and the marginal ≈+4.7/+4.8 — a −0.8pp move, unpriced.
location: §VII.F `.tex:709–714`; T5 `tab:assembly` `.tex:338`; App. N `sec:robustness-seasonalfloor` `.tex:1342–1392`
verified: **true, reproduces R1's twelve numbers exactly** — `seasonal_floor_timing_results.json` `h_month_normalizations_annual_cpr.shape_only` (Jan–Dec, annual CPR %): 2.5036 / 2.7565 / 3.7502 / 4.2218 / 4.9374 / 5.2619 / 4.8135 / 4.7157 / 4.1301 / 3.9225 / 3.2517 / 3.1143. Weighting Jul–Dec by 2/48/48/49/49/49 (n=245) gives **3.830030%**; `h_month_exposure_weighted_mean.shape_only = 0.04000000000000001` (pinned 4.000%). Rescale: 4.991 × 4.000/3.83003 = **5.2124%** ✓.
fix: R7(a) — calendar-standardize the off-window read to the QT window's month mix using `seasonal_floor_timing`'s own normalizer; writes a new leg into the seasonal-floor artifact family. **Must be run together with R7(b)** (C-SY-17): the synthesis is explicit (line 1289) that "Running only (a) makes the paper worse-off honestly; running only (b) is self-serving."

### C-SY-17
raiser: Synthesis
synth_ref: Z5 / R2:M3 / R7(b) / §2.2
raisers_upstream: R2:M3 only
severity: **MAJOR — but the CHARACTER of the complaint is arbitrated DOWN (§2.2): the paper's sentence is "literally true" and the defect is FRAMING, not fact**
class: RUN
panel_lines: 1123, 1157–1159, 1289
condition: The off-window floor imports 2018's housing-activity level; up to 56% of the $20.874bn window component (~+1.5pp) may be cycle level rather than lock-in circularity. This is the assembly's **one available upward** floor-side correction, and it has never been run.
location: §VII.F `.tex:709–714`; T5 `tab:assembly` `.tex:338`
verified: **partly** — the window component is verified exactly: `matched_depth_reconciliation_results.json` `step3_decomposition.path_a_depth_first.window_component_b = -20.873648458129964` (= −2.7295pp), `depth_component_b = -7.437875622174431`, `window_share_of_total = 0.737284520569178`. The synthesis itself records that "the 24% activity ratio is R2's external datum, **not verified here**" (line 1123) and that R2's is "the only one that requires external data the repository does not hold" (line 1157). So the *existence* and *sign* of the correction are established; its *magnitude* is not.
fix: R7(b) — measure the floor's dependence on housing-activity level and report an activity-matched read. **Requires external housing-activity data the repo does not hold** — if that data cannot be obtained, record R7(b) as INFEASIBLE and say so, because R7(a) alone is the self-harming half. Also required regardless: repair the framing defect §2.2 upholds — the sentence "every correction I can measure … moves it down within the range rather than up" must not be readable as "the unmeasured ones do too."

### C-SY-18
raiser: Synthesis
synth_ref: Z6 / R10
raisers_upstream: R2:M4 only
severity: MAJOR
class: WORDING (1 sentence) + RUN (1 run)
panel_lines: 1124, 1292
condition: The Ginnie attribution is wrong on the window. Over the 42-month window CRR (voluntary) carries **63%** of the CPR gap and CDR **40%**; the manuscript quotes a May-2025 snapshot, the one month in which buyouts dominate.
location: §V.B `.tex:269` (the 8,051-char paragraph); §I; §VIII.A
verified: **true, computed independently** — `gmar_dec25_cpr_series.json`, months 2022-06…2025-11 (n = 42), Ginnie-minus-Freddie means: CPR **2.1365pp**, CRR **1.3541pp** (63.4% of the CPR gap), CDR **0.8475pp** (39.7%). Matches the synthesis's 2.137 / 1.354 / 0.847 and 63% / 40% exactly. Cross-checked against `ginnie_cpr_overlay_results.json` `gates.G3_static_bound.window_mean_ginnie_minus_freddie_pp = 2.1365238095238093`. The manuscript's snapshot is confirmed at `.tex:269`: "…5\% in May 2025 … with the involuntary buyout channel (CDR 2…4\% in May 2025) supplying most of the structural difference". The string "CRR" appears **nowhere** in the .tex, so R10's CRR content is entirely new.
fix: R10 — restate the attribution as a **window mean** (CRR 1.354 of 2.137 = 63%; CDR 0.847 = 40%; note the CRR+CDR identity residual, `cpr_vs_crr_cdr_identity_pp.mean_abs = 0.0398`), and score a Ginnie leg with the elasticity **attenuated by the observed CRR differential** rather than only share-scaled to zero; machinery = `ginnie_cpr_overlay` (which already has a `crr_only` variant: `marginal_pp = 7.333248797494442`). Add the assumability upper bound the CRR series supplies. Bears on the imported elasticity for 20.4% of book face (`committed_anchors.ginnie_share_of_soma_face = 0.204`).

### C-SY-19
raiser: Synthesis
synth_ref: Z7 / X9 / R9
raisers_upstream: R2:M5 only
severity: MAJOR
class: RUN (1 calculation) + WORDING
panel_lines: 1125, 1171–1173, 1291
condition: The Danish buyback discount D ∈ {0.32…0.38} is a **zero-prepayment** PV applied to a leg prepaying at 5.61% CPR. A prepayment-consistent D ≈ 0.21–0.24 roughly **halves every cash figure** (−$89/−$118bn → −$42/−$52bn). The `REVERSES` verdict survives; only the magnitudes move.
location: T1 `tab:headline` `.tex:67`; §V.B; §VI.D `.tex:582–622`; T13 `tab:danish` `.tex:605`; §VIII
verified: **true, independently priced by the synthesizer and re-checked here** — `buyback_credit_bracket_results.json`: `gap_face_b = 61.18833737010482`, `early_face_E_b = 470.65325285410216`, `cash_rows` D ∈ {0.32, 0.34, 0.36, 0.38} → `gap_cash_b` −89.421 / −98.834 / −108.247 / −117.660, `gap_cash_range_b = [-117.65989871445402, -89.42070354320788]`, `verdict.code = "REVERSES"`. Re-pricing at D = 0.22 / 0.24: 61.188 − 0.22×470.653 = **−42.36**; 61.188 − 0.24×470.653 = **−51.77** → −$42.4bn to −$51.8bn, exactly as stated. The artifact's own spec calls the grid "the manuscript's committed proxy range", i.e. it derives nothing.
fix: R9 — re-derive D from the leg's own 5.61% CPR against the window rate path (or matched-coupon TBA marks) and restate every dependent figure; headline the band [+$61.2, +$256.8]bn in T1's headline cell; add one sentence that the Danish mechanism is an open-market bond repurchase, so the par-denominated cap is not the natural scorer. 1 calculation + edits. **Do not quote −$89/−$118bn aloud until done** (R2's pre-talk precondition).

### C-SY-20
raiser: Synthesis
synth_ref: Z8 / R4
raisers_upstream: DA:M3 only
severity: MAJOR — "defect class has bitten twice"
class: WORDING + CHECK (new gate)
panel_lines: 1126, 1286
condition: T3 prints β₁ = +0.069 and T7's β₁ column prints −0.0686 for the same δ = 6.5%, with no reconciling note and no gate, in a paper with two prior documented sign/units defects in this coefficient.
location: T3 `tab:params` row at `.tex:244`; T7 `tab:lowband` at `.tex:388–407` (the δ = 6.50 row is `.tex:404`); `eq:beta1` at `.tex:228`
verified: **true** — `.tex:244` = `$\beta_1$ (central) & $0.069$ & per 100 bp gap & \eqref{eq:beta1} at $\delta = 0.065$ \citep{liebersohn2024} \\`; `.tex:404` = `6.50 & $-0.0686$ & $+70.3$ & $+9.20$ & $+42.6$ & $+5.57$ \\`. The T7 `threeparttable` at 388–410 has **no `\tablenotes` block** (it closes `\end{tabular}` → `\end{threeparttable}`), so there is nowhere the note currently lives.
fix: R4 — add a `\tablenotes` block to T7 reconciling the two printings, plus a gate asserting T3's and T7's δ = 6.5% values agree in sign. **DO NOT flip the printed signs** (anti-condition 9): `eq:beta1` at `.tex:228` carries a leading minus (`\beta_1 = -\ln[...]`), making β₁ positive, and T3/`tab:params` are correct; `hazard/literature_hazard.py:32` `rothstein_beta1` omits that minus. The fix is harmonisation plus a replicator note, not a sign flip. 15 min.

### C-SY-21
raiser: Synthesis
synth_ref: Z9 / DA:M2 / X3
raisers_upstream: DA:M2 only
severity: MODERATE
class: CHECK (anchor-rule robustness)
panel_lines: 1127, 1235
condition: The implicit "mid-grid anchor" rule (median of three printed cuts) is not robust to the paper's own ladder extension: on the five well-supported reads {4.695, 4.722, 4.869, 4.991, 5.334} the median is **4.869** (≈+6.0pp), not 4.991.
location: §V.E `.tex:323`; §VII.F `.tex:709–714`
verified: **true** — `matched_depth_reconciliation_results.json` `clean_band_under_extended_ladder.well_supported_reads_pct = [5.334, 4.991, 4.695, 4.722, 4.869]`; sorted median = **4.869** ✓. Also `point_floor_pct = 4.991`, `point_marginal_b = 42.584238395300545`, `committed_band_pct = [4.695, 5.334]`, `band_unchanged_by_extension = true`.
fix: This is the evidence that decides C-SY-03. If an anchor rule is to be stated and defended, it must survive all five reads; if it cannot, drop the point and print the range.

### C-SY-22
raiser: Synthesis
synth_ref: Z10 / DA:M7 / R16
raisers_upstream: DA:M7 only
severity: MODERATE — "and the paper should *say* it"
class: WORDING (1 sentence)
panel_lines: 1128, 1212, 1298
condition: The 108 gates are a consistency layer, not a validity layer, and the repository proves it — the render defect survived every prior round because every literal was present and correctly derived in the source. The paper should state the gates' domain.
location: App. O `app:verdicts` ¶1 (`.tex:1393`ff)
verified: **true, verbatim** — `tools/render_gate.py:2` = "RENDER-LAYER GATE — the check the 108 source gates structurally cannot make"; `:4–7` = "Every gate in tools/liveness_gates.py reads the .tex and the frozen artifacts. None reads the built PDF. Round 31 found the consequence: ~919 text items across 9 pages sat OUTSIDE the physical sheet (the worst page carried 302 items of the Appendix O adjudication ledger more than a full page below the bottom margin)". `tools/liveness_gates.py` gate ids run to `#108`.
fix: R16 — one sentence in App. O ¶1 stating the gates' domain (source-and-artifact consistency, not validity, and not render-layer). The synthesis notes this sentence **strengthens** the credibility claim. Also relevant to scoring: §3 explains that DA charged this defect to *Writing Quality* although it is already repaired (line 1212).

### C-SY-23
raiser: Synthesis
synth_ref: Z11 / EIC:W2 / R1(a) / Carroll answer 4
raisers_upstream: EIC:W2 only
severity: **MAJOR, trivial to fix** — flagged separately as "cheap and embarrassing if left"
class: WORDING
panel_lines: 1129, 1275, 1283
condition: The abstract's "and it identifies levels only" flatly contradicts §V.E ("The design does not identify the aggregate recovery level") and §VII.F ("does not identify levels").
location: abstract `.tex:31`; §V.E `.tex:319`; §VII.F `.tex:709`
verified: **true at HEAD** — HEAD `.tex:31` contains "and it identifies levels only"; `.tex:319` contains "does not identify the aggregate recovery level"; `.tex:709` contains "does not identify levels". (The synthesis attributes the two contradicting strings to §V.E and §VII.F respectively, which matches: 319 ∈ `sec:identification`, 709 ∈ `sec:robustness-floor`.) **Already repaired in the working tree** — see C-SY-33, and note that R1(a)'s *proposed literal* would not have fixed it.
fix: Already applied. Verify no other site asserts level identification before printing the handout.

### C-SY-24
raiser: Synthesis
synth_ref: Z12 / EIC:W4 / R1
raisers_upstream: EIC:W4 only
severity: MAJOR
class: WORDING
panel_lines: 1130
condition: The abstract omits the paper's most novel result — the $87.8bn / 11.5% expectations complement — which is T1 row 2 and contribution #2.
location: abstract `.tex:31`
verified: **true** — `87.8` appears at `.tex:77, 142, 150 (×2), 152, 590, 613, 795` and `11.5\%` at `.tex:77, 150, 152, 795, 1354`; **neither appears at `.tex:31`** in the HEAD baseline, and neither appears in the modified working-tree line 31 either. Still open.
fix: One clause in the abstract giving the expectations-based complement ($87.8bn / 11.5%). Note this is an **addition** to a line the working tree has already lengthened from 1,552 to 1,795 chars; check the abstract word budget before landing (HEAD abstract = 248 words by my count; see C-SY-45).

### C-SY-25
raiser: Synthesis
synth_ref: Z13 / R1:M1 / R8 / §8.1
raisers_upstream: R1:M1 only
severity: **MAJOR — the FINDING sustained, the SUPERLATIVE struck (§8.1)**
class: WORDING + CHECK
panel_lines: 1131, 1290, 1306
condition: Webb is quoted as "the binding layer" while the paper's own stated rule — "the widest layer that does have a coverage property" — selects a **wider** rung it computed and did not quote. Rademacher–Webb agreement is not a stability claim at h_max = 0.33.
location: T9 `tab:ladder` `.tex:445–470` (Webb row at `.tex:457`, "primary; the binding layer"); T8 `tab:uncertainty` `.tex:422`; T1 `.tex:67`; the rule string is at `.tex:31`
verified: **true on all ten rungs, recomputed independently** — `floor_inference_correction_v2_results.json` `reads["R2_2018_gap<=-0.0025_age>=12"]`, widths in pp: CR1-t **5.1967** [3.1532, 8.3499] · CR2-t **5.5787** [2.9740, 8.5527] · **Webb 5.8230** [2.8550, 8.6780] · Rademacher **5.9268** [2.7963, 8.7231] · CR3-t **6.0012** · CR1-BM **6.0431** · CR2-BM **6.7400** [2.4098, 9.1498] · WCR **6.8284** [2.2809, 9.1093] · CR3-BM **7.2836** [2.2809, 9.5645]; percentile (demoted) prints +3.0/+8.0 in T9 = 5.0. All ten match §8.1 to 3 dp. **CR2-BM (6.740pp) is wider than Webb, carries a Bell–McCaffrey coverage property, and is NOT grid-truncated** — so Z13 survives even after excluding both truncated rungs. `verdict.width_pp = 5.822976726802727` confirms Webb is the printed binding layer.
fix: R8 — quote CR3-BM $[+2.3,+9.6]$ or the WCR inversion $[+2.3,+9.1]$ beside Webb, **or** state in one sentence why the wild bootstrap is preferred to Bell–McCaffrey at G* = 5.87 / h_max = 0.332; delete the Rademacher–Webb near-identity as a stability claim. **Correction to R8's own note:** the synthesis says "CR3-BM's upper endpoint is grid-truncated at 6.0%" and §8.1 names 9.5645 as the truncated endpoint — the artifact says otherwise. `cr3_t_interval_df_bm.upper_pp_edge` (9.5645) has `truncated_at_grid_edge: false`; it is the **lower** pp edge (2.2809) that is truncated, mapped at the 6.0% **floor** grid edge. Word the note as "the floor CI's upper endpoint sits at the 6.0% grid edge, truncating the marginal's lower endpoint", and extend the floor sweep grid if CR3-BM is to be promoted.

### C-SY-26
raiser: Synthesis
synth_ref: Z14 / R3:M4 / R13 / X4
raisers_upstream: R3:M4 only
severity: MAJOR
class: STRUCTURE + WORDING
panel_lines: 1132, 1295
condition: §VI.B's cap arithmetic has no objective function, conflicts with §I and §III.B, and omits the one deliverable a cap-setter needs — $bn/month with a band.
location: §VI.B `sec:discussion-capdesign` `.tex:544–577`
verified: **true (structural), and the arithmetic checks** — `.tex:546` gives $740.6bn implied runoff against $1,417.5bn of caps over 42 months → 1417.5/740.6 = **1.9140**, and on the monthly form 1417.5/42 = **33.75**, 740.6/42 = **17.63**, ratio **1.9143** ✓ (the synthesis's 33.75/17.63 = 1.91). §VI.B states no objective function and reports only totals plus a WAL comparison; there is no $bn/month figure and no band. The §III.B conflict is verified at C-SY-04.
fix: R13 — rewrite §VI.B around the achievable-path band in **$bn/month** (≈$16–18bn/month, centred on the verified 17.63, ±≈$4bn from the floor read's own interval), a two-input table (book OTM share × turnover-floor band → implied cap), and an explicit statement of the objective a cap serves. Half day. The synthesis calls this "the paper's most exportable contribution". Prepare the slide for the talk.

### C-SY-27
raiser: Synthesis
synth_ref: Z15 / R3:M6b
raisers_upstream: R3:M6b only
severity: MAJOR **opportunity** (not a defect)
class: WORDING (argument the paper already owns but does not make)
panel_lines: 1133
condition: The 2018 depth ladder's *shape* — step then plateau: 4.695 / 4.722 / 4.869 — is own-data evidence **for** the max form, and is currently spent only as a level band.
location: §VII.F `.tex:713` (prints 4.722 and 4.869); `.tex:709` (prints 4.695); T6 `tab:oosfloor` `.tex:362`
verified: **true — nested reads verified** — `matched_depth_reconciliation_results.json` `step3_decomposition.window_component_by_depth`: `off_window_floor_pct` = 5.334 at gap≤0, **4.991** at −0.0025, **4.695** at −0.0050, **4.722** at −0.0075, **4.869** at −0.0100 — i.e. a step down then a plateau/rise, not a monotone deepening. All four −0.0050…−0.0100 cells have `off_window_well_supported: true`.
fix: Add the affirmative argument: under the additive form the floor should keep falling with depth because the elasticity is never censored; the observed plateau is what a censoring (max) form predicts. This is the paper's only own-data evidence bearing on the form fork besides R14, and it is currently unused. Pairs directly with C-SY-06.

### C-SY-28
raiser: Synthesis
synth_ref: Z16 / R3:M7
raisers_upstream: R3:M7 only
severity: MAJOR
class: WORDING (scope condition)
panel_lines: 1134
condition: A scope condition is missing. The sign is forced in this episode (99.53% of exposure sits below the window minimum), so the design is not identified in a mixed-gap episode — yet §VIII generalizes.
location: `.tex:323` and `.tex:590` (both print 99.53); §VIII `sec:conclusion` `.tex:719–751`
verified: **true (structural)** — `99.53` appears at exactly `.tex:323` and `.tex:590`; §VIII contains no scope restriction to forced-sign episodes.
fix: One sentence in §VIII stating the scope condition: the design's sign is forced by the window's rate configuration, so it transports to one-sided-gap episodes only, and a mixed-gap episode would require a different identification argument.

### C-SY-29
raiser: Synthesis
synth_ref: Z17 / R2:M8 / §8.9
raisers_upstream: R2:M8 only
severity: "Major **if sustained**" — **NOT ARBITRATED**; the synthesizer did not re-derive the benchmark
class: META (open question, not an actionable condition this round)
panel_lines: 1135, 1322
condition: The benchmark's monthly series is differenced off weekly Wednesday SOMA levels — arguably the wrong frequency for MBS paydowns — and the window-boundary allocation is unpriced.
location: §III.B `sec:method-benchmark` `.tex:135–153`; App. N
verified: **partly** — the synthesis explicitly records M8 as "plausible-but-unverified rather than confirmed" (line 1322) and confirms only the cap arithmetic (3 × 17.5 + 39 × 35 = 1,417.5; 1,417.5 − 652.8 = **764.7**, which matches the benchmark implied by every artifact cell: **764.7482532227002**).
fix: **TREAT AS OPEN — do not act.** Per anti-condition 10, R2:M8 is not arbitrated. If the author disputes it, that is a legitimate response; if not, R2's rebuild from published **monthly** SOMA principal-payment data is the right remedy and would also reopen the timing question the paper currently forecloses on the strength of a defect in its own comparator. Requires an Eugene-level scope decision before any run.

### C-SY-30
raiser: Synthesis
synth_ref: Z18 / EIC:W9 / R16
raisers_upstream: EIC:W9 only
severity: MINOR (submission mechanics)
class: STRUCTURE
panel_lines: 1136, 1298
condition: Double-blind review is precluded: named author, affiliation, and a live GitHub URL.
location: `.tex:25` `\author{Eugene Ong}`; `.tex:26` `\affil{Carnegie Mellon University}`; `.tex:758` (App. A) carries the `github.com` URL
verified: **true** — all three confirmed at the lines given. Note the URL is in **App. A**, not the title block as the synthesis's "title block" phrasing in R16 implies.
fix: R16 — anonymized master with an archived DOI (Zenodo) in place of the GitHub URL at `.tex:758`, plus author/affil suppression at `.tex:25–26`. Required for submission only.

### C-SY-31
raiser: Synthesis
synth_ref: Z19 / R16
raisers_upstream: R2 only
severity: Minor-Major
class: REFERENCE
panel_lines: 1137, 1298
condition: Seven references are missing: Deng–Quigley–Van Order; Hanson 2014; Frankel et al. 2004; Fonseca–Liu–Mabille; López-Salido–Vissing-Jørgensen / Acharya et al.; Aiello 2022; Fuster–Lucca–Vickery.
location: `paper/v18/references.bib`
verified: **partly** — the bib has exactly **70** `@`-entries ✓. Genuinely absent: Deng–Quigley–Van Order (only `quigley1987` and `quigley2002`, both sole-authored Quigley), Hanson (0), Frankel (0), López-Salido / Vissing-Jørgensen / Acharya (0), Aiello (0), Fuster–Lucca–Vickery as a standalone entry (Fuster appears only inside `beraja2019` and `boyarchenko2019`; Lucca only in `boyarchenko2019`; Vickery in `berg2018` and `vickery2013`). **The synthesis's "none of these" is wrong for one item**: `fonseca2024` = "Fonseca, J. and Liu, L." is already in the bib and already cited at `.tex:227`, so only the Mabille extension would be new.
fix: R16 — add the six genuinely missing references; for Fonseca–Liu–Mabille, check whether the intended paper is distinct from the already-cited `fonseca2024` before adding a duplicate. 2–3 hours with C-SY-30. Submission only.

---

## PART D — ROADMAP ROWS (R1–R16)

### C-SY-32
raiser: Synthesis
synth_ref: R1 / Z11 / X6 / X1
raisers_upstream: EIC:W2, R1:M6, DA:C2 (via the arbitration)
severity: **REQUIRED BEFORE PRESENTING**
class: WORDING
panel_lines: 1283
condition: Three abstract repairs: (a) "identifies levels only" → a formulation that does not assert level identification; (b) label the 85.7% as a max-form result and give the additive null (35.6% shared) in the same clause; (c) replace "The design bounds it between +2.9 and +8.7" with §V.E's own qualified formulation.
location: `.tex:31` (and the parallel line 31 of `revised_paper_v18_long_abstract.tex`)
verified: **true at a785f3d; LANDED in commit 66df169** — see C-SY-33 for the applied text and its two follow-ons. Effort as stated: 1 hour, no runs.
fix: Nothing further on (a)–(c). Proceed to C-SY-33's two follow-on repairs and to C-SY-24 (Z12, still open in the abstract).

### C-SY-33
raiser: Coordinator-facing finding (this pass), on the R1 landing
synth_ref: R1 landing (commit 66df169) / Z13 / Z11
raisers_upstream: n/a — found verifying R1 against the live tree
severity: **CRITICAL for the pre-talk handout** (it is inside the four required repairs)
class: WORDING
panel_lines: 1275, 1283, 1306 (the panel text the applied edit interacts with)
condition: Commit 66df169 landed R1(a)(b)(c) at line 31 (now 1,795 chars vs a785f3d's 1,552). Two things must now be checked before the handout prints.
location: `paper/v18/revised_paper_v18.tex:31` and `revised_paper_v18_long_abstract.tex:31` at c2e505e
verified: **true** — applied text reads: "Under the production floor form, most of that gap was never about behavior: switch the lock-in response off and the model still accounts for 85.7\% of it (35.6\% under the additive form) …" and "… bounds it between $+2.9$ and $+8.7$ points under its production floor form (the floor read's sampling error at my central elasticity, **the widest layer that does have a coverage property**; a wild-cluster interval on 31 clusters; the percentile read under-covers; the unestimated baseline seasoning ramp spans $+0.9$ to $+15.6$ at the same calibration) … and it identifies a marginal, not a level and not monthly timing."
fix: (1) **GOOD NEWS on (a):** R1(a)'s literal proposal — "identifies levels, not monthly timing" — would have *kept* asserting level identification and so would NOT have fixed Z11. The applied wording ("identifies a marginal, not a level and not monthly timing") is the correct repair. Record R1(a)-as-written as an 11th panel self-refutation (see `## PANEL SELF-REFUTATIONS` item 11). (2) **DEFECT INTRODUCED by (c):** the applied clause now asserts in the abstract that the Webb interval IS "the widest layer that does have a coverage property". Per C-SY-25 that is **false on the paper's own ladder** — CR2-BM is 6.740pp wide, untruncated, and carries a Bell–McCaffrey coverage property, against Webb's 5.823pp. R1(c) has moved Z13's defect from §V.E into the abstract. Either soften to "the widest layer I quote that has a coverage property" **with** R8's one-sentence justification, or land R8 first. (3) Confirm the two abstract files stay in sync — the diff touched line 31 of both. (4) Re-count abstract words after (2) and after C-SY-24 lands.

### C-SY-34
raiser: Synthesis
synth_ref: R2 / Z2
raisers_upstream: R1:M6(i)
severity: **REQUIRED BEFORE PRESENTING**
class: WORDING
panel_lines: 1284
condition: Repair the basis mix at the sentence adjudicating the form fork: one basis, either 100.4→55.9 standalone or 91.3→46.8 shared.
location: `.tex:709`
verified: **true** — see C-SY-14. Both replacement pairs are derived from `floor_form_mixture_results.json` and check to 1 dp. 15 min.
fix: **LANDED in commit c2e505e** as the standalone pair (100.4 → 55.9, with "standalone-scorer" named in the sentence), which is the recommended option. Nothing further on the basis mix, and the landing is internally consistent: the same line's neighbouring "at the 4.695\% and 5.334\% anchors 59.3\% and 52.0\%" are also standalone and were already present at a785f3d — verified against `floor_form_offwindow_results.json` `rows[1].band["6.5"].central_share_pct = 59.2865508298278` and `rows[5].band["6.5"].central_share_pct = 51.97503141757978`, both = `central_trapped_b`/764.748 with no netting. **One presentation hazard for the talk, not a defect:** 59.3 is also the number Framing 1 (C-SY-01) quotes as the 150-PSA *shared* null. Two different objects share the digits; do not let them land in the same breath. (Note also that `concave_hull_band_ends_results.json` gives 57.30/49.99 for the nominally same additive cells — a different artifact family with a different scorer; the manuscript correctly quotes the offwindow artifact, and the two must not be cross-quoted.)

### C-SY-35
raiser: Synthesis
synth_ref: R3 / Z3 / DA:C1 / X7
raisers_upstream: R1:M2, DA:C1
severity: **REQUIRED BEFORE PRESENTING**
class: WORDING
panel_lines: 1285, 1273
condition: Disclose the floor read's support in one sentence at every quoting site and correct T6's "(2017–2019 performance)" for the three defensible rows.
location: §VII.F `.tex:709–714`; T6 caption `.tex:361`; the Definitions block
verified: **true** — see C-SY-15 for the exact support (245 rows / vintage 2017 / 201807–201812 / ages 12.00–17.50; the headline read is the 137-cohort-month gap≤−0.0025 subset). 1–2 hours, no runs. The synthesis's reason holds: "Z3 + C1 are the two facts a methodologist will find in five minutes."
fix: As C-SY-15. Preserve T6's existing "except the final row" carve-out. Enumerate the quoting sites before editing: `.tex:323`, `.tex:361`, `.tex:709`, `.tex:713`, `.tex:741`.

### C-SY-36
raiser: Synthesis
synth_ref: R4 / Z8
raisers_upstream: DA:M3
severity: **REQUIRED BEFORE PRESENTING**
class: WORDING + CHECK
panel_lines: 1286
condition: Add the β₁ sign note to T7 plus a gate asserting T3's and T7's δ = 6.5% values agree in sign.
location: `.tex:388–407` (T7 `tab:lowband`); T3 row `.tex:244`; `tools/liveness_gates.py`
verified: **true** — see C-SY-20. T7 has no `\tablenotes` block to extend, so one must be created. 15 min.
fix: As C-SY-20. **Reject R4's parenthetical alternative** ("or flip the printed signs") per anti-condition 9.

### C-SY-37
raiser: Synthesis
synth_ref: R5 / X1 / DA:C2
raisers_upstream: DA:C2 (fix c), R1:M5, R2:M7
severity: Optional for the talk; **REQUIRED BEFORE SUBMISSION**. The synthesis ranks this "the panel's single highest-value new run".
class: RUN
panel_lines: 1169, 1236, 1287
condition: Re-anchor h₀ on Path A's **estimated** seasoning spline (knots {12, 24, 36, 60, 84, 120}) and report the paired-leg marginal there, converting the largest disclosed uncertainty layer from a convention into an estimate.
location: new run; then §V.E `.tex:417`ff and T8 `tab:uncertainty` `.tex:422–468`
verified: **true that the layer is the largest** — width 14.770pp vs the binding 5.823pp, ratio 2.492 (`psa_level_sweep_results.json` `comparison`/`ranges`). The knot set {12,24,36,60,84,120} is the synthesis's proposal; I found no committed artifact pinning it, so it must be pre-committed in the spec.
fix: 1 run. Machinery: the `psa_level_sweep` harness with h₀ supplied by Path A's estimated spline instead of the PSA table; writes a new artifact (do not overwrite `psa_level_sweep_results.json`). **The synthesis states no pre-committed expectation** — line 1236 says only that this run "flips the sign of that trade", i.e. converts candour into an asset. Spec must therefore pre-commit a band and pre-authorise an unfavourable landing.

### C-SY-38
raiser: Synthesis
synth_ref: R6 / Z1
raisers_upstream: R2:M1
severity: **REQUIRED BEFORE SUBMISSION** (Carroll slide required before the talk)
class: RUN + STRUCTURE
panel_lines: 1288, 1270
condition: Post-stratify the existing 75,000 loans onto the SOMA coupon × vintage-group cells and re-derive the marginal; state the sampler's allocation rule in App. E; add the draw's own composition row to T25.
location: new run; App. E `app:params` `.tex:1011`; T25 `tab:composition` `.tex:1272`
verified: **true, with the basis narrowing in C-SY-13** — the composition gap is real on counts (20.00% per vintage against book shares 0.06 / 0.163 / 0.439 / 0.231) but much smaller on the balance weights the aggregation actually uses (2021: 42.31% draw vs 43.9% face).
fix: 1 run, reusing `cross_design_reweight` machinery. Writes a new post-stratified artifact. Report **both** count and balance-weighted draw composition in the new T25 row. The synthesis states no pre-committed band. Per line 1270, the paper must **not** claim the coupon reweight tests this — it rescales aggregate output and cannot test a per-loan censoring effect.

### C-SY-39
raiser: Synthesis
synth_ref: R7 / Z4 / Z5
raisers_upstream: R1:M3, R2:M3
severity: **REQUIRED BEFORE SUBMISSION**
class: RUN (2 runs, must be run as a pair)
panel_lines: 1289
condition: Two-sided floor transport test: (a) calendar-standardize the off-window read to the QT window's month mix using `seasonal_floor_timing`'s own normalizer; (b) measure the floor's dependence on housing-activity level and report an activity-matched read.
location: new runs; then §VII.F `.tex:709–714` and T5 `tab:assembly` `.tex:338`
verified: **partly** — (a) is fully computable from committed artifacts and its expected direction is verified (3.830% vs 4.000% → floor ≈5.21% → marginal ≈+4.7/+4.8, a −0.8pp move). (b) requires external housing-activity data the repository does not hold (synthesis line 1157), so its feasibility is unestablished.
fix: Run both. The synthesis is explicit that running only (a) makes the paper worse-off honestly and running only (b) is self-serving. If (b) is infeasible for lack of external data, record it as INFEASIBLE with that reason and still land (a) — but say in the text that the one available upward correction remains unpriced, so the assembly's one-directional posture is not vindicated by (a) alone.

### C-SY-40
raiser: Synthesis
synth_ref: R8 / Z13
raisers_upstream: R1:M1
severity: Optional for the talk
class: WORDING + CHECK
panel_lines: 1290
condition: Quote CR3-BM [+2.3, +9.6] or the WCR inversion [+2.3, +9.1] beside Webb, or state in one sentence why the wild bootstrap is preferred to Bell–McCaffrey at G* = 5.9 / h_max = 0.33; delete the Rademacher–Webb near-identity as a stability claim; note the CR3-BM grid truncation.
location: T9 `tab:ladder` `.tex:445–470` + its note `.tex:468`; T8 `.tex:422`; T1 `.tex:67`
verified: **true** — all ten widths recomputed (C-SY-25). The truncation direction in R8's own note needs correcting before it is printed (see C-SY-25 fix).
fix: 1 hour, no runs. **Elevated priority by the R1(c) landing** (C-SY-33): the abstract now asserts the "widest layer with a coverage property" claim that R8 exists to repair, so R8 should either land before the handout or the abstract clause must be softened.

### C-SY-41
raiser: Synthesis
synth_ref: R9 / Z7 / X9 / §8.6
raisers_upstream: R2:M5/M6, EIC:W8, R3:M3, DA:m2/A5
severity: Optional for the talk; **do not quote −$89/−$118bn aloud until done**
class: RUN (1 calculation) + WORDING
panel_lines: 1291, 1173, 1175
condition: Re-derive D from the leg's own 5.61% CPR against the window rate path (or matched-coupon TBA marks) and restate every dependent figure; headline the band [+$61.2, +$256.8]bn in T1's headline cell; add one sentence that the Danish mechanism is an open-market bond repurchase, so the par-denominated cap is not the natural scorer.
location: §VI.D `.tex:582–622`; T1 `.tex:67`; T13 `tab:danish` `.tex:605`; §V.B; §VIII
verified: **true** — see C-SY-19. The identity `gap_cash(D) = 61.188 − D × 470.653` is a gate in `buyback_credit_bracket_results.json` (`P1_gap`, `P3_channel_magnitude`), so the restatement is arithmetic on committed quantities. The `REVERSES` verdict survives at D = 0.21–0.24. Per §8.6 the reframing is smaller than R2 claimed: §I and §VI.D already carry the band and label +$61.2bn "the zero-refinance edge"; the fix is **one table cell and one abstract sentence**.
fix: 1 calculation + edits. Restate T1's Danish cell as the band, add the abstract sentence, and propagate the halved magnitudes wherever −$89/−$118bn is printed.

### C-SY-42
raiser: Synthesis
synth_ref: R10 / Z6
raisers_upstream: R2:M4
severity: Optional
class: WORDING (1 sentence) + RUN (1 run)
panel_lines: 1292
condition: Restate the Ginnie attribution as a window mean (CRR 63%, CDR 40%); score a Ginnie leg with the elasticity attenuated by the observed CRR differential rather than only share-scaled to zero; add the assumability upper bound the CRR series supplies.
location: `.tex:269`; §V.B; §I; §VIII.A
verified: **true** — see C-SY-18; the 42-month means recompute exactly from `gmar_dec25_cpr_series.json`. The `ginnie_cpr_overlay` harness already carries a `crr_only` variant (`marginal_pp = 7.333248797494442`), so the attenuated leg reuses existing machinery.
fix: 1 sentence + 1 run. Bears on 20.4% of book face. Note that "CRR" is absent from the .tex, so the term must be defined at first use.

### C-SY-43
raiser: Synthesis
synth_ref: R11 / X2
raisers_upstream: all five
severity: **REQUIRED BEFORE SUBMISSION**; recommended before the talk if time permits
class: STRUCTURE
panel_lines: 1293, 1226
condition: Split §V.B at its five seams; move the competing-risks taxonomy to App. E; split §V.E and the App. F/G monoliths; fold §VI.C into §VI.B.
location: §V.B `.tex:219–306`; §V.E `.tex:319–323`; App. F `.tex:1099–1100`; §VI.C `.tex:578–581`
verified: **partly** — the four paragraph magnitudes reproduce exactly; the third one is in App. **F**, not App. G (C-SY-02).
fix: 1 day. Mechanical, costs no content, and the synthesis calls it "the single largest scoring deficit (Writing 56)". Nothing in R28–R31 touched paragraph architecture.

### C-SY-44
raiser: Synthesis
synth_ref: R12 / R3:M1 / R3:M2 / X5 / Y1
raisers_upstream: R3:M1/M2
severity: Optional for the talk (but prepare the slide)
class: RUN (1 script)
panel_lines: 1294
condition: Report the marginal in transaction counts with the moving-share bracket applied, set against realized mortgage-financed transaction volume, and state the verdict whichever way it falls.
location: new script; §VI.A `sec:discussion-fallout` `.tex:534–543`; T1 `.tex:67`
verified: **true** — the gap it fills is verified: `.tex:741` concedes "no outcome-holdout months exist anywhere in this paper", and T1 has no household row (C-SY-10). Existing memory flags an E7 floor-units band as Eugene-only, which touches the same units question.
fix: 1 script. The synthesis's own framing binds the spec: "state the verdict whichever way it falls" — pre-authorise an unfavourable landing.

### C-SY-45
raiser: Synthesis
synth_ref: R13 / Z14
raisers_upstream: R3:M4
severity: Optional for the talk (prepare the slide)
class: STRUCTURE + WORDING
panel_lines: 1295
condition: Rewrite §VI.B around the achievable-path band in $bn/month (≈$16–18bn/month, ±≈$4bn from the floor read's own interval), a two-input table (book OTM share × turnover-floor band → implied cap), and an explicit statement of the objective a cap serves.
location: §VI.B `.tex:544–577`
verified: **true** — see C-SY-26; 740.6/42 = 17.63 anchors the $16–18bn/month band, and 1417.5/42 = 33.75 gives the printed cap in the same units. The paper currently prints neither.
fix: Half day. Also resolves the §I/§III.B conflict flagged in C-SY-04 if the objective statement is written to match §III.B's refusal to call it a policy miss. Cross-check against the memory note that a state-contingent cap band already exists in §VI.B from committed reads (4.70–5.33% floors → +6.8/+4.3 marginals, NY Fed $20–30bn precedent) — R13 should extend that band into $bn/month, not replace it.

### C-SY-46
raiser: Synthesis
synth_ref: R14 / R1:M7 / X8
raisers_upstream: R1:M7
severity: Optional
class: RUN (analytic)
panel_lines: 1296
condition: Recompute the analytic implied cross-sectional gradient at the 4.991% headline floor and under the additive form, at 75/100/125 PSA.
location: §V.D `.tex:311–316`; §VII.F `.tex:709–718`
verified: **true** — the object exists and the 4.5× miss is printed at `.tex:315`. All four PSA cells at floor 4.991 and both form cells are committed (`psa_level_sweep_results.json`, `floor_form_mixture_results.json`), so the gradient is analytic from frozen inputs.
fix: Under an hour, no engine run. Would be the first *realized-data* evidence bearing on the form fork, alongside C-SY-27 (Z15's ladder shape).

### C-SY-47
raiser: Synthesis
synth_ref: R15 / X4
raisers_upstream: EIC:W1, DA:m1, R3
severity: Optional for the talk; required for submission
class: WORDING (title)
panel_lines: 1297
condition: Retitle to the claim the paper establishes.
location: `.tex:24`
verified: **true** — see C-SY-04.
fix: 5 min. Either "…Redemption-Cap Shortfall" or "Mortgage Lock-In and the Composition of the Federal Reserve's Agency-MBS Runoff". Note the second option matches this worktree's own branch name (`agency-mbs-runoff-qt`), suggesting it is already the working preference.

### C-SY-48
raiser: Synthesis
synth_ref: R16 / Z18 / Z19 / Z10
raisers_upstream: EIC:W9, R2, DA:M7
severity: Required for submission only
class: STRUCTURE + REFERENCE + WORDING
panel_lines: 1298
condition: Anonymized master with an archived DOI (Zenodo) in place of the GitHub URL; add the seven missing references; add one sentence to App. O ¶1 stating the gates' domain.
location: `.tex:24–26`, `.tex:758`, `paper/v18/references.bib`, App. O `.tex:1393`ff
verified: **partly** — see C-SY-30 (all three anonymity sites confirmed; the URL is in App. A, not the title block), C-SY-31 (six not seven references are genuinely missing; `fonseca2024` already present and cited), C-SY-22 (the App. O sentence, verified verbatim against `tools/render_gate.py:2–7`).
fix: 2–3 hours. The App. O sentence *strengthens* the credibility claim and is the only part of R16 worth landing early.

### C-SY-49
raiser: Synthesis
synth_ref: §2.5 / R2:M2 / Z1
raisers_upstream: R2:M2
severity: **MAJOR (R2) -> CONFIRMED AS A LABELING DEFECT, DOWNGRADED (§2.5)**
class: WORDING
panel_lines: 1177–1179, 1318
condition: T25's coupon row puts two objects in one row — exposure-weighted universe-panel shares (18.0/68.2/13.8) and the 75,000-loan draw's WAC (3.865%) — in the table whose purpose is basis discipline. Imprecise presentation, not an arithmetic error.
location: T25 `tab:composition` `.tex:1272`ff and its tablenote
verified: **partly** — the synthesis states the printed shares reproduce `freddie.universe_panel.coupon_shares_exposure_weighted` exactly and that the tablenote already names both objects. I did not independently re-derive the 18.0/68.2/13.8 triple; `composition_shift_results.json` was read for the vintage/Ginnie/bound anchors only. The synthesis's own §8.7 correction (53.7% is UPB-weighted-rounded-bucket only; 58.2% count-weighted; 47.0% raw ≥4.00%) is anti-condition 7 and must not be acted on as stated.
fix: Name the basis of each number in the row itself, not only in the note. **Do not restate the ≥4.0% share as 53.7%** (anti-condition 7). The synthesis's ruling is that "Z1 (the pool's vintage composition) is the serious version of this complaint, and it is a different, worse problem" — so effort belongs on C-SY-38, not here.

---

## PANEL SELF-REFUTATIONS

Guard rails, not conditions. Each is a factual error the synthesis attributes to the panel itself; none overturns the issue it appears in. Items 1–10 are the synthesis's own §8 plus §2.6; items 11–15 are errors *in the synthesis* that this pass found.

1. **R1:M1 — "Webb is the narrowest of the ten rungs."** FALSE. Correct fact: Webb is **third**-narrowest live (5.823pp), behind CR1-t 5.197 and CR2-t 5.579, and fourth counting the demoted percentile rung (5.045). It **is** the narrowest of the six with a credible few-cluster coverage property — which is R1's actual argument, and it survives. Verified: `floor_inference_correction_v2_results.json` read `R2_2018_gap<=-0.0025_age>=12`, all ten widths recomputed to 3 dp (C-SY-25).
2. **§8.1 rider — CR3-BM's grid truncation.** The synthesis says the truncation applies to the upper endpoint "(9.5645)". Correct fact: `cr3_t_interval_df_bm.upper_pp_edge.truncated_at_grid_edge = false`; the truncation is on the **lower** pp edge (2.2809), mapped at the 6.0% **floor** grid edge. The substantive point — that promoting CR3-BM requires extending the floor sweep grid — is right; the endpoint attribution is not. **New in this pass.**
3. **DA:m3 — "the abstract is a single paragraph, 248 words."** FALSE on structure. Correct fact: an explicit `\par` sits at `.tex:31`, so the abstract is **two** paragraphs, and DA's proposed break ("at 'What lock-in itself adds…'") describes a seam that already exists. Verified: `.tex:31` contains exactly one `\par`. On the count: the synthesis says 250 words, DA 248, EIC 248, R3 246; my count on the HEAD line is **248**, so the synthesis's own 250 is also off by two. **The word-count part is new in this pass.**
4. **DA:N9 — of the ~13 T27 rows adjudicated against the headline, "not one moved a reported number."** FALSE. The floor demotion moved the headline +9.2 → +5.6 and the central level 97.9% → 91.3% through every dependent number; the bootstrap retraction replaced $[+9.17,+9.23]$ with $[+8.27,+10.19]$; the Webb correction moved the printed lower endpoint (`floor_inference_correction_v2_results.json` `verdict.printed_lower_unchanged = false`, 2.796 → 2.855 — verified); the Danmarks Nationalbank validation turned a point into a swept band; `buyback_credit_bracket`'s `REVERSES` verdict turned a signed relief claim into the printed incidence bracket (verified: `verdict.code = "REVERSES"`).
5. **DA:N1 — "no cell anywhere in the paper's apparatus in which the mechanical baseline fails to deliver the majority."** FALSE as a universal. Correct fact: `floor_form_mixture_results.json` `cells["4.991|1|0"]` gives a β₁=0 null of $341.84bn = **44.7% standalone / 35.6% shared** — a minority. DA scoped its check to the PSA sweep at the production form; the claim as written ranges over the apparatus. This is the arbitration with the largest editorial consequence in the report (it drives C-SY-06).
6. **R2 minor 10 — "duplicated table captions will read as sloppiness in a submitted PDF."** No PDF defect. The duplication is a longtable→markdown converter artifact (bold caption at md:41, re-emitted inside the header row at md:43); in the .tex the caption sits correctly before `\endfirsthead`. R2 hedged correctly and then drew the wrong inference.
7. **R2:M6 — "the paper headlines the Danish minimum."** Right for T1's headline cell ("+$61.2 billion") and for the abstract (which omits the Danish result entirely); **wrong for §I and §VI.D**, both of which give the band and explicitly label +$61.2bn "the zero-refinance edge of a band swept to +$256.8 billion at 3% refinance-in-place". The fix is one table cell and one abstract sentence, not a reframing.
8. **R2:M2 — "the sample's ≥4.0% share is 53.7%, not 13.8%."** 53.7% is correct **only** on UPB-weighted rounded-coupon buckets; the same draw is 58.2% count-weighted and 47.0% on raw coupons ≥4.00%. The three-object confusion R2 identifies is real; the number needed its own basis named — the irony of a basis-labeling complaint.
9. **R3 — "40,234 active at window start" from `loan_sample.parquet`.** Correct fact: the parquet gives **40,077** rows with `balance > 0` (verified independently); 40,234 is the survival count in `attenuation_sensitivity_results.json`. The mean balance and downstream arithmetic are unaffected — verified: mean balance over all 75,000 rows = **$126,812.61**, matching the synthesis's $126,813.
10. **R2:M8 (benchmark frequency) — not arbitrated.** The synthesizer did not re-derive the $764.7bn benchmark from the weekly SOMA series and records M8 as plausible-but-unverified. The cap arithmetic itself checks: 3 × 17.5 + 39 × 35 = 1,417.5; 1,417.5 − 652.8 = 764.7 (and every artifact cell implies a benchmark of 764.7482532227002 — verified). **Treat as OPEN** (anti-condition 10).
11. **R1(a)'s own proposed replacement is itself a Z11 defect. NEW in this pass.** R1(a) asks for "identifies levels only" → "identifies levels, not monthly timing". That still asserts the design identifies levels, which is exactly what §V.E (`.tex:319`, "does not identify the aggregate recovery level") and §VII.F (`.tex:709`, "does not identify levels") deny. Had R1(a) been applied literally it would have left Z11 unfixed. The working tree instead landed "identifies a marginal, not a level and not monthly timing", which is correct. Do not restore R1(a)'s wording.
12. **X3's "Table 12" is the wrong table. NEW in this pass.** T12 is `tab:wal` (portfolio WAL by prepayment scenario); its `5.6` values are WAL **years**, not +5.6pp. The tables that print +5.6pp are T1, T5, T6 and T8.
13. **X2's third paragraph location is off by one appendix. NEW in this pass.** The 10,696-char paragraph is at `.tex:1099–1100`, inside **App. F** (`app:patha-detail`, 1089–1167), not App. G (`app:ridge`, 1168). All four character counts are exact.
14. **Z1's "2021 at 22% of the draw" is an unlabelled basis. NEW in this pass.** The count share is **20.00%**; 22.32% is the orig-UPB-weighted share; and the balance-weighted share — the one the aggregation actually uses per `.tex:269` — is **42.31%**, against 43.9% of book face. Z1's per-loan censoring argument survives; its "factor of ten" magnitude rhetoric is count-basis only.
15. **Z19's "none of these" is wrong for one item. NEW in this pass.** `fonseca2024` (Fonseca, J. and Liu, L.) is already in the 70-entry bib and already cited at `.tex:227`. Six of the seven, not seven, are genuinely absent.

---

## CARROLL ROUND PRE-TALK CONDITIONS

**Verdict: PRESENT WITH FIXES.** All five reviewers wrote "ready to present and defend as-is" and all five attached a precondition that cannot be met in the room without changing the text first. With **no revision checkpoint**, the fixes must land in the deck and in the .tex before the talk (panel lines 1260–1262).

### Must be fixed BEFORE presenting — exactly four .tex repairs, plus two slides

| # | Condition | Row | Site | Status |
|---|---|---|---|---|
| 1 | **R1** — three abstract repairs (Z11 self-refuting clause; X6 unlabelled form-conditional headline; X1 unqualified bounding claim) | C-SY-32 / C-SY-33 | `.tex:31` (both abstract files) | **DONE — commit 66df169.** Two follow-ons remain: soften or justify the newly-introduced "widest layer that does have a coverage property" claim (C-SY-33 item 2), and re-count the abstract |
| 2 | **R2** — basis mix at the form-fork sentence | C-SY-34 / C-SY-14 | `.tex:709` | **DONE — commit c2e505e**, standalone pair 100.4→55.9, basis named |
| 3 | **R3** — floor-read support disclosure + T6 caption correction | C-SY-35 / C-SY-15 | `.tex:361`, `.tex:709–714`, Definitions | OPEN. 1–2 hours |
| 4 | **R4** — β₁ sign note on T7 + sign-agreement gate | C-SY-36 / C-SY-20 | `.tex:388–407` | OPEN. 15 min. **Note, not a sign flip** |
| 5 | **R10** — Ginnie window-mean sentence | C-SY-42 / C-SY-18 | `.tex:269` | §6 names R10 among the sentences that must land pre-talk (line 1262); §7 marks R10 "Optional". Treat §6 as binding for the *sentence* and defer the run |
| — | Slide: three-column draw / estimation universe / book face (Z1) | C-SY-13 | deck | REQUIRED — "own it before the question is asked" |
| — | Slides: R12 transaction-count metric and R13 $bn/month cap band | C-SY-44, C-SY-45 | deck | "prepare the slide", runs optional |

**Also required before the handout prints** (line 1275, flagged separately as "cheap and embarrassing if left"): the Z11 abstract clause. Covered by fix 1.

**Do not say aloud until R9 lands** (line 1291): the −$89bn / −$118bn Danish figures. R2's explicit precondition.

### The three prepared-answer framings, with every cited number verified

**Framing 1 — "What sets your baseline seasoning ramp — did you estimate it?" (X1 / DA:C2).**
*Defensibility: weak on the fact, strong on the consequence.* Concede immediately: no, 100 PSA is an industry convention, and sweeping it 75–150 carries the marginal **+0.9 → +15.6** points, disclosed in §V.E and T8 as a convention range with no coverage property. Then follow through without pause: **the headline qualitative claim survives the entire sweep** — the β₁=0 null recovers **92.8% / 85.7% / 73.3% / 59.3%** of the benchmark on the shared basis at 75 / 100 / 125 / 150 PSA, so the baseline delivers the majority in every cell. Lead with that. Do **not** defend +5.6 as a central tendency; the paper already says it is not one (`.tex:79`).
> Verified: `psa_level_sweep_results.json` `ranges["4.991"]` lo_pp **0.8560355409769471**, hi_pp **15.626488479897219**. Standalone nulls at floor 4.991: 101.9415 / 94.7917 / 82.3669 / 68.3873. Shared basis (net $69.56220187263008bn of common curtailment from the numerator, benchmark 764.7482532227002): **92.845 / 85.696 / 73.271 / 59.291** → 92.8 / 85.7 / 73.3 / 59.3 ✓ all four to 1 dp. Ratio 2.492 confirmed (`psa_over_floor_read_at_headline`, and 14.770/5.823 = 2.536 on the recomputed Webb width — quote the artifact's 2.492, not a hand ratio).

**Framing 2 — "Is your 75,000-loan pool a sample of the Fed's book?" (Z1).**
*Defensibility: weak.* Answer no, and give the unflattering numbers: equal allocation per origination-quarter file, ~15,000 loans per vintage, 2017–19 at **60% of the draw against 6.0% of book face**, 2022 absent, all weights 1.0. What can be said: §III.B states **51.0%** book-face coverage on the book's own agency × vintage joint cells; the out-of-window vintage share is bounded at **$11.7bn** from Fannie cohort speeds and the Ginnie share at **$20–47bn** from published differentials, both signed toward overstatement. What must **not** be said: that the pool is representative, or that the coupon reweight tests this — it rescales aggregate output and cannot test a per-loan censoring effect.
> Verified: `loan_sample.py:97` (equal per-file allocation) and `:169` (`weight` = 1.0); `loan_sample.parquet` 15,002/14,999/15,001/14,997/15,001 per vintage, one distinct weight value; `composition_shift_results.json` `committed_anchors.vintage_shares["2017-19"] = 0.06`, `vintage_bound_b = 11.748139002824871`, `ginnie_share_of_soma_face = 0.204`; `ginnie_cpr_overlay_results.json` `gates.G3_static_bound.static_bound_b = [20.3, 47.3]`; `51.0` appears at `.tex:146` (§III.B) ✓.
> **Prep caveat for the slide (C-SY-13):** if asked how much the composition gap survives the balance weighting the paper actually applies, the honest answer is that on current balance the draw is 27.05% 2017–19 against 6.0% of face (≈4.5×, not 10×) and 2021 is 42.31% against 43.9% — nearly matched. Have that ready; the per-loan censoring point is what carries the concern, not the aggregate weight.

**Framing 3 — "Your floor is read on 12–24-month-old loans, one vintage, six months of 2018 — and both of your own corrections put it above your band." (X7 / DA:C1).**
*Defensibility: moderate, and best handled by conceding hard.* Say it first: the band's lower edge is the soft one; the composed correction lands at **+2.9pp**, the interval's lower endpoint; the age-transport error is signed against the headline and is **not computable** in the clean leg — the artifact's own verdict string is `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`. The paper already prints both corrections in T8 ("age-standardized floor 5.51% → +3.8, band open below +4.3"; Fannie 5.52% "bracketing the marginal below +4.3"). Do **not** say the floor is "measured on 2017–2019 performance" — T6's caption says that and it is wrong for the three rows that set the headline.
> Verified: `b5_joint_cell_results.json` `agestd_floor_pct = 5.507748455937158`, `overlay_agestd.primary.marginal_pp = 2.928173869093058`, `adjudication.verdict = "LANDS_AS_COMPOSED_LOWER_MEMBER"`; `oos_identification_results.json` 2018 leg `contamination.verdict = "CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE"`, `mature_test_computable = false`, `ramp_rise_is_psa_confounded = true`; pooled 2017–2019 age≥12 6.065% vs age≥24 10.995%, matched depth 5.185% vs 8.92%; T8 (`.tex:422–468`) contains both `5.51` and `5.52`; T6 caption at `.tex:361` contains "(2017--2019 performance)" ✓.

**Editorial finding to state plainly if pressed on where the answer sits** (line 1163, verified as an implication of the above): on the paper's own committed reads the marginal's mass sits in the **lower** half of [+2.9, +8.7], and +5.6 is above the centre of the measured evidence, not at it. Three of four candidate corrections are measured or computable and all three raise the floor (5.21 seasonal, 5.51 age-standardized, 5.52 Fannie) against a point of 4.991 and a clean-band top of 5.334.

---

## COORDINATOR DERIVATIONS

### 1. The PSA-sweep span for the unestimated baseline seasoning ramp

`hazard/data/psa_level_sweep_results.json`, key `ranges["4.991"]`:

```
lo_pp    = 0.8560355409769471
hi_pp    = 15.626488479897219
width_pp = 14.770452938920272
```

**Basis of each endpoint: BOTH are marginals in percentage points of the $764.7bn benchmark, and the marginal is basis-invariant** — the shared-accounting netting is a common constant that cancels in a central-minus-null difference (the manuscript states this at `.tex:323`: "which is basis-invariant because the shared-accounting netting is common to both legs"). Confirmed arithmetically: `cells["4.991|75|6.5"].marginal_pp = 0.8560355409769471` = `ranges.lo_pp` and `cells["4.991|150|6.5"].marginal_pp = 15.626488479897219` = `ranges.hi_pp`, and each is `marginal_b / 764.7482532227002 × 100` with no netting applied to either leg. So **neither endpoint carries a shared/standalone label; the shared/standalone distinction applies only to the *null recovery shares*, not to the span.** Report the span as "+0.9 to +15.6 points of the benchmark", with no basis qualifier.

  · lo: `marginal_b = 6.546516846586769` / 764.7482532227002 × 100 = 0.85604 ✓ (75 PSA)
  · hi: `marginal_b = 119.50329769006044` / 764.7482532227002 × 100 = 15.62649 ✓ (150 PSA)
  · production cell for reference: `cells["4.991|100|6.5"].marginal_pp = 5.571558182909726`, `marginal_b = 42.60839388108866` — the headline +5.6 / $42.6bn.
  · ratio against the binding layer: 14.770452938920272 / 5.822976726802727 = 2.5366; the artifact's own committed ratio is `psa_over_floor_read_at_headline = 2.492`, which uses the committed Rademacher width 5.9268210320175605 (14.770/5.9268 = 2.4922). **Quote 2.492 and cite the artifact key**, or quote 2.54 and say it is against the Webb width — do not mix.

**Null recovery shares at 75 / 100 / 125 / 150 PSA (floor 4.991, β₁ = 0):**

| PSA | `trapped_b` | standalone `share_pct` | shared (computed) | synthesis claims |
|---|---|---|---|---|
| 75 | 779.5957537746586 | 101.9415 | **92.845** | 92.8 ✓ |
| 100 | 724.9180585654117 | 94.7917 | **85.696** | 85.7 ✓ |
| 125 | 629.8991036027942 | 82.3669 | **73.271** | 73.3 ✓ |
| 150 | 522.9905524391946 | 68.3873 | **59.291** | 59.3 ✓ |

All four verified to 1 dp. Shared = (`trapped_b` − 69.56220187263008) / 764.7482532227002 × 100.

**Pre-committed expectation, for the record:** the sweep's `expectation_check` is **0-for-3 at the headline floor** (75, 125, 150 all outside their pre-committed bands) and **3-for-3 at floor 4.0**. Any manuscript sentence quoting this span must not describe the off-window cells as having met expectation.

### 2. Is "35.6% shared" derivable from committed artifacts?

**YES — exactly, to 4 dp.** The derivation:

```
standalone numerator  cells["4.991|1|0"].trapped_b          = 341.83938974816874   (β₁ = 0 null, additive form s = 1)
standalone share      cells["4.991|1|0"].share_pct          =  44.69959732600039
implied benchmark     341.83938974816874 / 0.4469959732600039 = 764.7482532227002
common curtailment    shared_layer_scoring_results.json
                        results.no_lockin_null.curtailment_netted_b = 69.56220187263008
                      (identical in results.path_a, results.path_b_central,
                       results.path_a_fullbook_composed, results.path_b_fullbook_composed
                       — i.e. the same constant on every U.S. leg, as the shared basis requires)

shared share = (341.83938974816874 - 69.56220187263008) / 764.7482532227002 * 100
             = 272.27718787553866 / 764.7482532227002 * 100
             = 35.60346...  ->  35.6 %
```

**The netting is applied to the NUMERATOR ONLY; the denominator stays at the full $764.7482532227002bn benchmark.** This is confirmed independently by the constant offset: `69.56220187263008 / 764.7482532227002 × 100 = 9.09609`, and every standalone→shared pair in the sweep differs by exactly that 9.096pp (101.9415→92.845, 94.7917→85.696, 82.3669→73.271, 68.3873→59.291, 44.6996→**35.603**, 100.3633→91.267, 55.9066→46.811). If the netting were applied to both numerator and denominator, the additive null would be 272.277/695.186 = 39.17%, which matches nothing the panel or the paper prints.

**Coordinator note — the exact curtailment figure is 69.56220187263008, not "≈69.6".** The 69.6 in the prompt is a rounding of it; the artifact key is `shared_layer_scoring_results.json` → `results.no_lockin_null.curtailment_netted_b`.

**Companion pairs the coordinator will need for the R2 basis repair (C-SY-14), all from `floor_form_mixture_results.json` at floor 4.991:**

| cell | form | `trapped_b` | standalone | shared |
|---|---|---|---|---|
| `4.991\|0\|0` | max, null | 724.9181 | 94.7917 | 85.6956 |
| `4.991\|0\|6.5` | max, central | 767.5265 | **100.3633** | **91.2672** |
| `4.991\|1\|0` | additive, null | 341.8394 | **44.6996** | **35.6035** |
| `4.991\|1\|6.5` | additive, central | 427.5449 | **55.9066** | **46.8105** |

So the like-for-like recovery pairs are **100.4 → 55.9 (standalone)** or **91.3 → 46.8 (shared)**; the manuscript's `.tex:709` currently prints the mixed pair 91.3 → 55.9. Marginals: max `marginal_pp = 5.571558182909726`, additive `marginal_pp = 11.207021073656186` — the fork multiplies the marginal by **2.011×** ("roughly doubles" ✓). Interior named cell: `named_interior["4.991"]` = `{s: 0.4, marginal_pp: 10.691918730047902, central_share_pct: 87.84463957141757}`.

### 3. What landed while this pass ran (read this before editing)

Two R32 commits landed on top of the a785f3d baseline during verification, and the tree is clean at the second:

```
66df169  R32 C-R1 (Task 1): abstract repairs      -> line 31 of revised_paper_v18.tex AND
                                                     revised_paper_v18_long_abstract.tex
c2e505e  R32 C-R2 (Task 2): basis-mix repair      -> line 709 of revised_paper_v18.tex
```

| | a785f3d (panel-reviewed) | c2e505e (now) |
|---|---|---|
| `.tex:31` length | 1,552 chars | 1,795 chars |
| Z11 clause | `and it identifies levels only` | `it identifies a marginal, not a level and not monthly timing` |
| X6 label | 85.7% unlabelled | `Under the production floor form … 85.7\% … (35.6\% under the additive form)` |
| X1 caveat | absent | `the unestimated baseline seasoning ramp spans $+0.9$ to $+15.6$ at the same calibration` |
| `.tex:709` form-fork pair | `91.3\% to 55.9\%` (mixed bases) | `standalone-scorer recovery falls from 100.4\% to 55.9\%` |

File length is unchanged at 1,429 lines, and I re-verified byte-identity at every anchor line this inventory cites
(24, 146, 244, 269, 319, 361, 404, 417, 457, 546, 741, 758) — so all `.tex:NNN` references remain valid.

**Consequences (detail in C-SY-33):**
1. R1(a) landed **better than the panel specified** — its literal proposal would not have fixed Z11 (self-refutation item 11).
2. R1(c) **imported Z13's defect into the abstract**: the abstract now asserts the Webb interval is "the widest layer that does have a coverage property", which is false on the paper's own ladder (CR2-BM is 6.740pp, untruncated, coverage-bearing, vs Webb's 5.823pp). Soften the clause or land R8 first. **This is the highest-priority open wording item.**
3. **Z12 ($87.8bn / 11.5%) is still absent from the abstract** — verified absent from the c2e505e line 31 as well as from a785f3d.
4. Re-count the abstract: a785f3d was **248 words** by my count (the synthesis says 250; DA and EIC say 248; R3 says 246). The line grew by 243 chars, so the count must be re-taken before Z12 is added.
5. Of the four required pre-talk .tex repairs, **two are done (R1, R2) and two are open (R3, R4)**, plus the R10 sentence §6 names.
