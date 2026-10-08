# Paper-improvement verification and plan disposition — October 8, 20 26

Execution root: `/Users/eugene/.codex/worktrees/f586/Lock-in-Effect`.
Local branch: `codex/paper-improvement-20 26-10-08`.

## Version reconciliation and preservation

The saved project is based on f3b4cff and has uncommitted October 5 manuscripts plus a 143-page PDF. The 6930 worktree contains the newer short manuscript and fresh Freddie artifacts. The c470 working tree contains a subsequently completed October 7 economics-review revision, verified October 8, whose combined PDF is 29 pages. This was newer than the earlier memory note describing c470 as incomplete.

This task chose the **exact dirty c470 state** as its editing base and imported 1,473 relevant source/input/check files into the isolated f586 branch. It preserved the saved project's exact plan, TeX, bibliography, figures, PDF and research artifacts, plus the relevant 6930 and c470 sources. Three dated self-contained archives and a SHA-256 inventory preserve 1,269 files: 557 saved-project,269 newer-draft,443 editing-base files. Original link-preserving archives also remain. Rehashing every source and every self-contained archive member found **zero changes or mismatches**. The twenty survivor snapshots stay in6930; the read-only evidence audit independently rechecked all twenty hashes and sample membership.

The saved project and other worktrees were never reset, cleaned, overwritten, or merged. Local archive paths and hashes are versioned in `docs/20 26-10-08-preservation-manifest.json`. Large/loan-grain inputs remain local and are not in the editable delivery ZIP.

## Current deliverables

- `output/pdf/lock-in-paper-improved-20 26-10-08.pdf`: **32 pages combined**.
- `output/pdf/lock-in-paper-improved-20 26-10-08-main.pdf`: **21 pages**: title/abstract p.1, narrative pp.2–19, references pp.20–21.
- `output/pdf/lock-in-paper-improved-20 26-10-08-online-appendix.pdf`: **11 pages**, preserving printed pp.22–32.
- `output/pdf/lock-in-paper-improved-20 26-10-08-long-abstract.pdf`: long-abstract edition with identical body page text.
- `output/packages/lock-in-paper-improved-20 26-10-08-sources.zip`: editable manuscript, figures, bibliography, aggregate numerical artifacts, calculation/check code, specifications, claim/evidence/review reports and preservation inventory.
- Current source wrapper: `paper/final/paper_final_v1.tex`; body `journal_main_v2.tex`; appendix `review_appendix.tex`; new evidence and floor-support tables are separate editable TeX files.
- Controlling ledger: `docs/20 26-10-08-paper-improvement-claims.md`; evidence decisions: `docs/20 26-10-08-paper-improvement-evidence.md`.

The main narrative remains shorter than the plan's approximate 25–35-page editorial target because the newer base had already removed repetition. It retains 12pt text, one-inch margins, double-spaced main prose and every restored material qualification. No padding or smaller type was used to meet a count.

## Changes completed in this task

1. Carried forward the verified shorter manuscript and its material accounting/validation/composition work; preserved the 143-page saved edition and 83-page reviewed edition.
2. Added an early compact display distinguishing observed accounting, projected/allocated benchmarks, conditional marginal, assumed scenarios, floor-measurement uncertainty, support and adverse prediction.
3. Restored the meaning and common assumed curtailment adjustment behind 85.7%/91.3%; qualified the Ginnie zero-marginal overlay and 15-year extension; moved the historical 4%-floor group-ablation figure to the appendix.
4. Added the observed/imputed age-support table and the missing mature-age limitation:83.9874% target weight is imputed. Distinguished the existing exact +3.6713-point age-adjusted pair from its older interpolated +3.8 reading.
5. Reconciled source dates: 51.0% broad agency-vintage scope is July 15,20 26;47.6% strict joint-cell support is June 29,2022. The same broad definition at June 2022 is 57.6%, bounded above at 58.5% for omitted cells. No simulations were changed by this accounting clarification.
6. Audited primary sources, independently retrieved the NY Fed workbook, clarified the selected mobility-calibration band, added Freddie payoff-code documentation, and updated Batzer et al. to its20 26 journal publication while preserving historical versions.
7. Applied the independent reader's substantive correction: the monthly rescaled reported-flow marginal is not automatically an additional retained-principal stock. Reserved the conserved-stock interpretation for the closed book; made the central results caption state horizon, denominator and subtraction order.

## Empirical results and gates

The compact-input accounting, validation and 60/80/100bp bridge calculations were actually rerun here. **Every numerical field exactly matches** the imported result dictionaries. One bridge JSON's serialization hash changed while its complete parsed content remained identical; the publication ledger was regenerated from the current bytes. No new identification or empirical estimate is claimed.

