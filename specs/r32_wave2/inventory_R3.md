# Round 32 condition inventory — Peer Reviewer 3 (cross-disciplinary: housing finance / mortgage law / public finance)

Source: `REVIEW3_v18_panel_2026-07-29.md` lines 666–893. Verification target: `paper/v18/revised_paper_v18.tex` (1,429 lines), `paper/v18/references.bib` (70 entries), `hazard/data/*.json`, `hazard/data/*.parquet`. No repo script executed; no file in the worktree touched.

R3 grade: 64.6/100, MAJOR REVISION (one point below Minor). Carroll Round: "Ready to present and defend as-is" with two missing presentation-layer slides (C-R3-42, C-R3-43).

Section-letter note: R3's §V letters drift by one in two places (`episode_confrontation` and the sign-forcing paragraph are both in §V.E = `sec:identification`, .tex:317–468; R3 calls the first §V.D). R3's §VI/§VII/§VIII letters and every table number (1, 5, 8, 9, 11, 12, 13, 27) map correctly. All locations below are given as .tex line numbers.

---

### C-R3-01
raiser: R3
severity: MAJOR (MAJOR 1)
class: WORDING
panel_lines: 47–59
condition: The paper's bottom-line comparison — "the cost to households who could not move is real; the institutional cash-flow cost is small" — must stop setting a measured institutional quantity against an imported, never-measured household quantity. Either the household side is quantified in the same unit of account (C-R3-02/03) or the comparison is explicitly retired in favour of "this paper measures the institutional leg only; the mobility leg is imported at the elasticity and never re-measured, so the ranking rests on external evidence."
location: abstract .tex:31 (final two sentences); §I .tex:52 ("household mobility is constrained … so the trade-off's binding cost is denominated in mobility rather than in institutional cash flow"); §VI.A .tex:542; §VIII .tex:731
verified: true — .tex:31 carries R3's quoted sentences verbatim; .tex:52 carries the quoted §I clause verbatim; .tex:542 carries the double declination ("I do not translate the \$764.7 billion shortfall into welfare terms… The welfare-relevant objects are the constrained moves themselves… and the forgone labor-reallocation gains this literature identifies, which my accounting framework does not measure"); "welfare" occurs 4× in the .tex, "per household" 0×.
fix: Rewrite the abstract's closing pair and the §VIII leg-(2)-vs-leg-(3) sentence so the asymmetry is on the page: name the household leg as imported-at-the-elasticity and unmeasured in this design, and say the ranking of legs (2) and (3) is an external-evidence ranking, not a within-paper measurement. If C-R3-02/03 land, this row is discharged by them instead.

