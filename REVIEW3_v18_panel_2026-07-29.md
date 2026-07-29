# REVIEW3 — ARS full panel on the final manuscript (2026-07-29)

**Instrument:** ARS academic-paper-reviewer v1.10.0, full mode, 7 agents (opus), run on the
post-round-31 manuscript (139pp, 108 gates, 495 tests, render-clean).
**Result: 63.6/100 reconciled — MAJOR REVISION.** Prior panel on the pre-round-28 draft: 76.3.
Five reviewers independently returned 61.4-64.6 (3.2-point spread).
**Carroll Round verdict: PRESENT WITH FIXES** (R1-R4 of the roadmap required before the talk).

Dimensions (reconciled): Originality 72 | Methodological Rigor 62 | Evidence Sufficiency 59 |
Argument Coherence 70 | Writing Quality 56.

Reviewers worked independently and read-only; the synthesis arbitrates their disagreements
against the manuscript and closes with section 8, the panel's OWN factual errors (10 logged).

---

# Phase 0 — Field Analyst Configuration

## PHASE 0 — FIELD ANALYST CONFIGURATION DOCUMENT

Read: `~/Downloads/UPLOAD_ROUND11/revised_paper_v18.md` (full, 1,143 lines), `paper/v18/revised_paper_v18.tex` (structure, paragraph metrics, abstract env), and read-only spot checks of `hazard/data/floor_inference_correction_results.json`, `hazard/data/oos_identification_results.json`, `hazard/floor_inference_correction.py` (cluster definition), `hazard/data/` inventory (~200 frozen artifacts), `specs/` (14 spec files), `tests/` (29 test modules). No repo script executed.

---

## 1. FIELD CHARACTERIZATION

**Primary discipline:** Empirical macro-finance — monetary-policy *implementation* (central-bank balance-sheet mechanics), not monetary transmission theory.
**Secondary:** Mortgage-market microstructure / MBS prepayment modeling; comparative housing finance (US–Denmark); computational economics (ABM validation methodology).

**Research paradigm:** Quantitative, model-based *accounting decomposition* — explicitly and repeatedly disclaimed as causal identification (§V.E fifth qualification: "not causal identification in the econometric sense… none is claimed"). The paradigm is closer to structural policy-counterfactual simulation with imported elasticities than to reduced-form causal inference. Epistemically it is a **pre-committed, adversarially-audited calibration exercise** — an unusual paradigm that reviewers will not have a standard rubric for.

**Methodology type:** Triangulated multi-estimator simulation. (i) 10,000-household ABM (utility-maximizing decision rule, synthetic population, 50-seed distribution); (ii) Path A stratum-month Poisson PML hazard, 296 cells, 295 FE + ridge (declared non-corroborating, excluded from headlines); (iii) Path B loan-level competing-risks microsimulation, 75,000 Freddie loans, elasticity imported from Liebersohn–Rothstein (2025) and never fitted to the target — **the headline estimator**. Core identified object is a paired-run differential (Eq. 4), central minus $\beta_1{=}0$ null. Uncertainty via cluster bootstraps + wild-cluster bootstrap-$t$ + pre-committed calibration grids. External replication on 17.6M Fannie loans.

**Plausible journal tier:** The *empirical content* is field-journal grade: **Journal of Money, Credit and Banking / Journal of Housing Economics / Real Estate Economics / Journal of Financial Stability**, or a Fed Bank working-paper series. A top-5 or *JF/JFE/RFS* placement is out of reach because the paper itself forecloses the identification claim that would justify it. As submitted (139pp, no clean holdout, imported elasticity) the realistic slot is **JMCB-tier major revision, or a policy outlet (Journal of Policy Modeling, FEDS-Note-adjacent)**. Score on the field-journal rubric.

**Paper maturity:** Very high polish, **advanced-revision** stage — 31 internal rounds, 108 liveness gates, 495 tests, ~200 frozen artifacts, a 27-row self-administered adverse-findings register (Table 27). This is *not* a rough draft. Its remaining weaknesses are therefore **structural** (what the design can identify; whether the reporting convention is defensible) rather than executional. Reviewers must not confuse polish with rigor, and must not award credit for self-criticism that changes no reported number.

---

## 2. REVIEWER CONFIGURATION CARDS

### EIC — Editor, monetary-policy implementation & central-bank operations
**Identity:** Senior editor of a general-interest money/banking field journal; former central-bank markets-desk economist; publishes on reserve demand, balance-sheet normalization, and operating frameworks.
**Expertise:** FOMC operating objectives, SOMA portfolio management, redemption-cap design, the QE/QT policy record; editorial triage of scope-versus-length.
**Focus:** Whether the *marginal* contribution over the Fed's own already-published claims justifies publication; whether the abstract's claim structure matches what §V.E says is identified; whether the title is supportable; length and venue fit.
**Toughest about:** The contribution net of Na et al. (2024), Perli (2024), Hammack (2025) and **York (2022)** — the paper concedes the mechanism, the below-cap regime, *and* the ex-ante-projection observation are all pre-existing (§II, "the observation is theirs"), leaving decomposition + quantification. Also: §III.B's own concession that "a shortfall against the MBS cap is not by itself evidence that a stated policy objective was missed" — which undercuts the title's framing of a "Shortfall." Expect hard pressure on 139pp and on whether one 2,200-word paragraph is publishable prose.

### R1 — Methodology: applied microeconometrician, survival analysis & few-cluster inference
**Identity:** Empirical microeconometrician specializing in discrete-time hazard/competing-risks estimation and cluster-robust / bootstrap inference in small-$G$ settings; secondary interest in simulation-based inference and indirect inference.
**Expertise:** Cause-specific vs subdistribution hazards, Poisson PML with high-dimensional FE, wild-cluster bootstrap-$t$ and its failure modes, Webb weights, effective cluster counts, delta-method validity under nonlinear transforms, seed-noise vs parameter uncertainty.
**Focus:** The inference ladder (Tables 8, 9); the legitimacy of the "binding layer" $[+2.9,+8.7]$; the ABM's non-existent null; the Path A ridge and its holdout; peak-lag selection across 7 lags.
**Toughest about:** **The headline interval's construction.** Verified from the artifact: the floor read R2 is a *cluster-ratio estimator* on 137 cohort-months in **31 four-way-stratum clusters** (`hazard/floor_inference_correction.py:23`, cluster = `stratum.build_stratum_id`), whose Rademacher wild-$t$ endpoints (B=9,999) are then pushed through a **PCHIP interpolant of a frozen floor→marginal sweep**. R1 will ask: does a coverage property survive a nonlinear, non-analytic monotone map applied to interval *endpoints*? Also: the stratum-cluster loan bootstrap has **25.8 effective clusters of 130** (largest stratum 9.77% of balance) and the paper itself calls a percentile interval on 26 effective clusters "noisy" — yet quotes it. Also that §IV.B's ABM null yields marginals of $+270.4$ and $-105.3$ points (sign disagreement), i.e. the second estimator supplies *no* differential at all, so the "two structurally distinct estimators" claim is a level-only contrast.

### R2 — Domain: agency-MBS prepayment modeling / SOMA portfolio
**Identity:** Fixed-income researcher who builds production prepayment models for agency MBS; fluent in PSA conventions, WAC/WAL, pass-through vs note-rate coupon bases, servicer buyouts, Ginnie vs GSE speed differentials, TBA delivery.
**Expertise:** SOMA CUSIP-level composition, empirical CPR back-outs, curtailment, remittance/settlement lags, burnout, GMAR/Recursion speed data, cohort seasoning.
**Focus:** Whether the loan universe can carry the SOMA book; whether the baseline (100 PSA + turnover floor) is a defensible level-setter; coupon-convention hygiene; the benchmark's monthly construction.
**Toughest about:** **Coverage and baseline.** §III.B concedes Path B's universe (Freddie 2017–2021 conventional) is **51.0% of SOMA book face** on the book's own agency×vintage joint cells — the "two-thirds" vintage marginal overstates it — and Freddie conventional hazards are extrapolated **as-is** to 20.4% Ginnie (statutory assumability, buyout channel, CDR 2.1% vs 0.4%) and 33.7% out-of-window vintages. The two overlays that re-score those shares ($+4.4$, $+3.7$) are labeled in Table 5 as "**change of estimand, not a correction**" — R2 should test whether that label is doing work the run does not license. Second: `psa_level_sweep` moves the marginal **$+0.9$ to $+15.6$ points** across 75–150 PSA (§V.E, "the widest disclosed layer… no coverage property") — a convention, not an estimate, that dwarfs the headline interval. Third: the four **clip-induced zero months** in the benchmark's monthly series (Appendix N) that flip the paper's own frozen timing rule from pass to concede, and the $-5.5\%$ mechanical shift under settlement alignment (§VII.B).

### R3 — Perspective / cross-disciplinary: comparative housing-finance institutions & mortgage law
**Identity:** Institutional economist of mortgage-market design, works on Danish/Dutch/German covered-bond and match-funding systems; publishes at the law-and-economics boundary (due-on-sale, assumability, CoD income).
**Expertise:** Danish Balance Principle, tap-issued series, callable-bond buyback mechanics, Danish tax treatment of discount extinguishment, Garn–St. Germain, FHA/VA assumability, TBA homogeneity.
**Focus:** §VI.D's transplant construction; §VIII's "trilemma dissolution"; the two-sided-exchange frame; whether the institutional conclusions travel.
**Toughest about:** **The Danish counterfactual's epistemic status and the tax-law override.** The paper states the positive gap is *forced* by the zero-gap anchor ("could not have come out otherwise"), so only the magnitude is informative — yet $+\$61.2$bn is carried into the abstract, Table 1, and the conclusion. It imports the payoff rule but **not** the Balance Principle, series-level match funding, tap issuance, advisory distribution, or the Danish interest-only share (which the paper concedes would move the shortfall *the other way*). And §VI.D **overrules its own source's** US tax counterfactual on a legal reading (Berger et al.'s 22%/15% treatment vs the paper's IRC §61(a)(11) cancellation-of-debt-at-ordinary-rates claim, plus post-TCJA deductibility) — R3 must verify that reading and judge whether a single-authored paper should rest a channel dismissal on it. Also: §VIII concedes the trilemma dissolution "reduces to 'the marginal is small'" and that under the max form the marginal is "bounded small **by construction**" — i.e. the policy conclusion may be an artifact of the floor's functional form.

### DA — Devil's Advocate: adversarial replication / research-integrity referee
**Identity:** Meta-science and replication specialist; reviews pre-registration compliance, computational reproducibility, and rhetorical use of robustness apparatus.
**Expertise:** Spec-before-run verification, artifact/manifest provenance, gate-vacuity detection, garden-of-forking-paths auditing, distinguishing conservatism from selective concession.
**Focus:** Whether the pre-commitment architecture is evidence or armor.
**Toughest about:** **Concession without consequence.** The paper concedes 15+ items (Table 27) — retracts the 0.2-point convergence, retracts the within-stratum bootstrap ($37\times$ understatement), demotes 27-cell positivity to a wiring check, declares its own Fannie envelope gate too wide to inform, admits both forced signs — and **keeps every headline number**. DA must test: (a) is "**mid-grid anchor**" a defensible reporting convention, given the paper explicitly disclaims it as a central tendency yet it lands just below the binding interval's midpoint; (b) does Table 5's "assembly" *display* eight downward corrections while §V.E declines to compose any of them ("a composed figure would carry a precision nothing in the design supports") — is that principled or convenient, given the one measured composition (`b5_joint_cell`) came in at $+2.9$, i.e. **at the interval's floor**; (c) provenance: Appendix A admits **two freezes ran on uncommitted working trees** and one ABM manifest's `git_commit` points at the *previous* tree state, so specifications must be identified by cohort-bucket count rather than by commit; (d) 14 spec files in `specs/` against 60+ named runs cited in text — is spec-before-run verifiable for all of them, or only for the ones with committed specs?

---

## 3. HIGHEST-RISK CLAIMS THE PANEL MUST SCRUTINIZE

**RISK 1 — The entire headline rests on 137 cohort-months.**
*Claim:* $+5.6$pp $= +\$42.6$bn, with binding interval $[+2.9,+8.7]$.
*Location:* Abstract; Table 1 row 4; §V.E; §VII.F ¶3–4; Table 6 row 2; Table 9; Table 15.
*Verified:* the off-window anchor is 4.9906% CPR from **137 cohort-months / 31 clusters** of 2018 Freddie discount cohorts (`floor_inference_correction_results.json`, gate `P1_R2`). The floor is the design's "dominant level-setter"; everything else is a mapping. Two independent reads (**5.51%** age-standardized with 84% imputed weight; **5.52%** Fannie, `fannie_floor_read`) sit *above* the clean band and imply a marginal below the quoted $+4.3$ lower edge. The paper concedes "the band's *lower* edge is the soft one." Panel must decide whether $+5.6$ is reportable as a headline at all.

**RISK 2 — The floor's functional form can roughly double the answer, and the paper's own semantics point the wrong way.**
*Location:* §VII.F ¶3 (`floor_form_mixture`, `floor_form_offwindow`); §V.B (floor semantics); §VIII (form-conditionality of the policy conclusion).
Under the additive/competing-risks form the marginal is $+11.2$ and **nearly floor-invariant** ($+11.22/+11.21/+11.19$ at the three off-window anchors) — the entire in-window→off-window demotion operates through max-form censoring. The measured mixture curve reaches $+9.7$ at $s{=}0.25$ and plateaus near $+11.2$ from $s{=}0.6$. Yet §V.B states the strictly-involuntary share is "**plausibly well under half**" — which on the paper's own curve pushes toward the additive end. The paper keeps $s{=}0$ on "semantics," conceding the near-coincidence defense "does not extend to the shallow-gap off-window anchors." Counter-consideration the panel must weigh: the additive central leg recovers only **55.9%** of the benchmark at the headline floor (vs 91.3% max-form), so form choice trades the marginal against aggregate fit — and the paper says levels are not identified, so fit cannot be the selection rule. This is the single largest unresolved fork; it decides whether the headline is ~$+5.6$ or ~$+11$.

**RISK 3 — Both headline signs are forced by construction; the elasticity has no internal empirical support.**
*Location:* §V.E (`sign_forcing_stats`: 99.53% of exposure below the 5.2311% window-minimum rate; 27-cell positivity demoted); §VI.D (Danish positivity "forced by the zero-gap anchor"); §V.B/§V.D (`patha_sign_test`: $p=0.093$ stratum, $0.412$ temporal, $0.241$ permutation — $\beta_g$ not distinguishable from zero); §IV.B (ABM null: $+270.4$ vs $-105.3$).
So: the lock-in marginal's sign is forced, the Danish gap's sign is forced, the in-sample estimate of the same channel fails its own sign test, and the second estimator cannot form a null. The elasticity's evidential base is **entirely external** — Liebersohn–Rothstein (2025) 5.5–7.7% band (a *specification* range, no SE propagated anywhere), plus Fonseca–Liu (2024) and Graybill–Mangum (2026) corroborating from *above* the band. Meanwhile the paper's own realized cross-sectional gradient (`episode_confrontation`: $+4.20$ CPR points, cluster CI $[+3.59,+4.66]$, permutation $p=0.005$, composition-standardized $+3.44$) runs **$4.5\times$** the model's implied $+0.94$ — a factor-of-4.5 miss the paper files as a "counterweight" rather than as evidence of misspecification. Panel must decide what identified content survives.

**RISK 4 — No outcome holdout anywhere, and the level is evaluated on the window that calibrates it.**
*Location:* "Definitions used throughout" (line 59, stated globally); §VIII.A; §VII.F ¶5 (the 19-month construction is an *input-stability* check, "cannot falsify the marginal against data"); Table 2 row 2.
Every recovery percentage is in-sample or calibrated in the time dimension. Path A trains on 19 of 42 QT months and its ridge-selection holdout doubles as its out-of-sample diagnostic. Path B's level is set by a floor measured in the window it is scored on. The paper discloses this unusually forthrightly — but disclosure is not remedy, and the panel must score Evidence Sufficiency on what exists, not on the candor of the caveat.

**RISK 5 — Benchmark standing and denominator choice.**
*Location:* §III.B (final ¶: "a shortfall against the MBS cap is not by itself evidence that a stated policy objective was missed"); §III.B expectations complement; Appendix N (four clip zeros); §VII.B (settlement re-basing $-5.5\%$).
The $\$764.7$bn denominator is measured against a ceiling Fed staff projected would never bind. The expectations-based complement is **$\$87.8$bn (11.5%)**, against which the marginal is 49% / 23% / *undefined* across three disclosed allocations — and the paper concedes these are upper bounds on lock-in's share of a *mixed lock-in-and-rate-path* surprise. Panel must judge whether the title, abstract, and Table 1's lead row are calibrated to a composition statement rather than a policy-miss statement.

---

## 4. STRUCTURAL FEATURES A REVIEWER MUST KNOW TO REVIEW FAIRLY

1. **Two-part document.** Main text pp.1–94; online appendix pp.95–139 (Appendices A–O), explicitly flagged at line 585. Appendices are *apparatus*: run ledger + superseded-figure catalogue (A), ABM spec (B–D), Path B parameters (E), Path A detail (F–H), composition (I), sweep mechanics (J), behavioral mechanics (K), WAL (L), units corrections (M), seasonal floor (N), adjudication audit (O). Do not fault the main text for material deliberately placed there — but do check the appendix delivers what the main text promises.

2. **Uncertainty is a ranked hierarchy, deliberately not merged.** Four layers, with the ranking itself a claim: (a) seed noise — negligible at reporting precision; (b) genuine sampling intervals — loan-level bootstrap $[+9.17,+9.23]$ *retracted*, stratum-cluster $[+8.27,+10.19]$ operative, floor-read cluster bootstrap; (c) the **calibration box $+2.1$ to $+13.2$ — a grid with explicitly no coverage property** ("the elasticity band it sweeps is Liebersohn and Rothstein's *specification* range… no sampling error of theirs is propagated anywhere in this paper"); (d) the form×transform hull $+3.5$ to $+13.1$. The paper names layer (b)-on-the-floor-read, $[+2.9,+8.7]$, as **binding**. Reviewers must engage that ranking on its terms — treating the box as a confidence interval, or the interval as the box, is a misreading the paper pre-empts.

3. **Two floor calibrations attach to every number; most legs exist at only one.** "In-sample calibration point" = 4.0% in-window ($+9.2$pp, 97.9%). "Off-window" = 4.70–5.33% ($+5.6$pp, 91.3%) — **the headline**. §V.E: only the central and null legs (plus concave) were re-run off-window; Path A, full-book, composed, covariate bands, Ginnie overlay, and *both Danish legs* were run **in-window only**, and "any level appearing without a floor label should be read at the in-window 4.0% calibration." Cross-floor comparisons are apples-to-oranges by the paper's own admission.

4. **Four accounting bases; the marginal is basis-invariant.** Standalone-scorer / benchmark-consistent shared (main-text convention, nets $\$69.56$bn curtailment, a flat 9.1pp wedge) / full-book / composed. The paper previously published an 18.3-point gap that was a basis-mixing error (Appendix A) — reviewers must not repeat it. On the shared basis the framework **undershoots** (91.3%); it overshoots only on the standalone basis (107.0%).

5. **Path A is disclaimed, not defended.** Declared "aggregate context only; does not corroborate the result; excluded from every headline" (Table 2, Table 20). Do not credit it as a third confirming estimator; equally, do not attack the paper as if it leaned on it.

6. **The pre-commitment apparatus, and where to find the paper's real weaknesses cheapest.** `specs/*.md` and script headers fix grids, parity gates and interpretive thresholds before execution; ~200 frozen JSON artifacts with parity gates that reproduce committed figures bit-exactly (I verified two); 108 liveness gates; 495 tests. **Appendix O / Table 27 is a self-administered adverse-findings register** — 27 rows, each stating the committed rule, the outcome, and the adjudication *with its direction relative to the headline*. Read Table 27 before Section V. Note its own framing: "a green gate suite is therefore not self-certifying."

7. **Voice and provenance.** First-person "I", single author. Appendix A discloses that two freezes ran on uncommitted trees and that one ABM manifest's `git_commit` points at the pre-run tree state.

8. **Untrusted-data check (clean).** I found **no** text in the manuscript directed at a reader-agent, no embedded instructions, no attempts to steer a review. Line 61 ("How to read this paper… the short path for a referee: §II–III.B, §V.B, §V.E, §VII.F, §VIII") is ordinary authorial signposting — reviewers may use it as a map but must not let it substitute for reading §IV, §VI.D, §VII.C, or Appendix O, all of which contain material adverse to the headline.

9. **Writing is a genuine, measurable scoring dimension here — not a courtesy deduction.** The longest single body paragraph in the source is **14,732 characters (~2,200 words)**, in §V.B (`paper/v18/revised_paper_v18.tex`); the next three are 11,312 (§V.E), 10,696 (Appendix G), and the §V.E paragraph at md line 261 runs 10,336 characters. Sentences routinely nest 4–6 parentheticals and 3+ em-dash asides. The abstract environment is ~248 words plus a second unbracketed paragraph. Density is being used to carry qualification load that structure should carry. Score Writing Quality on readability actually delivered; do not read compression as rigor, and do not read self-qualification as clarity.

10. **Calibration note.** A prior panel scored **76.3/100** on this same instrument. Score independently on the field-journal rubric; do not anchor to that number, and do not inflate for undergraduate authorship — the venue judgment is a separate one-line output.

---

# EIC Report

# EDITOR-IN-CHIEF REPORT
**Manuscript:** "Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"
**Reviewer role:** EIC — monetary-policy implementation & central-bank operations
**Basis of review:** full read of `~/Downloads/UPLOAD_ROUND11/revised_paper_v18.md` (1,143 lines, all sections and Appendices A–O), structural metrics from `paper/v18/revised_paper_v18.tex`, page counts from `paper/v18/build_split/` (main 94pp, online appendix 45pp), `paper/v18/references.bib` (70 entries), and read-only inspection of `hazard/data/floor_inference_correction_results.json` and `specs/`. No repo script executed.

**Untrusted-data note:** I found no text in the manuscript addressed to a reader-agent and no embedded instructions. Line 61's "How to read this paper" is ordinary authorial signposting; I used it as a map but read §IV, §VI.D, §VII.C–D and Appendix O in full, all of which carry material adverse to the headline.

---

## SUMMARY OF SUBMISSION

The paper measures how much of the $764.7bn by which the Fed's agency-MBS runoff fell below its redemption caps (June 2022–November 2025) is attributable to mortgage lock-in rather than to mechanics, and answers: mostly mechanics. A loan-level microsimulation with the lock-in elasticity switched off still recovers 85.7% of the benchmark on the paper's own accounting basis, because scheduled amortization plus a measured turnover floor cannot fill a $35bn monthly ceiling under any rate response. Lock-in's own identified contribution is delivered as a range — $[+2.9,+8.7]$ points, a wild-cluster bootstrap-*t* on the turnover floor's 31 stratum clusters — with $+5.6$ points / $+42.6$bn named as the value at the calibration the author headlines. A Danish market-value-repurchase transplant onto the same book gives a $+\$61.2$bn to $+\$256.8$bn institutional gap under face accounting, reversing under a cash-haircut reading.

## SIGNIFICANCE & FIT

The question is squarely in this journal's scope and the answer is one implementation economists should have. The claim that matters is not "lock-in slowed QT" — the Fed's own staff said that (Na et al. 2024; Perli 2024; Hammack 2025) and York (2022) projected the below-cap regime in the month the $35bn cap took effect, all of which §II concedes explicitly. The claim that matters is the **cap-design arithmetic**: the ceiling was set 1.7–1.9× the Fed's own contemporaneous projection of achievable runoff (§VI.B), and against that projection rather than the never-binding cap the shortfall is $87.8bn, 11.5% of the cap-relative figure (§III.B). That reframing is genuinely new, it is arithmetic on a published source that nobody appears to have done, and it is the result I would expect to be cited. It is also the result the abstract does not mention.

Two things cap significance. First, the paper forecloses the identification claim that would earn a higher-tier placement, and does so correctly (§V.E fifth qualification: "not causal identification in the econometric sense … none is claimed"). Second, the paper's own §III.B concedes that "a shortfall against the MBS cap is not by itself evidence that a stated policy objective was missed" — the Committee's operating object was the aggregate portfolio, Treasury runoff ran against its own caps, and nothing here shows reserves or the aggregate path came in off course. What the $764.7bn measures, on the paper's own account, is *composition*. That is a real and publishable finding. It is not the finding the title advertises.

Realistic slot: JMCB / *Journal of Housing Economics* / *Real Estate Economics* / a Reserve Bank working-paper series. Not *JF/JFE/RFS*, for the reason the author himself gives.

## STRENGTHS (specific)

1. **§V.E's seventh qualification (md line 271) is the best paragraph in the manuscript and I have not seen its equivalent in a submission.** It lines up every downward correction to the headline — off-window re-anchor $+5.6$, Ginnie overlay $+4.4$, age-standardized floor $\sim+3.8$, Fannie floor read below $+4.3$, joint cell $+2.9$, moving-share brackets $+3.4/+1.8$, Aladangady-anchored $+0.9$ — against the upward counterweights (additive form $+11.2$, Fonseca–Liu $+11.5$), states that the sections never show them together, and refuses to compose them. Most authors bury one of these; this one tabulates all twelve (Table 5).
2. **Appendix O / Table 27 is a 27-row self-administered adverse-findings register**, each row giving the rule as committed, the outcome, and the adjudication *with its direction relative to the headline*, under the framing "a green gate suite is therefore not self-certifying." Rows include a FAILED floor-sweep stability gate, a retracted bootstrap scheme (37× understatement), a demoted 27-cell positivity check, and a reversed buyback-incidence claim.
3. **A correction executed against the author's own interest.** §VII.F re-measures the level-setting turnover floor outside the evaluation window and re-runs both legs there, moving the headline from $+9.2$ to $+5.6$ points and the level from 97.9% to 91.3% — then carries the demotion through every dependent number, table and the conclusion.
4. **§V.C refuses to bank its own passing gate:** "A gate that wide cannot fail against anything but a sign error, and I do not treat its passing as evidence." The 0.52-point Freddie–Fannie agreement on 17.6M staged loans is quoted instead. That is the right instinct and it is rare.
5. **Accounting discipline.** Four bases named in one place (§III.B), the marginal proved basis-invariant term-by-term monthly, and the paper's own prior 18.3-point basis-mixing error disclosed (§VII.D). Table 11's notes then convert every recovery percentage into the sign-transparent cumulative runoff error and observe that "a large additive constant sits inside every percentage in the first four columns and makes all of them look better."
6. **The withdrawal in §III.B.** The 0.2-point near-equality between the Fed's ex-ante 88.5% and the null's 88.7% was presented as convergent evidence and is retracted in print, with the $-2.8$ to $+13.2$ range across two disclosed choices shown as the reason.
7. **Reproducibility is real, not asserted.** I confirmed `hazard/data/floor_inference_correction_results.json` reproduces the 4.990624% floor read on 137 cohort-months / 31 clusters with every parity gate passing and the verdict code (`MOVES`) recorded.

## WEAKNESSES (specific, located)

