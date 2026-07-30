# SPEC — R32 C-73 (analytic): recompute the implied cross-sectional gradient at the headline floor and under the additive form

**Status: SPEC COMMITTED, NOT YET RUN.** Written before the run, per the round's absolute
spec-before-run rule.

**Condition (inventory C-73).** "The one internal test of the imported elasticity's implied
magnitude is computed at a demoted calibration and declined rather than diagnosed; it must
be recomputed at the 4.991% headline floor and under the additive form, at 75/100/125 PSA
— and if the implied gradient still falls short, diagnose it."

**This run may move a number against the author's interest. That outcome is pre-authorised
and lands (§5).**

---

## 1. What the committed run did, and why it is at the wrong calibration

`episode_confrontation` compares a *realized* cross-sectional CPR gradient across rate-gap
buckets against the gradient the imported elasticity *implies*. Its committed figures
(`episode_confrontation_results.json`, verdict T5):

| quantity | value |
|---|---|
| `realized_gradient_pp` | 4.198179219676357 |
| gradient CI95 | [3.58526, 4.65648] |
| `model_implied_gradient_pp_at_0.069` | 0.9371125522400376 |
| `realized_over_implied_mid` | 4.479909280524726 |
| `power_injected` at 0.069 | 0.675 |

The implied path is analytic, from the paper's own eq. (2):
`h = max(h_floor, h0_PSA(age) · exp((−β₁)·100·gap))`, with the exposure-weighted mean over
each bucket converted to CPR. But it is evaluated at the **production** floor
`INVOLUNTARY_CPR_ANNUAL = 4%` and **100 PSA** — the in-sample calibration this paper has
since demoted. The headline is the 4.991% off-window floor, and the form fork is live.

## 2. Why the answer is not obvious, stated before the run

Two effects work against each other and the spec does not pre-judge their net:

- **Raising the floor 4% → 4.991% under the MAX form compresses the implied gradient.**
  Wherever `h_floor ≥ h_vol` the cell sits at the floor regardless of its gap, so bound
  cells contribute *zero* gradient. A higher floor binds in more cells, in the deep-gap
  buckets first. Direction: implied gradient **falls**, `realized/implied` **rises**.
- **The ADDITIVE form removes the censoring entirely** — `h = 1 − (1−h_floor)(1−h_vol)`
  never clips the voluntary term, so the full voluntary gradient survives. Direction:
  implied gradient **rises**, `realized/implied` **falls**.
- **PSA scales h0**, hence the voluntary term and its spread across gaps, roughly
  proportionally. 125 PSA raises the implied gradient, 75 PSA lowers it.

**Pre-committed expectation.** Under the max form at 4.991% the implied gradient FALLS
below the committed 0.9371 and the ratio RISES above 4.48. Under the additive form at the
same floor the implied gradient RISES above 0.9371. **No band is committed for either**,
because the magnitude depends on how much exposure the floor censors, which is exactly what
the run measures; the two SIGNS are the pre-commitment. If either sign comes out the other
way it is reported as a failed prediction with this paragraph quoted.

## 3. Inputs and machinery — all committed, nothing re-fitted

| input | source |
|---|---|
| stratum-month panel | `mdr.build_panel()` (the same call `episode_confrontation.main` makes) |
| stratum id | `build_stratum_id(vintage, coupon, fico_bucket, ltv_bucket)` |
| bucket rule | stratum window-mean gap (exposure-weighted), buckets `[-1,0)/[-2,-1)/[-3,-2)/<=-3`, `gap >= 0` excluded |
| window | 202206..202509 (40 months) |
| seasoning | `age0 >= 24` at window start (PRIMARY) |
| endpoint support | `>= 1%` of four-bucket exposure AND `>= 10` strata |
| β₁ | `lh.rothstein_beta1` at declines 5.5 / 6.5 / 7.7% |
| h0 | `lh.h0_psa(age, psa_speed)` |

The gradient is `implied CPR(shallow endpoint) − implied CPR(deep endpoint)`, the same
definition `bucket_block` uses. **No new estimation; this is arithmetic on a frozen panel.**

## 4. Gates

| gate | assertion |
|---|---|
| **E1** panel/bucket parity | rebuilt selection reproduces the committed `realized_gradient_pp` **4.198179219676357** to `< 1e-9`, and the committed `qualified_buckets` and endpoint labels exactly. This is the gate that proves the reconstruction is the committed one. |
| **E2** implied parity | at the production cell (4% floor, max form, 100 PSA) the recomputed implied gradient reproduces `0.9371125522400376` to `< 1e-9` |
| **E3** censoring monotone | under the max form the floor-bind exposure share must be non-decreasing in the floor, per bucket — a mechanical property; if it fails the reconstruction is wrong |
| **E4** additive never binds | under the additive form the reported bind share is 0 by construction |
| **E5** frozen artifacts | sha256 of every file under `hazard/data/` unchanged except the one new output |

E1 and E2 together are the anti-gaming pair: E1 fixes the data, E2 fixes the arithmetic, so
any movement in the new cells is attributable to the calibration change alone.

## 5. Output and landing

`hazard/data/episode_gradient_recompute_results.json` — refuse to overwrite. Carries the
3×2×3 grid (floor × form × PSA) of implied gradients, bind shares, and
`realized_over_implied`, all five gate results, the §2 prediction with a `prediction_held`
boolean per sign, and the branch taken.

- **If the ratio at the headline calibration is still > 1** (the implied gradient still
  falls short of realized): land one sentence in §V.D/§VII where the confrontation is
  reported, saying the shortfall is *not* an artifact of the demoted calibration — it
  survives at the headline floor and under both forms — and give the range of ratios. This
  is the honest diagnosis the condition asks for, and it makes the paper's position
  *weaker*, not stronger: the imported elasticity under-explains the observed cross-section
  by more than the committed figure suggests.
- **If the additive form closes the gap** (ratio ≈ 1 there): land that, and say the
  confrontation is form-conditional — which would be a genuine finding about the fork.
- **If E1 or E2 fails:** record NOT_FEASIBLE in
  `specs/RECORD_R32_c73_infeasible.md` with the failing gate and the numeric miss. The
  honest alternative that lands instead: one sentence stating that the confrontation is
  computed at the in-sample calibration only, and that recomputing it at the headline was
  attempted and could not be made to reproduce the committed run.

**No branch permits deleting the existing T5 verdict or its power analysis.**
