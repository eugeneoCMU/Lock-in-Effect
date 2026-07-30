# SPEC — R32 / C-77: the Aladangady reconciliation under the additive floor form

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `scaled_null_housing_activity_additive`. Runner:
`hazard/scaled_null_housing_activity_additive.py` (not yet written; this spec lands first and
stands on its own). New artifact:
`hazard/data/scaled_null_housing_activity_additive_results.json`.

---

## 1. The condition

C-77 (R3:M2 fix (ii), MAJOR, RUN + WORDING). The housing-activity reconciliation was solved **only
under the production hard-maximum floor form** — the form that censors the elasticity in 68.8% of
loan-months at the headline floor — while max-vs-additive is the paper's largest open question.
The condition: re-solve the same calibration condition under the additive form, and **mark the row
form-conditional either way**.

The calibration condition, unchanged:

$$\text{trapped\_null}(\phi^{*}) - \text{trapped\_null}(1) \;=\; \frac{0.56}{0.44}\,
\bigl[\text{trapped\_central}(1) - \text{trapped\_null}(1)\bigr]$$

with the ratio $1.272727272727273$ from `aladangady2024`'s 44% rate-gap share, and $\phi$ scaling
the PSA seasoning baseline $h_0$ in **both** legs (mapping M1; the floor is untouched, because it
is an empirical read that already embeds the non-rate suppression and scaling it would
double-count).

**This is an ENGINE RUN, not an analytic re-derivation.** The committed max-form run took
**379.5 s** (`runtime_s`) for 10 ladder cells plus two bisections. The additive re-solve is the
same order — roughly 6–10 minutes. **The engine is SINGLE-TENANT** (`hazard/data/floor_sweep/`):
this run must not overlap any other engine run, and the runner must say so in its header.

**Note on line numbers.** The inventory cites the T5 row at `.tex:346`; the live site is the
`tab:assembly` row at **`.tex:377`**. The inventory's number is stale.

## 2. What is already known — DECLARED, NOT PREDICTED

All read from committed artifacts during scoping, *before this spec existed*.

**The max-form solution (`scaled_null_housing_activity_results.json`):**

| floor | null(1) | central(1) | marginal | required lift | $\phi^{*}$ | marginal at root | floor-bind at root |
|---|---|---|---|---|---|---|---|
| 4.0% | 748.1850239867648 | 818.5300844066606 | 70.34506041989584 | 89.53007689804927 | **0.75625** | 3.4679508192893707 pp | 0.7564017862023238 |
| 4.991% | 724.9180585654117 | 767.5264524465003 | 42.60839388108866 | 54.228864939567394 | **0.75390625** | **0.897850936460884 pp** | **0.9444295250973784** |

**The additive endpoints (`floor_form_mixture_results.json`, $s = 1$ — production additive code
path):**

| floor | null(1) = `s1|pq0` | central(1) = `s1|pq6.5` | marginal |
|---|---|---|---|
| 4.0% | 427.7040999885527 | 513.7265922748531 | **86.02249228630046** |
| 4.991% | **341.83938974816874** | **427.54488764725437** | **85.70549789908563** |

**Feasibility, pre-computed — in the committed run's own style ("so the run is not started on a
hope").**

1. **Required lift under additive**, from the committed marginals $\times 1.272727272727273$:
   **\$109.4831720007bn** at the 4.0% floor and **\$109.0797245988bn** at the 4.991% floor —
   roughly double the max form's \$89.53 / \$54.23.
2. **But the headroom is far more than double.** As $\phi \to 0$ the volitional hazard vanishes and
   **both** forms collapse to the same limiting leg — $\max(\underline h, 0) = \underline h$ and
   $1-(1-\underline h)(1-0) = \underline h$ — so the two forms share a $\phi \to 0$ endpoint $L$.
   Headroom is $L - \text{null}(1)$, hence
   $$\text{headroom}_{\text{additive}} = \text{headroom}_{\max} + \bigl[\text{null}_{\max}(1) -
   \text{null}_{\text{add}}(1)\bigr] = \text{headroom}_{\max} + 383.08\text{bn at the 4.991\% floor.}$$
   The max form's own recorded `headroom_estimate_b` there is 74.0 and a root was found at a
   required 54.23, so the additive headroom is **on the order of \$457bn against \$109bn
   required**. This is a limit argument on committed values, **not a run**, and it is the reason
   E2 below is stated as an expectation rather than a hope.

