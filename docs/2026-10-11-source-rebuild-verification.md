# Corrected source-input rebuild, October 11, 2026

The rebuild starts from the implementation repairs in `dfd3370` and follows
`specs/SPEC_2026-10-11_source_rebuild.md`. The user authorized continuation of
the source rebuild. Existing fitted inputs, simulations, manuscript sources,
PDFs and archives remain preserved; this note does not announce a revised
headline estimate.

## Verified first quarter

Freddie 2017Q1 completed its strict schema, streaming reconstruction, independent
production comparison, immutable-source and cloud-cleanup checks. The saved
completion is verified from its full manifest, not inferred from a log or an
output filename.

- Original source: 290,601 origination rows and 16,516,599 performance rows.
- Corrected eligible population: 217,530 known 360-month fixed-rate loans with
  the specified valid FICO, LTV, original balance and note rate. This population
  differs from the older all-term panel.
- Outputs: 4,153 cohort-month cells, 40 full-source history cohorts, and 61,934
  active positive-balance loans observed exactly in May 2022.
- Adjacent identified transitions through May 2022: 9,379,312 usable pairs;
  three calendar-gap pairs excluded. There were no terminal-state reappearances.
- All eligible original loans had valid pre-cutoff and pre-snapshot histories.
  The stream found no duplicate loan-months, group re-entry, invalid balances
  or missing/nonfinite ages in this eligible quarter.
- The 109 first-observed voluntary payoffs used the inherited original-UPB
  fallback: $27.05 million, or approximately 0.0706% of this quarter's reconstructed
  voluntary payoff principal. No payoff used a nonadjacent prior balance.
  The fallback is an assumption, not observed preceding-month principal.
- The independent production implementation matched cohort membership and all
  ten checked numeric columns under the frozen relative/absolute tolerance.
  The largest absolute balance difference was $0.000153. Cohort mode-state tie
  breaking was excluded as a diagnostic; identified transitions do not use it.
- Before/streamed/after source SHA-256 hashes agree. Peak worker RSS was
  2,854,731,776 bytes, below the 8 GiB ceiling.
- Both originals remained uploaded and untrashed after FileManager eviction:
  `isDownloaded=0`, `isTrashed=0`, `isUploaded=1`, zero allocated bytes.

The first attempt failed on an offline configuration import before processing
outcomes and was safely cleaned up. Its directory remains preserved as
`quarters/2017Q1.attempt1`. The successful attempt's initial completion record
was retained before adding stronger manifest checks. Its exact executed code
was archived only after matching every saved code hash. Resealing used saved
evidence and did not reread cloud originals or change rebuilt artifacts.

## Rebuild safeguards and verification

`hazard/run_freddie_rebuild.py` processes the frozen 20-quarter Freddie manifest
serially. A quarter must finish and verify its cloud-only cleanup before the
next starts. Any failed gate stops the sequence. It retains a 12 GiB free-disk
reserve and an 8 GiB worker-memory limit. There is no bulk hydration, deletion
of cloud originals, purchase, external message or change to a published result.

Review found and repaired two driver defects before starting 2017Q2: a worker
that ignored termination could previously outlive source cleanup, and a resume
could previously accept an incomplete set of audit records. Termination now
escalates to kill and successful reaping before cleanup; inability to reap
prohibits eviction. Timeouts, monitoring failures and interruption are tested.
Completion requires the expected outputs, schema, source hashes, worker report,
resource evidence, source metadata, cleanup receipt, frozen protocol and exact
executed code. Before/streamed/after hashes, source identity, row counts,
population counts and cutoffs must agree. The first quarter also requires its
independent comparison. Tampering or missing evidence prevents resume.

The combiner requires all 20 verified quarters by default, rejects overlapping
original loan IDs (including terminated loans), sums fixed cohort denominators
once per source cohort, and attaches globally combined historical totals to
May survivors. It pools transition opening-balance totals before normalization.
Equal per-file oversampling remains an explicit inherited sampling assumption.

