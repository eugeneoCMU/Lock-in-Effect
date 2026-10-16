# Corrected seasoning support and structural envelopes, 14 October 2026

This supplement uses accepted corrected Freddie outputs from `output/research-rerun/2026-10-14-archive`. It adds a fixed descriptive support grid and summarizes an already accepted scenario matrix. Existing primary 2018 measurement inference and accepted simulations are unchanged. The final Task4 attempt is `output/research-next/2026-10-14/support/attempt-002`; attempt-001 remains as an earlier immutable calculation with less detailed calendar/support status reporting.

## Population and exposure conventions

The panel covers the corrected known360FRM source population with original vintages 2017–2021. Its count-weighted cohort mean age is an observed aggregate of finite age observations, not the age of every borrower in a selected cohort. Missing mean ages are excluded; no vintage-based age imputation is used. The 100 grid cells cross years 2018, 2019, 2023, 2024 and 2025; mean ages at least 12, 24, 36 and 60 months; and note-minus-market gaps no greater than 0, −25, −50, −100 and −200 basis points. The 2025 window ends September. Thresholds are nested, so the cells are not independent populations.

Each cell reports supported cohort-month rows, distinct strata and months, expected and missing calendar months, sum of cohort-month loan counts, and exposure/payoff dollars. Loan-count months are repeated monthly exposures, not distinct individuals. Positive end-of-month exposure and positive adjacent-opening exposure have separate support statuses and can retain different rows.

The end-exposure monthly ratio is the sum of full payoff dollars divided by the sum of positive same-row end-of-month exposure. This reproduces the inherited measured-speed convention. It excludes zero-end-exposure rows and reports their excluded payoff dollars separately. The adjacent-opening monthly ratio instead divides source adjacent-opening dollars into matched adjacent payoff dollars: `prepaid_upb − first_observed_payoff_upb − gap_payoff_upb`. It excludes zero-adjacent-exposure rows. Source first-observed and calendar-gap opening dollars, payoff dollars and payoff counts are reported explicitly. This adjacent exposure is source loan-history bookkeeping, not a lag of the aggregate cohort balance. Adjacent-only loan counts are unavailable; its reported loan-count months still sum the selected cohort-month total loan counts and are labeled accordingly.

For monthly ratios in [0,1], annualized CPR is `100 × [1 − (1 − monthly_ratio)^12]`. Annualization is a transformation of an aggregate measured ratio, not an estimated loan-level survival distribution. Nonphysical end-exposure ratios are flagged and have no CPR value. Neither convention separates sale from refinance or identifies an involuntary floor.

All rates are the frozen weekly within-month means from the mortgage-rate CSV recorded in the accepted floor-calibration input manifest. Complete required months are checked through September 2025; no rate is fetched or interpolated.

## Observed support and designated mature diagnostic

The fixed grid contains 71 cells with positive end-exposure support and 29 empty cells. The 2018 age≥12/gap≤−25bp cell has 96 rows, 24 strata and seven months; its end-exposure annualized payoff speed is 4.688125%, compared with 4.660240% for the adjacent-opening convention. All 2018 cells requiring age≥24 are empty. These facts concern observed cohort means in this source vintage population; they do not establish individual seasoning effects.

The designated 2019 age≥24/gap≤−25bp diagnostic has 32 rows, nine strata, eight months and 3,154 loan-count months. End exposure totals $831,410,552.05 and full payoff dollars $5,865,231.78. The end monthly ratio is 0.007054555376448091, annualized to 8.14460847651749%. Adjacent opening exposure totals $801,775,049.04, with the same payoff numerator in this particular cell because first/gap payoff dollars are zero. Its monthly ratio is 0.007315308435979263, annualized to 8.43365167543%.

The prespecified inference guard requires at least ten strata and six months. Nine strata fail that guard. The mature diagnostic therefore reports `insufficient_support`, and both the stratum and month inference fields are null. No mature confidence interval is produced. The code is verified on a separate supported synthetic fixture to call the existing `post_rerun_diagnostics.infer_floor` implementation for both cluster layers with the same matched positive-end-exposure observations; that fixture is a software check, not empirical evidence.

