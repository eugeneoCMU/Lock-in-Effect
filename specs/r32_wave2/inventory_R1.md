# Round 32 — condition inventory, PEER REVIEWER 1 (METHODOLOGY)

Source: `REVIEW3_v18_panel_2026-07-29.md` lines 205–434.
Manuscript checked: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945/paper/v18/revised_paper_v18.tex` (all `.tex:N` below are that file).
Artifacts checked: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945/hazard/data/*.json`.
Gate/test pins checked (read, never run): `tools/liveness_gates.py`, `tests/`.

Table-number crosswalk used throughout (R1's md-edition numbering vs `.tex` labels):
R1 Table 1 = `tab:headline` (.tex:67) · Table 3 = `tab:params` (239) · Table 5 = `tab:assembly` (338) · Table 6 = `tab:oosfloor` (362) · Table 7 = `tab:lowband` (386) · Table 8 = `tab:uncertainty` (422) · Table 9 = `tab:ladder` (445) · Table 20 = `tab:pathadiag` (1107) · Table 27 = `tab:verdicts` (1400). R1's numbering runs +1 against the `.tex` count from ~position 10 onward.

---

### C-R1-01
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 241–256
condition: R1's headline framing of M1 — that the Webb wild-$t$ rung quoted as binding is "the *narrowest* of the ten rungs it is chosen from" — must not be accepted as stated.
location: `tab:ladder` (.tex:445–468); the ten rungs are printed at .tex:456–465
verified: false — ANTI-CONDITION #1. Measured widths recomputed from `floor_inference_correction_v2_results.json` `reads.R2_2018_gap<=-0.0025_age>=12` (+ `verdict.committed_percentile_pp`): percentile 5.0442, CR1-t 5.1967, CR2-t 5.5787, **Webb 5.8230**, Rademacher 5.9268, CR3-t 6.0012, CR1-BM 6.0431, CR2-BM 6.7400, WCR 6.8284, CR3-BM 7.2836 pp. Webb is fourth-narrowest of the ten as printed, not narrowest; it *is* the narrowest of the rungs with a credible few-cluster coverage property, which is R1's real argument and is carried by C-R1-02/03.
fix: No manuscript change on this premise. If a reply letter answers M1, state the measured width ordering and answer the surviving argument (C-R1-02, C-R1-03) rather than the "narrowest of ten" claim.

### C-R1-02
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 241–256, 260
condition: §V.E's own stated selection rule — "the widest layer that does have a coverage property" — selects CR3-BM $[+2.3,+9.6]$ or the WCR inversion $[+2.3,+9.1]$ when applied *within* the ladder, not Webb $[+2.9,+8.7]$. Either the wider rung is quoted as binding (Webb beside it), or the rule is restated so that it does not select against the paper's own choice.
location: .tex:333 (the rule sentence, gate-pinned as `ASSEMBLY_SPANS["posture_binding_layer"]`, `tools/liveness_gates.py:406`); `tab:ladder` caption .tex:443; `tab:uncertainty` headline row .tex:433; `tab:headline` row 4 .tex:79; abstract ¶2 .tex:31
verified: true — .tex:333 reads verbatim "The widest layer that does have a coverage property is the floor reads' own sampling error, $+2.9$ to $+8.7$ points after wild-cluster correction … and that is the interval this paper quotes as binding"; the ladder prints CR3-BM $+2.3$ to $+9.6$ and WCR $+2.3$ to $+9.1$ as wider, coverage-bearing rungs (.tex:464–465).
fix: Choose one. (a) Promote CR3-BM (or WCR) to binding: touches the 12 occurrences of `$+2.9$ to $+8.7$` (the gate at `tools/liveness_gates.py:4573` asserts `tex.count("$+2.9$ to $+8.7$") >= 4`), `ABSTRACT_POSTURE["interval"]` (:595), `ASSEMBLY_SPANS["posture_binding_layer"]` (:406), the letter literal list (:739), `tests/test_headline_posture_gate.py`. CAVEAT to disclose if promoted: both candidate rungs' **lower** endpoints are grid-edge-truncated — `cr3_t_interval_df_bm.lower_pp_edge.truncated_at_grid_edge = True` (floor 6.116% clipped to the 6.0% grid edge) and `wcr_inverted.lower_pp_edge.truncated_at_grid_edge = True` (6.181% clipped) — so both print $+2.281$ as a *clipped* bound, and both would need the truncation flagged (cf. C-R1-25). (b) Keep Webb and restate the rule with its scope (rungs sharing one studentizer / one df convention), plus C-R1-03. No run required either way.

### C-R1-03
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 256, 260
condition: If Webb is kept, the paper must say why a wild-cluster bootstrap is preferred to the Bell–McCaffrey/Imbens–Kolesár construction at $G^{*}=5.87$ with $h_{\max}=0.332$ — the configuration in which the wild bootstrap's own coverage is known to degrade.
location: Notes to `tab:ladder`, .tex:467–468
verified: true — the note justifies the wild-cluster correction only *against the percentile rung* ("That concentration is why the wild-cluster correction is applied and the percentile read demoted", .tex:468) and reports $G^{*}=5.9$ / $h_{\max}=0.33$; no wild-vs-BM argument appears anywhere. Leverage figures confirmed: `floor_inference_correction_v2_results.json` `parity_gates.P5_leverages.cells.R2…` `G_star_css = 5.871713810074106`, `h_max = 0.3323311750696546`, `sum_h_sq = 0.1703080280044131`.
fix: One sentence in the Notes to `tab:ladder` giving the preference argument (or conceding that at $G^{*}\approx6$ the two constructions are not ranked and both are quoted). Wording only; the BM rows are already printed.

### C-R1-04
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 258, 260
condition: The Rademacher/Webb near-identity must stop being read as evidence of robustness. With one cluster at $h=0.33$ both weight schemes are dominated by the same cluster's sign flip, so their agreement is uninformative about the leverage profile.
location: Notes to `tab:uncertainty`, .tex:440 — "the Rademacher and Webb constructions land with both endpoints within a tenth of a point, a re-printing rather than a substantive move" (R1 locates this in the Table 9 note; it is in fact the Table 8 note)
verified: partly — the span exists verbatim at .tex:440, and the endpoint gap is 0.059/0.045pp (`verdict.delta_lower_pp`/`delta_upper_pp`), i.e. R1's "within 0.06pp"; but R1's site attribution (Table 9's note) is wrong, and the paper already labels the pair "a re-printing rather than a substantive move" — it does not claim robustness *to the leverage profile*, only that the two constructions do not differ. Not currently pinned in `tools/liveness_gates.py` (no "re-printing" match) so the edit is gate-free.
fix: At .tex:440, replace the agreement clause with the mechanical reason it is uninformative (both schemes are dominated by the $h=0.33$ cluster), keeping the endpoint comparison as a re-printing statement only. Wording only.

### C-R1-05
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 264–277
condition: Every site quoting the floor read must disclose that its estimation support is a single origination vintage (2017) observed in a handful of consecutive 2018 calendar months, and that the cluster scheme prices cross-sectional dependence only, leaving any month-level common shock unpriced.
location: .tex:713 (§VII.F "31 clusters carry the 2018 leg"); `tab:ladder` caption .tex:443; `tab:uncertainty` headline row .tex:433; `tab:headline` row 4 .tex:79; abstract ¶2 .tex:31 ("a wild-cluster interval on 31 clusters"); "Definitions used throughout" .tex:92
verified: partly — the **vintage** claim is confirmed from a frozen artifact: all 31 entries of `floor_inference_correction_v2_results.json` `reads.R2….cluster_strata` begin `2017_` (31 of 31), and `n_cohort_months = 137`. The **month** distribution (201807–201812; 2/48/48/49/49/49) is recorded in no JSON I could read — R1 read `hazard/data/cohort_month_panel.parquet` directly, which I did not open (JSON/.tex reads only), so I cannot confirm the counts, only that they are absent from every artifact. R1's own text is internally inconsistent (it says "six reporting periods" at line 271 and "the same five consecutive months" / "five months of 2018" at 273/431). The absence of disclosure in the manuscript is confirmed: no "201808", "second half of 2018", "five months", "six months", "one vintage" or "vintage 2017" appears at any floor-read site (the three "2017 vintage" hits at .tex:269/743 are about SOMA book coverage, not the read).
fix: Re-derive the month histogram from the parquet under the committed selection (2018, `mean_loan_age >= 12`, gap cut) before printing anything, then add the support clause at the five sites above; also fix R1's five/six discrepancy in whatever number is printed. Wording only once the histogram is in hand; the ladder-caption edit is `tools/liveness_gates.py`-adjacent (see C-R1-08).

### C-R1-06
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 275, 277
condition: `tab:oosfloor`'s header describes the floors as measured on "2017–2019 performance"; for the three defensible rows that set the headline the performance window is 2018 only. The header must be corrected for those rows.
location: `tab:oosfloor` caption, .tex:361
verified: true — .tex:361 reads "measured *outside* the June 2022--November 2025 evaluation window (2017--2019 performance), except the final row"; `oos_identification_results.json` `instrument1_oow_floor.defensible_clean_floor` is `leg = 2018_rising_rate` with reads 5.334/4.991/4.695 (age ≥ 12). Nuance: the caption is accurate for the table's *contaminated* rows (pooled 2017–2019 read 6.065, 2019 leg 6.910), so the correction is per-row rather than wholesale.
fix: Split the caption's provenance clause: pooled/2019 rows on 2017–2019 performance, the three defensible rows on the 2018 rising-rate leg (and its vintage/month support once C-R1-05 lands). Wording only.

### C-R1-07
raiser: R1
severity: MAJOR
class: RUN
panel_lines: 273, 277, 427
condition: The ladder must add a month-clustered rung ($G\approx6$) and a two-way (stratum × month) rung, so that the month-level common shock the current scheme cannot see is priced — or is shown not to matter.
location: `tab:ladder` (.tex:445–468); the ladder's ten rungs at .tex:456–465
verified: true — no `month-clustered` and no `two-way` string exists anywhere in the manuscript; the committed cluster unit is cross-sectional only: `floor_uncertainty_results.json` `part_a_sampling_uncertainty.cluster_unit = "4-way stratum (vintage x coupon-bps x fico_bucket x ltv_bucket; stratum.build_stratum_id)"`.
fix: RUN. Compute a month-clustered and a two-way stratum×month CR/wild-$t$ interval on the R2 read and map the endpoints through the frozen PCHIP grid exactly as the committed path does (`hazard/floor_inference_correction.py:36–50`, whose grid-edge-truncation convention and refusal to extrapolate must be reused). Existing machinery: `hazard/floor_uncertainty.py`'s `cluster_bootstrap_cpr` (cluster unit is a parameter of the read) plus `hazard/floor_inference_correction_v2.py`'s Webb/BM/WCR constructions. Would write a new artifact (e.g. `floor_inference_correction_v3_results.json`) with the same P1–P7 parity gates; two new `tab:ladder` rows + one note clause. NOTE a within-design caveat R1 does not state: with 5–6 month clusters and 31 strata, the two-way estimator's own df is tiny, and `episode_confrontation_within_results.json` `limb_c.confounds_note` already records that a two-way (stratum + month) FE variant of the neighbouring within-estimator is "EXACTLY unid[entified]" — the two-way rung must be pre-committed with a NOT_COMPUTABLE landing available.

### C-R1-08
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 277
condition: The ladder caption's "31 clusters carry the read" must be restated as 31 cross-sectional coupon × FICO × LTV cells of a single vintage observed over a few months.
location: `tab:ladder` caption, .tex:443
verified: partly — the actual printed phrase is "All reads are on the 2018 leg's mid-grid anchor, which 31 stratum clusters carry" (.tex:443), not R1's quoted "31 clusters carry the read"; .tex:440 additionally says "31 carry the floor read". Substance of the condition holds (see C-R1-05's artifact evidence); only R1's quotation is loose.
fix: Reword .tex:443 (and the parallel phrase at .tex:440) to name the cluster unit and the vintage/month support. Check `tools/liveness_gates.py` ladder-span block near :4573 and `tests/test_floor_ladder_gate.py` for a pinned caption fragment before editing.

### C-R1-09
raiser: R1
severity: MAJOR
class: RUN
panel_lines: 281–293
condition: The read months are seasonally selected into the descending half of the paper's own committed calendar profile while the floor is then applied flat across all 42 QT months; standardizing the read to the QT window's month mix raises it to ≈5.21% and moves the headline by roughly $-0.8$pp. That correction must be measured and reported.
location: §VII.F .tex:713 (the floor-read paragraph); Appendix N (`sec:robustness-seasonalfloor`, .tex:1342–1392); `tab:oosfloor` (.tex:362); `tab:uncertainty` headline row (.tex:433)
verified: true — arithmetic reproduces from frozen artifacts. `seasonal_floor_timing_results.json` `h_month_normalizations_annual_cpr.shape_only` = 2.5036/2.7565/3.7502/4.2218/4.9374/5.2619/4.8135/4.7157/4.1301/3.9225/3.2517/3.1143 % (Jan–Dec; matches R1's printed vector), `peak_to_trough = 2.1307`, `h_month_exposure_weighted_mean.shape_only = 0.04000` (the 4.000% pin). Weighting by R1's month counts 2/48/48/49/49/49 (Jul–Dec) gives 3.8300% — R1's figure exactly — i.e. 4.25% below the 4.000% mean; $4.9906/0.95751 = 5.213\%$; the committed grid (`oos_identification_results.json` `instrument1_marginal_table`, band 6.5) gives 5.000 → $+5.5355$ and 5.334 → $+4.2657$, so 5.213% maps to $\approx+4.7$ to $+4.8$pp against the headline $+5.5716$ — a $-0.77$ to $-0.84$pp move. Nothing of this appears in the manuscript: Appendix N prices only *within-window floor dispersion* (a $-\$4.897$B Jensen effect, 89.2% of which survives month-scrambling, .tex:1348–1354) and the timing concession — not the read months' seasonal position. Depends on C-R1-05's month histogram being re-derived (R1 weighted the 245 candidate rows, not the 137 rows read R2 retains).
fix: RUN. Re-read the off-window floor with calendar-month standardization to the QT window's month mix using `hazard/seasonal_floor_timing.py`'s own 12-cell profile builder/normalizer (full-panel basis, the basis every committed leg uses), then remap through the frozen PCHIP grid; report the standardized read beside the raw 4.991% and restate `tab:oosfloor`'s band and `tab:uncertainty`'s calibration column. Artifact: a new `seasonal_standardized_floor_read_results.json` with a parity gate reproducing the committed `shape_only` vector and the 4.991% raw read bit-exactly. Two disclosures the run must carry, both already in the repo: Appendix N .tex:1362 records that the off-window leg cannot support its own 12-cell profile (335 cohort-months, zero prepaid balance in February and April), so the profile basis is necessarily the full panel; and the profile's deep-OTM filter "captures 98.2\% of QT exposure", so it is close to the identity map on the panel.

### C-R1-10
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 293
condition: If the calendar standardization is judged too dependent on the full-panel profile basis, the standardized read must still be reported as an indicative bound in the same register as the 5.51% age-standardized read, and joined to the sentence conceding that the band's lower edge is the soft one.
location: .tex:713 — "reads 5.51\%, above the clean band's top … an indicative bound rather than a measurement, but signed one way, so the clean band is open below $+4.3$ and that endpoint is not a conservative floor"
verified: true — the target register and sentence exist verbatim at .tex:713; the gate pins the companion span `ASSEMBLY_SPANS["ladder_agestd"]` (`tools/liveness_gates.py:385`) and requires the literal `"open below $+4.3$"` in the tex (:4576).
fix: Wording. Add the standardized read to the same indicative-bound sentence and to the "open below $+4.3$" clause; if it lands, add the corresponding row to `tab:assembly` (.tex:338) as a downward entry labelled directional.

### C-R1-11
raiser: R1
severity: MAJOR
class: CHECK
panel_lines: 297–305
condition: R1's arithmetic core for M4 — that the read-to-read (Freddie vs Fannie) spread is 0.53pp of CPR against a within-read cluster SE of 0.39pp, so "the layer that is *not* priced is the larger one" — must not be accepted as stated.
location: `tab:uncertainty` headline row .tex:433; §V.E .tex:333; §VII.F .tex:713
verified: false — the 0.53pp is a basis mix. `fannie_floor_read_results.json` `comparison` reports `freddie_headline_cpr_pct = 5.185`, `fannie_headline_cpr_pct = 5.522`, `difference_pp = 0.337` on the *same* selection (`books.freddie.out_of_window_2017_2019["gap<=-0.0025_age>=12"]`, 438 cohort-months) — the artifact carries **no** 2018-leg Fannie read at all (no `2018` key anywhere in it). R1 differenced Fannie's pooled-2017–2019 read (5.522) against Freddie's 2018-leg read (4.991, 137 cohort-months). Like for like the read-to-read spread is **0.337pp**, *below* the within-read cluster SE of 0.3934pp (`floor_inference_correction_v2_results.json` `parity_gates.P2_percentile_bitexact_R2.got_se_pp = 0.3933971547430653`). The variance ranking M4 asserts therefore reverses on the artifact's own like-for-like pair.
fix: No manuscript change on this premise; the reply should print the 5.185 / 5.522 / 0.337 triple from `fannie_floor_read_results.json`. The surviving parts of M4 are C-R1-12 (the paper's own basis mix) and C-R1-13 (transport variance disclosed but unpropagated).

### C-R1-12
raiser: R1
severity: MAJOR (inferred — the corrected form of M4)
class: WORDING
panel_lines: 297–305
condition: The manuscript describes the Fannie read as "the independent Fannie Mae read of **the same off-window cell**, 5.52\%" and brackets the headline against it, but 5.522% is the pooled-2017–2019 cell (438 cohort-months) whose Freddie counterpart is 5.185%, not the 2018-leg 4.991% the headline is read from. The comparison must be stated on one basis.
location: .tex:433 (`tab:uncertainty` calibration column), .tex:333 (§V.E ¶7 assembly), .tex:713 (§VII.F); the span is gate-pinned as `ASSEMBLY_SPANS["ladder_fannie"]` = `"5.52\\%, brackets the marginal below the $+4.3$ edge"` (`tools/liveness_gates.py:386`)
verified: true — `fannie_floor_read_results.json` `spec` = "the committed out_of_window_floor selection rule applied to the Fannie cohort-month panel, with the Freddie panel replayed through the same code path as parity", and its only out-of-window block is `out_of_window_2017_2019`; Freddie parity at that cell is 5.185 (n=438) against the headline's 2018-leg 4.991 (n=137). This is the same defect class the paper catalogues as retracted in Appendix A (differencing a standalone-scorer leg against a shared-basis null).
fix: Wording. Either state the Fannie comparison as Freddie 5.185 vs Fannie 5.522 (+0.337pp, pooled 2017–2019) and drop "the same off-window cell", or run the Fannie 2018-leg read to make the sentence true. Touches `ASSEMBLY_SPANS["ladder_fannie"]` and the `tab:uncertainty` calibration cell. If the second route is taken it is a RUN: `hazard/fannie_floor_read.py` already carries the leg-split machinery from `out_of_window_floor`; artifact would gain a `2018_rising_rate` block.

### C-R1-13
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 303–305
condition: The transport (read-to-read) variance component is disclosed but never propagated, while the within-read sampling layer is called "binding". Either the interval is built from the read-to-read spread, or the note says plainly that the binding layer prices only the within-read component and that the transport component is unpropagated.
location: Notes to `tab:uncertainty` .tex:440; the headline row .tex:433
verified: partly — the "disclosed but unpropagated" fact is true: the three reads (4.991 point, 5.5077 age-standardized per `b5_joint_cell_results.json.agestd_floor_pct`, 5.522 Fannie) all appear in the calibration column at .tex:433 and none enters the interval, and .tex:440 calls the wild-$t$ interval "the binding layer" without qualifying which variance component it prices. R1's *ranking* argument (transport > sampling) does not survive C-R1-11, so the "As written, 'binding' is not defensible" conclusion is weakened, not established.
fix: Wording. One clause in the Notes to `tab:uncertainty`: the binding layer is the floor read's own sampling error at fixed ramp/form/elasticity and does not price read-to-read transport, which is disclosed in the calibration column at 5.185/5.522 (pooled) and 5.51 (age-standardized). Do NOT rebuild the interval on R1's "3.7–4.3pp" pooled-read arithmetic — it rests on the C-R1-11 basis mix.

### C-R1-14
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 309–326
condition: $[+2.9,+8.7]$ must be relabelled as the sampling interval on the floor read *at fixed seasoning ramp, floor form and elasticity*, with the convention envelope (each of whose spans exceeds it) carried as the outer statement and the sampling interval nested and labelled inside it.
location: .tex:333 (`posture_binding_layer`, gate `tools/liveness_gates.py:406`); .tex:433; .tex:79; abstract .tex:31
verified: partly — the three convention spans reproduce exactly: PSA 75–150 at floor 4.991 gives $+0.856 \to +15.626$pp (`psa_level_sweep_results.json` `ranges["4.991"]`, `verdict = "PSA_WIDER"`, `comparison.psa_over_floor_read_at_headline = 2.492`); floor form $s\in[0,1]$ gives $+5.5716 \to +11.2070$ with $+9.660$ at $s=0.25$ (`floor_form_mixture_results.json` `cells["4.991|…"]`); $\delta = 3.25\%$ gives $+3.4658$ (`band_low_extension_results.json` `half_central_pq3.25["4.991"]`); binding width 5.8230. But the spans are **not** undisclosed: the PSA span is printed in `tab:uncertainty`'s calibration column ("baseline-level sweep 75--150 PSA $+0.9$ to $+15.6$ (a convention range, no coverage property)", .tex:433) and in §V.E ¶7 (.tex:333), the form curve and the $\delta$ curve likewise. What R1 objects to is the hierarchy and the word "binding", not absence.
fix: Wording. Relabel at the four sites; the honest minimum is to name the three fixed conventions in the label ("at 100 PSA, $s=0$, $\delta=6.5\%$"). Note that the ranking scope is already deliberate and gate-pinned — the comment above `posture_binding_layer` records it as ROUND-28 R1-W1/C3 branch (a) — so any change must move the gate span and `tests/test_headline_posture_gate.py` together.

### C-R1-15
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 326
condition: At minimum the abstract and `tab:headline` row 4 must not present $[+2.9,+8.7]$ as what *the design bounds*.
location: abstract .tex:31 — "The design bounds it between $+2.9$ and $+8.7$ points under its production floor form"; `tab:headline` row 4 .tex:79 — "floor-read wild-cluster bootstrap-$t$ $[+2.9, +8.7]$, the binding layer"
verified: true — both literals are present as R1 describes. Partial mitigation already in place: the abstract's parenthetical says "the floor read's sampling error at my central elasticity; a wild-cluster interval on 31 clusters; the percentile read under-covers", and row 4 says "the floor read's own sampling error propagated at the central elasticity … not an interval on the elasticity"; neither names the seasoning ramp or the floor form as fixed conventions, and `tab:headline`'s sensitivity catalogue (note a, .tex:90) omits the PSA span and the scaled-null companion entirely.
fix: Wording. Amend the abstract verb ("The design bounds" → a formulation naming what is held fixed) and row 4's label; add the PSA span and the scaled-null companion to note a's catalogue. Gate pins: `ABSTRACT_POSTURE["interval"] = "The design bounds it between $+2.9$ and $+8.7$ points"` (`tools/liveness_gates.py:595`) plus its ordering assert, and `tests/test_headline_posture_gate.py`.

### C-R1-16
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 326
condition: §V.E ¶7's own sentence ("the widest disclosed layer is the baseline level: $+0.9$ to $+15.6$") says the right thing and is then contradicted three lines later by quoting $[+2.9,+8.7]$ as binding; the tension must be resolved on the page.
location: .tex:333, both sentences on the same line
verified: partly — both sentences are present verbatim, but the paper explicitly distinguishes them ("a span with no coverage property — it is a range over a convention I did not estimate" vs "The widest layer that *does* have a coverage property"), so this is a hierarchy complaint rather than a literal contradiction. The scoping is deliberate (see C-R1-14's gate comment).
fix: Wording, and largely the same edit as C-R1-14: state once, in ¶7, which object is the paper's outer statement and which is nested, rather than leaving the reader to rank "widest disclosed" against "widest with coverage".

### C-R1-17
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 322
condition: The pre-committed externally-anchored calibration (`scaled_null_housing_activity`) roots at $\phi^{*}=0.754$ and returns $+0.9$pp — outside the quoted interval — and R1 charges that `tab:assembly` lists it and "nothing follows".
location: `tab:assembly` (.tex:338); §V.E ¶7 .tex:333
verified: partly — the run reproduces exactly (`scaled_null_housing_activity_results.json` `root["4.991"]`: `phi_star = 0.75390625`, `marginal_pp = 0.897850936460884`, `marginal_b = 6.866`; anchor `aladangady2024` 0.44/0.56). But "nothing follows" is wrong: .tex:333 states the root, the $+0.9$/$+3.5$ pair, the bit-exact $\phi=1$ parity, and then two consequence sentences — "The variant documents an upward bias; the corrected member lies below the headline, at the bottom of the seasoning-ramp span just swept." What does *not* follow is any restatement of the interval or of the headline.
fix: Wording, if anything: make explicit that a pre-committed externally-anchored member lies outside the quoted interval (that word is not used at .tex:333), which is the part R1's complaint actually reaches. No run.

### C-R1-18
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 324
condition: Aggregate fit cannot be used to defend the 100 PSA convention: at 75 PSA with the 4.991% floor the $\beta_1=0$ null recovers 101.9% standalone, a *better* fit than the production null's 94.8%. This must be on the page wherever the ramp convention is defended.
location: `tab:uncertainty` calibration column .tex:433 (the PSA entry); §V.E ¶7 .tex:333; `tab:params` (.tex:239) where 100 PSA is specified
verified: true — `psa_level_sweep_results.json` `cells["4.991|75|0"].share_pct = 101.9415` against `cells["4.991|100|0"].share_pct = 94.7917`; neither figure is printed anywhere in the manuscript (the PSA entry prints only the marginal span $+0.9$ to $+15.6$).
fix: Wording. One clause beside the PSA span reporting the null's standalone recovery at 75/100 PSA, so the ramp convention is not implicitly fit-defended. Committed literals only; no run.

### C-R1-19
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 330–343
condition: The sentence adjudicating the form fork compares a shared-basis 91.3% against a standalone 55.9%. It must be restated on a single basis (like for like: $100.4 \to 55.9$ standalone, or $91.3 \to 46.8$ shared).
location: .tex:709 — "while the central leg's recovery falls from 91.3\% to 55.9\% along the way, the level cost the additive end pays"
verified: true — `floor_form_mixture_results.json` `cells["4.991|0|6.5"].share_pct = 100.3633` (standalone central, max form) and `cells["4.991|1|6.5"].share_pct = 55.9066` (standalone central, additive); the shared basis is standalone minus the common 9.10pp netting, giving 91.26 / 46.81 (and null 94.7917 → 85.69, 44.6996 → 35.60). So 91.3 is shared and 55.9 is standalone: the printed fall of 35.4 points understates the like-for-like 44.5. Mitigation to note: three sentences later the same paragraph states the correct like-for-like magnitude — "the additive form undershoots the max form's aggregate level by 43.5 to 45.3 points at every off-window anchor" — so the paper has the right number in the right paragraph and the wrong one in the fork sentence. Flagged by R1's reproducibility verdict as one of the two printed numbers to change.
fix: Wording at .tex:709: restate as $100.4 \to 55.9$ (standalone) or $91.3 \to 46.8$ (shared) and keep the basis label; both literals are committed in `floor_form_mixture_results.json`. Check the ABM/basis-label gates for a pinned "91.3\%" span before editing (91.3 appears at .tex:31, 58, 82, 182, 211, 323, 431, 498 for the *max-form* central level, which is correct and must not be swept).

### C-R1-20
raiser: R1
severity: MAJOR
class: WORDING
panel_lines: 345–347
condition: The mechanical-majority headline is a max-form result and must be labelled as such: the $\beta_1=0$ null recovers 85.7% of the benchmark on the shared basis under the hard maximum and 35.6% under the additive form, so the form choice conditions the decomposition as well as the marginal.
location: abstract ¶1 .tex:31 — "switch the lock-in response off and the model still accounts for 85.7\% of it"; `tab:headline` mechanical-null row .tex:78 ("85.7\% of benchmark at the headline off-window floor; 88.7\% in-sample", uncertainty column "83.9--86.9\% across the off-window floor range"); §VIII ¶3 (`sec:conclusion`, .tex:719+); §VII.F .tex:709
verified: true — the 85.7% shared / 44.70% standalone (= 35.60% shared) pair is exact in `floor_form_mixture_results.json` (`cells["4.991|0|0"].share_pct = 94.7917` → 85.69 shared; `cells["4.991|1|0"].share_pct = 44.6996` → 35.60 shared) and cross-checks against `oos_identification_results.json` (`instrument1_marginal_table` floor 4.991, `null_share_pct = 94.7917`). Neither the abstract nor `tab:headline`'s row conditions the figure on the form; the additive null's 44.7% standalone is printed once, at .tex:709, and its 35.6% shared equivalent nowhere.
fix: Wording. One clause in the abstract and one sentence in §VII.F (plus the `tab:headline` row's uncertainty cell) stating that 85.7% is a max-form figure and the additive form's null is 35.6% shared. Committed literals; no run. Note the sharper consequence R1 draws and the paper should answer: a null recovering 35.6% does not partition the object being decomposed, so the $+11$ branch and the mechanical-majority claim cannot both be taken (see C-R1-21).

### C-R1-21
raiser: R1
severity: MAJOR
class: STRUCTURE
panel_lines: 345–347
condition: If aggregate fit is in fact doing the work of keeping the max form — as it must be, since the additive null does not partition the benchmark — the paper should say so, and the $+11$ branch's standing in the hull should be resolved rather than left alive alongside a headline that depends on the max form.
location: .tex:709 (the form-selection paragraph); `tab:headline` note a hull entry .tex:90; abstract ¶2 .tex:31
verified: partly — the premise that the paper refuses fit as the selection rule is confirmed verbatim: "the aggregate-level comparison is context for the level, not the selection rule for the marginal's form, since the design does not identify levels" and "What keeps the headline at the $s = 0$ endpoint is the max form's semantics, now displayed as the conservative endpoint of a measured curve rather than defended by fit" (.tex:709). The paper also already discounts the hull's top ("The hull's upper endpoint is produced by the least accurate of these cells … should not be read as an equally credentialed member"). So the incoherence R1 charges is between the abstract's unlabelled 85.7% and this refusal — i.e. it is C-R1-20's consequence, not an independent factual error.
fix: Wording/structure, no run. Either add the sentence R1 asks for (fit is doing partition work, so the max form is retained and the $+11$ branch is a form sensitivity rather than a co-equal member), or state explicitly that the mechanical-majority claim is scoped to the max form and the hull is scoped to the marginal only. Coordinate with C-R1-20 so one clause serves both.

### C-R1-22
raiser: R1
severity: MAJOR
class: RUN
panel_lines: 351–359
condition: The one internal test of the imported elasticity's implied magnitude (realized cross-sectional gradient $+4.198$pp vs model-implied $+0.937$pp, ratio 4.48, power 0.675) is computed at a demoted calibration and declined rather than diagnosed. The implied gradient must be recomputed analytically at the 4.991% headline floor and under the additive form, at 75/100/125 PSA.
location: §V.D ¶"A cumulative counterpart" (.tex:315); §V.E qualification six (.tex:333); `tab:assembly` last row (.tex:338)
verified: true — every figure reproduces from `episode_confrontation_results.json`: `verdict.inputs.realized_gradient_pp = 4.198179219676357`, `gradient_ci95_pp = [3.5852591750975797, 4.656477952145319]`, `model_implied_gradient_pp_at_0.069 = 0.9371125522400376`, `part_a.primary_age_matched.realized_over_implied_mid = 4.479909280524726`, `part_b.power_at_named_betas.mid.power_injected = 0.675`, `verdict.branch = "T5"`, `t5_subcase = "excess_gradient_ci_above_model"`, permutation `p_value_one_sided = 0.004975`. The composition-standardized $+3.44$ is `episode_confrontation_within_results.json` `limb_a.standardized_gradient_pp = 3.4409160684432125` (CI $[+1.170,+5.140]$). R1's two enabling facts are both confirmed in the artifact's own spec: `spec.model_implied_path` = "**ANALYTIC** from hazard eq.(2): max(h_floor, h0_PSA(age)*exp((-beta1)*100*gap)), **production floor 4% / FLOOR_MODE max / PSA-100** … NO engine run"; and the censoring asymmetry is `oos_identification_results.json` `floor_bind_share` 0.6882 at 4.991 against 0.3627 at 4.0.
fix: RUN, cheap and engine-free. Evaluate the same analytic path $\max(\underline{h}, h_0^{PSA}(\text{age})e^{-\beta_1 \cdot 100 g})$ at (a) $\underline{h}$ = 4.991% CPR and (b) the additive combination $h = 1-(1-\underline{h})(1-h^{vol})$, each at 75/100/125 PSA, on the frozen bucket definitions. Existing machinery: `hazard/episode_confrontation.py` (its `main()` must not be called — it would rewrite the frozen artifact; `hazard/episode_confrontation_within.py` shows the established pattern of replicating the committed gates line-for-line instead) plus `hazard/competing_risks.py` for the additive survival-scale combination. Writes a new artifact (e.g. `episode_implied_gradient_grid_results.json`) with a G-gate reproducing $+0.9371$ at the committed 4%/max/PSA-100 cell bit-exactly. Must not touch `episode_confrontation.py`, its artifact, or the pinned $+4.20$/$[+3.59,+4.66]$/$+0.94$/$0.68$/$p=0.005$ literals (the within-run's `spec.must_not_change` names them and `tools/liveness_gates.py` carries them).

### C-R1-23
raiser: R1
severity: MAJOR
class: STRUCTURE
panel_lines: 359
condition: If the implied gradient approaches the realized $+3.4$ to $+4.2$ only at additive or steeper-ramp settings, that is the paper's first *realized-data* evidence bearing on the form fork and belongs in §VII.F's form discussion, not filed in `tab:assembly` as a declined directional counterweight.
location: `tab:assembly` last row (.tex:338); §VII.F form paragraph (.tex:709); the current landing is recorded in `episode_confrontation_within_results.json` `verdict.landing` ("UPWARD entry in tab:assembly … Status 'directional; not a marginal re-estimate'")
verified: true — the artifact's own landing confirms the current filing, and §VII.F's form paragraph currently rests the form choice on semantics plus the mixture curve with no realized-data input.
fix: Conditional on C-R1-22's result: move/duplicate the finding into §VII.F with the grid, keeping the existing `tab:assembly` row and its "directional; not a marginal re-estimate" status. If the grid shows the implied gradient *flatter* at the headline floor (as the 68.8% vs 36.3% bind shares predict) and steeper only under the additive form, that must be stated as evidence about the form, not about $\beta_1$'s magnitude — the artifact's own verdict sentence forbids reading an excess gradient as corroboration of $\beta_1$.

### C-R1-24
raiser: R1
severity: MINOR
class: WORDING
panel_lines: 365
condition: `tab:assembly` / `tab:uncertainty` quote the ladder grid-read $\sim+3.8$ at the age-standardized floor where a measured value exists; quote the measured $+3.7$ with the grid-read beside it.
location: .tex:333 ("the age-standardized floor read of 5.51\% implies a marginal near $+3.8$"), .tex:433, .tex:713; gate-pinned as `ASSEMBLY_SPANS["ladder_agestd"] = "floor read of 5.51\\% implies a marginal near $+3.8$"` (`tools/liveness_gates.py:385`)
verified: true — `b5_joint_cell_results.json` `conventional_agestd`: `marginal_pp = 3.67131541392159`, `ladder_implied_pp = 3.8`, `measured_minus_implied_pp = -0.1286845860784096`; `agestd_floor_pct = 5.507748455937158`. Flagged by R1's reproducibility verdict as one of the two printed numbers to change; the substitution's direction is favourable to the headline.
fix: Wording. Print $+3.7$ measured (grid-read $3.8$ beside it, $-0.13$ wedge) at the three sites; move the `ASSEMBLY_SPANS["ladder_agestd"]` span and re-run the census of the literal before committing (the gate asserts presence and ladder ordering).

### C-R1-25
raiser: R1
severity: MINOR
class: WORDING
panel_lines: 367
condition: The demoted percentile rung's printed lower edge depends on an unlabelled convention: 26 of 1,000 draws fall outside the PCHIP grid, all above the 6.0% floor edge (i.e. all on the low-marginal side), and the two conventions differ at exactly the endpoint the paper cares about. The convention and the count belong in one clause of the Table 9 note.
location: Notes to `tab:ladder` .tex:467–468; the percentile row .tex:456
verified: true — `layer_convolution_results.json` `layers.floor_percentile`: `n_draws_outside_grid_excluded = 26`, `n_truncated_above_grid_hi = 26`, `n_truncated_below_grid_lo = 0`, `ci95_pp_edge_truncation = [2.280914554561832, 8.014703355311358]` against `ci95_pp_exclusion = [2.974329560125351, 8.01850965353176]`, with an explicit `disclosure` field saying all 26 sit on the low-marginal side. `2.281` appears nowhere in the manuscript, and `floor_inference_correction_v2_results.json` `parity_gates.P2_percentile_bitexact_R2.n_draws_outside_grid = 26` carries the same count.
fix: Wording. One clause in the Notes to `tab:ladder` naming the exclusion convention, the 26/1000 count, their one-sided position, and the $[+2.281,+8.015]$ alternative. Committed literals; no run. Same clause should carry the CR3-BM / WCR lower-edge truncation flags noted in C-R1-02 if either rung is promoted.

### C-R1-26
raiser: R1
severity: MINOR
class: WORDING
panel_lines: 369
condition: Two width ratios circulate for one comparison; the denominator must be named in the tablenote.
location: `tab:uncertainty` headline row .tex:433 — "loan/stratum cluster bootstrap $[+4.63, +6.92]$pp (width $0.39\times$ the corrected floor read; 25.8 effective clusters)"
verified: true — the loan layer width is 2.2935pp (`layer_convolution_results.json` `dependence_bracket.comonotone_components_pp.loan_layer`); $2.2935/5.8230 = 0.394$ against the Webb width, while `bootstrap_pathb_cluster_results.json` `comparison.width_ratio_vs_floor_read = 0.4546851318235146` is computed against the *percentile* width 5.0442 (`floor_read_interval_pp = [2.974…, 8.018…]`). Both are internally correct; the manuscript prints only 0.39 and does not name its denominator.
fix: Wording. Name the denominator in the `tab:uncertainty` note (0.39× the Webb corrected read; 0.455× the demoted percentile read). Committed literals.

### C-R1-27
raiser: R1
severity: MINOR
class: REFERENCE
panel_lines: 371
condition: R1 asks that "The two layers sit on disjoint data and disjoint time" be rephrased to "different observation windows and different aggregation units", the stated reason being wrong (both layers sit on the same Freddie 2017–2021 origination universe).
location: n/a in the manuscript — the phrase lives in `layer_convolution_results.json` `dependence_bracket.note`
verified: false as a manuscript defect — `disjoint` appears nowhere in `revised_paper_v18.tex`. The manuscript says only "the two layers convolved as independent, $[+2.80, +8.99]$pp … independence is assumed, not measured --- under maximal positive dependence the width is $8.12$pp" (.tex:433), which makes no claim about disjointness. R1's substantive point (the two layers share the origination universe; only observation windows and aggregation units differ) is correct on the facts and would be a fair addition, but there is no wrong reason on the page to repair.
fix: No manuscript edit required. If the point is worth carrying, add the correct reason ("different observation windows and different aggregation units") as a positive statement at .tex:433; and note in the reply that the offending sentence is an artifact field, not manuscript prose. The comonotone hedge is confirmed correct: `comonotone_width_pp = 8.116490407183028` → "8.12".

### C-R1-28
raiser: R1
severity: MINOR
class: WORDING
panel_lines: 373
condition: The paper's single imported parameter is evaluated at a quarterly slot $P_q = 0.06$, four times Liebersohn–Rothstein's own 1.5% zero-gap moving level; the near-insensitivity claim is asserted in the main text with the derivation deferred. Print $\beta_1(P_q)$ at $\{0.015, 0.03, 0.06, 0.12\}$ in `tab:params`.
location: .tex:231 (the claim: "retained because the conversion is nearly insensitive to it over $P_q \in (0, 0.12]$ (Appendix~\ref{app:params})"); Appendix E .tex:1087 (the derivation: "in the small-$P_q$ limit the transform reduces to $\beta_1 = -\ln(1-\delta) = 0.0672$ … over $P_q \in (0, 0.12]$ … the central $\beta_1$ ranges only from $0.0672$ to $0.0701$"); `tab:params` .tex:239
verified: true — both texts are as R1 describes; the 1.5% comparison is stated twice (.tex:229 footnote and .tex:231); Appendix E gives only the endpoints of the range, no per-$P_q$ values, and `tab:params` carries no $P_q$ row.
fix: Wording plus a four-cell arithmetic evaluation of `eq:beta1` at $\delta = 0.065$ (analytic, no engine, no artifact needed — the transform is $\beta_1 = -\ln[(1-(1-(1-\delta)P_q)^{1/3})/(1-(1-P_q)^{1/3})]$ at .tex:228–230). Add one row or one tablenote line to `tab:params`; check `tests/test_elasticity_discipline_gate.py` and `tests/test_units_conventions.py` for pinned $\beta_1$ literals (0.0686/0.068571/0.069/0.0693) before editing.

### C-R1-29
raiser: R1
severity: MINOR
class: WORDING
panel_lines: 375
condition: The stratum-cluster bootstrap is a ratio estimator with random denominators and the percentile interval is not bias-corrected; the resampled loan count moves from 54,134 to 101,404. One sentence, or a fixed-$n$ (rescaled-weight) variant.
location: .tex:277 — "the resampled loan count varies from roughly $54{,}000$ to $101{,}000$, which is harmless here only because the engine renormalises the pool to Fed holdings each month, so the level is set exogenously and only composition varies"
verified: true — `bootstrap_pathb_cluster_results.json` `n_loans` = {p2_5: 54134.325, median: 75612.5, p97_5: 101403.6, sd: 11342.5}; the renormalization defence is on the page exactly as R1 reports, and no statement about ratio bias or bias correction appears. `cluster_structure`: 130 clusters, 25.777 effective, largest 9.77% — all as printed.
fix: One sentence at .tex:277 conceding that composition weights are then a ratio of random totals and the percentile interval is uncorrected. A fixed-$n$ rescaled-weight variant would be a RUN (`hazard/bootstrap_pathb_cluster.py`, 200 replicates, new artifact) and is optional — R1 accepts the sentence.

### C-R1-30
raiser: R1
severity: MINOR
class: WORDING
panel_lines: 377
condition: "The interval does not contain zero" is offered as the first of "three things that stop the list from becoming a retraction" after the paper has established that the sign is forced; if the sign is forced the zero-exclusion carries no information and should not be in that list.
location: .tex:333; the sign-forcing establishment is .tex:323 (99.53% of exposure at or below 5.09% against a window-minimum 30-year rate of 5.2311%, `sign_forcing_stats`)
verified: true — .tex:333 reads "Three things stop the list from becoming a retraction. The interval does not contain zero, and the sign is fixed by the window's rate configuration rather than by any of these calibrations, as the sign-forcing argument above establishes, so nothing here bears on the direction of the result." The 99.53% figure is confirmed at .tex:323 and reused at .tex:590. Mitigation: the sentence already conjoins the sign-forcing point in the same breath, so the paper is not treating zero-exclusion as independent evidence — but it does list it first.
fix: Wording. Drop the zero-exclusion clause and let the sign-forcing sentence carry the point alone (three items become two, or a different third is named). Check `ASSEMBLY_SPANS` / `tests/test_assembled_corrections_gate.py` for a pinned span on this sentence before editing (`posture_lower_half` and `posture_retired_range_carries` sit on the same line).

### C-R1-31
raiser: R1
severity: MINOR
class: WORDING
panel_lines: 379
condition: The CR1-BM note is confusing because CR1-BM $[+2.753,+8.796]$ and CR3-conventional $[+2.773,+8.774]$ coincide at one decimal but are distinct objects; print the unrounded pairs in the note.
location: `tab:ladder` rows .tex:459 (CR3 $t$: "$+2.8$ to $+8.8$") and .tex:462 (CR1 $t$, Bell--McCaffrey: "$+2.8$ to $+8.8$"); note .tex:467 ("its Bell--McCaffrey row printing CR3's conventional-df interval is an accident of this leverage profile, not an identity")
verified: true — `floor_inference_correction_v2_results.json` `reads.R2….cr1_t_interval_df_bm.marginal_ci95_pp = [2.753082197773479, 8.79621469284935]` (df 6.246) and `cr3_t_interval.marginal_ci95_pp = [2.7732237922014704, 8.774405758790092]` (df 30); both print as $+2.8$ / $+8.8$. The note's characterization is correct as R1 concedes.
fix: Wording. Add the unrounded pairs to the Notes to `tab:ladder`. The row literals are gate-pinned (`cr1_conventional`, `cr1_bell_mccaffrey`, `df_ownership` spans near `tools/liveness_gates.py:4577` and `tests/test_floor_ladder_gate.py`), so add to the note rather than altering the printed rows.

### C-R1-32
raiser: R1
severity: MINOR
class: STRUCTURE
panel_lines: 381
condition: `tab:pathadiag` mixes specifications in adjacent rows ("Aggregate recovery (spec v4) \$928.9bn" directly above "point \$915.1bn (spec v3)"); a single-spec table with the other spec in a footnote would remove the trap.
location: `tab:pathadiag` .tex:1107–1123 (rows at .tex:1114–1117; the tablenote at .tex:1122 already says "the table mixes two")
verified: true — the adjacency and the per-row labels are exactly as R1 describes, and the note discloses the mixing.
fix: Structure. Demote the spec-v3 rows to a tablenote (or split into two tables). Appendix-only, no committed literal changes; check `tests/test_verdict_audit_gate.py` / render gate for pinned row text.

### C-R1-33
raiser: R1
severity: MINOR (inferred — reproducibility verdict limit (i))
class: META
panel_lines: 407
condition: `specs/` holds 14 files against ~60 named runs; for the remainder, pre-run status rests on script-header commit ordering, which the paper documents only for the floor sweeps. The convention is sound but is verifiable only from git history, not from the paper.
location: Appendix A .tex:780–782 (the commit-ordering disclosure, e.g. `ad52db6` at .tex:782); `tab:runindex` .tex:816–878
verified: true — `specs/` now holds 15 files (`DRAFT_R29_A2_floor_rename.md`, `DRAFT_R29_length_levers.md`, `DRAFT_R30_E7_CR1.md`, `DRAFT_WPE_sec3_sec4.md`, `DRAFT_WPE_sec5_exhibits.md`, `DRAFT_WPE_sec7_policy.md`, `PATCH_G2A.md`, `RECORD_R30_ginnie_vintage_infeasible.md`, `SPEC_R30_wal_normal_turnover.md`, four `SPEC_round28_*.md`, `SPEC_round28_H1_zero_months.md`, `VERIFIED_R32_prep.md`) — R1's 14 plus one added since; `tab:runindex` carries 58 `\texttt{}` run tags, matching R1's "~60 named runs"; the only commit hashes in the manuscript are the floor-sweep pair at .tex:782.
fix: Wording. Either extend Appendix A's ledger so the spec-before-run ordering is checkable from the paper for the runs that carry headline numbers, or state plainly that for runs without a `specs/` file the ordering is verifiable from git history alone. No run.

### C-R1-34
raiser: R1
severity: MINOR (inferred — reproducibility verdict limit (ii))
class: META
panel_lines: 407
condition: Appendix A's disclosure that two freezes ran on uncommitted trees and that one ABM manifest's `git_commit` points at the pre-run parent (with cohort-bucket count 7 vs 11 as the substitute identifier) is honest and should stay — but it means the ABM headline is not commit-addressable.
location: Appendix A .tex:780 and .tex:782
verified: true — .tex:780: "two freezes ran on uncommitted working trees, so manifest git hashes alone do not name an exact reproduction checkout … specifications must be identified by cohort-bucket count---seven for the thirty-year-only specification, eleven for the fold-in---rather than by the manifest commit"; .tex:782: "a manifest's recorded \texttt{git\_commit} is the pre-run parent of the freezing commit".
fix: No change requested — R1 says the disclosure should stay. Optional one clause stating the consequence (the ABM headline is not commit-addressable) if the paper wants to own it explicitly.

### C-R1-35
raiser: R1
severity: MAJOR (inferred — Argument Coherence score basis)
class: WORDING
panel_lines: 418
condition: "Two structurally distinct estimators" survives in the framing of a decomposition that only one estimator can produce; the framing must be scoped.
location: §III.A heading `\subsection{Two Structurally Distinct Estimators}` .tex:120; the framing sentences at .tex:50 and .tex:58
verified: true — the heading and both sentences are present verbatim; the decomposition and the marginal are Path B objects only (Path A is excluded from every headline on the resimulation interval spanning zero, and the ABM null's sign disagrees: $+270.4$ vs $-105.3$, carried in `LETTER_CURRENT_LITERALS`, `tools/liveness_gates.py:739`).
fix: Wording. Scope the framing where the decomposition is introduced (two estimators for the aggregate level; one for the mechanical/elastic partition). Heading edits may be gate-pinned — check `tools/liveness_gates.py` and `tests/test_render_gate.py` for the subsection title.

### C-R1-36
raiser: R1
severity: MAJOR (inferred — Writing Quality score basis, 52/100)
class: STRUCTURE
panel_lines: 419
condition: At 139pp the structure carries none of the load: the longest body paragraphs run thousands of words, mean sentence length is 39–44 words in §V.B/§V.E against a field norm near 22–26, single sentences reach 111 words, and a referee cannot locate a claim's conditions without re-reading its paragraph. R1 grades this a substantive defect, not a courtesy deduction.
location: §V.B `sec:pathb` (.tex:217–306, longest lines 231 at 7,348 chars and 227 at 5,697); §V.E `sec:identification` (.tex:317–468, line 323 at 10,640 chars — the longest body paragraph in the `.tex` — and line 333 at 6,233); Appendix G `app:ridge` (.tex:1168–1223); `tab:verdicts` block (.tex:1393+)
verified: partly — the defect is real and measurable, but R1's specific figure does not reproduce on the `.tex`: the longest single body paragraph is 10,640 chars at .tex:323 (§V.E), not 14,732 in §V.B. R1's number is most likely the md edition's merge of .tex:227 + `eq:beta1` + .tex:231 (5,697 + 7,348 ≈ 13.0k chars plus the display equation), which renders as one paragraph after conversion. Direction, magnitude and section attribution of the underlying problem all hold.
fix: Structure. Split the four or five longest paragraphs (.tex:323, 269, 277, 231, 709) at their natural argument seams and shorten sentences in §V.B/§V.E; a prior round already built length levers (`specs/DRAFT_R29_length_levers.md`). Any split must preserve gate-pinned spans verbatim — `ASSEMBLY_SPANS`, `ABSTRACT_POSTURE`, the ladder spans and the ABM_LEAD spans are all whole-sentence pins.

### C-R1-37
raiser: R1
severity: MAJOR (inferred — Evidence Sufficiency score basis, 60/100)
class: WORDING
panel_lines: 417
condition: The evidence supports "mostly mechanical under the max form" and "the margin is small-to-moderate and positive"; it does not support a 0.1pp-resolution interval. The reported precision should be cut to what the design carries.
location: abstract .tex:31 ($+2.9$/$+8.7$/$+5.6$ to one decimal); `tab:headline` row 4 .tex:79; `tab:uncertainty` .tex:433; `tab:ladder` rows .tex:456–465
verified: partly — the manuscript already prints the ladder and the headline to one decimal only, and states repeatedly that the range rather than any point is the identified content (.tex:333, .tex:79 "an anchor convention rather than a central tendency"). So R1's target is the *endpoint* resolution ($+2.9$ vs $+2.3$ across rungs, $\pm0.06$pp between weight schemes), not spurious extra digits. The supporting facts hold: no outcome holdout exists (the paper concedes this itself at .tex:716 — "a floor-stability check rather than an outcome holdout"), the elasticity is entirely external with no SE propagated, and 49% of SOMA book face lies outside the estimation universe (the paper prints the complement, 51.0% coverage, at .tex:146).
fix: Wording. State the design's resolution once (e.g. the interval is credible to about half a point, given a 0.06pp weight-scheme wobble and a 5pp-wide ladder) and stop leaning on one-decimal endpoint comparisons in the posture sentences. No run.

### C-R1-38
raiser: R1
severity: MAJOR (inferred — Evidence Sufficiency score basis)
class: WORDING
panel_lines: 417
condition: The imported elasticity's evidential base is entirely external and no standard error is propagated from it; that absence should be stated where the interval is claimed, since the interval prices only the floor read.
location: `tab:uncertainty` headline row .tex:433 and its note .tex:440; .tex:231 (the import); abstract ¶2 .tex:31
verified: true — the manuscript propagates the elasticity as a swept *band* (5.5/6.5/7.7, `tab:lowband`) and never as an estimated uncertainty; the interval is explicitly "at the central elasticity $\delta = 6.5\%$ … not an interval on the elasticity" (.tex:433/.tex:79). Path A supplies no in-sample sign support (`patha_sign_test_results.json` verdict T3, $p = 0.093/0.412/0.241$), so no internal SE exists to propagate — which is why the fix is a disclosure, not a computation.
fix: Wording. One clause at .tex:433/.tex:440: no sampling error from the source elasticity enters any layer of the ladder; the band edges are a convention sweep, not a confidence interval. Overlaps C-R1-14's label fix and C-R1-28's $P_q$ row — do them together.
