# Research-limits improvement pass — October 9, 2026

Authorization: the user asked to continue working and do what is possible after
the four concrete remedies discussed on October 8. This pass executes evidence
improvements, preserving the October 8 publication and every prior result.

## Scope fixed before new calculations

1. Reconstruct older Fannie cohort support from existing compact quarterly cells.
   Freeze source hashes and 2018 mortgage rates, reproduce the published filtered
   panel, then inventory the omitted earlier vintages. Distinguish acquisition-tail
   selection, agency differences, rate-gap overlap, and end versus opening exposure.
2. Diagnose the existing retrospective Freddie prediction error. Reconcile saved
   scores, identify floor binding and cohort approximations, then compare a small
   candidate set fixed before its evaluation. Fit candidates only on development
   observations through 2023. Previously inspected 2024–September 2025 outcomes
   remain retrospective evaluation, not an untouched holdout.
3. Test public SOMA-to-pool disclosure matching on a small deterministic sample of
   the June 29, 2022 book. Freeze source bytes and match criteria. Require the actual
   collateral rate at a matching date, not a security coupon mislabeled as a note
   rate. Report nonmatches and resecuritization issues, without broad extrapolation.
4. Verify practical access to earlier Freddie quarters and suitable payoff-reason
   data. No purchases, contact messages, account creation, bulk downloads, or opening
   post-September-2025 Freddie loan outcomes in this pass. Prepare a future evaluation
   protocol before obtaining those outcomes.

## Interpretation and preservation

The $42.6B response-on/off anchor is conditional, not a causal or full-SOMA estimate.
Improved observed fit cannot establish causal attribution. A mature-loan observation
does not identify moving versus refinancing. No provisional diagnostic replaces a
production parameter merely because it produces a preferred result.

Work runs in the existing isolated f586 checkout. Original local and cloud source
files are read-only; licensed cells and downloaded artifacts stay in ignored
output/research-limits/2026-10-09/. Code, tests, specifications and non-disclosive
aggregate research notes may be versioned locally. No remote push is authorized.

## Acceptance checks

- Source bytes/hashes and the relevant population, period, units and denominator
  accompany each calculation.
- Exact or tolerance-stated replay checks precede comparisons to prior results.
- Synthetic tests cover aggregation, exposure accounting, calibration separation
  and any corrected implementation behavior.
- A separate review checks new conclusions against generated artifacts.
- The final research note distinguishes completed improvements, adverse findings,
  external access blocks and remaining scientific limitations.
