Worktree root: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/paper-v18-review-plan-5b7b5e`

---

# Round-28 run spec — WP-G2, coupon-convention conversion

**Status:** draft for coordinator + Eugene sign-off. Nothing here has been executed; no manuscript, gate, test, artifact, or letter line was touched by the drafting session. Every literal below carries its source location. Items that change what the paper *claims* are flagged ⚖. Items I could not verify without a data load or a run are collected in §G2.9 and must be re-checked before the first leg executes.

**Mandate.** PLAN_review2_fixes_2026-07-28.md:77 (WP-G), G1 disposition recorded at PLAN_review2_fixes_2026-07-28.md:134: *"label every coupon column, convert with vintage g-fee + 25bp servicing (public FHFA/Freddie g-fee data), re-run the full-book reweight, composed-basis cell, and tab:wal row (run-class; the composed 100.0% cell will move — landing rule pre-commits its disposition; the marginal is basis-invariant and must not move, which is itself the parity check)."*

**Verification basis.** Written against the executing code and the committed artifacts, not against their manuscript descriptions: `hazard/agents.py`, `hazard/simulate.py`, `hazard/microsim_engine.py`, `hazard/competing_risks.py`, `hazard/rate_gap.py`, `hazard/macro.py`, `hazard/extension_risk.py`, `hazard/full_book_weighting.py`, `hazard/shared_layer_scoring.py`, `hazard/wal_table.py`, `hazard/wal_anchors.py`, `hazard/composition_shift.py`, `hazard/loan_sample.py`, `hazard/ingest.py`, `abm/fed_mbs_extension_risk.py`, `abm/cross_design_reweight.py`, `figures/make_theil_data.py`, `tools/liveness_gates.py`, `paper/v18/revised_paper_v18.tex`.

---

## 0. Verified engine-entry facts (file:line), and five findings that change the shape of this spec

### 0.1 The three convention mixes, confirmed independently

| # | Claim in the G1 diagnosis | Verified at | Verdict |
|---|---|---|---|
| (a) | SOMA parse extracts the **security pass-through** coupon from `securityDescription` | `abm/fed_mbs_extension_risk.py:561-563` (`mc = re.search(r"(\d+(?:\.\d+)?)%", desc)`; `coupon = float(mc.group(1))/100.0`), bucketed at `:573` `rounded = round(coupon/step)*step` | CONFIRMED |
| (a) | `reweight_to_soma_coupons` buckets loan **note rates** against those pass-through buckets on the same 0.5% grid, no conversion | `hazard/agents.py:180` (SOMA side, `round(round(float(c["coupon"])/step)*step, 4)`) vs `hazard/agents.py:187` (sample side, `np.round(np.round(self.coupon/step)*step, 4)`), where `self.coupon` is loaded at `hazard/agents.py:119` from the parquet `coupon` column | CONFIRMED |
| (a) | Same defect exists a second time on the Path A side | `hazard/simulate.py:76-100` `_reweight_balances_to_soma` — identical two-sided bucketing, SOMA coupons at `:79`, cohort note-rate coupons at `:90` and `:96` | CONFIRMED, **and not named in the G1 diagnosis** |
| (b) | The SOMA CPR back-out amortizes at hard-coded `coupon=0.025` | `hazard/macro.py:241-243` (`sched_smm = scheduled_amortization_series(df.index, coupon=0.025, origin=pd.Timestamp("2020-06-01"))`), consumed at `hazard/macro.py:245-247` | CONFIRMED |
| (b) | Consumers are GoF / Theil / cross-correlation timing exhibits only; trapped-$ untouched | `hazard/extension_risk.py:57-70`: `emp_trapped` is `qt_emp["Extension_Delta_Billions"].sum()` and `sim_trapped` is `(qt_sim["simulated_rolloff_b"] - qt_target).sum()` — neither reads `Empirical_CPR_Pct`; `Empirical_CPR_Pct` enters only `cpr_goodness_of_fit` (`:63-66`) and `cpr_cross_correlation` (`:67-70`) | CONFIRMED |
| (c) | tex 263's "sample WAC 3.9% mapped to the book's 2.49%" mixes weighting AND rate basis | `3.9` ← `hazard/full_book_weighting.py:94` `float(loans["coupon"].mean())*100` = **unweighted** mean of **note rates** = `3.864892813333334` (`hazard/data/full_book_weighting_results.json → sample_wac_pct`; re-derived and gate-pinned at `hazard/composition_shift.py:695,705-707` with `G1_WAC_TOL = 1e-9`). `2.49` ← `hazard/composition_shift.py:334 BOOK_WAC_PCT`, checked at `:858` as `sum(c["coupon"]*c["weight"])*100` = **face-weighted** mean of **pass-through** coupons (artifact `composition_shift_results.json → soma_book.latest.wac_face_weighted_pct = 2.4954359698681268`; June-2022 as-of `2.4710166626442693`) | CONFIRMED |

### 0.2 Finding 1 — the amortization defect is not one convention, it is **three**

`hazard/macro.py:241` amortizes at **2.5%**. `abm/fed_mbs_extension_risk.py:77` sets `PORTFOLIO_COUPON = 0.03` and that is the default of `scheduled_amortization_series` (`:121-124`), used at `:890` and `:1115`; the ABM's own back-out is `abm/fed_mbs_extension_risk.py:1150-1152`. And `abm/cross_design_reweight.py:562-568` (`sched_series`) computes `wac = float(np.average(loans["coupon"], weights=weights))` — the **note-rate** WAC of the actual population, which is the physically correct convention and is already in the repo.

So the paper's two headline accounting bases use different amortization coupons for the *same* empirical CPR series, and a third script already does it right. Consequence that must be carried through §G2-B: **the printed `mean CPR 5.14\%` is the ABM series** (`abm/data/latest_run_manifest.json → metrics.cpr_pct.empirical.mean = 5.13881153921074`, produced under `PORTFOLIO_COUPON = 0.03`), while Path B's printed GoF and lag-0 `r = +0.190` are scored against the **hazard** series (2.5%). The two differ by ≈0.19 CPR pp before any conversion. This was flagged once before, in `tools/claims_liveness_audit_2026-07-14.json` (claim on the back-out), and never landed.

### 0.3 Finding 2 — a fourth run-class consumer of the unconverted bucket match exists, and it is the load-bearing one

`abm/cross_design_reweight.py:279-281` `coupon_bucket_pct` applies the identical `round(c/0.005)*0.005` grid, and `:365-366, :421-423, :449-452` feed it **Freddie note rates** while the target shares come from the SOMA CUSIP pass-through tabulation (`:294-315`, pinned at `:126-131` against `composition_shift`'s book WAC 2.49). That run produces the **76.3%** figure quoted at tex **152**, tex **432**, and tex **558** — the number §IV now leads with, whose ordering gate #100 (`ABM_LEAD_SPANS`) pins.

**This spec does NOT silently expand to cover it.** §G2.6.4 pre-commits the disposition (run it in this batch, or land a one-sentence disclosure), and marks the choice as requiring Eugene's call, because labeling three consumers and leaving the fourth unlabeled would be selective.

A fifth, in the ABM proper: tex **753** ("each household's mortgage coupon and origination date are drawn from the Federal Reserve's actual holdings composition: the live CUSIP-level SOMA parse") — SOMA **pass-through** coupons are endowed as household **note rates**, and the ABM's rate gap is coupon minus market rate. tex **784** records the resulting 2.55% multi-vintage WAC and tex **1273** the "inversion" puzzle it produced. I record this as an observation, not a finding: it is out of G2's scope, it needs its own verification pass, and nothing in this spec may be read as diagnosing tex 1273.

### 0.4 Finding 3 — three committed gates read the artifacts a naive re-run would overwrite

- **Gate #44** (`tools/liveness_gates.py:1268-1284`) reads `hazard/data/wal_table_results.json` and asserts three *derived* tex literals are present: `(5.61\%) & 9.1 & 8.2`, `(3.39\%) & 10.8 & 9.6`, and `0.6-year rule-only shortening`. `wal_table.py` writes `OUT` unconditionally (`:136`).
- **Gate at `tools/liveness_gates.py:3155`** (calibration-reconciliation battery) reads `shared_layer_scoring_results.json → results.path_b_central` for `curtailment_netted_b`, `empirical_trapped_b`, `share_pct`, `standalone_share_pct`, all at `CR_TOL = 1e-9`. **Gate at `:3801`** reads it again. `shared_layer_scoring.py:189` writes `OUT` unconditionally.
- **Gate #38** (`tools/liveness_gates.py:1136-1146`) reads `composition_shift_results.json` and pins the printed PSI literals including the coupon PSI `2.29` (tex 1164).
- `full_book_weighting_results.json` is read by **no** gate and by **no** test (verified by grep over `tools/` and `tests/`), but it *is* read by `hazard/composition_shift.py:158,173,795` as a committed anchor.

**Therefore every converted leg writes to a NEW artifact path. No committed artifact is overwritten. A post-run byte-identity check (G9) enforces this.**

### 0.5 Finding 4 — the marginal cannot move, and the reason is stronger than "basis invariance"

`reweight_to_soma_coupons` fires only when `soma_cohorts is not None` (`hazard/microsim_engine.py:43-44`). The only callers that pass it are `hazard/full_book_weighting.py:34,48` and `hazard/shared_layer_scoring.py:134,142` (verified by grep). The production central and null legs — `floor_sweep._run_scored`, `oos_identification`, `no_lockin_null` — never pass it. The hazard's own rate gap is `pool.coupon − market_rate` (`hazard/rate_gap.py:14-16`, called at `hazard/competing_risks.py:120-126`), and `pool.coupon` is the **note rate**, matched against `MORTGAGE30US`, which is also a note-rate quote. **The conversion touches nothing the hazard reads.** That is what makes the marginal parity check (§G2.4) a wiring test rather than an economic claim.

**One distinction the tasking's phrasing invites and this spec refuses.** "The marginal is basis-invariant" is a statement about the *accounting* basis (the curtailment netting is bit-identical across the central and null legs and cancels — tex 409, `calibration_reconciliation`). It is **not** a claim that a marginal computed on a *reweighted pool* equals the production marginal; a reweighted pool is a different population and its marginal is a different object. §G2.3(iv) measures the reweighted marginal at both conventions as a reported quantity, explicitly obliging only itself.

### 0.6 Finding 5 — the conversion is not a clean bucket translation, and the split is measurable

With grid step 0.5pp and a wedge Δ, write a loan's note rate as `0.5k + u`, `u ∈ [−0.25, +0.25)`. Its bucket-index shift under `round((c−Δ)/0.5) − round(c/0.5)` is `round(2u − 2Δ)`:

| Δ (pp) | Δ / 0.5 | share shifting **2** buckets down | share shifting **1** bucket down |
|---|---|---|---|
| 0.70 | 1.4 | 40% | 60% |
| **0.80 (primary)** | **1.6** | **60%** | **40%** |
| 0.90 | 1.8 | 80% | 20% |
| 1.00 (reference leg) | 2.0 | 100% | 0% |

(shares under a uniform within-bucket distribution of `u`; the realized shares are a reported diagnostic). A wedge that is not an integer multiple of the grid therefore *splits* each origin bucket across two target buckets, which changes within-bucket composition on top of the level shift. §G2.3 leg `φ_ref` (Δ = 1.00) isolates the two.

### 0.7 Corrections to pointers used in the tasking

| Tasking said | Verified |
|---|---|
| `abm/fed_mbs_extension_risk.py:562-566` | the regex pair is at **561-563**, the coupon conversion at **565**, the bucket rounding at **573** |
| `hazard/macro.py:240-243` | the call is at **241-243**; the consuming line is **246**, the write is **247** |
| `hazard/extension_risk.py:56-59` | `emp_trapped`/`sim_trapped` are at **57-61**; the untouched-by-CPR property holds |
| "the composed 100.0% cell" | `shared_layer_scoring_results.json → results.path_b_fullbook_composed.share_pct = 100.04305273304554`; printed at tex **79**, **398**, **416**, **576**, **679** |
| "full-book 107.0%→109.1%" | `full_book_weighting_results.json → path_b.balance_weighted.share_pct = 107.0326190295068`, `path_b.full_book_weighted.share_pct = 109.13914436574825`; also reproduced inside `shared_layer_scoring_results.json` as `standalone_share_pct` for `path_b_central` and `path_b_fullbook_composed` — **bit-identical across the US-only and (US,Danish) regime tuples**, which is the regime-tuple invariance C4.3 established, re-confirmed here |
| "the loan_sample has a `vintage` column" | CONFIRMED as a schema fact without loading data: `hazard/loan_sample.py:74` selects `"vintage"`; it is an `Int64` origination **year** built by `hazard/ingest.py:62-64` `_vintage_from_seq` (`seq.str.slice(1,2).cast(Int64) + 2000`), so values are 2017–2021 for this sample |

---

# The conversion φ

## G2.1.1 Definition, and the three design options

**PICKED — Option 1: a per-vintage additive wedge on the note rate, applied to a LOCAL COPY inside the bucketing routines only.**

```
φ_v(c_note) = c_note − (g_v + s)          g_v = vintage-v average single-family guarantee fee
                                          s   = 0.0025 (25 bp base servicing)
