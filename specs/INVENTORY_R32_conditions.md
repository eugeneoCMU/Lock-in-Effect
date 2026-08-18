# INVENTORY_R32_conditions.md — CANONICAL R32 CONDITION TABLE

Consolidates six verified inventories (`inventory_EIC.md` 22 rows, `inventory_R1.md` 38, `inventory_R2.md` 50,
`inventory_R3.md` 43, `inventory_DA.md` 34, `inventory_SYNTH.md` 49 = **236 source rows**) into one canonical set.
Baseline for every `.tex:NNN`: commit `a785f3d` (`paper/v18/revised_paper_v18.tex`, 1,429 lines), except where a row
says a Wave-1 commit has already moved the line. Four Wave-1 commits have landed (`66df169`, `c2e505e`, `d22b265`,
`7189c8e`) — see `## ALREADY SATISFIED IN THIS ROUND`.

Conventions used below:
- `raisers:` upstream reviewer refs; **CONSENSUS** is stamped at 3 or more distinct raisers.
- `severity:` the synthesis's arbitrated severity where it arbitrated, written as `MAJOR->CRITICAL (X6)`.
- `verified:` carried from the source row, with its reason.
- `wave:` 1 = pre-talk wording (the panel's "must fix before presenting" set), 2 = remaining wording/posture,
  3 = runs, 4 = exhibits/tables, 5 = minor wording sweeps + references, 6 = compression/relocation,
  CLOSE = post-edit re-verification, EUGENE = reserved (no agent action).
- Rows whose source ids also appear in another row's `source_rows` are cross-listed deliberately (a synthesis row
  that governs two different edits); the cross-listing is named in the row.

---

## CANONICAL CONDITIONS

### C-01 — Soften or justify the abstract's newly-asserted "widest layer that does have a coverage property"
raisers: SY:R1-landing finding (C-SY-33), R1:M1 (upstream), SY:Z13
severity: CRITICAL for the pre-talk handout (synthesis's own arbitration on the 66df169 landing; "the highest-priority open wording item")
class: WORDING
verified: true — 66df169's applied clause asserts the Webb interval **is** the widest coverage-bearing layer; false on the paper's own ladder: CR2-BM is 6.740pp wide, untruncated, Bell–McCaffrey coverage-bearing, against Webb's 5.823pp (`floor_inference_correction_v2_results.json`, read `R2_2018_gap<=-0.0025_age>=12`).
location: `paper/v18/revised_paper_v18.tex:31` and `revised_paper_v18_long_abstract.tex:31` (post-`66df169`)
condition: The abstract must not assert that the quoted Webb interval is the widest layer with a coverage property, since the paper's own ladder computes wider coverage-bearing rungs it does not quote.
fix: Either soften to "the widest layer I quote that has a coverage property" **or** land C-20 (the ladder's selection-rule repair) first and inherit its justification sentence. Re-pin `ABSTRACT_POSTURE` spans and `tests/test_headline_posture_gate.py` with the edit; keep both abstract files in sync.
wave: 1
source_rows: C-SY-33 (also cross-listed at C-125 for its items 3–4)

### C-02 — Disclose the floor read's actual support and correct tab:oosfloor's provenance caption
raisers: R1:M2/M4-support, DA:C1, SY:X7/Z3/R3, EIC (evidence rationale)  [CONSENSUS]
severity: CRITICAL (X7 — "DA:C1 upheld, the panel's most consequential finding"; DA's "confined to a note" characterisation narrowed)
class: WORDING
verified: true — `cohort_month_panel.parquet` filtered to 2018 + `mean_loan_age>=12` returns 245 rows, **all vintage 2017**, periods {201807:2, 201808:48, 201809:48, 201810:49, 201811:49, 201812:49}, ages 12.00–17.50; the headline read is the gap<=-0.0025 subset (137 cohort-months, 31 clusters, G*=5.8717, h_max=0.3323, 4.9906%). `.tex:361` says "(2017--2019 performance)", true only of the contaminated pooled/2019 rows. `.tex:443`/`.tex:440` say "31 stratum clusters carry" with no cluster unit, vintage or month support named.
location: `.tex:323`, `.tex:361` (T6 caption), `.tex:440`, `.tex:443` (T9 caption), `.tex:709`, `.tex:713`, `.tex:741`, `.tex:92` (Definitions)
condition: Every site quoting the floor read must state its support — one origination vintage (2017), six 2018 reporting periods, all cohort-months aged 12–24, 31 cross-sectional coupon×FICO×LTV cells pricing cross-sectional dependence only — and T6's caption must attribute "2017–2019 performance" only to the rows for which it is true.
fix: One disclosure sentence at the five quoting sites; split T6's caption provenance clause per row (pooled/2019 = 2017–2019 performance; the three defensible rows = the 2018 rising-rate leg), preserving the existing "except the final row" carve-out. Restate `.tex:443`/`.tex:440` to name the cluster unit. No runs. Check `tools/liveness_gates.py` near :4573 and `tests/test_floor_ladder_gate.py` for pinned caption fragments first.
wave: 1
source_rows: C-R1-05 + C-R1-06 + C-R1-08 + C-SY-07 + C-SY-15 + C-SY-35

### C-03 — State the clean leg's zero mature-age support and the unpriced age transport
raisers: DA:C1(b), SY:X7 (upstream R1:M2)
severity: CRITICAL (DA:C1, upheld by X7)
class: WORDING
verified: partly — artifact exact: 2018 leg `seasoning` has 505 cohort-months in age[0,12), 155 in [12,24), **0** in every cell >=24; `contamination.mature_test_computable = false`, `verdict = "CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE"`, `ramp_rise_is_psa_confounded = true`. The non-computability is already stated in `app:floormech` (`.tex:1314`) and the soft lower edge at `.tex:92`; what is missing is the >=24-emptiness at §VII.F and in the Definitions block, and the words "unpriced"/"signed against the headline". DA's *direction* premise is not corroborated by the in-window population: `fannie_floor_read_results.json` in-window deep-OTM reads 3.840% (age>=12) vs 3.909% (age>=24), essentially flat.
location: §VII.F `.tex:711`, `.tex:713`; Definitions `.tex:92`; existing statement at `.tex:1314` (must not be deleted)
condition: §VII.F and the Definitions block must state that the clean 2018 leg contains no cohort-month aged >=24, so the age transport onto a book aging 2–162 months is unpriced; the direction must be stated as *indicated* by the leg's PSA-confounded ramp and *not corroborated* by the in-window deep-OTM age contrast.
fix: Two sentences (one at §VII.F beside the age-standardization passage, one clause in the Definitions block) reusing the committed 3.840/3.909 and 8.92/10.995 figures. No run.
wave: 1
source_rows: C-DA-03

### C-04 — Label the 85.7% mechanical majority as form-conditional at every remaining quoting site
raisers: R1:M8, DA:N1-inverted, SY:X6/Z2, EIC:W6/W7 (upstream)  [CONSENSUS]
severity: MAJOR->CRITICAL (X6, §2.1 arbitration — "the highest-leverage sentence-level repair in the report")
class: WORDING
verified: true — `floor_form_mixture_results.json` `cells["4.991|1|0"].share_pct = 44.6996` standalone = **35.6035% shared** (numerator netted of the committed 69.56220187263008bn curtailment, denominator 764.7482532227002), against `cells["4.991|0|0"] = 94.7917` standalone = 85.6956 shared. A null recovering 35.6% does not partition the object being decomposed.
location: abstract `.tex:31` (**SATISFIED** by 66df169); still open at T1 `tab:headline` mechanical-null row `.tex:78` (incl. its uncertainty cell "83.9--86.9\% across the off-window floor range"), §VII.F `.tex:709`, §VIII `.tex:725`, §VI.B `.tex:546`, §V.F `.tex:526`
condition: Wherever the 85.7% (or 88.7%/91.3% companion) is quoted, the max-form conditioning must be attached, with the additive form's counterpart (44.7% standalone / 35.6% shared) available in the same breath.
fix: One clause per site using the committed literals; if the shared 35.6% is quoted, derive it in text (it is standalone minus the 9.096pp common-netting wedge) or quote standalone only. Do not weaken the finding itself — it holds across the whole PSA sweep under the production form (92.8/85.7/73.3/59.3 shared at 75/100/125/150 PSA).
wave: 2
source_rows: C-SY-06 + C-DA-32 + C-R1-20

### C-05 — Qualify "binding layer" wherever it appears without the coverage-property scope, including T1
raisers: DA:C2(b), SY:X1 (T1 leg), R2:M7 (adjacent)
severity: CRITICAL (DA:C2b); X1 arbitration splits severity by site — CRITICAL at abstract + T1, MAJOR in the body
class: WORDING
verified: partly — "binding layer" occurs 10x; exactly one site is already qualified (`.tex:417` "binding among the layers with a coverage property; the unestimated baseline-level convention spans wider"), `.tex:433` carries a partial qualifier. Eight remain unqualified. The qualifying phrase already exists verbatim in the manuscript and can be reused.
location: `.tex:46`, `.tex:66` (T1 caption), `.tex:79` (T1 row 4), `.tex:433`, `.tex:440`, `.tex:444`, `.tex:457`, `.tex:713`, and `.tex:1412` (App. O ledger — historical narration, qualify separately or leave as record)
condition: Every unqualified use of "binding layer" must carry the scope the paper's own §V.E formulation states; T1's uncertainty cell must additionally carry the ramp-convention qualifier X1 requires at that site.
fix: Propagate the `.tex:417` formulation to the eight unqualified sites; add the ramp qualifier to T1's cell. Gate pins: `ASSEMBLY_SPANS["posture_binding_layer"]` (`tools/liveness_gates.py:406`), `ABSTRACT_POSTURE` (:595) and `tests/test_headline_posture_gate.py` move with any span change. Keep this edit verbally distinct from C-60's "binding constraint" (policy sense).
wave: 2
source_rows: C-DA-06 + C-SY-01 (wording leg at T1; C-SY-01's RUN leg is C-08)

### C-06 — Disclose the sampler's allocation rule and that the pool is not a probability sample of the book
raisers: R2:M1, SY:Z1/§2.5, R3 (Carroll answer 2, adjacent)
severity: MAJOR (R2) -> **CRITICAL** (§2.5 arbitration: "worse than any single reviewer's rigor deduction credited")
class: STRUCTURE (disclosure)
verified: partly — code exact: `hazard/loan_sample.py:97` `per_file = max(1000, pool_target // max(len(pairs),1))`, `:169` `weight = 1.0`; `loan_sample.parquet` 15,002/14,999/15,001/14,997/15,001 per vintage 2017–2021 (20.00% each), 2022 absent, one distinct weight. Book face shares 2017-19 0.06 / 2020 0.163 / 2021 0.439 / 2022 0.231. **Basis caveat (anti-condition A-15):** the "factor of ten" rhetoric is count-basis; on the balance weights the aggregation actually applies (`.tex:269`) the draw is 27.05% 2017–19 (~4.5x) and 42.31% 2021 vs 43.9% of face (nearly matched).
location: App. E `app:params` `.tex:1085`; §V.B `.tex:269`; descriptors `.tex:122`, `.tex:202`, `.tex:219`, `.tex:275`
condition: The manuscript must state the pool's actual allocation rule (equal allocation per quarterly origination file, all weights 1.0, 2022 absent) at the place it describes the sample, so the draw is not read as a probability sample of the book on the two dimensions that set censoring.
fix: One sentence in App. E naming the rule and its consequence for vintage composition; report both count and balance-weighted shares so the magnitude claim is basis-labelled. No gate pins `.tex:1085`. Pairs with C-64 (the T25 row) and C-07 (the run).
wave: 2
source_rows: C-R2-01 + C-SY-13

### C-07 — RUN: post-stratify the 75,000-loan draw onto the SOMA coupon x vintage-group cells and re-derive the marginal
raisers: R2:M1(ii), SY:Z1/R6
severity: MAJOR (R2) -> CRITICAL (§2.5); required before submission, Carroll slide required before the talk
class: RUN
verified: true — the composition gap and the censoring mechanism are the paper's own: 2021+2022 = 67.0% of book face against 0%/~22% of the draw; the central leg is floor-pinned in 68.8% of 1,683,124 loan-months and the null in 35.8% (`.tex:323`); §VII.E's coupon reweight rescales aggregate output (107.0%->109.1%) and leaves the marginal bit-invariant (`.tex:697`, `.tex:701`), so it cannot test a censoring-mediated composition effect.
location: new run; then T5 `tab:assembly` `.tex:338` and §V.E `.tex:333`
condition: The central/null pair must be scored once on a pool post-stratified to the book's coupon x vintage-group cells, and the resulting marginal reported with its direction, so the headline stops being computed on a pool that is not a probability sample of the book.
fix: Post-stratify the existing draws and re-run the pair; machinery = the `cross_design_reweight` harness plus the `vintage` column already carried on the pool (`hazard/agents.py`, read today only by `reweight_to_soma_coupons`). Writes a new artifact (e.g. `book_composition_marginal_results.json`) carrying the marginal, both legs' bind shares on the re-weighted pool, and parity against the committed 68.8%/35.8%. Spec-before-run; no pre-committed band exists, so one must be pre-committed. Limit to state with the result: 2022 and pre-2017 have zero support in the draw (`G1...vintage_range = [2017,2021]`), so only 2017–2021 can be re-weighted and the 33.7% out-of-window share stays covered by `vintage_overlay`. The result enters `tab:assembly` with its sign (R2's fix (iii)).
wave: 3
source_rows: C-R2-03 + C-R2-04 + C-SY-38

### C-08 — RUN: re-anchor h0 on Path A's estimated seasoning spline instead of the 100 PSA convention
raisers: DA:C2(c)/A1, R2:M7, R1:M5, SY:X1/R5  [CONSENSUS]
severity: CRITICAL (DA:C2c); X1 §2.3 splits by site — the run is "the panel's single highest-value new run", optional for the talk, **required before submission**
class: RUN
verified: partly — the layer is the largest disclosed one: `psa_level_sweep_results.json` `ranges["4.991"]` = {lo 0.8560, hi 15.6265, width 14.7705} against the binding 5.8230 (ratio 2.492 on the artifact's committed key). The censoring-geometry lockstep is exact: `floor_bind_share` 0.9469/0.6882/0.3657/0.1808 at 75/100/125/150 PSA with marginals 0.856/5.572/11.419/15.626pp. **Feasibility caveat:** `hazard/literature_hazard.py:73` `baseline_hazard` supports only `"psa"` and `"weibull"`; there is no tabulated-profile or spline mode, so "one run" is false as a code claim. The knot set {12,24,36,60,84,120} is the synthesis's proposal and is pinned in no artifact.
location: new run; then §V.E `.tex:417`ff, T8 `tab:uncertainty` `.tex:422–468`, §VII.F
condition: The paper's widest disclosed uncertainty layer must be converted from a convention into an estimate, or the attempt recorded infeasible with its reason.
fix: RUN, scoped honestly before any spec: (a) a new `BASELINE_MODE` accepting a tabulated age->CPR profile, (b) a stated rule for mapping Path A's spline onto it and normalizing its level (Path A's own level is not the production level), (c) parity gates showing psa-mode is bit-unchanged. Writes a new artifact; must not overwrite `psa_level_sweep_results.json`. Spec must pre-commit a band and pre-authorise an unfavourable landing. Separable WORDING leg that needs no run (DA:A1): state in §V.E that under the censoring-geometry reading the marginal is a joint function of floor level and ramp and the design cannot separate them, citing the committed bind-share/marginal lockstep. If (a)–(c) are out of scope, record infeasible-this-round and let C-10's landed abstract disclosure stand as the honest alternative.
wave: 3
source_rows: C-DA-07 + C-DA-21 + C-R2-18 + C-SY-01 (RUN leg) + C-SY-37

### C-09 — Abstract must not assert that the design identifies levels — SATISFIED
raisers: EIC:W2, SY:Z11/R1
severity: MAJOR ("REQUIRED BEFORE PRESENTING"; SY: "cheap and embarrassing if left")
class: WORDING
verified: true at a785f3d — `.tex:31` read "and it identifies levels only" against `.tex:319` "The design does not identify the aggregate recovery level" and `.tex:709` "does not identify levels".
location: abstract `.tex:31`
condition: The abstract must not contradict §V.E/§VII.F by asserting level identification.
fix: **SATISFIED — `66df169`.** Landed as "it identifies a marginal, not a level and not monthly timing"; gate pin `levels_only_abstract` re-pinned. Note R1(a)'s literal proposal would NOT have fixed this (see A-11). Residual: verify no other site asserts level identification before the handout prints.
wave: 1
source_rows: C-EIC-02 + C-SY-23 + C-SY-32

### C-10 — Abstract's bounding claim must name the unestimated baseline ramp span — SATISFIED
raisers: DA:C2(a), R2:M7, R1:M5, SY:X1  [CONSENSUS]
severity: CRITICAL (DA:C2a) -> CRITICAL at the abstract site (X1 §2.3)
class: WORDING
verified: true — the main clause claimed more than its parenthetical supported; `psa_level_sweep_results.json` `verdict = "PSA_WIDER"`, ratio 2.4921, and the production cell reproduces trapped 767.5264524465003 / marginal 42.608 bit-exactly, so "under its production floor form" did not quarantine the span.
location: abstract `.tex:31`
condition: The abstract's bound must claim only what its parenthetical supports and must name the +0.9 to +15.6 ramp span at the same calibration.
fix: **SATISFIED — `66df169`** (ramp span added in the same clause). Introduced C-01's defect in the process.
wave: 1
source_rows: C-DA-05 + C-R2-19

### C-11 — Abstract paragraph 2's topic clause must carry the form condition — SATISFIED
raisers: EIC:W6-alternative
severity: MAJOR (EIC item 6's own alternative branch)
class: WORDING
verified: partly — the abstract was never form-silent (sentence 2 carried "under its production floor form" and the +3.5/+13.1 hull); what was unconditioned was the paragraph-2 topic sentence and the 85.7%/91.3% sentences.
location: abstract `.tex:31`
condition: If the form fork is not resolved, the form condition must sit in the topic clause rather than in the paragraph's last sentence.
fix: **SATISFIED — `66df169`** ("front-loading the condition into the topic clause"). C-22 remains the open resolution question.
wave: 1
source_rows: C-EIC-08

### C-12 — The form-fork sentence's basis mix — SATISFIED
raisers: R1:M6(i), SY:Z2/R2
severity: MAJOR ("same defect class Appendix A already retracted")
class: WORDING
verified: true — `.tex:709` compared a shared 91.3% with a standalone 55.9%; like-for-like is 100.4->55.9 standalone or 91.3->46.8 shared (`floor_form_mixture_results.json` cells `4.991|0|6.5` = 100.36328 and `4.991|1|6.5` = 55.90662).
location: §VII.F `.tex:709`
condition: The sentence adjudicating the form fork must be stated on one named basis.
fix: **SATISFIED — `c2e505e`**: "the central leg's standalone-scorer recovery falls from 100.4\% to 55.9\%", one basis, named; the mixed string is gone. Consistent with the 44.7% standalone null already on the line. Presentation hazard for the talk (not a defect): 59.3 is both the 5.334% anchor's standalone central share and the 150-PSA shared null — do not let them land in the same breath.
wave: 1
source_rows: C-R1-19 + C-SY-14 + C-SY-34

### C-13 — Reconcile tab:params' +0.069 with tab:lowband's -0.0686 — SATISFIED
raisers: DA:M3, SY:Z8/R4
severity: MAJOR ("the defect class has bitten twice"); "REQUIRED BEFORE PRESENTING"
class: WORDING
verified: true — `.tex:244` printed `$\beta_1$ (central) & $0.069$`, `.tex:404` printed `6.50 & $-0.0686$`, no reconciling note, and T7 had no `\tablenotes` block. `eq:beta1` (`.tex:228`) carries a leading minus so the positive sign is correct for eq:beta1; `hazard/literature_hazard.py:32` `rothstein_beta1` omits it and returns -0.06857052676484808.
location: T7 `tab:lowband` `.tex:388–407`; T3 row `.tex:244`
condition: The two printings must be reconciled with the convention named.
fix: **SATISFIED — `d22b265`**: tab:lowband's nine cells harmonised to positive per `eq:beta1`, with a replicator note recording that `rothstein_beta1` returns the opposite sign. **Residual check for the coordinator:** the inventories recommended the other branch (keep the engine's printed sign, add the note) precisely so the table could not contradict the production code — see A-09; confirm the replicator note carries the code's signed value so the anti-condition's substance is met.
wave: 1
source_rows: C-DA-10 + C-SY-20 + C-SY-36

### C-14 — Gate asserting the two beta_1 printings agree with the stated convention — SATISFIED
raisers: DA:M3 (second limb)
severity: MAJOR
class: CHECK
verified: true — no such gate existed; the only beta_1 mention was gate #94 at `tools/liveness_gates.py:4666`, testing a different string.
location: `tools/liveness_gates.py`, `tests/`
condition: A gate must assert the documented relation between T3's and T7's delta=6.5% values (not naive sign equality, which would enforce the wrong fix).
fix: **SATISFIED — `d22b265`**: new gate #109 plus 5 tests.
wave: 1
source_rows: C-DA-11

### C-15 — Restate the Ginnie–Freddie attribution on the window mean, not the May-2025 snapshot
raisers: R2:M4(a), SY:Z6/R10
severity: MAJOR; §6 of the synthesis names the R10 *sentence* among the pre-talk landings (the run is deferred to C-74)
class: WORDING
verified: true, computed independently in two inventories — `gmar_dec25_cpr_series.json` over 2022-06…2025-11 (n=42): CPR gap +2.1365pp, CRR (voluntary) gap **+1.3541pp = 63.4%**, CDR gap +0.8475pp = 39.7%; identity residual `mean_abs = 0.0398`pp. May-2025 is the buyout-dominated month (CPR gap 2.84, CDR gap 1.71). Cross-checked against `ginnie_cpr_overlay_results.json` `G3_static_bound.window_mean_ginnie_minus_freddie_pp = 2.1365238095238093`. "CRR" appears nowhere in the .tex, so the term must be defined at first use.
location: §V.B `.tex:269` (the clause "with the involuntary buyout channel (CDR 2.1\% versus 0.4\% in May 2025) supplying most of the structural difference")
condition: The excess Ginnie speed must be attributed on the 42-month window mean, where the majority is **voluntary**, rather than on the one month in which buyouts dominate.
fix: Replace the snapshot clause with the window-mean decomposition (CRR +1.35 of +2.14 = 63%; CDR +0.85 = 40%; name the extraction residual), labelling May-2025 as the buyout-dominated month if it is kept. No gate pins "structural difference".
wave: 1
source_rows: C-R2-10 + C-SY-18

### C-16 — Carroll-Round preparation deliverables — SATISFIED
raisers: EIC (Carroll note), R2 (three provisos), R3 (two slides), DA (venue judgment)  [CONSENSUS]
severity: CRITICAL-for-deadline (DA:Carroll — no revision checkpoint exists after the talk) / MINOR (EIC, R2, R3 talk prep)
class: META
verified: true — each proviso is verified in its source row: the form fork is the question that can sink the defense (`.tex:709`); the 139pp navigation problem; the pool-vs-book question is currently unanswerable from the manuscript; the -$89/-$118bn magnitudes rest on an asserted D.
location: n/a (deck and prep doc, not the manuscript)
condition: Before the talk the author must hold prepared answers to (i) "what is your number, and why isn't it +11?", (ii) "is your 75,000-loan pool a sample of the Fed's book?", (iii) the household side in the same units, (iv) the cap deliverable in $bn/month, plus a 15-minute route through 139 pages; and must not quote the Danish cash range aloud until C-75 lands.
fix: **SATISFIED — `7189c8e`** (`docs/carroll_round_qa_prep.md`). Residual dependencies, unchanged: the pool slide is strongest after C-06/C-64/C-07; the household slide after C-76; the cap slide after C-54; the Danish magnitudes stay unquoted until C-75. DA's sequencing condition is discharged by the Wave-1 landings plus C-01.
wave: 1
source_rows: C-EIC-22 + C-R2-48 + C-R2-49 + C-R2-50 + C-R3-42 + C-R3-43 + C-DA-34

### C-17 — Settle the +5.6 posture: drop the point and print the range, or state and defend an anchor rule
raisers: EIC:W5, DA:C1(a)/§1, R1:M5-fix, R3:M5, SY:X3  [CONSENSUS]
severity: CRITICAL (DA:C1a) -> **MAJOR** (X3 arbitration; §4 records that half-retiring the posture while keeping +5.6 was net negative on coherence)
class: WORDING (posture decision)
verified: partly — the disclaimer "an anchor convention rather than a central tendency" is verbatim at `.tex:79` and the "attach no posture" sentence at `.tex:333`; the circulation is understated by the panel (24 occurrences of `$+5.6$` across 21 lines). Two panel site claims are false: §VI contains no +5.6, and T12's 5.6 is a WAL in years (A-13, A-20). DA's own proposed replacements are mutually inconsistent (A-12) and its "+2.9 to +6.8" lower endpoint is not derivable from the reads it names (~+3.8 is).
location: `.tex:79`, `.tex:333` (the defenses); quoting sites `.tex:31`, 46, 58, 92, 110, 211, 323 x3, 333 x2, 342, 345, 368, 433, 524, 625, 635, 711, 713, 725, 731, 797, 1413
condition: One posture must be chosen and carried to every quoting site: either the point is dropped from the abstract/§I framing and the range printed, or the anchor is defended on stated grounds and the "no posture" disclaimer withdrawn.
fix: Whichever branch, apply it consistently to §VIII (`.tex:725/731`) or abstract and conclusion will disagree. Gate pins to move together: `ABSTRACT_POSTURE["interval"]` (`:595`) and its ordering assert, `ASSEMBLY_SPANS["posture_binding_layer"]` (`:406`), the `tex.count("$+2.9$ to $+8.7$") >= 4` gate (`:4573`), the letter literal list (`:739`), `tests/test_headline_posture_gate.py`. C-18 supplies the evidence that decides it. Do not cite T12.
wave: 2
source_rows: C-EIC-06 + C-SY-03 + C-DA-02

### C-18 — State the anchor-selection rule and show it against the five-read extension
raisers: DA:M2, SY:Z9
severity: MAJOR (DA) -> MODERATE (SY:Z9), and it is the evidence that decides C-17
class: CHECK
verified: true — `.tex:713` already prints the two extra reads (4.722% at gap<=-0.75, 4.869% at gap<=-1) and states the clean band is unchanged, but never states the counting rule that makes 4.991% the anchor. `matched_depth_reconciliation_results.json` `clean_band_under_extended_ladder.well_supported_reads_pct = [5.334, 4.991, 4.695, 4.722, 4.869]`, median **4.869** (~+6.0pp by the printed delta=6.5 column), `band_unchanged_by_extension = true`.
location: §VII.F `.tex:713`; T6 `.tex:365–367`; T5 row 2 `.tex:345`; §V.E `.tex:323`
condition: The implicit "median of the three pre-committed depth cuts" rule must be stated ex ante, with the five-read median shown as a robustness line — or the interior point abandoned per C-17/C-19.
fix: One sentence in §VII.F stating the rule and the five-read median (4.869% -> roughly +6.0 points); both endpoints are committed literals, so no run.
wave: 2
source_rows: C-DA-09 + C-SY-21

### C-19 — Promote the measured composed +2.9 cell into T1 and the abstract, or drop the interior point
raisers: DA:M1
severity: MAJOR
class: WORDING
verified: partly — the refusal-to-compose sentence is verbatim at `.tex:333` and the paper does **not** hide the cell: `.tex:333` already reports "the joint cell has now been run under a pre-committed landing rule (run b5_joint_cell) and measures +2.9 points, an interaction within 0.1 of proportional", repeated in T8's note. `b5_joint_cell_results.json` `overlay_agestd.primary.marginal_pp = 2.928`, `verdict = "LANDS_AS_COMPOSED_LOWER_MEMBER"`. The gap is confined to T1 and the abstract. DA mis-cites `measured_minus_implied_pp = -0.129` (that is `conventional_agestd` vs the 3.8 grid-read; the overlay's proportional deviation is 0.00023pp).
location: T1 row 4 `.tex:79`; abstract `.tex:31`; §V.E `.tex:333`; T5 `.tex:345`
condition: Either the composed +2.9 enters T1 and the abstract as the assembly's operative lower member, or the named interior +5.6 is dropped from both; "neither" is not allowed.
fix: Promote the committed literal (no run), or delete the interior point per C-17. Do not delete §V.E's refusal-to-compose reasoning; the honest statement is that one composition was measured and lands at the bottom. Beware three numerically distinct +2.9s (wild-t endpoint, composed cell, DA's proposed interval floor) — they must not read as one number.
wave: 2
source_rows: C-DA-08

### C-20 — The ladder's stated selection rule selects a wider coverage-bearing rung than the one quoted
raisers: R1:M1, SY:Z13/R8, (SY:R1-landing — C-01 is its abstract site)
severity: MAJOR — the FINDING sustained, the SUPERLATIVE struck (§8.1); elevated by the 66df169 landing
class: WORDING + CHECK
verified: true — all ten widths recomputed independently in two inventories: CR1-t 5.1967, CR2-t 5.5787, **Webb 5.8230**, Rademacher 5.9268, CR3-t 6.0012, CR1-BM 6.0431, CR2-BM 6.7400, WCR 6.8284, CR3-BM 7.2836 (percentile 5.0442, demoted). `.tex:333`'s rule ("the widest layer that does have a coverage property") selects CR3-BM [+2.3,+9.6] or WCR [+2.3,+9.1]; **CR2-BM (6.740pp) is wider than Webb, coverage-bearing, and NOT grid-truncated**, so the finding survives excluding both truncated rungs. The Notes to T9 justify the wild-cluster correction only against the percentile rung; no wild-vs-Bell–McCaffrey argument exists anywhere (`G*_css = 5.8717`, `h_max = 0.3323`).
location: T9 `tab:ladder` rows `.tex:456–465` and notes `.tex:467–468`; `.tex:333` (the rule); T8 `.tex:433`; T1 `.tex:79`; abstract `.tex:31` (C-01)
condition: Either the wider coverage-bearing rung is quoted beside Webb, or the rule is restated with its scope (rungs sharing one studentizer / one df convention) plus one sentence on why a wild-cluster bootstrap is preferred to Bell–McCaffrey/Imbens–Kolesár at G*~6 — or a concession that at G*~6 the two constructions are not ranked and both are quoted.
fix: No run. If a truncated rung is promoted, disclose the truncation **on the correct edge** (A-17: the *lower* pp edge 2.2809 is clipped at the 6.0% floor grid edge; `upper_pp_edge.truncated_at_grid_edge = false`) and extend the floor sweep grid. Gate pins: the `$+2.9$ to $+8.7$` count gate (`:4573`), `ASSEMBLY_SPANS["posture_binding_layer"]` (`:406`), `ABSTRACT_POSTURE` (`:595`), the ladder ordering asserts (`:818–821`), `tests/test_floor_ladder_gate.py`, `tests/test_headline_posture_gate.py`.
wave: 2
source_rows: C-R1-02 + C-R1-03 + C-SY-25 + C-SY-40

### C-21 — The Rademacher–Webb near-identity is not evidence of robustness
raisers: R1:M1 (rider), SY:R8
severity: MAJOR
class: WORDING
verified: partly — the span exists verbatim at `.tex:440` ("land with both endpoints within a tenth of a point, a re-printing rather than a substantive move") and the gap is 0.059/0.045pp; R1's site attribution (T9's note) is wrong — it is T8's note — and the paper already calls the pair a re-printing rather than claiming robustness to the leverage profile. Not gate-pinned (no "re-printing" match).
location: Notes to T8 `tab:uncertainty` `.tex:440`
condition: The agreement clause must carry the mechanical reason it is uninformative (both weight schemes are dominated by the same h=0.33 cluster's sign flip), keeping the endpoint comparison as a re-printing statement only.
fix: One clause at `.tex:440`. No run, gate-free.
wave: 2
source_rows: C-R1-04

### C-22 — Resolve the floor-form fork with a stated selection rule, and settle the +11 branch's standing
raisers: EIC:W6/Carroll, R1:M8-consequence
severity: MAJOR (EIC makes a stated resolution the sixth condition for Minor Revision; the Carroll note calls it "the only question that can sink the defense")
class: CHECK
verified: true — `.tex:709` contains the whole fork: additive marginal +11.25 at the production floor (a +2.05 shift past the ex-ante ±1-point immateriality threshold), near floor-invariance off-window (+11.22/+11.21/+11.19), the mixture curve (+7.5 at s=0.1, +9.7 at 0.25, +10.7 at 0.4, flat near +11.2 from s=0.6), the concession that the near-coincidence defense does not extend to the shallow-gap off-window anchors, and the explicit statement that the "well under half" reading does *not* pull toward the max end. The paper also refuses fit as the selection rule ("the design does not identify levels") — which is the incoherence R1 presses, since the additive null (35.6% shared) does not partition the benchmark.
location: §VII.F `.tex:709`; §V.B `.tex:227`; §I `.tex:92`; T1 note a hull entry `.tex:90`; abstract `.tex:31`
condition: The fork must be resolved by a stated rule rather than disclosed, and the +11 branch's standing in the hull settled rather than left co-equal beside a headline that depends on the max form.
fix: No new run — `floor_form_mixture_results.json` and `floor_form_offwindow_results.json` already measure the curve and its endpoints. Two admissible resolutions: (i) argue the semantics claim explicitly as a prior over s and report the marginal at that s; (ii) promote the form-robust statement already written at the end of `.tex:709` ("roughly +9 to +11 points at the production floor" — note: the *production-floor* band, not the off-window one) to headline status, which changes the abstract. Or state that fit is doing partition work, the max form is retained on that ground, and the +11 branch is a form sensitivity. Whichever is chosen must be stated once and inherited by `.tex:31` and `.tex:731`. C-80 and C-73 are the only own-data evidence bearing on it.
wave: 2
source_rows: C-EIC-07 + C-R1-21

### C-23 — §VIII must state its policy conclusion as form-conditional, in the opening clause
raisers: EIC:W7, R2 (coherence deduction), R3 (coherence cell)  [CONSENSUS]
severity: MAJOR
class: WORDING
verified: partly — the concession is verbatim at `.tex:731` ("reduces to ``the marginal is small''---and under the production floor form the marginal is bounded small by construction") and the paragraph does **not** restate the conclusion flat afterwards; the live defect is ordering — the paragraph opens with the flat claim ~2,900 characters before the qualification arrives — and the absence of a pointer to the additive form's +11.2 counterweight at the concession. Same concession also at `.tex:528`.
location: §VIII `.tex:731` (4,470-char paragraph); §V.F `.tex:528`
condition: The form condition must sit in the opening clause of the conclusion's trilemma paragraph, with a pointer to the additive member (+11.2 points, floor-invariant) at the concession itself.
fix: Reorder `.tex:731` (or split it at "What this dissolution rests on is thinner than the framing suggests" with a `\paragraph` head, which also serves C-87). No content is deleted — the qualifying sentences already exist. Ensure the §VIII policy sentence that leans on smallness carries the condition explicitly.
wave: 2
source_rows: C-EIC-09 + C-R2-47 + C-R3-41

### C-24 — Relabel the binding interval with what is held fixed, and state the hierarchy once in §V.E ¶7
raisers: R1:M5
severity: MAJOR
class: WORDING
verified: partly — the three convention spans reproduce exactly (PSA 75–150 -> +0.856/+15.626, `verdict = PSA_WIDER`; floor form s in [0,1] -> +5.5716/+11.2070 with +9.660 at s=0.25; delta=3.25% -> +3.4658) and each exceeds the binding width 5.8230 — but none is undisclosed: all three are printed in T8's calibration column and §V.E ¶7. What R1 objects to is the hierarchy and the word "binding", not absence. The scoping is deliberate and gate-pinned (the comment above `posture_binding_layer` records it as the ROUND-28 R1-W1/C3 branch (a)). T1's note a omits the PSA span and the scaled-null companion.
location: `.tex:333` (¶7, both sentences on one line); `.tex:433`; `.tex:79`; abstract `.tex:31`; T1 note a `.tex:90`
condition: [+2.9,+8.7] must be labelled as the sampling interval on the floor read *at fixed seasoning ramp, floor form and elasticity*, with the convention envelope carried as the outer statement and the sampling interval nested and labelled inside it; ¶7 must say once which object is outer and which is nested.
fix: Relabel at the four sites (honest minimum: name the fixed conventions — "at 100 PSA, s=0, delta=6.5%"); amend the abstract's "The design bounds" verb; add the PSA span and the scaled-null companion to T1's note-a catalogue. Move `ASSEMBLY_SPANS["posture_binding_layer"]`, `ABSTRACT_POSTURE["interval"]` and `tests/test_headline_posture_gate.py` together.
wave: 2
source_rows: C-R1-14 + C-R1-15 + C-R1-16

### C-25 — State that no sampling error from the imported elasticity enters any layer of the ladder
raisers: R1 (evidence basis), R2 (evidence basis)
severity: MAJOR
class: WORDING
verified: true / partly — the elasticity is propagated as a swept band (5.5/6.5/7.7, T7) and never as an estimated uncertainty; the interval is explicitly "at the central elasticity delta = 6.5% … not an interval on the elasticity" (`.tex:433`, `.tex:79`). Path A supplies no in-sample sign support (`patha_sign_test_results.json` verdict T3, p = 0.093/0.412/0.241), so no internal SE exists to propagate — which is why the fix is a disclosure. R2 requests no fix and raises it only as a score basis; what would settle it is checking whether Liebersohn–Rothstein publish a standard error on the mobility coefficient.
location: T8 headline row `.tex:433` and its note `.tex:440`; `.tex:231` (the import); abstract `.tex:31`; T7 `.tex:386`; the band sweep `.tex:282`
condition: The absence of any propagated source-elasticity sampling error must be stated where the interval is claimed, and the band edges named as a convention sweep rather than a confidence interval.
fix: One clause at `.tex:433`/`.tex:440`. If the source publishes an SE, propagating it through the committed floor-to-marginal grid would add a fourth layer with its coverage property named; if not, one sentence saying so converts an unpriced gap into a documented one. Do together with C-24 and C-102.
wave: 2
source_rows: C-R1-38 + C-R2-45

### C-26 — State the Fannie comparison on one basis (or run the Fannie 2018-leg read)
raisers: R1:M4 (surviving limb)
severity: MAJOR
class: WORDING (with an optional RUN branch)
verified: true — `fannie_floor_read_results.json`'s only out-of-window block is `out_of_window_2017_2019`; at that cell Freddie parity is 5.185% (n=438) and Fannie 5.522%, difference 0.337pp, while the headline is read from the 2018 leg at 4.991% (n=137). The artifact carries **no** 2018-leg Fannie read. So "the independent Fannie Mae read of the same off-window cell" is false as written — the same defect class Appendix A catalogues as retracted. (R1's variance-ranking argument built on a 0.53pp spread does not survive: A-18.)
location: `.tex:433` (T8 calibration column), `.tex:333` (§V.E ¶7), `.tex:713`; span gate-pinned as `ASSEMBLY_SPANS["ladder_fannie"] = "5.52\\%, brackets the marginal below the $+4.3$ edge"` (`tools/liveness_gates.py:386`)
condition: The Fannie bracketing statement must be stated on one basis — either Freddie 5.185 vs Fannie 5.522 (+0.337pp, pooled 2017–2019) with "the same off-window cell" dropped, or a Fannie 2018-leg read produced so the sentence becomes true.
fix: Wording branch: restate and drop the claim of cell identity; move `ASSEMBLY_SPANS["ladder_fannie"]` and the T8 cell together. RUN branch: `hazard/fannie_floor_read.py` already carries the leg-split machinery from `out_of_window_floor`; the artifact would gain a `2018_rising_rate` block — **but its input `cohort_month_panel_fannie.parquet` is absent from this worktree** (see RUN INVENTORY), so the wording branch is the only one executable here.
wave: 2
source_rows: C-R1-12

