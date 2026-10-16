# Source field and state verification — October 13, 2026 UTC

**Later October 13 update:** the first rerun completed five quarters and exposed
an REO/assistance precedence defect in 2018Q2. Its five receipts remain preserved
version-1 evidence. The current repair and separate version-2 rerun are recorded
in `2026-10-13-reo-priority-repair.md`.

The five-stage pipeline was deliberately stopped at 02:31 UTC before any
combination, calibration, scoring or paired simulation. The 2020Q4 driver reaped
its worker and verified cloud-only cleanup of both original files. The previous
15 completion receipts still document the earlier code, bytes and accounting;
they do not resolve the newly identified field-meaning question below. Preserve
all of those artifacts and the interrupted attempt.

## Finding and bounded investigation

The January 2026 [Freddie General User Guide](https://www.freddiemac.com/research/pdf/user_guide.pdf)
places the last-paid-installment date at performance column 13 and borrower
assistance at column 30, using one-based numbering. The earlier parser omitted
the former and read assistance from column 29, although both layouts have 32 fields.
The guide also permits numeric delinquency values above nine and identifies
zero-balance codes 16 and 96 as termination events. The earlier state mappings
fell through to Current for those inputs. The first twelve fields, including
balance, age and voluntary-payoff code, have matching positions.

A synthetic fixture written independently of the parser reproduces seven
failing checks covering native forbearance placement, extended delinquency,
other terminal events and the last-paid-date layout. The bounded source probe
under `output/research-rebuild/2026-10-11/source-layout-diagnostic/` checked
the first million physical 2020Q4 records, decoding only 343,251 rows through
May 2022. At zero-based positions, field 28 contained 285 Y values and no F values; field 29 contained
285 F, 18 R and 9 T values. There were 56 delinquency values of ten or more
and 52 code-96 terminations. These agree with the native layout. Both full-file
hashes matched the saved schema hash. Cleanup passed for both pair paths.
This is a bounded diagnostic, not a whole-quarter prevalence estimate.

## Completed repairs and remaining execution

1. Finished the source-layout probe and verified both-file cleanup before changing code.
2. Reconciled the 32-field names with the observed native layout. Corrected both
   scalar and vectorized state mappings, retaining voluntary payoff only for code
   01 and representing codes 16/96 as other terminal transfers with no invented
   cash. Existing credit-event classifications are preserved.
3. Added semantic validation after applying the declared outcome cutoff. A row count or
   field count alone cannot establish the meaning of the assistance column.
4. Bound the declared layout/state version to quarter reports and downstream
   gates. A direct replay of an earlier completion with an unavailable source
   path confirmed rejection before raw access.
5. Focused regressions and the canonical suite passed. The fresh serial pipeline
   is prepared in a separate output root, preserving the old root. Its remaining
   work is all twenty corrected extractions, combination, calibration, scoring
   and paired simulation under the existing parameter choices. No manuscript
   result changes precede the audited chain.

The independent reviewer completed its bounded correctness, cutoff, provenance
and regression review with no actionable findings. Its initial pass was
interrupted by the account usage limit, then resumed and completed after the
repair commit. It reviewed native positions, snapshot tuple handling, downstream
version gates and non-voluntary terminal treatment without raw access or model
execution. The primary agent verified rejection of archived semantics, all 292
protected baseline hashes, all 259 prepared pipeline hashes and the copied
identity-exception evidence. The reviewer did not independently rerun the suite.
See the new root's `pipeline/review.json` and `pipeline/review_completed.json`.

Commit `f0c9ef28` binds the repaired implementation. The fresh pipeline launched
at 13:07:58 UTC on October 13 (9:07:58 a.m. Eastern), starting with 2017Q1.
Its live status is `pipeline/state.json`; each quarterly receipt remains required
before combination. Launch is not evidence that the corrected rebuild or any
dependent result is complete.

## Other work completed during the source run

The corrections and semantic gates pass **1,474 tests, with 29 warnings** in
the canonical suite. The focused tests cover native column placement, missing
layout versions, extended delinquency, terminal transfers without invented
payoff cash, invalid tokens, and the unchanged post-202509 outcome boundary.
New snapshots retain May current-contract fields alongside original inputs;
both note rates use decimal units. All 292 protected baseline files still match
their saved hashes. The fresh output root is
`output/research-rebuild/2026-10-13/`; no earlier completion receipt was copied.

The frozen 15-quarter snapshot audit covered 2,527,494 May-2022 rows before
global sampling. Reported current principal totaled $605.4749514593 billion.
52,199 rows (2.06525%) had current principal above reported original principal;
they held $15.00662155316 billion (2.47849% of snapshot principal). The excess
over their reported original principal totaled $599.26655316 million. Other
checks found no nonfinite/nonpositive balances, non-360 original terms,
negative/nonfinite ages, ages at or above original term, or wrong snapshot dates.
These describe the preserved subset produced by the earlier state mapping,
not a newly validated full-population model input.

The balance relationship is not a modification classification. Freddie rounds
original principal, and the guide distinguishes original terms from modified
current contracts. The model retains the observed balance without capping it
at original principal, but uses original note rate and term with reported age.
Current rate, remaining maturity, and non-interest-bearing principal are needed
for a separate current-contract assessment. No cause was inferred or loan
removed in the saved snapshot diagnostic.

Metadata-only connected-Drive discovery found the same forty named orig/perf
quarter files in the shared source folder. The bounded filename search located
no native Fannie acquisition/performance files. This does not establish absence
from differently named files, inaccessible locations or disconnected accounts.
The metadata evidence is `fannie_drive_metadata_check.json` under the old root.
