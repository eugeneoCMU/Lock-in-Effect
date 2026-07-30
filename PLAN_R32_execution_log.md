# R32 execution log — REVIEW3 remediation

Plan: `docs/superpowers/plans/2026-07-29-review3-remediation.md`
Branch `claude/brave-shaw-b02840`, from `a785f3d`. **Nothing pushed — Eugene pushes.**

Baseline measured before the first edit, and the invariant every batch restores:
**ALL GATES PASS | 495 tests | ALL RENDER CHECKS PASS | 139pp canonical / 140pp
variant | split main 1–94, online appendix 95–139 | 0 undefined refs | 0 errors |
0 overfull vbox | canonical and variant differ at line 31 only.**

---

## WAVE 1 — required before the Carroll Round talk

| Task | Condition | Commit | State |
|---|---|---|---|
| 1 | C-R1a/b/c — abstract | `66df169` | LANDED |
| 2 | C-R2 — basis mix at the form fork | `c2e505e` | LANDED |
| 3 | C-DA-C1 — floor read's true support | `6a34d5c` | LANDED |
| 4 | C-R4 — β₁ sign | `d22b265` | LANDED |
| 5 | Carroll Round Q&A prep | `7189c8e` | LANDED |

**WAVE 1 COMPLETE.** Gate/test count: **109 gates (was 108), 501 tests (was 495)**.
Page count moved **139 -> 140** canonical / **140 -> 141** variant at Task 3, split
recut **1-95 + 96-140**; that is the cost of Task 3's added rows and support
statements, and Task 18's bundle notes must carry it.

### What each landing changed, and what it cost elsewhere

