# Economics-review revision: final verification

**Completed October 8, 2026.** Edition date October 7, 2026. Execution root `/Users/eugene/.codex/worktrees/c470/Lock-in-Effect`; local branch `codex/economics-review-revision`. All nine approved tasks are complete within their stated research scope. Findings 1, 3 and 7 retain scientific limitations after the authorized analyses; the other nine findings are corrected. The separate twelve-row disposition supplies the evidence for each.

## Delivered artifacts

- `output/pdf/lock-in-effect-economics-review-revision-2026-10-07.pdf`: **29 pages** combined.
- `output/pdf/lock-in-effect-economics-review-main-2026-10-07.pdf`: **20 pages**, including title/abstract and two reference pages; main narrative ends on page 18.
- `output/pdf/lock-in-effect-economics-review-online-appendix-2026-10-07.pdf`: **9 pages**, retaining printed pages 21–29.
- `output/packages/lock-in-effect-economics-review-sources-2026-10-07.zip`: editable sources, figures, code, specifications, aggregate results, claims ledger, review disposition, verification records and preserved reviewed edition. `REVISION_README.md` explains build/replay scope. The package manifest hashes each included file.
- Both standard and long-abstract LaTeX wrappers remain editable in `paper/final/`. The long edition was built and checked; its body is identical to the standard edition.

The standard abstract is 220 words by the recorded source checker. The six-section paper retains 12pt type, one-inch margins and double-spaced main text. The main text is shorter than the approximate 20–25-page target; no padding or smaller type was used. Material assumptions, new comparisons and adverse results remain in the main paper. The appendix retains current derivations, full validation cells, support/inference detail, benchmark stress cases, WAL and adverse checks. Historical development narrative is preserved separately.

## Numerical conclusions verified

| Check | Result |
|---|---|
| Production reporting parity | Reproduced $42.60839388108877B; absolute difference from saved result 1.1369×10^-13B. |
| Closed-book accounting | $37.00239497010875B = 4.8385066346 cap-gap points; change −$5.6059989110B, −13.1570%. Both monthly active-identity errors below 10^-12B; total claims conserve principal separately from inactive default transfers. |
| Cap and cash separation | Production response-off excess $0.0157812862B in two months; cap-allowed paired difference $42.5926125949B. Closed-book paths do not bind. |
| Retrospective validation | Observed $131.3033218B; predicted $161.7841953B response on, $172.6428556B off, $121.4361995B comparator. On RMSE 0.1338854 monthly pp exceeds comparator 0.0867908. Adverse result retained. |
| Validation denominators | 6,077 usable evaluation rows, 5,019 retained in 239 cohorts over 21 months. Support retains 99.994564% of usable exposure and 99.993494% of observed principal. No evaluation lag/invalid exclusions; full-panel counts separately recorded. |
| Coupon bridge | Fixed 75,000 candidate IDs, same twelve targets, exact paired weights. Production marginals $36.9512/$42.1761/$45.3018B at 60/80/100bp. Positive-weight counts 69,613/75,000/74,701; all twelve targets supported; shares match within 5.6×10^-17. |
| Saved sensitivities | Moving-share/PSA parity passes; 75–150 PSA gives 0.8560–15.6265 points. Survival-combination row uses exact probability formula. Figure values read precise artifacts, with saved provenance. |
| Projection source | Original NY Fed workbook independently retrieved; Chart 34 column D matches all five year-end MBS levels. Uniform and settlement-aware allocation calculations reconcile. |

The accounting comparison uses two common underlying on/off loan walks and reports each under both conventions, yielding the requested four paths without duplicating identical state evolution. It does not mutate the production engine. Default cash, curtailment, additions and reinvestment-pool receipts are explicitly zero in the scoped closed book. It is not a full-book counterfactual.

Validation is a cohort-level approximation conditional on realized exposure and rates, with a pre-evaluation comparator and prediction-only burnout recursion. Outcomes had already been examined in earlier diagnostics. The design was fixed for this task before scoring; no external preregistration, untouched sample, loan-ID independence, causal identification or successful independent model validation is claimed. The compact panel cannot support separate realized scheduled/default/curtailment validation.

## Software and publication checks

All command outputs are preserved under `output/review-revision/2026-10-07-checks/`.

