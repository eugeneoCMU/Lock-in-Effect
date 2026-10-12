# Corrected source-input rebuild — October 11, 2026

Authorization: the user asked to "continue with the rebuild" after the four
implementation repairs were completed as dfd3370. This extends the prior
one-quarter pilot to the available sources. Preserve that pilot, all existing
data/results, and the October 10 paper/PDF/archive. Use the active f586 worktree.

## Frozen scope and choices

1. Rebuild Freddie 2017Q1–2021Q4 in explicit chronological quarter order from
   the 40 mounted Drive originals already inventoried. Process one pair at a
   time, never bulk-download or copy whole raw files. Keep at least 12 GiB free
   and stop a processing worker above 8 GiB RSS. No purchase or external message.
2. Inspect file metadata and freeze this specification before opening source
   contents. Complete a strict 32-field schema/ID/date gate and record source
   hashes before processing outcomes. Read reporting month before interpreting
   outcomes; skip all observations after 202509. Do not inspect an untouched
   later evaluation window or select parameters using new outcomes.
3. The corrected population is known 360-month fixed-rate loans with the
   existing valid FICO (300–850), original LTV (1–200), positive original UPB,
   valid note rate, and source-quarter IDs. Record excluded term composition
   in the schema gate. This differs from the old all-term panel; do not label
   a population change as solely a software correction.
4. Stream contiguous per-loan histories, sorting within each loan by month.
   Reject duplicate loan-months, ID group re-entry, missing eligible-source
   histories, or schema/source ambiguity. Retain and quantify chronological
   original-UPB fallback for first-observed voluntary payoffs, and payoffs with
   a nonadjacent prior. These are explicit inherited assumptions, not measured
   preceding principal. Do not silently drop or impute away a failed audit.
5. Produce compact corrected cohort cells with fixed original denominators,
   finite-age sums/counts, and explicit opening-risk diagnostics; raw exact
   May-2022 active snapshots; full-source pre-QT cohort history; private eligible
   source IDs; and adjacent opening-balance/count transition totals through
   202205 only. Validate the streaming path against production logic on
   synthetic histories and the first real quarter where resource headroom
   allows. Report any unavailable full-join comparison explicitly.
6. Retain sufficient statistics from all quarters, including cohorts with no
   surviving May-2022 loans. Check cross-file source IDs before global
   combination. Rebuild the sample and identified transition matrix only after
   all 20 quarters pass. Do not manufacture missing source history from saved
   survivor samples or old aggregate cells.
7. Rehash the exact source pair after processing, verify compact output hashes,
   and use FileManager eviction (Remove Download), never deletion. Confirm
   isDownloaded=0, isTrashed=0, isUploaded=1 and zero allocated bytes before
   accessing another quarter. Record error evidence and perform the same safe
   cleanup if processing fails. An unresolved gate halts the sequence.
8. Locate Fannie originals using metadata first. Apply a separately frozen
   native schema/cutoff mapping before a Fannie original-source rebuild. Old
   quarter aggregates remain an age-only reconstruction, not original-source
   validation. Lack of native sources is reported as an access limitation.

## Output and interpretation

All raw-derived quarter files, source identifiers, snapshots, and detailed
audits stay local under ignored output/research-rebuild/2026-10-11/. Version
code, tests, the protocol, and aggregate verification notes only. Save input,
code, environment and output hashes with each quarter; preserve earlier
attempt directories. A resume uses verified completion records, not the mere
existence of an output file.

This pass establishes corrected inputs and source accounting. Calibration and
dependent simulation reruns use separate outputs and require all applicable
input gates. Preserve the existing floor grid, imported response and candidate
selection; report adverse findings and population changes without tuning.
Do not replace published estimates until the full dependent chain is audited.
Source reconstruction alone does not identify sale payoffs, the moving response,
or full-SOMA transport.

## Execution ledger

- Initial state: dfd3370, clean working tree; 34 GiB free; all 40 Freddie source
  files present as dataless Drive placeholders; Google Drive process active.
- No source content opened before this specification was written and hashed.