1. **The title is not supported by §III.B.** "Quantitative Tightening Shortfall" asserts the program fell short; §III.B (md line 111, final sentence) concedes it does not show that. **Fix:** retitle to the composition claim the paper actually establishes — e.g. *"Mortgage Lock-In and the Composition of the Federal Reserve's Agency-MBS Runoff"* — or narrow to *"…Redemption-Cap Shortfall."*
2. **The abstract's second paragraph contains a flat contradiction of the body.** It reads "and it identifies levels only"; §V.E opens "The design does not identify the aggregate recovery level." The intended sense is presumably "levels, not monthly timing." **Fix:** "and it identifies levels, not monthly timing" — three words, and it removes a sentence a referee will read as self-refuting.
3. **The abstract leads with two quantities the body declines to identify.** 85.7% and 91.3% are recovery *levels*, floor-dominated by §V.E's own first sentence, and neither carries a floor label or a basis label in the abstract. **Fix:** state the null's share as the composition claim it is, and attach basis and floor to both figures.
4. **The abstract omits the paper's most novel result.** The expectations-based complement ($87.8bn, 11.5%; §III.B) is listed as affirmative contribution #2 in the introduction (md line 37) and appears as row 2 of Table 1, but not in the abstract. **Fix:** one sentence. This is the finding that changes how the QT record is read.
5. **The headline number is defended as a convention, then used as a result.** Table 1 row 4 calls $+5.6$ "an anchor convention rather than a central tendency"; §V.E says "I attach no posture to where $+5.6$ sits." It nonetheless appears in the abstract, the introduction (twice), §VI.A's welfare paragraph, §VIII, and Table 12's WAL row. A field journal cannot publish a headline whose own defense is mid-grid position. **Fix:** either drop the point from the abstract and title-level framing and report the interval, or defend the anchor on stated grounds.
6. **The functional-form fork is disclosed and left open, and it roughly doubles the answer.** §VII.F measures $+11.2$ points under the additive form, *nearly floor-invariant* across all three off-window anchors, while §V.B states the strictly-involuntary share is "plausibly well under half" — which on the paper's own measured mixture curve ($+9.7$ at $s{=}0.25$, plateau near $+11.2$ from $s{=}0.6$) points toward the additive end. The paper keeps $s=0$ on semantics and concedes the near-coincidence defense "does not extend to the shallow-gap off-window anchors." **Fix:** resolve it, or make the abstract's and §VIII's topic sentences form-conditional rather than relegating that to a fourth sentence.
7. **§VIII concedes its own policy conclusion is an artifact of that choice** — the trilemma dissolution "reduces to 'the marginal is small'," and under the production form the marginal is "bounded small **by construction**." A conclusion stated after that concession needs to be stated *as* form-conditional, not restated flat.
8. **The Danish channel rests on one unrefereed source, whose own counterfactual the paper overrules.** `references.bib` records `berger2026` as `@misc … Working paper, SSRN`; §VI.D imports its moving-flatness estimate and then rejects its US tax treatment on a single-authored legal reading (IRC §61(a)(11) cancellation-of-debt at ordinary rates, plus post-TCJA deductibility). **Fix:** flag the source's status in text, and state the tax point as one reading of US law that the paper does not adjudicate rather than as a correction to the source.
9. **Submission mechanics.** `\author{Eugene Ong}\affil{Carnegie Mellon University}` plus a live GitHub URL with an identifiable handle in Appendix A (md line 589) precludes double-blind submission. **Fix:** anonymized master, with an archived DOI (Zenodo) standing in for the repo URL.

## PRESENTATION & LENGTH JUDGMENT

Not defensible as submitted. The main text is **~43,200 words over 94pp**, against a field-journal norm of 12,000–15,000; the online appendix adds ~18,600 words over 45pp. §V.B alone is **6,710 words** and §V.E **5,543** — 12,253 words in two subsections, i.e. an entire article's length inside two headings. Subsection lengths span **134 words (§VI.C) to 6,710 (§V.B)**, a 50× spread that is itself the diagnosis: structure is not carrying the load.

Nor is the paragraph architecture. The longest single body paragraph in the source is **14,732 characters (~2,200 words)** in §V.B; the next three are 11,312 (§V.E), 10,696 (Appendix G), and 8,051 (§V.B again). Sentences routinely nest four to six parentheticals and three or more em-dash asides; Table 8's cells run past 900 characters. I could not audit §V.B's claims by reading — I had to extract substrings. A referee should not have to. The prose is precise and unpadded, which makes this a compression failure rather than a verbosity failure, but the reader pays either way.

Concrete cuts to reach ~15,000 words of main text:
- **§IV + §VII.A + §VII.C + §VII.D → ~2pp.** The ABM is ~13% of the main text and 0% of the abstract, it admits no null (§IV.B: the two readings give $+270.4$ and $-105.3$ points, disagreeing in sign), and its own cross-design leg crosses the author's pre-committed undercutting threshold on all fifty seeds. Report the negative result and the cross-design verdict; move the rest to the appendix.
- **§V.B → ~2,500 words.** Move the κ-grid/floor-dispersion material (md lines 207–211) to Appendix N where its Jensen diagnosis already lives, and the Ginnie/vintage overlay construction to Appendix I.
- **§V.E → ~2,500 words.** Keep the seven qualifications and Table 5; move the group-ablation placebo and the composition decomposition to an appendix.
- **§VI.D → ~3pp**, sweep mechanics and the redemption-validation confounds to appendix.
- Split the four >6,000-character paragraphs at their own topic boundaries with `\paragraph` heads; fold §VI.C's 134 words into §VI.B.

## SCORES

| Dimension | Weight | Score |
|---|---|---|
| Originality | 20% | **73** |
| Methodological Rigor | 25% | **62** |
| Evidence Sufficiency | 25% | **60** |
| Argument Coherence | 15% | **74** |
| Writing Quality | 15% | **52** |

**Weighted final: 73(.20) + 62(.25) + 60(.25) + 74(.15) + 52(.15) = 64.0 / 100**

Rationale in one line each. *Originality:* the decomposition and the expectations complement are real but incremental over a conceded literature; the reporting architecture (pre-commitment + adverse-findings register + paired cross-design) is arguably the more original contribution and is not claimed as one. *Rigor:* transparent and internally disciplined, but the headline rests on an admitted convention and an unresolved form choice that doubles it. *Evidence:* vast in quantity; the single measurement that must carry the headline is 137 cohort-months in 31 clusters (5.9 effective), two independent reads sit above the clean band, Path B's universe is 51.0% of book face, and there is no outcome holdout anywhere. *Coherence:* exceptional about its own limits, weakest exactly at the top — title and abstract. *Writing:* a 2,200-word paragraph is a scoring fact, not a courtesy deduction.

## RECOMMENDATION

**MAJOR REVISION.** I would send this out rather than desk-reject — the apparatus is real, the decomposition is right, and the cap-design arithmetic is worth the journal's pages — but not at this length, and not with this abstract. I would return it once for compression and abstract repair before refereeing. The score sits at the top of the Major band: fixing items 1–5 above (title, abstract contradiction, abstract's identified-object mismatch, the missing expectations result, the headline-as-convention) plus a stated resolution of the form fork would move this to Minor Revision without a single new run.

## CARROLL ROUND VENUE JUDGMENT

**Ready to present and defend as-is** — the empirical execution and the candor are far above undergraduate norm and it would likely win its session — provided the author rehearses a 60-second answer to "what is your number, and why isn't it $+11$?", because the form fork is the only question that can sink the defense.

---

# Peer Reviewer 1 — Methodology

# PEER REVIEWER 1 — METHODOLOGY

*(survival/hazard modeling; cluster-robust and bootstrap inference; simulation-based estimation; computational reproducibility)*

---

## SUMMARY

The paper decomposes a \$764.7bn agency-MBS runoff shortfall against the FOMC's QT redemption caps into a mechanical component (scheduled amortization plus a baseline turnover floor) and an elastic component (lock-in), using a paired-run differential — central minus a $\beta_1=0$ null — on a 75,000-loan competing-risks microsimulation whose rate-gap elasticity is imported from Liebersohn–Rothstein (2025) and never fitted to the target. It reports the mechanical null at 85.7% of the benchmark and the lock-in marginal as a range, $[+2.9,+8.7]$ points, with $+5.6$pp / \$42.6bn named as the value at the headline calibration.

The reproduction apparatus is the best I have seen attached to a single-authored paper: pre-committed specs written into script headers with verbatim interpretive rules, parity gates that reproduce committed artifacts bit-exactly, and a gate suite whose mutations are verified non-vacuous before they are applied. I verified eight headline quantities against the frozen artifacts and every one reproduces (details in §Reproducibility). The paper's self-criticism is also real, not decorative: it retracts its own within-stratum bootstrap, demotes its own 27-cell positivity check, and declares its own Fannie envelope gate too wide to inform.

My objection is not to execution. It is that the object in the abstract — the interval $[+2.9,+8.7]$ — is a cross-sectional cluster-robust interval on a floor read whose entire estimation support is **one origination vintage observed in six calendar months**, that the narrowest of ten available small-sample corrections is the one selected as "binding," that the read's month support is seasonally selected in a direction the paper's own committed calendar profile signs against the headline, and that three level-setting conventions each move the marginal by more than the interval's whole width. Execution rigor is high; inferential rigor is the weak link, and inference is the entire headline. Six of my seven major issues are fixable with machinery already in the repository, but three of them can move the printed number, which is why this is a major and not a minor revision.

---

## STRENGTHS

1. **The differential is the right estimand, and its basis-invariance is proved rather than asserted.** Eq. (4)'s netting cancels term-by-term monthly because the curtailment flow is the product of a shared rate and the shared actual-holdings path (§VII.E). The $\pm25\%$ stress, the seasonal profile, the regime split, and the two-servicer mix all leave the marginal unchanged to $10^{-13}$. This is the correct way to defend an invariance claim.

2. **The retraction of the within-stratum bootstrap is exemplary practice.** The committed scheme held all 130 strata fixed and returned $[+9.17,+9.23]$; the stratum-cluster scheme returns $[+8.27,+10.19]$ in-window and $[+4.63,+6.92]$ off-window. The paper reports the $30.8\times$/$37\times$ understatement, retracts the committed claim, and quotes the wider read (Table 27 row 7). Most authors would have kept the narrow interval.

3. **The floor→marginal map is applied correctly.** Mapping *interval endpoints* through a monotone decreasing transform preserves coverage — quantile equivariance — and the code does exactly that (`floor_inference_correction.py:36–50`), refusing extrapolation and flagging grid-edge truncation. The PCHIP's own fidelity is gated at \$0.687bn against a \$0.69bn tolerance (`P3_mapping_fidelity`). A reviewer's instinct is to attack the nonlinear map; it survives.

4. **Coverage gaps are bounded by external observed speeds rather than assumed away.** The Ginnie share is bounded at \$20–47bn from published Recursion/GMAR differentials and then *scored* by a time-varying overlay whose Ginnie-specific component (\$38.5bn) lands inside the static bound; the out-of-window vintages are bounded at \$11.7bn from Fannie cohort speeds. Both are signed toward overstating trapped liquidity. Bounding an unmodellable segment by observed speed, with a placebo to strip the common level shift, is the right move.

5. **The Poisson-PML/FE consistency argument in Appendix F is correct and correctly scoped** — concentrating the fixed effects out returns the conditional-likelihood score, so the 295-dummy fit is consistent at fixed panel length, unlike FE logit. The ridge is then shown to be a numerical no-op (max parameter difference $4.5\times10^{-17}$) and the point verified against an unpenalized refit on the estimable strata to within 0.002. Path A is then *excluded* from every headline on the strength of a 95% resimulation interval that spans zero. Disclaiming your own second estimator rather than quoting its point estimate is the correct call and is rarely made.

6. **Gate non-vacuity is engineered, not claimed.** `tests/test_floor_ladder_gate.py` asserts each pinned span is present *before* mutating it, tests ladder ordering (not just presence), and opens `floor_inference_correction_v2_results.json` to pin the printed rows against the live derivation. A green suite here means something.

---

## MAJOR ISSUES

### M1. The layer called "binding" is the *narrowest* of the ten rungs it is chosen from, and this leverage profile argues for one of the widest.

**Location:** Table 9 (§V.E) and its note; Table 8 headline row; abstract ¶2; §VIII ¶5.

**Verified.** `floor_inference_correction_v2_results.json`, read `R2_2018_gap<=-0.0025_age>=12`:

| construction | interval (pp) | df |
|---|---|---|
| Webb wild-$t$ (**quoted as binding**) | $[+2.855,\,+8.678]$ | bootstrap |
| Rademacher wild-$t$ | $[+2.796,\,+8.723]$ | bootstrap |
| CR1-$t$, Bell–McCaffrey | $[+2.753,\,+8.796]$ | $t(6.246)$ |
| WCR restricted inversion | $[+2.281,\,+9.109]$ | 401-grid |
| CR2-$t$, Bell–McCaffrey | $[+2.410,\,+9.150]$ | $t(5.095)$ |
| CR3-$t$, Bell–McCaffrey | $[+2.281,\,+9.564]$ | $t(4.103)$ |

with `G_star_css = 5.8717`, `h_max = 0.3323` (on cluster `2017_400_740+_≤80`), `sum_h_sq = 0.1703`. §V.E's own selection rule is "the widest layer that does have a coverage property." Applied *within* the layer, that rule selects CR3-BM $[+2.3,+9.6]$, not Webb. At $G^\*\approx6$ with a single cluster carrying a third of the weight, this is precisely the configuration in which the wild cluster bootstrap's own coverage degrades and the Bell–McCaffrey/Imbens–Kolesár correction is the recommended construction; the paper has computed it and then quoted the narrower rung.

Compounding this: the Table 9 note reads the Rademacher/Webb near-identity (endpoints within 0.06pp) as agreement — "a re-printing rather than a substantive move." With one cluster at $h=0.33$, both weight schemes are dominated by that cluster's sign flip, so their agreement is uninformative about robustness to the leverage profile. It is not evidence; it is the same cluster twice.

**Fix.** Quote CR3-BM $[+2.3,+9.6]$ (or the WCR inversion $[+2.3,+9.1]$) as the binding layer, with Webb reported beside it; **or** keep Webb and add one sentence stating why the wild bootstrap is preferred to BM at $G^\*=5.9$, $h_{\max}=0.33$. Delete the Rademacher–Webb agreement as a stability claim.

---

### M2. The floor read's estimation support is one origination vintage and six calendar months, and the cluster scheme prices cross-sectional dependence only. Neither fact is in the paper.

**Location:** §VII.F ¶"Two further pre-committed measurements"; Table 6 header; Table 9 note; Table 8 headline row; "Definitions used throughout" (md line 59).

**Verified directly from `hazard/data/cohort_month_panel.parquet`** — this is *not* recorded in any artifact. Applying the committed selection window and age cut (2018, `mean_loan_age >= 12`, before the gap cut, which only removes rows):

- all candidate rows are **vintage 2017** — no other vintage clears age ≥ 12 inside 2018;
- they fall in **six reporting periods only**: 201807 (2 rows), 201808 (48), 201809 (48), 201810 (49), 201811 (49), 201812 (49) — 245 rows total, of which read R2 retains 137.

The artifact's own `cluster_strata` field confirms it: all 31 cluster labels begin `2017_`. So the 31 "clusters" are 31 coupon × FICO × LTV cells of a single vintage, observed in the same five consecutive months. The scheme permits arbitrary within-stratum dependence over those months, but treats the 31 strata as independent draws while every one of them experiences the same calendar months, the same 2018 rate path, and the same servicing environment. Any month-level common shock is cross-cluster correlated and unpriced. No month-clustered SE, and no two-way (stratum × month) SE, appears anywhere in the ladder.

Table 6's header describes the floors as measured on "2017–2019 performance." For the three defensible rows — the rows that set the headline — performance is 2018 only, and within 2018 only H2.

**Fix.** (a) State the read's vintage and month support at every site that quotes it, and correct Table 6's header for the defensible rows. (b) Add two rungs to Table 9: month-clustered ($G\approx6$) and two-way stratum × month. With 5–6 month clusters both will be wider, and if they are not, that is itself worth printing. (c) Table 9's "31 clusters carry the read" should read "31 cross-sectional cells of one vintage over five months."

---

### M3. Those six months are seasonally selected, and the paper's own committed calendar profile signs the bias against the headline — by roughly $-0.8$pp, unpriced.

**Location:** §VII.F; Appendix N; Table 6; Table 8.

**Verified.** The committed calendar profile of deep-out-of-the-money turnover (`seasonal_floor_timing_results.json`, `h_month_normalizations_annual_cpr.shape_only`, full-panel basis, exposure-weighted mean pinned at 4.000%) runs, in % annual CPR:

> Jan 2.504 · Feb 2.757 · Mar 3.750 · Apr 4.222 · May 4.937 · **Jun 5.262** · Jul 4.814 · Aug 4.716 · Sep 4.130 · Oct 3.922 · Nov 3.252 · Dec 3.114

peak-to-trough 2.13. Weighting that profile by the read's own month counts from M2 (2/48/48/49/49/49) gives **3.830%** against the profile's 4.000% mean: the read months sit ~4.3% below the calendar-annual level, because the age ≥ 12 cut and the rising-rate gap cut jointly force the read into the descending half of the seasonal curve while the floor is then applied as a constant across all 42 QT months, summers included.

Scaling the 4.991% point read by that factor gives ≈5.20%. The committed floor→marginal grid (`oos_identification_results.json`, band 6.5: 5.000 → $+5.536$pp, 5.334 → $+4.266$pp) maps 5.20% to ≈$+4.8$pp. That is a **$-0.8$pp** move on the headline — a seventh of the binding interval's entire width, larger than the whole lower half of the depth-cut band $[+4.3,+6.8]$, and in the same direction as the two reads the paper already flags as above the clean band (5.51% age-standardized, 5.52% Fannie). It appears nowhere in the paper.

**Fix.** Re-read the off-window floor with calendar-month standardization to the QT window's month mix — the machinery exists in `seasonal_floor_timing.py`, which already builds and normalizes 12-cell profiles. Report the standardized read beside the raw one and restate Table 6's band and Table 8's endpoints. If the standardization is judged too dependent on the full-panel profile basis, report it as an indicative bound in the same register as the 5.51% age-standardized read — it is signed the same way, and both belong in the "the band's lower edge is the soft one" sentence.

---

### M4. The between-read variance exceeds the within-read variance that is called binding.

**Location:** §V.E ¶"The floor's provenance now has an out-of-agency read"; Table 8; §VII.F.

**Verified.** The Freddie point read is 4.991% (`se = 0.393pp` of CPR, `floor_uncertainty`/`P2_percentile_bitexact_R2`). The Fannie read of the *same committed off-window cell under the identical code path* is 5.520% (`fannie_floor_read`). The read-to-read spread is **0.53pp of CPR**, against a within-read cluster SE of **0.39pp**. The age-standardized Freddie read adds a third point at 5.51%.

The paper's response is to call the Fannie read "bracketing," decline to restate the headline on it, and quote the within-read cluster SE as the binding layer. That inverts the variance ranking: the layer that is *not* priced is the larger one. Two independent reads of one parameter, differing by more than the SE of either, is a transport-variance measurement, and it is the component that actually matters for a parameter that must be transported from 2018-vintage-2017 Freddie conventionals to 2020–21 SOMA collateral in 2022–25.

**Fix.** Either build the interval from the read-to-read spread (three reads: 4.991, 5.51, 5.52 — a defensible pooled read near 5.3–5.5%, mapping to $\approx+3.7$ to $+4.3$pp), or state plainly in Table 8's note that the binding layer prices the smaller of the two available variance components and that the larger is disclosed but unpropagated. As written, "binding" is not defensible.

---

### M5. The reported interval is nested inside three unpriced conventions each of which dominates it, and one pre-committed externally-anchored run lands outside it.

**Location:** §V.E ¶7; Table 5; Table 8; abstract; Table 1 row 4.

**Verified.**

| convention swept | span of the marginal at the headline floor | source artifact |
|---|---|---|
| seasoning ramp 75–150 PSA | $+0.856$ → $+15.6$pp | `psa_level_sweep_results.json` (4.991\|75 = 0.856) |
| floor form $s\in[0,1]$ | $+5.572$ → $+11.207$pp ($+9.66$ already at $s{=}0.25$) | `floor_form_mixture_results.json` |
| elasticity $\delta$ below the band | $+3.47$pp at $\delta{=}3.25\%$ | Table 7 / `band_low_extension` |
| **binding interval, for comparison** | **$+2.855$ → $+8.678$pp (width 5.82)** | `floor_inference_correction_v2` |

Each convention's span exceeds the binding interval's width. And the paper's own externally-anchored calibration — `scaled_null_housing_activity`, which scales the baseline until the non-rate channel traps $0.56/0.44$ times the rate channel, per Aladangady et al.'s 44% attribution — roots at $\phi^\*=0.754$ (≈75.4 PSA) and returns **$+0.9$pp**, outside the interval. Table 5 lists it as "below the interval / upward-bias entry" and nothing follows.

The paper's defense is that the conventions "have no coverage property." True — but neither does the *choice* of 100 PSA, $s=0$, or $\delta=6.5\%$, and a confidence interval on one calibration input, conditional on point values of three others each of which matters more, is not an interval on the lock-in marginal. Note also that at 75 PSA / 4.991% floor the null recovers **101.9% standalone** — a *better* fit to the benchmark than the production null (94.8%) — so fit does not rescue the convention either.

**Fix.** Demote $[+2.9,+8.7]$ from "the binding layer" to "the sampling interval on the floor read at fixed ramp, form and elasticity," and headline the convention envelope, with the sampling interval nested and labelled inside it. At minimum, the abstract and Table 1 row 4 must not present $[+2.9,+8.7]$ as what the design bounds; §V.E ¶7's own sentence ("the widest disclosed layer is the baseline level: $+0.9$ to $+15.6$") already says the right thing and is contradicted three lines later.

---

### M6. A basis mix at the passage that decides the form fork — and the abstract's mechanical-majority claim is itself form-conditional and nowhere labelled.

**Location:** §VII.F, the sentence "the central leg's recovery falls from 91.3% to 55.9% along the way"; abstract ¶1; §VIII ¶3.

**Verified,** `floor_form_mixture_results.json`, floor 4.991:

| $s$ | leg | trapped (\$B) | standalone | shared ($-9.10$) |
|---|---|---|---|---|
| 0 (max) | central | 767.53 | 100.36% | **91.26%** |
| 0 (max) | null | 724.92 | 94.79% | **85.69%** |
| 1 (additive) | central | 427.54 | **55.91%** | 46.81% |
| 1 (additive) | null | 341.84 | 44.70% | **35.60%** |

The printed sentence compares a **shared-basis 91.3%** with a **standalone 55.9%**. Like for like the fall is $100.4\to55.9$ (standalone) or $91.3\to46.8$ (shared): the additive form's level cost is 44.5 points, not the 35.4 the sentence implies. This is the same defect class Appendix A catalogues as retracted (the 18.3-point central-minus-null gap that "differenced a standalone-scorer central leg against a shared-basis null"), reappearing in the passage that adjudicates the paper's single largest fork. The error understates the additive form's level cost, i.e. it flatters the branch that doubles the headline.

The larger point is the one the table makes: **under the additive form the $\beta_1=0$ null recovers 35.6% of the benchmark on the shared basis, not 85.7%.** The abstract's lead claim — "switch the lock-in response off and the model still accounts for 85.7% of it" — and §VIII's "the shortfall against the phased caps is mostly mechanical" are max-form results. The paper simultaneously refuses to let aggregate fit select the form ("the design does not identify levels," so fit "is not the selection rule for the marginal's form") while its headline qualitative finding depends entirely on the max form's fit. A reader is currently free to take the $+11.2$ branch and the 85.7% mechanical majority together; they are incompatible.

**Fix.** (i) Correct the sentence to a single basis. (ii) Add one clause to the abstract and one sentence to §VII.F: the mechanical-majority result is a max-form result (null 85.7% shared under the hard maximum, 35.6% under the additive form), so the form choice conditions both the marginal *and* the headline decomposition. (iii) If fit is being used to keep the max form — and it is, implicitly, since a null at 35.6% does not partition the object being decomposed — say so and let the $+11$ branch die honestly, rather than keeping it alive in the hull while relying on the max form elsewhere.

---

### M7. The one internal test of the imported elasticity's implied magnitude misses by $4.5\times$, is computed at a demoted calibration, and is declined instead of diagnosed — when the diagnosis is a one-line analytic recomputation that bears directly on M6's fork.

**Location:** §V.D ¶"A cumulative counterpart"; §V.E qualification six; Table 5 last row.

**Verified,** `episode_confrontation_results.json`: realized gradient $+4.198$pp (cluster CI $[+3.585,+4.656]$, permutation $p=0.00498$, composition-standardized $+3.44$), model-implied $+0.937$pp, ratio $4.480$, injected power $0.675$, verdict branch `T5 excess_gradient_ci_above_model`. The paper declines it because a level gradient is not a dollar marginal and because within-window refinancing on the shallow buckets is inseparable from moving. Both are correct reasons to decline it *as a re-estimate of $\beta_1$*. Neither is a reason to decline it *as a specification test*: the implied cross-sectional gradient is a testable implication of the joint $(\beta_1,\underline{h},\text{PSA})$ triple, the design had power (0.68) to resolve it, and it failed by a factor of 4.5 in the direction of too-flat.

Two things make this actionable rather than rhetorical. First, the artifact's own spec records that the implied path is **analytic** — `max(h_floor, h0_PSA(age)*exp(-beta1*100*gap))` — with no engine run required; and it is computed at **`production floor 4% / FLOOR_MODE max / PSA-100`**, i.e. at the in-window calibration the paper has demoted, not at the 4.991% headline floor. Second, the mechanism that would flatten the implied gradient is exactly the max-form censoring of M6: at 4.991% the floor binds in 68.8% of loan-months against 36.3%, so the implied gradient at the headline calibration is flatter still and the miss larger, while under the additive form (never censoring) it would be steeper.

**Fix.** Recompute the implied gradient analytically at (a) the 4.991% headline floor and (b) the additive form, at 75/100/125 PSA. If the implied gradient approaches the realized $+3.4$ to $+4.2$ only at additive or steeper-ramp settings, that is the first piece of *realized-data* evidence in the paper bearing on the form fork, and it should be reported as such in §VII.F rather than filed in Table 5 as a declined directional counterweight. The run costs nothing and is the single highest-value addition available to this manuscript.

---

## MINOR ISSUES

1. **Table 5 / Table 8 quote the grid-read, not the measured value, at the age-standardized floor.** `b5_joint_cell_results.json.conventional_agestd` measures $+3.671$pp with `ladder_implied_pp: 3.8` and `measured_minus_implied_pp: -0.129`. The paper prints "$\sim+3.8$." Quote $+3.7$ (measured) with the grid-read beside it; the direction of the substitution is favorable to the headline.

2. **The demoted percentile layer's lower edge is a convention artifact, unlabelled.** `layer_convolution_results.json.layers.floor_percentile` records 26 of 1,000 draws outside the PCHIP grid, **all above the 6.0% floor edge, i.e. all on the low-marginal side**, and reports $[+2.281,+8.015]$ under edge truncation against the committed $[+2.974,+8.019]$ under exclusion. Printing "$+3.0$ to $+8.0$" without the convention or the count makes the demoted rung look tighter at exactly the endpoint the paper cares about. One clause in the Table 9 note.

3. **Two width ratios for one comparison.** Table 8 says the loan/stratum interval is "width $0.39\times$ the corrected floor read"; the artifact's own `comparison.width_ratio_vs_floor_read` is 0.455 against the *percentile* width. Both are printed elsewhere in the manuscript's apparatus. Name the denominator in the tablenote.

4. **"The two layers sit on disjoint data and disjoint time" is not right.** Both the floor read (cohort-month panel) and the loan bootstrap (75k subsample) are computed on the same Freddie 2017–2021 origination universe; only the observation windows differ. Independence remains a reasonable working assumption and the comonotone bound (8.12pp) is the right hedge — but the stated *reason* is wrong. Rephrase to "different observation windows and different aggregation units."

5. **$P_q = 0.06$ deserves a main-text sensitivity row.** The transform (3) evaluates $\beta_1$ at a quarterly slot four times Liebersohn–Rothstein's own 1.5% zero-gap moving level. The paper asserts near-insensitivity over $(0,0.12]$ and defers the derivation to Appendix E. For the paper's single imported parameter, print $\beta_1(P_q)$ at $\{0.015,0.03,0.06,0.12\}$ in Table 3.