```

applied at exactly two call sites, to a local array, never to `self.coupon` / `coupons[...]`:

- `hazard/agents.py:187` — `buckets = np.round(np.round(phi(self.coupon, self.vintage)/step)*step, 4)`
- `hazard/simulate.py:90` and `:96` — the same substitution on the cohort `coupons[key]`

**Rejected — Option 2: convert the SOMA side upward instead** (`c_pt + g + s → note-equivalent`, bucket both on the note-rate grid). Rejected for two reasons. First, the SOMA parse carries no vintage per bucket that the reweight consumes — `abm/fed_mbs_extension_risk.py:566-571` derives an origin date per (term, coupon) bucket, but it is a **face-weighted average origin within a coupon bucket**, which smears adjacent vintages (`wal_anchor_results.json → note` says so explicitly for the same object), so a vintage-specific g-fee cannot be attached cleanly on that side. Second, the target shares would then have to be re-derived on a shifted grid, which changes the object the committed 2.49% anchor and gate #38's PSI describe. Converting the sample side leaves every committed SOMA-side anchor untouched.

**Rejected — Option 3: mutate `self.coupon` in place and restore in a `finally`.** Rejected outright. `pool.coupon` is read by `compute_rate_gap` (`hazard/competing_risks.py:120-126`), `rate_stress` (`:127`), and the Danish `danish_cpr_annual` / `danish_refi_in_place_cpr_annual` branches (`:147-168`). A live conversion there would move the hazard, which is precisely the thing that must not move. The `_ORIG_PREPAY`-class seam lesson applies: the safe design is one where the unsafe outcome is *unreachable*, not one where it is restored afterwards. Gate **G3** below makes the unreachability testable.

**What φ deliberately does not model, stated ex ante.** Excess servicing above the 25 bp base; buy-up/buy-down of the pass-through coupon to the 50 bp TBA grid; LLPAs delivered as upfront points rather than as an amortized g-fee. The realized note-to-pass-through distance is therefore ≥ φ's for most loans, and φ is a **lower** bound on the wedge. This is the correct direction to be conservative in: it makes the converted composition effect an **upper** bound on what survives the correction (§G2.3.4).

## G2.1.2 The g-fee schedule, and why it is FLAT

**I cannot pin per-vintage FHFA figures to the precision this table would imply, and I will not invent them.** What I can state with confidence about the FHFA *Annual Report on Guarantee Fees Charged by Fannie Mae and Freddie Mac* (the HERA §1601-mandated series, single-family acquisitions, average total g-fee including amortized upfront charges): the series sits in the **mid-50s of a basis point** across 2017–2020 and is **materially lower for 2021 acquisitions**. I am not confident of the per-year integers, and the 2020–21 period is additionally complicated by the 50 bp upfront adverse-market refinance fee (in force Dec 2020 – Jul 2021), which pushes the amortized average for 2021 refinance production the *other* way.

**Therefore: FLAT PRIMARY, with a ±10 bp sensitivity leg.** This is not merely a fallback — it is the right primary, and the argument is arithmetic:

> The bucket grid is 50 bp. The entire plausible 2017–2021 g-fee dispersion is ≤ ~12 bp = **0.24 of one bucket**. Under §0.6's split arithmetic, replacing a flat wedge by a per-vintage wedge that differs by 12 bp moves at most 24% of a vintage's mass by one bucket. The ±10 bp sensitivity leg bounds that displacement by construction, and it does so *without* asserting a number I cannot source.

**PRE-COMMITTED CONVERSION TABLE.** The `vintage` column is the origination year (§0.7).

| vintage `v` | g-fee `g_v` (bp) — PRIMARY | base servicing `s` (bp) | **Δ_v = g_v + s (pp)** | Δ_v / 0.5 (buckets) | example: 3.50% note → pass-through |
|---|---|---|---|---|---|
| 2017 | 55 | 25 | **0.80** | 1.60 | 2.70% |
| 2018 | 55 | 25 | **0.80** | 1.60 | 2.70% |
| 2019 | 55 | 25 | **0.80** | 1.60 | 2.70% |
| 2020 | 55 | 25 | **0.80** | 1.60 | 2.70% |
| 2021 | 55 | 25 | **0.80** | 1.60 | 2.70% |
| *any other* | 55 | 25 | **0.80** | 1.60 | — (absent from this sample) |

**Sensitivity legs, pre-committed, run at the same seeds:**

| leg | g-fee (bp) | Δ (pp) | role |
|---|---|---|---|
| `φ_id` | — | 0.00 | identity; the parity leg. Must reproduce the committed artifacts bit-exactly. |
| `φ_lo` | 45 | 0.70 | −10 bp band edge |
| **`φ_0`** | **55** | **0.80** | **PRIMARY. Everything printed comes from this leg.** |
| `φ_hi` | 65 | 0.90 | +10 bp band edge |
| `φ_ref` | (75) | 1.00 | mechanism reference only (§0.6): clean 2-bucket translation, isolates shift from split. **Not** a g-fee claim; never printed as an economic result. |

**Per-vintage leg `φ_vint` — CONDITIONAL, and the condition is binding.** If, at run time, the operator sources the per-vintage average total single-family g-fee for acquisition years 2017–2021 directly from the FHFA report (name the report year and table in the artifact's `gfee_provenance` field), leg `φ_vint` runs with those figures and is reported **beside** `φ_0`. If the figures cannot be sourced to a citable table, `φ_vint` is **NOT RUN** and the artifact records `gfee_provenance.per_vintage = "NOT SOURCED — flat primary carries"`. Under no circumstance are per-vintage numbers written into the artifact from recollection. A `φ_vint` result never displaces `φ_0` as the printed leg; it enters the landing only as a robustness clause.

## G2.1.3 The wedge applied to the book side (leg (b) only)

Leg (b) needs the **note-rate WAC of the SOMA book**, not of the Freddie sample. The book's pass-through WAC is 2.49% and its vintage mix is committed at tex 1302 (2021: 43.9%; 2020: 16.3%; 2017–19: 6.0%; 2022: 23.1%; pre-2017: 10.6%). **Under a flat g-fee the book-vintage weighting is irrelevant** — one more reason the flat primary is the clean choice — and the converted book WAC is:

| leg | Δ (pp) | book note-rate WAC = 2.49 + Δ |
|---|---|---|
| `φ_lo` | 0.70 | **3.19%** |
| **`φ_0`** | **0.80** | **3.29%** |
| `φ_hi` | 0.90 | **3.39%** |

The G1 diagnosis's "~3.1%" corresponds to Δ ≈ 0.60, i.e. below this spec's low leg. §G2.9 records this as a disagreement to resolve, not a discrepancy to paper over: the −0.22/−0.23 CPR pp wedge the G1 diagnosis quotes is exactly what Δ = 0.60 produces (§G2.5.2), so the two are the same computation at different Δ, and the *only* open question is the Δ.

---

# G2-A — `coupon_convention_reweight` (full-book reweight + composed cell)

## G2-A.1 Run name, script, artifact

- **Run tag:** `coupon_convention_reweight` (manuscript form `\texttt{coupon\_convention\_reweight}`).
- **New script:** `hazard/coupon_convention_reweight.py`, following the repo's convention for a companion run (`floor_form_offwindow`, `covariate_ablation_offwindow`): its own file, its own pre-committed header spec, its own artifact, machinery imported **unmodified**.
- **Artifact:** `hazard/data/coupon_convention_reweight_results.json` (new path). `full_book_weighting_results.json` and `shared_layer_scoring_results.json` are **read and never written**.

## G2-A.2 Required pre-committed patch (minimal, three changes, committed before the run)

1. **`hazard/agents.py`** — `reweight_to_soma_coupons` gains an optional keyword `coupon_convert=None`. Line 187 becomes
   `src = self.coupon if coupon_convert is None else coupon_convert(self.coupon, self.vintage)`,
   `buckets = np.round(np.round(src/step)*step, 4)`. `self.coupon` is **never** reassigned. Default behaviour is bit-identical to HEAD.
   *(Requires `self.vintage` to be carried onto the pool. If `LoanPool.__init__` does not currently retain it — §G2.9 item 3 — add `self.vintage = pdf["vintage"].values` beside `hazard/agents.py:119`; it is otherwise unused, so it cannot alter any hazard.)*
2. **`hazard/simulate.py`** — `_reweight_balances_to_soma` gains the same keyword; the substitution goes at `:90` and `:96`, on the local `coupons[key]` read, and requires a per-cohort vintage, which the cohort key already carries via `stratum_id` (`hazard/loan_sample.py:39-46`: `vintage_couponbp_ficobucket`). Parse the vintage off the stratum id; do not re-derive it.
3. **`hazard/microsim_engine.py`** — `run_qt_microsim` forwards `coupon_convert` to `pool.reweight_to_soma_coupons` at `:44`. No other change.

Everything else — seed 42, `LOAN_SAMPLE_PATH`, `FLOOR_MODE`, `LITERATURE_COEFS`, `INVOLUNTARY_CPR_ANNUAL = 0.04`, macro frame, `scale_to_holdings`, the scorer basis — is unchanged.

## G2-A.3 Engine entry and leg set

```
cohorts = fed.fetch_soma_mbs_cohorts()                       # committed parser, unmodified
res = run_qt_microsim(loan_sample=loans, macro=macro_h, output=<tmp>,
                      soma_cohorts=cohorts, coupon_convert=phi)   # default regimes ("US","Danish")
