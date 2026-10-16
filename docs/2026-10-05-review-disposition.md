# Review disposition for the short manuscript

This ledger follows the numbered points in the pasted review. **Edited** means the current short-paper source changed in this pass. **Present** means the 34-page version already addressed the point. **Open** means the requested empirical result cannot be obtained by rewriting the paper and is not claimed as complete. The source of record is `paper/final/paper_final_v1.tex`, which inputs `journal_main_v2.tex`.

## Substantive argument (1–7)

1. **Present, tightened.** The introduction separates the observed cap gap, the New York Fed projection, and the paired model marginal.
2. **Edited.** The abstract and Table 1 call $+5.6$ points an interior specification anchor and place it beside wider assumption ranges.
3. **Edited; empirical share open.** Table 1 and Figure 2 show zero and 25/50/100% moving-share scenarios. Zero is definitional, and 25% is not an empirical lower bound. The share is not estimated because the ingested loan data do not distinguish sale terminations from other voluntary prepayment.
4. **Present, visualized.** Maximum versus additive turnover is a substantive result in the main text, table, and sensitivity figure.
5. **Edited.** The floor-read interval is labeled conditional measurement uncertainty; structural and population choices appear separately.
6. **Present.** The off-window floor is described as a transported calibration from 2018 cohorts, not a clean control group.
7. **Present.** Housing inventory remains an unseparated competing channel beside the floor-transport discussion.

## Data, model, and validation (8–18)

8. **Present.** Direct conventional 2017–2021 coverage is 51.0% of SOMA face; the Fannie, Ginnie, vintage, and term treatments are external extensions.
9. **Freddie support and fresh draw complete.** All 20 `orig_YYYYQn.txt` and matching `perf_YYYYQn.txt` pairs for 2017--2021 were streamed one quarter at a time from the shared Drive folder into compact May-2022 snapshots. All 40 raw Drive files were verified cloud-only and preserved after the final storage cleanup; about 28 GiB was free. The 20 snapshots contain 6,261,485 unique, positive-balance, 360-month Freddie survivors observed in May 2022. A seed-42 draw contains exactly 75,000 unique loans, with positive support in all 12 listed June 29, 2022 UMBS 30-year coupon-by-vintage target cells after the assumed 80-basis-point note-to-pass-through conversion. Those cells represent 47.6% of total SOMA MBS face. The 51.0% conventional-vintage coverage figure uses another book/date/cell calculation and is not interchangeable with this share. The Freddie draw is not a SOMA probability sample; the disclosed UMBS cells do not identify the Freddie/Fannie collateral mix or supply a full agency-by-term mapping.
10. **Saved and fresh paired sensitivities complete.** The saved-draw joint weighting moved the marginal from +5.5716 points ($42.6084B) to +4.7759 points ($36.5234B), and its 12-cell dollar attribution reconciles to the aggregate. The new May-2022 Freddie survivor draw gives +5.5150 points ($42.1761B) on the same supported cells, with the fresh response-off and response-on floor binding in 42.6% and 79.3% of the same 3,149,666 evaluated loan-months. Target balance shares match within 5.6e-17. The fresh dollar marginal reconciles to the percentage-point result using the exact $764.748253B cap gap. Both joint-cell runs scale the supported pool to all holdings; neither estimates the actual dollar contribution of the 47.6% slice or a full-SOMA causal effect. Snapshot and output hashes, code hashes, seed, input dates, and checks are recorded in `hazard/data/soma_fresh_audit.json`.
11. **Present.** The 15-year share is disclosed as a scheduled-principal/accounting extension without a separately estimated behavioral hazard.
12. **Present, simplified.** The main coverage and validation tables show the Ginnie overlay and clarify that it is not directly sampled; assumption take-up is not measured.
13. **Open as estimation; interpretation tightened.** Calibrated covariate priors remain. The paper does not promote them as identification, and their sensitivity is in the appendix. A credible re-estimation or a simpler production model requires a new run.
14. **Edited.** Burnout is a survivor-selection control, not a headline mechanism.
15. **Edited.** The main text gives the $0.39B extreme-transition materiality check and leaves matrix detail in the appendix.
16. **Edited.** The 380-basis-point extrapolation and concave-response result appear beside the model and in the sensitivity table and figure.
17. **Edited.** The main text gives the cumulative-only conclusion in one paragraph; month permutations and reporting artifacts remain in the appendix.
18. **Adopted.** No new robustness run was added for this editorial revision. The two open composition and moving-share questions are the empirical priorities.

## Scope and presentation (19–36)

