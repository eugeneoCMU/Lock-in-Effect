# SPEC — R32 Task 9 (R5 / DA:C2 / X1): re-anchor $h_0$ on Path A's estimated seasoning spline

**Status: SPEC COMMITTED, NOT YET RUN.** Nothing in this file may be executed until it is
committed. Written before any run, per the round's absolute spec-before-run rule.

**Condition.** The panel's second CRITICAL (X1, upheld, severity split Critical at the
abstract and Table 1). The baseline seasoning ramp is a **convention** — 100 PSA — and it is
the widest disclosed layer in the paper: sweeping 75–150 PSA carries the marginal from
$+0.9$ to $+15.6$ points at the off-window floor, a 14.77pp span with **no coverage
property** (`psa_level_sweep_results.json` → `ranges["4.991"]`). An estimate of the same
object exists inside the paper — Path A fits a seasoning spline — so the condition is to
convert this layer from a convention into an estimate, or to record why that cannot be done.

**This run may move the headline marginal against the author's interest. That outcome is
pre-authorised and lands (§7, Branch rules).**

---

## 1. What is being estimated, and what is NOT

Path A fits, on the stratum-month panel:

```
log h = spline(loan_age) + β₁·RateGap_bps + β₂·Burnout_orth + β₃·Friction + FE(stratum)
```

with `AGE_SPLINE_KNOTS = [12, 24, 36, 60, 84, 120]` and the truncated power basis
`[age, (age−12)²₊, (age−24)²₊, (age−36)²₊, (age−60)²₊, (age−84)²₊, (age−120)²₊]`
(`hazard/hazard_fit.py:58`, `hazard/config.py:86`).

**Only the SHAPE of that spline is transportable, and this run estimates only the shape.**
Three reasons, all of which must be stated in the manuscript wherever the result is quoted:

1. The spline's **level** is absorbed by the fitted constant and the stratum fixed effects,
   so it is not separately identified.
2. Path A's units are *annualized stratum-month CPR, percentage points*
   (`pathA_ridge_v4_results.json` → `spec_v4.units`); Path B's $h_0$ is a *monthly loan-level
   hazard*. There is no unit-preserving transport of the level.
3. Path B's level is pinned by something else entirely — the baseline turnover floor
   calibration — which this run holds fixed at the off-window headline 4.991%.

So the object under test is **the age profile of baseline turnover**, holding the level at
the floor calibration. That is exactly the convention the panel objects to, and no more.
Any manuscript sentence must say "the ramp's shape", never "the ramp".

## 2. Inputs — all committed; nothing is re-fitted

| input | path | what it supplies |
|---|---|---|
| spline coefficients, per bootstrap replicate | `hazard/data/pathA_bootstrap_fullvec_draws_specv4.csv` | 200 rows; `head_const`, `head_age_linear`, `head_age_spline_{12,24,36,60,84,120}`, `converged`, `failure` |
| loan panel | `hazard/data/loan_sample.parquet` | 75,000 loans, `loan_age`, vintages 2017–2021 |
| production floor + convention | `hazard/config.py`, `hazard/literature_hazard.py` | `PSA_SPEED = 100.0`, `BASELINE_MODE = "psa"` |
| the leg this run must reproduce | `hazard/data/psa_level_sweep_results.json` → `cells["4.991|100|0"]`, `cells["4.991|100|6.5"]` | parity target: null `trapped_b` 724.9180585654117, central `trapped_b` 767.5264524465003, `marginal_pp` 5.571558182909726 |

**There is NO committed point-estimate spline.** `pathA_resimulate_joint_pointhead_spec4.csv`
carries only the three macro betas (`rate_gap_bps`, `burnout_orth`, `friction`) and the
outcome columns — no `head_age_*`. This is a measured fact, not an assumption, and it is why
§4 works from the replicate distribution rather than from a point vector. Re-fitting to
recover a point estimate is **out of scope for this spec** (it would be a new estimation, not
a transport, and would need its own spec).

## 3. Substitution mechanism — settled precedent, not invention

`PSA_SPEED` binds at **def time**: `h0_psa(age_months, psa_speed=PSA_SPEED)` and
`baseline_hazard` calls `h0_psa(age_months)` without the argument. **Mutating
`config.PSA_SPEED` at runtime is a silent no-op.** (Round-28 finding, re-verified.)

**The seam is `literature_hazard.baseline_hazard`, not `floor_sweep._ORIG_PREPAY`.** This
spec's first draft named the latter and was wrong: `_ORIG_PREPAY` is the seam for replacing
the whole *prepay closure* (what `psa_level_sweep` and `floor_form_mixture` do, because they
change terms inside it), whereas this run replaces **$h_0$ itself**, one function deeper.
Round 28's WP-J2 (`hazard/scaled_null_housing_activity.py`) establishes and validates the
right one, and documents why:

> `literature_hazard.prepay_hazard:99` calls `baseline_hazard(loan_age)` as a MODULE-LEVEL
> name, resolved in `literature_hazard`'s namespace at CALL time; `baseline_hazard:73-76`
> dispatches to `h0_psa(age_months)`. Patching the module attribute
> `literature_hazard.PSA_SPEED` does NOT work (the default binds at def time); patching
> `literature_hazard.baseline_hazard = lambda age, mode=None: ...` DOES.

It also records that `fs._ORIG_PREPAY` and the bind tally pick a replaced baseline up
automatically, so the bind column stays meaningful and is expected to move — a lower $h_0$ is
censored by the floor more often. Both facts are load-bearing here: the substitution needs no
reimplementation of the prepay closure, and `floor_bind_share` becomes a diagnostic of
whether the substitution took effect.

So: assign `lh.baseline_hazard = <spline closure>`, restore in a `finally`, and change
nothing else.

**Disclosure carried over from WP-J2:** `competing_risks.py:148` calls `prepay_hazard` on the
Danish `us_intercept` branch too, so a Danish leg simulated in the same run would also carry
the substituted baseline. Only the U.S. legs are scored here, and the run must not report any
Danish quantity.

New runner: `hazard/h0_reanchor.py`. **MUST NOT CHANGE:** `config.py` (`PSA_SPEED` stays
100.0, `BASELINE_MODE` stays `"psa"`), `literature_hazard.py`, `competing_risks.py`,
`floor_sweep.py`, or any file under `hazard/data/` that an existing gate reads.

## 4. The shape transport, stated as arithmetic

For replicate $r$ with coefficients $(c_r, b_r)$ over the basis $B(a)$:

1. Raw log-shape: $\ell_r(a) = c_r + B(a)\,b_r$ over integer ages $a \in [A_{lo}, A_{hi}]$.
2. **Age support.** $[A_{lo}, A_{hi}] = [18, 107]$ — the band Path B's population occupies
   over the QT window (vintages 2017–2021 against June 2022–November 2025). Outside it the
   truncated-power basis extrapolates without support: the median $\ell$ reaches **+97 at
   age 360**, i.e. `exp` overflow. Ages outside the band are **clamped to the band's
   endpoints**, and the clamp is reported.
3. **Level normalisation (the step that makes this a shape test).** Rescale so the
   exposure-weighted mean of the transported $h_0$ over the evaluated loan-months equals the
   exposure-weighted mean of the production $h_0^{\text{PSA-100}}$ over the *same*
   loan-months:
   $h_0^{(r)}(a) = \exp(\ell_r(a)) \cdot \dfrac{\overline{h_0^{\text{PSA-100}}}}{\overline{\exp(\ell_r)}}$
   with both means taken on the identical loan-month weights. The level is therefore
   **unchanged by construction**; only the profile moves.
4. **Usability screen, applied AFTER normalisation** (not before — the pre-normalisation
   screen is not the right test): replicate $r$ is usable iff $h_0^{(r)}(a)$ is finite and
   within $(10^{-6}, 0.5)$ for every $a$ in the band, and `converged` is true and `failure`
   is empty.

**Measured now, read-only, before any run:** 199 of 200 replicates are flagged converged;
on the *pre-normalisation* screen only **98 (49%)** are usable, and even among those the
normalised shape spans p05 0.88 to p95 9.80 at age 107. The post-normalisation count is what
§7 branches on and is **not yet known** — that is one of the two things this run measures.

**Direction the shape implies, pre-committed as a prediction.** The median usable shape
*falls* with age over the band (normalised 2.004 at 18 → 0.400 at 60) whereas PSA-100 is flat
after month 30 (0.618 → 1.030). A profile that puts less hazard on older loans leaves more
loan-months pinned at the floor under the max form, and the marginal is zero wherever the
baseline sits below the floor — so **the marginal is predicted to fall relative to $+5.6$.**
Recorded here so the result cannot be reinterpreted after the fact. If it rises, that is
reported as a failed prediction, with the prediction quoted.

## 5. Parity gates — all must pass before any substituted leg is believed

| gate | assertion | why |
|---|---|---|
| **G1a** unpatched parity | with no patch installed, the 4.991% central and null legs reproduce `psa_level_sweep_results.json` `cells["4.991|100|*"]` `trapped_b` to $<10^{-9}$ \$B | the harness is wired correctly before anything is substituted |
| **G1b** identity patch, run PATCHED | install `lh.baseline_hazard = lambda age, mode=None: lh.h0_psa(age, psa_speed=100.0)` and require the result to equal the unpatched leg to $<10^{-9}$ \$B, **and** `max abs(lh.h0_psa(age,100) − lh.baseline_hazard(age)) == 0.0` on age 0…360 | WP-J2's design: at the identity parameter the patched call is bit-identical to production **by construction**, which is why the identity cell is run *patched* — it is the wiring test, not a shortcut around it |
| **G1b′** bind-tally movement | `floor_bind_share` must MOVE between the identity cell and each substituted cell | WP-J2 records that the bind tally picks a replaced baseline up automatically; a frozen bind share is therefore independent evidence the substitution did not reach the engine |
| **G1c** no-op detection | the substituted leg must differ from the PSA-100 leg by **more than \$1B**; if it does not, that is **GATE_FAILURE, never a result** | a patch that silently failed to take effect would otherwise read as "no change" |
| **G2** frozen-artifact guard | `psa_level_sweep_results.json`, `oos_identification_results.json`, `floor_form_mixture_results.json` and every other file under `hazard/data/` byte-identical (sha256) before and after the run, except the single new output path | never overwrite a frozen artifact |
| **G3** level invariance | the exposure-weighted mean $h_0$ of every substituted leg equals the PSA-100 mean to $<10^{-12}$ relative | proves the run tests shape and not level, i.e. §1's claim is true of the code |
| **G4** floor untouched | the floor stays 4.991% and `FLOOR_MODE` stays the production value on every leg | the floor is the level anchor and is not part of this test |

