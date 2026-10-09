# Older-vintage 2018 floor support — October 9, 2026

Existing compact Fannie files contain some older-origin loans, but correcting
the pooled age calculation removes 99.05% of the exposure that the legacy
calculation classified as mature in the main 2018 cut. The remaining data are
small, concentrated and selected by later acquisition. **They do not establish
a representative mature-loan turnover floor.**

## Source and reconstruction

The pilot reads the 24 existing Fannie acquisition-quarter aggregates from
2017Q1–2022Q4, without downloading or changing loan files. Their 175,383 input
quarter-cell-months reproduce all 23,443 rows of the saved 2017–2021-origination
panel under its legacy combination rule. Keys, counts, balances and calculated
rates reconcile; finite numeric differences were zero in this run. The parity
gate allowed relative 1e-12 and absolute 1e-7 floating-point tolerance.

There were no performance observations before their acquisition quarter.
There were 231 rows with missing mean age; these were excluded from age cuts
after creating within-quarter lagged balances. Ten were in 2018, carrying zero
2018 exposure. Source files and their manifest passed the final hash check.

The 2018 mortgage rates are calendar-month means of observed weekly Freddie
PMMS rates from [the official FRED series](https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US&cosd=2018-01-01&coed=2018-12-31).
All twelve months are present, without future filling. Retrieved source bytes,
metadata and monthly rates are frozen locally. Source SHA256:
`d0eaba91dc65a44e3c685fe18e8de69901c0f4b7476e231bb7f22974ecb9031e`.

## The age error matters for eligibility

The old combination took an unweighted average of quarter-level mean ages.
A small quarterly group could therefore move the combined age as much as a
large one. The corrected combination weights finite quarter mean ages by their
loan counts. The repair is applied in both Freddie ingestion and Fannie quarter
combination, with regression tests for unequal counts and missing ages.

This recovers the pooled mean when each quarter mean describes its reported
loan count. Existing compact cells do not contain the number of individual
loans with nonmissing age; partial missingness within a quarter remains an
unmeasured limitation. Entirely missing quarter means are excluded from the age
average while production aggregation retains their additive balances and counts.
No claim is made that cohort mean-age cuts select only individual loans above
the age threshold.

For older origins through 2016, calendar 2018, mean age at least 24 months and
coupon at least 25 basis points below the contemporaneous market rate:

| Quantity | Legacy unweighted age | Loan-count-weighted age |
|---|---:|---:|
| Combined cohort-months | 210 | 183 |
| Distinct vintage/coupon/FICO/LTV strata | 45 | 23 |
| End-balance exposure, billion dollar-months | 46.674146 | 0.443588 |
| Loan-months, not unique loans | 216,448 | 2,546 |
| Descriptive annualized payoff rate, end-balance denominator | 5.0829% | 5.5621% |
| Descriptive annualized payoff rate, lagged opening denominator | 5.0445% | 5.5635% |

The corrected age rule reclassifies 27 cohort-months carrying $46.230558 billion-
months below the age cutoff. That is 99.0496% of the previously qualifying
exposure. These balances are reclassified, not deleted from the source data.
The standard 2017–2021-origination panel contributes zero observations to this
pure-2018 age-at-least-24 cut under either convention.

## Depth and concentration after the correction

All rows below use older origins through 2016 and corrected mean age at least
24 months. Dollar-month exposure is the sum of monthly balances, not a single
date's balance, unique borrower count or independent sample size.

| Coupon minus market-rate maximum | Cohort-months | Strata | Exposure, $B-months | Annualized payoff rate using end balance |
|---|---:|---:|---:|---:|
| 0 bp | 225 | 23 | 0.489167 | 5.2857% |
| -25 bp | 183 | 23 | 0.443588 | 5.5621% |
| -50 bp | 153 | 17 | 0.342472 | 4.8644% |
| -100 bp | 87 | 10 | 0.078942 | 4.8618% |
| -200 bp | 0 | 0 | 0 | Not estimable |

At -25 bp, all twelve months appear, but the exposure concentration corresponds
to only 5.10 equally weighted strata. The largest stratum carries 32.45% of
exposure. These are concentration diagnostics, not effective independent
observations or a basis for confidence intervals. No support exists at -200 bp.

The lagged opening-balance sensitivity first forms adjacent-month lags within
each acquisition-quarter subpopulation, preventing later-acquired cells from
borrowing another quarter's risk set. It covers 180 combined cohort-months and
99.5431% of selected end-balance exposure at -25 bp. It is still an aggregate
accounting sensitivity, not a reconstruction of individual loans at risk.

Annualization is `100 * [1 - (1 - total prepaid UPB / total exposure)^12]`.
It is a transformation of an exposure-weighted monthly rate, not a directly
observed annual CPR. Outcome summaries require at least 30 cohort-months and
five strata; smaller groups are suppressed. Suppression thresholds do not
establish identification or representativeness.

## Implication for the paper

The older loans are a selected acquisition tail inside later Fannie files.
They are not representative earlier Fannie vintages, and they are not Freddie
loans. The measured payoff includes both sales and refinancing. Small support,
age aggregation, acquisition selection and poor deep-discount overlap prevent
this pilot from validating a universal 4.991% floor or identifying moving share.
Its descriptive 5.56% rate also does not validate or overturn the separately
calibrated 3.5% predictive candidate, which uses a different sample and period.

The prior pooled 2017–2019 Fannie read is a different calendar and population
object; it has not been replaced. Saved compact cells also predate the newly
corrected payoff-ordering code. Whether actual input ordering affected their
payoff numerators is unknown until source histories are audited and rebuilt.

The completed code is `hazard/older_vintage_floor_support.py`. Frozen protocol,
source hashes, parity checks, support grids, age-bin summaries and membership
changes are in `output/research-limits/2026-10-09/floor/`. The first attempt
stopped on missing ages; its freeze and logs are retained. The missing-age rule
was documented before calculating the new payoff summaries. No production
panel, parameter or paper result was overwritten.