standalone = score_extension_risk(res["US"], empirical)           # 107.0/109.1 basis
shared     = score_on_shared_layer(macro_abm, soma, res)          # 97.9/100.0 basis
```

One leg produces **both** committed cells — this is verified, not assumed: `shared_layer_scoring.py:160` derives `standalone_share_pct = 109.13914436574825` for `path_b_fullbook_composed` from the same two-regime run whose shared score is `100.04305273304554`, and that standalone figure is bit-identical to `full_book_weighting.py`'s US-only run.

**Leg set — Path B: 7 microsims.**

| leg | φ | p_q | purpose |
|---|---|---|---|
| B1 | `φ_id` | 6.5 | **parity** (G4/G5) |
| B2 | `φ_0` | 6.5 | **PRIMARY** |
| B3 | `φ_lo` | 6.5 | band |
| B4 | `φ_hi` | 6.5 | band |
| B5 | `φ_ref` | 6.5 | mechanism (§0.6), reported only |
| B6 | `φ_id` | 0.0 | reweighted null, reported (§G2.3(iv)) |
| B7 | `φ_0` | 0.0 | reweighted null, reported (§G2.3(iv)) |
| B8 | *(no reweight at all)* | 6.5 / 0.0 | **the invariance check — see §G2.4; run from the caches, no engine cost** |

**Leg set — Path A: 2 sims.** `simulate_qt_window(soma_cohorts=cohorts, coupon_convert=φ)` at `φ_id` (parity) and `φ_0` (primary). Path A's cheap deterministic loop makes the band legs optional; they are **not** pre-committed.

**Runtime estimate:** 7 × (2-regime microsim ≈ 60–90 s) + 2 Path A + one FRED/SOMA fetch ≈ **12–18 minutes**.

## G2-A.4 Held at production (must not vary)

`LOAN_SAMPLE_PATH` (75k), `RNG_SEED = 42`, default regime tuple `("US","Danish")`, one shared hazard macro frame and one shared ABM macro frame, `FLOOR_MODE = "max"`, `INVOLUNTARY_CPR_ANNUAL = 0.04`, `LITERATURE_COEFS`, `beta1` from `p_q ∈ {6.5, 0}`, the committed SOMA cohort parser and its default arguments, `scale_to_holdings`, both scorers. `hazard/config.py` is not edited.

## G2-A.5 Pre-committed expectation, with derivation

**Committed inputs.**

| quantity | value | source |
|---|---|---|
| Path B balance-weighted (standalone) | `818.5300844066606` / `107.0326190295068` | `full_book_weighting_results.json → path_b.balance_weighted` |
| Path B full-book (standalone) | `834.6397001192607` / `109.13914436574825` | `→ path_b.full_book_weighted` |
| Path B composed (shared) | `765.0774982466306` / `100.04305273304554` | `shared_layer_scoring_results.json → path_b_fullbook_composed` |
| Path B central (shared) | `748.9678825340305` / `97.9365273968041` | `→ path_b_central` |
| Path A balance-weighted / full-book | `121.46388911324269` / `127.45487776525697` | `full_book_weighting_results.json → path_a` |
| Path A composed (shared) | `118.35878613255424` | `shared_layer_scoring_results.json → path_a_fullbook_composed` |
| shared-basis offset | `9.096091632702699` | `calibration_reconciliation_results.json → basis_map.offset_pp` |
| sample WAC, unweighted note | `3.864892813333334` | `full_book_weighting_results.json → sample_wac_pct` |
| sample WAC, **balance-weighted** note | **`3.78`** | PLAN_review2_fixes_2026-07-28.md:134 — **RE-VERIFY, §G2.9 item 1** |
| book WAC, face-weighted pass-through | `2.49` (latest `2.4954359698681268`) | `composition_shift.py:334`; artifact `soma_book.latest` |

**Verified identity (no run needed):** `109.13914436574825 − 9.096091632702699 = 100.04305273304556` against the committed composed `100.04305273304554` — agreement to 2e-14, i.e. the composed cell *is* the full-book cell minus the flat wedge, exactly as tex 576 asserts (`the joint results equal the one-at-a-time deltas composed ($107.0 + 2.1 - 9.1$) exactly`). This makes the composed projection a pure consequence of the full-book projection.

**Direction, signed.** The reweight matches SOMA balance shares by bucket, and SOMA is heavy at low coupons (tex 1164: book `<3.0%` 73.9% against sample 18.0%). Under the *current* unconverted match, the loans up-weighted into the book's 2.0–2.5% buckets are loans whose **note rate** is 2.0–2.5%, i.e. gaps of roughly −4.5 to −4.0 pp against the window's market rates; deeply locked, slow, so trapped liquidity rises: `+2.107` pp. Under φ, the loans mapped into those same buckets are loans whose note rate is 2.8–3.3%, gaps of −3.7 to −3.2: **less** locked, faster, so **less** trapped. The composition effect must therefore **shrink and stay positive** — positive because even after conversion the sample's pass-through-equivalent WAC (3.78 − 0.80 = 2.98) still sits **above** the book's 2.49.

**Central projection (linear in the WAC gap the reweight closes).** With `g₀ = 3.78 − 2.49 = 1.29` pp and `g₁ = 3.78 − Δ − 2.49`:

| leg | Δ | `g₁` | `g₁/g₀` | Path B composition effect | Path B full-book | **Path B composed** |
|---|---|---|---|---|---|---|
| committed | 0.00 | 1.290 | 1.0000 | +2.107 pp | 109.139% | 100.043% |
| `φ_lo` | 0.70 | 0.590 | 0.4574 | +0.964 pp | 107.996% | **98.900%** |
| **`φ_0`** | **0.80** | **0.490** | **0.3798** | **+0.800 pp** | **107.833%** | **98.737%** |
| `φ_hi` | 0.90 | 0.390 | 0.3023 | +0.637 pp | 107.669% | **98.573%** |

Under the *unweighted* sample WAC instead (`g₀ = 1.3749`) the `φ_0` figures are `+0.881` / `107.913%` / **`98.817%`** — the weighting choice moves the projection by 0.08 pp, an order of magnitude below the materiality band, which is why the unresolved 3.78 does not block the spec.

**Path A** (same ratio, cruder because Path A reweights cohort aggregates rather than loans): committed effect `+5.991` pp; `φ_0` projection `+2.276` pp → full-book **123.740%**, composed **114.643%**. Materiality band doubled (±1.0 pp) for Path A.

**PRE-COMMITTED CENTRAL VALUES (the numbers this spec is judged against):**

> **Path B full-book, converted: 107.83%** (band across `φ_lo`–`φ_hi`: 107.67–108.00)
> **Path B composed, converted: 98.74%** (band 98.57–98.90)
> **Path A composed, converted: 114.64%** (band 115.11–114.18)

**Materiality band: ±0.5 pp** on the Path B converted composed cell. Justification stated ex ante: it is a quarter of the committed composition effect (2.107 pp), 5× the printed precision (0.1 pp), and it exceeds the 0.33 pp span the entire ±10 bp g-fee band produces — so a landing inside it cannot be manufactured by the g-fee choice.

**Why the linear projection may be wrong, stated ex ante.** The map from bucket shares to trapped dollars is not linear in the WAC gap: (i) `prepay_hazard` is exponential in the rate gap, so the same bucket displacement is worth more at shallow gaps; (ii) the hard maximum censors 36.3% of central-leg loan-months at the 4.0% floor (`oos_identification_results.json → floor_bind_share = 0.36269282595934704` over `1683124` loan-months), and censored months absorb the perturbation entirely; (iii) the reweight redistributes mass, not just the mean, so a projection through the mean is a first-order approximation. (i) argues the realized effect is **larger** than projected; (ii) argues **smaller**. The direction of the net is not signed and nothing is read into it after the fact.

**Falsifiable ordering check (C1, non-parity, BLOCKING as a wiring alarm):**
`107.0326190295068 < fullbook(φ_0) < 109.13914436574825` and `fullbook(φ_hi) < fullbook(φ_0) < fullbook(φ_lo) < fullbook(φ_id)`.
A violation means the conversion is wired backwards or applied to the wrong side; the artifact is written with `status = CHECK_FAILURE` and **nothing lands**.

## G2-A.6 Parity and identity checks (BLOCKING; any FAIL voids the run)

Free gates first (no engine; seconds), so input drift is separated from conversion effects.

- **G0 (benchmark):** `score_extension_risk`'s empirical benchmark `== 764.7482532227002` to `< 1e-9`. The input-drift detector; distinguishes a FRED/SOMA revision from an engine change.
- **G1 (SOMA parse invariance):** `fetch_soma_mbs_cohorts()` face-weighted 30-year WAC reproduces `composition_shift`'s A1 anchor `2.49 ± 0.05` (`composition_shift.py:340 A1_WAC_TOL`), and the parsed cohort set is **byte-identical** across all legs (the conversion must not touch the SOMA side).
- **G2 (φ arithmetic, analytic, no engine):** on the fixed probe vector `c ∈ {0.0200, 0.0249, 0.0300, 0.0350, 0.0386, 0.0450, 0.0500}` and every vintage 2017–2021, `φ_0(c) == c − 0.0080` to `1e-15`; `φ_id(c) == c` bit-exactly; and the realized bucket-shift split reproduces §0.6's table to within the sample's within-bucket distribution (reported, not gated).
- **G3 (NON-LEAKAGE — the run's most important gate):** after every leg, `pool.coupon` is bit-identical to `coupon_to_decimal(loan_sample["coupon"])` (`np.array_equal`, exact), and the pre/post hash of the `coupon` column of the in-memory frame is unchanged. Independently: run leg **B8** — the production central and null with `soma_cohorts=None` — inside the same process, **after** a converted leg, and require §G2.4's four literals bit-exactly. A FAIL here means the conversion reached the hazard and every number in the run is void.
- **G4 (φ_id standalone parity, bit-exact `< 1e-9`):** leg B1 must return `trapped_b == 834.6397001192607`, `share_pct == 109.13914436574825`, `cpr_r_lag0 == 0.27823879699900067`, `best_lag == -3` (`full_book_weighting_results.json → path_b.full_book_weighted`).
- **G5 (φ_id composed parity, bit-exact `< 1e-9`):** the same leg scored on the shared layer must return `us_trapped_b == 765.0774982466306`, `share_pct == 100.04305273304554`, `danish_trapped_b == 846.6912914390132`, `curtailment_netted_b == 69.56220187263008`, `empirical_trapped_b == 764.7482532227002`.
- **G6 (Path A φ_id parity):** `121.46388911324269` unreweighted and `127.45487776525697` reweighted, both `< 1e-9`; composed `118.35878613255424`.
- **G7 (basis identity, arithmetic):** for every leg, `shared_share_pct == standalone_share_pct − 9.096091632702699` to `< 1e-9`, with the offset read at run time from `calibration_reconciliation_results.json → basis_map.offset_pp` and asserted against `69.56220187263008 / 764.7482532227002 × 100`. This is `burnout_ablation`'s G0g convention and it is what licenses quoting the composed cell as a derived object.
- **G8 (bucket-coverage disclosure, reported):** per leg, the share of sample balance landing in a bucket **absent from SOMA** (zeroed by `agents.py:190-193`) and the share of SOMA weight landing in a bucket **absent from the sample** (renormalized away). Under φ these move — the converted sample reaches lower buckets — and the change is a first-order explanation of any deviation from the projection. Reported in every branch.
- **G9 (committed-artifact integrity, run last):** re-read `full_book_weighting_results.json`, `shared_layer_scoring_results.json`, `wal_table_results.json`, `composition_shift_results.json` and assert byte-identity against their pre-run hashes; then assert **gate #38, gate #44, and the batteries at `liveness_gates.py:3155` and `:3801` still PASS**. This is the guard against §0.4.
- **G10 (restoration):** after every leg, `literature_hazard.INVOLUNTARY_CPR_ANNUAL == 0.04`, `LITERATURE_COEFS` equal to its production dict, and no temporary parquet left on disk.

Status ladder: `OK` / `GATE_FAILURE` / `CHECK_FAILURE`; non-`OK` raises `SystemExit` and nothing lands.

## G2-A.7 Artifact schema

`hazard/data/coupon_convention_reweight_results.json`

```
mode, status, spec (verbatim header), parity_tolerance (1e-9),
conversion{ rule: "c_pt = c_note - (g_v + 0.0025)",
            gfee_provenance{ primary: "FLAT 55bp, FHFA Annual Report on Guarantee Fees,
                             single-family acquisitions 2017-2021; per-year integers NOT
                             sourced at spec time — see gfee_provenance.per_vintage",
                             per_vintage, report_year, table, retrieved_utc },
            legs{ phi_id:0.0, phi_lo:0.0070, phi_0:0.0080, phi_hi:0.0090, phi_ref:0.0100 },
            servicing_bp: 25, vintage_column: "vintage", vintages_present[] },
