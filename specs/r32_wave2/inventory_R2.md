# Round-32 condition inventory — Reviewer 2 (Domain: MBS prepayment modeling, agency-MBS/SOMA operations, comparative mortgage institutions)

Source: `REVIEW3_v18_panel_2026-07-29.md`, lines 435–665.
Manuscript verified against: `paper/v18/revised_paper_v18.tex` (1,429 lines), `paper/v18/references.bib` (70 entries), `hazard/data/*.json`, `hazard/*.py`, `tools/liveness_gates.py`, `tests/*.py`. No repo script executed; nothing in the worktree modified.

Table-number crosswalk used below (R2 numbers ↔ labels, resolved from `\label{tab:...}` order): T1 `tab:headline` (.tex:67), T2 `tab:specbox` (195), T3 `tab:params` (239), T4 `tab:floorband` (289), **T5 `tab:assembly` (338)**, T6 `tab:oosfloor` (362), T7 `tab:lowband` (386), T8 `tab:uncertainty` (422), T9 `tab:ladder` (445), T10 `tab:estimators` (478), T11 `tab:bases` (505), T12 `tab:wal` (553), T13 `tab:danish` (605), **T25 `tab:composition` (1272)**, T27 `tab:verdicts` (1400).

---

### C-R2-01
raiser: R2
severity: MAJOR (M1, fix (i) first clause)
class: WORDING
panel_lines: 481–505
condition: The manuscript must state the loan pool's actual allocation rule — equal allocation per quarterly origination file, not proportional to origination volume or to SOMA book face — at the place it describes the sample (Appendix E / `app:params`).
location: `paper/v18/revised_paper_v18.tex:1085` (Appendix E attrition paragraph); descriptors at .tex:122, .tex:202 (T2 `tab:specbox`), .tex:219, .tex:275
verified: true — `hazard/loan_sample.py:97` is `per_file = max(1000, pool_target // max(len(pairs), 1))` with `k = min(per_file, len(df))` at :103 inside the per-file-pair loop, i.e. equal allocation per quarterly origination pair; `_stratified_sample` (:110) is proportional only *within* the resulting pool. The .tex says only "stratified 75,000-loan sample drawn from that universe" (122) / "stratified 75{,}000-loan draw from the same universe" (202); the strings "equal allocation", "per origination quarter", "per quarterly" appear **zero** times in the manuscript, and .tex:1085 states attrition (34,734 prepaid, 32 defaulted, 40,234 active) but not allocation.
fix: Add one sentence to Appendix E, e.g. R2's own wording: "the pool is drawn with equal allocation per origination quarter, so the draw's vintage composition is approximately uniform over 2017–2021 and is not proportional to origination volume or to book face." Pure disclosure; no committed number moves; no gate span touched (no gate pins the .tex:1085 paragraph text).

### C-R2-02
raiser: R2
severity: MAJOR (M1, fix (i) second clause)
class: STRUCTURE
panel_lines: 483–505
condition: T25 must show the *draw's* own composition beside the estimation-universe panel, so the reader can see the draw is neither the universe nor the book.
location: T25 `tab:composition` panel (a), .tex:1279–1283 (vintage row 1281, coupon row 1282)
verified: true — `composition_shift_results.json` holds all three objects: `freddie.sample.vintage_year_shares_upb_weighted` = 17.84/17.94/19.73/22.17/22.32% (2017–2021), `freddie.universe_panel.vintage_group_shares_exposure_weighted` = 12.47/37.28/50.25% (2017-19/2020/2021), `committed_anchors.vintage_shares` (book face) = pre2017 10.6 / 2017-19 6.0 / 2020 16.3 / 2021 43.9 / 2022 23.1. Panel (a) currently prints only the universe and the book (.tex:1281). R2's draw-count row (20/20/20/20/20) is corroborated by the UPB row matching his figures exactly.
fix: Add a third column (or a stacked sub-row) to panel (a) carrying the draw's vintage and coupon shares with the weighting basis named. Overlaps C-R2-06 — do both in one table edit. Note the *count* shares (15,000/vintage) are a parquet fact, not in the artifact; either cite `loan_sample.py`'s allocation rule for them or print the artifact's UPB-weighted row instead.

### C-R2-03
raiser: R2
severity: MAJOR (M1, fix (ii)) — R2's own "three of my eight can move the reported headline point"
class: RUN
panel_lines: 496–505
condition: The central/null pair must be scored once on a pool post-stratified to the SOMA book's coupon × vintage-group cells, and the resulting marginal reported with its direction, so the headline stops being "+5.6 points of the benchmark" computed on a pool that is not a probability sample of the book on the two dimensions that set censoring.
location: new run + entry in T5 `tab:assembly` (.tex:338) and §V.D `sec:identification`
verified: true — the composition gap is real and the censoring mechanism is the paper's own: 2021+2022 = 67.0% of book face (`committed_anchors.vintage_shares`) against 0% (2022) and ~22% (2021) of the draw; .tex:323 states the central leg is pinned at the floor in 68.8% of 1,683,124 loan-months and the null leg in 35.8%, both measured on the draw; .tex:269 shows `vintage_overlay` scores only the *out-of-window* 33.7% share to zero marginal (→ +3.7 points, pure 0.66× share scaling), leaving the in-window 2021 under-weighting uncovered; .tex:701 confirms the §VII.E coupon reweight rescales aggregate output ("shifts Path B from 107.0% to 109.1%") rather than re-simulating, and .tex:697 pins the marginal's bit-invariance under it — so R2 is right that it cannot test a censoring-mediated composition effect.
fix: Post-stratify the existing 75,000 draws to the SOMA coupon × vintage-group cells and re-run the central/null pair; R2 names `cross_design_reweight` as the analogous existing machinery, and `hazard/agents.py` already carries `vintage` on the pool (agents.py:~122, currently read only by `reweight_to_soma_coupons`), so the weighting hook exists. Would write a new `hazard/data/*_results.json` (e.g. `book_composition_marginal_results.json`) with the marginal, the two legs' bind shares on the re-weighted pool, and parity against the committed draw-based 68.8%/35.8%. Spec-before-run; the result lands whichever way it falls. Note: the 2022 and pre-2017 vintages have **zero** support in the draw (artifact gate `G1...vintage_range` = [2017, 2021]), so post-stratification can only re-weight 2017–2021 — the 33.7% out-of-window share stays covered by `vintage_overlay`, and that limit must be stated with the result.

### C-R2-04
raiser: R2
severity: MAJOR (M1, fix (iii))
class: WORDING
panel_lines: 505
condition: Once C-R2-03 exists, its result must enter the assembly with its sign, not sit in an appendix.
location: T5 `tab:assembly` (.tex:338) and the assembly prose at .tex:333
verified: true — `tab:assembly` is the assembly exhibit and .tex:333/433 are where corrections are listed with directions; no composition-of-the-draw entry exists in either today.
fix: One row in `tab:assembly` plus one clause in the .tex:333 assembly sentence, naming the direction. Conditional on C-R2-03; if C-R2-03 is not run, C-R2-05 is the honest substitute.

### C-R2-05
raiser: R2
severity: MAJOR (M1, fix, closing sentence)
class: WORDING
panel_lines: 505
condition: Absent the book-composition re-run, the headline must be stated as conditional on the draw's composition: "+5.6 points on a pool whose vintage and coupon composition differ materially from the book's, in directions that have not been signed," rather than "+5.6 points of the benchmark."
location: abstract .tex:31; T1 `tab:headline` marginal cell .tex:79; §V.D .tex:333
verified: true — the abstract at .tex:31 reads "Inside that range, +5.6 points, or \$42.6 billion, is the value at the calibration I headline" with no composition conditioning; the two limbs R2 signs (seasoning limb inflationary via the floor gate, gap-depth limb deflationary via `H(1−d)`) are nowhere signed in the .tex.
fix: Add the conditioning clause at the three quoting sites. This is the fallback, not the preferred fix — R2 explicitly says the run is available. Do **not** delete the existing disclosure language to make room.

