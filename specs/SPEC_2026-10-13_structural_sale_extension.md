# Exploratory contracting and sale/refinancing extension

Implement the user's October 13 pasted proposal as a separate future extension.
No active production hook, selected calibration, new dollar effect or lender
optimum is introduced. The existing mixture model remains a different assumed
intensity decomposition.

`scheduled_loan_value` discounts scheduled P&I with supplied annual decimal
rates and integer remaining months. Its USD value is a deterministic proxy,
not an observed market value or an option/default-adjusted price. Contractual
financing loss can be constructed as max(balance - modeled value, 0).

`effective_penalty` defaults to no concessions. Explicit institutional permission
and a supplied assumed USD cap are required to use min(contractual loss, cap).
This does not solve or estimate Dunn–Spatt's lender equilibrium.

`sale_intensity` multiplies a supplied monthly Poisson opportunity intensity by
the tail of a supplied gains-in-USD CDF. `sale_termination_intensity` requires
an explicit sale-to-mortgage-termination probability. Sale, termination, cash
repayment, principal loss and pool repurchase are distinct objects. No cash
or par-payoff rule is inferred from sale incidence.

`competing_probabilities` converts supplied nonnegative sale-termination,
refinancing, other and default intensities into mutually exclusive monthly
first-exit probabilities. It does not replace the fractional/Markov engine.

Source boundary: publisher abstract and bibliography are verified; full 1985
text was not retrieved. The appendix's cap and probability equations are a
proposed research sketch, not a replicated theorem. Current agency guides
illustrate constraints and exceptions, not historical compliance of every loan.


## October 13 refinancing interface extension

The existing 1985-inspired prototype functions remain unchanged. The 2005
Dunn–Spatt attachment motivates keeping borrower mobility and refinancing
separate; it does not authorize describing this sketch as a replicated pricing
model. The 2005 publisher abstract is verified, while the full paper is not.
Future interest-rate expectations and the option value of waiting are essential
boundaries: a static savings comparison cannot identify a dynamic exercise rule.
This extension does not reproduce the full dynamic borrower/lender model.

`supplied_cause_probabilities` requires four explicit monthly cause-specific
intensities and an explicit nonnegative dimensionless `sale_mobility_factor`.
Its sale input is mortgage termination on sale. Home-sale incidence must first
be translated with the separately supplied termination probability. The mobility
factor multiplies only the sale-exit intensity. Refinancing, other and default
intensities are untouched; their mutually exclusive first-exit probabilities
may change because sale competes for the first exit. A factor of zero suppresses
sale exits, one leaves them unchanged, and values above one increase the assumed
intensity. There is no empirical default or automatic refinance calibration.
For borrower i and cause j, the monthly mapping is
`p_ij = lambda_ij / Lambda_i * (1 - exp(-Lambda_i))`, with zero exit probabilities
when `Lambda_i = 0`. Inputs can broadcast over borrower arrays.

`aggregate_borrower_probabilities` accepts exactly four aligned one-dimensional
borrower probability arrays and explicit finite nonnegative weights with positive
mass. It computes `sum_i w_i p_ij / sum_i w_i` after the individual conversion.
It never converts a weighted mean intensity. Weights define the denominator:
equal weights describe borrowers; supplied balance weights describe the weighted
population, without implying a cash payoff or principal-return calculation.
Each borrower's sum of cause probabilities must be at most one (allowing
1e-12 numerical roundoff). Aggregate survival is one minus the sum of mean
cause probabilities. A simple heterogeneity check uses sale intensities 0 and
`2 log(2)`: equal borrower weights imply a .375 sale probability, while converting
the mean intensity incorrectly gives .5.

`static_refinancing_savings` is an optional deterministic screen only. Every
argument is mandatory: current balance, annual nominal decimal contract rate,
replacement rate, discount rate, positive integer remaining months, and explicit
upfront cash refinancing cost in USD. The replacement mortgage amortizes the
same principal over the same remaining term; the cost is not financed. Both
payment schedules use the supplied discount rate. The signed result is
`PV(old scheduled P&I) - PV(new scheduled P&I) - upfront cost`. Positive savings
do not mean refinancing now is optimal and never become an empirical hazard
in this interface. Future-rate expectations, waiting, dynamic optimization,
market-value fitting, credit/default pricing, and endogenous lender pricing
remain outside scope. The deterministic P&I proxy is not a mortgage market
value.

Validation rejects nonfinite/negative intensities, factors, weights, rates,
balances and costs; invalid terms; incompatible probability shapes; invalid or
nonexclusive probabilities; zero aggregate weight; and nonfinite computed
results. The additions have no production hooks and change no manuscript
estimates, fitted hazard inputs, or production defaults.