6. **The stratum-cluster bootstrap is a ratio estimator with random denominators, uncorrected.** Resampling 130 strata moves the loan count from 54,134 to 101,404 (`n_loans.p2_5/p97_5`). The engine's monthly renormalization to Fed holdings fixes the level, as the paper says, but the composition weights then become a ratio of random totals and the percentile interval is not bias-corrected. One sentence, or a fixed-$n$ (rescaled-weight) variant.

7. **A non-argument is offered as reassurance.** §V.E ¶7 lists "the interval does not contain zero" as the first of "three things that stop the list from becoming a retraction," three sentences after establishing that 99.53% of exposure sits below the window-minimum rate so the sign cannot come out negative. If the sign is forced, an interval excluding zero carries no information and should not be in that list.

8. **Table 9's CR1-BM note is confusing.** $[+2.753,+8.796]$ against CR3-conventional $[+2.773,+8.774]$ coincide at one decimal but are distinct objects; "an accident of this leverage profile, not an identity" is correct but reads as a defect. Print the unrounded pairs in the note.

9. **Table 20 mixes specs adjacently.** "Aggregate recovery (spec v4) \$928.9bn" sits directly above "point \$915.1bn (spec v3)." The per-row labels are there, but a single-spec table with the other spec in a footnote would remove the trap.

---

## REPRODUCIBILITY VERDICT

**Read-only inspection only. No repository script was executed** (`tools/liveness_gates.py` and `pytest` were deliberately not run, per the stated hazard). All checks were `python3` reads of frozen JSON/CSV/parquet artifacts.

**What I checked and what happened:**

| # | Claim | Source | Result |
|---|---|---|---|
| 1 | Table 9, all ten rungs | `floor_inference_correction_results.json`, `floor_inference_correction_v2_results.json` | **Reproduces at printed precision.** CR1 $[3.153,8.350]$; CR2 $[2.974,8.553]$; CR3 $[2.773,8.774]$; Rademacher $[2.796,8.723]$; Webb $[2.855,8.678]$; CR1-BM $[2.753,8.796]$ df 6.246; CR2-BM $[2.410,9.150]$ df 5.095; CR3-BM $[2.281,9.564]$; WCR $[2.281,9.109]$. $G^\*=5.872\to$ "5.9" ✓; $h_{\max}=0.3323\to$ "0.33" ✓; 31 clusters / 137 cohort-months confirmed by gate `P1_R2` ✓; $B=9{,}999$, seed 42 ✓ |
| 2 | $t^\*$ distributions are genuine and non-degenerate | `floor_inference_v2_tstar_R2_{rademacher,webb}.csv` | 9,983 / 9,988 distinct values in 9,999 draws; Webb $q_{2.5},q_{97.5}=-2.3248,+2.3187$, matching the committed `t_star_q` to machine zero. Not a re-draw, not degenerate |
| 3 | Headline marginal and both levels | `oos_identification_results.json` | **Exact.** Floor 4.991 → marginal \$42.608bn = 5.572pp; central 100.363% standalone = **91.26% shared**; null 94.792% = **85.69% shared**; band 4.695→6.771pp, 5.334→4.266pp; bind shares 0.6882 / 0.3627. Committed-sweep crosscheck $\Delta=0.0$ at four floors |
| 4 | Temporal floor-stability check | same | \$45.145bn held-out vs \$44.829bn at production floor → "\$45.1 / \$44.8" ✓; additivity gate true |
| 5 | Both cluster bootstraps | `bootstrap_pathb_cluster_results{,_floor4}.json` | Off-window $[4.631,6.924]$ sd 0.604; in-window $[8.273,10.192]$ sd 0.52; effective clusters 25.777; largest stratum 9.77%; $n_{\text{loans}}$ 54,134–101,404. All ✓ |
| 6 | Convolved line | `layer_convolution_results.json` | $[2.796,8.992]\to$ "$[+2.80,+8.99]$" ✓; comonotone width 8.116 → "8.12" ✓; exact enumeration of 1,999,800 pairs, not Monte Carlo |
| 7 | Mixture curve | `floor_form_mixture_results.json` | $s{=}0.25\to+9.660$; $s{=}0.4\to+10.692$; $s{=}1\to+11.207$ at 4.991 ✓. Parity gates bit-exact against \$818.5300844066606 / \$748.1850239867648. **Surfaced the M6 basis mix** |
| 8 | Path A sign test | `patha_sign_test_results.json` | $p=0.0928/0.4118/0.2412\to$ "0.093/0.412/0.241" ✓ |
| 9 | PSA sweep, joint cell | `psa_level_sweep_results.json`, `b5_joint_cell_results.json` | $+0.856/+3.323/+16.468$ ✓; joint cell $+2.928\to$ "$+2.9$" ✓. **Surfaced Minor 1** |
| 10 | Gate non-vacuity | `tests/test_floor_ladder_gate.py` | Mutations asserted present before application; ladder ordering gated; artifact opened live. Sound |
| 11 | **Floor read's estimation support** (not in any artifact) | `cohort_month_panel.parquet` | **Discrepancy with the paper's description.** 2018 + age ≥ 12 ⇒ vintage 2017 only, six reporting periods (201807–201812; 2/48/48/49/49/49 rows). See M2 |

**Verdict: reproducible, with two printed numbers I would change and one material sample fact absent.** Every headline quantity I checked reproduces from the frozen artifacts, and the pre-commitment convention is genuinely auditable — I read the full ex-ante spec in `hazard/floor_inference_correction.py`'s header, including the verbatim interpretive rule ("CONFIRMS if $|L^*-L_p|\le0.5$pp … MOVES otherwise"), and confirmed the run fired `MOVES` ($\Delta_{\text{upper}}=0.705$pp) and that the manuscript subsequently restated the binding layer. That is pre-commitment working against the author's interest, and it is real.

Three limits on the verdict. (i) `specs/` holds 14 files against ~60 named runs; for the rest, pre-run status rests on script-header commit ordering, which the paper documents only for the floor sweeps (`ad52db6`/`651d1a0` before `d0ef130`/`57181b3`). The convention is sound but is verifiable only from git history, not from the paper. (ii) Appendix A's disclosure that two freezes ran on uncommitted trees, and that one ABM manifest's `git_commit` points at the pre-run parent — with cohort-bucket count (7 vs 11) as the substitute identifier — is honest and should stay, but it means the ABM headline is not commit-addressable. (iii) The two printed numbers to change are Minor 1 ($+3.8$ vs measured $+3.671$) and M6 (the $91.3\to55.9$ basis mix).

---

## SCORES

| Dimension | Weight | Score | Basis |
|---|---|---|---|
| **Originality** | 20% | **71** | The mechanical/elastic partition, the ex-ante cap multiple (1.7–1.9×), and the expectations-based complement are genuine quantifications; but the mechanism, the below-cap regime, and the ex-ante observation are all conceded to Na et al. (2024), Perli (2024), Hammack (2025), York (2022) — "the observation is theirs." The switch-off counterfactual is a standard device on imported elasticities; the Danish gap's sign is forced by the anchor. The paired cross-design validation is the most original element, and the paper itself concedes it is not a named member of the Fagiolo/Grazzini/Platt taxonomy. Real, incremental, honestly scoped |
| **Methodological Rigor** | 25% | **62** | Execution rigor is field-leading (parity gates, non-vacuous gate suite, retracted bootstrap, disclaimed second estimator, proved basis-invariance). Inferential rigor is not: the narrowest of ten small-sample corrections is called binding at $G^\*=5.9$/$h_{\max}=0.33$ (M1); the binding SE prices cross-sectional dependence only, on a one-vintage six-month support that the paper does not disclose (M2); a signed seasonal-selection bias worth ~$-0.8$pp in the dominant level-setter is unpriced (M3); the between-read variance (0.53pp) exceeds the within-read SE (0.39pp) called binding (M4); three conventions each dominate the interval and one pre-committed run lands outside it (M5); a basis mix sits at the form fork (M6). Cannot reach the strong band while the abstract's object rests on 31 cross-sectional cells of one vintage over five months |
| **Evidence Sufficiency** | 25% | **60** | Extensive: 17.6M-loan Fannie replication landing 0.52pp away, ~200 frozen artifacts, external bounds on two of three coverage gaps. But **no outcome holdout exists anywhere** (stated globally, remedied nowhere — the 19-month construction is an input-stability check by the paper's own admission); the level is scored on the window that calibrates it; the second estimator supplies no differential ($+270.4$ vs $-105.3$); Path A is disclaimed; the elasticity's evidential base is entirely external with no SE propagated; the one internal test of its implied magnitude misses $4.5\times$ (M7); 49% of SOMA book face lies outside the estimation universe on the book's own joint cells. Supports "mostly mechanical under the max form" and "the margin is small-to-moderate and positive"; does not support a 0.1pp-resolution interval |
| **Argument Coherence** | 15% | **70** | Bookkeeping is unusually disciplined — basis labels, floor labels, the seventh qualification's assembly, the retracted 0.2pp convergence, the withdrawn curtailment-immateriality claim. Four specific failures: fit is refused as a form-selection rule while the mechanical-majority headline silently depends on the max form's fit (M6); "binding" is asserted under a rule the ladder violates (M1); zero-exclusion is offered as reassurance after the sign is declared forced (Minor 7); "two structurally distinct estimators" survives in the framing of a decomposition only one estimator can produce |
| **Writing Quality** | 15% | **52** | Measured, not impressionistic. Longest body paragraph 14,732 chars ≈ 2,230 words (§V.B); four more above 1,600 words (§V.E 1,713; Appendix G 1,620; Table 27 block 1,779). Mean sentence length 39–44 words in §V.B/§V.E against a field norm near 22–26; single sentences to 111 words; 24 parenthetical openers per 1,000 words in §V.B. Abstract ~248 words carrying five conditioned numbers plus a second unbracketed paragraph. The prose is *precise* — every qualification is load-bearing — but structure carries none of the load, so a referee cannot extract the argument in one pass and cannot locate a claim's conditions without re-reading its paragraph. At 139pp that is a substantive defect, not a courtesy deduction. Offsetting: disciplined terminology, explicit labelling conventions, self-documenting tables, non-evasive voice |

**Weighted final: $71(.20) + 62(.25) + 60(.25) + 70(.15) + 52(.15) = 14.2 + 15.5 + 15.0 + 10.5 + 7.8 = \mathbf{63.0/100}$**

## RECOMMENDATION

**MAJOR REVISION.**

Every one of M1–M7 is executable with machinery already in the repository and no new data: a month-clustered and two-way rung added to Table 9; a calendar-standardized floor read from `seasonal_floor_timing`'s own normalizer; the conservative rung promoted or the choice of Webb defended at $G^\*=5.9$; the read's vintage/month support disclosed and Table 6's header corrected; one basis mix repaired; one clause labelling the mechanical-majority result as form-conditional; and one analytic recomputation of the implied cross-sectional gradient at the headline floor and under the additive form. Three of these can move the printed headline — M3 by roughly $-0.8$pp on its own, M1 by $\approx0.6$pp at each endpoint, M4 potentially below the band's lower edge — which is what makes it major rather than minor. A revision that lands them would, on this rubric, sit in the low-to-mid 70s and be a credible JMCB-tier submission; the empirical work already deserves that, and the inference layer does not yet support it.

## CARROLL ROUND JUDGMENT

**Ready to present and defend as-is** — the apparatus and the author's command of his own weaknesses will carry the room — but present the *range* and the mechanical-majority result rather than $+5.6$pp, and walk in with an answer prepared for the first hard question a methodologist will ask: that the headline interval's 31 clusters are 31 coupon×FICO×LTV cells of a single 2017 vintage observed in five months of 2018.

---

# Peer Reviewer 2 — Domain (MBS/SOMA)

# Referee Report — Reviewer 2 (Domain: MBS prepayment modeling, agency-MBS/SOMA operations, comparative mortgage institutions)

**Manuscript:** "Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"
**Files read:** `~/Downloads/UPLOAD_ROUND11/revised_paper_v18.md` (full, 1,143 lines), `paper/v18/revised_paper_v18.tex` (locations), `paper/v18/references.bib`; read-only inspection of `hazard/data/{composition_shift,gmar_dec25_cpr_series,ginnie_cpr_overlay,buyback_credit_bracket,danish_discount_bound,h1_zero_months_diagnosis}_results.json`, `hazard/data/loan_sample.parquet`, `hazard/loan_sample.py`. No repo script executed; no file modified.
**Untrusted-data check:** I found no text in the manuscript directed at a reader-agent and no embedded instructions.

---

## Summary

The paper measures how much of the Fed's \$764.7bn agency-MBS runoff shortfall against its QT redemption caps (June 2022–Nov 2025) is attributable to mortgage lock-in rather than to mechanics, using a 10,000-household ABM, an estimated stratum-month Poisson hazard (Path A, disclaimed), and a 75,000-loan competing-risks microsimulation (Path B, the headline estimator) on Freddie Mac data with the lock-in elasticity imported from Liebersohn–Rothstein. The central finding — the β₁=0 null already recovers 85.7–88.7% of the benchmark, so the shortfall is mostly mechanical, and lock-in's identified contribution is a bounded margin of [+2.9, +8.7] points — is, in my judgment as a prepayment modeler, the correct qualitative reading of this episode and is defended with unusual discipline.

My concerns are not about execution and not about honesty. They are about six modeling conventions, each checkable, that the 108-gate apparatus was never pointed at because gates test code against committed numbers rather than conventions against the market. In order of consequence: (1) the 75,000-loan pool that carries the headline is **not a probability sample of the SOMA book** — the sampler draws equally per origination year, so 2017–2019 vintages are 60% of the pool against 6.0% of the book, and the two dimensions that decide whether the max-form floor censors the elasticity (gap depth and PSA position) are both mis-weighted, with a signed inflationary limb the paper's own logic supplies; (2) Table 25's composition comparison is pointed at the estimation *universe* while §VII.E's reweight is anchored on the *draw's* WAC — a basis mix of the class Appendix A already retracted once; (3) the off-window floor imports 2018's housing-activity level, an upward correction to the headline that the assembly is missing and that the paper's own Aladangady anchor can size; (4) the Ginnie differential is attributed to buyouts when the paper's own extracted series says voluntary speeds carry 63% of it; (5) the Danish buyback discount proxy (32–38%) is a zero-prepayment PV applied to a leg that prepays at 5.61% CPR, so every reversal magnitude is roughly double; (6) 100 PSA is doing more work than the elasticity and is never estimated although the data to estimate it are in hand.

Five of the six require re-runs the existing machinery can execute. None of them threatens the paper's sign or its qualitative decomposition. Three of them can move the headline point, and one moves it *up*.

---

## Strengths

These are specific and I verified them independently.

1. **The coupon-convention work is practitioner-grade and is the single best technical passage in the paper.** §III.B/Appendix M correctly identify that scheduled principal physically follows the borrower's note rate, not the security pass-through coupon; the +0.80-point g-fee-plus-base-servicing wedge (legs 0.60–0.90) is the right number for 2017–2021 GSE production (25bp base servicing + ~45–55bp average g-fee including TCCA, plus coupon rounding); the +0.27 CPR-point effect has the **right sign** (higher note rate ⇒ slower early amortization ⇒ less scheduled principal ⇒ larger backed-out prepayment residual — I confirmed the direction analytically); and `coupon_convention_reweight` correctly collapses the headline "two-point composition effect" to +0.2 points once note rates and pass-through buckets are put on one basis. Most published work in this space silently mixes these two coupon bases. This paper found the error, sized it, and pinned dollar bit-invariance.

2. **The Ginnie overlay is built the way a practitioner would build it.** Extraction of the monthly CPR/CDR/CRR series from the December-2025 GMAR (post-methodology-revision, one consistent WAUPB aggregation across the window), with endpoint residuals validated at |≤0.033| pp and a CPR ≈ CRR + CDR identity check at 0.040 pp mean absolute. I reproduced the quoted snapshots exactly from the artifact: Feb-2023 Ginnie 5.20 vs Freddie 4.05, May-2025 10.34 vs 7.50, CDR 2.10 vs 0.39. The judgment that a *passthrough holder* must treat buyout-inclusive speeds as data (§V.B) is correct and is the right call.

3. **The institutional attribution of the par-payoff obligation is correct and better than most policy commentary.** §I locates it in the fixed-rate note enforced by due-on-sale (Garn–St. Germain 1982), not in TBA eligibility, and notes it binds portfolio and non-agency loans alike. §VIII's observation that Denmark and the US differ in the *locus* of standardization (tap-issued series under one-to-one match funding vs the deliverable pool) rather than in whether market-value redemption is compatible with liquidity is a genuine insight, and the Danish callable market's own depth is the right evidence for it.

4. **§VI.C on assumability and portability is right and rarely stated.** An assumed loan does not prepay — the below-market coupon and the extension transfer to the investor — and the buyer must separately finance the price-minus-balance gap at prevailing rates, which caps take-up. Both instruments relocate extension risk rather than eliminating it.

5. **The competing-risks taxonomy placement is correct.** §V.B's reason for not using Fine–Gray — that every cumulative-incidence functional is obtained by forward composition of cause-specific hazards, so subdistribution machinery buys nothing — is the right reason, and the fractional-drain caveat (cause-specific reading exact for default, balance-aggregate for prepayment) is stated where it belongs.

6. **The benchmark's cap arithmetic is verifiable and correct.** 3 × 17.5 + 39 × 35 = 1,417.5; 1,417.5 − 652.8 = 764.7. The \$652.8bn realized runoff matches the public SOMA record (≈\$2,707bn at June 2022 to ≈\$2,091bn at Sept 2025 in the artifact's own weekly series, continuing to ≈\$650bn by Nov 2025).

7. **The WAL calculator is independently reproducible.** I computed origination WAL for a 30-year 2.49% pool at 0 CPR = 16.89 years against the paper's stated 16.9, and the 15-year sleeve at 8.01 against its stated 8.0. Table 12's external anchoring against CUSIP-back-derived origination dates (14.9 vs printed 14.7) is the right kind of check.

8. **`danish_redemption_validation` is real intellectual honesty.** Going to Danmarks Nationalbank securities statistics to test the paper's own ≈0 refinance-in-place pin, finding realized deep-discount redemptions of 26.4%/yr, and reporting that the pin is contradicted, is the behavior one wants and rarely sees.

9. **Path A is correctly demoted rather than defended**, and the reason given (its own rate-gap coefficient is not distinguishable from zero under any bias-respecting construction) is the right reason.

---

## MAJOR issues

### M1. The pool carrying the headline is not a probability sample of the SOMA book, on exactly the two dimensions that decide censoring. Undisclosed, uncorrected.

**Where.** `hazard/loan_sample.py:97` — the loan pool is built with `per_file = max(1000, pool_target // max(len(pairs), 1))` and `k = min(per_file, len(df))` sampled from **each quarterly origination file pair**, i.e. equal allocation per origination quarter; `_stratified_sample` (line 110) is then proportional *within that pool*. Described in the manuscript only as "a stratified 75,000-loan sample drawn from that universe" (.tex:122) and "stratified 75,000-loan draw from the same universe" (Table 2, .tex:202). Appendix E states the attrition accounting but not the allocation rule.

**Evidence.** `hazard/data/loan_sample.parquet` contains exactly 15,000 loans per vintage year — 20.0%/20.0%/20.0%/20.0%/20.0% by count for 2017–2021, 17.8/17.9/19.7/22.2/22.3% by original UPB. Mean coupon by vintage: 2017 4.2%, 2018 4.7%, 2019 4.2%, 2020 3.2%, 2021 3.0%. Pool WAC 3.86% unweighted, 3.78% UPB-weighted; the `weight` column is 1.0 for all 75,000 rows, so no post-stratification is applied anywhere.

Compare the two targets, both from `composition_shift_results.json`:

| Vintage group | Draw (count) | Estimation universe (exposure, window open) | SOMA book (face) |
|---|---|---|---|
| 2017–19 | 60.0% | 12.5% | 6.0% |
| 2020 | 20.0% | 37.3% | 16.3% |
| 2021 | 20.0% | 50.2% | 43.9% |
| 2022 | 0.0% | 0.0% | 23.1% |

The oldest, highest-coupon vintages are over-represented ten-fold relative to the book; the 2021 vintage, 43.9% of book face, is under-represented by 2.2×.

**Why it bites, using the paper's own mechanics.** Under (1) with the hard maximum, the per-loan-month marginal is `max(floor, H·d) − max(floor, H)` where `H` is the PSA baseline times the covariate/burnout terms and `d = exp(β₁g) < 1`. Three regimes: if `H < floor` the marginal is **exactly zero**; if `H·d < floor < H` it is `H − floor`, capped and gap-independent; if `H·d > floor` it is `H(1−d)`, increasing in |g|. So seasoning is a hard gate and gap depth sets the position within the cap.

- **Seasoning limb, signed inflationary.** The 2021 and 2022 vintages are 67.0% of book face. At window open they are aged 6–18 and 0–2 months, so on a 100 PSA ramp their baseline CPR is 1.2–3.6% and 0–0.4% — **below the 4.99% headline floor**. Where the null itself is pinned, §V.E states the point precisely: "switching the elasticity off cannot raise the hazard at all." So for two-thirds of book face the marginal is zero for roughly the first 18–36 months of the window. In the draw that segment is 20% of loans and the 2022 vintage is absent entirely. The paper reports the null's floor-bind share as 35.8% of loan-months at the headline floor — measured on the draw. On a book-composition pool it would be materially higher, and the marginal correspondingly lower.
- **Gap-depth limb, signed the other way.** The draw's 60% at 4.2–4.7% coupons sit in the uncapped `H(1−d)` region rather than at the `H − floor` cap, which deflates.

Neither limb is signed anywhere in the paper, and the two do not obviously cancel. `vintage_overlay` scores the *out-of-window* 33.7% share to zero marginal (→ +3.7 points), which is the extreme version of the seasoning limb for 2022 and pre-2017 — but nothing covers the in-window distortion (2021 at 43.9% of book vs 22% of the draw). The coupon reweight of §VII.E rescales aggregate output rather than re-simulating a book-composition pool, and reports the marginal as bit-invariant, which cannot be a test of a composition effect that operates through per-loan censoring.

**Fix.** (i) State the allocation rule in Appendix E in one sentence — "the pool is drawn with equal allocation per origination quarter, so the draw's vintage composition is approximately uniform over 2017–2021 and is not proportional to origination volume or to book face" — and add the draw's own composition row to Table 25 beside the universe panel's. (ii) Run the central/null pair on a book-composition pool: post-stratify the existing 75,000 loans to the SOMA coupon × vintage-group cells and re-derive the marginal. This is exactly the machinery `cross_design_reweight` already implements on the ABM side, so it is one run, not a new design. (iii) Put the result in Table 5's assembly with its direction. Until (ii) exists, the honest statement of the headline is "+5.6 points on a pool whose vintage and coupon composition differ materially from the book's, in directions that have not been signed," not "+5.6 points of the benchmark."

### M2. Table 25 mixes two different objects: universe bucket shares with the draw's WAC. §VII.E's reweight is anchored on the draw's number.

**Where.** Table 25 panel (a), coupon row, .tex:1282: "Coupon | <3.0%: 18.0; 3.0–4.0%: 68.2; ≥4.0%: 13.8 | 73.9; 18.7; 7.3"; note at .tex:1294: "Sample coupon shares are exposure-weighted universe-panel shares at the window open; the sample WAC is 3.9% against the book's 2.49%." §VII.E: "the Freddie sample's composition, whose weighted-average coupon (3.9%)."

**Evidence.** The 18.0/68.2/13.8 shares are `freddie.universe_panel.coupon_shares_exposure_weighted` and imply a WAC of ≈3.14% on bucket midpoints. The 3.865% figure is `freddie.sample.mean_coupon_pct` — the 75,000-loan draw, whose ≥4.0% share is **53.7%**, not 13.8%. Two objects, one row.

**Consequence.** The full-book reweight's origin (3.9% → 2.49%) is the draw's WAC, while the shift it is displayed against is the universe's. Appendix A records that a previously published 18.3-point gap was a basis-mixing error; this is the same class, in the table whose stated purpose is to bound the sample-to-book extrapolation.

**Fix.** Print both rows in Table 25 (universe and draw), label which object each is, and state in §VII.E which one the reweight is anchored on.

### M3. The off-window floor imports 2018's housing-activity level. The assembly is missing its one upward floor-side correction, and the paper's own anchor can size it.

**Where.** §VII.F's matched-depth decomposition (window component −\$20.874bn, 73.7% of the demotion; depth −\$7.438bn, 26.3%); Table 6; "Definitions used throughout"; Table 5's seventh-qualification assembly.

**Argument.** The floor is explicitly *total* deep-discount turnover — §V.B: "it includes discretionary life-cycle moves and cash-out refinancings alongside strictly involuntary events, and the strictly-involuntary share … is plausibly well under half." Total turnover on discount cohorts is therefore a function of the housing-market activity level, and the two windows are not comparable on it: existing-home sales ran 5.34M in 2018 against 4.09M (2023) and 4.06M (2024) on a comparable owner-occupied stock — a ~24% lower transaction rate. The paper's own in-window read of 3.8–3.9% is almost exactly the off-window 4.99% scaled by that ratio (4.99 × 0.77 = 3.84), which is at minimum a coincidence that demands a test.

The demotion charges 73.7% of the move to "the window," and §VII.F reads that as lock-in circularity in the in-window read. But part of the 2018-to-2023 activity decline is not lock-in — affordability at the *level* of house prices and rates, inventory, demographics — and the paper has already catalogued the anchor that splits it: Aladangady et al. (2024) attribute 44% of the 2021–2022 mobility decline to rate-gap lock-in. Applied to the window component, up to 56% of \$20.874bn ≈ **\$11.7bn ≈ +1.5 points** of the demotion is a housing-cycle level effect wrongly charged to circularity. That places the headline near +7.1 points — inside the binding interval, but in its **upper** half, which reverses §V.E's posture that "every correction I can measure to the floor or to the accounting basis moves it down."

**Fix.** Measure the floor's dependence on housing activity across the 2017–2019 reads (the three legs already differ in activity as well as in rate regime), instrument the activity level with something not driven by the coupon gap (new-home sales, the all-cash transaction share, or the non-mortgaged share of existing-home sales), and report the marginal at an activity-matched off-window floor. Add it to Table 5 as the assembly's first upward floor-side entry, or state explicitly that the assembly is one-directional because the one available upward floor-side correction was not run. The second is acceptable; the current silence is not, because §V.E's "every correction … moves it down" is doing real rhetorical work.

### M4. The Ginnie differential is attributed to buyouts; the paper's own series says voluntary speeds carry the majority. The voluntary piece is the one that bears on the imported elasticity.

**Where.** .tex:269: "with the involuntary buyout channel (CDR 2.1% versus 0.4% in May 2025) supplying most of the structural difference."

**Evidence.** From `gmar_dec25_cpr_series.json`, June-2022–Nov-2025 means (42 months):

| Series | Ginnie | Freddie | Gap | Share of CPR gap |
|---|---|---|---|---|
| CPR (total) | 8.337 | 6.200 | +2.137 | — |
| CRR (voluntary) | 7.295 | 5.941 | **+1.354** | **63%** |
| CDR (involuntary) | 1.161 | 0.314 | +0.847 | 40% |

The May-2025 snapshot the sentence quotes is the one month where buyouts dominate (1.71 of a 2.84 gap). On the window mean, the majority of the Ginnie excess is **voluntary**.

**Consequence.** ~1.35 CPR points of faster *discretionary* turnover on FHA/VA collateral — 20.4% of book face, onto which Freddie conventional hazards *including the imported lock-in elasticity* are extrapolated as-is. That is a behavioral difference, not a mechanical one, and it says the imported elasticity is too strong on a fifth of the book. The overlay treats it only as a level correction, and the marginal correction is pure conventional-share scaling (0.797×), i.e. it assumes the Ginnie share generates *zero* marginal rather than a *weaker* one — an assumption the CRR series can replace with a measurement.

