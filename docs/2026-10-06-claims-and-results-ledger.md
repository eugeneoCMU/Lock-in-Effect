# Claims and results ledger for the short lock-in paper

Source of record: `paper/final/paper_final_v1.tex`, which inputs `journal_main_v2.tex`. This ledger is an editorial control, not an additional empirical result. Every percentage point below uses the $764.748253 billion June 2022–November 2025 cap-relative gap as its denominator unless another denominator is named.

| Object | Display | Status and denominator | Source / required wording |
|---|---:|---|---|
| Cap-relative agency-MBS runoff gap | $764.7B in prose; $764.748B in tables | Observed accounting construction: announced phased caps less realized runoff. Not a no-lock-in counterfactual. | `hazard/data/expectation_benchmark_results.json` (`cap_benchmark_b`) and main §III.A. |
| Expectations-relative gap | $87.8B | Published May 2022 NY Fed projection allocated within years minus realized runoff. Allocation- and projected-rate-path-dependent; may already contain lock-in. Not a causal surprise estimate. | `hazard/data/expectation_benchmark_results.json` (`e_benchmark_b`) and main §III.B. |
| Headline paired marginal | +5.6 pp / $42.6B | Response-on minus response-off under the off-window 4.991% floor, hard-maximum form, imported 6.5% quarterly moving response, and 100% voluntary-prepayment mapping. Interior anchor, not a directly observed or uniquely preferred effect. | `hazard/data/joint_soma_pair_results.json` (`baseline_pair.marginal_pp`, `marginal_b`) and main §§IV–V. |
| Response-off / response-on levels | 85.7% / 91.3% | Model shares of the cap gap on the shared accounting basis. The level fit is calibrated and has no aggregate outcome holdout. The difference, not 91.3%, is the paired marginal. | Main §V.A and §IV.F. |
| Floor-read sampling interval | +1.9 to +9.1 pp | Conditional floor-read uncertainty at the central imported elasticity and maximum form. It does not include moving-share, form, elasticity-estimation, or population-transport uncertainty. | Main Table 1 and §V.C; detailed inference in Online Appendix. |
| Economic sensitivity | +2.1 to +13.2 pp joint floor–elasticity box; about +11.2 pp additive form; 0/+1.8/+3.4/+5.6 pp at assumed 0/25/50/100% moving shares | Different assumption comparisons, not one statistical interval. The moving share is unestimated; zero share gives zero marginal by definition. The 25% case is not an estimated lower bound. Positive signs at assumed positive shares are a model check, not independent identification from runoff. | Main §§IV.D–E and V.B–C. |
| Conventional 2017–2021 book share | 51.0% of SOMA face | Joint agency-by-vintage coverage calculation. Freddie is the primary loan sample; Fannie is a separate replication. This is not the share sampled with known inclusion probabilities. | Main §III.C and Table 2. |
| June 2022 supported UMBS 30-year cells | 47.5876% of total SOMA MBS face | Twelve listed coupon-by-vintage cells under an assumed 80 bp note-to-pass-through conversion. Different book/date/cell definition from the 51.0% figure. Neither run estimates the dollar contribution of this 47.6% slice: each scales its supported pool to total holdings. | `hazard/data/joint_soma_pair_results.json`, `hazard/data/soma_fresh_pair_results.json`, main §III.C. |
| Saved-sample joint-cell run | +4.7759 pp / $36.5234B | Saved Freddie sample, reweighted to the twelve supported cells; conditional whole-pool sensitivity. | `hazard/data/joint_soma_pair_results.json` (`joint_pair`). |
| Fresh-survivor joint-cell run | +5.5150 pp / $42.1761B | New seed-42 draw of 75,000 unique May 2022 Freddie survivors from 6,261,485 eligible 30-year loans, weighted to the same supported cells; conditional whole-pool sensitivity. | `hazard/data/soma_fresh_pair_results.json`, `hazard/data/soma_fresh_umbs30_sample_report.json`. |

## Submission wording decisions

1. Do not attribute the saved-versus-fresh difference to sampling noise alone: the sampling frame and draw both changed. A design decomposition or repeated matched-frame draws would be needed to isolate either source.
2. Do not say Fannie validates the causal sign: the Fannie run uses the same imported response. It checks conventional-agency transfer of the calculation.
3. Do not call the turnover floor strictly involuntary. It is read from total deep-discount turnover and can include voluntary behavior and housing-activity changes.
4. Do not present the floor-read sampling interval as total uncertainty. Display economic specification and population sensitivities at least as prominently.
5. Do not claim a full-SOMA representative estimate. Ginnie, excluded vintages, and 15-year behavioral hazards require separate mapping assumptions.

## New evidence required to narrow the result

- **Moving share:** termination reasons or a defensible loan-to-property-sale linkage. Freddie Mac's [dataset FAQ](https://www.freddiemac.com/fmac-resources/research/pdf/faq.pdf) defines zero-balance code 01 as "Prepaid or Matured (Voluntary Payoff)" and does not split that code into sale and refinancing. The current payoff flags therefore cannot estimate the 25/50/100% mapping; those values remain assumptions.
- **Floor transport and housing supply:** linked local inventory, listings, or transactions with a defined loan risk set and comparison design. The current 2018 floor is a calibration, not a lock-in-free control group.
- **Full-book estimate:** comparable loan-level coverage across agency, vintage, and term, plus a collateral mapping that identifies the relevant SOMA cells. The existing supported UMBS cell runs cannot supply it.

Until these inputs exist, the paper's defensible claim is a conditional portfolio translation and sensitivity range, with $42.6B as one disclosed anchor.