### C-R3-02
raiser: R3
severity: MAJOR (MAJOR 1, fix (a))
class: RUN
panel_lines: 55–57
condition: The paired legs' differential must be converted from foregone prepaid face into a count of foregone payoffs, with the moving-share bracket applied, so the household leg is expressed in the same unit as the institutional leg.
location: new quantity; inputs at .tex:1085 (attrition accounting), .tex:261 and .tex:333 (moving-share bracket, production convention s=1), Table 1 row 4 (.tex:80)
verified: partly — the arithmetic reproduces on committed data (`loan_sample.parquet` mean `balance` = 126,812.61, i.e. R3's \$126,813 exactly; \$42.6bn / \$250k ≈ 170k payoffs over 42 months ≈ 49k/yr), but R3's provenance for "40,234 active at window start" is wrong: the parquet's `balance > 0` count is **40,077**, and 40,234 is the manuscript's own attrition figure (.tex:1085: "of the 75,000 sampled loans, 34,734 prepaid and 32 defaulted before the QT window opens, so 40,234 are active at the June 2022 start (39,752 current, 482 delinquent)"; also .tex:219, .tex:275, .tex:1026, .tex:1063; the same line prints a 40,074 mean-active-per-month). It is also the survival count in `attenuation_sensitivity_results.json`. Anti-condition list item 8 applies: use 40,234 as the manuscript's window-start survivor count, do not present it as a parquet balance filter, and do not swap in 40,077.
fix: Compute the count inside the existing Path B machinery rather than by ratio outside it: divide the central-minus-null prepaid-face differential (\$42.61bn at the 4.991% headline floor, \$70.35bn in-sample — both in `floor_form_mixture_results.json` parity gates) by the run's own mean active-loan balance, and report it as a band across the floor band (\$33.31–\$51.75bn, .tex:713) with the moving-share bracket s ∈ {0.25, 0.5, 1} from `moving_share_bracket_offwindow` applied. Disclose that aggregate face ÷ mean balance is an approximation to a transaction count (curtailment and partial prepayment are in the numerator), and that the SOMA-book average loan size R3 uses (\$250k) is an external assumption, not a repo quantity — the sample's own per-active-loan balance is ≈\$236k.

### C-R3-03
raiser: R3
severity: MAJOR (MAJOR 1, fix (a); restated as MINOR 5)
class: STRUCTURE
panel_lines: 57, 173
condition: Table 1 must carry a household-side row. It currently has none, so the exhibit that "collects the core results" omits one of the two legs §VIII's conclusion compares.
location: Table 1 = `tab:headline`, .tex:64–90; rows at .tex:76–86
verified: true — the nine rows are cap benchmark, expectations complement, mechanical null, lock-in marginal (off-window), lock-in marginal (in-sample), Path B level, production ABM, cross-design ABM, Danish counterfactual. No household row, no duration row.
fix: Add a row "Foregone payoffs implied by the marginal" carrying the C-R3-02 count with its floor band and moving-share bracket, and price it with `batzer2024`'s \$2.4trn foregone-capital-gains magnitude and `hsieh2019`'s mechanism as bounds — both already cited (see C-R3-04, C-R3-33). Row must be labelled as an implied count, not a measured one.

### C-R3-04
raiser: R3
severity: MAJOR (MAJOR 1)
class: WORDING
panel_lines: 51
condition: The one household-side magnitude the paper carries — Batzer et al.'s ≈\$2.4 trillion of foregone household capital gains — appears only in the literature review and is never set beside the \$61.2bn institutional gap it dwarfs by ~40×.
location: .tex:100 (§II); comparison sites .tex:542 (§VI.A), .tex:731 (§VIII), Table 1 Danish row .tex:86
verified: true — `batzer2024` occurs exactly once in the .tex (.tex:100), and "2.4 trillion" once, in the same clause.
fix: Carry the \$2.4trn figure to the comparison site (§VI.A's welfare-declination paragraph or §VIII's three-considerations paragraph) with its scope stated (a stock of foregone capital gains on a counterfactual universal-relocation basis, not a flow and not commensurate with a 42-month cash-flow gap), so the order-of-magnitude asymmetry is visible where the ranking is asserted.

### C-R3-05
raiser: R3
severity: MAJOR (MAJOR 2)
class: WORDING
panel_lines: 65–67
condition: The global "no outcome-holdout months exist anywhere in this paper, without exception" claim is stated as an unavoidable design property. It is unavoidable for the SOMA cash-flow margin only; the household margin admits an external outcome moment (mortgage-financed existing-home-sale volume) that needs no SOMA holdout. The claim must be scoped accordingly.
location: .tex:92 ("Definitions used throughout"); repeated at .tex:741 (§VIII.A)
verified: true — both sites verified verbatim; .tex:92 has the italicised "no outcome-holdout months exist anywhere in this paper, without exception", .tex:741 restates it and names the nineteen-month temporal holdout as the nearest construction.
fix: One clause at each site: the absence of an outcome holdout is a property of the *cash-flow* margin, which is evaluated on the window that calibrates it; the behavioral implication of the marginal is testable against an external transaction aggregate, and (per C-R3-06) the paper does/does not do so.

### C-R3-06
raiser: R3
severity: MAJOR (MAJOR 2, fix (i)) — R3's single most-emphasised computation
class: RUN
panel_lines: 67–75
condition: The implied foregone-payoff count must be set against realized mortgage-financed existing-home-sale volume and the verdict stated whichever way it falls. This is the design's only available outcome-side external validation, and R3's own arithmetic says it strains: ~230k/yr whole-market at most (49k/yr on the SOMA book ÷ ≈21% SOMA share) against ~1.3m/yr fewer mortgage payoffs implied by the 6.1m→4.1m existing-home-sales decline — about one-sixth — against Aladangady et al.'s 44% attribution.
location: new subsection or §V.E addendum; scaling input `microsim_results.parquet` `exposure` column
verified: true as a gap — no such comparison exists anywhere in the .tex; R3's repo-side inputs check out (`microsim_results.parquet` `exposure` opens at 2,702,542,348,466.7 = \$2.7025trn, so the ≈21% share against \$12.5–13trn 1–4 family debt is right; the s=1 production convention that makes the count an upper bound on the moving component is stated at .tex:261: "the production convention $s = 1$ remains the reported form"; the 68.8% censoring at the headline floor is at .tex:269/323/333; the 4.5× realized-over-implied gradient is `episode_confrontation_results.json` `realized_gradient_pp` = 4.198, `realized_over_implied_mid` = 4.4799, implying the ≈0.94 model gradient).
fix: One script on committed outputs plus a public series: take the C-R3-02 count band, gross it to the whole market by the SOMA exposure share, bracket by moving share, and compare against NAR/Census existing-home-sales volume × mortgage-financed share for the same months. Report as an order-of-magnitude external check with its confounds named (SOMA book is compositionally more locked-in than the market average, which widens the discrepancy rather than narrowing it; the denominator decline includes non-rate causes). New external data (sales volume, mortgage-financed share) must be pinned like any other benchmark input.

### C-R3-07
raiser: R3
severity: MAJOR (MAJOR 2, fix (ii))
class: RUN
panel_lines: 73, 75
condition: The Aladangady 44% reconciliation was run only under the production hard-maximum floor form, which censors in 68.8% of loan-months at the headline floor. It must also be run under the additive form, which never censors and returns +11.2 points, since the max-vs-additive fork is the paper's largest open question.
location: run `scaled_null_housing_activity`; Table 5 = `tab:assembly` row at .tex:346
verified: true — `scaled_null_housing_activity_results.json` spec fixes FLOOR_MODE at production (max) and scales the PSA baseline h0 only; root φ* = 0.75390625 at the 4.991% floor (R3's 0.754 ✓) driving the marginal to `marginal_pp` = 0.8979 (R3's +0.9 ✓). The additive-form machinery exists and is production code (`floor_form_mixture_results.json` parity gates `P_marg_4.991_s1` = 85.705, s=1 ≡ additive).
fix: Re-solve the same calibration condition `trapped_null(φ*) − trapped_null(1) = (0.56/0.44)·[central(1) − null(1)]` with FLOOR_MODE additive (s=1), at both committed floors, using the existing bisection harness. Expected direction: with no censoring, more of the housing-activity deflation passes into the null, so φ* and the surviving marginal will differ materially from the max-form cell — which is exactly why the row's status is form-conditional.

### C-R3-08
raiser: R3
severity: MAJOR (MAJOR 2)
class: WORDING
panel_lines: 73, 75
condition: Table 5's Aladangady row is form-conditional in a way the table does not mark; the mark must be added either way (before or after C-R3-07 runs).
location: `tab:assembly` row .tex:346: "Housing-activity-scaled baseline (Aladangady-anchored) & $+0.9$ & below the interval & scaled-null variant; upward-bias entry, root $\phi^{*} = 0.754$"
verified: partly — the row itself carries no form mark, but the paragraph introducing the assembly does: .tex:334 opens "Holding the production hard-maximum form and the imported elasticity fixed, every correction to the floor or to the accounting basis moves the headline down", and the additive form appears as its own +11.2 counterweight row. So the conditioning is stated for the table as a whole and missing at the row.
fix: Append "(max form; not re-run additive)" — or the C-R3-07 result — to the row's status cell. Zero new literals if C-R3-07 is not run.

### C-R3-09
raiser: R3
severity: MAJOR (MAJOR 3, defect (a) + fix (i)); R3 calls it "cheapest high-value addition in the paper" (opportunity 1)
class: WORDING
panel_lines: 79–89, 185
condition: Under the cash-haircut reading the 1−P wedge is a transfer from the SOMA portfolio — hence from Treasury remittances, hence from general taxpayers — to households who move. That fiscal incidence, and the fact that its welfare sign turns on the relative marginal value of public funds versus household liquidity, is never stated; the current phrasing ("costs the Federal Reserve") obscures it.
location: §V.B .tex:273 (the par-windfall sentence); §VIII .tex:727 and .tex:731; Table 13 notes (`tab:danish`, notes block after .tex:618)
verified: true — .tex:273 carries R3's quoted sentence verbatim ("the $1-P$ wedge on bought-back face is exactly the par windfall a moving household pays the bondholder under the U.S. rule and keeps under the Danish one, so the cash-flow cost is the disappearance of a household-to-bondholder transfer, not an added resource cost"); .tex:727 has "as reserve drain the rule costs the Federal Reserve exactly the par windfall it would otherwise have extracted from moving households — legs (2) and (3) … are the same dollars seen from two sides". Word counts in the .tex: "taxpayer" 0, "seigniorage" 0, "deferred asset" 0, "remittance" 3 (all agency-settlement-timing sense, §VII.B).
verified (cont.): artifact side confirmed — `buyback_credit_bracket_results.json`: `gap_face_b` = 61.18834, `early_face_E_b` = 470.65325, `gap_cash_range_b` = [−117.660, −89.421], `code` = "REVERSES".
fix: One paragraph in §VIII plus one line in Table 13's notes: name the bondholder (the Federal Reserve), route the wedge through Treasury remittances to general taxpayers, and state that the welfare sign therefore depends on the relative marginal value of public funds and of household liquidity — a question outside this design. No new numbers required; the \$89.4–117.7bn bracket is already committed.

### C-R3-10
raiser: R3
severity: MAJOR (MAJOR 3, defect (b) + fix (ii))
class: REFERENCE
panel_lines: 87–89
condition: Every Danish figure is ex-post partial equilibrium with no ex-ante primary-rate offset: under a Danish payoff rule the repurchase option is paid for by borrowers in the coupon. The +\$61.2bn is therefore a gross figure, and the missing ex-ante coupon offset is absent from §VI.D's omission list.
location: §VI.D .tex:590 (omission list and the Berger ≈1bp import); Table 13 notes; §VI.D .tex:586
verified: true — .tex:586 imports Berger et al.'s ≈1bp general-equilibrium rate effect for the refinance-in-place channel only; .tex:590's omission list is exactly R3's five items (Balance Principle series-level match funding, tap-issued joint-and-several series, advisory distribution, Danish product mix, interest-only share "would … move the shortfall in the opposite direction") with no ex-ante pricing term. Both references R3 names are already in `references.bib` and already cited in the body: `campbell2013` (bib line 605; cited once, .tex:729, framing the U.S.–Danish contrast as a mortgage-design problem) and `berg2018` (bib line 50; cited twice, .tex:112 and .tex:729, for the Balance Principle). Nothing to add to the .bib.
fix: Add a sixth item to §VI.D's omission list and two lines to Table 13's notes: all Danish figures are ex-post and carry no ex-ante primary-rate offset; under a Danish payoff rule the repurchase option is priced into the coupon, which is part of why Danish and U.S. mortgage spreads differ — cite `campbell2013` and `berg2018` at that clause (new clause, existing keys) — and the sign of the omission runs against the reported relief.

### C-R3-11
raiser: R3
severity: MAJOR (MAJOR 4, defect (a) + fix (iii))
class: WORDING
panel_lines: 93–103
condition: §VI.B's "a cap intended to bind" is never justified. Making an MBS redemption cap bind forces reinvestment of principal above the ceiling and so slows the reduction of agency MBS — against §I's Treasuries-only framing and against §III.B's own concession that a shortfall against the MBS cap is not evidence a stated objective was missed. The objective a cap serves must be stated explicitly (R3's reading: predictability and communication, not speed).
location: §VI.B .tex:576 ("A cap intended to bind would therefore be set at or below the lower edge of the book's projected scheduled-plus-turnover principal path"); §I .tex:38–40 (Treasuries-only framing); §III.B .tex:150
verified: true — .tex:576 states the design rule with no objective function and no justification for bindingness; .tex:150 carries the concession verbatim ("a shortfall against the MBS cap is not by itself evidence that a stated policy objective was missed. The Committee's operating object was the aggregate securities portfolio's decline, Treasury runoff ran against its own caps throughout the window, and nothing in this paper shows that reserves or the aggregate path came in off the intended course because MBS ran slow").
fix: Insert an objective-function sentence before .tex:576's design rule: state that a redemption cap's function is predictability and communication of the composition path, not maximal speed; note that binding the MBS cap is inconsistent with the stated composition goal (it forces reinvestment); and cross-reference §III.B so the standing concession is discharged where it is used rather than left unresolved two sections earlier.

