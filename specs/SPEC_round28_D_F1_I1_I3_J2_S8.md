I have verified every engine, artifact, and manuscript site. Below is the deliverable.

---

# Six run specs — round 28 (WP-D, F1, I1, I3, J2, S8)

**Repo state verified against:** worktree `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/paper-v18-review-plan-5b7b5e`, manuscript `paper/v18/revised_paper_v18.tex` (**1,407 lines** — note: the brief's "tex 1601–1622 form discussion" does not exist; the form discussion is **line 588**, with the level/marginal restatement at **line 605**).

## 0. Cross-cutting facts every spec below depends on (all verified)

**Production convention (the "held-at-production" list, common to all engine-run specs).** Committed 75k loan sample `hazard/data/loan_sample.parquet` (present in worktree); `RNG_SEED = 42`; regime tuple `("US","Danish")` with per-regime seed offsets; **one** shared macro frame fetched once (`macro.fetch_data` + `fetch_soma_mbs_monthly` + `build_empirical_metrics`); raw-basis scoring via `extension_risk.score_extension_risk`; `config.py` constants `FLOOR_MODE="max"`, `INVOLUNTARY_CPR_ANNUAL=0.04`, `BASELINE_MODE="psa"`, `PSA_SPEED=100.0`, `P_Q_BASELINE=0.06`, Rothstein declines `(0.055, 0.065, 0.077)` (`hazard/config.py:34,40–52`); caches not consulted (fresh microsim runs); `config.py` never edited; no `.tex` edit by any run.

**Runtime unit:** 26.8 s per microsim run (`floor_form_offwindow_results.json` `runtime_s` 535.876 / 20 runs).

**The `_ORIG_PREPAY` patching gotcha, stated once and then per-spec.** `hazard/floor_sweep.py:79` captures `_ORIG_PREPAY = competing_risks.prepay_hazard`; `_run_scored` (`floor_sweep.py:120–147`) installs `_tallying_prepay(tally)` over `competing_risks.prepay_hazard`, and that wrapper **delegates to `fs._ORIG_PREPAY`** (line 102). A variant hazard must therefore be installed at `fs._ORIG_PREPAY`, not at `competing_risks.prepay_hazard` — the seam `moving_share_bracket.py:169–177` occupies. Two consequences verified in the source:

1. The tally computes `h_vol` by re-calling `_ORIG_PREPAY` with `literature_hazard.INVOLUNTARY_CPR_ANNUAL = 0.0` (`floor_sweep.py:103–108`); `cpr_annual_to_monthly_hazard(0.0)` **clips to 1e-8, not 0** (`literature_hazard.py:55`). Any variant must read `lh.INVOLUNTARY_CPR_ANNUAL` **at call time** (as `moving_share_bracket.py:109` does), so it inherits both the run's floor and this convention. Do not "fix" the clip.
2. The reported `floor_bind_share` is defined as `h_vol < h_floor` against the **full** floor. Under any variant that redistributes the floor, that column is a full-floor diagnostic, **not** the variant's own censoring share, and must be relabelled or supplemented.

`competing_risks.py:148` calls `prepay_hazard` on the **Danish** `us_intercept` branch too, so any patch of that name also moves the Danish leg.

**Danish artifact gotcha.** `abm/data/refi_sweep_results.json` is the **dk_level** sweep (0% cell `gap_pathB_b = −99.90187363535358`, breakeven 0.013828 → the manuscript's "crosses zero at 1.4%"). The **production U.S.-intercept** sweep — the one behind fig:gapsweep's production curve and `+$1,038.9B` at the ceiling — is `hazard/data/danish_us_intercept_results.json`. F1 targets the latter.

**Data-location gotcha (blocking for S8 and for I1's gate G3).** Gitignored inputs are **absent from this worktree** and present only in the main checkout:

| input | worktree | main checkout `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data/` |
|---|---|---|
| `fannie_quarters/` (24 cells + manifest) | **absent (dir does not exist)** | present, 50 files |
| `cohort_month_panel_fannie.parquet` | **absent** | present (851,213 B) |
| `floor_form_offwindow/` parquets | **absent** | present |
| `loan_sample.parquet`, `cohort_month_panel.parquet`, `microsim_results*.parquet`, `no_lockin_null_results.json` | present | present |

`.gitignore:55–59` is the cause. **Any spec below that names a Fannie or off-window-parquet input must be executed in the main checkout, or the inputs copied in first.** This is a STOP-before-start check, not a mid-run discovery.

**Committed anchor values (re-verified from artifacts, not from the tex):**

| quantity | value | source |
|---|---|---|
| max form, floor 4.0%, δ=6.5 | central $818.5300844066606B, null $748.1850239867648B, marginal **+$70.34506041989584B / +9.198459770709789pp** | `no_lockin_null_results.json` |
| additive form, floor 4.0%, δ=6.5 | central $513.726592B, null $427.7041B, marginal **+$86.0224923B / +11.248472pp** | `floor_form_results.json` additive@4.0 |
| max form, floor 4.991%, δ=6.5 | null $724.9180586B, marginal **+$42.6083939B / +5.5715582pp** | `floor_form_offwindow_results.json`; `oos_identification_results.json` `headline_oos_marginal` |
| additive form, floor 4.991%, δ=6.5 | null $341.8394B, marginal **+$85.7055B / +11.2070pp** | `floor_form_offwindow_results.json` |
| Danish U.S.-intercept gap @ refi 0% | **+$61.18833737010482B** | `danish_us_intercept_results.json` `sweep[0]` |
| Danish U.S.-intercept gap @ refi 3% | **+$256.8415840324639B** | `danish_us_intercept_results.json` `sweep[1]` |
| episode gradient | realized **+4.198179219676357pp**, CI [3.5852591750975797, 4.656477952145319], implied(mid) **+0.9371125522400376**, power 0.675, T5 | `episode_confrontation_results.json` |
| Ginnie overlay off-window | marginal **+4.443419164229439pp**, `marginal_scale_vs_conventional` **0.7975182199226121** | `ginnie_overlay_offwindow_results.json` |
| vintage segments (Fannie observed, QT window) | sampled 2017–21 **4.302657826519651%**, 2022 **4.475590534559171%**, pre-2017 **5.264339724557043%**; shares 0.231 / 0.106; sensitivity **82.8 $B/pp**; benchmark **$764.7482532227002B** | `vintage_residual_bound_results.json` |
| attrition | 34,734 prepaid + 32 defaulted pre-window of 75,000; **40,234 active** | tex 966 |

**Zero-slack literal counts (indicative — governing constraint #2 requires re-derivation at execution, including and-forms):** `$+5.6$` ×21 (lines 30, 45, 57, 76, 88, 106, 233, 301, 312, 321, 324, 357, 427, 514, 590, 592, 605, 611, 676, 1253, 1389); `61.2` ×17 lines (51, 76, 82, 267, 301, 427, 458, 464, 469, 487, 572, 578, 588, 607, 623, 653, 682); `$+11.2$` ×7 lines (76, 301, 312, 330, 357, 359, 605); `$+3.5$ to $+13.1$` ×7 lines (30, 76, 301, 312, 357, 588, 595); `form-conditional` ×11 sites (30, 76, 301, 312, 316, 357, 588 ×2, 592, 595, 729); `5.61\%` ×6 (464, 487, 572, 578, 653, 1295).

**Gate collisions (`tools/liveness_gates.py`):** L413 `counter_additive` ("the additive form returns $+11.2$ points"); L470 comment (additive/Fonseca "move the marginal UP"); L489 `hull_in_abstract`; L588/597 letter span list (`"$+3.5$ to $+13.1$"`, `"$+11.2$"`, `"$+11.5$"`); L2324–2325/2414 additive κ-span 11.2208/11.2654; L3836–3842 and L4288 the `$+\$61.2$ billion` paragraph assertions; L4033–4059 form-conditional cross-check (`tex.count("$+3.5$ to $+13.1$") >= 3`, `tex.count("$+3.9$ to $+13.1$") == 0`, `tex.count("form-conditional") >= 3`); L4315 `ginnie_overlay_offwindow_results.json`; L4396–4406 episode gate asserting `"$+4.20$ CPR points" in tex`.

---

# SPEC D — mixture-form curve (`floor_form_mixture`)

## Engine entry (verified)

New script `hazard/floor_form_mixture.py`, built on machinery verified in place:
- run driver: `floor_sweep._run_scored(loans, empirical, floor, pq)` (`floor_sweep.py:120`) — sets `literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor`, installs the bind tally, runs `microsim_engine.run_qt_microsim`, scores via `extension_risk.score_extension_risk`, restores in `finally`.
- variant seam: `fs._ORIG_PREPAY = mixture_prepay` inside a `try/finally` that restores **both** `fs._ORIG_PREPAY` and `competing_risks.prepay_hazard` — the exact pattern at `moving_share_bracket.py:162–178`.
- reference forms: `literature_hazard.prepay_hazard:110–116` (`additive` → `1-(1-h_floor)*(1-h_vol)`; else `np.maximum(h_floor, h_vol)`).

**The `_ORIG_PREPAY` gotcha BINDS for this spec.**

## Parameterization

Define **s = the share of the measured floor that enters as an additive competing involuntary cause**; `1−s` remains a floor on total turnover:

```
h_add   = s * h_floor
h_floorL = (1 - s) * h_floor
if s == 0.0:   combined = np.maximum(h_floor, h_vol)                    # production max expression, verbatim
elif s == 1.0: combined = 1.0 - (1.0 - h_floor) * (1.0 - h_vol)         # production additive expression, verbatim
else:          combined = 1.0 - (1.0 - h_add) * (1.0 - np.maximum(h_floorL, h_vol))
return np.clip(combined, 0.0, 1.0)
```

with `h_vol = h0(loan_age) * exp((-beta1)*(rate_gap*100) + beta_fico*fico_z + beta_ltv*ltv_z + beta_burnout*burnout)` and `h_floor = cpr_annual_to_monthly_hazard(full_like(h0, lh.INVOLUNTARY_CPR_ANNUAL))` — read at call time.

**The endpoint branch is mandatory and is not cosmetic.** The general expression at `s=0` evaluates `1-(1-0)*(1-M)`, which is not bit-identical to `M` in IEEE-754 (round-trip error ~1.1e-16 absolute on `M ≈ 3.4e-3`, i.e. ~3e-14 relative, propagating through 1,683,124 loan-months). Without the branch, the "bit-exact" parity the brief requires is **unachievable by construction**. The branch makes the reported endpoint cells arise from the production expressions themselves.

**Grid:** `s ∈ {0, 0.1, 0.2, …, 1.0}` (11 points) × legs `{null p_q=0, central p_q=6.5}` × floors `{0.04, 0.04991}` = **44 runs ≈ 20 min** plus one macro fetch. The off-window floor is consumed from `oos_identification_results.json` `headline_oos_marginal.clean_floor_point_pct` and asserted `== 4.991` to 1e-9 (the `floor_form_offwindow.py:150–156` convention), never hard-coded.

**Orientation, stated for the record:** **s = 0 ⇒ max form; s = 1 ⇒ additive form.** Verified against the code, not asserted from the reviews. The max form is a floor on *total* turnover (involuntary movers are a subset of the voluntary hazard's movers — the reading tex 588 defends: "a minimum total turnover matching the observed 4--5\% on deep-discount cohorts where the voluntary hazard is near zero"). The additive form treats the floor as a distinct competing cause, i.e. **strictly involuntary**. So **s is the strictly-involuntary share of the floor.**

## Held at production

Everything in §0 plus: `FLOOR_MODE` is never mutated (the mixture supersedes it inside the patched hazard and `lh.FLOOR_MODE` stays `"max"` throughout — assert at start and end); `δ = 6.5` only (no band cells this round); default hazard, delinquency pipeline, burnout, covariates untouched; `moving_share_bracket`'s own `_share` global is not involved.

## Pre-committed expectations + derivation

1. **Endpoint parity (blocking, see below).**
2. **Monotone increasing in s at both floors.** Derivation: the additive channel adds hazard on the survival scale wherever the max channel would have censored it; at fixed `h_vol`, `∂combined/∂s = h_floor·[(1 − max(h_floorL, h_vol)) − (1−h_add)·1{h_floorL > h_vol}] ≥ 0`, and the *central* leg is censored in a strictly larger set of loan-months than the null leg (bind shares 0.363 central vs 0.143 null at floor 4.0%, `moving_share_bracket_results.json`), so the central leg gains more than the null leg at every s.
3. **Interior values.** At the off-window floor the curve runs from **+5.5716pp to +11.2070pp** (a 5.635-point span); at the in-sample floor from **+9.1985pp to +11.2485pp** (2.050 points). The off-window curve should be **convex-to-concave but nowhere decreasing**; no shape beyond monotonicity is pre-committed.
4. **Floor-anchor preservation (asserted, reported).** At `h_vol = 0` the mixture returns `h_floor − s(1−s)h_floor²`, so the deep-discount calibration anchor is preserved to second order. Computed maxima at s = 0.5: floor 4.0% → `h_floor = 0.00339605`, defect `2.883e-6` = **0.0849%** of the floor hazard; floor 4.991% → `h_floor = 0.00425671`, defect `4.530e-6` = **0.1064%** (an effective annual floor of 4.9856% vs 4.991%). **Run check: max relative floor deviation across the grid < 0.15%; report the realized value per cell.** This is what licenses the claim that the curve varies the *form* and not the *calibration*.
5. **Level cost travels with the curve.** Each cell must also report `share_pct` (the central leg's recovery). At s=1 off-window the additive central recovers **55.9%** against the max form's 91.3% (tex 588, verbatim). Reporting the recovery beside the marginal at every s is what converts R1-W3's complaint ("the retention argument is aggregate fit … in the same section that opens by declaring aggregate levels unidentified") into a displayed trade-off rather than a hidden one.

## The "well under half" → s mapping ⚖ — READ THIS BEFORE LANDING

tex 249 states the **strictly-involuntary share is "plausibly well under half."** Under the orientation verified above, that maps to **s < 0.5** — i.e. the honest interior region is roughly **s ∈ [0.2, 0.45]**, *not* s ≈ 0.5–0.6.

The brief's "s ≈ 0.5–0.6" follows **R1's complementary labelling** (REVIEW2 finding #5: "the max form (share=1) and additive form (share=0)"), in which R1's `share` = the floor-on-total share = **1 − s**. The two statements agree on the *physics* and disagree on the *symbol*. Both cannot appear in the manuscript.

**Coordinator action:** the curve is symmetric in presentation — plot/table it over the full grid and let Eugene choose the symbol. But the **named interior value must be stated in the paper's own semantics**, and under the paper's own sentence that is `s < 0.5`. Recommended named point: **s = 0.4** (an upper edge of "well under half", conservative in the direction that keeps the headline low), with s = 0.25 reported beside it. Naming s = 0.5–0.6 requires either flipping the symbol to R1's or contradicting tex 249. **⚖ Eugene signs the symbol and the named point; the spec does not.**

## Landing rule per branch

**Decision already taken (PLAN Decision record item 5): "mixture curve RUNS, headline anchor unchanged this round, interior value named in form-conditionality statements."** The headline `$+5.6$` (×21 sites) and the binding interval `[+2.8,+8.7]` do **not** move under any branch below.

**Branch PASS (parity holds, curve monotone at both floors).**
- The curve becomes the form-dimension exhibit. It lands as a new table/figure in **§V.C at line 588**, immediately after the sentence ending *"…the near-coincidence defense of the max form at the deep-discount anchor does not extend to the shallow-gap off-window anchors."*
- The `form-conditional hull` language is **kept, not deleted** (gate L4050 requires `tex.count("$+3.5$ to $+13.1$") >= 3` and `tex.count("form-conditional") >= 3`), and gains one clause at each of the four *substantive* hull sites — **tex 30 (abstract), 76 (tab:headline), 301, 588** — of the form: *"…a form-conditional hull of $+3.5$ to $+13.1$ points, whose two endpoints are the endpoints of a mixture curve in the floor's strictly-involuntary share; at the share the floor's own semantics support the curve reads $+X.X$ points."* The hull sites at 312/316/357/592/595/729 are cross-references and take no new clause.
- **tex 588** gains the derivation sentence naming the orientation explicitly (s=0 ≡ max ≡ total-turnover reading; s=1 ≡ additive ≡ strictly-involuntary reading) and the floor-preservation figure (0.11% max).
- **tex 249** gains one clause tying its "well under half" concession to the named s.
- Gate work: extend the L4033–4059 form-conditional cross-check to require the curve's artifact and the named interior value; **do not** weaken `tex.count("$+3.9$ to $+13.1$") == 0`.

**Branch STOP-1 (any endpoint parity miss > $0.01B).** No landing. Write the artifact with `status: "GATE_FAILURE"`, report, stop. A miss at the endpoints is a wiring or upstream-data alarm and invalidates every interior cell.

**Branch STOP-2 (non-monotone at either floor, beyond 1e-9 $B tolerance).** No landing. `status: "CHECK_FAILURE"`. A non-monotone curve contradicts the derivation in expectation (2) and means the mixture is not the object specified. Report the offending cells; do not reinterpret.

**Branch STOP-3 (floor deviation ≥ 0.15% at any cell).** No landing of interior cells; endpoints may still be quoted (they are the committed forms). The curve would be re-calibrating the floor, not varying the form.

## Parity checks (blocking, run before any interior cell is interpreted)

| id | check | target | tol |
|---|---|---|---|
| P1 | s=0, floor 4.0%, δ=6.5, marginal_b | 70.34506041989584 | **1e-6 $B (bit-exact gate)**; > 0.01 = STOP |
| P2 | s=0, floor 4.0%, null trapped_b | 748.1850239867648 | as P1 |
| P3 | s=1, floor 4.0%, marginal_b | 86.0224923 | as P1 |
| P4 | s=0, floor 4.991%, marginal_b | 42.6083939 | as P1 |
| P5 | s=1, floor 4.991%, marginal_b | 85.7055 (`floor_form_offwindow_results.json` rows→4.991→additive→band["6.5"].marginal_b) | as P1 |
| P6 | algebraic identity probe | `max abs(mixture(s=0) − prepay_hazard@max)` and `max abs(mixture(s=1) − prepay_hazard@additive)` on the `moving_share_bracket.probe_identity` grid (10,000 points, `rng 42`, age 1–360, gap −0.05..+0.01, burnout 0–3, fico_z/ltv_z ±3) | **0.0 exactly** (branch equality) | exact |
| P7 | continuity probe | `max abs(general_expression(s=ε) − branch(s=0))` at ε=1e-12 | < 1e-15 | — |

A parity miss in `(1e-6, 0.01]` is a **soft alarm**: report as upstream float/library drift, do not land silently.

## Artifact

`hazard/data/floor_form_mixture_results.json` (frozen, committed after the run).
Fields: `mode`, `status ∈ {OK, GATE_FAILURE, CHECK_FAILURE}`, `spec` (verbatim string incl. the orientation sentence), `parity_gates` (P1–P7 with got/want/diff/pass), `parity_gates_all_pass`, `floor_anchor_preservation` (per-cell `max_rel_floor_deviation`, `max_over_grid`), `monotonicity` (per-floor ordered list + `pass`), `cells`: keyed `"{floor_pct}|{s}"` → `{floor_annual_cpr_pct, share_s, null_trapped_b, central_trapped_b, central_share_pct, null_share_pct, marginal_b, marginal_pp, floor_bind_share_fullfloor_diagnostic, mixture_censoring_share}`, `named_interior` `{s, marginal_pp, marginal_b, central_share_pct}`, `runtime_s`.

## Must NOT change

`config.py`; `literature_hazard.prepay_hazard` (the production function itself); `FLOOR_MODE` (assert `== "max"` at exit); the headline `$+5.6$` at all 21 sites; `[+2.8, +8.7]`; the hull `$+3.5$ to $+13.1$` and its ≥3-count; `moving_share_bracket_results.json`; `floor_form_results.json`; `floor_form_offwindow_results.json`; the `floor_bind_share` definition in `floor_sweep.py`.

## ⚖ flags

1. **The s-symbol and the named interior point** (above) — Eugene signs.
2. Whether the curve **replaces** or **sits beside** the hull language at tex 30/76. Recommendation: beside (gate L4050 and the abstract's 226-word pin both argue for beside; replacing costs an abstract recount).
3. Whether to report the central-leg **recovery share** alongside the marginal at every s. Recommendation: yes — it is the honest price of the upper curve and answers R1-W3 directly; it is also the one thing that makes s>0.5 visibly costly.

---

# SPEC F1 — Danish fine-grid refinance-in-place sweep (`danish_refi_finegrid`)

## Engine entry (verified)

`hazard/danish_us_intercept.py` — the production U.S.-intercept anchor run. Its `SWEEP` (line 81) is `np.linspace(0, 0.18, 7)`; the fine grid replaces that list only. Mechanism verified: `set_danish_moving_anchor("us_intercept")` (line 98) → `common/berger_calibration.set_us_transplant_refi(refi)` (line 144) → `run_qt_microsim` → `competing_risks.py:141–166` reads the module global inside `danish_refi_in_place_cpr_annual`, combines on the survival scale `h_prep = 1-(1-h_move)(1-h_refi)` → `shared_layer_scoring.score_on_shared_layer` → `institutional_gap_b`.

**The `_ORIG_PREPAY` gotcha does NOT bind** — `danish_us_intercept.py` calls `run_qt_microsim` directly and patches no hazard. (`competing_risks.py:148` does call `prepay_hazard` on the Danish branch, but nothing here patches that name.)

**Location:** runnable in the worktree (no Fannie or off-window-parquet inputs).

## Parameterization

`SWEEP = [0.0000, 0.0025, 0.0050, …, 0.0300]` — **13 cells, 0.25% steps**, U.S.-intercept anchor, production convention otherwise. One microsim per cell (both regimes in one call) ≈ **13 × 26.8 s ≈ 6 min**, plus the point run and two FRED/SOMA fetches. Both the `finally` restores at lines 163–167 (`set_us_transplant_refi(0.0)`, `set_danish_moving_anchor("dk_level")`, tmp parquet unlink) are retained verbatim.

**Optional extension cell ⚖ (beyond the brief; costs one run, ~27 s):** a single cell at the **realized-implied anchor, refi = 22.4%/yr**, reported in the artifact only, never in the fine-grid band. See the RULE-A′ arithmetic below for why it matters.

## Held at production

§0 list, plus: U.S. leg untouched (the anchor changes only the Danish branch); shared-accounting-layer gap on the Table 1 convention (`US − DK`); `PUBLISHED_US_SHARED_PCT = 97.9` gate retained.

## Pre-committed expectations + derivation

- Gap is **positive and strictly increasing** at every cell (forced by construction — tex 464: the zero-gap Danish leg must prepay faster, and refi only adds; the manuscript already says "I retain both as wiring checks and read neither as evidence").
- Local slope from the committed grid: `(256.8415840 − 61.1883374)/3 = **$65.218B per CPR point**` — reproducing REVIEW2 finding #7's "≈$65B per CPR point" exactly.
- Predicted band edges (linear on the committed grid, to be replaced by the run): 0–1% ≈ **[+$61.2B, ≈+$126B]**; 0–3% = **[+$61.2B, +$256.8B]**.

## The RULE-A′ anchor — an arithmetic the landing must confront

`SPEC_danish_redemption_validation_2026-07-28.md` §Execution log and `hazard/data/danish_external_validation/README.md`: **R = 26.42%/yr** on FK × coupon ≤2%, cross-check exact (2m DKK on a 1,202bn opening stock), **extraordinary lower bound 22.4%/yr** after the pre-committed 4pp scheduled allowance; stock 1,202.3 → 747.2bn DKK; verdict **RULE-A′** (>2× the 12% derived-space threshold).

**The realized-implied anchor (22.4%/yr) lies ABOVE the entire fine grid AND above the rejected partial-equilibrium ceiling (18%, `PE_CEILING`).** At the committed 18% cell the gap is **+$1,038.9B**; extrapolating the 15→18% segment slope ($44.0B/pt) to 22.4% gives ≈ **+$1,230B**. A band quoted over 0–3% therefore **cannot be described as bounded above by the realized anchor** — the anchor is off the top of it.

Three confounds travel with the anchor and must be stated wherever it is used (they are the spec's own ex-ante caveats, §Caveats 1–4, plus one the spec did not name):
1. gross bond-level measure — conversions bundle in (on the *hazard* question conversion **is** the delivery-option exercise, which is why the spec accepted it);
2. stock includes non-household collateral;
3. environment-matched, not book-matched;
4. **(name this one explicitly)** the realized rate is Danish borrowers under **Danish** tax, while the model's ≈0 is a **U.S.-transplant GE** estimate whose whole content is the tax attenuation. The realized figure is therefore an **upper anchor on the transplant, not an estimate of it** — and R2-W5d's correction (COD income at ordinary rates under IRC §61(a)(11), not the 15% capital-gains rate in `berger_calibration.THETA_G_US`) makes the attenuation *larger*, i.e. pushes the transplant value *down* from that anchor.

## Landing rule per branch

**Band presentation is MANDATORY (RULE-A′ dispositions (i)–(iii) are already active). There is no branch in which the 0% point survives as the sole Danish headline.**

**Branch PASS (parity holds, monotone).**
- **tab:danish (tex 481–488), row d** — `Berger hybrid, U.S.-intercept` gap cell changes from `$+\$61.2$B` to the band. Note [d] (tex 495) gains: the sweep is no longer described as a sign check but as the reported range, and the ≈0 pin's contradiction is stated.
- **tex 464** (§V.C body, the `+$61.2$ billion` sentence and the "$\approx$0" pin) — the pin sentence is replaced: *"the general-equilibrium best estimate of a negligible refinance-in-place contribution"* → the band + the realized-data contradiction (RULE-A′ disposition (iii)), citing the frozen artifact and window.
- **fig:gapsweep caption (tex 469)** — "the Berger et al. general-equilibrium best estimate (≈0, marked)" is restated as one anchor among the swept range, with the realized-implied anchor noted as lying above the plotted ceiling.
- **Zero-slack cascade:** 17 lines carry `61.2` (51, 76, 82, 267, 301, 427, 458, 464, 469, 487, 572, 578, 588, 607, 623, 653, 682) and 6 carry `5.61\%` (464, 487, 572, 578, 653, 1295). Re-derive **including and-forms** before the first edit. `liveness_gates.py:3836–3842, 4288` assert `"$+\$61.2$ billion"` inside specific paragraphs — those gates move in the same commit as the tex.
- **The Danish/marginal near-equality claim.** tex 464 states the rule-only gap and the in-sample marginal are "one object measured on two accounting legs ($+\$61.2$ billion here … $+\$70.3$ billion as the U.S.-leg marginal)", and `danish_offwindow_floor` gives +$28.2B at the off-window floor. **Under a band presentation the equality reading is retired, not re-pointed** — the 0% cell is one edge of a range, and an equality with one edge is not an equality. Draft: *"at the 0\% edge of that range the rule-only gap and the in-sample marginal nearly coincide, which is a property of that edge and of the demoted calibration, not of the counterfactual."*

**Branch STOP-A (0% cell misses +$61.18833737010482B by > $0.01B).** STOP. This is an upstream data-revision alarm (FRED/SOMA), not a spec failure. Report, land nothing.
**Branch STOP-B (3% cell misses +$256.8415840324639B by > $0.01B, or any cell non-monotone).** STOP. Same disposition.
**Branch STOP-C (`parity_gates_all_pass` false on the U.S. legs).** The script already raises `SystemExit` (lines 205–209); honour it.

## ⚖ How far up the grid the quoted band runs — spec both, Eugene picks

| variant | quoted band | argument for | argument against |
|---|---|---|---|
| **V1: 0–1%** | +$61.2B to ≈+$126B | closest to the committed row; the bracketing anchor crosses zero at 1.4% (dk_level), so 0–1% is the interval inside which the *other* anchor has not yet flipped | quoting a band that stops 21 points below the realized anchor invites the exact objection R3-W1 raised; requires an explicit sentence saying why the band stops there |
| **V2: 0–3%** | +$61.2B to +$256.8B | the full fine grid; matches the "no production-anchor cell between 0% and 3%" complaint verbatim; the 3% edge reconciles with the committed sweep cell | a >4× range on the paper's cleanest contribution; §V.C's magnitude claim ("$61.2 billion, 8.0\% of the benchmark, is the quantity the recalibration actually delivers") cannot survive unrestated |

**Both variants must carry the same sentence:** the realized-implied anchor (22.4%/yr, with its four confounds) lies **above** the quoted band and above the rejected PE ceiling, so the band is a reporting choice about where to stop, not a bound derived from the data. Recommendation: **V2**, with the 18% ceiling cell and the 22.4% anchor both named in the text — V1 reads as choosing the flattering stopping point once the external result is in the paper. **Eugene signs.**

## Parity checks

| id | check | target | tol |
|---|---|---|---|
| G1 | U.S. standalone leg | 818.5300844066606 | < 0.01 $B (script's own) |
| G2 | U.S. shared layer | 97.9% | < 0.25pp (script's own) |
| G3 | sweep cell refi=0.0 `institutional_gap_shared_b` | **61.18833737010482** | 1e-6 $B bit-exact gate; > 0.01 STOP |
| G4 | sweep cell refi=0.03 `institutional_gap_shared_b` | **256.8415840324639** | as G3 |
| G5 | monotone increasing over the 13 cells | — | 1e-9 $B |
| G6 | `mean_danish_cpr_pct` at refi=0 | 5.613626373336359 | 1e-6 pp |

## Artifact

`hazard/data/danish_refi_finegrid_results.json`. Fields: `mode`, `status`, `spec`, `anchor: "us_intercept"`, `grid_pct`, `parity_gates` (G1–G6), `parity_gates_all_pass`, `point` (as in the committed artifact), `sweep`: per cell `{refi_inplace_cpr, gap_hybrid_us_intercept_b, danish_trapped_shared_b, mean_danish_cpr_pct}`, `band_0_1_b`, `band_0_3_b`, `slope_b_per_cpr_point`, `realized_implied_anchor` `{value_pct: 22.4, source: "hazard/data/danish_external_validation/results_refinement.json", R_pct: 26.42, allowance_pp: 4.0, confounds: [...], above_grid: true, above_pe_ceiling: true}`, optional `cell_at_realized_anchor`, `runtime_s`.

## Must NOT change

`common/berger_calibration.py` constants (including `THETA_G_US = 0.15` — R2-W5d's tax correction is a **separate wording item under WP-F3**, not a parameter change in this run; changing it here would silently move the Danish leg); `_DANISH_MOVING_ANCHOR` default (`"dk_level"`, restored in `finally`); `abm/data/refi_sweep_results.json`; the committed `danish_us_intercept_results.json` (write a new file); the U.S. leg's committed values; `fig4_institutional_gap_sensitivity.png` unless the figure is regenerated deliberately (`figures/make_figures.py:243` reads the **dk_level** artifact — regenerating fig4 from the new file would silently change the *other* curve too: **check before touching the figure**).

---

# SPEC I1 — within-stratum episode confrontation (`episode_confrontation_within`)

## Engine entry (verified) — and one hard structural finding

`hazard/episode_confrontation.py`. Verified capabilities: it builds `df` from `matched_depth_reconciliation.build_panel()` (`episode_confrontation.py:633`) and attaches `stratum = build_stratum_id(vintage, coupon, fico_bucket, ltv_bucket)` (lines 634–638; `stratum.py`). The panel therefore carries **`vintage`, `coupon`, `fico_bucket`, `ltv_bucket`, `mean_loan_age`, `exposure_upb`, `prepaid_upb`, `reporting_period`** as separate columns. **No engine run** anywhere (the model counterpart is analytic, lines 38–57). The `_ORIG_PREPAY` gotcha does **NOT** bind.

**Structural finding the coordinator must absorb before writing any wording:** gap buckets are assigned **per stratum** from the stratum's exposure-weighted window-mean gap (lines 668–678), and `stratum` **contains coupon**, while `gap = coupon − market_rate`. **Every stratum therefore lives in exactly one bucket by construction.** A "within-stratum gradient" in the literal sense is **not computable, ever** — not for lack of data, but because the conditioning set and the treatment are the same variable. Any spec that says "re-run within the vintage×coupon×FICO×LTV cells" without saying this is specifying an empty run.

What the three reviewers are actually asking for is **composition control**: remove the credit/vintage differences between the shallow and deep buckets that tex 292 names as the confound ("credit composition, within-window refinancing on the high-coupon shallow buckets, residual seasoning past the age cut"). That is computable, on the axes of the stratum id **other than coupon**.

## Parameterization — three limbs, all on the existing panel

Define the **composition cell** `c = (vintage, fico_bucket, ltv_bucket)` — the stratum id with the coupon dimension removed.

- **Limb A (PRIMARY): composition-standardized gradient.** Direct standardization in the template already used and disclosed in this paper — `floor_uncertainty.py:478–521`, `part_b_age_standardization`, the run behind tab:assembly's "84% imputed weight" row. Reweight the deep bucket's cells to the shallow bucket's composition-cell weight vector; where a cell has no deep-bucket support, impute by ratio-scaling from the nearest populated cell **and report the imputed weight share**, exactly as `floor_uncertainty.py:493,499,514` does. Statistic: `CPR_shallow − CPR_deep_standardized`, with the joint stratum-cluster bootstrap (`joint_gradient_bootstrap`, imported verbatim, 1000 reps, seed 42).
- **Limb B: exact within/between decomposition.** Decompose the committed `+4.198pp` into (i) the part attributable to differences in composition-cell mix between endpoint buckets and (ii) the part surviving inside common cells. Always computable (it is an identity), so it never degenerates. This is the number that adjudicates the defence.
- **Limb C (SECONDARY, identified by construction): stratum-fixed-effects within estimator.** Regress the monthly SMM on the monthly gap with stratum fixed effects over the 40-month window, exploiting **time** variation in `market_rate` inside each stratum. Report the implied CPR-per-point response with stratum-clustered SE. Confounds named ex ante: within-stratum gap variation is collinear with calendar time, so seasoning and seasonality load onto it; this limb is reported, never primary.

**Feasibility gate FG (evaluated BEFORE any outcome is read, disposition fixed now).** From `exposure_upb` and cell counts **only** — `prepaid_upb` is not touched until FG resolves (the `episode_confrontation.py:102–110` ex-ante-inspection convention). Report: the number of composition cells carrying **both** endpoint buckets, their share of the shallow bucket's exposure, and their stratum counts.

The risk is concrete and must be sized before the run is interpreted: the primary selection's shallow endpoint B1 `[-1,0)` has **35 strata, 1.08% exposure, mean coupon 6.02%**; the deep endpoint B4 `<=-3` has **52 strata, 16.38% exposure, mean coupon 3.37%** (all from `episode_confrontation_results.json`). A 6.02% coupon and a 3.37% coupon in a **2017–2021** Freddie sample are 2018–19 and 2020–21 originations respectively — so B1 and B4 may occupy **nearly disjoint vintages**, and vintage-blocked overlap may be thin or empty.

- **FG-1:** common-cell coverage ≥ 30% of shallow-bucket exposure **and** ≥ 10 common cells → Limb A runs on `(vintage, fico_bucket, ltv_bucket)`.
- **FG-2:** coverage < 30% → Limb A **falls back to `(fico_bucket, ltv_bucket)` only** (drop vintage), and the vintage axis is handled by reporting Limb B's vintage component separately. Flag `standardization_axis: "fico_ltv_only"`.
- **FG-3:** even FG-2 fails (< 30% / < 10 cells) → Limb A is `NOT_COMPUTABLE`. **This is a landing, not a failure** (see branch (c)).

Runtime < 10 min (one FRED fetch, no engine runs). Deterministic, seed 42 throughout.

## Held at production

Panel conditioning identical to the committed run: window `202206..202509` (40 months, asserted), `coupon>0 & exposure_upb>0`, gap on the calendar-month FRED ME-mean, buckets `[-1,0)/[-2,-1)/[-3,-2)/<=-3` with `gap≥0` excluded, primary seasoning cut `age0 ≥ 24`, endpoint support rule `≥1%` exposure **and** `≥10` strata, pooled dollar SMM → `CPR = 1-(1-SMM)^12`, cumulative `1-(1-SMM)^40`, analytic model counterpart with covariate multiplier 1. Gates G0–G4 of the committed script run **unchanged and first**.

## Pre-committed expectation

**None on the outcome — this is the test the paper lacks, and the review says so explicitly.** The only pre-committed quantities are FG's thresholds, the parity targets, and the branch map. Committed reference values the run must reproduce: realized `+4.198179219676357`, CI `[3.5852591750975797, 4.656477952145319]`, implied(mid) `+0.9371125522400376`, power 0.675, B2-vs-B4 `+2.414104180240706`, verdict `T5`.

## Landing rule per branch

Let `G_std` = Limb A's standardized gradient with 95% CI, and `G_model = +0.937`.

**(a) Gap persists — `G_std` CI excludes `G_model` from above.** The composition-confounding defence at tex 292 falls as stated. tex 292's closing sentence — *"I therefore read the cross-section as a signed, significant, composition-confounded level gradient, consistent with lock-in operating but unusable as a measurement of its size"* — is replaced by the tested version, drafted here for Eugene's signature:

> *"Standardizing the deep bucket to the shallow bucket's [vintage ×] FICO × LTV composition leaves the gradient at $+X.XX$ points (95\% CI $[\cdot,\cdot]$, imputed weight share $Y\%$), against the production hazard's implied $+0.94$: the excess is not composition in the dimensions the panel can hold fixed. What remains unresolved is within-window refinancing on the high-coupon shallow buckets, which no field in this design separates from moving."*

The finding enters **tab:assembly (tex 313–334)** as an **UPWARD** entry — the realized cross-section exceeds the model's implied gradient by ~4.5×, which points the same way as the additive form and the Fonseca anchor. **⚖ posture-adjacent: this changes what the assembly contains and therefore what the retired-posture paragraph can say. Direction drafted; Eugene signs.** Note the honest limit that must ride along: the gradient is a *cross-sectional level* object and the marginal is a *dollar* object; the entry is directional, not a re-estimate, and must be labelled so in the `Status` column ("directional; not a marginal re-estimate").

**(b) Gap closes materially — `G_std` CI contains `G_model`, or `G_std` falls below half the raw `+4.198`.** The defence is **vindicated and stated as tested**. tex 292's "composition-confounded" survives, upgraded from assertion to result: *"…and the confound is measured: standardizing to common [vintage ×] FICO × LTV cells moves the gradient from $+4.20$ to $+X.XX$ points."* No assembly row. `liveness_gates.py:4396–4406` (which asserts `"$+4.20$ CPR points" in tex`) is **extended, not replaced** — `+4.20` stays as the raw number.

**(c) `NOT_COMPUTABLE` (FG-3).** Land the negative result, which is itself the answer three reviewers asked for: *"The within-stratum control this exhibit needs is not identified in this panel: the gradient axis (coupon) and the vintage axis are nearly collinear in a 2017--2021 sample, so the shallow and deep buckets share $Z\%$ of composition-cell exposure --- too little to standardize. The confound is named, not measured, and the exhibit stays declined on that basis."* Reported at tex 292 with the coverage number. No assembly row, no gate change beyond the artifact reference.

**(d) Wrong sign / Limb A negative CI.** STOP. Report, diagnose, land nothing — the same disposition as the committed script's T4.

**STOP-E:** any of G0–G4 fails, **or** `cohort_month_panel_fannie.parquet` is absent (G3 consumes it — **absent in this worktree**; run in the main checkout or copy it in). The script's `_fail_out` already halts; honour it.

## Parity checks

G0 production constants; G1 E3 pooled Freddie velocity `-0.07438857974396679` (n=39) < 1e-9; G2 six per-cohort lag-0 velocities < 1e-9; G3 Fannie pooled SMM anchor `4.302657826519651%` ≤ 1e-6 pp; G4 `floor_uncertainty` R2 read `4.990624060575566%`, n=137, clusters=31 ≤ 0.001pp. **Plus new:** G5 — the committed raw gradient, CI, implied gradient, and power reproduce the frozen artifact to 1e-9 / 1e-3 (power is a mean over 200 permutations at fixed seed, so exact reproduction is expected; a miss is an environment alarm).

## Artifact

`hazard/data/episode_confrontation_within_results.json`. Fields: `mode`, `status`, `spec`, `parity_gates` (G0–G5), `feasibility_gate` `{common_cells_n, shallow_exposure_covered_share, deep_exposure_covered_share, branch: FG-1|FG-2|FG-3, standardization_axis}`, `limb_a` `{standardized_gradient_pp, ci95_pp, se_pp, imputed_weight_share, per_cell_table}`, `limb_b` `{total_pp, between_composition_pp, within_composition_pp, identity_residual}`, `limb_c` `{coef_per_100bp, se, n_strata, n_obs, r2_within, confounds_note}`, `committed_reference` (the five frozen values), `verdict` `{branch: a|b|c|d, sentence}`, `runtime_s`.

## Must NOT change

`episode_confrontation.py` and its committed artifact (write a new script + new artifact; import its machinery); `matched_depth_reconciliation.build_panel`; `floor_uncertainty.cluster_bootstrap_cpr`; the bucket rule, age cut, and support rule; `+4.20`, `[+3.59,+4.66]`, `+0.94`, `0.68`, `p = 0.005` at tex 292 and at `liveness_gates.py:4396–4406`.

## ⚖ flags

1. **Branch (a)'s assembly entry is posture-adjacent** — it is the first *upward* entry sourced from realized data, and the assembly is the object the retired-posture decision rests on. Wording drafted above; Eugene signs.
2. Whether Limb C is reported at all. Recommendation: yes, in a tablenote — it is the estimator practitioners will ask about, and reporting a near-zero within-stratum response *strengthens* the paper's own monthly-timing nulls rather than weakening anything.
3. Whether the standardization axis includes vintage. Recommendation: let FG decide mechanically; do not choose after seeing the outcome.

---

# SPEC I3 — survival-selection attenuation sensitivity (`attenuation_sensitivity`)

## Engine entry (verified)

`hazard/floor_sweep._run_scored(loans, empirical, floor, pq)` at the two floors, varying **`p_q_shock_pct` only**. No hazard patching. **The `_ORIG_PREPAY` gotcha does NOT bind** (the tally wrapper is active but harmless and its bind column stays meaningful, since the floor is untouched).

**How β₁ is attenuated without touching the engine.** `microsim_engine.run_qt_microsim:100` computes `beta1 = rothstein_beta1(p_q_shock_pct/100.0)`, and `literature_hazard.rothstein_beta1` (lines 32–44) is monotone and invertible. For a target attenuation `a`, solve numerically for `δ'` such that `rothstein_beta1(δ') = a · rothstein_beta1(0.065)`, pass `p_q_shock_pct = 100·δ'`, and **assert** `|rothstein_beta1(δ') − a·β₁_mid| < 1e-12`. Scaling `δ` directly is **not** the same as scaling `β₁` (`β₁(0.055)/β₁(0.065) = 0.0577/0.0686 = 0.841` vs `δ` ratio `0.846`); the invert-and-pass route is exact and uses the production knob.

## The derivation the brief demands — and its honest limit

**A principled mapping IS derivable from the paper's own objects; a principled single range is NOT, because the mapping has one free parameter the design does not estimate.**

The paper cites `lesniewski2026`'s selection identity twice (tex 194, 980) and describes its own Path A design as "the estimation counterpart of \citepos{lesniewski2026} selection identity" (tex 980). Under the standard gamma-frailty form of that identity — individual hazard `h_i = Z_i·h_0·exp(βx)`, `Z ~ Gamma(mean 1, variance θ)` — the population-averaged hazard's local covariate slope is attenuated by `1/(1+θH_0)`, and the survival function satisfies `S = (1+θH_0)^{-1/θ}`. Eliminating `H_0`:

> **a(θ) = S^θ**, where **S is the pre-window survival share of the sampled pool**.

`S` is **measured in this paper**: `40,234 / 75,000 = 0.5364533` (tex 966, verified verbatim: "of the 75,000 sampled loans, 34,734 prepaid and 32 defaulted before the QT window opens, so 40,234 are active at the June 2022 start"). `ln S = −0.622772`. Hence:

| θ (frailty variance) | a = S^θ | reading |
|---|---|---|
| 0 | 1.000 | no unobserved heterogeneity — production |
| 0.25 | **0.8558** | mild |
| 0.50 | **0.7325** | moderate |
| 1.00 | **0.5365** | unit-CV frailty (exponential); attenuation equals the survival share |

**θ is not estimable in this design.** The only object that speaks to it — Path A's burnout coefficient — is `−0.13` under production spec, centred on the **opposite sign** (mean `+1.23`, median `+0.52`) by the temporal bootstrap, and "not statistically distinguishable from zero" under both schemes (tex 980, verbatim). So the spec reports the **θ-indexed curve**, with θ named as the free parameter, rather than a single invented factor. That is strictly more defensible than "0.8×/0.9×" because the free parameter is *visible*.

**Direction (signed ex ante).** The imported elasticity is a ZIP-level moving probability estimated on a population **not** conditioned on mortgage survival (tex 253: "a proportional fall in a quarterly ZIP-code moving probability"), applied to a pool depleted of exactly the rate-responsive (46.3% prepaid pre-window, largely into the 2020–21 refi wave). **a < 1; the marginal falls. This is a DOWNWARD member.** It discharges the second of R1-W5's two unnamed transport assumptions.

**Magnitude, pre-committed.** The marginal responds **sub-proportionally** to β₁ under the max form because attenuating β₁ raises `h_vol` and reduces floor censoring. Local elasticity derived from committed cells (`floor_form_offwindow_results.json` / `oos_identification_results.json`): at floor 5.334%, `δ` 5.5→6.5 moves the marginal `3.8915→4.2657pp` while β₁ moves by ×1.189, giving `ε = ln(1.0877)/ln(1.189) = 0.530`; at floor 4.695%, `6.771→7.458` for β₁ ×1.191 gives `ε = 0.553`. Take **ε ≈ 0.54**. Predicted off-window marginals (base `+5.5716pp`):

| a | predicted pp | tolerance |
|---|---|---|
| 0.8558 | **+5.12** | ±0.25 |
| 0.7325 | **+4.71** | ±0.30 |
| 0.5365 | **+3.98** | ±0.40 |

In-sample (base `+9.1985pp`): **ε is expected to be LARGER** than off-window (bind share 36.3% vs 68.8% ⇒ less censoring ⇒ closer to proportional). Ordering check pre-committed: `ε_in-sample > ε_off-window`. No point prediction.

## Parameterization

Cells: `a ∈ {1.00, 0.8558, 0.7325, 0.5365}` × floors `{0.04, 0.04991}`, central leg only — **the β₁=0 null is invariant to `a`** (`rothstein_beta1(0)=0` exactly, asserted at `floor_sweep.py:151`), so each floor needs **one** null (which doubles as the parity cell). **10 runs ≈ 4.5 min.**

## Held at production

§0 list; `FLOOR_MODE="max"`; floors consumed from `oos_identification_results.json`; loan sample, seed, macro frame, scorer unchanged; `config.ROTHSTEIN_Q_DECLINE_*` untouched.

## Landing rule per branch

**PASS (parity holds; marginal monotone decreasing in falling `a` at both floors).** The attenuation entries land in **tab:uncertainty (tex 350–370)**, headline-marginal row.

**⚖ layout note the brief's "new column" collides with:** tab:uncertainty is `p{2.4cm}p{3.3cm}p{4.0cm}p{4.8cm}` (line 348) — a fifth column will not fit and would re-wrap the whole table. Two variants:
- **V1 (recommended):** append to the headline row's existing **"Calibration range"** cell (which already carries four ranges) — *"survival-selection attenuation $+5.1$/$+4.7$/$+4.0$pp at $a = 0.86/0.73/0.54$, the frailty-identity mapping $a = S^{\theta}$ at $S = 40{,}234/75{,}000$ and $\theta = 0.25/0.5/1$"* — plus one tablenote giving the identity, the free parameter, and the sign.
- **V2:** a new `\addlinespace` **row** labelled "Attenuation sensitivity (transport)". Costs a row, not a column.

**tex 253** gains the named transport assumption itself (WP-I2's second limb): *"…and one further assumption: the elasticity is estimated on a population not conditioned on mortgage survival, and applied to a pool from which 34,734 of 75,000 sampled loans had already prepaid before the window opened. The direction is signed --- attenuation, not amplification --- and Table~\ref{tab:uncertainty} prices it."* This sentence lands **whatever the run returns**; it is a disclosure, not a result.

**STOP-1:** null cell at either floor misses its committed value (748.1850239867648 / 724.9180586) by > $0.01B.
**STOP-2:** `a=1.00` central cell misses 818.5300844066606 / 767.5264524 by > $0.01B, **or** the solved `δ'` at `a=1.00` is not exactly 6.5 to 1e-12.
**STOP-3:** marginal non-monotone in `a`, or any predicted cell outside its tolerance band by more than 2× — the latter is a **soft** alarm (report the realized ε, land the measured numbers, note the prediction miss); only non-monotonicity is a hard stop.

## Parity checks

| id | check | target |
|---|---|---|
| P1 | inversion identity, all four `a` | `|rothstein_beta1(δ') − a·β₁_mid| < 1e-12`; at `a=1`, `δ' == 0.065` exactly |
| P2 | null @4.0% | 748.1850239867648, tol 1e-6 $B |
| P3 | null @4.991% | 724.9180586, tol 1e-6 $B |
| P4 | central `a=1` @4.0% | 818.5300844066606, tol 1e-6 $B |
| P5 | central `a=1` @4.991% | 767.5264524 (`ginnie_overlay_offwindow_results.json` G1 reference), tol 1e-6 $B |
| P6 | bind-instrumentation gate at 4.0% | share ≈0.363, n = 1,683,124 (`floor_sweep.py:222–233`) |

## Artifact

`hazard/data/attenuation_sensitivity_results.json`. Fields: `mode`, `status`, `spec`, `selection_identity` `{form: "a = S^theta", S_numerator: 40234, S_denominator: 75000, S: 0.5364533…, source: "tex 966", theta_grid, a_grid, free_parameter_note: "theta is not estimated in this design; Path A's burnout coefficient is not distinguishable from zero under either bootstrap scheme (tex 980)"}`, `parity_gates` (P1–P6), `cells` keyed `"{floor}|{a}"` → `{a, theta, delta_prime, beta1, null_trapped_b, central_trapped_b, marginal_b, marginal_pp, floor_bind_share}`, `realized_elasticity_eps` per floor, `predicted_vs_realized`, `monotonicity`, `runtime_s`.

## Must NOT change

`literature_hazard.rothstein_beta1`; `config.ROTHSTEIN_Q_DECLINE_*` and the 5.5–7.7 band's meaning (the attenuation grid is a **different axis** from the elasticity band and must never be presented as widening it); the headline `+5.6`; `[+2.8,+8.7]`; the committed δ-band cells.

## ⚖ flags

1. **Frailty mapping vs illustrative two-point.** Primary = the θ-indexed mapping above. Fallback if Eugene judges it too model-laden: `a ∈ {0.9, 0.8}` labelled **"illustrative, not estimated"** in the cell text itself. Recommendation: the mapping — it is derived from a paper the manuscript already cites twice for exactly this identity, and it names its own free parameter, which the two-point version cannot.
2. **V1 vs V2 table layout** (above).
3. Whether the attenuation entries also enter **tab:assembly** as a downward member. Recommendation: **no** — they are a transport sensitivity on an imported coefficient, not a measured correction to this paper's own object, and the assembly's credibility depends on that distinction. Flagging because branch (a) of I1 and this item pull in opposite directions and a reader will line them up.

---

# SPEC J2 — scaled-null variant (`scaled_null_housing_activity`)

## Engine entry (verified)

`hazard/floor_sweep._run_scored`, with the **PSA baseline speed** as the scaling knob.

**Verified mechanism.** `literature_hazard.prepay_hazard:99` calls `baseline_hazard(loan_age)` as a module-level name; `baseline_hazard:73–76` dispatches to `h0_psa(age, psa_speed=PSA_SPEED)`, and `h0_psa:64` computes `cpr_ann = 0.06*(psa_speed/100)*min(age,30)/30` — **linear in `psa_speed` in annual-CPR space**, then converted by `cpr_annual_to_monthly_hazard`. Patching the module attribute `literature_hazard.PSA_SPEED` does **not** work (the default binds at `def` time); patching `literature_hazard.baseline_hazard = lambda age, mode=None: lh.h0_psa(age, psa_speed=100.0*phi)` **does**, because `prepay_hazard` resolves the name in `literature_hazard`'s namespace at call time. At `phi = 1.0` this is a bit-identical call to the production path, so **parity is exact by construction**.

**The `_ORIG_PREPAY` gotcha does NOT bind** (nothing patches `prepay_hazard` itself; `fs._ORIG_PREPAY` and the tally wrapper both pick the scaled baseline up automatically — which is correct, and means the bind column stays meaningful and will move, as expected).

**Note and disclose:** the Danish `us_intercept` branch (`competing_risks.py:148`) also calls `prepay_hazard` and so also carries the scaled baseline. Only the U.S. leg is scored here, but the Danish leg is simulated in the same run; state it.

**Bonus:** this is mechanically the **PSA level sweep** WP-C3 wants (75/100/125/150). One script can serve both; flagging so the coordinator does not build it twice.

## Mapping options — enumerated, one picked

| option | construction | verdict |
|---|---|---|
| **M1 (PICKED)** | scale `h₀` (PSA baseline) by `φ` in **both** legs; floor untouched | The floor is an *empirical read of realized turnover* on deep-discount cohorts (tex 249: "anchored to the same empirical observation as the ABM's mobility calibration … turnover on deeply out-of-the-money discount cohorts during 2023--2024"), so it **already embeds** the non-rate suppression — scaling it would double-count. `h₀` is the PSA convention, a normal-market seasoning ramp with **no housing-cycle content at all**, and is exactly the object R2-W2 says is missing a housing-activity term (tab:specbox "Time effects"). |
| M2 | scale the floor only | **Rejected**: double-counts the floor's empirical content; and it is already swept in level (3–5%) and in dispersion (κ grid). |
| M3 | scale the **null leg only** | **Rejected**: asymmetric, so `central − null` is no longer a β₁ contrast; it silently changes the estimand. |
| M4 | scale `h₀` **and** floor | **Rejected**: M1 + M2's defect. Reported as a stress cell only if Eugene asks. |

## Calibrating φ from the paper's own objects

The paper quotes `aladangady2024` at **tex 98** (verified verbatim): rate-gap lock-in explains **44%** of the 2021–22 mobility decline. It never converts that share into a magnitude, and no external decline magnitude is in the manuscript. So φ is calibrated **internally**, using the model's own legs, by requiring the non-rate channel to produce `(0.56/0.44) = 1.272727×` as much trapped liquidity as the rate channel:

> **Calibration condition:** find `φ*` such that `trapped_null(φ*) − trapped_null(1) = 1.272727 × [trapped_central(1) − trapped_null(1)]`.

**Feasibility, pre-computed (so the run is not started on a hope):**
- Off-window floor 4.991%: required null lift `= 1.272727 × 42.6084 = **$54.23B**`. As `φ→0` the null converges to the pure-floor leg; its mean CPR falls from `5.877%` (the 5.0% floor null, `floor_form_results.json`) toward `≈4.99%`, i.e. `≈0.89` CPR points at `≈$82.8B/pt` ⇒ **`≈$74B` of headroom > $54.23B**. A root exists.
- In-sample floor 4.0%: required lift `= 1.272727 × 70.3451 = **$89.53B**`; headroom `(5.6136 − 4.0) × 82.8 ≈ **$134B**`. A root exists.

**Direction, derived (do not assert it from the review's wording).** Lowering `h₀` lowers `h_vol` in both legs. The null is less censored than the central (bind 0.143 vs 0.363 at 4.0%, `moving_share_bracket_results.json`), so the null's trapped balance **rises faster** than the central's as `φ` falls. Therefore **`marginal(φ) < marginal(1)`: the member lies BELOW the headline, and it falls monotonically as φ falls.** At `φ→0` both legs collapse to the pure floor and the marginal → 0.

**⚖ The brief's "signed upward" needs reconciling before any wording is drafted.** REVIEW2 finding #9 says "Direction: **upward bias** on the marginal"; PLAN WP-J2 says the variant "enters the symmetric assembly as its **upward-bias entry**". Both mean: *the current marginal is biased upward, so the corrected member sits below it.* The brief's shorthand "signed upward" reads the opposite way. **The mechanics say DOWN.** Manuscript wording must therefore say *"documents an upward bias; the corrected member lies below the headline"* — never "an upward member". Eugene signs the sentence; the arithmetic is not negotiable.

## Parameterization

- **Ladder (always run):** `φ ∈ {1.00, 0.90, 0.80, 0.70}` × legs × floors `{0.04, 0.04991}` = 16 runs (the `φ=1.00` pair at each floor is the parity cell).
- **Root-find:** bisection on `φ ∈ [0.3, 1.0]` against the calibration condition, **null leg only** per evaluation, tolerance `$0.05B`, max 10 iterations; then one central run at `φ*` per floor. ≈ 11 runs/floor.
- Total ≈ **34 runs ≈ 15 min.**

## Held at production

§0 list; `FLOOR_MODE="max"`; `INVOLUNTARY_CPR_ANNUAL` set per floor by `_run_scored` and restored; `δ = 6.5`; `lh.baseline_hazard` restored in a `finally` and asserted identical to the original object at exit; `BASELINE_MODE` untouched.

## Landing rule per branch

**PASS (parity exact, root found at both floors, monotone).** The `φ*` cell enters **tab:assembly (tex 313–334)** as a new row: `Housing-activity-scaled baseline (Aladangady-anchored) | +X.X | below | scaled-null variant; upward-bias entry (run \texttt{scaled\_null\_housing\_activity})`. §V.C's assembly paragraph (**tex 312**) gains one sentence naming Aladangady's 44% as its anchor and the calibration condition as the mapping. **tex 98** gains a forward reference (currently the citation is catalogued and never used — R2's optional-dimension score dropped 11 points on precisely this). The specbox "Time effects" row gains the disclosure that the omitted housing-activity term is priced by this variant rather than modelled.

**⚖ posture-adjacent, whole item.** This adds a member to the assembly, which is the object the retired-posture decision rests on (PLAN Decision record item 1). Direction and wording drafted; Eugene signs.

**Branch NO-ROOT (calibration condition has no solution in `φ ∈ [0.3,1.0]`).** Land the **ladder only**, labelled as a sensitivity rather than a calibrated member: *"scaling the seasoning baseline by 10/20/30\% moves the marginal to $+X/+Y/+Z$ points"*, with the statement that the Aladangady share cannot be mapped into this design's units without an external decline magnitude. No assembly row.

**Branch STOP-1:** `φ=1.00` cells miss the committed values by anything at all (they should be **bit-identical** — a miss means the `baseline_hazard` patch is not a no-op at `φ=1`, i.e. the wiring is wrong).
**Branch STOP-2:** marginal non-monotone in `φ`, or `marginal(φ) > marginal(1)` at any `φ<1` — that contradicts the derived direction and means the construction is not what was specified.

## Parity checks

| id | check | target | tol |
|---|---|---|---|
| P1 | `φ=1` null @4.0% | 748.1850239867648 | **bit-exact** |
| P2 | `φ=1` central @4.0% | 818.5300844066606 | bit-exact |
| P3 | `φ=1` null @4.991% | 724.9180586 | bit-exact |
| P4 | `φ=1` central @4.991% | 767.5264524 | bit-exact |
| P5 | `φ=1` baseline identity probe | `max abs(patched_baseline(age) − lh.h0_psa(age))` on age 0..360 | **0.0** |
| P6 | bind gate @4.0%, `φ=1` | share ≈0.363, n = 1,683,124 | script's own |

## Artifact

`hazard/data/scaled_null_housing_activity_results.json`. Fields: `mode`, `status`, `spec` (incl. the M1–M4 option table and the rejection reasons), `anchor` `{source: "aladangady2024, tex 98", rate_share: 0.44, non_rate_share: 0.56, ratio: 1.272727}`, `calibration_condition` (verbatim), `feasibility_precheck` `{required_lift_b, headroom_estimate_b, root_expected: true}` per floor, `parity_gates` (P1–P6), `ladder`: per `(floor, φ)` → `{phi, psa_speed_effective, null_trapped_b, central_trapped_b, marginal_b, marginal_pp, null_mean_cpr_pct, floor_bind_share}`, `root` per floor `{phi_star, iterations, residual_b, marginal_b, marginal_pp}`, `direction_check` `{monotone: bool, all_below_production: bool}`, `runtime_s`.

## Must NOT change

`config.PSA_SPEED`; `literature_hazard.h0_psa` / `baseline_hazard` (patch and restore, never edit); the floor at either calibration; `δ=6.5`; the headline `+5.6`; the committed null values (they are the `φ=1` parity targets); tab:specbox's estimator description (only its disclosure column gains a clause).

---

# SPEC S8 — vintage overlay analogue (`vintage_overlay`) + the tex-263 characterization fix

## Engine entry (verified)

`hazard/ginnie_cpr_overlay.overlay_leg(sim, empirical, series_pct, share)` (`ginnie_cpr_overlay.py:109–128`), imported unmodified, driven exactly as `ginnie_overlay_offwindow.py` drives it. **No microsim runs** — the overlay is post-hoc arithmetic on existing leg parquets (`ginnie_overlay_offwindow.py` runs "in seconds").

Verified construction: `delta = share*(smm_g − smm_model)*exposure_b`; `simulated_rolloff_b -= delta`; `hazard_cpr_pct = (1-share)*cpr_model + share*(smm_g*1200)`. Applying the **same** series to **both** legs makes the overlaid share contribute identically in each, so it cancels in the marginal — which is why the Ginnie marginal scales by `marginal_scale_vs_conventional = **0.7975182199226121**` against a nominal conventional share of `1 − 0.204 = 0.796`. That empirical near-identity is the template's own validation.

**The `_ORIG_PREPAY` gotcha does NOT bind** (no engine run, no patching).

## BLOCKING pre-start check

Required inputs, **all absent from this worktree**:
- `hazard/data/floor_form_offwindow/microsim_max_floor4.991pct_pq{0,6.5}.parquet` — the off-window legs;
- `hazard/data/fannie_quarters/cells_FNMA{2017Q1..2022Q4}.parquet` (24) + `manifest.json` — the observed out-of-window vintage speeds;
- `hazard/data/cohort_month_panel_fannie.parquet` — the G1 parity reference.

All present in the **main checkout**. **Run there, or stage the files first.** If any is missing at start: `status: "INPUT_MISSING"`, STOP, report — do **not** substitute the committed `microsim_results*.parquet` (those are the in-sample legs, a different cell).

## Parameterization

1. **Build monthly observed series** from the Fannie cells, QT window `2022-06-01 ≤ period < 2025-12-01` (42 months, `common/qt_window.py`), on the `vintage_residual_bound.py` segmentation: `vintage_2022` (`vintage == 2022`) and `pre_2017` (`vintage <= 2016`). Per month: `SMM_t = Σprepaid_upb / Σexposure_upb`, `CPR_t = (1-(1-SMM_t)^12)*100` — the house convention for observed speeds (`vintage_residual_bound.py` step 3, and `ginnie_cpr_overlay`'s SMM↔CPR pair).
2. **Blend into ONE series** and apply `overlay_leg` **once** with `share = 0.337`:
   ```
   smm_blend_t = (0.231*smm_2022_t + 0.106*smm_pre2017_t) / 0.337
   cpr_blend_t = (1 - (1 - smm_blend_t)**12) * 100
   ```
   **Sequential application of two `overlay_leg` calls is WRONG and must not be used:** shares `s1` then `s2` yield `(1−s1)(1−s2)·CPR_m + s1(1−s2)·S1 + s2·S2`, not `(1−s1−s2)·CPR_m + s1·S1 + s2·S2`. Blending in **SMM space** and converting back with the compound form makes `overlay_leg`'s internal de-annualization (`smm_g = 1-(1-cpr_g/100)^(1/12)`) invert exactly — assert `max|smm_g − smm_blend| < 1e-12`.
3. Apply to **both** legs (central pq 6.5, null pq 0) at floor **4.991%**; `marginal = central − null`; report on the shared basis using `ginnie_cpr_overlay`'s `NETTING_B = 69.56220187263008`, `BENCHMARK_B = 764.7482532227002`.
4. **Placebo (mandatory, mirroring the Ginnie design):** the same overlay scored with the **sampled 2017–2021** observed series, isolating the common observed-series-vs-model component. `vintage_specific_component = primary − placebo`.

Shares consumed from `hazard/wal_table.py VINTAGE_SHARES` (the authoritative in-repo source per `vintage_residual_bound.py` and gate G4) and asserted `== (0.231, 0.106)`.

## Held at production

Off-window floor 4.991%; the committed off-window parquets, unmodified; `overlay_leg`, `NETTING_B`, `BENCHMARK_B` unmodified; QT window from `common/qt_window.py`; the `vintage_residual_bound` segmentation and CPR convention.

## Pre-committed expectation + derivation

**The marginal scales by the retained in-window-vintage face share.** Nominal retained share `= 1 − 0.337 = **0.663**`. By the Ginnie precedent (realized `0.7975` against nominal `0.796`, i.e. +0.15% relative), expect:

> **`marginal_scale_vs_conventional ∈ [0.655, 0.672]`; marginal `= 5.5716 × 0.663 ≈ **+3.69pp** (`$28.25B`), expected range +3.64 to +3.75pp.**

Invariance check (the Ginnie run's strongest property): the scale factor must be **near-identical across the primary and placebo variants** (Ginnie: 0.7975 primary vs a `ginnie_specific_marginal_component_pp` of just `0.0021`). A scale factor differing by more than 0.01 between variants is a wiring alarm.

Cross-check against the committed level bound: the same segments and shares produce a book-CPR error of `0.231×0.17293 + 0.106×0.96168 = +0.1419pp` → `×82.8 = **$11.75B**`, the committed vintage residual bound. The overlay must be consistent with it in **sign** (out-of-sample vintages prepaid *faster*: 4.4756% and 5.2643% vs 4.3027%).

## Landing rule per branch

**PASS (parity holds, scale in [0.655, 0.672], variant-invariant).**

- **tab:assembly (tex 313–334)** gains a row **labelled exactly like the Ginnie row's category**: `Vintage overlay at the corrected floor | $+3.7$ | below | change of estimand (re-scoping), not a correction`. And — per REVIEW2 S8's third limb — the **existing Ginnie row is relabelled the same way**: `Ginnie overlay at the corrected floor | $+4.4$ | below | change of estimand, not a correction`. Both rows measure a **re-scoped estimand** (the marginal confined to a sub-book), not an error in the headline.
- **tex 263** (§V.C, the vintage-extrapolation paragraph) gains the overlay beside the existing `$11.7$ billion` level bound: *"The same template applied as a marginal overlay --- scoring the 33.7\% out-of-window vintage share by its observed Fannie speeds in \emph{both} legs, so it contributes zero marginal --- confines the identified marginal to the in-window-vintage share: $+3.7$ points, pure share scaling ($0.66\times$), the vintage counterpart of the Ginnie overlay's $+4.4$."*
- **NO composed Ginnie×vintage cell is specified or claimed.** tex 1148 states, verified: *"of the 2022 vintage's 23.1\% of book face, 20.7\% is conventional and 2.4\% is the Ginnie intersection, so vintage and agency marginals cannot be added without double-counting that cell."* The pre-2017 × Ginnie intersection is **not** in the committed artifact. A composed cell therefore requires the full agency×vintage cross-tab to be verified first — flag it, do not run it.

**Branch OUT-OF-RANGE (scale outside [0.655, 0.672], or variants differ by > 0.01).** No landing. `status: "CHECK_FAILURE"`. A scale factor that is not the retained share means the overlay is not cancelling in both legs, i.e. the construction is not the Ginnie template.
**Branch INPUT_MISSING / parity failure.** STOP as above.

## Parity checks

| id | check | target | tol |
|---|---|---|---|
| G1 | own-series identity: overlaying each 4.991% leg with **its own** annualized CPR series reproduces that leg | central 767.5264524, null 724.9180586 | 1e-9 $B (`ginnie_overlay_offwindow.py`'s own G1 tolerance) |
| G2 | blend inversion | `max abs(overlay_leg's smm_g − smm_blend)` | < 1e-12 |
| G3 | segment pooled window CPRs from the cells | 2022 **4.475590534559171%**, pre-2017 **5.264339724557043%**, sampled **4.302657826519651%** | ≤ 1e-6 pp |
| G4 | cell integrity | 24 files, `staged_loans_total` 17,606,999, `staged_rows_total` 825,814,383, vintage range [2010, 2022] | exact (`vintage_residual_bound` G2) |
| G5 | shares from `wal_table.VINTAGE_SHARES` | (0.231, 0.106) | exact |
| G6 | conventional off-window baseline | central 91.26719121391939%, null 85.69563303100965%, marginal 5.57155818290974pp | 1e-9 |
| G7 | level-bound consistency | `0.231*d_2022 + 0.106*d_pre2017 = +0.1419pp`, `×82.8 = $11.75B` | 0.01 $B |

## Artifact

`hazard/data/vintage_overlay_results.json`. Fields: `mode`, `status`, `spec`, `floor_annual_cpr_pct: 4.991`, `shares` `{vintage_2022: 0.231, pre_2017: 0.106, combined: 0.337, retained: 0.663}`, `series` `{monthly CPR per segment, 42 months, blend}`, `parity_gates` (G1–G7), `conventional_offwindow` (the three G6 values), `overlay_offwindow` `{primary: {central, null, marginal_b, marginal_pp}, sampled_placebo: {...}}`, `marginal_scale_vs_retained`, `vintage_specific_marginal_component_pp`, `level_bound_crosscheck_b`, `composed_with_ginnie: {status: "NOT_COMPUTED", reason: "agency x vintage cross-tab incomplete: the 2022 x Ginnie intersection is 2.4pp of book face (tex 1148) but the pre-2017 x Ginnie intersection is not in the committed artifact"}`, `runtime_s`.

---

## S8 rider — the tex 263 "originated near or above prevailing market rates" fix (wording, unconditional, NO run needed)

**The claim, verbatim at tex 263:** the 2022 vintage *"lies outside the 2017--2021 Freddie sample, was originated near or above prevailing market rates (so its lock-in state differs qualitatively from the sampled vintages'), and neither the coupon reweighting nor the Ginnie speed comparison constrains the extrapolation."*

**This is false for the large majority of the vintage, and the refutation is already in a committed artifact.** `hazard/data/composition_shift_results.json` → `soma_book.latest.joint_cells_min_share_0p1pct` carries the **joint agency|term|coupon|vintage** grid (built by `composition_shift.py`, header lines 55–56). Aggregating its 2022-vintage cells:

| pass-through coupon | share of book face | share of covered 2022 vintage |
|---|---|---|
| 1.5% | 0.01031 | 4.47% |
| 2.0% | 0.07511 | 32.60% |
| 2.5% | 0.08094 | 35.13% |
| 3.0% | 0.01654 | 7.18% |
| 3.5% | 0.01712 | 7.43% |
| 4.0% | 0.01612 | 7.00% |
| 4.5% | 0.01189 | 5.16% |
| 5.0% | 0.00234 | 1.02% |

Covered face `0.23037` against the vintage's `0.231954` group share — **99.3% cell coverage**. **Below 3.0% coupon: 0.16636 of book face = 72.21% of the 2022 vintage.** Only 13.2% of it sits at ≥4.0%.

A 2.0–2.5% pass-through coupon is a note rate of roughly 2.6–3.2% (adding ~25bp servicing plus vintage g-fee), i.e. **4 to 5 points below** the QT-window market rate (5.2–7.8%). The 2022 vintage is therefore **predominantly late-2021/H1-2022 production that is deeply locked in — qualitatively the same state as the sampled 2020–2021 vintages, not different from them.**

**Drafted replacement clause (tex 263), for Eugene's signature:**

> *"…lies outside the 2017--2021 Freddie sample. Its lock-in state is not qualitatively different from the sampled vintages': 72.2\% of the 2022 vintage's book face carries a pass-through coupon below 3.0\% (SOMA CUSIP joint coupon $\times$ vintage cells, run \texttt{composition\_shift}), so the vintage is predominantly late-2021 and H1-2022 production sitting four to five points below the window's market rates, with only 13.2\% of it at 4.0\% or above. What the extrapolation lacks is not a different lock-in state but a different \emph{seasoning} state, and neither the coupon reweighting nor the Ginnie speed comparison constrains it."*

**Consistency cascade to check in the same commit:** the identical characterization appears near tex 65, 623, 1301 (`23.1`/`10.6` co-occurrence lines) — re-grep and harmonize. `liveness_gates.py` has no assertion on this phrase (verified), so the fix is tex-only unless a new gate is added.

**⚖ One consequence worth naming:** this fix *weakens* the paper's own stated reason for treating the 2022-vintage extrapolation as unbounded, i.e. it is a correction **against** a concession. That is the direction the paper's process favours, but it also removes some of the motivation for the $11.7B bound and for S8's own overlay — both of which stand on their own (out-of-sample-ness, not lock-in-state difference). Eugene should see that before signing.

---

## Execution ordering and shared risks

1. **F1** and **D** are independent and both run in the worktree. **I3** and **J2** share the `floor_sweep` seam and should run consecutively (one macro fetch each; do not attempt to share a fetch across scripts).
2. **S8** and **I1's gate G3** require the main checkout (Fannie + off-window parquets). Resolve location **before** starting either.
3. **Every** spec's parity gate rests on FRED/SOMA fetches reproducing the series that produced the committed artifacts. A parity miss > $0.01B at a cell that has passed before is an **upstream data-revision alarm**, not a spec defect: report, land nothing, do not re-tune tolerances.
4. **Zero-slack literals** (`$+5.6$` ×21, `61.2` ×17 lines, `$+11.2$` ×7 lines, hull ×7 lines, `form-conditional` ×11) must be re-derived **including and-forms** immediately before the first tex edit of each landing, per governing constraint #2 — the counts above are from this session and predate any round-28 edit.
5. Nothing in these six specs changes a committed number outside its own landing rule, and every ⚖ item is an author decision the specs record rather than resolve.

---

## I1 PRE-RUN AMENDMENTS (labeled, 2026-07-29; drafting surfaced four spec impossibilities/underspecifications, coordinator-verified)

- **I1-A1 (gate invocation).** The committed script's G0–G4 are inline in `main()`, which WRITES the frozen artifact — invoking them directly would clobber it. The new script replicates the gate block line-for-line with every anchor/tolerance READ FROM the committed module's constants (`ec.E3_POOLED_FREDDIE`, `ec.VRB_SAMPLED_CPR_PCT`, `ec.FU_R2_READ`, `ec.TOL_*`), so the gates cannot drift without the committed file changing.
- **I1-A2 (FG-2's cell bar).** The panel has ≤6 cells on the (fico, ltv) axis, so the drafted "≥10 cells" FG-2 bar is unreachable and would delete the branch. Coverage bar 30% unchanged; fallback cell bar = 2; the adaptation AND what a literal 10 would have returned are recorded in the artifact.
- **I1-A3 (standardized bootstrap).** `joint_gradient_bootstrap` cannot produce the standardized statistic; it runs verbatim for the raw gradient (G5), and the standardized bootstrap reproduces its exact rng-42 index stream with a bit-equality assertion (<1e-12) of the raw gradient recomputed from this run's indices against the imported function's draws. Imputation re-applied per replicate; mean imputed share reported.
- **I1-A4 (fixed ex ante where the spec was silent).** Nearest populated cell = L1 in ordinal coordinates, ties → larger deep exposure → lower id, candidates populated in both buckets. Limb B = telescoping counterfactual in SMM space (exact identity, residual <1e-12, total == committed +4.198179219676357 at 1e-9), symmetric Oaxaca reported never primary. Limb C: two-way (stratum+month) FE is EXACTLY unidentified (within a stratum, gap is a deterministic function of calendar time) — not run; the month-dummy share of within-regressor variance is reported as the confound's size instead.
