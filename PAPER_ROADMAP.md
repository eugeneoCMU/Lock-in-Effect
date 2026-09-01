# PAPER ROADMAP — Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall

Internal companion document. Not part of the manuscript; never cited by it; safe to
edit freely (no gate or test pins any span in this file).

**What this is.** A map of the whole paper for anyone (including a future session)
who needs to work on it without re-deriving it: what each section argues, which
numbers are headline and which are demoted, one canonical name for every recurring
concept, and disambiguation tables for the terms and numbers that look alike but are
not.

**Source of truth.** `paper/final/paper_final_v1.tex` (1,411 lines; `\appendix` at
line 766) plus `paper/final/replication_appendices.tex`, both on branch
`claude/v20-review-fixes`. Naming note: the file says "v18" but its content is
current through the v20 review-fix round (it carries the v20 N1-relanded inference
ladder, the paradigm withdrawal, and the v20 panel fixes). Line numbers cited below
are for that file at commit `3002141`. Every factual statement in this document was
extracted from the manuscript and independently re-verified against it
(draft-by-one-model, verify-by-another); if this document and the manuscript ever
disagree, the manuscript wins.

**Conventions in this document.**
- One canonical term per concept (Section 4). Where the paper itself uses variants,
  the variant list is recorded there and this document sticks to the canonical form.
- No new notation is introduced anywhere in this document. Every symbol used here is
  the paper's own, and Section 9 is the complete list.
- Every recovery percentage or marginal quoted here carries its three labels —
  **floor** (in-sample 4.0% vs off-window 4.99%), **accounting basis** (usually the
  shared basis), and **floor form** (production hard-maximum vs additive) — because
  the same object legitimately takes different values under different labels, and an
  unlabeled number is how misquotes happen.

---

## 1. The paper in plain language

U.S. fixed-rate mortgages are repaid at face value and are not portable, so when
market rates jumped in 2022, households holding 3% mortgages faced a large penalty
for moving: the **lock-in effect**. The Federal Reserve was simultaneously trying to
shrink its mortgage-bond portfolio by letting loans pay off ("Quantitative
Tightening"), with monthly redemption caps of up to $35 billion. Because locked-in
households did not prepay, actual paydowns ran **$764.7 billion below the caps** over
June 2022–November 2025.

The paper's question is *not* "did lock-in slow the runoff?" (the Fed's own staff had
said so). It is: **how much of that shortfall was ever about household rate
responses at all?** The answer is: surprisingly little. A model with the rate
response switched **off** — the same loan-level engine with one coefficient set to
zero, so loans still prepay at a seasoning-driven baseline speed above a measured
floor of housing turnover, just never *because* rates moved — already accounts for
**85.7%** of the shortfall (headline calibration, main accounting basis, production
floor form; only **35.6%** under the additive form, and see 2.1 for what the null
does and does not contain). Switching the rate response **on** adds a **lock-in
marginal** the paper deliberately reports as a range: **+1.9 to +9.1 percentage
points** of the benchmark, roughly **$1 billion a month**. The caps were set 1.7–1.9× above what the Fed's own projections said was
achievable, so most of the "shortfall" was arithmetic, anticipated, and rate-
inelastic — while the real cost of lock-in lands on households who could not move,
not on the Fed's cash flow.

