# Original Freddie source inventory — October 9, 2026

**The original Freddie files are available as Drive placeholders, but none of
the documented original origination/performance pairs are materialized locally.**
An audited monthly-history rebuild therefore needs a controlled one-quarter
retrieval. The local survivor snapshots cannot replace those histories.

This inventory used repository documentation, source code, small existing
provenance records, directory listings, and file metadata. It did not open,
hash, hydrate, copy, or delete cloud file contents; it did not inspect any
Freddie outcome after September 2025. Cloud file sizes are nominal sizes, not
locally allocated storage. No credentials or credential files were read.

## Source locations and availability

The mounted original-source directory is:

```text
/Users/eugene/Library/CloudStorage/GoogleDrive-eugeneo@andrew.cmu.edu/My Drive/Fannie and Freddie MAC
```

It contains exactly 40 files: `orig_YYYYQn.txt` and `perf_YYYYQn.txt` for
every quarter from **2017Q1 through 2021Q4**. There are no older vintages,
annual ZIPs, sample CSVs, or additional subdirectories in this folder. All
40 files have **zero allocated bytes** and macOS flags `0x40000060`;
`ls -lO` independently reports `compressed,dataless` for the proposed
verification pair. Total nominal size is **50,911,518,184 bytes (50.91 GB)**.
Their modification timestamps are July 3, 2026; timestamps do not establish
the vendor release, schema version, or last performance month.

| Origination quarter | Origination bytes | Performance bytes |
|---|---:|---:|
| 2017Q1 | 44,424,387 | 1,420,624,291 |
| 2017Q2 | 51,784,519 | 1,576,194,688 |
| 2017Q3 | 60,109,781 | 1,836,093,781 |
| 2017Q4 | 55,599,555 | 1,650,681,286 |
| 2018Q1 | 45,818,775 | 1,195,849,149 |
| 2018Q2 | 56,385,583 | 1,272,938,675 |
| 2018Q3 | 51,876,273 | 1,095,821,236 |
| 2018Q4 | 44,281,753 | 845,068,423 |
| 2019Q1 | 43,390,656 | 818,938,209 |
| 2019Q2 | 64,298,973 | 1,252,120,089 |
| 2019Q3 | 84,261,703 | 1,818,934,352 |
| 2019Q4 | 84,245,463 | 1,845,787,123 |
| 2020Q1 | 80,244,383 | 1,798,117,419 |
| 2020Q2 | 138,044,487 | 3,691,230,719 |
| 2020Q3 | 179,496,371 | 5,111,518,956 |
| 2020Q4 | 194,780,352 | 5,546,732,030 |
| 2021Q1 | 185,912,216 | 5,126,070,841 |
| 2021Q2 | 148,246,044 | 3,877,260,920 |
| 2021Q3 | 160,563,885 | 4,042,726,358 |
| 2021Q4 | 133,860,628 | 3,181,183,852 |

The repository-local inventory found:

- Primary checkout
  `/Users/eugene/somthing/Lock In effect/Lock-in-Effect`:
  `Historic Freddie/` contains only `.DS_Store`; `hazard/data/raw/` contains
  only `.DS_Store` and an empty `fannie/` directory; `data/cache/` is empty.
- Worktree `/Users/eugene/.codex/worktrees/6930/Lock-in-Effect`:
  `hazard/data/raw/` and `hazard/data/soma_raw_temp/` are empty. Its
  `hazard/data/soma_stream_quarters/` contains 20 materialized Parquet files
  named `2017Q1.parquet` through `2021Q4.parquet`.
- Current f586 worktree: no `Historic Freddie/`, `hazard/data/raw/`, or
  `data/cache/` directory. The c470, 6930, f586, and primary checkouts contain
  derived Freddie result CSVs, but the bounded filename inventory found no
  original `orig_*`, `perf_*`, `historical_data_*`, `sample_orig*`, or
  `sample_svcg*` text/ZIP files and no Freddie/sample CSV containing original
  histories. This is a statement about the inspected project locations,
  not a claim that no other copy exists anywhere on the computer.