**Bonus the paper is leaving on the table.** §I concedes that "realized take-up of that statutory right is not measured anywhere in this design, so the 20.4% share bounds the carve-out from above." Its own data answer this: an assumed loan **does not prepay**, so materially high assumption take-up would show as *slower* Ginnie voluntary speeds. Ginnie CRR running 1.354 points *above* conventional over the window caps assumption take-up at a level that cannot be materially slowing Ginnie payoffs. That converts an open-ended limitation into a signed bound with no new data.

**Fix.** (a) Restate the attribution as a window mean, not a snapshot, at .tex:269. (b) Score a Ginnie leg with the elasticity attenuated by the observed CRR differential rather than only share-scaled to zero, and report the resulting marginal. (c) Add the assumability bound to §I and §VIII.A.

### M5. The buyback-credit discount proxy is a zero-prepayment PV applied to a leg that prepays at 5.61% CPR. Every reversal magnitude is roughly double.

**Where.** .tex:273: "against a proxy discount of 32 to 34% at the representative 3.0% coupon / 6.8% market state (36 to 38% at the book's 2.49% weighted-average coupon)"; Table 1 row 8; §VI.D; §VIII. `buyback_credit_bracket_results.json` records the grid `D ∈ {0.32, 0.34, 0.36, 0.38}` as "the manuscript's committed proxy range" and does not derive it.

**Evidence.** I priced the cash flows independently. A 3.0% pass-through with ~340 months remaining, discounted at 6.8%:

| Coupon | 5% CPR | 8% CPR | **0% CPR** |
|---|---|---|---|
| 3.00% | 79.1 (disc. 20.9%) | 82.9 (17.1%) | 63.5 (**36.5%**) |
| 2.49% (book WAC) | 76.4 (23.6%) | 80.5 (19.5%) | 59.4 (**40.6%**) |

The paper's 32–38% band is what a **zero-prepayment annuity PV** produces (36.5% and 40.6%). Prepayment-consistent prices give 21–24%, which is also where observed TBA marks for 2.0–2.5% 30-year coupons sat at the 2023 trough (≈75–80). Using the 6.8% *primary mortgage rate* as the discount yield is itself conservative-for-discount, since MBS yields ran 100–150bp below primary rates.

**Consequence.** `gap_cash = 61.188 − D × 470.653`. At D = 0.22–0.24 the gap is **−\$43bn to −\$52bn**, not −\$89.4bn to −\$117.7bn. The sign reversal survives, so §VIII's incidence-conditional conclusion stands — but the magnitudes carried into Table 1, §V.B, §VI.D and §VIII are ~2× too large, and the paper's own statement that "a market-value credit would reduce the Danish leg's cash receipts by an amount **larger than** the \$61.2bn gap itself" is true at 22–24% but by a factor of 1.7 rather than 2.5–2.9.

**A deeper institutional point in the same place.** In Denmark the borrower's market-value payoff is executed by **buying the underlying bonds in the market and delivering them** (or by notice-based par redemption on the call side). The bondholder therefore sells at market voluntarily and is not haircut; what shrinks is the issuer's balance sheet, by the face of the delivered bonds. Transplanted onto a passthrough *holder* like the SOMA, the analogue is an **outright sale at a discount**, not a redemption — which is economically the "active sales" alternative §VI.B raises, and which means the par-denominated cap benchmark is not the right scorer for the Danish leg at all. The paper frames this as an incidence choice between "balance adjustment" and "cash haircut"; the mechanics say it is neither, it is a sale.

**Fix.** (a) Derive `D` from the Danish leg's own simulated cash flows at its own 5.61% CPR against the window's market-rate path — the pipeline holds both — or from matched-coupon/matched-month TBA marks, and restate the bracket everywhere it appears. (b) Add one sentence in §VI.D stating that the Danish mechanism is a bond repurchase, so under the transplant SOMA's redemption stream becomes a market-value retirement and the par-denominated cap is not the natural scorer. (c) Report the Danish counterfactual in duration units alongside dollars — Table 12/Appendix L already give 9.1 vs 9.7 years — since that metric is invariant to the incidence question the dollar metric cannot resolve.

### M6. The Danish headline pins the sweep edge that the paper's own realized-Denmark evidence most contradicts.

**Where.** §VI.D; Table 1 row "Danish rule-only counterfactual | +\$61.2 billion"; Table 13 note d; §VIII.

**Evidence.** `danish_redemption_validation` finds realized deep-discount (≤2% coupon) Danish callable redemptions at 26.4%/yr against a 4–5% baseline over 2022M07–2023M12, an extraordinary component of at least 22%/yr. The production Danish leg prepays at 5.61% CPR. The swept refinance-in-place band runs +\$61.2bn at 0% to +\$256.8bn at 3% CPR; the realized-implied anchor prices at +\$1,212bn.

**Consequence.** The paper headlines the **minimum** of a band whose only realized observation of the mechanism lies above the band's top, while simultaneously conceding that positivity is anchor-forced so that "the informative content is the magnitude." The magnitude is being read at the least-supported point in its own range. This is inconsistent with how the paper treats its US marginal, where it explicitly refuses to privilege an interior member and headlines the range.

**Fix.** Headline the band [+\$61.2, +\$256.8]bn in the abstract, Table 1 and §VIII, exactly as the abstract already does for the lock-in marginal's range; promote the realized-implied anchor and its four confounds from a subordinate clause to a sentence in the main text.

### M7. 100 PSA is doing more work than the elasticity, and it is a convention where an estimate is available.

**Where.** Table 2 age-profile row; Table 3 ("PSA speed | 100 | – | industry seasoning convention"); .tex:333: "the widest disclosed layer is the baseline level: sweeping the seasoning ramp over 75 to 150 PSA on both legs carries the marginal from +0.9 to +15.6 points at the off-window floor."

**Argument.** At the headline floor the central leg is pinned in 68.8% of loan-months, so the marginal is essentially the integral of `H − floor` over the months where the null clears the floor. With a 6% PSA plateau against a 4.99% floor that window is 1.0 CPR point wide. A 75-PSA plateau (4.5%) closes it almost entirely — hence +0.9 — and 150 PSA (9%) quadruples it. The paper concedes the sweep has "no coverage property," calls the floor read "binding," and keeps 100 PSA.

**Consequence.** The layer named binding, [+2.9, +8.7], is 5.8 points wide and prices the floor read's sampling error *at a fixed 100 PSA*. The unpriced convention alone spans 14.7 points. Ranking the floor read as binding is a statement about which layers have a coverage property, not about which layer determines the answer, and the abstract does not make that distinction visible. There is also no domain reason to use 100 PSA here: 100 PSA's 6% terminal CPR happens to land near observed 2022–2025 OTM turnover, which makes it a coincidence rather than a calibration, and the whole point of the exercise is that this window's turnover is *not* the historical convention.

**Fix.** Estimate the baseline from the panel. The raw material is already in hand: Path A's seasoning spline (knots {12,24,36,60,84,120}), the 2018 leg's own age ladder (3.78% below 12 months, 5.33% at ≥12), and Appendix J's 3.68/5.78/10.99% ladder. Report the marginal at an estimated OTM age profile as the headline with 100 PSA as robustness, or state the headline as a (baseline, floor) pair rather than a single number. As it stands the abstract's "+5.6 points" is conditional on an industry convention in a way no sentence in the abstract discloses.

### M8. The benchmark's monthly series is built by differencing weekly Wednesday SOMA levels — the wrong frequency for MBS paydowns — and the window-boundary allocation is unpriced.

**Where.** §III.B (.tex:137): "from the New York Fed's SOMA current face value series, netting realized roll-off against the actual phased redemption cap schedule"; Appendix N; §VII.B (`settlement_months_benchmark`).

**Evidence.** `h1_zero_months_diagnosis.json` shows the underlying weekly observations. For February 2023: 2023-01-25 = 2616.2735, 2023-02-01 = 2616.2735, 2023-02-08 = 2616.2735, 2023-02-15 = 2615.0506, 2023-02-22 = 2611.7887 — three identical weeks, then a step. This is the standard pattern: MBS holdings move only on paydown-posting and settlement dates, and the agency factor/remittance cycle posts around the 20th–25th. The `span_last_asof` convention (last Wednesday) therefore truncates the part of the month's paydown that posts after that Wednesday into the next month's reading. All four "zero" months are clip artifacts (unclipped −1.586/−0.493/−0.841/−0.841 CPR points), each followed by a spike to 9.4–14.1% annualized, with the pair totals conserved.

**Consequence.** The 42-month total is robust because the pairs conserve — which is why \$764.7bn holds and why I do not dispute it. But (i) the monthly series is unusable for timing, which the paper now concedes but does not fix, and (ii) at the window boundaries there is no partner month to cancel into: June 2022's reading is +\$1.987bn against an \$8.091bn partner in July, and the pre-window Jan–May 2022 rise of \$92.3bn is settlement of pre-window purchases. §VII.B prices the *cap*-side convolution (−5.5%, of which the entire \$42.0bn is the half-open window's dropped tail) and never the realized-side boundary allocation.

**Fix.** Rebuild the monthly series from the published monthly SOMA agency-MBS **principal-payment** data — which is what the cap is actually defined on, and which Na et al. (2024), whom the paper cites, themselves decompose into scheduled and prepayment components — or from CUSIP-level factor changes. That retires Appendix N's four clip zeros, lets the monthly-timing question be reopened on a clean series (the paper currently forecloses timing on the strength of a defect in its own comparator), and lets the window-boundary sensitivity be priced rather than assumed away.

---

## MINOR issues

1. **§III.B's coupon-convention sentence is self-contradictory as written** (.tex:146): "both amortize on the pass-through convention where scheduled principal physically follows the borrowers' note rates (the pass-through WAC plus the guarantee-fee and servicing wedge, +0.80 points)." The pass-through WAC *plus* 0.80 is the note rate, so the clause names both conventions at once. Rewrite as: "both amortize at the pass-through WAC; scheduled principal physically follows the note rate, which is the pass-through WAC plus a +0.80-point g-fee and base-servicing wedge, and recomputing on that basis raises the CPR level by +0.27 points."

2. **The corrected note-rate CPR never becomes the comparator.** The paper concedes the note-rate convention is physically right and that "Table 24 is scored on the corrected basis," but Table 10's benchmark row keeps 5.14% (hazard-basis 5.52%, note-rate 5.79% in parentheses), Table 12's WAL row is "Empirical path (5.14%)" (.tex:559), and every simulated-vs-empirical CPR comparison in §IV, §V and §VII.C uses 5.14%. On my own calculator, a single-pool 2.49% 30-year moves from 7.72 to 7.25 years between 5.14% and 5.79% CPR — a ~0.5-year revision to a table whose Danish rule-only headline effect is 0.6 years (.tex:540). Restate Table 12's empirical row at the corrected convention or print both columns, and say which comparator each CPR comparison uses.

3. **Burnout initialization is unstated and looks inconsistent with its own definition.** §V.B defines *B* as "the stratum's cumulative prepaid UPB as a share of its original UPB." Appendix E reports that 34,734 of 75,000 sampled loans prepaid before the window opens. If pre-window prepayment counts, *B* ≈ 0.46 at window open and the multiplier is e^(−0.23) ≈ 0.79 from the first month; the \$6.58bn / \$3.48bn ablations suggest it does not. Report *B*'s window-open distribution in Appendix E and state whether pre-window attrition is counted. This also interacts with the survival-selection transport the paper already prices in `attenuation_sensitivity`.

4. **§VI.C's FHFA claim carries no citation** (.tex:580: "U.S. policymakers, including the Federal Housing Finance Agency (FHFA), proposed expanding assumable and portable mortgages"). "assumab" appears only twice in the entire .tex, for a channel that covers 20.4% of the book by statute. Cite the actual proposal, plus HUD Handbook 4000.1 and the relevant VA circular for the assumption mechanics and the second-lien gap.

5. **The default baseline has free external corroboration the paper does not take.** h^def_0 = 3×10⁻⁴/month is 0.36% annual CDR, listed as a round "calibration prior." The paper's own GMAR extraction puts realized Freddie CDR at 0.314% window-mean. Say so — it is one of the few priors with an external check, and it passes.

6. **A constant floor is inconsistent with the age profile of the reads that calibrate it.** The floor enters (1) as a single constant SMM with no age argument, while its own measurement is strongly age-dependent (Appendix J: 3.68% below 12 months, 5.78% at 12–24, 10.99% at 24–36). At minimum note that the floor's flatness in age is an assumption contradicted by the ladder used to set it; better, sweep an age-varying floor, since the paper already sweeps a rate-varying and a calendar-varying one.

7. **"\$83 billion per CPR point" is used to convert two separate bounds and is never derived.** It checks out (≈\$2.4T average book × 3.5 years ≈ \$84bn), so state the derivation once in §V.B.

8. **§VI.A's "roughly six extension-years" is measured against a refi-boom comparator in the same breath as conceding that it is one.** Table 12's note correctly flags the 22.81% row as a refinancing-boom baseline and adds the 4.99% turnover-floor row (9.5/8.6 years) as "the normal-turnover counterpart." Quote the extension against *that* row too — 9.4 vs 9.5 years, i.e. essentially zero — so the reader can see that the entire "extension" is refinancing versus turnover rather than lock-in versus normalcy.

9. **"Assumable by statute" needs one qualifier.** FHA and VA loans are assumable, but subject to creditworthiness qualification of the assuming borrower, servicer processing, occupancy restrictions, and VA entitlement-restoration considerations. The 20.4% share bounds the carve-out from above only if assumption is frictionless, which it is not — worth one clause where the claim is made in §I.

10. **Table captions are duplicated into the first cell of the header row** in Tables 1, 8, 9, 25 and 27 (visible in the .md rendering, e.g. "| \caption{Core results and operative uncertainties…} Object | Headline value | …"). A build/converter artifact rather than a content error, but it will read as sloppiness in a submitted PDF.

---

## Missing references

Each of these is a reference a domain referee would require, with what it changes.

1. **Deng, Y., J. M. Quigley & R. Van Order (2000), "Mortgage terminations, heterogeneity and the exercise of mortgage options," *Econometrica* 68(2), 275–307.** The canonical competing-risks prepayment/default estimator with unobserved heterogeneity — i.e. Path B's exact structure. §V.B currently positions its competing-risks discussion against Fine–Gray, Putter et al. and PyDTS (biostatistics methods) with no anchor in the mortgage literature that built the estimator. It also supplies the frailty/heterogeneity apparatus that `attenuation_sensitivity`'s gamma-frailty identity assumes. `references.bib` contains `quigley2002` (Quigley, "Homeowner mobility and mortgage interest rates," *REE*) but not this.

2. **Hanson, S. G. (2014), "Mortgage convexity," *Journal of Financial Economics* 113(2), 270–299.** Establishes that the outstanding coupon distribution determines aggregate MBS duration and feeds back into long rates. §VI.A and §VIII build a convexity-and-hedging argument on Gabaix–Krishnamurthy–Vigneron (2007) and Malkhozov et al. (2016) but omit the paper that quantifies the mechanism the SOMA's low-coupon stock embodies. This is the reference that turns "convexity-neutral duration profiles" from a label into a measured channel.

3. **Frankel, A., J. Gyntelberg, K. Kjeldsen & M. Persson (2004), "The Danish mortgage market," *BIS Quarterly Review*, March, 95–109**, and **Svenstrup, M. & S. Willemann (2006), "Reforming housing finance: perspectives from Denmark," *Journal of Real Estate Research* 28(2).** §VI.D transplants "only the payoff rule" and enumerates what it omits (Balance Principle, series-level match funding, tap issuance, advisory distribution, the IO share), but cites only Berg–Nielsen–Vickery (2018) for the institution. Frankel et al. is the source that specifies *what* is being omitted and, critically for M5, that the market-value payoff is executed as an **open-market bond repurchase and delivery** rather than as a discounted loan payoff. Svenstrup–Willemann is the companion for §VIII's reform-design argument.

4. **Fonseca, J., L. Liu & P. Mabille, "Unlocking mortgage lock-in: evidence from a spatial housing ladder" (working paper).** General-equilibrium lock-in with spatial housing-ladder feedbacks. Every counterfactual in this paper — the β₁=0 null, the Danish transplant, the moving-share bracket — is strictly partial-equilibrium, and the imported elasticity is a partial-equilibrium moving response. This is the reference that says how much of that response survives GE, and it is the natural qualifier on the transport assumptions §V.B enumerates.

5. **López-Salido, D. & A. Vissing-Jørgensen (2023), "Reserve demand, interest rate control, and quantitative tightening"** and/or **Acharya, V., R. Chauhan, R. Rajan & S. Steffen (2024), "Liquidity dependence and the waxing and waning of central bank balance sheets."** §III.B's standing concession — "nothing in this paper shows that reserves or the aggregate path came in off the intended course because MBS ran slow" — is precisely the question these papers take up. Citing them converts an isolated self-limitation into a positioned claim and is the cheapest available upgrade to the section a referee will press hardest on.

6. **Aiello, D. J. (2022), "Financially constrained mortgage servicers," *Journal of Financial Economics* 144(2), 590–610.** The paper names servicer behavior beyond the delinquency pipeline as unmodeled and **unbounded** in §V.F, §VI and §VIII.A — three separate admissions with no sign attached. This is the paper that measures the servicer channel's effect on prepayment and default outcomes and would let the paper state a direction for the one residual candidate it currently leaves signless.

7. **Fuster, A., D. Lucca & J. Vickery, "Mortgage-backed securities" (NBER WP 28966 / *Handbook of Fixed-Income Securities*).** The standard institutional survey of TBA, pooling, and prepayment. §I's and §VIII's TBA-homogeneity argument currently rests on Vickery–Wright (2013) and Gao–Schultz–Song (2017) alone; a survey citation lets the institutional claims travel without each one needing its own primary source.

8. *Optional:* **Diep, P., A. Eisfeldt & S. Richardson (2021), "The cross section of MBS returns," *Journal of Finance* 76(5).** Prices prepayment risk by coupon, which is what §VI.A/§VIII's hedging discussion presumes and what M5's discount question turns on.

---

## Scores

| Dimension | Weight | Score | Basis |
|---|---|---|---|
| Originality | 20% | **74** | The mechanical-vs-elastic decomposition of the QT MBS shortfall, the ex-ante cap arithmetic, and the expectations-based complement are genuinely new in the QT-implementation literature, and no one has priced the Danish payoff rule against the SOMA book. But the paper itself concedes the mechanism, the below-cap regime, and the ex-ante-projection observation are pre-existing (Na et al., Perli, Hammack, York 2022); what is new is the quantification and the decomposition architecture. The Danish transplant is original in application but category-questionable in construction (M5, M6). |
| Methodological Rigor | 25% | **60** | The pre-commitment apparatus is exceptional and the retractions are real (within-stratum bootstrap, the 0.2-point convergence, percentile→wild-cluster). But six domain-level convention defects survive it: the headline pool is not a probability sample of the target book on the dimensions that set censoring (M1), the composition table is pointed at the wrong object (M2), the dominant baseline is an unestimated industry convention when the data to estimate it are in hand (M7), the off-window floor imports another market's activity level with the sign that flatters the demotion (M3), the benchmark is built at the wrong frequency for MBS paydowns (M8), and the buyback discount is a no-prepay PV (M5). None is a coding error; the gate suite could not catch any of them, and the paper's disclosure of other limitations is not a substitute. |
| Evidence Sufficiency | 25% | **57** | Voluminous and well-frozen: 17.6M-loan Fannie replication, ~200 artifacts, externally validated GMAR extraction, Danmarks Nationalbank statistics. But the claim actually made — that the lock-in marginal *on the SOMA book* is [+2.9, +8.7] points — is not supported by evidence computed on a population representative of that book (M1), the range's width is set by a layer that is not the widest (M7), target-book coverage is 51% of face with the rest bounded by proxies, the elasticity's evidential base is entirely external with no standard error propagated, the paper's own in-sample estimate of the same channel cannot reject zero, the second estimator supplies no differential, and there is no outcome holdout anywhere. |
| Argument Coherence | 15% | **74** | The strongest dimension. Levels vs marginals kept rigorously distinct, four accounting bases kept straight after a previously retracted basis-mixing error, range-not-point posture held consistently through abstract/Table 1/§V.E/§VIII, sign explicitly demoted to a specification check, Path A explicitly excluded. §V.E's seventh qualification is a model of adverse-finding assembly. Deductions: the assembly is one-directional only because its one available upward floor-side correction was never run (M3); the Danish headline pins a band edge while the text argues the magnitude carries the content (M6); §VIII concedes the trilemma dissolution "reduces to 'the marginal is small'" and is bounded small "by construction" under the production form, so the policy conclusion rests on a calibrated ceiling. |
| Writing Quality | 15% | **60** | Sentence-level precision is high and the hedges are load-bearing, not decorative; the table notes and the "Definitions used throughout" block are genuinely good devices. But readability delivered is poor: a 2,200-word single body paragraph in §V.B, sentences nesting 4–6 parentheticals and multiple em-dash asides, and qualification density that forces re-reading of load-bearing clauses (the §III.B coupon sentence is unparseable as written). 139pp total and 94pp of main text is roughly double a field-journal norm for this content. Duplicated captions in five table headers. |

**Weighted final: 74(0.20) + 60(0.25) + 57(0.25) + 74(0.15) + 60(0.15) = 14.8 + 15.0 + 14.25 + 11.1 + 9.0 = 64.2 / 100**

## Recommendation

**MAJOR REVISION.** The score lands at the top of the Major band, and that matches the substance: the sign and the qualitative decomposition are safe, but three of my eight major issues (M1, M3, M7) can move the reported headline point, and one of them (M3) moves it *up*, which would reverse §V.E's "every measurable correction moves it down" posture. Two more (M5, M6) change published magnitudes by roughly a factor of two. Five of the eight are executable with existing machinery — a post-stratified book-composition re-run, an activity-matched floor read, an estimated seasoning baseline, a prepayment-consistent discount proxy, a restated Ginnie attribution — and none requires new data. That is a revision, not a rejection: the underlying decomposition, the disclosure discipline, and the replication apparatus are all worth publishing once the estimation population is shown to represent the book it is scored against, and once the conventions that dominate the answer are estimated rather than assumed.

## Carroll Round judgment

**Ready to present and defend as-is** — the decomposition, the honesty of the adverse-findings register, and the artifact discipline will read as exceptional at an undergraduate international-economics conference — provided the author prepares a 15-minute path through the 139 pages, can answer "is your 75,000-loan pool a sample of the Fed's book?" (M1) in one slide, and stops quoting the −\$89bn-to-−\$118bn Danish cash figure out loud until the discount proxy is re-derived at the leg's own prepayment speed.

---

# Peer Reviewer 3 — Cross-Disciplinary Perspective

# Referee Report — Peer Reviewer 3 (Cross-Disciplinary Perspective)

**Manuscript:** "Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"
**Reviewer position:** housing economics / public policy / applied econometrics adjacent to macro-finance
**Basis of review:** full read of `~/Downloads/UPLOAD_ROUND11/revised_paper_v18.md` (1,143 lines, end to end) plus `paper/v18/revised_paper_v18.tex` for paragraph and table detail, and read-only inspection of 12 frozen artifacts in `hazard/data/` (`oos_identification_results.json`, `matched_depth_reconciliation_results.json`, `buyback_credit_bracket_results.json`, `expectation_benchmark_results.json`, `scaled_null_housing_activity_results.json`, `extension_risk_results.json`, `loan_sample.parquet`, `microsim_results.parquet`, and others). **No repo script was executed**; artifacts were read with `python3`/`pandas` only. No file was modified.

**Untrusted-data check:** I found no text in the manuscript or in any artifact directed at a reviewing agent, and no embedded instructions. One artifact field carries an interpretive claim the manuscript itself retracts (see Minor 1); I treat that as a stale documentation string, not an instruction.

---

## 1. Summary

The paper measures how much of the Fed's $764.7bn agency-MBS runoff shortfall against its QT redemption caps (June 2022–November 2025) is attributable to mortgage lock-in rather than to mechanics. Its central move is a paired-run differential (Eq. 4): a loan-level competing-risks microsimulation on 75,000 Freddie loans, with an elasticity imported unmodified from Liebersohn–Rothstein (2025), minus the same run with that elasticity switched off. The headline is deliberately deflationary — the null already recovers 85.7% of the benchmark, and the elasticity's own contribution is reported as a range, $[+2.9,+8.7]$pp, with $+5.6$pp / $+42.6$bn named as the value at the headline calibration. A Danish market-value-repurchase transplant gives a $+\$61.2$bn institutional gap under face accounting, reversing to $-\$89.4$ to $-\$117.7$bn under cash accounting.

Judged on execution and internal discipline, this is an unusually mature manuscript — 139pp, 108 liveness gates, 495 tests, ~200 frozen artifacts, and a 27-row self-administered adverse-findings register (Table 27) that retracts several of the paper's own earlier claims. I could not find a basis-mixed comparison, an unlabeled floor calibration, or an internally inconsistent headline number anywhere in the main text, and I looked hard.

My concerns are almost entirely at the level my brief covers: **what the paper is a measurement of, and for whom.** The paper's stated bottom line — the mobility cost is real, the institutional cash-flow cost is small — sets a measured quantity against an imported one, in units that are not commensurable, and neither side is the object the paper's own motivating channels (duration extension, fragility, labor reallocation) actually require. The identified marginal contributes roughly 0.6 of ~6.0 duration-extension years (Appendix L), contributes nothing measured to the household side, and is quoted as a share of a denominator §III.B expressly declines to call a policy miss. Separately, the paper leaves on the table a free external-validity test — the count of foregone payoffs its own runs already imply — which is the only outcome-side check available to a design with no holdout months, and which its own artifacts suggest it would not comfortably pass. And the policy section that a public-policy reader will turn to first (§VI.B) states a cap-design arithmetic without an objective function and without the one deliverable a cap-setter would need.

None of this is fatal. Most of it is fixable by reframing plus two or three runs the existing pipeline already supports. But it is enough that the paper as submitted is not yet a paper a housing economist or a public-finance reader can act on, and it caps my evidence and coherence scores well below what the polish would suggest.

---

## 2. Strengths

These are specific, and I would want them preserved through any revision.

1. **Table 11's notes are the most honest paragraph I have read in a calibration paper.** The observation that `recovery = 1 + error/764.7` — so that a large additive constant sits inside every percentage in the table — followed by the reframing of the in-sample 107.0% as an *8.2% under-prediction of the $652.8bn actually realized*, and by the per-row error shares ($+8.2\%, -2.5\%, +0.4\%, -6.1\%, +25.1\%, +6.7\%$), voluntarily dismantles the paper's own most flattering statistic. Most authors would have printed 97.9% and stopped.

2. **Appendix O / Table 27 is a transportable research-practice contribution, not decoration.** Each of the 27 rows states the committed rule, the outcome, *and the adjudication's direction relative to the headline*. It is where the paper retracts a 37× understated bootstrap, a 0.2-point "convergence" with the Fed's ex-ante projection, an 18.3-point basis-mixing error, and the evidential status of its own 27-cell positivity check. The framing sentence — "a green gate suite is therefore not self-certifying" — is exactly right and is not a sentence one usually gets from an author who built the gates.

3. **Basis discipline.** Four accounting bases, an exact invariance proof for the marginal, a month-by-month cancellation argument that covers arbitrary time profiles, and then $\pm 25\%$, seasonal, regime-split, and two-servicer demonstration runs (§VII.E). The Danish-leg curtailment differential is even carried to $-\$1.68$bn on the production anchor after the author *withdraws* the earlier immateriality claim.

4. **Choosing the right estimand against self-interest.** Given that the level is floor-dominated, the marginal over the $\beta_1=0$ null is the correct object, and the paper insists on it even though its level figures (97.9%, 100.0% composed) read far better.

