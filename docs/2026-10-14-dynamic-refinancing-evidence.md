# Proposed dynamic refinancing scenario and identification audit

## Scope and source boundary

The scenario is proposed by this project. It is not a replicated Dunn–Spatt
model, an estimated borrower hazard, mortgage market value, or lender equilibrium.
No existing dollar estimate, production hook, fitted hazard, or accepted source
receipt is changed. No raw loan file was read for this extension. This audit
incurred no purchase, contact, or access circumvention.

Primary source availability checked October 14, 2026:

- Dunn and Spatt (2005), *The Effect of Refinancing Costs and Market Imperfections
  on the Optimal Call Strategy and the Pricing of Debt Contracts*, *Real Estate
  Economics* 33(4), 595–617. [Publisher DOI page](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6229.2005.00132.x)
  supplies accessible metadata, abstract, and bibliography. The abstract describes
  simultaneous loan valuation and refinancing choices across coupons, accounting
  for future refinancing costs, and a call-price-plus-one-cost valuation bound.
  Full text was not retrieved. A3/A3′, pp. 601–602, the precise moving-opportunity
  assumptions, and conditions for the bound remain unverified.
- [Publisher PDF](https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.1540-6229.2005.00132.x)
  and [full text](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6229.2005.00132.x)
  failed retrieval. This is not proof an authorized institutional user lacks access.