Around that core sit: an agent-based model of household choice that *fails* to
explain the shortfall (used as a stress test, with the tempting "household models
are the wrong paradigm" reading formally **withdrawn**); a Danish counterfactual
showing the institutional cash-flow cost is a consequence of the U.S. par-payoff
rule; a cap-design analysis; and an unusually heavy layer of pre-committed rules,
disclosed failures, and demotions that the paper treats as part of the result.

## 2. The spine: the numbers that carry the paper

Every other number in the paper hangs off one of these. All percentages are of the
$764.7B benchmark on the **shared basis** under the **production floor form** unless
labeled otherwise.

| # | Object | Value | Label discipline |
|---|--------|-------|------------------|
| 1 | Cap-relative benchmark (“the shortfall”) | **$764.7B** (net, Jun 2022–Nov 2025) | The denominator of every recovery %. A construction, not an estimate. |
| 2 | Rate-inelastic baseline (β₁ = 0 null) | **85.7%** at the off-window floor; 88.7% in-sample; only 35.6% under the additive form | The paper’s central decomposition fact: the floor form, not fine calibration, is what swings it. |
| 3 | Path B central level | **91.3%** at the off-window floor; 97.9% in-sample (107.0% standalone basis) | Level is floor-dominated → explicitly *not* evidence for the elasticity. |
| 4 | Lock-in marginal (the identified object) | **+5.6 pp = $42.6B** at the off-window floor (anchor convention); **+9.2 pp = $70.3B** at the in-sample point | The two floors bracket two *estimands*, not two readings of one number (Section 5, pair 1). |
| 5 | Binding interval on the marginal | **[+1.9, +9.1] pp** (wild-cluster restricted inversion, 31 clusters) | The only quoted range with a coverage property. The identified content is this range, not any interior point. |
| 6 | Production ABM | **13.6%** fifty-seed mean ($103.7B); frozen seed-42 draw 11.9% ($91.0B) | Seed mean is the headline; the frozen draw is only the reproducibility anchor. |
| 7 | Expectations-based complement | **$87.8B** vs the Fed’s own May-2022 projection; lock-in ≈ half of it (23–80% across floors/allocations, all upper bounds) | Second denominator; caps were expected non-binding, so this is the “surprise” part. |
| 8 | Cap-design arithmetic | Caps set **1.7–1.9×** the Fed’s own contemporaneous projection | Third contribution; computable ex ante. |
| 9 | Danish rule-only counterfactual | **+$61.2B** (face accounting, zero-refinance edge; at the in-sample floor — compare to $70.3B, not $42.6B) | Sign is forced by the anchor; magnitude is the content; flips to −$51.0B under cash accounting. |

### 2.1 What the β₁ = 0 null actually computes

Row 2's one-line gloss — and the abstract's "scheduled amortization plus a turnover
floor" — compresses a six-term hazard, and it reliably misreads as *amortization
only*. It is not amortization only. The null prepays the book at a measured mean
**5.87% annual CPR** at the headline floor — *faster* than the central leg's 5.36%.
Everything below is Path B; `hazard/no_lockin_null.py` is the run.

**The switch is one scalar.** The null sets `p_q_shock_pct = 0.0`, which feeds
`rothstein_beta1(0.0)`. That returns exactly zero — the shocked and baseline
quarterly mobility probabilities coincide, so the log-ratio is log 1, and the
module asserts the exact-zero before running. Nothing else changes: same 75,000-loan
sample, same RNG seed, same floor, same scorer, same accounting. The null and the
central leg are two passes of one engine differing in one number, which is what makes
their difference (eq:marginal) the paper's identified object.

**The hazard, term by term.** Path B's monthly prepayment hazard
(`hazard/literature_hazard.py:prepay_hazard`) is

```
h_vol  = h₀(age) · exp( (−β₁)·100·gap  +  β_fico·z_fico  +  β_ltv·z_ltv  +  β_burn·burnout )
h_prep = max( h̲ , h_vol )                                     ← production floor form
```

Setting β₁ = 0 kills the first term inside the exponent and nothing else. What
survives, with what each is measured to be worth:

| Term | In the null? | What it is | Measured size |
|---|---|---|---|
| Scheduled amortization | **yes** | Contractual principal, `scheduled_amortization_smm(coupon, 360, age)`, applied to every surviving loan after the hazard step | The level's backbone; never ablated because it is the contract |
| `h₀(age)` — 100 PSA seasoning ramp | **yes** | CPR rising 0.2 pp per month of loan age to 6% at month 30, flat thereafter. Voluntary prepayment behavior, on the null's side of the line | Widest within-form convention layer (the PSA sweep); aggregate fit cannot arbitrate it |
| `h̲` — baseline turnover floor | **yes** | 4.0% annual CPR in-sample, 4.991% at the headline off-window read. Floors *total* turnover, not the strictly-involuntary part | Dominant level-setter. Bind share is cell-specific: 35.79% of the null's 1,683,124 evaluated loan-months at the headline floor, 68.82% of the central leg's (see the trap below) |
| FICO / LTV covariates | **yes** | `β_fico = −0.15`, `β_ltv = +0.10` on standardized scores | 1.3 points |
| Cohort burnout | **yes** | `β_burn = −0.5` on stratum cumulative prepaid share | 0.45 pt at the headline floor; 0.86 pt in-sample ($3.48B / $6.58B) |
| Competing-risk default + delinquency pipeline | **yes** | `h_def = 0.0003 · exp(2.0·stress + …)`, Bernoulli draw, Markov servicer states. Retained as a *competing risk*, not a prepayment channel: `default_upb = 0.0` is hard-coded, so a defaulting loan leaves the active pool without ever being credited as roll-off. The proportional clamp `normalize_competing_hazards` is the identity at production magnitudes | ≤ $0.39B |
| **Rate-gap term `(−β₁)·100·gap`** | **NO** | The imported Liebersohn–Rothstein elasticity | **This is the marginal: +5.6 pp / $42.6B at the headline floor** |

So six of seven terms survive. The null is the *whole model minus one coefficient*,
not a stripped-down amortization table.

**The null prepays *faster* than the central leg.** This is the single most useful
fact for reading the decomposition, and it is measured, not derived. Mean U.S. annual
CPR over the window (`floor_form_mixture_results.json`, cells `floor|ω|p_q`):

| Cell (production `max` form, ω = 0) | null (p_q = 0) | central (p_q = 6.5) |
|---|---|---|
| In-sample 4.0% floor | **5.614%** CPR, floor binds 14.34% | 4.763% CPR, floor binds **36.27%** |
| Headline 4.991% floor | **5.874%** CPR, floor binds 35.79% | 5.359% CPR, floor binds 68.82% |

The null runs the book off *harder* than the central leg, because lock-in is exactly
what suppresses prepayment. So the null is not a slower, cut-down model that trails
the real one — it is the faster one, and it still leaves 85.7% of the shortfall
unexplained-away. The floor's bind share is the mirror of this: the rate-gap term
pushes `h_vol` under the floor, so the floor pins the *central* leg roughly twice as
often as the null in both calibrations.

Where the floor does *not* bind — 64% of the null's 1,683,124 evaluated loan-months
at the headline floor — the hazard is set by the PSA ramp times the covariate and
burnout multiplier. The floor is the dominant *level-setter* through its effect on
the pinned region, not because it governs most loan-months of the null.

**Three rate channels the null keeps.** "Rate-inelastic" is exact; "rate-blind" is
not, and the difference is load-bearing.

1. **The default leg stays rate-sensitive.** `rate_stress = max(0, market − coupon)`
   enters `default_hazard` with `γ = 2.0`. It is not switched off by β₁ = 0. On a
   3 bp/month base it is immaterial (the whole delinquency channel is bounded at
   $0.39B), but the null is not literally free of rates even inside the hazard.
2. **The floor is read off realized, partly behavioral turnover.** The read is an
   exposure-weighted CPR over *all* prepayment on deep-discount cohorts — voluntary
   moves and cash-out refis mixed with strictly involuntary events, the involuntary
   share "plausibly well under half". So if lock-in depressed baseline turnover
   itself, part of what the null books as baseline belongs to the lock-in channel
   and the rate-inelastic share overstates what is invariant to household behavior.
   The paper concedes this in the abstract and rules it *unadjudicable below
   gap ≤ 0*, not refuted.
   **Do not evidence this with the 6.9%-vs-3.9% contrast.** The 2019 leg's 6.910%
   is `regime_contaminated` **and** `seasoning_contaminated`, verdict `CONTAMINATED`,
   filed under `contaminated_upper_anchors` — a falling-rate refi wave, i.e.
   refi-*inflated*, not lock-in-free. And the paper's own version of the comparison
   (6.910% at gap ≤ 0 against the retained 2018 leg's 4.991% at gap ≤ −0.25) it
   calls "not a valid comparison as written" because the depths differ; at matched
   depth the 2018-vs-2019 spread runs 1.576 / 0.491 / 2.112 / 0.857 points,
   non-monotone. Direction check: anchoring on the contaminated 6.91% read collapses
   the marginal to **+$5.69B**, so this correction would gut the marginal, not
   merely relabel the level.
3. **The benchmark is a rate-determined object.** The $764.7B denominator exists
   because rates rose. The null explains a rate-caused gap without a rate term; it
   does not describe a world without the rate shock.

**Why 85.7% and 35.6% are the same run.** The form fork is not a recalibration —
it is one line of `prepay_hazard`:

```
FLOOR_MODE == "max"       →  h_prep = max( h̲ , h_vol )                 [production]
FLOOR_MODE == "additive"  →  h_prep = 1 − (1 − h̲)(1 − h_vol)           [competing risks]
```

The difference is exactly `additive − max = min(h̲, h_vol) · (1 − max(h̲, h_vol))`:
a strictly positive addition at **every** loan-month, largest where the floor does
*not* bind (there `max()` discards the floor entirely while the additive form stacks
the whole of it). At the headline floor the null's mean CPR goes **5.874% → 10.408%**
and its recovery **94.8% → 44.7%** standalone (85.7% → 35.6% shared) — same
elasticity, same floor, same sample, same loan draw. The paper's own statement of the
reason: "a 4% involuntary hazard added to moderate voluntary hazards raises book-wide
prepayment."

**Censoring is the wrong explanation for that level gap, and the right one for the
marginal.** With β₁ = 0 there is no elasticity in the null to censor — the level gap
is pure hazard stacking. Censoring is what makes the *marginal* form-dependent:
under `max()`, wherever the floor pins the hazard, switching the elasticity off
cannot raise it at all, so the marginal is zero in those cells and falls as the floor
rises (+9.2 at 4.0%, +5.6 at 4.991%). The additive form never censors, so its
marginal is nearly floor-invariant (+11.25, moving only +11.29→+11.21 across a 3–5%
floor range). **The max form's floor-dependence is censoring, not elasticity
content** — and conflating the two mechanisms is the easy mistake here, because both
are consequences of the same one-line switch.

**Fit cannot settle the fork.** The additive central leg recovers 55.9% of the
benchmark at the headline anchor against its 44.7% null — undershooting the max
form's aggregate level by 43.5 to 45.3 points at every off-window anchor. That looks
like a decisive argument for the production form and is not available as one:
reading rule 3 forbids treating the level as evidence, and the paper states the
headline "is not a position defended by fit". The fork is resolved by the floor's
*semantics* (what share of the read is strictly involuntary), which is why the
two-point fork was replaced by the **mixture curve in ω** — and the curve rises to
+9.7 points by ω = 0.25 and plateaus near +11.2, so the paper's own reading of the
floor (strictly-involuntary share "plausibly well under half") points at the hull's
upper region while the headline sits at the ω = 0 conservative endpoint.

**Traps specific to this object.**
- The null is **not** "the mechanical component" and **not** "the non-behavioral
  baseline" (reading rule 5). β₁ = 0 partitions rate-elastic from rate-inelastic.
  The PSA ramp is voluntary behavior and it is inside the null.
- 85.7% (shared) and 94.8% (standalone) are the same run on two bases, exactly
  9.096 pp apart. 88.7% / 97.8% is that same pair in-sample. Four numbers, one
  object; mixing a standalone level with a shared one manufactures the retracted
  18.3-point "real-book gap" (S4).
- **The two 36% bind shares are different objects.** The paper's "the floor binds in
  36% of the 1,683,124 evaluated loan-months in the production U.S. run" is the
  *central* leg at the *in-sample* 4.0% floor (36.27%). The *null* at the *headline*
  4.991% floor is 35.79% — also "36%", a different cell. At the headline floor the
  central leg's bind share is 68.8%. Quote the cell, not the rounded number.
- The null "recovering 85.7%" is a statement of **fit, not prediction** — no
  outcome-holdout months exist anywhere (reading rule 7).
- The null reproduces the central leg's three-month lag peak. Nothing about timing
  distinguishes the two legs (reading rule 4).
- Distinguish this from the **scaled null** (look-alike pair 11), which additionally
  rescales the seasoning baseline to φ* = 0.754 and lands at +0.9 pp — outside the
  binding interval.

### 2.2 Where β₁ itself comes from

2.1 covers what switching β₁ off removes. This covers where its *value* comes from,
because every headline marginal is that one imported number pushed through one
transform. Nothing about β₁ is estimated in this paper.

**Source.** Liebersohn & Rothstein, "Household mobility and mortgage rate lock,"
*Journal of Financial Economics* 164 (2025), 103973; NBER WP 32781 (2024). Cite key
`liebersohn2024`.

> **Naming trap.** The code says `rothstein_beta1`, `ROTHSTEIN_Q_DECLINE_LOW/MID/HIGH`
> ([config.py:39-41](hazard/config.py:39)). There is no separate Rothstein paper.
> Rothstein is the second author of the Liebersohn–Rothstein import the manuscript
> cites. Code shorthand, one source.

**The estimand and the band.** They estimate that a 100 bp rise in the prevailing
rate above the locked-in coupon reduces **quarterly mobility probability** by
**5.5% to 7.7%**, depending on specification. That proportional decline is δ. The
paper adopts the **6.5% midpoint ex ante** as central, band edges as sensitivity
bounds.

**The transform (eq:beta1).** Their estimand is a quarterly probability; eq:pathB
needs a monthly proportional-hazard coefficient. The survival-function conversion:

```
β₁ = −ln[ ( 1 − (1 − (1−δ)·P_q)^(1/3) ) / ( 1 − (1 − P_q)^(1/3) ) ]
```

The inner terms are the monthly single-month mortalities implied by constant-hazard
compounding inside the quarter, `1 − P_q = (1 − h_m)³`. The **superseded
continuous-hazard ("divide-by-3") variant is a distinct object the simulation does
not use** — it survives only in the appendix.

| δ | Role | \|β₁\| | Marginal it produces |
|---|---|---|---|
| 5.5% | L&R band low | 0.0577 | band low edge |
| **6.5%** | **L&R midpoint, adopted ex ante** | **0.068571** (prints 0.069 in tab:params) | **+$70.3B / +9.2 pp in-sample; +$42.6B / +5.6 pp at the headline floor** |
| 7.7% | L&R band high | 0.0817 | +$79.5B / +10.4 pts at the production floor |
| 9.0% | Fonseca–Liu, *outside* anchor | ≈0.096 | +$87.9B / +11.5 pts at the production floor |

**`P_q = 0.06` is a conversion auxiliary, not a measurement.** It occupies the
transform's quarterly slot and nothing else. It sits well *above* Liebersohn–
Rothstein's own 1.5% zero-gap quarterly moving level, and is retained because the
conversion barely notices it:

| P_q | 0.015 | 0.03 | **0.06** | 0.12 |
|---|---|---|---|---|
| \|β₁\| at δ = 0.065 | 0.0675 | 0.0679 | **0.0686** | 0.0701 |

Quadrupling the assumed moving level above the source's own moves the imported
coefficient by under four percent.

**Sign convention.** `rothstein_beta1` returns β₁ **negative** (−0.068571), and
`prepay_hazard` applies `(−β₁)·(gap·100)` against a negative gap. The paper prints
β₁ **positive** in eq:pathB. Both conventions are live in the repo; marginal columns
are unaffected. (Related: the tab:lowband printing trap in the §V entry.)

**Two transport assumptions, plus a separate mapping assumption.** The paper's
"Transport assumptions" subsection names exactly two; the scope question is
introduced separately as a mapping assumption. Do not collapse them into "three
transport assumptions".

1. **Aggregation / response homogeneity.** The source estimand is a **ZIP-code-level
   moving hazard**, applied here as a loan-level log-hazard coefficient. Named, not
   priced.
2. **Survival selection.** Their population is not conditioned on mortgage survival;
   eq:pathB applies the coefficient to a pool from which **34,734 of the 75,000**
   sampled loans had already prepaid before the window opened — depleted of exactly
   the rate-responsive. Signed toward attenuation and priced: under the gamma-frailty
   identity η = S_pre^ξ, the off-window marginal reads **+5.1 / +4.6 / +3.7** points
   at ξ = 0.25 / 0.5 / 1 (run `attenuation_sensitivity`). ξ is not estimable in this
   design and is displayed as the free parameter.

*Mapping assumption — moving-vs-refi scope.* Their estimand is a **moving**
probability; eq:pathB applies β₁ to the **entire voluntary hazard**, refinancing
included. The pre-committed μ-bracket prices it (runs `moving_share_bracket`,
`moving_share_bracket_offwindow`): 1−μ of the voluntary hazard at no response, μ at
full response, floor unscaled, parity at μ = 1.

| μ | in-sample 4.0% floor | headline 4.991% floor |
|---|---|---|
| 1 (production) | +$70.3B | +$42.6B |
| 0.5 | +$37.7B (+4.9 pts) | +$25.7B (+3.36 pts) |
| 0.25 | +$19.2B (+2.5 pts) | +$13.9B (+1.82 pts) |

Mildly **super**-proportional at the higher floor, because that floor censors the
elasticity in more loan-months and censored contributions do not scale with μ
(the same censoring mechanism as 2.1). The convention is *signed*: applying the
import to less of the hazard can only shrink the marginal, roughly by its share.
No termination-reason field exists in the ingested data, so μ is a bracketing
parameter, never an estimate, and production stays at μ = 1.

**Corroboration from outside the import — both from *above* the band.**
- **Graybill et al. (2026):** a transaction-record sale-hazard response of roughly
  **7–11% per percentage point**, in a housing-market-equilibrium setting touching
  no credit file. Only the 7% low end falls inside 5.5–7.7%; the midpoint sits above
  the high edge. It also lands on exactly the margin μ varies.
- **Fonseca & Liu (2024):** ≈9% moving-rate reduction per 100 bp → β₁ ≈ 0.096 →
  +$87.9B (+11.5 pts), above the L&R high edge yet inside the pre-committed box.

Both are read as **directional corroboration, not competing point estimates** — a
sale hazard and a moving-rate reduction are not unit-comparable to a
quarterly-mobility decline. Their joint effect is to make the adopted central
calibration **conservative** among available literature estimates.

**Traps specific to this object.**
- **The 5.5–7.7% band is a specification range, not a confidence interval**
  (look-alike pair 12). No sampling error of Liebersohn–Rothstein's is propagated
  anywhere in this paper; the only interval with a coverage property is the binding
  interval on the *floor* read.
- **The elasticity's evidential basis is the external literature alone.** Path A's
  own rate-gap coefficient is not statistically distinguishable from zero under any
  bias-respecting construction, so it corroborates nothing about magnitude.
- β₁'s **causal** content is inherited from the source, not established here
  (reading rule 3). "Identifies" means a within-model counterfactual decomposition.
- The band's monotone response across the sweep is **forced**: eq:beta1 is monotone
  in δ and the hazard monotone in β₁ at this book's gap configuration, so the
  ordering composes monotone maps. It is a wiring check, not identified content —
  the same status as the sign (reading rule 2).

## 3. Reading rules (the paper's own discipline)

These are rules the manuscript itself states and enforces with gates. Violating any
of them in prose *about* the paper produces a misquote.

1. **Always attach the floor label.** The paper's own rule (line 306): never quote a
   level from one floor beside a marginal from another; any level printed without a
   floor label is at the in-sample 4.0% calibration.
2. **The range is the identified content.** +5.6 is "an anchor convention rather
   than a central tendency" (line 71); +9.2 is "the in-sample calibration point, not
   the headline". Neither the marginal's point value nor its **sign** is identified —
   the sign is forced by the window's rate configuration (97.40% of exposure sits
   at or below a 4.79% coupon, and at least 99.5% below the window-minimum 5.2311%
   market rate), so all-cells-positive is a wiring check.
3. **Levels are not evidence.** The aggregate level is floor-dominated; recovering
   ~100% of the benchmark says little about the elasticity. The design identifies
   the *difference* between two runs of one engine (central minus null), never the
   level, and never causally — "identifies" means a within-model counterfactual
   decomposition; β₁'s causal content is inherited from the literature it is
   imported from.
4. **Timing carries no credential anywhere.** The β₁ = 0 null reproduces the same
   three-month lag peak, four clip-induced zero months corrupt the monthly
   benchmark, and no estimator's monthly co-movement survives detrending. Every
   claim from the benchmark is a claim about **levels**.
5. **The baseline is not "non-behavioral".** The floor is read off realized, partly
   behavioral turnover. The partition separates *baseline* from *increment*, not
   mechanics from behavior. Never gloss the null as "the mechanical component".
6. **Pre-committed ≠ pre-registered.** The paper reserves "pre-registered" for
   third-party registries; its own repository-committed rules are "pre-committed", a
   disclosure device, not a proof — to be read net of the verdict appendix, which
   records post-run adjudications including outright failed predictions.
7. **No outcome-holdout months exist anywhere**, without exception. The 19/23-month
   floor split holds out *calibration* months, not the benchmark. Every recovery
   percentage is a description of fit, not a prediction.
8. **Two different denominators are in play.** Percentages "of the benchmark" divide
   by $764.7B (cap-relative). The 49%/80% lock-in shares divide by the $87.8B
   expectations-based complement. The ratio between the two denominators is 8.7×.
9. **The withdrawn stay withdrawn.** The paradigm reading (§VII.C) and the
   88.5%≈88.7% projection-null convergence (§III) are formally withdrawn; the
   weaker statements that replaced them are the only citable forms (Section 11).

## 4. Canonical vocabulary — one term per concept

Use the term in the first column; the paper's variants are listed so you can
recognize them, not so you can use them. "Never say" flags actively wrong forms.

| Canonical term | What it means | Paper's variants | Never say |
|---|---|---|---|
| **the benchmark** ($764.7B, cap-relative) | Net shortfall of realized SOMA MBS roll-off vs the phased redemption caps, Jun 2022–Nov 2025. Net: two opening months are settlement *inflows*. | "empirical benchmark", "cap-relative benchmark", "the shortfall" | that it shows the Fed *missed* anything — the caps never bound; it measures composition of the decline |
| **trapped liquidity** | Same object as "the shortfall", used for simulated legs (positive = runoff fell short). | "shortfall", "trapped balance/roll-off" | — |
| **rate-inelastic baseline (the β₁ = 0 null)**; "the null" after first use | The comparison leg with the imported elasticity off: scheduled amortization from the book's coupon/age/term mix + baseline turnover at its observed level. | "$β_1=0$ null", "rate-inelastic null", "null leg" | "non-behavioral baseline", "mechanical baseline" |
| **lock-in marginal** | R(central) − R(β₁=0): the paper's identified object. Basis-invariant (the $69.56B curtailment netting cancels exactly). Always floor-labeled. | "the marginal", "headline marginal", "bounded margin" | "margin" (collides with mobility/rate-responsive/cash-flow margins); an unlabeled point value |
| **baseline turnover floor**; "the floor" after first use | The constant hazard floor h̲ in eq:pathB — the annual-CPR level below which Path B never lets prepayment fall; read from realized turnover on deep-discount cohorts; the design's dominant level-setter. Floors on **total** turnover (strictly-involuntary share "plausibly well under half"). | "turnover floor", "floor read" (its measured value), "floor level" | "involuntary-turnover floor" (the paper flags it as an alias at line 89 and uses it once more, in the transportable-lesson paragraph) |
| **in-sample calibration point** (4.0% floor) | The floor calibrated in-window on locked-in 2023–24 discount cohorts. Returns +9.2 pp / $70.3B. Demoted from headline. | "production floor", "in-window calibration" | "production floor" when precision matters — "production" also modifies form/ABM/run |
| **off-window floor** (the headline calibration, 4.70–5.33%) | The floor re-read on pre-episode 2018 discount cohorts (the three defensible depth-cut reads on the 2018 leg; pooled-17–19 and 2019 legs are refi-contaminated). The mid-grid 4.99% read sets the headline +5.6 pp / $42.6B. | "headline floor", "off-window anchor", "clean band"; the table title says "out-of-sample" — text says off-window | calling +5.6 central or best |
| **depth** (of out-of-the-moneyness) | The gap threshold (≤0 / ≤−0.25 / ≤−0.5 pt) at which a floor read is defined — a second axis besides *when* the months are read. The +9.2→+5.6 demotion is 73.7% window, **26.3% depth** ($20.9B / $7.4B); at matched depth the in-sample point is $63.5B. | "depth cut", "depth ladder" | describing the demotion as purely an out-of-sampleness effect |
| **rate gap** | Loan coupon minus prevailing market rate (100 bp units in eq:pathB); negative = locked in. | "gap"; "coupon gap"/"yield gap" only inside the Danish/Berger discussion | mixing its units: g is in 100 bp units, g̃ decimal, ABM's r is a rate *level* |
| **Path B** (the headline estimator) | Loan-level literature-calibrated microsimulation, competing prepayment/default risks, stratified 75,000-loan Freddie draw (40,234 window-start survivors). Every headline level and marginal is Path B's. | "microsimulation form"; **hybrid pipeline** = Path B CPR scored through the ABM accounting layer (carries the Danish legs) | — |
| **Path A** (the excluded aggregate-context leg) | Stratum-month discrete-time hazard, Poisson pseudo-ML, full 2017–21 origination universe (296 cells / 295 fixed effects). "Aggregate context only"; excluded from every headline by pre-commitment; its rate-gap coefficient's sign is *not distinguishable from zero* under any bias-respecting construction. | "cohort-hazard form" | citing its 112.4% (shared) / 121.5% (standalone) as support for anything |
| **the hazard framework** | The container for Paths A **and** B, used only for the paradigm contrast with the ABM. | "hazard side/leg/path" | attaching numbers to it — numbers belong to Path B or Path A by name |
| **the ABM** (synthetic-population stress test) | 10,000-household agent-based model, utility-maximizing relocation rule, synthetic population drawn to FRED medians. A stress test, not an estimate. | "production ABM", "household-choice model" | "the ABM shows household choice doesn't explain the shortfall" without the qualifier **synthetic-population** |
| **accounting basis** (four) | standalone-scorer / **shared** (main-text: nets the common $69.56B curtailment flow = flat 9.1 pp) / full-book (reweights to book coupon mix) / composed (both). Pure presentation; cancels from every marginal. | "benchmark-consistent shared", "the shared layer"; pick one hyphenation of "standalone-scorer" | "berger basis", "cap-shortfall basis" (neither exists in the paper) |
| **face vs cash accounting** | The Danish leg's *incidence* axis — retired balance credited at face vs net of the market discount. Flips the institutional gap's sign (+$61.2B face → −$51.0B cash). Face answers the benchmark question, cash the reserve-drain question; the difference is the par windfall, a transfer. | "cash-haircut reading", "balance-adjustment reading" | confusing this axis with the four accounting bases (which never flip signs) |
| **the binding interval** [+1.9, +9.1] pp | The floor read's own sampling error propagated at the central elasticity: wild-cluster **restricted inversion**, 31 clusters, selected by a pre-committed coverage rule (measured coverage 94.3%/95.1%). Webb [+2.8, +8.7] and CR2 Bell–McCaffrey [+2.4, +9.1] stand *beside* it. Prices one layer only; no elasticity sampling error exists anywhere in the paper. | "binding layer", "quoted interval" | preferring the narrower percentile [+3.0, +8.0] — it under-covers, and its construction silently excluded 26/1000 off-grid draws |
| **the calibration box** (+2.1 to +13.2) | The pre-committed 7-floor × 3-band grid (21 cells; a *separate* 27-cell joint floor-ladder × band rerun also exists). A grid over conventions with **no coverage property** — the elasticity band is Liebersohn–Rothstein's *specification* range, not an estimate with a standard error. | "the box"; beware "envelope" (also names the 11.06-pt Fannie gate — don't reuse the word) | treating box membership as statistical confidence |
| **production floor form (hard maximum) vs additive form** | *How* the floor combines with the voluntary hazard: production takes max(floor, hazard) — censoring the elasticity where the floor binds; additive combines on the survival scale, never censoring. First-order: flips the null 85.7%↔35.6% and the marginal +5.6↔+11.2. The **mixture curve** in ω replaces the two-point fork. | "max form", "competing-risks form/combination", "form-conditional hull" (+3.5 to +13.1) | reading the additive +11.2 as stronger evidence for lock-in (the fork is about censoring, not the elasticity) |
| **U.S.-intercept anchor (rule-only)** | The production Danish transplant: Berger et al.'s moving-flatness, level anchored at the U.S. zero-gap hazard, floor retained — only the payoff rule changes. +$61.2B. The two other named anchors: **Danish-level** (bracketing, −$99.9B), **mechanism-extrapolated** (+$925.5B, superseded — the paper's own earlier figure, corrected by an order of magnitude). | "rule-only transplant" | "the Danish counterfactual" bare, without one of the three anchor labels |
| **pre-committed** | A rule/grid/gate/threshold entered into the repository before the run executed. A disclosure device, not a proof. | "fixed ex ante", "frozen" | "pre-registered" (reserved for third-party registries) |

