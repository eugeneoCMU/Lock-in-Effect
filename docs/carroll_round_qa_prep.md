# Carroll Round — Q&A preparation (R32, 2026-07-29)

Three prepared answers for the attacks the REVIEW3 panel judged likeliest. Every
number below was re-derived from a committed artifact or the draw itself in this
session; the artifact key is named beside each so it can be re-checked at the
podium. The framing throughout is **concede first, then state what survives** —
the panel's own recommendation, and the only framing that holds up when the
questioner already knows the answer.

**Standing instruction:** do not quote $-\$89.4$bn / $-\$117.7$bn (the Danish
buyback-credit reversal) aloud until R32 Task 14 lands. R2 established that every
Danish cash figure is roughly 2× too large because the discount is taken at the
representative-coupon state rather than derived from the leg's own realized 5.61%
CPR. The **sign survives**; the magnitude does not. Quote the sign, not the cash.

---

## Q1. "Your $+5.6$ rests on a 100 PSA seasoning ramp you never estimated."

**Concede immediately, and do not defend $+5.6$ as a central tendency.** The
baseline seasoning ramp is a convention, not an estimate, and it is the widest
disclosed layer in the paper: sweeping 75–150 PSA on both legs carries the
marginal from $+0.9$ to $+15.6$ points at the off-window floor — a 14.77pp span
with **no coverage property**, because it is a range over a convention I did not
estimate and its endpoints are not draws from anything.
(`psa_level_sweep_results.json` → `ranges["4.991"]`: `lo_pp` 0.8560, `hi_pp`
15.6265, `width_pp` 14.7705.)

**Then lead with the claim that survives the entire sweep** — the mechanical
majority, not the marginal:

| Ramp | Null recovery (shared basis) | Central-leg marginal |
|---|---|---|
| 75 PSA | 92.8% | $+0.9$ pp |
| 100 PSA (production) | 85.7% | $+5.6$ pp |
| 125 PSA | 73.3% | $+11.4$ pp |
| 150 PSA | 59.3% | $+15.6$ pp |

The null delivers the majority of the $\$764.7$bn shortfall at **every** point on
the convention sweep. That is the robust finding; the marginal's magnitude is not.
(Shared basis = standalone `share_pct` less the common curtailment flow,
`shared_layer_scoring_results.json` → `curtailment_netted_b` = 69.5622, over the
764.7483 benchmark — a flat 9.096pp. All four reproduce to the printed digit.)

**State the limit of that defence yourself, before it is put to you.** The
majority is a property of the **max floor form**. Under the additive form the same
null at 100 PSA recovers **35.6%**, which is not a majority
(`floor_form_mixture_results.json` → `cells["4.991|1|0"].share_pct` = 44.6996
standalone, 35.60 shared). So the defensible sentence is *"the mechanical baseline
delivers the majority under the production floor form, across the whole ramp
convention"* — never the unqualified version. The abstract now says exactly this.

**What is being done about it:** R32 Task 9 re-anchors $h_0$ on Path A's estimated
seasoning spline, which converts this layer from a convention into an estimate.
It runs under a committed spec with a landing rule per outcome branch. If it moves
the marginal against the headline, that result lands and gets reported.

---

## Q2. "Your 75,000 loans are not a sample of the SOMA book."

**Correct, and own the table before being asked.** There are **three different
objects** here, and conflating any two of them produces a wrong number:

| Vintage | The draw (by count) | Estimation universe (exposure-wtd) | SOMA book face |
|---|---|---|---|
| pre-2017 | 0% | 0% | 10.6% |
| 2017–19 | **60.0%** | 12.5% | **6.0%** |
| 2020 | 20.0% | 37.3% | 16.3% |
| 2021 | 20.0% | 50.2% | **43.9%** |
| 2022 | **0%** | 0% | **23.1%** |

Draw shares read directly from `loan_sample.parquet` (15,002 / 14,999 / 15,001 /
14,997 / 15,001 — an equal-allocation stratified design, ~15,000 per vintage, all
weights 1.0, `weight_sum` = 75,000). Book face from
`composition_shift_results.json` → `committed_anchors.vintage_shares`.

So: 2017–19 is **60% of the draw against 6.0% of book face** — a 10× overweight by
count. The 2021 vintage carries **43.9% of book face on 20% of the draw**. And
2022, **23.1% of book face**, is absent by construction — the sampler's vintage
range is `[2017, 2021]`.

**Why this is not a composition footnote.** Under the max form the marginal is
zero wherever the baseline sits below the floor. Vintage weighting therefore
changes *censoring geometry*, not just a weighted average — which is why the panel
upgraded this to CRITICAL (Z1).

**Bounds already committed, so this is not undisclosed:** vintage residual bound
$\$11.75$bn = 1.54% of benchmark (`vintage_bound_b` 11.7481, `vintage_bound_pct`
1.5362); full-book coupon reweighting moves the level 107.0% → 109.1%; PSI 4.33 on
vintage and 2.29 on coupon — with the artifact's own caveat that PSI inflates
where the sample carries structural zero mass on book support, which is exactly
the 2022 and pre-2017 case.

**Concede what is still missing:** Table 25 currently gives the *universe*-vs-book
comparison only — the **draw's own composition row is not in the paper**, and the
sampler's equal-allocation rule is nowhere in the manuscript. Both are being added
(R32 Task 10), together with a post-stratification of the draw onto SOMA coupon ×
vintage cells.

---

## Q3. "The floor read behind your headline has almost no estimation support."

**Concede first and concede hard — this is the panel's most consequential
finding, and understating it is the one move that will not survive follow-up.**