- The primary checkout's materialized `hazard/data/loan_sample.parquet`
  is 1,355,744 bytes. `hazard/loan_sample.py` constructs it from one latest
  pre-QT observation per loan. It is a model sample, not monthly histories.
  The saved Fannie quarterly aggregates are a different agency and also
  cannot reconstruct individual Freddie histories.

## What the existing lineage can establish

`hazard/soma_stream_snapshot.py` reads each original pair and retains one
May-2022 positive-balance survivor record per eligible 360-month fixed-rate
loan. Its 20 saved quarter snapshots establish useful pre-QT composition;
they omit earlier and later monthly paths and terminated loans. They cannot
reconstruct voluntary-payoff risk sets or a 2018 turnover rate.

`hazard/data/soma_fresh_audit.json` records SHA-256 hashes and row counts
for all 20 **derived snapshots**. It does not provide a raw-file checksum
manifest, vendor-release identifier, verified wire-column count, or maximum
performance date for the 40 originals. The October 6 rerun plan says those
original local downloads were evicted after processing. Current dataless
metadata corroborates their present local-storage status.

`hazard/prepare_freddie.py` documents the original annual archive layout:

```text
historical_data_YYYY.zip
  historical_data_YYYYQn.zip
    historical_data_YYYYQn.txt       -> orig_YYYYQn.txt
    historical_data_time_YYYYQn.txt  -> perf_YYYYQn.txt
```

No such annual archives remain in the documented primary `Historic Freddie`
directory. The cloud pairs already use the prepared names.

`hazard/schema.py` declares **32 pipe-delimited, headerless fields** for
both origination and performance. Relevant zero-based positions are:
origination loan ID 19, note rate 12, original balance 10, fixed-rate flag 15,
term 21; performance loan ID 0, report month 1, current balance 2, loan age 4,
zero-balance code 8, assistance 28. These are the repository's expected
layout, **not a verification of the unopened cloud files**. The actual
source release/schema remains unverified. `ingest.py` currently uses
`truncate_ragged_lines=True`, so a rebuild must add an independent strict
wire-width/field-position gate before trusting the existing parser.

`common/data_loader.py` supports prepared pairs through Drive/cache lookup.
Its year-based fallback tries an annual suffix and Q1; it does not enumerate
Q2–Q4 automatically. An audited full-frame rebuild should therefore use an
explicit quarter manifest and must not infer 20-quarter completeness from
this fallback. No loader/authentication/download function was called for
this inventory.

## Smallest practical verification pass

1. Use **2019Q1**, the smallest available pair: `orig_2019Q1.txt` plus
   `perf_2019Q1.txt`, totaling **862,328,865 bytes (0.862 GB)**. Retrieve only
   that pair when the controlled retrieval step is authorized; preserve the
   Drive originals. This quarter tests ingestion and event accounting, but
   it cannot assess support in 2018. If the first check must cover the 2018
   anchor, choose **2017Q1**, totaling **1,465,048,678 bytes (1.465 GB)**.
2. Before outcomes are examined, freeze the parser and strict schema checks,
   source manifest, relevant loan eligibility, event codes, and monthly
   beginning-balance rule. Record raw-byte hashes after retrieval and confirm
   row widths, duplicate loan-months, loan-ID joins, and date coverage. Read
   the reporting-month field first and reject rows later than **202509**
   before outcome extraction, aggregation, or diagnostic scoring. A newer
   vendor layout must pass schema-only tests rather than silent truncation.
3. Preserve all eligible pre-cutoff paths and competing terminations. Produce
   a quarter-level audit of opening UPB, scheduled principal, voluntary-event
   prior balances, censoring/missing histories, and cohort aggregation. The
   existing May-2022 snapshot is a composition checkpoint, not proof that the
   monthly histories or payoff denominators match.
4. Reconcile the compact rebuilt output and provenance, then use the approved
   Drive **Remove Download** mechanism to evict that local pair. Do not delete
   the Drive files or bulk-sync the folder. Proceed to another quarter only
   after the first pair passes.

Earlier Freddie origination vintages remain a separate source-access need:
there are no pre-2017 originals in this folder. None of the identified local
artifacts can fill that older-vintage gap. This inventory leaves cloud
hydration, source-content verification, monthly-history reconstruction, and
any manuscript/model change undone.