**Task 1 (`66df169`).** Three abstract repairs. The self-refuting clause turned out
not to be a contradiction but an *equivocation*: gate `levels_only_abstract` sits
beside `levels_only_body` and the artifact verdict `CONCEDE_LEVELS_ONLY`, so
"levels" carried the **timing** concession in the abstract and the **level** claim
in §V.E, unsignposted. The replacement states both truths and the gate pin follows
the timing half. The 85.7% mechanical majority is now conditioned in its own topic
clause with the additive form's 35.6% null beside it. The bounding claim names
itself as the widest layer *that does have a coverage property* (the body's exact
words) and names the unestimated seasoning ramp's +0.9→+15.6 span in the same
clause.
*Forced couplings:* abstract 248→287 words ⇒ the response letter's claimed count
moved (gate #101 requires equality) and `tests/test_response_letter_gate.py`'s
hardcoded `"taken it to 248 words"` mutation anchor moved to 287 — it would have
become a silent no-op and vacated three tests. `248` joined the wrong-count
parametrize list per that test's own convention. 287 avoids every entry.

**Task 2 (`c2e505e`).** The sentence deciding the max/additive fork paired a
shared-basis 91.3% with a standalone-basis 55.9%, reading as a 35.4-point fall
where the true single-basis fall is 44.5. Restated standalone (100.4→55.9,
basis named), which also makes it agree with the paper's other additive-form site.
The shared alternative was derived too (91.3→46.8) and is equally true.

**Task 4 (`d22b265`).** `tab:lowband`'s nine β₁ cells harmonised to positive.
NEW gate #109 asserts *agreement* between `tab:params` and `tab:lowband` rather
than a hardcoded sign, so it survives a later round restating `eq:beta1`.
Replicator note added recording that `rothstein_beta1` returns the opposite sign.

**Task 5 (`7189c8e`).** `docs/carroll_round_qa_prep.md`.

---

## The basis conversion, derived once and reused

The manuscript states its own rule: the shared basis nets a common curtailment
flow from every U.S. leg's **numerator**, "a flat 9.1 percentage points."
Exact values: `shared_layer_scoring_results.json` →
`curtailment_netted_b = 69.56220187263008`; benchmark `764.7482532227`; offset
**9.0964pp**. It reproduces every printed figure from
`floor_form_mixture_results.json`'s standalone `share_pct`:

| leg | standalone | shared | printed |
|---|---|---|---|
| central, max form | 100.363 | 91.267 | 91.3 |
| null, max form | 94.792 | 85.695 | 85.7 |
| central, additive | 55.907 | 46.810 | 46.8 |
| null, additive | 44.700 | 35.603 | 35.6 |

`psa_level_sweep_results.json`'s `lo_pp`/`hi_pp` are **marginals**, which are
basis-invariant because the netting cancels in a central-minus-null difference —
so they carry no basis label, and none was added.

---

## Findings that corrected the plan itself

Recorded because acting on the plan's text as written would have introduced
defects. All were derived from source, not taken from an agent's word.

1. **`identifies levels only` IS gate-pinned.** The plan's Task 1 Step 2 said to
   confirm no gate covered it and that the check "must return nothing". It
   returns `tools/liveness_gates.py:2133`. Handled by re-pinning in the same
   commit; had the check been trusted, the suite would have failed after the edit.
2. **The PSA span literals were not new.** Task 1 Step 4 expected `+0.9`/`+15.6`
   to go 0→1. Both were already in the body (`$+15.6$` twice). The abstract
   addition therefore aligns with existing body text rather than introducing a
   figure — better, but the expected counts were wrong.
3. **"Two corrections agree to 0.01pp" is not a safe thing to write.** Task 3
   Step 3 instructed it. The Fannie 5.52% is a cross-agency read on the **pooled
   2017–19** cell, whose like-for-like Freddie counterpart is **5.185%**
   (`difference_pp` 0.337) — not an age correction to the clean 2018 leg's 4.991%.
   The age-standardized 5.51% imputes **84.0%** of its weight. Their 0.01-point
   proximity is a coincidence between two different perturbations. Two independent
   audit agents flagged this separately and the artifact confirms it.
4. **The seasoning error's direction survives; its magnitude needed bounding.**
   The plan asserts the read "understates the mature book's baseline turnover".
   True — mature turnover is higher in **12 of 12** measurable cells across both
   agencies. But the clean leg cannot measure it at all (zero cohort-months at
   age ≥24), the in-window refi-suppressed contrast is only **+0.08/+0.19pp**, and
   the pooled **+3.74/+4.61pp** is itself refi-contaminated. The 2018 leg's own
   +1.558pp ramp is flagged `ramp_rise_is_psa_confounded: true` and is *not* the
   evidence. Stating a large signed correction would have overstated a
   self-criticism, which is still a false claim.
5. **The CR3-BM/WCR grid truncation is on the LOWER endpoint, not the upper.**
   The plan's Task 6 text says upper. Verified from
   `floor_inference_correction_v2_results.json`: both clip to `+2.2809` at the
   6.0% floor grid edge (`truncated_at_grid_edge: true` on `lower_pp_edge`).
   CR2-BM `[+2.41, +9.15]` is the untruncated wider comparator.
6. **The full ladder reproduces the plan's anti-condition width table exactly**
   (percentile 5.044, CR1-t 5.197, CR2-t 5.579, Webb 5.823, Rademacher 5.927,
   CR3-t 6.001, CR1-BM 6.043, CR2-BM 6.740, WCR 6.828, CR3-BM 7.284). Webb is
   third-narrowest; R1:M1's premise stays refuted and its real argument stands.
7. **An agent claim adjudicated and rejected.** One inventory agent reported that
   Task 1 imported Z13's defect by calling the Webb interval "the widest layer
   that does have a coverage property". It did not: the paper's taxonomy makes a
   *layer* a source of uncertainty (the PSA convention layer is wider but has no
   coverage property) and CR2-BM/Webb *rungs within* the sampling-error layer.
   The body already makes the layer claim verbatim. Z13 — which rung to quote
   inside that layer — remains open and is Task 6's.

## A mistake I made, and what it cost

`3a81e71`, reverted by `d2c0c67`. I audited every float for `\tnote{x}` markers
lacking a matching `\item[x]` **inside the float**, found `tab:oosfloor` (one
marker) and `tab:danish` (four), and committed four new in-float notes for the
latter. Both were false positives: round 31's `tools/render_fix_r31.py` lists
`tab:bases, tab:estimators, tab:danish, tab:ladder, tab:oosfloor` as **CLASS_B —
"tablenotes push the float over"** — and moved their notes into post-float
`\noindent{\footnotesize \emph{Notes to Table~\ref{…}.} …}` paragraphs. That *is*
the ~919-off-page-item repair this round must preserve. Both tables' markers were
already paired there, and `tab:danish`'s existing note defines a–d more fully than
what I wrote. So the commit added duplicates and re-floated a CLASS_B table.

It passed 109 gates, 501 tests and the render gate. Green was necessary and not
sufficient — this time against me. Two lessons:

1. **A structural audit must encode the repo's actual convention, not the
   language's default one.** Mine encoded "notes live inside floats", which this
   paper deliberately stopped doing in round 31.
2. **"No reviewer raised it and no gate caught it" is not evidence of a defect.**
   It was true here only because there was nothing to catch.

Caught by the Task-3 drafting agent, which found the same CLASS_B fact
independently and flagged my commit as a concurrent edit. Its Edit 3-ALT would
have reversed the round-31 repair a second time; Edit 3 (extend the existing
post-float paragraph) is what landed.

## Task 9 (R5, the h₀ re-anchor) — feasibility scouted read-only, NOT yet run

Groundwork so the spec is written against measured facts. Nothing executed; all
figures are from committed artifacts.

- **The transport target exists.** Path A fits
  `log h = spline(loan_age) + β₁·gap + β₂·burnout_orth + β₃·friction + FE(stratum)`
  with `AGE_SPLINE_KNOTS = [12, 24, 36, 60, 84, 120]` and a truncated power basis
  `[age, (age−k)²₊ …]` (`hazard/hazard_fit.py:58`).
- **The substitution mechanism is settled precedent, not invention.**
  `PSA_SPEED` binds at **def time** (`h0_psa(age, psa_speed=PSA_SPEED)`, called by
  `baseline_hazard` without the argument), so mutating `config.PSA_SPEED` at
  runtime is a silent no-op. `hazard/psa_level_sweep.py` already solves this: it
  patches `fs._ORIG_PREPAY` with a closure passing `psa_speed` explicitly, and
  gates it with (i) the patched PSA-100 leg reproducing the unpatched one to
  `<1e-9 $B`, (ii) `max|h0_psa(age,100) − baseline_hazard(age)| == 0` on age
  0–360, and (iii) **a no-op patch counting as GATE_FAILURE**. Task 9's spec
  should reuse all three.
- **But the spline is not usable as-is, and this is the finding that matters.**
  `baseline_hazard` supports only `"psa"` and `"weibull"` — there is no
  spline/tabulated mode, so a transport must be built. Worse, of the 200 committed
  bootstrap replicates in `pathA_bootstrap_fullvec_draws_specv4.csv` (which *do*
  carry `head_age_spline_*`), 199 are flagged converged but only **98 (49%)**
  imply a monthly hazard inside (1e-6, 0.5) across ages 18–107, the band Path B's
  population actually occupies. The truncated-power basis extrapolates
  explosively: the median linear predictor reaches **+97 at age 360** (i.e.
  `exp` overflow), and even normalised to its own mean the surviving shape spans
  p05 0.88 to p95 9.80 at age 107. The **point-estimate** spline is in no
  committed artifact — `pathA_resimulate_joint_pointhead_spec4.csv` carries only
  the three betas — so "Path A's estimated spline" is not a single object one can
  simply substitute.
- **Consequence for the spec:** Task 9 must either (a) restrict the transport to a
  usable age band with a stated replicate-exclusion rule and report the resulting
  interval as conditional on it, or (b) be recorded INFEASIBLE with this reason
  and the strongest honest alternative in its place. Either is a legitimate
  outcome under the plan; what is not legitimate is presenting a re-anchor as "the
  estimated ramp" when half the replicates are degenerate. The upside if (a)
  holds is real: the bootstrap draws would give the ramp layer a **coverage
  property**, which is exactly what the CRITICAL asks for.
