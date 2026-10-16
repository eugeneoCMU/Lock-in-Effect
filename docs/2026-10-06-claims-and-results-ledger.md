# Claims and results ledger — economics-review revision

Updated October 8, 2026 for the October 7 revision. Active source: `paper/final/paper_final_v1.tex`, shared body `journal_main_v2.tex`, and `review_appendix.tex`. The long-abstract edition has the identical body. This ledger supersedes the October 6 interpretation; the dated baseline preserves that earlier version.

All benchmark percentage points use **$764.7482532227002 billion**, the June 2022–November 2025 difference between announced caps and realized net face decline. A positive paired marginal is **response-off principal minus response-on principal** (equivalently, response-on retained principal minus response-off retained principal). The smaller expectations-relative gap never replaces the denominator. Dollars below are billions unless stated otherwise.

## Accounting and projected benchmarks

| Object | Precise value | Evidence class and interpretation | Current source |
|---|---:|---|---|
| Announced caps less realized net face decline | 1417.5 − 652.7517467773 = 764.7482532227 | Observed accounting construction; not a no-lock-in counterfactual. Net face changes include settlement effects. | Main II.A, equation (1); `expectation_benchmark_results.json` |
| Uniform allocation of May 2022 projection | Projected 740.5833333333; gap 87.8315865560; anticipated share 88.5149673522% | Published year-end projection plus assumed within-year allocation. Not a causal surprise. | Main II.B, Table 1; `expectation_benchmark_results.json` |
| Settlement-aware allocation | Projected 839.5299198738; gap 186.7781730965; anticipated share 75.5765152376% | Disclosed allocation incorporating the realized early-2022 holdings-rise proxy; not an untouched forecast. | Main II.B, Table 1; `expectation_spread_variants_results.json` |
| Original projection levels, YE2021–2025 | 2615.5, 2599.6, 2319.9, 2072.8, 1849.7 | NY Fed *Open Market Operations During 2021*, published May 2022, Chart 34 (printed p.49/PDF p.51); workbook sheet Chart 34, column D. Independently retrieved and matched. | `output/review-revision/2026-10-07-sources/workbook-provenance.json` |
| Phase-in MBS purchases | 32.8 | Actual June–August 2022 purchase-period total reported by NY Fed; purchases stopped in September. Not estimated by the new simulation. | Main II.A; NY Fed 2022 annual operations report, printed p.15 |

## Separate assumption comparisons

Unless varied: saved Freddie sample, 4.991% annual turnover floor, 100 PSA, full moving share, maximum form, observed-holdings monthly reporting. The moving share is **unestimated**. No row is selected as empirically preferred. These are separate comparisons, not a joint range or probability distribution.

| Changed assumption | Marginal dollars | Points of cap gap | Artifact and key |
|---|---:|---:|---|
| Moving share 0% | 0 | 0 | Definitional response-off equality |
| Moving share 25% | 13.9273992859 | 1.8211743835 | `moving_share_bracket_offwindow_results.json`, cells.0.25 |
| Moving share 50% | 25.7071312625 | 3.3615155254 | Same, cells.0.5 |
| Moving share 100% | 42.6083938811 | 5.5715581829 | Same, cells.1 |
| 75 PSA | 6.5465168466 | 0.8560355410 | `psa_level_sweep_results.json`, cells.4.991\|75\|6.5 |
| 100 PSA | 42.6083938811 | 5.5715581829 | Same, cells.4.991\|100\|6.5 |
| 125 PSA | 87.3270905528 | 11.4190637487 | Same, cells.4.991\|125\|6.5 |
| 150 PSA | 119.5032976901 | 15.6264884799 | Same, cells.4.991\|150\|6.5 |
| Survival combination | 85.7054978991 | 11.2070210737 | `floor_form_offwindow_results.json`, additive/4.991/6.5 |

The last formula is exactly `1-(1-f_monthly)*(1-h_voluntary)`, not the arithmetic sum. PSA scales the rate-responsive baseline; the annual turnover floor is a different input. All comparisons use matched on/off pairs. Main Table 3 and Figure 2 read exact saved artifacts through the publication exhibit and sensitivity generators; their provenance records the hashes.

## Dollar reporting and supported populations

The engine evolves balances and scales the opening book once. Production then separately scales each month's reported cash principal by observed holdings divided by **closing active exposure**. The new closed-book comparison removes that reporting step, with no later purchases, reinvestment pools, curtailments, or recovery receipts. Defaults transfer principal to inactive claims. This is not a complete SOMA counterfactual.

| Population | Production marginal | Closed-book marginal | Closed marginal per $100 initial active balance |
|---|---:|---:|---:|
| Saved production sample | 42.6084 | 37.0024 | 1.3658 |
| Saved sample, joint cells | 36.5234 | 32.1965 | 1.1884 |
| Fresh survivors, 80 bp bridge | 42.1761 | 37.0584 | 1.3678 |

