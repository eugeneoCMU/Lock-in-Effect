# Mortgage Lock-In Manuscript Redesign

## Objective

Restructure *Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall* into a journal-facing mortgage lock-in paper whose institutional application is Federal Reserve agency-MBS runoff.

The conference title remains unchanged. The revision will define "quantitative-tightening shortfall" immediately and precisely as the cumulative gap between realized Federal Reserve agency-MBS redemptions and the announced agency-MBS runoff ceilings. It will not use that phrase to describe the performance of the Federal Reserve's overall balance-sheet reduction program.

The target package is:

- a 35--45 page main paper, including references;
- an online appendix containing the material needed to evaluate the main estimates and all material adverse findings; and
- the existing repository records and replication materials containing the complete audit and development history.

The page target is a design objective, not permission to remove a unique qualification, change an estimand, or suppress an adverse result. Correctness and traceability take priority over the exact page count.

## Paper Identity

The revised paper asks one question:

> How much did mortgage lock-in add to the Federal Reserve's agency-MBS runoff shortfall during the June 2022--November 2025 quantitative-tightening cycle?

The paper's contribution is a portfolio-level quantitative decomposition. It imports causal mortgage-lock-in elasticities from prior household- and loan-level research and translates them into Federal Reserve MBS runoff using SOMA holdings, loan-level mortgage data, and a disclosed baseline-turnover model. It does not claim to identify a new causal elasticity.

The paper will distinguish three objects consistently:

1. **Cap-relative MBS runoff shortfall:** the $764.748 billion cumulative gap between realized agency-MBS redemptions and the announced caps.
2. **Expectations-relative shortfall:** the $87.8 billion central gap between realized runoff and the New York Fed's contemporaneous projection, conditional on the disclosed within-year allocation and subject to the possibility that the projection already incorporated some lock-in.
3. **Lock-in marginal:** the difference between model-implied cumulative runoff under the imported lock-in elasticity and under the rate-insensitive null, reported as a model-based and specification-dependent quantity.

The central conclusion is:

> Mortgage lock-in materially slowed Federal Reserve MBS runoff, but it did not cause the entire cap-relative shortfall. Most of that shortfall reflected ceilings set above achievable runoff and baseline mortgage cash flows. The incremental lock-in contribution is positive across the disclosed calibrations, while its exact institutional magnitude depends materially on how baseline turnover is combined with rate-sensitive prepayment.

## Evidence Hierarchy

The main paper will present the evidence in this order:

1. Agency-MBS runoff fell $764.748 billion below the announced caps.
2. The New York Fed's contemporaneous projection already anticipated most of that cap-relative gap.
3. The cap-relative gap is therefore not itself a measure of unexpected mortgage lock-in.
4. A loan-level mortgage model maps externally estimated lock-in elasticities into Federal Reserve portfolio runoff.
5. The rate-insensitive null accounts for a large share of the cap-relative gap under the production floor form.
6. Mortgage lock-in adds a positive but specification-dependent margin over that null.
7. Functional-form and calibration uncertainty, rather than simulation-seed or ordinary loan-sampling uncertainty, governs the interpretation.

The 91.3% Path B recovery is not a validation headline. When retained, it must be described as the model-implied share of the cumulative benchmark and immediately paired with the null's 85.7% contribution at the headline off-window floor. Monthly path fit is not evidence supporting the main result.

## Claim Boundaries

The revised paper will:

- describe the analysis as a quantitative model-based decomposition;
- state that the lock-in elasticity's causal content is inherited from external estimates;
- identify the lock-in marginal, not the entire level, as the primary estimand;
- distinguish direct sample evidence, SOMA reweighting, observed-speed overlays, and extrapolation to excluded cells;
- report that no clean outcome-holdout months validate the aggregate level;
- state that monthly timing remains unexplained by every estimator; and
- state that the expectations-relative ratio is an allocation-conditional upper-bound exercise, not a causal partition of surprise.

The revised paper will not claim:

- that it newly identifies the causal effect of mortgage-rate gaps;
- that mortgage lock-in caused the full $764.748 billion cap-relative gap;
- that the hazard framework is superior to the ABM as a modeling paradigm;
- that aggregate recovery validates monthly dynamics;
- that the Danish counterfactual estimates a complete institutional transition; or
- that the paper evaluates the Federal Reserve's entire quantitative-tightening program.

## Functional-Form Posture

The production hard-maximum floor and the additive alternative are first-order assumptions, not routine robustness checks. The main paper will introduce both forms before interpreting the lock-in marginal:

\[
h^{\mathrm{max}}_{it}=\max\{h^{\mathrm{floor}}_{it},h^{\mathrm{rate}}_{it}\}
\]

and

\[
h^{\mathrm{add}}_{it}=h^{\mathrm{floor}}_{it}+h^{\mathrm{rate}}_{it}.
\]

The production hard-maximum form remains the primary specification because it is the committed production construction. The paper must immediately disclose that it mechanically censors the rate component when the floor binds and that the additive form produces a materially different null and marginal.

The main result will therefore have two layers:

- the production-form interval and anchor, labeled as conditional on the hard-maximum construction; and
- a cross-form or convention envelope showing how the institutional magnitude changes under the additive or competing construction.

The paper may conclude that the lock-in contribution is positive across disclosed specifications. It may not call the institutional cash-flow contribution unconditionally small or treat the production-form result as form-invariant.

## Main-Paper Architecture

### 1. Introduction: 4--5 pages

The introduction will make six moves only:

1. state the mortgage lock-in mechanism;
2. define the agency-MBS runoff problem and the paper's use of "QT shortfall";
3. distinguish the cap-relative and expectations-relative benchmarks;
4. describe the loan-level decomposition and imported elasticity;
5. report the lock-in marginal together with its functional-form dependence; and
6. state the contribution and principal limits.

The current multi-page core-results table will be replaced by a one-page table containing the benchmark, expectations complement, rate-insensitive null, production-form lock-in marginal, and cross-form result. Robustness catalogs, estimator inventories, detailed policy mechanics, run history, and navigation prose will leave the introduction.

### 2. Mortgage Lock-In and Federal Reserve MBS Runoff: 3--4 pages

This section will combine the essential institutional setting and literature. It will organize prior work into:

- causal evidence on household and loan-level mortgage lock-in;
- mortgage prepayment, duration, and MBS cash flows; and
- Federal Reserve balance-sheet normalization and MBS runoff.

It will identify the missing translation from existing household- or loan-level elasticities to the runoff of the Federal Reserve's agency-MBS portfolio. Detailed model histories and policy-system comparisons will move to the sections where they are used or to the online appendix.

### 3. Data and Empirical Benchmarks: 5--6 pages

This section will define:

- SOMA holdings, caps, and the June 2022--November 2025 window;
- the cap-relative and expectations-relative benchmarks;
- the Freddie 2017--2021 conventional loan sample;
- the sample's joint agency-by-vintage coverage of SOMA book face;
- SOMA coupon reweighting and the common curtailment accounting layer; and
- which exclusions are bounded by Fannie, Ginnie, vintage, term, or observed-speed evidence.

The section will separate facts observed directly from modeling, calibration, reweighting, and proxy overlays.

### 4. Loan-Level Decomposition: 7--9 pages

The current internal label "Path B" will be replaced in publication-facing prose by **Loan-Level Prepayment Model**. Repository run names may remain in replication documentation.

The section will explain:

- the baseline turnover component;
- the imported rate-gap elasticity and its provenance;
- competing prepayment and default risks;
- the central and zero-elasticity simulations;
- the lock-in marginal as the difference between those simulations;
- the production and additive floor forms; and
- the conversion from simulated hazards to portfolio-level dollars and benchmark shares.

Path A will not appear as a coequal estimator. Its aggregate result, exclusion from headline ranges, and path-fit failure will appear only where they help evaluate the primary model.

### 5. Results: The Lock-In Marginal: 6--8 pages

This section will report:

- the rate-insensitive null and central model-implied levels;
- the production-form lock-in interval and anchor;
- the cross-form or convention envelope;
- the elasticity-by-floor calibration surface;
- the hierarchy of sampling, cluster, calibration, and functional-form uncertainty; and
- the limits on interpreting aggregate recovery as validation.