5. **§VII.B's settlement-alignment run** is a model of how a benchmark sensitivity should be reported: the $-5.5\%$ shift is decomposed to the exact $\$42.0$bn of cap schedule convolved past the half-open window, bracketed by two alternate kernels, and shown to move *no* dollar quantity in the paper.

6. **§VI.D contradicting its own pin.** The Berger et al. general-equilibrium "$\approx 0$ refinance-in-place" estimate is confronted with realized Danmarks Nationalbank data (26.4%/yr deep-discount redemptions against a 4–5% baseline) and the point estimate is replaced with a band to $+\$256.8$bn. A weaker paper keeps the pin.

7. **The Fannie replication's restraint.** 17.6M loans and 826M loan-months staged through an identical pipeline, and the author then declines to bank the pre-committed 11.06-point envelope gate as evidence ("A gate that wide cannot fail against anything but a sign error"), quoting the 0.52-point agreement instead and correctly limiting what it certifies to pipeline determinism.

---

## 3. MAJOR issues

### MAJOR 1 — The paper's bottom-line comparison is not well-posed: the household side is imported and unmeasured, the institutional side is measured in a unit that is not a welfare unit

**Where.** Abstract ¶2, final two sentences ("The cost to households who could not move is real. The institutional cash-flow cost is small…"); §I ¶13 (md line 29: "household mobility is constrained, as the household-level lock-in literature documents, while the cash-flow shortfall is governed mostly by loan-level and institutional mechanics"); §VI.A final paragraph (md line 417); §VIII's three-considerations paragraph (md line 569); Table 1, which has **no household-side row at all**.

**The defect.** The comparison that carries the paper — leg (2) versus leg (3) of the trade-off — puts a quantity this paper never measures on one side and a quantity it measures in the wrong unit on the other. §VI.A concedes both halves explicitly: "I do not translate the \$764.7 billion shortfall into welfare terms… The welfare-relevant objects are the constrained moves themselves… and the forgone labor-reallocation gains this literature identifies, which my accounting framework does not measure." So the household side rests entirely on citation (Quigley 1987; Ferreira et al. 2010; Fonseca–Liu 2024; Liebersohn–Rothstein 2025; Graybill–Mangum 2026), and the institutional side is denominated in *face principal that failed to arrive*, which is a cash-timing object, not a resource cost. The word "welfare" appears four times, three of them in declinations. The string "per household" appears **zero** times in 1,143 lines. Batzer et al.'s $\$2.4$ trillion of foregone household capital gains — the one household-side magnitude in the paper — appears exactly once, in the literature review (md line 67), and is never set beside the $\$61.2$bn institutional figure it would dwarf by a factor of ~40.

This matters more than a framing quibble, because §V.B and §VIII establish that under the cash-haircut reading legs (2) and (3) are *the same dollars seen from two sides*. If that is right — and I think it is — then the residual welfare question is entirely the deadweight loss from blocked moves, which is precisely the quantity the paper does not measure. The policy conclusion therefore rests on an unmeasured object, and the "real versus small" contrast is an assertion about the relative sizes of a citation and an accounting entry.

**Fix (concrete, uses existing runs).** Two options, and I would accept either.

(a) *Measure the household side in the same unit of account.* The paper's own paired legs already contain it. The central-minus-null differential is foregone prepaid face: $\$42.6$bn at the headline floor, $\$70.3$bn in-sample. Dividing by mean active-loan balance converts it to a count of foregone payoffs. From `hazard/data/loan_sample.parquet`: mean `balance` = $\$126{,}813$ across all 75,000 rows, with 40,234 active at window start, implying ~$\$236$k per active loan; at a SOMA-book average loan size of roughly $\$250$k, $\$42.6$bn ≈ **~170,000 foregone payoffs over 42 months on the SOMA book, ~49,000/yr**, of which the moving share is $s$ (§V.B's moving-share bracket already parameterizes exactly this). Add that as a Table 1 row, price it with Batzer et al. and the Hsieh–Moretti mechanism as bounds, and the two-sided exchange becomes a quantitative statement instead of a qualitative one.

(b) *If (a) is refused, retire the comparison.* Say in the abstract and §VIII that this paper measures the institutional leg only, that the mobility leg is imported at the elasticity and never re-measured, and that the paper therefore ranks the two legs on external evidence rather than on its own.

---

### MAJOR 2 — The foregone-payoff count is a free external-validity test the design never runs, and the paper's own artifacts indicate it would strain

**Where.** "Definitions used throughout" (md line 59): "*no outcome-holdout months exist anywhere in this paper*, without exception"; §VIII.A repeats it. §V.D's `episode_confrontation` (realized gradient $+4.20$ CPR points against the model's implied $+0.94$, a $4.5\times$ miss); §V.E's `scaled_null_housing_activity`.

**The defect.** The paper treats the absence of holdout months as an unavoidable design property. It is not — not for the *household* margin. The design's implied count of blocked transactions is a prediction about an external, public, independently measured aggregate (mortgage-financed existing-home-sale volume), and testing it requires no SOMA holdout at all. The paper never does it, and the arithmetic suggests why the test bites.

Taking the count from MAJOR 1 (~49,000/yr on the SOMA book) and scaling by SOMA's share of 1–4 family mortgage debt (the `microsim_results.parquet` `exposure` column opens at $\$2.70$trn against roughly $\$12.5$–13trn outstanding, ≈21%), the whole-market image is **~230,000 foregone payoffs per year, at most** — "at most" because the $s=1$ production convention applies the imported elasticity to the entire hazard, moving *and* refinancing, so the moving component is strictly smaller. Existing-home sales fell from ~6.1m (2021) to ~4.1m (2023), roughly two-thirds of them mortgage-financed: on the order of 1.3m fewer mortgage payoffs per year. The model's identified marginal therefore accounts for something on the order of **one-sixth** of the observed decline — against Aladangady et al.'s (2024) attribution of **44%** of the 2021–22 mobility decline to rate-gap lock-in, which the paper itself catalogues (md line 69) and uses as a calibration anchor.

I present this as an order-of-magnitude check, not a refutation; the SOMA book is compositionally *more* locked in than the average mortgage, which makes the discrepancy larger, not smaller. But it is exactly the direction the paper's other own-data readings already point: the realized cross-sectional gradient runs $4.5\times$ the model's implied gradient (§V.D), and §VII.F establishes that at the headline floor the elasticity is censored in 68.8% of evaluated loan-months. A model whose rate channel is truncated in two-thirds of its loan-months will under-predict blocked moves, and this test would say so in a unit housing economists can check.

**One asymmetry worth naming.** The paper *does* confront the Aladangady 44% anchor, in `scaled_null_housing_activity`. I read the artifact: the calibration condition is `trapped_null(φ*) − trapped_null(1) = (0.56/0.44)·[central(1) − null(1)]`, solved by deflating the PSA seasoning baseline to $\phi^*=0.754$, which drives the marginal down to $+0.9$pp at the headline floor. Table 5 files that as an "upward-bias entry" — i.e., the reconciliation is resolved in the direction that shrinks the paper's own headline. The alternative resolution of the same tension — the additive floor form, which never censors and returns $+11.2$pp — is disclosed in §VII.F but is **never run against this anchor**. Since the max-versus-additive fork is the single largest open question in the paper, Table 5's Aladangady row is form-conditional in a way the table does not mark.

**Fix.** (i) Run the foregone-payoff check: report the marginal in transaction counts with the moving-share bracket applied, set it against realized mortgage-financed transaction volume, and state the verdict whichever way it falls. This is the paper's first outcome-side external validation and it costs one script. (ii) Re-run `scaled_null_housing_activity` under the additive form and mark Table 5's row form-conditional either way.

---

### MAJOR 3 — The par windfall's fiscal incidence is unexamined, and it changes the sign of what the leg-(3) result means

**Where.** §V.B (md line 217): "the $1-P$ wedge on bought-back face is exactly the par windfall a moving household pays the bondholder under the U.S. rule and keeps under the Danish one, so the cash-flow cost is the disappearance of a household-to-bondholder transfer, not an added resource cost." Repeated at §VIII (md lines 565, 569). Artifact: `buyback_credit_bracket_results.json` (`gap_face_b` = 61.188, `early_face_E_b` = 470.653, `gap_cash_range_b` = $[-117.66, -89.42]$, verdict `REVERSES`).

**The defect, part (a): who the bondholder is.** In this counterfactual the bondholder is the Federal Reserve. The $\$89.4$–$117.7$bn "cash-flow cost" of the Danish rule is therefore a transfer from the SOMA portfolio — hence from Treasury remittances, hence from general taxpayers — to households who move. That is a *fiscal* incidence statement with a distributional sign, and it is the natural way for a public-finance reader to evaluate the rule. The paper never makes it. Searching the manuscript: "taxpayer" — 0 hits; "deferred asset" — 0; "seigniorage" — 0; "remittance" appears only in the agency-settlement-timing sense (§VII.B). The word "transfer" appears in exactly the right sentence and then stops short of the incidence.

This is not a decoration. Under standard marginal-value-of-public-funds reasoning, a transfer from Treasury remittances to liquidity-constrained moving households has a welfare sign the paper's phrasing ("cost to the Federal Reserve") actively obscures. The paper is *closer* to the right answer than its own framing lets it say.

**The defect, part (b): no ex-ante pricing offset.** Every Danish figure is ex-post partial equilibrium. Under a Danish payoff rule, the market-value repurchase option is paid for by borrowers in the coupon — that is why Danish and U.S. mortgage spreads differ, and Berg et al. (2018) and Campbell (2013) are both already in the bibliography. The paper imports Berger et al.'s $\approx$1bp general-equilibrium rate effect for the **refinance-in-place channel only** (§VI.D, md line 450); it never asks what the payoff-rule change itself does to the primary rate. So the $+\$61.2$bn "relief" is a gross figure with the option's ex-ante price omitted. §VI.D lists five omitted Danish features (Balance Principle, series-level match funding, tap issuance, advisory distribution, the interest-only share) and correctly notes the last would move the shortfall the *other* way — but the missing ex-ante coupon offset is not among them, and it is the one an institutional economist will ask about first.

**Fix.** One paragraph in §VIII, plus two lines in Table 13's notes: (i) state that under the cash-haircut reading the wedge is a transfer from the SOMA/Treasury to moving households, not a resource cost, and that its welfare sign therefore depends on the relative marginal value of public funds and household liquidity — which is a question outside this design; (ii) state that all Danish figures are ex-post and carry no ex-ante primary-rate offset, cite Campbell (2013) / Berg et al. (2018) for the Danish spread as the missing term, and add it to §VI.D's omission list.

---

### MAJOR 4 — §VI.B's cap-design arithmetic has no objective function, and the one deliverable a cap-setter needs is missing

**Where.** §VI.B (md lines 421, 440); §III.B's standing concession (md line 111, final sentences).

**Defect (a): "a cap intended to bind" is never justified, and conflicts with the paper's own opening.** §VI.B states: "A cap intended to bind would therefore be set at or below the lower edge of the book's projected scheduled-plus-turnover principal path." The paper never says *why* a binding MBS cap would be desirable. A redemption cap is a ceiling on principal not reinvested; making it bind forces reinvestment of MBS principal above the ceiling, which **slows** the reduction of agency MBS holdings — directly against the Treasuries-only ambition the paper's own §I opens with, and against the Committee's stated preference for reducing agency MBS. Worse, §III.B has already conceded that "a shortfall against the MBS cap is not by itself evidence that a stated policy objective was missed," that Treasury runoff ran against its own caps throughout, and that nothing here shows the aggregate path came in off course. Given that concession, the "$1.7$ to $1.9$ times" result criticizes a ceiling for not being a forecast. The paper's *second* option — "a standing policy of substituting Treasury runoff or outright MBS sales when passive runoff undershoots" — is the one consistent with §III.B, and it is the one buried.

**Defect (b): the state-contingent cap has no mapping.** §VI.B proposes "a cap indexed to the observable state of the outstanding stock (for example, to the share of the book sitting deeply below market coupon)" and then supplies no function from that observable to a cap level — even though every input is already in the repository: the SOMA CUSIP coupon-by-vintage tabulation (`composition_shift_results.json`), the amortization calculator behind Table 12, and the floor band with its wild-cluster interval of 4.177%–5.800% quoted in that very paragraph.

**Defect (c): the result is not stated in the units of a cap decision.** A cap is set in $bn/month. The paper's numbers give that directly: the NY Fed projection implied $\$740.6$bn over 42 months $=\$17.6$bn/month against a $\$33.75$bn/month average ceiling (which is precisely where "1.7 to 1.9×" comes from: $33.75/17.63 = 1.91$; against the settlement-aware allocation's $\$839.5$bn, $33.75/19.99 = 1.69$). And the floor read's own 1.62-CPR-point interval on a $\sim\$2.7$trn book is $\approx\$3.6$bn/month. So the *usable* statement is: **achievable passive MBS principal was ex-ante roughly $\$16$–18bn/month, pinnable to about $\pm\$4$bn — half the cap, with the uncertainty about 20% of the achievable level.** That is a genuinely actionable ex-ante result, and it is nowhere in the paper.

**Fix.** Rewrite §VI.B around three items: (i) the achievable-path band in $bn/month with its floor-read interval, as above; (ii) a two-input table — book out-of-the-money share (from the CUSIP tabulation, at 200/300/400bp cuts) × turnover-floor band — mapping to achievable monthly principal and hence to an implied cap; (iii) an explicit statement of the objective a cap serves. Predictability and communication, not speed — and note that binding the MBS cap is inconsistent with the stated composition goal, so the design recommendation is *publish the projected path with its band and pre-commit the substitution instrument*, not *lower the cap*. That framing also discharges §III.B's standing concession, which currently sits unresolved two sections earlier.

---

### MAJOR 5 — The identified object is second-order for both channels the paper invokes, and is quoted against a denominator the paper disowns

**Where.** Table 12 and Appendix L (md line 1042); §VI.A (md lines 413, 415, 417); §III.B (md line 111); §III.B's expectations complement and §VIII (md line 563).

**The defect.** Three of the paper's own numbers, read together, undercut the motivation:

1. **Duration.** §VI.A says explicitly that "this extension, not the cap arithmetic, feeds the fragility channels below." Table 12 then shows that at the headline turnover floor alone (4.99% CPR) the book's WAL is 9.5 years against the empirical 9.4 — i.e., the entire $\sim$6.0-year extension over the 2021-speed comparator is delivered without any lock-in response — and Appendix L puts the Danish rule-only shortening at **0.6 of those ~6.0 years**. So the identified elasticity accounts for roughly a tenth of the object the paper says matters for fragility. §VI.A does concede this ("a second-order contributor"), but the concession sits one paragraph after the fragility framing and is not carried to the abstract or conclusion.
2. **Mobility.** Unmeasured (MAJOR 1).
3. **Denominator.** Every headline percentage divides by $\$764.7$bn, a gap against a ceiling §III.B says is not a policy miss. Against the economically meaningful denominator — the $\$87.8$bn expectations complement — the same $\$42.6$bn is **49%** under the central allocation, 23% under the settlement-aware one, undefined at the extreme bracket. (I verified: `expectation_benchmark_results.json` records `pp_of_e_benchmark` = 80.09 for the in-sample $\$70.3$bn; $42.6/87.8 = 48.5\%$.) That is an order-of-magnitude difference in how large lock-in looks, and the abstract leads with the version that makes it look small.

The net effect is that the paper's deliverable and its motivation never meet. The marginal is the right object for exactly one purpose — a behavioral band around an ex-ante cap projection (§VI.B) — and the paper frames it around two purposes for which it is not.

Note also that the denominator choice cuts *against* the paper's own subject. "Most of the shortfall is mechanical" is substantially a statement about where the FOMC put the ceiling, not about mortgage markets, and the paper says so ("the caps sat far above what any plausible prepayment environment would have produced"). Leading with it understates lock-in relative to the benchmark the paper itself judges more faithful.

**Fix.** (i) In the abstract and Table 1 row 4, quote the marginal against both denominators in one breath: "$\$42.6$bn — 5.6% of the cap gap, and roughly half the ex-ante surprise under the central intra-2022 allocation (23% under the settlement-aware one)." (ii) In §VI.A, state the marginal's share of the extension in maturity units (0.6 of ~6.0 years) at the point the fragility channel is introduced, not after. (iii) Either add a market-value/DV01 image of that 0.6 year on the book — the paper cites Jiang et al.'s $\$2$trn for banks but never puts a mark-to-market number on SOMA, and Appendix L declines option-adjusted duration as out of scope — or restrict the institutional-cost claim explicitly to cash-flow timing and drop the fragility framing to a single referenced sentence.

---

### MAJOR 6 — "Mechanical" mislabels a null whose level is set by realized turnover — and the paper's own depth ladder both proves this and, unused, would help it

**Where.** Abstract ¶1 (hedged correctly: "baseline turnover (itself read from realized, partly behavioral turnover)"), then unhedged at §I, §V.E, §VI.A, §VI.B, §VIII (md line 569), and as Table 1's row label "Mechanical null, $\beta_1=0$". Depth ladder: §VII.F and `hazard/data/matched_depth_reconciliation_results.json`.

**Defect (a): the vocabulary contradicts the design.** The null's level is set by a floor read off realized deep-discount-cohort turnover, which §V.B concedes "mixes discretionary life-cycle moves and cash-out refinancings with strictly involuntary events" with a strictly-involuntary share "plausibly well under half." A null carrying that floor is not mechanical; it is *observed behavior minus one imported elasticity's increment*. The abstract hedges this once; the other ~40 uses of "mechanical" do not, and a policy reader will take "most of the shortfall is mechanical" as "not behavior," which the design cannot support.

The paper's own artifact demonstrates the point. Reading the 2018 off-window depth ladder from `matched_depth_reconciliation_results.json`:

| gap cut | CPR | exposure | cohort-months |
|---|---|---|---|
| ≤ 0 | 5.334% | $1{,}264.5$bn | 155 |
| ≤ −0.25pt | 4.991% | $1{,}058.1$bn | 137 |
| ≤ −0.50pt | 4.695% | $921.4$bn | 125 |
| ≤ −0.75pt | 4.722% | $453.5$bn | 107 |
| ≤ −1.00pt | 4.869% | $143.4$bn | 95 |

The first three reads are monotone in the rate gap. The floor-read population is itself rate-suppressed. The "mechanical" baseline contains lock-in, by the paper's own measurement.

**Defect (b) — which is an opportunity the paper misses.** The same ladder **flattens** beyond about half a point of out-of-the-moneyness (4.695 / 4.722 / 4.869). Backing the implied bins out of the nested exposures (exposure-weighted differencing): $(-0.25,0]\approx 7.1\%$; $(-0.50,-0.25]\approx 7.0\%$; $(-0.75,-0.50]\approx 4.7\%$; $(-1.0,-0.75]\approx 4.7\%$; $\leq-1.0 \approx 4.9\%$. That is a step followed by a plateau — which is what a *floor on total turnover* looks like, and what an additive competing-risks form (in which the voluntary hazard keeps declining with the gap) does not predict.

This bears directly on the paper's largest open fork. §VII.F settles max-versus-additive on "the max form's semantics… now displayed as the conservative endpoint of a measured curve rather than defended by fit," having just conceded that its own strictly-involuntary reading "points at the hull's upper region." The 2018 depth ladder is out-of-window, out-of-episode, own-data evidence on precisely that question, and it points toward the max form the paper actually uses. The paper currently spends the ladder as a robustness band on a *level* and never reads its *shape*.

**Fix.** (a) Rename Table 1's row and the surrounding vocabulary to "no-elasticity null" or "observed-turnover null," and add one sentence stating that the partition is between a model carrying observed baseline turnover and the imported elasticity's increment above it — not between mechanics and behavior. (b) Add a short exhibit reporting the binned 2018 ladder with exposure shares and stratum-cluster standard errors, and state plainly what it does and does not license: 2018 gaps are shallow relative to the window's $-380$bp; the $\leq-1$pt bin carries only 11.3% of the gap-$\leq 0$ exposure (the artifact records `exposure_share_of_gap0` = 0.113); deeper cuts shift vintage and coupon composition; and the shallow bins plausibly carry refinancing, the same confound §V.D names for `episode_confrontation`. Even hedged that way it is the paper's first own-data evidence on the form fork, and it runs in the paper's favor.

---

### MAJOR 7 — Generalizability: the design cannot produce a null in this episode, and no scope condition is stated

**Where.** §V.E's sign-forcing paragraph (99.53% of exposure at or below 5.09% against a window-minimum 5.2311% — `sign_forcing_stats`); §VIII's recurrence claim (md line 569); Du et al. (2024) cited once at md line 81.

**The defect.** §V.E establishes, correctly and to its credit, that the marginal's sign "is fixed by the rate configuration rather than by the estimated elasticity," and demotes the 27-cell positivity check accordingly. The unstated implication is that **the design's central quantity is not identified in an episode with mixed rate gaps** — the sign is guaranteed here and would be indeterminate elsewhere. The same is true of the Danish gap ("could not have come out otherwise"). So the exercise cannot be replicated as a falsification test in another cycle, another country, or another portfolio, and the paper offers no scope condition telling a reader when it could be. §VIII nonetheless generalizes ("severe duration extension should be expected to recur in future tightening cycles that begin, as this one did, with a large outstanding stock of deeply in-the-money mortgages"), which is a plausible claim that nothing in the design supports.

Relatedly, Du et al.'s seven-central-bank QT record is cited once and never used. Whether other central banks' passive-runoff caps were similarly non-binding is a one-page extension on public data, and it is the difference between an episode study and a general result about runoff-cap design — which is, on my reading, the paper's most exportable contribution.

**Fix.** (i) State the scope condition as an inequality in §V.E: the decomposition is informative only where the book's out-of-the-money share is high enough that the sign is not at issue, and it is *not* identified in a mixed-gap episode. (ii) Add a short subsection using the Du et al. record to ask whether the cap-above-achievable-runoff pattern generalized across the seven central banks, and say what data would settle it. (iii) Downgrade §VIII's recurrence sentence to a conditional statement about the stock, explicitly labeled as outside what this design tests.

---

## 4. MINOR issues

1. **A committed artifact carries a reading the manuscript retracts.** `hazard/data/extension_risk_results.json`, field `lag_interpretation`: "Negative lag = hazard CPR leads SOMA empirical CPR. Consistent with 45-90d TBA settlement delay between Freddie loan-level prepay and NY Fed SOMA cash receipt." §V.B reverses exactly this ("a peak at $k=-3$ means the simulated path *trails* the empirical path") and §V.B says no settlement interpretation attaches. Appendix A catalogues the in-print inversion but not the artifact string, so a reader consulting the replication package gets the superseded reading. **Fix:** correct the string, or add an Appendix A bullet naming the field.

2. **The tax-law override is stated more flatly than the law supports, and is the wrong kind of input for a transplant.** §VI.D (md line 450) overrules Berger et al.'s 22%/15% U.S. counterfactual on the ground that "a discount extinguishment is cancellation-of-debt income at ordinary rates, IRC §61(a)(11)." Directionally defensible, and the post-TCJA deductibility point is well taken. But it omits the §108 exclusions (qualified principal-residence indebtedness, insolvency) that would bear on exactly this fact pattern, and — more importantly — in a *transplant* counterfactual the U.S. tax treatment is a legislative choice, not a datum. Using it to shrink the refinance-in-place channel lets a policy-design parameter do the work of evidence, and it shrinks the channel in the direction that keeps the $\approx 0$ pin the paper's own Danish redemption data then contradicts. **Fix:** reclassify the tax attenuation as a design parameter; present the gap across both tax regimes using the existing `danish_refi_finegrid` sweep; move the legal reading to a footnote with the §108 caveat.

3. **Abstract structure.** 246 words plus a second unbracketed paragraph, and the *second* paragraph carries the actual headline (the range, the anchor convention, the form-conditionality). **Fix:** one abstract, ≤200 words, leading with the two denominators of MAJOR 5.

4. **§VI.C (assumability/portability) is the one un-numbered section in a paper that numbers everything.** It rests on "Fixed-income analysis suggests" with no citation, no magnitude, and no run — and it is the live U.S. policy proposal (FHFA). **Fix:** cite FHA/VA assumption-volume evidence, connect to the paper's own 20.4% statutory-assumability share, and state plainly that the design cannot score take-up (§I already concedes realized take-up "is not measured anywhere in this design"), so the section is a taxonomy rather than a finding.

5. **Table 1 omits the two objects §VIII's conclusion actually compares:** the household side and the duration extension. **Fix:** add both rows (see MAJOR 1 and MAJOR 5).

6. **"Trapped liquidity" does rhetorical work outside its definition.** It is defined precisely at md line 59 as a net shortfall against a ceiling, but for readers outside MBS the phrase connotes a resource loss, and it appears in that role at most headline sites. **Fix:** prefer "cap shortfall" in headline sentences; reserve "trapped liquidity" for the internal accounting object.

7. **The labor-reallocation leg has no number at all.** Hsieh–Moretti is cited for mechanism only — correctly, given the published correction — but no surviving magnitude is substituted, so the welfare argument's one remaining quantitative leg is empty. **Fix:** cite a per-move surplus estimate that survives scrutiny, or state that the leg is unquantified in the same sentence that invokes it.

8. **Reading burden is itself a reviewability problem** (see Writing Quality below): the author supplies a "short path for a referee" at md line 61, which is helpful and honest, but a 139-page paper that needs an author-supplied navigation map to be refereed has a structural problem, not a length problem.

---

## 5. Cross-disciplinary opportunities missed

1. **The public-finance framing of the buyback bracket.** §V.B has already derived that the cash-haircut leg is a household-to-bondholder transfer. One further step — the bondholder is the Fed, so the transfer is fiscal — connects the paper to the MVPF and pass-through-to-households literatures and gives the Danish counterfactual a welfare sign it currently cannot have. Cheapest high-value addition in the paper.

2. **The distributional result is buried in a homogeneity check.** §V.E's group ablations report per-balance intensities tilting toward sub-740-FICO ($1.23$–$1.26\times$) and above-80-LTV ($1.23\times$) borrowers, against a placebo whose twelve random partitions span only 0.011. That is a *distributional* finding about who bears the mobility cost, established against a proper placebo, and it is presented as evidence that a verdict label carries no information. For a housing-economics or public-policy audience it is arguably the most publishable result in the paper. **Promote it**, with the placebo caveat intact.

3. **Cross-country cap design** (Du et al., MAJOR 7). The general lesson — an announced ceiling is not a forecast, and whether it can bind is computable ex ante from portfolio composition plus a turnover band — travels to any central bank running passive runoff. The paper has the template and does not sell it.

4. **The general methodological lesson is left in §VII.F prose.** "A calibrated floor's functional form can double a policy-relevant marginal" is a warning for anyone doing calibrated policy counterfactuals, and the mixture curve (`floor_form_mixture`, $s$ from hard-maximum to additive) is a clean, portable device for exposing it. It deserves a named paragraph, not a robustness aside.

5. **Table 27 as a research-practice contribution.** The adverse-findings register — committed rule, outcome, adjudication *with direction* — is a better answer to the garden-of-forking-paths problem in calibration work than most pre-registration templates, and it is currently Appendix O of a 139-page paper. It would stand alone as a short methods note.

6. **Renters and entrants.** Lock-in's most-discussed housing-policy consequence is the inventory channel and its incidence on first-time buyers. The manuscript mentions inventory once, in passing (§I), and cites Graybill–Mangum (2026), whose setting is exactly housing-market equilibrium. One sentence connecting the two would locate the paper in housing economics rather than only in MBS mechanics — which matters for the "so what" question a non-specialist audience will ask first.

---

## 6. Dimension scores

