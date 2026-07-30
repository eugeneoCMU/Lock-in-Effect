# R32 condition inventory — DEVIL'S ADVOCATE (REVIEW3_v18_panel_2026-07-29.md lines 894–1078)

Verification sources used: `paper/v18/revised_paper_v18.tex` (worktree `agency-mbs-runoff-qt-424945`, HEAD a785f3d),
`hazard/data/{oos_identification,psa_level_sweep,floor_form_mixture,b5_joint_cell,attenuation_sensitivity,fannie_floor_read}_results.json`,
`tools/liveness_gates.py`, `tools/render_gate.py`, `hazard/literature_hazard.py`, `hazard/config.py`.
Table numbering confirmed from label order: T1 tab:headline, T3 tab:params, T5 tab:assembly, T6 tab:oosfloor,
T7 tab:lowband, T8 tab:uncertainty, T9 tab:ladder, T11 tab:bases, T12 tab:wal, T27 = Appendix O ledger (app:verdicts).
Section map confirmed: §III.B=sec:method-benchmark, §V.B=sec:pathb, §V.D=sec:patha, §V.E=sec:identification,
§VI.A=sec:discussion-fallout, §VI.B=sec:discussion-capdesign, §VI.D=sec:abm-danish, §VII.B=sec:robustness-benchmark,
§VII.F=sec:robustness-floor, §VIII=sec:conclusion, §VIII.A=sec:limitations.

---

