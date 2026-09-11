# Manuscript Compression Design

## Objective

Restructure *Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall* from the current 147-page combined build into a publication-facing package of approximately 50--55 pages without discarding the research record.

The target package is:

- a 38--42 page main paper, including references;
- a 12--15 page online appendix containing material a referee is likely to consult; and
- a separate technical and replication supplement of unrestricted length containing the complete audit trail, detailed specifications, diagnostic grids, and development records.

The page target is a design objective rather than permission to remove a unique qualification, change an estimand, or suppress an adverse result. If preserving a necessary disclosure puts the submitted package modestly above 50 pages, correctness takes priority over the exact page count.

## Editorial Principle

Keep the research; shorten the argument.

The main paper will answer four questions:

1. What was the Federal Reserve's cap-relative agency-MBS runoff shortfall?
2. How much of that shortfall does the preferred loan-level hazard framework attribute to the mortgage-rate response relative to a rate-insensitive null?
3. Which assumptions and uncertainty ranges materially govern that decomposition?
4. What does the result imply for runoff-cap design and the Danish market-value-repurchase alternative?

Material remains in the main paper only when it is needed to understand or evaluate an answer to one of those questions. Material needed to audit those answers goes to the online appendix. Material needed to reproduce the entire research process goes to the technical and replication supplement.

## Document Architecture

### Main paper

The main paper will use the hazard framework as the primary estimator. It will have the following approximate page budget:

| Section | Target |
|---|---:|
| Introduction | 3 pages |
| Institutional setting and related literature | 3 pages |
| Data, benchmark, and empirical design | 5 pages |
| Main hazard results and identification | 10--12 pages |
| Decisive robustness and validation | 4--5 pages |
| Policy counterfactual | 4--5 pages |
| Discussion and limitations | 3 pages |
| Conclusion | 1 page |
| References | 4--5 pages |
| Total | 38--42 pages |

The ABM will no longer be presented as a coequal estimator. It will become a compact cross-design robustness subsection. The main paper will retain its result, the real-covariate threshold crossing, the withdrawn paradigm interpretation, the path-fit failure, and the reason no ABM differential is reported.

The robustness section will retain only checks that can change the paper's interpretation: turnover-floor sensitivity, functional-form sensitivity, sample-to-book composition, the Fannie reproduction, the ABM cross-design comparison, and the two Danish anchors. These will be consolidated into a small number of exhibits rather than narrated run by run.

### Online appendix

The online appendix will contain approximately 12--15 pages of material that a referee may reasonably need while assessing the paper:

- benchmark and accounting construction;
- hazard specification and parameterization;
- preferred inference procedure and binding interval;
- essential floor and functional-form sensitivity;
- concise ABM specification and cross-design results;
- essential policy-counterfactual derivations; and
- compact additional-result tables cited directly by the main paper.

No appendix section will remain solely because it exists in the current manuscript. Each retained appendix section must support a specific main-text statement.

### Technical and replication supplement

The supplement will preserve material removed from the submitted article, including:

- full ABM decision rules, population construction, parameter provenance, frictions, and extensions;
- run identifiers, manifests, and run indexes;
- complete inference ladders and alternative clustering implementations;
- full floor, transform, depth, settlement, seasonal, and composition grids;
- timing, Theil, episode-gradient, age-band, and contamination diagnostics;
- fifteen-year and weighted-average-life implementation details;
- superseded-result ledgers and specification-adjudication records;
- development and validation history; and
- replication instructions and supporting tables.

Relocation must preserve the original content unless an item is demonstrably duplicated or obsolete. Historical material must remain labeled as historical or superseded.

## Content-Preservation Rules

The following content is protected and must survive in the main paper or online appendix:

- the cap-relative and expectations-based benchmark definitions;
- the preferred hazard estimand and its rate-insensitive null;
- the current headline values and binding uncertainty construction;
- the meaning, provenance, and sensitivity of the turnover floor;
- the distinction between level recovery and the lock-in marginal;
- every unique transport assumption;
- every unique identification limitation;
- the fact that the decomposition is model-based rather than a clean causal estimate;
- the sample-to-book and accounting-basis qualifications;
- the Fannie exercise's status as a robustness check rather than an outside test;
- the ABM's adverse results and the withdrawal of the paradigm claim;
- both Danish anchors and the resulting sign sensitivity;
- the unpriced TBA-liquidity and investor-side limitations; and
- all adverse or null findings that materially constrain interpretation.

Deletion is permitted only for:

- a repeated statement whose complete canonical statement remains elsewhere;
- prose that merely reads a table row by row;
- internal workflow or build-status narration that is preserved in the supplement or repository records;
- obsolete narrative whose current replacement is clearly identified; or
- an exhibit made redundant by a consolidated replacement that preserves its governing result and qualification.

No numeric claim may be changed merely to simplify exposition. No hedge may be weakened through compression. No negative result may be removed because it complicates the story.

## Editing Method

The current canonical files remain `paper/final/paper_final_v1.tex` and `paper/final/paper_final_v1_long_abstract.tex`. Their bodies must remain synchronized; the long-abstract variant retains its distinct abstract.

Work proceeds in bounded section batches:

1. inventory unique claims, pins, labels, citations, tables, and figures in the source span;
2. write a preservation test or explicit claim ledger before changing the span;
3. relocate technical material before deleting duplicate prose;
4. rewrite the main-text span to its page and argument budget;
5. run the relevant tests, liveness gates, reference validation, and build checks;
6. visually inspect changed pages; and
7. record the destination of relocated material.

The revision will not use broad regular-expression sentence surgery. Replacements must be anchored and count-checked. Existing liveness gates are evidence constraints, not wording requirements; a gate may be re-scoped only when the protected claim remains present in its appropriate destination and the change is documented.

## Exhibit Strategy

The shortened main paper should rely on a small exhibit spine:

1. benchmark and headline decomposition;
2. observed, central, and null runoff paths;
3. preferred uncertainty interval and the few interpretation-changing alternatives;
4. consolidated robustness results; and
5. policy-counterfactual results under both anchors.

Additional tables and figures move to the online appendix or supplement. Main-text prose will state the preferred result, the comparison that changes interpretation, and the governing qualification rather than repeat every cell.

## Verification and Acceptance Criteria

The revision is complete only when all of the following hold:

- the canonical and long-abstract bodies are synchronized;
- the main paper builds to approximately 38--42 pages including references, or any justified overage is documented;
- the online appendix builds to approximately 12--15 pages, or any justified overage is documented;
- every removed substantive block has a recorded destination or a documented duplication/obsolescence reason;
- all protected content in this design survives;
- all current numerical claims remain traceable to their committed artifacts;
- there are no unresolved references or citations;
- the complete test suite and liveness gates pass after any necessary documented re-scoping;
- the render gate reports no off-page material;
- the main paper, online appendix, and supplement are freshly built; and
- representative pages, all changed tables, section transitions, and split boundaries pass visual inspection.

The final handoff will report exact page counts, word counts, deleted-versus-relocated quantities, verification results, and any remaining editorial decisions rather than describing the target as achieved without measurements.
