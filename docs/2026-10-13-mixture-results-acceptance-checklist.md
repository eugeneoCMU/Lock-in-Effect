# Mixture results acceptance checklist

Prepared before empirical results; this does not validate an unfinished run.

1. Require final complete analysis, both benchmark forms (paired simulation and scoring), all 40 scenarios, verified
   combined inputs and passing accounting checks. Partial progress is insufficient.
2. Compare fit on the same supported rows, cells, months, exposure and observed
   principal. Inspect signed error and coupon/vintage and half-year groups.
   Larger OFF-minus-ON repayment differences do not establish better fit.
3. Label both references as inherited, not newly calibrated: zero-gap PSA100/covariates or the matched hard-max OFF schedule.
   Shares and response conversions are assumptions. Read actual gamma_per_pp,
   rather than the adapter's inherited quarterly-response input percentage.
4. Compare each scenario's ON/OFF pair first. All mixture OFF paths within a reference should agree; matched-max OFF must also match the hard-max benchmark. Share zero is an identity check for positive_only, but not
   necessarily preserve_refinancing: its separate boost affects total intensity.
5. Keep reported_marginal_b (holdings-scaled reporting) separate from
   closed_pool_cash_marginal_b (unscaled simulated cash). Neither is a leg's
   target-relative extension. Percentage points use the recorded benchmark.
6. Verify principal identities and voluntary/scheduled/terminal components.
   Equal default/amortization rules need not produce equal realized amounts.
   Terminal claim transfers are not recovery cash.
7. Require source-bound four-loan coverage evidence, May exclusion, known-history
   denominator and combined-cohort bounds. Unknown history must remain unknown.
   The upper burnout scenario assumes payoff is capped at original principal;
   this is not automatically a bound on dollar effects.
8. Calibration in this isolated revision propagates coverage directly into its receipt.
   The active frozen pipeline retains its original code; preserve that freeze.
9. Scenario ranges are structural sensitivity, not confidence intervals. Earlier
   uncertainty bands do not transfer automatically. These outcomes were already
   examined, so choosing a preferred scenario is retrospective selection.
10. Do not infer an estimated sensitive share, sale/refinance split, identified
    causal response or full-SOMA representativeness. Preserve manuscript estimates
    until completed comparisons are reviewed.

Inspect benchmark_scores, scenarios[].retrospective_scores, scoring support and
 groups, paired legs and pre_snapshot_coverage, alongside the analysis manifest.


Version 2 implements the objective completion requirements in `hazard/comparison_acceptance.py`. The runner writes acceptance.json and complete results only after that gate passes. Interpretation, cause identification, coefficient calibration, and review of conditional research claims still require judgment; a software gate does not resolve them.
