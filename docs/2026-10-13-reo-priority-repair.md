# REO precedence correction — October 13, 2026

The first corrected-layout run completed 2017Q1–2018Q1, then stopped safely in
2018Q2 on one apparent terminal revival. Those five version-1 receipts cover
1,329,246 eligible original loans, 89,164,445 source performance rows and 405,808
exact May-2022 snapshot rows. Their hashes and cleanup receipts still validate;
they are preserved historical outputs, not inputs to the version-2 model chain.

## Source evidence and cause

A protocol frozen before renewed raw access authorized only the exact 2018Q2
pair, the same eligibility and outcomes through May 2022. Both source hashes
matched before and after the diagnostic. It examined 14,749,218 physical records,
decoded 9,641,642 eligible pre-QT records, skipped later dates before outcome
decoding and reproduced exactly one offending edge. Peak RSS was about 204 MiB.
Both files passed cloud-only cleanup with no deletion.

The matching loan retained reported REO-acquisition status from July 2020 through
its May 2021 code-09 disposition. A September 2020 forbearance flag overrode that
status in the parser despite unchanged principal of $207,280.17. The source did
not report a cure of the REO status. The [Freddie guide](https://www.freddiemac.com/research/pdf/user_guide.pdf)
defines RA as REO acquisition and F as borrower assistance; the parser's order
created the artificial Defaulted-to-Forbearance transition.

The private diagnostic, with hashed identifiers, is under
`output/research-rebuild/2026-10-13/quarters/2018Q2/terminal-diagnostic/`.

## Repair and verification

Version `freddie-native32-reo-priority-v2` retains explicit zero-balance-code
precedence, then evaluates RA before F in both scalar and vector paths. Numeric
delinquency plus F retains its existing forbearance treatment. The stream counts
joint RA/F rows after the eligible-loan and date filters. No source exception,
balance adjustment, invented payoff or weakening of terminal absorption was
introduced. Unsupported nonterminal RP now stops native extraction, including
when F is present; the current guide does not establish a native RP meaning.

Five focused regression failures reproduced the missing behavior before repair.
The completed canonical suite passes **1,488 tests with 29 warnings**. An
independent read-only review found no actionable correctness or provenance
issue. Version-1 receipts remain verifiable, while current resume and downstream
consumption require version 2. Actual saved version-1 receipts validate and a
resume attempt with an unavailable raw-source path is rejected before access.

## Required fresh extraction

The first five quarters have no saved joint RA/F accounting proving they were
unaffected. A history beginning with both flags could be misclassified without
triggering a revival. Re-extract all twenty quarters into
`output/research-rebuild/2026-10-13-reo/`, copying no earlier source completions.
Preserve both earlier roots and the failed 2018Q2 attempt.

The five-stage sequence remains source extraction, combination, calibration,
retrospective scoring and paired simulation. Each stage stops on a failed gate.
The 202509 outcome boundary, 202205 transition/snapshot boundaries, one-pair
resource and cleanup controls, fixed model choices and empirical limitations
remain unchanged. No replacement paper estimate is available from this repair.