### C-R2-06
raiser: R2
severity: MAJOR (M2)
class: STRUCTURE
panel_lines: 507–515
condition: T25 must stop presenting universe bucket shares and the draw's WAC as one object: print both rows, each labelled with which population and which weighting it describes.
location: T25 `tab:composition` coupon row .tex:1282; tablenote .tex:1294
verified: true (with the arithmetic caveat of anti-condition #7) — the printed 18.0/68.2/13.8 are exactly `freddie.universe_panel.coupon_shares_exposure_weighted` bucketed (0.0392+0.1410 = 18.03; 0.5481+0.1336 = 68.17; remainder 13.80), while the "3.9%" in the same note is `freddie.sample.mean_coupon_pct` = 3.8649, the 75,000-loan draw. Two populations in one row is confirmed. **Per anti-condition #7, R2's "the draw's ≥4.0% share is 53.7%, not 13.8%" is only PARTLY right**: 53.7% is the draw's ≥4.0% share *UPB-weighted on rounded coupon buckets* (I recomputed 53.68% from `coupon_shares_upb_weighted`), 58.2% count-weighted (recomputed 58.21% from `coupon_shares_count_weighted`), and 47.0% on raw coupons. The three-object confusion is real; printing "53.7%" unqualified would repeat the error in the other direction.
fix: Split the coupon row into two labelled rows — "Estimation universe (exposure-weighted, window open)" 18.0/68.2/13.8 and "75,000-loan draw" with its ≥4.0% share **and its basis named** (53.7% UPB-weighted, 58.2% count-weighted on rounded buckets) — and repair the .tex:1294 note so the WAC is attributed to the draw. Same table edit as C-R2-02. No gate pins these literals (`13.8`, `3.9\%` absent from `tools/liveness_gates.py`).

### C-R2-07
raiser: R2
severity: MAJOR (M2, fix, second clause)
class: WORDING
panel_lines: 509–515
condition: §VII.E must say which object the full-book reweight's origin (3.9%) is — the draw's WAC — since the shift it is displayed against in T25 is the universe's.
location: .tex:701, §VII.E `sec:robustness-hybrid` ("Cross-Foundation Checks: Hybrid Pipeline and Full-Book Weighting")
verified: true — .tex:701 reads "balance-weighted estimates on the Freddie sample's composition, whose weighted-average coupon (3.9\%) sits above the SOMA book's (2.49\%)"; "sample" here is the 75,000-loan draw (3.8649), and the sentence never distinguishes it from the universe panel that T25 displays. R2's "same class as the basis-mixing error Appendix A already retracted" is a fair analogy — the retraction is real (memory + `tab:verdicts`), though the retracted item was a coupon-basis mix, not a population mix.
fix: One clause: "…the 75,000-loan draw's own weighted-average coupon (3.86%, the object T25's WAC row reports; T25's bucket shares are the exposure-weighted estimation universe)…". Wording-only; the `100.4`/`98.1`/`107.0`/`109.1` literals in that sentence are gate-pinned (gate #106 `COUPON_CONVENTION_SPANS`, `tools/liveness_gates.py:~710-724`) and must survive byte-identically.

### C-R2-08
raiser: R2
severity: MAJOR (M3) — R2's one correction that moves the headline **up**
class: RUN
panel_lines: 517–525
condition: The off-window (2018) floor's dependence on the housing-activity *level* must be measured, and the marginal reported at an activity-matched off-window floor, so that the share of the demotion charged to "the window" is not silently charging a housing-cycle level effect to lock-in circularity.
location: §VII.F decomposition at .tex:713; T6 `tab:oosfloor` (.tex:362–375); T5 `tab:assembly` (.tex:338)
verified: partly —
  • TRUE: the floor is total deep-discount turnover, not involuntary-only, in the paper's own words (.tex:227 "discretionary life-cycle moves and cash-out refinancings alongside strictly involuntary events … the strictly-involuntary share … is plausibly well under half"; repeated .tex:92, .tex:709), so it is activity-level dependent by construction.
  • TRUE: the demotion split is as quoted (.tex:713 carries 20.874 / 7.438 / 73.7 / 26.3).
  • TRUE: the sizing anchor is already in the paper — .tex:102 states \citet{aladangady2024} attribute 44% of the 2021–22 mobility decline to rate-gap lock-in; 0.56 × 20.874 = 11.69 ≈ \$11.7bn = 1.53pp of \$764.7bn, and 5.6 + 1.5 = 7.1, in the upper half of [+2.9, +8.7] — R2's arithmetic reproduces exactly.
  • WRONG in one number: R2 says "the paper's own in-window read of 3.8–3.9% is almost exactly the off-window 4.99% scaled by that ratio (4.99 × 0.77 = 3.84)". The in-window reads printed in T6 are **4.00%** (in-window production, .tex:374) and **3.97%** (early-window calibration, .tex:375). The implied ratio is 0.795, not 0.77, and the "almost exact" coincidence is 0.13–0.16pp loose. The structural argument survives; the coincidence claim should not be quoted as printed.
  • NOT VERIFIABLE FROM THE REPO: the existing-home-sales levels (5.34M 2018 vs 4.09M 2023, 4.06M 2024) are external NAR data; "existing-home sales" appears nowhere in the .tex. They would have to be sourced before use.
fix: Measure the floor read's dependence on activity across the three 2017–2019 legs (which already differ in activity as well as rate regime — the legs and their splits are described at .tex:1312), instrument the activity level with something not driven by the coupon gap (R2 proposes new-home sales, the all-cash share, or the non-mortgaged share of existing-home sales), and report the marginal at an activity-matched off-window floor as a new row of T6 plus an assembly entry. Existing machinery: the floor-read path behind `tab:oosfloor` / `floor_sweep` / `oos_identification`; would write a new artifact (e.g. `floor_activity_match_results.json`). If not run, C-R2-09 is mandatory.

### C-R2-09
raiser: R2
severity: MAJOR (M3, fix, second half)
class: WORDING
panel_lines: 523–525
condition: The assembly's one-directionality must be attributed to its cause. Either the upward floor-side correction enters T5, or the manuscript states that the assembly is one-directional *because the one available upward floor-side correction was not run* — because "every correction I can measure … moves it down" is doing real rhetorical work.
location: abstract .tex:31; §I .tex:46; §V.D/E .tex:333; T5 `tab:assembly` (.tex:338)
verified: true — the posture sentence exists verbatim at three sites: .tex:31 "every correction I can measure to the baseline turnover floor or to the accounting basis moves it down within the range rather than up"; .tex:46 the same with "moves the value down within the interval"; .tex:333 "every correction to the floor or to the accounting basis moves the headline down" and "every correction listed above falls in its lower half". No entry in `tab:assembly` or at .tex:433 is signed upward on the floor side.
fix: Preferred: land C-R2-08 and add the upward entry. Otherwise add one clause at .tex:333 (and mirror it in the abstract's hedge) naming the un-run correction: the activity-matched floor read is the one available upward floor-side correction and it was not executed. Note this is a *disclosure addition*, not a deletion of the existing claim — the anti-gaming rule against silencing a criticism by deleting a disclosure applies in reverse here.

### C-R2-10
raiser: R2
severity: MAJOR (M4, fix (a))
class: WORDING
panel_lines: 527–545
condition: The Ginnie–Freddie differential's attribution must be restated on the window mean rather than on the single month where buyouts dominate: the majority of the excess speed is **voluntary**.
location: .tex:269, the clause "with the involuntary buyout channel (CDR 2.1\% versus 0.4\% in May 2025) supplying most of the structural difference"
verified: true — recomputed from `hazard/data/gmar_dec25_cpr_series.json` over the 42 months 2022-06…2025-11: CPR Ginnie 8.337 vs Freddie 6.200 (gap +2.137); CRR 7.295 vs 5.941 (gap **+1.354**, 63.4% of the CPR gap); CDR 1.161 vs 0.314 (gap +0.847, 39.7%). May-2025 is indeed the buyout-dominated month (CPR gap 2.84, CDR gap 1.71). R2's table reproduces to the third decimal.
fix: Replace the snapshot clause with the window-mean decomposition: voluntary (CRR) carries +1.35 of the +2.14-point mean CPR gap (63%), involuntary (CDR) +0.85 (40%), the two summing above the total by the extraction residual; May-2025 is the month where buyouts dominate and should be labelled as such if kept. No gate pins "structural difference" (0 hits in `tools/liveness_gates.py`); the artifact's own validation block (endpoint residuals ≤0.033pp, CPR≈CRR+CDR mean |0.040|pp) supports the new literals.

### C-R2-11
raiser: R2
severity: MAJOR (M4, fix (b))
class: RUN
panel_lines: 541–545
condition: The Ginnie leg must be scored with the imported elasticity *attenuated by the observed voluntary-speed differential*, not merely share-scaled to zero marginal — i.e. the 20.4% Ginnie share should generate a weaker marginal, measured, instead of none, assumed.
location: §V.B Ginnie overlay passage, .tex:271; the +4.4 / 0.797× marginal correction quoted at .tex:271 and .tex:433
verified: true, and cheaper than R2 knows — .tex:271 confirms the overlay scores the Ginnie share "by the observed Ginnie speed in *both* Path B legs", so that share contributes zero marginal, and "the marginal correction is pure conventional-share scaling ($0.797\times$), identical across the primary, voluntary-only, and placebo series". The same sentence shows a **voluntary-only (CRR) series is already wired into the overlay run** as a level variant — so the CRR differential R2 wants used as an attenuation factor is already loaded by the existing machinery.
fix: Re-run the Ginnie overlay with the elasticity on the Ginnie share multiplied by an attenuation derived from the measured CRR differential (Ginnie voluntary running 1.354pp *above* conventional over the window) instead of zeroing that share's marginal; report the resulting marginal beside the +4.4 share-scaled figure. Existing machinery: `ginnie_cpr_overlay` / `ginnie_overlay_offwindow`, already consuming `gmar_dec25_cpr_series.json`'s `crr` block. Would write a new artifact (e.g. `ginnie_overlay_attenuated_results.json`). Direction is not obvious ex ante — faster voluntary Ginnie speeds are consistent with a *weaker* gap response, which would raise the retained marginal above 0.797× share scaling; the spec must pre-authorise either sign.

### C-R2-12
raiser: R2
severity: MAJOR (M4, fix (c)) — R2 calls it "a bonus the paper is leaving on the table"
class: WORDING
panel_lines: 543–545
condition: The assumability limitation must be converted from open-ended into a signed bound using the paper's own extracted series: an assumed loan does not prepay, so materially high assumption take-up would show as *slower* Ginnie voluntary speeds; Ginnie CRR running above conventional over the window therefore caps take-up.
location: §I .tex:52 ("Realized take-up of that statutory right is not measured anywhere in this design, so the 20.4\% share bounds the carve-out from above rather than sizing it"); §VIII.A
verified: true — the concession is at .tex:52 verbatim; the mechanism is the paper's own (.tex:580 "an assumed loan also fails to prepay"); and the CRR differential is +1.354pp *above* conventional on the window mean (computed above), which is the direction that caps take-up. The inference is sound and needs no new data.
fix: Add one sentence at .tex:52 and its §VIII.A counterpart: Ginnie voluntary (CRR) speeds run 1.35pp *above* conventional over the window, and since an assumed loan does not prepay, materially high assumption take-up would have to show as slower Ginnie voluntary speeds — so the observed differential caps realized take-up rather than leaving it unbounded. Wording-only, sourced entirely to `gmar_dec25_cpr_series.json`. Pairs with C-R2-31 (the frictions qualifier), which cuts the other way and should land in the same edit.

### C-R2-13
raiser: R2
severity: MAJOR (M5) — R2: "every reversal magnitude is roughly double"
class: RUN
panel_lines: 547–564
condition: The Danish buyback discount `D` must be derived from the Danish leg's own simulated cash flows at its own 5.61% CPR against the window's market-rate path (or from matched-coupon/matched-month TBA marks), not asserted as a zero-prepayment PV, and the resulting bracket restated everywhere the −\$89.4 to −\$117.7bn range appears.
location: .tex:273 (the "proxy discount of 32 to 34\% … (36 to 38\% at the book's 2.49\% weighted-average coupon)" clause); T1 `tab:headline` row .tex:85; §VI.D .tex:590; §VIII; also .tex:52, .tex:727, .tex:731, .tex:1424
verified: partly —
  • TRUE that `D` is asserted, never derived: `hazard/buyback_credit_bracket.py:33` calls the grid "the manuscript's committed proxy range" and `:107` hard-codes `D_GRID = [0.32, 0.34, 0.36, 0.38]`; the artifact's `spec` string repeats "the manuscript's committed proxy range"; the .tex at :273 states the band with no derivation, and no derivation exists in `TECHNICAL.md` (0 hits for "32 to 34" / "annuity").
  • TRUE that the arithmetic chain is as R2 states: `verdict.gap_face_b` = 61.18833737, `verdict.early_face_E_b` = 470.65325285, `gap_cash_range_b` = [−117.660, −89.421], and the Danish leg's 5.61% CPR is printed at .tex:590.
  • PARTLY on the diagnosis: an independent zero-CPR PV of a 3.0% pass-through with 340 months remaining discounted at 6.8% gives ≈65.8 (34.2% discount) on my arithmetic against R2's 63.5 (36.5%) — same order, so his identification of the band's origin as a **no-prepay annuity PV** is plausible but not exactly reproduced. His prepayment-consistent 21–24% limb and the TBA-mark cross-check are not reproducible from committed artifacts without a run.
fix: Compute `D` from the committed `microsim_results_us_intercept.parquet` Danish path (the same file `buyback_credit_bracket.py` already reads for `E`) by pricing each month's retired face at its own prepayment-consistent PV against the window market-rate path, or from matched-coupon/matched-month TBA marks; publish it as a derived grid in a new artifact and restate the bracket. **Gate impact, must be handled in the same change:** `BUYBACK_BRACKET_SPANS["reversal_range"]` (`tools/liveness_gates.py:~645`) pins the literal `"$-\\$89.4$ to $-\\$117.7$ billion"`, and `tests/test_buyback_incidence_gate.py::test_each_span_removal_fails` asserts each span is present — so gate #103 and its test must be updated to the re-derived range, not bypassed. R2 notes the sign reversal survives at 22–24% (the "larger than the \$61.2bn gap" claim holds by a factor ≈1.7 rather than 2.5–2.9), so the qualitative conclusion is not at risk.

### C-R2-14
raiser: R2
severity: MAJOR (M5, fix (b) — "a deeper institutional point in the same place")
class: WORDING
panel_lines: 562–564
condition: §VI.D must state that the Danish market-value payoff is executed as an **open-market repurchase and delivery of the underlying bonds**, so the bondholder sells voluntarily and is not haircut; transplanted onto a passthrough holder the analogue is an outright sale at a discount, which means the par-denominated cap is not the natural scorer for the Danish leg.
location: §VI.D `sec:abm-danish`, .tex:590 (the transplant-omissions sentence "The transplant imports the payoff rule alone…"); §VI.B's active-sales discussion at .tex:576
verified: partly — the manuscript's framing is confirmed to be an incidence choice between balance adjustment and cash haircut (`buyback_credit_bracket.py:30-45`; .tex:273 "The pipeline does not distinguish a cash haircut from a balance adjustment"), and .tex:590 enumerates the transplant's omissions (Balance Principle, tap issuance, advisory distribution, IO share) without naming the *execution* mechanism. R2's institutional claim about Danish delivery-based redemption is standard but is **not verifiable from this repo** — it is exactly what missing reference C-R2-35 (Frankel et al. 2004) would source. Treat as a claim requiring the citation before it is asserted.
fix: One sentence in §VI.D, cited to Frankel et al. (2004), stating the repurchase-and-deliver mechanics and drawing the consequence: under the transplant SOMA's redemption stream becomes a market-value retirement, so the par-denominated cap benchmark is not the natural scorer for that leg — which is the "active sales" alternative §VI.B (.tex:576) already raises. Blocked on C-R2-35.

### C-R2-15
raiser: R2
severity: MAJOR (M5, fix (c))
class: STRUCTURE
panel_lines: 564
condition: The Danish counterfactual must be reported in duration units alongside dollars, since duration is invariant to the incidence question the dollar metric cannot resolve.
location: T12 `tab:wal` .tex:563 ("Danish rule-only leg, production anchor (5.61\%) & 9.1 & 8.2") and .tex:562 (Path B 9.7/8.7); §VI.D .tex:590; Appendix L
verified: partly — the numbers exist in `tab:wal` (Danish 9.1/8.2 vs Path B 9.7/8.7, .tex:562–563), so R2's "Table 12/Appendix L already give 9.1 vs 9.7" is correct; what does not exist is a duration statement *at the Danish result's own sites* (§VI.D .tex:590, T1 .tex:85, §VIII), which quote dollars only. R2 cites "9.1 vs 9.7"; the same-endpoint pair is Nov-2025 8.2 vs 8.7.
fix: Add the duration pair (9.1 vs 9.7 years at June 2022; 8.2 vs 8.7 at Nov 2025, a ~0.6-year shortening) to the §VI.D sentence and, if it fits, to T1's Danish cell — with the point that this metric does not depend on the face-vs-cash incidence choice. Reuses committed `wal_table` figures; no run.

### C-R2-16
raiser: R2
severity: MAJOR (M6)
class: WORDING
panel_lines: 566–574
condition: Where the Danish rule-only counterfactual is headlined as a single number, it must be headlined as the band [+\$61.2, +\$256.8]bn — the same range-not-point posture the paper applies to its own lock-in marginal.
location: T1 `tab:headline` Danish row, .tex:85; abstract .tex:31
verified: partly — **per anti-condition #6.** RIGHT for T1's cell: .tex:85 prints "Danish rule-only counterfactual … & $+\$61.2$ billion" with the uncertainty column carrying the sign-forcedness and the −\$99.9bn bracketing anchor but **not** the +\$256.8bn sweep top. RIGHT about the abstract in the weaker sense that it carries no Danish figure at all ("Danish"/"Denmark" appear 0 times on .tex:31). **WRONG for §I and §VI.D**: .tex:52 already reads "+\$61.2 billion (8\% of the benchmark), the zero-refinance edge of a band swept to +\$256.8 billion at 3\% refinance-in-place", and .tex:590 already says "I therefore report the rule-only gap as a band over the refinance-in-place contribution rather than at the zero point … from +\$61.2 billion at 0\% to +\$256.8 billion at 3\%". Scope the fix to T1's cell (and the abstract only if a Danish sentence is reinstated there).
verified-supporting artifact: `danish_redemption_validation` realized 26.4%/yr deep-discount redemptions and the +\$1,212bn realized-implied anchor are both stated at .tex:590; `danish_refi_finegrid` is the sweep run.
fix: Extend T1's Danish cell to lead with the band and label +\$61.2bn as its zero-refinance edge, mirroring .tex:52's existing wording. **Gate impact:** gate #71 (`tools/liveness_gates.py:4061–4073`) requires the *first* paragraph containing `"$+\\$61.2$ billion"` to also carry "forced rather than found" and "$-\\$99.9$ billion", and `table1_disclosed` pins the exact cell substring "positivity is forced by the zero-gap anchor, so the refinancing sweep cannot flip it; the Danish-level bracketing anchor does, at $-\\$99.9$ billion". The band must be *added* around those spans, byte-preserving, and the first-mention ordering property must be re-checked after the edit.

### C-R2-17
raiser: R2
severity: MAJOR (M6, fix, second clause)
class: WORDING
panel_lines: 570–574
condition: The realized-implied Danish anchor (+\$1,212bn) and its four confounds must be promoted from a subordinate clause to a sentence in the main text.
location: §VI.D .tex:590
verified: partly — the anchor and its confounds *are* already in the main text at .tex:590, but exactly as R2 describes structurally: a trailing dependent clause ("and the realized-implied anchor sits above the swept range entirely, pricing at $+\$1{,}212$ billion beyond the rejected partial-equilibrium ceiling --- though four confounds travel with it: …") inside a 1,053-word paragraph (.tex:709 is the paper's other mega-paragraph; .tex:590 is comparable). So the condition is a promotion-within-the-body, not a missing disclosure.
fix: Break the clause into its own sentence (or two) at .tex:590, keeping all four confounds (gross rate, non-household collateral, environment- not book-matched, Danish-tax realization) intact. Overlaps C-R2-43 (paragraph splitting).

### C-R2-18
raiser: R2
severity: MAJOR (M7) — one of R2's three headline-moving issues
class: RUN
panel_lines: 576–584
condition: The seasoning baseline must be *estimated* from the panel rather than left at the 100 PSA industry convention, and the marginal reported at an estimated out-of-the-money age profile (with 100 PSA demoted to robustness) — or the headline stated as a (baseline, floor) pair.
location: T3 `tab:params` PSA row .tex:251 ("PSA speed & 100 & -- & industry seasoning convention"); T2 `tab:specbox` age row .tex:204; the sweep at .tex:333
verified: true — .tex:204 gives Path A's seasoning spline knots {12,24,36,60,84,120} and the Path B convention "100~PSA ramp to 6\% CPR at month 30"; .tex:333 states the sweep "over 75 to 150 PSA on both legs carries the marginal from $+0.9$ to $+15.6$ points at the off-window floor and from $+3.3$ to $+16.5$ at the in-sample calibration (run `psa_level_sweep`), a span with no coverage property"; 15.6 − 0.9 = 14.7 confirms R2's "14.7 points". The raw material R2 names is all in hand: the spline knots (.tex:204), the 2018 leg's own age ladder (.tex:571 reads 4.70/4.99/5.33 by depth; the age ladder proper is Appendix J at .tex:1312: 3.68% below 12 months, 5.78% at 12–24, 10.99% at 24–36).
fix: Estimate the OTM baseline age profile from the Freddie panel (the same panel behind Path A's spline and Appendix J's ladder), re-score the central/null pair on it, and report that marginal as the headline with 100 PSA as robustness. Would write a new artifact (e.g. `estimated_baseline_marginal_results.json`) alongside the existing `psa_level_sweep`. Note the tension R2 himself names: Appendix J's ladder *rises* with age, which is why .tex:1312 uses it as evidence against a flat involuntary-turnover floor — so an estimated profile interacts with C-R2-28 (age-varying floor) and the two should be specced together.

### C-R2-19
raiser: R2
severity: MAJOR (M7, consequence + fix, abstract clause)
class: WORDING
panel_lines: 580–584
condition: The abstract must make visible that "binding" ranks layers by *coverage property*, not by width — and that +5.6 points is conditional on an unestimated 100 PSA baseline whose own span (14.7 points) is wider than the binding interval (5.8 points).
location: abstract .tex:31; T1 `tab:headline` .tex:79; §V.D .tex:333
verified: true, with the scope narrowed to the abstract — the **body already draws the distinction explicitly**: .tex:333 says the PSA sweep is "the widest disclosed layer … a span with no coverage property --- it is a range over a convention I did not estimate", and immediately: "The widest layer that does have a coverage property is the floor reads' own sampling error, $+2.9$ to $+8.7$ points". T1's cell at .tex:79 also labels [+2.9,+8.7] "the binding layer" with the coverage reason. The abstract at .tex:31 says only "The design bounds it between $+2.9$ and $+8.7$ points under its production floor form (the floor read's sampling error at my central elasticity; a wild-cluster interval on 31 clusters; the percentile read under-covers)" — no mention of the baseline convention. So R2's complaint is true of the abstract and false of §V.D.
fix: One clause in the abstract: that the interval prices the floor read's sampling error at a fixed 100 PSA baseline, that the baseline is a convention rather than an estimate, and that sweeping it spans a wider (coverage-free) range — pointing to §V.D. Do not weaken the existing "binding layer" language; add the conditioning. (Note anti-condition #1 for a neighbouring but distinct claim: "Webb is the narrowest of the ten rungs" is false — Webb is third-narrowest at 5.823pp, narrowest only among rungs with a credible coverage property. R2 does not make that claim; do not import it.)

### C-R2-20
raiser: R2
severity: MAJOR (M8)
class: CHECK
panel_lines: 586–594
condition: Whether the benchmark's monthly series should be rebuilt from published monthly SOMA agency-MBS *principal-payment* data (or CUSIP-level factor changes) rather than by differencing weekly Wednesday current-face levels — which would retire Appendix N's four clip zeros and reopen the monthly-timing question on a clean comparator.
location: §III.B .tex:137 ("from the New York Fed's SOMA current face value series, netting realized roll-off against the actual phased redemption cap schedule"); Appendix N; §VII.B .tex:635
verified: OPEN-UNARBITRATED — **per anti-condition #10 this is recorded as a CHECK, not an established defect.** What I did verify: R2's evidence is exact. `hazard/data/h1_zero_months_diagnosis.json` `zero_months["2023-02"].weekly_obs_b` = {2023-01-25: 2616.2734730824, 2023-02-01: 2616.2734730824, 2023-02-08: 2616.2734730824, 2023-02-15: 2615.0506434441, 2023-02-22: 2611.7887093757} — three identical weeks then a step, exactly as quoted; the `span_last_asof` (last-Wednesday) convention is the artifact's own field name; four zero months exist (2022-06, 2023-02, 2024-04, 2025-09) with unclipped values −1.5866/… and `classification_summary.spike_followed_all_artifact = true`; the committed verdict is `outcome: ARTIFACT`, "wording-class only … NO re-score; no committed number moves." And the cap arithmetic checks: 3 × 17.5 + 39 × 35 = 1,417.5; 1,417.5 − 652.8 = 764.7, against `committed_anchors.benchmark_b` = 764.7482532227.
fix: What would settle it: re-derive the 42-month total from a monthly principal-payment (or CUSIP factor-change) series and compare to \$764.7482532227bn. If the total reproduces within the existing tolerance, M8 is a timing-only issue already conceded and the honest disposition is a wording note; if it does not, the benchmark itself is in play and the round's scope changes. Until that re-derivation exists, do not record M8 as a defect and do not restate .tex:137. R2's own text concedes "the 42-month total is robust because the pairs conserve — which is why \$764.7bn holds and why I do not dispute it."

### C-R2-21
raiser: R2
severity: MAJOR (M8, consequence (ii))
class: CHECK
panel_lines: 592–594
condition: Whether the *realized-side* window-boundary allocation should be priced, given that §VII.B prices only the cap-side convolution and the boundary months have no partner month to cancel into.
location: §VII.B .tex:635; §III.B .tex:150 (the pre-window \$92.3bn)
verified: OPEN-UNARBITRATED (same anti-condition #10 umbrella), but the sub-claim about what is and is not priced is TRUE: .tex:635 prices the cap-side convolution at −5.5% and states "the QT window is half-open, so cap convolved past its final month is dropped … \$42.0 billion of the \$1{,}417.5 billion schedule --- and because **the realized series is untouched** and both legs sum over the same months, the benchmark moves by exactly that \$42.0 billion." The boundary asymmetry is real in the artifact: `zero_months["2022-06"].me_last_diff_b` = +1.9873 against `next_month_diff_b` = 8.0913 (R2's "+\$1.987bn against an \$8.091bn partner in July"), and the pre-window Jan–May 2022 rise of \$92.3bn is stated at .tex:150 — but used there for the cap-shortfall anticipation share, not for realized-side boundary allocation.
fix: What would settle it: a realized-side boundary sensitivity — re-allocate the June-2022 and Nov-2025 boundary paydowns across the posting-cycle seam (e.g. shift the post-last-Wednesday tail into its accrual month at both ends) and report the benchmark's movement, the way `settlement_months_benchmark` already does for the cap side. Same machinery, opposite leg. If the movement is inside the existing tolerance, say so once and close it.

### C-R2-22
raiser: R2
severity: MINOR (1) — but R2's Writing-Quality basis calls this sentence "unparseable as written"
class: WORDING
panel_lines: 600
condition: The §III.B coupon-convention sentence must stop naming both conventions at once.
location: .tex:146
verified: true — .tex:146 reads "both amortize on the pass-through convention where scheduled principal physically follows the borrowers' note rates (the pass-through WAC plus the guarantee-fee and servicing wedge, $+0.80$ points)". Pass-through WAC + 0.80 *is* the note rate, so "amortize on the pass-through convention" and "follows the note rates" contradict inside one clause.
fix: R2's own replacement: "both amortize at the pass-through WAC; scheduled principal physically follows the note rate, which is the pass-through WAC plus a +0.80-point g-fee and base-servicing wedge, and recomputing on that basis raises the CPR level by +0.27 points." Gate-safe: the gate #106 pinned spans (`conversion_def` "note rate less the vintage guarantee fee and base servicing, $\Delta = 0.80$ points"; `mixed_basis_label`) live at .tex:697, not .tex:146; "0.27" is not pinned anywhere in `tools/liveness_gates.py`. Keep the run tag `\texttt{coupon\_convention\_amortization}` in the sentence (gate requires ≥2 occurrences document-wide).

### C-R2-23
raiser: R2
severity: MINOR (2)
class: STRUCTURE
panel_lines: 602
condition: The empirical-CPR comparator must be restated at the physically correct note-rate convention (or printed as both columns) in the WAL table, since the paper already concedes the note-rate basis is right.
location: T12 `tab:wal` empirical row .tex:559 ("Empirical path (5.14\%) & 9.4 & 8.5"); T10 `tab:estimators` benchmark row .tex:485
verified: true — .tex:485 prints "mean CPR 5.14\% (ABM-basis back-out; hazard-basis 5.52\%, 5.79\% at the note-rate WAC)", so all three bases are already computed and printed *there*; .tex:559 uses 5.14% alone as the WAL scenario. R2's own recomputation (a single-pool 2.49% 30-year moving 7.72 → 7.25 years between 5.14% and 5.79% CPR, ≈0.5 year) is not reproducible from committed artifacts without running the WAL calculator, and is a single-pool figure not comparable to the table's blended 9.4; the *structural* point — the corrected basis never becomes the comparator — is verified.
fix: Add a note-rate-basis row (or a second column) to `tab:wal` for the empirical path, computed through the same `wal_table` calculator that produced the existing rows, and say in the tablenote which basis each row uses. Worth noting the stake R2 names: the revision is of the same order as the Danish rule-only WAL effect the paper reports (0.6 years, .tex:540).

### C-R2-24
raiser: R2
severity: MINOR (2, second clause)
class: WORDING
panel_lines: 602
condition: Every simulated-vs-empirical CPR comparison must say which comparator basis it uses.
location: §IV `sec:abm`, §V `sec:hazard`, §VII.C; the 5.14% sites at .tex:160, 315, 485, 524, 559, 571, 590, 1102
verified: true — 5.14% appears at eight .tex sites; only .tex:485 discloses that it is the ABM-basis back-out with hazard-basis 5.52% / note-rate 5.79% alternatives. Two of the eight (.tex:559, .tex:571) are inside `tab:wal`; two gate references to "5.14" exist in `tools/liveness_gates.py` (lines checked: the string appears twice), so the literal is pinned and must be preserved where it is protected.
fix: A one-clause basis label at each comparison site (or a single "Definitions used throughout" entry that fixes the convention once and a pointer at each site). Separate edit from C-R2-23 because it is a prose sweep across three sections, not a table change.

### C-R2-25
raiser: R2
severity: MINOR (3)
class: WORDING
panel_lines: 604
condition: Burnout's initialization must be stated: whether pre-window prepayment counts toward *B*, and what *B*'s window-open distribution is.
location: §V.B definition of *B* at .tex:227 and .tex:269 ("cumulative prepaid UPB as a share of its original UPB"); Appendix E .tex:1085
verified: true — **and the code settles the question R2 could only infer.** `hazard/agents.py:149` initialises `self.cohort_burnout = np.zeros(self.n_strata)`, so *B* = 0 for every stratum at window open and accumulates only within-window prepayment (`update_cohort_burnout_amounts`, `hazard/competing_risks.py:65–80`, adding `prepaid_s / stratum_orig_upb[s]` each step). The denominator `stratum_orig_upb` (agents.py:145–147) sums `orig_upb` over **all** 75,000 sampled rows, including the 34,734 that prepaid pre-window (.tex:1085). So pre-window attrition is *not* counted in the numerator but *is* in the denominator — the manuscript's "cumulative prepaid UPB as a share of its original UPB" is window-cumulative, which the text does not say. R2's arithmetic (*B* ≈ 0.46 and a 0.79 multiplier from month one if pre-window counted) correctly describes the alternative the code does not implement, and his read of the \$6.58bn/\$3.48bn ablations (.tex:269, .tex:532) as evidence against it is right.
fix: One clause at .tex:227: *B* is initialised at zero at the window open and accumulates only within-window prepaid UPB, against the stratum's full original UPB including pre-window-terminated loans — so it is window-cumulative, not life-cumulative. Optionally report the window-open distribution in Appendix E (it is degenerate at zero by construction, which is the informative statement). Also note the interaction R2 flags with the `attenuation_sensitivity` survival-selection transport (.tex:433, `a = S^θ` at `S = 40{,}234/75{,}000`).

### C-R2-26
raiser: R2
severity: MINOR (4)
class: REFERENCE
panel_lines: 606
condition: The FHFA assumability/portability claim must carry a citation, and the assumption mechanics and second-lien gap must be sourced.
location: .tex:580 ("U.S. policymakers, including the Federal Housing Finance Agency (FHFA), proposed expanding assumable and portable mortgages")
verified: partly — TRUE that .tex:580 carries no `\cite` of any kind. R2's supporting count is slightly off: "assumab*" appears **three** times in the .tex (.tex:52 "assumable by statute", .tex:580 "assumable and portable", .tex:580 "assumability"), not twice.
fix: Cite the actual FHFA proposal document, plus HUD Handbook 4000.1 (FHA assumption mechanics and qualification) and the relevant VA circular (entitlement restoration and release of liability) for the mechanics and the price-minus-balance second-lien gap. None of these is in `references.bib` today (0 hits for "HUD", "FHFA" as entries). Pairs with C-R2-31.

### C-R2-27
raiser: R2
severity: MINOR (5)
class: WORDING
panel_lines: 608
condition: The default baseline's free external corroboration must be taken: h^def_0 = 3×10⁻⁴/month = 0.36%/yr against the paper's own GMAR-extracted realized Freddie CDR of 0.314% window-mean.
location: .tex:227 (the prior, "$3\times10^{-4}$ monthly") and T3 `tab:params` .tex:252 ("$h^{\mathrm{def}}_0$ & $3\times10^{-4}$ & monthly & calibration prior")
verified: true — both sites confirmed; 3×10⁻⁴ × 12 = 0.36%/yr; and the realized Freddie CDR window mean recomputed from `gmar_dec25_cpr_series.json` is **0.314%** (2022-06…2025-11, 42 months), matching R2 exactly. It is one of the few priors with an external check and it passes.
fix: One clause at .tex:227 (and/or the T3 provenance cell): the 0.36%/yr implied annual CDR is corroborated by the paper's own GMAR extraction at 0.314% realized Freddie window-mean. Wording-only, cites an already-committed artifact.

### C-R2-28
raiser: R2
severity: MINOR (6)
class: RUN
panel_lines: 610
condition: The floor's flatness in loan age must either be swept (an age-varying floor) or, at minimum, flagged as an assumption contradicted by the very ladder used to set it.
location: floor definition eq (1) region, §V.B; Appendix J ladder at .tex:1312; the existing rate-varying and calendar-varying sweeps (`tab:floorband` .tex:289, `tab:seasonalfloor` .tex:1369)
verified: true — .tex:1312 prints the age ladder as R2 quotes it ("3.68\% below twelve months, 5.78\% at twelve to twenty-four, and 10.99\% at twenty-four to thirty-six") and uses its monotone *rise* as evidence that the floor is not purely involuntary turnover; the floor enters as a single constant SMM; and the paper already sweeps a rate-varying floor (`tab:floorband`) and a calendar-varying one (`tab:seasonalfloor`), so the age dimension is the missing one of three.
fix: Sweep an age-varying floor built from the Appendix J ladder through the existing floor-grid machinery (the `floor_form_*` / `floor_sweep` family), reporting the marginal at the age-varying form; would write a new artifact (e.g. `floor_form_age_results.json`). Minimum acceptable substitute: one sentence noting that the floor's flatness in age is an assumption contradicted by the ladder used to calibrate it. **Caveat carried from the memory record:** `floor_cyclical` was previously mislabeled (it measured floor *dispersion* under `FLOOR_MODE='max'`, not cyclicality); an age-varying sweep must be specced so it cannot repeat that confusion — state ex ante what varies and what the scramble/permutation null is. Interacts with C-R2-18.

### C-R2-29
raiser: R2
severity: MINOR (7)
class: WORDING
panel_lines: 612
condition: The "\$83 billion per CPR point" conversion coefficient must be derived once where it is first used.
location: .tex:269 — used twice in the same paragraph, once for the Ginnie composition bound (\$20–47B) and once for the vintage bound ("At the same \$83-billion-per-CPR-point sensitivity, a bound of \$11.7 billion")
verified: true — both uses are at .tex:269 and neither derives the coefficient; "per CPR point" appears elsewhere only at .tex:590 (the Danish sweep's \$65bn/CPR-point slope, a different object). R2's check reproduces: ≈\$2.4T average book × 3.5 years × 1% ≈ \$84bn.
fix: One parenthetical at first use in §V.B giving the derivation (average book face × window length × one CPR point), so both bounds inherit a stated basis rather than an unexplained constant.

### C-R2-30
raiser: R2
severity: MINOR (8)
class: WORDING
panel_lines: 614
condition: §VI.A's "roughly six extension-years" must also be quoted against the normal-turnover row, so the reader can see the extension is refinancing-versus-turnover rather than lock-in-versus-normalcy.
location: §VI.A; T12 `tab:wal` rows .tex:559 (empirical 9.4/8.5), .tex:565 (turnover floor 4.99% → 9.5/8.6), .tex:566 (2021 speeds 22.81% → 3.4/3.3); the "six extension-years" phrase at .tex:540
verified: true — the six years is 9.4 − 3.4 (empirical vs the 22.81% refi-boom row), the tablenote at .tex:571 already flags 22.81% as "a refinancing-boom baseline rather than a normal-turnover one" and names the turnover-floor row "the normal-turnover counterpart", and against that row the extension is 9.4 vs 9.5 — essentially zero, exactly as R2 says.
fix: Add the against-the-turnover-floor comparison (9.4 vs 9.5 years at June 2022; 8.5 vs 8.6 at Nov 2025) to the §VI.A sentence at .tex:540. Uses only committed `tab:wal` figures.

### C-R2-31
raiser: R2
severity: MINOR (9)
class: WORDING
panel_lines: 616
condition: "Assumable by statute" needs one qualifier: FHA/VA assumption is subject to creditworthiness qualification of the assuming borrower, servicer processing, occupancy restrictions and VA entitlement-restoration considerations, so the 20.4% share bounds the carve-out from above only if assumption is frictionless.
location: §I .tex:52 ("the FHA/VA loans backing Ginnie Mae pools (20.4\% of the SOMA book) are assumable by statute")
verified: true — the claim is at .tex:52 as quoted, with the from-above bounding sentence immediately after; no frictions are named there. §VI.C (.tex:580) names only the price-minus-balance financing gap, which is a different friction.
fix: One clause at .tex:52 naming the qualification frictions. Note this cuts the *opposite* way from C-R2-12 (which uses the CRR differential to cap realized take-up); landing both in the same edit keeps the bound two-sided and honest.

### C-R2-32
raiser: R2
severity: MINOR (10)
class: META
panel_lines: 618
condition: R2 asks that duplicated table captions in the header row of Tables 1, 8, 9, 25, 27 be fixed before submission.
location: claimed at T1/T8/T9/T25/T27; actual defect at `~/Downloads/UPLOAD_ROUND11/revised_paper_v18.md:41,43`
verified: false — **anti-condition #5.** The defect exists only in the markdown edition: md:41 renders the caption as bold text and md:43 repeats it inside the header row's first cell. The .tex is correct: for T1 the sequence is `\begin{longtable}` (66) → `\caption{...}` (66) → `\label{tab:headline}\\` (67) → `\toprule` (68) → header row (69) → `\midrule` (70) → `\endfirsthead` (71), i.e. the caption sits properly before `\endfirsthead`. There is no PDF defect, so "it will read as sloppiness in a submitted PDF" is wrong.
fix: The honest alternative is a converter fix in `tools/editions/tex2md.py` (the longtable→markdown path introduced when R31 converted five over-tall tables to `longtable`), plus a regenerated .md edition. No manuscript edit. Record the panel's premise as refuted rather than silently satisfying it.

### C-R2-33
raiser: R2
severity: inferred MAJOR (R2: "a reference a domain referee would require")
class: REFERENCE
panel_lines: 626
condition: The canonical mortgage competing-risks estimator must anchor §V.B's competing-risks discussion, which currently positions itself only against biostatistics methods.
location: §V.B `sec:pathb` competing-risks/Fine–Gray passage; `attenuation_sensitivity`'s gamma-frailty identity (.tex:433)
verified: true — not in the .bib (0 hits for "Deng", "Van Order"); `references.bib` does contain `quigley1987` and `quigley2002` (Quigley, "Homeowner mobility and mortgage interest rates", REE 30(3)) as R2 says, plus `fine1999`, `putter2007`, `putter2022` and `meir2025` — confirming §V.B's anchors are the biostatistics ones.
fix: Add **Deng, Y., J. M. Quigley & R. Van Order (2000), "Mortgage terminations, heterogeneity and the exercise of mortgage options," *Econometrica* 68(2), 275–307.** Not in `references.bib`. Bears on the argument because it is Path B's exact structure — competing-risks prepayment/default with unobserved heterogeneity — and it supplies the frailty/heterogeneity apparatus the `attenuation_sensitivity` gamma-frailty identity assumes.

### C-R2-34
raiser: R2
severity: inferred MAJOR
class: REFERENCE
panel_lines: 628
condition: The convexity-and-hedging argument must cite the paper that quantifies the mechanism the SOMA's low-coupon stock embodies.
location: §VI.A; §VIII
verified: true — not in the .bib (0 hits for "Hanson", 0 for "convexity"); `gabaix2007` and `malkhozov2016` are both present, as R2 states.
fix: Add **Hanson, S. G. (2014), "Mortgage convexity," *Journal of Financial Economics* 113(2), 270–299.** Not in `references.bib`. Bears on the argument because it establishes that the outstanding coupon distribution determines aggregate MBS duration and feeds back into long rates — turning the paper's "convexity-neutral duration profiles" from a label into a measured channel.

### C-R2-35
raiser: R2
severity: inferred MAJOR (also blocks C-R2-14)
class: REFERENCE
panel_lines: 630
condition: The Danish institution must be sourced from the reference that specifies what the "payoff rule only" transplant omits, and that documents the market-value payoff as an open-market bond repurchase and delivery.
location: §VI.D .tex:590 (the omissions enumeration); §VIII
verified: true — not in the .bib (0 hits for "Frankel", "Gyntelberg"); `berg2018` (Berg, Nielsen, Vickery) is the paper's only institutional Denmark cite, as R2 states.
fix: Add **Frankel, A., J. Gyntelberg, K. Kjeldsen & M. Persson (2004), "The Danish mortgage market," *BIS Quarterly Review*, March, 95–109.** Not in `references.bib`. Bears on the argument twice: it specifies *what* the transplant omits (Balance Principle, series-level match funding, tap issuance, advisory distribution, the IO share — all enumerated at .tex:590 without a source), and, critically for C-R2-13/C-R2-14, it documents that the market-value payoff is executed as an open-market bond repurchase and delivery rather than as a discounted loan payoff.

### C-R2-36
raiser: R2
severity: inferred MAJOR
class: REFERENCE
panel_lines: 630
condition: §VIII's reform-design argument needs its Danish-reform companion source.
location: §VIII `sec:conclusion`
verified: true — not in the .bib (0 hits for "Svenstrup", "Willemann").
fix: Add **Svenstrup, M. & S. Willemann (2006), "Reforming housing finance: perspectives from Denmark," *Journal of Real Estate Research* 28(2).** Not in `references.bib`. Bears on the argument as the companion to Frankel et al. for the reform-design half of §VIII — the paper argues from the Danish payoff rule to a US design space (.tex:576) with no reform-literature anchor.

### C-R2-37
raiser: R2
severity: inferred MAJOR
class: REFERENCE
panel_lines: 632
condition: The strictly partial-equilibrium status of every counterfactual (β₁=0 null, Danish transplant, moving-share bracket) needs the GE qualifier the literature supplies.
location: §V.B transport-assumptions enumeration; §VI.D; §V.D
verified: partly — the *requested* paper is not in the .bib (0 hits for "Mabille"), but a closely related one **is**: `fonseca2024` = Fonseca, J. and Liu, L. (2024), "Mortgage lock-in, mobility, and labor reallocation," *Journal of Finance* 79(6), 3729–3772 (`references.bib:146-154`), and `hazard/data/fonseca_band_anchor_results.json` shows a Fonseca anchor already in the pipeline. So the author is cited; the spatial-housing-ladder GE paper is not.
fix: Add **Fonseca, J., L. Liu & P. Mabille, "Unlocking mortgage lock-in: evidence from a spatial housing ladder" (working paper)** — distinct from the already-cited `fonseca2024`. Bears on the argument because the imported Liebersohn–Rothstein elasticity is a partial-equilibrium moving response and every counterfactual here is partial-equilibrium; this is the reference that says how much of that response survives GE, and is the natural qualifier on the transport assumptions §V.B enumerates.

### C-R2-38
raiser: R2
severity: inferred MAJOR (R2: "the cheapest available upgrade to the section a referee will press hardest on")
class: REFERENCE
panel_lines: 634
condition: §III.B's standing concession that nothing here shows reserves or the aggregate path came in off course must be positioned against the literature that takes up exactly that question.
location: §III.B `sec:method-benchmark` (.tex:137–152)
verified: true — not in the .bib (0 hits for "Salido"); `krishnamurthy2011` (Krishnamurthy & Vissing-Jorgensen) is present, so the co-author appears but not this paper.
fix: Add **López-Salido, D. & A. Vissing-Jørgensen (2023), "Reserve demand, interest rate control, and quantitative tightening."** Not in `references.bib`. Bears on the argument because §III.B's self-limitation ("nothing in this paper shows that reserves or the aggregate path came in off the intended course because MBS ran slow") is precisely this literature's question; citing it converts an isolated concession into a positioned claim.

### C-R2-39
raiser: R2
severity: inferred MAJOR (R2 offers it as an alternative or complement to C-R2-38)
class: REFERENCE
panel_lines: 634
condition: Same as C-R2-38 — the reserves/balance-sheet-demand side of the QT question needs an anchor.
location: §III.B `sec:method-benchmark`
verified: true — not in the .bib (0 hits for "Acharya", "Steffen").
fix: Add **Acharya, V., R. Chauhan, R. Rajan & S. Steffen (2024), "Liquidity dependence and the waxing and waning of central bank balance sheets."** Not in `references.bib`. Bears on the argument as the liquidity-dependence counterpart to López-Salido–Vissing-Jørgensen for the same §III.B concession; R2 presents the pair as "and/or", so one may suffice.

### C-R2-40
raiser: R2
severity: inferred MAJOR
class: REFERENCE
panel_lines: 636
condition: The servicer channel — named unmodeled and **unbounded** at three separate sites — must acquire a direction from the literature that measures it.
location: §V.F, §VI, §VIII.A
verified: true — not in the .bib (0 hits for "Aiello", 0 for "servicer" as a bib field).
fix: Add **Aiello, D. J. (2022), "Financially constrained mortgage servicers," *Journal of Financial Economics* 144(2), 590–610.** Not in `references.bib`. Bears on the argument because it measures the servicer channel's effect on prepayment and default outcomes, which would let the paper state a direction for the one residual candidate it currently leaves signless in three admissions.

### C-R2-41
raiser: R2
severity: inferred MAJOR
class: REFERENCE
panel_lines: 638
condition: The TBA/pooling/prepayment institutional claims need a survey anchor so they can travel without each one carrying its own primary source.
location: §I .tex:52 (TBA homogeneity); §VIII
verified: partly — the specific survey is not in the .bib, but R2's characterization of what *is* there is right: `vickery2013` (Vickery & Wright) and `gao2017` (Gao, Schultz, Song) are present, and `boyarchenko2019` (Boyarchenko, Fuster, Lucca, "Understanding mortgage spreads") means both Fuster and Lucca already appear via a different paper. "Handbook" appears once in the .bib but not for this chapter.
fix: Add **Fuster, A., D. Lucca & J. Vickery, "Mortgage-backed securities" (NBER WP 28966 / *Handbook of Fixed-Income Securities*).** Not in `references.bib`. Bears on the argument as the standard institutional survey of TBA, pooling and prepayment, letting §I's and §VIII's institutional claims rest on a survey rather than on two primary sources.

### C-R2-42
raiser: R2
severity: MINOR (R2 marks it "Optional")
class: REFERENCE
panel_lines: 640
condition: The coupon-wise pricing of prepayment risk that the hedging discussion presumes, and that C-R2-13's discount question turns on, should be cited.
location: §VI.A; §VIII; and the M5 discount derivation
verified: true — not in the .bib (0 hits for "Diep", "Eisfeldt").
fix: Add **Diep, P., A. Eisfeldt & S. Richardson (2021), "The cross section of MBS returns," *Journal of Finance* 76(5).** Not in `references.bib`. Bears on the argument because it prices prepayment risk by coupon — what §VI.A/§VIII's hedging discussion presumes and what the re-derived Danish discount `D` (C-R2-13) turns on. Explicitly optional per R2.

### C-R2-43
raiser: R2
severity: inferred (basis of the Writing Quality score, 60/100)
class: STRUCTURE
panel_lines: 652
condition: The mega-paragraphs must be broken up: readability delivered is poor, with load-bearing clauses buried in single paragraphs nesting 4–6 parentheticals and multiple em-dash asides.
location: the paper's longest paragraphs, measured: .tex:323 (1,606 words, §V.D `sec:identification`), .tex:269 (1,155 words, §V.B `sec:pathb`), .tex:709 (1,053), .tex:277 (1,049), .tex:231 (1,016), .tex:150 (990), .tex:1100 (967), .tex:333 (964)
verified: partly — the complaint is real but the number is wrong. R2 says "a 2,200-word single body paragraph in §V.B". No 2,200-word paragraph exists: the longest in the whole .tex is 1,606 words (.tex:323, which is §V.D, not §V.B), and the longest inside §V.B (`sec:pathb`, lines 217–306) is 1,155 words (.tex:269). The markdown edition's longest paragraph is 1,618 words. So the target should be "eight paragraphs over 950 words, three over 1,050", not a single 2,200-word block.
fix: Split the worst offenders at their natural seams — .tex:323 (censoring shares / null-leg bind / floor-level sensitivity), .tex:269 (Ginnie overlay / vintage overlay / the two bounds), .tex:590 (band / realized anchor / confounds, which also satisfies C-R2-17). Text-preserving splits only: every gate-pinned span must survive byte-identically, and gate #71's `intro_para_carries_forcedness_and_flip` binds a *paragraph-level* co-occurrence property (`tools/liveness_gates.py:4061`), so splitting the paragraph that first states +\$61.2bn would break it unless the forcedness and −\$99.9bn clauses move with it.

### C-R2-44
raiser: R2
severity: inferred (basis of the Writing Quality score)
class: STRUCTURE
panel_lines: 652, 662
condition: The manuscript's length — 139pp total, 94pp of main text, "roughly double a field-journal norm for this content" — is a submission-readiness problem R2 raises twice (score basis and Carroll-Round proviso).
location: whole manuscript; the 1–94 / 95–139 split already produced by R31
verified: true on the page counts — the R31 commit records "Build 139pp … split recut main 1-94 / appendix 95-139", matching R2's figures exactly. Whether the norm comparison is right is a venue judgment, not a repo fact.
fix: Scope decision for Eugene, not an agent edit: either a venue with this length tolerance, or a compression pass that moves body material to appendices. Note this collides with almost every other condition in this inventory, all of which *add* text — so if compression is in scope it must be sequenced after the wording landings, not interleaved.

### C-R2-45
raiser: R2
severity: inferred (basis of the Evidence Sufficiency score, 57/100)
class: CHECK
panel_lines: 650
condition: R2 counts against the paper that "the elasticity's evidential base is entirely external with no standard error propagated." Whether the imported Liebersohn–Rothstein elasticity's own sampling error can be propagated into the marginal is the open question.
location: §V.B elasticity import; T7 `tab:lowband` (.tex:386); the band sweep at .tex:282
verified: partly — the paper sweeps the *published range* of δ (5.5%–7.7%, .tex:282, `tab:lowband`, and the δ columns of `tab:oosfloor` .tex:365) but that is a range over published values, not a propagated standard error, so R2's characterization holds as stated. R2 raises it only as a score basis and requests no fix.
fix: No fix is specified by R2. What would settle it: check whether Liebersohn–Rothstein publish a standard error on the mobility-decline coefficient; if they do, propagate it through the committed floor-to-marginal grid the way `floor_uncertainty` propagates the floor read's replicates, and report the resulting interval as a *fourth* layer with its coverage property named. If they do not, one sentence saying so converts an unpriced gap into a documented one. Flagged as inferred — confirm scope before running anything.

### C-R2-46
raiser: R2
severity: inferred (basis of the Evidence Sufficiency score)
class: CHECK
panel_lines: 650
condition: R2 counts "there is no outcome holdout anywhere" against the evidence. Whether the existing temporal holdout satisfies this, or a genuine outcome holdout is feasible, is the open question.
location: T6 `tab:oosfloor` tablenote a, .tex:381 (the early-window calibration holdout)
verified: partly — an *out-of-sample-in-time floor calibration* holdout does exist and is reported: .tex:381 states the 3.97% floor is calibrated on the window's first nineteen months and that over the strictly held-out remaining twenty-three months the central-minus-null marginal is +\$45.1bn against +\$44.8bn at the production floor. That is a holdout on the *calibration*, not on the *outcome* (the benchmark itself is never held out), so R2's claim is right in the strict sense and overstated as "nowhere".
fix: No fix is specified by R2. Minimum honest response: name the existing temporal holdout at the site where the no-holdout criticism would land, and state precisely what it does and does not hold out (calibration months, not the benchmark). A true outcome holdout would require splitting the benchmark itself, which the 42-month window and the cap schedule may not support — record as infeasible with the reason if so.

### C-R2-47
raiser: R2
severity: inferred (deduction in the Argument Coherence score, 74/100)
class: WORDING
panel_lines: 651
condition: R2 deducts for §VIII conceding that the trilemma dissolution "reduces to 'the marginal is small'" and is bounded small "by construction" under the production form — so the policy conclusion rests on a calibrated ceiling. The dependence should be visible where the policy conclusion is drawn.
location: §VIII `sec:conclusion`; the form-conditional hull [+3.5, +13.1] at .tex:79/433; the max-form censoring statement at .tex:323
verified: partly — the ingredients are all in the manuscript and consistent with R2's reading (the production max form censors the elasticity in 68.8% of loan-months at the headline floor, .tex:323; the additive form gives +11.2 and the form-conditional hull runs to +13.1, .tex:433 — so "small" is indeed form-dependent). Whether §VIII's own sentences already carry that conditioning I did not fully audit; R2 states them as concessions the paper makes, which implies they are present. No fix is requested.
fix: No fix specified. Candidate minimal response: ensure the §VIII policy sentence that leans on smallness carries the form condition explicitly (the max form bounds the marginal small; the additive form does not), pointing at the hull. Confirm scope before editing — this is a deduction rationale, not a stated condition, and the anti-gaming rule against tuning to the rubric applies.

### C-R2-48
raiser: R2
severity: inferred (Carroll Round proviso)
class: META
panel_lines: 662
condition: A 15-minute path through the 139 pages must be prepared for the talk.
location: n/a (talk prep)
verified: true — 139pp confirmed (R31 commit; main 1–94, appendix 95–139).
fix: Talk-prep deliverable for Eugene, not a manuscript change: a 15-minute route naming which exhibits carry the argument (T1 `tab:headline`, T6 `tab:oosfloor`, T5 `tab:assembly`, fig1/fig5) and which 90+ pages are appendix.

### C-R2-49
raiser: R2
severity: inferred (Carroll Round proviso)
class: META
panel_lines: 662
condition: A one-slide answer to "is your 75,000-loan pool a sample of the Fed's book?" must exist.
location: n/a (talk prep); substance is C-R2-01/02/03
verified: true — the question is well-posed and currently unanswerable from the manuscript (see C-R2-01: the allocation rule is undisclosed).
fix: One slide with the three-object comparison (draw / estimation universe / SOMA book face on vintage and coupon), the allocation rule stated, and the direction of each limb. Becomes straightforward once C-R2-01 and C-R2-02 land; strongest with C-R2-03.

### C-R2-50
raiser: R2
severity: inferred (Carroll Round proviso; substantively M5)
class: META
panel_lines: 662
condition: The −\$89bn-to-−\$118bn Danish cash figure should not be quoted aloud until the discount proxy is re-derived at the leg's own prepayment speed.
location: n/a (talk prep); substance is C-R2-13
verified: true as a conditional instruction — the range is the committed `gap_cash_range_b` = [−117.660, −89.421] and its input `D` is asserted, not derived (see C-R2-13). Whether the range is *wrong* is unsettled until the re-derivation runs; R2's advice is to withhold the magnitude, not to assert a replacement.
fix: Talk-prep note for Eugene: quote the face-incidence +\$61.2bn (and the band per C-R2-16), and describe the cash-incidence reversal qualitatively as sign-robust with a magnitude under revision, until C-R2-13 lands.
