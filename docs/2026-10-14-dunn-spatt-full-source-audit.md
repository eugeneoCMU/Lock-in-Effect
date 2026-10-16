# Dunn–Spatt 2005: full-source audit of the existing solver

The original 23-page published paper is now supplied and verified. This audit supersedes the earlier full-text-unavailable source status; previously sealed notes remain historical. The current solver is a coherent tested borrower-cost scenario with shared dynamic mechanisms, not a replication of the paper's simultaneous loan valuation. No solver parameters, behavior, empirical estimates or accepted paper files changed.

## The three objects must remain separate

The paper's Vs is the market-valued synthetic borrower liability, V is the original marketed loan, and cm is the lowest par-priced replacement coupon payment (printed 600). Our J discounts borrower payments and fees at a supplied borrower discount rate. It resembles the purpose of Vs but is not established as that market-valued synthetic claim. A quote grid and multi-coupon array do not implement endogenous par pricing.

At exercise the paper separates Vs(c)=Vs(cm)+T+P from V=F+P (printed 603,eqs 4–5). Third-party refinancing costs are not paid to the original lender. Proposition 7's V<=F+P+T bound is strict if currentT>0 and belongs to the A 3-prime section (printed 608–610). It is not a bound on borrower J. Removing cash fees from J also cannot reconstruct original-loan V: J continues replacement-loan payments after the original lender receives payoff.

## Comparison with the actual implementation

1. **Distinct borrower and lender values — Market-value part absent.** Paper, printed pp.600, 603: Synthetic borrower liability Vs includes refinancing costs; original loan V is a separate marketed claim. Implementation: Only borrower discounted cash-cost J is computed; supplied discount and quotes do not establish the paper pricing measure.

2. **Repeated future refinancing — Shared mechanism; tests pass.** Paper, printed pp.600, 611–612: Current choice includes future refinance opportunities and costs; replacement contracts retain options. Implementation: Backward monthly recursion resets coupon, preserves remaining term, and charges each cash fee.

3. **Borrower exercise inequality — Discrete analogue checked.** Paper, printed pp.603, equations 3/5: Vs(c) <= Vs(cm)+T+P; equality in exercise region. Implementation: Normalized v(c) <= k+v(q)+epsilon; exercised nodes equal replacement value plus current fee; ties wait.

4. **Loan call boundary — Not implemented.** Paper, printed pp.603, equation 4; 606: Original loan market value V equals F+P at exercise; external fees are not lender call proceeds. Implementation: No original-lender market valuation or call cash-flow recursion exists.

5. **Endogenous par replacement quote — Not implemented.** Paper, printed pp.600, 611–612: cm is the lowest coupon payment at which the new marketed contract is priced at par. Implementation: Market quote grid is supplied; evaluating several coupons does not solve for cm.

6. **Moving exits versus no-moving branch — Restricted branch only.** Paper, printed pp.601, 608: A 3 compares moving gains with coupon-dependent early-payoff costs; A 3-prime removes forced prepayments. Props 5–7 use A 3-prime. Implementation: No moving/default exits; corresponds only to the restricted no-forced-exit scenario.

7. **Coupon exercise nesting and plateau — Conditional checks pass.** Paper, printed pp.604–606: Exercise is upward closed in coupon payment; borrower liability shares an exercise-region plateau. Implementation: Same-state nominal-rate nesting and common exercised value checked on fixed supplied cases.

8. **Concavity parameter — Do not impose rate concavity.** Paper, printed pp.608, Proposition 5: Concavity is in coupon payment under pre-refinance cash-flow linearity. Implementation: Nominal annual rate changes nonlinear annuity payments. A two-month no-refinance case is strictly convex in rate.

9. **Fee wedge Vs minus V — Not a lender-price check.** Paper, printed pp.600, 608–609: Market-valued fee wedge uses correctly valued, par-priced replacement contracts. Implementation: Subtracting fees from J does not recover original lender V; borrower payments continue after first refinance.

10. **Single-cost market-price bound — Not testable with current outputs.** Paper, printed pp.609–610, Proposition 7: V <= F+P+T, strict for positive current T, within the A 3-prime theoretical section. Implementation: Cannot apply to J or verify without V, market valuation and par quote. Do not cap borrower J at principal plus one fee.

11. **Proportional-cost homogeneity and maturity — Shared restrictions checked.** Paper, printed pp.602, 611: Self-amortizing terminal balance is zero; proportional contemporaneous-balance costs give balance-independent policy. Implementation: Exact balance homogeneity, zero maturity balance and repeated fee accounting already tested.