The clean 2018 rising-rate leg carries cohort-months in **two age buckets only**:
505 at age [0,12) and 155 at age [12,24). Every bucket at 24 months or more is
**empty** — zero cohort-months, zero exposure. The three headline floors
(4.695 / 4.991 / 5.334%) all come from `age>=12` cells with 125 / 137 / 155
cohort-months, and every corresponding `age>=24` cell is empty. So the
mature-seasoning test is **not computable rather than passed**: the artifact's own
verdict string is `CLEAN_BY_CONSTRUCTION_MATURE_TEST_NOT_COMPUTABLE`, with
`mature_test_computable: false`. (`oos_identification_results.json` →
`instrument1_oow_floor.legs.2018_rising_rate`.)

**State the direction of the error against yourself.** Every cell where the
mature-versus-12–24 contrast *is* measurable puts mature turnover **higher**
(`fannie_floor_read_results.json`, headline selection cell `gap<=-0.0025`):

| Regime | age ≥12 | age ≥24 | Contrast |
|---|---|---|---|
| In-window 2023–24, Freddie (refi-suppressed) | 3.922% | 4.002% | $+0.08$pp |
| In-window 2023–24, Fannie | 3.962% | 4.151% | $+0.19$pp |
| Pooled 2017–19, Freddie (**refi-contaminated**) | 5.185% | 8.920% | $+3.74$pp |
| Pooled 2017–19, Fannie (**refi-contaminated**) | 5.522% | 10.136% | $+4.61$pp |

Twelve of twelve measurable cells point the same way. The in-window pair is the
one comparable **in regime** to the clean leg, so $+0.08$–$0.19$pp is the honest
guide and the contaminated pooled figures are an upper bound, not an estimate.
Conclusion to state plainly: the clean read **understates** the mature book's
baseline turnover and therefore **overstates** the marginal. The error is signed
against the headline and its size is unpriced.

Do **not** cite the 2018 leg's own $+1.558$pp rise from age [0,12) to [12,24) as
evidence for this. The artifact flags it `ramp_rise_is_psa_confounded: true`. The
cross-agency mature cells are the evidence; that ramp is not.

**Both floor corrections sit above the clean band's 5.334% top:** the
age-standardized read 5.51% (→ marginal near $+3.8$) and the Fannie read 5.52%
(→ below the $+4.3$ edge).

**Do not present those two as independent confirmations of each other.** The
0.01-point gap between them is a coincidence between two different perturbations:
the age standardization imputes **84.0% of its weight** from the in-window age
gradient and the paper labels it an indicative bound rather than a measurement;
the Fannie 5.52% is a **cross-agency read on the pooled 2017–19 cell**, whose
like-for-like Freddie counterpart is **5.185%** (`difference_pp` 0.337). Most of
the distance from 4.991 to 5.522 is the *pooling*, not the agency. Both readings
do point the same way, and that is all they jointly establish.

**Land on the composed cell.** It has been run under a pre-committed landing rule
(`b5_joint_cell`) and measures $+2.9$ points, an interaction within 0.1 of
proportional. The corrections compose to the **bottom of the binding interval**,
whose lower edge is the soft one — which is the paper's own posture, not a
concession extracted at the podium.

---

## If pressed further

- **"Then what do you actually identify?"** A marginal, not a level and not
  monthly timing. The design bounds the marginal between $+2.9$ and $+8.7$ points
  under the production floor form — the widest *layer* that has a coverage
  property, though not the widest *rung* within it (see the next item). The
  form-conditional hull is $+3.5$ to $+13.1$.
- **"Why Webb, and not a wider rung?"** Open — R32 Task 6. Webb (5.823pp) is
  **not** the narrowest of the ten rungs; it is the narrowest among those with a
  credible few-cluster coverage property. The full ladder at the headline read
  (`floor_inference_correction_v2_results.json` → `reads.R2_2018_gap<=-0.0025_age>=12`,
  widths in pp): percentile 5.044, CR1-t 5.197, CR2-t 5.579, **Webb 5.823**,
  Rademacher 5.927, CR3-t 6.001, CR1-BM 6.043, CR2-BM 6.740, WCR 6.828,
  CR3-BM 7.284. If asked before Task 6 lands: the selection is being restated, and
  note that CR3-BM $[+2.28, +9.56]$ and WCR $[+2.28, +9.11]$ both carry a
  **grid-truncated lower endpoint** — both clip to $+2.2809$ at the 6.0%
  floor-sweep edge (`truncated_at_grid_edge: true`) — so promoting either would
  require extending the floor grid first. CR2-BM $[+2.41, +9.15]$ is untruncated
  and is the honest wider comparator to quote.
- **"Is the sign identified?"** No — the sign is *forced*, not estimated. Over the
  forty window months the cohort panel covers, the exposure-weighted mean coupon
  on the surviving book is 3.134%, with 99.53% of exposure at or below 5.09%
  against a window-minimum 30-year rate of **5.2311%** (the August 2022 monthly
  mean, the window's rate dip; `sign_forcing_stats`). Essentially the whole book
  is out of the money throughout the window, so the margin cannot come out
  negative. The paper demotes this to a consistency check rather than claiming it
  as identified content, and says so. The identified content is the bounded range.

## Do not say

- "$+5.6$ is the central estimate." It is one member of a range, and the paper
  attaches no posture to where it sits.
- "The mechanical baseline delivers the majority." Always attach the form.
- "Two independent corrections agree." See Q3.
- Any Danish cash magnitude. See the standing instruction at the top.