**Nothing in scoping solved for $\phi^{*}$ under the additive form, or computed the surviving
marginal there.** Those are E2–E4.

## 3. Construction

Identical to the committed run in every respect except the floor form:

- **Mapping M1, unchanged.** `literature_hazard.baseline_hazard = lambda age, mode=None:
  lh.h0_psa(age, psa_speed=100.0*phi)`, both legs, floor untouched. The committed header's engine
  analysis (the module-level name resolved at call time; patching `PSA_SPEED` does **not** work;
  `_ORIG_PREPAY` does not bind) carries over verbatim and must be re-verified in source, not
  assumed.
- **Floor form set to additive** through the **production code path** — the same path
  `floor_form_mixture` uses for its $s = 1$ endpoint, whose equivalence to the additive mode that
  artifact already certifies (`P6_probes.max_s1_vs_additive` $\approx 1.1 \times 10^{-16}$). The
  form is **restored** at exit and the restoration asserted (the committed run's `P7_restoration`
  and the mixture run's `P_floor_mode_restored` convention).
- **Both committed floors**, 4.0% and 4.991%, the latter read live from
  `oos_identification_results.json:headline_oos_marginal.clean_floor_point_pct` and asserted
  $= 4.991$.
- **Bisection**, null leg only, tolerance \$0.05bn, $\le 10$ iterations, bracket $[0.3, 1.0]$ —
  the committed harness's parameters unchanged, **not re-tuned**. A ladder is run first to seed
  the bracket, exactly as the committed run does.
- **Disclosure carried over:** `competing_risks.py:148` calls `prepay_hazard` on the Danish
  `us_intercept` branch too, so the Danish leg simulated in the same run also carries the scaled
  baseline. Only the U.S. leg is scored.

## 4. Pre-commitments

**STOP-class:**

- **E1 — the $\phi = 1$ cells are the committed additive legs, bit-identically.** With
  $\phi = 1$, $100.0 \times 1.0$ is exactly `config.PSA_SPEED`, so the patched call is
  bit-identical to production by construction. The run must reproduce
  `floor_form_mixture_results.json`'s $s = 1$ cells **exactly**: 341.83938974816874 /
  427.54488764725437 at the 4.991% floor and 427.7040999885527 / 513.7265922748531 at 4.0%, all
  **read live from that artifact**, not from literals in the runner. A miss is an environment
  alarm and a **STOP**. This is the parity gate that ties the additive re-solve to the committed
  additive endpoint the condition names.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E2 — a root exists at both floors** (`no_root == false`, `converged == true`, residual within
  \$0.05bn). Grounded in the §2.2 headroom argument, which bounds but does not compute it.
- **E3 — the surviving marginal does not collapse.** At the additive root the surviving marginal
  lands **above +4.0 pp**, against the max form's **+0.90 pp**. The mechanism is the substantive
  claim: under max, the marginal collapses because at $\phi^{*} = 0.7539$ the floor binds in
  **94.4%** of loan-months and censors the elasticity almost entirely; **the additive form never
  censors**, so that collapse mechanism is structurally absent. **I do not know the realized value
  and this may fail.**
- **E4 — direction of $\phi^{*}$ is NOT predicted, deliberately.** Required lift roughly doubles
  while responsiveness to $\phi$ rises by much more (the additive leg's mean CPR spans
  10.41%$\to$4.99% from $\phi = 1$ to $\phi = 0$, against the max leg's 5.87%$\to$4.99%), and the
  max form's own $\phi$-response is strongly non-linear under censoring. **Either direction lands
  and neither is scored as a miss.** Recording a direction here that I cannot derive would be a
  guess dressed as a pre-commitment.

## 5. Gates

- **P0** sha pins on `hazard/scaled_null_housing_activity.py`, `hazard/literature_hazard.py`,
  `hazard/competing_risks.py`, `hazard/config.py` and both source artifacts, asserted live.
- **P1 (the additive-endpoint parity gate)** — E1 above, read live from
  `floor_form_mixture_results.json`.
- **P2 (the max-form parity gate)** — the four committed max-form legs still reproduce from the
  committed artifact's own values (748.1850239867648 / 818.5300844066606 / 724.9180585654117 /
  767.5264524465003), read live from `scaled_null_housing_activity_results.json`. This certifies
  the environment before the form is switched.
- **P3 (baseline identity)** — the patched baseline at $\phi = 1$ equals `lh.h0_psa` and
  `lh.baseline_hazard` on the age grid 0–360 to 0.0, the committed `P5_baseline_identity` check.
- **P4 (form restoration)** — the floor form is restored at exit and asserted, and the max-form
  bind-share anchors (`4.991|6.5` = 0.6881875607501289, $n$ = 1683124) still reproduce afterwards.
- **P5 (anchor integrity)** — the ratio is $0.56/0.44 = 1.272727272727273$ recomputed, not
  hard-coded, and the floor is read live and asserted $= 4.991$.
- **W1** — writes **only**
  `hazard/data/scaled_null_housing_activity_additive_results.json`; refuses to overwrite a
  differing file; **never rewrites `scaled_null_housing_activity_results.json` or
  `floor_form_mixture_results.json`**; edits no `.tex` file; never edits `config.py` persistently.
- **SINGLE-TENANCY** — the runner asserts no other engine run is in flight before touching
  `hazard/data/floor_sweep/`, and fails closed if it cannot establish that.

## 6. Landing rules, per branch

- **Branch A — gates pass, root found at both floors, E3 holds.** Land the additive re-solve.
  The `tab:assembly` row at `.tex:377` is marked **form-conditional** with both numbers: the max
  form's $+0.9$ at $\phi^{*} = 0.754$ and the additive form's realized marginal at its own root.
  §V.E's introducing sentence, which already says "Holding the production hard-maximum form … 
  fixed", gains the additive counterpart. New gate + test battery; `tab:runindex` row.
- **Branch B — gates pass, root found, E3 misses** (the additive marginal collapses too). **Land
  anyway**, with the pre-committed +4.0 pp bar quoted beside the realized value and the miss named.
  This outcome is *informative against my own reasoning*: it would mean the collapse is not
  censoring-driven, which bears directly on the paper's form-fork discussion in §VII.F.
- **Branch C — gates pass, NO ROOT at one or both floors.** **Land the no-root as the answer.**
  It says the additive form cannot be calibrated to Aladangady's 44% share within the achievable
  range of $\phi$, which is itself a form-conditional finding. The row is marked accordingly and
  the achievable-lift ceiling is reported.
- **Branch D — P0–P5 or E1 fails.** Land nothing from the run. Commit the runner output and a
  failure record, **then take Branch E**.
- **Branch E — THE ZERO-COST FALLBACK, available at any time without running anything.**
  Append **`(max form; not re-run additive)`** to the Status cell of the `tab:assembly` row at
  `.tex:377`, whose current text is

  > `Housing-activity-scaled baseline (Aladangady-anchored) & $+0.9$ & below the interval &`
  > `scaled-null variant; upward-bias entry, root $\phi^{*} = 0.754$`
  > `(run \texttt{scaled\_null\_housing\_activity}) \\`

  **Zero new literals. Zero gate changes** — verified: no gate in `tools/liveness_gates.py` and no
  test in `tests/` references `scaled_null_housing_activity`, the row, or the $0.754$ root, so the
  edit cannot break the suite. This branch discharges the condition's *stated* minimum ("the row
  must be marked form-conditional either way") at essentially no cost, and is the correct landing
  if the engine is unavailable, contended, or Eugene declines the run.

  **Branch E is a floor, not a substitute.** Taking it leaves C-77 recorded as satisfied-by-marking
  with the run still open, not as satisfied-by-measurement.

## 7. Scope limits this spec commits to stating

1. **The anchor is a share, not a magnitude.** `aladangady2024` gives 44%; the manuscript carries
   no external decline magnitude, so $\phi$ is calibrated **internally** against the paper's own
   objects. That is a calibration convention, not an external validation, and it stays labelled as
   one under every branch.
2. **The Danish leg carries the scaled baseline too** and is not scored — the committed run's
   disclosure, preserved.
3. **This does not resolve the form fork.** It marks one row as form-conditional. The max-vs-
   additive question stays open and stays the paper's largest, and no branch above may be written
   as settling it.
4. **The mapping is M1 and stays M1.** M2/M3/M4 were enumerated and rejected in the committed
   run's header for stated reasons; re-opening the mapping choice under a different floor form
   would change the estimand and break comparability with the max-form row this run exists to sit
   beside.