Tables will not mix incompatible accounting bases. Prose will not read tables row by row.

### 6. Functional Form, Calibration, and External Validation: 5--7 pages

Only interpretation-changing checks remain in the main paper:

- off-window turnover-floor measurement;
- hard-maximum versus additive or competing form;
- the imported elasticity range;
- Fannie replication;
- Ginnie and excluded-vintage overlays;
- SOMA composition and accounting-basis sensitivity;
- lack of monthly outcome validation; and
- a compact ABM cross-design comparison.

The uncertainty hierarchy will be explicit: simulation-seed noise is negligible at reporting precision; loan-sampling uncertainty is not the binding issue; calibration and functional form dominate.

### 7. Policy Implications: 3--4 pages

The primary implication is cap design. Future agency-MBS runoff ceilings should be based on scheduled amortization, plausible baseline turnover, and the coupon distribution of the portfolio rather than treated as symmetric with Treasury redemption caps.

The Danish market-value-repurchase exercise will become a short extension. The main text will retain the rule, the principal incidence-sensitive result, and the unpriced TBA-liquidity limitation. Detailed recalibration, alternative anchors, fine grids, and institutional-transition mechanics will move to the online appendix.

### 8. Conclusion: 1--2 pages

The conclusion will state three results without replaying the robustness section:

1. announced MBS caps substantially exceeded contemporaneously projected achievable runoff;
2. mortgage lock-in reduced MBS runoff but is not measured by the full cap-relative gap; and
3. the lock-in marginal is positive and economically meaningful but conditional on the baseline-turnover structure.

It will close with the cap-design implication and the precise identification boundary.

## Role of the ABM and Model Comparison

The ABM will remain as supporting and adverse evidence, not as a second paper inside the paper. The main text will retain:

- the production ABM level result;
- its weak monthly path fit;
- the reason no interpretable ABM differential is reported;
- the real-covariate threshold crossing; and
- the withdrawal of the clean modeling-paradigm interpretation.

The full household decision rule, behavioral extensions, seed results, null-feasibility analysis, cross-design experiments, and parameter provenance will move to the online appendix or existing replication material. The paper will not claim that the hazard framework wins a controlled model comparison.

## Online-Appendix Boundary

The online appendix may remain substantial. Its purpose is to let a referee evaluate the paper without carrying the entire research history in the main text. It will contain:

- full benchmark and accounting derivations;
- detailed loan-level hazard specification and parameter provenance;
- complete inference and calibration ladders;
- floor, elasticity, form, composition, settlement, seasonal, and accounting grids;
- Path A specification and results;
- full ABM model, extensions, seed analysis, null-feasibility analysis, and cross-design tests;
- Fannie, Ginnie, vintage, term, and sample-to-book analyses;
- monthly timing and path-fit diagnostics;
- detailed Danish counterfactual derivations, anchors, incidence cases, and TBA limitations; and
- additional exhibits directly cited by the main paper.

Internal run identifiers, manifests, gate histories, mutation-test records, superseded-result ledgers, and development chronology will remain in the repository's technical and replication records unless a referee needs them to interpret a reported result.

## Exhibit Strategy

The main paper will use a small exhibit spine.

### Figures

1. Realized agency-MBS runoff against the caps and contemporaneous projection.
2. Portfolio exposure to mortgage-rate gaps or the relevant coupon distribution.
3. Central and zero-elasticity cumulative runoff paths.
4. Lock-in marginal across elasticity, floor, and functional-form assumptions.
5. Sample-to-SOMA coverage or composition.

### Tables

1. Main quantities and definitions.
2. Data and SOMA sample coverage.
3. Main lock-in decomposition.
4. Functional-form and calibration sensitivity.
5. External replication and excluded-portfolio checks.

An exhibit may be omitted if its information is clearer in prose or consolidated with another exhibit. The ABM staircase, Danish sensitivity figure, full accounting-basis tables, complete uncertainty ladders, and detailed cross-design panels will move to the online appendix.

## Editorial Rules