## 5. Look-alike pairs — different concepts that will merge if you let them

Each pair below is two *different* objects. The one-line difference is the verified
distinction; getting any of these backwards is a substantive error, not a nuance.

1. **In-sample marginal (+9.2, $70.3B) vs off-window marginal (+5.6, $42.6B).** Two
   *estimands*, explicitly "not conservative and liberal readings of one estimand":
   the in-sample figure is best read as **total rate-attributable prepayment
   suppression** (and an upper bound only on the *strictly-voluntary* elasticity's
   contribution); the off-window figure bounds that total from **below** (the
   higher off-window floor reclassifies ~$20.9B of turnover as baseline).
2. **Floor dispersion vs floor cyclicality.** Dispersion is one-sided amplification
   of *any* floor variation by the hard-maximum rule (a Jensen effect; survives
   scrambling the time order: 85.0% of the κ-grid span remains under permutation).
   Cyclicality is genuine co-movement with the rate cycle — real but capped at
   $5.29B in any cell. The additive form eliminates 98% of the dispersion span.
3. **ABM fifty-seed mean ($103.7B, 13.6%) vs frozen seed-42 draw ($91.0B, 11.9%).**
   The mean is the headline; the frozen draw is the reproducibility anchor the run
   manifests freeze (≈34th percentile of its own distribution; seed SD $24.5B; read
   the ABM as "order of 10–17%", not a three-digit point).
4. **"Out-of-window": time sense vs vintage sense.** Same string, two axes: the
   floor's off-window *reporting months* (2017–19, pre-episode) vs out-of-window
   *vintages* (the 33.7% of book face originated in 2022 or before 2017, outside the
   Freddie 2017–21 sample). The off-window floor was NOT measured on different
   vintages — it is a different time period.
5. **The four accounting bases vs face-vs-cash.** The four bases are netting and
   reweighting layers that cancel from the marginal. Face-vs-cash is the Danish
   incidence question and *reverses the sign* of the institutional gap.
6. **Cap-relative benchmark ($764.7B) vs expectations-based complement ($87.8B).**
   Two denominators for one episode (never-binding caps vs the Fed's own May-2022
   projection). The marginal is ~5.6% of the first and ~49% of the second.
7. **Binding interval [+1.9, +9.1] vs calibration box [+2.1, +13.2] vs hull
   [+3.5, +13.1].** A sampling interval with measured coverage vs a convention grid
   vs a two-form envelope. Their widths are NOT close (6.8 vs 11.1 vs 9.6 points),
   and only the first has any coverage property. The hull may never be quoted alone
   — always together with the binding interval.
8. **The hazard framework vs Path B.** Framework = A + B; headline numbers are B
   alone. Quoting "the framework recovers 91.3%" is fine only because the value is
   B's; wholesale framework attribution would import Path A's excluded 112.4%.
9. **Floor anchor, sense A vs sense B.** Sense A: the off-window floor *value*
   (tab:oosfloor's "Floor anchor" column, a CPR level chosen for Path B's h̲).
   Sense B: the ABM's calibration *target* — the turnover moment θ is re-derived to
   hit. Sense B alone produces the $294B gap between the recalibrated (59.3%) and
   frozen (20.9%) cross-design variants.
10. **Temporal holdout (19/23-month floor split, +$45.1B) vs an outcome holdout.**
    The split holds out calibration months; no realized prepayment from held-out
    months enters either leg. It tests the floor's temporal stability, never the
    marginal against data.
11. **The β₁ = 0 null vs the scaled-null variant.** The null switches the elasticity
    off, seasoning baseline untouched. The scaled null *additionally* rescales the
    seasoning baseline (φ* = 0.754 ≈ 75.4 PSA) to price Aladangady's 44%
    attribution — and lands at +0.9 pp under the production form, *outside* the
    binding interval (form-conditional: +8.5 under the additive form).
12. **The elasticity band (5.5–7.7%) vs a confidence interval.** It is
    Liebersohn–Rothstein's specification range with the adopted midpoint at its
    centre. No sampling error of theirs is propagated anywhere.
13. **Recalibrated (59.3% / 60.2% / 76.3%) vs frozen (20.9% / 22.0% / 12.6%)
    cross-design variants.** Identical real covariates; they differ only in whether
    θ is re-derived to hold the 4–5% turnover floor. The frozen leg misses that
    turnover moment on all fifty seeds — the corroborating-looking leg is the *less*
    admissible one.
14. **Path A's estimated coefficient (+0.29 per 100 bp) vs Path B's imported β₁
    (0.0686).** Different scales, different estimands (prepayment hazard vs
    quarterly mobility). Compared on sign only — and even that is an orientation
    check, since the imported band cannot come out the other way.
15. **A correction to the marginal vs a change of estimand.** The off-window
    re-anchor and the age-standardized floor read *correct* the same question; the
    Ginnie overlay (+4.4) and vintage overlay (+3.7) *re-scope* it onto a sub-book.
    Lining them all up as successive downward corrections double-counts.
16. **The 6.0-year duration extension vs the floor-comparator extension.** Same
    empirical WAL path, two comparators: against 2021 refi-boom speeds (3.4yr) the
    extension is 6.0 years and measures refinancing-versus-turnover; against the
    floor's off-window read it nearly vanishes (9.4 vs 9.5 open; 8.5 vs 8.6 close).
    Quoting "lock-in extended duration six years" is the exact error the table note
    blocks.
17. **The shortfall (mostly rate-inelastic) vs the duration extension (the
    rate-driven object).** The bank-fragility channel feeds off the *extension*, not
    the cap arithmetic.
