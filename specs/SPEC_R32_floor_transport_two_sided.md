# SPEC — R32 Task 11 (R7 / Z4 + Z5): the two-sided floor transport test

**Status: SPEC COMMITTED, NOT YET RUN.** Both legs are specified and committed here
**before either executes.** This is the round's clearest anti-gaming checkpoint: the two
corrections are **opposite-signed**, and running only one would be dishonest in a direction
the choice of leg determines.

- **Leg (a), calendar standardization** — the off-window read is taken in seasonally slow
  months, so standardizing it **raises** the floor and **lowers** the marginal. Running only
  (a) makes the paper honestly worse off.
- **Leg (b), housing-activity matching** — the off-window read imports 2018's housing-activity
  level, and the QT window's is lower, so activity-matching **lowers** the floor and
  **raises** the marginal. Running only (b) is self-serving.

Neither leg may be reported without the other. If one proves infeasible, the other is
reported **together with the record of why its counterweight could not be computed** —
never alone as if it were the whole correction.

---

## 1. Leg (a) — calendar standardization. ANALYTIC, and already derived here.

**The support, measured from `cohort_month_panel.parquet` (recorded in no committed
artifact until now).** The 2018 leg at `mean_loan_age >= 12` spans reporting periods
**201807–201812**, all on 2017-vintage cohorts, with cohort-month counts
**2 / 48 / 48 / 49 / 49 / 49** and exposure shares
**0.00009% / 20.287% / 20.149% / 19.993% / 19.853% / 19.718%**.

So it is **six reporting periods by count and five by exposure weight** — August–December
2018 at ≈20% each, plus a July fragment carrying nine hundred-thousandths of one percent of
exposure. R1's report says "six reporting periods" in one place and "five consecutive
months" in two others; both are defensible on different weightings, and **the manuscript must
state which weighting it means** rather than picking one number.

**The standardization, from the committed calendar profile.**
`seasonal_floor_timing_results.json` → `b1_profile.smm_by_month_jan_dec` (peak month 6,
trough month 1, peak-to-trough 2.131) and `b1_profile.exposure_weight_by_month`:

| mix | exposure-weighted SMM | ratio to leg | 4.991% floor standardizes to |
|---|---|---|---|
| the 2018 leg's own (Aug–Dec) | 0.003405 | 1.00000 | 4.991% |
| the QT window's | 0.003558 | **1.04500** | **5.2156%** |
| flat 12-month | 0.003511 | 1.03125 | 5.1470% |

August–December sits on the **declining** side of the seasonal profile, so the read
understates calendar-average turnover: the floor is too low and the marginal too high.

**Independent corroboration.** R1's own arithmetic gives 4.991 → 5.213 and a marginal of
≈+4.7/+4.8, a −0.8pp move. This spec's derivation, computed from the artifacts without
reference to R1's, gives 4.991 → **5.2156%** and, interpolating this table's own grid between
the 4.991% row (+5.5716) and the 5.334% row (+4.3), **≈+4.74pp — a −0.83pp move**. Two
independent derivations agreeing to 0.003pp on the floor and 0.03pp on the marginal.

**Therefore leg (a) needs no engine run to establish its sign or its approximate size.** One
cheap engine cell is still required for the *exact* marginal, because the paper's committed
floor grid is coarse (4.991, 5.334) and the table value above is an interpolation:

- **Run (a1):** the paired central and null legs at floor **5.2156%**, production form,
  everything else at production convention. Output the exact `marginal_pp`.
- Parity gate **A1:** the same harness at floor 4.991% must reproduce
  `psa_level_sweep_results.json` `cells["4.991|100|*"].trapped_b` to $<10^{-9}$ \$B.
- Parity gate **A2:** the standardization ratio must be recomputed inside the run from the
  committed 12-vector and the panel-derived month mix, and must equal **1.04500** to 5dp — the
  run may not take the ratio from this file.

**Pre-committed expectation:** `marginal_pp` in **[+4.60, +4.90]**, i.e. a move of −0.67 to
−0.97pp. Outside that band, the interpolation is wrong and the discrepancy is reported.

## 2. Leg (b) — housing-activity matching

**The channel already exists in the model.** `hazard/macro.py:83`
`calculate_dynamic_friction` builds
`Dynamic_Friction = BASE_FRICTION (0.07) + search_penalty + sentiment_penalty`, where
`search_penalty = SEARCH_PENALTY_CAP (0.02) · max(0, baseline − ACTLISCOUUS)/(baseline − min)`
and **`baseline` is the 2017–2019 mean of `ACTLISCOUUS`** (active listings), set in
`macro.py:201-202`. So the model already carries a housing-activity term, baselined on exactly
the period the off-window floor is read from.

**The arbitration this leg must state, because the repo already contains a reasoned
objection.** Round 28's WP-J2 (`scaled_null_housing_activity.py`) explicitly **rejected**
scaling the floor:

> M2 scale the floor only — double-counts the floor's empirical content; the floor is an
> empirical read of realized deep-discount turnover and already embeds the non-rate
> suppression.

That rejection is correct **about the window** and does not answer this leg, because the two
concern different periods: WP-J2 asks whether the *window's* suppression is already in the
floor (it is), while R2:M3 asks whether the *2018 read* carries **2018's** activity level (it
does — a level the window never had). Leg (b) must quote WP-J2's rejection and state this
distinction, or it is arguing past the repo's own position.

**The proxy problem, pre-committed rather than chosen after the fact.** The repo's activity
series is `ACTLISCOUUS` — active **listings**. R2:M3's argument is about existing-home
**sales** (5.34M in 2018 against ≈4.09M in 2023–24). Over this window the two move
*differently*: listings were far below the 2017–19 baseline in 2021–22 and recovered through
2023–25, while sales fell and stayed low. Using listings where the argument is about sales
could invert the sign. So:

- **Primary specification (b1):** the repo's own `ACTLISCOUUS`-based measure, because it is
  committed, already baselined on 2017–19, and needs no new external input. Compute the
  2018-leg-months mean and the QT-window mean of the *activity level*, and express the floor
  read's activity premium as the ratio.
- **Secondary specification (b2):** the same computation on existing-home sales
  (FRED `EXHOSLUSM545S`). **Requires a live FRED call.** If the key or the network is
  unavailable, (b2) is recorded NOT_COMPUTABLE with that reason and (b1) is reported as the
  sole activity read, labelled as a listings-based proxy for a sales-based argument.
- **Both are reported.** If (b1) and (b2) disagree in sign, that disagreement **is** the
  result, and the leg lands as "the direction of the activity correction depends on which
  activity measure is used", with both numbers.

**Run (b1):** the paired central and null legs at the activity-matched floor, production form.
Parity gates **B1** (floor-4.991% reproduction, as A1) and **B2** (the activity ratio
recomputed inside the run from `macro.py`'s own function, not taken from this file).

**Pre-committed expectation:** the activity-matched floor is **below** 4.991% and the marginal
therefore **above** +5.57. No band is committed, because the size depends on a mapping from
an activity ratio to a turnover ratio that this spec does not fix — and inventing one after
seeing the number is exactly what a pre-commitment is supposed to prevent. **The sign is
pre-committed; the magnitude is reported as measured.** If the sign comes out the other way
(the window's activity exceeding 2018's on the chosen measure), that is reported as a failed
prediction with this sentence quoted.

## 3. Composition — stated in advance, because it is where a two-sided test can be gamed

The two legs are opposite-signed. A composed figure is **not** their sum: the paper's own
`b5_joint_cell` found that two floor-side adjustments compose with an interaction (the first
joint cell it ran returned an interaction of $-1.47$ points), and §V.E already states that
"corrections here do not compose additively" and that the floor corrections and the censoring
share are "one mechanism read twice".

So:
- Report each leg's marginal **separately**, at its own floor.
- Report the **composed** cell only if it is actually run as a joint cell, never by adding or
  netting the two legs.
- If a composed cell is not run, say so, and state that the two legs bound the correction from
  either side without pinning a net.
- **Do not report a net "they roughly cancel" claim.** Two opposite corrections of similar
  size cancelling is a *finding* that requires the joint cell; asserting it from the two
  separate legs would be arithmetic the design does not support.

## 4. Artifacts, guards, and what must not change

- Output: `hazard/data/floor_transport_two_sided_results.json`. Refuse to write if it exists.
- **Frozen-artifact guard:** sha256 of every file under `hazard/data/` unchanged before and
  after, except the one new output.
- **MUST NOT CHANGE:** `config.py`, `macro.py`, `literature_hazard.py`, `floor_sweep.py`,
  `competing_risks.py`. Leg (b) *reads* `calculate_dynamic_friction`; it does not modify it.
- Every leg records its floor, its ratio, its parity-gate results, its pre-committed
  expectation and a `prediction_held` boolean.

## 5. Landing rules

- **Both legs computed.** Land both, adjacent, in §V.E's assembly discussion, each with its
  sign and its floor, and add both to `tab:assembly` with the inclusion rule Task F's C-40
  edit establishes. Update the statement that "every correction I can measure … moves it down
  within the range rather than up" — **leg (b) is a measured correction that moves it up**, so
  that sentence becomes false as written and must be restated as it is, not deleted. This is
  the single most likely place for this round to quietly go wrong: the abstract carries the
  same claim.
- **Leg (a) only** (b1 and b2 both NOT_COMPUTABLE). Land (a) *and* a recorded statement that
  the opposite-signed activity correction could not be computed and why, so the assembly's
  one-directionality is not silently reinforced by an artifact of what was runnable.
- **Leg (b) only** (a's parity gate fails). Land (b) with the same symmetric disclosure.
- **Neither.** Record both reasons; the existing text stands unchanged.

In every branch, the direction of each computed leg is reported whichever way it falls.
