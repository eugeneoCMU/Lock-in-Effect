# Audited continuation: October 10, 2026

This continuation completes the available Fannie age-only reconstruction,
one original Freddie quarter audit, and a revised publication. It does not
complete the twenty-quarter source rebuild or replace the headline simulations.
The October 9 frozen specifications retain their dates; the publication is
dated October 10 because work continued into that date.

## Results and manuscript disposition

The 24 preserved Fannie acquisition-quarter aggregates reproduce the legacy
23,443-row panel before correction. All 28 saved agency/grid readings pass their
replay checks. Count-weighted recombination changes 20,906 pooled mean ages,
preserving financial columns, keys, counts, and state modes. The selected
2017–2019 comparison changes 5.522% to 5.544%; its age-24 comparison changes
10.136% to 9.523%. Original payoff numerators remain unchanged and unaudited
against original Fannie histories. See `2026-10-10-fannie-age-rebuild.md`.

The original Freddie 2017Q1 pair passes schema and hash checks. On 16,513,080
eligible loan-months, both production replays match the independent reference
over 4,847 cohort-months within frozen tolerances. No ordering-induced payoff
discrepancy was detected in that replay. The 139 first-observed payoff records
retain $33.659 million of original-principal fallback; this is not measured
error. Both cloud files are unchanged and were verified evicted, uploaded,
and not trashed. See `2026-10-10-raw-2017Q1-audit.md`.

The paper's new Appendix D.A reports both exercises, distinguishes individual
simulation ages from pooled calibration ages, and preserves the original 4.991%
floor dependency. The $42.6084B saved and $42.1761B fresh paired results remain
legacy-floor conditional calculations. The prior 3.5%/100-PSA development
candidate is now reported alongside its adverse comparison: 17.7376% lower
monthly-rate RMSE than the original response-on prediction, still worse than
the simple 2023 cohort-speed comparator. Already-examined evaluation data are
not called an untouched holdout.

## Review and software verification

An independent lineage review checked which outputs depend on aggregate ages
and legacy payoff numerators. A separate manuscript review matched the new
Fannie, older-tail, and candidate numbers to their saved artifacts. Its two
wording fixes are incorporated: the legacy numerator's chronological alignment
awaits the full source audit, and 91.5353% floor binding refers specifically to
the original response-on leg. A further read-only audit independently reread
the Freddie reference and replay cells and found no serious numerical or
method error within this single-quarter scope. These are AI-assisted reviews,
not external peer review or causal-validation certification.

- Full suite: **1,240 passed, 26 warnings**, 27.06 seconds, with ignored
  historical output directories excluded from test discovery.
- Nine new audit tests cover financial conservation, membership changes,
  support parity, malformed schemas, duplicate IDs/months, group re-entry,
  cutoff-before-outcome conversion, missing months, and chronological lags.
- LaTeX source, citations, environment nesting, table columns and math checks
  pass. Both active wrappers have 43 labels and 35 semantic references, with
  no reference errors. Publication claim and historical liveness gates pass.
- Tectonic 0.15 compiled both editions. Its existing bibliography-change
  detection warning recurs; the generated bibliography, extracted references,
  rendered text and repeat-build comparisons are the relevant output checks.
- Combined PDF: **35 pages**. Banner-based split: **22 main/reference pages**
  plus **13 appendix pages**. Render gates report zero off-page items,
  zero spans beyond the sheet, and zero unresolved references in all four PDFs.
- Every final page was rendered and visually inspected. The long abstract's
  first page was inspected separately; pages 2–35 have identical extracted
  body text in both editions. The first-page abstracts intentionally differ.
- The source ZIP passes its archive integrity and per-file hash checks. An
  independent extraction rebuilt the 35-page standard paper with identical
  text and identical rendered pixels at 72 dpi on every page. Licensed raw and
  loan-level files are excluded; this verifies document reproduction only.

## Preservation and provenance

Before work, 265 existing manuscript/data/publication paths were hashed in
`output/research-limits/2026-10-09/rebuild/baseline_manifest.json` at commit
`6f4fa2f0c9a34cafcab3d9dc642704ccd9a7c92c`. Only the six intended active
manuscript source files changed within that baseline. Existing hazard/ABM data,
the four October 8 PDFs, and the October 8 source archive match their hashes.
The new appendix input, audit drivers, tests, reports, and aggregate results
are additional files. Original Fannie source inputs also pass their own
post-run hash checks.

After resuming, an audit agent briefly reran the earlier older-tail diagnostic
before receiving the updated scope. Its ignored local diagnostics/timestamps
were refreshed; aggregate findings were unchanged. No production input or old
publication changed. The continuation therefore does not claim every ignored
working diagnostic remained byte-identical.

The Freddie first access attempt timed out before reading records. It is
preserved separately; restarting the existing Drive app and requesting the
same pair resolved it. No further quarter was downloaded. The read-only raw
bytes were rehashed before FileManager eviction, then File Provider reported
`isDownloaded=0`, `isTrashed=0`, `isUploaded=1` for both exact paths. Compact
evidence remains locally; original cloud files were not deleted.

## What remains

1. Audit and rebuild the remaining nineteen Freddie acquisition quarters,
   sequentially, and reconcile membership across files. Define and report an
   opening risk set separately from the historical end-balance floor reading,
   with explicit treatment of first-observed payoff events and gaps.
2. Rebuild the calibration, dependent prediction scores, transitions as needed,
   and paired simulations from audited inputs before presenting corrected
   headline results. Original Fannie payoff histories also remain unaudited.
3. Obtain genuinely additional evaluation outcomes under the frozen future
   evaluation protocol. Do not select a new principal model on the already-seen
   January 2024–September 2025 observations.
4. Sale-specific payoff labels, older collateral support and broader SOMA
   representation remain empirical data requirements. This pass supplies none
   of the missing causal identification or population mapping.

The saved build/check logs and rendered pages are under
`output/paper-improvement/2026-10-10/`. No remote push, publication, purchase,
external data inquiry or message was performed.