| **G5** cross-route reproduction | using the same `lh.baseline_hazard` seam with a *pure level scaling* $\phi = 0.75$ at floor 4.991%, the run must return `marginal_pp` $= 0.8560355409769471$ | two committed artifacts already agree on this number by two different routes — `scaled_null_housing_activity_results.json` `ladder["4.991\|0.75"].marginal_pp` and `psa_level_sweep_results.json` `cells["4.991\|75\|6.5"].marginal_pp` are bit-identical, because $\phi = 0.75$ and 75 PSA are the same object. A new harness that cannot reproduce a number two existing routes agree on is broken, and this catches it before any spline is substituted |

`G1c` and `G3` together are the anti-gaming pair: `G1c` makes a silent no-op fail, `G3` makes
a level change fail. Without both, this run could produce a comfortable number for the wrong
reason. `G5` is the independent-route check: it is the only gate here whose expected value
comes from outside this run's own machinery.

## 6. Output — a new path, written once

`hazard/data/h0_reanchor_results.json`, containing: `spec` (this file's path and its git
sha), the `age_band`, the per-replicate usability verdict with the exclusion reason, the
usable count and rate, the paired central/null `trapped_b` and `marginal_pp` per usable
replicate, the resulting marginal interval as percentiles (5/50/95) **and** as min–max, all
six parity-gate results, the pre-committed prediction from §4 with a `prediction_held`
boolean, and the branch of §7 taken. Refuse to write if the path exists.

## 7. Landing rules — one per branch, committed in advance

Let $u$ be the post-normalisation usable-replicate rate and $I$ the resulting marginal
interval at the 4.991% floor and central $\delta = 6.5\%$.

- **Branch A — $u \geq 0.60$ and all parity gates pass.** The ramp layer now has a
  *coverage property*. Land $I$ as an **estimated** replacement for the 14.77pp convention
  span: the abstract's "the unestimated baseline seasoning ramp spans $+0.9$ to $+15.6$"
  becomes the estimated interval with its exclusion rate; §V.E's "a range over a convention I
  did not estimate, and its endpoints are not draws from anything" is replaced by the
  estimated statement; the PSA sweep is retained as the convention sensitivity beside it.
  Report $I$ **whichever way it falls**, and if $I$ excludes $+5.6$, say so in the same
  sentence.
- **Branch B — $0.40 \leq u < 0.60$ and all parity gates pass.** Land $I$ as a
  **conditional** estimate: print it with the exclusion rate in the same clause, keep the word
  "unestimated" for the convention span, and add one sentence that a conditional estimate
  exists and what it is. Do **not** call it the ramp's sampling interval — with two-fifths of
  replicates discarded it is not one.
- **Branch C — $u < 0.40$, or any parity gate fails, or $I$ is not finite.** Record
  **NOT_FEASIBLE** in `specs/RECORD_R32_h0_reanchor_infeasible.md` with the measured $u$, the
  failing gate if any, and the specific numerical reason. The honest alternative that lands
  instead: one sentence in §V.E stating that the paper's own estimated seasoning spline
  **cannot** be transported to $h_0$ — the point-estimate coefficients are in no committed
  artifact and the replicate distribution is degenerate over the age band at the measured
  rate — so the ramp remains a convention *and the paper now says why*, rather than leaving
  the reader to assume no estimate was attempted. The 14.77pp span stays, labelled
  unestimated, exactly as it is.
- **In every branch:** the prediction in §4 is reported against the outcome, and if
  `prediction_held` is false that is stated in the manuscript sentence, not only in the
  artifact.

**No branch permits dropping the PSA convention span.** It is a disclosure; the round's
first anti-gaming rule forbids removing it to satisfy a criticism.

## 8. What this run does not settle

- The **level** of baseline turnover (pinned by the floor; that is Task 11's two-sided
  transport test).
- The **form** fork (max vs additive) — orthogonal, and the run is executed under the
  production form only.
- Whether Path A's spline is the *right* estimate of the age profile. It is the paper's own,
  which is why it is the one transported; its own identification is Path A's business and is
  not relitigated here.