Main Table 4 reads `stock_flow_accounting_2026-10-07_results.json`, `saved_joint_accounting_2026-10-07_results.json`, and `coupon_bridge_2026-10-07_results.json`. The original-sample change is −5.6059989110 billion, −0.7330515483 benchmark points, or −13.1570294% of the production marginal. Closed-book off/on totals are 679.7760860401/642.7736910700. Scheduled principal is 194.9784453877/196.4794001164: common rules do not imply equal cash amounts. Active-balance identities reconcile below 10^-12 billion.

Production's cap-allowed marginal is 42.5926125949, after 0.0157812862 of response-off excess in two phase-in months. Neither closed-book leg reaches a cap, so its principal and cap-allowed differences coincide. These simulated quantities do not estimate the actual 32.8 of purchases.

The 51.0% conventional 2017–2021 agency-by-vintage coverage and the 47.5876196720% listed UMBS 30-year coupon-vintage share have different definitions. Each supported-cell run expands its pool to total holdings; its dollars are **not the actual contribution of the 47.6% slice**. The sample has no known SOMA inclusion probabilities. Saved versus fresh changes both frame and draw, so their difference is not isolated sampling noise.

| Note-to-pass-through bridge | Production marginal | Closed marginal | Positive-weight candidates / 75,000 | Minimum target-cell count |
|---|---:|---:|---:|---:|
| 60 bp | 36.9512 | 32.4568 | 69,613 | 42 |
| 80 bp | 42.1761 | 37.0584 | 75,000 | 204 |
| 100 bp | 45.3018 | 39.7529 | 74,701 | 78 |

The candidate IDs and twelve targets are fixed; buckets and weights actually change. Off-target candidates receive zero weight. All target cells remain supported and all initial target shares match within 5.6×10^-17. Both legs use the same weights. Actual note coupons remain in hazards and amortization. These bridges are diagnostics, not a calibrated plausible interval.

## Retrospective prediction and conditional inference

The validation fixes a 2023 cohort-speed baseline and evaluates January 2024–September 2025: 239 cohorts, 5,019 rows, and 37,680.2301142 billion exposure-months. Observed voluntary prepaid principal is 131.3033217948 billion. The panel lacks loan IDs and separate scheduled/default/curtailment outcomes. Predictions condition on realized opening exposure and rates; state starts before evaluation and burnout advances from predictions. Previously examined outcomes make this **retrospective**, not untouched.

| Candidate | Predicted principal | Prediction / observation | Exposure-weighted monthly rate RMSE (percentage points) |
|---|---:|---:|---:|
| 2023 cohort-speed baseline | 121.4361995126 | 0.9248524550 | 0.0867907747 |
| Response off | 172.6428556095 | 1.3148399692 | 0.1569994927 |
| Response on | 161.7841953290 | 1.2321409170 | 0.1338853909 |

The response-on candidate overpredicts by 23.2% and loses to the simple comparator. No recalibration or candidate selection follows the score. These are Freddie cohort dollars, not scaled SOMA dollars. All 6,077 evaluation rows have usable exposure/numerators; support restrictions exclude 1,058, leaving 99.994564% of usable exposure and 99.993494% of observed principal. Full-panel lag/invalid counts are separately reported. Source: `pathb_validation_2026-10-07_results.json`; main Table 5 and appendix Tables 7–8.

Loan-draw uncertainty uses 130 vintage-coupon-FICO strata, effective count 25.78, with a conditional +4.631 to +6.924 point percentile interval at the 4.991% floor. Floor inference uses 31 vintage-coupon-FICO-LTV strata, effective count 5.87; the +1.9 to +9.1 point restricted wild-cluster interval conditions on response and form. Its coverage exercise tests Gaussian/t5 cluster-shock designs, not arbitrary dependence or model misspecification. The +2.1 to +13.2 point floor/elasticity grid is an assumption sweep. None includes all moving-share, PSA, population, or reporting uncertainty.

Figure 3 is explicitly the historical **4% floor** calculation: 70.345 billion paired total, 69.620 cell sum, 0.725 interaction residual (1.03%). It is not a decomposition of 42.608 billion and has not been proportionally rescaled.

## Wording and research boundaries

- Do not call $42.6B a preferred causal estimate or the scenario comparisons a calibrated confidence band.
- Do not call the floor strictly involuntary or lock-in-free. Deep-discount turnover can contain voluntary and housing-activity effects.
- Fannie checks transfer of the calculation under the same imported response; it cannot independently identify that response. Ginnie, excluded-vintage, and 15-year extensions retain their separate assumptions.
- The new retrospective check does not validate the imported elasticity, moving share, individual forward balance dynamics, or full-SOMA transport.
- Stronger interpretation needs sale/refinance separation, broader collateral mapping and coverage, and an untouched evaluation designed before outcome access.
- The incremental policy proposal is regular side-by-side cap and cash-flow scenarios with separate interest-rate and prepayment assumptions. It is not a probabilistic forecast or a claim that the full cap gap was unanticipated.

The machine-readable exact ledger is `output/review-revision/2026-10-07-checks/publication-ledger.json`; the issue disposition and final verification report explain what changed and what remains unresolved scientifically.
