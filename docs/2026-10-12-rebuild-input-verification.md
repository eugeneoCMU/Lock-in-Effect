# Rebuild input verification — October 12, 2026

This continues the authorized source rebuild in f586. The source job remains
serial, with one Freddie pair at a time and verified cloud-only cleanup before
the next pair. Existing results and the manuscript remain preserved. This note
records verified intermediate evidence, not a replacement paper estimate.

## Source checkpoint and the 2019Q4 stop

At this checkpoint, all 15 quarters from 2017Q1 through 2020Q3 passed the full
completion validator: 315,936,421 source performance rows, 5,527,605 eligible
original loans, and 2,527,494 exact May-2022 survivors. The 292 protected baseline
files still match their saved hashes. The private machine-readable checkpoint
is `output/research-rebuild/2026-10-11/verified_progress.json`.

The first 2019Q4 attempt stopped because a quarter partition of one vintage
cohort had payoff principal above its original balance. A separate read-only
diagnostic preserved the calculation and verified both source hashes before
and after processing. Its source pair passed safe cleanup. The attempt and
private loan histories remain under `quarters/2019Q4.attempt1/`.

The discrepancy is one positive payoff of $223,864.25 against $196,000 original
balance. The payoff in June 2024 used the adjacent May balance. The loan's
reported balance had increased; the diagnostic found no repeated positive
payoff or terminal revival. It does not establish the cause of the increase.
Across the complete 2019 vintage cohort, the existing other-quarter data plus
this partition give $4,193,349.04 payoff principal against $5,302,000 original
balance. The complete-cohort bound therefore holds for this observed case.

The separately frozen `SPEC_2026-10-12_quarter_cash_ratio.md` retains the exact
quarter numerator and denominator, records the exception, and keeps the final
complete-cohort bound. Multiple positive payoffs or terminal revivals prevent
use of the exception. Historical initialization checks remain unchanged. The
2019Q4 retry passed its full completion and cleanup checks with this explicit
clarification. Later quarters through 2020Q3 also passed; there is exactly one
reported intermediate quarter-cohort exception among these completed sources.

Synthetic tests verify strict rejection, audited intermediate preservation,
combination across partitions, rejection of a complete-cohort excess, and
rejection of unresolved event identity. Completion tests bind the clarification
hash and accounting evidence. The full canonical test suite after this change
and the calibration wrapper passed **1,388 tests, with 29 warnings**. Its log is
`tests-partial-cohort-and-calibration.log` under the private rebuild output.

## Downstream inputs checked without reopening originals

- The frozen official weekly mortgage-rate response has 466 finite observations
  and no duplicate dates. Its bytes match the saved source metadata. The floor
  calculation retains the within-month mean convention.
- The preserved historical Freddie panel and saved floor grid reproduce all
  **14 cells**, with the recorded count/exposure checks and 0.001 percentage-point
  CPR tolerance. The evidence is `legacy_floor_input_preflight.json`. This is a
  legacy-input replay; corrected calibration awaits all 20 quarters. The stricter
  numeric-input check also reproduced all 14 cells, recorded in
  `legacy_floor_input_preflight_v2.json`.
- The frozen macro file matches the earlier parameter-freeze hash. All 42 QT
  months from June 2022 through November 2025 contain finite required fields.
- The saved retrospective selection is 3.5% annual floor and 100 PSA in both
  candidate families. The selection period is 2023 and the previously examined
  evaluation period is January 2024–September 2025. These choices stay fixed.
- The recorded main pair uses 4.991% annual floor, 100 PSA, seed 42, and imported
  response 0 versus 6.5%. The generic configuration instead defaults to 4%, so
  an explicit, scoped override is required.
- Passing the full frozen macro frame to the existing simulation preserves its
  nearest-date initialization: May 31, 2022 holdings of $2,707.446 billion.
  Trimming the frame to QT first would select June holdings of $2,709.328 billion
  and would change the convention.
- The archived monthly empirical CSV agrees with independent saved monthly
  benchmark results. Its runoff is -$652.7517467773 billion, its targets total
  -$1,417.5 billion, and its gap is $764.7482532227 billion. Its current byte hash
  is recorded; the historical manifest did not contain a byte hash for this CSV.
  Cross-artifact agreement is not historical byte verification.