The main paper will present the final valid analysis, not narrate the development process. Phrases such as "the gate passed," internal run names, production-generator assertions, retracted intermediate intervals, and histories of earlier extrapolations will leave the main prose unless necessary to disclose a material change in the evidentiary status of a result.

Pre-commitment will be explained once as a specification-discipline device. It will not be repeated as a substitute for identification or validation.

The revision will preserve all substantive adverse findings. Moving an adverse result to the online appendix is permitted only when its governing implication remains stated in the main text.

## Content-Preservation Rules

The following content is protected and must survive in the main paper or online appendix:

- both empirical benchmark definitions and their construction limits;
- the preferred loan-level estimand and rate-insensitive null;
- the current headline values and binding uncertainty construction;
- the meaning, provenance, and sensitivity of the turnover floor;
- the hard-maximum and additive functional forms and their materially different implications;
- the distinction between aggregate level and lock-in marginal;
- every unique elasticity-transport and sample-to-book assumption;
- every unique identification and outcome-validation limitation;
- the Fannie exercise's status as external replication of sign and envelope rather than a hazard-level match;
- the ABM's adverse results and withdrawal of the paradigm claim;
- the Danish counterfactual's anchor, incidence, and sign sensitivity;
- the unpriced TBA-liquidity and investor-side limitations; and
- all adverse or null findings that materially constrain interpretation.

Deletion from the journal-facing package is permitted only for:

- a repeated statement whose complete canonical statement remains elsewhere;
- prose that merely reads a table row by row;
- internal workflow or build-status narration preserved in repository records;
- obsolete narrative whose current replacement is identified; or
- an exhibit made redundant by a consolidated replacement that preserves its governing result and qualification.

No numeric claim may be changed merely to simplify exposition. No hedge may be weakened through compression. No negative result may be removed because it complicates the story.

## Editing and Verification Method

The current canonical sources remain `paper/final/paper_final_v1.tex` and `paper/final/paper_final_v1_long_abstract.tex`. Their bodies must remain synchronized except for the approved abstract difference. The current built PDFs remain preserved as the pre-redesign reference artifacts.

Work will proceed in bounded section batches:

1. inventory unique claims, labels, citations, tables, and figures in the source span;
2. record each block's main-text, appendix, repository-record, duplicate, or obsolete disposition;
3. add or update preservation checks before changing the span;
4. relocate technical material before removing duplicate prose;
5. rewrite the main-text span to its argument and page budget;
6. run the relevant tests, liveness gates, reference validation, and builds;
7. visually inspect every changed page and exhibit; and
8. record the final destination of relocated material.

Edits will use anchored, count-checked changes rather than broad sentence-level regular-expression rewrites. Existing liveness gates are evidence constraints, not permanent wording constraints; a gate may be re-scoped only when its protected claim survives in an approved destination and the change is documented.

## Acceptance Criteria

The redesign is complete only when:

- the conference title remains unchanged;
- the abstract and introduction define the paper's MBS-specific use of "quantitative-tightening shortfall";
- the manuscript consistently distinguishes the cap-relative shortfall, expectations-relative shortfall, and lock-in marginal;
- the lock-in marginal is the main estimand and is labeled model-based rather than newly causally identified;
- the production and additive functional forms appear in the main paper with their distinct implications;
- the ABM and Danish exercises occupy supporting rather than coequal roles;
- the main paper is approximately 35--45 pages including references, or a justified overage is documented;
- every removed substantive block has a recorded destination or a documented duplication or obsolescence reason;
- all protected content survives in the main paper or online appendix;
- all numerical claims remain traceable to committed artifacts;
- the canonical and long-abstract bodies remain synchronized apart from the approved abstract difference;
- there are no unresolved references or citations;
- the complete test suite and applicable liveness gates pass after any documented re-scoping;
- the main paper and online appendix build freshly;
- the render gate reports no off-page or clipped material; and
- the title page, abstract, every section opening, every changed exhibit, references transition, and appendix boundary pass visual inspection.

The final handoff will report exact page and word counts, relocated-versus-deleted quantities, verification results, changed claims, and remaining authorial decisions. It will distinguish fresh validation from assumptions or checks that remain unavailable.
