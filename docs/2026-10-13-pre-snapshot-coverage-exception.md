# Source-bound pre-May history exception

The user explicitly approved: "Develop and audit that documented coverage exception."
The approval applies to the four already-diagnosed 2020Q4 loans, totaling
$1,487,000 in original principal. They have no valid performance record by May
2022; their first valid records are July (two) and August (two) 2022. Their
original first-payment months are November 2021 (one), December 2021 (two),
and March 2022 (one). Source hashes and aggregate patterns must match exactly.

## Treatment

- Preserve all eligible originals and their later observed panel outcomes.
- Exclude the four loans from the May starting portfolio; absence of valid May
  records means they cannot be assigned a known May balance or state.
- Their pre-May payoff history remains unknown, not a zero payoff observation.
- Remove their original balances only from the fixed denominator for known
  pre-May cohort history. That denominator, observed prepayments and known May
  survivors initialize the model's cohort burnout and denominator multiplier.
- Retain the full original-UPB denominator in the observed monthly panel. Its
  burnout variable is an observed-cash ratio, with unknown early cash explicitly
  qualified in the coverage audit.
- Report affected source-quarter and combined cohorts, known-history burnout,
  and full-cohort lower/upper cash-ratio scenarios. The upper scenario assumes
  each unknown loan's cumulative pre-May principal payoff is at most original
  principal. It is an assumption-dependent bound, not a guaranteed observed-cash
  bound. No missing payoff or borrower state is imputed.

## Gates and preservation

The exception is frozen before source access with the user's authorization,
completed read-only diagnostic, verified cloud cleanup, exact source hashes,
expected four-loan count, original principal and date distributions. Any mismatch
stops extraction. Missing pre-cutoff coverage and every other source/terminal/
identity/resource check stay strict. Quarter receipts validate the audit against
saved history denominators and verify unknown IDs did not enter the snapshot.
The audit travels into combined inputs and paired/scoring results.

A separate root `output/research-rebuild/2026-10-13-coverage` reuses the 15
unchanged completed quarters through symlinks to their archived receipts and
artifacts. The old failed 2020Q4 attempts remain intact. The source parser's native
layout/state semantics do not change; this is a separately frozen coverage policy.
The new pipeline freezes the revised code; it does not reuse the old code freeze.

Verification uses synthetic regressions plus the existing full test suite. The
actual affected-cohort audit is produced by the fresh 2020Q4 extraction. No new
portfolio estimate is claimed until all 20 quarters and downstream stages pass.

## Pre-run verification

The full suite passed: 1,518 tests, 29 warnings. Synthetic regressions verify
strict-default rejection, exact source/pattern binding, known-history denominator
removal, later-panel conservation, May exclusion, saved-history audit validation
and authorization tamper rejection. Independent static review found the bound
qualification issue; it was fixed and re-reviewed without a remaining finding.
All 15 real earlier receipts validate under the new verifier. All 292 protected
baseline files remain unchanged; all original source files were cloud-only before
preparing the new run. The new root contains a reuse manifest with the exact
completion hashes and frozen copies of the approval and diagnostic evidence.
