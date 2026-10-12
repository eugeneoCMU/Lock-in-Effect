# Explicit zero-note-rate exclusion in the source rebuild

This clarification is frozen after the failed 2018Q1 schema audit and before
processing any outcomes from that quarter. It implements the positive, valid
note-rate eligibility condition already stated in the original rebuild scope.
It does not alter the original frozen specification or completed quarters.

The strict schema gate found one otherwise eligible 360-month FRM origination
with a literal zero original note rate and $237,000 original UPB. A separate
origination-only diagnostic verified the exact source hash, confirmed all
296,816 records had the expected width, and inspected no performance outcomes.
The failed attempt and diagnostic remain preserved. Both source downloads were
safely evicted and verified before this clarification.

Rules for the resumed rebuild:

1. Only an explicitly enabled source-rebuild path may exclude a finite original
   note rate equal to zero from an otherwise eligible FRM population. The
   standalone strict audit default continues to reject it. Missing, nonfinite,
   negative or implausibly high rates remain blocking errors; no value is
   imputed from another record, a current performance rate or a fitted model.
2. Record the zero-rate exclusion count and original principal in the schema
   audit and streaming report, separately for all otherwise eligible FRMs and
   the target known-360-month population. Their count and balance must agree.
   All source IDs remain covered by schema, duplicate, chronology and overlap
   checks appropriate to their stage. Excluded loans contribute to neither
   cohort denominators, snapshots, payoff histories nor estimated transitions.
3. The unchanged source hashes and zero-rate original-UPB totals are evidence
   about omitted origination records, not their later payoff outcomes. Report
   this as incomplete information for those records and as an explicit
   positive-note-rate population restriction. Do not describe the excluded
   principal as a measured effect on the model result.
4. Archive and hash this clarification beside every newly executed quarter's
   original frozen specification and code. The first four quarters had zero
   invalid-rate records under the prior strict audit and remain valid without
   reconstruction. The combiner must retain the exclusions in its report.
5. Preserve the 2018Q1 failed attempt. Resume that quarter in a fresh attempt,
   rerun the schema gate under this declared rule, and require every existing
   source, cutoff, accounting, resource, comparison and cleanup check. Any
   other unresolved gate stops the sequence.

This is an outcome-blind eligibility clarification within the user's authorized
rebuild. No floor, response, tuning candidate, evaluation boundary or source
value changes. The original schema hashes are
`34f470619977957bc2abd97f844d102debf4bc683695e899c1956fddc93a1fdb`
(origination) and
`fefdc0bd2589322c2d5cb0de989747a37ce0b077c1065110e42df5fca2d6de6a`
(performance).