- Named anchor: **$42.608394B / +5.571558 points**, conditional on full moving share,100 PSA,4.991% floor, hard maximum, saved sample and monthly observed-holdings reporting.
- Once-scaled closed book: **$37.002395B / +4.838507 points**,13.1570% smaller; excludes later purchases/reinvestment pools and recovery cash.
- Moving share remains unmeasured;25/50/100% assumed shares give+1.821174/+3.361516/+5.571558 points.
- The fully age/depth/activity-matched floor gate remains unmet. Mature20 18 support is absent; imputation is disclosed rather than treated as observed.
- Full-SOMA loan/collateral coverage and actual slice-level dollar attribution remain unmet. The verified fresh sample is 75,000 loans from 6,261,485 eligible survivors; supported cells are conditionally scaled to total holdings.
- Validation remains retrospective and adverse: response on predicts $161.784B against $131.303B observed; weighted monthly-rate RMSE 0.1339pp exceeds the simple comparator's 0.0868pp. It conditions on realized exposures/rates and scores voluntary principal, not a complete forward balance path.

Tasks 1, 2, 4 and 5 are completed. Task 3 is completed **as the plan's evidence-gate audit and available-data reproduction**, with the above identification/data requirements explicitly unmet or partial. It is not reported as successful estimation of the missing empirical inputs.

## Verification evidence

All current logs are under `output/paper-improvement/20 26-10-08/`.

| Check | Current result |
|---|---|
| Imported-base suite |1,208 passed,27 warnings; no failures or skips |
| Final full suite after reader changes |**1,208 passed,0 skipped,26 warnings**,19.66s |
| TeX/bibliography validators |Both editions CLEAN |
| Semantic cross-reference audit |Both editions 42 labels, 30 references, 0 errors |
| Liveness and active-publication checks |All pass; current numerical/artifact/reference checks separate from preserved historical prose gates |
| Numerical replay |Accounting, validation and bridge result dictionaries exactly equal the frozen imported dictionaries |
| New claim audit |Named values reconciled to artifacts and found in final PDF; coverage sums, curtailment levels, imputation weights and exact age pair recomputed |
| Abstract |2 20 words under existing checker |
| Standard/long builds |Both produced 32 pages; identical extracted body text |
| PDF split |Appendix starts printed p.22;21+11=32; split page text and rendered pixels exactly reconstruct combined PDF |
| Render gates |All four builds: 0 off-page origins,0 off-sheet spans,0 unresolved references; no blank pages |
| Visual inspection |All 32 pages inspected; opening, changed evidence/coverage/results/support tables, figures, references and appendix boundary checked at readable size |
| Original preservation |1,269 source files unchanged; all resolved-archive member hashes match |
| Fresh-sample audit |All 20 source hashes, recorded code/output hashes, universe uniqueness, sample uniqueness/membership, survivor date/term/balance checked by separate evidence audit |
| Independent reader |Correctly recovered estimand; three disclosed scientific weaknesses; one stock-interpretation correction and one caption clarification applied |

Warnings are not hidden. The 26 pytest warnings include existing library/Python 3.9 deprecations, synthetic-test perfect-separation warnings and GLM ridge-optimization warnings in the bootstrap smoke test. They do not include a failed assertion, but the test run is not warning-free. Tectonic 0.15 reports an internal bibliography change-detection warning and stops after six passes. Citations/references resolve, both body editions agree, and no final overfull/underfull boxes are reported. The package rebuild check below separately tests output stability.

## Decisions and boundaries

- Used the completed c470 working state instead of regressing to an older checkout; a separate qualification audit caught and restored four important omissions.
- Kept the main paper below the approximate page target rather than add repetition.
- Used document/numerical/render checks for editorial work; no prose-pinning tests or new simulation behavior were introduced. Existing substantive tests are retained.
- Preserved 51.0% with its correct late snapshot date rather than silently calling it opening-book coverage.
- No remote push, merge, submission, publication, data purchase, or third-party contact occurred. Stronger causal/population/forward-validation claims still require data unavailable to this task.

## Editable-package reconstruction

The 526-file source package was extracted to a separate local directory. Its standard manuscript built using only the packaged source, bibliography and figures. All 32 rebuilt pages match the delivered PDF in **extracted text and rendered pixels**, and the bibliography bytes match. ZIP CRC and every manifest member SHA-256 passed. After adding this verification note and the reconstruction report, the final ZIP inventory was rehashed; no publication source or figure changed. The package is a verified publication rebuild, not a claim that omitted licensed loan-level inputs or unresolved empirical evidence are included.
