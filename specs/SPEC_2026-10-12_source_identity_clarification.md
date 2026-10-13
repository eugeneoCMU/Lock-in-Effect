# Audited same-year source-file identity exception

The 2020Q4 schema gate stopped before outcome processing: one original ID and
59 performance rows carried a valid F20Q3 prefix rather than F20Q4. All rows had
the expected 32 fields, all performance IDs existed in the origination file,
and all reporting dates passed. The original record is a known 360-month FRM,
with $197,000 original balance, 2.99% original rate, and December 2020 first
payment. The model's vintage is 2020 under either prefix. No ID is rewritten.

Origination-only diagnostics checked the exact hashed Q4 and Q3 originals.
The exceptional ID occurs once in Q4 and does not occur anywhere in Q3, including
ineligible records. All earlier completed files passed their own strict prefix
check. The two diagnostic source pairs passed verified cloud-only cleanup.
No diagnostic inspected performance outcomes. These observations establish
unique placement among completed sources; they do not explain the source's
file-placement choice.

The authorized rebuild may retain this record under a narrow frozen exception:

1. Store the exact ID's SHA-256, source quarter, both source hashes, expected
   original/performance exception counts, eligible count and original balance,
   and diagnostic evidence hashes in a separate local frozen manifest. Do not
   put an individual loan ID in committed code or prose.
2. Default identity checks remain strict. Only an exact allowlisted ID digest,
   otherwise valid Freddie ID syntax, with a different quarter in the SAME
   vintage year may use the exception. Other malformed, unknown, cross-year,
   or non-allowlisted mismatches remain errors. The allowlist must be exhausted
   by matching original records; unused or missing exceptions are errors.
3. Rerun the schema/ID/date audit. Its exception counts and original balance
   must match the frozen manifest and the outcome stream. Both source hashes
   must match the manifest before a completion can be sealed. Record the
   exception separately from zero-rate exclusions; retain all its source
   principal, history and outcomes within the existing cutoff.
4. Bind the frozen manifest and this clarification into execution and completion
   hashes. Propagate aggregate exception accounting to combination and each
   downstream stage. Preserve the failed attempt and both diagnostics.
5. Keep within-file duplicate checks, original-to-performance membership,
   chronological/group-reentry checks, outcome cutoff, and the final cross-file
   original-ID overlap gate unchanged. An overlapping original ID blocks the
   full rebuild; this exception never deduplicates a record or changes vintage.

The change corrects an overly strong file-prefix assumption for one evidenced
record. It does not change eligibility, cohort keys, denominators, parameters,
evaluation periods, or model interpretation. Later identity mismatches require
their own evidence; this is not a general relaxation of source validation.
