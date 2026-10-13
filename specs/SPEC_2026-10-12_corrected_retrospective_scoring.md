# Corrected Freddie retrospective scoring — October 12, 2026

The user authorized working through the remaining rebuild inputs and stages.
This specification is written before any corrected empirical scoring. It adds
an offline, separately saved comparison; it does not replace prior results.

1. Require all twenty verified 2017Q1–2021Q4 Freddie quarter receipts and the
   complete combined manifest through `calibrate_freddie_rebuild.validated_combined`.
   Explicitly supply root, frozen macro, recorded parameter freeze, recorded
   results binding that freeze's SHA256, and a new output directory. Preserve
   existing attempts, production inputs, source outputs and paper artifacts.
2. Freeze input, code, specification and environment hashes before reading
   outcome columns. Validate panel identity/date columns first; reject a
   duplicate, inconsistent or post-202509 date. Read outcome columns with a
   date predicate ending September 2025. No raw source, cloud or network access.
3. The conditioning rate is the saved monthly MORTGAGE30US value divided by
   100, retaining the existing monthly conditioning convention. Its exact
   bytes must match both the recorded parameter freeze and bound results.
   Require finite positive rates in every January 2024–September 2025 month.
   This is distinct from the separate floor grid's within-month weekly mean.
4. Keep the original 4.991% annual floor / 100 PSA and both recorded candidate
   families at 3.5% / 100 PSA. Verify the saved selection dates (all of 2023),
   candidate grid and selected values against the saved results. Never invoke
   parameter selection or change a choice after reading evaluation outcomes.
   For each family run response off (coefficient zero) and response on (the
   existing survival conversion of a 6.5% quarterly decline), otherwise identical.
5. Evaluate January 2024–September 2025 using December 2023 state and fixed
   May 2022 sample covariates. Require corrected fixed-cohort historical
   denominators and valid burnout; no legacy opt-in. Advance age and predicted
   payoff history monthly, including months whose observed score row is
   missing or invalid. Only cell/date/coupon feed this prediction calendar;
   evaluation outcomes never update predicted history. Reuse the existing
   `predict_path`, `make_covariates`, `strict_score` and `diagnose_groups`.
   Retain the declared combined sample, including identical source-loan draws
   created by sampling with replacement; bind row and unique-ID counts to the
   combined receipt and reject conflicting records for a repeated ID.
6. Preserve the existing simple comparator: each cohort's January–December
   2023 payoff principal divided by summed contiguous opening exposure, using
   `fit_baseline`. January–June 2022 is not its recorded training window.
   Use one common supported evaluation set for the comparator and all families.
   Disclose lag, zero-exposure, invalid-numerator and support exclusions, raw
   and retained row/cell/month counts, exposure dollar-months and observed
   principal; do not call an unknown first-row exposure zero coverage.
7. Save all family/leg metrics, coupon-by-vintage and half-year diagnostics,
   floor-bound diagnostics and compact scored cell-months. Reconcile grouped
   dollars with aggregate dollars. Recheck input/code hashes before success;
   retain a failure receipt and the input freeze if any check fails.

This comparison is conditional on realized opening exposures and mortgage
rates. The evaluation period has already been examined; it is not a new
holdout or a forward balance forecast. Population now consists of known
360-month fixed-rate loans, with the explicit source exclusions and payoff
fallback conventions in the combined manifest. Differences jointly reflect
population and implementation changes. They do not identify a causal moving
response, a sale-versus-refinance split, or transport to the full SOMA book.
No new empirical scoring may run before all twenty source quarters pass.

Implementation plan: create only `hazard/score_freddie_rebuild.py` and
`tests/test_score_freddie_rebuild.py`; write failing synthetic integration and
gate tests first, implement the offline wrapper, run the targeted tests and
the directly reused prediction tests. Root coordinates the complete suite
and any eventual empirical execution. No source-worker dependency is edited.
