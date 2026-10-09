# Path B prediction diagnostics and bounded retrospective development

Frozen 2026-10-09 before computing any new candidate's 2024–September 2025
scores. Existing published retrospective aggregate scores and source-code
structure have already been inspected. This is exploratory development using
an already examined evaluation period, never an untouched holdout.

## Question and scope

Reconcile the saved October 7 check exactly; audit lagged exposure, payoff
numerator, rates and probability units; attribute response-on signed error by
whether the 4.991% annual floor binds, coupon, vintage, and calendar half-year.
Keep production files and source data unchanged. Any verified implementation
bug gets a synthetic regression test and a proposed patch, not a silent change.
Do not read or download Freddie outcomes after September 2025.

Implementation amendment before any new candidate scoring: the synthetic row-order
regression established an ingestion defect, and unequal-size quarter fixtures
established incorrect pooled mean ages. Correct those ingestion operations with
regression tests under the user's authorization to fix what is possible. Do not
rebuild saved panels or change model parameters. The retrospective comparison still
uses the preserved original inputs, with their hashes and this limitation explicit.

Replay correction: the first attempt reached the support check and stopped because
the CSV and Parquet indexes stored identical dates at nanosecond and microsecond
resolution. Both had the same 5,019 keys, with zero set differences. Preserve that
failed attempt and parameter freeze. Normalize timestamp storage resolution and
rerun the unchanged candidate grid, checking that the selected parameters match
the initial freeze exactly. This is a replay repair, not additional tuning.

## Frozen comparison

Use the October 7 evaluation cells, observations, rates, and scoring basis.
The outcome is voluntary payoff prior-UPB principal divided by contiguous
prior-month end exposure. It excludes scheduled, default, and curtailment flows.
Reproduce the comparator (each cell's 2023 payoff/exposure ratio) and original
paired response-on/off paths. Retain the original forecast approximations:
frozen sample cell covariates; pre-period mean age advanced by elapsed months;
pre-period burnout advanced by predicted payoff only; no realized evaluation
outcomes in state updates. Competing-risk normalization remains unchanged.

Two candidate families are permitted, with no post-evaluation additions:

1. **Floor-only:** fix PSA at 100 and select annual floor from
   `[0.0, 0.02, 0.035, 0.04991]`.
2. **Floor plus PSA:** select the Cartesian product of the same four annual
   floors and PSA speeds `[50, 75, 100]`.

Fit each family only on January–December 2023 using December 2022 state,
fixed sample covariates, and conditioning rates. Development support requires
the December 2022 state and covariates, without evaluating 2024–25 outcomes.
Choose the lowest exposure-weighted monthly-rate RMSE of the **response-on**
leg; ties use smaller distance to original floor, then smaller distance to
100 PSA, then numeric floor and PSA. Store all 2023 grid scores and chosen
parameters before scoring the later period. Use the same chosen floor and PSA
in both structural legs; response-off always sets only the imported response
coefficient to zero. The grid's zero annual floor uses the existing conversion
helper's numerical minimum of 1e-8 monthly.

## Metrics and safeguards

Primary: exposure-weighted cell-month rate RMSE, in monthly percentage points.
Secondary: weighted MAE, cumulative predicted/observed voluntary principal,
prediction/observation ratio, and signed principal error. Report all original
and selected candidates; compare both to the simple comparator. Report fixed
half-year and coupon-vintage diagnostics, not a selected favorable subgroup.
Show floor-bound exposure and its signed error contribution. Reconcile grouped
amounts and source hashes; publish parameter freeze hash and times.

Tests cover accounting on hand-computed data, annual-to-monthly units,
off/on coefficient identity, no outcome leakage into predictions, development
date restrictions, and deterministic selection. No tuning after evaluation.
Any choice outside this spec requires a separate future protocol and remains
outside this run.

## Interpretation

A better score is evidence of conditional retrospective predictive improvement
on this supported Freddie cohort sample, not validation of imported elasticity,
causality, forward loan balances, SOMA transport, or the $42.6B result. The floor
and PSA are predictive calibration choices; they are not newly identified
economic parameters. The evaluation set has been seen before. Retain adverse
findings and recommend prospective testing with frozen code and fresh risk sets
before promotion. No manuscript edits or production promotion in this task.
