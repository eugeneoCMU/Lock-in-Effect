# Prediction diagnosis and bounded recalibration — October 9, 2026

The original minimum payoff rate explains most of the model's aggregate
overprediction in this check. A candidate selected using 2023 observations reduces
later-period error, but it still loses to the simple cohort-speed comparator on
the primary monthly-rate metric. **Retain the candidate for further testing;
do not promote it or replace the paper's simulation results.**

## Population, timing and evaluation object

The comparison uses the existing supported Freddie cohort sample: 239 cells,
5,019 cell-months, January 2024–September 2025. Summed beginning-balance exposure
is $37,680.230114 billion-months. Observed voluntary payoff principal is
$131.303322 billion. This is principal paid at voluntary termination, not total
agency runoff, scheduled principal, or home-sale principal alone.

Predictions condition on realized beginning balances and mortgage rates. The
internal burnout state advances using predicted voluntary payoffs, retaining the
original approximation. This is a conditional monthly payoff comparison, not a
forecast of an entire portfolio balance path. These evaluation outcomes had
already been examined before this exercise; they are not an untouched holdout.

Parameter selection used only January–December 2023, initialized in December
2022: 2,868 observations in 239 cells. The prespecified grid contained annual
floors 0%, 2%, 3.5%, 4.991% and PSA speeds 50, 75, 100. Both permitted candidate
families selected **3.5% annual floor and 100 PSA**. Their development RMSE was
0.124145657 monthly percentage points. No additional candidate was chosen after
seeing the later-period scores.

## Results on common evaluation support

| Specification | Predicted voluntary principal, $B | Predicted / observed | Weighted monthly-rate RMSE, pp | Weighted monthly-rate MAE, pp | Principal bias, $B |
|---|---:|---:|---:|---:|---:|
| Simple 2023 cohort-speed comparator | 121.4362 | 0.92485 | 0.08679 | 0.06884 | -9.8671 |
| Original, response on | 161.7842 | 1.23214 | 0.13389 | 0.11011 | +30.4809 |
| Original, response off | 172.6429 | 1.31484 | 0.15700 | 0.13355 | +41.3395 |
| Candidate, response on | 128.8461 | 0.98129 | 0.11014 | 0.08191 | -2.4572 |
| Candidate, response off | 160.7063 | 1.22393 | 0.15355 | 0.12826 | +29.4030 |

The floor-only and floor-plus-PSA selections coincide, so this table shows one
candidate rather than counting it twice. RMSE is weighted across cell-month
payoff rates, not an RMSE of aggregate dollars. The candidate reduces this RMSE
17.7376% relative to the original response-on model. Its near-matching cumulative
total does not overcome its worse monthly-rate performance than the comparator.
Response off sets only the imported rate-gap coefficient to zero. Its score does
not identify an observed counterfactual, and differences here do not replace the
separate $42.6 billion conditional simulation result.

## What drives the original error

The 4.991% annual floor converts to a monthly probability of 0.004257458056,
using compound probabilities. It binds in 4,158 cell-months, representing
91.5353% of exposure. No row triggers competing-hazard normalization.
Applying that minimum to all evaluation exposure alone gives $160.4220 billion,
already $29.1187 billion above observed payoffs. The complete response-on model's
excess is $30.4809 billion. This is a mechanical diagnostic of the floor on the
observed exposure, not an estimate of turnover or of a causal effect.

The floor-bound group contributes $28.8902 billion of signed overprediction;
the remaining group contributes $1.5907 billion. Grouped amounts reconcile to
the aggregate. Complete coupon, vintage, coupon-by-vintage and half-year
diagnostics are retained locally, including unfavorable groups.

The model's internal balance state is exposure-weighted 2.2799% above realized
beginning balances. Its recursion excludes scheduled amortization and defaults,
as did the original approximation. The candidate retains that limitation.

## Ingestion repair and its limits

A synthetic example established a real implementation defect: an unordered
within-loan lag could attach a $100 previous balance to a payoff whose actual
preceding monthly balance was $90. The production ingestion window now orders
observations by reporting month. The regression test demonstrates the old error
and verifies that the corrected production function returns $90.

This does not establish that real input rows were misordered or that this defect
caused the saved-panel overprediction. Duplicate and missing reporting months,
raw source ordering and individual termination histories still require an audit
before rebuilding. No saved panel was overwritten. The comparison above uses
the preserved existing inputs and retains this qualification.

## Reconciliation, freeze and reproducibility

The original predictions reproduce the saved October 7 check on identical
support. The largest absolute hazard difference is below 1e-16, with aggregate
metrics agreeing within the specified tolerance. Exposure and observed payoff
amounts also reconcile. Input hashes were checked after computation.

The first replay stopped on a timestamp-storage mismatch: the CSV used
nanoseconds and the Parquet used microseconds, with the same 5,019 date/cell keys.
Canonicalizing timestamp resolution repaired the comparison. The initial freeze
and failed attempt remain in `prediction-before-timestamp-repair/`; selected
parameters did not change. After the successful run, a helper docstring was
updated to acknowledge that the production ingestion repair had been applied.
The prior source snapshot and freeze remain in `prediction/`. A final replay in
`prediction-final/` has identical selected parameters, aggregate metrics,
group diagnostics and byte-identical cell predictions and score tables.

All paths below are relative to `output/research-limits/2026-10-09/`:

- Final results: `prediction-final/results.json`.
- Parameter freeze: `prediction-final/parameter_freeze.json`, SHA256
  `e83b21169558b58f67b299166a5d785bbf0e37651858fece84ae32b14a047c1a`.
- Final analysis code SHA256:
  `0032a6e3e7803d59e1c9ebc31e7fa1aac6d21a95f87e33be9107a9db30d1ab0a`.
- Runtime manifest: `environment.json`, SHA256
  `3071bb975e213f60d99164816a7119a2664a433b4f283d4eee1c7572ac5587bd`.

The final freeze follows an already completed evaluation replay; it does not
retroactively make this exercise preregistered. The earlier freeze documents the
unchanged parameter choice before the first successful candidate evaluation.
The separate future-evaluation protocol records the candidate and prerequisites
before any later Freddie outcomes are obtained. No later Freddie outcomes were
opened in this pass.
