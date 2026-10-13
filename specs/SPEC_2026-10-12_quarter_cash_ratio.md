# Quarter-file payoff principal versus the complete vintage cohort

The 2019Q4 rebuild stopped before publication because one quarter-file cohort
had $223,864.25 assigned voluntary payoff principal against $196,000 reported
original UPB. A read-only diagnostic reran unchanged production calculations,
verified both source hashes, and safely evicted the sources. This was a single
loan, a single positive payoff in June 2024 using the adjacent May balance,
with no duplicate loan-month, repeated positive payoff or terminal revival.
Its reported balance had increased; it was not a floating-point discrepancy.
The diagnostic does not establish which accounting component caused that rise.

The model cohort key is origination year, coupon bucket, FICO bucket and LTV
bucket. A quarter file is only a partition of that cohort. Existing verified
2019Q1–Q3 sources contribute $5,106,000 original balance and $3,969,484.79
payoff principal to the same key. Including Q4 gives $5,302,000 original and
$4,193,349.04 payoff principal through September 2025, below the complete-cohort
bound. No source principal or denominator needs to be altered.

This clarification authorizes only the following bounded implementation:

1. An explicitly enabled, separately frozen quarterly extraction may retain a
   monthly cash/original-balance ratio above one as an intermediate source
   statistic. Preserve its numerator and denominator exactly; do not clip,
   impute, omit the cohort or change the model's cohort definition.
2. Record every such quarter-cohort's first crossing month, peak principal
   ratio, original balance, cumulative payoff principal, loan count, and
   counts/balances of individual above-original payoffs. A cohort with multiple
   positive payoffs for a loan or a terminal-to-active reappearance through
   the outcome cutoff cannot use this exception. Unresolved event identity
   still stops extraction. Strict standalone extraction remains the default.
3. All completed quarter partitions must be combined before constructing the
   final panel. Keep the existing full-cohort bound and original denominator
   formula in `combine_panel`. If the complete cohort violates that bound,
   stop before publishing combined model inputs; do not reinterpret it as a
   bounded share or silently relax the downstream model.
4. Keep the pre-May-2022 historical-initialization checks and model input
   validation unchanged. This case has no historical payoff by May 2022.
   The clarification does not resolve later modified terms, rate changes,
   payment deferrals or a different burnout measure.
5. Hash this clarification in every newly executed quarter's evidence, and
   propagate the quarter-level exceptions into combination and calibration
   reports. Preserve the failed 2019Q4 attempt and private diagnostic. Earlier
   strictly completed quarters remain valid without rereading their sources.

This changes the placement of the intermediate partition check only. It does
not change the complete-cohort model, floor, imported response, prediction
candidate, outcome cutoff or published result. If the later full-cohort check
fails, that is a separate unresolved research decision.