### C-27 — Say plainly that the binding layer prices only the within-read component
raisers: R1:M4
severity: MAJOR
class: WORDING
verified: partly — the "disclosed but unpropagated" fact is true: the three reads (4.991 point, 5.5077 age-standardized, 5.522 Fannie) all appear in T8's calibration column and none enters the interval, and `.tex:440` calls the wild-t interval "the binding layer" without naming which variance component it prices. R1's transport>sampling ranking does not survive A-18, so the "not defensible" conclusion is weakened, not established.
location: Notes to T8 `.tex:440`; headline row `.tex:433`
condition: The note must state that the binding layer is the floor read's own sampling error at fixed ramp/form/elasticity and does not price read-to-read transport, which is disclosed in the calibration column.
fix: One clause. **Do not** rebuild the interval on the pooled-read arithmetic — it rests on the A-18 basis mix.
wave: 2
source_rows: C-R1-13

### C-28 — Report the null's standalone recovery at 75/100 PSA beside the PSA span
raisers: R1:M5
severity: MAJOR
class: WORDING
verified: true — `psa_level_sweep_results.json` `cells["4.991|75|0"].share_pct = 101.9415` against `cells["4.991|100|0"].share_pct = 94.7917`: at 75 PSA the beta_1=0 null fits *better* than the production null. Neither figure is printed anywhere; the PSA entry prints only the marginal span.
location: T8 calibration column `.tex:433`; §V.E ¶7 `.tex:333`; T3 `tab:params` `.tex:239` (where 100 PSA is specified)
condition: Aggregate fit must not be available as an implicit defense of the 100 PSA convention, so the null's recovery at 75 and 100 PSA must sit beside the span.
fix: One clause with committed literals; no run. Note for any sentence quoting the span: the sweep's `expectation_check` is 0-for-3 off-window and 3-for-3 at floor 4.0 — the off-window cells must not be described as having met expectation.
wave: 2
source_rows: C-R1-18

### C-29 — Rename the partition-carrying uses of "mechanical"
raisers: R3:M6(a), SY:Y2
severity: MAJOR
class: WORDING
verified: true — "mechanical" occurs 43x in the .tex; about 30 carry the partition, the rest are ordinary language ("mechanically inflates", "the mechanical reason", `.tex:635`, `.tex:1340`) and must be left alone. The floor's mixture concession is verbatim at `.tex:227`. The R29 rename to "baseline turnover floor" fixed a different word — no reviewer credits it and two still attack "mechanical".
location: T1 row label `.tex:78`; Definitions `.tex:92`; partition uses at `.tex:44` (x2), 58, 60 (x2), 98, 110 (x2), 150 (x4), 227, 277, 319, 323, 528, 538, 542, 546, 721, 725, 731 (x2), 745, 1100
condition: The object must be renamed to something that does not assert non-behavioral content ("no-elasticity null", "observed-turnover null", "rate-insensitive baseline"), starting with T1's row label.
fix: Per-site pass, not a blind replace-all; keep the ordinary-language uses. Gate-span check first — the `.tex:92` definitions paragraph and `.tex:150`'s "mechanical-majority threshold" are both inside quoted gate spans. Pairs with C-30; landing one without the other leaves the overclaim.
wave: 2
source_rows: C-R3-19 + C-SY-11

### C-30 — Define the partition where the word is first used
raisers: R3:M6(a)
severity: MAJOR
class: WORDING
verified: true — "mechanical" is never defined; `.tex:44` uses it twice without definition, the Definitions paragraph defines the floor and the marginal but not the word, and the closest gloss (`.tex:319`, "the mechanical model with the lock-in elasticity switched off") defines it by construction rather than content.
location: first use `.tex:44`; Definitions `.tex:92`
condition: One sentence must state what the partition is — a model carrying observed baseline turnover versus the imported elasticity's increment above it, not mechanics versus behavior — at first use and in the definitions block.
fix: Add the partition sentence at `.tex:92` and a first-use gloss at `.tex:44` tying the term to "elasticity switched off, baseline turnover held at its observed level", explicitly not "non-behavioral".
wave: 2
source_rows: C-R3-20

### C-31 — Quote both denominators (the cap gap and the ex-ante expectations benchmark)
raisers: R3:M5
severity: MAJOR
class: WORDING
verified: true — `expectation_benchmark_results.json` `e_benchmark_b = 87.8316`, `lockin_marginal.pp_of_e_benchmark = 80.0908` for the in-sample $70.3bn; 42.608/87.832 = 48.5% and 42.608/186.778 = 22.8% both reproduce. The abstract and T1 quote only the cap-relative 5.6% / +2.9-to-+8.7.
location: abstract `.tex:31`; T1 row 4 `.tex:80`; §III.B `.tex:150`
condition: The marginal must be quoted against both denominators in one breath, since every headline percentage divides by a ceiling §III.B declines to call a policy miss.
fix: One clause in the abstract and in T1's off-window-marginal row ("5.6% of the cap gap, and roughly half the ex-ante surprise under the central intra-2022 allocation, 23% under the settlement-aware one"), carrying the allocation-conditional-upper-bound reading `.tex:150` already governs these ratios with.
wave: 2
source_rows: C-R3-15

### C-32 — Name the mechanical-majority result as a fact about cap placement
raisers: R3:M5 (closing note)
severity: MAJOR
class: WORDING
verified: partly — the substance is already conceded in the same breath (`.tex:725`: "mostly mechanical, because the caps sat far above what any plausible prepayment environment would have delivered") and §III.B makes the cap-placement point directly; what is missing is the inference — that leading with it understates lock-in against the E-benchmark.
location: abstract `.tex:31`; §VIII `.tex:725`, `.tex:731`; §III.B `.tex:150`
condition: Where the mechanical majority is first stated it must be named as a statement about where the FOMC put the ceiling, with a pointer to the E-benchmark share as the reading that is about mortgage markets.
fix: One clause plus a re-ordering of sentences already present. Coordinate with C-31 and C-04.
wave: 2
source_rows: C-R3-18

### C-33 — Add the expectations complement ($87.8bn / 11.5%) to the abstract
raisers: EIC:W4, SY:Z12
severity: MAJOR
class: WORDING
verified: true — "87.8" occurs at `.tex:77, 142, 150 (x2), 152, 590, 613, 795` and 11.5% at `.tex:77, 150, 152, 795, 1354`; neither appears at `.tex:31` in the a785f3d baseline **or** in the post-66df169 line 31. The figure is contribution #2 (`.tex:60`) and T1 row 2 (`.tex:77`).
location: abstract `.tex:31`
condition: The abstract must carry the paper's most novel affirmative result — the expectations-based complement measured against the Fed's own ex-ante projection rather than the cap.
fix: One sentence quoting the committed pair; no new literal enters the manuscript. Check the abstract word budget first — 66df169 took it from 248 to 287 words (C-125).
wave: 2
source_rows: C-EIC-05 + C-SY-24

### C-34 — The abstract's 85.7%/91.3% must be stated as composition and fit, not as identified levels
raisers: EIC:W3
severity: MAJOR
class: WORDING
verified: true — abstract ¶1 gives "switch the lock-in response off and the model still accounts for 85.7\% of it" and "A loan-by-loan model run on Freddie Mac data accounts for 91.3\%" while `.tex:319` declares the level unidentified. Partial mitigation the EIC does not credit: the 85.7% sentence already carries a mechanism clause that is a composition statement in substance.
location: abstract `.tex:31`; §V.E `.tex:319`
condition: The null's share must be stated as a decomposition/composition share and the 91.3% as an in-sample fit description, so the abstract and `.tex:319` cannot be read against each other.
fix: Recast the two sentences keeping §V.E's disclaimer language. Overlaps C-04 (form label, abstract leg already landed) and C-35 — all three are edits to `.tex:31`; sequence as one edit.
wave: 2
source_rows: C-EIC-03

### C-35 — Attach floor and basis labels to both abstract figures
raisers: EIC:W3 (second, mechanical edit)
severity: MAJOR
class: WORDING
verified: true — `.tex:31` contains neither "shared basis" nor any floor label; the labelled forms already exist as committed strings at `.tex:66` ("recovery percentages are quoted on the benchmark-consistent shared basis"), `.tex:78` ("85.7\% of benchmark at the headline off-window floor; 88.7\% in-sample") and `.tex:82` ("91.3\% at the headline off-window floor; 97.9\% in-sample").
location: abstract `.tex:31`
condition: Neither abstract figure may stand without a floor label and a basis label.
fix: Add both labels inline reusing the committed wording from `.tex:66/78/82`, so no new literal enters. Land with C-34 and C-04.
wave: 2
source_rows: C-EIC-04

### C-36 — State the scope condition the forced sign implies
raisers: R3:M7, SY:Z16
severity: MAJOR
class: WORDING
verified: true — `.tex:323` prints "97.40\% of exposure at or below 4.79\% and 99.53\% at or below 5.09\%, against a window-minimum 30-year rate of 5.2311\%" (`sign_forcing_stats_results.json` confirms both), and `.tex:590` states the Danish sign "could not have come out otherwise". "99.53" appears at exactly those two lines; §VIII contains no scope restriction, yet it generalizes.
location: §V.E `.tex:323`; §VI.D `.tex:590`; §VIII `.tex:719–751`
condition: The design's central quantity is not identified in a mixed-gap episode; that must be stated as an inequality-form scope condition, attached to the Danish sign-invariance statement as well, so the exercise is not read as transportable to another cycle, country or portfolio.
fix: One sentence in §V.E plus the same sentence at `.tex:590`, and a scope clause in §VIII. No run.
wave: 2
source_rows: C-R3-22 + C-SY-28

### C-37 — State the gate suite's domain in Appendix O ¶1
raisers: DA:M7, SY:Z10/R16
severity: MAJOR (SY: MODERATE, "and the paper should *say* it"); the one condition that strengthens the paper while conceding
class: WORDING
verified: true, verbatim — `tools/liveness_gates.py` docstring declares four gate classes, all reading the .tex and frozen artifacts, numbering to #108; `tools/render_gate.py:2–7` is "the check the 108 source gates structurally cannot make … ~919 text items across 9 pages sat OUTSIDE the physical sheet (the worst page carried 302 items of the Appendix O adjudication ledger more than a full page below the bottom margin)". App. O ¶1 has the self-certification point but not the domain statement or the off-sheet episode. (Do not print a test count: `tests/*.py` defines 293 `def test_` functions against a claimed 495 collected; DA's "479" is unverifiable.)
location: App. O ¶1 `.tex:1395`
condition: Appendix O must state that the gates verify manuscript literals against committed artifacts, cannot test an artifact's premise, and that one defect class they structurally could not see (off-sheet rendering) survived all of them.
fix: One sentence sourced to the two docstrings. Costs no number.
wave: 2
source_rows: C-DA-15 + C-SY-22

### C-38 — Strike "the monotone response across the Liebersohn–Rothstein band" from the identified content
raisers: DA:M4
severity: MAJOR
class: WORDING
verified: true — `.tex:323` reads "the identified content is the marginal's \emph{bounded range}, together with the monotone response across the Liebersohn--Rothstein band, and neither its point magnitude nor its sign"; parallels at `.tex:277` and `.tex:526` (x2). Monotonicity is forced by the same composition-of-monotone-maps argument that retires the 27-cell positivity check (eq:beta1 monotone in delta, `prepay_hazard` exp-linear in beta_1*gap), which the paper already applies to positivity at `.tex:323`.
location: §V.E `.tex:323`; §V.B `.tex:277`; §V.F `.tex:526` (x2)
condition: A forced monotonicity cannot be listed as identified content; the band's monotone response is a wiring check, like positivity.
fix: Strike the clause at all four sites and retain T7 as a wiring/consistency check, mirroring the sentence already used for positivity. Zero numeric change; check gate-pinned spans covering `.tex:323` first.
wave: 2
source_rows: C-DA-12

### C-39 — Decide once whether the Ginnie and vintage overlays are corrections or a change of estimand
raisers: DA:M6
severity: MAJOR
class: WORDING (limb 1) / full restatement (limb 2 — needs a scope decision)
verified: true — `.tex:346` prints both rows verbatim as "change of estimand … not a correction", and the App. O ledger at `.tex:1424` confirms the relabelling was a post-run adjudication. Limb 2 is a large restatement (benchmark denominator plus every recovery percentage), not a wording tweak.
location: T5 rows 3–4 `.tex:346`; ledger `.tex:1424`; §V.B `.tex:219–231`; §III.B `.tex:150`
condition: Either the two overlays are corrections (+4.4 / +3.7 enter the assembly as such and the headline moves), or the estimand is the conventional in-window sub-book — in which case §III.B's 51.0% coverage becomes a definition and the denominator is re-scoped. The rule adopted must be stated once in §V.B and T5 and the ledger must agree with it.
fix: Limb 1 costs no run. Limb 2 must not be attempted without an explicit scope decision.
wave: 2
source_rows: C-DA-14