### C-R3-12
raiser: R3
severity: MAJOR (MAJOR 4, defect (a))
class: WORDING
panel_lines: 97, 103
condition: The paper's second design option — a standing policy of substituting Treasury runoff or outright MBS sales when passive runoff undershoots — is the one consistent with §III.B, and it is buried. The recommendation should be "publish the projected path with its band and pre-commit the substitution instrument", not "lower the cap".
location: §VI.B .tex:574
verified: true — .tex:574 puts both options in one sentence inside the paragraph flagged "The design question that follows is speculative, and I flag it as design space rather than as a finding these estimates support"; the binding-cap rule then gets its own sentence at .tex:576, giving it the emphasis.
fix: Reorder §VI.B's closing so the substitution instrument is the stated design implication and the cap level is the subordinate clause; keep the speculative flag on both.

### C-R3-13
raiser: R3
severity: MAJOR (MAJOR 4, defect (b) + fix (ii))
class: RUN
panel_lines: 99, 103
condition: The proposed state-contingent cap ("indexed … to the share of the book sitting deeply below market coupon") supplies no function from the observable to a cap level, though every input is already in the repository. A two-input table — book out-of-the-money share at 200/300/400bp cuts × turnover-floor band — mapping to achievable monthly principal and hence to an implied cap is required.
location: §VI.B .tex:574
verified: true — .tex:574 states the indexing idea and stops; the inputs exist: `composition_shift_results.json` (SOMA CUSIP coupon-by-vintage tabulation, anchor-gated to book WAC 2.49% and the vintage shares, .tex:1267), the Table 12 amortization calculator (`tab:wal` construction note, .tex:555, run `wal_normal_turnover`), and the floor band with its wild-cluster interval 4.177%–5.800% quoted in that same paragraph.
fix: Build the 3×3 (or 3×n) grid with the existing WAL/amortization calculator: for each OTM-share cut, take scheduled principal from the book composition and add turnover at each floor-band point, producing achievable \$bn/month and the implied cap. No new estimation — this is a re-tabulation of committed inputs through committed machinery — but it does print new literals, so it needs a spec-before-run header and parity gates against `tab:wal`'s printed rows.