| Dimension | Weight | Score | Basis |
|---|---|---|---|
| **Originality** | 20% | **72** | Real but narrow. The paper concedes that the mechanism (Na et al. 2024; Perli 2024; Hammack 2025), the below-cap regime, and the ex-ante-projection observation (York 2022 — "the observation is theirs") all pre-exist, and labels two of its own elements as non-contributions. What is genuinely new: the $\beta_1=0$ paired-run decomposition on the SOMA cash-flow side, the expectations-based complement, the priced rule-only Danish transplant, and — as methodology — the cross-design ABM/hazard pairing and the adverse-findings register. The Danish counterfactual is the most original piece and its sign is forced by its anchor. Adequate-to-strong. |
| **Methodological Rigor** | 25% | **64** | Polish is not rigor, and I have scored the design, not the apparatus. Genuine rigor: pre-committed specs with parity gates, the correct estimand given a floor-dominated level, exact basis-invariance with stress runs, the cluster-bootstrap ladder (Table 9), and the self-discovery of a $37\times$ bootstrap understatement. Against: no outcome holdout anywhere; the dominant level-setter measured on a population the paper's own depth ladder shows is rate-suppressed (MAJOR 6); a coverage claim propagated by pushing wild-$t$ *endpoints* through a PCHIP interpolant of a frozen sweep; 31 nominal / **5.9 effective** clusters with max leverage 0.33 (Table 9 notes) carrying the binding interval; the second estimator supplies no differential at all ($+270.4$ vs $-105.3$, sign disagreement); Path A's own coefficient not distinguishable from zero under any bias-respecting construction; the imported elasticity's specification range propagated with no standard error anywhere; a form choice that roughly doubles the answer settled on semantics; a PSA convention sweep ($+0.9$ to $+15.6$) that dwarfs the quoted interval; and, from my angle, a bottom-line comparison that is not well-posed. Bottom third of adequate. |
| **Evidence Sufficiency** | 25% | **61** | Scored on what exists, not on candor. The headline number's identifying evidence is 137 cohort-months in 31 clusters, plus an elasticity with no propagated uncertainty, on a sample covering 51.0% of SOMA book face with Freddie conventional hazards extrapolated as-is to 20.4% Ginnie and 33.7% out-of-window vintages. Two independent floor reads (5.51% age-standardized, 5.52% Fannie) sit *above* the clean band and imply a marginal below the quoted $+4.3$ edge; the paper concedes the lower edge is soft. Both headline signs are forced. Four clip-induced zero months sit in the benchmark's monthly series. Offsetting: the paper's *primary* claim — that the mechanical base delivers the large majority of the level — is robustly evidenced across floors, bases, both agencies, the Fed's own ex-ante projection, and Na et al.'s independent payments composition; the Fannie staging (17.6M loans, 826M loan-months) is a real asset; and the sensitivity coverage is extraordinary. Bottom of adequate. |
| **Argument Coherence** | 15% | **68** | Internally, near-exemplary: I could not find a basis-mixed comparison, an unlabeled floor, or an inconsistent number, and the qualification hierarchy (Tables 5, 8, 9, 27) is maintained without slippage. The deductions are structural: the identified object is second-order for both channels the paper invokes and is denominated in a benchmark §III.B disowns (MAJOR 5); the abstract's closing contrast sets a measured "small" against an unmeasured "real" (MAJOR 1); §VI.B's cap arithmetic lacks an objective function and conflicts with §I and §III.B (MAJOR 4); the title says "Shortfall" while §III.B declines to call it a policy miss; and §VIII concedes the trilemma dissolution "reduces to 'the marginal is small'," which is form-conditional. Motivation and deliverable do not meet. |
| **Writing Quality** | 15% | **58** | Measured, not impressionistic. Longest body paragraph in `paper/v18/revised_paper_v18.tex`: **14,732 characters (~2,250 words)** in §V.B; next three 11,312 (§V.E), 10,696 (Appendix G), 8,051. In the markdown edition the longest paragraph runs 1,618 words across 38 sentences at a **mean of 42.6 words per sentence**, maximum 111, with 14 parentheticals and 12 em-dash asides in that paragraph alone. Abstract 246 words in two paragraphs. 139pp with an author-supplied referee navigation map. Density is carrying qualification load that structure should carry, and compression is not rigor. Genuine credit where it is due: the prose is precise, the voice is consistent, there is no filler, and the exhibits — Tables 1, 5, 8, 9, 11's notes, and 27 — are excellent and do more work per line than the surrounding text. But a reader cannot extract the argument at the rate the argument arrives. |

**Weighted final:** $72(0.20) + 64(0.25) + 61(0.25) + 68(0.15) + 58(0.15) = 14.40 + 16.00 + 15.25 + 10.20 + 8.70 = \mathbf{64.6/100}$

---

## 7. Recommendation

**MAJOR REVISION** (64.6; at the upper boundary of the band, one point below Minor Revision).

I want to be precise about what that verdict does and does not mean, because the score is close to the boundary and the reasons matter. I am **not** asking for new identification — the paper has already established, more thoroughly than most referees would demand, that clean identification is unavailable here, and I accept that. Almost everything in §3 is either (i) framing and vocabulary that must be brought into line with what the design measures (MAJOR 1, 3, 5, 6a, 7; Minors 1–7), or (ii) computations the existing pipeline already supports: the foregone-payoff count and its external moment check (MAJOR 2), the Aladangady anchor under the additive form (MAJOR 2), the binned 2018 depth ladder (MAJOR 6b), and the cap-design deliverable in $bn/month with its two-input table (MAJOR 4). Two of those — MAJOR 6b in particular — would *strengthen* the paper's own positions on its largest open fork.

What holds it below Minor is not any single item but the conjunction: a paper whose stated bottom line compares a measured quantity against an unmeasured one, whose identified object is second-order for both channels it invokes, whose policy section states an arithmetic without an objective, and which never tests its central behavioral implication against a single external outcome moment it could have obtained for free. Those are content problems, not presentation problems, and a reader outside MBS mechanics cannot presently act on the paper. Fix them and I would expect this comfortably into Minor Revision territory; the underlying apparatus is more than good enough to carry it.

---

## 8. Carroll Round judgment (one line)

**Ready to present and defend as-is** — the assembly table, the adverse-findings register, and the author's command of his own paper's weaknesses will defend extremely well under hostile questioning — but the presentation layer needs two things the manuscript currently lacks: a one-slide answer to "what is the household side worth, in the same units?" and a one-slide cap-design deliverable in $bn/month, because an undergraduate international-economics audience will ask the welfare question the paper declines and the policy question the paper leaves in design space.

---

# Devil's Advocate Report

# DEVIL'S ADVOCATE REPORT
**Manuscript:** "Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"
**Reviewer role:** DA — adversarial replication / research-integrity referee
**Basis:** full read of `~/Downloads/UPLOAD_ROUND11/revised_paper_v18.md` (all 1,143 lines, main text + Appendices A and O in full), structural checks against `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945/paper/v18/revised_paper_v18.tex`, and read-only inspection of 11 frozen artifacts under `hazard/data/` plus `tools/liveness_gates.py` and `tools/render_gate.py`. No repo script executed; nothing modified.
**Untrusted-data check:** I found no text in the manuscript directed at a reader-agent and no embedded instructions. Line 61's "How to read this paper" is ordinary authorial signposting; I used it as a map and read §IV, §VI.D, §VII.C and Appendix O anyway, all of which carry material adverse to the headline.

---

## 1. STRONGEST COUNTER-ARGUMENT

Here is how I would put it at the seminar.

You have not measured lock-in's contribution to the QT shortfall. You have measured how much of an imported coefficient escapes a floor you set by convention, and then priced the sampling error of the floor as if it were the uncertainty of the answer.

Take your own numbers. The sign is forced — you concede 99.53% of exposure sits below the window-minimum rate, so no cell of any sweep could have come out negative. Positivity in 27 cells: you retire it yourself. The monotone response across the elasticity band, which you *keep* as identified content, is forced by the same argument: β₁ is monotone in δ by (3) and the hazard is monotone in β₁ by (1). Timing: no credential, the null peaks at the same lag. Levels: not identified. So the entire identified content is one conditional magnitude.

Now look at what conditions it. Your own committed artifact `psa_level_sweep_results.json` records that at the headline floor, moving the baseline seasoning ramp from 75 to 150 PSA — a convention you did not estimate, well inside industry practice — carries that magnitude from **+0.9 to +15.6 points**, and records the ratio to your binding interval as **2.49×**. Three of three off-window cells missed their pre-committed bands. Meanwhile the floor those 137 cohort-months set is measured entirely on loans aged 12–24 months (your artifact: age≥24 buckets empty, verdict `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`) and applied to a book aged 2 to 162 months. Both independent corrections for that — age-standardized 5.51%, Fannie 5.52% — land above your entire clean band.

So the headline is a point inside an interval that prices the wrong parameter, resting on a proxy whose comparability test your design cannot run. The honest statement is nearer "+1 to +11, concentrated low."

*(288 words)*

---

## 2. ISSUE LIST

### CRITICAL

**C1 — The headline floor is age-incomparable to the book it is applied to, and the comparability test is not computable by construction.**
*Dimension:* Methodological Rigor / Evidence Sufficiency.
*Location:* §VII.F ¶"Re-running the central and $\beta_1=0$ legs…" and ¶"Two further pre-committed measurements"; Table 6 rows 1–3; "Definitions used throughout" (md line 59); artifact `hazard/data/oos_identification_results.json`, `instrument1_oow_floor.legs.2018_rising_rate`.
*What is wrong:* the artifact's own seasoning block shows the 2018 leg carries `age[0,12) = 3.776%` (505 cohort-months) and `age[12,24) = 5.334%` (155 cohort-months), and **zero** cohort-months in `age[24,36)`, `age[36,60)`, `age[60,∞)`. The 137 cohort-months behind the headline 4.991% read are therefore all in a single 12–24-month age band. The artifact records `"mature_test_computable": false` and the verdict string `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`, and flags the within-leg ramp of +1.558pp from age[0,12) to age[12,24) as `"ramp_rise_is_psa_confounded": true`. The SOMA book this constant is broadcast to spans, on the paper's own Table 12 ages, roughly 2 to 162 months over the window, with 43.9% of face in the 2021 vintage alone. Because turnover rises with seasoning — which the paper asserts twice, in the 100 PSA ramp and in the age-standardization — a floor read at 12–24 months **understates** the mature book's baseline turnover, understates the null, and therefore **overstates** the marginal. The direction is signed against the headline, and it is not a hypothetical: the two reads that correct it (age-standardized 5.51%, Fannie 5.52%) agree to 0.01pp and both sit above the clean band's 5.334% top, implying a marginal below the quoted +4.3 lower edge. The paper's response — "the band's *lower* edge is the soft one" — mislabels the problem. When two independent corrections agree and both fall outside your band, the point is more likely wrong than both corrections.
*Why CRITICAL:* the +5.6 point and the [+4.3, +6.8] range are carried in the abstract, Table 1 row 4, §V.E, §VI.A, §VI.B, §VIII and §VIII.A. As printed they rest on a proxy whose only available comparability corrections both reject them.
*Concrete fix:* (a) restate the headline as the interval implied by all *available* off-window reads including the age-standardized and Fannie cells — approximately **+2.9 to +6.8** — with no interior point named; (b) state in §VII.F and in the Definitions block that the clean 2018 leg contains no cohort-month aged ≥24 and that the age-transport error is therefore unpriced and signed against the headline; (c) add a row to Table 6 for the 5.51% and 5.52% reads rather than confining them to a note.

**C2 — "Binding layer" designates the sampling error of one nuisance parameter while the paper's own artifact records a convention span 2.5× wider at the same calibration; the abstract's main clause overstates what its parenthetical supports.**
*Dimension:* Argument Coherence / Methodological Rigor.
*Location:* Abstract, sentence beginning "The design bounds it between $+2.9$ and $+8.7$ points under its production floor form"; Table 1 row 4 and its note a; Table 8 headline row; Table 9 caption; §VIII ¶3; artifact `hazard/data/psa_level_sweep_results.json`, keys `ranges["4.991"]` and `comparison`.
*What is wrong:* the artifact records, at the headline 4.991% floor, `ranges["4.991"] = {lo_pp: 0.856, hi_pp: 15.626, width_pp: 14.770}` against `floor_read_width_pp: 5.927`, with `psa_over_floor_read_at_headline: 2.492` and `verdict: "PSA_WIDER"`. Both PSA endpoints are computed **under the production max floor form**, so the abstract's qualifier "under its production floor form" does not quarantine them. Worse, `expectation_check` shows all three off-window PSA cells fell outside their pre-committed bands (`4.991|75` realized 0.856 vs band [1.5, 2.5]; `4.991|125` realized 11.42 vs [8.5, 10.0]; `4.991|150` realized 15.63 vs [11.0, 14.0]) — a 0-for-3 pre-commitment miss on the headline calibration, filed in Table 27 as "neutral." The paper's defence is that PSA has "no coverage property." That is true and it is the wrong test: a range without a coverage property that is 2.5× wider than one with a coverage property does not become less relevant to the answer, it becomes the reason not to print the narrow one as "what the design bounds."
*Why CRITICAL:* this is an abstract-and-Table-1-level claim. A reader who takes "the design bounds it between +2.9 and +8.7" at face value is misinformed by a factor of ~2.5 in width and, at the 75 PSA cell, by a factor of 6.5 in the point.
*Concrete fix:* (a) rewrite the abstract clause to "the floor read's own sampling error, holding the baseline ramp, floor form, elasticity and covariate priors fixed, puts it between +2.9 and +8.7 points; the unestimated baseline ramp alone spans +0.9 to +15.6 at the same calibration"; (b) demote the phrase "binding layer" to "binding *among the layers with a coverage property*" everywhere it appears without that qualifier (Table 1 row 4, Table 8, Table 9 caption, §VIII); (c) since Path A already fits a seasoning spline with knots {12,24,36,60,84,120}, re-run the paired legs with the baseline hazard set to that **estimated** age profile instead of 100 PSA, and report the marginal there. This is one run and it converts the largest disclosed layer from a convention into an estimate.

### MAJOR

**M1 — The refusal to compose corrections is asymmetric, and the one composition actually run lands at the interval's floor.**
*Dimension:* Argument Coherence.
*Location:* §V.E seventh qualification ("a composed figure would carry a precision nothing in the design supports"); Table 5 rows 3–10; artifact `hazard/data/b5_joint_cell_results.json`, `overlay_agestd.primary.marginal_pp = 2.928`.
The paper declines to compose eight downward readings on precision grounds, then names +5.6 as the "mid-grid anchor" — itself a composed grid artifact. The single composition it *did* run (`b5_joint_cell`: Ginnie overlay × age-standardized floor) returns **+2.928pp**, i.e. exactly the lower endpoint of the interval called binding, with `measured_minus_implied_pp = -0.129` against the proportional projection. A reporting rule that forbids composition but permits a mid-grid point is not a precision rule; it is the only rule under which the headline survives its own corrections.
*Fix:* either report the measured composed cell +2.9 as the assembly's operative lower member in Table 1 and the abstract, or drop the named interior point entirely and report the range alone. Do not do neither.

**M2 — "Mid-grid anchor" is not robust to the paper's own extension of the grid.**
*Dimension:* Methodological Rigor.
*Location:* §VII.F ¶"Extending the 2018 depth ladder from three well-supported depths to five"; Table 6; Table 5 row 2.
The anchor 4.991% is the median of three printed depth cuts. The paper then reports two more well-supported reads (4.722% at gap ≤ −0.75, 4.869% at gap ≤ −1). On the five reads {4.695, 4.722, 4.869, 4.991, 5.334} the median is **4.869%**, not 4.991% — a different anchor implying ≈ +6.0pp. The anchor is therefore a function of how many depth cuts were printed, not of the data, and the paper does not state the selection rule ex ante.
*Fix:* state the anchor rule explicitly ("median of the three pre-committed depth cuts") and show the five-cut median as a robustness line; or abandon the interior point per M1.

**M3 — Table 3 and Table 7 print the same parameter β₁ with opposite signs, unreconciled, in a paper with a documented history of sign/units defects in exactly this coefficient.**
*Dimension:* Writing Quality / Methodological Rigor.
*Location:* `paper/v18/revised_paper_v18.tex` line 244 — `$\beta_1$ (central) & $0.069$` — against line 404 and the rows above it, `6.50 & $-0.0686$` and `7.70 & $-0.0817$`, under a column header labelled `$\beta_1$`.
§V.B states "the *positive* $\beta_1$ of (3) suppresses prepayment exactly when the par-payoff penalty binds" and that (3) "evaluates to $\beta_1 = 0.0686$." Table 7's column prints the engine's internal value (`psa_level_sweep_results.json` records `"beta1": -0.0685705…`) under the opposite gap-sign convention, with no reconciling note. Appendix M records a prior units error in this coefficient's application and Appendix A records a superseded run "in which the calibrated lock-in elasticity was numerically inert" — this defect class has bitten the paper twice already. Nothing numerical is wrong (every trapped-dollar figure is gated bit-exact), but the 108-gate suite does not gate sign agreement between the two printings of its most load-bearing parameter.
*Fix:* flip Table 7's printed signs or add a one-line note naming the convention; add a liveness gate asserting Table 3's and Table 7's β₁ at δ = 6.5% agree in sign.

**M4 — The monotone response across the elasticity band is retained as identified content although it is forced by the same argument that retires the positivity.**
*Dimension:* Argument Coherence.
*Location:* §V.E first qualification, "the identified content is the marginal's *bounded range*, together with the monotone response across the Liebersohn–Rothstein band"; Table 7.
β₁(δ) is monotone by construction of (3), and the hazard is monotone in β₁ by construction of (1); the composition of two monotone maps cannot fail to be monotone. Table 7's monotonicity is arithmetic, not evidence. The paper demotes the 27-cell positivity on precisely this reasoning and then declines to apply it one clause earlier.
*Fix:* strike "together with the monotone response" from the identified-content sentence in §V.E and from §V.B's parallel sentence; retain the curve as a wiring check alongside the positivity check.

**M5 — Survival-selection attenuation is signed downward ex ante and then excluded from the assembly on a distinction that does not hold.**
*Dimension:* Methodological Rigor.
*Location:* §V.B ¶"Two further transport assumptions"; Table 8 headline row's calibration column; Table 27 row "Attenuation prediction bands"; artifact `hazard/data/attenuation_sensitivity_results.json`.
The artifact records the measured pre-window survival share S = 40,234/75,000 = 0.536, a grid a = S^θ = {1, 0.856, 0.732, 0.536}, off-window marginals {+5.6, +5.1, +4.6, +3.7}, and `"Direction SIGNED ex ante: a<1, the marginal falls, a DOWNWARD member."` It is then kept out of the assembly as "a transport sensitivity on an imported coefficient, not a correction to the paper's own object." That distinction fails: if the imported coefficient is attenuated in the survival-selected pool it is applied to, then the marginal computed with the unattenuated coefficient is biased up, which *is* a correction to the paper's own object. At the natural gamma-frailty case θ = 1 the marginal is +3.7pp.
*Fix:* move the attenuation row into Table 5's assembly with its θ grid displayed, or state a rule for what qualifies as a correction that this row fails and the Ginnie overlay passes.

**M6 — Two overlays are labelled "change of estimand, not a correction" while the convention they re-score is the production convention.**
*Dimension:* Argument Coherence.
*Location:* Table 5 rows 3–4 ("change of estimand (re-scoping onto the conventional sub-book), not a correction"); Table 27 row "Vintage-overlay expectations"; §V.B.
Path B's production object is the whole SOMA book: §V.B states hazards are "extrapolated to those segments as-is." Re-scoring the 20.4% Ginnie and 33.7% out-of-window shares by observed speeds therefore corrects a known error in the production object, it does not redefine the estimand. If the paper genuinely believes the estimand is the conventional in-window sub-book, then §III.B's 51.0% coverage concession should be a coverage *definition*, the benchmark denominator should be re-scoped accordingly, and the headline recovery percentages restated — which the paper does not do.
*Fix:* pick one. Either the overlays are corrections (+4.4 / +3.7 enter the assembly as such and the headline moves), or the estimand is the sub-book (denominator and every recovery percentage restate).

**M7 — The apparatus is a consistency layer, not a validity layer, and the repository proves it.**
*Dimension:* Methodological Rigor (bearing on how much credit the pre-commitment architecture earns).
*Location:* `tools/liveness_gates.py` docstring lines 6–20 (four gate classes: zero-count greps, exactly-one greps, manuscript-vs-manifest cross-checks, abstract-scoped hedge spans); `tools/render_gate.py` docstring; Appendix O ¶1.
Every one of the 108 gates reads the `.tex` and the frozen artifacts. None can test whether an artifact's *premise* — 100 PSA, the max floor form, the 2018 age band, s = 1, the covariate priors — is right. The repository supplies the demonstration: `tools/render_gate.py`'s own docstring records that ~919 text items across 9 pages sat outside the physical sheet, undetected through every prior round, and that "the worst page carried 302 items of the Appendix O adjudication ledger more than a full page below the bottom margin." For at least three review rounds the document as circulated did not deliver its own adverse-findings register to the page, and 108 gates plus 479 tests passed throughout. This does not impugn the author's diligence — the fix is exemplary — but it settles the question of what a green suite certifies: textual fidelity to frozen numbers, not the validity of the numbers' premises.
*Fix:* add a sentence to Appendix O ¶1 stating the gates' domain explicitly ("the gates verify that the manuscript's literals match the committed artifacts; they cannot test an artifact's premise, and one class of defect they structurally could not see — off-sheet rendering — survived 108 of them"). This strengthens the paper's credibility rather than weakening it.

**M8 — Length and paragraph structure defeat the qualification load they carry.**
*Dimension:* Writing Quality.
*Location:* `revised_paper_v18.tex` — the §V.B body paragraph beginning "The first hazard path brings competing risks" is **14,732 characters** (~2,200 words); §V.E's is 11,312; Appendix G's is 10,696; §V.B's aggregation paragraph is 8,051. 139 pages total.
The §V.B monolith is the paragraph a referee is directed to first (line 61) and it contains, without a paragraph break: equations (1)–(3), the floor's semantics, the moving-share transport, the ZIP-to-loan aggregation transport, the survival-selection transport, the competing-risks taxonomy mapping, the burnout ablation at two floors, and the covariate ablation at two floors. Each of those is a distinct claim with a distinct evidentiary status; run together they are unauditable at reading speed, and a reader who loses the thread cannot tell a concession from a defence.
*Fix:* split §V.B at the five natural seams (specification / floor semantics / elasticity import and its three transports / aggregation bounds / ablations); move the competing-risks taxonomy mapping to Appendix E. This is mechanical and costs no content.

### MINOR

**m1 — Title and abstract frame a policy miss that §III.B disclaims.**
*Location:* title; abstract sentence 2; §III.B final ¶ ("a shortfall against the MBS cap is not by itself evidence that a stated policy objective was missed").
The title pairs "Mortgage Lock-In" with "the Federal Reserve's Quantitative Tightening Shortfall" by conjunction, which a reader parses causally, while the paper's finding is that lock-in accounts for 3–9% of that shortfall. *Fix:* retitle to signal the decomposition, e.g. "Decomposing the Federal Reserve's Quantitative Tightening Shortfall: Mortgage Lock-In and the Mechanical Baseline."