A synthetic two-quarter end-to-end check verifies an extinct cohort, a cohort
shared by quarters, exact May survivors, a later payoff excluded from May history,
balance conservation, pooled transitions and overlapping source rejection.
Review also reproduced nondeterministic sampling with a fixed seed. Stable
stratum and loan ordering now makes that draw reproducible without changing
stratum targets, replacement rules or sampling probabilities.

Verification after these changes:

- `python3 -m pytest tests -q`: **1,356 passed, 29 warnings**.
- An initial unscoped test discovery tried to import preserved package copies
  under `output/` and stopped with duplicate-module collection errors. The
  complete canonical `tests/` suite above passes; the archival copies were
  preserved.
- Independent review of the driver and combiner found no remaining blocking
  issue within the reviewed code paths. This is code review, not external
  empirical validation.
- All **292 protected baseline files** matched their recorded hashes.
- Whitespace/diff checks passed.

Detailed logs, raw-derived private artifacts, the baseline manifest, exact
execution records and completion receipts remain under ignored
`output/research-rebuild/2026-10-11/`. No loan identifiers belong in this note.

## Work continuing and limits

The serial job subsequently completed and verified all four 2017 quarters:
75,291,361 source performance rows, 1,089,540 eligible original loans, and
336,936 May-2022 survivors. Across those quarters, 663 first-observed payoffs
used $163.169 million of original-UPB fallback; no payoff used a nonadjacent
prior balance. These are quarter-source totals, not model effects.

The 2018Q1 strict schema audit then stopped on one otherwise eligible 360-month
loan with a zero original note rate. All field widths, IDs and dates passed.
An origination-only diagnostic confirmed the record and its $237,000 original
balance without inspecting performance outcomes. The failed attempt, source
hashes and verified cleanup remain preserved as `2018Q1.attempt1`.

The separately frozen
`specs/SPEC_2026-10-11_source_rebuild_zero_rate_clarification.md` implements the
already specified positive-note-rate restriction with explicit zero-rate
exclusion accounting. Both the schema gate and streamer must report identical
excluded counts and original balances, and completion requires the clarification
hash. No value is imputed; missing, nonfinite, negative and implausibly high
rates remain blocking errors. The strict standalone audit default is unchanged.
Regression tests verify that excluded-loan outcome fields are not decoded and
that the excluded principal cannot enter cohort denominators or snapshots.
All four earlier quarters had no invalid-rate records and remain valid.

After this clarification, the complete canonical test suite passed again:
**1,364 passed, 29 warnings**. Independent review of this clarification and
63 targeted synthetic tests found no concrete blocker. The 2018Q1 retry then
completed successfully: 239,706 eligible original loans, 13,873,084 source
performance rows and 68,872 exact May survivors. The schema and stream both
recorded the one $237,000 zero-rate exclusion. Before/streamed/after hashes
agree and both source files passed verified cloud-only cleanup.

The latest verified checkpoint is **five of 20 quarters complete** (2017Q1
through 2018Q1), totaling 89,164,445 source performance rows, 1,329,246 eligible
original loans and 405,808 May survivors. The serial job advanced to 2018Q2.
Its command invokes
`hazard/combine_freddie_rebuild.py` only after all 20 quarters succeed. Later
completion counts must be read from verified receipts; a running log is not a
completed quarter.

Fannie native originals remain unavailable in the inspected local and mounted
source locations. The existing API configuration could not resolve credentials,
so that access check stopped before a network request. The previously saved
Fannie aggregates cannot establish native-source provenance. The request for
another existing source or configuration path remains pending.

After source combination, applicable calibration, retrospective scoring and
dependent simulations still need separate audited outputs with a consistent
population. Existing floor, response, candidate-selection and evaluation
boundaries remain frozen. Source reconstruction alone does not identify sale
versus refinance payoffs, establish a causal moving response, create an untouched
evaluation period, or establish full-SOMA transport.
