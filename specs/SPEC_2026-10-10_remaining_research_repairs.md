# Remaining research implementation repairs

The user's October 10 instruction "fix" authorizes the four repairs identified
in the immediately preceding audit. Preserve c1f893a, existing data, publication
PDFs and source archives. This pass fixes computation and rebuild prerequisites;
it does not silently replace frozen empirical results or select new parameters.

## Fixed choices

1. Every simulated payoff, whether from the hazard or delinquency transition,
   records the remaining principal once as cash, closes that balance, and updates
   voluntary-prepayment history. Loans newly entering delinquency cannot also
   take an opening-state monthly transition in that same step. Scheduled
   maturity principal is cash but is separate from voluntary burnout.
2. Preserve original contractual term from source through samples and use it
   in amortization. Explicitly label legacy missing-term assumptions; corrected
   production runs must require known valid terms. Positive remaining balances
   at contractual maturity are settled as scheduled principal, without applying
   voluntary/default hazards first. Modification extensions are not inferred.
3. Historical burnout is cumulative voluntary prepay principal divided by the
   fixed original balance of the eligible source cohort, not the shrinking sum
   of original balances on currently reporting rows. Store the fixed denominator
   and finite-age sum/count for future exact recombination. Do not manufacture
   these quantities from old aggregate cells. Corrected prediction initialization
   requires a verified fixed denominator and bounded historical fraction.
   Simulation snapshots carry historical burnout under the same cohort key;
   subsequent simulation changes accumulate against a fixed cohort balance.
   Old published prediction replays must opt explicitly into legacy clipping.
4. Transitions are opening-to-closing states for the same identified loan in
   consecutive calendar months, weighted by its opening balance (loan counts
   available as an explicit alternative). Reject duplicate loan-months, invalid
   states/balances and invalid probabilities; exclude gaps and observations
   beyond the frozen estimation end. No-observation rows retain their state
   rather than inventing transitions. Cohort-mode estimation is legacy only.

## Work and acceptance

- Reproduce the failures with targeted regression cases before modifying code.
- Parent owns ingestion, snapshot/burnout integration, prediction initialization
  and final verification. A delegated accounting repair owns competing_risks.py,
  macro.py, term fields in agents.py and its dedicated new tests. A delegated
  transition repair owns markov.py and its dedicated new tests. No overlap.
- Test disappearing paid-off loans, partial missing ages, unequal partitions,
  duplicate/overlapping source membership, term/maturity boundaries, reordered
  transition columns, first-observed events, and frozen-time cutoff behavior.
- Use synthetic histories and already available local compact evidence. Do not
  hydrate new cloud quarters or access later Freddie outcomes in this repair.
- Full suite, independent review, source/PDF preservation hashes, explicit
  remaining rebuild requirements and a local commit conclude the pass.

No software check identifies the moving share, validates counterfactual dollars,
or supplies missing population coverage. The dated publications remain historical
calculations until a separately audited input rebuild and dependent reruns finish.