**m2 — A channel dismissal rests on a single-author legal reading that does not bracket its own premise.**
*Location:* §VI.D ¶"The recalibration rests on two behaviorally distinct channels" — the parenthetical overriding Berger et al.'s 22%/15% US counterfactual with IRC §61(a)(11).
The COD-income reading is plausible in form, but the paper cites the statute without the implementing regulation (Treas. Reg. §1.61-12(c) on repurchase of one's own debt at a discount) and does not address §108's exclusions, which run the other way for some households. A single-authored paper overriding its own source's counterfactual should bracket, not assert.
*Fix:* cite the regulation, note §108(a)(1)(B)/(E) and why they are unlikely to bind in a rate-driven (rather than value- or insolvency-driven) discount, and present the tax adjustment as a directional bracket rather than a correction.

**m3 — The abstract carries five qualifications in a single 248-word paragraph.**
*Location:* `.tex` line 31 (single paragraph, 248 words, verified).
The content is honest — it leads with the range, states the null's 85.7%, states that levels only are identified, and states that the additive form roughly doubles the margin. The syntax is not: three em-dash asides and a three-clause semicolon parenthetical. *Fix:* break into two paragraphs at "What lock-in itself adds…" (already a natural seam) and move the wild-cluster/percentile detail out of the abstract into Table 1's note.

---

## 3. IGNORED ALTERNATIVE EXPLANATIONS / PATHS

**A1 — The marginal is an artifact of the unestimated baseline ramp, not of the elasticity.** The cleanest alternative account of every number in §V.E: the "lock-in contribution" is the portion of the imported coefficient's effect that is not censored by the floor, and the censored share is set jointly by the floor level *and* the baseline ramp. `psa_level_sweep_results.json` shows the floor-bind share at the headline calibration moving from 0.947 (75 PSA) to 0.181 (150 PSA); the marginal moves 0.9 → 15.6 in lockstep. Under this account the paper has measured a censoring geometry, not a behavioral channel. **Untested path:** re-run with Path A's estimated seasoning spline as $h_0$ (§V.D already fits it). If the marginal at the estimated profile lands near +5.6, the headline is vindicated; if it lands near +11 or near +2, the headline was a convention. One run, no new data.

**A2 — Seasoning, not lock-in, generates the cross-sectional gradient the paper calls its one lock-in-direction exhibit.** `episode_confrontation` finds +4.20 CPR points from shallow to deep gap buckets, +3.43 within common vintage×FICO×LTV cells. But coupon and age are collinear in a closed 2017–2021 book: the shallow high-coupon buckets are systematically *older* originations. §V.D says "residual seasoning past the age cut" is among the confounds and leaves it there. **Untested path:** re-run the gradient within narrow age bands (e.g. 12-month strata) rather than past a single age cut, and report the age-stratified gradient. If it survives, the exhibit becomes real support; if it collapses, the paper's only realized-data lock-in evidence is a seasoning artifact, and the 4.5× excess over the model's implied +0.94 is explained.

**A3 — Inventory and search frictions, not the payoff rule, suppressed turnover.** §I mentions "historic housing inventory shortages" and never returns. A seller who cannot find a house to buy does not move regardless of coupon. Because listings collapsed contemporaneously with rates, an inventory-driven turnover collapse is observationally equivalent to lock-in at the aggregate cash-flow level, and the paper's floor — measured on 2018 cohorts in a normal-inventory market — would be too high for a low-inventory window, biasing the marginal *down*, i.e. the one unpriced channel that runs the other way. **Untested path:** cite the housing-supply literature explicitly as an unmodelled competing channel in §VIII.A and state its sign; the `scaled_null_housing_activity` run already builds the machinery (Aladangady-anchored φ* = 0.754) but is presented as an "upward-bias entry" rather than as an alternative explanation.

**A4 — Servicer and remittance mechanics, not borrower behavior.** §VI.A concedes "no servicer channel beyond that pipeline is modeled at all" and that servicer behavior "carr[ies] no bound of any kind here," while §VII.B shows the settlement re-basing moves the benchmark −5.5% and Appendix N shows four clip-induced zero months flip the frozen timing rule. A pure reporting-and-remittance account of the monthly path is not excluded by anything in the paper — indeed it is *consistent* with the finding that no estimator's detrended co-movement is distinguishable from zero. **Untested path:** none needed; the paper should stop treating "no estimator matches the timing" as a shared failure and consider that the empirical monthly series may not be a behavioral object at all, which would retire the timing question rather than leave it "open."

**A5 — The Danish exercise cannot fail, in either direction, and the magnitude inherits the anchor too.** §VI.D concedes the sign is forced by the zero-gap anchor. It then says "the informative content is the magnitude." But the magnitude is $R_{\text{zero-gap}} - R_{\text{central}}$, which is the lock-in marginal computed on a second accounting leg — the paper says so explicitly ("one object measured on two accounting legs"). So the magnitude inherits every conditionality the marginal has, including the PSA convention and the floor's age transport. The Danish exercise adds no independent information about the payoff rule; it re-prints the marginal with a different balance loop. **Untested path:** if the claim is institutional, the transplant must change something the marginal does not already encode — the interest-only share, which §VI.D concedes "would move the shortfall in the opposite direction," is the obvious candidate and is not run.

---

## 4. MISSING STAKEHOLDER PERSPECTIVES

**S1 — The locked-in household.** The paper's welfare-relevant object, by its own §VI.A, is "the constrained moves themselves," and it declines to measure them. Every dollar figure is a central-bank cash-flow figure. The result is a paper whose title names a household friction and whose entire quantitative content is a bondholder's cash-flow ledger. §VI.A's one-paragraph gesture at Hsieh–Moretti, with its own point estimate withdrawn, is not a stakeholder analysis. *Concrete addition:* the design already has 75,000 loans with rate gaps and the imported mobility elasticity; the implied count of suppressed moves is one line of arithmetic and would give the mobility cost a magnitude to sit beside the $42.6bn.

**S2 — The FOMC's actual decision problem.** §III.B concedes the Committee's operating object was the aggregate portfolio, that Treasury runoff ran against its own caps, and that "nothing in this paper shows that reserves or the aggregate path came in off the intended course." That concession is buried at the end of a 6,600-character paragraph and is never carried into §VI.B, which nonetheless advises on cap design. A policymaker reading §VI.B is not told that the object being designed for may not have been a problem. *Concrete addition:* open §VI.B with the standing concession, and state what the composition shortfall cost that the aggregate path did not — the duration extension of §VI.A, which is the paper's genuine policy object.

**S3 — The MBS investor and the TBA dealer.** §VIII rests the whole policy conclusion on the TBA liquidity premium as "the binding constraint," citing Vickery–Wright, Gao et al. and Campbell. No investor-side cost of the Danish rule is quantified anywhere: not the pricing of a series-level call, not the hedging cost shift, not the effect on originator warehousing. The paper's own §VIII notes that Perotti et al. show behavioral risk can only be bounded, not hedged — and then asserts the Danish rule "removes the rate-rise extension leg" without pricing what it adds. *Concrete addition:* state explicitly that the investor-side cost of the transplant is unpriced in this design, so §VIII's "binding constraint" claim is an argument from the literature rather than a result.

**S4 — Ginnie Mae's borrowers.** 20.4% of the book is FHA/VA collateral, statutorily assumable, with a servicer buyout channel and CDR 2.1% vs 0.4%. §I concedes "realized take-up of that statutory right is not measured anywhere in this design." These are the lowest-income, highest-LTV borrowers in the book, and the paper's treatment of them is a composition-error bound. *Concrete addition:* one sentence in §VIII.A naming distributional silence as a limitation, not merely a coverage bound.

---

## 5. OBSERVATIONS (NON-DEFECTS)

These looked like problems and survive scrutiny. Saying so is what makes the rest of this report worth reading.

**N1 — The headline *qualitative* claim is robust to the sensitivity that destroys the quantitative one, and this is the paper's strongest result.** I attacked the PSA convention hard in C2. It does not touch "most of the shortfall was mechanical." Across the full 75–150 PSA sweep at the headline floor, the $\beta_1=0$ null recovers **68.4% to 101.9%** of the benchmark (`psa_level_sweep_results.json`, cells `4.991|{75,100,125,150}|0`); across the defensible off-window floor range it is 83.9–86.9%; and it is 97.8% standalone in-sample. There is no cell anywhere in the paper's apparatus in which the mechanical baseline fails to deliver the majority. That claim is over-determined, it is the claim that contradicts the natural reading of the Fed's own public characterization, and it is well evidenced. The paper should lead with it more confidently than it does.

**N2 — The nonlinear map does *not* break the interval's coverage.** My first instinct was that pushing wild-cluster endpoints through a PCHIP interpolant of a frozen sweep cannot preserve coverage. It can: the floor-to-marginal map is monotone, and interval endpoints are equivariant under monotone transformation. I verified from `floor_inference_correction_results.json` that the R2 wild-$t$ floor CI [4.163%, 5.820%] maps to [+2.796, +8.723]pp with `truncated_at_grid_edge: false` at both ends, and that `P3_mapping_fidelity` reproduces the committed grid with max error $0.687bn against a $0.69bn tolerance. The construction is sound. My objection to it is about *which parameter* is covered (C2), not about the transform.

**N3 — The inference ladder is real work, not decoration.** Table 9's ten rows — CR1/CR2/CR3 at $t(30)$, Rademacher and Webb wild-$t$ at B = 9,999, Bell–McCaffrey data-driven df at $t(6.2)$ and $t(5.1)$, and a 401-point restricted wild-cluster inversion — with the effective cluster count (5.9 by Herfindahl inverse, against 31 nominal) and maximum single-cluster leverage (0.33) disclosed in the note, is more careful few-cluster inference than most published applied work. The artifact confirms `max_leverage: 0.332` for R2. That the ladder prices the wrong parameter is a design failure, not an execution failure, and the distinction matters for how the author should be told to fix it.

**N4 — The placebo for the subgroup verdict is genuinely good practice.** §V.E's twelve random three-way partitions returning "broad-based" in all twelve, on intensities of 0.995–1.007, and the author's conclusion that "a partition with no economic content earns the label, so the label alone carries no evidential weight" — with the informative statement relocated to the *dispersion* comparison (0.381 vs 0.011) — is exactly the right move, executed unprompted. Very few papers falsify their own verdict vocabulary.

**N5 — The Fannie replication's honesty about its own gate is exemplary.** §V.C states plainly that the pre-committed envelope was 11.06 points wide around a 9.20-point estimate, that "a gate that wide cannot fail against anything but a sign error, and I do not treat its passing as evidence," and relocates the information to the 0.52-point agreement. Then it further limits *that*: the two samples are compositionally indistinguishable (PSI ≤ 0.018), so the agreement certifies pipeline determinism rather than external validity. That is three levels of self-limitation on a result most authors would have banked. It is also, on 17.6M loans and 826M loan-months, a real piece of work.

**N6 — The retraction of the 0.2-point "convergence" is the single most creditable passage in the paper.** §III.B and §V.E both retract the near-equality between the null's 88.7% and the Fed projection's 88.5%, on the ground that it requires *two* conditions at once, and show that the gap ranges from −2.8 to +13.2 points across the two disclosed choices. Withdrawing a presented result because it is doubly conditional, and then reporting the two quantities separately, is the behavior the pre-commitment architecture is supposed to produce. It happened.

**N7 — Path A's exclusion is honest and should not be attacked.** Table 2, Table 20, §V.D and Appendix G declare Path A non-corroborating, report that its own sign test fails ($p = 0.093/0.412/0.241$), that its resimulated 95% interval is $[-\$4{,}459.8, +\$1{,}190.1]$bn, that its mean (78.3%) sits *below* the mechanical null, and that the production spec "carries no valid uncertainty of its own." A reviewer who attacks the paper for leaning on a third estimator has not read §V.D. Equally, no credit is due for a 112.4% that the paper itself refuses to bank.

**N8 — The basis discipline is better than the field's norm.** Four accounting bases, defined once in §III.B, tabulated for every leg in Table 11, with the marginal's basis-invariance proved term-by-term monthly and stress-tested at ±25% on the curtailment rate and under four alternative time profiles; plus Table 11's note flipping the referent to show that a 107.0% "recovery" is an 8.2% *under*-prediction of realized runoff. The paper caught and catalogued its own 18.3-point basis-mixing error (Appendix A). Reviewers who repeat that error will be wrong, and the paper made it hard to.

**N9 — The self-administered adverse-findings register earns partial, not full, credit.** Appendix O / Table 27's 27 rows, each stating the committed rule, the outcome, and the adjudication *with its direction relative to the headline*, and the framing "a green gate suite is therefore not self-certifying," is a practice worth importing into the field. I withhold full credit for the reason the brief states: of the ~13 rows adjudicated "against the headline," not one moved a reported number, and (per M7) the register itself was the largest casualty of the off-sheet rendering defect. But the practice is real and should be named as such.

---

## SCORES

| Dimension | Weight | Score | One-line basis |
|---|---|---|---|
| **Originality** | 20% | **71** | Genuinely new decomposition and ex-ante cap arithmetic (1.7–1.9× the Fed's own projection); but the mechanism, the below-cap regime and the projection observation are all conceded to prior work (§II, "the observation is theirs"), the elasticity is wholly imported, and the Danish exercise re-prints the marginal on a second accounting leg. |
| **Methodological Rigor** | 25% | **60** | Top-decile execution (bit-exact parity gates, spec-before-run, Bell–McCaffrey df, placebo partitions, permutation decompositions) on a design that cannot identify what it reports: age-incomparable floor with the comparability test uncomputable (C1), the widest layer an unestimated convention (C2), zero elasticity sampling error propagated, no outcome holdout, sign and monotonicity both forced, and an unreconciled β₁ sign across two tables (M3). |
| **Evidence Sufficiency** | 25% | **58** | The mechanical-majority claim is over-determined and well evidenced (N1); the quantitative headline is not. No evidence internal to the paper that β₁ ≠ 0 (its own test: $p = 0.093/0.412/0.241$); no age-comparable floor read; no ABM differential; the one realized-data gradient runs 4.5× the model and is confounded. Scored on what exists, not on the candor of the caveats. |
| **Argument Coherence** | 15% | **66** | Unusually self-aware and mostly consistent, with real failures: monotonicity kept while positivity is retired (M4); composition refused as imprecise while a mid-grid point is printed and the one measured composition lands at the interval's floor (M1); "change of estimand" applied to corrections of the production convention (M6); attenuation signed downward then excluded (M5); title/§III.B mismatch (m1). |
| **Writing Quality** | 15% | **52** | 139pp; a 14,732-character (~2,200-word) single paragraph in the section referees are directed to first, plus 11,312 and 10,696-character companions; 4–6 nested parentheticals routine; and — verifiable from the repository, not the manuscript — ~919 text items across 9 pages, including 302 items of the adverse-findings ledger, rendered off the physical sheet through at least three prior rounds. Offset by disciplined terminology, a genuine definitions block, exemplary per-figure basis labelling, and a useful reading map. |

**Weighted final = 71(0.20) + 60(0.25) + 58(0.25) + 66(0.15) + 52(0.15) = 14.20 + 15.00 + 14.50 + 9.90 + 7.80 = 61.4 / 100**

## RECOMMENDATION

**MAJOR REVISION.** (Two CRITICAL findings independently forbid Accept.)

Both CRITICALs are repairable without redesign, which is why this is not a Reject: C2 is fixed by one run (re-anchor $h_0$ on Path A's estimated seasoning spline) plus abstract and Table 1 restatement; C1 is fixed by restating the headline as an interval spanning all available off-window reads (≈ +2.9 to +6.8) and disclosing the age-transport error's direction. The MAJORs are all restatement, relabelling, or one gate. If those land, the paper is a defensible field-journal contribution whose honest headline is that lock-in's own contribution to the QT cash-flow shortfall is *small and imprecisely bounded* — which is a more interesting finding than the one currently on the cover, and better supported.

## CARROLL ROUND (Georgetown undergraduate international-economics conference, spring 2027) — ONE-LINE VENUE JUDGMENT

Present it — the empirical apparatus is far beyond undergraduate norms and the author can defend every number in the room — but re-cut the headline to the range with the baseline-ramp caveat attached *before* the debut, because there is no revision checkpoint and the first knowledgeable questioner who asks "what sets your seasoning baseline, and did you estimate it?" will otherwise take the +5.6 apart in public.

---

# Editorial Synthesis (Phase 2)

# EDITORIAL SYNTHESIS — Phase 2

**Manuscript:** "Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"
**Panel:** R0:EIC (64.0) · R1:Methodology (63.0) · R2:Domain (64.2) · R3:Perspective (64.6) · DA:Devil's Advocate (61.4)
**Synthesizer's arbitration basis:** re-read of `paper/v18/revised_paper_v18.tex` (abstract, Tables 1/3/6/7/8/12/25, §V.B, §V.E, §VII.F) and the `.md` edition; independent read-only inspection of 12 frozen artifacts plus `hazard/loan_sample.py`, `hazard/data/cohort_month_panel.parquet`, `hazard/data/loan_sample.parquet`, `tools/render_gate.py`; one independent MBS pricing computation. No repo script executed; nothing modified.

---

## 1. CROSS-REVIEWER MATRIX

Severity is mine, after arbitration — not always the raising reviewer's.

### CONSENSUS (3+ reviewers converged independently)

| # | Issue | Raised by | Severity (arbitrated) | Verified? |
|---|---|---|---|---|
| **X1** | The unestimated 100-PSA seasoning baseline dominates the reported interval: at the headline floor the 75–150 PSA sweep carries the marginal +0.9 → +15.6pp (width 14.77) against the binding interval's 5.82, ratio 2.49×; and all three off-window PSA cells missed their pre-committed bands | R1:M5, R2:M7, DA:C2, R3 (rigor basis) | **Critical for the abstract and Table 1; Major for the body** | **Yes** — `psa_level_sweep_results.json`: `ranges["4.991"]` = 0.856/15.626, `psa_over_floor_read_at_headline` 2.492; `expectation_check` 0-for-3 off-window (3-for-3 inside at floor 4.0) |
| **X2** | Paragraph architecture and length defeat the qualification load: longest body paragraph 14,732 chars (~2,200 words, §V.B), then 11,312 (§V.E), 10,696 (App. G), 8,051; 139pp | all five | **Major** | **Yes** — paragraph-level measurement reproduces all four figures exactly |
| **X3** | +5.6pp is defended as "an anchor convention rather than a central tendency" and then used as a result (abstract, §I ×2, §VI.A, §VIII, Table 12) | EIC W5, DA M1+M2, R1 M5-fix, R3 M5 | **Major** | **Yes** — Table 1 row 4 prints both the disclaimer and the number |
| **X4** | Title and abstract assert a shortfall §III.B declines to call a policy miss | EIC W1, DA m1, R3 (coherence) | **Minor-Major** | **Yes** — §III.B: "not by itself evidence that a stated policy objective was missed" |
| **X5** | No outcome holdout anywhere; the behavioral margin is never tested against an external outcome moment | R1, R2, R3 M2, DA | **Major** | **Yes** — paper states it globally; Table 6 note a is an input-stability check by the paper's own words |
| **X6** | The max/additive form fork roughly doubles the marginal and also conditions the *headline decomposition* | EIC W6/W7, R1 M6, R3 M2/M6, DA A1 | **Critical** (see §2.1) | **Yes** — `floor_form_mixture_results.json` |
| **X7** | The floor read's evidential base is thin (137 cohort-months, 31 clusters, 5.9 effective, h_max 0.33) and its two independent corrections both sit above the clean band | R1 M2/M4, DA C1, EIC (evidence rationale), R2 M3 (opposite sign) | **Critical** | **Yes** — see §2.2 |
| **X8** | The imported elasticity carries zero propagated uncertainty, and the one internal test of its implied magnitude misses by 4.5× | R1 M7, R3 M2, DA (evidence), R2 M4 (adjacent) | **Major** | Artifact figures as reported by R1; not independently re-run |
| **X9** | The Danish leg is the weakest quantitative leg — one unrefereed source, a single-authored tax override, a band reported as a point | EIC W8, R2 M5/M6, R3 M3, DA m2/A5 | **Major** | **Yes** — see §2.4 |

### Two-reviewer

| # | Issue | Raised by | Severity | Verified? |
|---|---|---|---|---|
| Y1 | The bottom line sets a measured institutional quantity against an unmeasured household one; Table 1 has no household row | R3 M1, DA S1 (EIC partial) | Major | Yes (structural) |
| Y2 | "Mechanical" mislabels a null whose level is read off realized, partly behavioral turnover | R3 M6, DA (framing), R2 (adjacent) | Major | Yes — floor is *total* deep-discount turnover by §V.B's own concession |
| Y3 | Survival-selection attenuation is signed downward ex ante and excluded from the assembly | DA M5, R1 (adjacent) | Moderate — it *is* printed in Table 8 with the exclusion rationale | Yes |

### Single-reviewer, high value (all verified by me unless noted)

| # | Issue | Raised by | Severity | Verified? |
|---|---|---|---|---|
| **Z1** | The 75,000-loan pool is **not a probability sample of the SOMA book**: `loan_sample.py:97` allocates equally per origination quarter, giving exactly 15,000 loans per vintage 2017–2021 — 60% of the draw in 2017–19 against **6.0% of book face**, 2021 at 22% of the draw against 43.9% of face, 2022 absent; `weight` = 1.0 for all 75,000 rows | R2 M1 | **Critical** | **Yes** — code + parquet + `composition_shift_results.json` committed anchors |
| **Z2** | Basis mix at the sentence that adjudicates the form fork: "the central leg's recovery falls from 91.3% to 55.9%" compares a *shared* 91.3% with a *standalone* 55.9%; like-for-like is 100.4→55.9 or 91.3→46.8 | R1 M6(i) | **Major** (same defect class Appendix A retracted) | **Yes** — .tex:709 vs `floor_form_mixture` parity gates |
| **Z3** | Floor read's support undisclosed: 2018 + age≥12 selects **vintage 2017 only**, in **six reporting periods** (201807–201812; 2/48/48/49/49/49 rows), all cohort-months aged 12–24; Table 6's header says "2017–2019 performance" | R1 M2 | **Major** | **Yes** — `cohort_month_panel.parquet`, 245 rows, all `vintage == 2017` |
| **Z4** | Seasonal selection: the read months are the descending half of the committed calendar profile; weighting the profile by the read's own month counts gives 3.830% against a 4.000% pinned mean → floor ≈5.21% → marginal ≈+4.7/+4.8, a −0.8pp move, unpriced | R1 M3 | **Major** | **Yes** — `seasonal_floor_timing_results.json` `shape_only` profile reproduces R1's twelve numbers exactly |
| **Z5** | The off-window floor imports 2018's housing-activity level; up to 56% of the $20.874bn window component (~+1.5pp) may be cycle level, not lock-in circularity — the assembly's one available **upward** floor-side correction, never run | R2 M3 | **Major** | Window/depth components verified (`matched_depth_reconciliation`); the 24% activity ratio is R2's external datum, not verified here |
| **Z6** | Ginnie attribution wrong on the window: CRR (voluntary) carries **63%** of the CPR gap, CDR 40%; the quoted May-2025 snapshot is the one month buyouts dominate | R2 M4 | **Major** | **Yes** — 42-month means: CPR gap 2.137, CRR 1.354, CDR 0.847 |
| **Z7** | The Danish buyback discount D ∈ {0.32…0.38} is a **zero-prepayment** PV applied to a leg prepaying at 5.61% CPR; prepayment-consistent D ≈ 0.21–0.24, so every cash figure roughly halves (−$89/−$118bn → −$42/−$52bn) | R2 M5 | **Major** | **Yes, independently priced** — 3.0%/340mo/6.8%: 0 CPR → 65.8 (34.2% disc.), 5% → 79.1 (20.9%); at 2.49% WAC 61.8 (38.2%) / 76.4 (23.6%). The committed band *is* the no-prepay PV |
| **Z8** | Table 3 prints β₁ = +0.069, Table 7's β₁ column prints −0.0686, no reconciling note, no gate | DA M3 | **Major** (defect class has bitten twice) | **Yes** — .tex:244 vs .tex:395–404; Table 7 has no `tablenotes` |
| **Z9** | "Mid-grid anchor" is not robust to the paper's own ladder extension: on the five well-supported reads {4.695, 4.722, 4.869, 4.991, 5.334} the median is **4.869** (≈+6.0pp) | DA M2 | Moderate | **Yes** — `clean_band_under_extended_ladder.well_supported_reads_pct` |
| **Z10** | The 108 gates are a consistency layer, not a validity layer, and the repository proves it: `render_gate.py` records ~919 text items across 9 pages off the sheet, 302 of them the Appendix O ledger, surviving every prior round | DA M7 | Moderate — and the paper should *say* it | **Yes**, verbatim |
| **Z11** | Abstract's "and it identifies levels only" flatly contradicts §V.E ("The design does not identify the aggregate recovery level") and §VII.F ("does not identify levels") | EIC W2 | **Major, trivial to fix** | **Yes** |
| **Z12** | Abstract omits the paper's most novel result (the $87.8bn / 11.5% expectations complement), which is Table 1 row 2 and contribution #2 | EIC W4 | Major | **Yes** |
| **Z13** | Webb is quoted as "binding" while the paper's own rule ("the widest layer that does have a coverage property") selects a wider rung; Rademacher–Webb agreement is not a stability claim at h_max = 0.33 | R1 M1 | **Major** (superlative wrong — §8.1) | **Yes** on all ten rungs |
| Z14 | §VI.B's cap arithmetic has no objective function, conflicts with §I and §III.B, and omits the one deliverable a cap-setter needs ($bn/month with a band) | R3 M4 | Major | Structural; arithmetic checks (33.75/17.63 = 1.91) |
| Z15 | The 2018 depth ladder's *shape* (step then plateau: 4.695/4.722/4.869) is own-data evidence **for** the max form and is spent only as a level band | R3 M6b | Major **opportunity** | Nested reads verified |
| Z16 | Scope condition missing: the sign is forced here (99.53% of exposure below the window minimum), so the design is not identified in a mixed-gap episode, yet §VIII generalizes | R3 M7 | Major | Structural |
| Z17 | Benchmark's monthly series differenced off weekly Wednesday SOMA levels — wrong frequency for MBS paydowns; window-boundary allocation unpriced | R2 M8 | Major if sustained | **Not arbitrated** — I did not re-derive the benchmark |
| Z18 | Double-blind precluded: named author, affiliation, and a live `github.com/eugeneoCMU/Lock-in-Effect` URL | EIC W9 | Minor (submission mechanics) | **Yes** |
| Z19 | Missing references (Deng–Quigley–Van Order; Hanson 2014; Frankel et al. 2004; Fonseca–Liu–Mabille; López-Salido–Vissing-Jørgensen / Acharya et al.; Aiello 2022; Fuster–Lucca–Vickery) | R2 | Minor-Major | Bibliography has 70 entries; none of these |

---

## 2. ARBITRATION OF DISAGREEMENTS

### 2.1 The panel's two strongest claims contradict each other, and R1 wins

DA's **N1** — its single strongest positive finding — states: "There is no cell anywhere in the paper's apparatus in which the mechanical baseline fails to deliver the majority," evidenced by the PSA sweep's null recoveries of 68.4–101.9%.

**Ruling: N1 is false as a universal claim, and the counterexample is inside R1's M6.** I verified both sides. Across the PSA sweep at the headline floor the null recovers 101.9/94.8/82.4/68.4% standalone — 92.8/85.7/73.3/59.3% on the paper's own shared basis, so the majority does survive the convention DA attacked. But `floor_form_mixture_results.json` at floor 4.991, s = 1 gives central trapped $427.545bn and marginal $85.705bn, hence a null of $341.84bn — **44.7% standalone, 35.6% shared**. Under the additive form the mechanical baseline delivers a *minority*.

The editorial consequence is larger than either reviewer states. The abstract's lead finding — "switch the lock-in response off and the model still accounts for 85.7% of it" — is a **max-form result**, and the paper simultaneously (i) refuses aggregate fit as the form-selection rule and (ii) relies on the max form's fit for the claim that its partition partitions anything. A null at 35.6% does not decompose the object. **X6 is therefore upgraded to Critical**: it is the binding qualification on the paper's headline *qualitative* claim, not merely on the point estimate. R1's fix (ii) — one clause in the abstract, one sentence in §VII.F — is the highest-leverage sentence-level repair in this report.

Partially in the paper's favour: .tex:709 does print "55.9% of the benchmark against a 44.7% null," standalone against standalone. The additive null's level is not hidden. What is missing is the label on 85.7%.

### 2.2 The floor's transport error: R1:M3 and R2:M3 are opposite-signed, and both are unpriced

R1 says the read is seasonally selected low, so the true annual-equivalent floor is *higher* (≈5.21%) and the marginal *lower* (−0.8pp). R2 says the read imports 2018's hotter transaction market, so the floor is *too high* for 2022–25 and the marginal *higher* (+1.5pp). DA:C1 and R1:M4 add two measured reads that both push the same way as R1 (age-standardized 5.51%, Fannie 5.52%).

**Ruling: both mechanisms are real, they do not cancel by construction, and the preponderance of *measured* evidence runs against the headline.** Three of the four candidate corrections are measured or computable from committed artifacts and all three raise the floor (5.21 seasonal, 5.51 age-standardized, 5.52 Fannie, against a point of 4.991 and a clean-band top of 5.334). R2's is the only upward one and is the only one that requires external data the repository does not hold. So:

- The paper's sentence "every correction I can measure to the baseline turnover floor or to the accounting basis moves it down within the range rather than up" is **literally true** (R2's correction is not measured) and **must not be read as** "the unmeasured ones do too." R2's complaint that the sentence does rhetorical work is upheld as a framing defect; the sentence is not a factual error.
- Conversely, DA:C1's direction is supported by the paper's own artifact: on the pooled 2017–2019 leg, which *does* have mature cohort-months, the age≥24 read is **10.995%** against 6.065% at age≥12, and at matched depth (gap ≤ −0.0025) 8.92% against 5.185%. Turnover rises steeply with seasoning. A floor read entirely on 12–24-month-old loans, broadcast as a constant to a book aging 2→162 months, is signed toward understating the null and overstating the marginal. The paper's own verdict string is `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`, with `ramp_rise_is_psa_confounded: true`.
- **DA:C1 is upheld as the panel's most consequential finding.** Its severity claim is sustained, with one narrowing: the paper does *not* hide the two corrections — Table 8's headline row prints "age-standardized floor 5.51% → +3.8 (band open below +4.3)" and "Fannie… 5.52%… above the clean band and bracketing the marginal below +4.3." DA's "confining them to a note" is imprecise. The defect is that the headline was not moved to match, and the composed cell that *does* combine two of these corrections lands at **+2.928pp** — the interval's lower endpoint (`b5_joint_cell_results.json`, verdict `LANDS_AS_COMPOSED_LOWER_MEMBER`).

**Editorial finding I will state plainly:** on the paper's own committed reads, the marginal's mass sits in the *lower* half of [+2.9, +8.7], and +5.6 is above the centre of the measured evidence, not at it.

### 2.3 Is DA:C2 (the PSA layer) Critical, or an abstract defect?

DA argues the phrase "binding layer" and the abstract's "The design bounds it between +2.9 and +8.7 points" misinform by a factor of 2.5 in width.

**Ruling: Critical at the abstract and Table 1; Major elsewhere; DA's characterisation of the body is wrong.** §V.E already says "binding among the layers with a coverage property; the unestimated baseline-level convention spans wider (run `psa_level_sweep`)," and Table 8's headline row prints "baseline-level sweep 75–150 PSA +0.9 to +15.6 (a convention range, no coverage property)." The body is candid to the point of self-harm. The abstract is not: it carries the form-conditional hull (+3.5 to +13.1) and the phrase "under its production floor form," but no ramp caveat, and Table 1's uncertainty cell says "the binding layer" unqualified. DA's fix (a) and (b) are adopted; fix (c) — re-anchor h₀ on Path A's estimated seasoning spline — is the panel's single highest-value new run, and I rank it accordingly.

### 2.4 The Danish leg: how much of R2:M5/M6 survives?

**M5 is confirmed and I verified it independently.** My own cash-flow pricing of a 3.0% pass-through, 340 months, at 6.8%, gives 65.8 at 0 CPR (34.2% discount) and 79.1 at 5% CPR (20.9%); at the book's 2.49% WAC, 61.8 (38.2%) and 76.4 (23.6%). The committed grid {0.32, 0.34, 0.36, 0.38} is a no-prepayment PV band. `buyback_credit_bracket_results.json` derives nothing — its own spec calls the grid "the manuscript's committed proxy range." At D = 0.22–0.24, `gap_cash` = 61.188 − D×470.653 = **−$42.4bn to −$51.8bn**. The `REVERSES` verdict survives; the magnitudes in Table 1, §V.B, §VI.D and §VIII are ~2× too large; and R2's arithmetic on the derived claim is exact (the haircut is 1.69× the $61.2bn gap, not 2.5–2.9×).

**M6 is half right.** Table 1's headline cell is "+$61.2 billion" — the band's minimum — and the abstract omits the Danish result entirely. But §I already says "+$61.2 billion (8% of the benchmark), the zero-refinance edge of a band swept to +$256.8 billion at 3% refinance-in-place," and §VI.D/Table 13 carry the band and the realized-implied $1,212bn anchor. So the fix is one table cell and one abstract sentence, not a reframing.

### 2.5 R2:M2 — Table 25's coupon row

**Confirmed as a labeling defect, downgraded from Major.** The printed 18.0/68.2/13.8 reproduce `freddie.universe_panel.coupon_shares_exposure_weighted` exactly; the 3.865% WAC is `freddie.sample.mean_coupon_pct`, the 75,000-loan draw, whose own ≥4.0% share is 53.7% UPB-weighted / 58.2% count-weighted / 47.0% on raw coupons ≥4.00%. Two objects in one row — but the tablenote names both ("exposure-weighted universe-panel shares… the sample WAC is 3.9%"). This is imprecise presentation in the table whose purpose is basis discipline, not an arithmetic error. **Z1 (the pool's vintage composition) is the serious version of this complaint, and it is a different, worse problem.**

### 2.6 Abstract structure — DA vs EIC/R3

DA states the abstract is "a single paragraph, 248 words, verified." **It is two paragraphs** (an explicit `\par` at .tex:31) and **250 words** by my count. EIC and R3 are right on structure; DA's proposed fix ("break into two paragraphs at 'What lock-in itself adds…'") asks for a break the paper already has. Recorded in §8.

### 2.7 Y3 — attenuation in or out of the assembly

DA:M5 asks that survival-selection attenuation (+5.1/+4.6/+3.7 at a = 0.86/0.73/0.54) enter Table 5's assembly. **Partially upheld.** DA's logic is sound — if the imported coefficient is attenuated in the survival-selected pool it is applied to, the unattenuated marginal is biased up, which is a correction to the paper's own object. But Table 8 already prints the full grid, the frailty identity, the measured S = 40,234/75,000, and the exclusion rationale in the same cell. The remedy is a stated inclusion rule, not a disclosure. Severity: moderate, not major.

---

## 3. SCORE

### Reviewer-by-reviewer

| Dimension | EIC | R1 | R2 | R3 | DA | 5-rev mean | **Reconciled** |
|---|---|---|---|---|---|---|---|
| Originality (20%) | 73 | 71 | 74 | 72 | 71 | 72.2 | **72** |
| Methodological Rigor (25%) | 62 | 62 | 60 | 64 | 60 | 61.6 | **62** |
| Evidence Sufficiency (25%) | 60 | 60 | 57 | 61 | 58 | 59.2 | **59** |
| Argument Coherence (15%) | 74 | 70 | 74 | 68 | 66 | 70.4 | **70** |
| Writing Quality (15%) | 52 | 52 | 60 | 58 | 52 | 54.8 | **56** |
| **Weighted** | 64.0 | 63.0 | 64.2 | 64.6 | 61.4 | 63.4 | **63.6** |

**Reconciled weighted final: 72(.20) + 62(.25) + 59(.25) + 70(.15) + 56(.15) = 14.40 + 15.50 + 14.75 + 10.50 + 8.40 = 63.6 / 100**

### Departures from the mean, justified

- **Originality 72 (mean 72.2).** No departure. Five independent reviewers landed in a 3-point band, all crediting the same three genuinely new objects (the mechanical/elastic partition of the QT MBS shortfall, the 1.7–1.9× ex-ante cap arithmetic, the priced rule-only Danish transplant) and all discounting for the paper's own concessions in §II. Nothing in my arbitration moves it.
- **Rigor 62 (mean 61.6), +0.4.** I verified essentially every rigor complaint, so the level is right. The marginal upward nudge reflects two narrowings: R1's "narrowest of ten rungs" superlative is false (§8.1), and DA's C2 overstates the body's silence — §V.E and Table 8 both carry the coverage-property qualifier. Offsetting downward: Z1 (the pool is not a probability sample of the target book) is worse than any single reviewer's rigor deduction credited, and it was found by exactly one reviewer.
- **Evidence 59 (mean 59.2).** No material departure. The verified facts are decisive: the headline's identifying measurement is 137 cohort-months in 31 cross-sectional cells of **one origination vintage** observed in **six consecutive months**, all aged 12–24, on a pool whose vintage composition differs from the target book by a factor of ten, with 51% book-face coverage, no propagated elasticity uncertainty, and no outcome holdout. Offsetting credit the panel does give: the 17.6M-loan Fannie staging landing 0.52pp away, external bounds on two of three coverage gaps, ~200 frozen artifacts, and bit-exact parity gates that I confirmed reproduce every headline quantity I checked.
- **Coherence 70 (mean 70.4).** No departure. Seven verified coherence defects (Z11, X3, Z2, "binding layer" qualified in one place and not three, Z6's snapshot-for-mean, Table 1's Danish minimum, monotonicity retained as identified content) against genuinely exceptional machinery (Table 5's assembly, Table 27, three real retractions).
- **Writing 56 (mean 54.8), +1.2.** One deduction in the panel is not scorable against this draft: DA charged the off-sheet rendering history (~919 items, 9 pages) to *Writing Quality*. That defect is repaired in the current build — `tools/render_gate.py` exists, recomputes device coordinates, and the page count is now honest. A fixed defect belongs in §2 of a report about the gate suite's domain (where DA also correctly puts it, as M7), not in the current draft's presentation score. Everything else stands and is verified at paragraph level, so the score stays deep in the weak band.

---

## 4. DELTA VERSUS THE 76.3/100 BASELINE

Prior panel (`REVIEW2_v18_panel_2026-07-28.md`, manuscript at 125pp / ~79pp main / 226-word abstract): O 77.8 · M 76.5 · E 76.8 · C 78.5 · W 71.0 → **76.3**.

| Dimension | Prior | Now | Δ | What earned / what cost |
|---|---|---|---|---|
| Originality | 77.8 | 72 | **−5.8** | **Earned: nothing new.** R28–R31 added no contribution; they hardened existing ones. **Cost:** this panel priced §II's own concessions ("the observation is theirs") and the forced signs harder — all five landed 71–74. **This delta is calibration, not regression.** |
| Methodological rigor | 76.5 | 62 | **−14.5** | **Earned:** the 10-rung ladder is credited as "more careful few-cluster inference than most published applied work" (DA N3) and the retractions as exemplary (R1 S2, DA N5/N6). **Cost, and this is the core of the whole delta:** every new disclosure created a quotable liability that was disclosed but not *acted on*. Printing ten rungs let R1 find the one the paper's own selection rule prefers (Z13). Extending the depth ladder to five reads let DA compute a different median (Z9). Running `psa_level_sweep` documented a 14.77pp convention span (X1). Running `floor_form_mixture` documented that the additive form halves the null's level (X6/Z2). Then, independently, two reviewers went into `cohort_month_panel.parquet` and `loan_sample.py` — which the prior panel did not — and found Z3 and Z1. |
| Evidence sufficiency | 76.8 | 59 | **−17.8** | Largest drop. **Earned:** the Fannie floor read, the age-standardized read, the b5 composed cell, the Danish external validation are all credited as real additions. **Cost:** each new read landed *against* the headline (5.52, 5.51, +2.928) and was disclosed without moving the headline, so the panel scored the gap between what is now known and what is now printed. The prior panel wrote "the evidence exists; its aggregation is now the issue"; this panel found the aggregation issue plus two undisclosed sample facts. |
| Argument coherence | 78.5 | 70 | **−8.5** | **Earned:** the symmetric assembly and range-led front matter still register (EIC S1, R3 S2, DA N9). **Cost, and this is directly caused by the remediation:** retiring the "middle member" posture while keeping +5.6 in the abstract, title-level framing, §VI.A, §VIII and Table 12 manufactured a new attack — a headline whose own defense is "an anchor convention rather than a central tendency" (X3). Three reviewers hit it independently. |
| Writing quality | 71.0 | 56 | **−15.0** | **Cost:** 125pp → 139pp, and the render repair honestly added ~9pp of previously off-sheet content. More consequentially, this panel measured *paragraph* structure where the prior panel measured page count: 14,732 chars in the subsection referees are directed to first. **Nothing in R28–R31 touched paragraph architecture.** |
| **Weighted** | **76.3** | **63.6** | **−12.7** | Crossed back from the Minor band's interior to the Major band. |

### What bought nothing, and what hurt

Honest accounting, since the task asks for it:

- **Bought real credit:** the Danish band after external validation contradicted a pinned assumption (all five credit it); the Webb wild-cluster correction and its `MOVES` verdict (R1 verified the pre-commitment fired against the author's interest); the mixture curve replacing a circular selection rule; the render repair (necessary, and it is why the paper is now honestly 139pp).
- **Bought nothing measurable:** the floor rename to "baseline turnover floor." Not one reviewer credits it, and two (R3 M6, and R1/DA implicitly) still attack **"mechanical"** as the word doing the overclaiming. The rename fixed the wrong word. Likewise the results-section reorganization — no reviewer credits it, and §V.B is still one 2,200-word paragraph.
- **Net negative:** retiring the "middle member" posture *while keeping +5.6* as the printed headline. Either drop the point and print the range, or state and defend an anchor rule — DA:M2 shows the current implicit rule (median of three printed cuts) is not robust to the paper's own five well-supported reads. Half-retiring the posture cost more coherence than the honesty earned.
- **Ambiguous, and one run from being an asset:** `psa_level_sweep`. Running it was correct; disclosing a 2.49×-wider convention span and then not re-anchoring h₀ converted candor into the panel's second CRITICAL. One run (Path A's estimated seasoning spline as h₀) flips the sign of that trade.

The blunt summary: **R28–R31 measured more of the paper's own uncertainty than it re-priced.** A disclosure that is not carried into the headline reads to a fresh panel as an unpriced defect, not as candor.

---

## 5. EDITORIAL DECISION

## MAJOR REVISION

**Band check.** Reconciled weighted final **63.6**, inside the Major band (50–64), 1.4 points below Minor. All five reviewers recommended Major independently (61.4–64.6, a 3.2-point spread — unusually tight). The Devil's Advocate logged **two CRITICAL findings** (C1 the age-incomparable floor, C2 the unestimated baseline ramp), which independently bars Accept under the panel's iron rule. I have upheld both, and I have upgraded a third issue to Critical on my own arbitration (X6, the form fork's conditioning of the *mechanical-majority* headline) plus a fourth (Z1, the pool's non-representativeness of the target book).

**Reasoning.** The execution layer of this paper is at or above field-journal standard and I want to be unambiguous about that: I re-derived eight headline quantities from the frozen artifacts and every one reproduced; the pre-commitment convention is genuinely auditable and fired against the author's interest at least twice; the adverse-findings register is a transportable research-practice contribution. The paper is held at Major by three things, none of which is a wording problem:

1. **The estimation population is not the target population, on the dimensions that set the answer** (Z1). Sixty percent of the pool is 6.0% of the book; the vintage carrying 43.9% of book face is 22% of the pool; the sampler's allocation rule is nowhere in the manuscript. Under the max form the marginal is zero wherever the baseline sits below the floor, so vintage weighting is not a second-order composition detail — it is the censoring geometry.
2. **The layer called binding prices the smallest of at least four uncertainty sources.** Within-read cluster SE 0.39pp of CPR; between-read spread 0.53pp (4.991 vs 5.51 vs 5.52); seasonal selection ≈0.22pp signed; convention span 14.77pp on the marginal against the interval's 5.82. A confidence interval on one nuisance input, at fixed values of three inputs that each matter more, is not an interval on the lock-in marginal.
3. **The headline qualitative claim is form-conditional and unlabelled** (X6). "Mostly mechanical" is 85.7% under the max form and 35.6% under the additive form on the paper's own shared basis.

Every one of these is repairable with machinery already in the repository and no new data, which is why this is Major and not Reject. A revision that lands R1–R8 of §7 would, on this instrument, sit in the low-to-mid 70s and be a credible JMCB / *Journal of Housing Economics* / *Real Estate Economics* submission. The empirical work already deserves that hearing.

---

## 6. CARROLL ROUND VERDICT

## PRESENT WITH FIXES

All five reviewers wrote "ready to present and defend as-is" — and all five then attached a precondition that cannot be met in the room without changing the text first: DA says re-cut the headline "*before* the debut"; R1 says "present the range rather than +5.6"; R2 says stop quoting the −$89bn Danish figure out loud; EIC requires a rehearsed 60-second answer to the form fork; R3 requires two slides the manuscript does not contain. The union of five preconditions is not "as-is." With **no revision checkpoint**, the fixes below must land in the deck and in the four sentences of the .tex named in §7 (R1–R3, R10) before the talk. That done, this paper will read as far above undergraduate norm and should win its session.

### The three things most likely to be attacked, and how defensible each is

**1. "What sets your baseline seasoning ramp — did you estimate it?" (X1)**
*Defensibility: weak on the fact, strong on the consequence.* The honest answer is "no — 100 PSA is an industry convention, and sweeping it 75–150 carries my marginal from +0.9 to +15.6 points, which I disclose in §V.E and Table 8 as a convention range with no coverage property." That concession is survivable only if the follow-through is immediate and rehearsed: **the paper's headline qualitative claim survives the entire sweep** — the β₁=0 null recovers 92.8%, 85.7%, 73.3% and 59.3% of the benchmark on the shared basis at 75/100/125/150 PSA, so the mechanical baseline delivers the majority in every cell. Lead with that. Do not attempt to defend +5.6 as a central tendency; the paper already says it is not one.

**2. "Is your 75,000-loan pool a sample of the Fed's book?" (Z1)**
*Defensibility: weak.* The answer is no, and the numbers are unflattering: equal allocation per origination quarter, 15,000 loans per vintage, 2017–19 at 60% of the draw against 6.0% of book face, 2022 absent, all weights 1.0. What can be said: §III.B states the 51.0% book-face coverage on the book's own agency × vintage joint cells; the out-of-window vintage share is bounded at $11.7bn from Fannie cohort speeds and the Ginnie share at $20–47bn from published differentials, both signed toward overstatement. What must **not** be said is that the pool is representative, or that the coupon reweight tests this — it rescales aggregate output and cannot test a per-loan censoring effect. Prepare one slide with the three-column table (draw / estimation universe / book face) and own it before the question is asked.

**3. "Your floor is read on 12–24-month-old loans, one vintage, six months of 2018 — and both of your own corrections put it above your band." (X7 / DA:C1)**
*Defensibility: moderate, and best handled by conceding hard.* The paper already prints both corrections in Table 8 ("band open below +4.3"; Fannie 5.52% "bracketing the marginal below +4.3") and the composed cell at +2.9. Say it first: the band's lower edge is the soft one, the composed correction lands at the interval's lower endpoint, and the age-transport error is signed against the headline and not computable in the clean leg (the artifact's own verdict is `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`). Do not say the floor is "measured on 2017–2019 performance" — Table 6's header says that and it is wrong for the three rows that set the headline.

*Fourth, cheap and embarrassing if left:* the abstract says "it identifies levels only" while §V.E says the design does not identify levels. Fix the sentence before printing the handout.

---

## 7. REVISION ROADMAP (ranked by value per unit effort)

| # | What | Where | Why it matters | Effort | Before presenting? |
|---|---|---|---|---|---|
| **R1** | Three abstract repairs: (a) "identifies levels only" → "identifies levels, not monthly timing"; (b) label the 85.7% as a max-form result and give the additive null (35.6% shared) in the same clause; (c) replace "The design bounds it between +2.9 and +8.7" with §V.E's own qualified formulation ("binding among the layers with a coverage property; the unestimated baseline ramp spans +0.9 to +15.6 at the same calibration") | `.tex:31` | The abstract is the only page most readers and every session attendee will read, and it currently contains a self-refuting clause (Z11), an unlabelled form-conditional headline (X6) and an unqualified bounding claim (X1) | 1 hour, no runs | **Required** |
| **R2** | Repair the basis mix: "the central leg's recovery falls from 91.3% to 55.9%" → one basis (100.4→55.9 standalone, or 91.3→46.8 shared) | `.tex:709` | Same defect class Appendix A already retracted, in the sentence that adjudicates the paper's largest fork, understating the additive form's level cost by 9 points | 15 min | **Required** |
| **R3** | Disclose the floor read's support in one sentence at every quoting site, and correct Table 6's "(2017–2019 performance)" for the three defensible rows: vintage 2017 only, six reporting periods 201807–201812, all cohort-months aged 12–24, mature test not computable, age-transport error signed against the headline | §VII.F, Table 6 caption, Definitions block | Accuracy of the sample description behind the abstract's interval; Z3 + C1 are the two facts a methodologist will find in five minutes | 1–2 hours, no runs | **Required** |
| **R4** | Add the β₁ sign note to Table 7 (or flip the printed signs) plus a gate asserting Table 3's and Table 7's δ = 6.5% values agree in sign | `.tex:388–407` | Two printings of the paper's single most load-bearing parameter with opposite signs, in a paper with two prior documented sign/units defects in this coefficient | 15 min | **Required** |
| **R5** | Re-anchor h₀ on Path A's **estimated** seasoning spline (knots {12,24,36,60,84,120}) and report the paired-leg marginal there | new run + §V.E, Table 8 | Converts the largest disclosed uncertainty layer from a convention into an estimate. This single run is what turns X1/C2 from the panel's second Critical into an asset | 1 run | Optional for the talk; **required before submission** |
| **R6** | Post-stratify the existing 75,000 loans onto the SOMA coupon × vintage-group cells and re-derive the marginal; state the sampler's allocation rule in Appendix E; add the draw's own composition row to Table 25 | new run + Appendix E, Table 25 | Z1 — the estimation population must be shown to represent the book it is scored against, or the headline must be restated as conditional on the draw's composition | 1 run (reuses `cross_design_reweight` machinery) | **Required before submission** |
| **R7** | Two-sided floor transport test: (a) calendar-standardize the off-window read to the QT window's month mix using `seasonal_floor_timing`'s own normalizer; (b) measure the floor's dependence on housing-activity level and report an activity-matched read | new runs + §VII.F, Table 5 | Z4 and Z5 are opposite-signed and both unpriced; together they decide whether the assembly's one-directional posture can stand. Running only (a) makes the paper worse-off honestly; running only (b) is self-serving. Run both | 2 runs | **Required before submission** |
| **R8** | Quote CR3-BM $[+2.3,+9.6]$ or the WCR inversion $[+2.3,+9.1]$ beside Webb, **or** state in one sentence why the wild bootstrap is preferred to Bell–McCaffrey at G* = 5.9 / h_max = 0.33; delete the Rademacher–Webb near-identity as a stability claim; note that CR3-BM's upper endpoint is grid-truncated at 6.0% | Table 9 + note, Table 8, Table 1 | Z13 — the paper's stated selection rule ("the widest layer that does have a coverage property") selects a rung it computed and did not quote | 1 hour, no runs | Optional for the talk |
| **R9** | Re-derive the Danish discount D from the leg's own 5.61% CPR against the window rate path (or matched-coupon TBA marks) and restate every dependent figure; headline the band [+$61.2, +$256.8]bn in Table 1's headline cell; add one sentence that the Danish mechanism is an open-market bond repurchase, so the par-denominated cap is not the natural scorer | §VI.D, Table 1, Table 13, §V.B, §VIII | Z7 — every cash figure is ~2× too large; the sign reversal survives, so this is a magnitude repair the paper can absorb without changing a conclusion | 1 calculation + edits | Optional for the talk; **do not quote −$89/−$118bn aloud until done** |
| **R10** | Restate the Ginnie attribution as a window mean: CRR carries 63% of the CPR gap (1.354 of 2.137), CDR 40%; score a Ginnie leg with the elasticity *attenuated* by the observed CRR differential rather than only share-scaled to zero; add the assumability upper bound the CRR series supplies | `.tex:269`, §V.B, §I, §VIII.A | Z6 — the quoted May-2025 snapshot is the one month buyouts dominate; the voluntary majority is the piece that bears on the imported elasticity for 20.4% of book face | 1 sentence + 1 run | Optional |
| **R11** | Split §V.B at its five seams (specification / floor semantics / elasticity import and its three transports / aggregation bounds / ablations); move the competing-risks taxonomy to Appendix E; split §V.E and Appendix G's monoliths; fold §VI.C into §VI.B | §V.B, §V.E, App. G | X2 — a 2,200-word paragraph in the subsection referees are directed to first. Mechanical, costs no content, and it is the single largest scoring deficit (Writing 56) | 1 day | **Required before submission**; recommended before the talk if time permits |
| **R12** | Report the marginal in transaction counts with the moving-share bracket applied, set against realized mortgage-financed transaction volume, and state the verdict whichever way it falls | §VI.A, Table 1 | R3 M1/M2 — the paper's first outcome-side external check, and the only unit in which the household leg becomes commensurable with the institutional one | 1 script | Optional for the talk (but prepare the slide) |
| **R13** | Rewrite §VI.B around the achievable-path band in $bn/month (≈$16–18bn/month, ±≈$4bn from the floor read's own interval), a two-input table (book OTM share × turnover-floor band → implied cap), and an explicit statement of the objective a cap serves | §VI.B | Z14 — this is the paper's most exportable contribution and it is currently stated without an objective function or a deliverable | Half day | Optional for the talk (prepare the slide) |
| **R14** | Recompute the analytic implied cross-sectional gradient at the 4.991% headline floor and under the additive form, at 75/100/125 PSA | §V.D, §VII.F | R1 M7 — the implied path is analytic, needs no engine run, and would be the first *realized-data* evidence bearing on the form fork | Under an hour | Optional |
| **R15** | Retitle to the claim the paper establishes (e.g. "…Redemption-Cap Shortfall" or "Mortgage Lock-In and the Composition of the Federal Reserve's Agency-MBS Runoff") | title | X4 | 5 min | Optional for the talk; required for submission |
| **R16** | Anonymized master with an archived DOI (Zenodo) in place of the GitHub URL; add the seven missing references (Z19); add one sentence to Appendix O ¶1 stating the gates' domain (Z10) | title block, App. A, bib, App. O | Submission mechanics and positioning; the Appendix O sentence *strengthens* the credibility claim | 2–3 hours | Required for submission only |

---

## 8. WHAT THE PANEL GOT WRONG

Checked against the manuscript and the artifacts. Each of these is a factual error in a report; none of them overturns the issue it appears in, which is itself worth knowing.

**8.1 R1:M1 — "the narrowest of the ten rungs."** False as stated. Widths in pp: percentile (demoted) 5.045; **CR1-t(30) 5.197**; **CR2-t(30) 5.579**; Webb 5.823; Rademacher 5.927; CR3-t 6.001; CR1-BM 6.043; CR2-BM 6.740; WCR 6.828; CR3-BM 7.284. Webb is the **third**-narrowest live rung, and the narrowest of the six with a credible few-cluster coverage property — which is R1's actual argument and it survives. Two further corrections R1 does not mention: CR3-BM's upper endpoint (9.5645) is **grid-truncated** (`truncated_at_grid_edge: true`, mapped at the 6.0% grid edge), so promoting it as the binding layer requires extending the floor sweep grid; and the paper's own printed selection sentence is "the widest layer that does have a coverage property," which R1 quotes accurately.

**8.2 DA:m3 — the abstract is "a single paragraph, 248 words, verified."** Wrong on both counts. There is an explicit `\par` at `.tex:31`; the abstract is two paragraphs, and my count is **250 words**. DA's recommended fix ("break into two paragraphs at 'What lock-in itself adds…'") describes a break that already exists at exactly that seam. EIC (248) and R3 (246) are right on structure and marginally low on the count.

**8.3 DA:N9 — of the ~13 Table 27 rows adjudicated against the headline, "not one moved a reported number."** False. The floor demotion moved the headline from +9.2 to +5.6 points and the central level from 97.9% to 91.3%, through every dependent number, table and the conclusion. The bootstrap retraction replaced a printed $[+9.17,+9.23]$ with $[+8.27,+10.19]$. The Webb correction moved the printed lower endpoint (`floor_inference_correction_v2_results.json`: `printed_lower_unchanged: false`, 2.796 → 2.855). The Danmarks Nationalbank validation turned a Danish point estimate into a swept band. `buyback_credit_bracket`'s `REVERSES` verdict turned a signed relief claim into the incidence bracket now printed in Table 1. DA's withholding of full credit for the register is defensible on other grounds (M7); this specific reason is not.

**8.4 DA:N1 — "no cell anywhere in the paper's apparatus in which the mechanical baseline fails to deliver the majority."** False as a universal claim, and refuted by another reviewer's evidence in the same panel: `floor_form_mixture_results.json` at floor 4.991, s = 1 gives a β₁=0 null of $341.84bn = 44.7% standalone / **35.6% shared**. DA scoped its check to the PSA sweep at the production form; the claim as written ranges over the apparatus. See §2.1 — this is the arbitration with the largest editorial consequence in this report.

**8.5 R2 minor 10 — duplicated table captions "will read as sloppiness in a submitted PDF."** The duplication exists only in the markdown edition (a bold caption at md:41 and the same caption re-emitted inside the header row at md:43), an artifact of the longtable→markdown converter. In the `.tex` the caption sits correctly before `\endfirsthead`. There is no PDF defect. R2 hedged correctly ("a build/converter artifact") and then drew the wrong inference.

**8.6 R2:M6 — "the paper headlines the minimum."** Right for Table 1's headline cell (which prints "+$61.2 billion") and for the abstract (which omits the Danish result entirely); wrong for §I and §VI.D, both of which give the band and explicitly label +$61.2bn "the zero-refinance edge of a band swept to +$256.8 billion at 3% refinance-in-place." The fix is one table cell and one abstract sentence.

**8.7 R2:M2 — "the sample's ≥4.0% share is 53.7%, not 13.8%."** 53.7% is correct only on UPB-weighted rounded-coupon buckets. The same draw is 58.2% on count-weighted buckets and 47.0% on raw coupons ≥ 4.00%. The three-object confusion R2 identifies is real and the finding stands; the number needed its own basis named — which is the irony of a basis-labeling complaint.

**8.8 R3 — "40,234 active at window start" from `loan_sample.parquet`.** The parquet gives **40,077** rows with `balance > 0`; 40,234 is the survival count in `attenuation_sensitivity_results.json`. The mean balance ($126,813) and the downstream arithmetic are unaffected.

**8.9 R2:M8 (benchmark frequency) — not arbitrated.** I did not re-derive the $764.7bn benchmark from the weekly SOMA series, so I record M8 as plausible-but-unverified rather than confirmed. The cap arithmetic itself checks (3 × 17.5 + 39 × 35 = 1,417.5; 1,417.5 − 652.8 = 764.7), and the paper's own Appendix N documents the four clip-induced zero months. If the author disputes M8, that is a legitimate response; if not, R2's proposed rebuild from published monthly SOMA principal-payment data is the right remedy and would also reopen the timing question the paper currently forecloses on the strength of a defect in its own comparator.

**8.10 A calibration note on the panel as a whole.** Four reviewers independently reported the same paragraph-length measurement (14,732 / 11,312 / 10,696 / 8,051 characters) and I reproduced all four exactly; four independently reported the PSA span and the 2.49× ratio and I reproduced them exactly; three converged on the floor read's thin support from two different entry points (the artifact's seasoning block and the raw cohort panel) and both reproduce. The panel's factual error rate is low and concentrated in superlatives and in one shared blind spot — no reviewer checked whether the abstract they were criticising was one paragraph or two.

---
