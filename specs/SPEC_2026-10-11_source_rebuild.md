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

## October 13 source-semantics correction and separate rerun

The original October 11 freeze remains preserved in its output root. A bounded
October 13 diagnostic on the exact 2020Q4 performance hash confirmed the
January-2026 native layout: zero-based field 12 is last-paid-installment date,
28 is disaster, 29 is borrower assistance, and 31 is interest-bearing UPB.
The first 1,000,000 physical records contained 343,251 rows through 202205;
the assistance column had 285 F, 18 R and 9 T values. Column 28 instead had
285 Y values. There were also 56 delinquency values of ten or more and 52
zero-balance-96 events. These are diagnostic-subset counts, not population
prevalences. Both full-file hashes matched and source cleanup was verified.

For the separate rerun, use source semantics version
`freddie-native32-ddlpi-states-v1`. Record it in quarter and combined reports;
downstream gates must reject earlier semantics. All numeric delinquency values
of at least three map to D90+. Codes 16 and 96 map to the existing Liquidated
terminal state and generate no voluntary or recovery cash. Keep existing
01 payoff and 02/03/09/15 credit classifications. Validate last-paid-date,
disaster, assistance, zero-balance and delinquency tokens only after the
202509/eligibility boundary; unresolved nonterminal unknown states block.

Retain additional contemporaneous fields in the exact-May snapshot: current
note rate, remaining months, modification and payment-deferral flags,
non-interest-bearing UPB and interest-bearing UPB. Preserve missing values.
These fields are audit evidence only: the queued model continues to use its
recorded original-rate/original-term convention until a separately specified
current-contract comparison is completed. Do not silently replace coupons,
terms, balances, eligibility, parameters or the fixed cohort denominator.

Run all quarters into a new output root. No previous state-dependent source
artifact may be relabeled or copied as a new completion. Prior financial
aggregates remain preserved for reconciliation. Keep every earlier resource,
cutoff, identity, zero-rate and intermediate-cash-ratio requirement.

## October 13 REO and assistance precedence correction

The v1 rerun completed five quarters, then stopped in 2018Q2 on one apparent
terminal revival. A separately frozen diagnostic verified the exact source
hashes and decoded only eligible records through 202205. The loan remained RA
(REO acquisition) from July 2020 through its May 2021 code-09 disposition. A
September 2020 F assistance flag overrode RA in the old state mapping, despite
unchanged reported principal. This is a parser precedence defect; no source
exception or weakening of the terminal-absorption gate is warranted.

For a fresh full rerun use `freddie-native32-reo-priority-v2`: explicit zero-
balance codes remain first; RA maps to Defaulted before assistance F maps to
Forbearance. Numeric delinquency plus F keeps its prior treatment. Count the
joint RA/F source rows. Nonterminal RP is unsupported by the native guide and
must fail semantic validation, with or without assistance; do not assume a
meaning from a legacy mapping. Keep the existing rule allowing explicit known
termination codes to determine a terminal state when delinquency is unresolved.

Preserve v1 receipts and their exact bytes as verifiable historical evidence.
They cannot feed a current model. The earlier five quarters have no joint RA/F
audit establishing that their outputs are unaffected, so re-extract all twenty
quarters into `output/research-rebuild/2026-10-13-reo/`. Copy no completed source
artifacts. Retain all source/resource/cutoff/cleanup requirements and the same
fixed downstream choices. The original and v1 frozen specifications remain
unchanged in their respective output roots.