- Reuse the saved monthly runoff with the hazard module's existing scheduled
  principal convention. The archived ABM CPR uses a different amortization
  convention and cannot be substituted blindly, even though runoff and targets
  agree.

The complete local inventory and exact hashes are in
`downstream_input_inventory.json`. No new network data or paid source is used.

The actual saved model inputs also pass the new wrappers' standalone preflight:
the exact May initialization, all 42 monthly comparator values, the $764.7482532227
billion denominator, all 21 scoring rate months and recorded choices match.
The saved benchmark contains one extra month, December 2025. The wrapper selects
the declared QT window before numeric decoding and records that excluded month;
the extra reference value cannot extend the analysis. Evidence is saved in
`downstream_model_input_preflight.json`. No corrected model or scorer ran in
this preflight.

## 2020Q4 identity check and bounded repair

The strict schema audit stopped before outcome processing on one original ID
and 59 performance rows with a valid 2020Q3 prefix in the 2020Q4 pair. The loan
is otherwise eligible, with $197,000 original balance and 360-month original
term. All performance IDs have matching original records, all reporting dates
passed, and every source row has the expected 32 fields.

Separate origination-only scans verified the original Q4 hash and found zero
matches for this ID anywhere in the exact original Q3 file, including ineligible
records. Both diagnostic pairs passed cloud-only cleanup. The failed attempt
and private diagnostics are preserved in `quarters/2020Q4.attempt1/`.

The new `SPEC_2026-10-12_source_identity_clarification.md` permits one exact
allowlisted ID digest, in the same vintage year, with unchanged ID, balance,
cohort key and eligibility. The manifest binds both source hashes, the diagnostic
evidence, and exact original/performance counts and eligible original UPB.
The schema audit must rerun. The stream must match the same frozen accounting.
Unlisted, malformed, cross-year, unused or inconsistent exceptions fail. All
duplicate and cross-file overlap checks remain in place. Aggregate exception
accounting propagates to combination and every downstream result.

All 24 focused identity tests pass, including tampering, source/count mismatch,
unlisted and cross-year identities, strict-default behavior, exact original
principal retention, and compatibility with earlier strict completions.

## Prepared next stages and remaining limitations

`hazard/calibrate_freddie_rebuild.py` requires explicit input and new output
paths, validates all 20 quarter receipts and combined hashes, freezes provenance,
replays the saved grid first, and only then calculates the corrected grid. It
never selects a floor or updates production results. The new
`hazard/score_freddie_rebuild.py` and `hazard/simulate_freddie_rebuild.py` implement
the remaining offline stages with the same source gate and separate outputs.
The scorer preserves recorded candidates and advances a complete prediction
calendar even when an observed score row is invalid. The paired runner preserves
the full macro initialization, matched inputs and seeds, and original main-pair
parameters, with monthly cash and retained-claim reconciliation. Both accept
identical draws from sampling with replacement while rejecting conflicting
repeated IDs and mismatches against the combined sample counts.

Independent focused reviews found one calibration input bug: a saved NaN CPR
could bypass the historical difference check. The new wrapper rejects malformed
numeric cells before any panel outcomes are read; its 27 tests pass. The scorer's
16 and paired runner's 18 targeted tests pass. These synthetic checks establish
code behavior, not corrected empirical results.

Final combined verification for this checkpoint: the canonical `tests/` suite
passes **1,458 tests, with 29 warnings**; all 15 completed quarter manifests
validate with the current driver; and all **292 protected baseline files**
still match. The full test log is `tests-identity-and-downstream-full.log`.
Source and downstream execution remains serial and fails closed at any gate.

The ordinary rebuilt sample retains equal per-file oversampling. It is not the
older SOMA cell-targeted fresh draw. Original note rates and 360-month original
terms do not establish the current contractual terms of modified loans. The
balance increase above makes that distinction material; the source rebuild
does not resolve it by itself.

Native Fannie originals remain absent from the inspected locations. Corrected
Freddie inputs do not identify sale versus refinance payoffs, estimate a causal
moving response, create an untouched evaluation sample, or establish transport
to the entire SOMA portfolio. Those are substantive limits, not software checks
that can be declared passed.
