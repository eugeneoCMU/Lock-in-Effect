# Major-revision evidence decision

This note records the data search and manuscript decision for the two unresolved assumptions. It does not add an estimate.

## Sale-related share of voluntary prepayment

**Target.** The paper needs the fraction of voluntary terminations among comparable low-coupon loans in the QT period that followed a property sale, ideally by rate gap and loan vintage. This would discipline the model's `mu`, the share of voluntary prepayment receiving the imported moving response.

**Freddie data held for this project.** [Freddie Mac's loan-level dataset FAQ](https://www.freddiemac.com/fmac-resources/research/pdf/faq.pdf) defines zero-balance code 01 as “Prepaid or Matured (Voluntary Payoff).” It does not split that code into property sale, rate-and-term refinance, cash-out refinance, or other voluntary payoff. Codes for distressed property dispositions are different events and cannot be substituted for ordinary home sales.

**Public FHFA alternatives checked on 2026-10-06.** The [2026 NSMO public-use file](https://www.fhfa.gov/data/nsmo) has mortgage performance through 2025Q3. Its [codebook](https://www.fhfa.gov/document/d/nsmo/nsmo-appendix-c-v70.pdf), columns 510–512, supplies termination year, month, and open/terminated status. It does not supply a sale-versus-refinance reason for termination. The `Cashout` flag in column 513 describes whether the sampled mortgage was a cash-out refinance **at origination**; it does not identify how that mortgage later terminated. The [National Mortgage Database program](https://www.fhfa.gov/programs/nmdb) contains richer linked administrative/property information, and the American Survey of Mortgage Borrowers asks about terminations, but the public materials located here do not provide a loan-level termination-reason file linked to the Freddie risk set. An aggregate purchase/refinance origination ratio would have a different denominator and would not identify `mu` for existing loans that prepaid.

**Decision.** No credible `mu` point estimate can be added from the accessible data. Show zero alongside the 25/50/100% assumed mappings; zero gives a zero marginal by definition, while 25% is not a data-backed lower bound. Identify `mu=1` as the upper endpoint within the fixed hard-maximum mapping, and present the $42.6B result as one conditional anchor. A true estimate requires sale-linked deed/servicing data or an accessible borrower-level termination-reason source with comparable coupons, vintages, and dates. Do not treat the public data search as evidence that any scenario is more likely.

## Baseline turnover and housing supply

**Existing evidence.** The 2018 discount-cohort floor read is 4.70–5.33% annual CPR, with a 4.991% anchor. The maximum-form marginal moves +4.3 to +6.8 percentage points across that floor range. Calendar standardization gives +4.7 points; a housing-activity transport correction gives +10.7. An additive baseline-rate rule gives about +11.2. These are separate assumption or transport comparisons; none is an independent estimate of a pure non-rate turnover hazard.

**Missing design.** The 2018 cohort is separated in time from the QT outcome but does not share the QT housing market, inventory, or borrower composition. The paper's Freddie data do not provide a sale reason or a loan-linked listing/inventory history. Public housing-activity series can scale the floor but cannot distinguish an individual borrower staying because of housing supply from staying because of the financing gap.

**Decision.** Keep the hard-maximum rule as a named scenario, not an empirically selected preferred rule. Show it beside the additive rule and housing-activity correction. Do not interpret the floor-read sampling interval as covering this specification uncertainty. Estimating a stronger baseline requires geographic-month housing supply and transaction information linked to a defined loan risk set, with a predeclared comparison design and overlap checks.

## Manuscript consequence

Lead with the cap-versus-projection benchmark and a conditional simulation result. Describe the $42.6B hard-maximum, `mu=1` calculation as an illustrative anchor. Put the moving-share, floor, elasticity, form, and portfolio-coverage assumptions next to it in the abstract, introduction, results, and conclusion. No data-backed point estimate of the full-SOMA causal effect is available from the present evidence.