Later-year support is broader: the age≥24/gap≤−25bp cells contain 2,561 rows/257 strata in 2023, 2,910 rows/256 strata in 2024, and 2,222 rows/258 strata during January–September 2025. Their end-exposure annualized ratios are approximately 4.023101%, 4.088818%, and 4.334124%. The frozen design does not authorize new inference for these cells or transport them back to 2018.

## Accepted structural envelope

The matrix crosses two reference modes (`inherited_psa`, `matched_max_off`), two imported response conversions (`legacy_conversion`, `illustrative`), two gap treatments (`positive_only`, `preserve_refinancing`), and five supplied sensitive shares (0, 0.25, 0.5, 0.75, 1), totaling 40 scenarios. The reference, response conversion and sensitive share are structural inputs, not estimated sale/refinance shares or causal parameters. The scenario CSV records actual exercised gamma, reference annual floor, both accounting measures and each OFF/ON principal total.

Across all 40 scenarios, the reported OFF-minus-ON principal marginal spans −$0.019629974482882062B to $78.24022546087724B. Under the unreweighted closed-pool cash measure, it spans −$0.014934135617977518B to $68.42722401214542B. Both minima occur at `matched_max_off-legacy_conversion-preserve_refinancing-share-0.0`; both maxima occur at `matched_max_off-legacy_conversion-positive_only-share-1.0`. These are structural envelopes over the supplied matrix, not confidence intervals, total uncertainty intervals, or probability distributions. Reported and pool cash quantities use different accounting conventions and should remain separate.

At zero sensitive share, `positive_only` requires ON=OFF and has zero marginal. `preserve_refinancing` retains the refinancing channel, so zero sensitive share does not require ON=OFF. Negative marginal values in the latter mode are preserved as accepted scenario outputs. The envelope JSON distinguishes all eight zero-share combinations, rather than treating every zero-share scenario as an identity check.

## Evidence and checks

Before calculations, the worker seals input, design, code, test and specification hashes in the new attempt's `input_manifest.json`. It verifies panel/report/rate hashes against the accepted calibration input manifest. It reads accepted matrix `results.json` and `acceptance.json`, requires matching passed/completed evidence, reruns the local output acceptance gate, and binds its validated receipt identities to saved acceptance. The gate checks the complete 40-scenario grid, all 84 benchmark/pair/scoring receipt sets, saved output hashes, principal identities, common support/input/population evidence, invariant OFF paths, matched OFF equality and required zero-share identities. Top-level scenario values and scoring summaries are then checked against the accepted corresponding pair and scoring receipts before being summarized.

All captured input and code hashes are verified again after calculations. Final output hashes are stored in `completed.json`; failed runs preserve `failed.json`. Existing output attempts cannot be overwritten. This worker does not read or hash raw annual source archives and does not certify retained-source receipt validation. The parent workflow performs its separate source receipt fullcheck and complete regression suite.

Thirteen targeted tests pass. They cover matched adjacent numerator/denominator arithmetic, empty cells, no age imputation, the September 2025 cutoff, invalid numerators/duplicate months/missing rates, zero exposure, separate calendar/support statuses, sparse inference refusal and supported execution of both cluster layers, matrix completeness, zero-share mode distinctions, refused unaccepted evidence, changed hashed outputs and mismatched top-level pair/scoring summaries.

Key SHA-256 identities:

- Corrected panel: `047225a29d5003a116b4c23ff44263e002341db8ef9993b225f84488b49f1976`.
- Frozen rate CSV: `c2f7298dbd9c382fd9796631d92fd8234f1506605e25f1f2e1c86efea9c96205`.
- Frozen rate source metadata: `0380f2dd639fd22c6cb328b587b80324a4f2714d8ce13495345af46af3063fa2`.
- Accepted matrix results: `40402aa4e46e5eace6b14b8f5a3704dc456ab5c3985dffe9842f28fc6c5e5a23`.
- Accepted matrix acceptance: `7e849ddde64c5ba3170596b55202e75b341c527a952aef0d64dcc98e4366e621`.

Editable implementation: `hazard/corrected_floor_support.py`; tests: `tests/test_corrected_floor_support.py`. Run with `/usr/bin/python3 -u hazard/corrected_floor_support.py --accepted-root <accepted archive root> --output <new attempt directory>`. Source paths are supplied explicitly; there is no production hook, source reconstruction or new parameter selection.