### C-40 — State the assembly's inclusion rule (and, if it qualifies, add the attenuation row)
raisers: DA:M5, SY:Y3
severity: MAJOR (DA) -> MODERATE (§2.7, "partially upheld"; the remedy is a stated inclusion rule, not a disclosure)
class: CHECK
verified: true — `attenuation_sensitivity_results.json` `selection_identity` S = 40,234/75,000 = 0.53645, `a_grid = [1, 0.8558, 0.7324, 0.5365]`, marginals 5.5716/5.0955/4.6177/3.7037 at floor 4.991, spec string "Direction SIGNED ex ante: a<1, the marginal falls, a DOWNWARD member"; the exclusion rationale is verbatim in T8's note ("a transport sensitivity on the imported coefficient, kept out of the assembly on that ground") and the full grid, frailty identity and measured S are printed in the same cell. The row is absent from T5.
location: T8 `.tex:433`; T5 `.tex:338`; §V.B `.tex:219–231`; ledger `.tex:1424`
condition: Either the attenuation row enters T5 with its theta grid displayed, or the paper states an explicit inclusion rule for the assembly that this row fails and the Ginnie overlay satisfies, applied consistently.
fix: Prefer the stated rule (§2.7's arbitration). If the row is added, note theta is not estimable (`free_parameter_note`). No run. Interacts with C-39 (which asks the same question of the overlays).
wave: 2
source_rows: C-DA-13 + C-SY-12

### C-41 — Attribute the assembly's one-directionality to its cause
raisers: R2:M3 (second half), SY:Z5 framing leg
severity: MAJOR
class: WORDING
verified: true — the posture sentence exists verbatim at three sites: `.tex:31` ("every correction I can measure to the baseline turnover floor or to the accounting basis moves it down within the range rather than up"), `.tex:46`, `.tex:333` ("every correction listed above falls in its lower half"). No entry in T5 or at `.tex:433` is signed upward on the floor side. §2.2 upholds the framing defect: the sentence must not be readable as "the unmeasured ones do too."
location: abstract `.tex:31`; §I `.tex:46`; §V.E `.tex:333`; T5 `.tex:338`
condition: Either the upward floor-side correction enters T5 (C-71), or the manuscript states that the assembly is one-directional because the one available upward floor-side correction was not run.
fix: One clause at `.tex:333` mirrored in the abstract's hedge. This is a **disclosure addition**, not a deletion of the existing claim.
wave: 2
source_rows: C-R2-09

### C-42 — Stop ranking a measured institutional quantity against an unmeasured household one
raisers: R3:M1
severity: MAJOR
class: WORDING
verified: true — `.tex:31` carries the bottom-line pair verbatim; `.tex:52` carries "the trade-off's binding cost is denominated in mobility rather than in institutional cash flow"; `.tex:542` carries the double declination ("I do not translate the \$764.7 billion shortfall into welfare terms… which my accounting framework does not measure"); "welfare" occurs 4x, "per household" 0x.
location: abstract `.tex:31` (final two sentences); §I `.tex:52`; §VI.A `.tex:542`; §VIII `.tex:731`
condition: Either the household side is quantified in the same unit (C-76), or the comparison is explicitly retired: this paper measures the institutional leg only, the mobility leg is imported at the elasticity and never re-measured, so the ranking of legs (2) and (3) is an external-evidence ranking rather than a within-paper measurement.
fix: Rewrite the abstract's closing pair and the §VIII leg-(2)-vs-(3) sentence so the asymmetry is on the page. Discharged instead by C-76/C-82 if they land.
wave: 2
source_rows: C-R3-01

### C-43 — Carry Batzer et al.'s ~$2.4trn to the comparison site
raisers: R3:M1
severity: MAJOR
class: WORDING
verified: true — `batzer2024` occurs exactly once in the .tex (`.tex:100`) and "2.4 trillion" once, in the same clause; the figure is never set beside the $61.2bn institutional gap it dwarfs by ~40x.
location: `.tex:100` (source); comparison sites §VI.A `.tex:542`, §VIII `.tex:731`, T1 Danish row `.tex:86`
condition: The one household-side magnitude the paper carries must appear where the ranking is asserted, with its scope stated (a stock of foregone capital gains on a counterfactual universal-relocation basis, not a flow, not commensurate with a 42-month cash-flow gap).
fix: One sentence at the comparison site. Existing key, existing literal.
wave: 2
source_rows: C-R3-04

### C-44 — Scope the "no outcome-holdout months exist anywhere, without exception" claim
raisers: R3:M2, R2 (evidence basis)
severity: MAJOR
class: WORDING
verified: true / partly — both sites verified verbatim (`.tex:92` italicised, `.tex:741` restating it and naming the nineteen-month temporal holdout as the nearest construction). The existing holdout is on the *calibration*: T6 note a (`.tex:381`) reports the 3.97% floor calibrated on the window's first nineteen months with +$45.1bn over the held-out twenty-three against +$44.8bn at the production floor. So the claim is right in the strict sense and overstated as "nowhere"; and it is unavoidable only for the cash-flow margin — the household margin admits an external outcome moment.
location: `.tex:92`; §VIII.A `.tex:741`; T6 note a `.tex:381`
condition: The claim must be scoped to the cash-flow margin, and the existing temporal holdout named at the site where the no-holdout criticism lands, stating precisely what it holds out (calibration months, not the benchmark).
fix: One clause at each site. If a true outcome holdout is judged infeasible (splitting the benchmark itself), record it infeasible with the reason.
wave: 2
source_rows: C-R3-05 + C-R2-46

### C-45 — Name the fiscal incidence of the 1-P wedge
raisers: R3:M3(a) — R3's "cheapest high-value addition in the paper"
severity: MAJOR
class: WORDING
verified: true — `.tex:273` carries the par-windfall sentence verbatim and `.tex:727` "as reserve drain the rule costs the Federal Reserve exactly the par windfall it would otherwise have extracted from moving households"; word counts in the .tex: "taxpayer" 0, "seigniorage" 0, "deferred asset" 0, "remittance" 3 (all agency-settlement-timing sense). Artifact side confirmed: `gap_face_b = 61.18834`, `early_face_E_b = 470.65325`, `gap_cash_range_b = [-117.660, -89.421]`, `code = "REVERSES"`.
location: §V.B `.tex:273`; §VIII `.tex:727`, `.tex:731`; T13 notes (after `.tex:618`)
condition: Under the cash-haircut reading the wedge is a transfer from the SOMA portfolio — hence from Treasury remittances, hence from general taxpayers — to households who move, and its welfare sign turns on the relative marginal value of public funds versus household liquidity; "costs the Federal Reserve" obscures this.
fix: One paragraph in §VIII plus one line in T13's notes. No new numbers.
wave: 2
source_rows: C-R3-09

### C-46 — Add the missing ex-ante primary-rate offset to §VI.D's omission list
raisers: R3:M3(b)
severity: MAJOR
class: REFERENCE (existing keys)
verified: true — `.tex:586` imports Berger et al.'s ~1bp GE rate effect for the refinance-in-place channel only; `.tex:590`'s omission list is exactly five items with no ex-ante pricing term. Both references R3 names are already in the bib and cited (`campbell2013` at `.tex:729`, `berg2018` at `.tex:112`/`.tex:729`) — nothing to add to the .bib.
location: §VI.D `.tex:590`, `.tex:586`; T13 notes
condition: All Danish figures are ex-post and carry no ex-ante primary-rate offset; under a Danish payoff rule the repurchase option is priced into the coupon, so +$61.2bn is a gross figure and the omission's sign runs against the reported relief.
fix: A sixth item in the omission list plus two lines in T13's notes, citing `campbell2013` and `berg2018` at the new clause.
wave: 2
source_rows: C-R3-10

### C-47 — State that the Danish magnitude inherits every conditionality the marginal has
raisers: DA:A5 (first limb)
severity: MAJOR (inferred)
class: WORDING
verified: true — the paper's own sentence supplies the premise: "the rule-only Danish counterfactual and the paper's lock-in contribution at the in-sample calibration point are one object measured on two accounting legs (+$61.2 billion here … +$70.3 billion as the U.S.-leg marginal)" (`.tex:590`), together with the sign-forcing concession on the same line. What is absent is the explicit inheritance statement for the PSA convention and the floor's age transport.
location: §VI.D `.tex:590`
condition: §VI.D must state that the Danish leg inherits the PSA convention and the age transport because it is the same object on a second accounting leg, so the exercise adds no independent information about the payoff rule.
fix: One clause, no run. Known trap: the $61.2bn equality holds against the **demoted in-sample** point, not the headline off-window one — the inheritance sentence must not re-assert the equality at the headline calibration.
wave: 2
source_rows: C-DA-25

### C-48 — Report the Danish counterfactual in duration units at its own sites
raisers: R2:M5(c)
severity: MAJOR
class: STRUCTURE
verified: partly — the numbers exist in T12 (Danish 9.1/8.2 vs Path B 9.7/8.7, `.tex:562–563`); what does not exist is a duration statement at the Danish result's own sites (§VI.D `.tex:590`, T1 `.tex:85`, §VIII), which quote dollars only.
location: §VI.D `.tex:590`; T1 `.tex:85`; T12 `.tex:562–563`; App. L
condition: Duration is invariant to the face-vs-cash incidence question the dollar metric cannot resolve, so the Danish result must be reported in duration units alongside dollars.
fix: Add the pair (9.1 vs 9.7 years at June 2022; 8.2 vs 8.7 at Nov 2025, ~0.6-year shortening) to the §VI.D sentence and, if it fits, T1's Danish cell, with the point that this metric does not depend on the incidence choice. Committed `wal_table` figures; no run.
wave: 2
source_rows: C-R2-15

### C-49 — T1's Danish cell must lead with the band
raisers: R2:M6, SY:Z7/R9 (T1 leg)
severity: MAJOR
class: WORDING
verified: partly — **per anti-condition A-06**: right for T1's cell (`.tex:85` prints "+\$61.2 billion" with the sign-forcedness and the -$99.9bn anchor but not the +$256.8bn sweep top) and right that the abstract carries no Danish figure at all; **wrong for §I and §VI.D**, both of which already give the band and label +$61.2bn "the zero-refinance edge".
location: T1 Danish row `.tex:85`; abstract `.tex:31` (only if a Danish sentence is reinstated)
condition: Where the rule-only counterfactual is headlined as a single number it must be headlined as the band [+$61.2, +$256.8]bn, the same range-not-point posture the paper applies to its own marginal.
fix: Extend T1's cell to lead with the band and label +$61.2bn as its zero-refinance edge, mirroring `.tex:52`'s existing wording. **Gate impact:** gate #71 (`tools/liveness_gates.py:4061–4073`) requires the *first* paragraph containing `"$+\\$61.2$ billion"` to also carry "forced rather than found" and `"$-\\$99.9$ billion"`, and `table1_disclosed` pins the exact cell substring; the band must be added **around** those spans byte-preserving, and the first-mention ordering property re-checked.
wave: 2
source_rows: C-R2-16

### C-50 — Promote the realized-implied Danish anchor and its four confounds out of a trailing clause
raisers: R2:M6 (second clause)
severity: MAJOR
class: WORDING
verified: partly — the anchor and confounds *are* in the main text at `.tex:590`, but exactly as described structurally: a trailing dependent clause ("the realized-implied anchor sits above the swept range entirely, pricing at $+\$1{,}212$ billion beyond the rejected partial-equilibrium ceiling --- though four confounds travel with it") inside a 1,053-word paragraph. So this is a promotion-within-the-body, not a missing disclosure.
location: §VI.D `.tex:590`
condition: The +$1,212bn realized-implied anchor and its four confounds must be their own sentence(s).
fix: Break the clause out, keeping all four confounds (gross rate, non-household collateral, environment- not book-matched, Danish-tax realization) intact. Overlaps C-87 (paragraph splitting) — do them together.
wave: 2
source_rows: C-R2-17

### C-51 — State the Danish execution mechanics (open-market repurchase and delivery)
raisers: R2:M5(b)
severity: MAJOR (inferred)
class: WORDING (blocked on a reference)
verified: partly — the manuscript's framing is confirmed as an incidence choice between balance adjustment and cash haircut (`.tex:273`, `buyback_credit_bracket.py:30-45`) and `.tex:590` enumerates the transplant's omissions without naming the *execution* mechanism. R2's institutional claim is standard but **not verifiable from this repo** — it is what the missing Frankel et al. (2004) reference would source. Treat as a claim requiring the citation before it is asserted.
location: §VI.D `.tex:590`; §VI.B `.tex:576`
condition: The Danish market-value payoff is executed as an open-market repurchase and delivery of the underlying bonds, so the bondholder sells voluntarily; transplanted onto a passthrough holder the analogue is an outright sale at a discount, which means the par-denominated cap is not the natural scorer for the Danish leg.
fix: One sentence cited to Frankel et al. (2004), drawing the consequence and pointing at the active-sales alternative §VI.B already raises. **Blocked on C-85's Frankel entry.**
wave: 2
source_rows: C-R2-14

### C-52 — State the objective a redemption cap serves, and open §VI.B with §III.B's concession
raisers: R3:M4(a), DA:S2, SY:Z14/R13 (objective leg)
severity: MAJOR
class: WORDING
verified: true — `.tex:576` states the design rule ("A cap intended to bind would therefore be set at or below the lower edge of the book's projected scheduled-plus-turnover principal path") with no objective function and no justification for bindingness; `.tex:150` carries the standing concession verbatim, at the end of a 6,640-char paragraph; §VI.B opens on the arithmetic without restating it. Binding the MBS cap forces reinvestment above the ceiling and so slows the MBS decline — against §I's Treasuries-only framing.
location: §VI.B `.tex:544`, `.tex:576`; §III.B `.tex:150`; §I `.tex:38–40`
condition: §VI.B must open with §III.B's concession and state the objective a cap serves (predictability and communication of the composition path, not maximal speed), noting that binding the MBS cap is inconsistent with the stated composition goal.
fix: One opening sentence carrying the concession forward plus an objective-function sentence before `.tex:576`'s design rule, cross-referencing §III.B so the concession is discharged where it is used; plus a pointer to the WAL/duration figures as the policy object the composition shortfall actually moves.
wave: 2
source_rows: C-R3-11 + C-DA-28

### C-53 — Make the substitution instrument the stated design implication
raisers: R3:M4(a)
severity: MAJOR
class: WORDING
verified: true — `.tex:574` puts both options in one sentence inside the paragraph flagged speculative, and the binding-cap rule then gets its own sentence at `.tex:576`, giving it the emphasis; the substitution option is the one consistent with §III.B.
location: §VI.B `.tex:574`
condition: The recommendation should be "publish the projected path with its band and pre-commit the substitution instrument", not "lower the cap".
fix: Reorder §VI.B's closing so the substitution instrument is the stated design implication and the cap level the subordinate clause; keep the speculative flag on both.
wave: 2
source_rows: C-R3-12

### C-54 — Restate §VI.B's result in $bn/month with a band
raisers: R3:M4(c)/Carroll slide 2, SY:Z14/R13
severity: MAJOR (SY: "the paper's most exportable contribution")
class: STRUCTURE + WORDING
verified: partly — the multiples and inputs reproduce exactly: $740.6bn / 42 = $17.63bn/month, caps $1,417.5bn / 42 = $33.75bn/month, ratio 1.914; the wild-cluster floor interval 4.177–5.800 = 1.623 CPR points is ~$3.6bn/month on the $2.70trn book (R3's ±$4bn). But R3's second multiple rests on a settlement-aware total of **$839.5bn the .tex never prints** (derivable as 652.752 + 186.778 from `expectation_benchmark_results.json`, giving $20.0bn/month and 1.689) — printing it creates a new literal needing a gate. §VI.B currently prints no $bn/month figure and no band.
location: §VI.B `.tex:546`, `.tex:574`
condition: The cap result must be stated in the units of a cap decision: achievable passive MBS principal ~$17.6bn/month (uniform-spread allocation) and ~$20.0bn/month (settlement-aware) against the $33.75bn/month average ceiling, with ~±$3.6bn/month from the floor read's own sampling interval.
fix: Rewrite §VI.B around the band; extend (do not replace) the state-contingent cap band already in §VI.B from committed reads (4.70–5.33% floors -> +6.8/+4.3 marginals, NY Fed $20–30bn precedent) into $bn/month. Gate any newly printed literal.
wave: 2
source_rows: C-R3-14 + C-SY-26 + C-SY-45

### C-55 — State the marginal's share of the duration extension where the fragility channel is introduced
raisers: R3:M5(item 1)
severity: MAJOR
class: WORDING
verified: true — `.tex:538` introduces the fragility channel ("this extension, not the cap arithmetic, feeds the fragility channels below") and `.tex:540`, one paragraph later, carries "shortens the portfolio by only 0.6 of the roughly six extension-years … a second-order contributor"; App. L `.tex:1328` derives both numbers; T12 `.tex:566` shows the whole extension is delivered at the floor alone (9.5 vs the empirical 9.4).
location: §VI.A `.tex:538`, `.tex:540`; App. L `.tex:1328`; abstract `.tex:31`; §VIII `.tex:721–731`
condition: The identified elasticity accounts for ~0.6 of the ~6.0 extension-years the paper says feed the fragility channel; that share must sit where the channel is introduced and be carried to the abstract and the conclusion.
fix: Move the maturity-unit share into `.tex:538` and add the clause to the abstract's institutional-cost sentence and §VIII. Zero new literals.
wave: 2
source_rows: C-R3-16

### C-56 — Restrict the institutional-cost claim to cash-flow timing (or price the 0.6 year)
raisers: R3:M5(fix iii)
severity: MAJOR
class: WORDING (cheap branch) / RUN (expensive branch, not recommended)
verified: true — the paper cites `jiang2023`'s ~$2trn of bank mark-to-market losses (`.tex:108`) but puts no mark-to-market number on SOMA, and App. L `.tex:1328` explicitly declines option-adjusted duration and convexity as out of scope.
location: §VI.A `.tex:538–540`; App. L `.tex:1328`
condition: Either a market-value/DV01 image of the 0.6 WAL-year is put on the book, or the institutional-cost claim is restricted explicitly to cash-flow timing and the fragility framing cut to a single referenced sentence.
fix: Take the wording branch (restrict + one sentence citing `jiang2023`). The expensive branch needs a discount curve the design does not carry and would reopen App. L's scope declination — Eugene's call if wanted.
wave: 2
source_rows: C-R3-17

### C-57 — Label the recurrence claim as outside what the design tests
raisers: R3:M7(fix iii)
severity: MAJOR
class: WORDING
verified: partly — the §VIII sentence already carries a state-dependence qualifier citing `berger2021` and `eichenbaum2022`, so conditionality is present; what is missing is the explicit out-of-scope label.
location: §VIII `.tex:731`
condition: The claim that severe duration extension should be expected to recur must be labelled as outside what this design tests.
fix: One phrase added to the existing conditional clause; no new content.
wave: 2
source_rows: C-R3-24

### C-58 — Ask the cross-country generalization question using Du et al.'s record
raisers: R3:M7(fix ii) / opportunity 3
severity: MAJOR (R3: "the paper's most exportable contribution" on their reading)
class: STRUCTURE
verified: true — `du2024` occurs exactly once (`.tex:114`) and is used only to place the paper in that literature; the key is already in `references.bib`.
location: §II `.tex:114`; new §VI.B paragraph or short subsection
condition: The paper should ask whether other central banks' passive-runoff caps were similarly non-binding, framed by Du et al.'s seven-central-bank record, and state what data would settle it (per-bank announced caps against realized redemptions).
fix: One short paragraph. Do **not** assert the generalization — the ask is the question plus the data requirement, and it costs no run.
wave: 2
source_rows: C-R3-23

### C-59 — Make the assumability bound two-sided in one edit
raisers: R2:M4(c) + R2 minor 9
severity: MAJOR (R2 calls the CRR bound "a bonus the paper is leaving on the table")
class: WORDING
verified: true — the concession is at `.tex:52` verbatim ("Realized take-up … is not measured anywhere in this design, so the 20.4\% share bounds the carve-out from above rather than sizing it"); the mechanism is the paper's own (`.tex:580` "an assumed loan also fails to prepay"); the CRR differential is +1.354pp **above** conventional on the window mean, which is the direction that caps take-up. No frictions are named at `.tex:52`; §VI.C names only the price-minus-balance financing gap.
location: §I `.tex:52`; §VIII.A; §VI.C `.tex:580`
condition: Two clauses must land together: (i) Ginnie voluntary speeds run 1.35pp above conventional, and since an assumed loan does not prepay, materially high take-up would show as *slower* Ginnie voluntary speeds — so the observed differential caps realized take-up; (ii) FHA/VA assumption is subject to creditworthiness qualification, servicer processing, occupancy restrictions and VA entitlement-restoration considerations, so the 20.4% share bounds from above only if assumption is frictionless.
fix: One edit at `.tex:52` (plus the §VIII.A counterpart) carrying both directions; sourced to `gmar_dec25_cpr_series.json` and, for the frictions, to C-85/C-86's citations.
wave: 2
source_rows: C-R2-12 + C-R2-31

### C-60 — Concede that the investor-side cost of the Danish transplant is unpriced
raisers: DA:S3
severity: MAJOR (inferred)
class: WORDING
verified: true — `.tex:731` reads "The binding constraint against adopting such a rule is therefore not a mobility--cash-flow trade-off but the TBA liquidity premium described above", resting on cited work; nothing in the paper prices a series-level call, the hedging-cost shift, or originator warehousing. §VIII.A's nearest statement is narrower (`.tex:741`).
location: §VIII `.tex:731`; §VIII.A `.tex:741`
condition: The "TBA liquidity premium is the binding constraint" claim must be relabelled as an argument from the literature rather than a result, with the investor-side cost named unpriced.
fix: One sentence. Keep verbally distinct from C-05's "binding layer" (uncertainty sense) — two different "binding"s are being qualified this round.
wave: 2
source_rows: C-DA-29

### C-61 — Name the housing-supply/inventory channel as an unmodelled competing channel
raisers: DA:A3
severity: MAJOR (inferred)
class: REFERENCE + WORDING
verified: partly — §I mentions "historic housing inventory shortages" once (`.tex:56`) and §VIII.A contains no housing-supply or inventory limitation at all (read in full). But "never returns" is not exact: inventory enters the ABM friction calibration through FRED Active Listing Count shortfall (`.tex:919`) as a search-friction scaler, not a competing explanation. DA's sign claim (a floor read on normal-inventory 2018 cohorts is too high for a low-inventory window, biasing the marginal down) is an argument, not a measured result, and nothing in the artifacts prices it.
location: §VIII.A `.tex:733–752`; §I `.tex:56`; T5 row `.tex:349`; §V.E `.tex:333`
condition: §VIII.A must name the housing-supply channel as an unpriced competing channel with its sign stated as argued-not-measured, cross-referencing the existing friction scaler and the phi*=0.754 scaled-null run so the paper is not read as ignoring inventory.
fix: One limitation paragraph citing `aladangady2024` (already in the bib) plus at least one supply-side source. No run.
wave: 2
source_rows: C-DA-23

### C-62 — Recast the open timing question as possibly ill-posed
raisers: DA:A4
severity: MAJOR (inferred)
class: WORDING
verified: partly — the concessions are verbatim ("no servicer channel beyond that pipeline is modeled at all" at `.tex:528`, `.tex:532`, `.tex:725`; "the path-level timing question remains open for every estimator" at `.tex:752`), and `.tex:186` already floats a near-neighbour of the reporting-mechanics account. Both supporting figures check out ($722bn settlement-aligned benchmark, -5.5% re-basing; four exact-zero months traced to the non-negativity clip). ONE imprecision: DA says the zero months "flip the frozen timing rule" — `.tex:1356` says the rule PASSED and that nothing is claimed from the pass because five post-hoc diagnostics cannot discriminate. Do not restate it as a flip.
location: §VIII.A `.tex:752`; §VI.A `.tex:528`, `.tex:532`; §VII.B; App. N
condition: The paper should name the reporting-and-remittance account as a candidate under which the empirical monthly series is not a behavioral object, so the open timing question is stated as possibly ill-posed rather than as a shared estimator failure.
fix: Recast the framing in §VIII.A and the §VI.A residual passage, anchored on `.tex:186`'s existing sentence. No run.
wave: 2
source_rows: C-DA-24

### C-63 — Name the object behind §VII.E's 3.9% origin
raisers: R2:M2 (second clause)
severity: MAJOR
class: WORDING
verified: true — `.tex:701` reads "balance-weighted estimates on the Freddie sample's composition, whose weighted-average coupon (3.9\%) sits above the SOMA book's (2.49\%)"; "sample" there is the 75,000-loan draw (3.8649%), and the sentence never distinguishes it from the universe panel T25 displays.
location: §VII.E `.tex:701`
condition: §VII.E must say which object the full-book reweight's origin is — the draw's own WAC — since the shift it is displayed against in T25 is the universe's.
fix: One clause naming the draw (3.86%) and stating that T25's bucket shares are the exposure-weighted estimation universe. **The `100.4`/`98.1`/`107.0`/`109.1` literals in that sentence are gate-pinned (gate #106 `COUPON_CONVENTION_SPANS`, `tools/liveness_gates.py:~710–724`) and must survive byte-identically.**
wave: 2
source_rows: C-R2-07

### C-64 — T25 must stop presenting two populations as one row, and must show the draw's own composition
raisers: R2:M1(i)/M2, SY:§2.5/Z1-labeling
severity: MAJOR (R2) -> confirmed as a labeling defect, downgraded (§2.5)
class: STRUCTURE
verified: true / partly — the printed 18.0/68.2/13.8 are `freddie.universe_panel.coupon_shares_exposure_weighted` bucketed, while the "3.9%" in the same note is `freddie.sample.mean_coupon_pct = 3.8649` (the draw): two populations in one row, confirmed. All three objects exist in `composition_shift_results.json` (draw UPB vintage shares 17.84/17.94/19.73/22.17/22.32; universe 12.47/37.28/50.25; book face 10.6/6.0/16.3/43.9/23.1). **Per A-07, do not restate the draw's >=4.0% share as an unqualified 53.7%** (53.7 UPB-weighted rounded buckets, 58.2 count-weighted, 47.0 raw).
location: T25 `tab:composition` panel (a) `.tex:1279–1283` (vintage row 1281, coupon row 1282); tablenote `.tex:1294`
condition: T25 must carry the draw's own vintage and coupon composition beside the estimation-universe panel, each row labelled with which population and which weighting it describes, and the WAC attributed to the draw.
fix: One table edit adding a third column (or labelled sub-rows) with **both** count and balance-weighted draw shares (only the latter enters the aggregation), and repairing the `.tex:1294` note. No gate pins `13.8` or `3.9\%`. The count shares are a parquet fact, not in the artifact — cite `loan_sample.py`'s allocation rule (C-06) for them or print the artifact's UPB row.
wave: 2
source_rows: C-R2-02 + C-R2-06 + C-SY-49

### C-65 — Fallback: state the headline as conditional on the draw's composition
raisers: R2:M1 (closing sentence)
severity: MAJOR
class: WORDING
verified: true — `.tex:31` reads "Inside that range, +5.6 points, or \$42.6 billion, is the value at the calibration I headline" with no composition conditioning; the two limbs R2 signs (seasoning limb inflationary via the floor gate, gap-depth limb deflationary via H(1-d)) are nowhere signed in the .tex.
location: abstract `.tex:31`; T1 marginal cell `.tex:79`; §V.E `.tex:333`
condition: Absent C-07, the headline must be stated as "+5.6 points on a pool whose vintage and coupon composition differ materially from the book's, in directions that have not been signed."
fix: Add the conditioning clause at the three quoting sites. This is the fallback, not the preferred fix — R2 says the run is available. Do not delete existing disclosure language to make room.
wave: 2
source_rows: C-R2-05

### C-66 — Scope the "Two Structurally Distinct Estimators" framing
raisers: R1 (argument-coherence basis)
severity: MAJOR (inferred)
class: WORDING
verified: true — the heading (`.tex:120`) and both framing sentences (`.tex:50`, `.tex:58`) are verbatim, but the decomposition and the marginal are Path B objects only: Path A is excluded from every headline (resimulation interval spans zero) and the ABM null's two readings disagree in sign (+270.4 vs -105.3, carried in `LETTER_CURRENT_LITERALS`, `tools/liveness_gates.py:739`).
location: §III.A heading `.tex:120`; framing sentences `.tex:50`, `.tex:58`
condition: The framing must be scoped where the decomposition is introduced: two estimators for the aggregate level, one for the mechanical/elastic partition.
fix: Wording at the three sites. Heading edits may be gate-pinned — check `tools/liveness_gates.py` and `tests/test_render_gate.py` for the subsection title first.
wave: 2
source_rows: C-R1-35

### C-67 — State the design's resolution once and stop leaning on one-decimal endpoint comparisons
raisers: R1 (evidence-sufficiency basis)
severity: MAJOR (inferred)
class: WORDING
verified: partly — the manuscript already prints to one decimal and repeatedly says the range rather than any point is the identified content, so the target is *endpoint* resolution (+2.9 vs +2.3 across rungs, ±0.06pp between weight schemes), not spurious digits. Supporting facts hold: no outcome holdout (`.tex:716` "a floor-stability check rather than an outcome holdout"), the elasticity entirely external with no SE, and 49% of SOMA book face outside the estimation universe (the paper prints the 51.0% complement at `.tex:146`).
location: abstract `.tex:31`; T1 row 4 `.tex:79`; T8 `.tex:433`; T9 rows `.tex:456–465`
condition: The design's resolution must be stated once (the interval is credible to about half a point, given a 0.06pp weight-scheme wobble against a 5pp-wide ladder).
fix: One sentence; no run. Coordinate with C-24 and C-20.
wave: 2
source_rows: C-R1-37

### C-68 — Recast the U.S. tax override as one reading, with the §108 exclusions and the implementing regulation
raisers: EIC:W8-adjacent, R3 minor 2, DA:m2  [CONSENSUS]
severity: MAJOR (EIC/R3 rate it MINOR; DA MINOR; consolidated as MAJOR because three raisers converge on one asserted legal conclusion that shrinks a channel)
class: REFERENCE + WORDING
verified: true — `.tex:586` carries the override verbatim ("a characterization U.S. law does not support: a discount extinguishment is cancellation-of-debt income at ordinary rates, IRC \S 61(a)(11) … both corrections push the U.S.-transplant channel *below* Berger et al.'s already-small estimate"); neither "\S 108" nor "1.61-12" nor "insolven" occurs anywhere in the .tex. In a transplant counterfactual U.S. tax treatment is a legislative choice, not a datum, so it lets a design parameter do the work of evidence — in the direction that preserves the ~0 pin the paper's own Danish redemption data then contradicts.
location: §VI.D `.tex:586`
condition: The parenthesis must be rewritten as a reading the paper does not adjudicate rather than a correction, cite the implementing regulation (Treas. Reg. §1.61-12(c)), address §108(a)(1)(B)/(E), and be presented as a directional bracket; the tax attenuation must be reclassified as a design parameter.
fix: Rewrite the parenthesis and move the legal reading to a footnote carrying the exclusions. The direction-of-effect sentence and the "neither touches the realized Danish evidence" clause must survive the edit. Satisfied by a defensible citation, not by a number.
wave: 2
source_rows: C-EIC-11 + C-R3-26 + C-DA-18

### C-69 — Say that a pre-committed externally-anchored member lies outside the quoted interval
raisers: R1:M5
severity: MAJOR
class: WORDING
verified: partly — the run reproduces exactly (`scaled_null_housing_activity_results.json` `root["4.991"]`: phi* = 0.75390625, marginal_pp = 0.8979, marginal_b = 6.866; anchor `aladangady2024` 0.44/0.56), but "nothing follows" is wrong: `.tex:333` states the root, the +0.9/+3.5 pair, the bit-exact phi=1 parity, and two consequence sentences. What does not follow is any statement that the member lies *outside the quoted interval* — that word is not used there.
location: T5 `tab:assembly` `.tex:338`; §V.E ¶7 `.tex:333`
condition: The manuscript must state explicitly that a pre-committed externally-anchored calibration returns +0.9pp, outside the quoted interval.
fix: One clause; no run.
wave: 2
source_rows: C-R1-17

### C-70 — RUN: calendar-standardize the off-window floor read to the QT window's month mix
raisers: R1:M3, SY:Z4/R7(a)
severity: MAJOR; required before submission
class: RUN
verified: true, reproduces to the decimal in two inventories — `seasonal_floor_timing_results.json` `h_month_normalizations_annual_cpr.shape_only` (Jan–Dec) = 2.5036/2.7565/3.7502/4.2218/4.9374/5.2619/4.8135/4.7157/4.1301/3.9225/3.2517/3.1143, `peak_to_trough = 2.1307`, `h_month_exposure_weighted_mean.shape_only = 0.04000` (the pinned 4.000%). Weighting Jul–Dec by 2/48/48/49/49/49 gives **3.83003%**, so 4.991 x 4.000/3.83003 = **5.2124%**, mapping through the committed PCHIP grid to ~+4.7/+4.8pp — a **-0.8pp** move. Nothing of this is in the manuscript: App. N prices only within-window floor dispersion (-$4.897B Jensen, 89.2% surviving month-scrambling) and the timing concession.
location: new run; then §VII.F `.tex:713`, T6 `.tex:362`, T8 headline row `.tex:433`, T5 `.tex:338`, App. N `.tex:1342–1392`
condition: The read months sit in the descending half of the paper's own committed calendar profile while the floor is applied flat across all 42 QT months; that standardization must be measured and reported, and if judged too dependent on the full-panel profile basis, reported as an indicative bound in the same register as the 5.51% age-standardized read and joined to the "open below +4.3" concession.
fix: Re-read with calendar-month standardization using `hazard/seasonal_floor_timing.py`'s own 12-cell profile builder/normalizer (full-panel basis, as every committed leg uses), remap through the frozen PCHIP grid, report the standardized read beside the raw 4.991% and restate T6's band and T8's calibration column; add a T5 row labelled directional. New artifact (e.g. `seasonal_standardized_floor_read_results.json`) with a parity gate reproducing the `shape_only` vector and the 4.991% raw read bit-exactly. Depends on C-02's month histogram being re-derived under the committed selection (the 137 retained rows, not the 245 candidates). Two disclosures the run must carry, both already in-repo: the off-window leg cannot support its own 12-cell profile (`.tex:1362`; 335 cohort-months, zero prepaid balance in February and April), and the profile's deep-OTM filter captures 98.2% of QT exposure. Gate pins to move: `ASSEMBLY_SPANS["ladder_agestd"]` (`:385`) and the literal `"open below $+4.3$"` (`:4576`). **Must be run with C-71 as a pair** — running only this half makes the paper worse-off honestly; running only C-71 is self-serving.
wave: 3
source_rows: C-R1-09 + C-R1-10 + C-SY-16 + C-SY-39 (C-SY-39 governs both halves; cross-listed at C-71)

### C-71 — RUN: measure the floor read's dependence on housing-activity level and report an activity-matched read
raisers: R2:M3, SY:Z5/R7(b)
severity: MAJOR — the CHARACTER of the complaint arbitrated down (§2.2: the paper's sentence is literally true; the defect is framing); this is the assembly's **one available upward** floor-side correction
class: RUN
verified: partly — TRUE that the floor is total deep-discount turnover, not involuntary-only, in the paper's own words (`.tex:227`, `.tex:92`, `.tex:709`), so it is activity-level dependent by construction; TRUE that the demotion split is 20.874 / 7.438 / 73.7 / 26.3 (`matched_depth_reconciliation_results.json` `window_component_b = -20.8736`, `depth_component_b = -7.4379`, `window_share_of_total = 0.7373`); TRUE that the sizing anchor is already in the paper (`.tex:102`, Aladangady 44%: 0.56 x 20.874 = 11.69 = $11.7bn = 1.53pp of $764.7bn, and 5.6 + 1.5 = 7.1). **WRONG in one number:** R2's "in-window read of 3.8–3.9% is 4.99 x 0.77" — T6's in-window reads are 4.00% and 3.97%, ratio 0.795, so the "almost exact" coincidence is 0.13–0.16pp loose and must not be quoted as printed. **NOT VERIFIABLE FROM THE REPO:** the existing-home-sales levels (5.34M 2018 vs 4.09M 2023) are external NAR data; "existing-home sales" appears nowhere in the .tex. The synthesis records the 24% activity ratio as R2's external datum, not verified.
location: new run; then T6 `.tex:362–375`, T5 `.tex:338`, §VII.F `.tex:713`
condition: The share of the demotion charged to "the window" must not silently charge a housing-cycle level effect to lock-in circularity; the marginal must be reported at an activity-matched off-window floor.
fix: Measure the floor read's activity dependence across the three 2017–2019 legs (which differ in activity as well as rate regime, `.tex:1312`), instrumenting activity with something not driven by the coupon gap (new-home sales, the all-cash share, or the non-mortgaged share of existing-home sales); report as a new T6 row plus a signed assembly entry. Machinery: the floor-read path behind `tab:oosfloor` / `floor_sweep` / `oos_identification`; new artifact (e.g. `floor_activity_match_results.json`). **Requires external housing-activity data the repository does not hold** — if it cannot be obtained, record INFEASIBLE with that reason and land C-41's disclosure instead. Regardless of outcome, repair the framing defect §2.2 upholds.
wave: 3
source_rows: C-R2-08 + C-SY-17 (+ C-SY-39, cross-listed from C-70)

### C-72 — RUN: add a month-clustered rung and a two-way (stratum x month) rung to the ladder
raisers: R1:M3
severity: MAJOR
class: RUN
verified: true — no "month-clustered" and no "two-way" string exists anywhere in the manuscript; the committed cluster unit is cross-sectional only (`floor_uncertainty_results.json` `part_a_sampling_uncertainty.cluster_unit = "4-way stratum (vintage x coupon-bps x fico_bucket x ltv_bucket)"`).
location: T9 `tab:ladder` `.tex:445–468`
condition: The month-level common shock the current scheme cannot see must be priced, or shown not to matter.
fix: Compute month-clustered (G~6) and two-way stratum x month CR/wild-t intervals on the R2 read and map endpoints through the frozen PCHIP grid exactly as the committed path does (`hazard/floor_inference_correction.py:36–50`, whose grid-edge-truncation convention and refusal to extrapolate must be reused). Machinery: `hazard/floor_uncertainty.py`'s `cluster_bootstrap_cpr` (cluster unit is a read parameter) plus `hazard/floor_inference_correction_v2.py`'s Webb/BM/WCR constructions. New artifact (e.g. `floor_inference_correction_v3_results.json`) with the same P1–P7 parity gates; two new T9 rows plus a note clause. **Pre-commit a NOT_COMPUTABLE landing:** with 5–6 month clusters and 31 strata the two-way estimator's df is tiny, and `episode_confrontation_within_results.json` `limb_c.confounds_note` already records a two-way (stratum + month) FE variant of the neighbouring within-estimator as "EXACTLY unidentified".
wave: 3
source_rows: C-R1-07

### C-73 — RUN (analytic): recompute the implied cross-sectional gradient at the headline floor and under the additive form
raisers: R1:M7, SY:X8/R14
severity: MAJOR
class: RUN (analytic, engine-free)
verified: true — every figure reproduces from `episode_confrontation_results.json`: `realized_gradient_pp = 4.19818`, CI [3.58526, 4.65648], `model_implied_gradient_pp_at_0.069 = 0.93711`, `realized_over_implied_mid = 4.47991`, `power_injected = 0.675`, branch T5, permutation p = 0.004975; composition-standardized +3.4409 (CI [+1.170,+5.140]) in the within-artifact. Both enabling facts are in the artifact's own spec: the implied path is **ANALYTIC** from hazard eq.(2) at production floor 4% / FLOOR_MODE max / PSA-100 with NO engine run, and the censoring asymmetry is `floor_bind_share` 0.6882 at 4.991 against 0.3627 at 4.0. The 4.5x miss is printed at `.tex:315`.
location: §V.D `.tex:315`; §V.E qualification six `.tex:333`; T5 last row `.tex:338`; then §VII.F `.tex:709–718`
condition: The one internal test of the imported elasticity's implied magnitude is computed at a demoted calibration and declined rather than diagnosed; it must be recomputed at the 4.991% headline floor and under the additive form, at 75/100/125 PSA — and if the implied gradient approaches the realized +3.4 to +4.2 only at additive or steeper-ramp settings, that is the paper's first realized-data evidence on the form fork and belongs in §VII.F's form discussion, not filed in T5 as a declined directional counterweight.
fix: Evaluate the same analytic path max(h_floor, h0_PSA(age) e^{-beta_1 100 g}) at (a) h_floor = 4.991% CPR and (b) the additive combination h = 1-(1-h_floor)(1-h_vol), each at 75/100/125 PSA, on the frozen bucket definitions. Machinery: `hazard/episode_confrontation.py` (its `main()` must NOT be called — it would rewrite the frozen artifact; `hazard/episode_confrontation_within.py` shows the established pattern of replicating the committed gates line-for-line) plus `hazard/competing_risks.py` for the additive survival-scale combination. New artifact (e.g. `episode_implied_gradient_grid_results.json`) with a G-gate reproducing +0.9371 at the committed 4%/max/PSA-100 cell bit-exactly. Must not touch `episode_confrontation.py`, its artifact, or the pinned +4.20 / [+3.59,+4.66] / +0.94 / 0.68 / p=0.005 literals (`spec.must_not_change`). Keep the existing T5 row and its "directional; not a marginal re-estimate" status; the artifact's verdict forbids reading an excess gradient as corroboration of beta_1.
wave: 3
source_rows: C-R1-22 + C-R1-23 + C-SY-08 + C-SY-46

### C-74 — RUN: score the Ginnie leg with the elasticity attenuated by the measured CRR differential
raisers: R2:M4(b), SY:Z6/R10 (run leg)
severity: MAJOR
class: RUN
verified: true, and cheaper than R2 knows — `.tex:271` confirms the overlay scores the Ginnie share "by the observed Ginnie speed in *both* Path B legs", so that share contributes zero marginal, and "the marginal correction is pure conventional-share scaling ($0.797\times$), identical across the primary, voluntary-only, and placebo series"; a voluntary-only (CRR) series is therefore already wired into the overlay run as a level variant (`ginnie_cpr_overlay_results.json` carries a `crr_only` variant, `marginal_pp = 7.3332`).
location: §V.B `.tex:271`; T8 `.tex:433`; new artifact
condition: The 20.4% Ginnie share should generate a weaker marginal, measured, rather than none, assumed.
fix: Re-run the overlay with the elasticity on the Ginnie share multiplied by an attenuation derived from the measured CRR differential (Ginnie voluntary +1.354pp above conventional on the window mean) instead of zeroing that share's marginal; report beside the +4.4 share-scaled figure. Machinery: `ginnie_cpr_overlay` / `ginnie_overlay_offwindow`, already consuming `gmar_dec25_cpr_series.json`'s `crr` block. New artifact (e.g. `ginnie_overlay_attenuated_results.json`). **Direction is not obvious ex ante** — faster voluntary Ginnie speeds are consistent with a weaker gap response, which would raise the retained marginal above 0.797x share scaling; the spec must pre-authorise either sign. Bears on 20.4% of book face.
wave: 3
source_rows: C-R2-11 + C-SY-42

### C-75 — RUN: re-derive the Danish buyback discount D from the leg's own prepayment speed
raisers: R2:M5, EIC:W8, R3:M3, DA:m2/A5, SY:X9/Z7/R9  [CONSENSUS]
severity: MAJOR; "do not quote -$89/-$118bn aloud until done" (R2's explicit pre-talk precondition)
class: RUN (1 calculation) + WORDING
verified: partly/true — TRUE that D is asserted, never derived: `hazard/buyback_credit_bracket.py:33` calls the grid "the manuscript's committed proxy range", `:107` hard-codes `D_GRID = [0.32, 0.34, 0.36, 0.38]`, the artifact spec repeats the phrase, `.tex:273` states the band with no derivation and `TECHNICAL.md` has no derivation. TRUE that the chain is `gap_cash(D) = 61.18834 - D x 470.65325` (a committed parity gate), giving `gap_cash_range_b = [-117.660, -89.421]`, `verdict.code = "REVERSES"`, against the leg's printed 5.61% CPR. Re-pricing at D = 0.22/0.24 gives **-$42.4bn to -$51.8bn**, so every magnitude roughly halves and the REVERSES verdict survives. PARTLY on the diagnosis: an independent zero-CPR PV of a 3.0% pass-through at 6.8% gives ~34.2% against R2's 36.5% — same order, so the "no-prepay annuity PV" identification is plausible but not exactly reproduced; R2's 21–24% limb and the TBA cross-check are not reproducible without the run.
location: `.tex:273`; T1 row `.tex:85`; §VI.D `.tex:590`; T13 `.tex:605`; §VIII; also `.tex:52`, `.tex:727`, `.tex:731`, `.tex:1424`
condition: D must be derived from the Danish leg's own simulated cash flows at its own 5.61% CPR against the window market-rate path (or from matched-coupon/matched-month TBA marks), and every dependent figure restated.
fix: Price each month's retired face at its own prepayment-consistent PV using the committed `microsim_results_us_intercept.parquet` path (the same file `buyback_credit_bracket.py` already reads for E), publish a derived grid in a new artifact, and restate the bracket. **Gate impact, same change:** `BUYBACK_BRACKET_SPANS["reversal_range"]` (`tools/liveness_gates.py:~645`) pins the literal `"$-\\$89.4$ to $-\\$117.7$ billion"` and `tests/test_buyback_incidence_gate.py::test_each_span_removal_fails` asserts each span is present — gate #103 and its test must be updated to the re-derived range, not bypassed. Land C-49's band and C-51's mechanics sentence with it.
wave: 3
source_rows: C-R2-13 + C-SY-09 + C-SY-19 + C-SY-41

### C-76 — RUN: express the marginal in transaction counts and set it against realized mortgage-financed volume
raisers: R3:M1/M2, DA:S1, SY:X5/Y1/R12  [CONSENSUS]
severity: MAJOR; the paper's first outcome-side external check and the only unit in which the household leg becomes commensurable
class: RUN
verified: true / partly — the gap is verified (no such comparison exists in the .tex; `.tex:741` concedes no outcome-holdout months exist; T1 has no household row). The arithmetic reproduces on committed data: `loan_sample.parquet` mean `balance` = **126,812.61**; $42.6bn / $250k ~ 170k payoffs over 42 months ~ 49k/yr; `microsim_results.parquet` `exposure` opens at $2.7025trn, so the ~21% SOMA share against $12.5–13trn 1–4 family debt is right; the s=1 production convention that makes the count an upper bound on the moving component is at `.tex:261`. R3's strain arithmetic: ~230k/yr whole-market at most against ~1.3m/yr fewer mortgage payoffs implied by the 6.1m->4.1m existing-home-sales decline, about one-sixth, against Aladangady's 44% attribution. **Provenance caveat A-08:** 40,234 is the manuscript's window-start survivor count (`.tex:1085`), not a parquet `balance > 0` count (40,077) — use the manuscript figure and do not swap it.
location: new script; §VI.A `.tex:534–543`; T1 `.tex:67`; inputs `.tex:1085`, `.tex:261`, `.tex:333`
condition: The central-minus-null prepaid-face differential must be converted into a count of foregone payoffs with the moving-share bracket applied, grossed to the whole market by the SOMA exposure share, and compared against realized existing-home-sale volume x the mortgage-financed share for the same months — with the verdict stated whichever way it falls.
fix: Compute the count inside the existing Path B machinery (divide the differential — $42.61bn at the headline floor, $70.35bn in-sample, band $33.31–51.75bn — by the run's own mean active-loan balance, ~$236k per active loan) with s in {0.25, 0.5, 1} from `moving_share_bracket_offwindow`; DA's suppressed-move variant is the difference in cumulative move-hazard between the central and beta_1=0 legs. **Two honesty constraints:** aggregate face / mean balance is an approximation to a transaction count (curtailment and partial prepayment are in the numerator), and the hazard is total prepayment with no move/refi split (`.tex:231`) — so the output is a bound, not a count; do NOT print a move count that silently treats prepayment as moving, and record infeasible with that reason if the split makes it uninterpretable. External inputs (sales volume, mortgage-financed share) are **not in the repo** and must be pinned like any other benchmark input. Confounds to name: the SOMA book is compositionally more locked-in than the market average (widening the discrepancy), and the denominator decline includes non-rate causes. Pre-authorise an unfavourable landing.
wave: 3
source_rows: C-R3-02 + C-R3-06 + C-DA-27 + C-SY-05 + C-SY-44

### C-77 — RUN: re-solve the Aladangady reconciliation under the additive floor form, and mark the row either way
raisers: R3:M2(fix ii)
severity: MAJOR
class: RUN + WORDING
verified: true / partly — `scaled_null_housing_activity_results.json` fixes FLOOR_MODE at production (max) and scales the PSA baseline h0 only; root phi* = 0.75390625 at the 4.991% floor driving `marginal_pp = 0.8979`. The additive machinery exists and is production code (`floor_form_mixture_results.json` parity gate `P_marg_4.991_s1 = 85.705`, s=1 = additive). The T5 row itself carries no form mark (`.tex:346`), though the introducing paragraph does (`.tex:334`, "Holding the production hard-maximum form and the imported elasticity fixed").
location: run `scaled_null_housing_activity`; T5 row `.tex:346`
condition: A reconciliation run only under the form that censors in 68.8% of loan-months cannot stand unmarked while the max-vs-additive fork is the paper's largest open question; the row must be marked form-conditional either way.
fix: Re-solve the same calibration condition `trapped_null(phi*) - trapped_null(1) = (0.56/0.44)[central(1) - null(1)]` with FLOOR_MODE additive (s=1) at both committed floors, using the existing bisection harness; expected direction is that with no censoring more of the activity deflation passes into the null, so phi* and the surviving marginal differ materially. If the run does not land, append "(max form; not re-run additive)" to the row's status cell — zero new literals.
wave: 3
source_rows: C-R3-07 + C-R3-08

### C-78 — RUN: re-run the episode gradient within narrow age bands
raisers: DA:A2
severity: MAJOR (inferred)
class: RUN
verified: true — `.tex:315` prints the raw +4.20 (CI [+3.59,+4.66], p = 0.005), the composition-standardized +3.44 and the exact decomposition (+0.77 to composition, +3.43 within common cells), against the implied +0.94. Crucially the standardization holds vintage x FICO x LTV and **not** age, and the same sentence lists "residual seasoning past the age cut" among the confounds left open — so coupon/age collinearity in a closed 2017–2021 book is untested in the dimension that matters.
location: §V.D `.tex:315`; run index `.tex:841`
condition: The paper's only realized-data lock-in exhibit must be shown not to be a seasoning artifact: the gradient must be re-run with loan age in the standardization cells as 12-month strata.
fix: Re-execute `hazard/episode_confrontation_within.py` (already doing exact within-cell decomposition on the cohort-month panel, which carries `mean_loan_age`) with age added to the cells. No new data. Spec the landing rule before running: the gradient may collapse, and that result lands.
wave: 3
source_rows: C-DA-22

### C-79 — RUN: score a Danish leg with an interest-only share
raisers: DA:A5 (second limb)
severity: MAJOR (inferred)
class: RUN
verified: true — the concession is verbatim at `.tex:590` ("in particular the large interest-only share, which would cut scheduled amortization, the null's largest component, and so move the shortfall in the opposite direction from the payoff rule. Each omission is a held-fixed feature of the U.S. leg, not a measured invariance"), and no interest-only run exists in `hazard/data/` (the danish_* family covers us_intercept, refi_finegrid, offwindow_floor, discount_bound, external_validation and curtailment scaling).
location: §VI.D `.tex:590`
condition: If the Danish claim is institutional, the transplant must change something the marginal does not already encode; the interest-only share is the obvious candidate and is not run.
fix: Score a Danish leg with an IO share applied to scheduled amortization on both legs, spec-before-run with the direction signed ex ante (opposite to the payoff rule) and a landing rule fixed in advance. Touches the amortization path, not the hazard, so it does not need C-08's baseline machinery — but it needs a defensible IO-share input, which is an imported institutional parameter with **no committed source in this repo**; if none can be sourced, record infeasible and let the existing concession stand.
wave: 3
source_rows: C-DA-26

### C-80 — RUN: read the 2018 depth ladder's shape, not only its level
raisers: R3:M6(b), SY:Z15
severity: MAJOR **opportunity** (R3 flags it as one of two items that would strengthen the paper; SY: the paper's only own-data evidence on the form fork besides C-73)
class: RUN
verified: true — every ladder value reproduces from `matched_depth_reconciliation_results.json` `step2_matched_depth_grid.OFF_2018_rising_rate`: gap<=0 -> 5.334% / $1,264.5bn / 155 cohort-months; <=-0.25 -> 4.991 / 1,058.1 / 137; <=-0.50 -> 4.695 / 921.4 / 125; <=-0.75 -> 4.722 / 453.5 / 107; <=-1.00 -> 4.869 / 143.4 / 95, `exposure_share_of_gap0 = 0.113374` at the deepest cut. Exposure-weighted differencing gives 7.09 / 6.99 / 4.67 / 4.65 / 4.87 — a step then plateau, independently re-derived. All four deeper cells are `off_window_well_supported: true`. The .tex already prints the five *nested* reads (`.tex:709`, `.tex:713`); absent are the binning, the exposure shares, the standard errors and the shape reading.
location: §VII.F `.tex:709`, `.tex:713`; T6 `.tex:362`
condition: The ladder's shape is out-of-window, out-of-episode, own-data evidence on the form fork — a floor on total turnover produces a step-then-plateau; an additive competing-risks form predicts the floor keeps falling with depth because the elasticity is never censored. It must be read, with the affirmative argument stated.
fix: Re-bin the committed nested reads by exposure-weighted differencing and add a short exhibit with per-bin CPR, exposure share and stratum-cluster standard errors. Standard errors are the only new computation (the CPR bins are arithmetic on committed fields), so this needs a spec header and a parity gate reproducing the five nested reads. Four hedges must be in the note: 2018 gaps are shallow against the window's -380bp; the <=-1pt bin carries only 11.3% of gap<=0 exposure; deeper cuts shift vintage and coupon composition; the shallow bins plausibly carry refinancing, the same confound §V.E names for `episode_confrontation`.
wave: 3
source_rows: C-R3-21 + C-SY-27

### C-81 — RUN (re-tabulation): build the state-contingent cap's two-input table
raisers: R3:M4(b)
severity: MAJOR
class: RUN
verified: true — `.tex:574` states the indexing idea ("indexed … to the share of the book sitting deeply below market coupon") and stops; every input exists: `composition_shift_results.json` (SOMA CUSIP coupon-by-vintage tabulation, anchor-gated to book WAC 2.49% and the vintage shares), the T12 amortization calculator (`.tex:555`, run `wal_normal_turnover`), and the floor band with its wild-cluster interval 4.177–5.800% quoted in the same paragraph.
location: §VI.B `.tex:574`
condition: The proposed state-contingent cap supplies no function from the observable to a cap level; a two-input grid — book out-of-the-money share at 200/300/400bp cuts x turnover-floor band — mapping to achievable monthly principal and hence to an implied cap is required.
fix: Build the grid with the existing WAL/amortization calculator: per OTM-share cut take scheduled principal from the book composition and add turnover at each floor-band point, producing achievable $bn/month and the implied cap. No new estimation — a re-tabulation of committed inputs through committed machinery — but it prints new literals, so it needs a spec-before-run header and parity gates against T12's printed rows. Lands with C-54.
wave: 3
source_rows: C-R3-13

### C-82 — Add a household-side row to Table 1
raisers: R3:M1(a)/minor 5, SY:Y1
severity: MAJOR
class: STRUCTURE
verified: true — T1's nine rows are cap benchmark, expectations complement, mechanical null, lock-in marginal (off-window), lock-in marginal (in-sample), Path B level, production ABM, cross-design ABM, Danish counterfactual. No household row, no duration row.
location: T1 `tab:headline` `.tex:64–90`
condition: The exhibit that "collects the core results" must not omit one of the two legs §VIII's conclusion compares.
fix: Add "Foregone payoffs implied by the marginal" carrying C-76's count with its floor band and moving-share bracket, labelled as an implied count, not a measured one, and priced against `batzer2024`'s $2.4trn and `hsieh2019`'s mechanism as bounds. **Add only once C-76 lands — do not add an unquantified placeholder.**
wave: 4
source_rows: C-R3-03 + C-SY-10

### C-83 — Add a duration row to Table 1
raisers: R3 minor 5
severity: MAJOR
class: STRUCTURE
verified: true — T1 contains no WAL/duration row; the 9.4-year empirical WAL, the 3.4-year comparator, the 6.0-year extension and the 0.6-year rule-only shortening are all committed elsewhere (T12, App. L `.tex:1328`).
location: T1 `.tex:64–90`; sources T12 `.tex:553–575`, App. L `.tex:1328`
condition: Table 1 must carry the duration extension, the other object §VIII's conclusion compares.
fix: One row quoting the 9.4-year empirical WAL against the 3.4-year 2021-speed comparator (6.0-year extension) with the 0.6-year rule-only shortening as the marginal's share — all repeating committed figures, per T1's own convention.
wave: 4
source_rows: C-R3-31

### C-84 — Give the 5.51% age-standardized and 5.52% Fannie reads their own labelled rows in tab:oosfloor
raisers: DA:C1(c)
severity: CRITICAL (DA:C1c) -> MAJOR (§2.2 narrowed: "confining them to a note" is imprecise — they are already rows in T5 and printed in T8's note and the Definitions block)
class: STRUCTURE
verified: partly — T6's rows are 4.70/4.99/5.33 (defensible), 6.07/6.91 (refi-contaminated), 4.00/3.97 (in-sample), with no 5.51/5.52 row; but they already appear at `.tex:347–348`, `.tex:92` and `.tex:433`. Implementation constraint: T6 has three delta columns (5.5/6.5/7.7) and only one committed marginal exists for each new read (~+3.8 for 5.51%; "below +4.3" for 5.52%), so full rows cannot be printed without inventing cells. Substantive caveat: the Fannie 5.522% is the **pooled 2017–2019** cell whose Freddie parity is 5.185% — it is not a second age correction, so DA's "two independent corrections agree to 0.01pp" is a coincidence across two different perturbations.
location: T6 `tab:oosfloor` `.tex:360–381`
condition: The two reads that sit above the clean band's top must be visible in the table that sets the band, labelled so they cannot be read as more than they are.
fix: Add them as clearly-labelled rows with dashes in the uncommitted delta cells and a distinguishing Status ("indicative bound, 84% imputed weight" / "independent agency, pooled leg"), or as a stub block beneath the defensible rows. The Fannie row **must** state its leg and its 5.185% Freddie parity, otherwise the table asserts an age correction the artifact does not support.
wave: 4
source_rows: C-DA-04

### C-85 — Add the missing references
raisers: R2 (ten named entries), SY:Z19/R16
severity: MAJOR (R2: "references a domain referee would require"); Minor-Major (SY)
class: REFERENCE
verified: partly — `references.bib` holds exactly 70 entries. Genuinely absent and verified absent: **Deng–Quigley–Van Order (2000)** (only sole-authored `quigley1987`/`quigley2002` present); **Hanson (2014) "Mortgage convexity"** (0 hits for Hanson, 0 for convexity); **Frankel–Gyntelberg–Kjeldsen–Persson (2004)** (0 hits; `berg2018` is the only institutional Denmark cite) — **blocks C-51**; **Svenstrup–Willemann (2006)**; **López-Salido–Vissing-Jørgensen (2023)** and/or **Acharya–Chauhan–Rajan–Steffen (2024)** (R2 offers the pair as and/or); **Aiello (2022)** (the servicer channel, named unmodeled and unbounded at three sites); **Fuster–Lucca–Vickery** as a standalone survey entry; **Diep–Eisfeldt–Richardson (2021)** (R2 marks it optional). **Per A-16, "none of these is cited" is wrong for one item:** `fonseca2024` (Fonseca & Liu) is already in the bib and cited at `.tex:227` — only the **Fonseca–Liu–Mabille** spatial-housing-ladder extension would be new, and it must be checked as distinct before adding a duplicate.
location: `paper/v18/references.bib`; citing sites §V.B (competing risks), §VI.A/§VIII (convexity, hedging), §VI.D (Danish institution), §III.B (reserves/QT), §VIII.A (servicer), §I/§VIII (TBA survey)
condition: The named references must be added and cited at the argument each one bears on, so single-authored institutional and methodological claims stop resting on the author's own reading.
fix: Add the entries and place one citation each; verify the Fonseca–Liu–Mabille identity first. Required for submission.
wave: 5
source_rows: C-R2-33 + C-R2-34 + C-R2-35 + C-R2-36 + C-R2-37 + C-R2-38 + C-R2-39 + C-R2-40 + C-R2-41 + C-R2-42 + C-SY-31 + C-SY-48 (C-SY-48 cross-listed at C-129)

### C-86 — Give §VI.C's assumability claims a cited basis
raisers: R2 minor 4, R3 minor 4
severity: MAJOR (R2 inferred) / MINOR (R3)
class: REFERENCE
verified: partly/true — `.tex:580` carries "U.S. policymakers, including the Federal Housing Finance Agency (FHFA), proposed expanding assumable and portable mortgages" and "Fixed-income analysis suggests" with **no `\cite` of any kind**, and the span contains zero digits; none of FHFA, HUD or a VA circular is in the bib. (R2's supporting count is slightly off: "assumab*" occurs three times, not twice. R3's "the one un-numbered section" is true only under "carries no quantities" — §VI.C *is* numbered.)
location: §VI.C `.tex:578–580`
condition: The FHFA proposal, the assumption mechanics and the second-lien gap, and the "fixed-income analysis" hedge must carry sources.
fix: Cite the actual FHFA proposal document, HUD Handbook 4000.1 (FHA assumption mechanics and qualification) and the relevant VA circular (entitlement restoration, release of liability), plus an assumption-volume basis for the hedge (Ginnie Mae issuance/assumption reporting or an FHFA take-up analysis). The specific sources are not named by the panel, so they must be selected and verified before citing. Pairs with C-59 and C-116.
wave: 5
source_rows: C-R2-26 + C-R3-29

### C-87 — Split the oversized paragraphs at their own topic boundaries
raisers: EIC:W10, R1 (writing basis), R2 (writing basis), R3 (writing basis), DA:M8, SY:X2/R11 — all five reviewers  [CONSENSUS]
severity: MAJOR (SY: "the single largest scoring deficit"; EIC: "a scoring fact, not a courtesy deduction")
class: STRUCTURE
verified: partly — the four headline magnitudes reproduce **exactly** on blank-line-delimited blocks in three independent inventories: 14,732 (`.tex:219–231`, §V.B), 11,312 (`.tex:319–323`, §V.E), 10,696 (`.tex:1099–1100`), 8,051 (`.tex:269`, §V.B). Corrections carried forward: (i) the 10,696 block is in **App. F** (`app:patha-detail`), not App. G (A-14); (ii) "the four >6,000-char paragraphs" undercounts — **11** prose blocks exceed 6,000 chars (`.tex` 219, 319, 1099, 269, 277, 713, 709, 150, 590, 333, 315) plus two oversized table blocks (1397, 813); (iii) the word-count claims are inflated — the longest single body paragraph is 1,606 words (`.tex:323`), and no 2,200-word paragraph exists (A-20); (iv) the 14,732-char block spans 13 source lines including three display equations, so its longest uninterrupted prose run is 7,348 chars.
location: all 11 oversized prose blocks; highest-value targets `.tex:219–231`, `.tex:319–323`, `.tex:269`, `.tex:709`, `.tex:731`, `.tex:590`, `.tex:1099–1100`
condition: The qualification load must be carried by structure: oversized blocks split at their own topic seams (each already runs "First… Second… Third…"), with §V.B split at its five seams (specification / floor semantics / elasticity import and its three transports / aggregation bounds / ablations) and the competing-risks taxonomy moved to App. E.
fix: Insert `\paragraph{...}` heads at the seams; **text-preserving only.** Every gate-pinned span must survive byte-identically (`ASSEMBLY_SPANS`, `ABSTRACT_POSTURE`, the ladder spans, the ABM_LEAD spans are whole-sentence pins), and **gate #71 binds a paragraph-level co-occurrence** (`tools/liveness_gates.py:4061`) — splitting the paragraph that first states +$61.2bn breaks it unless the forcedness and -$99.9bn clauses move with it. Re-run `tools/render_gate.py` afterwards: re-flowed floats caused the R31 off-sheet defect. Splitting `.tex:731` also serves C-23; splitting `.tex:590` also serves C-50.
wave: 6
source_rows: C-EIC-14 + C-R1-36 + C-R2-43 + C-R3-35 + C-DA-16 + C-SY-02 + C-SY-43

### C-88 — Bring §IV + §VII.A/§VII.C/§VII.D down to ~2pp
raisers: EIC (cut 1)
severity: MAJOR
class: STRUCTURE
verified: partly — three of four supporting facts are exact: the sign-disagreeing null readings +270.4 / -105.3 at `.tex:178`, "all fifty seeds classify as undercutting" verbatim at `.tex:645`, and zero "agent-based" in the abstract. The "~13% of the main text" figure is high: the four subsections are 10 of 94 main pages (10.6%) and 4,363 of 45,192 tokens (9.7%); §IV alone is 4 pages / 3.7%. §VII.A is genuinely ABM material (`.tex:631`), so the bundling is right even though the percentage is not.
location: §IV `.tex:154–179`; §VII.A `.tex:629–632`; §VII.C `.tex:637–686`; §VII.D `.tex:687–690`
condition: The main text keeps the ABM's negative verdict, the +270.4/-105.3 no-null finding and the fifty-seed undercutting verdict; the construction and diagnostic prose moves to the ABM appendices.
fix: Relocate `.tex:631`, `.tex:637–644`, `.tex:646–686`, `.tex:687–690` to `sec:method-abm` (`.tex:880`) and `app:abmspec` (`.tex:931`). **Relocation only** — `tab:crossdesign` literals are gate-pinned, and `tools/liveness_gates.py` matches on the whole `.tex` as one string, so a move is gate-safe while a deletion is not.
wave: 6
source_rows: C-EIC-17

### C-89 — Bring §V.B down to ~2,500 words
raisers: EIC (cut 2)
severity: MAJOR
class: STRUCTURE
verified: true — all four premises check: §V.B is the longest subsection (7,294 tokens, pp.26–38); the kappa-grid/floor-dispersion prose is exactly `.tex:263/265/267` (5,978 chars combined); App. N already carries "a Jensen effect operating through the floor's combination rule" at `.tex:1350`; App. I is the composition appendix (`.tex:1265`). "Ginnie" occurs 24 times in the range.
location: §V.B `.tex:217–306`; destinations App. N `.tex:1342/1350`, App. I `.tex:1265`
condition: The kappa-grid / floor-dispersion material moves to App. N beside its Jensen diagnosis, and the Ginnie/vintage overlay construction to App. I, leaving one-sentence pointers.
fix: Pure relocation into existing destinations; verify afterwards that §V.B's remaining cross-references still resolve in the direction the prose asserts.
wave: 6
source_rows: C-EIC-18

### C-90 — Bring §V.E down to ~2,500 words
raisers: EIC (cut 3)
severity: MAJOR
class: STRUCTURE
verified: true — §V.E is the second-longest subsection (6,193 tokens, pp.41–52); the group-ablation decomposition is at `.tex:323/325` with its figure caption at `.tex:413`; the composition qualification is the 3,979-char paragraph at `.tex:325`; `tab:assembly` is Table 5 as described.
location: §V.E `.tex:317–468`; keep `tab:assembly` `.tex:338` and the seven qualifications; move `.tex:325`, the group-ablation prose and `fig:marginalcells` `.tex:410–415`
condition: The seven qualifications and Table 5 stay; the group-ablation placebo and the composition decomposition move to an appendix.
fix: Relocate to `app:composition` (`.tex:1265`) or `app:floormech` (`.tex:1301`), leaving the qualification's verdict sentence in place so the "seven qualifications" count and Table 27's cross-references stay true. The fourth qualification is a disclosure — it may be moved, never deleted. Interacts with C-96 (the distributional promotion lives in `.tex:325`).
wave: 6
source_rows: C-EIC-19

### C-91 — Bring §VI.D down to ~3pp
raisers: EIC (cut 4)
severity: MAJOR
class: STRUCTURE
verified: true — the subsection runs six pages (`.tex:582–622`, 2,735 tokens, pp.63–68) and contains the 6,583-char anchor/incidence sweep prose at `.tex:590` that the cut targets.
location: §VI.D `.tex:582–622`
condition: The sweep mechanics and the redemption-validation confounds move to an appendix; the +$61.2bn / -$99.9bn / cash-haircut bracket and the forced-sign disclosure stay in the main text (all are quoted in §VIII at `.tex:727/731`).
fix: Relocate `.tex:590` and neighbours (`SPEC_danish_redemption_validation_2026-07-28.md` documents the validation design; `tab:danish` is Table 13). Sequence **after** C-46/C-47/C-50 land so their new sentences are not relocated mid-edit.
wave: 6
source_rows: C-EIC-20

### C-92 — RUN or flag: the floor's flatness in loan age
raisers: R2 minor 6
severity: MINOR
class: RUN (with a wording minimum)
verified: true — `.tex:1312` prints the age ladder (3.68% below twelve months, 5.78% at 12–24, 10.99% at 24–36) and uses its monotone **rise** as evidence the floor is not purely involuntary turnover; the floor still enters as a single constant SMM. The paper already sweeps a rate-varying floor (`tab:floorband`) and a calendar-varying one (`tab:seasonalfloor`) — age is the missing third dimension.
location: floor definition eq (1) region, §V.B; App. J `.tex:1312`; `tab:floorband` `.tex:289`; `tab:seasonalfloor` `.tex:1369`
condition: The floor's flatness in age must be swept, or at minimum flagged as an assumption contradicted by the very ladder used to calibrate it.
fix: Sweep an age-varying floor built from the App. J ladder through the existing `floor_form_*` / `floor_sweep` machinery; new artifact (e.g. `floor_form_age_results.json`). **Spec it so it cannot repeat the `floor_cyclical` mislabel** (that run measured floor *dispersion* under FLOOR_MODE='max', not cyclicality): state ex ante what varies and what the scramble/permutation null is. Minimum acceptable substitute is the one-sentence flag. Interacts with C-08.
wave: 3
source_rows: C-R2-28

### C-93 — Move Table 8's oversized calibration cell into its tablenote
raisers: EIC (presentation evidence)
severity: MINOR
class: STRUCTURE
verified: partly — the headline row `.tex:433` is 2,089 chars and its fourth cell (Calibration range) is 1,411 chars; but no other cell exceeds 601 chars, so "cells" plural overstates — exactly one cell is over 900.
location: T8 `tab:uncertainty` `.tex:420–437`, offending row `.tex:433`; destination tablenote `.tex:440`
condition: The 1,411-char calibration cell must not carry a prose catalogue.
fix: Move the catalogue into the existing tablenote block at `.tex:440` (already the table's prose annex), leaving a pointer in the cell — the pattern `tab:ladder` uses at `.tex:467` and `tab:headline` at `.tex:90`. Text-preserving, gate-safe.
wave: 4
source_rows: C-EIC-16

### C-94 — Give tab:wal a note-rate-basis row for the empirical path
raisers: R2 minor 2
severity: MINOR
class: STRUCTURE
verified: true — `.tex:485` already prints all three bases ("mean CPR 5.14\% (ABM-basis back-out; hazard-basis 5.52\%, 5.79\% at the note-rate WAC)"), while `.tex:559` uses 5.14% alone as the WAL scenario, so the corrected basis never becomes the comparator. R2's single-pool 7.72->7.25-year recomputation is not reproducible from committed artifacts and is not comparable to the table's blended 9.4 — the structural point is what is verified.
location: T12 `tab:wal` empirical row `.tex:559`; T10 `tab:estimators` `.tex:485`
condition: The empirical-CPR comparator must be available at the physically correct note-rate convention, with each row's basis named.
fix: Add a note-rate-basis row (or second column) computed through the same `wal_table` calculator, and say in the tablenote which basis each row uses. Stake: the revision is of the same order as the Danish rule-only WAL effect the paper reports (0.6 years).
wave: 4
source_rows: C-R2-23

### C-95 — Make tab:pathadiag single-spec
raisers: R1 minor
severity: MINOR
class: STRUCTURE
verified: true — the adjacency is exactly as described ("Aggregate recovery (spec v4) \$928.9bn" directly above "point \$915.1bn (spec v3)") and the tablenote at `.tex:1122` already discloses the mixing.
location: `tab:pathadiag` `.tex:1107–1123` (rows `.tex:1114–1117`, note `.tex:1122`)
condition: A single-spec table with the other spec in a footnote removes the trap.
fix: Demote the spec-v3 rows to a tablenote or split into two tables. Appendix-only, no committed literal changes; check `tests/test_verdict_audit_gate.py` and the render gate for pinned row text.
wave: 4
source_rows: C-R1-32

### C-96 — Promote the distributional-incidence result out of the homogeneity check
raisers: R3 (cross-disciplinary opportunity 2 — "arguably the most publishable result in the paper" for that audience)
severity: MINOR
class: STRUCTURE
verified: true — `.tex:325` carries all three figures verbatim: tilts toward below-740-FICO (1.23x–1.26x) and above-80-LTV (1.23x), regional intensities spanning only 0.93–1.06, against a placebo whose widest of twelve partitions spans 0.011 while the economic groupings span 0.381 (run `subgroup_marginals_placebo`).
location: §V.E `.tex:325`
condition: A distributional finding about who bears the mobility cost, established against a proper placebo, must not be buried inside a check presented as evidence that a verdict label carries no information.
fix: Promote to a named paragraph or short exhibit with a distributional-incidence framing, carrying the placebo caveat and the "structure, not sampling noise" reading already in the text. Zero new numbers. Sequence with C-90, which relocates the containing paragraph.
wave: 4
source_rows: C-R3-36

### C-97 — Give the transportable methodological lesson its own named paragraph
raisers: R3 (cross-disciplinary opportunity 4)
severity: MINOR
class: STRUCTURE
verified: true — the curve and the lesson are both in §VII.F running prose (+7.5 at s=0.1, +9.7 at 0.25, +10.7 at 0.4, flat near +11.2 from s=0.6, central recovery falling along the way), and `floor_form_mixture_results.json` confirms the endpoints run through production code paths (42.608 max vs 85.705 additive at the 4.991% floor — very nearly a doubling).
location: §VII.F `.tex:709`
condition: "A calibrated floor's functional form can double a policy-relevant marginal" deserves a named paragraph with the mixture curve named as the portable device, not a robustness aside.
fix: One named paragraph in §VII.F or the limitations. Text-only; the numbers are committed.
wave: 4
source_rows: C-R3-37

### C-98 — Flag berger2026's working-paper status where its estimates are imported
raisers: EIC:W8
severity: MINOR
class: REFERENCE
verified: partly — the bib entry is exactly as reported (`@misc{berger2026 … howpublished = {Working paper, {SSRN} abstract 6150766}`) and the manuscript already flags it once at §II `.tex:112` ("in a January 2026 SSRN working draft"); the flag is missing at `.tex:586`, where the estimates are imported and the source's own counterfactual is overruled.
location: `references.bib:61–67`; §VI.D `.tex:586`
condition: The Danish channel's single unrefereed source must carry its status where the load is carried, not 60pp earlier.
fix: Add the status clause at `.tex:586` reusing the §II wording. Land with C-68.
wave: 5
source_rows: C-EIC-10

### C-99 — Print the measured +3.7 at the age-standardized floor with the grid-read beside it
raisers: R1 minor (flagged in R1's reproducibility verdict as one of two printed numbers to change)
severity: MINOR
class: WORDING
verified: true — `b5_joint_cell_results.json` `conventional_agestd`: `marginal_pp = 3.67132`, `ladder_implied_pp = 3.8`, `measured_minus_implied_pp = -0.12868`, `agestd_floor_pct = 5.50775`. The substitution's direction is favourable to the headline.
location: `.tex:333`, `.tex:433`, `.tex:713`; gate pin `ASSEMBLY_SPANS["ladder_agestd"] = "floor read of 5.51\\% implies a marginal near $+3.8$"` (`tools/liveness_gates.py:385`)
condition: Where a measured value exists it must be quoted, with the grid-read beside it.
fix: Print +3.7 measured (3.8 grid-read, -0.13 wedge) at the three sites; move the gate span and re-run the census of the literal before committing (the gate asserts presence and ladder ordering).
wave: 5
source_rows: C-R1-24

### C-100 — Name the percentile rung's grid-exclusion convention and its 26/1,000 count
raisers: R1 minor
severity: MINOR
class: WORDING
verified: true — `layer_convolution_results.json` `layers.floor_percentile`: `n_draws_outside_grid_excluded = 26`, `n_truncated_above_grid_hi = 26`, `n_truncated_below_grid_lo = 0`, `ci95_pp_edge_truncation = [2.28091, 8.01470]` against `ci95_pp_exclusion = [2.97433, 8.01851]`, with an explicit `disclosure` field stating all 26 sit on the low-marginal side; `2.281` appears nowhere in the manuscript. The same count is in `floor_inference_correction_v2_results.json` `P2_percentile_bitexact_R2.n_draws_outside_grid = 26`.
location: Notes to T9 `.tex:467–468`; percentile row `.tex:456`
condition: The demoted rung's printed lower edge depends on an unlabelled convention that differs from its alternative at exactly the endpoint the paper cares about; the convention, the count and their one-sided position belong in one clause.
fix: One clause naming the exclusion convention, 26/1,000, the one-sided position and the [+2.281,+8.015] alternative. Committed literals. The same clause should carry the CR3-BM / WCR lower-edge truncation flags if C-20 promotes either rung.
wave: 5
source_rows: C-R1-25

### C-101 — Name the denominator of the width ratio
raisers: R1 minor
severity: MINOR
class: WORDING
verified: true — the loan-layer width is 2.2935pp; 2.2935/5.8230 = 0.394 against the Webb width, while `bootstrap_pathb_cluster_results.json` `comparison.width_ratio_vs_floor_read = 0.45469` is computed against the *percentile* width 5.0442. Both are internally correct; the manuscript prints only 0.39 and names no denominator.
location: T8 headline row `.tex:433`
condition: Two width ratios circulate for one comparison; the denominator must be named.
fix: One clause in T8's note (0.39x the Webb corrected read; 0.455x the demoted percentile read). Committed literals.
wave: 5
source_rows: C-R1-26

### C-102 — Print beta_1(P_q) at {0.015, 0.03, 0.06, 0.12} in tab:params
raisers: R1 minor
severity: MINOR
class: WORDING
verified: true — the near-insensitivity claim is asserted in the main text with the derivation deferred (`.tex:231`), App. E gives only the endpoints of the range ("the central beta_1 ranges only from 0.0672 to 0.0701"), `tab:params` carries no P_q row, and the 1.5% comparison against the quarterly 0.06 slot is stated twice (`.tex:229` footnote, `.tex:231`).
location: `.tex:231`; App. E `.tex:1087`; T3 `tab:params` `.tex:239`
condition: The single imported parameter's conversion is evaluated four times above the source's own zero-gap moving level; the per-P_q values must be printed.
fix: Four-cell arithmetic evaluation of `eq:beta1` at delta = 0.065 (analytic, no engine, no artifact); add one row or one tablenote line. Check `tests/test_elasticity_discipline_gate.py` and `tests/test_units_conventions.py` for pinned beta_1 literals (0.0686/0.068571/0.069/0.0693) first. Do together with C-25.
wave: 5
source_rows: C-R1-28

### C-103 — Concede that the cluster bootstrap is a ratio estimator with random denominators
raisers: R1 minor
severity: MINOR
class: WORDING
verified: true — `bootstrap_pathb_cluster_results.json` `n_loans` = {p2.5: 54,134, median: 75,613, p97.5: 101,404, sd: 11,343}; the renormalization defence is on the page at `.tex:277` exactly as reported, and no statement about ratio bias or bias correction appears. `cluster_structure`: 130 clusters, 25.777 effective, largest 9.77%.
location: `.tex:277`
condition: Composition weights are a ratio of random totals and the percentile interval is uncorrected; one sentence must say so.
fix: One sentence at `.tex:277`. A fixed-n (rescaled-weight) variant would be a RUN (`hazard/bootstrap_pathb_cluster.py`, 200 replicates, new artifact) and is optional — R1 accepts the sentence.
wave: 5
source_rows: C-R1-29

### C-104 — Drop the zero-exclusion clause from the "three things" list
raisers: R1 minor
severity: MINOR
class: WORDING
verified: true — `.tex:333` reads "Three things stop the list from becoming a retraction. The interval does not contain zero, and the sign is fixed by the window's rate configuration…"; the sign-forcing establishment (99.53% of exposure at or below 5.09% against a window-minimum 5.2311%) is at `.tex:323`. Mitigation: the sentence already conjoins the sign-forcing point, so zero-exclusion is not treated as independent evidence — but it is listed first.
location: `.tex:333`
condition: If the sign is forced, zero-exclusion carries no information and should not head that list.
fix: Drop the clause and let the sign-forcing sentence carry the point (three items become two, or a different third is named). Check `ASSEMBLY_SPANS` / `tests/test_assembled_corrections_gate.py` first — `posture_lower_half` and `posture_retired_range_carries` sit on the same line.
wave: 5
source_rows: C-R1-30

### C-105 — Print the unrounded CR1-BM and CR3-conventional pairs in the ladder note
raisers: R1 minor
severity: MINOR
class: WORDING
verified: true — `cr1_t_interval_df_bm.marginal_ci95_pp = [2.75308, 8.79621]` (df 6.246) and `cr3_t_interval.marginal_ci95_pp = [2.77322, 8.77441]` (df 30); both print as +2.8/+8.8. The note's characterization ("an accident of this leverage profile, not an identity") is correct.
location: T9 rows `.tex:459`, `.tex:462`; note `.tex:467`
condition: Two distinct objects coinciding at one decimal must be distinguishable.
fix: Add the unrounded pairs to the note — **not** to the printed rows, which are gate-pinned (`cr1_conventional`, `cr1_bell_mccaffrey`, `df_ownership` spans near `tools/liveness_gates.py:4577`, `tests/test_floor_ladder_gate.py`).
wave: 5
source_rows: C-R1-31

### C-106 — Make the spec-before-run ordering checkable from the paper, or say it is git-only
raisers: R1 (reproducibility limit (i))
severity: MINOR
class: META
verified: true — `specs/` holds 15 files (R1's 14 plus one added since); `tab:runindex` carries 58 `\texttt{}` run tags against R1's "~60 named runs"; the only commit hashes in the manuscript are the floor-sweep pair at `.tex:782`.
location: App. A `.tex:780–782`; `tab:runindex` `.tex:816–878`
condition: For runs without a `specs/` file the pre-run status rests on script-header commit ordering, verifiable only from git history; the paper must either extend the ledger for the runs carrying headline numbers or say plainly that the ordering is git-verifiable only.
fix: Wording. No run.
wave: 5
source_rows: C-R1-33

### C-107 — Optional: own the consequence that the ABM headline is not commit-addressable
raisers: R1 (reproducibility limit (ii)) — **no change requested**
severity: MINOR
class: META
verified: true — `.tex:780` discloses that two freezes ran on uncommitted trees and that specifications must be identified by cohort-bucket count (seven vs eleven) rather than by manifest commit; `.tex:782` discloses that a manifest's `git_commit` is the pre-run parent of the freezing commit.
location: App. A `.tex:780`, `.tex:782`
condition: R1 asks that the disclosure **stay**; the only optional addition is one clause naming its consequence (the ABM headline is not commit-addressable).
fix: No change required. If taken, one clause. Recorded so the disclosure is not "tidied" away by any compression pass (C-88).
wave: 5
source_rows: C-R1-34

### C-108 — Repair the §III.B coupon-convention sentence
raisers: R2 minor 1 (R2's Writing-Quality basis calls it "unparseable as written")
severity: MINOR
class: WORDING
verified: true — `.tex:146` reads "both amortize on the pass-through convention where scheduled principal physically follows the borrowers' note rates (the pass-through WAC plus the guarantee-fee and servicing wedge, $+0.80$ points)"; pass-through WAC + 0.80 *is* the note rate, so the clause contradicts itself.
location: `.tex:146`
condition: The sentence must stop naming both conventions at once.
fix: R2's replacement: "both amortize at the pass-through WAC; scheduled principal physically follows the note rate, which is the pass-through WAC plus a +0.80-point g-fee and base-servicing wedge, and recomputing on that basis raises the CPR level by +0.27 points." Gate-safe: gate #106's pinned spans live at `.tex:697`, not `.tex:146`, and "0.27" is unpinned. Keep the run tag `\texttt{coupon\_convention\_amortization}` in the sentence (the gate requires >=2 document-wide occurrences).
wave: 5
source_rows: C-R2-22

### C-109 — Label the comparator basis at every simulated-vs-empirical CPR comparison
raisers: R2 minor 2 (second clause)
severity: MINOR
class: WORDING
verified: true — 5.14% appears at eight sites (`.tex:160, 315, 485, 524, 559, 571, 590, 1102`); only `.tex:485` discloses that it is the ABM-basis back-out with hazard-basis 5.52% / note-rate 5.79% alternatives. Two of the eight are inside `tab:wal`, and "5.14" appears twice in `tools/liveness_gates.py`, so the literal is pinned where it is protected.
location: §IV, §V, §VII.C — the eight 5.14% sites
condition: Every comparison must say which comparator basis it uses.
fix: A one-clause basis label at each site, or one "Definitions used throughout" entry fixing the convention once with a pointer at each site. Separate edit from C-94 (a prose sweep across three sections, not a table change).
wave: 5
source_rows: C-R2-24

### C-110 — State how burnout is initialized
raisers: R2 minor 3
severity: MINOR
class: WORDING
verified: true, **and the code settles the question R2 could only infer** — `hazard/agents.py:149` initialises `self.cohort_burnout = np.zeros(self.n_strata)`, so B = 0 for every stratum at window open and accumulates only within-window prepayment (`hazard/competing_risks.py:65–80`), while the denominator `stratum_orig_upb` sums `orig_upb` over **all** 75,000 rows including the 34,734 that prepaid pre-window. So pre-window attrition is excluded from the numerator and included in the denominator: B is window-cumulative, which the text does not say. R2's B~0.46 / 0.79-multiplier arithmetic correctly describes the alternative the code does not implement.
location: §V.B `.tex:227`, `.tex:269`; App. E `.tex:1085`
condition: Burnout's initialization and its window-open distribution must be stated.
fix: One clause at `.tex:227`: B is initialised at zero at the window open and accumulates only within-window prepaid UPB against the stratum's full original UPB including pre-window-terminated loans — window-cumulative, not life-cumulative. Optionally note the window-open distribution is degenerate at zero by construction. Note the interaction with the `attenuation_sensitivity` survival-selection transport (`a = S^theta` at S = 40,234/75,000).
wave: 5
source_rows: C-R2-25

### C-111 — Take the default baseline's free external corroboration
raisers: R2 minor 5
severity: MINOR
class: WORDING
verified: true — both sites confirmed (`.tex:227` prior "$3\times10^{-4}$ monthly"; T3 provenance cell "calibration prior"); 3e-4 x 12 = 0.36%/yr against a realized Freddie CDR window mean of **0.314%** recomputed from `gmar_dec25_cpr_series.json` over the 42 months. It is one of the few priors with an external check and it passes.
location: `.tex:227`; T3 `.tex:252`
condition: The implied 0.36%/yr CDR should be shown corroborated by the paper's own GMAR extraction.
fix: One clause at `.tex:227` and/or the T3 provenance cell, citing an already-committed artifact.
wave: 5
source_rows: C-R2-27

### C-112 — Derive the "$83 billion per CPR point" coefficient at first use
raisers: R2 minor 7
severity: MINOR
class: WORDING
verified: true — both uses are at `.tex:269` (the Ginnie composition bound $20–47B and the vintage bound $11.7B) and neither derives the coefficient; the only other "per CPR point" is `.tex:590`'s Danish $65bn/CPR-point slope, a different object. R2's check reproduces: ~$2.4T average book x 3.5 years x 1% ~ $84bn.
location: §V.B `.tex:269`
condition: The conversion coefficient must be derived once where it is first used, so both bounds inherit a stated basis.
fix: One parenthetical giving average book face x window length x one CPR point.
wave: 5
source_rows: C-R2-29

### C-113 — Quote the six extension-years against the normal-turnover row as well
raisers: R2 minor 8
severity: MINOR
class: WORDING
verified: true — the six years is 9.4 - 3.4 (empirical vs the 22.81% refi-boom row); the tablenote at `.tex:571` already flags 22.81% as "a refinancing-boom baseline rather than a normal-turnover one" and names the turnover-floor row "the normal-turnover counterpart", against which the extension is 9.4 vs 9.5 — essentially zero.
location: §VI.A `.tex:540`; T12 rows `.tex:559`, `.tex:565`, `.tex:566`
condition: The reader must be able to see that the extension is refinancing-versus-turnover rather than lock-in-versus-normalcy.
fix: Add the against-the-turnover-floor comparison (9.4 vs 9.5 years at June 2022; 8.5 vs 8.6 at Nov 2025) to `.tex:540`. Committed `tab:wal` figures only. Coordinate with C-55.
wave: 5
source_rows: C-R2-30

### C-114 — Retire the superseded lag interpretation carried in a committed artifact
raisers: R3 minor 1
severity: MINOR
class: CHECK
verified: true — `extension_risk_results.json` `lag_interpretation` reads verbatim "Negative lag = hazard CPR leads SOMA empirical CPR. Consistent with 45-90d TBA settlement delay…", while `.tex:275` states "a peak at $k=-3$ means the simulated path \emph{trails} the empirical path by three months" and `.tex:305` "I therefore attach no settlement interpretation to the timing alignment." The .tex never names the file or the field (0 hits).
location: `hazard/data/extension_risk_results.json` field `lag_interpretation`; §V.B `.tex:275`, `.tex:305`; App. A `app:ledger` `.tex:756`ff
condition: A reader consulting the replication package must not receive a reading the manuscript reverses.
fix: Prefer an App. A bullet naming the file, the field and the superseded reading — editing a frozen artifact's documentation string touches a SHA-pinned replication object; if the string is corrected instead, the manifest pin and any gate hashing that file must be re-checked.
wave: 5
source_rows: C-R3-25

### C-115 — Read the Danish sweep at two named tax-regime points
raisers: R3 minor 2 (second half)
severity: MINOR
class: CHECK
verified: partly — the sweep exists and is committed (`.tex:590`: "swept in 0.25\%-CPR steps under the production anchor, the gap runs from $+\$61.2$ billion at 0\% to $+\$256.8$ billion at 3\%"), but it parameterizes the **refinance-in-place CPR**, not a tax regime; presenting "both tax regimes" requires mapping each regime to a point on that axis, which the paper does not do. The U.S. regime is the marked ~0 anchor; the Danish-tax realization is the 22.4%/yr realized-implied read that `.tex:590` places above the swept range entirely.
location: run `danish_refi_finegrid`; §VI.D `.tex:590`, `.tex:595`; T13 row `.tex:613`
condition: The institutional gap should be presented across both tax regimes rather than only at the U.S.-tax-attenuated anchor, with the axis named.
fix: Read the existing sweep at two named points and print both, stating explicitly that the axis is refi-in-place CPR and the regimes enter only through that input. No new run if a defensible Danish-tax point lies on the 0–3% grid; a new grid point if not. Land with C-68.
wave: 5
source_rows: C-R3-27

### C-116 — Connect §VI.C to the paper's own 20.4% share and take-up concession
raisers: R3 minor 4
severity: MINOR
class: WORDING
verified: partly — the concession exists but in §I, not §VI.C (`.tex:52`: "the 20.4\% share bounds the carve-out from above rather than sizing it"); §VI.C references neither the share nor the concession.
location: §VI.C `.tex:580`; source `.tex:52`
condition: §VI.C must cross-reference the 20.4% statutory-assumability share and restate the take-up concession where the policy proposal is evaluated, so the section reads as a taxonomy rather than a finding.
fix: Two clauses, existing literals. Land with C-59 and C-86.
wave: 5
source_rows: C-R3-30

### C-117 — Prefer "cap shortfall" in headline sentences
raisers: R3 minor 6
severity: MINOR
class: WORDING
verified: true — `.tex:92` defines the term ("``Trapped liquidity'' and ``shortfall'' denote the net shortfall of realized roll-off against the phased redemption caps") and it is used 35 times (32 lowercase + 3 capitalised), including headline and table-note sites, where for readers outside MBS it connotes a resource loss.
location: definition `.tex:92`; 35 occurrences
condition: Headline uses should read "cap shortfall"; "trapped liquidity" should be reserved for the internal accounting object.
fix: Per-site pass leaving accounting-object uses (artifact names, table sign conventions, run labels) intact. Check gate spans first — several quoted spans contain the phrase.
wave: 5
source_rows: C-R3-32

### C-118 — Say that the labor-reallocation leg is unquantified in this design
raisers: R3 minor 7
severity: MINOR
class: REFERENCE
verified: true — `.tex:542` carries "their headline magnitudes are cumulative level effects over 1964--2009 and were revised in a published correction, so I cite the mechanism rather than a point estimate", and no per-move or per-household surplus magnitude appears anywhere ("per household" = 0 hits).
location: §VI.A `.tex:542`
condition: The welfare argument's one remaining quantitative leg is empty; either a per-move surplus estimate that survives scrutiny is cited, or the sentence invoking the leg says it is unquantified here.
fix: The second branch costs nothing and is consistent with the paper's existing declination discipline. R3 names no source, so a citation would have to be selected and verified (the second of R3's two not-in-bib references).
wave: 5
source_rows: C-R3-33

### C-119 — Connect the mobility constraint to the inventory channel and its incidence on entrants
raisers: R3 (cross-disciplinary opportunity 6)
severity: MINOR
class: REFERENCE (existing key)
verified: partly — "inventory" occurs twice, not once (the §I passing mention at `.tex:56` and a technical use in the ABM friction appendix at `.tex:919`); `graybill2026` is already in the bib and cited four times, already described as "in a housing-market-equilibrium setting" (`.tex:277`). No renters/first-time-buyer incidence sentence exists anywhere.
location: §I `.tex:56` or §VI.A; `graybill2026` at `.tex:100`, `.tex:261`, `.tex:277`, `.tex:329`
condition: Lock-in's most-discussed housing-policy consequence — the inventory channel and its incidence on first-time buyers and renters — should be connected to the paper's mobility constraint in one sentence.
fix: One sentence citing `graybill2026`'s housing-market-equilibrium setting. Existing key, no new bib entry.
wave: 5
source_rows: C-R3-39

### C-120 — Name distributional silence about Ginnie Mae borrowers as a limitation
raisers: DA:S4
severity: MINOR (inferred) — "the cheapest condition in the report"
class: WORDING
verified: true — §I concedes take-up is unmeasured (`.tex:52`) and the CDR contrast is committed at `.tex:269`, but §VIII.A contains no distributional limitation of any kind (read in full).
location: §VIII.A `.tex:733–752`
condition: §VIII.A must name the distributional silence about Ginnie borrowers as a limitation, not merely as a coverage bound.
fix: One sentence.
wave: 5
source_rows: C-DA-30

### C-121 — De-nest the sentences carrying four or more parentheticals
raisers: EIC (writing-quality judgment)
severity: MINOR
class: WORDING
verified: true — 21 main-text sentences carry >=4 parenthesized spans or >=3 em-dash asides; maxima at `.tex:731` (11 spans, three of them the trilemma's numbered legs) and `.tex:227` (6). So "routinely" holds at roughly 21 sites, not as a property of all prose.
location: main text `.tex:38–751`; worst offenders `.tex:731`, `.tex:433`, `.tex:227`, `.tex:349`
condition: The nesting must come down at those sites.
fix: Promote load-bearing parentheticals to their own sentences and demote the rest to footnotes or tablenotes. **Every parenthetical carrying a committed number must survive verbatim somewhere in the same file** — gate strings are matched against the whole `.tex`.
wave: 6
source_rows: C-EIC-15

### C-122 — Fold §VI.C into §VI.B
raisers: EIC (cut 5), SY:R11 (fold leg)
severity: MINOR
class: STRUCTURE
verified: true — §VI.C is 127 whitespace tokens on one page (`.tex:578–581`), the shortest subsection and the short pole of the 57x spread; §VI.B immediately precedes it. Checked: no gate or test references `sec:discussion-policy`, and the only ordering asserts in the gate suite (`tools/liveness_gates.py:818–821`) concern `tab:ladder` rows, not section order — so the fold is gate-free apart from the label repoint.
location: §VI.C `.tex:578–581`; destination §VI.B `.tex:544–577`
condition: A 134-word subsection should not stand alone.
fix: Delete the `\subsection` head and append the paragraph to §VI.B, then repoint any `\ref{sec:discussion-policy}`. Sequence after C-86/C-116, which add content to §VI.C.
wave: 6
source_rows: C-EIC-21

### C-123 — Abstract length and structure
raisers: R3 minor 3
severity: MINOR
class: WORDING
verified: true at a785f3d — the line was 246–248 words in two paragraphs (explicit `\par` at character offset 706), and the *second* paragraph carries the actual headline. **Now in tension with the Wave-1 landing:** 66df169 took the abstract to 287 words, and C-33 adds one more sentence.
location: `.tex:31`; a long-abstract variant already exists (`revised_paper_v18_long_abstract.tex`) as the natural home for anything cut
condition: R3 asks for one paragraph of <=200 words leading with the marginal against both denominators (C-31).
fix: **Do not act mechanically — this collides with three upheld conditions** (C-04, C-10, C-33 all add abstract content, and the two-paragraph structure is correct per A-02). If compression is wanted, it is a venue-scoped drafting decision: preserve the pinned spans ("+2.9 to +8.7", 85.7%, 91.3%, the hedged "(itself read from realized, partly behavioral turnover)" clause) and re-check the gate suite. Sequence after every abstract-adding condition.
wave: 6
source_rows: C-R3-28

### C-124 — Move the inference-machinery detail out of the abstract into T1's note
raisers: DA:m3 (second limb)
severity: MINOR
class: WORDING
verified: true — the parenthetical is in the abstract and T1 row 4 already carries the same content in its cell/note ("31 clusters; percentile read $[+3.0, +8.0]$, under-covering; the corrected ladder and its degrees of freedom are Table~\ref{tab:ladder}"), so the abstract's version is duplicative and the destination exists.
location: abstract `.tex:31`; T1 note a `.tex:79`
condition: The wild-cluster/percentile detail should live in T1's note, not the abstract.
fix: **Sequence conflict to resolve first:** C-01, C-04, C-10, C-33, C-34, C-35 all edit the same sentence, and 66df169 has already lengthened it — treat the abstract as one edit at the end of the wording waves, and keep whatever the abstract-scoped hedge-span gates (gate class 4) require inside the abstract.
wave: 6
source_rows: C-DA-20

### C-125 — CLOSE: re-count the abstract and confirm the two abstract files stay in sync
raisers: SY (R1-landing finding, items 3–4)
severity: MAJOR (handout-blocking bookkeeping)
class: CHECK
verified: true — 66df169 moved `.tex:31` from 1,552 to 1,795 characters and the abstract from 248 to 287 words, and the diff touched line 31 of **both** `revised_paper_v18.tex` and `revised_paper_v18_long_abstract.tex`; the response letter's claimed count and the tests' hardcoded anchor moved with it. Every further abstract condition (C-01, C-04, C-33, C-34, C-35, C-123, C-124) changes the count again.
location: `paper/v18/revised_paper_v18.tex:31`; `paper/v18/revised_paper_v18_long_abstract.tex:31`; the response letter's count; the tests' word-count anchor
condition: After the last abstract edit lands, the word count must be re-taken and propagated to the letter and the test anchor, and the two abstract files must be verified in sync.
fix: Re-count, update the letter and the anchor, diff the two line 31s. Also the close-out slot for `tools/render_gate.py` after the Wave-6 float re-flows and for the editions/bundle regeneration.
wave: CLOSE
source_rows: C-SY-33 (cross-listed from C-01)

### C-126 — EUGENE: retitle to the claim the paper establishes
raisers: EIC:W1, DA:m1, R3 (coherence cell), SY:X4/R15  [CONSENSUS]
severity: MAJOR (EIC item 1 of the five whose repair "would move this to Minor Revision without a single new run"); Minor -> Minor-Major (X4 widened it, and §5 keeps it out of the three Major-holding reasons)
class: WORDING
verified: true — `.tex:24` is exactly `\title{Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall}`; `.tex:150` contains verbatim "not by itself evidence that a stated policy objective was missed"; `.tex:546` computes the cap at "roughly 1.7 to 1.9 times as high as the Federal Reserve's own contemporaneous projection". Nuance: `.tex:92` already stipulates "shortfall" as cap-relative, so the term is defined even though the title reads as an assertion.
location: `.tex:24`; conceding sentence `.tex:150`; `.tex:546`
condition: The title asserts what §III.B declines to call a policy miss; the tension must be resolved (retitle) or explicitly accepted.
fix: **Reserved for Eugene — do not act.** Scope if authorized: `revised_paper_v18.tex:24`, `revised_paper_v18_long_abstract.tex`, `response_to_referees_round22.tex`, and load-bearing `tools/liveness_gates.py:168`, where the exact title sits in the `EXACTLY_ONE` list and will fail the suite unless updated in the same commit; plus the bundle/editions and every filename-adjacent reference. Archived `paper/v16/*`, `paper/v17/*` must not be touched. Candidates on the record: "…Redemption-Cap Shortfall" or "Mortgage Lock-In and the Composition of the Federal Reserve's Agency-MBS Runoff" (the latter matches this worktree's branch name). Cheaper alternative R3 accepts and Eugene may prefer: add the definitional gloss to the abstract's first sentence, or accept the tension explicitly at `.tex:150`.
wave: EUGENE
source_rows: C-EIC-01 + C-DA-17 + C-R3-40 + C-SY-04 + C-SY-47

### C-127 — EUGENE: whether the benchmark's monthly series should be rebuilt at monthly frequency
raisers: R2:M8
severity: "Major **if sustained**" — **NOT ARBITRATED** (the synthesizer did not re-derive the benchmark); see A-10
class: CHECK
verified: OPEN-UNARBITRATED — the evidence is exact but the defect is not established. `h1_zero_months_diagnosis.json` `zero_months["2023-02"].weekly_obs_b` = three identical Wednesdays (2616.2734730824) then a step, exactly as quoted; `span_last_asof` is the artifact's own field name; four zero months exist (2022-06, 2023-02, 2024-04, 2025-09) with `classification_summary.spike_followed_all_artifact = true` and committed `outcome: ARTIFACT`, "wording-class only … NO re-score; no committed number moves". The cap arithmetic checks: 3 x 17.5 + 39 x 35 = 1,417.5; 1,417.5 - 652.8 = 764.7 against `committed_anchors.benchmark_b = 764.7482532227`. R2 himself concedes "the 42-month total is robust because the pairs conserve … I do not dispute it."
location: §III.B `.tex:137`; App. N; §VII.B `.tex:635`
condition: Whether the monthly series should be rebuilt from published monthly SOMA principal-payment data (or CUSIP factor changes) rather than by differencing weekly Wednesday current-face levels — which would retire App. N's four clip zeros and reopen the monthly-timing question on a clean comparator.
fix: **Reserved for Eugene — do not act, do not restate `.tex:137`.** What would settle it: re-derive the 42-month total from a monthly principal-payment series and compare to 764.7482532227. Inside tolerance -> timing-only, wording note; outside -> the benchmark is in play and the round's scope changes. Requires an Eugene-level scope decision before any run.
wave: EUGENE
source_rows: C-R2-20 + C-SY-29 (SY:Z17 records M8 as "Major **if sustained**", explicitly not arbitrated, and covers both this leg and C-128's)

### C-128 — EUGENE: whether the realized-side window-boundary allocation should be priced
raisers: R2:M8 (consequence ii)
severity: OPEN-UNARBITRATED (same A-10 umbrella)
class: CHECK
verified: OPEN-UNARBITRATED, but the sub-claim about what is and is not priced is TRUE — `.tex:635` prices the cap-side convolution at -5.5% and states "the realized series is untouched"; the boundary asymmetry is real in the artifact (`zero_months["2022-06"].me_last_diff_b = +1.9873` against `next_month_diff_b = 8.0913`), and the pre-window Jan–May 2022 rise of $92.3bn is stated at `.tex:150` but used there for the anticipation share, not for boundary allocation.
location: §VII.B `.tex:635`; §III.B `.tex:150`
condition: §VII.B prices only the cap-side convolution, and the boundary months have no partner month to cancel into.
fix: **Reserved for Eugene — do not act.** What would settle it: a realized-side boundary sensitivity re-allocating the June-2022 and Nov-2025 boundary paydowns across the posting-cycle seam, reported the way `settlement_months_benchmark` already does for the cap side (same machinery, opposite leg). If the movement is inside the existing tolerance, say so once and close it.
wave: EUGENE
source_rows: C-R2-21

### C-129 — EUGENE: anonymized master and an archived DOI in place of the GitHub URL
raisers: EIC:W9, SY:Z18/R16
severity: MINOR (submission mechanics; blocking only for a double-blind venue, not for the talk)
class: STRUCTURE
verified: true — `.tex:25` `\author{Eugene Ong}`, `.tex:26` `\affil{Carnegie Mellon University}`, and `.tex:758` (App. A, **not** the title block) contains `\url{https://github.com/eugeneoCMU/Lock-in-Effect}` with an identifying handle.
location: `.tex:25–26`; App. A `.tex:758`
condition: Double-blind submission is precluded by the named author, the affiliation and a live repo URL with an identifiable handle.
fix: **Reserved for Eugene.** An `_anon` build variant (author/affil suppressed, `.tex:758` URL replaced by a DOI placeholder) is a new artifact, not an edit to the master — the split/variant machinery already produces `revised_paper_v18_long_abstract.tex`, so the pattern exists. Zenodo minting is outside-repo publishing and Eugene-only.
wave: EUGENE
source_rows: C-EIC-12 + C-SY-30 + C-SY-48 (cross-listed at C-85)

### C-130 — EUGENE: length and venue scope
raisers: EIC:W10, R2 (twice: score basis and Carroll proviso), R3 minor 8  [CONSENSUS]
severity: MAJOR (EIC: "Not defensible as submitted"; the RECOMMENDATION conditions sending it out on compression)
class: META
verified: partly/true — the page counts are exact (139pp total; main 1–94, appendix 95–139 per the R31 recut) and every measurable component checks to within a few percent: main text 45,192 tokens over 94 pages, appendix 20,291 over 45, §V.B 7,294 (pp.26–38), §V.E 6,193 (pp.41–52), §VI.C 127 (p.63) — a 57x subsection spread. The "12,000–15,000-word field norm" is an editorial assertion with nothing in-repo to check it against, and whether the norm comparison is right is a venue judgment, not a repo fact. R3's framing: a paper that needs an author-supplied navigation map (`.tex:94`) to be refereed has a structural problem, not a length problem.
location: whole main text `.tex:38–751`; the existing 1–94 / 95–139 split
condition: Either a venue with this length tolerance, or a compression pass moving body material to appendices.
fix: **Reserved for Eugene (scope decision).** Two hard constraints if compression is authorized: 108 gates and ~495 tests pin hundreds of manuscript strings, so every cut must be a **move** (literals preserved) rather than a deletion; and almost every other condition in this inventory *adds* text, so compression must be sequenced **after** the wording landings (which is why C-87 through C-91 sit in Wave 6). Mechanical relocations are carried by C-87–C-91 and C-122 once the scope call is made.
wave: EUGENE
source_rows: C-EIC-13 + C-R2-44 + C-R3-34

### C-131 — EUGENE: the adverse-findings register as a standalone methods note
raisers: R3 (cross-disciplinary opportunity 5 / Strength 2)
severity: MINOR
class: META
verified: true — the register exists at `app:verdicts` (`.tex:1393–1427`, Table 27 at `.tex:1400`) with the framing sentence R3 praises; R3 credits it with retracting the bootstrap understatement, the 0.2-point convergence, the 18.3-point basis-mixing error and the 27-cell positivity check. (Row count not independently verified — the table packs multiple rows per source line. A-03 concerns a different, false claim about this table.)
location: App. O `.tex:1393–1427`
condition: The register is a better answer to the garden-of-forking-paths problem in calibration work than most pre-registration templates and would stand alone as a short methods note.
fix: **Reserved for Eugene** — no manuscript edit; route to the venue/spin-off decision. C-37 is the one App. O edit this round should carry.
wave: EUGENE
source_rows: C-R3-38

### C-132 — EUGENE: the public Freddie loan-level parquet licensing question
raisers: coordinator (R32 plan; two auditors rated it CRITICAL) — not raised in any of the six panel inventories
severity: CRITICAL (as rated by the two auditors)
class: META
verified: OPEN — nothing in the six inventories addresses it; no verification was performed here and none should be attempted by an agent (it is a licensing judgment, not a repo fact).
location: repository history (the committed loan-level parquet inputs)
condition: Whether the public Freddie loan-level parquet may be redistributed in this repository at all.
fix: **Reserved for Eugene — do not act.** If it is a problem the remedy involves rewriting history, which no agent may attempt. Flagged here only so it is not lost from the round's ledger.
wave: EUGENE
source_rows: none (coordinator-supplied)

### C-133 — EUGENE: the push
raisers: coordinator (R32 plan; standing repo rule)
severity: n/a (process)
class: META
verified: n/a — the four Wave-1 commits are local; pushing is Eugene-only on this public-origin repo.
location: n/a
condition: Nothing in this round is pushed by an agent.
fix: **Reserved for Eugene.**
wave: EUGENE
source_rows: none (coordinator-supplied)

---

## ANTI-CONDITIONS — do not act

A-01 through A-10 are the ten pre-adjudicated anti-conditions (the synthesis's §8 plus §2.6, cross-checked in the
EIC, R1, R2, R3 and DA inventories). A-11 through A-20 are the additional panel self-refutations the inventories
discovered while verifying; each was confirmed present in the source files and is carried forward with its correction.

### A-01 — "Webb is the narrowest of the ten rungs it is chosen from"
claim: R1:M1's headline framing (also the premise of R1's M1 rhetoric).
why it is wrong: Measured widths recomputed twice, independently, from `floor_inference_correction_v2_results.json` read `R2_2018_gap<=-0.0025_age>=12`: percentile 5.0442 (demoted), CR1-t 5.1967, CR2-t 5.5787, **Webb 5.8230**, Rademacher 5.9268, CR3-t 6.0012, CR1-BM 6.0431, CR2-BM 6.7400, WCR 6.8284, CR3-BM 7.2836pp. Webb is third-narrowest live, fourth counting the demoted rung.
what a naive fix would break: Nothing in the manuscript needs changing on this premise. The surviving argument — Webb is the narrowest rung with a credible few-cluster coverage property, and the paper's own rule selects a wider one — is carried by C-20 (and its abstract instance by C-01). A reply letter answering M1 should print the width ordering and answer the surviving argument, not the superlative.
source_rows: C-R1-01 (+ SY self-refutation 1)

### A-02 — "The abstract is a single paragraph, 248 words"
claim: DA:m3 (first limb) asks for a break at "What lock-in itself adds…".
why it is wrong: `.tex:31` is 1,553 characters and contains an explicit `\par` at character offset 706, immediately before that exact sentence. The abstract is already two paragraphs and the break already sits at the seam DA names. The word count is the only half-true part (248 by whitespace split; the synthesis's 250 and R3's 246 are also off).
what a naive fix would break: Implementing it inserts a duplicate break. Note the diagnostic: the check was performed against the `.md` edition, where `\par` does not survive as a visible break — treat other panel claims that cite line 31 with that in mind. R3's reading (two paragraphs) is the correct one, and C-123 is recorded on that true premise.
source_rows: C-DA-19

### A-03 — "Of the ~13 Table 27 rows adjudicated against the headline, not one moved a reported number"
claim: DA:N9, offered as grounds for withholding credit for Appendix O.
why it is wrong: The floor demotion moved the headline +9.2 -> +5.6 and the central level 97.9% -> 91.3% through every dependent number (both marginals committed in `attenuation_sensitivity_results.json` `base_marginal_pp`); the percentile-bootstrap retraction replaced [+3.0,+8.0] as binding (`.tex:1412`) and the printed lower endpoint moved (`verdict.printed_lower_unchanged = false`, 2.796 -> 2.855); the floor-sweep reinterpretation landed at `.tex:1409`; the Danmarks Nationalbank validation turned a point into a swept band; `buyback_credit_bracket`'s `REVERSES` verdict turned a signed relief claim into the printed incidence bracket. The EIC's own STRENGTHS item asserts the opposite of DA:N9.
what a naive fix would break: A defensive paragraph rebutting this would add text to a paper already over length and would defend against a false charge. The one App. O edit worth landing is C-37's domain sentence.
source_rows: C-DA-33

### A-04 — "There is no cell anywhere in the paper's apparatus in which the mechanical baseline fails to deliver the majority"
claim: DA:N1, offered as a reason to lead **more** confidently with "most of the shortfall was mechanical".
why it is wrong: Refuted by the paper's own frozen artifact — `floor_form_mixture_results.json` `cells["4.991|1|0"].share_pct = 44.6996` standalone (~35.6% shared) at the headline floor under the disclosed additive form: a minority. DA's supporting cells (101.94 / 94.79 / 82.37 / 68.39 across 75–150 PSA) are all correct but sweep the ramp under the **max form only**, which is exactly the conditioning DA's own C2 says must be disclosed.
what a naive fix would break: Strengthening the claim would deepen the defect C-04 exists to repair (the arbitration's largest editorial consequence). The salvageable inverse is C-04 itself.
source_rows: C-DA-31

### A-05 — "Duplicated table captions in the header rows of Tables 1, 8, 9, 25, 27 will read as sloppiness in a submitted PDF"
claim: R2 minor 10.
why it is wrong: The defect exists only in the markdown edition (`~/Downloads/UPLOAD_ROUND11/revised_paper_v18.md:41` renders the caption as bold text and `:43` repeats it inside the header row's first cell). The `.tex` is correct: for T1 the sequence is `\begin{longtable}` -> `\caption{...}` -> `\label{}\\` -> `\toprule` -> header row -> `\midrule` -> `\endfirsthead`. There is no PDF defect.
what a naive fix would break: "Fixing" the .tex would damage correct LaTeX. The honest alternative is a converter fix in `tools/editions/tex2md.py` (the longtable->markdown path introduced when R31 converted five over-tall tables to `longtable`) plus a regenerated .md edition — and recording the panel's premise as refuted rather than silently satisfying it.
source_rows: C-R2-32

### A-06 — "The paper headlines the Danish minimum"
claim: R2:M6.
why it is partly wrong: Right for T1's cell (`.tex:85` prints "+$61.2 billion" with the sign-forcedness and the -$99.9bn anchor but not the +$256.8bn sweep top) and right in the weak sense that the abstract carries no Danish figure at all. **Wrong for §I and §VI.D**: `.tex:52` already reads "+\$61.2 billion (8\% of the benchmark), the zero-refinance edge of a band swept to +\$256.8 billion at 3\% refinance-in-place", and `.tex:590` already says "I therefore report the rule-only gap as a band … rather than at the zero point".
what a naive fix would break: A reframing of §I/§VI.D would duplicate language that is already there. Scope the fix to T1's cell (C-49) and, only if a Danish sentence is reinstated, the abstract — one table cell and one sentence, not a reframing.
source_rows: C-R2-16 (scoped) + SY self-refutation 7

### A-07 — "The draw's >=4.0% coupon share is 53.7%, not 13.8%"
claim: R2:M2's corrective figure.
why it is partly wrong: 53.7% is correct **only** on UPB-weighted rounded-coupon buckets (recomputed 53.68%); the same draw is 58.21% count-weighted and 47.0% on raw coupons >=4.00%. The three-object confusion R2 identifies is real; the corrective number itself needed a basis label — the irony of a basis-labeling complaint.
what a naive fix would break: Printing "53.7%" unqualified repeats the error in the other direction. C-64 must name the basis of each number in the row itself.
source_rows: C-R2-06 (correction) + C-SY-49 + SY self-refutation 8

### A-08 — "40,234 active at window start, from `loan_sample.parquet`"
claim: R3's provenance for the household-count arithmetic.
why it is wrong: The parquet's `balance > 0` count is **40,077**. 40,234 is the manuscript's own attrition figure (`.tex:1085`, also `.tex:219/275/1026/1063`) and the survival count in `attenuation_sensitivity_results.json`.
what a naive fix would break: Swapping in 40,077 would contradict the manuscript's committed attrition accounting and the frozen artifact. Use 40,234 as the manuscript's window-start survivor count, do not present it as a parquet balance filter, and do not swap the number (C-76 is recorded verified:partly on this basis). The downstream arithmetic is unaffected: mean balance over all 75,000 rows = $126,812.61.
source_rows: C-R3-02 (constraint) + SY self-refutation 9

### A-09 — "Flip the printed beta_1 signs so Table 3 and Table 7 agree"
claim: DA:M3's first proposed remedy, repeated as R4's parenthetical alternative.
why it is wrong: `eq:beta1` (`.tex:228`) carries a **leading minus**, so beta_1 = +0.0686 is correct for `tab:params` and for §V.B's "the *positive* beta_1 of (3)", while `hazard/literature_hazard.py:32` `rothstein_beta1` **omits** that minus and returns -0.06857052676484808 — the value `tab:lowband` printed and every artifact records (`psa_level_sweep_results.json` `"beta1": -0.06857052676484808`).
what a naive fix would break: A blind sign flip makes the table contradict the production code, and a gate asserting naive sign equality would enforce that wrong fix. The admissible remedy is harmonisation **plus** a reconciling note naming both conventions and a replicator note pointing at `rothstein_beta1`. **Status:** `d22b265` landed the harmonisation-to-`eq:beta1` branch (nine tab:lowband cells positive) **with** the replicator note recording the code's opposite sign, plus gate #109 and 5 tests — a different branch than the inventories recommended, but one that keeps the code's sign disclosed. Coordinator check: confirm the replicator note carries the signed value so this anti-condition's substance is met (recorded as the residual in C-13).
source_rows: C-DA-10 (rejected limb) + C-SY-20 + C-SY-36

### A-10 — R2:M8 (benchmark frequency) is not arbitrated
claim: R2:M8 and its consequence (ii), that the monthly benchmark series is built at the wrong frequency and the realized-side boundary is unpriced.
why it must not be treated as a defect: The synthesizer explicitly did not re-derive the $764.7bn benchmark and records M8 as plausible-but-unverified; R2 himself concedes the 42-month total is robust because the weekly pairs conserve. The committed diagnosis is `outcome: ARTIFACT`, "wording-class only … NO re-score; no committed number moves", and the cap arithmetic checks exactly (3 x 17.5 + 39 x 35 = 1,417.5; 1,417.5 - 652.8 = 764.7 against 764.7482532227).
what a naive fix would break: Restating `.tex:137` on an unarbitrated premise, or launching a benchmark rebuild, would put the paper's denominator — and every percentage in it — in play without an established defect. Recorded as C-127 and C-128, both wave EUGENE, both "do not act".
source_rows: C-R2-20 + C-R2-21 (both routed to EUGENE) + SY self-refutation 10

### A-11 — R1(a)'s own proposed abstract wording
claim: R1(a) asks for "identifies levels only" -> "identifies levels, not monthly timing".
why it is wrong: The replacement still asserts that the design identifies levels, which is exactly what §V.E (`.tex:319`, "does not identify the aggregate recovery level") and §VII.F (`.tex:709`, "does not identify levels") deny. Applied literally it would have left the self-refutation unfixed.
what a naive fix would break: Restoring R1(a)'s wording would reintroduce the contradiction. The working tree instead landed "identifies a marginal, not a level and not monthly timing", which is the correct repair (C-09, `66df169`). Do not restore R1(a)'s literal.
source_rows: C-SY-33 / SY self-refutation 11 (and the EIC's C-EIC-02 fix text, which proposed the same literal)

### A-12 — DA §1's "the headline should be restated as nearer +1 to +11, concentrated low"
claim: DA's §1 closing sentence, its summary of both CRITICALs.
why it is wrong: No committed pair supports (+1, +11). The nearest committed endpoints are the PSA convention span +0.9 to +15.6 (`psa_level_sweep_results.json` `ranges["4.991"]`), the form-conditional hull +3.5 to +13.1, and the additive-form point +11.2. "+1 to +11" is a rhetorical rounding of the PSA span truncated at the top, and it **contradicts DA's own C1(a)** proposal of +2.9 to +6.8. Separately, C1(a)'s own lower endpoint is not derivable from the reads it names: the age-standardized 5.51% floor implies ~+3.8 and the Fannie 5.52% only "below +4.3", so an all-available-reads interval is ~+3.8 to +6.8 — DA's +2.9 is the *composed* Ginnie x age-std cell (2.928), a different object that numerically collides with the wild-t lower endpoint.
what a naive fix would break: Implementing both DA proposals would install two incompatible restatements. Any interval restatement must be C-17's or C-19's, with its provenance named, and must not let three distinct +2.9s (wild-t endpoint, composed cell, proposed interval floor) read as one number.
source_rows: C-DA-01 (+ the caveats recorded in C-DA-02)

### A-13 — X3's "Table 12" as a +5.6pp site
claim: The synthesis's X3 lists Table 12 among the tables printing +5.6pp; the EIC makes the same slip and adds a non-existent "§VI.A welfare paragraph" instance.
why it is wrong: T12 is `tab:wal` (approximate SOMA portfolio WAL by prepayment scenario); its `5.6` occurrences are weighted-average lives **in years** ("Production ABM (11.68%) & 6.0 & 5.6"), a numeric collision. §VI (`.tex:530–622`) contains no `+5.6` at all. The tables that do print +5.6pp are T1, T5 (`.tex:333–345`), T6 (`.tex:368`) and T8 (`.tex:433`); the `tab:wal` row that depends on the headline calibration is `.tex:565` (floor read 4.99%), which prints 9.5/8.6.
what a naive fix would break: A posture sweep (C-17) that "fixed" T12 would overwrite WAL years with a marginal, silently corrupting the duration exhibit C-48/C-83/C-113 all depend on. Do not cite T12 in any repair note.
source_rows: C-SY-03 / SY self-refutation 12 (+ C-EIC-06's verified:partly correction)

### A-14 — X2's third paragraph attributed to Appendix G
claim: X2 (and R3's writing cell) place the 10,696-char paragraph in Appendix G.
why it is wrong: The block at `.tex:1099–1100` falls inside **Appendix F** (`app:patha-detail`, `.tex:1089–1167`); Appendix G is `app:ridge` at `.tex:1168`. All four character counts (14,732 / 11,312 / 10,696 / 8,051) are exact.
what a naive fix would break: A splitting pass aimed at `app:ridge` would restructure the wrong appendix and leave the actual monolith intact. C-87 carries the corrected location.
source_rows: C-SY-02 / SY self-refutation 13 (+ C-R3-35's same correction)

### A-15 — Z1's "2021 at 22% of the draw" and the "factor of ten" magnitude rhetoric
claim: Z1 (and R2:M1) describe the draw's 2021 share as 22% and the 2017–19 gap as a factor of ten against book face.
why it is partly wrong: 22.32% is the **orig-UPB-weighted** share; the count share is 20.00%; and the **balance-weighted** share — the one the aggregation actually uses, per `.tex:269` ("Aggregation from the 75,000-loan sample to the SOMA book applies balance weights") — is **42.31%**, against 43.9% of book face, i.e. nearly matched. On balance weights 2017–19 is 27.05% against 6.0% of face (~4.5x, not 10x). Same unlabelled-basis slip the synthesis convicts R2 of in §8.7.
what a naive fix would break: Restating the count-basis magnitudes as exposure facts would misdescribe the aggregation and hand a referee an easy correction. The per-loan censoring argument survives — that is what carries C-06/C-07 — but the magnitude rhetoric must be basis-labelled, and both bases must be printed in T25 (C-64).
source_rows: C-SY-13 (correction) / SY self-refutation 14

### A-16 — Z19's "none of these references is cited"
claim: Z19/R16 lists seven missing references and says none is cited.
why it is wrong: `fonseca2024` (Fonseca, J. and Liu, L., *Journal of Finance* 79(6)) is already in the 70-entry bib and already cited in the body, and `hazard/data/fonseca_band_anchor_results.json` shows a Fonseca anchor already in the pipeline. Six of the seven, not seven, are genuinely absent.
what a naive fix would break: Adding a Fonseca entry blind would create a duplicate key or a duplicate reference. Only the **Fonseca–Liu–Mabille** spatial-housing-ladder extension would be new, and its distinctness must be verified before it is added (C-85).
source_rows: C-SY-31 (correction) + C-R2-37 / SY self-refutation 15

### A-17 — §8.1's CR3-BM truncation attributed to the upper endpoint
claim: The synthesis's §8.1 rider says CR3-BM's upper endpoint (9.5645) is grid-truncated at 6.0%.
why it is wrong: The artifact says the opposite — `cr3_t_interval_df_bm.upper_pp_edge.truncated_at_grid_edge = false`; it is the **lower** pp edge (2.2809) that is truncated, mapped at the 6.0% **floor** grid edge (the floor CI's *upper* endpoint sits at the grid edge, which truncates the *marginal's lower* endpoint). The same holds for `wcr_inverted.lower_pp_edge`.
what a naive fix would break: A note printed with the truncation on the wrong endpoint would misstate which side of the interval is unreliable — and the substantive consequence (promoting CR3-BM requires extending the floor sweep grid) attaches to the lower edge. C-20 and C-100 carry the corrected wording.
source_rows: C-SY-25 (correction) / SY self-refutation 2 (+ C-R1-02's truncation caveat)

### A-18 — R1:M4's "read-to-read spread 0.53pp against a within-read SE of 0.39pp"
claim: R1:M4's arithmetic core — "the layer that is *not* priced is the larger one", hence "binding" is not defensible.
why it is wrong: The 0.53pp is a basis mix. `fannie_floor_read_results.json` `comparison` gives `freddie_headline_cpr_pct = 5.185`, `fannie_headline_cpr_pct = 5.522`, `difference_pp = 0.337` on the **same** selection (pooled 2017–2019, 438 cohort-months); the artifact carries no 2018-leg Fannie read at all. R1 differenced Fannie's pooled read against Freddie's 2018-leg read. Like for like the spread is **0.337pp**, *below* the within-read cluster SE of 0.3934pp — the variance ranking reverses.
what a naive fix would break: Rebuilding the interval on R1's "3.7–4.3pp" pooled-read arithmetic would propagate the basis mix into the headline. The surviving parts of M4 are C-26 (the paper's own basis mix in the ladder_fannie span) and C-27 (transport disclosed but unpropagated); a reply should print the 5.185 / 5.522 / 0.337 triple.
source_rows: C-R1-11

### A-19 — R1's "The two layers sit on disjoint data and disjoint time" as a manuscript defect
claim: R1 minor asks that the phrase be rephrased to "different observation windows and different aggregation units".
why it is wrong as a manuscript condition: `disjoint` appears nowhere in `revised_paper_v18.tex`. The phrase lives in `layer_convolution_results.json` `dependence_bracket.note` — an artifact field, not manuscript prose. The manuscript says only "the two layers convolved as independent, $[+2.80, +8.99]$pp … independence is assumed, not measured --- under maximal positive dependence the width is $8.12$pp" (`.tex:433`), which makes no disjointness claim; the comonotone hedge is confirmed correct (`comonotone_width_pp = 8.1165`).
what a naive fix would break: A search-and-replace for a string that is not in the .tex, or an edit to a frozen artifact's documentation field. R1's substantive point (the two layers share the Freddie 2017–2021 origination universe; only observation windows and aggregation units differ) is correct on the facts and may be added at `.tex:433` as a positive statement — optional, and the reply should note the offending sentence is an artifact field.
source_rows: C-R1-27

### A-20 — Other verified mis-citations and inflated figures that must not drive edits
claim/correction, each verified in a source row:
- **EIC:W6's +5.6 site list** — the "§VI.A welfare paragraph" instance does not exist and Table 12's 5.6 is a WAL year (see A-13); the circulation complaint is nonetheless *understated* (24 occurrences across 21 lines).
- **EIC/R2/R3's "2,200-word paragraph in §V.B"** — no such paragraph exists: the longest single body paragraph is 1,606 words at `.tex:323` (§V.**D**/E, not §V.B), and the longest inside §V.B is 1,155 words at `.tex:269`; the markdown edition's merge of `.tex:227` + `eq:beta1` + `.tex:231` is the likely origin. The correct target is "eight paragraphs over 950 words, three over 1,050" and 11 blocks over 6,000 chars (C-87).
- **EIC's "Table 8's cells run past 900 characters"** — exactly one cell does (1,411 chars); no other exceeds 601 (C-93).
- **EIC's "~13% of the main text" for the ABM bundle** — 10.6% of pages / 9.7% of tokens (C-88).
- **R2:M3's "4.99 x 0.77 = 3.84, almost exactly the in-window read"** — the in-window reads are 4.00% and 3.97%, implied ratio 0.795; the coincidence is 0.13–0.16pp loose and must not be quoted as printed (C-71).
- **R1:M3's five-vs-six read months** — R1 says "six reporting periods" in one place and "five consecutive months" in two others; the verified histogram is six periods (201807–201812) with 2 rows in the first (C-02, C-70).
- **R3's "York 2022"** for the ex-ante-projection observation — the key is `nyfed2022` (cited at `.tex:546`); no `york2022` exists in the bib or the .tex. An artifact of reading "New York Fed" through the markdown edition.
- **R3's "§VI.C is the one un-numbered section"** — §VI.C *is* numbered in both the .tex and the md edition; the true reading is "carries no quantities" (C-86).
- **DA's "479 tests"** and any other test count — `tests/*.py` defines 293 `def test_` functions against a claimed 495 collected; **do not print a test count** (C-37).
- **DA's "the zero months flip the frozen timing rule"** — `.tex:1356` records that the rule **passed** and that nothing is claimed from the pass because five post-hoc diagnostics cannot discriminate; do not restate it as a flip (C-62).
- **DA's `measured_minus_implied_pp = -0.129` attributed to the composed overlay** — that key belongs to `conventional_agestd` (against the 3.8 grid-read); the overlay's proportional deviation is 0.00023pp (C-19, C-99).
what a naive fix would break: each of these would put a false literal, a wrong location or a wrong count into the manuscript or a reply letter. They are recorded so the conditions built on the same rows can be landed without inheriting them.
source_rows: corrections carried inside C-EIC-06, C-EIC-13, C-EIC-16, C-EIC-17, C-R1-05, C-R2-08, C-R2-43, C-R3-29, C-R3-35, C-DA-08, C-DA-15, C-DA-24, C-SY-03

---

## RUN INVENTORY

One row per RUN-class condition. "Frozen — must NOT touch" names the committed artifact whose bit-exactness the run
must preserve. Inputs known absent from this worktree: **`floor_form_offwindow/`**, **`fannie_quarters/`**,
**`cohort_month_panel_fannie.parquet`** (the *JSON* results these directories produced are committed and readable;
the raw staging inputs are not). External (non-repo) data needs are flagged the same way.

### R-01 — C-07 post-stratified marginal
computes: the central/null pair re-scored on the 75,000 draws post-stratified onto the SOMA coupon x vintage-group cells; both legs' floor-bind shares on the re-weighted pool.
machinery: the `cross_design_reweight` harness + the `vintage` column already on the pool (`hazard/agents.py`, today read only by `reweight_to_soma_coupons`).
writes: new artifact, e.g. `hazard/data/book_composition_marginal_results.json`.
must NOT touch: the committed draw-based bind shares (68.8% / 35.8%) — parity gate required; `composition_shift_results.json`.
inputs present: **yes** (`loan_sample.parquet`, `composition_shift_results.json`).
pre-committed expectation: **none stated** — the spec must pre-commit a band. Hard limit to report with the result: 2022 and pre-2017 have zero support in the draw (`vintage_range = [2017, 2021]`).

### R-02 — C-08 estimated-spline baseline hazard
computes: the paired-leg marginal with h0 supplied by Path A's estimated seasoning spline instead of the 100 PSA ramp.
machinery: the `psa_level_sweep` harness, but requires a **new** `BASELINE_MODE` accepting a tabulated age->CPR profile — `hazard/literature_hazard.py:73` `baseline_hazard` supports only `"psa"` and `"weibull"`.
writes: new artifact (must not overwrite `psa_level_sweep_results.json`).
must NOT touch: `psa_level_sweep_results.json`; the psa-mode path must be shown bit-unchanged.
inputs present: **yes** (Path A's spline is fitted in-repo; knots {12,24,36,60,84,120} are the synthesis's proposal, pinned in no artifact and so must be pre-committed).
pre-committed expectation: **none stated** — the synthesis says only that the run "flips the sign of that trade". Spec must pre-commit a band and pre-authorise an unfavourable landing. If the three scoping requirements are out of reach, record infeasible-this-round.

### R-03 — C-70 calendar-standardized floor read
computes: the off-window floor read standardized to the QT window's month mix, remapped through the frozen PCHIP grid.
machinery: `hazard/seasonal_floor_timing.py`'s own 12-cell profile builder/normalizer (full-panel basis) + the committed PCHIP mapping.
writes: new artifact, e.g. `seasonal_standardized_floor_read_results.json`, with a parity gate reproducing the `shape_only` vector and the 4.991% raw read bit-exactly.
must NOT touch: `seasonal_floor_timing_results.json`; the pinned 4.000% exposure-weighted mean.
inputs present: **yes** (`cohort_month_panel.parquet`, `seasonal_floor_timing_results.json`).
pre-committed expectation: **stated by the source rows** — standardized read ~5.21%, marginal ~+4.7/+4.8pp, a **-0.8pp** move (arithmetic reproduced in two inventories). Must be run as a pair with R-04.

### R-04 — C-71 activity-matched floor read
computes: the floor read's dependence on housing-activity level across the three 2017–2019 legs, and the marginal at an activity-matched off-window floor.
machinery: the floor-read path behind `tab:oosfloor` / `floor_sweep` / `oos_identification`.
writes: new artifact, e.g. `floor_activity_match_results.json`.
must NOT touch: `oos_identification_results.json`, `matched_depth_reconciliation_results.json`.
inputs present: **NO — external data required and absent.** Existing-home-sales / new-home-sales / all-cash-share series are NAR or Census data; "existing-home sales" appears nowhere in the .tex and the repo holds no such series. The synthesis records R2's 24% activity ratio as an unverified external datum.
pre-committed expectation: direction **upward** (the assembly's one available upward floor-side correction); sizing anchor already in the paper (0.56 x 20.874 = $11.7bn = 1.53pp, giving 5.6 + 1.5 = 7.1). If the data cannot be obtained: record **INFEASIBLE** with that reason and land C-41's disclosure.

### R-05 — C-72 month-clustered and two-way ladder rungs
computes: month-clustered (G~6) and two-way stratum x month CR / wild-t intervals on the R2 read, endpoints mapped through the frozen PCHIP grid.
machinery: `hazard/floor_uncertainty.py` `cluster_bootstrap_cpr` (cluster unit is a read parameter) + `hazard/floor_inference_correction_v2.py`'s Webb/BM/WCR constructions + `hazard/floor_inference_correction.py:36–50`'s grid-edge-truncation convention.
writes: new artifact, e.g. `floor_inference_correction_v3_results.json`, with the same P1–P7 parity gates.
must NOT touch: `floor_inference_correction_v2_results.json`; the printed T9 rows and their gate spans.
inputs present: **yes** (`cohort_month_panel.parquet`).
pre-committed expectation: none; **pre-commit a NOT_COMPUTABLE landing** — with 5–6 month clusters and 31 strata the two-way df is tiny, and `episode_confrontation_within_results.json` `limb_c.confounds_note` already records the analogous two-way FE variant as "EXACTLY unidentified".

### R-06 — C-73 implied cross-sectional gradient grid
computes: the analytic implied gradient at the 4.991% headline floor and under the additive form, at 75/100/125 PSA.
machinery: analytic evaluation of hazard eq.(2) — `max(h_floor, h0_PSA(age) e^{-beta_1 100 g})` — plus `hazard/competing_risks.py` for the additive survival-scale combination. **`hazard/episode_confrontation.py`'s `main()` must not be called** (it would rewrite the frozen artifact); `hazard/episode_confrontation_within.py` shows the established replicate-the-gates pattern.
writes: new artifact, e.g. `episode_implied_gradient_grid_results.json`, with a G-gate reproducing +0.9371 at the committed 4% / max / PSA-100 cell bit-exactly.
must NOT touch: `episode_confrontation_results.json` and the pinned +4.20 / [+3.59,+4.66] / +0.94 / 0.68 / p=0.005 literals (`spec.must_not_change`).
inputs present: **yes** (frozen bucket definitions; no engine run needed).
pre-committed expectation: directional — the 68.8% vs 36.3% bind shares predict a **flatter** implied gradient at the headline floor and steeper only under the additive form; if so it is evidence about the **form**, not about beta_1's magnitude (the artifact's verdict forbids the latter reading).

### R-07 — C-74 Ginnie attenuated-elasticity leg
computes: the Ginnie share scored with the elasticity attenuated by the measured CRR differential, instead of zeroed.
machinery: `ginnie_cpr_overlay` / `ginnie_overlay_offwindow`, already consuming `gmar_dec25_cpr_series.json`'s `crr` block (a `crr_only` variant already exists, `marginal_pp = 7.3332`).
writes: new artifact, e.g. `ginnie_overlay_attenuated_results.json`.
must NOT touch: `ginnie_cpr_overlay_results.json` (incl. `G3_static_bound` = [20.3, 47.3] and the window mean 2.1365).
inputs present: **yes**.
pre-committed expectation: **direction not obvious ex ante** — faster voluntary Ginnie speeds are consistent with a weaker gap response, which would *raise* the retained marginal above 0.797x share scaling; the spec must pre-authorise either sign.

### R-08 — C-75 Danish buyback discount D
computes: D derived from the Danish leg's own prepayment-consistent PVs at its 5.61% CPR against the window market-rate path (or matched-coupon/matched-month TBA marks), then the restated cash bracket.
machinery: `hazard/buyback_credit_bracket.py`'s existing path (it already reads `microsim_results_us_intercept.parquet` for E), with `D_GRID` derived instead of hard-coded at `[0.32, 0.34, 0.36, 0.38]`.
writes: new artifact (derived-D grid) + restated bracket.
must NOT touch: `buyback_credit_bracket_results.json`'s identity gates (`gap_cash(D) = 61.18834 - D x 470.65325`, `P1_gap`, `P3_channel_magnitude`) — the identity must still hold at the new D.
inputs present: **yes** (`microsim_results_us_intercept.parquet`; TBA marks would be external and are optional).
pre-committed expectation: **stated** — a prepayment-consistent D ~0.21–0.24 roughly halves every cash figure (-$89.4/-$117.7bn -> ~-$42.4/-$51.8bn); the `REVERSES` verdict survives (larger than the $61.2bn gap by ~1.7x rather than 2.5–2.9x). Gate #103 `BUYBACK_BRACKET_SPANS["reversal_range"]` and `tests/test_buyback_incidence_gate.py` must be updated with it, not bypassed.

### R-09 — C-76 transaction-count metric and external volume check
computes: foregone-payoff / suppressed-move counts implied by the marginal, with the moving-share bracket, grossed to the whole market by the SOMA exposure share and compared against realized mortgage-financed existing-home-sale volume.
machinery: existing Path B outputs (`floor_form_mixture_results.json` parity gates for the differential; `moving_share_bracket_offwindow` for s in {0.25,0.5,1}; `microsim_results.parquet` `exposure` for the share) plus one new script — not a new microsimulation.
writes: new artifact + a T1 row (C-82) once it lands.
must NOT touch: `loan_sample.parquet`; the committed differentials ($42.61bn off-window, $70.35bn in-sample, band $33.31–51.75bn).
inputs present: **partly — external data required and absent.** Existing-home-sales volume and the mortgage-financed share are NAR/Census series not in the repo and must be pinned like any other benchmark input.
pre-committed expectation: **stated as a strain** — ~49k/yr on the SOMA book, ~230k/yr whole-market at most, against ~1.3m/yr fewer mortgage payoffs implied by the 6.1m->4.1m sales decline (about one-sixth) and Aladangady's 44% attribution. Pre-authorise an unfavourable landing. Two honesty constraints: face/mean-balance is an approximation to a transaction count, and the hazard has no move/refi split — the output is a **bound**, not a count.

### R-10 — C-77 Aladangady reconciliation under the additive form
computes: the same calibration condition `trapped_null(phi*) - trapped_null(1) = (0.56/0.44)[central(1) - null(1)]` re-solved with FLOOR_MODE additive (s=1) at both committed floors.
machinery: the existing bisection harness in `hazard/scaled_null_housing_activity.py` (which currently asserts `FLOOR_MODE == "max"` / `BASELINE_MODE == "psa"`) + the additive path already production code in the `floor_form_mixture` family.
writes: new artifact or a new block; the T5 row gains the result.
must NOT touch: `scaled_null_housing_activity_results.json` (phi* = 0.75390625, `marginal_pp = 0.8979`); `floor_form_mixture_results.json` parity gate `P_marg_4.991_s1 = 85.705`.
inputs present: **yes** (note `floor_form_offwindow/` staging is absent, but `floor_form_offwindow_results.json` and `floor_form_mixture_results.json` are committed and are what this needs).
pre-committed expectation: **directional** — with no censoring, more of the housing-activity deflation passes into the null, so phi* and the surviving marginal differ materially from the max-form cell. If not run, the row still gets its form mark.

### R-11 — C-78 episode gradient within age bands
computes: the within-cell gradient decomposition with loan age added to the standardization cells as 12-month strata.
machinery: `hazard/episode_confrontation_within.py` unchanged in structure (it already does exact within-cell decomposition and reads `mean_loan_age`).
writes: new artifact or a new limb.
must NOT touch: `episode_confrontation_within_results.json` (`limb_a.standardized_gradient_pp = 3.4409`, CI [+1.170,+5.140]) and `episode_confrontation_results.json`'s pinned literals.
inputs present: **yes** (`cohort_month_panel.parquet`).
pre-committed expectation: none stated; **the gradient may collapse and that result lands** — spec the landing rule before running.

### R-12 — C-79 Danish interest-only share
computes: a Danish leg with an IO share applied to scheduled amortization on both legs.
machinery: the Danish amortization path (not the hazard), so it does not need R-02's baseline machinery.
writes: new artifact.
must NOT touch: the committed danish_* family (`us_intercept`, `refi_finegrid`, `offwindow_floor`, `discount_bound`, `external_validation`, curtailment scaling).
inputs present: **NO — the IO share is an imported institutional parameter with no committed source in this repo.**
pre-committed expectation: **signed ex ante** — opposite in direction to the payoff rule (an IO share cuts scheduled amortization, the null's largest component). If no defensible input can be sourced, record infeasible and let the existing `.tex:590` concession stand.

### R-13 — C-80 depth-ladder shape exhibit
computes: exposure-weighted per-bin CPR (7.09 / 6.99 / 4.67 / 4.65 / 4.87), exposure shares, and **stratum-cluster standard errors** — the SEs are the only new computation; the bins are arithmetic on committed fields.
machinery: the committed nested reads in `matched_depth_reconciliation_results.json` + the existing stratum-cluster bootstrap.
writes: new artifact + a short exhibit, with a parity gate reproducing the five nested reads (5.334 / 4.991 / 4.695 / 4.722 / 4.869).
must NOT touch: `matched_depth_reconciliation_results.json`.
inputs present: **yes**.
pre-committed expectation: the shape is already measured — step then plateau, which is what a censoring (max) form predicts and an additive form does not. Four hedges must print with it (shallow 2018 gaps; 11.3% exposure in the deepest bin; composition drift with depth; refinancing in the shallow bins).

### R-14 — C-81 state-contingent cap two-input table
computes: for each book OTM-share cut (200/300/400bp) x turnover-floor band point, achievable $bn/month and the implied cap.
machinery: the existing WAL/amortization calculator behind `tab:wal` (run `wal_normal_turnover`) + `composition_shift_results.json`'s CUSIP coupon-by-vintage tabulation.
writes: new artifact + a §VI.B table; **prints new literals**, so a spec-before-run header and parity gates against T12's printed rows are required.
must NOT touch: `tab:wal`'s committed rows; `composition_shift_results.json`'s anchors (book WAC 2.49%, vintage shares).
inputs present: **yes** — a re-tabulation of committed inputs through committed machinery, no new estimation.
pre-committed expectation: anchored on the verified arithmetic ($17.63bn/month achievable, $33.75bn/month ceiling, ±~$3.6bn/month from the floor read's interval).

### R-15 — C-92 age-varying floor sweep
computes: the marginal under an age-varying floor built from the App. J ladder (3.68% / 5.78% / 10.99% by age band).
machinery: the existing `floor_form_*` / `floor_sweep` grid machinery.
writes: new artifact, e.g. `floor_form_age_results.json`.
must NOT touch: `tab:floorband` / `tab:seasonalfloor` committed rows.
inputs present: **yes**.
pre-committed expectation: none; **spec it so it cannot repeat the `floor_cyclical` mislabel** (that run measured floor dispersion under FLOOR_MODE='max', not cyclicality) — state ex ante what varies and what the scramble/permutation null is. Minimum acceptable substitute is the one-sentence flag.

### R-16 — C-26 (optional branch) Fannie 2018-leg floor read
computes: the Fannie counterpart of the 2018 rising-rate leg, so the manuscript's "same off-window cell" claim becomes true.
machinery: `hazard/fannie_floor_read.py`, which already carries the leg-split machinery from `out_of_window_floor`.
writes: a `2018_rising_rate` block in the Fannie artifact family.
must NOT touch: `fannie_floor_read_results.json`'s committed `out_of_window_2017_2019` block (Freddie parity 5.185, Fannie 5.522, difference 0.337).
inputs present: **NO — `cohort_month_panel_fannie.parquet` is absent from this worktree, and `fannie_quarters/` staging is absent.** Not executable here; take C-26's wording branch instead.
pre-committed expectation: none stated.

### Also RUN-adjacent, deliberately NOT proposed as runs
- **C-103's fixed-n bootstrap variant** (`hazard/bootstrap_pathb_cluster.py`, 200 replicates): optional; R1 accepts the one-sentence concession instead.
- **C-56's DV01 / market-value image** of the 0.6 WAL-year: needs a discount curve the design does not carry and would reopen App. L's explicit scope declination — recommended against unless Eugene wants it.
- **C-25's elasticity-SE propagation**: only feasible if Liebersohn–Rothstein publish a standard error on the mobility coefficient; otherwise it is a disclosure, not a computation.
- **C-127 / C-128** (benchmark rebuild, realized-side boundary): wave EUGENE, unarbitrated — no run may be specced without a scope decision (A-10).

---

## GATE AND TEST COUPLINGS

Every gate pin or test coupling the six inventories flagged, with the condition whose fix disturbs it. Line numbers
are as read in the inventories (read-only; **no repo script was executed and none may be — `tools/liveness_gates.py`
executes its full workload even on `--help`**).

| gate / test | pinned literal or property | condition(s) whose fix disturbs it |
|---|---|---|
| `tools/liveness_gates.py:168` (gate class 2, `EXACTLY_ONE`) | the ratified title, **byte-exact** | **C-126** (EUGENE retitle) — must be updated in the same commit or the suite fails; also the bundle/editions and `response_to_referees_round22.tex` |
| `tools/liveness_gates.py:2133` `levels_only_abstract` | was "identifies levels only" (abstract), paired with `levels_only_body` = "restrict every claim in this paper to levels" | **C-09** — re-pinned to "not a level and not monthly timing" by `66df169`; any further abstract edit (C-01/C-33/C-34/C-35/C-123/C-124) must re-check it |
| `ASSEMBLY_SPANS["ladder_fannie"]` (`:386`) | `"5.52\%, brackets the marginal below the $+4.3$ edge"` | **C-26** (state the Fannie comparison on one basis); the T8 calibration cell moves with it |
| `ASSEMBLY_SPANS["ladder_agestd"]` (`:385`) | `"floor read of 5.51\% implies a marginal near $+3.8$"` | **C-99** (print measured +3.7), **C-70** (adds a standardized read to the same sentence) |
| `ASSEMBLY_SPANS["posture_binding_layer"]` (`:406`) | §V.E's rule sentence, "the widest layer that does have a coverage property … the interval this paper quotes as binding" (comment records it as the ROUND-28 R1-W1/C3 branch (a) scope decision) | **C-20**, **C-24**, **C-17**, **C-05** |
| `ASSEMBLY_SPANS` `posture_lower_half`, `posture_retired_range_carries` | spans on the same `.tex:333` line as the "three things" sentence | **C-104** (drop the zero-exclusion clause); with `tests/test_assembled_corrections_gate.py` |
| `ABSTRACT_POSTURE["interval"]` (`:595`) + its ordering assert | `"The design bounds it between $+2.9$ and $+8.7$ points"` | **C-01**, **C-24**, **C-17**, **C-19**; with `tests/test_headline_posture_gate.py` |
| `tools/liveness_gates.py:4573` | `tex.count("$+2.9$ to $+8.7$") >= 4` | **C-17** (if the point/range posture changes), **C-20** (if a wider rung is promoted), **C-24** |
| `tools/liveness_gates.py:4576` | the literal `"open below $+4.3$"` | **C-70** (joins the standardized read to that clause), **C-84** |
| `tools/liveness_gates.py:4577` area + `tests/test_floor_ladder_gate.py` | ladder row spans `cr1_conventional`, `cr1_bell_mccaffrey`, `df_ownership`; also the T9 caption fragments | **C-20**, **C-105** (add to the note, never alter the pinned rows), **C-02** (caption), **C-72** (new rows) |
| `tools/liveness_gates.py:818–821` | **ordering** asserts on `tab:ladder` rows (not section order) | **C-20**, **C-72**, **C-100**; checked clear for **C-122** (no gate references `sec:discussion-policy`) |
| gate #103 `BUYBACK_BRACKET_SPANS["reversal_range"]` (`:~645`) + `tests/test_buyback_incidence_gate.py::test_each_span_removal_fails` | `"$-\$89.4$ to $-\$117.7$ billion"` | **C-75** (re-derived D halves the range) — the gate and its test must be **updated with** the new range, not bypassed |
| gate #71 (`:4061–4073`) `intro_para_carries_forcedness_and_flip` | a **paragraph-level co-occurrence**: the *first* paragraph containing `"$+\$61.2$ billion"` must also carry "forced rather than found" and `"$-\$99.9$ billion"`; `table1_disclosed` pins the exact T1 cell substring | **C-49** (band added byte-preserving **around** the pinned spans; first-mention ordering re-checked), **C-87** and **C-91** (splitting or relocating that paragraph breaks it unless the forcedness and -$99.9bn clauses move with it) |
| gate #106 `COUPON_CONVENTION_SPANS` (`:~710–724`) | `100.4` / `98.1` / `107.0` / `109.1` and `conversion_def` / `mixed_basis_label` at `.tex:697` | **C-63** (the surrounding sentence is edited; these literals must survive byte-identically). Checked clear for **C-108** (the pinned spans are at `.tex:697`, not `.tex:146`; "0.27" is unpinned) |
| gate #109 + 5 tests (**new**, `d22b265`) | the beta_1 sign relation between T3 and T7 | **C-13**/**C-14** (landed); any later change to `tab:lowband`'s printed cells or `eq:beta1` must move it |
| gate #94 (`:4666`) | "NO ABM COUNTERPART TO THE beta_1 = 0 NULL" | noted while checking **C-14**; unaffected, but do not confuse it with the new sign gate |
| `LETTER_CURRENT_LITERALS` (`:739`) | the letter's literal list, incl. `+270.4` / `-105.3` and `$+2.9$ to $+8.7$` | **C-66**, **C-17**, **C-88** |
| `"5.14"` (two occurrences in `tools/liveness_gates.py`) | the empirical-CPR comparator literal | **C-109** (basis labels at the eight 5.14% sites — preserve the literal where protected), **C-94** |
| abstract-scoped hedge spans (gate class 4) | the abstract's hedge clauses, incl. "(itself read from realized, partly behavioral turnover)" | **C-01**, **C-04**, **C-33**, **C-34**, **C-35**, **C-123**, **C-124** — treat the abstract as **one** edit at the end of the wording waves |
| `tests/test_elasticity_discipline_gate.py`, `tests/test_units_conventions.py` | beta_1 literals 0.0686 / 0.068571 / 0.069 / 0.0693 | **C-102** (P_q row), **C-13** |
| `tests/test_verdict_audit_gate.py` + render gate | `tab:pathadiag` row text; App. O ledger rows | **C-95**, **C-37**, **C-114** |
| `tests/test_render_gate.py` / `tools/render_gate.py` | the render-layer check the 108 source gates structurally cannot make (R31: ~919 off-sheet items across 9 pages) | **every structure condition** — C-87, C-88, C-89, C-90, C-91, C-93, C-122, and C-84/C-94/C-95 (float re-flow); re-run at **C-125** |
| the tests' hardcoded abstract word-count anchor + the response letter's claimed count | 248 -> 287 words (moved by `66df169`) | **C-125** (re-count after the last abstract edit), **C-33**, **C-123** |
| `tab:crossdesign` literals; the ABM_LEAD spans | whole-sentence pins in the ABM material | **C-88** (relocation only — the suite matches the whole `.tex` as one string, so a move is gate-safe and a deletion is not) |
| frozen-artifact SHA pins / manifest | `extension_risk_results.json`'s documentation field is inside a SHA-pinned replication object | **C-114** — prefer the App. A bullet; if the string is corrected instead, re-check the manifest pin and any gate hashing that file |
| the `must_not_change` ledger in `episode_confrontation_within_results.json` | `+4.20` / `[+3.59,+4.66]` / `+0.94` / `0.68` / `p=0.005` | **C-73**, **C-78** |

Standing rule that governs every relocation: `tools/liveness_gates.py` matches on the `.tex` as **one string**, so
moving text within the file is gate-safe while deleting it is not. Gate #71 is the one flagged exception — it binds a
**paragraph-level** property, so a split or relocation can break it even with every literal preserved.

---

## ALREADY SATISFIED IN THIS ROUND

| commit | canonical conditions satisfied | notes |
|---|---|---|
| **`66df169`** (Task 1, abstract) | **C-09** (self-refuting "levels only" replaced by "identifies a marginal, not a level and not monthly timing"; gate pin `levels_only_abstract` re-pinned) · **C-04** *at the abstract site only* (85.7% labelled form-conditional with the additive form's 35.6% printed beside it, condition front-loaded into the topic clause) · **C-11** (topic-clause form condition) · **C-10** (bounding claim qualified; unestimated seasoning ramp's +0.9 to +15.6 span named in the same clause) | Abstract 248 -> 287 words; the response letter's claimed count and the tests' hardcoded anchor moved with it. **Introduced C-01** (the clause now asserts the Webb interval *is* the widest coverage-bearing layer — false on the paper's own ladder) and left **C-33** (the $87.8bn/11.5% complement) still absent. Remaining C-04 sites (T1 row `.tex:78`, §VII.F, §VIII, §VI.B, §V.F) are open. |
| **`c2e505e`** (Task 2, form-fork basis) | **C-12** (one basis, named: "the central leg's standalone-scorer recovery falls from 100.4\% to 55.9\%") | The recommended standalone-standalone pair; consistent with the 44.7% null already on the line and with the neighbouring standalone 59.3%/52.0% anchors. Talk hazard only: 59.3 is also the 150-PSA *shared* null — do not let the two land in the same breath. |
| **`d22b265`** (Task 4, beta_1) | **C-13** (T3/T7 reconciliation) · **C-14** (the sign-agreement gate: **new gate #109 + 5 tests**) | Landed by harmonising `tab:lowband`'s nine cells to positive per `eq:beta1` **plus** a replicator note recording that `rothstein_beta1` returns the opposite sign. This is a different branch than the inventories recommended (keep the engine's printed sign + note); see **A-09** — confirm the replicator note carries the code's signed value, which is what the anti-condition protects. |
| **`7189c8e`** (Task 5, `docs/carroll_round_qa_prep.md`) | **C-16** (all Carroll-Round preparation deliverables: the 60-second form-fork answer, the pool-vs-book answer, the household-units slide, the $bn/month cap slide, the 15-minute route, and the standing "do not quote the Danish cash range" instruction) | Prep-layer only; the substantive dependencies remain open (C-06/C-64/C-07 for the pool slide, C-76 for the household slide, C-54 for the cap slide, C-75 before the Danish magnitudes are spoken). DA's pre-talk sequencing condition is discharged by the four Wave-1 landings plus **C-01**. |

Total: **8 canonical conditions SATISFIED** (C-04 partially — abstract site only; counted as SATISFIED-partial and
still listed as open at its remaining sites).

---

## COUNTS

**Canonical conditions: 133** (C-01 … C-133), collapsed from **236 source rows** across six inventories —
a merge ratio of **1.77 source rows per canonical condition** (236 -> 133; 103 rows absorbed by merging).
Counts below were extracted mechanically from this file's own field lines.

**By class** (133)
| class | n |
|---|---|
| WORDING | 74 |
| STRUCTURE | 20 |
| RUN | 15 |
| CHECK | 9 |
| REFERENCE | 8 |
| META | 7 |

**By severity** (133) — using the synthesis's arbitrated severity wherever it arbitrated
| severity | n |
|---|---|
| CRITICAL | 11 |
| MAJOR | 82 |
| MODERATE (arbitrated down from MAJOR) | 2 |
| MINOR | 35 |
| unrated (2 OPEN-UNARBITRATED + 1 process) | 3 |

**By verified status** (133)
| status | n |
|---|---|
| true | 94 |
| partly | 32 |
| partly/true (mixed limbs within one row) | 3 |
| OPEN-UNARBITRATED | 2 |
| OPEN | 1 |
| n/a (process) | 1 |

**By wave** (133)
| wave | n | content |
|---|---|---|
| 1 | 11 | pre-talk wording (4 landed + C-01, C-02, C-03, C-15 open) |
| 2 | 56 | remaining wording and posture decisions |
| 3 | 15 | runs |
| 4 | 8 | exhibits and tables |
| 5 | 25 | minor wording sweeps + references |
| 6 | 9 | compression, paragraph architecture, relocations |
| CLOSE | 1 | abstract re-count / file sync / render gate / editions |
| EUGENE | 8 | reserved — no agent action |

**CONSENSUS (3+ distinct raisers): 13** — C-02, C-04, C-08, C-10, C-16, C-17, C-23, C-68, C-75, C-76, C-87 (all five reviewers), C-126, C-130. (C-85's ten missing references are one deliverable raised by R2 and endorsed by the synthesis — two raisers, so it is not stamped CONSENSUS.)

**Already SATISFIED: 8 rows carry a SATISFIED mark** — 7 fully (C-09, C-10, C-11, C-12, C-13, C-14, C-16) and
1 partially (C-04, abstract site only; its five remaining sites are open).

**Reserved for Eugene: 8** — C-126 (retitle), C-127 (R2:M8 benchmark frequency), C-128 (realized-side boundary),
C-129 (anonymized master + Zenodo DOI), C-130 (length/venue scope), C-131 (register as a standalone note),
C-132 (Freddie loan-level parquet licensing), C-133 (the push).

**Anti-conditions: 20** (A-01 … A-20; the 10 pre-adjudicated plus 10 additional panel self-refutations, the last of
which bundles 11 separate verified mis-citations and inflated figures).

**Run inventory: 16 rows** (R-01 … R-16), of which **3 are blocked on inputs absent from this worktree**:
R-04 (external housing-activity data), R-09 (external existing-home-sales volume and mortgage-financed share),
R-12 (no committed interest-only-share source), plus **R-16 not executable here** (`cohort_month_panel_fannie.parquet`
and `fannie_quarters/` absent — take C-26's wording branch instead). Four more carry mandatory pre-committed
NOT_COMPUTABLE / INFEASIBLE landings (R-02, R-05, R-11, R-15).

---

## NOT CARRIED FORWARD

No source row was dropped. Every one of the 236 appears either in a canonical row's `source_rows`, in
`## ANTI-CONDITIONS`, or as a named correction carried inside a canonical row's `verified:` field. Two categories
deserve explicit note rather than a section of their own:

1. **Rows carried as constraints rather than as conditions.** C-R1-34 (the ABM's commit-addressability disclosure —
   R1 asks that it *stay*) is recorded as C-107 with "no change requested", so a compression pass cannot tidy it away.
   C-R1-27 and C-R1-11 are recorded as anti-conditions (A-19, A-18) because the manuscript defect they allege does not
   exist; their surviving substance is carried by C-26, C-27 and an optional positive statement at `.tex:433`.
2. **R3's own "not recorded as conditions" list** (nine score-cell criticisms in R3's Methodological Rigor and Evidence
   Sufficiency cells with no requested remedy, each of which R3 notes the paper already discloses) was read and is
   deliberately not turned into canonical rows. Every item is covered elsewhere: PCHIP propagation and the 31/5.9
   cluster count by C-02/C-20/C-72; the ABM's sign disagreement by C-66/C-88; Path A's indistinguishability by C-66;
   the un-propagated elasticity by C-25; the PSA sweep by C-05/C-08/C-24/C-28; the two high floor reads by
   C-02/C-03/C-84; the four clip zeros by C-127 (EUGENE); and the 51.0% coverage by C-39/C-67.

### Line-item accounting — source ids appearing in NO section

| inventory | rows | source ids not appearing anywhere in this file |
|---|---|---|
| `inventory_EIC.md` | 22 (C-EIC-01…22) | **none** |
| `inventory_R1.md` | 38 (C-R1-01…38) | **none** |
| `inventory_R2.md` | 50 (C-R2-01…50) | **none** |
| `inventory_R3.md` | 43 (C-R3-01…43) | **none** |
| `inventory_DA.md` | 34 (C-DA-01…34) | **none** |
| `inventory_SYNTH.md` | 49 (C-SY-01…49) | **none** |

All 236 source ids are placed. Verified mechanically against this file's full text (every id of the form
`C-EIC-NN`, `C-R1-NN`, `C-R2-NN`, `C-R3-NN`, `C-DA-NN`, `C-SY-NN` in the six declared ranges was found, and no
out-of-range id is referenced). Nine source ids are deliberately **cross-listed** in two canonical rows because one
synthesis row governs two different edits: C-SY-01 (C-05 wording leg / C-08 run leg), C-SY-33 (C-01 / C-125),
C-SY-39 (C-70 / C-71), C-SY-48 (C-85 / C-129), and C-R2-50 (C-16, with its substance in C-75).