19. **Edited.** The ABM receives one main-text paragraph; its comparison figure is in the appendix.
20. **Present.** Path A is an adverse check, not a coequal headline estimator.
21. **Edited.** Denmark receives one main-text paragraph; signed scenarios and transition limits are in the appendix.
22. **Partly open.** The terminology crosswalk moved to the separate replication notes, which already contain the run ledger. Engineering language remains in the inherited Online Appendix and needs a line-by-line extraction before submission.
23. **Edited.** The title names Federal Reserve MBS runoff and the model-based decomposition.
24. **Edited.** The standard abstract is shorter and centers the paired result; the long-abstract edition remains available separately.
25. **Present.** The contribution is the translation from household rate-gap response to the Fed portfolio's cash flows.
26. **Partly open.** The main paper is less defensive after the ABM/Denmark cuts; a final copy edit should remove repeated exclusions without deleting unique limitations.
27. **Edited, with appendix cleanup open.** Main-text terminology is reduced, and the internal terminology table moved to the replication notes. Older parallel systems remain in the inherited appendix.
28. **Edited in the journal main.** The zero-response path is called the response-off counterfactual rather than the statistical “null.” The historical appendix retains the old term where needed for source traceability.
29. **Partly open.** Headline prose can use $764.7B, while the exact accounting figure belongs in the benchmark construction and tables. Remaining precision needs a display-level copy edit.
30. **Present.** The cap/projection/realized-runoff benchmark figure remains central.
31. **Edited.** Figure 2 now plots the paired marginal across moving share, rate curve, Ginnie overlay, floor anchors, calibration, and form.
32. **Present.** The coupon × vintage allocation figure retains its noncausal caption.
33. **Edited.** The cross-estimator level comparison figure moved to the Online Appendix.
34. **Edited.** The uncertainty table now has measurement, calibration, and structural/population blocks.
35. **Edited.** Table 1 contains the moving-share scenarios and distinguishes observed, projected, and simulated objects.
36. **Edited.** Policy language distinguishes an operational ceiling from an achievable cash-flow forecast.

## Sources and publication package (37–40)

37. **Present.** The literature section separates household mobility, MBS prepayment, and balance-sheet normalization.
38. **Partly complete.** The ten 2025–26 bibliography entries were checked against publisher, Federal Reserve, NBER, Philadelphia Fed, SSRN, arXiv, and JOSS records on 2026-10-05, as recorded in `docs/2026-10-05-recent-citation-audit.md`; source identifiers were added where missing. The full bibliography still needs a submission-date verification.
39. **Partly open.** The main, academic appendix, and replication-notes PDFs are separate; the terminology crosswalk moved into the latter. Internal engineering history still appears in the inherited Online Appendix and should be moved without losing final economic derivations.
40. **Partly complete.** LaTeX reference and label validation and PDF unresolved-reference checks pass. A final human read is still needed for references to superseded specification names in appendix prose.

## Empirical work that the current files do not establish

- A full-SOMA representative sample and paired estimate across agencies, vintages, and terms; the fresh Freddie run is conditional on supported UMBS 30-year cells (points 9–10).
- An estimate of the sale-related share of voluntary termination, rather than an assumed $\mu$ bracket (point 3).
- A better estimate or principled removal of calibrated borrower coefficients (point 13).
- A housing-supply design that distinguishes inventory from financing lock-in (point 7).

The current editorial revision does not claim these results.

## 2026-10-06 follow-up to the professor-style review

The new `docs/2026-10-06-claims-and-results-ledger.md` records the claim hierarchy, denominator, evidence status, source artifacts, and wording rules for the short paper. The journal main text now says explicitly that the positive simulated sign is a model check under the imported response, not independent portfolio identification. Its coverage table distinguishes the 51.0% conventional agency-by-vintage face share from a probability sample and describes the Fannie result as a transport check under the same imported response. The fresh-versus-saved Freddie comparison now states that both sampling frame and draw changed; their difference does not isolate one source of variation. The uncertainty table leads with economic assumption and population sensitivities and places conditional sampling intervals last. The conclusion repeats the unestimated moving-share bracket. Headline prose rounds the cap gap to $764.7B while the exact value remains in tables and methods.

Freddie Mac's public loan-level dataset FAQ labels zero-balance code 01 "Prepaid or Matured (Voluntary Payoff)"; it does not distinguish a property sale from refinancing. The available loan files therefore cannot estimate the moving share. The housing-supply design and a full-SOMA representative sample likewise still need the external data and mapping described in the empirical rerun plan. No estimate was invented for those open questions.

The standard and long-abstract editions were synchronized apart from their abstracts, including the saved and fresh Freddie appendix tables. The full repository suite passed (1,190 tests), and the final PDF render gate passed for the 82-page standard paper (34 main, 48 Online Appendix) and 83-page long-abstract edition, with zero unresolved references or off-page text. The remaining publication judgment is editorial: whether to shorten the inherited Online Appendix further by moving internal implementation history to the separate replication notes. Its academic derivations and adverse results have been retained.

## 2026-10-06 major-revision implementation

The later evidence search and decision are recorded in `docs/2026-10-06-major-revision-evidence-decision.md`. The standard abstract, introduction, identification discussion, results, Table 1, Table 4, Figure 2, and conclusion now present the $42.6B hard-maximum, full-moving-share calculation as a conditional anchor. They include the zero scenario, state that 25% is not an empirical lower bound, and make the unestimated sale-related share and baseline-turnover form first-order limits. The long-abstract edition received the same substantive correction. The response-letter abstract count was updated to 218 words.

After these edits, the full suite passed again (1,190 tests). The rebuilt standard PDF has 83 pages (35 main, 48 Online Appendix), and the long-abstract edition has 84 pages. The render gate found zero unresolved references and zero off-page items in either edition. The abstract and revised tables were visually checked. The longer main section is a page-layout consequence of the added assumption disclosure, not new empirical identification.
