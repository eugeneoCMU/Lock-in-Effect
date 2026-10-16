# Research implementation repairs, completed October 11, 2026

The user's October 10 instruction to fix the four reported implementation
defects is complete. This is a code and rebuild-contract repair, not an
empirical re-estimation. The baseline is commit
`c1f893a12605c57a8b6e53f68620bb6c8e4e9bf4`. Existing source data, fitted inputs,
simulations, manuscript files, October 10 PDFs, and the source archive were
preserved. No additional raw quarter was downloaded or read in this pass.

## What changed

### Fixed original cohort balances and historical initialization

New ingestion stores `cohort_original_upb` as the original balance of the
eligible source cohort, using vintage, coupon bucket, FICO bucket, and LTV
bucket. Cumulative voluntary payoff principal uses that fixed denominator.
Paid-off loans disappearing from subsequent reports no longer shrink it.
New quarter aggregates also retain finite-age sums and counts, so recombination
handles partially missing ages exactly instead of weighting a partial mean by
every loan in a cell.

Ingestion rejects duplicate loan-months, overlapping origination sources,
missing performance coverage for eligible original loans, and invalid fixed
history. Old quarter cells cannot reconstruct the missing denominator; their
age-only replay requires explicit `allow_legacy_cells=True`.

Fresh snapshots retain reported original loan terms, the exact pre-QT reporting
month (May 2022), active positive balances, and full-source historical cohort
totals. They exclude stale earlier observations and terminated loans. Source
histories combine across quarters before being attached to sampled survivors.
The denominator multiplier represents the full source cohort relative to the
original balance of its surviving loans. The simulation initializes historical
burnout from these fields, and rescales that fixed denominator with balances.

Fannie quarter pool pieces now have accompanying history and source-ID files.
An entirely paid-off quarter still contributes history to a cohort surviving
in another quarter. Finalization checks all eligible IDs, including unsampled
and terminated loans, for overlapping sources. It rejects missing, mixed,
duplicated, nonfinite, or inconsistent history metadata before writing a sample.
Missing history in one source cannot be hidden by a different source with the
same cohort. Old pieces require explicit legacy replay.

Corrected cohort predictions use the same fixed-denominator contract and reject
invalid initial shares rather than clipping them. The two frozen retrospective
prediction drivers explicitly retain their recorded legacy convention. They
were not rerun and their saved parameter selections/results were not changed.

### Payoff cash and monthly state timing

A delinquency transition into Prepaid now records its remaining principal as
cash, zeros the balance, and updates voluntary payoff history exactly once.
Binary prepayment records principal before zeroing the balance. Fractional
prepayment followed by a terminal payoff counts the borrower only once.

A loan newly entering delinquency waits until the next monthly step for a
delinquency-state transition. Reordering transition-matrix columns does not
change the destination states. Invalid probability arrays are rejected.
Legacy all-zero unsupported rows remain permitted by the low-level simulator;
the new estimator supplies explicit self-loops for unsupported rows.

### Contractual terms and maturity

The sample carries `original_loan_term`, and amortization uses each loan's
reported original term. Both Danish calibration branches also receive that term.
Remaining principal at or beyond the modeled maturity closes as scheduled
principal before voluntary/default hazards are applied. Maturity cash does not
increase voluntary payoff history. The last scheduled installment closes the
remaining balance.

Legacy samples with no term/history fields remain usable through explicit
legacy entry points, with assumptions recorded on the pool. Corrected production
runs require valid known fields. New default sample builds restrict to known
360-month loans; callers constructing another population must specify it and
use the same population for panel estimation/calibration. Original terms do not
identify subsequent contractual extensions or modification schedules.

### Identified loan transitions and input cutoffs

The new transition estimator uses consecutive calendar-month observations for
the same loan. Its default weights are opening balances; loan-count weights
are an explicit alternative. It excludes gaps, validates actual loan-month
uniqueness independently of table row labels, and rejects reappearance as an
active loan after a terminal state, including across a reporting gap.

An explicit estimation cutoff filters outcomes before state/balance conversion.
Unsupported transition rows retain their state, with diagnostics exposing the
lack of observations; no transition probabilities are invented from cohort
modes or unsupported literature priors. Cohort-mode estimation requires an
explicit legacy option. Estimator identity and cutoff metadata survive the
matrix's Parquet storage path.

The corrected microsimulation entry point checks the exact pre-QT snapshot,
known terms/history, and a supplied identified-loan matrix with an estimation
cutoff before QT. It rejects an old cached cohort-proxy matrix or later outcomes
by default. Corrected sample and simulation writes require new output paths;
forcing a rebuild does not delete the frozen sample. These are structural
validation checks, not independent certification of source provenance.

## Verification

- Full repository suite: **1,307 passed, 29 warnings**. The added legacy-replay
  warnings are intentional; the remaining warning classes are the existing
  Python/library and synthetic-estimator warnings.
- Targeted regressions first reproduced the reported failures. Additional
  review found and fixed duplicate borrower counts, repeated table-index
  labels, term propagation, partial missing source histories, cutoff wiring,
  and malformed Fannie history files.
- A synthetic two-month corrected run used a rebuilt snapshot and an identified
  transition matrix loaded back from disk. Its outputs were finite, scheduled
  principal was positive, and a repeated write could not overwrite its output.
- Financial tests force terminal payoffs, binary/fractional branches, maturity
  boundaries, mixed terms, reordered transition columns, and monthly state
  timing. History tests cover disappearing loans, fully terminated source
  quarters, unequal partitions, partial missing ages, duplicate/overlapping
  inputs, strict versus legacy prediction, and ignored post-cutoff outcomes.
- Whitespace/diff checks pass. The four original repairs and the Fannie
  integration received separate AI-assisted code reviews. Findings were
  incorporated and verified; these reviews are not external peer review.
- A SHA-256 comparison checked **438 baseline files**. The **236 protected
  data, manuscript, PDF, and source-archive files** were all unchanged; none
  were missing. Only the intended implementation and test paths changed in
  that baseline. Paper compilation was not repeated because paper sources
  and delivered PDFs were unchanged.

Detailed logs and the preservation manifest are retained in the ignored local
directory `output/research-repairs/2026-10-10/`, where work began. The final
suite is `full-suite-final.log`; preservation evidence is
`preservation_check.json` and `baseline_manifest.json`. The committed regression
tests are the portable verification evidence.

## What this does not finish

The existing empirical estimates are still historical calculations from their
recorded inputs. No numerical effect on the headline result has been estimated
in this repair pass. In particular, the cached delinquency matrix had zero
delinquency-to-Prepaid probabilities in the prior audit; reproducing a possible
accounting defect does not establish that it changed those cached dollars.

Before any revised headline estimate, the remaining source quarters must be
audited/rebuilt, the Fannie original payoff numerators must be audited, and
cohort panels, snapshots, transitions, calibration, and dependent simulations
must be regenerated under one consistent population and cutoff specification.
The first-observed payoff convention still uses original principal when no
prior observed balance exists; new snapshot histories expose those counts,
and gap-payoff counts, for review. Those counts are repeated cohort metadata
on sampled rows and must not be summed over sample rows as event totals.
They do not resolve missing prior balances or imply audit completion.

Equal per-file oversampling and transport to the SOMA book remain sampling/model
assumptions. Loan-ID uniqueness in separately built panel aggregates still
requires the source audit/manifest; aggregate cells alone do not contain IDs.
None of these software repairs supplies sale-versus-refinance labels, establishes
the moving response causally, adds an untouched evaluation period, or validates
full-population coverage. The previously examined evaluation data remain
retrospective evidence.