- [Spatt CV on SEC](https://www.sec.gov/comments/sr-batsbzx-2017-34/batsbzx201734-3432889-162194.pdf)
  lists author-hosted `http://wpweb2.tepper.cmu.edu/spatt/refinancing.pdf`.
  The host failed DNS resolution; `wpweb2k.tepper.cmu.edu` and
  `web.tepper.cmu.edu` variants also failed browser retrieval. The current
  [CMU profile](https://scholars.cmu.edu/982-chester-spatt) supplied no working copy
  in the bounded search. No full-text file appeared in the repository filename search.
- Separate primary full text: [Agarwal, Driscoll, and Laibson author-hosted PDF](https://laibson.scholars.harvard.edu/sites/g/files/omnuum5971/files/laibson/files/optimal_mortgage_refinancing_092012.pdf),
  *Optimal Mortgage Refinancing: A Closed Form Solution*. Printed pp. 9–10
  give a borrower-cost Bellman and value matching after the contract rate resets,
  with refinancing cost paid upon each exercise. Its analytic simplification
  holds real principal constant until Poisson repayment; its repayment parameter
  combines moving, principal reduction, and inflation. That shortcut is not
  imported here: monthly amortization is explicit. This separate source is
  useful for recursive logic, not attribution of our equations to Dunn–Spatt.

## Proposed state, timing, and equations

State is opening principal b, contract coupon c, remaining contractual months n,
and supplied market Markov state x. Coupon quotes and borrower discount rates
are annual nominal decimals divided by 12. Decision date t is immediately after
the preceding scheduled payment. Keep or refinance to today's supplied quote
q(x). Refinancing advances exactly b to retire the old balance, preserves the
remaining term n, and pays unfinanced cash cost k*b now. Next scheduled payment
and Markov transition occur at t+1. Replacement mortgages retain future exercise
opportunities; there is at most one exercise per monthly decision date.

Let a(c,n) be the monthly payment per dollar of opening principal and
z(c,n)=1+c/12-a(c,n) the closing balance fraction (z(c,1)=0 exactly).
With supplied monthly discount factor d=1/(1+r_discount/12), normalized costs are

    hold[n,c,x] = d * (a(c,n) + z(c,n) * sum_x' P[x,x'] v[n-1,c,x'])
    exercise[n,c,x] = k + hold[n,q(x),x]
    v[n,c,x] = exercise if exercise < hold - epsilon; otherwise hold
    J(b,c,n,x) = b * v[n,c,x]

The tie tolerance epsilon is explicit, default 1e-12 per opening dollar, and selects
wait. Zero remaining months require zero principal; no positive debt is discarded
at a shorter horizon. Final payment clears the balance exactly. Transition rows
must be finite, nonnegative and sum to one within 1e-12; only accepted numerical
row-sum roundoff is normalized. Supplied states may share a rate (a clock state
can preserve deterministic future rate changes). Coupons are the union of the
initial coupon and supplied quotes. No interpolation over coupons or balance occurs.

Proportional cash costs yield exact degree-one balance homogeneity, avoiding a
balance grid. Fixed-dollar costs are deliberately unsupported; adding them would
require an independently checked interpolation/solution scheme. This restriction
is a scenario assumption, not a measured cost distribution. Lender pricing,
sale/default, taxes, financed costs, eligibility, inattention, empirical hazard
conversion, and endogenous quoted rates remain absent. Borrower expected costs
use the supplied Markov matrix; no pricing measure is inferred.

The prescribed scenario inputs are saved in `declared_scenarios.json` under the
main `output/research-next/2026-10-14/dynamic-refinancing` root. They were saved
before implementation/evaluation. Four base scenarios: constant/no-savings,
prohibitive cost, falling rates with option to wait, and repeated rate falls.
Additional predeclared quote steps: 100, 50, 25, and 12.5 basis points on the
same deterministic clock, plus the exact supplied quotes. This is quote
approximation sensitivity, not convergence to a continuous stochastic diffusion.
The computational balance grid size is zero. The Bellman is exact on each
supplied Markov grid up to arithmetic and the declared tie tolerance.

## Sale/refinance identification audit

[Official Freddie SFLLD General User Guide](https://www.freddiemac.com/fmac-resources/research/pdf/user_guide.pdf)
was accessible. Origination column 21 describes purchase/refinance purpose at
origination, not the cause of later payoff. Performance column 9 bundles prepaid
or matured voluntary payoff in code 01; it does not split ordinary sale, refinance,
and other voluntary repayment. Codes 02, 03, and 15 refer respectively to third-party
sale, short sale/charge-off, and whole-loan sale, not general ordinary homeowner
sale labels. Origination column 27 and printed p. 22 link predecessor/successor
sequence numbers for Relief Refinance only; the predecessor may appear as payoff
or repurchase. Lack of this restricted link is not a sale label. Printed p. 23
records random identifiers and masked geography/amounts/dates. Coverage of the
special linkage in our 2017Q1–2021Q4 loans was not measured. Only documentation,
not raw loan records, was inspected.

Other primary data possibilities, without claiming identification of existing loans:

- [Public HMDA field documentation](https://ffiec.cfpb.gov/documentation/publications/loan-level-datasets/lar-data-fields/)
  describes purchase/refinance/cash-out refinance applications and originations.
  It is not an outstanding-loan payoff risk set and has no verified common link
  to Freddie's random loan sequence numbers. Origination shares are not payoff hazards.
- [FHFA NSMO public-use file](https://www.fhfa.gov/data/nsmo), May 2026 release,
  includes performance through 2025Q3. Its [codebook](https://www.fhfa.gov/document/d/nsmo/nsmo-appendix-c-v70.pdf)
  has origination purpose, refinance motivations and cost/rate trade-offs, plus
  quarterly performance. Status A means reporting ended, usually after closure;
  B is potential closure. Those statuses are not verified sale/refinance labels.
  This can inform external scenario heterogeneity, not label existing Freddie loans.
- [Cotality Loan Releases](https://www.cotality.com/products/loan-releases) describes
  recorded release dates, document numbers and links to underlying transactions.
  Release alone may reflect payoff, refinance or foreclosure. Linked deeds/new
  liens plus validation would be needed. Access is commercial; pricing varies by
  volume/geography/delivery. Historical coverage, license, cost, match rates and
  classification quality were not verified.
- [Official Payoff Analysis update](https://corelogic.launchnotes.io/announcements/powerful-new-features-now-available-in-property-intelligence-and-payoff-analysis)
  describes persistent Owner Link and subsequent transactions. It does not establish
  an available academic extract, outstanding-loan denominator, or reliable linkage
  to this public Freddie population.

Required additional empirical object: sale/refinance/other payoff labels with the
comparable outstanding-loan risk set, dates, coverage and reliable validated linkage.
A released-loan share, new-origination share, household mobility estimate, and
outstanding-loan hazard have different denominators. Neither this source audit
nor the dynamic scenario identifies a sale fraction, revised dollars, or direction
of bias in an existing model result.

## Verification protocol

Tests were written before implementation and initially failed because the new
module was absent (21 failures). Short-horizon exhaustive action trees independently
track dollar balances and payments; they are compared with the normalized Bellman.
Other checks cover equal-rate scheduled PV, zero horizon, prohibitive-cost bounds,
positive static savings with optimal waiting, repeated exercises charged each time,
contractual maturity, balance homogeneity, invalid matrices/inputs and impossible
traced paths. All new tests treat warnings as errors.

A local NumPy matrix multiplication emitted divide/overflow/invalid warnings even
for an all-one finite array times a finite transition matrix, while producing all-one
finite output. The expectation uses an explicit equivalent einsum contraction,
which avoids this observed BLAS warning path without suppressing warnings. The
combined new dynamic and unchanged structural extension tests passed (54 tests)
without warnings. Full regression is coordinated by the parent task.

Additional requested verification splits each state of a supplied two-state chain
into two equivalent labels with duplicate quotes and identical aggregate transition
laws. Values and exercise policies agree. This is representation invariance, not
convergence to an unspecified continuous-rate process. The model has no fixed-dollar
cost component; all costs are proportional to opening principal, including the
explicit zero-cost scenario permitted by the interface. Quote discretization
errors need not improve monotonically because individual quotes round differently.
