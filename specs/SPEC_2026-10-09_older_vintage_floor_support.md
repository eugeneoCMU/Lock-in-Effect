# Older-vintage Fannie support pilot — frozen before calculation

Frozen 2026-10-09. This is a descriptive support pilot, not a production floor
estimate or a change to the paper. Support counts inspected before this freeze
established only that the local quarterly files contain older originations;
no new pure-2018 older-tail payoff rate has been calculated.

Input-validation amendment before any new payoff calculation: the first run found
231 quarterly cells with missing mean age, including 10 in 2018. Preserve the first
frozen specification and failed-run log. Audit and exclude missing current ages
from the pilot, after constructing lagged balances so valid prior exposure is not
lost. Legacy-panel parity continues to include those cells. Count-weighted age
uses reported loan counts; within-quarter partial age missingness is unavailable
in the saved aggregates and remains a limitation.

## Inputs and population

- Read the 24 existing `cells_FNMA2017Q1.parquet` through
  `cells_FNMA2022Q4.parquet` files and their manifest under the primary
  checkout's `hazard/data/fannie_quarters/`. These are acquisition-quarter
  extracts, not a representative sample of older origination vintages.
- Read the existing primary-checkout
  `hazard/data/cohort_month_panel_fannie.parquet` for parity. Never overwrite
  these inputs. Record input hashes and check they remain unchanged.
- The main comparison is performance in calendar 2018, separately for the
  production origination frame (2017–2021), the omitted older acquisition tail
  (origination year <=2016), and their union. The older group is further split
  into 2015–2016 and <=2014 for support descriptions.
- Record which acquisition quarters supply 2018 observations. Performance
  preceding the start of its acquisition quarter is an acquisition-history
  selection concern: report and exclude those rows from the pilot before
  combination. Do not describe the remaining older tail as older Freddie
  support or the full older Fannie population. A loan identifier is unavailable
  in these aggregates, so source-disjoint loan membership cannot be re-audited.

## Sequence and accounting gates

1. Freeze this file and record its SHA-256 before any new outcome calculation.
2. Load every named quarter once; reject duplicate quarter identifiers or
   duplicate cohort-month keys *within* a quarter. Same cohort-month keys in
   different quarters represent additive subpopulations and must be combined,
   not discarded or treated as independent cells.
3. Reproduce the existing filtered panel with the legacy unweighted mean of
   quarter mean ages and its derived rate/burnout fields. Keys and counts must
   agree exactly. All deterministic numeric columns must agree within
   relative 1e-12 and absolute 1e-7 tolerance (floating reduction ordering).
   Record maximum differences and exact-equality counts. State-mode differences
   are reported separately because they are not used by this pilot. Stop on
   any failed numeric/key parity gate, before reporting new payoff results.
4. For the pilot, add exposure, original UPB sums, prepaid UPB, and loan counts.
   Compute age as sum(quarter mean age * quarter loan count)/sum(loan count).
   Verify additive conservation. Also retain the legacy age convention as a
   sensitivity and report membership/exposure changes at each age/depth cut.
   These are mean-age cells, not individual-loan age thresholds.
5. Fetch official FRED `MORTGAGE30US` weekly data for 2018. Preserve exact
   response bytes, retrieval metadata, and SHA-256. Take the unweighted mean
   of the observed weekly rates in each calendar month and divide percent by
   100, as in the existing floor read. Require all twelve months. Never use
   a later interest-rate value to fill a missing 2018 observation.

## Fixed descriptive grid

- Positive coupon and positive end-of-month exposure; 2018 only.
- Gap = coupon minus contemporaneous monthly market rate. Maximum gaps:
  0, -25, -50, -100, and -200 basis points.
- Minimum mean age: 12, 24, 36, and 60 months. Also report disjoint age
  groups [12,24), [24,36), [36,60), and [60,infinity) at gap <=-25bp.
- For each selected population report combined cohort-month count, unique
  vintage/coupon/FICO/LTV strata, calendar months covered, end-UPB dollar-month
  exposure, loan-month counts (not distinct borrowers), and exposure share of
  the same population/age group at gap<=0. Report effective cohort-months and
  effective strata as (sum exposure)^2/sum(exposure^2), aggregating exposure
  across months for the latter. These are concentration measures, not
  independent statistical sample sizes. No minimum support count will be
  construed as establishing floor identification.
- When 30+ cohort-months and 5+ strata are present, report aggregate historical
  annualized payoff rate: 100*[1-(1-sum(prepaid UPB)/sum(end UPB))^12], provided
  SMM is in [0,1]. Smaller groups have their payoff results suppressed. Never
  publish a single cohort's payoff outcome. This is a descriptive annualized
  rate under the prior floor convention, not a directly observed annual CPR.
- Separately report a lagged-opening-UPB sensitivity using the same selected
  cohort-months where the preceding calendar month's exposure exists in the
  *same acquisition-quarter subpopulation*. Build lags before combining
  quarters, so newly acquired cohorts cannot borrow another quarter's risk
  set. Use only numerator/exposure pairs with valid lags, disclose their
  coverage, and do not treat it as an exact loan-level risk set.
- Compare aggregate headline pure-2018 age>=24 / gap<=-25bp with the filtered
  panel and the already reported pooled 2017–2019 Fannie read. A calendar-
  year comparison and an acquisition-tail comparison are distinct.

## Deliverables and boundaries

Write code/tests plus a short aggregate report in the owned files. Put frozen
spec copy, provenance, rate bytes, parity audit, local aggregate diagnostics,
and results under `output/research-limits/2026-10-09/floor/` (ignored). No raw
loan or cell data are committed. Do not edit the manuscript or production
artifacts, fetch cloud data, refit models, rerun a simulation, add confidence
intervals, or call the pilot a representative or sale-specific floor. The
voluntary-payoff outcome still does not distinguish sale from refinancing.
