# Candidate new Freddie-outcome evaluation — October 9, 2026

Status: protocol prepared; no new Freddie outcomes opened. This is not a registered
preregistration, a completed validation, or a certificate that outcomes are unseen.

## Candidate record attached October 9

The bounded 2023 development comparison selected an annual floor of 0.035 and
PSA speed 100 for both candidate families. Retain the imported response coefficient
and all other declared cohort approximations. The candidate reduced retrospective
2024–September 2025 rate RMSE relative to the original model but did not beat the
simple comparator. It is retained for testing and is not promoted to production.

- Final local freeze: `output/research-limits/2026-10-09/prediction-final/parameter_freeze.json`.
- Freeze SHA256: `e83b21169558b58f67b299166a5d785bbf0e37651858fece84ae32b14a047c1a`.
- Analysis: `hazard/pathb_prediction_diagnostics.py`; SHA256
  `0032a6e3e7803d59e1c9ebc31e7fa1aac6d21a95f87e33be9107a9db30d1ab0a`.
- Runtime: `output/research-limits/2026-10-09/environment.json`; SHA256
  `3071bb975e213f60d99164816a7119a2664a433b4f283d4eee1c7572ac5587bd`.

The freeze includes exact input and protocol hashes. Earlier freezes and code
snapshots preserve the timestamp-only replay repair and subsequent docstring-only
cleanup. Candidate parameters and final numerical outputs did not change. This
attachment precedes obtaining later outcomes but does not itself complete the
source-exposure audit, freeze a new-period parser, or fix future sample membership.
Those preconditions remain mandatory before any prospective claim or new scoring.

## Preconditions before data access

1. Audit the project's prior access to October 2025–March 2026 Freddie loan outcomes.
   Existing macro/SOMA observations and Fannie aggregates through December 2025
   mean the economic period itself is not untouched. If relevant Freddie outcomes
   were inspected, label the exercise retrospective and reserve a later period
   for an uninspected test. Record the audit scope and residual uncertainty.
2. Freeze a candidate model using only the authorized development comparisons,
   with exact parameter, code, input and environment hashes. Retain the original
   production model and simple cohort-speed benchmark as comparators. Freeze the
   choice before obtaining additional outcomes; do not choose among candidates
   using the new test scores. Attach the frozen candidate artifact to this record.
3. Validate the July 2026 source layout with schema-only/sample information. Test
   conversions for interest-rate units, loan age, balances and zero-balance events.
   Do not inspect test-period outcome distributions as part of parser development.

## Population, event and denominator

Evaluate eligible conventional fixed-rate 360-month loans outstanding at the end
of September 2025 in the frozen source frame. Draw any sample by a fixed seeded
rule from that pre-test population, preserving all IDs and inclusion weights.
Retain subsequent terminations; never define eligibility by survival in March 2026.
The 2017–2021 frame can be the initial continuity cohort, with additional vintages
reported separately. Do not describe it as the full agency or SOMA population.

Use monthly beginning balances, voluntary payoff events and their pre-payoff
balances, with maturity, repurchase, default and other competing termination
codes separately tabulated. Verify event dates and lag alignment on synthetic
cases before scoring. Show excluded loans, gaps, missing codes, count/balance
coverage and weight concentration. Do not treat missing histories as zero events.

## Two distinct evaluation objects

- Primary conditional monthly-rate evaluation uses realized beginning exposure and
  the prespecified realized mortgage-rate path. It assesses conditional payoff
  predictions and must not be called a full balance-path forecast.
- A secondary closed opening-book projection can roll forward predicted balances
  from September 2025 without injecting realized survival exposure. Its scheduled
  amortization and competing-event assumptions must be frozen and disclosed before
  it is used. Do not equate its object with the primary conditional evaluation.

Primary metrics are exposure-weighted monthly rate RMSE, MAE, total predicted to
observed voluntary principal ratio and bias. Report them for every frozen model
on a common supported sample. Also report performance by coupon, origination
vintage, loan-age bucket and calendar month; preserve unsupported exposure rather
than silently renormalizing. A six-month test has limited regime coverage.

## Decision and interpretation

The candidate must improve primary rate RMSE over the original model and not
worsen it relative to the simple benchmark to support a predictive-improvement
claim. Report all metrics even if this criterion fails. Use paired differences
and a prespecified loan/cohort clustering method if sampling uncertainty is
reported; six monthly observations alone do not justify asymptotic precision.

No tuning after new test scores. Any subsequent revision moves this period into
development and requires a new uninspected test. Good observed response-on fit
does not validate the response-off counterfactual, moving share, functional form,
portfolio transport or causal attribution. No headline simulation is changed by
this protocol alone.
