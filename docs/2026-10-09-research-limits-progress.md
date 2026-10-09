# Research improvements completed — October 9, 2026

Two data-processing defects are corrected, a bounded prediction recalibration is
complete, and the available older-loan baseline has been tested. The candidate
substantially reduces overprediction but still does not beat a simple comparator
on monthly-rate error. Correcting loan-age aggregation also reveals that the
local older-loan baseline is much thinner than the legacy calculation suggested.
These results improve the diagnosis; they do not resolve causal identification.

## Prediction improvement, with an adverse comparison retained

For the supported Freddie sample in January 2024–September 2025, observed
voluntary payoff principal was $131.303 billion. The 4.991% annual minimum binds
on 91.54% of exposure and alone implies $160.422 billion. The original model
predicts $161.784 billion. That minimum is therefore central to the excess.

Choosing among a fixed small grid using only 2023 observations selects a 3.5%
annual minimum with the existing 100 PSA setting. On the later evaluation period:

| Specification | Predicted payoff principal | Monthly-rate RMSE, percentage points |
|---|---:|---:|
| Original model, response on | $161.784B | 0.13389 |
| Candidate, response on | $128.846B | 0.11014 |
| Simple 2023 cohort-speed comparator | $121.436B | 0.08679 |

The candidate cuts the original model's primary error metric by 17.74%, but the
simple comparator still performs better. The candidate is recorded for further
testing, not substituted into the paper. These scores condition on realized
opening exposure and mortgage rates, and the evaluation outcomes were already
examined. They are neither an untouched holdout nor full-book forecasts.

See [the prediction analysis](2026-10-09-pathb-prediction-diagnostics.md) for
both response legs, accounting reconciliation, model-state limitations, parameter
selection and exact freeze hashes. The comparison figure is in the local
`output/research-limits/2026-10-09/` folder as PNG and PDF.

## Code repairs and older-loan support

1. Previous balances now follow reporting dates within each loan. A synthetic
   unsorted history exposed a $100 payoff numerator where the correct previous
   balance was $90. The regression test verifies the repaired production code.
2. Combining quarterly cells now weights mean loan ages by loan counts. An
   unweighted average of file means gave small files too much influence.
   Regression tests cover unequal file sizes and missing quarter mean ages.

The Fannie pilot reconstructs the saved panel from all 24 existing acquisition-
quarter files before testing older originations. At the pure-2018 cut of mean
age at least 24 months and coupon at least 25 bp below the market rate, corrected
weighting reduces qualifying exposure from $46.674 billion-months to $0.444
billion-months. This is reclassification of 99.05% of formerly qualifying exposure,
not deletion of balances. The remaining 183 cohort-months span 23 strata but
are concentrated like only 5.10 equally weighted strata. No support remains at a
200 bp discount.

That selected acquisition tail has a descriptive annualized payoff rate of
5.56%; it does not establish a representative turnover floor or moving share.
The count-weighted age recovery also assumes the reported loan count describes
each finite quarter mean; partial missing ages inside quarters cannot be checked
from these aggregates. The original saved panels have not been rebuilt after the
ingestion fixes, and any realized effect of source-row ordering remains unknown.
See [the older-vintage analysis](2026-10-09-older-vintage-floor-support.md).

## Access work completed and remaining dependencies

- The June 29, 2022 NY Fed holdings response was frozen. A deterministic pilot
  selects the five largest 30-year UMBS positions, covering 5.26% of MBS face.
  PoolTalk stopped at its terms page before collateral attributes were obtained.
  This is a prepared matching sample, not a completed pool match.
- Freddie's official download portal reached an empty sign-in page. Earlier
  Freddie source quarters and later test outcomes were not downloaded.
- Public CMU support pages do not establish access to Cotality payoff-reason
  data. The needed extract and its comparable outstanding-loan denominator are
  specified; no sale-specific moving share has been estimated.
- A future Freddie evaluation protocol now contains the exact candidate and
  artifact hashes. Auditing prior outcome exposure and freezing the new parser
  and sample remain prerequisites before calling any future test prospective.

The [access and pool note](2026-10-09-data-access-and-pool-pilot.md) records the
five identifiers, official sources and precise remaining data requirements.
No purchases or external messages occurred, and no account was created. The
under-$25 constraint remains in place. The further data steps require portal or
institutional access, not another broad literature search.

## Verification and preservation

- **1,231 tests passed**, with 26 warnings. New regression and diagnostic tests
  cover accounting, chronological payoff lags, age weighting, missing ages,
  annual/monthly probability conversion, development-period restrictions and
  exclusion of evaluation outcomes from prediction-state updates.
- An initial unrestricted test discovery found duplicate test copies in the
  ignored October 8 package-rebuild folders. Running the active tree with
  `python3 -m pytest -q --ignore=output` completed successfully. The initial
  collection failure and successful run are both retained. The warning count
  includes dependency deprecations and existing numerical optimization warnings;
  a passing suite does not establish economic identification.
- Original prediction paths reconcile within floating-point tolerance, and all
  23,443 rows of the saved Fannie filtered panel reproduce under its legacy rule.
- All 11 final prediction inputs and 26 Fannie source/manifest hashes were
  rechecked. None changed during the analyses. A docstring-only cleanup was
  replayed in a separate folder; parameters, scores and cell predictions match.
- All 316 tracked paper and data files match the pre-pass Git revision. All four
  October 8 publication PDFs match their saved hashes. The source ZIP retains
  SHA256 `e9b1abed48c9cdc38dbdcd6f03688ac16e03f05f1e43f9053e1fe8a4d2554fc0`
  and passes its archive integrity check. No manuscript rebuild was needed.
- A separate agent review could not finish because of a service usage limit.
  The parent agent checked calculations, artifacts and limitations; this is not
  claimed as a completed independent review.

Machine-readable verification, runtime versions, frozen inputs, detailed local
diagnostics, attempt logs and the comparison figure are retained in
`output/research-limits/2026-10-09/`. Licensed cell predictions and source files
remain excluded from version control. Code, tests, protocols and aggregate notes
are saved locally; the October 8 publication package remains a separate edition.

The remaining scientific steps are an audited source rebuild, evaluation on new
outcomes with a frozen protocol, dated collateral matching, and data that
distinguish sale payoffs from other voluntary terminations. Better observed fit
alone cannot validate the response-off counterfactual, the imported elasticity,
the whole-SOMA transport assumptions, or a causal interpretation of $42.6 billion.
