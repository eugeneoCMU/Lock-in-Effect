# Fannie SF LPH replication: first-download checklist

**STATUS 2026-07-15 (evening): the probe download happened (2019Q1, 341,865
loans / 11,583,612 rows) and every silent-corruption gate below was walked
against the real file. Items 1–5 are RESOLVED and the code updated; item 6 is
resolved-by-evidence pending the author's nod; items 7–10 remain author
decisions. End-to-end validation: the staged pair was consumed by an
UNMODIFIED `ingest.py` → 9,534 cohort-month cells, vintages 2017–2019 (pre-2017
seasoned tail auto-filtered by VINTAGE_YEARS), reporting 2019-01..2025-12,
implied average CPR ≈30% (plausible for 2018–19 coupons through the refi wave
and QT lock-in). Panel at `hazard/data/cohort_month_panel_fannie.parquet`.**

**STATUS 2026-07-16: COMPLETE. Author ratified; the pre-committed spec was
executed end-to-end (24 quarters, 17.6M loans) — see
`hazard/fannie_replication.py`, `hazard/data/fannie_replication_results.json`,
and TECHNICAL.md §24.2 (lock-in marginal +8.68pp, inside the pre-registered
envelope; license posture: code-only, headline statistics committed).**

Provenance: Fannie's published glossary (108 fields, 2023-06) + public FAQ +
the real 2019Q1 file itself. The ingestion layer: `common/fannie_key.py`,
`common/fannie_auth.py`, `common/fannie_lph.py`, `hazard/schema_fannie.py`,
`hazard/prepare_fannie.py`.

## Resolved against the real file (code updated accordingly)

1. **Delimiter: PIPE**, despite the `.csv` inner filename and the FAQ's "CSV
   format" wording. (Seller/Servicer names contain commas; comma parsing would
   have silently corrupted.) `DEFAULT_SEPARATOR = "|"`; the 113-column
   assertion remains the guard against any future format change.
2. **ZBC width: two-digit** (`01`,`02`,`03`,`06`,`09`,`15`,`16` observed), so
   `is_prepay == "01"` matches correctly. The all-zero-outcome catastrophe is
   ruled out. No `96`/`97`/`98` anywhere in the file (legacy gate holds).
3. **Six-month UPB privacy mask renders as `0.00`, not blank.** Left alone it
   would zero early-life exposure and, worse, credit a month-7 prepay at a
   masked-zero prev_upb. FIXED at staging: `_unmask_early_upb()` imputes
   `original_upb` where `current_upb == 0 & no ZBC & loan_age <= 6` (a genuine
   payoff carries its ZBC in the same month it zeroes — verified). Parameter
   `unmask_early_upb=True`.
4. **No post-removal ("zombie") rows.** Sampled removed loans end exactly at
   the ZBC month (UPB 0.00, zero rows after). The glossary's blank-after-
   removal language is CAS/CIRT reference-pool behavior, not SF LPH. Loan
   counts, Table-2-style disclosures, and prev_upb logic are all safe.
5. **Quarter semantics: acquisition quarter, with full performance history.**
   The 2019Q1 file carries originations 2012-10..2019-03 and reporting
   2019-01..2025-12 (Q4 2025 tail — the QT window is fully covered). Vintage
   is derived from Origination Date via the synthesized sequence number, and
   the existing VINTAGE_YEARS filter drops out-of-window originations
   automatically. **Coverage rule: to assemble the 2017–2021 origination
   universe, pull acquisition quarters ≈2017Q1 through 2022Q4** (acquisition
   lags origination by roughly 1–6 months, with a small seasoned tail).
   Also resolved: **113 physical columns** = the glossary's 108 (positions
   verified by value-distribution profiling: empty FRM-only ARM block 88–101,
   borrower assistance at 102 with the documented {7,F,N,T,R} set, etc.)
   plus 5 appended positions 109–113 (post-2023 additions; none consumed;
   named `appended_109..113` in `schema_fannie.FANNIE_COLS_WIRE`).

6. **ZBC 06/16/96 handling — resolved by evidence, author to ratify.**
   Full-file cross-tab of removals: 01 = 276,186 (99.4%); credit events
   02/03/09/15 = 620 with deep-delinquency status as expected; **06 = 459**
   (delinquency at removal mostly current/'XX' → rep-and-warranty pattern,
   not delinquency buyouts); **16 = 586** (all current at removal, as a
   reperforming sale implies); **96 = 0**. The censoring treatment stands, and
   the worst-case bracket (all 1,045 codes 06+16 counted as prepay vs censored)
   spans 0.38% of removals — negligible at the paper's reporting precision.
   State the treatment + bracket in the run-spec header.

## Still the author's call (unchanged)

7. **Secondary Markov mislabel (non-blocking).** `ingest.py` routes
   unrecognized ZBCs to "Current" in mode_state, so removed loans would appear
   as performing survivors in a Fannie delinquency-transition exhibit. The
   headline hazard is unaffected. Fixing needs an `ingest.py` change (adds
   explicit censor states); alternatively, don't report a Fannie transition
   matrix. Decide at write-up.
8. **Cross-agency LEVEL comparison caveat.** Whether Freddie's ZBC 01 absorbs
   exits Fannie codes 06/16 requires the Freddie data dictionary. Given item
   6's 0.38% scale the confound is small, but the defensible replication claim
   remains sign + floor/band-conditional marginal, not a hazard-level match.
9. **Field 82 (ZBC change date):** empty throughout this file (SF NA), so the
   revisable-exit concern is moot for SF LPH.
10. **License.** Fannie's Terms prohibit redistribution without written
    consent; analytics for internal purposes. Replication package ships CODE
    only — no Fannie data, conservatively no derived cells. Manuscript
    replication-package language must reflect this.

## Pre-committed run spec (write BEFORE the production run, per repo convention)
When the author green-lights: commit the spec (acquisition quarters 2017Q1–
2022Q4, ZBC treatment + 06/16 bracket, parity gate, expected artifact
`fannie_replication_results.json`) before executing. Suggested gate: the
Fannie lock-in marginal is positive and inside the floor/band envelope
reported for Freddie; state item 8's level-comparison caveat in the header.
