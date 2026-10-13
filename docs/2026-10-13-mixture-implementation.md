# Mixture model implementation — October 13, 2026

The approved alternative is implemented separately in the f586 worktree. No
existing model file, frozen source receipt, estimate or manuscript was changed.

## Implemented

- `hazard/mixture_hazard.py`: vectorized intensity decomposition; validates inputs;
  zero-gap PSA100/FICO/LTV/modeled-burnout reference; no hard turnover floor.
- `hazard/run_mixture_rebuild.py`: gated paired simulations for assumed shares
  0, .25, .5, .75, 1; existing seed, defaults, amortization and accounting;
  saves reported holdings-scaled and closed-pool principal marginals separately.
- `hazard/score_mixture_rebuild.py`: fixed PSA100 mixture candidate, same supported
  retrospective rows and comparator as the corrected scorer. Predicted history
  evolves without contemporaneous evaluation outcomes updating burnout.
- `specs/SPEC_2026-10-13_mixture_alternative.md`: model and evidence boundaries.

The legacy-conversion default reuses the old monthly probability-ratio response
as an intensity coefficient. This is an assumption, not an exact conversion of
an estimated prepayment-intensity elasticity. The illustrative option uses
-log(.935). Positive-only is the proposed model; preserve_refinancing is a
separate structural sensitivity on the intensity scale. OFF disables both the
positive-gap suppression and, in the latter variant, favorable-gap boosting.

No reference schedule or sensitive share has been newly estimated. The scorer
validates the old parameter freeze but does not reuse selected floor parameters;
its new candidate is fixed in advance at PSA100 and the explicitly supplied share.
The retrospective period has already been examined; these scores are not a new
untouched holdout validation. Do not promote whichever scenario gives a preferred
repayment effect.

The separate `hazard/mixture_analysis.py` entry point runs the existing-model
pair/scoring benchmarks first, then all 20 prespecified mixture scenarios
(five shares, two coefficient conversions, two gap treatments), with scoring
and both principal accounting measures for every scenario. It validates the
old frozen code hashes and complete corrected inputs before creating outputs.

```sh
python3 -m hazard.mixture_analysis \
  --pipeline output/research-rebuild/2026-10-13-reo/pipeline-after-timeout/pipeline.json \
  --output output/mixture-model/2026-10-13/full-comparison
```

## Verification and current data boundary

Final full regression: 1509 passed, 29 warnings.
Focused mixture and legacy pair/scoring checks: 51 passed. Tests exercise real engine mechanics on synthetic
fixtures, not a new empirical portfolio estimate. The example returns ON
1.6493379231% and OFF 2% monthly. The old pipeline's 264 frozen file hashes were
checked and unchanged after implementation.

The corrected source pipeline stopped at 2020Q4: eligible original records lack
valid pre-snapshot performance coverage. Its 15 earlier completed quarters remain
preserved. The mixture runner requires complete verified combined inputs and
must not run on a partial portfolio under the full-sample label.

A read-only coverage diagnostic is saved under
`output/mixture-model/2026-10-13/coverage-diagnostic`. It checks exact source hashes,
measures missing coverage, writes aggregate evidence, and requests/validates
cloud-only eviction in a finally block. It does not alter the source population
or waive the completeness check.

Prepared production arguments are in
`output/mixture-model/2026-10-13/prepared_commands.json`; they have not been run.
After complete source receipts and combination exist, finish the existing model
benchmark first, then run these separate mixture outputs. Repeat scoring across
all five assumed shares and both calibration/gap variants if required for the
final comparison. Existing floor calibration is retained only for the benchmark;
mixture reference calibration remains an additional empirical exercise.

The real-input comparison preflight was attempted and correctly stopped before
creating the comparison directory: verified completion receipts are missing for
2020Q4, 2021Q1, 2021Q2, 2021Q3 and 2021Q4. The evidence is in
`output/mixture-model/2026-10-13/preflight.log`.

Independent review found protected-output and coefficient-labeling issues;
both were fixed, tested, and re-reviewed with no remaining substantive findings
in that scope. The review was static, not an independent empirical rerun.

## Completed coverage diagnostic

The exact frozen 2020Q4 files contain 946,085 eligible original loans and
64,493,775 performance rows. All eligible loans have valid performance by the
September 2025 cutoff. Four loans expected to have pre-May history do not:
original first-payment months are November 2021 (one), December 2021 (two),
and March 2022 (one). Their first valid observed performance months are July
2022 (two) and August 2022 (two). Combined original principal is $1,487,000.
None has an invalid-balance row explaining the gap.

Both raw source hashes match the frozen source pair. Cloud-only cleanup was
verified for both files after the scan. All 15 existing completion receipts
were revalidated. No loan, cohort denominator or eligibility rule was changed.

The research decision is whether to develop an explicit coverage exception
that represents pre-May history as unknown, excludes these loans from the
May starting portfolio, and audits their cohort-history/burnout impact before
resuming; or retain the strict gate until complete records are available.
No exception is applied without the user's choice. This is a source-coverage
policy decision, not a requirement of the mixture equation.