18. **"The marginal" vs ordinary "margins".** The paper also says mobility margin,
    rate-responsive margin, cash-flow margin, originator margin. Never shorten the
    identified object to "margin".
19. **88.7% vs 88.5%.** The null's in-sample shared-basis recovery vs the
    projection's uniform-spread implied share. Their 0.2-point proximity was once
    presented as convergence and is **withdrawn** — doubly conditional coincidence.
20. **+9.2 pp (in-sample marginal) vs 9.1 pp (the flat standalone→shared netting)
    vs +9.1 (the binding interval's upper edge).** Three unrelated objects one
    decimal apart.

## 6. The argument, section by section

Main text is lines 1–765; each entry: what the section does, what it commits to,
and its traps. Statuses used: *measured* (a construction from data), *identified*
(the within-model decomposition the design supports), *bounded*, *consistency-check*
(wiring, not evidence), *conceded*, *withdrawn*, *imported* (external, qualified).

### Abstract + §I Introduction (lines 31–89)

Sets the entire epistemic posture in one page and one table. States the fact
($764.7B), demotes the obvious story (the null already recovers 85.7%), delivers
lock-in as a bounded range with an anchor it refuses to call central, and names the
three contributions: the decomposition, the expectations-based complement ($87.8B),
and the cap-design arithmetic (caps at 1.7–1.9× the Fed's own projection). Two
design elements are explicitly *not* contributions: the cross-design test (a
validation device that ran against the paper's own ABM reading) and the Danish
order-of-magnitude correction (of the paper's own earlier $925.5B extrapolation).

- **Table 1 (`tab:headline`, lines 56–87)** is the paper's own one-page spine — every
  row repeats a committed, gated figure, and its tablenote (line 87) carries the
  sensitivity catalogue for the headline marginal.
- **The Definitions paragraph (line 89) is the paper's built-in glossary** — four
  accounting bases, two floor calibrations, the floor's measured reads
  (3.8–3.9% in-window; 4.70–5.33% off-window band with a *soft lower edge*; 5.51%
  age-standardized and 5.52% Fannie reads sit above the band), CPR back-out
  conventions, the trapped-liquidity definition, the grid-not-confidence-region
  distinction, and the no-outcome-holdout property. Read it before editing anything.
- §I traps: the four-ranges family (rule 2 of Section 3); 5.52% appears twice on one
  line with unrelated meanings (CPR back-out vs Fannie floor read); the in-window
  floor *read* is 3.8–3.9% but the in-sample calibration *point* is 4.0%; the flow
  restatement of the marginal is ~$1B/month against the $35B cap.

### §II Literature Review (lines 91–111)

Places the two estimators in five strands: prepayment theory (Dunn–McConnell
"ruthless exercise" → Schwartz–Torous hazard ancestry → Stanton's S-curve →
Agarwal's threshold → Chernov's turnover/rate split, which the null
operationalizes); the 2022–25 lock-in literature; behavioral-residual work; the
Danish institutional literature (supplies the *rule* and the *slope*, never a priced
U.S. counterfactual); and — closest — the Fed's own staff notes, whose mechanism the
paper concedes as established and extends in four named measurement ways.

- Traps: Graybill–Mangum "corroborates" the imported elasticity band from **at or
  above** it (only the 7% low end overlaps 5.5–7.7%); berger2026 is an unrefereed
  July-2026 working draft and lesniewski2026 an arXiv preprint — two load-bearing
  theoretical anchors are unrefereed, and the abstract itself flags "an unrefereed
  import"; the 170→300 bp spread numbers are the author's own FRED computation, not
  boyarchenko2019's.

### §III Empirical Methodology (lines 112–146)

Defines the instruments and builds the target. Two structurally distinct estimators
(ABM; hazard framework with Paths A and B — two estimators, three runnable models);
the $764.7B cap-relative benchmark construction (net accumulation; four exactly-zero
months are a non-negativity-clip artifact, not behavior — repairing them flips the
frozen monthly-timing rule from PASS to CONCEDE, one reason every claim is
levels-only); the four accounting bases; and the expectations-based complement
($740.6B projected vs $652.8B realized ⇒ $87.8B), built from the NY Fed's May-2022
OMO report under a pre-committed uniform-spread allocation of its annual print.

- **The withdrawal that lives here:** the 88.5% ≈ 88.7% projection–null convergence
  is formally withdrawn ("I withdraw the presentation"). What survives is coarse and
  allocation-robust: under the production floor form, both objects put the
  anticipated rate-inelastic component in the **large majority** of the shortfall.
- Coverage: the Freddie 2017–21 conventional universe covers **51.0%** of SOMA book
  face on the book's own agency × vintage joint cells (66.2% is the vintage-only
  marginal and overstates; 20.4% of face is Ginnie). External-speed overlays bound
  the exclusions: Ginnie $20–47B, out-of-window vintages $11.7B — both signed toward
  overstating trapped liquidity.
- The curtailment netting ($69.56B = flat 9.1 pp = 0.84%/yr, one object in three
  units) is bit-identical across legs, so it cancels **exactly** from every marginal
  — the structural reason the marginal is basis-invariant.
- Standing caveat (line 144): the benchmark "measures the composition of the
  decline… not a claim that the decline itself fell short" — the Committee's
  operating object was the aggregate portfolio, a cap shortfall is not by itself
  evidence a policy objective was missed, and nothing in the paper shows the
  aggregate path came in off course. The 49%/80% marginal shares of the complement
  are allocation-conditional **upper bounds** resting on two untestable conditions.
- Traps: the 115.3% allocation bracket means the expectations shortfall turns
  negative (ratio *undefined*, not enormous); three coverage numbers 51.0/51.8/52.7
  are one estimate plus two bounds, not competitors.

### §IV Agent-Based Model Results (lines 147–171)

A stress test, not an estimate — and the section's own lead depends on a later
section's result. Every specification tried (rational baseline 71.1% → behavioral
extensions 54.9% → 45.1% → 33.7% → production) moves *away* from the benchmark.
Production headline: **fifty-seed mean $103.7B = 13.6%** (frozen seed-42 draw
$91.0B = 11.9%, the manifests' reproducibility anchor). Path fit is a disclosed
failure (simulated CPR 11.68% vs empirical 5.14% ABM-basis; r₀ = −0.318;
R² = −6.98 — negative because R² is defined against a mean-only null, worse than a
constant). The burnout variant fails *informatively*: closed-population survivor
selection collapses CPR to ~0 and overshoots to 147% — the stated reason burnout is
cohort-level in Path B.

- **The paradigm reading is WITHDRAWN** (formally in §VII.C; §IV's lead points to
  it): the cross-design leg on real Freddie structural covariates recovered
  59.3%/60.2%/76.3% — *above* the pre-fixed 50% undercut threshold on all fifty
  seeds. What §IV falsifies is a **synthetic-population** household-choice
  specification; whether the ABM–hazard contrast is paradigm or data source is
  explicitly not separable.
- **No ABM marginal exists.** The two ways of building an ABM null disagree in sign
  (+270.4 vs −105.3 implied marginals; a feasibility probe, not a pre-committed
  estimate) — so the paper reports *no* ABM differential and the estimator contrast
  stays a contrast of levels. (The ABM's 4–5% "turnover floor" is a calibration
  target for θ, not a separable model term like Path B's floor — this is why.)
- The SMD two-moment falsification returns joint infeasibility (nearest admissible
  fit overshoots at 107.1%) under a pre-fixed verdict vocabulary.
- Traps: 54.9% (highest behavioral recovery) is a revoked recalibration artifact —
  never cite it as behavioral support; "above threshold" here means *fail*;
  147% / 107.1% / +116.3% are three different kinds of overshoot, none a recovery
  result; the settlement-lag kernel is a documented timing null but *retained* —
  removing it would not reproduce the numbers.

### §V The Hazard Framework (lines 172–513)

The paper's centre of mass: installs the headline estimator, then spends most of its
length pricing everything that could make the headline wrong.

**§V.A–C — Motivation, Path B, Fannie replication (172–292).** Drops the household utility function;
models loan-level survival, proportional above the baseline turnover floor. Core
hypothesis: the binding constraints on prepayment lie at least partly *outside* the
household decision function. Path B: stratified 75,000-loan Freddie draw (40,234
window-start survivors), 100 PSA seasoning ramp, floor = SMM-equivalent of 4% annual
CPR broadcast flat (acyclical, flat in age — flagged, deliberately not swept: the
age-rising pattern is carried by the refi-contaminated 2019 leg), imported
elasticity β₁ = 0.0686 (Liebersohn–Rothstein 5.5–7.7% band, 6.5% midpoint adopted ex
ante, converted via eq:beta1; P_q = 0.06 is a conversion auxiliary the transform is
insensitive to). Central run $818.5B = 107.0% standalone. **Two** named transport
assumptions travel with the import — aggregation/response homogeneity (named, not
priced; the source estimand is a ZIP-code-level moving hazard) and survival selection
(signed toward attenuation, priced by the ξ-bracket) — plus a **separate mapping**
assumption, moving-vs-refi scope (signed to shrink, priced by the μ-bracket, which
alone spans +$19.2B to +$70.3B in-sample). Full provenance chain in 2.2; the paper
names two transport assumptions, not three, so do not collapse them.
Composition bounds: Ginnie $20–47B; vintage $11.7B; coupon-reweight +0.2 pp
single-convention. The floor binds in 36% of the 1.68M evaluated loan-months — that
is the **central** leg at the **in-sample 4.0%** floor (36.27%); see 2.1's trap.

- Fannie external replication (24 quarters, 17.6M loans, 826M loan-months, spec
  frozen before the run): marginal +8.68 vs Freddie +9.20 — the pre-committed
  envelope pass is explicitly *not* evidence (an 11.06-pt gate "fails only on a sign
  error"); the 0.52-pt closeness certifies pipeline determinism, not external
  validity.
- Traps: 88.7% doubles as the 6.0%-floor-row bind share (numeric coincidence);
  296 cells vs 295 fixed effects (dropped reference); the lag-direction printing was
  corrected in-text (peak at k = −3 means the simulated path *trails* SOMA cash);
  the additive-form marginal +11.25 is *not* stronger lock-in evidence (censoring
  artifact); Fonseca's +$87.9B lands above the band's high edge yet inside the box —
  "conservative" describes the adopted central, not the outside anchors.

**§V.D–F — Path A, Identification, Interpretation (293–513).** Path A: excluded
corroboration (112.4% shared / 121.5% standalone); its H₀: β_g ≤ 0 test does not
reject under any bias-respecting scheme (p = 0.093–0.412). The estimand is
eq:marginal — the difference of two runs — and §V.E's **seven numbered
qualifications** are the paper's epistemic core: (1) the identified content is the
range, not point or sign; (2) timing carries no credential (the null peaks at the
same lag); (3) sampling precision is not the operative uncertainty; (4) the
"broad-based" label is placebo-earned — only the >30× dispersion comparison
survives, and its content is *distributional incidence* (weaker-credit,
higher-leverage borrowers bear mildly more); (5) "identifies" = within-model
counterfactual, no quasi-experimental variation anywhere; (6) three declined
readings, none pointing to a smaller channel; (7) the assembled-corrections ledger
(tab:assembly) settles where in the interval the mass sits, not whether the finding
holds — corrections do not compose additively (the paper's first joint cell
returned a −1.47-pt interaction; the second, b5_joint_cell, measures +2.9 within
0.1 of proportional under a pre-committed landing rule — note tab:assembly's "the
one joint cell run" status text is stale against the body), and the two floor
transports (+4.70 calendar-standardizing vs +10.69 activity-matched) deliberately
stay un-netted.

- **The inference ladder** (tab:ladder): binding = restricted wild-cluster inversion
  [+1.9, +9.1], selected by a pre-committed coverage rule (94.3%/95.1% measured) —
  with the disclosed caveat that the rule was applied *after* seeing which way it
  fell. Webb [+2.8, +8.7] demoted from binding, stands beside; CR2 Bell–McCaffrey
  [+2.4, +9.1] qualifies; percentile [+3.0, +8.0] under-covers (and silently
  excluded 26/1000 off-grid draws — truncation would print [+2.28, +8.01]).
- The PSA seasoning-ramp sweep is the widest within-form convention layer; aggregate
  fit cannot arbitrate it (the two legs rank ramps opposite ways). Two pre-committed
  predictions in this range **failed** and are reported as failures: the h₀
  re-anchor rose instead of falling (median +9.44), and the additive form moved the
  implied gradient the "wrong" way.
- The realized cross-sectional gap gradient is the only realized-data exhibit moving
  in the lock-in direction — and is *declined* as a size measurement (≈4.5× the
  imported implication; its age-augmented interval now covers the implied +0.94,
  flipping its own pre-committed branch).
- Traps: the floor-percentage family (4.695 / 4.869 / 4.991 / 5.185 / 5.2156 / 5.33
  / 5.51 / 5.52) — each is a different read; tab:assembly's two +3.7 rows are a
  rounding accident (3.67 vs 3.70); the +3.8-vs-+3.7 age-standardized wedge is a
  deliberate grid-consistency choice; β₁ prints positive in tab:lowband but the
  production helper returns it negated (marginal columns unaffected); 107.0%
  standalone is simultaneously an 8.2% under-prediction of realized runoff — the
  referent flips, the map doesn't; the 68.8% pinned-loan-month share is unweighted
  counts, not "the estimate rests on a third of the data"; the Danish +$61.2B
  compares to the in-sample $70.3B, **not** the $42.6B headline; 15-year face is in
  the benchmark and the ABM but *not* the hazard rows — cross-estimator dollar
  comparisons inherit that asymmetry.

### §VI Discussion (lines 514–621)

Turns the accounting result into consequences: systemic channels, cap design, and
the Danish counterfactual.

- **Two systemic channels, one measured.** (1) Duration extension deprives SOMA of
  scheduled cash flow, breaking the predictability QT requires — but the shortfall
  against the caps is mostly rate-inelastic; **the duration extension itself is the
  rate-driven object**, and it, not the cap arithmetic, feeds (2) the bank
  mark-to-market fragility channel — which is context only (per the cited Jiang et
  al., extension alone did not precipitate failures; it interacted with uninsured
  deposits). Back-of-envelope: the trapped roll-off carries on the order of **$1B
  per year** of negative carry (funding spread ~250–300 bp over the book's coupon).
- **WAL table (tab:wal).** Empirical-path WAL 9.4yr at the window's open, 8.5 at its
  close; a **6.0-year extension** against the no-shock 2021 refi-boom comparator
  (3.4yr) — but nearly vanishing (9.4 vs 9.5; 8.5 vs 8.6) against the floor's
  off-window read (look-alike pair 16). Deliberately not restated on the note-rate
  basis; single-pool-per-cell approximation; OAD/convexity declined as out of scope.
- **Cap design.** The phased ceilings averaged $33.75B/month against projections of
  $17.6–20.0B — ratios 1.91 and 1.69, the "1.7–1.9×" seen monthly. Both components
  of the rate-inelastic path were computable ex ante. The state-contingent
  (indexed) cap is priced and **worth little**: the observable (share of book face
  below market, 99.9/99.6%) is near-degenerate. Two design levers (substitution
  instrument; indexed cap) are design space, not recommendations — active sales
  would realize the mark-to-market losses passive runoff defers. Whether a cap
  should bind at all is left contested.
- **The transfer list** (what travels to a future runoff designer): the baseline
  turnover floor in CPR units, the scheduled-amortization path, and the elasticity
  band as a behavioral budget. Two numbers must **not** travel alone: +5.6 ("a
  convention inside a range rather than a central tendency") and $764.7B ("a
  statement about a never-binding schedule's composition rather than a missed
  objective").
- **Household side.** Implied foregone payoffs: ~179,500 on the book over 42 months
  (51,300/yr; 233,000–256,000/yr grossed to the whole market, 5.7–6.3% of the 4.08M
  annual existing-home-sale run rate) — implied counts, upper bounds at μ = 1, and
  the divisor choice (surviving-loan balance) roughly halves what an all-loan mean
  would give. Assumability: the 20.4% Ginnie share is a **ceiling** on the
  carve-out, take-up measured nowhere; the practical limiter is that the buyer must
  finance the price-minus-assumed-balance gap at prevailing rates.
- **The Danish counterfactual** (§VI.D + tab:danish). The anchor, not the
  refinance-in-place channel, decides the sign (look-alike pair: U.S.-intercept
  +$61.2B vs Danish-level −$99.9B, the latter demoted to a bracket because its legs
  run at 3.39–3.40% mean CPR, below the 4% floor the U.S. side imposes). Berger et
  al.'s "negligible" refinance-in-place is a *price* statement (~20 bp), not a
  volume one — realized Danish deep-discount redemptions ran 26.4%/yr, so the
  rule-only gap is a **band**, not a point at zero. Three disclosed reversals of the
  +$61.2B: cash-haircut accounting (−$51.0B; the wedge is a transfer — face answers
  the benchmark question, cash the reserve-drain question); a Danish interest-only
  share above 34.3% (Denmark's own read is 45%, giving −$19.2B; the 30.8% crossing
  is the first-order version); and the bracketing anchor. The upper half of the
  refinance-in-place sweep (the eye-catching ~$1,039B ceiling) is explicitly not a
  quantitative statement — the Danish trapped balance goes negative there. And the
  self-demotion that keeps this section honest: **the rule-only gap is the lock-in
  marginal viewed from the counterfactual side** — it re-denominates an
  already-conditioned quantity and supplies no independent information about the
  payoff rule. The paper's closing verdict: the mobility relief such a rule would
  provide "remains the better-supported and larger effect."
- Traps: +$61.2B is at the **in-sample** floor (compare $70.3B; the off-window
  counterpart is +$28.2B); $0.42–1.66B per *month* (marginal in foregone principal)
  vs ~$1B per *year* (negative carry); tab:danish's rows b and c share a U.S.-leg
  label with different values ($84.5B ABM-basis vs $749.0B hybrid) — row b is
  deliberately not the $91.0B headline because both legs must share one calibration
  freeze; berger2026's refinance-in-place estimate moved ~20× between its January
  and July 2026 drafts — the stated reason it travels as an unrefereed import.

### §VII Robustness Checks (lines 622–728)

The self-audit. It opens by naming the only two checks that changed reported
results: the **cross-design test** (which forced the paradigm withdrawal) and the
**off-window floor re-measurement** (where the headline marginal is actually
derived). Everything else is invariance.

- **Scale sensitivity (§VII.A) — and the ABM spec fork.** Population size does not
  drive the ABM–hazard gap (pre-committed rerun on the full production behavioral
  spec). The one dimension the rerun does not carry is the 15-year fold-in: the
  rerun evaluates the 15-year book on the **native behavioral gate** (12.66% at
  N=10,000; 12.18% at N=75,000), production **folds it in on structural terms only**
  (13.56% fifty-seed mean). The 0.90 points between 12.66 and 13.56 are a
  *documented level offset the run was specified to expose* — not an error, and not
  a population-size effect. Do not "fix" it. (Repo side: see Section 10.)
- **Benchmark sensitivity (§VII.B).** Net accumulation defended (comparability with
  the Danish legs); settlement-alignment variants move the benchmark to $722.7B /
  $739.4B but re-basing moves **no dollar quantity** — every percentage scales by a
  common 1.058. The "cash-arrival object" worry about the monthly series is stated
  as a candidate account, not a finding.
- **Cross-design test (§VII.C) — the withdrawal.** Ex-ante thresholds: >50%
  recovery undercuts the paradigm reading, <35% corroborates. Recalibrated variant:
  59.3% committed draw, 60.2% fifty-seed, **76.3%** after pre-committed
  post-stratification to SOMA composition (which *widened* the calibration spread —
  frozen leg fell 20.9% → 12.6%; the raw spread $294B grew to $488B). The frozen
  ("corroborating-looking") leg is the *less admissible* one — it misses the
  observed turnover moment on all fifty seeds. **The paradigm reading is withdrawn**;
  narrowing after the fact what the threshold was allowed to mean is exactly the
  move pre-commitment exists to prevent. A third, no-floor externally anchored
  variant lands at 150.6% (classified undercutting; the author's discount of it is
  labeled post-hoc); the simulated-minimum-distance two-moment fit returns joint
  infeasibility (nearest admissible fit 107.1%). Firewall: no hazard-side headline
  can move under any of this. What survives: the path-level failure (every
  estimator, both variants) — though the text only says the dollar-recovery
  critique "does not straightforwardly survive," a load-bearing hedge.
- **Symmetric companion (§VII.D).** Path B run on a fully synthetic population
  recovers essentially its real-data level (~106%) — read on the *differential*,
  since levels are floor-dominated everywhere. The previously reported 18.3-point
  cross-basis gap was an error of basis (standalone central vs shared null); the
  single-basis gap is 9.2 in-sample / 5.6 off-window. Aggregate contrast
  corroborated *on the differential*; "nothing here is offered in support of" the
  withdrawn paradigm reading.
- **Cross-foundation checks (§VII.E).** The hybrid pipeline (one accounting layer,
  swapped micro-foundation) makes accounting differences unable to explain the
  estimator gap. Curtailment: ±25% stress moves every U.S. leg uniformly and the
  marginal not at all (bit-identical netting) — but the **Danish curtailment
  differential's immateriality is withdrawn**: re-scored on the production cache it
  reverses sign (+$0.77B → −$1.68B) and crosses materiality. Full-book joint run
  reads 100.0% — the committed *mixed-basis* reading; like-for-like is 98.1%.
- **Calibration box and the form question (§VII.F).** The box sweeps the floor's
  *level*; the floor's *form* is the first-order choice it never sweeps
  (85.7%↔35.6% on the null; +5.6↔+11.2 on the marginal). The mixture curve in ω is
  the transportable device: it rises steeply and plateaus (+7.5 at ω=0.1, +9.7 at
  ω=0.25), so a modest strictly-involuntary share does **not** pull toward the max
  form. Form × transform do not compose (−1.47-pt interaction at the headline
  anchor); the form-conditional hull widened at the bottom (+3.89 → **+3.5**, upper
  edge +13.1 unchanged) — and the hull may only be quoted beside the binding
  interval. Own-data evidence (2018 ladder step-then-plateau) is *consistent with*
  the max form — a shape comparison on one leg, not a test, with its deepest bins
  flagged as not well supported. The separate near-coincidence-of-forms defense at
  the deep-discount anchor carries its own disclosed concession: it does not reach
  the shallow-gap off-window anchors where the headline is taken.
- **The off-window re-anchor (also §VII.F).** Where the headline is derived. The
  demotion +9.2 → +5.6 decomposes 73.7% window / 26.3% depth (Section 4, "depth");
  the 2018 leg's mature-seasoning test is **uncomputable, not passed** (all reads
  sit on ages 12–24), and every measurable mature-vs-young contrast signs the band
  low — the clean band's lower edge is soft, and the age-standardized 5.51% bound
  (84% imputed weight) is indicative, one-signed. Extending the depth ladder 3 → 5
  leaves the band exactly unchanged. The 2019-leg rejection stands but its original
  argument does not (matched-depth comparison is non-monotone; the honest verdict
  is "unadjudicable below gap ≤ 0", with the seasoning diagnostic carrying the
  rejection). The floor-stability split (19 calibration / 23 evaluation months)
  reproduces the marginal (+$45.1B vs +$44.8B) — weak evidence by design, being an
  input-stability check. One **open definitional alternative** is named and not
  priced: if the floor's level is itself an equilibrium outcome of the episode,
  part of what the null absorbs belongs to the lock-in channel — the rate-inelastic
  share would overstate what is invariant to household behavior.

### §VIII Conclusion and Limitations (lines 729–765)

What the paper claims, and — at unusual length — what it does not.

- Restated core: the cap shortfall was the structural design of the U.S. mortgage
  contract meeting caps set above any plausible prepayment path; the null alone
  clears most of the benchmark; the ABM (rational, behavioral, or burnout-tested)
  cannot explain the majority; **on the modeling-paradigm question the paper makes
  no claim** (withdrawn; the decomposition never rested on it). The ABM's status:
  "a stress-test companion" standing beside the central finding.
- The trilemma reading self-undercuts, deliberately: "(2) mobility and (3) duration
  profiles do not trade off sharply" reduces to "the marginal is small," which is
  **bounded small by construction under the production max form** — a
  form-conditional statement, inheriting the marginal's floor-and-band
  conditionality. The binding constraint against adopting a market-value rule is
  the TBA liquidity premium — an argument from cited literature; nothing here
  prices a series-level call. Recurrence in future tightening cycles is flagged as
  an extrapolation beyond the one-episode design.
- Distributional: the marginal's per-balance intensity tilts toward weaker-credit,
  higher-leverage borrowers (the placebo-surviving incidence result); who bears the
  mobility cost across FHA/VA vs conventional is *unanswerable here* (Ginnie
  borrowers sit outside the Freddie sample).
- **Limitations block** (§VIII.A), the paper's own list: housing supply enters only
  as a friction scaler (a household that doesn't move because nothing is listed is
  observationally identical to a locked-in one); size settled, data source not;
  15-year face excluded on the hazard side only (by design — cross-estimator
  dollar comparisons inherit it); ABM path fit weak; Path A needs a ridge and has
  no forward precision; Path B is literature-calibrated, recovery reported as a
  band; the Fannie replication is sign-and-envelope, with the 0.52-pt agreement
  (not the 11.06-pt gate) the informative part; **no outcome-holdout months**; the
  floor is calibrated in-window (every recovery percentage is in-sample or
  calibrated); no causal identification; the Danish source is unrefereed and moving.
  Three open questions: a seasonal multiplier for Path B's baseline; a total-debt
  DTI variant for the ABM; the monthly-frequency question (the empirical path's
  monthly variation is seasonal, not rate-driven).
- Traps: "8.7 points" (the level miss at the headline floor) vs "+8.68" (the Fannie
  marginal) — unrelated; "about +11" (Danish under the additive form) vs "+11.2"
  (the marginal under the additive form); two different "nineteen"s (floor-holdout
  calibration months vs Path A's 19-of-42 training span); 23–49% and 38–80% are the
  same expectations-share quantity at the two floors — "roughly half" is the verbal
  gloss over both.

### Online Appendices A–M (lines 766–1411)

What each appendix is *for* (the main text points here constantly). Printed table
numbers: tab:abmparams = Table 13, tab:hazard-notation = Table 14, tab:terminology
= Table 15, tab:delinq = 16, tab:params = 17, tab:pathadiag = 18, tab:panel = 20,
tab:bootstrap = 21, tab:seasonalfloor = 25.

| Appendix | Job | What to know before touching it |
|---|---|---|
| **A — ABM spec** | Makes the ABM reimplementable: 10,000 households, endowments log-normal to FRED medians, coupons from the live CUSIP-level SOMA parse (7 cohorts). | The single 3.0%/60-month cohort is expository, not production. The CPR surface is precomputed and interpolated (~100× cost cut; exact at nodes). Danish pricing is an option-free PV at the capped primary rate — both pricing choices overstate the borrower's buyback discount, immaterial to the production finding. "Convexity-neutral" = rate-rise sense only. |
| **B — Macro frictions** | Builds the dynamic friction from two FRED series (listing shortfall; UMCSENT at +5 bp/point, capped +150 bp). | Provenance is deliberately uneven: DTI 43% is a repurposed regulatory heuristic, loss aversion 2.25 external, the wait-and-see freeze an author calibration with no external source. Nothing is tuned to the benchmark. |
| **C — Decision rule** | The move rule as three conjunctive, side-effect-free gates (DTI veto, cost-benefit, freeze) pinned to committed code; Table 13 gives every parameter with provenance. | θ (mobility-desire scale) is the ONE re-derived parameter; the floor-recalibration is the named artifact behind the 54.9% stage. The mobility-desire distribution is **exponential on a dollar scale** — the "log-normal" description was a corrected error of description. |
| **D — Path B parameterization** | All parameters fixed a priori; delinquency matrix published but disclaimed (describes the panel, doesn't estimate a law); sampling design + attrition (75,000 → 40,234 active; 1,683,124 loan-months); Tables 14/15 are the paper's own notation and terminology disambiguators. | Benchmark-independence is not window-independence (the 4% floor is in-window). The two credit covariates carry signs opposite the canonical direction, defended for a turnover-dominated window. The committed within-stratum bootstrap understates loan-sampling uncertainty ~37× (30.8× in-window) — the retraction lives in the verdict appendix. Burnout is cohort-level, β_B = −0.5, window-cumulative. The >1 rescaling is a safety clamp that never binds, not a competing-risks construction. |
| **E — Path A estimation** | Stratum-month Poisson PML, 295 FE, seasoning spline; the spec v3/v4 fork (v4 = production, eleven calendar dummies, 121.5%; v3 carries every inferential object because v4 bootstrap replications are branch-unstable). | Propagated coefficient uncertainty leaves the forward simulation with *no useful precision* — the committed interval spans zero by thousands of billions. That is the stated reason for the headline exclusion. Calendar seasonality improves timing (p = 0.031), not level. |
| **F — Panel, uncertainty, ridge** | Verifies the ridge device (numerical no-op; warm-start convention; production point survives dropping inestimable strata); Table 20 (fitted on the full universe, not the 75k sample), Table 21 (both bootstrap schemes). | The ridge-selection holdout later serves as the out-of-sample diagnostic, so the reported RMSE is weakly selection-favored — a carried caveat. |
| **G — Theil / dynamic fit** | Localizes each estimator's monthly error (ABM = level bias; Path B = under-dispersion; Path A intermediate); no estimator beats a naive no-change forecast (U₂ > 1). | Two known text-vs-table wobbles on Path A's Theil shares (26.5/63.0 prose vs 30.6/58.8 table; U₁ 0.431 vs 0.438) — flagged by review, unresolved; don't silently reconcile. |
| **H — Composition shift** | Quantifies Freddie-sample vs SOMA-book covariate shift (PSI); every shift carries a committed signed bound; missing dimensions covered by a Freddie–Fannie stability check. | — |
| **I — Floor-sweep mechanics** | Where the floor machinery lives: the **failed** ±2pp stability rule (moved +10.8 → +5.5; reinterpreted as max-form censoring mechanics), the pooled off-window read's rejection, the 2018-leg operative anchor, the depth ladder, and the twelve-rung inference ladder (tab:ladder). | Ladder wrinkles: the artifact's `landing_branch` string records L1 ("Webb retains"), contradicting the frozen rule — the tablenote is the adjudication; three wide rungs' lower endpoints WERE censored at the grid's former 6.0% edge; the FP2-B1 extension decensored them (+2.0/+1.9/+2.2, each below the +2.3 that edge printed); CR1 = CR3 at one decimal is a leverage accident. |
| **J — Behavioral extension mechanics** | Each ABM extension moves the wrong way or for the wrong reason: loss aversion = recalibration artifact; curtailment's drop was predicted ex ante; the multi-vintage drop *inverts* the stated hypothesis and is left undiagnosed. | The DTI sweep is non-monotone with 43% at its minimum — looks like cherry-picking, but the decomposition shows the pattern doesn't survive holding θ fixed. |
| **K — WAL quantification** | The duration mechanism in maturity units; documents tab:wal (printed in §VI). | The Berger-recalibrated Danish CPR surface is near-flat (~quarter point across the grid) — the moving-flatness underneath the WAL rate-invariance claim. |
| **L — 15-year fold-in + units fix** | Why the fold-in is structural-only (the fully native treatment produced out-of-bounds values), and the rate-gap **units correction**: applied to a decimal gap the imported coefficient was numerically inert; production applies it per 100 bp. Disabling either change exactly reproduces the superseded figures. | This is the appendix behind both the spec fork (§VII.A) and superseded figure #7. |
| **M — Seasonal floor** | The dispersion result: a calendar-profiled floor moves the marginal, but the permutation family retains on average 89.2% of the shape effect under scrambled calendar order (69.9–102.8% across draws) — a Jensen effect of the hard maximum, **not seasonality**. (The 85%-survives / 98%-removed-by-additive figures belong to the separate cyclical κ grid, which indexes the floor to the rate path.) Flat-floor convenience bounded at ≤ $4.897B of the in-sample marginal. | Four caveats travel with the seasonal floor (circular identification; no off-window shape rescue; R² 0.011-vs-0.755 instability; peak-month tension). The frozen timing rule is *met* and claims nothing — the null clears it more strongly. Level and shape do not separate; no additive split exists. |

### Replication appendices (`replication_appendices.tex`)

The audit trail, two sections:

- **L1 — Superseded figures + run ledger.** Replication is **code-only** for
  loan-grain data (Freddie terms; Fannie prohibits redistribution). The
  superseded-figures catalogue lists ten retired headline numbers with the
  specification error behind each — the fastest way to recognize a stale figure
  quoted from an old draft (e.g. $101.2B/13.2% pre-fold-in ABM; $925.5B Danish;
  $915.0B Path A spec v3; the 18.3-pt basis error; "within 2.1%" unqualified;
  "log-normal" mobility desire). `tab:crosswalk` maps each live headline to basis,
  exhibit, and source run; `tab:runindex` (~90 rows, 89 unique tags —
  `bootstrap_pathb_cluster` appears twice, once per floor) indexes every cited run.
  Two disclosed permanences: **two freezes ran on uncommitted trees**, so the ABM
  headline is not commit-addressable (identify specs by manifest and content, not
  git commit); and spec-before-run is only *partly checkable* from the document (25
  standalone specs in `specs/`; the rest rest on script headers).
- **L2 — Verdict appendix (`tab:verdicts`).** Every pre-committed rule with its
  post-run adjudication — the paper's own "read the credential net of this" device.
  The gate suite "is not self-certifying": it checks printed literals against
  committed artifacts and span presence/order, **no premise**. Highlights a reader
  should know exist: the floor-stability rule FAILED and was reinterpreted (for the
  headline); the 27-cell positivity PASSED and was withheld (against the paper's
  own pass); the Fannie envelope PASSED and was withheld; the percentile interval
  was superseded by the pre-committed coverage rule; the in-window floor was
  demoted (the +9.2 → +5.6 event); the pooled-read disqualification was itself
  re-adjudicated as weaker (conclusion retained); the within-stratum CI was
  retracted (37×); the κ grid was re-labeled dispersion; the timing rule was
  withheld to levels; the cross-design threshold was enforced (the withdrawal);
  the ABM-null probe is stamped `pre_committed: false`; a FRED revision halted one
  parity tier (tolerance kept, re-run — not a failed test); the Danish redemption
  validation forced the gap to a band. Trap: "108 green gates" appears as evidence
  **against** relying on gate counts (they coexisted with ~919 off-sheet items).

---

## 7. Result status ledger

The paper's claims sorted by epistemic status — the current text's own framing.
Quote claims only at the status listed here.

**Measured constructions** (data + committed rules, no estimation): the $764.7B
benchmark; the $87.8B expectations complement (allocation-conditional); the
1.7–1.9× cap multiple; the floor reads (each labeled by window/depth/method).

**Identified (within-model; the paper's own "identifies")**: the lock-in marginal
as a **bounded range**, stated separately by form; the binding interval
[+1.9, +9.1]; the marginal's basis-invariance; the window/depth demotion
decomposition; the distributional-incidence tilt (the one placebo-surviving
composition result); the cross-design threshold crossing as a fact about the test.

**Anchor conventions (reported, refused as central)**: +5.6 pp / $42.6B (mid-grid
anchor); +9.2 pp / $70.3B (in-sample calibration point).

**Bounded / bracketed**: Ginnie composition ($20–47B, signed conservative); vintage
bound ($11.7B, signed conservative); μ-bracket and ξ-bracket (transport conventions
on the imported coefficient) and the ω mixture curve (a floor-form device, measured
not estimated); the Danish rule-only gap as a band
over refinance-in-place; flat-floor convenience ≤ $4.897B; household counts (upper
bounds at μ = 1).

**Consistency checks (wiring, not evidence — the paper says so each time)**: the
27-cell positivity (sign is forced); the sign agreement between Path A and Path B
(the imported band cannot disagree); the Danish sweep's uniform positivity (anchor-
forced); the Fannie envelope pass (gate too wide; the 0.52-pt closeness is the
content); the temporal floor-stability agreement (+$45.1B — input-stability only);
the φ=1 / parity-gate reproductions.

**Qualified external imports**: the elasticity band (Liebersohn–Rothstein
specification range; no sampling error propagated); berger2026 (unrefereed, moving
~20× between drafts); graybill2026 (corroborates from at-or-above the band);
fonseca (from above); Aladangady's 44% (as a calibration target); batzer2024's
$2.4T (stock, universal relocation, not additive with the counts).

**Conceded / disclosed and left open**: no outcome holdouts anywhere; the floor is
in-window (Path B's level is set by a floor measured on the window it is evaluated
on); the 2018 leg's mature-seasoning test is uncomputable (signed against the
headline, priced nowhere); the endogenous-floor definitional alternative; three
unbounded residual mechanisms (servicer behavior, updated equity, equity
extraction), each plausibly rate-cycle-correlated; monthly timing (all estimators);
the composition question of whether ABM–hazard is paradigm or data source.

**Excluded by pre-commitment**: Path A from every headline (112.4% shared / 121.5%
standalone; sign not distinguishable from zero; no forward precision).

**WITHDRAWN — never quote as live** (each replaced by a stated weaker form):
1. **The paradigm reading** (§VII.C withdraws; §IV lead + conclusion point at it).
   Weaker surviving form: the contrast "cannot be cleanly attributed" to paradigm
   vs calibration/data source.
2. **The 88.5% ≈ 88.7% projection–null convergence** (§III). Surviving form: both
   put the anticipated rate-inelastic component in the large majority.
3. **Timing as evidence**, everywhere (the null reproduces the lag; the peak was
   selected over seven lags; four clip-zeros corrupt the differenced signal).
4. **"Recovers 97.9%, within 2.1% of the benchmark" as an unqualified headline**
   (mixed floors). Both numbers retained, floor-labeled.
5. **The 18.3-point central-minus-null gap** (basis error; correct: 9.2 / 5.6).
6. **The curtailment-differential immateriality** on the Danish leg (sign is
   cache-dependent: +$0.77B vs −$1.68B, crosses materiality).
7. **The Danish-level anchor as production** (−$99.9B; demoted to bracket).
8. **The mechanism-extrapolated Danish gap** ($925.5B; superseded, order of
   magnitude).
9. **The within-stratum bootstrap CI [+9.17, +9.23]** (retracted; ~37×
   understatement).
10. **Webb [+2.9, +8.7] as the binding layer** (demoted beside the restricted
    inversion by the pre-committed coverage rule).
11. **The "broad-based" homogeneity label** (placebo-earned; only the >30×
    dispersion comparison survives).
12. **Floor cyclicality readings of the κ grid / seasonal floor** (re-labeled
    dispersion; co-movement real but ≤ $5.29B).
13. **The 2019-leg rejection's original argument** (rejection retained on the
    seasoning diagnostic; matched-depth comparison unadjudicable).
14. **"Log-normal" mobility desire** (exponential; description error).
15. **The Danish discount-rate immunity reading** (the zeros bound the hazard
    channel only; the accounting credits ~$470B at par).

**Failed pre-committed predictions, reported as failures** (the paper's credibility
device — these run against the author's prior): the ±2pp floor-stability rule; the
h₀ re-anchor direction (marginal rose to median +9.44); the additive-form gradient
direction; the covariate compression band (realized 1.17 vs [0.45, 0.60]); the
coupon-conversion projection (98.1% vs 98.7 projected); the month-rung censoring
prediction; the multi-vintage direction (inversion undiagnosed).

## 8. Numbers that look alike — disambiguation tables

### 8.1 The two floor calibrations, side by side

The paper's own rule: never a level from one floor beside a marginal from another.
This table is how to obey it cheaply. (All recoveries shared basis, production form.)

| | **In-sample calibration point** (4.0% floor, in-window 2023–24) | **Off-window floor** (4.99% mid-grid read of 4.70–5.33%, 2018 cohorts) |
|---|---|---|
| Lock-in marginal | **+9.2 pp = $70.3B** | **+5.6 pp = $42.6B** (the headline anchor) |
| Path B central recovery | 97.9% (107.0% standalone) | 91.3% (100.4% standalone) |
| β₁ = 0 null recovery | 88.7% (97.8% standalone) | 85.7% (94.8% standalone) |
| Floor-bind share (central / null) | 36.3% / 14.3% | 68.8% / 35.8% |
| What the marginal bounds | total rate-attributable suppression from **above** | from **below** |
| Danish rule-only gap | +$61.2B | +$28.2B |
| μ = 0.5 bracket reading | +$37.7B (+4.9) | +$25.7B (+3.36) |

### 8.2 The interval taxonomy — sampling layers vs grids

Only the first block prices sampling error. Never let a grid and a confidence
region share a bracket.

| Interval (pp) | What it is | Status |
|---|---|---|
| **[+1.9, +9.1]** | Floor read's own sampling error at central δ: restricted wild-cluster inversion, 31 clusters, measured coverage 94.3%/95.1% | **BINDING** (pre-committed coverage rule; note: applied after seeing which way it fell) |
| [+2.4, +9.1] | CR2 Bell–McCaffrey rung | qualifies, stands beside |
| [+2.8, +8.7] | Webb wild-t rung | demoted beside (coverage 90.8%/91.4% vs the bar) — not "superseded history", still printed |
| [+3.0, +8.0] | Percentile read of the same layer | demoted: under-covers; excluded 26/1000 off-grid draws (truncating gives [+2.28, +8.01]) |
| [+4.63, +6.92] | Loan/stratum cluster bootstrap (a *different* layer; 25.8 effective clusters) | lower bound on sampling uncertainty |
| [+2.80, +8.99] | The two layers convolved as independent | itself a lower bound |
| [+9.17, +9.23] / [+8.27, +10.19] | In-sample point's within-stratum / stratum-cluster intervals (around +9.2, not +5.6) | first is RETRACTED (30.8× understatement in-window; the ~37× figure is the off-window measurement); second is the operative scheme |
| — grids below: **no coverage property** — | | |
| [+4.3, +6.8] | Defensible off-window floor range (max form) | calibration range |
| [+3.9, +7.5] | Same, jointly with the elasticity band | calibration range |
| [+2.1, +13.2] | The calibration box (7 floors × 3 elasticities; a separate 27-cell joint sweep also exists) | convention grid |
| [+3.5, +13.1] | Form-conditional hull (widened at bottom from +3.89) | two-form envelope; quote only beside the binding interval |
| [+3.3, +16.5] | PSA level sweep | widest within-form convention layer |
| [+0.9, +15.6] | Convention envelope across named variants | no coverage; the scaled null's +0.9 sits outside the binding interval |

### 8.3 Four unit systems that all print as small numbers

| Unit | Means | Examples |
|---|---|---|
| **pp / "points"** | percentage points **of the $764.7B benchmark** (~$7.65B per point) | +5.6 pp, [+1.9, +9.1] |
| **%** | a recovery level or a share of a book/pool | 91.3%, 20.4% Ginnie, 43% DTI |
| **bp** | basis points of interest rate | 100 bp gap unit, 150 bp freeze trigger |
| **points of CPR** | floor-read errors and floor levels | floor SE 0.39–0.46, the 4.99% floor |

"Basis" (accounting) has nothing to do with basis points.

### 8.4 Exact numeric collisions — guard-sentence list

These are identical digits on unrelated objects. Any sentence using one should say
which.

- **5.52%** — hazard-basis empirical CPR mean *and* the Fannie off-window floor read.
- **61.2** — $61.2B Danish rule-only gap *and* 61.2% recovery at the hull's upper
  corner (additive form, 4.695% floor, 7.7% edge — a cell the paper de-credentials).
- **9.1** — binding interval's upper edge (pp) *and* the flat curtailment netting
  (pp) *and* the 15-year sleeve's share of SOMA face (%).
- **45.1** — +$45.1B held-out floor-stability marginal *and* 45.1% ABM
  curtailment-stage recovery.
- **88.7%** — the null's in-sample shared recovery *and* the 6.0%-floor-row bind
  share in tab:floorband.
- **+2.3** — the binding interval's FORMER grid-censored lower edge (now +1.9) *and* the marginal implied by the
  *disqualified* pooled 6.07% floor read (opposite rhetorical roles).
- **59.3%** — cross-design recalibrated recovery *and* the SMD parity-gate replay
  (59.303%) *and* the additive central leg's recovery at the 4.695% anchor.
- **97.8% vs 97.9%** — null standalone in-sample vs central shared in-sample: one
  tenth apart, different leg *and* different basis.
- **9.2 vs 9.1** — see Section 5, pair 20.
- **8%** — the Danish gap as share of benchmark *and* the ABM floor-calibration
  market rate.
- **42** — window months, the frozen engine seed, and the 42-loan-month gap between
  the U.S. (1,683,124) and Danish (1,683,082) panels.
- **+3.7** — the age-standardized floor's directly measured marginal *and* the
  vintage overlay's (3.67 vs 3.70; a printed rounding accident).

### 8.5 Confusable clusters (each line is one family; members are NOT interchangeable)

- **ABM dollars**: $103.7B (fifty-seed mean, the headline) / $91.0B (frozen seed-42
  draw) / $96.9–110.5B (CI of the mean — simulation noise only) / $24.5B (seed SD)
  / $84.5B (frozen Danish-anchor accounting used by freeze/DTI sweeps) / $544.0B
  (rational baseline) / $453.5B vs $159.5B (cross-design recalibrated vs frozen).
- **ABM shares**: the specification ladder 71.1 → 54.9 → 45.1 → 33.7 → 13.2 → 11.9
  (fold-in draw) → 11.1 (native gate); the seed summaries 13.6/13.56 mean, 10–17
  band; the scale test 12.66 vs 12.18 (native gate, two population sizes). 12.66
  vs 13.56 = the fold-in/native offset, never a size effect.
- **Marginal dollars**: $70.3B (in-sample) / $63.5B (matched-depth in-sample
  comparison point — narrate the demotion against this) / $42.6B (headline) /
  $32.6–51.8B (floor range; $33.31–51.75B is the same band off the PCHIP grid, the
  $0.69B wedge is a grid-read artifact) / $45.1B–$44.8B (held-out months only) /
  $37.7B, $25.7B, $19.2B, $13.9B (μ-bracket conventions).
- **Recoveries above 100%**: 107.0% (Path B standalone in-sample) / 107.1% (SMD
  near-fit at joint infeasibility) / 107.4% (Fannie replication central) / 105.7%
  (concave-gap variant) / 112.4% = 121.5% − 9.1 (Path A shared = standalone minus
  netting — one estimator, one run, two bases) / 150.6% (no-floor external variant)
  / 147% (burnout) / +116.3% (ABM null probe). None is evidence for anything.
- **Benchmark-family dollars**: $764.7B (cap-relative; $764.748B unrounded) /
  $740.6B (Fed's projected runoff) / $652.8B (realized) / $87.8B (their difference)
  / $722.7B, $739.4B (settlement-aligned variants) / $765.1B (Path B composed-basis
  reading, 100.04% — nothing to do with the benchmark) / $69.56B (curtailment
  netting) / $1,217.6B (zero-voluntary-prepayment censoring artifact, not an
  estimate).
- **Floor levels (annual CPR)**: 4% (in-sample) / 3.97–3.972% (stability-check and
  gap≤−2 variants) / 3.8–3.9% (in-window realized reads) / 4.695, 4.722, 4.869,
  4.991, 5.334 (the 2018 depth reads; 4.99 = mid-grid) / 5.185–5.19 (like-for-like
  Freddie pooled) / 5.2156 (calendar-standardized) / 5.51 (age-standardized, 84%
  imputed) / 5.52 (Fannie) / 6.07–6.1 (rejected pooled read) / 6.91 (rejected 2019
  leg) / 3.1533 (activity-matched transport). **5.5–7.7% with midpoint 6.5% is not
  a floor** — it is δ, the elasticity band.
- **Empirical vs simulated CPR**: back-outs 5.14 (ABM basis, default) / 5.52
  (hazard basis) / 5.79 (note-rate WAC); simulated means 4.76 (Path B) / 11.68
  (ABM) / 3.34 (Path A) / 5.61 vs 3.39 (Danish legs, U.S.-intercept vs
  Danish-level) / 8.14, 11.63 (cross-design legs).
- **Strata and cells**: 296 four-way strata / 295 fixed effects / 226 in-window
  clusters / **31 off-window clusters (= the floor-read clusters, 5.9 effective)**
  vs **130 three-way draw strata (25.8 effective; Path B's bootstrap unit)**; 137
  is their intersection; 22 standardization cells; 21-cell box; 27-cell joint
  sweep. The 296-vs-130 key difference (LTV axis dropped) is the collision that
  once cost a reconciliation cycle.
- **Loan-month counts**: 1,683,124 (U.S. panel) vs 1,683,082 (Danish classification
  universe; exactly 42 fewer) / 75,000 drawn / 34,734 prepaid pre-window / 40,234
  window-start survivors (the 32-loan gap to 40,266 is other pre-window attrition)
  / 10,000 ABM households (unrelated framework).
- **Floor-bind shares**: 36% ≈ 36.3% (central, in-sample) / 14.3% (null, in-sample)
  / 68.8% (central, off-window) / 35.8% (null, off-window — not the 36.3%
  look-alike) — all unweighted loan-month counts, never dollar shares.
- **Path correlations**: +0.190 (Path B lag 0) vs +0.19/0.192/0.195 (ABM's best at
  lag −3) vs +0.404 (Path B peak, lag −3); −0.318/−0.316 (ABM lag 0, two back-out
  series) / −0.378 vs −0.444 (Path A with/without calendar terms) / −0.487 (an
  income-growth diagnostic, not a path correlation).
- **Expectations shares**: 49% and 80% (central allocation, at the two floors);
  23–49% and 38–80% (across the two allocations); 23–80% (the envelope); "roughly
  half" (the verbal gloss). All upper bounds, all on the $87.8B denominator.

## 9. Notation — the paper's symbols, with collision warnings

This document introduces no notation. The paper's own Table 14 (tab:hazard-notation)
and Table 15 (tab:terminology) are the canonical disambiguators; this section adds
the collisions they don't cover. Word-labels are given for distinctions that
survive only in typeset math — use the words in prose, slides, and .md/.txt
editions, where case and subscripts die.

| Symbol | Meaning | Collision warning |
|---|---|---|
| **β₁** | Path B's imported rate-gap coefficient: 0.0686 per 100 bp (printed 0.069; unrounded 0.068571), from δ via eq:beta1 | Doubles as the *name of a simulation leg* ("the β₁ = 0 null" — 44 of its 61 lines). The null is a paired run scored in dollars, **not a hypothesis test**; a leg clearing a threshold is not a non-rejection. |
| **δ** | The elasticity band: proportional quarterly mobility decline per 100 bp; 6.5% central, 5.5–7.7% edges, 3.25% sub-band member | Quoted as a %, so it reads like a rate — and its range overlaps the floor reads (5.19–5.52) and the hazard-basis CPR (5.52). δ and β₁ are two encodings of ONE object; never quote both in one sentence. |
| **β_g** ("Path A's estimated rate-gap coefficient") | +0.65 standardized / +0.29 per 100 bp (spec v4) | vs β₁: same nickname, incomparable scales — sign-only comparison, and even the sign is "not distinguishable from zero under any bias-respecting construction". |
| **β_b vs β_B** ("Path A estimated burnout" vs "Path B calibrated burnout prior") | −0.17/−0.13 estimated on demeaned b_{s,t}; vs the fixed prior −0.5 on cohort B_{s(i),t} ∈ [0,1] | Case-only distinction, on objects that also differ only in case — it vanishes in prose/speech/editions. Always use the word-labels. "B" also means billions in adjacent columns. |
| **β_φ vs β_F** | Path A friction coefficient vs Path B FICO prior | Both read "beta-F" aloud. Also γ_F/γ_L (default hazard, −0.20/+0.25) sit beside β_F/β_L (prepayment, −0.15/+0.10) in Table 17 — transposition risk. |
| **φ** — three objects, rename all | "the friction index" (Path A regressor, index units) · "the friction share" (ABM moving cost, share of home value, 8.23–9.96% realized) · "the PSA scale root" (φ* = 0.754 ≈ 75.4 PSA in the scaled null; bare φ = 1 parity cells also appear) | Unflagged in the paper. The first two are *not* the same series (the Path A construction isn't given in the tex). Never write bare φ in this project's prose. |
| **h̲ (the floor) vs h₀ (the PSA baseline)** | The floor censors the elasticity (enters a max); the baseline multiplies it | They enter eq:pathB on opposite sides and move the marginal in opposite directions. Quote the floor in annual CPR everywhere (4% = 0.0034 SMM); the h-family also includes h^def₀ (3e−4 monthly default intercept), h^vol/h^prep (before/after floor), h_m (quarterly identity), h̲_t (the cyclical variant). |
| **r** | Reserve for the correlation coefficient (its dominant use: r₀ = −0.318 etc.) | The rate-level senses collide: eq:annuity's r is *monthly*, A(P,r,n)'s is *annual*. Write rates as "the market rate m_t" / "the note rate c_i". γ_r is the default-hazard rate-stress coefficient (2.0). |
| **R vs R²** | R = recovered dollars (the marginal = R_central − R_{β₁=0}); R² = fit statistics | Four incompatible R² senses: the raw path R² (−6.984; vs a mean-only null, so negative = worse than a constant); the ~0 out-of-sample R² of the ceiling learner and isotonic recalibration scored on Path A's holdout (+0.003/−0.007 — Path A's own fit prints no holdout R², only RMSE and Theil U); the seasonal-stability variance share (0.011/0.755). Also: Path A's holdout RMSE is 38 points unweighted but 2.5–3.0 exposure-weighted — a 15× gap in one sentence. U₁ vs U₂: only U₂ carries the worse-than-naive reading. |
| **θ** | The ABM's mobility-desire scale — the ONE re-derived parameter. Four live values: 43,883 production (43,882.8125 unrounded), 36,086 cross-design recalibrated, 4,472 external variant, 41,934 in the 50%-DTI leg; 12,500 is a module-default placeholder, always overwritten | Never quote an ABM dollar figure without saying which θ it was scored at. The θ re-derivation is "floor anchor, sense B" (Section 5, pair 9). |
| **κ, z_t** | Cyclical-floor amplitude over [−0.5, +0.5] on the window-standardized mortgage rate z_t | The κ grid measures floor **dispersion**, not cyclicality (85% survives time-scrambling; the additive form removes 98%). z^FICO_i / z^LTV_i are unrelated per-loan credit covariates. |
| **ω** | Floor-form mixture weight (share entering additively): 0 = production max, 1 = additive; marginal +7.5/+9.7/+10.7/+11.2 at 0.1/0.25/0.4/0.6 | ω = 0 (a headline convention) vs β₁ = 0 (a counterfactual leg) — both read as "the null setting" of a Greek parameter. |
| **μ** | Moving-share bracket (production μ = 1 = upper bound) | Its readings (+4.9, +3.36, +2.5, +1.82) sit in the same numeric range as genuine interval endpoints, distinguished only by status text. |
| **η = S_pre^ξ** | Survival-selection attenuation: ξ is the frailty exponent (not estimable; bracketed 0.25/0.5/1 → +5.1/+4.6/+3.7), S_pre the pre-window survival share | Write the ABM's S = 60 as "the 60-month stay horizon" — same letter, incompatible units. |
| **s — two stratum keys** | Four-way estimation stratum (vintage × coupon × FICO × LTV): 296 observed / 295 FE / 226 in-window / 31 off-window clusters (5.9 effective; these 31 carry the floor read). Three-way draw stratum s(i) (LTV dropped): 130, 25.8 effective — Path B's bootstrap unit. 137 = intersection | The known costly conflation. Both are called "stratum-cluster"; only Table 15 and the s vs s(i) marker separate them. |
| **λ** | loss aversion 2.25 (ABM) · λ_ridge (Path A, numerical no-op) · λ_p, λ_d (competing-risks intensities in the taxonomy comparison) | Three frameworks, one glyph; subscript or name in words. |
| **Δ** | ABM payment difference ($/month) · the 0.80-pt note-to-pass-through spread · the Danish buyback yield offset · differencing operator ("in first differences" — write the words) | Four senses, three bare. |
| **σ** | rate stress max{0, −g̃} (default hazard) · log-normal shape (0.45/0.35, ABM draws) | — |
| **P family** | P principal · P_q = 0.06, the conversion auxiliary in eq:beta1 (NOT a measured turnover rate; sits 4× above the source's 1.5%) · p-values · p_t WAL cash flow · p_i/q_i PSI shares | P_q is the dangerous one — it looks like a turnover level. |
| **n** | months/term (eq:annuity, WAL) · sample size (√n bands, n = 42/41) · **n_{s,t} in DOLLARS** (Path A's UPB exposure offset — the only dollar-denominated n; Table 14's units column says so) | Carrying "n = months" into eq:pathA misreads the offset. |
| **t** | calendar month index · the t-distribution (t₅ disturbances, wild-t, Webb wild-t) | "the wild-t read at month t" is constructible; keep the hyphen ("wild-t") vs subscript. |
| **y** | y_i ABM household income · y_{s,t} Path A's prepaid-UPB outcome | Same glyph, both dollars — a units check won't catch a swap. |
| **χ** | The Danish interest-only share (cuts the face gap by χ × $198.67B) | Not a chi-squared anything. |
| **CPR/SMM/WAL/WAC/PSA/UPB** | Pool conventions; SMM = 1−(1−CPR)^(1/12); WAL in years; **WAC has two incompatible senses**: the book's 2.49% face-weighted pass-through coupon vs the draw's 3.86–3.9% unweighted mean note rate — the 1.4-pt gap drives the whole full-book reweight | Every printed CPR level is convention-dependent (ABM/hazard/note-rate basis); attach the basis. |
| **PSI, SMD** | Population Stability Index (>0.25 = large shift); **simulated minimum distance** — an ABM calibration method | Always expand SMD: outside this paper it reads as "standardized mean difference" and inverts the reader's model of the falsification test. The main tex never abbreviates it; the string appears once in the corpus, as the `smd_two_moment` run-index row in the replication appendices. |

## 10. Estimators, runs, and artifacts — the repo side

**Three runnable models, two estimators**: the ABM; the hazard framework = Path A
(excluded) + Path B (headline). The hybrid pipeline scores Path B CPR through the
ABM accounting layer and carries the Danish legs.

**The ABM spec fork (verified against the artifacts — do not "fix" it):**

| | `run-2026-07-04-15yr-foldin` | `run-2026-07-05-berger` ≡ `run-2026-07-05-native15yr` |
|---|---|---|
| Role | **the paper's production headline** (structural-only 15-yr fold-in) | native-15yr behavioral gate |
| Frozen draw | $90.98B / 11.897% | $84.51B / 11.050% |
| Seed mean | $103.68B / 13.557% (the dollar mean is in the run dir's `monte_carlo_summary.json`; the share at 13.557% precision only in `production_scale_test_results.json`'s R3 block) | — |
| Diagnostics | r₀ −0.318, raw R² −6.984, CPR 11.677% | r₀ −0.315, raw R² −7.086, CPR 11.761% |
| Artifacts | `abm/data/runs/run-2026-07-04-15yr-foldin/` | `abm/data/runs/run-2026-07-05-{berger,native15yr}/` — **US legs byte-identical; Danish legs differ by construction** (berger's tax-adjusted anchor ~3.36% CPR vs native's ~44%) |

`abm/data/latest_run_manifest.json` points at the **berger** run — which is why the
native gate *looks* like HEAD. `production_scale_test_results.json` ran the native
gate (12.66%) and its `R3_cross_spec_reference` block exists to expose the
fold-in/native offset; its label `NOT-HEAD-REPRODUCIBLE` (run at code commit
5cf33a3) is the recorded reason the fold-in is not reproducible at HEAD. Table 8's
ABM row is the fold-in run throughout.

**Other repo facts a roadmap reader needs**: the ABM headline freezes ran on
uncommitted trees → identify those specs by manifest content, not commit;
`tab:runindex` in `replication_appendices.tex` is the run index (~80 rows — 82
tag-bearing rows, some naming more than one tag; never build a second index). Tag
citations are gate-counted over manuscript + appendices concatenated: the base
convention is ≥ 1 per tag, but several gates and tests pin *exact* per-tag counts
(2 for some, 3 for others — e.g. two batteries assert exactly three occurrences:
assembly + prose + index), so never add or delete a run citation without grepping
`tools/liveness_gates.py` and `tests/` for that tag first;
verification = `python3 tools/liveness_gates.py` (129 gates) + `python3 -m pytest
tests/ -q` (1,139 tests, 1 skip); ~644 literal spans in the manuscript and 119 in
the appendices are gate/test-pinned — run the protected-span check *before* editing
the tex. Never execute anything under `abm/` or `hazard/` (pre-registered runs;
spec-before-run). Reading JSON artifacts is always fine.

## 11. How the paper got here — the demotion history

The current text is the residue of ~30 adversarial rounds. The big state changes,
newest first, with durable records:

- **v20 review-fix round** (2026-08): paradigm reading formally withdrawn (gated by
  `tests/test_paradigm_withdrawal_gate.py`, 18 collected tests); §VII.D repaired
  (was still calling the withdrawn reading corroborated); the §VII.A spec-fork
  explanation written; berger2026 qualified everywhere; readability pass (sentences
  split ~44 → ~28 words mean). Handoff: `specs/RECORD_v20_review_fixes_handoff.md`.
- **N1 relanding** (v20): the binding interval became **[+2.3, +9.1]** via the
  restricted inversion under the frozen coverage rule; Webb [+2.9, +8.7] demoted
  beside (it was briefly the binding layer — an inconsistency at line 1298's
  intro sentence vs the ladder note is a known leftover). Record:
  `specs/RECORD_v20_N1_relanding.md`.
- **Panel review driving the round**: `panel_review_v19.md` +
  `improvement_plan_v19.md` + `specs/RESPONSE_v20_panel_draft.md`.
- **R28–29** (2026-07): the floor renamed **"baseline turnover floor"** globally
  (from "involuntary-turnover floor" — the reads measure total turnover); binding
  interval was [+2.9, +8.7] then.
- **Rounds 22–24**: every downward correction assembled into one §V.E paragraph;
  the paper's front rebuilt to lead with the range; +5.6 stated as an upper-middle
  member only for floor/basis corrections.
- **v17–v18 era** (2026-07): the off-window (2018) re-anchor landed — the +9.2 →
  +5.6 demotion and the "report a range, not a point" posture; the "within 2.1%"
  recovery claim found false at the headline floor and retired; floor_cyclical
  re-read as dispersion; seasonal floor re-read as dispersion; IV/RD identification
  found NOT_FEASIBLE (pre-QT censoring in the loan sample is the binding
  constraint — see `OOS_IDENTIFICATION.md` and TECHNICAL.md).
- **W4 Fannie replication** (2026-07): 24 quarters / 17.6M loans / 826M loan-months;
  marginal +8.68 vs +9.20.

**Maintenance.** This file is not gate-pinned; update it whenever a headline
number, status, or canonical term changes in the manuscript, and re-verify any
number you carry forward against the tex rather than against this file's history.

*Built 2026-08-12 from a 24-agent extraction sweep over `paper_final_v1.tex`
and `replication_appendices.tex` (Opus extractors, each adversarially verified
against the tex by an independent Fable verifier), synthesized by the coordinator
(Fable), then re-verified whole by a second 5-agent Fable pass that checked every
number, interval, status label, and attribution in this file against the
manuscript; the 18 disagreements it found (5 substantive) were corrected before
commit. This document paraphrases the manuscript; it asserts nothing the tex does
not.*