### C-DA-01
raiser: DA
da_ref: §1 strongest counter-argument (closing sentence)
severity: inferred CRITICAL (it is the DA's summary of both CRITICALs)
class: WORDING
panel_lines: 908–916
condition: The headline should be restated as "nearer +1 to +11, concentrated low" rather than +5.6 inside [+2.9,+8.7].
location: abstract (.tex:31); tab:headline row 4 (.tex:79); §I (.tex:46)
verified: false — no committed pair supports (+1, +11). The nearest committed endpoints are the PSA convention span +0.9 to +15.6 (`psa_level_sweep_results.json` `ranges["4.991"] = {lo_pp 0.856, hi_pp 15.626}`), the form-conditional hull +3.5 to +13.1 (.tex:31), and the additive-form point +11.2 (`floor_form_mixture` 4.991|1|6.5 marginal_pp 11.207). +1 to +11 is a rhetorical rounding of the PSA span truncated at the top, and it CONTRADICTS the DA's own C1(a) proposal of +2.9 to +6.8 (line 929). Recording it so nobody implements two incompatible restatements.
fix: Do not implement as stated. If any interval restatement lands, it must be C-DA-02's or C-DA-05's, with its provenance named; the DA's §1 sentence carries no derivation and its two CRITICALs propose a narrower interval than it does.

### C-DA-02
raiser: DA
da_ref: C1(a)
severity: CRITICAL
class: WORDING
panel_lines: 924–929
condition: The headline must be restated as the interval implied by ALL available off-window reads — including the age-standardized 5.51% and Fannie 5.52% cells — approximately +2.9 to +6.8, with no interior point named.
location: abstract (.tex:31); tab:headline row 4 (.tex:79); §I (.tex:46); §V.E (.tex:323, 333); tab:assembly (.tex:345); §VIII (.tex:725)
verified: partly — (i) the reads exist and sit where the DA says: `oos_identification_results.json` `instrument1_oow_floor.legs.2018_rising_rate.anchor_grid` gives 4.695/4.991/5.334, and tab:oosfloor (.tex:365–367) prints the δ=6.5 marginals +6.8/+5.6/+4.3, so [+4.3,+6.8] is the defensible-range statement the DA attacks; the 5.51% and 5.52% reads are printed at .tex:92, 347, 348, 433. (ii) The proposed LOWER endpoint is not derivable from those reads: the age-standardized 5.51% floor implies "~+3.8" (.tex:347) and the Fannie 5.52% is quoted only as "below +4.3" (.tex:348) — an all-available-reads interval is therefore ~+3.8 to +6.8, not +2.9 to +6.8. The DA's +2.9 is the *composed* Ginnie×age-std cell (`b5_joint_cell_results.json` `overlay_agestd.primary.marginal_pp = 2.928`), a different object, and it numerically collides with the wild-$t$ lower endpoint +2.9 already printed as the binding interval's floor. Any edit must not let three distinct +2.9s (wild-$t$ endpoint, composed cell, DA's proposed interval floor) be read as one number.
fix: WORDING only, no run. If adopted, restate as "+3.8 to +6.8 across every available off-window read" (or +2.9 if and only if the composed b5 cell is explicitly named as the source, per C-DA-08) and drop or demote the named +5.6. Every quoting site above must move together, and gate #-pinned spans in `tools/liveness_gates.py` for the abstract and tab:headline must be re-pinned.

### C-DA-03
raiser: DA
da_ref: C1(b)
severity: CRITICAL
class: WORDING
panel_lines: 924–929
condition: §VII.F and the "Definitions used throughout" block must state that the clean 2018 leg contains no cohort-month aged ≥24, and that the age-transport error is therefore unpriced and signed against the headline.
location: §VII.F (.tex:711, 713); Definitions block (.tex:92); currently stated only in app:floormech (.tex:1314)
verified: partly — the artifact facts are exact: `oos_identification_results.json` `...2018_rising_rate.seasoning` has `age[0,12) = 3.776%` (505 cohort-months), `age[12,24) = 5.334%` (155), and 0 cohort-months in `age[24,36)`, `age[36,60)`, `age[60,10000)`; `contamination.mature_test_computable = false`, `verdict = "CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE"`, `ramp_rise_pp_12_vs_0 = 1.558`, `ramp_rise_is_psa_confounded = true`; the 137 cohort-months behind 4.991% must all sit in [12,24) since the ≥24 cell is empty. BUT the paper already states the non-computability and its reason in Appendix (.tex:1314: "Its mature-age seasoning test is *not computable*: the leg contains no out-of-the-money cohort-months at all past the twenty-four-month age cut"), and the Definitions block already concedes "the last two lines sit above the clean band, which is why the band's lower edge is the soft one" (.tex:92). So the missing content is narrower than the DA implies: the ≥24-emptiness is absent from §VII.F and from the Definitions block, and the words "unpriced" / "signed against the headline" appear nowhere for the age transport. FURTHER CAVEAT on the DA's *direction* premise: `fannie_floor_read_results.json` `books.freddie.in_window_deep_OTM_validation` reads 3.840% at age≥12 vs 3.909% at age≥24 (Fannie 3.864 vs 4.029) — the in-window age gradient on deep-OTM cohort-months is essentially FLAT (+0.07 to +0.17pp), so "turnover rises with seasoning" is supported by the 2018 leg's own PSA-confounded ramp and by contaminated pooled mature cells (Freddie 8.92%, Fannie 10.136% at age≥24, on 65/71 cohort-months) but NOT by the in-window population the floor is broadcast to.
fix: WORDING. Add the ≥24-emptiness sentence to §VII.F beside the age-standardization passage and one clause to the Definitions block. State the transport as unpriced; state its direction as *indicated* by the 2018 leg's PSA-confounded ramp and *not* corroborated by the in-window deep-OTM age contrast (both figures are already committed in `fannie_floor_read_results.json`), rather than asserting it flatly. Do not delete the existing appendix statement.

### C-DA-04
raiser: DA
da_ref: C1(c)
severity: CRITICAL
class: STRUCTURE
panel_lines: 924–929
condition: Table 6 (tab:oosfloor) must carry rows for the 5.51% age-standardized and 5.52% Fannie reads rather than confining them to a note.
location: tab:oosfloor (.tex:360–381)
verified: partly — tab:oosfloor's rows are 4.70/4.99/5.33 (defensible), 6.07/6.91 (refi-contaminated), 4.00/3.97 (in-sample), with no 5.51/5.52 row. But "confined to a note" is wrong: they are already table ROWS in tab:assembly (.tex:347–348), plus the Definitions block (.tex:92) and tab:uncertainty's note (.tex:433). Implementation constraint: tab:oosfloor has three δ columns (5.5/6.5/7.7) and only ONE committed marginal exists for each new read (~+3.8 for 5.51%; "below +4.3" for 5.52%), so full rows cannot be printed without inventing cells. Additional substantive caveat: the Fannie 5.522% is `out_of_window_2017_2019` `gap<=-0.0025_age>=12` on the POOLED 2017–2019 leg (its Freddie parity read of the identical cell is 5.185%, `comparison.difference_pp = 0.337`), i.e. it is a cross-agency read on the leg the same table labels refi-contaminated at gap≤0 — it is NOT a second age correction. The DA's "two independent corrections agree to 0.01pp" is therefore a coincidence across two different perturbations, and this is the load-bearing premise of C1's "the point is more likely wrong than both corrections" argument.
fix: STRUCTURE. Add the two reads as clearly-labelled rows with dashes in the uncommitted δ cells and a Status value distinguishing them ("indicative bound, 84% imputed weight" / "independent agency, pooled leg"), or add them as a stub block beneath the defensible rows. Whichever lands, the Fannie row must state that its leg is the pooled 2017–2019 one and that its Freddie parity is 5.185%, otherwise the table would assert an age correction the artifact does not support.

### C-DA-05
raiser: DA
da_ref: C2(a)
severity: CRITICAL
class: WORDING
panel_lines: 931–936
condition: The abstract's "The design bounds it between +2.9 and +8.7 points under its production floor form" must be rewritten so the main clause claims only what its parenthetical supports, and must name the unestimated baseline ramp's +0.9 to +15.6 span at the same calibration.
location: abstract (.tex:31, second paragraph)
verified: true — the abstract reads exactly as quoted, with the parenthetical "(the floor read's sampling error at my central elasticity; a wild-cluster interval on 31 clusters; the percentile read under-covers)" and no mention of the ramp. The artifact backs the DA verbatim: `psa_level_sweep_results.json` `ranges["4.991"] = {lo_pp 0.8560, hi_pp 15.6265, width_pp 14.7705}`, `comparison.floor_read_width_pp = 5.9268`, `comparison.psa_over_floor_read_at_headline = 2.4921`, `verdict = "PSA_WIDER"`. The DA's "under production floor form does not quarantine them" is also true: the sweep's cell 4.991|100|6.5 reproduces the production trapped_b 767.5264524465003 and marginal 42.608 bit-exactly, and `hazard/scaled_null_housing_activity.py:279` asserts `FLOOR_MODE == "max"` / `BASELINE_MODE == "psa"` for the same production convention. The body already carries the disclosure the abstract lacks (§V.E .tex:333: "Within the production form the widest disclosed layer is the baseline level: sweeping the seasoning ramp over 75 to 150 PSA … carries the marginal from +0.9 to +15.6 points at the off-window floor").
fix: WORDING. Rewrite the abstract clause along the DA's line, reusing the §V.E literals (+0.9 to +15.6; "a range over a convention I did not estimate") so no new number enters. Check the abstract-scoped hedge-span gates in `tools/liveness_gates.py` (gate class 4) before and after — the abstract is gate-pinned.

### C-DA-06
raiser: DA
da_ref: C2(b)
severity: CRITICAL
class: WORDING
panel_lines: 931–936
condition: "Binding layer" must be demoted to "binding among the layers with a coverage property" (or equivalent) at every site where it appears without that qualifier.
location: 10 sites — .tex:46 (§I), 66 (tab:headline caption), 79 (tab:headline row 4), 417 (§V.E, already qualified), 433 (tab:uncertainty headline row), 440 (tab:uncertainty notes), 444 (tab:ladder caption), 457 (tab:ladder row), 713 (§VII.F), 1412 (Appendix O ledger)
verified: partly — "binding layer" occurs 10×; exactly ONE site is already qualified: .tex:417 reads "binding among the layers with a coverage property; the unestimated baseline-level convention spans wider (run psa_level_sweep …)". .tex:433 carries a partial qualifier ("a sampling interval on the floor read alone rather than on the elasticity"). The other 8 are unqualified. So the condition is real but its scope is 8–9 sites, not 10, and the qualifying phrase already exists verbatim in the manuscript and can be reused.
fix: WORDING. Propagate the .tex:417 formulation. Note that .tex:1412 (Appendix O ledger row) narrates history — "the wild-cluster interval became the binding layer (against the headline)" — and should be left as a historical record or qualified separately, not rewritten as a claim.

### C-DA-07
raiser: DA
da_ref: C2(c)
severity: CRITICAL
class: RUN
panel_lines: 936
condition: The paired legs must be re-run with the baseline hazard $h_0$ set to Path A's ESTIMATED seasoning spline instead of the 100 PSA convention, and the marginal reported there — converting the widest disclosed layer from a convention into an estimate.
location: §V.E / §VII.F reporting sites; new run
verified: partly — Path A does fit the spline the DA names: tab:specbox (.tex:204) reads "Age profile & seasoning spline, knots $\{12,24,36,60,84,120\}$ months (seven columns) & 100 PSA ramp to 6% CPR at month 30", and .tex:1033 confirms $f(a_{s,t})$ is Path A's loan-age seasoning spline. BUT "this is one run" is FALSE as a code claim: `hazard/literature_hazard.py:73` `baseline_hazard(age_months, mode)` supports only `"psa"` and `"weibull"` (`hazard/config.py:34` `BASELINE_MODE = "psa" | "weibull"`), and `h0_psa` is a two-parameter ramp — there is no tabulated-profile or spline mode. The run also requires transporting a stratum-month log-rate spline estimated with 295 stratum fixed effects into a loan-level monthly hazard, which is a new transport with its own assumptions (and Path A is declared non-corroborating at .tex:741 and in §V.D).
fix: RUN, but scope it honestly before committing a spec: it needs (a) a new `BASELINE_MODE` accepting a tabulated age→CPR profile, (b) an explicit rule for mapping Path A's spline onto that profile and normalizing its level (Path A's own level is not the production level), (c) parity gates showing the psa-mode path is bit-unchanged. Existing machinery that *is* one run and prices the same dimension: `psa_level_sweep` (level scaling of the same ramp) and `scaled_null_housing_activity` (root-finding on the same scale factor, φ*=0.754). If (a)–(c) are judged out of scope, the condition should be recorded infeasible-this-round with the ramp span disclosed in the abstract per C-DA-05 as the honest alternative.

### C-DA-08
raiser: DA
da_ref: M1
severity: MAJOR
class: WORDING
panel_lines: 940–944
condition: Either the measured composed cell +2.9 enters Table 1 and the abstract as the assembly's operative lower member, or the named interior point +5.6 is dropped entirely and the range reported alone. "Neither" is not allowed.
location: tab:headline row 4 (.tex:79); abstract (.tex:31); §V.E seventh qualification (.tex:333); tab:assembly (.tex:345)
verified: partly — the refusal-to-compose sentence is verbatim at .tex:333 ("corrections here do not compose additively, and a composed figure would carry a precision nothing in the design supports"), and +5.6 is named "mid-grid anchor" at .tex:46, 79, 345. `b5_joint_cell_results.json` `overlay_agestd.primary.marginal_pp = 2.928` with `adjudication.interaction_vs_proportional_pp = 0.00023` and `verdict = "LANDS_AS_COMPOSED_LOWER_MEMBER"`. BUT the paper does NOT hide it: .tex:333 already reports "the joint cell has now been run under a pre-committed landing rule (run b5_joint_cell) and measures +2.9 points, an interaction within 0.1 of proportional", and tab:uncertainty's note repeats "composed +2.9, within 0.1 of proportional" (.tex:433). So the gap is confined to Table 1 and the abstract. One mis-citation: the DA's "`measured_minus_implied_pp = -0.129` against the proportional projection" is the key from `conventional_agestd` (vs `ladder_implied_pp = 3.8`), not from `overlay_agestd.primary`; the overlay's proportional deviation is 0.00023pp.
fix: WORDING. Promote the committed +2.9 composed cell into tab:headline row 4 and the abstract as the assembly's lower member (literal already exists, no run), or delete the interior +5.6 from both. Do NOT delete the §V.E refusal-to-compose reasoning; the honest statement is that one composition was measured and lands at the bottom.

### C-DA-09
raiser: DA
da_ref: M2
severity: MAJOR
class: WORDING
panel_lines: 946–950
condition: The anchor rule must be stated explicitly ex ante ("median of the three pre-committed depth cuts"), with the five-cut median shown as a robustness line — or the interior point abandoned per M1.
location: §VII.F (.tex:713); tab:oosfloor (.tex:365–367); tab:assembly row 2 (.tex:345)
verified: true — .tex:713 already reports the two extra reads ("4.722% at gap ≤ −0.75 points, 4.869% at gap ≤ −1 point") and states that the clean band stays exactly [4.695%, 5.334%], but nowhere states the selection rule that makes 4.991% the anchor. The DA's arithmetic holds: median{4.695, 4.722, 4.869, 4.991, 5.334} = 4.869, and tab:oosfloor's own δ=6.5 column (4.70→+6.8, 4.99→+5.6, 5.33→+4.3) puts 4.869 at roughly +6.0 by interpolation. The paper calls 4.991 a "mid-grid anchor … an anchor convention rather than a central tendency" (.tex:79), which concedes convention but not the counting rule.
fix: WORDING. State the rule in §VII.F ("the median of the three pre-committed depth cuts; on the five-read extension the median is 4.869%, implying roughly +6.0 points") — both endpoints are committed literals, so no run. If C-DA-08's second limb (drop the interior point) lands instead, this condition is discharged by it.

### C-DA-10
raiser: DA
da_ref: M3 (first limb)
severity: MAJOR
class: WORDING
panel_lines: 952–956
condition: Table 3's and Table 7's opposite-signed printings of β₁ must be reconciled — a reconciling note naming the convention, or harmonized signs.
location: tab:params (.tex:244, `$\beta_1$ (central) & $0.069$`); tab:lowband (.tex:400–405, e.g. `6.50 & $-0.0686$` under a `$\beta_1$` column header); eq:beta1 (.tex:228–230); §V.B (.tex:231)
verified: partly — the two printings and the missing reconciliation are real and exactly where the DA says. But the DA's *first* proposed remedy is wrong and is an adjudicated anti-condition: eq:beta1 (.tex:228) carries a LEADING MINUS, so β₁ = +0.0686 is correct for tab:params and for §V.B's "the *positive* β₁ of (3)", while `hazard/literature_hazard.py:32` `rothstein_beta1` omits that minus and returns −0.06857052676484808 — the value tab:lowband prints and every artifact records (`psa_level_sweep_results.json` `"beta1": -0.06857052676484808`). Flipping tab:lowband's printed signs would make the table contradict the production code. The DA's supporting history checks out too: Appendix (.tex:1338) records the prior rate-gap-units defect in this same coefficient.
fix: WORDING, harmonisation-plus-note only. Keep tab:lowband's printed values as the engine's, add one reconciling clause naming the two conventions (eq:beta1's suppression-positive sign vs the code's gap-sign convention) and a replicator note pointing at `rothstein_beta1`. Do not flip signs in either table.

### C-DA-11
raiser: DA
da_ref: M3 (second limb)
severity: MAJOR
class: CHECK
panel_lines: 956
condition: A liveness gate must assert that Table 3's and Table 7's β₁ at δ = 6.5% agree in sign (or, per C-DA-10, that both agree with the stated convention).
location: `tools/liveness_gates.py`
verified: true — no such gate exists. The only β₁ mention in the gate file is gate #94 at line 4666 ("NO ABM COUNTERPART TO THE beta_1 = 0 NULL"), which tests a different string; the suite's numbering runs to #108 and none pins β₁ sign agreement between tab:params and tab:lowband.
fix: CHECK. Add a gate that reads both printed literals and asserts the documented relation (equal magnitude, sign related by the named convention), rather than naive sign equality — naive equality would enforce the wrong fix from C-DA-10. Read-only for the manuscript; new gate + test.

### C-DA-12
raiser: DA
da_ref: M4
severity: MAJOR
class: WORDING
panel_lines: 958–962
condition: "Together with the monotone response across the Liebersohn–Rothstein band" must be struck from the identified-content sentence (and its parallel in §V.B), since monotonicity is forced by the same composition-of-monotone-maps argument that retires the 27-cell positivity; the curve stays as a wiring check.
location: §V.E first qualification (.tex:323); §V.B (.tex:277); also §V.F/cross-design parallels at .tex:526 (two sites)
verified: true — .tex:323 reads "the identified content is the marginal's \emph{bounded range}, together with the monotone response across the Liebersohn--Rothstein band, and neither its point magnitude nor its sign"; the parallel constructions are at .tex:277 ("the bounded interval the calibration box implies and the monotone response across that band reported below") and .tex:526 (×2, "the band's monotone response"). The forcing argument is structural: eq:beta1 is monotone in δ and eq:pathB's hazard is monotone in β₁ (`prepay_hazard` in `hazard/literature_hazard.py` is exp-linear in β₁·gap), and the paper already demotes positivity on exactly that ground at .tex:323 ("its positivity … verifies the specification rather than identifying the mechanism").
fix: WORDING. Strike the clause at all four sites and retain tab:lowband as a wiring/consistency check, mirroring the sentence already used for positivity. Zero numeric change; check any gate-pinned span covering .tex:323 first.

### C-DA-13
raiser: DA
da_ref: M5
severity: MAJOR
class: STRUCTURE
panel_lines: 964–968
condition: The survival-selection attenuation row must either enter Table 5's assembly with its θ grid displayed, or the paper must state a rule for what qualifies as a correction that this row fails while the Ginnie overlay passes.
location: tab:assembly (.tex:338–352); tab:uncertainty note (.tex:433); §V.B transports (.tex:219–231); Appendix O ledger (.tex:1424)
verified: true — the artifact is exactly as described: `attenuation_sensitivity_results.json` `selection_identity` gives S = 40234/75000 = 0.53645, `a_grid = [1, 0.8558, 0.7324, 0.5365]`, cells at floor 4.991 give marginal_pp 5.5716/5.0955/4.6177/3.7037, and the spec string contains verbatim "Direction SIGNED ex ante: a<1, the marginal falls, a DOWNWARD member." The exclusion rationale is verbatim in tab:uncertainty's note (.tex:433): "a transport sensitivity on the imported coefficient, kept out of the assembly on that ground". The row is absent from tab:assembly. (The 40,234 figure here is the artifact's survival count, quoted from .tex:275/.tex:219 — the DA does not repeat the separate "40,234 active" anti-condition.)
fix: STRUCTURE. Either add an attenuation row to tab:assembly displaying +5.1/+4.6/+3.7 at θ = 0.25/0.5/1 (all committed literals; note θ is not estimable, per the artifact's `free_parameter_note`), or add one sentence stating the inclusion rule and showing the Ginnie overlay satisfies it. No run.

### C-DA-14
raiser: DA
da_ref: M6
severity: MAJOR
class: WORDING
panel_lines: 970–974
condition: Pick one: either the Ginnie and vintage overlays are corrections (+4.4 / +3.7 enter the assembly as such and the headline moves), or the estimand is the conventional in-window sub-book (in which case §III.B's 51.0% coverage becomes a definition, the benchmark denominator is re-scoped, and every recovery percentage restates).
location: tab:assembly rows 3–4 (.tex:346); Appendix O ledger row (.tex:1424); §V.B (.tex:219–231, "extrapolated to those segments as-is"); §III.B (.tex:150)
verified: true — .tex:346 prints both rows verbatim as "change of estimand (re-scoping onto the conventional sub-book), not a correction" and "change of estimand (re-scoping onto the in-window-vintage share), not a correction (run vintage\_overlay)", and the ledger at .tex:1424 confirms the relabelling was a post-run adjudication ("landed as a change of estimand --- the Ginnie row is relabelled the same way … (neutral)"). The 20.4% Ginnie share is at .tex:52 and .tex:269.
verified-note: the DA's second limb is a large restatement (denominator + every recovery percentage), not a wording tweak.
fix: WORDING for limb 1 (relabel the two rows as corrections and let the assembly's lower half carry them), or a full restatement for limb 2. Limb 1 costs no run; limb 2 touches the benchmark denominator and should not be attempted without a scope decision. State whichever rule is adopted once, in §V.B, and make tab:assembly and the ledger row agree with it.

### C-DA-15
raiser: DA
da_ref: M7
severity: MAJOR
class: WORDING
panel_lines: 976–980
condition: Appendix O ¶1 must state the gates' domain explicitly — that they verify manuscript literals against committed artifacts, cannot test an artifact's premise, and that one defect class they structurally could not see (off-sheet rendering) survived 108 of them.
location: Appendix O ¶1 (.tex:1395)
verified: true — every premise checks out. `tools/liveness_gates.py` docstring lines 5–20 declare exactly four gate classes (zero-count greps, exactly-one greps, manuscript-vs-manifest cross-checks, abstract-scoped hedge spans), all reading the .tex and frozen artifacts; the suite numbers to #108. `tools/render_gate.py` docstring lines 3–9 read "the check the 108 source gates structurally cannot make … ~919 text items across 9 pages sat OUTSIDE the physical sheet (the worst page carried 302 items of the Appendix O adjudication ledger more than a full page below the bottom margin)". Appendix O ¶1 currently says "A green gate suite is therefore not self-certifying, and this table exists so the judgment itself can be audited" — the self-certification point is present; the DOMAIN statement and the off-sheet episode are absent. (Unverifiable side-figure: the DA's "479 tests"; `tests/*.py` defines 293 `def test_` functions and the R31 commit message claims 495 collected — do not print a test count.)
fix: WORDING. Add the DA's sentence, sourced to the two docstrings. This is the one condition in the report that strengthens the paper's credibility while conceding; it costs no number.

### C-DA-16
raiser: DA
da_ref: M8
severity: MAJOR
class: STRUCTURE
panel_lines: 982–986
condition: §V.B must be split at its five natural seams (specification / floor semantics / elasticity import and its three transports / aggregation bounds / ablations), and the competing-risks taxonomy mapping moved to Appendix E.
location: §V.B (.tex:219–231, the paragraph beginning "The first hazard path brings competing risks"); §V.E (.tex:319–323); app:ridge (.tex:1099–1100); §V.B aggregation (.tex:269)
verified: true — measured on the current .tex, paragraph 219–231 is 14,720 characters (DA: 14,732), §V.E's 319–323 is 11,308 (DA: 11,312), the app:ridge paragraph 1099–1100 is 10,695 (DA's "Appendix G's 10,696"), and the aggregation paragraph at 269 is 8,051 exactly (DA: 8,051). The named contents are all inside 219–231: eq:pathB, eq:default, eq:beta1, floor semantics, the moving-share transport, ZIP-to-loan aggregation, survival selection, the putter2007/fine1999/meir2025 competing-risks taxonomy, and both ablations. The paper's own reading map (.tex:94) does direct a referee to §V.B first. The 139pp figure matches the R31 commit's build.
fix: STRUCTURE. Split at the five seams; move the competing-risks taxonomy block (from "In the taxonomy of standard competing-risks formulations" to "settle to simulated SOMA cash flow") to the appendix. Text-preserving only — this paragraph contains many gate-pinned spans and every literal must survive byte-identically; verify against `tools/liveness_gates.py` and re-run `tools/render_gate.py` afterwards, since re-flowed floats are what caused the R31 off-sheet defect.

### C-DA-17
raiser: DA
da_ref: m1
severity: MINOR
class: WORDING
panel_lines: 990–992
condition: The title should be re-cut to signal decomposition rather than a causal pairing, e.g. "Decomposing the Federal Reserve's Quantitative Tightening Shortfall: Mortgage Lock-In and the Mechanical Baseline".
location: .tex:24 `\title{Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall}`; abstract sentence 2 (.tex:31); §III.B (.tex:150)
verified: true — the title is verbatim as quoted, and §III.B's disclaimer is verbatim at .tex:150 ("a shortfall against the MBS cap is not by itself evidence that a stated policy objective was missed. The Committee's operating object was the aggregate securities portfolio's decline … nothing in this paper shows that reserves or the aggregate path came in off the intended course").
fix: WORDING, but note a hard constraint: `tools/liveness_gates.py` gate class 2 pins "the ratified title" as an exactly-one grep, so a retitle requires re-pinning that gate, the bundle/editions, and every filename-adjacent reference. Weigh against the Carroll Round deadline; this is the highest-cost MINOR in the report.

### C-DA-18
raiser: DA
da_ref: m2
severity: MINOR
class: REFERENCE
panel_lines: 994–997
condition: The COD-income override of Berger et al.'s 22%/15% U.S. counterfactual must cite the implementing regulation (Treas. Reg. §1.61-12(c)) and address §108(a)(1)(B)/(E), and be presented as a directional bracket rather than a correction.
location: §VI.D (.tex:586, the parenthetical beginning "Under U.S. tax treatment (a 22\% mortgage-interest deduction and a 15\% capital-gains tax on the discount, per Berger et al.'s own counterfactual --- a characterization U.S. law does not support: a discount extinguishment is cancellation-of-debt income at ordinary rates, IRC \S 61(a)(11) …")
verified: true — the parenthetical is verbatim at .tex:586 and asserts rather than brackets ("both corrections push the U.S.-transplant channel \emph{below} Berger et al.'s already-small estimate"). Neither "1.61-12" nor "\S 108" occurs anywhere in the .tex (grep count 0 for both), so the regulation and the exclusions are genuinely absent.
fix: REFERENCE + WORDING. Add the regulation cite and a clause on why §108(a)(1)(B)/(E) are unlikely to bind in a rate-driven rather than value- or insolvency-driven discount, and soften "a characterization U.S. law does not support" to a bracket. This is a legal-judgment condition, not a technical one: no artifact speaks to it, so it is satisfied by a defensible citation, not by a number.

### C-DA-19
raiser: DA
da_ref: m3 (first limb)
severity: MINOR
class: WORDING
panel_lines: 999–1001
condition: The abstract — "a single paragraph, 248 words, verified" — should be broken into two paragraphs at "What lock-in itself adds…".
location: .tex:31
verified: false — ADJUDICATED ANTI-CONDITION #2, confirmed independently here. Line 31 is 1,553 characters and contains an explicit `\par` at character offset 706, immediately before "What lock-in itself adds is a range rather than a number." The abstract is already TWO paragraphs and the break already sits at exactly the seam the DA names; the word count (248 by whitespace split, ~250 excluding LaTeX tokens) is the only half-true part. Implementing the fix as written would insert a duplicate break.
fix: Do not implement. Record as a panel error. The DA's "(single paragraph, 248 words, verified)" annotation shows the check was performed against the `.md` edition, where `\par` does not survive as a visible break — worth noting when other panel claims cite line 31.

### C-DA-20
raiser: DA
da_ref: m3 (second limb)
severity: MINOR
class: WORDING
panel_lines: 1001
condition: The wild-cluster / percentile detail should move out of the abstract into Table 1's note.
location: abstract (.tex:31, the parenthetical "(the floor read's sampling error at my central elasticity; a wild-cluster interval on 31 clusters; the percentile read under-covers)"); tab:headline note a (.tex:79 tnote)
verified: true — the parenthetical is present in the abstract as quoted, and tab:headline row 4 already carries the same content in its cell/note ("floor-read wild-cluster bootstrap-$t$ $[+2.9, +8.7]$, the binding layer (31 clusters; percentile read $[+3.0, +8.0]$, under-covering; the corrected ladder and its degrees of freedom are Table~\ref{tab:ladder})"), so the abstract's version is duplicative and the destination already exists.
fix: WORDING. Delete the abstract parenthetical's inference-machinery detail and let tab:headline's note carry it. CONFLICT to resolve first: C-DA-05 requires the abstract's main clause to gain the ramp-span qualifier — the two edits touch the same sentence, so sequence them as one edit, and keep whatever the abstract-scoped hedge-span gates (class 4) require inside the abstract.

### C-DA-21
raiser: DA
da_ref: A1
severity: inferred CRITICAL (the DA calls it "the cleanest alternative account of every number in §V.E")
class: RUN
panel_lines: 1007
condition: The paper must confront the account under which the marginal is a censoring geometry rather than a behavioral channel — floor-bind share moving 0.947 → 0.181 as the ramp goes 75 → 150 PSA while the marginal moves +0.9 → +15.6 in lockstep — by re-running with Path A's estimated seasoning spline as $h_0$.
location: §V.E (.tex:323, 333); §VII.F (.tex:709–713)
verified: partly — the artifact confirms the lockstep exactly: `psa_level_sweep_results.json` cells 4.991|{75,100,125,150}|6.5 give `floor_bind_share` 0.9469 / 0.6882 / 0.3657 / 0.1808 with marginals 6.55 / 42.61 / 87.33 / 119.50 $bn (0.856 / 5.572 / 11.419 / 15.626 pp). The paper already names the mechanism ("raising the floor is what crowds the elasticity out", .tex:333, with the 68.8% vs 36.3% bind shares printed) and already diagnoses the max form's floor-dependence as "censoring-driven rather than evidence about the elasticity" (.tex:231). So the *statement* is largely present; what is absent is the estimated-$h_0$ test. THE RUN IS THE SAME RUN AS C-DA-07 — do not spec it twice.
fix: RUN (identical to C-DA-07, same feasibility caveats: `baseline_hazard` has no spline mode). Separable WORDING limb that needs no run: state in §V.E that under the censoring-geometry reading the marginal's magnitude is a joint function of floor level and ramp, and that the design cannot separate them, citing the bind-share/marginal lockstep already in the artifact.

### C-DA-22
raiser: DA
da_ref: A2
severity: inferred MAJOR
class: RUN
panel_lines: 1009
condition: The episode gradient must be re-run within narrow age bands (e.g. 12-month strata) rather than past a single age cut, and the age-stratified gradient reported — otherwise the paper's only realized-data lock-in exhibit may be a seasoning artifact.
location: §V.D (.tex:315); run index entry for `episode_confrontation_within` (.tex:841)
verified: true — .tex:315 prints the raw gradient +4.20 CPR points (95% CI [+3.59,+4.66], permutation p = 0.005), the composition-standardized +3.44 and the exact decomposition "+0.77 of the raw +4.20 to composition and +3.43 to differences within common cells (run episode\_confrontation\_within)", against "the production hazard's implied +0.94" — so the DA's 4.5× excess is 4.20/0.94 ✓. Crucially the standardization holds vintage × FICO × LTV and NOT age, and the same sentence lists "residual seasoning past the age cut" among the confounds it leaves open. Coupon/age collinearity in a closed 2017–2021 book is therefore untested in the dimension that matters.
fix: RUN. Re-execute the existing `episode_confrontation_within` machinery (`hazard/episode_confrontation_within.py`, already does exact within-cell decomposition on the cohort-month panel) with loan age added to the standardization cells as 12-month strata. Spec the landing rule before running: the gradient may collapse, and per the round's rules that result lands. No new data — `hazard/data/cohort_month_panel.parquet` carries mean_loan_age (the script already reads it row-wise, per its header at line 90).

### C-DA-23
raiser: DA
da_ref: A3
severity: inferred MAJOR
class: REFERENCE
panel_lines: 1011
condition: The housing-supply / inventory literature must be cited explicitly in §VIII.A as an unmodelled competing channel with its sign stated — an inventory-driven turnover collapse is observationally equivalent to lock-in at the aggregate cash-flow level, and it is the one unpriced channel that biases the marginal DOWN.
location: §VIII.A limitations (.tex:733–752); §I (.tex:56); tab:assembly row (.tex:349); §V.E (.tex:333)
verified: partly — §I does mention "historic housing inventory shortages" once (.tex:56) and §VIII.A contains no housing-supply or inventory limitation at all (read in full: sample scale, data, model, status — none names it). The φ*=0.754 machinery is as described: .tex:333 and .tex:349 carry the Aladangady-anchored `scaled_null_housing_activity` root and its +0.9-point marginal, labelled "upward-bias entry". BUT "never returns" is not exact: inventory enters the ABM's friction calibration through FRED Active Listing Count (ACTLISCOUUS) shortfall against a 2017–2019 baseline (.tex:919, app sec:method-frictions) — a search-friction scaler, not a competing explanation for the hazard-path marginal. The DA's sign claim (a floor read on normal-inventory 2018 cohorts is too high for a low-inventory window, biasing the marginal down) is an argument, not a measured result, and nothing in the artifacts prices it.
fix: REFERENCE + WORDING, no run. Add a §VIII.A limitation naming the housing-supply channel, citing aladangady2024 (already in the bib and used at .tex:102/333) plus at least one supply-side source, stating the sign as argued-not-measured, and cross-referencing both the existing ACTLISCOUUS friction scaler and the φ*=0.754 run so the paper is not read as ignoring inventory entirely.

### C-DA-24
raiser: DA
da_ref: A4
severity: inferred MAJOR
class: WORDING
panel_lines: 1013
condition: The paper should stop treating "no estimator's detrended co-movement is distinguishable from zero" as a shared estimator failure and consider that the empirical monthly series may not be a behavioral object at all — a servicer/remittance-mechanics account — which would retire the timing question rather than leave it open.
location: §VI.A (.tex:528, 532); §VIII (.tex:725); §VIII.A (.tex:752, "the path-level timing question remains open for every estimator"); §VII.B; Appendix N
verified: partly — the concessions the DA leans on are verbatim: "no servicer channel beyond that pipeline is modeled at all" appears three times (.tex:528, 532, 725), and §VIII.A closes with "the path-level timing question remains open for every estimator" (.tex:752). .tex:186 already floats a near-neighbour of the DA's account ("the binding constraints on the empirical prepayment path lie at least partly outside the household decision function: in loan-level heterogeneity, servicer pipeline dynamics, and cohort-level path dependence"). Both supporting figures also check out: §VII.B (.tex:633–636) carries the settlement-aligned benchmark of $722bn with the −5.5% re-basing figure (run `settlement_months_benchmark`), and the four exact-zero months (June 2022, Feb 2023, Apr 2024, Sep 2025) are traced to the non-negativity clip at .tex:137, 275, 526, 833 and 1356 (run `h1_zero_months_diagnosis`). ONE imprecision: the DA says the zero months "flip the frozen timing rule" — .tex:1356 says the rule PASSED and that the author claims nothing from the pass because five post-hoc diagnostics show it cannot discriminate. Do not restate it as a flip.
fix: WORDING, no run. Recast the timing framing in §VIII.A (and the §VI.A residual passage) to name the reporting-and-remittance account as a candidate under which the monthly series is not a behavioral object, so the open timing question is stated as possibly ill-posed rather than as a shared failure. Reuse .tex:186's existing sentence as the anchor.

### C-DA-25
raiser: DA
da_ref: A5 (first limb)
severity: inferred MAJOR
class: WORDING
panel_lines: 1015
condition: §VI.D must state that the Danish magnitude inherits every conditionality the marginal has — including the PSA convention and the floor's age transport — because it is the same object measured on a second accounting leg, so the exercise adds no independent information about the payoff rule.
location: §VI.D (.tex:590)
verified: true — the paper's own sentence supplies the DA's premise: "the rule-only Danish counterfactual and the paper's lock-in contribution at the in-sample calibration point are one object measured on two accounting legs (+$61.2 billion here … +$70.3 billion as the U.S.-leg marginal)" (.tex:590), together with the sign-forcing concession in the same line ("99.53% of exposure below the window-minimum market rate … the hazard is monotone in the gap … it could not have come out otherwise"). What is absent is the explicit inheritance statement for the PSA convention and the age transport.
fix: WORDING, no run. One clause in §VI.D. Watch the known trap that the $61.2B Danish equality holds against the demoted in-sample point, not the headline off-window one — the inheritance sentence must not re-assert that equality at the headline calibration.

### C-DA-26
raiser: DA
da_ref: A5 (second limb)
severity: inferred MAJOR
class: RUN
panel_lines: 1015
condition: If the Danish claim is institutional, the transplant must change something the marginal does not already encode; the interest-only share — which §VI.D concedes would move the shortfall in the opposite direction — is the obvious candidate and is not run.
location: §VI.D (.tex:590)
verified: true — the concession is verbatim at .tex:590 ("in particular the large interest-only share, which would cut scheduled amortization, the null's largest component, and so move the shortfall in the opposite direction from the payoff rule. Each omission is a held-fixed feature of the U.S. leg, not a measured invariance"), and no interest-only run exists in `hazard/data/` (danish_* artifacts cover us_intercept, refi_finegrid, offwindow_floor, discount_bound, external_validation, curtailment scaling — none an IO-share variant).
fix: RUN. Score a Danish leg with an interest-only share applied to scheduled amortization on both legs, spec-before-run with the direction signed ex ante (opposite to the payoff rule) and a landing rule fixed in advance. Feasibility note: this touches the amortization path, not the hazard, so it does not need the C-DA-07 baseline machinery; but it does need a defensible IO-share input, which is an imported institutional parameter with no committed source in this repo — if none can be sourced, record infeasible and let the existing concession stand.

### C-DA-27
raiser: DA
da_ref: S1
severity: inferred MAJOR
class: RUN
panel_lines: 1021
condition: The implied count of suppressed moves should be computed and reported, giving the household mobility cost a magnitude beside the $42.6bn — the design already has 75,000 loans with rate gaps and the imported mobility elasticity.
location: §VI.A (.tex:542)
verified: true — §VI.A is as described: "The welfare-relevant objects are the constrained moves themselves, whose fiscal image is the lock-in marginal (+$42.6 billion of trapped roll-off at the headline off-window floor, +$70.3 billion at the in-sample calibration point), and the forgone labor-reallocation gains this literature identifies, which my accounting framework does not measure" (.tex:542). The withdrawn Hsieh–Moretti point estimate is the `hsieh2019` cite (references.bib:173) used in that paragraph. Every dollar figure in the paper is a central-bank cash-flow figure, as the DA says.
fix: RUN, but the cheapest kind: closed-form arithmetic on committed inputs (the 75k sample's gaps, `rothstein_beta1(0.065)`, the paired central/null hazard paths), not a new microsimulation — the suppressed-move count is the difference in cumulative move-hazard between the central and β₁=0 legs. Spec the estimand precisely before computing (moves vs prepayments: the hazard is total prepayment and the design has no move/refi split, per .tex:231 — so the honest output is a bound, not a count). If the split makes it uninterpretable, record infeasible with that reason; do NOT print a move count that silently treats prepayment as moving.

### C-DA-28
raiser: DA
da_ref: S2
severity: inferred MAJOR
class: WORDING
panel_lines: 1023
condition: §VI.B must open with §III.B's standing concession (the Committee's operating object was the aggregate portfolio; nothing shows the aggregate path came in off course) and state what the composition shortfall cost that the aggregate path did not — the duration extension of §VI.A.
location: §VI.B (.tex:544, sec:discussion-capdesign); §III.B (.tex:150)
verified: true — the concession is verbatim at .tex:150 and sits at the end of a very long paragraph (line 150 is 6,640 characters, consistent with the DA's "buried … 6,600-character paragraph"), and §VI.B (the cap-design arithmetic subsection) opens on the arithmetic without restating it. The duration object exists and is quantified (tab:wal, .tex:548–562, WAL 14.7 → 12.6 years scheduled-only vs 9.4 → 8.5 empirical).
fix: WORDING, no run. One opening sentence in §VI.B carrying the §III.B concession forward, plus a pointer to the WAL/duration figures as the policy object the composition shortfall actually moves.

### C-DA-29
raiser: DA
da_ref: S3
severity: inferred MAJOR
class: WORDING
panel_lines: 1025
condition: §VIII must state explicitly that the investor-side cost of the Danish transplant is unpriced in this design, so the "TBA liquidity premium is the binding constraint" claim is an argument from the literature rather than a result.
location: §VIII (.tex:731); §VIII.A (.tex:741)
verified: true — .tex:731 reads "The binding constraint against adopting such a rule is therefore not a mobility--cash-flow trade-off but the TBA liquidity premium described above", resting on cited work; nothing in the paper prices a series-level call, the hedging-cost shift, or originator warehousing. §VIII.A's nearest existing statement is narrower — the transplant "does not estimate how Danish institutional frictions would themselves migrate" (.tex:741) — and does not name the investor side.
fix: WORDING, no run. One sentence in §VIII (or §VIII.A with a pointer from §VIII) conceding the investor-side cost is unpriced and relabelling the binding-constraint claim as literature-based. Note the collision with C-DA-06: "binding" is being qualified in two different senses in this round (uncertainty layer vs policy constraint) — keep the two edits verbally distinct.

### C-DA-30
raiser: DA
da_ref: S4
severity: inferred MINOR
class: WORDING
panel_lines: 1027
condition: §VIII.A must name distributional silence about Ginnie Mae borrowers as a limitation, not merely as a coverage bound.
location: §VIII.A (.tex:733–752); §I (.tex:52); §V.B (.tex:269)
verified: true — §I concedes "Realized take-up of that statutory right is not measured anywhere in this design, so the 20.4% share bounds the carve-out from above rather than sizing it" (.tex:52), and the CDR contrast is committed at .tex:269 ("the involuntary buyout channel (CDR 2.1% versus 0.4% in May 2025) supplying most of the structural difference"). §VIII.A contains no distributional limitation of any kind (read in full).
fix: WORDING, no run. One sentence in §VIII.A. Cheapest condition in the report.

### C-DA-31
raiser: DA
da_ref: N1
severity: inferred (filed as a non-defect / credit)
class: WORDING
panel_lines: 1035
condition: The paper should lead more confidently with "most of the shortfall was mechanical", on the ground that "there is no cell anywhere in the paper's apparatus in which the mechanical baseline fails to deliver the majority".
location: abstract (.tex:31, "the model still accounts for 85.7%"); §VIII (.tex:725)
verified: false — ADJUDICATED ANTI-CONDITION #4, confirmed here. The universal is refuted by the paper's own frozen artifact: `floor_form_mixture_results.json` cell `4.991|1|0` (headline floor, additive form s = 1) gives `share_pct = 44.6996` — a MINORITY standalone, and ~35.6% on the shared basis (standalone minus the committed 9.1-point netting wedge, .tex:699). The DA's *supporting* numbers are all correct (cells 4.991|{75,100,125,150}|0 give 101.94 / 94.79 / 82.37 / 68.39%, i.e. "68.4% to 101.9%"), but they sweep the PSA ramp under the max form only, which is exactly the conditioning the DA's own C2 says must be disclosed.
fix: Do not implement "lead more confidently" as stated — a naive edit would strengthen a claim whose form-conditionality is a separately-upheld condition. See C-DA-32, which is the salvageable inverse.

### C-DA-32
raiser: DA
da_ref: N1 (inverted — the real condition inside the refuted universal)
severity: inferred MAJOR
class: WORDING
panel_lines: 1035 (inverted per the round's ANTI-CONDITIONS table item 4)
condition: The 85.7% mechanical-majority headline must be labelled form-conditional wherever it is quoted, since under the disclosed additive floor form the same null delivers a minority (44.7% standalone / ~35.6% shared at the headline floor).
location: abstract (.tex:31, sentence 3); §VIII (.tex:725); §V.F (.tex:526); tab:bases / tab:headline quoting sites
verified: true — `floor_form_mixture_results.json` `4.991|1|0` `share_pct = 44.6996` against `4.991|0|0` `share_pct = 94.7917` (production max form, whose shared-basis reading is the quoted 85.7%, .tex:725). The abstract's mechanical-majority sentence carries no form qualifier; the abstract's form qualifier ("under the production floor form; the additive form roughly doubles the margin") attaches to the MARGINAL, not to the null's share. The form fork is already documented as production-vs-additive at `floor_form_mixture_results.json` `orientation` (s0 = production hard maximum, s1 = additive competing-risks).
fix: WORDING, no run. Attach the form condition to the 85.7% at each quoting site, using the committed additive-form counterpart. The two literals to use are 44.7% standalone and, if the shared basis is quoted, ~35.6% — the latter is a derived number (standalone less the committed 9.1-point wedge), so either derive it explicitly in text or quote standalone only. Do NOT weaken the mechanical-majority finding itself: it holds across the whole PSA sweep under the production form.

### C-DA-33
raiser: DA
da_ref: N9
severity: inferred (filed as partial credit withheld)
class: META
panel_lines: 1051
condition: Credit for Appendix O / Table 27 should be withheld because, of the ~13 rows adjudicated "against the headline", not one moved a reported number.
location: Appendix O (.tex:1393–1428); tab:headline; abstract
verified: false — ADJUDICATED ANTI-CONDITION #3, confirmed here. Rows that moved reported numbers: the floor demotion (headline +9.2 → +5.6; the in-sample +9.198 and off-window +5.572 marginals are both committed in `attenuation_sensitivity_results.json` `base_marginal_pp`), the percentile-bootstrap retraction (.tex:1412: "Reported: [+3.0, +8.0] & Superseded by rule: … the wild-cluster interval became the binding layer (against the headline)" — the printed interval is now [+2.9,+8.7]), the floor-sweep reinterpretation (.tex:1409), and the Danish validation's point→band move. A defensive paragraph rebutting this is unnecessary.
fix: Do not implement. Record as a panel error. If anything, C-DA-15's domain sentence is the one Appendix O edit this round should carry.

### C-DA-34
raiser: DA
da_ref: Carroll Round venue judgment
severity: inferred CRITICAL-for-deadline
class: META
panel_lines: 1073–1075
condition: Before the Carroll Round debut (no revision checkpoint exists after it), the headline must be re-cut to the range with the baseline-ramp caveat attached, so that "what sets your seasoning baseline, and did you estimate it?" cannot take the +5.6 apart in public.
location: abstract (.tex:31); tab:headline row 4 (.tex:79); §I (.tex:46) — the talk-facing surfaces
verified: true — the exposure is real and unmitigated at the talk-facing surfaces: the abstract names +5.6 with no ramp caveat, and the ramp disclosure lives only in §V.E (.tex:333), tab:uncertainty's note (.tex:433) and .tex:417. The DA's premise that the caveat is answerable from committed material is also true (`psa_level_sweep_results.json` supplies the whole span and its 2.49× ratio).
fix: META/sequencing, not a new edit: this condition is discharged by landing C-DA-05 (abstract ramp qualifier) and C-DA-06 (binding-layer qualifier), plus whichever of C-DA-02/C-DA-08 resolves the interior point, BEFORE the talk. It adds a deadline, not a change. The C-DA-07/A1 run is NOT required for the talk — the caveat is answerable by disclosure alone.