### C-R3-14
raiser: R3
severity: MAJOR (MAJOR 4, defect (c) + fix (i)); also Carroll-Round slide 2
class: CHECK
panel_lines: 101, 103
condition: The cap result is not stated in the units of a cap decision (\$bn/month). The usable statement — achievable passive MBS principal was ex-ante roughly \$16–18bn/month, pinnable to about ±\$4bn, against a \$33.75bn/month average ceiling, with uncertainty ≈20% of the achievable level — is nowhere in the paper.
location: §VI.B .tex:546 (the 1.7–1.9× result) and .tex:574 (the band)
verified: partly — the two multiples and their inputs are in print and reproduce exactly (\$740.6bn projected ÷ 42 = \$17.63bn/month; caps \$1,417.5bn ÷ 42 = \$33.75bn/month; 33.75/17.63 = 1.914; wild-cluster floor interval 4.177–5.800 = 1.623 CPR points, which on the \$2.70trn book is ≈\$3.6bn/month, R3's ±\$4bn). But R3's second multiple rests on a settlement-aware allocation total of **\$839.5bn that the .tex never prints** (0 hits): it is derivable from `expectation_benchmark_results.json` as `actual_runoff_window_b` 652.752 + `settlement_aware_allocation.e_benchmark_b` 186.778 = 839.530, giving 839.53/42 = 19.99 and 33.75/19.99 = 1.689 — consistent with the printed "roughly 1.7 to 1.9 times".
fix: Restate §VI.B's result in \$bn/month: achievable ex-ante principal \$17.6bn/month under the pre-committed uniform-spread allocation and \$20.0bn/month under the settlement-aware one, against the \$33.75bn/month average ceiling, with the floor read's own sampling interval contributing ≈±\$3.6bn/month. Derived from committed artifact fields only; if \$839.5bn is printed it becomes a new literal and needs a gate.

### C-R3-15
raiser: R3
severity: MAJOR (MAJOR 5, item 3 + fix (i))
class: WORDING
panel_lines: 115, 121
condition: Every headline percentage divides by \$764.7bn — a gap against a ceiling §III.B declines to call a policy miss. Against the economically meaningful denominator, the \$87.8bn expectations complement, the same \$42.6bn is ≈49% (23% settlement-aware). Both denominators must be quoted in one breath in the abstract and in Table 1's marginal row.
location: abstract .tex:31; Table 1 row 4 (.tex:80); §III.B .tex:150
verified: true — `expectation_benchmark_results.json` `e_benchmark_b` = 87.8316 and `lockin_marginal.pp_of_e_benchmark` = 80.0908 for the in-sample \$70.3bn (R3's 80.09 ✓); 42.608/87.832 = 48.5% and 42.608/186.778 = 22.8% both reproduce; the abstract and Table 1 quote only the cap-relative 5.6%/+2.9-to-+8.7 points.
fix: In the abstract's second paragraph and in Table 1's off-window-marginal row, add the E-benchmark share beside the cap share ("\$42.6bn — 5.6% of the cap gap, and roughly half the ex-ante surprise under the central intra-2022 allocation, 23% under the settlement-aware one"), carrying the allocation-conditional-upper-bound reading that .tex:150 already governs every quotation of these ratios with.

### C-R3-16
raiser: R3
severity: MAJOR (MAJOR 5, item 1 + fix (ii))
class: WORDING
panel_lines: 113, 121
condition: The identified elasticity accounts for ~0.6 of the ~6.0 duration-extension years the paper says feed the fragility channel — roughly a tenth of the object it names as mattering. The concession exists but sits one paragraph after the fragility framing and is carried to neither the abstract nor the conclusion.
location: §VI.A .tex:538 (fragility framing: "this extension, not the cap arithmetic, feeds the fragility channels below") and .tex:540 (the concession, in the next paragraph); Appendix L .tex:1328; abstract .tex:31; §VIII .tex:721–731
verified: true — .tex:538 introduces the fragility channel and .tex:540 carries "shortens the portfolio by only 0.6 of the roughly six extension-years … a second-order contributor", i.e. exactly one paragraph later; Appendix L .tex:1328 derives both numbers (9.4-year empirical WAL against 3.4 at 2021 speeds = 6.0-year extension; rule-only 9.1 vs 9.7 = 0.6-year shortening); and R3's Table 12 reading checks out — `tab:wal` .tex:566 prints "Baseline turnover floor, off-window headline read (4.99\%) & 9.5 & 8.6" against the empirical 9.4, so the whole extension is delivered at the floor alone.
fix: Move the maturity-unit share into .tex:538 at the point the fragility channel is introduced, and add the same clause to the abstract's institutional-cost sentence and to §VIII. Zero new literals (0.6, ~6.0, 9.5 and 9.4 are all committed).

### C-R3-17
raiser: R3
severity: MAJOR (MAJOR 5, fix (iii))
class: RUN
panel_lines: 121
condition: Either put a mark-to-market number on the SOMA book for that 0.6 year (a market-value/DV01 image), or restrict the institutional-cost claim explicitly to cash-flow timing and drop the fragility framing to a single referenced sentence.
location: §VI.A .tex:538–540; Appendix L .tex:1328
verified: true — the paper cites `jiang2023`'s ≈\$2 trillion of bank mark-to-market losses (.tex:108) but puts no mark-to-market number on SOMA, and Appendix L .tex:1328 explicitly declines option-adjusted duration and convexity as out of scope ("I deliberately price extension rather than convexity").
fix: The cheap branch is the second: restrict §VI.A's institutional-cost claim to cash-flow timing and cut the fragility framing to one sentence citing `jiang2023`. The expensive branch (a DV01/market-value image of 0.6 WAL-years on the \$1,940.9bn book) needs a discount curve the design does not carry, and Appendix L's scope declination would have to be reopened — recommend the wording branch unless Eugene wants the run.

### C-R3-18
raiser: R3
severity: MAJOR (MAJOR 5, closing note)
class: WORDING
panel_lines: 119
condition: The denominator choice cuts against the paper's own subject: "most of the shortfall is mechanical" is substantially a statement about where the FOMC put the ceiling, not about mortgage markets, so leading with it understates lock-in relative to the benchmark the paper itself judges more faithful.
location: abstract .tex:31; §VIII .tex:725, .tex:731; §III.B .tex:150
verified: partly — the substance is already conceded in the same breath as the claim (.tex:725: "the shortfall against the phased caps is mostly mechanical, because the caps sat far above what any plausible prepayment environment would have delivered"), and §III.B .tex:150 makes the cap-placement point directly. What is missing is the inference: that the mechanical-majority headline is therefore a statement about cap placement rather than about mortgage-market behavior, and that leading with it understates lock-in against the E-benchmark.
fix: One clause where the mechanical-majority result is first stated (abstract, then §VIII): name it as a fact about cap placement, and point to the E-benchmark share (C-R3-15) as the reading that is about mortgage markets. Largely a re-ordering of sentences already present.

### C-R3-19
raiser: R3
severity: MAJOR (MAJOR 6, defect (a) + fix (a))
class: WORDING
panel_lines: 125–129, 147
condition: "Mechanical" mislabels a null whose level is set by a floor read off realized deep-discount turnover — a mixture the paper itself says is plausibly less than half strictly involuntary. Table 1's row label "Mechanical null, β₁=0" and the surrounding vocabulary must be renamed to "no-elasticity null" or "observed-turnover null".
location: Table 1 row label .tex:78; label also at .tex:92 (definitions), and the partition-carrying uses at .tex:44 (×2), 58, 60 (×2), 98, 110 (×2), 150 (×4), 227, 277, 319, 323, 528, 538, 542, 546, 721, 725, 731 (×2), 745, 1100
verified: true — "mechanical" occurs 43× in the .tex (42 lowercase + 1 capitalised). About 30 of those carry the partition; the remainder are ordinary-language ("mechanically inflates", "near-mechanical strength", "mechanical enforcement", "the mechanical reason", .tex:635's "the shift is mechanical", .tex:1340's "structural or mechanical") and must be left alone. The abstract hedges once, exactly as R3 says (.tex:31: "baseline turnover (itself read from realized, partly behavioral turnover)"). Note: this is a *different* word from the one already renamed in an earlier round — .tex:92 shows "baseline turnover floor" is already the global name, with "(sometimes called an involuntary-turnover floor)" as the retired label.
fix: Global rename of the partition-carrying uses only, starting with Table 1's row label; keep the ordinary-language uses. Requires a per-site pass, not a blind replace-all, and a gate-span check (the .tex:92 definitions paragraph and .tex:150's "mechanical-majority threshold" are both quoted in gate spans).

### C-R3-20
raiser: R3
severity: MAJOR (MAJOR 6, fix (a))
class: WORDING
panel_lines: 129, 147
condition: One sentence must state what the partition actually is — a model carrying observed baseline turnover versus the imported elasticity's increment above it, not mechanics versus behavior — and the word must be defined where it is first used, because a policy reader takes "most of the shortfall is mechanical" as "not behavior".
location: first use .tex:44 (§I: "partitions the realized shortfall between an elastic channel and a mechanical baseline … Most of the shortfall is mechanical"); definitions paragraph .tex:92
verified: true — "mechanical" is never defined. .tex:44 uses it twice without definition; the "Definitions used throughout" paragraph (.tex:92) defines "baseline turnover floor", "trapped liquidity"/"shortfall" and "lock-in marginal", and calls the null the "$\beta_1 = 0$ mechanical null" without defining "mechanical"; the closest thing to a gloss is .tex:319's parenthetical "(the mechanical model with the lock-in elasticity switched off)", which defines it by construction rather than by content. The mixture disclosure exists but is attached to the floor (.tex:92 and .tex:227), not to the word.
fix: Add the partition sentence to .tex:92's definitions paragraph and a first-use gloss at .tex:44 tying "mechanical" to "elasticity switched off, baseline turnover held at its observed level" — explicitly not "non-behavioral". This pairs with C-R3-19; landing one without the other leaves the overclaim.

### C-R3-21
raiser: R3
severity: MAJOR (MAJOR 6, defect (b) + fix (b)); R3 flags this as one of two items that would *strengthen* the paper
class: RUN
panel_lines: 131–147
condition: The 2018 depth ladder is spent as a robustness band on a floor *level* and its *shape* is never read. Exposure-weighted differencing of the nested reads gives a step-then-plateau — 7.1% / 7.0% / 4.7% / 4.7% / 4.9% across the (−0.25,0], (−0.50,−0.25], (−0.75,−0.50], (−1.0,−0.75] and ≤−1.0 bins — which is what a floor on total turnover looks like and what an additive competing-risks form does not predict. It is out-of-window, out-of-episode, own-data evidence on the paper's largest open fork, and it points toward the max form the paper uses.
location: `matched_depth_reconciliation_results.json`; the level reading is at §VII.F .tex:713; the fork is settled on semantics at .tex:709
verified: true — every ladder value R3 prints reproduces exactly from `step2_matched_depth_grid.OFF_2018_rising_rate`: gap ≤0 → 5.334% / \$1,264.5bn / 155 cohort-months; ≤−0.25pt → 4.991 / 1,058.1 / 137; ≤−0.50 → 4.695 / 921.4 / 125; ≤−0.75 → 4.722 / 453.5 / 107; ≤−1.00 → 4.869 / 143.4 / 95, with `exposure_share_of_gap0` = 0.113374 at the deepest cut (R3's 0.113 ✓). I re-derived the binned figures independently and got 7.09 / 6.99 / 4.67 / 4.65 / 4.87 — R3's arithmetic is right. The .tex already prints all five *nested* reads (.tex:713: "the two additional reads (4.722\% at gap $\leq -0.75$ points, 4.869\% at gap $\leq -1$ point) fall strictly inside it"), so what is genuinely absent is the binning, the exposure shares, the standard errors, and the shape reading. The semantics-not-fit settlement R3 quotes is verbatim at .tex:709.
fix: Re-bin the committed nested reads by exposure-weighted differencing and add a short exhibit with per-bin CPR, exposure share and stratum-cluster standard errors, plus R3's four hedges stated in the note: 2018 gaps are shallow against the window's −380bp; the ≤−1pt bin carries only 11.3% of the gap-≤0 exposure; deeper cuts shift vintage and coupon composition; the shallow bins plausibly carry refinancing, the same confound §V.E names for `episode_confrontation`. Standard errors are the only new computation (the CPR bins are arithmetic on committed fields), so this needs a spec header and a parity gate reproducing the five nested reads.

### C-R3-22
raiser: R3
severity: MAJOR (MAJOR 7, fix (i))
class: WORDING
panel_lines: 151–159
condition: Because 99.53% of exposure sits below the window-minimum market rate, the marginal's sign is fixed by the rate configuration, so the design's central quantity is *not identified* in an episode with mixed rate gaps. No scope condition states this, and the same holds for the Danish gap ("could not have come out otherwise").
location: §V.E .tex:323 (sign-forcing statistics); §VI.D .tex:590 (the Danish sign invariance)
verified: true — .tex:323 prints "97.40\% of exposure at or below 4.79\% and 99.53\% at or below 5.09\%, against a window-minimum 30-year rate of 5.2311\%" and demotes the 27-cell positivity check; `sign_forcing_stats_results.json` confirms `exposure_share_le_5_09_pct` = 99.5297 and `window_min_mortgage30us_pct` = 5.2311. .tex:590 states the Danish sign "could not have come out otherwise". No inequality-form scope condition appears at either site.
fix: State the scope condition as an inequality in §V.E: the decomposition is informative only where the book's out-of-the-money share is high enough that the sign is not at issue, and it is not identified in a mixed-gap episode — so the exercise cannot serve as a falsification test in another cycle, country, or portfolio. Attach the same sentence to the Danish sign-invariance statement at .tex:590.

### C-R3-23
raiser: R3
severity: MAJOR (MAJOR 7, fix (ii)); repeated as cross-disciplinary opportunity 3
class: STRUCTURE
panel_lines: 157–159, 189
condition: Du et al.'s seven-central-bank QT record is cited once and never used. Whether the cap-above-achievable-runoff pattern generalized across those seven central banks is a one-page extension on public data, and it is the difference between an episode study and a general result about runoff-cap design — on R3's reading the paper's most exportable contribution.
location: §II .tex:114 (the single `du2024` citation)
verified: true — `du2024` occurs exactly once in the .tex (.tex:114, "assemble the cross-country QT record---seven central banks, active and passive runoff---and find announcement effects concentrated in yields") and is used only to place the paper in that literature. `du2024` is already in `references.bib` (line 615); nothing to add to the .bib.
fix: Add a short subsection (or a §VI.B paragraph) asking whether other central banks' passive-runoff caps were similarly non-binding, using the Du et al. record as the frame, and stating what data would settle it (per-bank announced caps against realized redemptions). Do not assert the generalization — R3 asks for the question and the data requirement, which costs no run.

### C-R3-24
raiser: R3
severity: MAJOR (MAJOR 7, fix (iii))
class: WORDING
panel_lines: 155, 159
condition: §VIII's recurrence claim — severe duration extension "should be expected to recur in future tightening cycles that begin … with a large outstanding stock of deeply in-the-money mortgages" — is plausible but nothing in the design supports it; it must be downgraded to a conditional statement about the stock, explicitly labelled as outside what this design tests.
location: §VIII .tex:731
verified: partly — the sentence already carries a state-dependence qualifier ("the state dependence documented by \citet{berger2021} and \citet{eichenbaum2022} makes the extension conditional on that stock, not on tightening per se"), so the conditionality is present; what is missing is the explicit label that the recurrence claim is outside what the design tests, which is R3's actual ask.
fix: Add the out-of-scope label to the existing conditional clause (one phrase); no new content.

### C-R3-25
raiser: R3
severity: MINOR 1
class: CHECK
panel_lines: 165
condition: A committed artifact carries a reading the manuscript retracts: `extension_risk_results.json`'s `lag_interpretation` asserts the hazard CPR leads SOMA and attaches a 45–90d TBA settlement explanation, which §V.B reverses. A reader consulting the replication package gets the superseded reading.
location: `hazard/data/extension_risk_results.json` field `lag_interpretation`; §V.B .tex:275 and .tex:305; Appendix A = `app:ledger` (.tex:756ff)
verified: true — the artifact field reads verbatim "Negative lag = hazard CPR leads SOMA empirical CPR. Consistent with 45-90d TBA settlement delay between Freddie loan-level prepay and NY Fed SOMA cash receipt", while .tex:275 states "a peak at $k=-3$ means the simulated path \emph{trails} the empirical path by three months" and .tex:305 states "I therefore attach no settlement interpretation to the timing alignment." The .tex references `app:ledger` for the in-print inversion but never names `extension_risk_results.json` or the field (0 hits for the filename anywhere in the .tex).
fix: Prefer the Appendix A bullet (naming the file and the field and stating the superseded reading), since editing a frozen artifact's documentation string touches a SHA-pinned replication object; if the string is corrected instead, the manifest pin and any gate hashing that file must be re-checked.

### C-R3-26
raiser: R3
severity: MINOR 2
class: WORDING
panel_lines: 167
condition: The tax-law override of Berger et al.'s 22%/15% U.S. counterfactual is stated more flatly than the law supports (it omits the IRC §108 exclusions — qualified principal-residence indebtedness, insolvency — that bear on exactly this fact pattern) and is the wrong kind of input for a transplant: in a transplant counterfactual U.S. tax treatment is a legislative choice, not a datum, so using it to shrink the refinance-in-place channel lets a policy-design parameter do the work of evidence — in the direction that preserves the ≈0 pin the paper's own Danish redemption data then contradicts.
location: §VI.D .tex:586
verified: true — .tex:586 carries the override verbatim ("a characterization U.S. law does not support: a discount extinguishment is cancellation-of-debt income at ordinary rates, IRC \S 61(a)(11), and post-TCJA the assumed interest deduction overstates most households' marginal benefit; both corrections push the U.S.-transplant channel \emph{below} Berger et al.'s already-small estimate"). The .tex contains no occurrence of "\S 108" or "insolven", confirming the omission.
fix: Reclassify the tax attenuation in the text as a design parameter rather than a datum, and move the legal reading to a footnote that adds the §108 qualified-principal-residence and insolvency exclusions as caveats on the ordinary-rate characterization.

### C-R3-27
raiser: R3
severity: MINOR 2
class: CHECK
panel_lines: 167
condition: Present the Danish institutional gap across both tax regimes rather than only at the U.S.-tax-attenuated anchor, using the existing sweep.
location: run `danish_refi_finegrid`; §VI.D .tex:590, .tex:595; Table 13 row .tex:613
verified: partly — the sweep exists and is committed (.tex:590: "swept in 0.25\%-CPR steps under the production anchor, the gap runs from $+\$61.2$ billion at 0\% to $+\$256.8$ billion at 3\%"; also .tex:595, .tex:613, run index .tex:831), but it parameterizes the *refinance-in-place CPR*, not a tax regime. Presenting "both tax regimes" therefore requires mapping each regime to a point (or interval) on that CPR axis — a mapping the paper does not currently make; the U.S. regime is the marked ≈0 anchor and the Danish-tax realization is the 22.4%/yr realized-implied read that .tex:590 places above the swept range entirely.
fix: Read the existing sweep at two named points and print both: the U.S.-tax-attenuated anchor (≈0 refi-in-place, +\$61.2bn) and a Danish-tax point justified from the committed `danish_redemption_validation` read, stating explicitly that the axis is refi-in-place CPR and the regimes enter only through that input. No new run if a defensible Danish-tax point already lies on the 0–3% grid; a new grid point if not.

### C-R3-28
raiser: R3
severity: MINOR 3
class: WORDING
panel_lines: 169
condition: The abstract is 246 words in two paragraphs, and the *second* paragraph carries the actual headline (the range, the anchor convention, the form-conditionality). R3 asks for one abstract, ≤200 words, leading with the two denominators of MAJOR 5.
location: .tex:31 (single 1,552-char line containing an explicit `\par`)
verified: true — the line is 246 words by my count (matching R3 exactly) and contains an explicit `\par`, so the two-paragraph structure is real. Note anti-condition 2 concerns the opposite claim ("the abstract is a single paragraph"), which is the false one; R3's reading is correct.
fix: Compress to one ≤200-word paragraph leading with the marginal against both denominators (C-R3-15). Caution: the abstract carries pinned spans — the "$+2.9$ to $+8.7$" binding interval, the "85.7\%" and "91.3\%" levels, and the hedged "(itself read from realized, partly behavioral turnover)" clause that is the only hedged use of "mechanical"'s premise — so a rewrite must preserve those and be re-checked against the gate suite. A long-abstract variant already exists (`revised_paper_v18_long_abstract.tex`), which is the natural home for anything cut.

### C-R3-29
raiser: R3
severity: MINOR 4
class: REFERENCE
panel_lines: 171
condition: §VI.C (assumability/portability) — the live U.S. policy proposal (FHFA) — rests on "Fixed-income analysis suggests" with no citation, no magnitude and no run, in a paper that quantifies everything else.
location: §VI.C .tex:578–580 (a single 917-char paragraph)
verified: partly — the uncited hedge is verbatim at .tex:580 and the span contains **zero digits**, so R3's "the one un-numbered section" is true under the reading "carries no quantities" (the section *is* numbered VI.C in both the .tex `\subsection` and the markdown edition's `### VI.C`, so the literal "un-numbered" reading is false). No `\cite` appears in the span.
fix: Replace "Fixed-income analysis suggests" with a cited basis — FHA/VA assumption-volume evidence (e.g. Ginnie Mae issuance/assumption reporting or an FHFA analysis of assumable-mortgage take-up). This is the one place R3 asks for a reference that is **not** already in `references.bib`; the specific source is not named in the report, so it has to be selected and verified before it can be cited.

### C-R3-30
raiser: R3
severity: MINOR 4
class: WORDING
panel_lines: 171
condition: §VI.C must connect to the paper's own 20.4% statutory-assumability share and state plainly that the design cannot score take-up, so the section reads as a taxonomy rather than as a finding.
location: §VI.C .tex:580; the share and the take-up concession are at §I .tex:52
verified: partly — the concession already exists, but in §I, not §VI.C: .tex:52 states "the FHA/VA loans backing Ginnie Mae pools (20.4\% of the SOMA book) are assumable by statute … Realized take-up of that statutory right is not measured anywhere in this design, so the 20.4\% share bounds the carve-out from above rather than sizing it." §VI.C itself references neither the share nor the concession.
fix: Two clauses in §VI.C: cross-reference the 20.4% statutory-assumability share (already committed, quoted at .tex:52, .tex:146, .tex:269, .tex:271, .tex:1267) and restate the take-up concession at the point the policy proposal is evaluated, labelling the subsection a taxonomy.

### C-R3-31
raiser: R3
severity: MINOR 5
class: STRUCTURE
panel_lines: 173
condition: Table 1 omits the duration extension, one of the two objects §VIII's conclusion actually compares. (The household-side row is C-R3-03.)
location: `tab:headline` .tex:64–90; the numbers exist at `tab:wal` .tex:553–575 and Appendix L .tex:1328
verified: true — Table 1's nine rows contain no WAL/duration row; the 9.4-year empirical WAL, the 3.4-year comparator, the 6.0-year extension and the 0.6-year rule-only shortening are all committed elsewhere.
fix: Add a duration row to Table 1 quoting the 9.4-year empirical WAL against the 3.4-year 2021-speed comparator (6.0-year extension) with the 0.6-year rule-only shortening as the marginal's share, all repeating committed figures — Table 1's own convention ("every value repeats a committed, gated figure").

### C-R3-32
raiser: R3
severity: MINOR 6
class: WORDING
panel_lines: 175
condition: "Trapped liquidity" is defined precisely as a net shortfall against a ceiling, but for readers outside MBS it connotes a resource loss, and it appears in that role at headline sites. Prefer "cap shortfall" in headline sentences and reserve "trapped liquidity" for the internal accounting object.
location: definition at .tex:92; 35 occurrences overall (32 lowercase + 3 capitalised), including Table 13's sign convention note and §V.B/§VII sites
verified: true — .tex:92 defines it ("``Trapped liquidity'' and ``shortfall'' denote the net shortfall of realized roll-off against the phased redemption caps"); the term is used 35× including at headline and table-note sites.
fix: Per-site pass replacing headline uses with "cap shortfall" while leaving the accounting-object uses (artifact names, table sign conventions, run labels) intact. Check gate spans before editing — several quoted spans contain the phrase.

### C-R3-33
raiser: R3
severity: MINOR 7
class: REFERENCE
panel_lines: 177
condition: The labor-reallocation leg has no magnitude at all: Hsieh–Moretti is cited for mechanism only (correctly, given the published correction), but no surviving magnitude is substituted, so the welfare argument's one remaining quantitative leg is empty.
location: §VI.A .tex:542
verified: true — .tex:542 carries "their headline magnitudes are cumulative level effects over 1964--2009 and were revised in a published correction, so I cite the mechanism rather than a point estimate", and no per-move or per-household surplus magnitude appears anywhere in the paper ("per household" = 0 hits).
fix: Either cite a per-move surplus estimate that survives scrutiny (R3 names none, so the source must be selected and verified — this is the second reference not already in the .bib), or state in the same sentence that invokes the leg that it is unquantified in this design. The second branch costs nothing and is consistent with the paper's existing declination discipline.

### C-R3-34
raiser: R3
severity: MINOR 8
class: META
panel_lines: 179
condition: Reading burden is a reviewability problem: a 139-page paper that needs an author-supplied navigation map to be refereed has a structural problem, not a length problem.
location: .tex:94 ("How to read this paper" / "The short path for a referee")
verified: partly — the referee short path exists verbatim at .tex:94 and R3 credits it as helpful and honest; the 139-page count is R3's and I did not independently verify it (the PDF's page tree is in compressed object streams, and page count is not itself a condition).
fix: No text edit implied by itself; this is R3's framing for C-R3-35 and for the split/venue decision already in Eugene's queue. Record and route to the length/venue call rather than to a drafting task.