basis_map{ curtailment_netted_b, cap_benchmark_b, offset_pp, note },
legs{ B1..B7, A1..A2 }: each with phi_label, delta_pp, p_q_shock_pct, beta1,
  trapped_b, share_pct_standalone, share_pct_shared, cpr_r_lag0, best_lag, peak_lag_r,
  mean_us_cpr_pct, danish_trapped_b,
  bucket_diagnostics{ sample_share_by_bucket_pre, sample_share_by_bucket_post,
                      soma_share_by_bucket, reweight_factor_by_bucket,
                      zeroed_balance_share, unreachable_soma_weight_share,
                      shift_split{ two_buckets_pct, one_bucket_pct } },
sample_wac{ unweighted_note_pct, balance_weighted_note_pct,
            balance_weighted_passthrough_equivalent_pct, book_face_weighted_passthrough_pct },
parity_gates{ G0..G10 }, parity_gates_all_pass,
invariance{ production_central_4pct, production_null_4pct,
            production_central_4991, production_null_4991,
            got, want, abs_diff, pass },                     # §G2.4, leg B8
reweighted_marginal{ phi_id{ marginal_b, marginal_pp }, phi_0{ ... },
                     note: "a reweighted pool is a different population; this quantity
                            obliges only itself and is NOT the identified marginal" },
projection{ committed_effect_pp, ratio_g1_over_g0, projected_effect_pp,
            projected_fullbook_pct, projected_composed_pct,
            realized_effect_pp, deviation_pp, within_materiality_band_0p5 },
c1_ordering_pass, landing_branch (A|B|C|D, pure function fixed in the header), runtime_s
```

## G2-A.8 Landing rule (pre-committed; branch on the **Path B converted composed** cell)

The classifier is a pure function fixed in the script header so it is testable without a run.

> **Branch A — converted composed ∈ [99.5, 100.5]%.** The composed cell survives at one decimal. Disposition: tex 79, 398, 416, 576, 679 keep their literals and gain the convention label; tex 263 and 580 gain the labeled pair; the run is reported as *confirming* that the mixed-basis comparison was not load-bearing. **No claim changes.**

> **Branch B — converted composed ∈ [97.94, 99.5)%. THE PROJECTION'S BRANCH (98.74%).** The composed cell moves by ≈1.3 pp and falls below 100. ⚖ Disposition below. The composition effect is still positive, so the *direction* of the full-book correction stands; only its size and the "100.0%" coincidence change.

> **Branch C — converted composed < 97.94%** (below the leg's own **shared** figure, i.e. the composition effect turned **negative**). This contradicts the ordering check and the WAC arithmetic simultaneously. **STOP.** Write `status = CHECK_FAILURE`, land nothing, and treat it as evidence that the balance-weighted sample WAC is not 3.78 (§G2.9 item 1) or that φ is applied to the wrong side.

> **Branch D — converted composed > 100.5%** (the effect grew under conversion). Also a wiring alarm: converting the sample *toward* the book cannot enlarge the distance the reweight closes. **STOP**, same treatment.

**Disposition sites for Branch B, with current text quoted verbatim (anchors for the edit; this spec changes none of them).**

1. **tex 416** (tab:bases, the primary numeric site):
   > `Path B, central (in-sample calibration) & 107.0\% & 97.9\% & 109.1\% & 100.0\% & $+53.8$ \\`

   The Full-book and Composed cells gain the converted companion. Header at **tex 414** currently reads `& (scorer) & ($-9.1$pp) & (book WAC) & ($-9.1$pp) & error (\$B) \\` — `(book WAC)` becomes `(book pass-through WAC)`, and a note states which convention each column's reweight matched on.
2. **tex 576** (§VII.F):
   > `The fully corrected figure comes from a joint run (the book-coupon-reweighted simulation scored through the shared layer in one pass), which recovers \$765.1 billion (unrounded: \$765.077 billion): 100.0\% of the \$764.7 billion benchmark at one decimal, and exactly 100.04\% as the ratio of the two unrounded figures, $765.077/764.748$, with Path A's joint run at \$905.1 billion, 118.4\%.`

   ⚖ **The "100.0% at one decimal" and "exactly 100.04%" clauses are RETAINED but relabeled as the mixed-basis measurement they are, and the converted companion is stated beside them as the like-for-like figure.** The sentence must not be allowed to read as if 100.0% were the corrected number. The identity cross-check that follows (`the joint results equal the one-at-a-time deltas composed ($107.0 + 2.1 - 9.1$) exactly`) is verified above to 2e-14 and survives with its own converted restatement.
3. **tex 432** (§V, the reconciliation paragraph):
   > `the 2.1-point miss (97.9\%, and within 0.05\% composed) is the in-sample figure, retained as the model-fit diagnostic it is`

   ⚖ **`within 0.05\% composed` is STRUCK or requalified** — at 98.74% the composed miss is ≈1.3 points, not 0.05. This is the single most consequential wording consequence of G2 and it must not be smuggled through as a number change.
4. **tex 79** (tab:headline): `97.9\% in-sample (100.0\% composed, in-sample)` → the composed figure gains its convention label and the converted companion.
5. **tex 398** (tab:estimators note): `(97.9\%, and 100.0\% composed, at the in-sample calibration point; 91.3\% at the off-window floor the paper headlines)` → same treatment.
6. **tex 679** (tab:crosswalk row): `Path B central 97.9\% (107.0\% standalone; 100.0\% composed), in-sample calibration; 91.3\% (100.4\% standalone) at the off-window floor & shared / standalone / composed & Table~\ref{tab:bases} & …` → same treatment. **Note the collision hazard:** `100.4\%` on this line is the off-window *standalone* central, a different object from `100.0\%` composed; a careless global replace corrupts it.
7. **tex 263** (§V.C, the sentence the G1 diagnosis names):
   > `Along the coupon dimension, Section~\ref{sec:robustness-hybrid}'s full-book reweighting (sample WAC 3.9\% mapped to the book's 2.49\%) moves Path B from 107.0\% to 109.1\%, a composition effect of about two percentage points.`

   Gains the convention parenthetical (§G2.6.1) **and** the converted figure. Under Branch B, `a composition effect of about two percentage points` becomes a two-part statement: about two points as measured across conventions, about **0.8** points like-for-like.
8. **tex 580** (§VII.F, second check):
   > `The Path A and Path B headline recoveries are balance-weighted estimates on the Freddie sample's composition, whose weighted-average coupon (3.9\%) sits above the SOMA book's (2.49\%). Reweighting the simulated hazards to the book's actual coupon mix shifts Path B from 107.0\% to 109.1\% of the benchmark and Path A from 121.5\% to 127.5\%, a composition effect of roughly two percentage points for Path B that bounds the sample-to-book extrapolation error along the coupon dimension`

   Same treatment; **plus** the "bounds the sample-to-book extrapolation error along the coupon dimension" claim is re-checked: after conversion the bound is `0.8` points, not `2.1`, and the bound tightens (which cuts *for* the paper, and must be stated as such rather than quietly).
9. **tex 1164** (tab:composition, Coupon row): `Coupon & $<3.0\%$: 18.0; 3.0--4.0\%: 68.2; $\geq 4.0\%$: 13.8 & 73.9; 18.7; 7.3 & 2.29; full-book reweighting 107.0\% $\to$ 109.1\% \\` — the sample column gains its basis label (note rate) and the book column gains its own (pass-through); the consequence cell gains the converted pair. **PSI `2.29` is gate-#38-pinned and must survive verbatim** (§G2.7).
10. **tex 1177** (tab:composition note): `Sample coupon shares are exposure-weighted universe-panel shares at the window open; the sample WAC is 3.9\% against the book's 2.49\%.` — the *weighting* mismatch is disclosed here as well as the *basis* mismatch: 3.9 is unweighted over loans while the shares beside it are exposure-weighted.
11. **tab:runindex** (`\label{tab:runindex}` at tex **697**; rows through tex ~740): one row for `\texttt{coupon\_convention\_reweight}`.
12. **tab:verdicts** (`\label{tab:verdicts}` at tex **1380**): one row. Under Branch B the Adjudication cell reads *against the headline framing* (a favourable-looking coincidence dissolves), which is the direction gate #104's `row_against_own_pass` discipline exists to keep visible.

## G2-A.9 What this run must NOT change

The headline marginal `+5.6` pp / `+$42.6` billion at any floor and the in-sample `+9.2` pp; the FLOOR values and `FLOOR_MODE`; **tab:assembly** in its entirety (tex 314–334, gate #98 `ASSEMBLY_SPANS` / `ASSEMBLY_TABLE_SPANS`); **the abstract** (tex 30 — verified to carry no composed figure and no coupon literal, so it is untouched by construction, and this line records that it stays that way); the shared central `97.9\%` and null `88.7\%`; the off-window `91.3\%` / `100.4\%`; `2.29` and every other gate-#38 PSI literal; the committed artifacts of §0.4; `hazard/config.py`; any `.tex` file (the run writes only its artifact).

---

# G2-B — `coupon_convention_amortization` (the back-out leg)

## G2-B.1 Run name, script, artifact

- **Run tag:** `coupon_convention_amortization`. **New script:** `hazard/coupon_convention_amortization.py`. **Artifact:** `hazard/data/coupon_convention_amortization_results.json`.
- **No engine run anywhere.** One FRED fetch + one SOMA fetch, then `build_empirical_metrics` with an injected `sched_smm`, then re-scoring of the **cached, committed** simulated paths. `hazard/macro.py:241` already accepts `sched_smm` as a parameter (`hazard/macro.py:215, 240`), so **no patch to `macro.py` is required** — the override is a caller-side argument. Verified.

## G2-B.2 Parameterization

```
sched_conv = macro.scheduled_amortization_series(index, coupon=0.0249+Δ,
                                                 origin=pd.Timestamp("2020-06-01"))
emp_conv   = macro.build_empirical_metrics(macro_df, soma_rolloff=fetch_soma_mbs_monthly(),
                                           sched_smm=sched_conv)
```

- Legs: `Δ ∈ {0.0000, 0.0070, 0.0080, 0.0090}` → amortization coupon `∈ {2.49%, 3.19%, 3.29%, 3.39%}`, **plus** the committed `2.50%` as the exact reproduction leg (the hard-code is `0.025`, not `0.0249` — a 1 bp difference that must be reproduced exactly rather than assumed away).
- **The ABM-side series is recomputed too**, at `PORTFOLIO_COUPON ∈ {0.03 (parity), 0.0329 (primary)}`, using the committed `abm/fed_mbs_extension_risk.scheduled_amortization_series` with an explicit `coupon=` argument. This is required, not optional: the printed `5.14\%` is the ABM series (§0.2).
- Re-scored consumers, all from committed caches, no re-simulation: `microsim_results.parquet` (Path B central), `microsim_results_pq0.0.parquet` (null), `SIM_RESULTS_PATH` (Path A), and the committed ABM `metrics_monthly.csv`. Re-scored quantities: `cpr_goodness_of_fit`, `cpr_cross_correlation` at lags −3…+3, best lag, peak r, and the Theil blocks `figures/make_theil_data.py` builds (U, U₂, bias/variance/covariance shares on levels, first differences, detrended).

## G2-B.3 Pre-committed expectation, with derivation

**The wedge, computed in-spec from the published closed form** (`hazard/macro.py:51-64`; `scheduled_amortization_smm(r, 360, k)`), averaged over the QT window's `k = 24…65` (origin 2020-06, window 2022-06…2025-11):

| leg | hazard basis (2.50% → ·) | ABM basis (3.00% → ·) | ABM basis, 2021 (`k = 7…18`) |
|---|---|---|---|
| Δ = 0.70 (3.19%) | **+0.2596** CPR pp | +0.0695 | +0.0671 |
| **Δ = 0.80 (3.29%)** | **+0.2956** CPR pp | **+0.1055** | **+0.1018** |
| Δ = 0.90 (3.39%) | **+0.3312** CPR pp | +0.1411 | +0.1361 |
| *(G1's ~3.1%)* | *+0.2269* | — | — |

**This reconciles the G1 diagnosis exactly:** its quoted −0.22 to −0.23 CPR pp/yr is the `2.50% → 3.10%` case (+0.2269, monthly range +0.2224…+0.2313). The two calculations agree; only Δ is in dispute (§G2.9 item 2).

**Signed, falsifiable predictions.**

- **P-a (levels move, one direction only).** Empirical CPR rises at every month. Hazard-basis window mean rises by `+0.2956` pp; the ABM-basis printed `5.14\%` rises by `+0.1055` → **`5.24\%`**. Every estimator over-predicts less / under-predicts more against the raised empirical path, so **every** estimator's Theil **bias share rises** on levels. No estimator's ranking changes.
- **P-b (timing is invariant, and this is the sharp one).** The per-month wedge spans `+0.2896` to `+0.3017` (hazard basis, Δ = 0.80) — a **range of 0.012 pp** against an empirical CPR standard deviation of `2.7723865044362053` (`latest_run_manifest.json → cpr_pct.empirical.std`). The wedge is therefore an additive constant to within 0.4% of the signal's own dispersion, and cross-correlations are computed on demeaned series. **Pre-committed: every peak lag is unchanged in location (0 months of movement, not 1), and every reported `r` moves by less than 0.005.** The committed anchors that must hold: Path B `cpr_r_lag0 == 0.19000395255236566`, `best_lag == -3`, peak `r = +0.404`; Path A `best_lag == -2`; and the first-difference `U₂` values `1.23` (ABM) / `1.01` (Path A) / `1.00` (Path B) at tex 1019 must move by **< 0.01**, because differencing removes an additive constant exactly and leaves only the 0.012 pp drift.
- **P-c (the clip is the one nonlinearity, and it is a live interaction).** `hazard/macro.py:246-247` computes `empirical_smm.clip(lower=0)`; the committed empirical series has `min = 0.0` over `n = 42`. Lowering `sched_smm` **un-clips** any month whose raw `actual/holdings − sched` sat in `(−Δsched, 0)`. **Pre-committed as a reported diagnostic:** the count of clipped months before and after, per leg. This is the same object as **WP-H1's "four exact-zero months"** — if the count falls, G2-B has partially diagnosed H1 and the two packages must be sequenced; if it does not, H1's zero months are not an amortization artifact, which is itself informative. **No claim is attached to either outcome in this spec.**

**Materiality convention:** levels may move up to ±0.5 CPR pp without comment (the projection is +0.30); **timing may not move at all** — a peak-lag location change or an `|Δr| ≥ 0.005` is a FAIL of P-b and is reported as such.

## G2-B.4 Parity checks (BLOCKING)

- **H0** the Δ = 0 leg at `coupon=0.025` reproduces the committed empirical frame bit-exactly: window-mean `Empirical_CPR_Pct`, the full 42-month vector, and `Extension_Delta_Billions.sum() == 764.7482532227002` to `< 1e-9`.
- **H1** the **dollar invariance**, and it is the leg's headline gate: `emp_trapped`, `sim_trapped`, `hazard_trapped_b`, and `share_explained_pct` are **bit-identical** across every Δ (`np.array_equal`, exact 0.0 difference), for Path B central, the null, and Path A. This is the code-level proof of §0.1's claim that the trapped-$ scoring never reads `Empirical_CPR_Pct`. A FAIL means the accounting is not what `extension_risk.py:57-61` reads as, and the whole (b) leg is void.
- **H2** the ABM Δ = 0 leg at `PORTFOLIO_COUPON = 0.03` reproduces `latest_run_manifest.json → cpr_pct.empirical` `{mean 5.13881153921074, std 2.7723865044362053, max 13.497501108600144, min 0.0, n 42}` to `< 1e-9`.
- **H3** monotonicity: window-mean empirical CPR strictly increasing in Δ, on both bases.
- **H4** the committed simulated caches are read-only; their hashes are unchanged post-run.
- **H5** committed-artifact integrity: `figures/theil_data.json` and `hazard/data/b3_timing_scores.json` unchanged on disk (the converted Theil block goes to the new artifact only).

## G2-B.5 Landing rule

> **Branch (i) — P-b HOLDS (peak lags unchanged, all `|Δr| < 0.005`, `|ΔU₂| < 0.01`). THE EXPECTED BRANCH.**
> Landing is a **disclosure sentence plus a labeled level restatement**, no timing exhibit changes:
> - §III.B / Appendix `sec:robustness-pipeline` gain one sentence naming the amortization convention, its two committed values (2.5% hazard, 3.0% ABM), the physically correct note-rate basis, and the measured wedge with the statement that the timing exhibits are invariant to it.
> - **tab:theil is NOT refreshed** — its verdicts are unchanged and its levels shares move within their printed precision. Instead its tablenote gains the convention label. (If any printed Theil share moves by ≥ 0.5 pp, tab:theil **is** refreshed; that is a sub-branch, not a new branch.)
> - The printed `mean CPR 5.14\%` at **tex 386** (tab:estimators, `Empirical benchmark (SOMA, phased cap, 30+15yr) & \$764.7B & 100.0\% & -- & mean CPR 5.14\%`) and inside **tab:wal** gains its convention label and, under §G2-C's landing, its converted companion `5.24\%`.
> - The **dollar invariance (H1) is stated in the same sentence.** It is the reason the correction does not touch the benchmark, and leaving it implicit would invite the reader to assume the opposite.

> **Branch (ii) — P-b FAILS** (any peak lag moves, or `|Δr| ≥ 0.005`, or `|ΔU₂| ≥ 0.01`).
> The additive-constant argument is wrong and something else is going on (most likely the clip, P-c). **tab:theil IS refreshed** on the converted series, the timing sentences at tex 270 and tex 398 are re-derived rather than re-numbered, and the peak-lag interpretation at tex 270 (`a peak at $k=-3$ means the simulated path \emph{trails} the empirical path by three months`) is re-verified before anything lands. ⚖ if the lag interpretation moves.

> **Unconditional in both branches:** the clip-count diagnostic (P-c) is reported and handed to WP-H1; the converted series is **not** promoted to production (the committed series remains the scored one until a separate decision) — G2-B measures and labels, it does not re-base.

## G2-B.6 What this leg must NOT change

`Extension_Delta_Billions`, the `$764.7482532227002` benchmark, `hazard_trapped_b` / `share_explained_pct` for any leg (H1 enforces bit-identity), the committed simulated caches, `figures/theil_data.json`, `hazard/data/b3_timing_scores.json`, `hazard/macro.py`'s production default (the override is caller-side), `abm/fed_mbs_extension_risk.py:77 PORTFOLIO_COUPON`.

---

# G2-C — `wal_converted` (the tab:wal row)

## G2-C.1 Run name, script, artifact

- **Run tag:** `wal_converted`. **New script:** `hazard/wal_converted.py`. **Artifact:** `hazard/data/wal_table_converted_results.json`.
- **Required minimal patch to `hazard/wal_table.py`:** `cell_wal` reads the module global `WAC` at `:76`. Change the signature to `cell_wal(term_n, age, cpr, wac=WAC)` and thread `wac` through `book_wal`, **preserving the default exactly**. `hazard/wal_anchors.py:36` imports `cell_wal` and calls it positionally, so a defaulted trailing parameter is safe; `functools.lru_cache` at `:72` still keys correctly because `wac` becomes part of the key. `wal_table.py` must remain byte-output-identical when run with no arguments — its five `V15_PRINTED` parity asserts (`:115-117`) are the test.
- **`wal_table_results.json` is NOT overwritten.** Gate #44 reads it (§0.4).

## G2-C.2 What changes, and the coupling to G2-B

Three inputs move together, and only together:

1. `WAC` `0.0249 → 0.0249 + Δ` (the amortization rate in `cell_wal`). Physically, scheduled principal follows the **note** rate; the committed table amortizes the book at its **pass-through** WAC (tex 1303: `coupon at the book's 2.49\% WAC`).
2. `SCENARIOS["empirical"]` `0.0514 → 0.0514 + w_emp`, where `w_emp` is G2-B's **ABM-basis** wedge (§0.2: the printed 5.14% is the ABM series). `φ_0`: `w_emp = +0.001055` → `5.245\%`.
3. `SCENARIOS["no_shock_2021_speeds"]` `0.2281 → 0.2281 + w_21`, `w_21 = +0.001018` at `φ_0`.

Simulated-CPR scenarios (`abm`, `path_a`, `path_b`, both Danish rows) are **unchanged** — they are model output, not back-outs.

## G2-C.3 Pre-committed expectation, computed in-spec from the published formula

The table note's formula (tex 1303-1304) was transcribed and evaluated on literals; the **parity leg reproduces every committed value exactly**, which is what licenses the converted projections below.

| Scenario | committed (Jun 22 / Nov 25) | **`φ_0` projected** | `φ_lo` | `φ_hi` |
|---|---|---|---|---|
| Scheduled amortization only (0%) | 14.7 / 12.6 | **15.2 / 13.0** | 15.1 / 12.9 | 15.2 / 13.0 |
| Empirical path (5.14% → 5.24%) | 9.4 / 8.5 | **9.5 / 8.6** | 9.5 / 8.6 | 9.6 / 8.6 |
| Production ABM (11.68%) | 6.0 / 5.6 | **6.1 / 5.7** | 6.1 / 5.7 | 6.1 / 5.7 |
| Hazard Path A (3.34%) | 10.9 / 9.7 | **11.2 / 9.9** | 11.1 / 9.9 | 11.2 / 9.9 |
| Hazard Path B (4.76%) | 9.7 / 8.7 | **9.9 / 8.9** | 9.9 / 8.9 | 10.0 / 8.9 |
| Danish rule-only, production anchor (5.61%) | 9.1 / 8.2 | **9.3 / 8.4** | 9.2 / 8.4 | 9.3 / 8.4 |
| Danish-level bracketing (3.39%) | 10.8 / 9.6 | **11.1 / 9.9** | 11.1 / 9.8 | 11.2 / 9.9 |
| No-shock, 2021 speeds (22.81% → 22.91%) | 3.4 / 3.3 | **3.4 / 3.3** | 3.4 / 3.3 | 3.4 / 3.3 |

**Derived statistics — three invariant, three not.** Pre-committed:

| statistic | committed | `φ_0` projected | verdict |
|---|---|---|---|
| Danish rule-only shortening (`path_b − danish_us_intercept`, Jun 22) | **0.6** yr | **0.6** yr | **INVARIANT** — and it is gate-#44-pinned (`0.6-year rule-only shortening`) |
| ABM's error vs empirical (`empirical − abm`) | 3.4 yr | **3.4** yr | **INVARIANT** (tex 1311 `roughly 3.4 years too short`) |
| Extension vs no-shock (`empirical − no_shock`) | 6.0 yr | **6.1** yr | moves 0.1 (tex 1311 `a 6.0-year extension`) |
| Path B's error vs empirical | 0.3 yr | **0.4** yr | moves (tex 1311 `Path B lands within 0.3 years`) |
| Path A's error vs empirical | 1.5 yr | **1.7** yr | moves (tex 1311 `a book 1.5 years too long`) |
| scheduled-only, origination WAL 30yr | 16.9 yr | **17.5** yr | moves (tex 1304; `wal_anchor_results.json → origination_wal_years.30yr_at_2.49 = 16.89`) |
| 2021 cell aged 12mo | 16.3 yr | **16.8** yr | moves (`cell_2021_age12_30yr = 16.27`) |
| 15yr sleeve origination WAL | 8.0 yr | **8.2** yr | moves (`15yr_at_2.49 = 8.01`) |

**The interesting result, pre-committed as such:** the Empirical row is *nearly* invariant (9.4 → 9.5) because the two corrections oppose — slower scheduled amortization lengthens WAL, a higher backed-out CPR shortens it — and they cancel to within one printed decimal. **This must be stated as a measured offset, not discovered after the fact.** The scheduled-only row, which has no CPR to offset it, moves by the full 0.5 years, and it is the row whose literal (`14.7`) appears **4 times** in the tex.

**Materiality band: ±0.2 years** on any printed row.

## G2-C.4 Parity checks (BLOCKING)

- **W0** the parity leg (`wac=0.0249`, committed scenarios) reproduces `wal_table.py`'s five `V15_PRINTED` pairs exactly **and** the three Danish/derived literals gate #44 reads: `danish_us_intercept (9.1, 8.2)`, `danish_level (10.8, 9.6)`, `rule_only_wal_shortening_years == 0.6`.
- **W1** `wal_table_results.json` and `wal_anchor_results.json` byte-identical post-run; **gate #44 still PASSes**.
- **W2** `wal_anchors.py` run unchanged reproduces `blend_standin_ages == 14.7`, `origination_wal_years.30yr_at_2.49 == 16.89`, `15yr_at_2.49 == 8.01`, `cell_2021_age12_30yr == 16.27` — the defaulted-parameter patch must be inert.
- **W3** the empirical-scenario CPR consumed here equals G2-B's ABM-basis converted window mean to `< 1e-9`. **G2-C is BLOCKED on G2-B**; it may not use a hand-entered wedge.
- **W4** monotonicity: every scenario's WAL weakly increasing in `wac` at fixed CPR.

## G2-C.5 Landing rule

> **Branch (α) — every row within ±0.2 years of the projection. THE EXPECTED BRANCH.**
> tab:wal gains a **converted companion block** (a second column pair, or a stacked converted panel — presentation is the coordinator's call), the tablenote gains the convention sentence, and the four derived statements at **tex 1311** are re-derived from the converted column with their invariant/moved status stated. **tex 769**'s `a 14.7-year weighted-average life at zero CPR against the no-shock 3.4-year life (Table~\ref{tab:wal}), an order-of-magnitude extension ceiling rather than an unbounded one` gains the converted figure; the *claim* (order-of-magnitude ceiling) survives at 15.2 vs 3.4 and must be shown to survive rather than asserted to.
> **tex 1313**'s `folding it in brings coverage to 99.8\% of SOMA face value at a SOMA weighted-average coupon of 2.49\%` gains `pass-through` as the label — the coverage figures do not move.

> **Branch (β) — any row deviates by > ±0.2 years from the projection.**
> Report the deviation with its size, do **not** reinterpret. The most likely cause is a wedge disagreement (§G2.9 item 2) or the empirical-scenario basis (§G2.9 item 4); resolve that first and re-run before landing anything.

> **Branch (γ) — the parity leg W0/W2 fails.** The defaulted-parameter patch is not inert. **STOP**; nothing lands; `wal_table.py` is reverted.

## G2-C.6 What this leg must NOT change

`wal_table_results.json`, `wal_anchor_results.json`, gate #44's PASS state and its three tex literals, `wal_table.py`'s no-argument output, the `VINTAGE_SHARES` / `TERM_SPLIT` / `AGES_JUNE_2022` constants, the coverage reconciliation figures (90.7%/9.1%/99.8%/90.6%).

---

# G2.4 — The invariance parity check (leg B8)

**Claim under test.** The conversion is confined to bucket matching inside `reweight_to_soma_coupons` / `_reweight_balances_to_soma`, both of which are unreachable from the production central and null legs (§0.5). Therefore the **identified marginal must not move at any floor, by any amount.**

**Executed as part of G2-A, in the same process, after at least one converted leg has run** (so that any leaked state would be present):

| leg | floor | p_q | committed value | tolerance |
|---|---|---|---|---|
| production central | 4.0% | 6.5 | `818.5300844066606` | `< 1e-9` |
| production null | 4.0% | 0.0 | `748.1850239867648` | `< 1e-9` |
| production central | 4.991% | 6.5 | `767.5264524465003` | `< 1e-9` |
| production null | 4.991% | 0.0 | `724.9180585654117` | `< 1e-9` |
| derived marginal | 4.0% | — | `70.34506041989584` / `+9.198459770709789` pp | `< 1e-9` |
| derived marginal | 4.991% | — | `42.60839388108866` / `+5.571558182909726` pp | `< 1e-9` |

(sources: `no_lockin_null_results.json`, `oos_identification_results.json → instrument1_marginal_table`.)

**Rule: if the marginal moves by any amount at any floor → STOP the entire G2 branch.** It is a wiring error, not a finding. Write `status = GATE_FAILURE`, land nothing from G2-A, G2-B, or G2-C, and diagnose before proceeding. This is the check the tasking names, and it is stated as an *absolute* rather than a tolerance because there is no mechanism by which a bucket relabel inside an unreached function could move it by a legitimate amount.

**Reported beside it, obliging only itself:** the **reweighted** marginal (central minus null on the reweighted pool) at `φ_id` and `φ_0` (legs B1/B6 and B2/B7). This object does not currently exist anywhere. It is **not** required to be invariant — a reweighted pool is a different population — and no headline quantity may be restated from it. It is reported because the natural referee question ("did the coupon-convention error contaminate the identified quantity?") deserves a measured answer and not only an argument from unreachability.

---

# G2.5 — Labeling edits (no-run, wording-class, land with the run batch)

Every edit below is a **label**, not a number. They land in the same commit as the run batch, and they are count-asserted so a later concision pass cannot silently drop them.

## G2.5.1 The two required label definitions (add once, at the definition site)

**tex 144** is the site — it defines all four accounting bases and contains **four** of the tex's ambiguous `coupon` uses:

> `The \emph{full-book basis} instead reweights the standalone figure from the estimation sample's coupon mix to the SOMA book's weighted-average coupon (WAC), with no curtailment netting.`

Proposed labeled replacement (illustrative; exact wording is the coordinator's):

> `The \emph{full-book basis} instead reweights the standalone figure from the estimation sample's \emph{note-rate} coupon mix to the SOMA book's face-weighted \emph{pass-through} coupon (WAC). The two are different rates on the same loan: the pass-through coupon is the note rate less the guarantee fee and base servicing, roughly 80 basis points over this book's vintages, so a note-rate bucket and a pass-through bucket of the same nominal value describe different collateral.`

## G2.5.2 Count-asserted site list

`coupon` occurs on **58 distinct tex lines** (95 occurrences). Of these, the sites requiring a convention label are:

**Book / pass-through sites (label: *pass-through*) — 15 lines:**
tex **88**, **144** (×4 occurrences), **152**, **263** (the primary; note tex 263 *already* labels one use correctly: `carries a pass-through coupon below 3.0\%`), **267**, **409**, **414** (`(book WAC)` header), **432**, **558**, **576**, **580** (×2), **740**, **784**, **1164**, **1177**, **1303**, **1313**.

**Sample / note-rate sites (label: *note rate*) — 12 lines:**
tex **228**, **241**, **249** (`the loan's coupon minus the prevailing market rate` — already unambiguous in context, label optional), **263** (`sample WAC 3.9\%`), **292** (×6 occurrences: `mean coupon 6.02\%`, `mean coupon 3.37\%`), **301** (`exposure-weighted mean coupon on the surviving book is 3.134\%`), **303**, **339**, **580** (`weighted-average coupon (3.9\%)`), **913**, **976**, **1042**, **1047**, **1102**, **1164**, **1177**.

**Already correctly labeled — do not touch:** tex **761** (`the annual note rate divided by twelve; a 3.0\% coupon`), tex **263**'s pass-through clause.

**Flagged, NOT edited by G2 (§0.3):** tex **152**, **432**, **558**, **740** (the `cross_design_reweight` family) and tex **753**, **784**, **1273** (the ABM multi-vintage endowment). Their disposition is §G2.6.4.

**Assertion to add to the landing commit** (proposed **gate #105**, `COUPON_CONVENTION_SPANS`, presence-only in the style of gates #102/#103/#104):

```
"basis_definition":  "note-rate coupon mix to the SOMA book's face-weighted"
"wedge_named":       "less the guarantee fee and base servicing"
"tex263_label":      <the labeled replacement clause, verbatim>
"tex580_label":      <the labeled replacement clause, verbatim>
"table_header":      "(book pass-through WAC)"
"converted_companion": "\\texttt{coupon\\_convention\\_reweight}"
```

Presence-only, not count-based — the round-27 lesson that every count gate in this repo is `>=` and that an edit priced as tex+gates+tests+letter can be tex-only.

---

# G2.6 — Cross-cutting landing, gates, letter, and the scope question

## G2.6.1 Gate numbering

The current top gate is **#104** (`verdict_audit_check`, `tools/liveness_gates.py:670-690`, printed at `:4678-4684`). G2 proposes:

- **#105** `coupon_convention_check` — the label spans of §G2.5.2 (presence-only) plus a cross-check that the converted companion figures printed in tab:bases equal `coupon_convention_reweight_results.json`'s `φ_0` leg, rounded as printed.
- **#106** `amortization_convention_check` — the disclosure sentence's presence, plus the artifact-level assertion that G2-B's dollar invariance (H1) passed and that the peak lags in `coupon_convention_amortization_results.json` equal the committed ones. This gate's whole point is that it fails if someone later re-bases the empirical series without re-deriving the timing exhibits.

No gate is proposed for G2-C: gate #44 already pins tab:wal's derived literals, and extending it to the converted block is a one-line addition to the existing check rather than a new gate.

## G2.6.2 Tests

`tests/` contains **no** reference to `full_book_weighting`, `shared_layer_scoring`, `wal_table`, or `composition_shift` (verified by grep). The letter mutation tests hard-code historical counts (`tests/test_headline_posture_gate.py:79,151`) but reference none of G2's literals. **G2's landing is tex + artifacts + the two new gates; no test file changes.** Re-verify this by grep immediately before the landing commit — it is a claim about HEAD, not an invariant.

## G2.6.3 Letter, verdicts, runindex

- **Response letter:** one paragraph under R2-W1/S2 stating (i) the wedge is real and has three instances, (ii) the marginal did not move and why it could not, (iii) the composed cell's converted value with its branch disposition, (iv) the timing invariance of the back-out correction. The letter's abstract word count (currently claimed **226**, gate #101) is untouched — G2 does not edit the abstract.
- **tab:verdicts** (tex 1380): one row per sub-run. G2-A's Adjudication cell direction under Branch B is *against the paper's own favourable coincidence*; G2-B's is *neutral* under Branch (i). Gate #104's `row_against_own_pass` discipline means the G2-A row is exactly the kind the table exists to display.
- **tab:runindex** (tex 697): three rows (`coupon_convention_reweight`, `coupon_convention_amortization`, `wal_converted`).

## G2.6.4 ⚖ THE SCOPE QUESTION — `cross_design_reweight` (needs Eugene's call before landing)

The 76.3% cross-design figure is produced by the **same unconverted note-vs-pass-through bucket match** (§0.3). Three options:

- **(I) Run it in this batch.** The patch is the same shape (`coupon_bucket_pct` gains a conversion), the run is expensive (fresh 3,380-point CPR surface builds, plus a floor search under G4's double-execution determinism rule), and the result would move a number that **§IV now leads with** and that gate #100 orders. Highest integrity, highest cost, and it re-opens a settled section.
- **(II) Disclose without running.** One sentence at tex 152 / 558 stating that the cross-design post-stratification matches note-rate buckets against pass-through targets on the same grid, with the ~80 bp wedge named and its direction stated (the reweight over-weights deeply-locked collateral, so 76.3% is if anything an over-statement of the reweighted recovery — **direction to be verified, not asserted**). Cheap, honest, and it leaves a known defect unquantified.
- **(III) Defer to the venue revision** with a TECHNICAL.md entry. Cheapest, and the one that most resembles the thing this paper's own conventions criticize.

**Recommendation: (II) now, (I) scheduled.** Option (III) is not recommended: G2's whole content is that unlabeled conventions matter, and labeling three consumers while leaving the load-bearing fourth silent is the selective disclosure the paper's own verdict table exists to prevent. **This spec does not choose. It records that the choice must be made before the G2 batch lands, because the tex 152/558 edits belong to whichever option is taken.**

---

# G2.7 — MUST NOT CHANGE (the whole batch)

1. **The committed `2.49` and `3.9` artifact values.** `full_book_weighting_results.json → sample_wac_pct = 3.864892813333334`, `composition_shift.py:321/334`, `composition_shift_results.json → committed_anchors`, `soma_book.*.wac_face_weighted_pct`, `wal_table.py:40 WAC = 0.0249`. These are **measurement records under their own stated conventions and they are each correct as such**. The fix is a **label plus a converted companion**, never a restatement. Any edit that changes a committed artifact value is out of spec.
2. **The headline marginal at every floor:** `+$42.6` billion / `+5.6` pp off-window, `+$70.3` billion / `+9.2` pp in-sample, and every cell of the calibration box. Enforced by §G2.4.
3. **FLOOR values and `FLOOR_MODE`:** `INVOLUNTARY_CPR_ANNUAL = 0.04`, the off-window `4.991%`, the 3–5% sweep, `FLOOR_MODE = "max"`.
4. **tab:assembly** (tex 314–334) in its entirety, and gate #98's `ASSEMBLY_SPANS` / `ASSEMBLY_TABLE_SPANS`. G2 adds no assembly row: a coupon-convention correction is a level/composition object, not a member of the marginal's correction assembly.
5. **The abstract** (tex 30). Verified to contain no coupon literal and no composed figure; gate #99's `ABSTRACT_POSTURE` spans and the letter's 226-word claim are untouched by construction.
6. **The binding interval and the posture spans.** Gate #98's `posture_binding_layer` currently reads `$+2.9$ to $+8.7$ points` — G2 touches nothing near it.
7. **Gate-pinned literals G2 must route around:** `2.29` and the other gate-#38 PSI values (tex 1164); gate #44's `(5.61\%) & 9.1 & 8.2`, `(3.39\%) & 10.8 & 9.6`, `0.6-year rule-only shortening`; the `100.4\%` at tex 679 (off-window standalone, **not** the composed cell).
8. **The committed artifacts of §0.4**, byte-identical, enforced by G9/H4/H5/W1.
9. **`hazard/config.py` production defaults**, `LITERATURE_COEFS`, `beta_burnout = -0.5`, `RNG_SEED = 42`, `LOAN_SAMPLE_PATH`.
10. **`pool.coupon`, `pool.rate_gap`, and every hazard input.** Enforced by G3.

---

# G2.8 — Sequencing

```
G2-A  (independent; the invariance check B8 runs inside it)
G2-B  (independent of G2-A; must precede G2-C)
G2-C  (BLOCKED on G2-B via W3)
labels + landing  (one commit; after §G2.6.4's scope call)
```

G2-A's tex 416/576/432 edits and WP-B1's tab:assembly rebuild do not collide (§G2.7 item 4). G2-B's clip diagnostic must be handed to **WP-H1** before H1 executes, or H1 will re-diagnose the same months. G2-C's tab:wal edit and any WP-A wording pass on tex 1311 must be sequenced; assign tex 1311 to whichever lands first and have the other verify.

---

# G2.9 — Where my inputs need re-verification at run time (honest list)

1. **The balance-weighted sample WAC `3.78`** comes from PLAN_review2_fixes_2026-07-28.md:134, not from an artifact. I could not verify it without loading `loan_sample.parquet`. It sets `g₀` in §G2-A.5's projection. **Re-derive as `np.average(coupon, weights=balance)*100` in the run's step 0 and write it to the artifact.** The projection moves by ~0.08 pp between the weighted and unweighted readings, so this does not block the spec, but a materially different value (say 3.60 or 3.95) would move the projected composed cell by ~0.15 pp and must be recorded before the branch classifier fires.
2. **The wedge Δ.** The G1 diagnosis says the offset is "~0.5–0.6pp (≈ one bucket)" and the note-rate WAC is "~3.1%"; this spec's mechanical g-fee + servicing rule gives **0.80 pp**, and 3.29%. These are not contradictory — §G2-B.3 shows the −0.22/−0.23 CPR pp figure is exactly the Δ = 0.60 case — but they are **different numbers for the same object**, and the difference is 40% of the wedge. Whoever executes must reconcile: either the g-fee rule is right and G1's estimate was an empirical bucket-mode distance (which would be biased low by the down-rounding φ deliberately omits, §G2.1.1), or the g-fee figure is too high. **If the reconciliation lands at Δ ≈ 0.60, that is BELOW `φ_lo` and the leg set must be widened to `Δ ∈ {0.60, 0.70, 0.80}` before running, not after.**
3. **`self.vintage` on `LoanPool`.** I verified `vintage` is selected into the sample (`loan_sample.py:74`) and derived at `ingest.py:62-64`, but I did **not** verify that `LoanPool.__init__` retains it — the constructor block I read (`agents.py:119-155`) does not obviously assign it. If it does not, §G2-A.2 item 1's one-line addition is required. Check before writing the patch.
4. **Which basis the printed `5.14\%` is on.** I traced it to `abm/data/latest_run_manifest.json → cpr_pct.empirical.mean = 5.13881153921074` (ABM basis, `PORTFOLIO_COUPON = 0.03`), and G2-C's projection uses the ABM-basis wedge accordingly. If it turns out that `wal_table.py:51 SCENARIOS["empirical"] = 0.0514` was instead taken from the **hazard** series (2.5%), the correct wedge is `+0.296` not `+0.105`, and the Empirical WAL row becomes 9.4/8.5 — i.e. **fully invariant** rather than +0.1. Both outcomes are inside the ±0.2-year band, so the branch does not change, but the printed companion does. Resolve in step 0. Likewise for `no_shock_2021_speeds = 0.2281`, whose provenance comment (`wal_table.py:58`) says only "FRED/SOMA back-out".
5. **The within-bucket distribution in §0.6's split table** assumes `u` is uniform. It is not — the sample's coupons cluster. The realized split is a reported diagnostic (`bucket_diagnostics.shift_split`), and §0.6's percentages are an expectation, not a prediction with a band.
6. **The FHFA per-vintage figures are deliberately absent.** §G2.1.2 states the condition under which `φ_vint` may run. If the operator cannot cite a report year and table, the leg does not run and the artifact says so. Nothing printed may depend on a per-vintage g-fee number that is not sourced to a citable table.
7. **`_reweight_balances_to_soma`'s vintage recovery.** §G2-A.2 item 2 proposes parsing the vintage off `stratum_id` (`vintage_couponbp_ficobucket`, `loan_sample.py:39-46`). I verified the stratum-id construction but **not** that the Path A cohort keys in `simulate.py`'s `cohort_meta` preserve that format end-to-end. Verify before patching; if they do not, Path A's converted leg is dropped from the batch and disclosed rather than approximated.
8. **Gate #38's coupon PSI (`2.29`) under conversion.** The converted sample bucket shares are computed for free inside G2-A (`bucket_diagnostics`), so a converted PSI is available as a reported diagnostic. It is **not** landed into tab:composition by this spec: `composition_shift` is a measurement of the two conventions as they stand, and re-running it is out of scope. If the coordinator wants the converted PSI in tab:composition, that is a separate decision with a separate landing rule.

---

## PRE-RUN AMENDMENT G2-AM1 (labeled, 2026-07-29 — coordinator resolution of §G2.9 item 2, the Δ disagreement)

The G1 diagnosis's "~0.5–0.6 pp" was an assumption (2.49 + ~0.6 ≈ 3.1), not a
derivation; the g-fee arithmetic (55 bp flat + 25 bp servicing → Δ = 0.80) is the
derivation, with the caveat that FHFA reports TOTAL g-fee (ongoing + amortized
upfront) while only the ongoing portion separates note from pass-through — so
0.80 is an upper-leaning central. Resolution by measurement, not adjudication:
**the Δ leg set widens to {0.60, 0.70, 0.80, 0.90}** (one added leg, same
construction; the Δ=1.00 mechanism leg stays). The primary quoted leg remains
Δ = 0.80 per the spec's rule; the 0.60 leg brackets the G1 reading and its
distance from the 0.80 leg is reported as the conversion-uncertainty span.
Everything else in the spec is unchanged.