| Verification | Final outcome | Evidence |
|---|---|---|
| Baseline repository suite | 1,186 passed, 1 skipped, 27 warnings. Skip was absence of a built PDF. | `baseline-tests.log` |
| Final full repository suite | **1,208 passed, 0 skipped, 26 warnings**, 10.08 seconds. | `integrated-tests.log` |
| Current numerical/artifact/reference tests | Included in final suite; reviewer independently ran 18 targeted tests successfully. | `tests/test_stock_flow_accounting.py`, `test_pathb_cohort_validation.py`, `test_coupon_bridge_sensitivity.py`, `test_revision_artifacts.py`, `test_manuscript_references.py` |
| LaTeX validation | Both editions clean: parse, nesting, citations, labels, math delimiters, table columns. | `tex-validation-standard.log`, `tex-validation-long.log` |
| Semantic references | Both editions: 40 labels, 26 references, no errors. | `semantic-references.log` |
| Claim checks | All historical gates and distinct active-publication checks pass. | `liveness.log` |
| Tectonic builds | Both editions produced 29-page PDFs. | `build-standard.log`, `build-long.log` |
| Render checks | Combined, main, appendix and long edition: zero off-page origins, zero spans past sheet, zero unresolved references. | `render-gate.log` |
| Split reconstruction | Detected appendix banner on page 21. Split page text **and rendered pixels** exactly match the 29-page combined PDF. | `pdf-package-check.json` |
| Edition consistency | Standard and long edition have identical body source and identical extracted text on every body page. | Current source test and `pdf-package-check.json` |
| Visual QA | All pages inspected for layout; changed tables, figures, equations, bibliography, selected reference destinations and appendix transition checked at readable resolution. No blank pages or visible clipping/overlap. | Rendered pages retained locally; package check reports no blank pages. |

Selected compiled destinations: imported coefficient **equation (2), p.8**; voluntary hazard **equation (4), p.8**; default hazard **equation (8), p.21**; current validation **Table 5, p.15**; code/timing map **Table 6, p.22**; WAL **Table 12, p.28**. These were checked against the actual equations/exhibits, not merely a successful reference resolution.

### Warning and failure disposition

- The first integrated run exposed two archived specification-count failures: the preserved edition said 27 while the live folder now has 30. The test now reads a hash-verified original 27-file inventory. The reviewed prose was not altered and the three new dated specifications are not reclassified as part of the earlier freeze.
- Legacy wording gates now explicitly read the byte-preserved reviewed source. Their assertions remain; three stale historical gate literals were reconciled to that actual archived edition. Current-paper checks independently validate expanded active sources, exact result values/hashes, specification qualifiers, edition agreement and reference semantics. This is a scope separation, not a claim that old prose gates certify the revised manuscript.
- The final pytest warnings concern existing Python/library deprecations and Python 3.9 support, rather than failing research assertions. The baseline had the same warning families.
- Tectonic 0.15.0 reports an internal bibliography change-detection warning and stops after six passes. Both bibliographies are byte-identical across successive final builds; both editions have resolved citations, identical body text and clean render checks. BibTeX reports no bibliography errors. Final builds have no overfull or underfull box warnings. This backend warning is disclosed rather than described as a warning-free build.

## Preservation and source provenance

The baseline source revision is `4a4aaceb361a8fc57e7bb83b417f1265aac4e47d`, including its dirty source state. The task imported and hash-verified 676 relevant files (35.7MB) into the isolated execution worktree. It did not copy or alter the twenty survivor snapshots and did not process raw cloud data.

The final preservation check rehashed **all 676 authoritative files and all twenty snapshots: zero changes**. All seven archived manuscript/reference/manifest files match their original hashes. The original 83-page PDF remains byte-identical, SHA-256 `03211f9440c26a9859c04db105e3c5f1e59b57cc8e1b40a0cc3b0afd8c098f92`. Evidence: `preservation-check.json` and the baseline `source-manifest.json`.

The fresh-sample audit's 33 recorded source/code/output hashes were verified. New analyses use a frozen public macro extract and the saved compact local inputs, with input hashes in their results. The original NY Fed workbook and URL/hash/retrieval/source-cell provenance are saved under `2026-10-07-sources/`. No credentials, raw loan files, loan-grain samples, compact small-cell panels, or row-level validation scores are included in the delivered source ZIP.

## Scoped independent review

A read-only reviewer checked new code, monthly accounting rows, validation calculations, bridge support/weights, current scientific wording and semantic references. It found **no critical or important issue within that scope**. The minor missing validation-coverage diagnostics and optional positive-weight-count disclosure were both added; the candidate scores and existing bridge weight hashes did not change.

The reviewer did not certify raw ingestion, payoff-event classification, source licensing, historical pre-score chronology, final page layout, or the empirical validity of the imported elasticity. Final layout/package checks were completed separately in the parent task. No external peer review or independent causal validation is implied.

## Editable-package reconstruction

The source ZIP was extracted to a separate local directory, and its standard manuscript rebuilt there using only packaged sources, figures and bibliography. The rebuilt PDF has 29 pages; **every page's extracted text and rendered pixels match the delivered PDF**. Active-publication checks also pass in the extracted copy. All ZIP member hashes and the archive CRC check pass. Loan-level inputs were not required to rebuild the publication. Evidence: `package-build-check.json`, `package-build-smoke.log`, the ZIP's `package-manifest.json`, and the local `package-verification.json`.

## Remaining research limitations and local status

The unestimated moving share, total-turnover floor transport, limited collateral mapping, hypothetical accounting conventions and lack of untouched validation remain substantive limitations. Software and publication checks do not resolve them. The final paper states the contribution as an assumption-sensitive accounting decomposition and conditional portfolio translation.

The original worktree and all source/cloud data are preserved. The revision and artifacts remain local in the isolated branch/worktree; no remote publication, merge or submission was performed.