### C-R3-35
raiser: R3
severity: MINOR (inferred from the Writing Quality score cell, 58/100)
class: STRUCTURE
panel_lines: 179, 207
condition: Density is carrying qualification load that structure should carry: the longest body paragraph is 14,732 characters (~2,250 words), the next three 11,312, 10,696 and 8,051; in the markdown edition one paragraph runs 1,618 words across 38 sentences at a mean of 42.6 words per sentence (max 111) with 14 parentheticals and 12 em-dash asides. A reader cannot extract the argument at the rate it arrives.
location: .tex:219–231 (14,732 chars, §V.B Path B); .tex:319–323 (11,312, §V.E); .tex:1099–1100 (10,696); .tex:269 (8,051, §V.B)
verified: true — I reproduced all four measurements exactly by joining consecutive non-blank lines between blank-line boundaries: 14,732 / 11,312 / 10,696 / 8,051, in that order. One attribution slip: R3 labels the 10,696 block "Appendix G", but .tex:1099–1100 falls inside Appendix F (`app:patha-detail`, .tex:1089); Appendix G is `app:ridge` at .tex:1168.
fix: Split the four blocks at their existing internal seams (each already runs "First… Second… Third…"), promoting the enumerations to `\paragraph` heads or a table where the content is a list of qualifications. High collision risk: .tex:219–231 and .tex:319–323 contain many gate-quoted spans and the pinned round-28 lead; any split must preserve span text byte-identically and leave numeric tokens intact.