12. **Full general equilibrium — Use precise scope.** Paper, printed pp.602: Paper explicitly states its specification is not full general equilibrium; it simultaneously values loans and borrower strategies under no arbitrage. Implementation: Supplied-quote borrower scenario is narrower still; full general equilibrium is not the missing requirement.

## A concrete parameterization warning

Proposition 5 is concavity in coupon PAYMENT under a linear pre-refinance cash-flow comparison. The API coupon is a nominal annual RATE and recomputes annuity payments. With two months, zero discount and no exercise, monthly rate m=c/12 gives payment fraction a=m+1/(m+2) and J/b=2 a. Its second derivative in m is positive. At annual rates 0,6%,12%, normalized costs are 1,1.007506234414,1.015024875622. The middle point is below the endpoint average. This is a parameterization difference, not a numerical failure or a refutation of Proposition 5.

The existing 54 dynamic/structural tests plus 8 source-scoped tests pass. New checks cover the borrower branch ceiling with the declared tie tolerance, exercised-node equality, coupon exercise nesting/common plateau, same-quote wait behavior and the independent two-payment calculation. Internal cost monotonicity, no-refinance cost upper bound, terminal balance and homogeneity checks also pass. Those are conditional software/economic properties, not validation of absent lender pricing.

## What the source says about moving and observed behavior

A 3 models moving gains compared with coupon-dependent early-prepayment costs; it does not establish rate-independent sale behavior (printed 601). A 3-prime removes forced prepayment and governs Propositions 5–7. The borrower scenario uses that restricted setting, while the production Markov/default model is a distinct specification. The paper itself discusses slow refinancing/passivity and qualification barriers as possible explanations of observed prices (printed 612–615). It supplies neither estimated monthly exercise probabilities for our population nor a household-mobility coefficient for refinance events.

A financial optimum must therefore remain separate from realized exercise propensity. An empirical bridge would require a stated attention/qualification/delay mechanism fitted on appropriately labeled events and outstanding-loan exposures. No such parameters are introduced here. Allocating total payoffs across causes under plausible assumptions produces a sensitivity exercise; call it partial identification only after defining observed restrictions, identifying assumptions and the resulting identified set.

## Data-source corrections relevant before calibration

- NSMO's May 27,2026 publicrelease details are verified:62,359 originations 2013–2024 with performance through 2025 Q 3. Closure month/year and open/terminated status are useful; checked fields do not label sale/refinance/other. Public Z 47 is an answer indicator, not actual dollar closing costs. Sampling/nonresponse weights, imputation and suppression require explicit treatment.
- The linked 2024 ASMB questionnaire is Homeowner Costs and Expectations. It does not have the attributed realized refinance/payoff-keeping-property/sale split. Response-level public access and the alleged older-wave question remain unverified. A blank questionnaire is not training labels.
- FannieHARP has documented predecessor-successor links, but covers selected acquired 2000–2015 originals and 2009–2016 fixed-rateHARPsuccessors. It gives positive refinance events, not sale labels for unmatched exits or ordinary 2017–2021 refinance behavior. Registration/access is not completed here.
- Saved 51.0%is broad agency-vintage intersection asofJuly 15,2026. Same broad definition at June 29,2022 is 57.6%; strict listedUMBS 30-year coupon-vintage support at that date is 47.6%using the assumed 80 bpconversion. These are different definitions/dates, not directly matched collateral coverage. No newOct 2026 holdingscoverage was calculated.
- Aggregate portfolio alignment and flow reconciliation must remain distinct from individual Freddie-to-MBSmapping. The checked Freddie terms prohibit the latter. SOMA holdings changes can include purchases/sales, principal, rolls/swaps and aggregation, so holdings differences alone are not principal repayments.

Primary URLs and access statuses are preserved in data-access-evidence.json. No data was purchased, provider contacted, authenticated file downloaded or raw loan matched.

## Concrete meeting agenda

1. Verified implementation: present the monthly borrower-cost Bellman, repeated-fee/waiting examples and the source-scoped tests. State explicitly that original-loan valuation and endogenous par quotes are absent.
2. Identification problem: total voluntary payoff combines causes; mobility pertains to moving, and A 3 makes actual movement coupon-dependent. Public datasets inspected do not currently supply general matched cause labels or transaction-cost amounts.
3. Proposed empirical path: decide with ProfessorSpatt whether runoff prediction needs simultaneous loan pricing or a supplied-quote trigger plus empirical exercise propensity. Choose evidence for the cause/risk-set problem before fitting those additional mechanisms, and transport permitted aggregate moments only after validation.

Questions: Which valuation object is necessary for the runoff estimand? Is the intended restriction in coupon payments or nominal rates? Should equality trigger exercise or waiting? How should moving gains, financing loss and refinance attention interact? Which data can identify both exit cause and the eligible outstanding-loan denominator?