### C-R3-36
raiser: R3
severity: MINOR (cross-disciplinary opportunity 2; R3: "arguably the most publishable result in the paper" for this audience)
class: STRUCTURE
panel_lines: 187
condition: The distributional result is buried inside a homogeneity check that is presented as evidence a verdict label carries no information. Per-balance intensities tilt toward sub-740-FICO (1.23–1.26×) and above-80-LTV (1.23×) borrowers against a placebo whose twelve random partitions span only 0.011 — a distributional finding about who bears the mobility cost, established against a proper placebo. Promote it, with the placebo caveat intact.
location: §V.E .tex:325
verified: true — .tex:325 carries all three figures verbatim: "The mild tilts run toward below-740-FICO ($1.23\times$--$1.26\times$) and above-80-LTV ($1.23\times$) borrowers, with regional intensities spanning only 0.93--1.06", and the placebo comparison "the widest of the twelve spans 0.011 --- while the economic groupings span 0.381, more than thirty times wider" (run `subgroup_marginals_placebo`).
fix: Promote to a named paragraph (or a short exhibit) with a distributional-incidence framing, carrying the placebo caveat and the "structure, not sampling noise" reading already in the text. Zero new numbers; a re-siting and a heading.

### C-R3-37
raiser: R3
severity: MINOR (cross-disciplinary opportunity 4)
class: STRUCTURE
panel_lines: 191
condition: The general methodological lesson — "a calibrated floor's functional form can double a policy-relevant marginal" — is left in §VII.F prose, and the mixture curve (s from hard maximum to additive) is a clean, portable device for exposing it. It deserves a named paragraph, not a robustness aside.
location: §VII.F .tex:709 (the `floor_form_mixture` curve and the semantics-not-fit settlement)
verified: true — the curve and the lesson are both in §VII.F running prose (.tex:709: +7.5 at s=0.1, +9.7 at s=0.25, +10.7 at s=0.4, flat near +11.2 from s=0.6, against the central leg's recovery falling 91.3%→55.9%); `floor_form_mixture_results.json` confirms the endpoints (max 42.608 vs additive 85.705 at the 4.991% floor — very nearly exactly a doubling) and that the endpoints run through production code paths.
fix: Give the lesson a named paragraph (in §VII.F or in the limitations) stating it as a transportable warning for calibrated policy counterfactuals, with the mixture curve named as the device. Text-only; the numbers are committed.

### C-R3-38
raiser: R3
severity: MINOR (cross-disciplinary opportunity 5; also Strength 2)
class: META
panel_lines: 193
condition: The adverse-findings register — committed rule, outcome, adjudication with direction — is a better answer to the garden-of-forking-paths problem in calibration work than most pre-registration templates, and it is currently Appendix O of a 139-page paper. It would stand alone as a short methods note.
location: Appendix O = `app:verdicts`, .tex:1393–1427 (Table 27 = `tab:verdicts`, .tex:1400)
verified: true — the register exists at `app:verdicts` with the framing sentence R3 praises; I did not independently count its rows (R3 says 27) because the table packs multiple rows per source line. Anti-condition 3 applies to a different claim about this table ("not one Table 27 row moved a reported number"), which R3 does not make — R3 correctly credits the register with retracting the bootstrap understatement, the 0.2-point convergence, the 18.3-point basis-mixing error and the 27-cell positivity check.
fix: No manuscript edit. Route to the venue/spin-off decision already in Eugene's queue as a candidate standalone methods note.

### C-R3-39
raiser: R3
severity: MINOR (cross-disciplinary opportunity 6)
class: REFERENCE
panel_lines: 195
condition: Lock-in's most-discussed housing-policy consequence is the inventory channel and its incidence on first-time buyers and renters. The manuscript mentions inventory once in passing and cites Graybill–Mangum (2026), whose setting is exactly housing-market equilibrium; one sentence connecting the two would locate the paper in housing economics rather than only in MBS mechanics.
location: §I .tex:56 (the passing inventory mention); `graybill2026` cited at .tex:100, .tex:261, .tex:277, .tex:329
verified: partly — "inventory" occurs twice, not once: the §I passing mention at .tex:56 ("compounded by historic housing inventory shortages and depressed consumer sentiment") and a technical use in the ABM friction appendix (.tex:919, Active Listing Count shortfall). `graybill2026` is already in `references.bib` (line 644) and cited four times, already described as "in a housing-market-equilibrium setting" (.tex:277) — so nothing to add to the .bib. No renters/first-time-buyer incidence sentence exists anywhere.
fix: One sentence in §I (at .tex:56's inventory mention) or in §VI.A connecting the mobility constraint to the inventory channel and its incidence on entrants, citing `graybill2026`'s housing-market-equilibrium setting. Existing key, no new bib entry.

### C-R3-40
raiser: R3
severity: inferred (Argument Coherence score cell, 68/100 — listed as a structural deduction, no fix supplied)
class: WORDING
panel_lines: 206
condition: The title says "Shortfall" while §III.B declines to call it a policy miss; the tension between the two should be resolved or acknowledged.
location: title .tex:24 ("Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall"); §III.B .tex:150
verified: true — both sites are as R3 describes; the .tex:92 definitions paragraph does define "shortfall" as the net shortfall against the phased caps, which is the defence, but the title carries the connotation unqualified.
fix: Either add the definitional gloss to the abstract's first sentence (the shortfall is a gap against a ceiling, not an established policy miss — .tex:150's standing concession) or accept the tension explicitly at .tex:150. Retitling is the expensive option and R3 does not ask for it.

### C-R3-41
raiser: R3
severity: inferred (Argument Coherence score cell, 68/100)
class: WORDING
panel_lines: 206
condition: §VIII concedes the trilemma dissolution "reduces to 'the marginal is small'", which is form-conditional; the conditionality should be marked at the concession.
location: §VIII .tex:731
verified: partly — the conditionality is already stated at the site: ".tex:731: ``(2) and (3) do not trade off sharply'' reduces to ``the marginal is small''---and under the production floor form the marginal is bounded small by construction", followed by the hard-maximum argument. What is absent is a pointer to the additive form's +11.2 counterweight at that sentence.
fix: One clause pointing to the additive form's member (+11.2 points, floor-invariant) so the reader sees the dissolution's form dependence at the concession rather than only in §VII.F. Largely discharged already — lowest priority of the R3 set.

### C-R3-42
raiser: R3
severity: MINOR (Carroll Round judgment)
class: META
panel_lines: 223–225
condition: The presentation layer needs a one-slide answer to "what is the household side worth, in the same units?", because an undergraduate international-economics audience will ask the welfare question the paper declines.
location: n/a (talk deck, not the manuscript)
verified: true — follows from C-R3-01/02/03; R3's overall Carroll judgment is "Ready to present and defend as-is", so this is additive, not blocking.
fix: One slide carrying the C-R3-02 foregone-payoff count with its floor band and moving-share bracket, the Batzer \$2.4trn and the \$61.2bn institutional gap side by side, and an explicit "this side is imported, not measured here" line.

### C-R3-43
raiser: R3
severity: MINOR (Carroll Round judgment)
class: META
panel_lines: 223–225
condition: The presentation layer needs a one-slide cap-design deliverable in \$bn/month, because the audience will ask the policy question the paper leaves in design space.
location: n/a (talk deck, not the manuscript)
verified: true — follows from C-R3-14 (and C-R3-13 if the two-input table lands).
fix: One slide: achievable ex-ante passive MBS principal ≈\$17.6–20.0bn/month against the \$33.75bn/month average ceiling, ±≈\$3.6bn/month from the floor read's own sampling interval, with the substitution instrument as the design implication.

---

## Not recorded as conditions (score-cell criticisms with no requested fix)

Recorded here so the coordinator can see they were read and deliberately not turned into rows. Each is a scoring basis in R3's Methodological Rigor (64) or Evidence Sufficiency (61) cell, stated as a reason for the grade with no accompanying remedy, and in every case R3 notes the paper already discloses it:

- coverage propagated by pushing wild-t endpoints through a PCHIP interpolant of a frozen sweep;
- 31 nominal / 5.9 effective clusters, max leverage 0.33, carrying the binding interval (Table 9 notes);
- the second estimator supplying no differential (+270.4 vs −105.3, sign disagreement);
- Path A's coefficient not distinguishable from zero under any bias-respecting construction;
- the imported elasticity's specification range propagated with no standard error;
- the PSA convention sweep (+0.9 to +15.6) dwarfing the quoted interval;
- two independent floor reads (5.51% age-standardized, 5.52% Fannie) sitting above the clean band and implying a marginal below the +4.3 edge (R3 credits the existing "soft lower edge" concession);
- four clip-induced zero months in the benchmark's monthly series (disclosed in Appendix N);
- 51.0% face coverage with Freddie conventional hazards extrapolated to 20.4% Ginnie and 33.7% out-of-window vintages.

One naming slip in the Originality cell, not a condition: R3 attributes the ex-ante-projection observation to "York 2022". The key is `nyfed2022` (cited at .tex:546); there is no `york2022` in the .bib and no such string in the .tex — it is an artifact of reading "New York Fed" through the markdown edition.

## Anti-conditions

R3 raises **none** of the ten adjudicated anti-conditions as its own condition. Two touch the list and both come out on the correct side:

- Anti-condition 2 ("the abstract is a single paragraph" — false): R3 says the abstract is 246 words *in two paragraphs*, which is what .tex:31's explicit `\par` shows. C-R3-28 is recorded on the true premise.
- Anti-condition 8 ("40,234 active at window start"): R3 uses 40,234, which is the number the manuscript prints (.tex:1085 attrition accounting, plus .tex:219/275/1026/1063), but attributes it to `loan_sample.parquet`, whose `balance > 0` count is 40,077. C-R3-02 is recorded verified:partly on that basis and instructs against swapping the number.
