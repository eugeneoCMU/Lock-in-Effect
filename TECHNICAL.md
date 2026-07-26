# Technical Narrative — Lock-In Effect Project

This document is the **repository-level** technical history: what was built, what broke, what was fixed, what was falsified, and why the codebase now has two frameworks (`abm/` and `hazard/`). It is written for a reader who wants the full causal chain from the original **$972.3B** headline to the current validated **$764.7B** empirical benchmark and the current reconciled model results: the ABM explains **11.1%** on its synthetic population (post native 15-year gate, §19) but **59.3%** when fed real Freddie structural covariates with a recalibrated anchor (§15 Fix 1) — the share is calibration- and data-source-dependent, and both figures must be quoted together (§18). The hazard paths recover 107–121.5% of the benchmark (Path A spec v4 calendar-month production as of the 2026-07-14 freeze, §22.5), but an executed no-lock-in null (β₁=0) recovers **97.8%** (§12), so aggregate benchmark recovery is not by itself evidence about lock-in; the frameworks are distinguished by marginal lock-in contribution and monthly CPR-path fit. The Danish institutional gap is approximately **zero** under estimated elasticities, with its sign not identified (§20–§20.1). A July 2026 robustness-fix program (§15) plus follow-on analyses (§16–§19) revised the headline figures and added permutation, cross-foundation, and synthetic-companion tests — see those sections for what changed and why.

For module-level runbooks, see [README.md](README.md). For hazard pipeline specs, see [hazard/README.md](hazard/README.md). The former `abm/TECHNICAL.md` (granular ABM archaeology) and `REVISION_VERIFICATION.md` (manuscript verification record) were consolidated into this file on 2026-07-11 — see [Appendix B](#appendix-b--abm-era-granular-archaeology) and [§22](#22-manuscript-verification-record-referee-rounds-july-2026); their full texts remain in git history.

---

## Table of Contents

1. [Economic Question](#1-economic-question)
2. [Repository Evolution](#2-repository-evolution)
3. [Empirical Benchmark: From $972.3B to $764.7B](#3-empirical-benchmark-from-9723b-to-7647b)
4. [ABM Architecture and Role](#4-abm-architecture-and-role)
5. [ABM Correctness Fixes and Validation Suite](#5-abm-correctness-fixes-and-validation-suite)
6. [Mechanisms Tested and Falsified in the ABM](#6-mechanisms-tested-and-falsified-in-the-abm)
7. [Danish Counterfactual: Three Stages of Bugs](#7-danish-counterfactual-three-stages-of-bugs)
8. [Why the Residual Persisted](#8-why-the-residual-persisted)
9. [Pivot to the Hazard Framework](#9-pivot-to-the-hazard-framework)
10. [Hazard Path A — Cohort Fractional Model](#10-hazard-path-a--cohort-fractional-model)
11. [Hazard Path B — Literature Microsim](#11-hazard-path-b--literature-microsim)
12. [Current Headline Numbers](#12-current-headline-numbers)
13. [Architectural Decisions](#13-architectural-decisions)
14. [Known Limitations and Next Steps](#14-known-limitations-and-next-steps)
15. [Robustness Fix Program (July 2026)](#15-robustness-fix-program-july-2026)
16. [Permutation Test — Does Path B Depend on Joint Covariate Structure?](#16-permutation-test--does-path-b-depend-on-joint-covariate-structure)
17. [Cross-Foundation Checks — Hybrid Pipeline and Full-Book Weighting](#17-cross-foundation-checks--hybrid-pipeline-and-full-book-weighting)
18. [Symmetric Companion Test — Synthetic Population into the Hazard Framework](#18-symmetric-companion-test--synthetic-population-into-the-hazard-framework)
19. [Native 15-Year Behavioral Gate](#19-native-15-year-behavioral-gate)
20. [Berger et al. Danish Recalibration — Two Estimated Channels](#20-berger-et-al-danish-recalibration--two-estimated-channels)
21. [July 2026 Verification Round — Committed Artifacts and Manuscript v14](#21-july-2026-verification-round--committed-artifacts-and-manuscript-v14)
22. [Manuscript Verification Record (Referee Rounds, July 2026)](#22-manuscript-verification-record-referee-rounds-july-2026)

Appendices: [A — File Map](#appendix-a--file-map) · [B — ABM-Era Granular Archaeology](#appendix-b--abm-era-granular-archaeology)

---

## 1. Economic Question

When the Federal Reserve began **Quantitative Tightening (QT)** in June 2022, it targeted a phased reduction in its Mortgage-Backed Securities (MBS) holdings. The plan assumed mortgages would prepay at something close to historical turnover rates. Instead, the post-2022 rate shock created a **lock-in effect**: households with below-market fixed coupons faced punitive par-payoff math if they moved or refinanced, crushing voluntary prepayment.

The empirical signature is **extension risk** — actual MBS roll-off consistently fell short of the QT cap, keeping MBS on the Fed's balance sheet far longer than planned.

**Terminology.** "Trapped liquidity" is used throughout as shorthand for the **cumulative QT roll-off shortfall versus the cap** — an extension/duration phenomenon. It is *not* a claim about monetary liquidity: slower runoff means the balance sheet shrinks (and reserves drain) *more slowly*, so nothing is trapped in a monetary-operations sense. Where precision matters, read "trapped liquidity" as "QT roll-off shortfall" or "extension shortfall."

This project quantifies that shortfall and asks two structural questions:

1. **How much liquidity was trapped, and is the measurement defensible?**
2. **How much of the shortfall is explained by household lock-in under U.S. mortgage rules, versus other mechanisms (pool composition, servicer pipelines, income stress, institutional design)?**

The **Danish counterfactual** isolates institutional design: Danish borrowers can buy back mortgage debt at **market price** rather than par, neutralizing lock-in when rates rise. Contrasting U.S. and Danish simulated roll-off paths separates *rate dynamics* from *contract design*.

**Outcome (so the motivation is not read as the conclusion):** under Berger et al.'s *estimated* Danish elasticities the institutional gap collapses to **approximately zero**, and its sign is not identified (§20–§20.1). The large early gap estimates (±$900B range) were artifacts of extrapolating a U.S.-calibrated mobility function to a Danish rate gap.

---

## 2. Repository Evolution

The project went through three structural phases:

| Phase | Layout | What changed |
|---|---|---|
| **v1 — Monolithic** | Scripts at repo root | `abm_lockin_simulation.py`, `fed_mbs_extension_risk.py`, validation suite, CSV/PNG outputs |
| **v2 — ABM archive** | `abm/` subdirectory | All agent-based work moved under `abm/`; `paths.py` centralizes output paths; root `README.md` becomes an index |
| **v3 — Dual framework** | `abm/` + `hazard/` | New Freddie Mac reduced-form hazard pipeline alongside frozen ABM; literature microsim with competing risks |

**Why reorganize?** The ABM pipeline had grown into a self-contained research artifact (simulation, macro scoring, sensitivity, robustness, Monte Carlo, 500+ lines of bug history). Separating it under `abm/` keeps that archive intact while allowing a structurally different estimator (`hazard/`) to evolve without entangling imports or output paths.

**What stayed frozen:** `abm/abm_lockin_simulation.py` utility-gate logic is not the estimation engine for the hazard framework. The ABM remains the behavioral counterfactual and validation baseline.

---

## 3. Empirical Benchmark: From $972.3B to $764.7B

The original pipeline reported **$972.3B** in cumulative trapped liquidity. Independent reasoning (Fed ~$600B actual redemptions vs. cap-implied shortfall) suggested the true figure was closer to **$800–870B**. Investigation found **four compounding errors**:

### Error 1 — Flat QT cap (why it inflated the headline)

The code assumed **-$35B/month** from June 2022 onward. In reality, QT ramped at **-$17.5B/month** for three months (June–August 2022) before reaching full **-$35B/month** in September 2022. Treating ramp months as full-pace overstated early shortfalls.

**Fix:** `compute_qt_target_series()` with `QT_TARGET_RAMP_B = -17.5`, `QT_TARGET_FULL_B = -35.0`, `QT_RAMP_END = 2022-09-01`.

### Error 2 — WSHOMCB settlement and amortized-cost noise (why roll-off was wrong)

Actual roll-off was computed as `WSHOMCB.diff()`. `WSHOMCB` is booked at **amortized cost on a settlement-date basis**, not current face value. Premium amortization on pandemic-era purchases conflates accounting drift with real principal paydown.

**Fix:** Prefer NY Fed SOMA API **current face value** (`fetch_soma_mbs_monthly()`). SOMA and WSHOMCB now agree to within **0.1%** on the trapped total, but SOMA is the preferred source.

### Error 3 — One-sided accumulation (why Danish broke completely)

Cumulative trapped liquidity used `.clip(lower=0)`, accumulating only months where roll-off fell short of cap. This had negligible effect on the U.S. series (no month exceeded cap) but **zeroed the entire Danish counterfactual** — see [Section 7](#7-danish-counterfactual-three-stages-of-bugs).

**Fix:** Net accumulation: `Extension_Delta_Billions.fillna(0.0).cumsum()` over the active QT window, no clipping.

### Error 4 — QT window boundary (why $672.9B became $764.7B)

Earlier versions summed all months `>= QT_START` without an upper bound. QT ended December 2025, but the data series extends past it. Post-QT months added spurious negative deltas while the cumulative series flatlined, **understating** the headline.

**Fix:** `qt_active_mask()` restricts accumulation to `QT_START ≤ month < QT_END` (June 2022 – November 2025).

**Result:** Validated empirical benchmark **$764.7B** (SOMA, phased cap, active QT window only).

---

## 4. ABM Architecture and Role

The agent-based model ([`abm/abm_lockin_simulation.py`](abm/abm_lockin_simulation.py)) simulates **10,000 heterogeneous households** deciding whether to move under a rate shock. Each household has income, home value, mobility desire, transaction-cost draw, and patience draw.

### Institutional regimes

| Regime | Payoff rule | Lock-in when rates rise |
|---|---|---|
| **U.S.** | Prepay at par (outstanding principal) | Large effective penalty — golden handcuff |
| **Danish** | Buy back at market PV of remaining payments (capped at par) | Lock-in neutralized — debt retired at discount |

### Behavioral gates (literature-grounded, not tuned to $764.7B)

1. **DTI hard wall** — 43% housing-payment/income, applied **front-end**. Caveat: the CFPB QM/ATR 43% threshold is a *back-end total-debt* ratio; the model has no non-housing debts (§14), so this gate is QM-*inspired* rather than QM-implementing, and binds less often than the regulation would
2. **Loss aversion** — payment increases scaled 2.25× (Kahneman-Tversky)
3. **Wait-and-see** — 20% freeze when 6-month rate change exceeds 150 bps

### Output: 3D CPR surface

The ABM precomputes a **Conditional Prepayment Rate (CPR) surface** over `(market_rate × dynamic_friction × rate_velocity)` per coupon cohort. The macro pipeline ([`abm/fed_mbs_extension_risk.py`](abm/fed_mbs_extension_risk.py)) interpolates this surface month-by-month, weighted by live NY Fed SOMA coupon composition, to simulate counterfactual Fed roll-off.

**Why a surface, not online simulation?** Building the 3D grid (3,380 points × 7 cohorts) once and interpolating is ~120× faster than per-month household loops, making Monte Carlo (50 seeds) feasible in minutes.

### Calibration anchor

`calibrate_mobility_scale()` sets involuntary turnover so CPR at 8% market rate hits a **4–5% floor** (death, divorce, distress moves). This anchor is independent of the empirical trapped target and cannot be dropped without breaking the model's connection to real-world baseline turnover.

---

## 5. ABM Correctness Fixes and Validation Suite

Beyond the empirical benchmark fixes, the ABM–macro link received structural corrections:

| Fix | Problem | Solution |
|---|---|---|
| **Scheduled amortization** | Simulated roll-off used CPR only, missing routine principal paydown | `scheduled_amortization_smm()` added to all roll-off paths (~$224B over QT) |
| **Multi-vintage cohorts** | Flat 3.0% coupon misrepresented Fed book (WAC ≈ 2.55%) | Live SOMA CUSIP parse → 7 coupon buckets with weights |
| **Cohort-weighted SMM** | Empirical CPR back-out used single-coupon amort | Per-cohort scheduled amort, weighted to SOMA composition |
| **Reference cohort** | Mobility calibrated on wrong coupon | Max-weight **2.0%** cohort (39.7% of book) as calibration reference |
| **Cohort bucket folding** | Tiny tail buckets unstable | `min_share = 2%` merges into nearest survivor |
| **Settlement-lag kernel** | TBA remittance delay between decision and SOMA receipt | `[0.10, 0.60, 0.30]` convolution — tested, largely null (see below) |
| **Vectorization** | 3D surface + Monte Carlo infeasible in Python loops | `_precompute_arrays()` + `_cpr_vec()` — 120× speedup |

### Validation suite

| Script | What it tests |
|---|---|
| [`abm/sensitivity_analysis.py`](abm/sensitivity_analysis.py) | 125-scenario sweep of friction parameters |
| [`abm/robustness_analysis.py`](abm/robustness_analysis.py) | Empirical side: SOMA vs WSHOMCB, cap-schedule variants |
| [`abm/monte_carlo_simulation.py`](abm/monte_carlo_simulation.py) | 50 population draws, CPR surface rebuilt per seed |

**Bug found in sensitivity:** early versions compared ABM trapped to itself (trivially 100% share explained). Fixed by anchoring to independent `Extension_Delta_Billions` sum.

---

## 6. Mechanisms Tested and Falsified in the ABM

Each extension was **pre-registered** with an expected direction before running. Several moved the model the **wrong way**:

### Behavioral extensions (DTI + loss aversion + wait-and-see)

**Hypothesis:** Residual unexplained trapped liquidity reflects credit constraints and prospect-theory frictions.

**Result:** Share explained **fell** from 80.8% to 62.3% (historical pre-QT-window figures). Loss aversion steepened the penalty function, forcing mobility-scale recalibration upward to maintain the 4–5% turnover floor — which **increased CPR at all rate levels**, including the 5–7% band where most QT data lives.

**Conclusion:** Not a bug. An honest finding that behavioral frictions + turnover anchor can increase predicted mobility.

### Curtailment channel (income-driven partial prepayment)

**Hypothesis:** Missing curtailment explains over-prediction bias in high-income months.

**Pre-registration:** Curtailment is additive-only; should **worsen** aggregate match by $60–90B.

**Result:** Trapped liquidity fell $75B — exactly as predicted. CPR path diagnostics unchanged.

**Conclusion:** The ABM already over-predicts roll-off; adding more voluntary prepayment deepens the bias.

### Multi-vintage coupon cohorts

**Hypothesis:** Replacing flat 3.0% with real SOMA composition (dominated by 2.0–2.5% coupons) increases trapped liquidity (larger rate gap).

**Result:** Trapped liquidity **fell** $87B (51.2% → 38.3% share, historical). Weighted CPR **rose** to 8.67% vs empirical 5.53%.

**Conclusion:** Pool composition is real but swapping coupon weights does not close the gap. The household lock-in mechanism still produces too much aggregate mobility.

### Vintage burnout via survivor selection

**Hypothesis:** Path-dependent burnout (removing movers from the population each month) lowers late-sample CPR and raises trapped liquidity.

**Implementation:** `simulate_cohort_path()` walks historical rate paths; movers permanently removed from survivor pool.

**Result:** QT-window CPR collapsed to **~0%**; trapped liquidity hit **$1,124B (147% of empirical)** — opposite direction.

**Diagnosis:** The closed 10,000-agent population depletes its mobile mass in the 2020–21 low-rate window before QT begins. Survivors are exclusively never-movers — an absorbing state incompatible with a real MBS pool that retains involuntary turnover and ongoing origination.

**Production decision:** `use_burnout=False`. Code retained for reproducibility.

### Settlement-lag kernel

**Hypothesis:** Weak cross-correlation peak at lag -3 reflects TBA settlement timing; convolving roll-off should align timing.

**Result:** Peak unchanged at lag -3 (r = +0.192). Trapped liquidity shifted modestly ($117.7B → $101.2B) because kernel is mass-conserving.

**Conclusion:** Timing lag is not the binding residual. Kernel kept in production as documented null result.

---

## 7. Danish Counterfactual: Three Stages of Bugs

The Danish counterfactual was the most serious bug chain in the project:

| Stage | Danish Trapped | Institutional Gap | Root cause |
|---|---|---|---|
| **0** | **$0.0B** | ≈ U.S. only | `.clip(lower=0)` zeroed every month of overshoot |
| **1** | **-$1,132B** | $1,676B | ~47% Danish CPR (market-value surface, pre-Berger §20) applied to static U.S. balance |
| **2 (current)** | **-$829.1B** | **$930.3B** | Dynamic declining-balance simulation per cohort |

**Why Stage 0 happened:** Danish CPR was high under the market-value-buyback surface (**36–51%**, mean **47.2%** over the 42-month active QT window; the older rational-only calibration was ~21–27%). Simulated roll-off consistently **exceeded** the QT cap, producing negative extension deltas every month. One-sided clipping turned all negatives to zero. (That ~47% surface is itself superseded by the Berger recalibration, §20, which brings Danish CPR to ~3.4%.)

**Why Stage 2 is correct:** Danish balance is simulated forward month-by-month from QT-start holdings, applying Danish CPR + scheduled amort + curtailment to the *already-shrunk* balance each month.

**Interpretation caveat:** Danish friction was U.S.-calibrated here — the $930.3B institutional gap is an **upper bound** under U.S.-style transaction costs. **This was superseded by the Berger et al. recalibration (§20)**, which imports estimated Danish elasticities and collapses the gap to approximately zero (Path B hybrid −$99.9B), showing the large gap was an artifact of extrapolating the U.S. mobility function to a Danish rate gap.

---

## 8. Why the Residual Persisted

*(Figures below are as of the pre-15yr-foldin, synthetic-population ABM. Current production figures are $84.5B / 11.1% — see [§12](#12-current-headline-numbers), [§15](#15-robustness-fix-program-july-2026), and [§19](#19-native-15-year-behavioral-gate); [§18](#18-symmetric-companion-test--synthetic-population-into-the-hazard-framework) shows real Freddie covariates recover 59.3% under recalibration while the hazard framework recovers the benchmark even on synthetic data — results that revisit the diagnosis below.)*

After all ABM fixes, extensions, and falsifications, the production pipeline explains **13.2%** of the $764.7B empirical trapped liquidity ($101.2B simulated vs $764.7B actual). The ABM **over-predicts** aggregate CPR (mean 11.98% vs empirical 5.53%) while **under-predicting** trapped liquidity — a sign that the monthly CPR *path* is wrong-shaped, not merely scaled wrong.

Mechanisms **outside** the household decision function likely dominate the residual:

- **Loan-level heterogeneity** (FICO, LTV, geography) not captured by representative-coupon buckets
- **Servicer forbearance, modification, and pipeline delays** not modeled in the ABM
- **Path-dependent vintage burnout** that cannot be implemented as closed-population survivor selection
- **Ongoing origination and pool replenishment** absent from a fixed 10,000-agent cohort
- **Competing risks** — high rates suppress mobility but stress balance sheets, shifting mass from prepay to delinquency/default pipelines

This diagnosis motivated the `hazard/` framework.

---

## 9. Pivot to the Hazard Framework

**Why not keep extending the ABM?** The ABM answers: "What would a representative household do under utility maximization with institutional payoff rules?" The residual suggests the binding constraints are **not** in that utility function — they are in **loan-level survival dynamics**, **servicer state transitions**, and **cohort path dependence**.

**Design principles for `hazard/`:**

1. **No mobility desire, loss aversion, or utility gates** — replaced by proportional hazards on real loan outcomes
2. **Freddie Mac loan-level data** as the empirical foundation (Polars lazy scan, never materialize full loan-month panels)
3. **Cohort-month aggregation** for estimation; optional **loan-level microsim** for competing risks
4. **Markov servicer pipeline** replaces the ABM's fixed `[0.10, 0.60, 0.30]` settlement kernel
5. **Same $764.7B benchmark** and QT window definitions as `abm/` for comparability

---

## 10. Hazard Path A — Cohort Fractional Model

**Pipeline:** `ingest.py` → `hazard_fit.py` → `markov.py` → `simulate.py` → `extension_risk.py`

### Ingest

Polars lazy-scans Freddie `orig_*.txt` / `perf_*.txt`, immediately aggregates to cohort-month cells:

`(vintage, coupon, fico_bucket, ltv_bucket, period)`

Synthetic fixture (5,000 loans) auto-generated when real files absent.

### Hazard model (spec v3)

Discrete-time **Poisson GLM** with log(exposure) offset and **stratum fixed effects**:

$$\log(h_{c,t}) = \text{spline}(\text{loan\_age}) + \beta_1 \cdot \text{RateGap\_bps}_t + \beta_2 \cdot \text{Burnout\_orth}_{c,t} + \beta_3 \cdot \text{Friction}_t + \text{FE}(\text{stratum})$$

- **Stratum FE:** 295 dummies for `(vintage, coupon, fico_bucket, ltv_bucket)` cross-sections — absorbs baseline pool fastness so burnout measures within-pool adverse selection
- **Burnout_orth:** within-stratum demeaned stock, orthogonalized on age spline
- **Ridge:** α=1e-5–1e-4 selected on holdout RMSE (IRLS fails with 295 FE; mild ridge required)

**Spec evolution:** Spec v2 used vintage-year FE (4 dummies) and left β(burnout) positive (+0.76). Spec v3 replaced vintage FE with 295 stratum dummies and within-stratum demeaned burnout, flipping the sign to −0.13.

### Real-data results (Freddie 2017–2021, 20 quarters)

> **Status: robustness exhibit, not a headline estimate.** Path A's monthly
> CPR is *anticorrelated* with the empirical series (r(lag 0) = −0.444), its
> holdout RMSE (~38pp) is large against ~5% CPR levels, stratum-bootstrap
> CIs (§21) leave only the rate-gap coefficient distinguishable from zero
> (burnout and friction are controls, not findings), and §16's permutation shows
> β(rate_gap) is not sign-stable under covariate scramble ([−1.13, +1.19]).
> The $915B (119.7%) aggregate is retained for the fitted-vs-literature
> contrast (§16, §18) and should not be quoted as a standalone estimate.
> (Status note superseded at the 2026-07-14 freeze: the calendar-month
> spec v4 is now production Path A — §12 and §22.5.)

| Metric | Value |
|---|---|
| Trapped liquidity | **$915B (119.7%)** |
| β(rate_gap_bps) | +0.67 (standardized; stratum-bootstrap 95% CI **[+0.60, +4.11]**, sign stable in 99.5% of reps, §21) |
| β(burnout_orth) | **−0.13** (n.s. — bootstrap CI [−1.76, +1.43], §21; sign also not stable under permutation, §16) |
| β(friction) | −0.037 (n.s. — bootstrap CI [−0.25, +1.38], §21) |
| CPR r (lag 0) | −0.444 |
| Holdout RMSE | ~38pp |

### Forward simulation

`simulate.py` drains cohort balances deterministically: `balance × hazard` each month. Fractional prepay settles **directly** to SOMA roll-off — **no settlement-lag convolution** in the hazard path (by design; see CPR timing in [hazard/README.md](hazard/README.md)).

### CPR timing and settlement lag

| Path | CPR r (lag 0) | Peak lag | Peak r |
|---|---|---|---|
| Literature microsim | +0.368 | **−3** | **+0.444** |
| Empirical cohort GLM (spec v3) | −0.444 | 0 | −0.444 |

**Convention (corrected in the v15 referee round, §22.3b):** under the implemented cross-correlation, a peak at lag −3 means the **empirical path leads and the simulated path trails** by ~3 months — a synthetic-data test proved the direction. The earlier settlement-pipeline reading (hazard CPR leads SOMA by the TBA delay) had the two series interchanged and is **retracted**. The β₁=0 null shares the −3 peak and the peak correlation is not distinguishable from zero under block-bootstrap bands, so no timing credential attaches to any estimator; the estimators are distinguished by level accuracy and the +9.2pp lock-in marginal only.

The ABM tested a `[0.10, 0.60, 0.30]` settlement kernel and found it **null for timing** ([Appendix B.8](#b8-settlement-lag-kernel--pre-registered-null)). Empirical cohort lag-0 negative r reflects contemporaneous alignment misspecification, not a failure to model settlement delay.

---

## 11. Hazard Path B — Literature Microsim

Added after the cohort model to address competing risks, literature-calibrated elasticities, and clean Danish counterfactual isolation — without reviving the utility ABM.

### Architecture

```
loan_sample.py  →  75k stratified loans with stratum_id
       ↓
microsim_engine.py  ←  literature_hazard.py (PSA h₀, Rothstein β₁)
       ↓              rate_gap.py (US par vs Danish market-value)
       ↓              competing_risks.py (normalized hazards + Markov)
microsim_results.parquet
       ↓
extension_risk.py --mode literature
       ↓
fed_mbs_extension_risk.py  (use_hazard_microsim=True)
```

### Agent model

`MortgageAgent` backed by vectorized `MicrosimPool` (75,000 loans). Static covariates: FICO, region, orig LTV, coupon, `stratum_id`. Dynamic: loan age, balance, regime-specific rate gap.

### Burnout — cohort-level only (category correction)

Individual loans prepay entirely (absorbing state) or stay active. **Per-loan fractional burnout is undefined** under this transition structure.

Correct implementation:

1. `cohort_burnout[stratum_id]` accumulates monthly stratum CPR after all prepay transitions
2. Value broadcast to all active agents in that stratum before next month's hazard evaluation
3. Never updated on individual prepay events

### Literature hazard calibration

**Prepay:**

$$h_i^{prep}(t) = h_0(t) \cdot \exp\big(\beta_1 \Delta r_i(t) + \mathbf{\beta}_x^\top X_i + \beta_b \cdot \text{burnout}_{s(i)}\big)$$

**Default (competing risk):**

$$h_i^{def}(t) = h_0^{def} \cdot \exp\big(\gamma_1 \cdot \text{rate\_stress}_i + \mathbf{\gamma}_x^\top X_i\big)$$

**Baseline** \(h_0(t)\): PSA seasoning curve (standard MBS convention).

**Rothstein β₁** — survival-function conversion, **not** divide-by-3:

$$h_m = 1 - (1 - P_q)^{1/3}$$

$$\beta_1 = \ln\left(\frac{h_{m,\text{shocked}}}{h_{m,\text{baseline}}}\right)$$

where a 100bp rate gap reduces quarterly mobility probability \(P_q\) by 6.5% (sensitivity band 5.5%–7.7%).

### Competing risks

Each month per active agent:

1. Compute `h_prepay`, `h_default`
2. **Normalize** if \(h_{prep} + h_{def} > 1\) (row-wise scale)
3. Single uniform draw: prepay → `Prepaid`; default band → `D30`/pipeline; else survive
4. Delinquent agents transition via Markov matrix
5. Voluntary prepay UPB settles to SOMA **same-month** (`settled_b = prepay_upb`, `competing_risks.py`) — no settlement delay is modeled in the hazard path. The Markov matrix governs **delinquency-state transitions only** (`_markov_step_delinquent`). (`route_through_pipeline()` in `markov.py` implements delayed settlement but is **not wired into the microsim** — retained as dead code.)

### Danish counterfactual isolation

Identical \(h_0\), \(\beta_1\), \(X_i\), and draw logic. **Only** the rate-gap function swaps:

| Regime | Rate gap fed into β₁ |
|---|---|
| U.S. par-payoff | `coupon - market_rate` |
| Danish market-value | `(market_PV / balance) - 1` |

When rates rise above coupon, U.S. gap is large and negative → prepay crushed. Danish gap approaches zero → hazard resets toward baseline \(h_0(t)\).

### Bridge to ABM macro pipeline

```python
df = compute_metrics(df, use_hazard_microsim=True)
```

Replaces CPR surface interpolation with microsim paths. Disables the ABM settlement-lag kernel because the hazard path deliberately models **no** settlement delay — prepay settles same-month, and the lag −3 lead vs SOMA (§10) is the *unmodeled* TBA delay appearing in the diagnostic, not delay handled elsewhere. Danish dynamic balance loop unchanged.

### Real-data results (Freddie 2017–2021 sample; post-β₁-units-fix, see §15)

| Metric | Value |
|---|---|
| Trapped liquidity | **$818.5B (107.0%)** — band $810B–$828B at P_q 5.5%–7.7% |
| CPR r (lag 0) | +0.190 |
| **Peak cross-corr** | **lag −3, r = +0.404** (stable across band) |
| Runtime | ~15s cached / ~23s per band point (75k loans × 42 months × 2 regimes) |

Literature microsim is calibrated via defendable bounds (PSA speed, Rothstein band, involuntary floor) — not fitted to $764.7B. Under the corrected convention (§22.3b), the −3 peak means the simulated path **trails** the empirical series; the peak correlation is not distinguishable from zero under block-bootstrap bands and carries no timing credential. The earlier $747B (97.7%) figure predates the β₁ units fix (§15) and is reproducible from the `pre-fix-2026-07` baseline.

---

## 12. Current Headline Numbers

### Empirical anchor (all frameworks)

| Metric | Value |
|---|---|
| Empirical trapped liquidity (SOMA, active QT) | **$764.7B** |
| QT window | June 2022 – November 2025 |
| Empirical CPR mean | 5.53% (30yr-only back-out) / 5.14% (30yr+15yr, current default) |
| SOMA WAC | 2.55% (7 buckets, 30yr-only, 90.6% coverage) / 2.49% (11 buckets, 30yr+15yr, 99.8% coverage) |

### ABM (production: native 15yr gate + Berger Danish recalibration, **`run-2026-07-05-berger`**)

| Metric | Value |
|---|---|
| U.S. trapped liquidity | **$84.5B** (**11.1%** of empirical) |
| Danish trapped (dynamic balance) | **+$812.9B** (Berger elasticities; §20) |
| Institutional gap (U.S. − Danish) | **−$728.4B** (was +$925.5B pre-Berger; see §20 caveat) |
| U.S. CPR mean | 11.76% |
| Empirical CPR back-out | 5.14% (15yr scheduled amort weighted in; §15 Fix 2) |
| Danish CPR mean | **3.36%** (was 44.09%; Berger 3.2% flat moving + ≈0 refi) |
| Institutional wedge (DK − US) | −8.40pp mean |
| Monte Carlo (50 seeds, current pipeline) | mean **$96.7B**, seed-draw std **$24.8B** (production seed ~0.5σ below the mean) |

The defensible institutional-gap headline is the **Path B hybrid −$99.9B** (both
regimes empirically grounded); the ABM's −$728B overstates the reversal because
its U.S. leg is over-predicted (§20).

Lineage (each reproducible): `run-2026-07-04` (30yr-only, $101.2B / 13.2%,
`terms=("30yr",)`) → `run-2026-07-04-15yr-foldin` (structural-only 15yr,
$91.0B / 11.9%, §15 Fix 2) → `run-2026-07-05-native15yr` (native 15yr
behavioral gate, $84.5B / 11.1%, §19) → **`run-2026-07-05-berger`** (Berger
Danish recalibration, U.S. leg unchanged at $84.5B, §20, current). Note: the
§15 Fix 1 cross-design, §17.1 hybrid, and §18 2×2 analyses were run against
the $91.0B / 11.9% baseline; the native-15yr revision shifts the ABM cell by
<1pp and leaves every qualitative conclusion unchanged. Monte Carlo (seeds
0–49, surface rebuilt per draw against this pipeline) puts population-draw
uncertainty at std $24.8B — ~29% of the point estimate — so the ABM headline
should be quoted as **$84.5B ± $25B (1σ population-draw)**, not to three
digits. The production seed sits ~0.5σ below the 50-seed mean ($96.7B). The
95% CI of the *mean* ([$89.8B, $103.6B]) narrows mechanically with seed count
and is not a prediction interval — do not quote it as the uncertainty range.

A second, spec-distinct Monte Carlo exists for the **paper's production
headline** (the $91.0B fold-in freeze): mean **$103.7B**, SD **$24.5B**, CI of
mean [$96.9B, $110.5B], seed 42 reproducing the frozen **$90.98B** to the cent
(34th percentile). It was run at code commit `5cf33a3`, not HEAD, because the
unconditional native gate at HEAD cannot reproduce the fold-in spec; artifacts
are committed under `abm/data/runs/run-2026-07-04-15yr-foldin/monte_carlo_*`
(§21). Do not mix the two MCs: $96.7B belongs to the native-gate pipeline,
$103.7B to the fold-in paper spec.

Reproduce: `cd abm && python3 freeze_run.py --tag <name>` → `data/runs/<name>/manifest.json`. All CPR means use the 42-month active QT window (`qt_active_frame`), not `index >= QT_START` alone.

### Hazard Path A — cohort fractional (Freddie 2017–2021, spec v4 calendar-month; production as of the 2026-07-14 freeze, §22.5)

| Metric | Value |
|---|---|
| Trapped liquidity | **$928.9B (121.5%)** (`run-2026-07-14-pathA-seasonal`) |
| β(rate_gap_bps) | +0.65 (standardized, spec v4 point; the uncertainty exhibit remains spec v3 — stratum-bootstrap 95% CI **[+0.60, +4.11]**, sign stable in 99.5% of reps, §21 — because bootstrap replications under the seasonal design are branch-unstable, §22.5) |
| β(burnout_orth) | **−0.17** (spec v3 CI [−1.76, +1.43], §21; sign also not stable under permutation, §16) |
| β(friction) | −0.007 (month dummies absorb most within-year variation of the time-only friction index; spec v3 CI [−0.25, +1.38], §21) |
| Month log-effects (Jan = 0) | +0.12 to +0.43 (peak March/September–October) |
| CPR r (lag 0) | −0.378 |
| Peak cross-corr | lag −2 |
| Mean sim CPR | 3.34% |
| Holdout RMSE | ~38pp (spec v3; not re-evaluated at adoption) |
| Stratum FE | 295 four-way pools |

Prior spec v3 ($915.1B / 119.7%, r(lag0) −0.444, +0.67/−0.13/−0.037) is
preserved as `hazard_coefficients_specv3.json`; `permutation_test_pathA.py`
remains a spec-v3 exhibit.

### Hazard Path B — literature microsim (Freddie 2017–2021, post-β₁-fix)

| Metric | Value |
|---|---|
| Trapped liquidity | **$818.5B (107.0%)** |
| Rothstein band (5.5%–7.7%) | $810B – $828B (105.9%–108.2%) |
| CPR r (lag 0) | +0.190 |
| **Peak cross-corr** | **lag −3, r = +0.404** |

**Which number is production — balance-weighted vs full-book.** The Path A/B
headlines above are the **balance-weighted sample estimates** (Freddie
2017–2021 sample composition); they remain the quoted production numbers
because the loan sample is the estimation population. §17.2's full-book SOMA
reweighting (Path B **109.1%**, Path A **126.1%**) is the more
portfolio-faithful projection onto the Fed's actual coupon mix and should
accompany the headline as the primary robustness reading — the
balance-weighted figures understate lock-in by the sample's coupon skew
(WAC 3.4% vs SOMA 2.5%).

### No-lock-in null — what benchmark recovery can and cannot validate

An explicit null run ([`hazard/no_lockin_null.py`](hazard/no_lockin_null.py))
executes Path B with the lock-in elasticity disabled exactly — `p_q_shock_pct=0`,
so `rothstein_beta1(0) == 0` (regression-tested in
[`tests/test_units_conventions.py`](tests/test_units_conventions.py)) — on the
identical 75k loan sample and RNG seed. The mechanical model (PSA seasoning
baseline, involuntary floor, FICO/LTV covariates, burnout, competing-risk
default, scheduled amortization) recovers:

| Metric | No-lock-in null (β₁=0) | Central (P_q 6.5%) | Lock-in marginal |
|---|---|---|---|
| Trapped liquidity | **$748.2B (97.8%)** | $818.5B (107.0%) | **+$70.3B (9.2pp)** |
| CPR r (lag 0) | **+0.367** | +0.190 | −0.177 |
| Peak cross-corr | lag −3, r = +0.444 | lag −3, r = +0.404 | — |

This corroborates the §15 Fix 3 accident (pre-fix inert channel: $747.3B /
97.7%) as a designed experiment: a $35B/month cap sits far above what routine
turnover plus amortization delivers on this book, so nearly all of the
$764.7B shortfall exists with *no* lock-in channel at all. Note also that the
null's contemporaneous CPR correlation (+0.367) is *better* than the central
run's (+0.190) — switching the lock-in channel on buys +$70B of aggregate
level at the cost of monthly path fit.

Three implications, which govern how every recovery figure in this document
should be read:

1. **The lock-in channel's marginal contribution in Path B is +$70.3B
   (9.2pp of benchmark)** — that, not the 107%, is the quantity the lock-in
   mechanism is responsible for.
2. **"Recovers ~100% of the benchmark" is not by itself evidence for a
   lock-in mechanism.** Any amortization-respecting model clears most of the
   bar; model comparisons must be stated as marginal contribution above the
   null and judged on the monthly CPR-path diagnostics, where the frameworks
   genuinely differ (r(lag 0): ABM ≈ −0.32, Path A −0.44, Path B +0.19).
3. **This reframes §18.** Path B's 106.0% recovery on a fully synthetic
   population is *expected under the null* — the survival structure plus a
   coupon marginal recovers the level because the level is mostly mechanical —
   so the 2×2's hazard row demonstrates the benchmark's insensitivity to
   loan-level data, not independent confirmation of the survival paradigm.

Reproduce: `cd hazard && python3 no_lockin_null.py` →
`data/no_lockin_null_results.json` (cache `microsim_results_pq0.0.parquet`).

### 12.1 Involuntary-turnover floor sweep (pre-registered)

The 4% floor is calibrated on in-window 2023–24 discount-cohort turnover
(the floor-circularity concession, manuscript §V.C / App. B), so the null
comparison above inherits a floor-level assumption. A pre-registered sweep
([`hazard/floor_sweep.py`](hazard/floor_sweep.py), spec committed before any
run in `ad52db6`; ex-ante threshold: marginal stable within ±2pp over the
empirically plausible 3–5% floor range) reran the central and null legs at
seven floors, production convention otherwise. Parity gates at 4.0%
reproduce the committed artifacts exactly, and the bind instrumentation
reproduces the published 36.3% of 1,683,124 evaluated loan-months.

| Floor (ann. CPR) | Null $B (%) | Central $B (%) | Marginal $B (pp) | Floor binds |
|---|---|---|---|---|
| 2.0% | 763.1 (99.8) | 849.4 (111.1) | +86.4 (+11.3) | 3.9% |
| 3.0% | 758.6 (99.2) | 841.3 (110.0) | +82.7 (+10.8) | 12.1% |
| 3.5% | 754.4 (98.6) | 832.8 (108.9) | +78.5 (+10.3) | 21.6% |
| **4.0%** | **748.2 (97.8)** | **818.5 (107.0)** | **+70.3 (+9.2)** | **36.3%** |
| 4.5% | 738.9 (96.6) | 796.5 (104.2) | +57.6 (+7.5) | 53.5% |
| 5.0% | 724.6 (94.8) | 766.9 (100.3) | +42.3 (+5.5) | 69.1% |
| 6.0% | 674.6 (88.2) | 692.1 (90.5) | +17.4 (+2.3) | 88.7% |

The ex-ante threshold trips: the marginal spans **+10.8pp → +5.5pp across
3–5% floors** (range 5.28pp > 2pp). Mechanism: the hazard is
`max(floor, h_vol)`, so wherever the floor binds the elasticity is inert;
raising the floor mechanically crowds out the lock-in channel (bind share
12% → 69% across that range). Governing implication, superseding the
unqualified reading of implication 1 above: **the +9.2pp marginal is itself
conditional on the floor calibration — its sign is floor-robust (positive
at every swept floor, +2.3pp even at 6%), its magnitude is not.** Manuscript
sentences presenting the marginal as the floor-independent "clean
verification content" must state the 5.5–10.8pp range over the empirically
plausible floor band — executed in the v16 weakening pass (§22.4(d)).
Artifact:
[`hazard/data/floor_sweep_results.json`](hazard/data/floor_sweep_results.json)
(per-run parquets regenerable, gitignored).

**Floor × band cross** ([`hazard/floor_band_cross.py`](hazard/floor_band_cross.py),
pre-registered `651d1a0`): the calibration box has a second axis, the
Rothstein 5.5–7.7% band. Running both band edges across all seven floors
(central row and nulls reused from the committed artifacts; parity gates at
the 4% floor reproduce `extension_risk_band_literature.json` exactly)
completes the box. Lock-in marginal in pp of benchmark:

| Floor | p_q 5.5 | p_q 6.5 | p_q 7.7 | Bind (7.7) |
|---|---|---|---|---|
| 2.0% | +9.7 | +11.3 | **+13.2** | 4.4% |
| 3.0% | +9.3 | +10.8 | +12.6 | 14.3% |
| 3.5% | +8.9 | +10.3 | +11.8 | 25.9% |
| 4.0% | +8.1 | **+9.2** | +10.4 | 42.2% |
| 4.5% | +6.7 | +7.5 | +8.4 | 59.5% |
| 5.0% | +5.0 | +5.5 | +6.0 | 73.7% |
| 6.0% | +2.1 | +2.3 | +2.4 | 90.8% |

Both ex-ante monotonicities hold (marginal decreases in floor, increases in
band; bind share increases in both axes). **Box maximum = +13.17pp
($100.7B) at the (2% floor, 7.7) corner** — the expected corner, inside the
ex-ante 12–14pp range. Ceiling phrasing note: 13.17% of benchmark exceeds
"about an eighth" (12.5%); a ceiling sentence should say "never exceeds
roughly 13%" (or "about a seventh" if a fraction is wanted), and even
restricted to the empirically plausible 3–5% floor band the box maximum is
+12.6pp, still above an eighth. The "roughly 13%" phrasing was adopted in
the v16 weakening pass (§22.4(d)). Artifact:
[`hazard/data/floor_band_cross_results.json`](hazard/data/floor_band_cross_results.json).

---

## 13. Architectural Decisions

| Decision | Choice | Why |
|---|---|---|
| Empirical roll-off source | SOMA current face value | Removes amortized-cost confound in WSHOMCB |
| QT accumulation window | `qt_active_mask()` | Prevents post-QT dilution |
| ABM estimation unit | 10,000 households + CPR surface | Fast interpolation; Monte Carlo feasible |
| Turnover floor | 4–5% at 8% rates | Grounded in involuntary mobility data; non-negotiable anchor |
| Burnout in ABM | Survivor selection rejected | Closed population depletes mobile mass → 0% CPR |
| Burnout in hazard microsim | Cohort-level `stratum_id` broadcast | Per-loan fractional burnout is a category error |
| Burnout in hazard GLM | Within-stratum demeaned stock + stratum FE | Vintage-year FE left wrong sign (+0.76) |
| Hazard GLM fixed effects | 295 stratum dummies (4-way cohort) | Vintage FE (4 dummies) insufficient for cross-section heterogeneity |
| Rothstein β₁ | Survival-function conversion | Divide-by-3 mis-scales quarterly elasticity |
| Competing risks | Normalized hazard sum ≤ 1 | Independent literature priors can exceed unity in tails |
| Settlement timing | No delay modeled (hazard) vs lag kernel (ABM) | ABM kernel tested null (§21); hazard settles prepay same-month (Markov matrix is delinquency-only) — document lag −3 as the unmodeled TBA delay, do not convolve |
| Danish balance | Dynamic forward simulation | Static-balance application produced -$1,132B |
| Repo layout | `abm/` frozen + `hazard/` new | Separates behavioral counterfactual from reduced-form estimation |
| QT window definition | Single `common/qt_window.py`, imported by both frameworks | Duplicated definitions were how the Error-4 post-QT drift bug crept in (§15 Fix 4) |
| Rothstein β₁ application | Per-100bp rate gap (`exp(-β₁·100·gap)`) | Applying β₁ to the decimal gap left the lock-in channel numerically inert (§15 Fix 3) |
| 15-year MBS in ABM | Structural-only (weights + amortization; CPR from 30yr surface) | Payment-delta gate breaks down for short-amortization loans — predicts 32–61% CPR vs ~5–8% empirical (§15 Fix 2) |
| Cross-design covariates | Structural only (coupon, loan age, LTV); behavioral draws stay synthetic | Freddie sample has no analogue for mobility desire, patience, transaction cost (§15 Fix 1) |
| Cross-design calibration | Both variants reported (recalibrated primary, frozen robustness) | The variant gap is itself diagnostic of calibration-dependence (§15 Fix 1) |

---

## 14. Known Limitations and Next Steps

### Data

- **Freddie Mac 2017–2021** integrated via `prepare_freddie.py` (20 quarters in `hazard/data/raw/`).
- **15-year MBS fully folded in** (weights + scheduled amortization, coverage
  99.8%) with a **native term-aware behavioral gate** (§19) — 15yr voluntary
  CPR is now modeled directly (5–8% range), no longer borrowing the 30-year
  surface.
- **FRED API key** resolved via `common/fred_key.py` from the `FRED_API_KEY`
  env var or a gitignored `.env` (see `.env.example`); no key in committed
  source.

### Model

- ABM monthly CPR path fit remains weak (negative R²) despite 11.1% aggregate share (post native 15yr gate; §19).
- Danish counterfactual uses U.S.-calibrated friction.
- DTI check is front-end only (no total debt).
- Empirical lag-0 CPR correlation remains negative for the ABM and Path A (structural timing mismatch with SOMA settlement, not fixed with GLM lag terms); Path B's lag-0 correlation is positive (+0.19) with peak at lag −3, r=+0.40 — the two hazard paths disagree on contemporaneous alignment even though both lead SOMA by ~3 months at peak.
- Hazard Path A uses Poisson GLM with stratum FE (295 dummies) and mild ridge; plain IRLS is ill-conditioned at this FE dimensionality. Production α = **1e-4**, selected from `RIDGE_ALPHA_GRID = [1e-5, 1e-4]` on a temporally blocked holdout (all cohort-months ≥ `HOLDOUT_DATE` 2024-01-01 — no within-stratum leakage); `config.py: RIDGE_ALPHA = 1e-5` is only the IRLS-fallback default, not the production choice (§21).
- Cross-design test (§15 Fix 1) only swaps structural covariates; the recalibrated-vs-frozen calibration gap ($294B) shows aggregate share is highly sensitive to how the mobility anchor is set, not just to which population feeds it.

### Engineering (audit flags, July 2026 — known risks, not yet fixed)

- **Silent synthetic-data fallback.** `hazard/ingest.py` (`load_or_build_panel`)
  falls back to `generate_synthetic_fixture()` with only a `print()` when raw
  Freddie pairs are missing. Any run whose claim depends on the real/synthetic
  distinction (§15 Fix 1, §18) could silently be synthetic; this should be a
  hard failure unless synthetic mode is explicitly requested.
- **Mutable global calibration state.** The U.S.-transplant refi channel that
  drives the *sign* of the institutional gap (§20.1) is a module global set via
  `set_us_transplant_refi()` (`common/berger_calibration.py`) — order-dependent
  and invisible to `freeze_run.py` manifests unless separately recorded.
  *(Partially addressed, §21: `freeze_run.py` now writes
  `us_transplant_refi_annual` into every manifest; the global itself remains
  order-dependent.)*
- **Test coverage is thin relative to the bug history.** *(Partially
  addressed, §21: `test_units_conventions.py` now covers both §15 Fix 3 units
  bugs and `rothstein_beta1(0) == 0`; `test_bootstrap_se.py` covers the
  bootstrap resampler; `test_loan_sample_cache.py` guards the cache path.)*
  Still untested: the `.clip()` bug in §3, the self-comparison bug in §5, the
  mutual-recursion refit breakage in §15 Fix 4.
- **Dead settlement-routing code.** `route_through_pipeline()` (`hazard/markov.py`)
  has no callers; earlier revisions of this document described it as live (§11
  now corrected — prepay settles same-month).
- **Discrete-branch burnout ordering bug.** In `competing_risks.py`'s
  non-production discrete branch (`PREPAY_MODE != "fractional"`), prepaid
  balances are zeroed *before* `prepaid_bal` is computed from `pool.balance`,
  so `cohort_burnout` can never accumulate in that branch. Production uses the
  fractional branch (`config.py: PREPAY_MODE = "fractional"`), which updates
  burnout from pre-zeroing amounts and is unaffected — but the discrete branch
  is misleading as written.

### Next steps (priority order)

1. ~~**Symmetric companion test**~~ — **done (§18).** Path B on a fully synthetic population recovers 106.0% vs 107.0% real; the hazard survival structure recovers the benchmark with zero real data, while the ABM needs real covariates to reach even 59%. The paradigm gap survives the data-source swap; only the CPR *path* shape (not the level) still depends on real structure.
2. ~~**Reconcile the cross-design and synthetic-companion results with the paper's paradigm claim.**~~ — **addressed in manuscript v14 (§21).** The abstract now conditions the household-choice claim on the synthetic population and flags the cross-design complication; the estimator table carries both cross-design variants (59.3% recalibrated / 20.9% frozen) alongside the synthetic-population figure, and the §18 synthesis is quoted with the null-corrected reading (§12).
3. ~~**Re-run Monte Carlo (50 seeds)**~~ — **done.** Against the current pipeline (native 15yr gate + Berger Danish): mean **$96.7B**, seed-draw std $24.8B (was $113.5B on the 30yr-only book). Verified bit-identical under the contiguous-subgrid speedup before running. Population-draw uncertainty is ~29% of the point estimate — quote the ABM headline as **$84.5B ± $25B (1σ)**, not to three digits; the CI of the mean is not a prediction interval (§12).

---

## 15. Robustness Fix Program (July 2026)

Four pre-registered robustness fixes, executed against the frozen
`runs/pre-fix-2026-07/` baseline so every diff is attributable to a specific
fix. Baseline manifest consolidates all four headline numbers with config
hashes: $764.7B empirical, $101.2B ABM (13.2%), $915.1B Path A (119.7%),
$747.3B Path B (97.7%).

### Fix 4 — QT window filter consolidation (done)

**Problem:** `QT_START`/`QT_END` and the mask/target logic were defined twice
(`abm/fed_mbs_extension_risk.py`, `hazard/config.py` + `hazard/macro.py`).
Duplicated window definitions were how the Error-4 post-QT drift bug
originally crept in; two copies meant any future edit could silently
desynchronize the frameworks.

**Fix:** Single source of truth in [`common/qt_window.py`](common/qt_window.py)
(bounds, cap schedule, `qt_active_mask/frame`, `compute_qt_target_series`,
`expected_qt_active_months`). Both frameworks import it; duplicated logic
deleted. Aggregations now call `assert_qt_window_only()` on the frame they
are about to sum (`export_headline_metrics`, `score_extension_risk`) so an
unmasked frame fails loudly.

**Validation:** [`tests/test_qt_window.py`](tests/test_qt_window.py) feeds a
synthetic series with 8 months of large nonzero values past `QT_END`;
aggregates must be identical with and without those rows, and the pre-fix
filter (`index >= QT_START`, no upper bound) is shown to drift by construction.
All headline numbers reproduce the baseline exactly after consolidation.

**Incidental fix:** the Path A refit was unrunnable due to infinite mutual
recursion between `_stratum_fe_row` and `_stratum_dummy_matrix`
(`hazard/hazard_fit.py`); fixed mechanically, refit reproduces committed
coefficients byte-for-byte.

### Fix 3 — Rothstein elasticity band propagation (done), and the β₁ units bug it exposed

**Parameterization:** `run_qt_microsim()` now takes `p_q_shock_pct` and derives
β₁ via the survival-function conversion per band point — one parameterized
function, no copied code paths. `extension_risk.py --mode literature --band`
re-runs the full 75k-loan × 42-month × 2-regime microsim at 5.5% / 6.5% / 7.7%
(same loan sample and RNG seeds; only β₁ varies), scores each against the
benchmark, and writes `hazard/data/extension_risk_band_literature.json` with
the Table-1 interval. Central 6.5% run keeps the standard cache; band edges
cache as `microsim_results_pq{5.5,7.7}.parquet`. Runtime ~23s per band point.

**Validation of the parameterization (pre-bug-fix):** with the original
hazard code the central run reproduced $747.3B / 97.7% exactly, confirming
the parameterization itself changed nothing.

**Bug the band exposed:** the band came out flat ($747.1B–$747.4B), which
diagnosis traced to a units/sign mismatch: `rothstein_beta1()` returns
ln(h_shocked/h_base) **per +100bp of lock-in**, but `prepay_hazard()` applied
it to the **decimal** rate gap (`beta1 * rate_gap`). At a typical QT state
(3.0% coupon, 6.8% market) the multiplier was ×1.0026 — inert and
wrong-signed — versus the intended ×0.77. The lock-in elasticity channel
contributed nothing to the $747B headline; that figure was produced by the
PSA baseline + involuntary floor + burnout alone.

**Fix (user-approved):** `prepay_hazard` now applies
`exp(-β₁ · 100 · rate_gap)` — one β₁ of suppression per −100bp of refi
incentive, matching Path A's positive-coefficient-on-gap convention.
`rate_gap_danish` was simultaneously moved from price units (PV/balance − 1)
to rate-equivalent units using the NPV identity: the buyback discount exactly
offsets the PV of the locked-in spread, so the Danish effective gap is 0 when
out-of-the-money and `coupon − market` when in-the-money (buyback capped at
par) — implementing the documented "resets toward baseline" semantics.

**Post-fix results (supersede the $747B / 97.7% headline):**

| P_q shock | Trapped | Share | CPR r (lag 0) | Peak |
|---|---|---|---|---|
| 5.5% | $809.9B | 105.9% | +0.248 | lag −3, r = +0.423 |
| **6.5% (central)** | **$818.5B** | **107.0%** | +0.190 | lag −3, r = +0.404 |
| 7.7% | $827.7B | 108.2% | +0.094 | lag −3, r = +0.371 |

Sensitivity interval for Table 1 / §V.C: **$810B – $828B (105.9%–108.2% of
benchmark)**. Peak cross-correlation lag is stable at −3 across the band
(TBA settlement pipeline). Stronger mobility suppression now correctly maps
to more trapped liquidity. Path B moves from just under the benchmark to
modest over-prediction, consistent in direction with Path A (119.7%). The
pre-fix $747B remains reproducible from the `pre-fix-2026-07` baseline tag.

### Fix 2 — 15-year MBS fold-in (done, structural-only)

**Problem:** SOMA cohort modeling filtered to `term == "30yr"`, covering 90.6%
of MBS face value; the ~9.1% 15-year book contributed holdings but no
cohort-correct amortization or weights.

**Fix:** `fetch_soma_mbs_cohorts(terms=("30yr","15yr"))` (new default) buckets
both terms separately — never merged, `min_share` evaluated within-term so
the 30-year cohort structure is invariant to the fold-in. Cohorts carry
`term_months`; the CPR surface is keyed `(coupon, term)` (`Cohort_Term`
column; old CSVs load as term 360); `scheduled_amortization_series` and the
Danish balance loop are term-aware. Coverage: **90.6% → 99.8%** of $1,941B
MBS face (11 buckets: 7×30yr identical to the pre-fix set + 4×15yr; WAC
2.55% → 2.49%).

**Behavioral finding (user-decided scope):** the ABM's payment-delta gate
breaks down for 15-year loans. A seasoned 15yr borrower's same-term
replacement payment is nearly flat, so loss aversion never binds — native
15yr surfaces predict 32–61% CPR vs ~5–8% empirical, enough to flip ABM
trapped liquidity to −$169B. Production therefore used (initially) a
**structural-only** fold-in: 15yr cohorts contribute real weights and
15-year scheduled amortization, but voluntary CPR came from the same-coupon
30-year surface. Movers refinance same-term (was: hardcoded fresh 30-year —
identical behavior for the 30-year book). **This was superseded by the native
15yr gate — see §19.**

**Results (`run-2026-07-04-15yr-foldin`):**

| Metric | 30yr-only (old) | 30+15yr (revised) |
|---|---|---|
| Empirical benchmark | $764.75B | **$764.75B (unchanged)** |
| ABM U.S. trapped | $101.2B (13.2%) | **$91.0B (11.9%)** |
| Institutional gap | $930.3B | $925.5B |
| US CPR mean | 11.98% | 11.68% |
| Empirical CPR back-out | 5.53% | 5.14% (15yr sched amort now weighted in) |

The −$10.2B shift is modest, as pre-registered: mostly real 15-year
scheduled principal flow the simulated roll-off was missing. 30yr-only mode
(`terms=("30yr",)`) reproduces the baseline to all decimals — the extension
is additive, not a rewrite.

### Fix 1 — Cross-design test: real Freddie covariates → ABM (done)

**Scope (pre-registered):** only structural covariates transfer — per-loan
coupon, loan age, and original LTV from the hazard framework's 75k stratified
sample ([`abm/freddie_population.py`](abm/freddie_population.py),
balance-weighted 10k draw; sample WAC 3.36%, age 22mo, LTV 72, FICO 753).
Behavioral draws (income, home value, mobility desire, transaction cost,
patience) stay synthetic with production distributions and seed. FICO and
state are carried but have no ABM decision-rule analogue. Not "fully real"
agents, and per §VII.A this does not fully resolve the data-source confound
without the symmetric companion test (hazard framework on a synthetic
population — now done, §18).

**Mechanics:** `--population=freddie` on `abm_lockin_simulation.py`, full
two-variant diagnostic in [`abm/cross_design_test.py`](abm/cross_design_test.py).
Engine internals (`_n_rem`, `_term_years_vec`, `_pmt`) are now per-household
vectors; synthetic-mode headline metrics verified **byte-for-byte identical**
to `run-2026-07-04-15yr-foldin` after the change (the control condition).

**Pre-registered criterion (fixed before results):** recovery >50% of the
benchmark undercuts the paradigm claim; 10–35% corroborates §VIII.A; 35–50%
ambiguous.

**Results (`abm/data/cross_design_results.json`):**

| | (a) recalibrated [primary] | (b) frozen [robustness] | synthetic control |
|---|---|---|---|
| mobility_scale | 36,086 | 43,883 | 43,883 |
| Trapped | **$453.5B (59.3%)** | **$159.5B (20.9%)** | $91.0B (11.9%) |
| Mean CPR | 8.14% | 11.63% | 11.68% |
| CPR r (lag 0) | −0.336 | −0.311 | −0.316 |
| Peak lag | 0 | 0 | −3 (r=+0.19) |

**Interpretation (reported with pre-registered symmetry):** the primary
recalibrated variant recovers **59.3%** — above the pre-registered 50%
threshold, so by our own criterion this **moves against the paradigm claim**:
with real structural covariates and a like-for-like turnover anchor, the
household-choice ABM explains far more of the benchmark than the synthetic
population suggested. The frozen variant stays in the corroborating band
(20.9%). The **$294B discrepancy between variants is itself the headline
diagnostic**: earlier ABM results depended heavily on synthetic-population
calibration, not just on the decision rules. Both variants retain the
wrong-shaped monthly CPR path (r(lag 0) ≈ −0.32, no lead structure), so the
path-shape critique of §VIII survives even where the aggregate share moves.
Real LTV heterogeneity (mean 72 vs the synthetic fixed 80% LTV) is the main
lever: smaller balances relative to home values shrink payment deltas, and
recalibrating the anchor against that population lowers the desire scale,
suppressing QT-window CPR toward empirical levels (8.14% vs 5.83% backed out
under the population's own amortization assumptions).

---

## 16. Permutation Test — Does Path B Depend on Joint Covariate Structure?

**Question.** Path B recovers ~107% of the benchmark from a real 75k Freddie
loan pool. Is that recovery a property of the pool's *joint* covariate
structure (which borrowers hold which coupon × FICO × LTV × vintage
combination), or only of the covariate *marginals*? If independent marginals
reproduce the result, the loan-level microdata adds little over marginal
distributions for the aggregate figure.

**Method (`hazard/permutation_test.py`).** A marginal-preserving permutation
null: independently permute each stratum-defining axis across the 75k loan
index, so every marginal is preserved but cross-column correlation is
destroyed. `fico_bucket`/`ltv_bucket` and `stratum_id` are recomputed from the
permuted values (recipe verified to reproduce the stored `stratum_id`
75000/75000), and the stratum-level burnout broadcast follows the new
assignments. The microsim is otherwise unchanged — same hazard form, same β₁
(Rothstein 6.5% midpoint), same competing-risks logic, same draw seed. The
reported null uses **999 independent permutations** (exact-p floor 1/1000);
the reproduce command's default `--n 100` runs a faster 100-draw check
consistent with the 50-seed Monte Carlo convention.

Two implementation choices: (1) LTV is permuted even though the Path B
`stratum_id` keys only on {vintage, coupon, FICO} — LTV still enters the hazard
continuously via `ltv_z`. (2) `vintage` and `loan_age` are permuted together as
one origination-time block (they are two encodings of the same quantity;
permuting them independently would fabricate contradictory loans and inject h0
noise unrelated to cross-covariate structure). All four distinct axes still
receive independent permutations, so cross-axis correlation is fully destroyed.

Because `PREPAY_MODE="fractional"` makes prepayment deterministic (`bal ×
h_prep`) and only the negligible default channel (h₀=0.0003/mo) draws from the
RNG, the spread across replicates is almost entirely the covariate-scramble
effect, not Monte Carlo draw noise.

**Results (real vs. 999-permutation null).** The primary claim is the exact
rank-based permutation p-value — the fraction of the reference set (the N nulls
plus the observed value) at least as extreme as the real result,
`(1 + #{null ≥ real}) / (N + 1)`. The z-score is reported only as a secondary
descriptive statistic; it is inflated because deterministic fractional prepay
makes the null sd tiny, and it assumes a normality the rank-based p does not.

| Diagnostic | Real | Null mean ± sd | Null range | Rank-based p | z (descriptive) |
|---|---|---|---|---|---|
| Trapped liquidity | $818.5B | $816.36B ± $0.31B | [814.9, 817.4] | 0/999, **p=0.001** | +7.1 |
| Share of benchmark | 107.03% | 106.75% ± 0.04pp | [106.56, 106.88] | 0/999, **p=0.001** | +7.1 |
| CPR r (lag 0) | +0.190 | +0.227 ± 0.002 | [0.220, 0.234] | 0/999, **p=0.001** | −18.0 |
| Peak cross-corr lag | −3 | −3 (999/999) | — | — | — |

The real value falls outside *every* one of the 999 draws on all three
continuous diagnostics, so the exact two-sided p hits its floor of
1/(999+1) = 0.001 without leaning on any distributional assumption.

**Interpretation — read magnitude and significance separately.**

1. **The aggregate recovery is a marginal-distribution phenomenon.** Scrambling
   the entire borrower-level joint distribution moves trapped liquidity by only
   **$2.2B — 0.27% of the headline** (0.28pp of the 107% share). Independent
   marginals reproduce the ~107% to within a third of a percent. Path B's
   benchmark recovery does **not** depend on the real cross-covariate
   correlations; it is driven by the marginal distributions of coupon, FICO,
   LTV, and age (coupon → rate-gap being dominant).

2. **There is a small but cleanly resolved real-structure signal.** Despite the
   tiny magnitude, the real result sits outside all 999 permutation draws
   (rank-based p=0.001) and, per the bootstrap below, is ~2× the full width of
   the sampling CI — so it is a genuine effect, not noise. The direction is
   interpretable: the real pool's assortative structure (high-coupon loans
   clustering with particular FICO/LTV/age profiles) slightly *amplifies*
   aggregate lock-in (+$2B trapped) and slightly *degrades* contemporaneous CPR
   alignment (−0.037 at lag 0) relative to a decorrelated pool. Real,
   reproducible, but economically second-order. (The z-scores — +7.1 on trapped,
   −18 on r — are large only because the null sd is minuscule under
   deterministic prepay; they are descriptive, not the basis of the claim.)

3. **The timing signature is structurally invariant.** Peak cross-correlation
   lag is −3 in the real data and in all 999 permutations — the ~3-month
   TBA-settlement lead is a property of the pipeline routing, not of the pool's
   joint composition. The paper's timing claim is robust to covariate scramble.

**Implication.** This cuts both ways. It is *reassuring* that the ~107% is not a
fragile artifact of one particular correlation pattern — it survives complete
joint-structure scramble. But it also *tempers* any claim that Path B's success
demonstrates the value of real loan-level joint heterogeneity for the aggregate
trapped-liquidity number: independent marginals get you to essentially the same
place. The real-structure signal that does exist lives in the monthly CPR
*path* (the −0.037 lag-0 shift), consistent with §8's theme that the
path-shape, not the aggregate level, is where loan-level structure matters.

**Controls.** Two additional modes validate the methodology choices above.

- **Block-shuffle (structure preserved, `--mode block`, n=20).** Shuffling intact
  rows — one permutation applied to every column, so all covariate correlations
  are preserved and only the RNG→loan alignment changes — reproduces the real
  result: null $818.528B ± $0.003B, with the real value sitting *inside* the
  distribution (75th percentile, p=0.35). This pins the pure draw-noise floor at
  **~$3M**. The $2.18B independent-permutation effect is therefore **~700× the
  noise floor** — a genuine structure signal, not an artifact of the shuffling
  mechanics (and confirming the microsim aggregate is order-invariant, as a pool
  statistic should be).
- **`loan_age` permuted independently (`--mode age-independent`, n=50).** Giving
  `loan_age` its own fifth independent permutation instead of blocking it with
  `vintage` yields null $816.40B ± $0.34B — statistically indistinguishable from
  the main null, same r(lag 0) (+0.228), same peak lag (−3 in all 50). The
  origination-time blocking choice drives no conclusion.

| Null model | Structure | Trapped null (mean ± sd) | Real vs. null |
|---|---|---|---|
| Block-shuffle (n=20) | preserved | $818.528B ± $0.003B | inside, p=0.35 |
| Independent — main (n=999) | destroyed | $816.36B ± $0.31B | +$2.17B, above all (p=0.001) |
| `loan_age` independent (n=50) | destroyed | $816.40B ± $0.34B | +$2.13B, above all |

**Axis attribution — single-axis ablation (`--mode ablate --axis`, n=100 each).**
Permuting exactly one axis while block-shuffling the other three together
isolates that axis's cross-correlation with the rest. Two clear findings:

| Axis decorrelated (other 3 kept jointly intact) | Trapped null | real − null | r(lag 0) null | real − null |
|---|---|---|---|---|
| coupon | $814.2B ± 0.3 | +$4.3B | +0.207 | −0.017 |
| FICO | $813.3B ± 0.3 | +$5.3B | +0.190 | 0.000 (p=0.89) |
| LTV | $813.4B ± 0.3 | +$5.2B | +0.179 | +0.011 |
| origination-time | $812.9B ± 0.3 | +$5.6B | +0.237 | −0.047 |
| *(full four-axis, ref)* | *$816.35B ± 0.3* | *+$2.18B* | *+0.227* | *−0.037* |

1. **The trapped-liquidity effect is interaction-dominated, not attributable to a
   single axis.** Every single-axis ablation lands *below* the full four-axis
   scramble (each real−null of +$4.3B to +$5.6B *exceeds* the full +$2.18B). That
   is the signature of non-additivity: keeping three axes clustered while
   detaching one is *more* disruptive than decorrelating all four uniformly,
   because uniform scrambling partially cancels the higher-order configuration
   that single-axis scrambling exposes. All four axes matter (each p≈0.01 at the
   n=100 floor); none is inert; but the real pool's four-way assortative
   structure jointly *maximizes* aggregate lock-in (real $818.5B is the highest
   of every configuration tested), and no clean per-axis decomposition of the
   $2.2B exists.
2. **The CPR-path signal is concentrated in origination-time.** Decorrelating the
   vintage/age axis moves r(lag 0) the most — from real +0.190 up to +0.237 — so
   the real age structure is what *depresses* contemporaneous alignment with
   SOMA. FICO is inert for the path (real sits at the 48th percentile of its
   ablation null, p=0.89); LTV pulls weakly the other way. This localizes §16's
   "the real-structure signal lives in the CPR path" claim specifically to
   loan-age/vintage composition — consistent with the TBA-settlement seasoning
   story (§10–11), since age is what the PSA baseline hazard keys on.

**Bootstrap context (`--mode bootstrap`, n=499).** How large is the $2.2B
joint-structure effect relative to ordinary sampling variability — the wobble
you would get just from drawing a different 75k sample, with no scrambling?
Resampling the real loans with replacement centers on the real estimate
(bootstrap mean $818.55B, real $818.53B at p=0.95) with sd **$0.27B** and a 95%
CI of **[$818.0B, $819.1B]** (width $1.06B). So the joint-structure effect
(+$2.18B) is **~8× the bootstrap sampling sd and ~2× the full 95% CI width**.
This refines the "economically second-order" reading: the effect is tiny as a
*fraction of the level* (0.27%), yet it is roughly four times larger than how
imprecisely the level is even pinned down by a finite sample — it is a real,
resolved signal, not sampling noise.

**Stratum-sparsity check (§1.4 diagnostic).** Both Path B's burnout broadcast and
the stratum key operate at the stratum level, so a permutation that fragmented
strata into sparse cells could confound the result. It does not: over 20
independent permutations the real 130 strata (median 136 loans, max 6076, 18
cells <5 loans holding 0.22% of mass) become ~149 strata that are *more* evenly
populated (median ~209, max ~2377, ~11 cells <5 loans, sparse mass still ~0.2%).
Permutation slightly increases stratum count and *evens out* mass — the real
pool is the more concentrated one — so the effect is not a stratum-sparsity
artifact; if anything the permuted burnout cells are better-conditioned.

Reproduce: `cd hazard && python3 permutation_test.py --n 100`
(add `--mode block`, `--mode age-independent`, `--mode bootstrap`, or
`--mode ablate --axis {coupon,fico,ltv,orig}`) →
`data/permutation_test*_results.csv` + `data/permutation_test*_summary.json`.

### The same permutation on Path A — a *fitted* model (roadmap 1.3)

Path A *learns* its coefficients from data, so a permutation can change what the
model learns, not just what it predicts — a strictly harder test than Path B's.
The panel is pre-aggregated, so the permutation operates at the stratum level:
independently reassign the four axes (vintage, coupon, FICO, LTV) across the ~297
strata, keeping each stratum's outcome series (exposure, prepaid_upb, burnout
stock, age) in place, then **re-fit the 295-FE ridge GLM and re-simulate** per
replicate (`permutation_test_pathA.py`, n=50). The GLM fit is deterministic, so
there is no RNG noise floor — any spread is structure effect. A second mode
(`profile-block`) moves each stratum's *whole* 4-axis profile to a different
outcome slot (within-profile joint structure preserved, profile↔outcome pairing
broken), isolating pairing from axis correlation.

| Quantity | Real | Independent null (n=50) | Profile-block null (n=50) |
|---|---|---|---|
| β(rate_gap_bps) | +0.673 | +0.71 ± 0.64 [−1.13, +1.19] | +0.33 ± 0.55 |
| β(burnout_orth) | −0.130 | **+0.12 ± 0.31** (sign flips) | −0.53 ± 0.30 (stays negative) |
| β(friction) | −0.037 | −0.14 ± 0.06 (p=0.02) | −0.17 ± 0.10 |
| Trapped | $915B (119.7%) | $967B ± 174 [788, 1272] | $1140B ± 145 (real below all, p=0.02) |

Three findings, in sharp contrast to Path B:

1. **A fitted model's outputs are far more structure-dependent than a
   literature-calibrated one's.** Where Path B's aggregate barely moved (±$0.3B),
   Path A's forward-simulated trapped swings by **±$150–175B** and β(rate_gap)
   ranges from −1.13 to +1.19 (it can flip sign). The specific coefficient values
   are not robustly identified once covariate structure is scrambled.
2. **The spec-v3 negative burnout coefficient requires the real within-profile
   covariate correlations.** Under independent scramble β(burnout) flips to a
   *positive* mean (+0.12); under profile-block (joint structure preserved) it
   stays negative (−0.53). So β(burnout) < 0 is a genuine feature of the real
   four-way covariate joint structure — corroborating the adverse-selection
   reading (§10) — but also demonstrably sensitive to it.
3. **The real profile↔outcome pairing *suppresses* trapped.** Breaking the
   pairing while preserving joint covariate structure (profile-block) inflates
   trapped to $1140B, above the real $915B in all 50 draws (p=0.02): the actual
   loan pool's alignment of covariates to prepay outcomes is on the low-trapped
   side of what a mismatched pairing would produce.

Reproduce: `cd hazard && python3 permutation_test_pathA.py --n 50`
(`--mode profile-block` for the second column) →
`data/permutation_pathA_*_results.csv`.

---

## 17. Cross-Foundation Checks — Hybrid Pipeline and Full-Book Weighting

### 17.1 Hybrid pipeline: shared accounting, hazard micro-foundation (roadmap 3.2)

**What.** [`abm/hybrid_pipeline.py`](abm/hybrid_pipeline.py) runs the ABM's
macro-accounting layer (SOMA balance tracking, phased-cap netting, curtailment,
scheduled amortization, Danish dynamic-balance loop) but replaces the ABM CPR
surface with Path B's literature microsim CPR (`use_hazard_microsim=True`; no
settlement kernel applies — the kernel is skipped under a hazard
micro-foundation (`fed_mbs_extension_risk.py`) because Path B settles
prepayments in the month they occur; `hazard/markov.py`'s
`route_through_pipeline` has no callers). Only the micro-foundation for loan
behavior varies; the accounting is held identical.

**Result** (the Danish leg here uses Path B's *pre-Berger* NPV-reset heuristic;
§20 re-runs this hybrid with the Berger-recalibrated Danish regime — see the
note below):

| Metric | ABM-native (surface) | Hybrid (hazard micro-foundation) |
|---|---|---|
| U.S. trapped | $91.0B (11.9%) | **$749.0B (97.9%)** |
| Danish trapped | −$834.5B | **+$687.8B** |
| Institutional gap (US − DK) | **$925.5B** | **$61.2B** |
| U.S. / Danish CPR mean | 11.68% / 47.14% | 4.76% / 5.61% |

**Interpretation — the institutional gap is not robust across micro-foundations.**
The headline $925.5B U.S.–Danish gap is largely an artifact of *how the ABM
surface encodes the Danish market-value buyback*: its mobility gate reads the
sub-par payoff as a low replacement payment and fires a 47% Danish CPR refi
wave, draining the Danish book fast (deeply negative Danish trapped). The hazard
framework (here) encodes the same institution through the NPV identity (§15 Fix
3): the buyback discount offsets the locked-in spread, so prepaying is
economically *neutral* and the Danish hazard resets to the ~6% PSA baseline
rather than a refi wave. Under that encoding the Danish and U.S. books behave
similarly and the gap nearly vanishes ($61.2B).

This shows the *magnitude* of the institutional gap is a micro-foundation
artifact, not a robust structural number. (The U.S.-side recovery also rises
from Path B's standalone 107% to 97.9% here because the shared layer nets ~$70B
of curtailment and term-aware scheduled amortization the standalone scorer
omits.)

> **Superseded by §20, then restored by §23.** The NPV-reset heuristic used for
> the Danish leg above was itself a mechanism-extrapolation, not an estimated
> elasticity. §20 replaced it with Berger et al.'s estimated Danish channels
> (flat 3.2% moving + ≈0 U.S.-transplant refi) and re-ran this exact hybrid:
> Danish CPR 5.61% → 3.39%, institutional gap **$61.2B → −$99.9B**. A referee
> round then established that §20's 3.2% import is Denmark's descriptive LEVEL
> (a rule+country bundle whose Danish CPR sits below the 4% involuntary floor),
> and §23's U.S.-intercept anchor — Berger's flatness fact anchored at the U.S.
> zero-gap hazard — is the rule-only production reading. Because the NPV
> identity zeroes the effective rate gap, §23's run reproduces THIS hybrid leg
> for leg ($+\$61.2B$, Danish CPR 5.61%): the construction above turned out to
> be right for a reason it could not, at the time, cite. The ~$925B figure was
> never a robust number either way.

Reproduce: `cd abm && python3 hybrid_pipeline.py` →
`data/hybrid_pipeline_results.json`.

### 17.2 Full-book SOMA cohort weighting (roadmap 3.1)

**What.** Both hazard paths draw their loan population from the Freddie 2017-2021
sample (WAC ~3.4%), then scale total UPB to Fed holdings — but neither aligned
the pool's *coupon composition* to the actual SOMA book (WAC ~2.5%, dominated by
2.0-2.5% pandemic coupons). Full-book weighting rescales per-cohort (Path A,
`simulate.py`) and per-loan (Path B, `MicrosimPool.reweight_to_soma_coupons`)
balances so each 0.5% coupon bucket's share matches SOMA.

**Result.**

| | balance-weighted | full-book | shift |
|---|---|---|---|
| Path B trapped | $818.5B (107.0%) | **$834.6B (109.1%)** | +$16.1B, +2.1pp |
| Path B CPR r(lag 0) | +0.190 | **+0.278** | +0.088 |
| Path A trapped | $915.1B (119.7%) | **$964.3B (126.1%)** | +$49.3B, +6.4pp |
| Path A CPR r(lag 0) | −0.444 | −0.441 | ~0 |

**Interpretation.** Contrary to the prior expectation that full-book weighting
would *tighten* the estimates toward 100%, it moves **both paths up**. The Freddie
sample's higher WAC (3.4% vs SOMA's 2.5%) had *understated* lock-in: aligning to
the real, lower-coupon book deepens the rate gap at 6-7% market rates, suppresses
voluntary prepay, and raises trapped liquidity. Path A shifts more (+6.4pp) than
Path B (+2.1pp) because its cohort composition was further from SOMA. Path B's
contemporaneous CPR-path correlation also *improves* materially (+0.190 → +0.278),
a second-order benefit of matching the real coupon mix. The full-book figures
(Path B 109.1%, Path A 126.1%) are the more portfolio-faithful estimates; the
balance-weighted headline numbers should be read as mild under-statements of
lock-in driven by the sample's coupon skew.

Reproduce: `cd hazard && python3 full_book_weighting.py` →
`data/full_book_weighting_results.json`.

---

## 18. Symmetric Companion Test — Synthetic Population into the Hazard Framework

**What (roadmap 2.1-2.3).** The ABM cross-design test (§15 Fix 1) put *real*
Freddie covariates into the *behavioral* ABM. The symmetric companion is the
mirror image: put a *fully synthetic* population — every covariate drawn from
external, non-Freddie sources (`synthetic_population.py`: PMMS annual-average
rates for coupon-by-vintage, published FICO/LTV/vintage priors) — into the
*hazard* framework's survival structure. This tests whether that structure,
divorced from any real loan-level data, still recovers the $764.7B benchmark.
Path B uses literature calibration (Rothstein/PSA), so synthetic-population +
Path B is a *fully* Freddie-free test. Path A applies its real fitted
coefficients to the synthetic covariates in forward simulation (structure real,
population synthetic; novel strata fall back to the reference fixed effect).

**The 2×2 (roadmap 2.2), share of the $764.7B benchmark:**

| | synthetic population | real Freddie population |
|---|---|---|
| **ABM (behavioral)** | 11.9% (§12) | 59.3% (§15 Fix 1, recalibrated) |
| **Hazard Path B (survival + literature)** | **106.0%** | 107.0% (§16) |
| *Hazard Path A (survival + fitted coefs)* | *75.8%* | *119.7% (§10)* |

**This is the cleanest resolution of the paradigm-vs-data-source confound that
runs through the paper.** Read the rows:

- **The hazard survival structure recovers the benchmark with zero real data.**
  Path B on a fully synthetic population recovers **106.0%** — within one point
  of its real-data 107.0%. The benchmark recovery is a property of the survival
  structure plus the coupon marginal (which the synthetic PMMS-calibrated coupons
  reproduce), *not* of Freddie loan-level data. This is exactly what §16's
  permutation test implied (marginal-dominated), now confirmed by construction.
- **The ABM's recovery is data-source-limited, not structural.** The behavioral
  paradigm goes from 11.9% (synthetic) to 59.3% (real covariates) — real data
  buys +47pp, but even then it only reaches 59%. The gap between the ABM and the
  hazard framework is a genuine *paradigm* gap that largely survives the
  data-source swap: the hazard framework recovers the benchmark on synthetic data
  where the ABM cannot.
- **Path A sits between (75.8%), reflecting its data-dependence.** Consistent with
  §16's Path A permutation (its fitted coefficients need the real structure),
  Path A's synthetic recovery falls well below its real-data 119.7% — the fitted
  stratum fixed effects cannot transfer to novel synthetic strata — whereas the
  literature-calibrated Path B is essentially data-source-invariant.

**Variance decomposition of the 2×2, and reconciliation with §15's
pre-registered classification.** The two factor effects, in share points:

| Effect | holding population synthetic | holding population real | average |
|---|---|---|---|
| Paradigm (hazard − ABM) | +94.1pp | +47.7pp | **+70.9pp** |
| Data source (real − synthetic) | +47.4pp (ABM) | +1.0pp (hazard) | **+24.2pp** |

with a large negative interaction (−46.4pp): real data substitutes for the
paradigm *only inside the ABM*. On average the paradigm factor is ~3× the
data-source factor, and the hazard row is data-source-invariant. This resolves
the apparent tension between §15 Fix 1 and this section: §15's pre-registered
criterion asked whether household choice *could* explain >50% once fed real
covariates — it can (59.3%, recalibrated), so the narrow claim "the ABM's low
share proves household choice cannot matter" is indeed undercut. But the 2×2
shows the broader paradigm claim survives: the survival structure reaches ~106%
with *no* real data, while the fully-fed behavioral ABM reaches only 59.3% (and
20.9% without recalibration). Both statements are true at their own scope; the
paper should state them together rather than choose one.

**Calibration sensitivity (roadmap 2.3).** Path B's synthetic recovery is
**105.9%–106.0%** across all three calibrations (baseline, looser FICO, higher
LTV) — the choice of external distribution does not move the result, echoing the
§16 ablation finding that FICO/LTV are second-order and coupon dominates. So the
synthetic-hazard recovery is not an artifact of a particular calibration.

**Caveat — the CPR path, not the level, still needs real structure.** While the
aggregate recovers identically, Path B's synthetic monthly CPR-path correlation
is r(lag 0) ≈ −0.06 (vs +0.19 real): the synthetic population lacks the real
age/vintage structure that §16 localized as the driver of contemporaneous
alignment. Aggregate level is data-source-invariant; path shape is not. This is
the one place the companion test does *not* fully close the confound, exactly as
§VII.A anticipated.

Reproduce: `cd hazard && python3 synthetic_companion.py` →
`data/synthetic_companion_results.json` (population generator:
`synthetic_population.py`).

---

## 19. Native 15-Year Behavioral Gate

**Problem (from §15 Fix 2).** The 15-year fold-in was structural-only: 15yr
voluntary CPR borrowed the same-coupon 30-year surface because the ABM's
payment-delta gate produced 32–61% CPR for 15yr cohorts, versus the ~5–8%
empirical range. Root cause: for a seasoned short-amortization loan the new
same-term loan is financed on the much-reduced payoff, so
`new_pmt − current_payment` is large and *negative* — a spurious "gain" that
clears the loss-aversion gate for nearly every 15yr borrower.

**Fix (roadmap 3.3).** A term-aware `MicrosimPool._mobility_penalty` in
[`abm/abm_lockin_simulation.py`](abm/abm_lockin_simulation.py). 30-year loans
keep the legacy payment-delta penalty unchanged. 15-year loans use the **pure
rate-lock penalty**: the payment increase from financing the *same payoff* at
the market rate versus the borrower's *own coupon*. This isolates the
golden-handcuff cost (the value of below-market financing given up), is ≥0 when
locked in and 0 otherwise, and never manufactures a false gain from the
amortization-schedule difference. 15yr mobility is then governed by desire vs
transaction cost + genuine rate lock-in, not an artifact.

**Validation.**

- Native 15yr CPR at QT-typical coordinates (market 6.8%, friction 9%):
  **6.78%** (2.0% coupon), **8.77%** (3.0%) — squarely in the 5–8% empirical
  band, vs 32–61% under the borrowed-30yr artifact.
- 30-year CPR is **byte-identical** (spot check: 30yr 2.0% at 7.0%/9.0% =
  0.0684 before and after), since 30yr uses the unchanged legacy branch.
- The 30yr-only production path reproduces the baseline **exactly**
  ($101.1744B U.S. trapped, gap $930.2989B) — the native gate is purely
  additive to the 15yr treatment.

**Production switch and result (`run-2026-07-05-native15yr`).** `compute_metrics`
now uses each 15yr cohort's own native surface instead of borrowing the 30-year
one. Headline shifts modestly:

| Metric | structural-only (§15 Fix 2) | native 15yr gate (§19) |
|---|---|---|
| ABM U.S. trapped | $91.0B (11.9%) | **$84.5B (11.1%)** |
| Danish trapped | −$834.5B | −$752.8B |
| Institutional gap | $925.5B | $837.3B |
| U.S. / Danish CPR mean | 11.68% / 47.14% | 11.76% / 44.09% |

The 15yr cohorts (~9% of the book) now carry economically defensible voluntary
CPR rather than a borrowed 30-year proxy; the ~$6.5B reduction in U.S. trapped
and the lower Danish CPR (44.1% vs 47.1%) both flow from the 15yr book no longer
inheriting the 30-year behavioral surface. The 15yr fold-in is now a *resolved*
model feature, not an acknowledged scope limitation.

Reproduce: `cd abm && python3 abm_lockin_simulation.py` (rebuilds the surface
with native 15yr slabs) `&& python3 freeze_run.py --tag run-2026-07-05-native15yr`.

---

## 20. Berger et al. Danish Recalibration — Two Estimated Channels

**Problem.** Both frameworks previously computed the Danish counterfactual by
taking a *U.S.-calibrated* response function and feeding it a Danish-style rate
gap (ABM: market-value payoff through the U.S. mobility gate → ~47% Danish CPR;
Path B: NPV-reset-to-baseline heuristic → ~6%). That calibrates against a
*mechanism*, not against an elasticity estimated for this exact counterfactual,
and it conflates two channels that behave differently under a U.S. transplant.

**Fix.** [`common/berger_calibration.py`](common/berger_calibration.py) imports
Berger, Jeong, Marx, Olesen & Tourre's estimated elasticities directly (`berger2026`,
"A Danish fix for U.S. mortgage lock-in?"; Table 3 structural parameters;
§3.3.1 / §4.9.1) and models **two separate channels**:

- **Moving channel** — anchored to the Danish unconditional moving rate of
  **3.2%/yr**, with the (statistically flat) Danish moving-hazard slope
  (−0.198 … +0.12 %/yr per 100bp). The moving attenuation vs the U.S. slope
  (Fonseca–Liu 0.57–1.20 %/yr per 100bp) is **0.044** — i.e. Danish moving is
  ~insensitive to the coupon gap (no lock-in on the moving margin), so it is
  imported as a near-flat 3.2%/yr curve rather than derived from the U.S. model.
- **Refinance-in-place channel** (discount buyback while staying put) — new to
  both frameworks. The buyback is NPV-neutral on the financing, so its value is
  the *tax* treatment of the realized discount. Denmark: capital-gains exempt
  (θ=33%) → strong shield → a large home refi channel. U.S. transplant: taxable
  gain (θg=15%) with a smaller deduction (θi=22%) removes the shield; Berger's
  realistic-tax scenario moves the equilibrium mortgage rate only **~1bp**, so
  the U.S.-transplant refi channel is anchored to that GE result as **negligible**
  (a partial-equilibrium reduced form over-predicts because it omits the rate
  adjustment; the Danish-home reduced form is retained for the contrast).

So the U.S.-transplant Danish CPR = flat 3.2% moving + ≈0 refi.

**Result — the institutional gap collapses and reverses.**

| | old (mechanism-extrapolated) | Berger-recalibrated |
|---|---|---|
| ABM Danish CPR mean | 47.1% | **3.4%** |
| ABM Danish trapped | −$834.5B | **+$812.9B** |
| ABM institutional gap (US−DK) | +$925.5B | **−$728.4B** |
| ABM DK−US CPR wedge | +32.3pp | −8.4pp |
| Path B (hybrid) institutional gap | +$925.5B | **−$99.9B** |
| Path B (hybrid) US / Danish CPR | 11.68% / 47.1% | 4.76% / 3.39% |

**Interpretation.** The old +$925B institutional gap was largely an artifact of
the ABM's market-value-payoff path generating a spurious ~47% Danish CPR. Under
Berger's *estimated* Danish elasticities the Danish counterfactual prepays only
~3.4%/yr — barely faster than the empirical U.S. book — so the "Danish system
frees up far more trapped liquidity" claim does not survive contact with the
real elasticities. This is exactly Berger's own conclusion: under U.S. tax law
the buyback institution adds ~1bp, i.e. almost nothing.

The two frameworks now bracket the sign. The **Path B hybrid** puts both regimes
on empirically-grounded footing (US 4.76%, Danish 3.39%) and gives a **small
−$99.9B gap** (≈−13% of benchmark); the **ABM's larger −$728B** gap is partly an
artifact of the *opposite* problem on the U.S. side (the ABM over-predicts U.S.
CPR at 11.76% vs empirical 5.5%). The unambiguous statement is that real Danish
elasticities shrink the institutional wedge from tens of points to approximately
zero — but the **sign of that near-zero gap is not robust in Path B**; see the
sweep in §20.1.

Reproduce: `cd abm && python3 abm_lockin_simulation.py && python3 freeze_run.py
--tag run-2026-07-05-berger && python3 hybrid_pipeline.py`
(channel sanity check: `python3 common/berger_calibration.py`).

### 20.1 Sensitivity sweep of the U.S.-transplant refi channel

§20 anchors the U.S.-transplant refi-in-place CPR to Berger's ~1bp GE result
(≈0). Because that zero drives the *sign* of the institutional gap, it is
parameterized (`set_us_transplant_refi`) and swept from 0 to the partial-
equilibrium reduced-form ceiling (**~18%/yr** — the estimate §20 rejected as
over-predicting, representative ~17.4% at QT rates; Denmark's own ~33%/yr
opportunity hazard is an even-more-generous alternative), holding the moving
channel and both U.S.-side calibrations fixed through to the gap.

| refi-in-place CPR | ABM gap | Path B (hybrid) gap |
|---|---|---|
| **0% (best estimate)** | **−$728.4B** | **−$99.9B** |
| 3% | −$525.8B | +$116.8B |
| 6% | −$342.5B | +$317.3B |
| 9% | −$176.6B | +$502.4B |
| 12% | −$26.5B | +$672.7B |
| 15% | +$109.2B | +$829.0B |
| 18% (PE ceiling) | +$231.9B | +$972.0B |

**Breakeven** (gap = 0): **ABM at refi ≈ 12.6%**, **Path B at refi ≈ 1.4%**.

**Where the best estimate sits — and the honest conclusion.** The best-evidence
refi is ≈0 (Berger's realistic-tax ~1bp). Against that:

- The **ABM's** negative gap has a **wide ~12.6pp margin** to breakeven — its
  sign is robust to any plausible refi. But the ABM's U.S. leg is over-predicted
  (§20), so that robustness is less meaningful than it looks.
- The **Path B hybrid's** negative gap has only a **~1.4pp margin** — a refi
  contribution of just 1.4%/yr (far below even the rejected ~18% PE estimate,
  and well within what a non-zero channel could plausibly deliver) flips the
  sign positive. **So in the more defensible framework the sign is *not* robust.**

The correct takeaway is therefore the *magnitude*, not the sign: across the
entire plausible refi range the institutional gap stays small relative to the
$925.5B the old calibration reported, and it is approximately zero at the best
estimate. Claiming a robustly *negative* gap would overstate the evidence — the
honest headline is "the Danish institutional benefit is approximately zero under
U.S. conditions, with the sign sensitive to a refi channel that Berger's GE
result puts near zero but does not pin to exactly zero."

Reproduce: `cd abm && python3 refi_sweep.py` → `data/refi_sweep_results.json`.

---

## 21. July 2026 Verification Round — Committed Artifacts and Manuscript v14

The v11→v14 manuscript revision (a simulated editorial panel producing a
17-item action ledger) triggered a code-level verification pass over this
repository; the full trace — every re-run, diagnostic, and replacement number
— is in [§22.1](#22-manuscript-verification-record-referee-rounds-july-2026)
(absorbed from the former `REVISION_VERIFICATION.md`). **No headline
result changed.** What the round produced, now committed:

| Artifact | Commit | What it settles |
|---|---|---|
| `abm/data/runs/run-2026-07-04-15yr-foldin/monte_carlo_*` | `0878eac` | Seed uncertainty for the paper's fold-in headline: mean $103.7B, SD $24.5B, CI of mean [$96.9B, $110.5B]; seed 42 reproduces $90.98B exactly (34th pctile). See §12 on why this MC is spec-distinct from the $96.7B pipeline MC |
| `hazard/no_lockin_null.py` + `data/no_lockin_null_results.json` (+ `microsim_results_pq0.0.parquet` cache) | `b4e31f5` | β₁ = 0 null: $748.2B / 97.8%, peak lag −3 shared with production — timing does not identify lock-in; the marginal +$70.3B / +9.2pp does (§12) |
| `hazard/bootstrap_se.py` + `data/hazard_bootstrap_{se.json,draws.csv}` + `tests/test_bootstrap_se.py` | `b6a3e51` | Path A coefficient uncertainty (table below) |
| `abm/freeze_run.py` manifest field + `tests/test_units_conventions.py` | `3476dfe` | Manifests now record `us_transplant_refi_annual` (§20.1 audit flag); regression tests for both §15 Fix 3 units bugs and `rothstein_beta1(0) == 0` |

### Path A stratum block-bootstrap (closes the "no SE" gap in §10)

Stratum-level cluster bootstrap: strata resampled with replacement, a fresh
FE label per resampled stratum (so duplicates contribute independent fixed
effects), per-replication standardization rescaled to production units, ridge
α **held at the production 1e-4** rather than re-selected (re-selection would
bootstrap a different estimator: coefficient-plus-model-selection). 198/200
replications converged; the point refit reproduces production coefficients to
four decimals on the same 10,176 training cells.

| Coefficient | Point | Bootstrap SE | 95% pctile CI | Draws ≤ 0 |
|---|---|---|---|---|
| rate_gap_bps | +0.673 | 1.152 | **[+0.60, +4.11]** | **0.5%** |
| burnout_orth | −0.130 | 1.363 | [−1.76, +1.43] | 75.3% |
| friction | −0.037 | 0.506 | [−0.25, +1.38] | 48.0% |

Reading: only the rate-gap coefficient survives — sign-stable, CI excludes
zero — but the distribution is heavily right-skewed with the point estimate
near the lower bound (identification concentrated in a subset of strata), so
the magnitude is imprecise. Burnout and friction are **controls, not
findings**. The α = 1e-4 production choice was made on a temporally blocked
holdout (all cohort-months ≥ 2024-01-01), so no within-stratum information
crosses the split — which is also what licenses holding α fixed inside the
bootstrap (§13).

Reproduce: `cd hazard && python3 bootstrap_se.py --reps 200` (~12 min).

### Manuscript v14 (2026-07-10)

`revised_paper_v14` (.tex canonical; .pdf; .docx regenerated from the tex)
applied the full editorial ledger against this repository's artifacts:

- **Bootstrap table inserted** in the Path A section (sourced from
  `hazard_bootstrap_se.json`), with burnout/friction demoted to controls.
- **Timing claims null-corrected** per `no_lockin_null_results.json`: the
  abstract and Path B section no longer cite the three-month lead as evidence
  for the lock-in elasticity (the null shares the lead); the elasticity's
  identified content is the +9.2pp marginal and band monotonicity.
- **Estimator-table Danish row** prints the berger run's own $84.5B U.S. leg
  (single-freeze consistency, §19–§20) instead of mixing runs, and the notes
  state the peak-lag convention (max-|r| vs most-positive-r — the §15 B2
  finding that both conventions coexist in this codebase).
- **Bibliography rebuilt** (natbib author-year; the previous
  biblatex-on-bibtex build silently dropped author labels for `@misc` entries
  and title-sorted the Works Cited), both blank display equations restored,
  robustness moved before the conclusion, declarations added, and the title's
  "Failure of Quantitative Tightening" softened to "Shortfall".
- **15-year exclusion correctly scoped**: hazard side only — the ABM folds
  15-year MBS structurally (§15 Fix 2, §19).

---

## 22. Manuscript Verification Record (Referee Rounds, July 2026)

> Absorbed from the former `REVISION_VERIFICATION.md` on 2026-07-11 — the full
> round-by-round text is preserved in git history (through commit `d0549e7`).
> This section keeps every settled number and standing rule; the per-round
> narrative is consolidated thematically. Manuscript editions live outside the
> repository (`~/Downloads/revised_paper_v15.*` canonical; versioned delivery
> bundles `v15r*_bundle.zip`).

### 22.1 v11 → v12 verification pass (2026-07-09)

**No headline result changed** ($764.7B benchmark; $91.0B / 11.9% ABM; $915B /
119.7% Path A; $818.5B / 107.0% Path B). Findings, each traced to a committed
artifact or reproducible run:

- **Table 1 Danish row was a mixed-runs error, not arithmetic.** The berger
  manifest is internally consistent: U.S. leg **$84.507B**, Danish
  **+$812.921B**, gap **−$728.415B** (exact). The paper had substituted the
  $90.98B fold-in headline U.S. leg into that row. Fix adopted: print the
  berger run's own $84.5B leg (single-freeze consistency, §21).
- **Two peak-lag conventions coexist in the codebase.**
  `abm/cross_design_test.py` uses max-|r| (lag **0**, r −0.318);
  `abm/fed_mbs_extension_risk.py` uses most-positive-r (lag **−3**, +0.195).
  Neither is stale; the convention is now stated wherever a peak lag is printed.
- **Sample provenance:** the production Path B sample is **75,000 unique real
  Freddie loans** (all 20 quarters 2017–2021, coupons 1.75–6.875%, natural
  dispersion); the synthetic fixture (5,000 single-vintage loans on a coupon
  grid) never fired. "Synthetic-augmented" deleted from the paper. (Path A's
  estimation panel is the **full origination universe** — a round-3 erratum;
  see §22.3f.)
- **Fold-in-spec Monte Carlo** (50 seeds at `5cf33a3`, one harness function
  backported, model code unchanged): mean **$103.7B**, SD $24.5B, CI of mean
  [$96.9B, $110.5B]; **seed 42 reproduces $90.98B to the cent** (34th
  percentile, z −0.52). Two premise corrections en route: the HEAD MC ($96.7B)
  was the native-15yr spec, not fold-in; and manifest `git_commit` fields are
  unreliable (the freeze ran on a dirty tree 2 minutes before its code was
  committed) — identify specs by cohort-bucket count (7 = 30yr-only,
  11 = fold-in), not by manifest commit.
- **Ridge α selection is temporally blocked** (train < 2024-01-01): no
  within-stratum leakage; this also licenses holding α fixed in the bootstrap.
- **Competing-risks normalization never binds:** 0 events in 2 × 1,683,124
  loan-months; max h_prep + h_def = **0.0155** against a threshold of 1.
- **β₁ = 0 no-lock-in null:** $748.2B / **97.8%**; elasticity band strictly
  monotone ($809.9 / $818.5 / $827.7B at P_q 5.5 / 6.5 / 7.7%); lock-in
  marginal **+$70.3B (+9.2pp)**. The null also peaks at lag −3 — timing never
  discriminates the elasticity (see §22.3b).
- **SOMA coverage:** 66.2% of face value in 2017–2021 vintages (2022 tail
  23.1%, pre-2017 10.6%); the cohort parse includes **GNMA (20.4%** vs UMBS
  79.6%; terms 30yr 90.7% / 15yr 9.1% / other 0.2%).
- **R² convention:** 1 − SSE/SST against a mean-only null over the 42
  active-QT months, identical in both frameworks. Value map: **−6.984**
  current (fold-in), −6.443 stale (30yr-only), −7.086 native-15yr; simulated
  U.S. CPR **11.68%** (fold-in).
- **"Pre-registered" downgraded to "specified ex ante":** the repo has no git
  tags and the registration commit postdates the results file by 2 minutes.
- **FRED key (closed 2026-07-10):** the key hard-coded in early public history
  was rotated; the old key is issuer-deactivated (FRED returns 400 on it), so
  historical copies are inert — no history rewrite, by panel-accepted scope.
  The replacement key appears in zero tracked files and zero commits
  (`git log --all -S` empty); it lives only in the untracked `.env`.

Path A bootstrap SEs from this pass: table and method in §21. Defense
one-liners: the elasticity's verified content is the +9.2pp marginal and band
monotonicity, never timing; 66.2% vintage coverage; normalization never binds;
significance is rate-gap-only; the headline is a 34th-percentile seed.

### 22.2 Referee round 2 — three-persona audit (2026-07-10): the shared accounting basis

Executed against manuscript v15; every requested computation ran, each script
carrying a parity gate that reproduces a published number first. **Headline
framing changed:** recoveries are stated on the shared accounting layer
(benchmark-consistent), where Path B = 97.9%, Path A = 110.6%, β₁=0 null =
88.7%, and the composed (shared-layer + full-book) Path B = **$765.1B =
100.0%** of benchmark. The +9.2pp lock-in marginal is basis-invariant.

| Item | Script → artifact (`hazard/`) | Key result |
|---|---|---|
| Shared-layer scoring + composed | `shared_layer_scoring.py` | B 97.9 / A 110.6 / null 88.7%; composed B 100.0%; curtailment netted $69.6B |
| Rate-input timing scan | `rate_timing_scan.py` | Empirical CPR ~ rate(t) (+0.40); sim ~ rate(t−4) (+0.60); no ±1–3mo shift kills the −3 peak; trapped moves <$1.5B |
| FICO/LTV priors estimated | `covariate_priors_estimation.py` | β̂_F −0.39 [−1.51,+0.65], β̂_L +0.21 [−0.59,+1.00] — priors' signs supported (turnover regime); zero-out 108.3%, estimated 101.3% |
| Seasonality + concave gap | `seasonality_concave_gap.py` | Month effects to +0.43; Path A r(lag0) −0.444→−0.378, peak −2, 121.5%; concave gap 105.7%, r(lag0) +0.281 |
| Path A refit-and-resimulate | `bootstrap_resimulate.py` | median $922.6B, IQR [900.1, 1130.6], 95% pctile [−4459.8, +1190.1] (15 blowups) — $915B demoted from abstract |
| WAL table + no-shock row | `wal_table.py` | Reproduces every printed Table 6 cell; 2021-speed row (22.81% CPR) WAL 3.4y ⇒ extension 6.0y |
| Ginnie composition bound | `ginnie_bound.json` | 20.4% face × 1.2–2.8pp GMAR differential × ~$83B/pp ⇒ $20–47B (2.6–6.2%), toward overstating trapped |
| Panel/attrition/Markov | `panel_disclosures.py` | Full-universe panel (peak 8.84M loans, $72.48T/$37.43T raw); attrition 75,000→40,234; thin Markov cells, extreme-matrix bound $0.39B |

### 22.3 Rounds 3–12 — adjudication findings, consolidated

Chronological ledger (one commit per round; full narratives in git history):

| Round | Commit | Scope |
|---|---|---|
| 2–3 | `749c5a8` + `14fe816` | Shared basis (§22.2); netting mechanics; timing attribution withdrawn; Markov crosstab; Table-2 erratum; LO render check |
| 4 | `5989023` | Output-side timing demotion; per-leg netting scope; bidirectional parity v2 |
| 5 | `d182958` | All-estimator detrended collapse; sweep-log process adopted; composed covariate band |
| 6 | `0e1fa20` | Artifact regates; −0.316/−0.318 convention; zero-band bookkeeping; versioned bundles |
| 7 | `369fd8a` | Table 4 per-row convention; closest-call straddle; sweep multi-hit fix |
| 8 | `554c0f7` | Full 45-item review: temporal bootstrap, ridge/reference audit, Danish discount bound, convention-definition fix, floor circularity, WAL defense |
| 9 | `dedaf5a` | Danish bound reconciled to printed basis; WAL external anchor; dead-code re-scope |
| 10 | `96d7fd1` | Remainder/age-floor notes; golden fixture; parity tally discipline |
| 11 | `5e759ea` | Convergence declared; three provenance one-liners |
| 12 | `d0549e7` | Round-11 parity embed defect found and fixed |

**(a) Accounting basis and netting.** The shared layer nets exactly
**$69.562B** for every U.S. leg — pure income-scaled curtailment on the
*actual* WSHOMCB path, common by construction because every simulation
rescales its roll-off to that path monthly. Conversion is **per-leg**:
invariance is scoped to U.S. legs; the Danish leg's curtailment on
counterfactual balances is $70.33B (+$0.77B, immaterial). Composed Path B
prints **$765.077B = 100.04%** of the unrounded $764.748B benchmark (a joint
run; the additive identity is exact with zero cross-term and demoted to
cross-check); covariate band 92.2–99.2% shared, ≈94.3–101.3% composed.
Danish standalone basis chain: $934.254B = shared **$848.870B** (printed
848.9; U.S. leg 748.97 vs printed 749.0) + Danish-leg curtailment $70.33B +
dynamic-balance remainder **$15.05B** — the remainder is the
roll-off-conversion analogue of the +$0.77B differential (the Danish leg
compounds a counterfactual balance that the slower drain leaves higher, so
each month's CPR converts to more roll-off dollars; U.S. legs are pinned by
the monthly rescale). The Danish **discount-rate wedge is exactly $0.00**:
the production Danish leg uses the imported Berger flat elasticity, and
`rate_gap_danish`'s PV classification is computed but consumed by nothing
(7,803/32,486 classifications flip under −50/−100bp; paths bit-identical).

**(b) Timing credential — fully demoted.** Round 3 withdrew the burnout/floor
attribution (both ablations keep peak −3; levels correlations
trend-contaminated; sim ΔCPR ~ Δrate r = −0.94 at lag 0 — correct sign,
mechanical — while empirical Δ is +0.25, wrong sign: empirical monthly
variation is not rate-driven; "mechanism not isolated"). Round 4:
corr(Δsim, Δemp) = −0.23, detrended levels −0.20 — Path B's +0.190 lag-0
levels r is trend-carried; its distinction is **level accuracy only**.
Round 5: detrended r₀ = ABM −0.30 / Path A −0.29 / Path B −0.20 — one
indistinguishable cluster. Zero bands are 1.96/√n (±0.30 at n=42 detrended;
±0.31 at n=41 differences; per-lag n−k, so lag-3 has n=39 → ±0.314). Two
empirical back-out conventions: the manuscript's ABM −0.318 is the frozen
run's own cohort-weighted series (recomputed −0.3183 exactly); the common
hazard-side series gives −0.316 — and the closest call **straddles**: ABM
detrended r₀ = −0.3030 under the production convention vs the ±0.3024 i.i.d.
band (outside; common-series −0.301 inside), so all in/out verdicts rest on
moving-block bands. Round 8 identified the printed intervals as circular
joint-series MBB with fixed lags (reconstruction parity ±0.02); block lengths
4/6/8 change no zero-inclusion verdict except Path A's lag-0 upper endpoint at
block 8 (+0.04) — "significantly negative" is block-scoped ("excluding zero at
block 4; marginal at 6 — upper −0.02 at the production seed, −0.00 under the
committed reconstruction — and 8"). The §V.C convention-definition sentence
was inverted in print (series interchanged); synthetic re-verification proved
a peak at k=−3 means the simulated path **trails**; every direction claim was
computed under the implemented convention and stands
(`hazard/extension_risk.py::lag_interpretation` fixed likewise). **Standing
rule:** no timing claim returns; the identified content is the +9.2pp marginal
and band monotonicity.

**(c) Estimation and inference.** Temporal moving-block bootstrap (blocks of
6 over 36 training months; 196/200 converged): `Dynamic_Friction` is built
from national series only, so the stratum scheme is structurally silent about
it — temporal friction SE **2.80 vs 0.51** (≈5.5×), CI [−3.71, +7.69];
burnout SE 2.59, CI [−3.16, +6.16]; rate gap CI [+0.44, +12.18]. **Rate-gap
sign stability is 99.5% under both schemes**; the burnout sign is
point-estimate-only (temporal center +1.23 / +0.52, opposite sign). Ridge and
reference audit: the two ridge-grid fits are **bit-identical** (max |Δ|
4.5e-17 — grid selection vacuous, the penalty a no-op from the IRLS start;
"mildly shrunk" removed from print); a reference-stratum swap moves cold-start
penalized refits by Δ1.29; the true ill-conditioning is **20 of 296 strata
with zero training events** (FE MLEs nonexistent; the production reference is
not among them; 295-dummies status stated). Dropping those strata (423/10,176
cells), unpenalized PML is exactly reference-invariant (Δ ≈ 6e-15) and
reproduces the production macro coefficients **to within 0.002** standardized
(rate gap 0.6727/0.6734 and friction −0.0373/−0.0371 third-decimal; burnout
−0.1317/−0.1301 — a demeaning/orthogonalization sample change). The
inestimable FEs are pinned by the warm-started optimizer, not the penalty.
Holdout RMSE: exposure-weighted **2.53pp** vs 37.8pp unweighted (both
printed). Panel holdout recount: **6,077** (printed 6,076 — fixed, erratum).
eq(β₁) print/code mismatch: the printed equation was the continuous-hazard
transform (0.0693) while the code compounds discretely (**0.0686**; both
print 0.069) — the equation was corrected to the implemented form (range
0.0672–0.0701 over P_q ∈ (0, 0.12]). **Floor circularity conceded:** the 4%
involuntary floor is anchored to 2023–24 in-window turnover;
benchmark-independence is not window-independence, and the clean verification
content is the +9.2pp marginal only.

**(d) WAL.** The 14.7y approximate WAL was defended against a 16–17y
replication: origination WAL at 2.49% is 16.89y (15yr sleeve 8.01y), and the
9.1% 15-year sleeve plus the aged book pull the blend down (midpoint ages
give only 14.9). External anchor (`hazard/wal_anchors.py`): SOMA-CUSIP
back-derived ages (origin = maturity − term, face-weighted, no reference to
Table 6) give {2021: 11.6, 2020: 28.0, 2017–19: 50.5} months → blend
**14.94** — 16–17y excluded externally. The grid-search age objective is
disclosed as a reconstruction of the printed table; the 2022 cell's 0.0
months is floored, not data (bucket origin postdates June 2022; <0.05y effect
at 23.1% weight). Coverage reconciliation: 90.7 + 9.1 = 99.8 exact (0.2%
other-term); 90.6% is the production parse's as-of-date share.

**(e) Danish-leg liveness.** §V.C re-scoped: the rate-gap swap defines the
mechanism-substitution *variant* (the superseded 47.1% surface); the
production leg is the Berger flat elasticity, whose PV classification is
computed but unconsumed (cross-referenced to the $0.00 diagnostic). The bound
script's baseline reproduces the frozen production Danish CPR path **exactly**
(max |Δ| = 0.0) once the full production regime tuple and a shared macro frame
are used — the earlier 2.7e-06 residual was per-regime RNG stream ordering.
A claims-vs-code liveness audit joined the §VIII freeze gate (no grep family
covers liveness claims).

**(f) Panel and Markov disclosures.** Path A's estimation panel is the
**full Freddie 2017–2021 origination universe** (peak 8.84M active loans;
$72.48T/$37.43T are raw unweighted dollars; fit window 2021-01–2023-12);
"75,000 loans" is Path-B-scoped (the v15 Table 2 note said otherwise —
erratum). Attrition: 75,000 → 40,234 window-start survivors → 1,683,124
loan-months. The delinquency matrix is exposure-UPB-weighted; printed
probabilities equal UPB shares exactly (D30 cure: 13 events = 95.6% of $58.3M
row exposure vs 0.62 count share); the crosstab is published; 482
(window-start stock) and 154 (max month-end stock; mean 24, end 14) are both
true; the extreme-matrix bound is **$0.39B** (0.05pp) with the 482 included.
Seasonality is real but insufficient (Path A 121.5% with peak −2); the
concave-gap variant scores 105.7% — extrapolation is not load-bearing.

**(g) Document-integrity tooling and process.** *Parity checker:* 94.8%
containment (round 3) → bidirectional with full hand-clearing (round 4; found
2 real tex→docx drifts; real drift 0 both directions ever since) → rebuilt
with escaped-\$/rendered-ref handling (round 8; 59/59 edit probes) →
per-miss class on every miss (round 9) → computed tally==misses assertion
embedded in the report (round 10; 27 + 98 = 125; motivated by the round-9
letter hand-miscounting a cross-sum 126 ≠ 124). The 135→97 docx→tex miss drop
is the round-8 bibliography trim having been ineffective (wrong heading
occurrence, ~1 character removed); corroboration exact — 37 rendered entries
(= the 37 `.bib` keys) + heading = 38 units = the drop. *Timing sweep:*
committed generator (`tools/timing_sweep.py`) regenerated per round; defect
history — word-boundary matching (v3; "flags" false positive),
every-phrase-per-line (v4; first-match shadowing had hidden 22 rows),
suffix-s truncation self-caught and restored (v6; the v4→v5 reconciliation is
two-sided: 60 − 6 + 28 = 82); v7 = 92 rows, all dispositioned. Golden fixture
`tools/test_timing_sweep.py` hand-enumerates an 11-hit multiset covering all
three defect classes; exact multiset match required. *Renders:* LibreOffice
26.2.4 headless (`writer_pdf_Export`), 46 pp at v15r4/r5, equation pages
7/16/20/21 content-verified each round (U+2223→U+007C glyph fix). *Bundles:*
editions versioned per round (v15r2…v15r5); the manifest is generated last and
excludes the current letter and itself; letters inline evidence verbatim
(SHA256SUMS + JSON excerpts) since round 5. *Round-12 defect:* the round-11
parity corroboration was recorded in the letter and the verification record
but never written into the artifact (hash unchanged at `ba26e2…`,
contradicting the letter's own inlined manifest); fixed before delivery after
independently re-verifying the docx entry count; new hash `078f0cae…`.
**Standing lesson:** after writing any claim about an artifact's content or
hash, re-hash the artifact in the same session and diff it against the claim
before cutting a bundle.

**(h) Standing state.** The panel declared the review **converged on paper**
at round 11: every open item is delivery-gated or inside the §VIII
pre-submission freeze gate — (i) seasonal Path A production adoption with
restated Table 4/WAL/interval, (ii) Word REF-field conversion, (iii)
claims-vs-code liveness audit, (iv) golden fixture passing at freeze,
(v) clean two-pass build with log. Panel-accepted facts not to relitigate:
per-leg netting and the $0.77B differential; the crosstab reconciliation;
482/154; 100.04% against the unrounded benchmark; the FRED-key scope
decision (no history rewrite).

### 22.4 v16 round (2026-07-13): intro reposition, Fed-source citations, and the calibration-box weakening pass

The manuscript advanced to a v16 edition. Editions live outside version
control (`paper/` is gitignored, `b54f551`); this section records the
verification history, per this document's standing practice.

**(a) Edition.** v16 was assembled from the review-converged v15r5 content
with eight repository figures wired in (`figures/` output regenerated
title-free so the in-image "Figure N" headers no longer collide with LaTeX
caption numbering; stale TECHNICAL.md-numbered §-references stripped from
in-figure annotations — the committed generator was not modified). v16
prose is em-dash-free; the only `---` tokens are table-cell markers.

**(b) Intro reposition (decomposition lead).** The introduction was
repositioned to open on priority concession and decomposition ("not a new
claim … this paper's contribution is its decomposition") rather than the
Securitization Trade-Off framing. The ordering was adjudicated with a
fresh-reader review plus a devil's-advocate steelman of the trade-off-led
alternative, each claim adversarially verified against the tex: the
decomposition lead stands because it inoculates against the
Fed-staff-priority objection in sentence one, while the trade-off's third
leg is the paper's weakest, partially retracted material (the Danish gap
collapsed to ~$100B with unidentified sign) and must not lead. Cleanups
applied with the verdict: the three Fed-staff quotes now appear only in
the related-literature paragraph (they had been duplicated verbatim in the
opening paragraph), the $764.7B benchmark is defined at first use, and the
trade-off paragraph gained the bridge sentence explaining why the frame
survives the decomposition (mobility genuinely constrained; plumbing, not
household choice, governs the cash-flow shortfall).

**(c) New sources, verified.** Four keys were added and each verified
against its primary source: `na2024` (Na, Newman & Schlusche, FEDS Notes
2024-09-20 — both quotes verbatim; the $450B actual vs $820B binding-cap
June 2022–June 2024 runoff figures match the note), `perli2024` (NY Fed
speech 2024-05-08; quote is a faithfully marked elision; then-SOMA-Manager
role confirmed), `hammack2025` (Cleveland Fed speech 2025-04-23; quote
verbatim, and the manuscript's attribution was tightened from "the
low-coupon book" to "some of the low-coupon holdings" to match the
source's scope), and `eyal2026` (Eyal, Na & Skaperdas, FEDS Notes
2026-02-02; the manuscript's macro-vs-loan-level contrast matches the
note's own decomposition). Build after insertion: zero undefined
citations, no dead keys.

**(d) Calibration-box weakening pass.** The §12.1 sweeps trip their
pre-registered threshold, so the manuscript executed the pre-registered
remedy in a 13-edit pass (surgery script with per-edit uniqueness
assertions; pre-pass backup retained): every statement of the +9.2pp
lock-in marginal is now conditioned "at the production calibration" and
bounded by the calibration box (+2.1 to +13.2 points; ceiling stated as
"never exceeds roughly 13% of the benchmark" — deliberately not "an
eighth," which the +13.17pp corner exceeds); the phrase "clean
verification content" is retired in favor of the floor-conditional
interval; a new manuscript subsection (Floor and Elasticity-Band
Sensitivity: The Calibration Box) carries the 3×7 marginal table with the
pre-registration commit chain named in prose; the abstract was resynced to
the decomposition lead; and the basis-invariance claim is extended to
every cell (the shared-accounting netting is common to the central and
null legs of each cell). Definition of done, both checked by grep: zero
unconditioned "+9.2" instances, zero occurrences of "clean verification".
Build: 52 pp, zero undefined references or citations; no hardcoded
table-number literals, so the new table's insertion shifts downstream
numbering safely through `\ref`.

**(e) Standing state.** The §VIII freeze gate (h, above) is unchanged.
Open beyond it: the title is still a placeholder while the conclusion
invokes "the Securitization Trade-Off of this paper's title" — the title
must carry the phrase now that the abstract leads with the decomposition.

### 22.5 Pre-submission freeze execution (2026-07-14): Path A spec v4 adoption and restatement

**(a) Phases 0–1.** Repo hygiene (`0141614`: §17.1 kernel/Markov claim
corrected to code truth; editor dirs gitignored) and the liveness gates
mechanized as `tools/liveness_gates.py` (`e828240`): 8 zero-count phrases,
4 exactly-one phrases, and the settlement-lag-kernel manifest cross-check;
all 13 gates pass, and `tools/test_timing_sweep.py` passes (freeze item iv).

**(b) Adoption (freeze item i) — two pre-registrations.** The FIRST
attempt (`7c3c673`) failed Gate B: re-assembling the seasonal design inside
`fit_hazard_glm` (pandas ddof-1 standardization) flipped Poisson IRLS into
its cold-start ridge fallback and a different, incompletely converged
penalized optimum (rate-gap ≈ +1.96; near-uniform −0.30 "month effects" —
an intercept split). Read-only diagnostic: the committed construction,
`seasonality_concave_gap.fit_with_month_dummies`, reproduces its artifact
to zero drift — the seasonal numbers are **construction-pinned**. The
SECOND pre-registration (`4e11124`) defines spec v4 as that construction
verbatim; both gates then passed exactly (`6895b2e`): Gate A reproduced
the v3 macro coefficients to 1e-6, Gate B reproduced the committed
seasonal artifact to the 4th decimal ($928.8930B, r(lag0) −0.3782, peak
lag −2). v3 preserved as `hazard_coefficients_specv3.json`; frozen tag
`run-2026-07-14-pathA-seasonal` (`9234b96`), artifacts sha256-pinned.

**(c) Downstream restatements, Path B invariant.** WAL table (`ecdb927`):
Path A 10.9/9.7yr at 3.34% mean CPR, spec v3 row kept as a gated exhibit.
Shared layer (`8f58e57`): Path A 112.4% shared (121.5% standalone); every
Path B figure unchanged (97.9/88.7/composed 100.0). Full book (`656e054`):
Path A 127.5%; Path B invariant to 4 decimals (107.0326 → 109.1391).
Unblocking fix (`9721beb`): loan-sample cache path + dead
`authenticate_service_account` call (suite 26/26; frozen sample untouched).
Known wart: `full_book_weighting` writes its reweighted sim over
`simulation_results.parquet` (restored from the committed artifact).

**(d) Bootstrap under v4: invalid, reverted, prior-spec retained.** All
200 stratum-cluster replications jumped to the +1.96 alternative optimum
despite production warm-starts (95% CI [+1.91, +2.01] excluding its own
+0.6469 point), and the resimulate pass propagated those draws ($1,122B
mean around a $928.9B point). Mechanism: eleven month dummies are nearly
collinear with the time-only friction regressor, flattening the resampled
likelihood into two basins. Artifacts reverted to committed spec v3 state;
the manuscript labels the coefficient-uncertainty table and the
refit-and-resimulate interval as spec v3 prior-spec exhibits with the
branch-instability disclosure. This is also why the v4 friction point
(−0.007) is a fifth of v3's (−0.037).

**(e) Manuscript restatement.** 27 assert-checked edits (Path A material
only): production statement and promotion provenance in §V.B, v4
coefficients with the friction-identification note, Table 2 row, Table 4
note, WAL row, §V.D comparatives, §VII shared/full-book sentences,
conclusion ranges, freeze item (i) marked executed with the prior-spec
labeling, in/out-of-sample split scoped to spec v3 (not recomputed).
Build clean (53 pp, zero undefined); all 13 liveness gates pass on the
restated manuscript; md/txt editions regenerated in lockstep.

**(f) Freeze items (ii) and (iii) executed (2026-07-14, later).**
Item (ii), LaTeX half: the master carries zero hardcoded
Table/Figure/Section/Appendix/Equation cross-reference literals —
machine-checked by five strictly-additive gates in
`tools/liveness_gates.py` (v2; 18 gates total) — and builds clean with
zero unresolved references or citations, the log shipping in the local
bundle (`paper/v16/tectonic_build_freeze.log`). The Word REF-field half
awaits a v16 Word submission master (none exists; the only Word edition
is the superseded v15r5). Item (iii): a claims-versus-code liveness
audit ran as an adversarial multi-agent sweep —
**77 production-mechanism claims extracted, each independently traced
to its executing code path; 68 traced as written, 9 did not**
(`tools/claims_liveness_audit_2026-07-14.json` carries every claim,
verdict, and disposition). The nine: curtailment is netted on the
simulated side, not in the empirical CPR back-out (corrected — the
audit's headline catch); the 15-year borrowed-30yr-surface sentences
now scope to the frozen headline specification (native gate at HEAD),
two sites; "recorded reproduction commit" removed (manifest
`git_commit` is the pre-run parent; no artifact records a reproduction
checkout); "bit-identical" grid fits restated as machine-precision
identity (4.5e-17, per artifact); two ridge/reference verification
baselines scoped to spec v3 post-adoption; the Danish rate-gap unit
correction scoped as computed-but-unconsumed in the production leg
(round-9 defect class, resurfaced in one §VII sentence); the
"declining as defaults absorb" attrition mechanism dropped (a static
month-one zero-balance exclusion dominates; the verifier's live
decomposition traces to no committed artifact, so no replacement
numbers were printed). One failure was extraction over-reach (the
seven-cohort sentence is correctly scoped to the superseded diagnostic)
and received no edit. Freeze-list items (ii)/(iii) marked executed in
the manuscript; build clean at 54 pp; all 18 gates pass; editions in
lockstep. Item (iv) passes (`tools/test_timing_sweep.py`). Item (v):
the author ratified the title as "The Securitization Trade-Off:
Mortgage Lock-In and the Federal Reserve's QT Shortfall" (2026-07-14) —
the Trade-Off lead is preserved, so the conclusion's title-reference
sentence and the pre-registered title gate hold unchanged, and the
subtitle now names the paper's subject mechanism. All five freeze items
are closed.

### 22.6 Post-freeze consistency pass (2026-07-14)

A full 54-page review of the built PDF after the freeze found the text
layer correct but the figure layer never regenerated, plus four small
text defects and one open diagnostic. All were closed in one pass
(commits `28536d4`, `33c9862`, `0065d6a`, `b93886c`, `33eb8ea`; the
manuscript editions themselves are local-only, `paper/` being
gitignored).

**(a) Spec v4 out-of-sample evaluation (the §V.B open diagnostic).**
`hazard/pathA_v4_holdout.py` (spec commit before the run) re-scored the
frozen spec v4 coefficients prediction-only on the identical
≥ 2024-01-01 holdout (n = 6,077): exposure-weighted RMSE **3.04pp**,
unweighted **37.90pp**, versus spec v3's 2.53 / 37.83 — the seasonal
terms do not improve the out-of-sample fit. A parity gate reproduced
the committed v3 values through the same prediction path to 1e-6pp
before the v4 numbers were trusted; the pre-registered STOP gate
(weighted ≤ 5.0pp) passed. §V.B and §VIII.A now print both specs
(`hazard/data/pathA_v4_holdout_results.json`).

**(b) §VII.F composed Path A restated to spec v4.** The printed
"$894.8B / 117.0%" was the spec v3 joint figure, unlabeled beside v4
numbers. The v4 joint run already existed as a committed freeze
artifact (`shared_layer_scoring_results.json`,
`path_a_fullbook_composed`: a genuine one-pass reweighted-simulation
scoring, commit `8f58e57`): **$905.1B / 118.4%**, equal to the
composition identity to 1.4e-14pp (exactness is what common netting
predicts). No rerun; the sentence now prints the committed values.

**(c) Figure layer regenerated, artifact-fed.** `figures/make_figures.py`
rewritten so every share/dollar/correlation is read from committed
artifacts; `figures/make_ccf_data.py` (new, gated) replaces the README
snippet and rebuilt `ccf_data.json` with the spec v4 Path A curve
(lag-0 r −0.3782 gated to the frozen manifest, ±3 peak −2) and the
**production fold-in** ABM series (lag-0 −0.318, the series Table 2
quotes; the old file plotted the Berger variant). The CCF figure drops
the retracted model-leads/TBA-settlement annotations and the 119.7
footer; axis states the implemented convention (empirical leads,
simulated path trails); footer is the no-timing-evidence statement.
Recovery figure: Path A 112.4% (121.5), r₀ −0.38; ABM row and the
waterfall's final-stage labels aligned to the production naming of
Table 2 (fold-in 11.9% = production headline; native gate 11.1% =
Berger-run variant). Architecture footer restated to the standalone-
scorer production headlines; cross-design footer neutralized. The
paper's Monte Carlo PNG was verified hash-identical to the frozen
`run-2026-07-04-15yr-foldin` copy.

**(d) Text fixes.** WAL sentence corrected to "1.5 years too long"
(10.9 − 9.4, `wal_table_results.json`); Appendix A ledger gained the
Path A spec v3 → v4 supersession bullet ($915.0B / 119.7%, r −0.444 at
lag 0, peak −3 → $928.9B / 121.5%, peak −2;
`run-2026-07-14-pathA-seasonal`); the conclusion's two-word orphan page
resolved by reflow of the §V.B/§VIII.A insertions (final conclusion
page carries three full lines; full-PDF scan confirms no page below
three); §III.D's curtailment-accounting sentence verified as traced in
the audit artifact (`claims_liveness_audit_2026-07-14.json`,
`failures_with_dispositions[0]`: amortization-only back-out at
`fed_mbs_extension_risk.py:1151` / `macro.py:246`, curtailment
simulated-side, netted commonly) — no edit needed.

**(e) Gates.** `tools/liveness_gates.py` v3, strictly additive, 28
gates: zero-count "1.3 years too long"; "894.8" allowed only within
120 chars of a "spec v3" label; the Appendix A ledger must contain
"spec v3" and "121.5"; three figure scripts zero-grepped for 35
benchmark-share/headline-dollar literals and the retracted timing
phrases. All 28 pass; `tools/test_timing_sweep.py` golden fixture
passes; tectonic builds twice with zero undefined references (54 pp);
tex/md/txt editions in lockstep.

---

## 23. Referee Round 13 — External Critique Implementation (July 2026)

A 30-item external critique (methodological / logical / structural / minor)
was triaged claim-by-claim against the manuscript and code; ~27 items
confirmed, 2 rejected on evidence (no unresolved `(?)` citation exists — the
build log is clean and `nyfed2022` resolves; the 97.9–112.4% range was never
in the abstract), 1 falsifier tested and failed (floor form, below). Three
new ex-ante-specified runs and one production restatement implement the fixes.
All spec headers were written before their runs executed; no committed
production artifact changed.

### 23.1 Danish counterfactual: U.S.-intercept anchor (production restatement)

The critique's flagship objection held up: the §20 Danish legs import
Denmark's descriptive 3.2%/yr moving LEVEL, producing Danish mean CPRs
(3.39–3.40%) below the 4% involuntary-turnover floor, conflating the payoff
rule with Danish baseline mobility. Berger's identified moving-margin fact is
the SLOPE (flat in the coupon gap). Fix: `common/berger_calibration.py` gains
a transplant-anchor switch (`set_danish_moving_anchor`, default `dk_level`
preserving all committed artifacts); the Danish branches of
`hazard/competing_risks.py` and `abm/abm_lockin_simulation.py` gain a
`us_intercept` mode = each framework's own U.S. hazard at zero rate gap
(floor, PSA baseline, burnout, covariates retained) + the sweepable refi
channel, combined on the survival scale.

Run `hazard/danish_us_intercept.py` → `hazard/data/danish_us_intercept_results.json`
(+ `microsim_results_us_intercept.parquet`): U.S. leg reproduces committed
central artifacts exactly (standalone $818.5301B, shared 97.94% — both parity
gates PASS); Danish leg 5.61% mean CPR, $687.8B trapped (shared); gap
**+$61.2B (8.0% of benchmark)**, positive at every point of the 0–18% refi
sweep (+$61.2B → +$1,038.9B; no crossing). Reproduces the §17 NPV-identity
hybrid leg for leg (see §17 note). The paper adopts us_intercept as
production (Table 1 row d), retains dk_level rows as a labeled rule+country
bracketing case, and rewrites §IV.C, fig4 (both anchors), abstract, intro,
and conclusion accordingly: the institutional gap is now signed, equals the
lock-in marginal in size and origin, and the "sign not robustly identified"
reading survives only for the bracketing anchor. ABM us_intercept direction
follows a fortiori without a run (the lock-in penalty only suppresses
moving, so the zero-gap intercept exceeds the locked-in leg by construction).

### 23.2 Floor functional-form test

Critique: eq. (3)'s hard max censors the elasticity wherever the floor binds
(36% of loan-months at production), and the floor's LEVEL was swept seven
ways while its FORM never was. Fix: `FLOOR_MODE` in `hazard/config.py` +
survival-scale competing-risks combination in
`hazard/literature_hazard.py:prepay_hazard` (`h = 1-(1-h_floor)(1-h_vol)`),
production default `max` unchanged. Run `hazard/floor_form_test.py` (spec in header before runs) →
`hazard/data/floor_form_results.json`; max-form pair at 4% reproduces
committed artifacts to 4 decimals (all parity gates PASS).

Results: additive marginal at 4% floor **+11.25pp** vs max-form +9.20pp
(delta +2.05pp — exceeds the critique's ±1pp immateriality falsifier, so the
form-dependence is real and now reported in §VII.I). But the additive
marginal is nearly floor-invariant (+11.29/+11.25/+11.21 at 3/4/5% floors vs
the max form's +10.82/+9.20/+5.54): the failed ±2pp stability gate of the
floor sweep was measuring max-form censoring mechanics, not elasticity
instability. Levels are strongly form-dependent (additive central 67.2% at
4%) because additive lifts book-wide hazards; max remains production because
the 4–5% anchor is a minimum-total-turnover reading measured where h_vol≈0,
where the forms coincide. Form-robust statement: lock-in marginal ≈ +9 to
+11pp, positive under every level/band/form combination tested.

### 23.3 Path B stratified loan-level bootstrap

Critique: 107.0% rides on a single stratified 75,000-loan draw with no
loan- or stratum-level bootstrap, an omission §VIII.A conceded. Net-new
machinery: `hazard/bootstrap_pathb.py` (spec fixed in header before runs; script and artifact enter the repo in one revision) —
within-stratum resample with replacement preserving stratum sizes, resample
rng = replicate index, engine seed fixed at 42, US regime only (seed-offset
0 ⇒ draw-identical to the production tuple), central (p_q 6.5) + null (p_q
0) paired per replicate, 200 replicates, ~21.8 s/rep (73 min total).
Artifacts: `hazard/data/bootstrap_pathb_results.json` + per-replicate
`bootstrap_pathb_draws.csv`.

Results (standalone basis; the 9.1pp shared-basis netting is common and
cancels from the marginal): central 107.03% median, 95% [106.96, 107.10],
sd 0.034pp; null 97.84% [97.75, 97.92]; paired marginal +9.20pp [+9.17,
+9.23], sd 0.016pp (+$70.33B [70.10, 70.58]). Sampling uncertainty from
the loan draw is negligible at reporting precision — the operative
uncertainty in Path B's level and marginal is calibration (floor level,
band, floor form), not sampling. Reported in §V.C; §VIII.A's concession
("rather than with estimated sampling uncertainty") replaced; the global
"no untouched evaluation months exist anywhere in this paper" statement
added in the same pass.

## 24. Referee Round 14 — Author-Ratified Data Runs (July 2026)

On 2026-07-15 (evening) the author ratified, in one message, every decision
round 14 had left open: the Fannie ZBC 06/16 treatment (censor, report the
0.38% bracket), the replication-package license posture (CODE ONLY — no
Fannie data and, conservatively, no derived cells), commits/pushes, and the
production-pull green light; the parked W2 cyclical-floor variant was
green-lit in the same message. Both NEEDS-NEW-RUN items were then executed
with pre-committed specs (spec-before-run, strong form). This entry was
first committed while the W4 production pull was still in flight; §24.1
records the completed W2 run, §24.2 the Fannie replication when it lands.
No committed production artifact changed in either run.

### 24.1 W2 cyclical-floor variant (spec 47e8ea9, run 9a00e7e)

The V.C acyclical-floor concession's residual: the marginal-over-null
cancels the floor's LEVEL but not a floor co-varying with the rate cycle.
Run: floor_t = 4%·(1 + κ·z_t), z_t the QT-window-standardized MORTGAGE30US
(ddof=1), window mean pinned at 4% exactly so κ=0 nests production
(SPEC INTENT; the pin holds only where the ≥0 clip does not bind — see the
mean-pinning correction below and §24.1a, and do not quote this clause alone)
(implemented as a `monthly_step` wrapper — at κ=0 the production code path
runs bit-for-bit); κ ∈ {±0.5, ±0.25, ±0.1, 0}; central (p_q 6.5) + null
(0.0) legs per κ under full production convention (committed 75k sample,
RNG_SEED 42, shared macro frame, raw-basis scoring).

Parity gate at κ=0: EXACT (818.5301/748.1850/+70.3451B/+9.1985pp, all
PASS). Marginals across the grid span **[+7.09, +9.36]pp** — every cell
inside the constant-floor level-sweep envelope [+5.54, +10.82]pp (p_q 6.5,
floors 3–5%, floor_sweep_results.json) → ex-ante verdict as recorded at the
time: **cyclicality is bounded by the reported level sweep; the
acyclical-floor concession stands as written.** That bound survives the
2026-07-19 re-diagnosis below (a fortiori, since most of the grid's movement
turns out not to be cyclicality at all), but the ATTRIBUTION recorded in the
original entry did not, and is superseded by §24.1a. The |κ|=0.5 stress
cells hit the ≥0 clip (flagged per spec; the spec header's parenthetical
expectation that the floor stays strictly positive across the grid was wrong
for those two cells — the per-cell flag governs). Mean-pinning is exact
everywhere the clip does not bind, and is NOT exact where it does: realized
window means are 4.000519% at κ=−0.5 and 4.082786% at κ=+0.5.

**Direction (rewritten 2026-07-19; the original narrative here read the grid
as a co-movement response and was wrong about which component dominates).**
The grid's movement splits into a large symmetric part and a small
asymmetric part. The symmetric part is DISPERSION, not co-movement: under
FLOOR_MODE='max' any within-run dispersion in the floor lifts the effective
hazard one-sidedly (low cells truncated away, high cells bind), so BOTH
signs of κ move the marginal down once the time order is destroyed, and the
permuted means are near-symmetric in |κ| — 68.888/69.104B at |κ|=0.1,
66.163/64.359B at 0.25, 62.789/56.783B at 0.5. The asymmetric part is the
genuine co-movement: κ>0 (floor rising with rates) lowers the marginal, κ<0
raises it, the true marginals being strongly asymmetric (68.078B at κ=−0.5
against 54.256B at +0.5) where the permuted ones are not. Isolated order
components: +5.289/+4.766/+2.691B at κ=−0.5/−0.25/−0.1 and
−1.420/−1.751/−2.526B at +0.1/+0.25/+0.5 — monotone in |κ| and
sign-consistent, so floor cyclicality is real and directional, but at most
$5.29B in any cell against a grid span of ~$17B. The grid maximum +9.36pp at
κ=−0.1 is within 0.2pp of production (+$1.234B) and is production, not a
cyclicality endpoint.

Artifact: `hazard/data/floor_cyclical_results.json` (runtime 238 s;
per-run parquets under `hazard/data/floor_cyclical/`, regenerable,
gitignored). Manuscript: V.C's concession paragraph upgraded from
"future work" to the tested bound; the VIII.A next-steps sentence
restated in the same pass as §24.2's edits (both further corrected
2026-07-19, see §24.1a). Gate arithmetic (mean-pin, κ=0 nesting, clip
flag) is test-gated in `tests/test_floor_cyclical.py`.

### 24.1a Re-diagnosis of the floor_cyclical range (2026-07-19)

Module: `hazard/floor_cyclical_permutation.py` (pre-committed spec in the
module docstring). Artifact: `hazard/data/floor_cyclical_permutation_results.json`
(seed 20260719, 12 permutations per non-zero κ, multiset AND mean preserved).
Liveness gate #59 binds the artifact to the manuscript literals; tests in
`tests/test_floor_cyclical_permutation.py`.

The diagnosis was first run as a scratchpad probe and has since been promoted
into the repo in the house idiom: the module recomputes the 72-permutation
family, the additive-mode grid, the convexity-matched level controls and the
per-κ decomposition from the macro frame rather than reading any of them from
a stored table, and re-derives the floor path through a positional cursor over
`qt_index` (self-checked every call against the market rate the engine passes,
same wiring idiom as `seasonal_floor_timing.py:476-490`) rather than through
floor_cyclical's rate-keyed callback. That re-wiring is why parity is asserted
BIT-EXACT rather than to a tolerance: anything less would mean the re-wiring
changed the object under study.

Parity first: all SEVEN committed floor_cyclical cells reproduce bit-exactly
(68.078268/70.928467/71.579067/70.345060/67.684635/62.607698/54.256434 B),
and an independent second gate — additive-mode κ=0 giving 86.022492B —
matches committed floor_form_results.json additive@4% (86.0225B/11.2485pp).

The reported range [+7.09, +9.36]pp (span 2.2651pp) is mostly not
cyclicality:

- **Time-order scramble.** 72 permutations span [7.198683, 9.123154]pp,
  1.9245pp = **84.96%** of the committed span. Destroying the time order
  destroys almost none of the range.
- **Combination-rule swap (decisive).** Under FLOOR_MODE='additive' the
  identical κ grid gives [11.220844, 11.265427]pp, span 0.044583pp.
  Changing ONLY the rule eliminates **98.03%** of the span. The additive κ
  grid moves LESS (0.0446pp) than the constant-floor 3–5% level sweep moves
  under additive (0.0845pp: 11.291154/11.248472/11.206648pp at 3/4/5%,
  floor_form_results.json).
- **Low endpoint (κ=+0.5, −16.0886B vs production).** Level-equivalence
  −2.1413B (13.3%); order-free dispersion −11.4211B (71.0%); genuine
  time-order −2.5263B (15.7%) → **84.3% order-free**.
- **Genuine signal (why this is PARTIAL, not a full retraction).** The true
  marginal lies OUTSIDE the whole 12-draw permutation range at every one of
  the six non-zero κ (0/72 draws bracket it), and the order components are
  monotone and sign-consistent (above). Cyclicality moves the marginal in
  the predicted direction; it is the RANGE that is not its measure.

Mechanism is the same one-sided Jensen/max effect already diagnosed and
written up for seasonal_floor_timing (manuscript
`sec:robustness-seasonalfloor`); floor_cyclical predates that diagnosis and
never received it until now.

**Neighbour exposure audit.** `floor_sweep.py:124`, `floor_form_test.py:80`
and `oos_identification.py:258` each set a SCALAR CONSTANT floor per run, so
within-window dispersion is zero and a permutation is a literal no-op: the
level sweep is a genuine level sweep, the form test genuinely tests the
rule, and **the v17 headline (+5.57pp / $42.6B off-window floor) is NOT
exposed**. Only `floor_cyclical.py` and `seasonal_floor_timing.py` vary the
floor within a run.

**Manuscript edits made in the same pass:** V.C's cyclical paragraph
rewritten to report the range, the scramble/additive shares, the Jensen
mechanism (cross-referenced to `sec:robustness-seasonalfloor` rather than
repeated), the surviving directional signal, and the clip-broken mean
pinning; `tab:uncertainty`'s cell relabelled "within-run floor dispersion"
with an explanatory tablenote; `sec:robustness-seasonalfloor`'s opening
sentence corrected to count floor_cyclical among the within-window-varying
checks; the VIII.A next-steps sentence corrected. On promotion, V.C also
gained the `floor_cyclical_permutation` run citation so the artifact is
reachable from the prose.

**Test correction made on promotion.** `tests/test_floor_cyclical.py` carried
the same false invariant as the manuscript did: its docstring asserted the
window mean is "pinned at exactly 4% for every kappa", and
`test_window_mean_pinned_for_every_kappa` asserted `not cf.clip_bound`
alongside the pin. The test passed only because its synthetic six-point rate
series is too narrow for the clip to bind at the kappas it sweeps — it was
gating a claim it could not have falsified. The docstring is corrected, the
test renamed `test_window_mean_pinned_where_the_clip_does_not_bind`, and a
companion `test_window_mean_is_not_pinned_where_the_clip_binds` added so the
conditional is exercised in both directions. The pin was never load-bearing
for any reported marginal; what was wrong was the description of the spec.

### 24.2 W4 Fannie Mae external replication (spec cbabbd2; amendments a3ef6b7, 81c9fd8, f65976a; artifact d8199eb)

The round-14 W4 item executed end-to-end: Fannie SF LPH acquisition
quarters 2017Q1–2022Q4 (24 files) pulled, staged into Freddie-coded
orig/perf pairs, and consumed quarter-at-a-time under the pre-committed
spec (download → stage → per-quarter cells + Path B pool piece → delete;
5.5 GiB free-disk guard; ~76 min of processing across relaunches).
Universe: **17,606,999 loans / 825,814,383 loan-months**; combined panel
23,443 cohort-month cells (explicit vintage filter 2017–2021 = the Freddie
universe definition); 75,000-loan stratified sample from a 267,996-loan
pool (130 strata, production draw design, per-quarter seeds fixed by spec
index). Late acquisition quarters contribute 0 pool rows by construction
(no pre-QT rows) — anticipated in the spec.

Gates, all PASS: (i) Freddie scoring parity — the live macro/SOMA frame
reproduces the committed no-lock-in-null anchors within ±$0.01B/±0.01pp;
(ii) 2019Q1 staging+ingest determinism — cells equal the probe panel
exactly on every deterministic column (15 mode_state divergences, each a
verified modal tie; see the amendment below); (iii) the PRE-REGISTERED
envelope gate. Results: Path B on the Fannie sample — central $820.99B
(107.35%), β₁=0 null $754.60B (98.67%), **lock-in marginal +$66.40B
(+8.68pp of benchmark)** vs Freddie's +$70.35B (+9.20pp): inside the
[2.11, 13.17]pp envelope, within half a point of the Freddie estimate.
Path A FE-Poisson (spec v4) on the Fannie panel: rate-gap coefficient
sign REPLICATES (+2.343 standardized; per-bps ≈3.64× Freddie's), n_train
10,140 / 293 strata, holdout r² −0.05 — the same no-forward-precision
character as Freddie's Path A, so it retains aggregate-corroboration
status; the level difference is exactly what the spec's cross-agency
caveat pre-registered (sign + envelope-conditional marginal, NOT a
hazard-level match; ZBC 06/16 censored, worst-case bracket 0.38% of
removals).

Three production incidents, each root-caused and disclosed BEFORE resuming
(the run ledger's honest-log convention): (1) the 2019Q1 determinism gate
as first committed demanded full-frame equality and failed on
ingest.py:236's mode().first(), which breaks modal ties in nondeterministic
order — a latent property of the frozen Freddie path; all divergences
verified exact ties, estimator columns equal, gate amended to
tie-verification (a3ef6b7). (2) Refi-wave acquisition files are ~5× normal
size (2020Q2: 17 GB native, 1.24M loans / 57.5M rows; 2020Q4: 1.51M loans
/ 80M rows) — eager staging OOM'd (SIGKILL) on the 16 GiB machine; staging
gained a low-memory streaming path (auto ≥5 GiB: streaming sinks, early
native deletion, byte-identical output; 81c9fd8), whose pass-2 polars sort
also OOM'd and was externalized to sort(1) with LC_ALL=C on the unique key
(byte-preserving, disk-spilling; f65976a). (3) The frozen ingest cells
build needed POLARS_MAX_THREADS=4 on ≥80M-row quarters; the runner also
gained a staged-pair resume so a completed pair is never re-downloaded.
2020Q2 was completed manually with the runner's own primitives after the
sort fix (recorded in the quarter manifest with a note).

License enforcement (ratified posture): the committed artifact
`hazard/data/fannie_replication_results.json` carries headline statistics
only; the native files, staged pairs, per-quarter cells/pool pieces,
combined panel, Fannie loan sample, and the Fannie coefficient artifact
are all local-only and .gitignore-blocked. Manuscript: V.C gains the
external-replication paragraph (with both ex-ante scope notes), VIII.A's
Model paragraph gains the one-line result, the next-steps pair is
restated as completed with the 2022/pre-2017 vintage residual retained as
the open item, and `tools/liveness_gates.py` gains a manifest-vs-tex
cross-check (artifact envelope pass + printed marginal literals must
agree; 29 gates now, all PASS; PDF rebuilt).

### 24.3 W6 Danish exact curtailment scaling (spec 81c9fd8, run f-artifact commit)

A third run from the same ratification message (the round-14 parked list's
"Danish exact curtailment scaling"): VII.F's ±25% curtailment stress is
exactly linear for U.S. legs by construction, but the Danish legs compute
curtailment on their own compounding counterfactual balances, so the
manuscript could only assert their differential "stays immaterial (below
$1 billion)" to first order. Run: the production Danish path re-scored
through the shared accounting layer with the curtailment rate at
{0.75×, 1.0×, 1.25×} (rate-only stress; income fraction untouched;
simulated CPR paths asserted bit-identical across scales — curtailment
enters only the accounting layer). Implementation note: patching the
`CURTAILMENT_CPR_HEALTHY` module global alone is a silent no-op (it is
consumed as a def-time-bound default argument); the operative patch wraps
`curtailment_series` pinning `healthy_cpr`.

Parity at 1.0×: all four gates PASS (US netting $69.5622B exact; Danish-leg
curtailment $70.3345B vs the $70.33 anchor; printed shared-layer Danish
cell $848.8698B vs $848.9 within the danish_discount_bound gate width;
differential $+0.7723B vs $+0.77). Exact differentials: **+$0.76B (0.75×),
+$0.77B (1.0×), +$0.66B (1.25×)** — max $0.77B, below the $1.0B ex-ante
threshold, so the manuscript phrase upgrades to exact figures with NO claim
change. Structural finding: the second-order balance feedback pulls the
differential DOWN at the high endpoint (a faster Danish drain leaves lower
counterfactual balances for the higher rate to act on) — the first-order
intuition that the differential scales up with the rate is wrong in
direction at the margin. Artifact:
`hazard/data/curtailment_danish_scaling_results.json`; VII.F sentence
upgraded in the same manuscript pass as §24.1's edits (PDF rebuilt, all 28
liveness gates PASS).

## 25. Referee Round 15 — Coverage, Composition, and Calibration Runs (July 2026)

Round-15 review (8 "Questions for Authors" + positive overall assessment;
roadmap and response-letter skeleton at
`paper/v16/revision_roadmap_round15.md`). Author ratified all four
proposed decisions 2026-07-16 ("approve all"). Three data runs executed,
each under a spec committed before execution; two new manuscript tables
(tab:specbox, tab:uncertainty) and seven prose blocks added; three new
liveness cross-checks (32 gates now, all PASS; PDF rebuilt, 68pp, zero
undefined).

### 25.1 Q3 marginal heterogeneity decomposition (spec 8d034c5, run d59ed49)

Group-ablation of the +9.20pp Path B lock-in marginal over a vintage ×
coupon-bucket grid ({2017..2021} × {<3.0, 3.0–4.0, ≥4.0}%): per cell, a
paired engine run zeroing β₁ ONLY for that cell's loans (per-loan β₁
vector; engine amendment in competing_risks.monthly_step is a pure
generalization — a constant vector is elementwise bit-identical to the
scalar path). Gates: G1/G2 parity BIT-EXACT (diff 0.0 vs committed central
818.5300844B and null 748.1850240B); G3 additivity residual +0.725B =
+1.0% of the +70.345B total (ex-ante threshold 10%) → shares readable.
Results: all 15 cells positive; 2020–21 vintages carry 72.2% of the
marginal on 73.0% of balance; max cell 20.7% (2021 <3.0%); per-balance
intensity 0.82–1.51×. Reading: the marginal is a book-wide property of
the gap distribution, not one cohort's nonlinearity. Artifact:
`hazard/data/marginal_decomposition_results.json`; manuscript sentence in
V.D (sec:identification).

### 25.2 Q2 Ginnie published-CPR overlay (spec 7ee589f, run 08c676b)

Static $20–47B composition bound upgraded to a time-varying overlay. Data:
monthly agency CPR/CDR/CRR series (Jun-2017–Nov-2025) extracted from the
December 2025 GMAR chart VECTOR PATHS (tools/extract_gmar_dec25.py; the
Dec-2025 issue is the only single-methodology source — its note records
the aggregation revision to weighted-average UPB, where the 2022–2025
issues span three chart/aggregation regimes; stitching 42 endpoint labels
was designed, attempted, and REJECTED for that reason). Extraction
validation: endpoint residuals ≤0.034pp vs printed labels; independently
extracted CRR/CDR charts reproduce CPR to 0.04pp mean / 0.20pp max via
1−(1−CRR)(1−CDR). Construction: 20.4% Ginnie face share scored by the
observed series in BOTH Path B legs (settled-flow adjustment through the
production scorer; SMM conversions per each side's own convention).
Gates: G1 zero-differential parity exact (≤3.4e-13 B); G3 raw-adjustment
verdict bound_revision (+66.28B > 47.3B) with the disclosed post-first-run
amendment adding differential attribution: the GSE-mean placebo moves the
level +27.81B on its own (model level calibration + full-universe-vs-SOMA
composition, common to any observed-series overlay), so the
Ginnie-SPECIFIC differential is +38.46B = 5.0% of benchmark — INSIDE the
committed bound and matching the linearized check (2.14pp window-mean
differential × 0.204 × 82.8 ≈ 36.1B). Headline sensitivities: central
97.9→89.3% shared (107.0→98.4% standalone), null 88.7→81.9%, marginal
+7.34pp — sign-positive and variant-invariant (total-CPR/CRR-only/
placebo: +7.33/+7.34), scaling by the conventional share exactly (0.797
vs 0.796). Structural Ginnie inclusion remains formally declined
(2026-07-15, response of record). Artifacts:
`hazard/data/gmar_dec25_cpr_series.json` (provenance + validation),
`hazard/data/ginnie_cpr_overlay_results.json`; manuscript paragraph in
V.C after the static bound, VIII.A next-steps restated.

### 25.3 Q4 ABM external-gates variant (spec 335797a, run aa65eee)

Reviewer hypothesis: recovery rises without the turnover-floor
recalibration when gates are externally parameterized. Design: DTI 0.43
(CFPB) and λ=2.25 (K–T) already external, unchanged; wait-and-see freeze
20%→18.26% (L&R 6.5%/qtr per 100bp compounded at the production 150bp/6mo
trigger, 1−0.935³); mobility scale anchored to the L&R zero-gap moving
level (1.5%/qtr = 5.87%/yr annualized, verbatim source quoted in the spec
header) with NO floor reference. Cross-design harness (real Freddie
covariates), same pre-registered bands. Gates: G1 harness parity EXACT
(59.303% vs committed 59.303%, diff 0.0000pp); G2 anchor hit (zero-gap
CPR 5.85%; scale 4,472 vs recalibrated 36,086 / frozen 43,883). Result:
recovery rises to 150.6% of benchmark ($1,151.8B) — overshooting by half
— while mean QT-window CPR collapses to ~0.0% and CPR(8% market) = 0.00%,
violating the observed 4–5% discount-cohort band AND L&R's own observed
deep-gap mobility (1.44–1.45%/qtr, 2022–2023). Reading: the exponential
mobility-desire architecture can match the zero-gap level or the observed
deep-gap turnover, not both; the floor anchor is the disciplining moment,
not a suppressing artifact. Incident (disclosed): first launch KeyError'd
on the committed cross-design JSON's `variants` nesting before any
variant ran; script corrected, no results affected. Artifact:
`abm/data/abm_external_gates_results.json` (+ cached external surface
CSV); manuscript paragraph in VII (sec:robustness-crossdesign).

### 25.4 Manuscript pass and gate-suite extension

Eight assert-unique tex edits (backup .bak-round15): E1 tab:specbox
(compact two-panel Path A/B specification, end of V.A — Q1); E2
tab:uncertainty (sampling/seed/calibration on both bases; shared-basis
CIs [97.9, 98.0]%/[88.7, 88.8]% derived from the committed bootstrap
percentiles by the exact 9.0961pp netting — ARITHMETIC-FROM-ARTIFACTS)
+ E5 decomposition sentences, both in V.D (Q8/Q3); E3 Danish
pricing-inertness sentence in V.C (Q6); E4 ex-ante cap-rule arithmetic
appended to the VI.B speculative-design paragraph (Q7; no new numbers);
E6 overlay paragraph in V.C (Q2); E7 external-gates paragraph in VII
(Q4); E8 VIII.A next-steps restatement. Build: 68pp, zero undefined,
residual overfulls ≤3pt. liveness_gates.py gains three manifest-vs-tex
cross-checks (overlay G1+differential verdict+3 literals; decomposition
G1/G2+verdict+composition shares; external-gates G1/G2+floor-violation+2
literals): 32 gates, ALL PASS. UPDATE (same day, "update everything" pass):
the .md/.txt editions were regenerated to the round-15+Q10 generation with
the preserved custom converters (tex2md.py / md2txt.py, session-scratchpad
provenance; want-counts bumped to 14 tables; zero unresolved refs), so the
earlier stale-editions note no longer applies; pypandoc-binary (pandoc 3.9)
is importable but the custom converters remain the edition path.

### 25.5 Q10 expectations benchmark (spec 88ef11e; amendment ef3e317;
### transcription b8ad13c; run 24be41b)

Executed 2026-07-16 on the author's go-ahead, closing the last
pre-committed-but-blocked spec. SOURCE AMENDMENT (committed BEFORE the
transcription commit so the ordering is git-auditable): the spec pinned
"OMO During 2022" but its binding clauses (QT-start vintage; full
Jun-2022–Nov-2025 window) are satisfiable only by the report published
during 2022 — "OMO During 2021" (May 2022; projections from the
Feb-28-2022 balance sheet, May-2022 Plans, runoff modeled from June 2022);
the During-2022 report projects from the Dec-30-2022 balance sheet and has
no agency-MBS paydown series. The spec's nyfed2022 identification was also
wrong (that bib key is the Sept-2022 Teller Window post). TRANSCRIPTION:
five published year-end agency-MBS levels from the NY Fed's own chart-data
workbook (omo2021-xls.xlsx, sheet 'Chart 34': 2021=2615.5 historical;
2022=2599.6, 2023=2319.9, 2024=2072.8, 2025=1849.7 projected, $B); runoff
= first difference; adversarially verified by a 3-agent workflow pass
before commit (independent workbook re-read with column-swap ruled out
against known 2010/2021 holdings; chart-render match; printed anchors
'roughly 68/32 composition', '$5.9T mid-2025 plateau', '$2.61T (32%)'
YE2021; the workbook cover sheet carries the NY Fed's own 'May 2021'
release-date typo, noted). Gate (i) disclosed as reducing to a telescoping
identity for a levels-format source (verification weight on the workbook
citation + this record). RESULTS: projected window runoff $740.583B
(spread rule: uniform within printed year, clipped; 7/12 of 2022, 11/12 of
2025) vs actual $652.752B (SOMA source) → E-benchmark $87.832B (11.5% of
the cap-relative $764.748B). Parity gate EXACT (0.00pp, all five
estimators); identity gate machine-precision. Threshold: null share_E
851.8% > 50% → mechanical-majority SURVIVES. Load-bearing trigger FIRES
(mechanically, benchmark ratio 8.71×) → manuscript states pp magnitudes
are cap-basis (III.D canonical paragraph + V.D pointer). HEADLINE (the
supplementary wedge, computed not hard-coded): the ex-ante projection
already implied $676.92B = 88.51% of the realized cap-shortfall, vs the
null's benchmark-consistent 88.74% — 0.22pp apart; the identified marginal
+$70.35B = 80.1% of the expectations-based shortfall. Manuscript: III.D
expectations-complement paragraph, V.D basis sentence, VI.B cap-rule
backtest sentence (caps ≈ 2× the Fed's own contemporaneous projection of
achievable runoff: 1417.5 vs 740.6). Artifact:
expectation_benchmark_results.json; liveness gate #33 cross-checks
threshold/parity/literals. AMENDMENT (2026-07-16, author-ratified
"implement"): settlement-aware allocation sensitivity added (disclosed,
supplementary, not gated) — the 88.51% anticipated share is the
pre-committed uniform-spread rule's value; allocating the projection's 2022
first-half settlement inflows to Jan–May (proxy: realized H1-2022 rise
+$92.32B in the benchmark's own SOMA series) implies Jun–Dec projected
runoff $108.22B → anticipated share 75.58% (lower bound), null share_E
400.6%, threshold survives. Manuscript: abstract's point value replaced
with "the large majority" (robust to any intra-2022 allocation); III.D
gains the precision-discipline sentence quoting both bounds; gate #33
extended to cross-check the $92.3/75.6% literals and the alt-threshold.

## 26. Referee Round 16 — Weakness-List Revision: Vintage Bound, Dynamic-Fit Diagnostics, Flexible-Learner Comparator (July 2026)

Source: an author-supplied five-cluster weakness list (technical limitations,
experimental gaps, clarity/presentation, missing related work; no verdict, no
positives block), parsed 2026-07-16 via the revision-coach protocol against
HEAD 7fc22da into `paper/v16/revision_roadmap_round16.md` (10 items: 4 Major,
5 Minor-constructive, 1 Editorial). A 12-agent assessment pass found three
items already answered by committed artifacts (W1 uncertainty, W2's agency
half, W3's substance), four placement/prose/citation fixes, and three
feasible new runs. Author go-ahead of record: "can we fix everything here?"
(2026-07-16). Three runs executed under spec-before-run (spec commit
725f92f), ~20 tex edits applied (backup `.bak-round16`), five bib entries
added plus one upgraded, gate suite extended 33→36, PDF rebuilt (74pp, zero
undefined), md/txt editions regenerated (15-table validation), bundle
restaged. New decline of record: loan-level deep-learning head-to-head
(data grounds — raw loan-month universe not shippable; comparator supplied
at the paper's own unit of analysis instead). Prior declines preserved.

### 26.1 W2 vintage residual bound (spec 725f92f, run e535459)

Reviewer: hazards are Freddie 2017–2021; older vintages' extrapolation "only
indirectly bounded." The manuscript's standing concession ("no bound of
either kind", III.D/V.C/VIII.A) was closable from data already on disk: the
W4 Fannie replication ingest's retained per-quarter cell files
(`hazard/data/fannie_quarters/`, local-only, gitignored) carry observed
QT-window prepayment for the 2022 and pre-2017 vintages. Construction:
pooled dollar SMM compound-annualized per segment over the 42-month window;
signed differentials vs the sampled 2017–2021 universe; face-share weights
0.231/0.106 (`wal_table.VINTAGE_SHARES`); dollar bound via the static Ginnie
bound's 82.8 $B/CPR-pt sensitivity. Gates: G1 parity of the cells against
the committed combined panel (exposure rel diff 0.0, prepaid 5.4e-16,
loan_count exact 393,755,296); G2 manifest ties local cells to the committed
replication universe exactly (17,606,999 loans / 825,814,383 rows); G3
sampled CPR vs panel rate-column 1.1e-05pp; G4 constants integrity. All
PASS. **Result: sampled 4.303%, 2022 vintage 4.476% (+0.173pp), pre-2017
5.264% (+0.962pp); share-weighted book-CPR error +0.1419pp → bound $11.75B,
1.54% of benchmark, verdict below_ginnie_bound, signed overstates_trapped**
(out-of-sample vintages prepaid faster — conservative for the headline, the
same direction as the Ginnie bound). Mean-monthly variant $11.99B disclosed,
not primary. Caveats carried in artifact and tex: Fannie-proxies-SOMA
posture; pre-2017 leg is a seasoned acquisition tail (~3.4M QT loan-months);
2022 leg is a full-year speed applied to an H1-tilted face; overlaps the
Ginnie bound on Ginnie's out-of-sample vintages (not additive). Artifact
`hazard/data/vintage_residual_bound_results.json` (headline stats only,
license posture identical to the replication). Manuscript: V.C bound
paragraph rewritten, III.D coverage parenthetical updated, VIII.A
"remains unbounded" retired in favor of the bound + the proxy assumption
that stays open. Gate #34 added.

### 26.2 W4 Theil dynamic-fit diagnostics (spec 725f92f, run fb6cc24)

Reviewer: detrended co-movement weak; wants Theil decomposition and
cumulative error profiles. Round-15 Q5's "fit diagnostic (NOT a timing
credential)" option, now exercised. `figures/make_theil_data.py`
pattern-copies `make_ccf_data.py` (hazard-side empirical via FRED+SOMA;
inputs gated to committed references: ABM CCF 1e-9, Path A 1e-3, Path B
1e-6; terminal cumulative errors reproduce $928.893B/$818.530B exactly,
diffs 0.0). Nine gates, all PASS. **Result: levels U1 ABM 0.412 / Path A
0.431 / Path B 0.265; levels MSE shares (bias/var/cov) ABM 68.1/0.4/31.5,
Path A 26.5/10.6/63.0, Path B 6.7/86.6/6.7; detrended variance share Path B
93.7; U2 on first differences 1.226/1.010/1.003 — no estimator beats a
naive no-change forecast.** Reading (pre-committed cells hit exactly): Path
B's error is variance-dominated with near-zero bias (level accuracy;
residual is under-dispersion against a seasonal empirical path); the ABM's
is bias-dominated (level failure); the U2 row restates the
no-timing-credential concession in forecast-accuracy units. Terminal
cumulative errors: ABM −$673.8B, Path A +$164.1B, Path B +$53.8B (each =
trapped aggregate − empirical $764.7B on its own basis). Artifact
`figures/theil_data.json`. Manuscript: V.C paragraph after the moving-block
discussion; new appendix section with `tab:theil`; pointer sentence in
`tab:estimators` notes. Gate #35 added.

### 26.3 W6 flexible-learner comparator (spec 725f92f, run 97674e0)

Reviewer: "no head-to-head predictive comparisons" with survival ML. The
sadhwani2021-class deep loan-level comparator is declined on data grounds
(recorded above); the deliverable comparison at the paper's own unit ran
instead: `hazard/ml_comparator_holdout.py` reuses `pathA_v4_holdout`'s
panel pipeline, split (2024-01-01), and exact RMSE formulas; parity gates
reproduce the frozen artifacts first (v4 37.9032/3.0379pp, v3
37.8295/2.5338pp, diffs ~1e-10 — proving identical split+metric before any
learner runs); hyperparameters selected train-only (temporal inner split,
2023 validation year). All gates PASS. **Result: HGB-Poisson (lr 0.05, 15
leaves, 300 iters) holdout exposure-weighted RMSE 0.926pp vs Path A v4's
3.038pp (material under the pre-committed 0.80x threshold), unweighted
37.63pp vs 37.90pp (not material), R2 +0.0029; penalized Poisson GLM
(alpha 1e-6) 2.610/38.06/−0.0198. Overall verdict (pre-committed):
flexible_fit_helps_no_headline_change.** Reading: flexibility recalibrates
the high-exposure cells out-of-sample but gains no cross-cell predictive
power in the 2024+ regime; Path A remains excluded from headline figures by
pre-committed spec, so no headline moves and the Section II transparency
rationale stands with an empirical price tag. Artifact
`hazard/data/ml_comparator_holdout_results.json`. Manuscript: V.B holdout
paragraph extended; Section II "rather than implementing them here" clause
replaced with the comparator pointer. Gate #36 added.

### 26.4 Manuscript pass, citations, and gate-suite extension

Tex edits beyond the three run blocks (backup
`paper/v16/revised_paper_v16.tex.bak-round16`): E1 intro — bootstrap CI
[+9.17,+9.23]pp attached at the marginal's first mention (W1; abstract
deliberately unchanged per the precision-discipline posture); E2 III.C —
floor-anchor tautology named head-on ("an input, not a finding"; W3), with
a reinforcing clause in VII.D's external-gates paragraph; E3 III.D — the
accounting-convention sentences pulled out of the coverage mega-paragraph
into a titled "Accounting bases." paragraph stating the bit-identical
cancellation guarantee at first use (W5); E4 anticipated-share framing —
intro, III.D, V.D now lead with 75.6–88.5% (88.5% labeled the uniform-spread
central construction), VI.B cap multiple restated as "roughly 1.7 to 1.9
times" with the allocation dependence disclosed (W8); E5 Section II — deep
mortgage ML engaged on substance (120M-loan burnout/nonlinearity learning
vs Path A's explicit burnout regressor and the ABM falsification) and the
landmarking/drift strand added (W9); E6 conclusion — hedging-side
literature paragraph (who bears/prices/hedges prepayment risk under each
payoff rule; behavioral residual only boundable; W10), with the lit-review
perotti2024 clause extended to name its robust-hedging contribution; E7 —
W7 trim-and-move: provenance boilerplate deleted at ~10 main-text spots
(caption tails, '(frozen-run manifest)', duplicated manifest note,
artifact filenames, four commit hashes, script path) and consolidated into
a new "Reproducibility conventions." paragraph in the run-ledger appendix;
fn:manifest slimmed to its load-bearing content. Bibliography: added
vanhouwelingen2007 (SJS 34(1)), putter2022 (SiM 41(11)), peng2026
(arXiv:2601.20533 — the "LMISO" reference), gabaix2007 (JF 62(2)),
malkhozov2016 (RFS 29(5)); perotti2024 upgraded to the published JCAM 477
(2026) version, key unchanged; all web-verified before insertion; the
sadhwani2021 key/order stays per the round-14 three-way verification (the
reviewer's "Sirignano–Sadhwani–Giesecke" is the 2016 working-paper order).
Gate suite: three manifest-vs-tex cross-checks added (#34 vintage bound,
#35 Theil, #36 ML comparator), each requiring the in-run gates to have
passed, the pre-committed verdicts as printed, exactly one lowercase run
citation, and the printed literals to match the artifact rounded as
printed. 36 gates ALL PASS at the round-16 head. PDF rebuilt twice with
Tectonic (74pp, zero undefined references); md/txt editions regenerated
with the preserved converters (table want-count 14→15 for `tab:theil`);
`~/Downloads/UPLOAD_ROUND11` restaged (round-15 generation preserved in
`superseded-2026-07-16-round15/`). Response letter filled in
`paper/v16/revision_roadmap_round16.md`.

### 26.5 Title change and voice/tone passes (author-directed, same day)

Three author-directed manuscript passes followed the round-16 revision, all
verified under the full gate suite and rebuilt (PDF, md/txt editions,
Downloads + bundle staging refreshed each time). (a) Single-author voice:
we/our/ours/us → I/my/mine/me, 137 word-boundary replacements; the
historical self-quote "sign we cannot identify" kept verbatim. (b)
Concision: 142 edits from a 13-agent section sweep, each passing a
mechanical invariant verifier (numbers, refs, cites, texttt, quotes, and
run citations multiset-equal between old and new; scratchpad
apply_concision.py), ~5,000 characters of metadiscourse and doublets
removed; ledger paper/v16/concision_pass_round16.md. (c) Title + register:
the coined "Securitization Trade-Off" was retired — the phrase collides
with the existing securitization trade-off literature (author's catch) —
title now "Mortgage Lock-In and the Federal Reserve's Quantitative
Tightening Shortfall" (gate #10's exactly-one string updated accordingly);
the four coinage sites became plain description of the two-sided exchange;
83 register edits from a second 13-agent sweep dropped rhetorical emphasis
("precisely", "vindicated"-class verbs, reader-coaching adverbs) under the
same invariant verifier plus a no-mushy-hedges check, with one proposal
rejected in review ("materially" in the ML-comparator sentence is
pre-committed threshold vocabulary, not swagger); ledger
paper/v16/humility_pass_round16.md. Scope discipline throughout: every
negotiated hedge and verified-precision phrase grep-confirmed to survive
each pass. Manuscript now 71pp, zero undefined references; abstract 232
words; 36 gates PASS at every step. A same-day figure-placement pass
(author-directed) moved fig:waterfall's block to its first-mention
paragraph, ordered all eight figure environments by first mention, and
switched every figure to exact [H] placement (float package added):
figures no longer drift from their citing text — each renders on its
first-mention page or the next (verified in the built PDF), at the cost
of short pages where a figure breaks (73pp).

### 26.6 Figure pass: the 3D grid rendered, plus three artifact-backed additions (author-directed, 2026-07-16)

Author-directed: the manuscript described the ABM's three-dimensional CPR
grid (§II.B) without showing it, and a multi-agent audit of the remaining
sections (6 section scanners → 18 proposals, 15 artifact-feasible, judged
by a 3-lens reader-value / economy / integrity panel) found three more
places where a claim carried entirely in prose had a committed artifact
behind it. Four figures added, all generated by `figures/make_figures.py`
from committed artifacts only (no hardcoded result literals; the existing
figure-script gates cover the new generators automatically):

- `fig8_cpr_surface` (fig:cprsurface, §II.B): the precomputed CPR surface
  at the 3.0% thirty-year SOMA cohort — rate × friction heatmap
  (no-freeze regime) with the 42 realized QT-window (rate, friction)
  months overlaid, plus rate slices showing the wait-and-see freeze and
  the Berger-recalibrated near-flat Danish curve. The generator asserts
  the grid's two-regime velocity structure (velocity enters only through
  the freeze), so a future spec change breaks the build loudly.
  Provenance: the U.S. 3.0%/360 slice is git-identical across 5cf33a3
  (fold-in), bc07d32 (native 15yr), and d3e21f6 (Berger), so the slice
  shown is exactly what the frozen production run interpolated; the
  Danish column is the Berger production spec.
- `fig9_benchmark_construction` (fig:benchmark, §II.D): monthly roll-off
  vs the phased cap (net-inflow months circled) and cumulative paths with
  the $764.7B / $87.8B wedges; the projection's monthly path is derived
  under the pre-committed uniform-spread rule and asserted in-generator
  against `expectation_benchmark_results.json` window totals (realized,
  cap, and projection cumulatives all assert-checked). Caption avoids a
  second `run` citation so the exactly-one run-citation gates stay green.
- `fig10_abm_cpr_paths` (fig:abmpaths, §III.A): simulated vs empirical
  CPR paths (fold-in run); means, lag-0 r, and R² annotated from the
  frozen manifest.
- `fig11_marginal_decomposition` (fig:marginalcells, §V): vintage ×
  coupon group-ablation cells from `marginal_decomposition_results.json`;
  footer states the additivity residual (1.0%).

Duplicate-merging: the audit's two §II.D expectations proposals and the
policy-section cap-vs-projection proposal collapse into fig9's right
panel; the marginal-across-constructions forest plot and the remaining
shortlist items were declined as redundant with existing tables (the
calibration box, tab:bases) or as single-number figures. All 37 liveness
gates PASS; PDF rebuilt with zero undefined references; md/txt editions
regenerated (converter's element-count self-check updated to figures=12);
UPLOAD_ROUND11 bundle restaged.

Same-day follow-up (author-directed): tables extended to the figures'
exact-placement convention and a whitespace pass run over the result. All
15 `\begin{table}` placements converted from `[!htbp]`/`[t]` floats to
`[H]` — this fixes the drift the author flagged (tab:uncertainty rendered
after §V.E's opening despite being discussed before it; tab:estimators
two pages past its summary paragraph; both now render in source order at
their home paragraphs). Two float-era `\newpage` leftovers after tab:wal
and tab:delinq removed (each was orphaning most of a page). A PyMuPDF
whitespace detector (content-bottom per page vs text height) then drove
figure fits: canvases compressed rather than print-width shrunk so fonts
keep size (fig1 4.8→3.7in, fig3 5.0→3.9in, fig6 4.2→3.1in, fig8
4.1→3.5in, fig9 4.0→3.3in heights; fig2 → 0.9\textwidth, fig9 →
0.94\textwidth; fig8/fig9/fig1 captions tightened; fig3's pre-existing
clipped one-line footer split into two lines). Result: fig8 fits its
§II.B page, fig9 its §III.D page, fig1+fig3 share the §IV page, fig2 and
fig6 close their gaps; manuscript 74pp (vs 75pp before the table
conversion and 78pp immediately after it). Remaining short pages are all
table-inherent (the full-page tab:danish, tab:bootstrap, tab:estimators
under exact placement), the deliberate pre-appendix `\newpage`, and the
final page. Gates 37/37 PASS; zero undefined references; editions and
bundle refreshed.

## 27. Round-17 revision: full referee report — seven runs, three tables, identification status (2026-07-17)

Source: a complete external referee report on the v16 draft (strengths /
3+2+2+2 weaknesses / 10 detailed comments / 7 questions / overall
assessment "solid potential for a top-tier venue"). Parsed by a 15-agent
revision-coach assessment against HEAD; roadmap and response letter in
`paper/v16/revision_roadmap_round17.md`. The parse found the report's
three "main limitations" to be third-generation recurrences with
quantified stacks at HEAD, and four reviewer premises factually wrong in
the paper's favor (production curtailment already monthly income-tied and
the netting cancellation structural under any time profile; the Danish
OAS sensitivity already printed as tab:discount with a structural $0.00;
3 footnotes total; the settlement-aware allocation IS the requested
back-loaded spread). Author go-ahead of record: "go" (2026-07-17).

### 27.1 Runs (spec commit ef039ca; per-run artifact commits 2ef6fea..08dc288)

Seven pre-committed specs, all executed same-day, all in-run gates PASS:

- `hazard/composition_shift.py` (R17-B/Q1, gate #38): formal
  covariate-shift table, Freddie sample/universe + Fannie sample/pools vs
  the SOMA book via the production CUSIP parser, anchor-gated to the
  committed marginals (WAC 2.490, GNMA 0.2042, terms 0.906/0.091/0.002,
  vintage max|d| 0.0010). The NY Fed API served the historical June-2022
  as-of (2022-06-29) — reported as a non-gated secondary block. PSI:
  coupon 2.29 / vintage 4.33 / agency 2.54 (large, the expected/disclosed
  outcome, each with its committed bound as consequence); Freddie-vs-Fannie
  state 0.018 / orig-UPB 0.000 / FICO 0.005 / LTV 0.000 (all negligible)
  → verdict cross_agency_stable. Geography/size/FICO/LTV for the book:
  DECLINED (CUSIP-level disclosure), substitute supplied.
- `abm/freeze_sensitivity.py` (R17-C/Q4, gate #39): scored on the frozen
  berger-run accounting (production parity +$0.02B). Freeze-off $44.6B →
  isolated freeze contribution +$39.9B/+5.2pp; triggers 100/150/200bp →
  $105.9/99.7/70.5B; share sweep with floor RETAINED 10/18.3/30% →
  $65.1/81.5/103.3B vs production $84.5B (L&R-implied share moves recovery
  −0.4pp). G6: calibrated scale and floor CPR bit-identical at every share
  (the floor point is evaluated at zero velocity — freeze cannot bind).
- `hazard/landmark_isotonic_holdout.py` (R17-D/Q3, gate #40): LMISO-style
  exposure-weighted isotonic map fit on 2023 only, applied to frozen spec
  v4 holdout predictions; v4/v3 parity to committed digits first.
  2.534pp weighted / 37.82 unweighted / R² −0.007 vs frozen
  3.038/37.90/−0.011; verdict no_material_change (0.80× threshold
  2.430pp). Rolling-landmark variant declined in-spec (different protocol).
- `hazard/marginal_monthly_decomposition.py` (R17-L/DC6/Q7, gate #41):
  monthly marginal path from the two committed legs (sum bit-exact
  $70.34506041989584B); all 42 months positive, thirds 21.3/41.9/36.8%,
  peak 2023-11 $2.29B; month × 15-cell retention with terminal cells
  bit-exact vs the committed decomposition, per-month additivity residual
  cumulating to the committed +0.725B; coupon buckets 38.0/43.7/18.3% of
  cells sum. Verdict monthly_shares_readable. Figure data
  `figures/marginal_monthly_data.json` (theil_data precedent).
- `abm/interp_spot_check.py` (R17-J/DC3, gate #42): G1 amended at first
  execution, BEFORE any off-grid number was interpreted — the committed
  CSV's Danish column serializes one ulp short of round-trip, so Danish
  tolerance bit-exact → 1e-12 (observed 7.6e-15; US stays bit-exact,
  observed 0.0). Non-kink off-grid max 0.230pp (inside the pre-committed
  0.25pp), Danish exact; realized weighted mean 0.217pp breaches the
  0.05pp tolerance via the pre-registered kink mode: 4 realized months
  (2022-08..11) sit in the freeze's velocity-ramp band, where the engine's
  step and the surface's ramp differ by construction — surface semantics
  the production figures share, priced at the trapped level by the
  freeze_sensitivity binary-step leg.
- `abm/smd_two_moment.py` (R17-K/DC4, gate #43): joint 2-parameter fit
  (mobility scale + forced-move point mass π₀, an explicit structural
  extension; π₀=0 wrapper bit-identical, G2 96-point probe exact; 59.303%
  harness replay). Verdict joint_fit_infeasible: at the distance-minimizing
  point (scale 1,000, π₀ 3.9%) M1 0.0644 vs [0.055,0.063] and M2 0.0394
  vs [0.040,0.050] — the forced mass lifts both moments together once the
  scale bottoms out. Near-fit scores 107.1% of benchmark (far above the
  35/50 bands). QT-window moment-matching declined on discipline grounds.
- `hazard/wal_table.py` extension (R17-E/DC10, gate #44): two Danish rows
  through the identical calculator under the unchanged V15 parity gates —
  danish_us_intercept (5.61%) 9.1/8.2yr, danish_level (3.39%) 10.8/9.6yr;
  rule-only WAL shortening 0.6yr vs Path B's 9.7.

### 27.2 Manuscript edits (backup .bak-round17)

P1: (i) identification status — new fifth qualification in V.D
("identifies" = within-model counterfactual decomposition, not causal
identification; no quasi-experimental variation exploited or claimed;
β₁'s causal content inherited from liebersohn2024, fonseca2024
corroborating), VIII.A limitation sentence, abstract "identified
contribution" → "contribution", the one unqualified causal claim ("the
paper's causal channel") reworded to "the mechanism the paper
quantifies"; (ii) tab:headline at the end of Section I (committed values
only, all \ref); (iii) app:composition + tab:composition + two pointer
wirings (V.C bounds paragraph, VII full-book-weighting sentence).

P2: freeze-sensitivity paragraph in VII (extensions) + floor-insulation
sentence in III.C; isotonic sentence in V.B + Section II comparator
clause updated; timing paragraph in V.D + tab:pathadiag at the end of
V.B + app:theil null-profile sentence; competing-risks taxonomy paragraph
in V.C (putter2007/fine1999/meir2025-PyDTS; fractional-prepayment caveat);
burnout-selection engagement ×3 (II, V.B stratum design, IV.B degenerate
limit) citing lesniewski2026 (arXiv:2603.12422, web-verified); curtailment
invariance upgraded to its structural any-monthly-profile form (III.D and
VII.F); omo2021 citation at the expectations-complement construction + the
no-public-monthly-path clause; two Danish WAL rows + extension-per-regime
reading sentences (extension-not-convexity scoping restated). P3: the
β₁-conversion footnote's derivation detail moved to app:params with a
one-clause pointer (footnote census now: R² convention, fn:manifest,
slimmed conversion hedge).

Declines of record this round (new): SOMA-book geography/loan-size/
FICO-LTV composition (CUSIP-level disclosure; Freddie-vs-Fannie substitute
supplied); Fed staff internal monthly projection paths (non-public at any
covering vintage); QT-window CPR moment-matching for the ABM (recovery
would become a fitted quantity). Preserved: loan-level deep multinomial
(data grounds); structural Ginnie inclusion; option-model convexity
(extension quantified instead). The mid-2022 mobility-dip citation was
investigated and NOT added: the Census CB24-TPS.118 release verifies but
prints no mover-rate figure in the release text, so the freeze trigger
keeps its no-external-source concession.

### 27.3-pre Follow-up: the four optional items executed (author-directed, same day)

Author go-ahead: "can you work on everything on the not done?" All four
items the round left optional were then executed under the same
discipline (specs ea13e0f/3a73209; runs 8170152/fa0e5e5/bb95a7b/00c79b6):

- `hazard/curtailment_profile_demo.py` (gate #45): unit/seasonal/
  regime-split profiles wrapped around `fed.curtailment_series`
  (patch-and-restore; the CURTAILMENT_CPR_HEALTHY global is a documented
  silent no-op and never touched); unit parity to the committed
  $69.56220187263008B netting and shares; CPR paths bit-identical;
  netting equal central-vs-null. The wedge moves (9.16/8.90 vs 9.10pp;
  netted $70.06/$68.09 vs $69.56B) while the marginal is IDENTICAL at
  +9.198460pp / $70.3451B to ≤1.4e-14pp — verdict: identity demonstrated.
  One sentence added to VII.F.
- `hazard/expectation_spread_variants.py` (gate #46): pure arithmetic on
  the committed expectations artifact; G1/G2 reproduce 88.514967/75.576515
  at rel 0.0. Plausible ramps: 2022 back/front 88.05/88.98%; 2025
  all-front 86.08% (lowers — more in-window projection), 2025 linear
  back-ramp 90.57%; all-December bracket 115.26% with a degenerate-E flag
  (projection then exceeds realized). Threshold survives everywhere. NOTE:
  the roadmap's earlier read-only direction labels were SWAPPED; the run
  records the correction in prior_reconstruction_check. One sentence added
  to III.D.
- `hazard/danish_discount_bound.py` grid fill (gate #47): SPREADS
  {0,25,50,75,100}bp; flips 0/2,470/7,805/17,493/32,488 of 1,683,082,
  monotone, with CPR paths bit-identical and $0.00 deltas at every point;
  tab:discount now prints five rows and the 25--100bp phrasing replaces
  50--100bp at both mentions.
- `figures/make_figures.py` fig12_marginal_timing (fig:marginaltiming,
  §V.D): stacked monthly marginal by coupon bucket with aggregate overlay,
  peak and thirds annotations, nine in-generator asserts, all series read
  from marginal_monthly_data.json (zero literal-scan hits); footer split
  to two lines per the §26.6 clipped-footer precedent; placed [H] at its
  first mention in the timing paragraph. Figures now 13 (converter
  want-count updated), tables 18.

Manuscript 82pp, zero undefined references; liveness gates 44 → 47, ALL
PASS; 39 tests pass; editions and UPLOAD_ROUND11 refreshed
(BUNDLE_NOTES_ROUND17.md addendum).

### 27.3 Gates, bib, editions

Liveness gates 37 → 44 (#38–#44 artifact-vs-tex cross-checks in the
round-16 pattern: in-run gates PASS + exactly-one run citation + printed
literals derived from the artifact), ALL PASS. references.bib 54 → 59
(lesniewski2026, putter2007, fine1999, meir2025 JOSS, omo2021 — all
web-verified; fine1999 volume confirmed 94(446) against Crossref). PDF
rebuilt (tectonic, 80pp, zero undefined references); md/txt editions
regenerated (tex2md want-counts now tables=18; converters in
session-d36a47d9 scratchpad); UPLOAD_ROUND11 restaged
(round-16 generation → superseded-2026-07-17-round16/,
BUNDLE_NOTES_ROUND17.md). Letter placeholders filled with executed
values in revision_roadmap_round17.md. Commits local — push awaits
Eugene.

## 28. Round-18 revision: full referee report — eight runs, basis crosswalk, non-cancellation finding (2026-07-17)

Source: a second complete external referee report on the v16 draft
(technical/methodological/clarity/related-work weaknesses, detailed
comments, 10 questions, overall assessment "strong candidate for a
top-tier field venue" conditional on enhancements). Parsed by an 18-agent
coverage-and-adversarial-verify pass against HEAD (9 cluster readers + 9
verifiers; 16 reference-precision corrections applied, zero coverage
verdicts overturned); roadmap and response letter in
`paper/v16/revision_roadmap_round18.md`. The parse found 12 of 30 items
already addressed at HEAD, 18 partial, 0 absent; three requests already
executed in rounds 15–17 (seasonal curtailment = gate #45's demo run;
landmark+isotonic = gate #40's run; Danish OAS = tab:discount, short only
of the reviewer's 150bp endpoint), and one existing object needing only
reframing (Path A's fitted rate-gap coefficient IS the requested in-sample
elasticity). Author go-ahead of record: "go" (2026-07-17).

### 28.1 Runs (per-run artifact commits 060a725..2b86b57; opus subagents, spec-before-run)

Eight runs (seven main + the E3 cohort-timing diagnostic added on author
approval), all in-run gates PASS at execution:

- `hazard/subgroup_marginals.py` (R18-A, gate #48, commit 2b86b57): the
  review's most-repeated ask (M1+E2+Q3) — group-ablation marginal
  decomposition extended past vintage × coupon to FICO/LTV/Census-region
  partitions of the 75k sample (region replicates
  `agents.MicrosimPool.region_code` including the GU/PR/VI→West
  fallback). Central/null parity bit-exact (818.5300844066606 /
  748.1850239867648, diffs 0.0). All nine cells positive; per-balance
  intensities 0.879–1.261 (tighter than the committed grid's 0.8–1.5);
  additivity residuals 0.80/0.37/0.54% (all under the committed 1.03%);
  largest cell 740+ FICO $40.38B at 0.88×. Verdict (pre-committed rule):
  broad_based_all_dimensions — the generality outcome the referee named.
- `hazard/regime_split_marginal.py` (R18-G, gate #50, commit bf0a3db):
  ±20% multiplicative break on h₀(a) from 2023-01 (pre-committed date and
  grid), applied identically to both legs, nothing fit to the benchmark.
  **The round's consequential finding: the marginal does NOT cancel under
  a multiplicative baseline break** — it scales with the baseline level,
  +4.966pp ($37.97B) at 0.8× to +12.124pp ($92.72B) at 1.2× around the
  bit-exact +9.198460pp anchor; a floor-only ±20% break moves it
  oppositely (+6.573 to +10.411pp). Verdict material_sensitivity per the
  pre-committed envelope rule (outside the cyclical-floor band E2, inside
  the calibration box E3, sign-positive everywhere). This REFUTED the
  roadmap's drafted E4 cancellation narrative — cancellation is an
  additive-layer property (curtailment), not a multiplicative-baseline
  one — and the planned V.D sentence was replaced with the honest
  statement before any commit carried the wrong claim. Pre-break marginal
  identical at 5.330696B across all five legs (wrapper validation).
- `hazard/danish_discount_bound.py` 125/150bp fill (R18-I, gate #51,
  commit 7fb4cbb): SPREADS extended to the reviewer's named endpoint;
  flips 55,210 / 92,495 of 1,683,082 at 125/150bp with deltas exactly
  $0.00 (trapped standalone 934.2540552143059B identical at every grid
  point); five prior rows byte-identical; grid now [0,25,50,75,100,125,150].
- `hazard/grouped_calibration.py` (R18-J, gate #52, commit 8c3e8c9):
  Q10's grouped exhibit — frozen spec v4 predictions on the committed
  16,253-cell panel, five exposure-weighted prediction quintiles (edges
  fit on train only) × ten calendar half-years, pure scoring. Frozen-RMSE
  parity bit-exact (3.037942336998421 / 37.903228802264934). Train pooled
  predicted/realized 1.000 (exact by construction of the exposure-offset
  fit; per-half 0.80–1.17); holdout 0.532 with monotone worsening
  0.64/0.57/0.44/0.43 across 2024H1–2025H2; upper bins 0.94–1.11 pooled.
  Verdict temporal_drift_post_boundary — localizes tab:theil's U₂>1 to
  prediction level × half-year. Path A diagnostic; no headline touched.
- `hazard/fonseca_band_anchor.py` (R18-B, gate #53, commit 67738ae):
  fonseca2024's ~9%/100bp moving-rate reduction through the eq:beta1
  transform (β₁=0.0962) and the production band machinery
  (`floor_sweep._run_scored` unchanged, parquets isolated): marginal
  +$87.883B/+11.492pp at the 4% floor — ABOVE the L&R high edge
  (+$79.47B/+10.39pp), inside the pre-committed box. Committed
  central/null/marginal and both band edges reproduced bit-identically.
  Reading: corroboration from the stronger side; the adopted L&R central
  is the conservative choice. Unit caveat carried in artifact and letter
  (moving-rate reduction vs quarterly-mobility decline; treated
  quarterly-equivalent under the transform's near-frequency-invariance).
- `hazard/vintage_1516_subleg.py` (R18-K, gate #54, commit 060a725): the
  referee-named 2015–16 cohorts isolated from the pre-2017 tail by
  re-aggregating the committed Fannie ingest cells (manifest ties
  d8199eb: 24 cell files, 17,606,999 loans / 825,814,383 rows). They are
  99.99% of the tail's exposure: observed speed 5.2644% (+0.9617pp),
  bound with isolation $11.7484B/1.536% vs committed $11.7481B; residual
  pre-2015 tail degenerate (332 loan-months, 2010–2013; no 2014 vintage
  in the ingest). The named cohorts sit inside the bound already priced.
- `hazard/curtailment_profile_demo.py` servicer_mix profile (R18-N,
  gate #45 artifact extended, commit 7fb4cbb): deterministic 0.60/0.40
  two-servicer mix (front-loaded and flat group factors aggregating to
  one monthly rate) as a fourth profile — wedge 9.299pp/$71.118B netted,
  marginal 9.198459770709775pp (departure 1.42e-14pp from unit);
  unit/seasonal/regime results byte-identical to the committed artifact.
- `abm/cohort_timing_diagnostic.py` (R18-L / referee E3, gate #55,
  commit 2ab7582): the E3 cohort-split timing falsification, run after
  the author approved the initially-optional extension. Parity bit-exact:
  abm CCF lag-0 −0.3183375411255578, Path B first-difference velocity
  −0.9428012605757549 (= manuscript −0.94), empirical +0.25496827096410607
  (= +0.25), band 2/√41 = 0.31234752377721214. Predicted 30-year coupon
  cohorts 2.0–4.5% all track the contemporaneous rate mechanically
  (Δ-corr −0.87 to −0.94; five of six cohorts phase-locked at lag 0, the
  4.5% coupon CCF peaking at lag −6 with r=−0.29 — the frozen artifact
  verdict string still says "phase-locked at lag 0" for all six and was
  left untouched); realized cohorts (Freddie 2017–21 + Fannie
  replication) show no rate-velocity response at any lag ±6mo (Freddie
  lag-0 −0.05 to −0.16, Fannie −0.03 to −0.14, all inside ±2/√n; best |r|
  over all cohorts/lags 0.343). Residual structural not compositional,
  not a datable phase shift. HONEST LIMIT (carried in §V.C and the letter):
  realized cohort monthly CPR exists only in the loan-level Freddie/Fannie
  panels (Path B universe), not the SOMA holdings behind the aggregate
  empirical CPR — which justifies the estimator-level timing falsification
  staying at the SOMA aggregate; pooled Freddie realized velocity −0.074
  vs SOMA +0.25 differ in sign but both deep inside the zero band. 7 gates
  PASS, deterministic. Note the artifact stores `gates` as a list (the
  other round-18 runs use dicts); the liveness check #55 handles both.
- `abm/dti_threshold_sweep.py` (R18-C, gate #49, commit ad83725):
  36/43/50% front-end DTI wall on the frozen berger surface
  (run-2026-07-05-berger, surface sha pinned; the run completed but its
  agent's turn ended before reporting, so the artifact was audited
  directly). Trapped $153.35B / $84.53B / $119.70B (share 20.05 / 11.05 /
  15.65%); production 43% reproduced to +$0.025B (G1c). Involuntary floor
  re-anchored into [4,5]% at every threshold (G6 floor-retention PASS,
  recal floor_cpr 0.0483 / 0.0442 / 0.0447, all in-band). Isolated DTI
  contribution production-vs-50% −$35.16B, production-vs-36% −$68.82B.
  The ABM trapped estimate is materially DTI-sensitive — reinforcing that
  the headline rests on the hazard marginal, not the ABM gates — while
  never breaching the floor. 8 gates PASS.

### 28.2 Manuscript edits (backup .bak-round18)

Zero-compute batch: numeric FICO/LTV/coupon bucket edges + "geography is
not a stratum axis" (V.B, T2/Q2); equity-as-static-original-LTV /
no-CLTV-dynamics / no-HPA-feed design boundary (V.C, Q1/Q9); in-sample
triangulation reframing of Path A's rate-gap coefficient + Fannie sign
replication with unit-comparability caveats (V.C, M2/Q5); functional-form
immateriality clause in the III.D accounting-bases paragraph (M3);
one-sided Ginnie bound note (V.C, Q4); tab:crosswalk — basis-and-inputs
crosswalk for every headline quantity, end of app:ledger, with
tab:headline's caption pointing to it (C2; ABM basis "shared layer,
native" verified against the fig. 5 caption before printing). Run-driven
batch: subgroup-marginals sentence extending the fourth qualification
(V.D); the corrected non-stationary-baseline passage (V.D — replaces the
falsified cancellation draft); fonseca second-anchor sentence (V.C);
tab:discount +2 rows and the 25–150bp prose span (III.C); servicer-mix
sentence (VII.F); grouped-calibration paragraph (app:theil, placed per
the run agent's direction caution — cell-panel CPR object, not the V.B
dollar split); 2015–16 isolation clause (V.C). DTI sentence (VII.C)
executed (gate #49).

### 28.3 Gates, editions, letter

Liveness gates 47 → 55 executed (#48–#55 in the round-16/17
artifact-vs-tex pattern: in-run gates PASS + exactly-one run citation +
printed literals derived from the artifact), suite ALL PASS. references.bib
unchanged at 59 (no new sources needed; fonseca2024 and all round-18
citations already present). PDF rebuilt (tectonic, 84pp, zero undefined
references); md/txt editions regenerated (19 tables). Letter placeholders
filled with executed values in revision_roadmap_round18.md — eight runs
total (the seven main runs plus the E3 cohort-timing diagnostic added on
author approval; no blocks remain pending). Commits local — push awaits
Eugene.

## 29. Round-19 partial: third-reviewer clarity/citation pass (2026-07-17)

Source: an additional referee note (clarity/presentation + missing-related-work
bins) supplied in-session. The coverage assessment found most points already
addressed at HEAD — two suggested citations were already cited (ferreira2010
L80 rate/equity mobility lock-in; defusco2020 L86 refinancing frictions), and
the precision-discipline concern (the $[+9.17,+9.23]$ sampling CI ``gives false
certainty'') is already answered by the explicit subordination of that CI to
the calibration box at intro L43 and Path B L479. The author directed
execution of the three genuinely-additive items only (``execute''); the
presentation/foregrounding asks were left as an open style call.

Three edits (backup .bak-round18 covers round 18+19; no separate .bak taken):

- **QE/QT balance-sheet-supply transmission literature** (reviewer's one real
  citation gap; the strand at L96 previously carried only micro
  refinancing-channel cites — berger2021/eichenbaum2022/beraja2019/dimaggio2020).
  Added two web-verified references and one situating sentence at L96:
  `krishnamurthy2011` (Brookings Papers on Economic Activity 2011(2):215--287,
  NBER WP 17555; documents QE's several channels incl. an agency-MBS prepayment
  channel) and `vayanos2021` (Econometrica 89(1):77--112; preferred-habitat
  foundation for why held-asset supply moves the term structure). Both verified
  via WebSearch before insertion; DOIs omitted to match the bib's zero-DOI house
  style (0/59 prior entries carry a doi field). New sentence frames the lock-in
  friction as an input to the balance-sheet-supply channel, not a separate
  phenomenon. references.bib 59 -> 61.
- **Preprint status made explicit** (reviewer: future-dated 2025/2026 sources
  need explicit status): peng2026 and lesniewski2026 `howpublished` changed to
  ``Preprint, arXiv:...''; berger2026 already carried ``Working paper, SSRN''.
  The other future-dated entries (liebersohn2024 JFE 2025, perotti2024 JCAM
  2026) are published journal articles, left as-is.
- **Round-18 E4 regime-split folded into the consolidated uncertainty exhibit**
  (reviewer: magnitude insufficiently pinned down): tab:uncertainty's lock-in
  marginal ``Calibration range'' cell extended with ``regime-split baseline
  break $+5.0$ to $+12.1$'' alongside the box ($+2.1$ to $+13.2$), floor form
  ($+11.2$), and cyclical floor ($+7.1$ to $+9.4$) — putting the
  baseline-conditionality dimension into the one table a reader consults for how
  pinned the magnitude is. The §V.D non-cancellation passage (round 18) already
  states it in prose; this surfaces it in the summary table.

Liveness suite unchanged at 55 gates, ALL PASS (gate #50's regime-split literals
now appear in both §V.D and tab:uncertainty; the `in tex` presence checks are
unaffected). PDF rebuilt (tectonic, 84pp, 0 undefined references; both new
\cite resolve into the bibliography); md/txt editions regenerated (still 19
tables). Response-letter blocks (L2, future-dated status, precision/magnitude)
updated in revision_roadmap_round18.md and response_to_referees_round18.tex.
Declined without action, with reasons of record: the ``front-load definitions /
reduce parenthetical density'' restructuring (left to author judgment given the
deliberately meaning-dense house style); ``foreground non-binding-cap logic /
Fed-benchmark justification / ABM-hazard reconciliation earlier'' (all already
present — L169 non-binding-cap + Fed-projection justification; L51/L270/L791 +
cross-design 59.3% reconciliation — the asks are prominence tweaks, not missing
content). Paper-dir files on disk only (gitignored). Commits: TECHNICAL.md this
section, local-unpushed.

## 30. Panel revision (2026-07-18): out-of-window involuntary-turnover floor anchor

Source: the blind cold-panel referee report on the v16 draft (`paper/v16/referee_panel_v16.md`), parsed into the AE Revision Plan whose applied edits are logged in `paper/v16/panel_revision_applied.md` (branch `panel-revision-2026-07-18`). This section documents the one data run behind that revision — AE Revision-Plan **item 2**, "calibrate the involuntary floor out-of-window," the operator-marked GO item and the empirical response to the panel's sharpest new identification objection (R1-Obj2, echoed by R2-Obj1 and R3-Obj3): that the $\beta_1=0$ null's dominant level-setter, the 4\% involuntary-turnover floor, is measured in-window on the very locked-in cohorts whose behavior the marginal decomposes, so a floor itself suppressed by lock-in would understate baseline turnover and inflate the marginal. Author go-ahead of record: "write it up + integrate" (2026-07-18). NOTE: on this branch the LaTeX master is gitignored (edits are on the working file `paper/v16/revised_paper_v16.tex`, revertable via `revised_paper_v16.tex.bak-prePanelrev`), so §30.2 below is not a tracked diff.

### 30.1 Run

- `hazard/out_of_window_floor.py` (AE item 2 / R1-Obj2, R2-Obj1, R3-Obj3; gate #56): pre-committed spec and acceptance gate fixed in the script header before its runs, the ex-ante convention Appendix~A records. Definitions identical to the paper: rate gap = coupon − MORTGAGE30US (FRED monthly mean); exposure-weighted CPR = 1−(1−ΣprepaidUPB/ΣexposureUPB)^12; OTM = gap≤0; seasoning cut mean_loan_age≥12.
  - **Method validation (in-window).** The identical procedure on the deeply out-of-the-money 2023–24 discount cohorts (gap≤−0.02) reproduces the production floor: 3.84% (age≥12) / 3.91% (age≥24). The measurement is sound where it is used.
  - **Out-of-window primary.** Applied to 2017–2019 discount-cohort turnover (gap≤0, age≥12), before both the QT window and the 2020–21 refi wave, it recovers 6.065% (5.07–5.19% stripping shallow-OTM at gap≤−0.0025/−0.005; 5.1–6.1% across the OTM grid). Year-split (gate diagnostic, this round): 2018 (rising-rate, market 4.03→4.87%, mean gap −1.25%) 5.33% (n=155); 2019 (falling-rate refi year, 4.46→3.60%, mean gap −0.88%, the bulk of the sample) 6.91% (n=373); 2017 contributes nothing (all gap≤0 cells fail the age≥12 seasoning cut, panel begins 2017-01). The reading is **upper-leaning**: the episode drove rates only to 4.87%, so almost no deeply-OTM out-of-window cohorts exist (109 cohort-months at gap≤−0.02, $0.51B ≈ 0.0035% of the $14.76T window, on anomalous 2.0–2.5% coupons), and residual voluntary prepayment cannot be stripped as in-window; even so, the cleaner rising-rate 2018 leg alone exceeds 4%. The out-of-window reading also **rises with seasoning** (6.065% at age≥12 → 10.995% at age≥24, n=95; 8.92% at the deeper gap≤−0.005 age≥24 cut), whereas the in-window validation is flat across the same cuts (3.84% → 3.91%). A genuine involuntary floor is age-invariant, so the out-of-window age-rise is itself the signature of voluntary refinancing the episode cannot strip — the ~11% age≥24 figure is not a floor candidate and is excluded on that basis, not hidden; the pre-committed spec anchors on the age≥12 primary.
  - **Pre-committed gate verdict: DOES_NOT_CORROBORATE** (F=6.065% outside both the [3.5, 4.5] corroboration band and the [3.0, 5.0] consistency band). Per the header's pre-registered branch, the in-window concession stands; the floor is disclosed as window-specific rather than a period-invariant involuntary rate.
  - **Identification reading.** The result does not refute R1-Obj2's premise — the off-window floor is if anything *higher* (5–6%) than the in-window 4%, consistent with lock-in suppressing baseline turnover — but it bounds the consequence. Because the lock-in marginal decreases in the floor (`tab:floorband`: +9.2 at 4%, +2.1 to +2.4 at 6%), a higher anchor **shrinks** the identified contribution rather than reversing it; at the 6% out-of-window reading the marginal is +2.1 to +2.4 points, the box's bottom row, still positive. The lock-in sign survives a floor measured off the locked-in population; its magnitude sits toward the low edge of the pre-committed box, consistent with the abstract's "sign and a bounded range, not a pinned magnitude."
  - Complementary to §24.1's within-window cyclical-floor variant (W2). **Corrected 2026-07-19 (see §24.1a): the characterization that stood here was wrong on both of its halves, and both halves were load-bearing.** It read that W2 "sweeps the floor's *shape* with its window-mean pinned at 4% and so, by construction, detects cyclicality but not level bias." Neither clause holds. (i) The window mean is pinned at 4% only where the floor's ≥0 clip does not bind, and it binds in both |κ|=0.5 cells — realized means 4.000519% at κ=−0.5 and 4.082786% at κ=+0.5 (convexity-matched flat 4.097653% at κ=+0.5) — and the κ=+0.5 cell is the one that sets the grid's low end (+7.094679 pp; κ=−0.5 sits mid-grid at +8.902049 pp, fourth lowest of seven), so the invariant failed in the cell that mattered most. (ii) The grid does not predominantly detect cyclicality: 84.96% of its range span survives scrambling the time order (72 permutations spanning +7.198683 to +9.123154 pp against the committed +7.094679 to +9.359821 pp), and 98.03% of the span vanishes under FLOOR_MODE='additive' (+11.220844 to +11.265427 pp, span 0.044583 pp). What W2 mostly measures is within-run floor DISPERSION under the hard maximum, not co-movement with the rate cycle. A genuine cyclicality component does survive — monotone in |κ| and sign-consistent, order components +5.289/+4.766/+2.691 B at κ=−0.5/−0.25/−0.1 and −1.420/−1.751/−2.526 B at +0.1/+0.25/+0.5 — but it is capped at $5.29B in any cell. The **complementarity claim itself stands**, restated on correct grounds: this run interrogates the floor *level's provenance* holding the shape constant, W2 varies the floor within the window, and neither subsumes the other. What W2 cannot be cited for is a clean cyclicality-versus-level separation.
  - Artifacts (on branch): `hazard/out_of_window_floor.py`, `hazard/data/out_of_window_floor_results.json`.

### 30.2 Manuscript edits (.tex gitignored on this branch; revert via `.bak-prePanelrev`)

- **§VII.I floor box (`sec:robustness-floor`):** new paragraph — the cited out-of-window provenance anchor, framed as the *third* pre-committed floor check alongside the level sweep (the calibration box) and the competing-risks form test. Carries the single `run \texttt{out\_of\_window\_floor}` citation and the gated literals (in-window 3.8–3.9%, out-of-window 6.1% / 5.1–6.1%, the 2018/2019 legs, the +2.1 to +2.4 direction).
- **§VIII.A limitations (`sec:limitations`):** the pre-existing uncited "≈5–6%" parenthetical (panel edit E) tightened to a cited cross-ref to §VII.I; loose literals removed so the result is single-sited. The "no untouched evaluation months" global disclosure is untouched.
- **Appendix A run ledger:** the `out_of_window_floor` row was already present (added with panel edit E); its cross-ref repointed from `sec:limitations` to `sec:robustness-floor`, where the run's detailed treatment now lives (§VIII.A only cross-refs there).

### 30.3 Gate

- **Liveness gate #56** (`out_of_window_floor` cross-check, in the round-16/17 artifact-vs-tex pattern): loads `out_of_window_floor_results.json`, asserts gate_verdict == DOES_NOT_CORROBORATE, headline 6.065%, in-window deep-OTM validation 3.84%, floor 4.0%; requires the tex to cite the run exactly once and to print the literals 6.1% / 3.8–3.9% / 5.1–6.1% / +2.1 to +2.4. PASSES.
- **Pre-existing suite state on this branch (NOT introduced here):** the gitignored working `.tex` on `panel-revision-2026-07-18` diverges from the committed round-19 gates — 21 round-17/18 runs are cited without the exact `run \texttt{NAME}` form the gates grep (their numeric literals are all present), plus one missing "supersede this tag" load-bearing sentence and one un-updated Danish "25--150 basis points" prose span. The suite therefore reports 23 pre-existing failures unrelated to this run; gate #56 itself passes. Flagged to Eugene as a separate branch-hygiene item (candidate cause: the `.bak-prePanelrev` reconstruction predates or diverges from the round-17/18 citation phrasing).
- **RESOLVED 2026-07-19 (re-synced the gates, not the `.tex`):** the three divergences above were all *deliberate* manuscript evolution, so `tools/liveness_gates.py` was updated to the current conventions rather than reverting the narrative. Round-19b moved the inline `run \texttt{NAME}` repository identifiers into the Appendix `tab:runindex`/`tab:crosswalk` tables (each run is still tagged exactly once as bare `\texttt{NAME}`); the 24 artifact-vs-tex cross-checks now count `\texttt{NAME}` with `>= 1` (`out_of_window_floor` is tagged both inline in §VII.I and in the index, so count 2). The `supersede this tag` EXACTLY-ONE check was re-pointed to the surviving reproduction-provenance sentence `against the fold-in specification's code` (Reproducibility conventions paragraph, which carries the spec-drift disclosure's operational content), and the Danish prose literal updated to `25--150 bp`. The value-literal (tex == frozen-artifact) checks are unchanged, so the anti-drift guarantee is intact — teeth verified: deleting a run's `\texttt{}` tag drives its count to 0 and the gate fails. **Suite now reports `ALL GATES PASS` (55/55).** The gate-file change is git-tracked but was UNCOMMITTED pending review.

Commits (local, push awaits Eugene): `hazard/out_of_window_floor.py` + `hazard/data/out_of_window_floor_results.json` (new, previously untracked), `TECHNICAL.md` (this section), `tools/liveness_gates.py` (gate #56 + OOWFLOOR_RESULTS constant). The `.tex` edits are on the working file only (gitignored).

## 31. Panel revision (2026-07-19/20): headline-calibration reconciliation and sign-statistic provenance

Two defects, both consequences of the same incomplete edit. When the lock-in marginal was demoted from the 4.0% in-window involuntary floor to the off-window floor of §30 / `oos_identification` (+$42.6B / +5.57pp at the clean mid 4.991%, band 4.695–5.334%), the demotion was propagated to the marginal and to nothing else. The recovery figures stayed at 4.0%.

### 31.1 The mixed calibration (`hazard/calibration_reconciliation.py`, gate #63)

**Basis mapping, established first because everything rests on it.** The paper's 97.9% ("benchmark-consistent accounting basis") and 88.7% (β₁=0 null on the same basis) are `share_pct` from `shared_layer_scoring_results.json`, produced by `fed_mbs_extension_risk.compute_metrics(use_hazard_microsim=True)`. Its 107.0%/97.8% counterparts are `standalone_share_pct` from `extension_risk.score_extension_risk`, the same numbers `floor_sweep_results.json` carries. The two bases differ by **one additive macro layer**: the shared scorer nets a constant $69.56220187263008B of curtailment off trapped liquidity over a common $764.7482532227002B cap benchmark, so

    trapped_shared = trapped_standalone − 69.56220187263008 ;  share_shared = trapped_shared / 764.7482532227002 × 100

equivalently a flat **−9.096092 pp** on the share basis. This is exact, not approximate: it reproduces the committed 97.9365273968041 and 88.73806762609433 from the committed 107.0326190295068 and 97.83415925879702 to machine precision (Gate A, bit-exact, run before anything new is computed). The layer is **path-invariant** — `curtailment_netted_b` and `empirical_trapped_b` are identical across all five committed estimators, which span 29.6 pp of standalone recovery from Path A's 121.5% to the null's 97.8% (Gate B) — so it does not depend on the CPR path and therefore does not depend on the floor generating it. That is what licenses carrying it to floors the shared layer was never run at. No new microsim and no new scorer: the standalone legs at every reported floor are already committed in `oos_identification_results.json`'s `instrument1_marginal_table`.

**Recovery on the shared basis, floor by floor** (central = p_q 6.5, null = β₁ 0):

| floor | central $B | central % | null $B | null % | marginal | miss vs benchmark |
|---|---|---|---|---|---|---|
| 4.000% (in-window, demoted) | 748.968 | 97.94% | 678.623 | 88.74% | +$70.345B / +9.198pp | **2.06 pp** |
| 4.695% (clean band low) | 716.226 | 93.66% | 664.445 | 86.88% | +$51.782B / +6.771pp | **6.34 pp** |
| 4.991% (**headline**) | 697.964 | 91.27% | 655.356 | 85.70% | +$42.608B / +5.572pp | **8.73 pp** |
| 5.334% (clean band high) | 674.283 | 88.17% | 641.661 | 83.90% | +$32.622B / +4.266pp | **11.83 pp** |

**The claim "recovers 97.9% … landing within 2.1% of the benchmark" is false at the calibration the paper headlines.** At the headline floor the central leg recovers **91.3%** (88.2–93.7% across the clean band) and the miss is **8.7 points** (6.3–11.8 across the band), not 2.1. The 97.9%/2.1-point pair belongs to the demoted in-window calibration and cannot be quoted alongside the $42.6B marginal. Roughly 15 occurrences are affected, including the abstract and conclusion.

**The 88.7-vs-88.5 convergence does not survive either.** The NY Fed's ex-ante (May 2022) projection implied 88.51496735220967% of the realized cap-shortfall under the pre-committed uniform-spread allocation and 75.5765152376043% under the settlement-aware allocation the manuscript itself calls the more faithful of the two. Against the null's shared-basis recovery:

| floor | null (shared) | vs uniform-spread 88.51% | vs settlement-aware 75.58% |
|---|---|---|---|
| 4.000% | 88.74% | **+0.22 pp** | +13.16 pp |
| 4.991% (headline) | **85.70%** | **−2.82 pp** | +10.12 pp |
| 4.695% / 5.334% | 86.88% / 83.90% | −1.63 / −4.61 pp | +11.31 / +8.33 pp |

The 0.2-point coincidence is doubly conditional: on the demoted floor *and* on the allocation. At the headline calibration it is 2.8 points under one allocation and 10.1 points under the other, and it cannot be reported as a convergence.

**Five collateral restatements**, all recomputed in the same artifact against their own sources: **S1** the seasonal-floor shape component $4.897B is 7.0% of the in-sample $70.345B but **11.49%** of the headline $42.608B; **S2** the $11.748B vintage bound is "about a sixth" of the in-sample marginal but **27.57%** — more than a quarter — of the headline; **S3** the "$+\$70$ billion of trapped roll-off" at §VII carries no in-sample qualifier, unlike every other occurrence; **S4** the "18.3-point real-book gap between the central leg's 107.0% and the β₁=0 null's 88.7%" **crosses accounting bases** (standalone minus shared) — the single-basis differential is +9.198pp in-window and +5.572pp at the headline; **S5** the vintage × coupon per-balance intensity range printed "0.8× to 1.5×" is actually **0.821 to 1.746** recomputed as `share_of_sum_pct / balance_share_pct` from `marginal_decomposition_results.json`; **S6** "the cells sum to within 1.0% of the paired-run total" is false as written — the artifact's own `residual_frac_of_total` is 0.010302, i.e. **1.03%**.

### 31.2 Sign-statistic provenance (`hazard/sign_forcing_stats.py`, gate #64)

§V rests the sign demotion (from identified content to a consistency check) on five figures that had been computed in session and written straight into the `.tex` with no committed artifact behind them — the one sourcing rule every other run in this repo is held to. They are now computed from `hazard/data/cohort_month_panel.parquet` and FRED `MORTGAGE30US`, and **all five reproduce at the manuscript's own printing precision**: exposure-weighted mean coupon **3.134%**, **97.40%** of exposure at or below 4.79%, **99.53%** at or below 5.09%, window-minimum 30-year rate **5.2311%** (August 2022), **40** covered window months.

Two things the module pins deliberately. First, **the coupon column is decimal-scaled** (0.0–0.075, a 14-point grid), not percent: a naive percent-threshold query returns a meaningless 100.00% of exposure and would silently "confirm" the claim, so the gate asserts both the decimal range and that the reported shares are not the degenerate 100%. Second, **coverage is disclosed, not repaired**: the panel ends 2025-09, two months short of the window's 2025-11 close, so these are shares of 40 of 42 months. The gap cannot overturn the reading — the book is closed at 2017–2021 originations, so no higher-coupon loan can enter and the out-of-the-money share can only hold or rise as the low-coupon cohorts season — but it is not measured, and the artifact says so. Supplementary: the exposure share at or below the *window minimum* itself, the economically binding cut, is 99.53%.

### 31.3 Gates

- **Gate #63** (`calibration_reconciliation`): binds the arithmetic, not prose, because the whole correction rests on one claim. The basis map must equal the shared-layer artifact's own fields (read from that artifact, not from this one's echo); the 4.0% anchors must reproduce bit-exactly with the gate performing the subtraction itself rather than trusting a stored zero; the layer must be path-invariant across all five estimators *and* the standalone spread it is invariant across must exceed 20 pp, or the claim is vacuous; every floor row must trace to the committed OOS table so no floor can be silently re-simulated in; the miss must re-derive as 100 minus the central share; the direction must hold (miss < 2.5 pp at 4.0%, > 8.0 pp at the headline); and the convergence must be reported on **both** allocations with the retirement verdict intact, so a later editor cannot reinstate the 0.2-point coincidence by editing one field. PASSES.
- **Gate #64** (`sign_forcing_stats`): binds the artifact to the manuscript literals by **deriving** each expected string from the artifact at the manuscript's printing precision, plus the decimal-scale assertion, the 40-of-42 coverage disclosure, and the requirement that the window minimum dominate both thresholds (if a data revision moved it below them the statistics would still compute but would no longer mean what §V says). PASSES.

Suite state after this round: **63 gates, ALL PASS**.

Artifacts (untracked/uncommitted, per this round's standing instruction): `hazard/calibration_reconciliation.py`, `hazard/data/calibration_reconciliation_results.json`, `hazard/sign_forcing_stats.py`, `hazard/data/sign_forcing_stats_results.json`, `tools/liveness_gates.py` (gates #63/#64 + five artifact-path constants), `TECHNICAL.md` (this section).

### 31.4 The manuscript edit (`revised_paper_v17.tex`)

§31.1's table is the source of record for every number below. The compute round left the `.tex` untouched; this round reconciled it.

**Decision: report both calibrations, headline the off-window one.** The alternative — headline the in-window 4.0% recovery and footnote the off-window figure — was rejected. The recovery level and the lock-in marginal are computed by the *same paired run at the same floor*, so a reader who sees "recovers 97.9%" next to "marginal +$42.6B" reasonably infers that the model recovering 97.9% is the model producing +$42.6B, and it is not: that model recovers 91.3%. Nothing in the prose could fix that inference while the two numbers sat at different floors, which is why the fix is structural rather than a hedge. The paper had *already* adopted the both-calibrations pattern for the marginal (+5.6 headline, +9.2 labelled in-sample); extending the same pattern to the level keeps one convention throughout, whereas headlining the level in-window and the marginal off-window would have institutionalized the mix. The 4.0% figures are retained everywhere, never deleted, and labelled *in-sample calibration point*: they are not wrong, they are the model-fit diagnostic at the floor the framework was assembled on.

**Discipline observed.** Only the central and null legs have committed off-window values. Path A (112.4%), the concave-gap variant (96.6%), the full-book (109.1%) and composed (100.0%) columns, the covariate-prior band (92.2–99.2%), the elasticity band, the Ginnie overlay, and the Danish legs were run only in-window and are **not** extrapolated; each is now explicitly labelled an in-sample-calibration quantity. `tab:bases` gains two off-window rows (central 100.4% standalone / 91.3% shared; null 94.8% / 85.7%) with `--` in the columns that were never run there.

**What was retracted, not reworded.** (i) "Lands within 2.1% of the benchmark" as an unqualified headline: the miss is 8.7 points at the headline floor, 6.3–11.8 across the band, and 2.1 points in-sample. (ii) The 88.7-vs-88.5 convergence, in both places it appeared: it needs the in-window floor *and* the uniform-spread allocation, and the gap ranges from −2.8 pp (headline floor vs uniform) to +13.2 pp (in-sample vs settlement-aware) across those two disclosed choices. The coarse claim that survives — both objects put the anticipated mechanical component in the large majority of the shortfall — is stated and relied on; the 0.2-point precision is not. Both retractions are recorded in the run ledger rather than silently overwritten.

**S1–S7.** S1 the $4.897B flat-floor bound is 7.0% of the in-sample marginal and 11.5% of the headline one, both now printed. S2 the $11.748B vintage bound is 27.6% of the headline marginal (a sixth only of the in-sample one). S3 the bare "+$70 billion of trapped roll-off" now carries both calibrations. S4 the 18.3-point real-book gap was a **basis error** — standalone central minus shared null — and the defect was in the artifact, not only the prose: `synthetic_companion_null.py`'s `real_book_reference` block hardcoded 107.0/88.7/18.3. It now derives both legs from one artifact on one basis (`floor_sweep_results.json` row 4.0), giving 107.0/97.8/9.2, and carries the off-window 5.6 from the OOS table. The synthetic differential (10.37 pp) therefore slightly *exceeds* its real-book counterpart rather than falling short, which the manuscript now says. S5 per-balance intensity 0.82×–1.75×, not 0.8×–1.5×. S6 the additivity residual is 1.03%, so "within 1.0%" was false as written; all three occurrences now say 1.03%. S7 the sign-forcing statistics were already numerically correct and gate #64 already bound them, but the manuscript cited no run; it now carries `\texttt{sign\_forcing\_stats}` and gate #64 requires that citation.

**Gate changes made in the same pass, per the never-loosen rule.** Gate #61's stored precedent moved from 18.3 to 9.2, so its derived literals follow automatically; the gate was additionally **strengthened** to cross-read both legs from `floor_sweep_results.json` (so a cross-basis difference cannot be reinstated), to re-derive the gap on the shared basis and require the same value (basis-invariance), to require the superseded 18.3 stay recorded as superseded and differ from the live value by more than 8 points, and to trace the off-window leg to the committed OOS table. Gate #64 gained the run-citation requirement. No check was relaxed.

**Verification.** 63 gates PASS, 267 pytest pass, PDF 99pp, 0 undefined references and 0 undefined citations. Nothing committed or pushed.

## 32. Panel revision (2026-07-20): matched-depth reconciliation of the floor demotion, and three forced claims relabelled

Two independent problems. §32.1–32.2 are a factual error and a missing decomposition in the off-window floor narrative (§VI.B / `sec:robustness-floor`). §32.3 applies, to three further claims, the same relabel-do-not-delete pattern already used twice in this repo for the sign demotion (§31.2) and the floor-cyclicality mislabel (§24.1a): keep the result, correct what it demonstrates, and say why the check could not have failed.

### 32.1 The depth error (`hazard/matched_depth_reconciliation.py`)

The manuscript asserted that the off-window 2017–2019 panel reaches no cohort at the two-point discount depth at which the in-window anchor is measured, and that "the off-window grid stops at half a point." **Both halves are false.** The 2018 leg's observed gap runs to **−0.02866**; the `gap<=-0.02` cell **exists** and holds **35 cohort-months** reading **3.440%** annual CPR. The grid stopped at −0.005 because `GAP_THRESHOLDS` was hardcoded to `(0, -0.0025, -0.005)` in the `oos_identification` script header — a grid choice, not a data limitation.

The true limitation is **exposure collapse**. Down the 2018 leg's depth ladder, the share of its `gap<=0` exposure retained runs:

| depth | 0 | −0.0025 | −0.005 | −0.0075 | −0.01 | −0.015 | −0.02 |
|---|---|---|---|---|---|---|---|
| exposure share | 100% | 83.68% | 72.87% | 35.87% | 11.34% | 3.87% | 0.02% |
| CPR | 5.334% | 4.991% | 4.695% | 4.722% | 4.869% | 4.342% | 3.440% |

The deep cell carries **$0.282B of $1,264.5B**. It is present and worthless. The run therefore fixes an **ex-ante support rule** in its header — a depth is admissible for a leg only if the leg retains **≥10%** of its `gap<=0` exposure there — and excludes the deep cell before any reading is taken. This distinction is load-bearing rather than pedantic: the hostile reading of the demotion is that it is a depth artifact, and the answer is not that the deep cell is missing but that it is noise.

### 32.2 The decomposition the paper never gave

Floor→marginal is taken from the committed `floor_sweep_results.json` by PCHIP, **not re-derived**; the mapping reproduces the committed grid to within **$0.69B** at every read inside it, and reads above 6.0% are refused rather than extrapolated. Step 1 parity-gates all 20 cells against `oos_identification_results.json`'s anchor grid (all pass, bit-exact).

Total move, in-window `gap<=-0.02` **3.972%** → off-window 2018 `gap<=-0.0025` **4.991%**: **−$28.312B / −3.702pp**, splitting

- **WINDOW** (depth held at −0.0025 on both sides): **−$20.874B / −2.729pp = 73.7%**
- **DEPTH** (within the in-window panel, −0.02 → −0.0025): **−$7.438B / −0.973pp = 26.3%**

Cross-checked at the deepest depth both panels support (`gap<=-0.01`): **66.9% window / 33.1% depth**. **Window dominates either way**, so the demotion is not primarily a depth artifact — but depth owns a real, previously unattributed **$7.4B**, and the consequence is that **at matched depth the correct in-sample comparison point is $63.5B, not $70.3B**. The paper narrates a $27.7B demotion; only ~$20.9B of it is the window.

**The reverse ordering is refused, not computed.** Window-first at matched deep depth would read the off-window leg at `gap<=-0.02`, where it holds 0.02% of exposure. `path_b_window_first` is reported (`admissible: false`) and **no Shapley average is formed** (`shapley_average_refused: true`). Note the reported-but-unused reverse path would have given a *positive* window component (+$8.21B) and a −$36.5B depth component — i.e. the hostile reading is exactly what the support rule excludes, which is why the rule is ex ante.

**A clean new robustness result.** Extending the 2018 ladder from 3 to **5** well-supported depths leaves the committed clean band **exactly [4.695%, 5.334%]** — the two new reads (**4.722%** at −0.0075, **4.869%** at −0.01) fall strictly inside it. Marginal band **$33.31B–$51.75B**, point **$42.58B**. The headline is better supported than the three-depth grid could show.

### 32.2a What the matched-depth grid does *not* rescue

The paper's rejection of the 2019 falling-rate leg compares 2019's `gap<=0` read (6.910%) against the retained 2018 `gap<=-0.0025` read (4.991%) — **a 1.919pp spread across different depths**, not a valid comparison as written. But matching depth does **not** make the legs converge either. Over the four depths where both legs clear the support rule the 2018-vs-2019 spread runs **1.576 / 0.491 / 2.112 / 0.857 pp** — non-monotone, and at −0.005 the matched-depth spread (2.112) **exceeds** the 1.919 the narrative rested on. So "the legs agree once depth is matched" would be a cherry-pick of one depth in four.

Two further pins. `pooled_2017_2019` **contains** both 2018 and 2019 (plus 2017), so it is **not a third independent leg**: there are **two**, and any "three legs agree" phrasing double-counts. (Grepped: no such phrasing was present in the `.tex`; the fact is now stated affirmatively so it cannot be introduced.) And the 2019 leg's exposure collapses from **$1,085B** at `gap<=0` to **$199B** by −0.005 and **$0.29B** by −0.015, so its deep reads are noise on the same grounds that disqualify the deep off-window cell.

**Verdict written into the paper:** the refi-contamination story is **unadjudicable below `gap<=0`, not refuted**. The only depth on solid exposure for both legs is `gap<=0`, where 2019 sits **1.576pp above** 2018 — directionally consistent with contamination, and consistent with the independent seasoning diagnostic. *The conclusion is defensible; the argument as stated was not.* The paper now states the weaker one.

### 32.3 Three forced claims relabelled

**B1 — the Danish positivity is an identity.** `hazard/danish_us_intercept.py` defines the Danish moving leg as *the production U.S. hazard evaluated at a zero rate gap*; its own docstring (line 37) concedes the zero-gap intercept exceeds the locked-in U.S. hazard wherever the gap is negative. The U.S. book carries a negative gap in essentially every cell (99.53% of exposure below the window-minimum market rate — §31.2), and the hazard is monotone in the gap. So the zero-gap leg **must** prepay faster, Danish trapped (**687.7795451639257B**) **must** come in below U.S. trapped (**748.9678825340305B**), and the gap (**+61.18833737010482B**) **must** be positive. `sweep_sign_robust: true` is forced for the same reason: additional refinance-in-place only adds Danish prepayment. Both are now labelled wiring checks.

What is *not* forced and is preserved: the **magnitude** (+$61.2B, 8.0% of benchmark), and the **Danish-level bracketing anchor of −$99.9B**, which imports Denmark's baseline mobility rather than only the payoff rule and **does flip the sign**. The edits **lead with the flip**.

Sites fixed: abstract, `tab:headline` row (both of which a reader meets before the §VII.C disclosure), the §I framing paragraph, §VII.C body, `tab:danish` note d, the `fig:gapsweep` caption, the §VII.C closing paragraph, the conclusion, and the ledger's superseded-figures entry. Also corrected: the Danish gap was repeatedly called **equal in size** to the lock-in marginal. That holds only against the **demoted** in-sample $70.3B. Against the **$42.6B headline** the Danish gap is **~44% larger**, and every unscoped occurrence now says so.

**B2 — the Fannie envelope is too wide to constrain.** Pre-committed envelope **[2.113539257759882, 13.17046899604594] pp** — an **11.06pp** window around a Freddie point of **+9.20pp**, admitting a replication **77% below** or **43% above**. Fannie landed at **8.682485610390856 pp** ($66.39915704177633B), `in_envelope: true`, on **17,606,999** staged loans. The width is now stated at every site so a reader can price the evidence. **Critical distinction preserved:** the *envelope gate* is uninformative; the *agreement* is not — 17.6M loans landing **0.52pp** from the Freddie point is genuinely reassuring. The replication is kept and is **not** described as failed; the paper simply stops leaning on the PASS.

**B3 — "stable in sign across both hazard specifications."** Only Path A *estimates* the rate-gap coefficient; Path B *imports* it from `liebersohn2024` as a signed elasticity band, so it has no freedom to take the other sign. The agreement is an **orientation/wiring check** on unit and sign conventions between the two paths (it would catch a transposed sign, and it passes), not corroboration that the par-payoff penalty does real work. Restated on that footing rather than dropped, per the standing preference for explicit-why-it-cannot-fail over deletion; the evidential load moves to the estimated Path A coefficient and the external literature taken separately.

### 32.4 Gates

No new gate. `matched_depth_reconciliation` carries its own hard-wiring self-checks (anchor-grid parity across all 20 cells, path-A components summing to the total, mapping reproducing the committed grid, mapping fidelity under $1B — all true) and four soft interpretive checks recorded honestly, two of which are **false by design and reported as such**: `off_window_reaches_gap_le_0.02_with_support: false` and `leg_spread_converges_monotonically_with_depth: false`. The manuscript's new prose states both.

Existing gates that touched edited prose were reconciled **by updating the derived format strings, never by loosening a check or reverting prose** (see §32.5).

### 32.5 Verification

Protected content grepped and confirmed byte-identical after the pass: the +$42.6B/+5.57pp headline, the $4.695–5.334% OOS band and its $32.6–51.8B range, the levels-only timing concession, the sign demotion, the floor-dispersion relabel, the `floor_cyclical` corrections, the §31 calibration reconciliation, and the tex:476/716/430 null corrections.

Artifacts (untracked/uncommitted, per this round's standing instruction): `hazard/matched_depth_reconciliation.py`, `hazard/data/matched_depth_reconciliation_results.json`, `paper/v17/revised_paper_v17.tex`, `TECHNICAL.md` (this section).

## Appendix A — File Map

```
Lock-in-Effect/
├── README.md                 # Quick start and index
├── TECHNICAL.md              # this document
├── requirements.txt
├── common/                   # Shared config, imported by abm/ and hazard/
│   ├── qt_window.py           # QT window single source of truth (§15 Fix 4)
│   ├── fred_key.py            # FRED key from env/.env (§15, 3.4)
│   └── berger_calibration.py  # Danish two-channel elasticities (§20)
├── tests/                     # Cross-framework regression tests
│   ├── test_qt_window.py      # 7 tests incl. post-QT-drift regression
│   ├── test_units_conventions.py  # §15 Fix 3 units bugs + β₁(0)=0 (§21)
│   ├── test_bootstrap_se.py       # stratum bootstrap resampler (§21)
│   └── test_loan_sample_cache.py  # cache hits never touch download path
├── runs/                      # Frozen baseline snapshots (§15 Step 0)
│   └── pre-fix-2026-07/       # pre-robustness-fix manifest + builder script
├── abm/                      # Agent-based pipeline (frozen archive)
│   ├── README.md             # Granular ABM history: Appendix B of this file
│   ├── abm_lockin_simulation.py   # --population={synthetic,freddie} (§15 Fix 1)
│   ├── fed_mbs_extension_risk.py   # + use_hazard_microsim bridge; term-aware cohorts (§15 Fix 2)
│   ├── freddie_population.py       # structural-covariate loader (§15 Fix 1)
│   ├── cross_design_test.py        # both calibration variants + report (§15 Fix 1)
│   ├── hybrid_pipeline.py          # shared accounting + hazard micro-foundation (§17.1)
│   ├── refi_sweep.py               # refi-in-place gap sensitivity sweep (§20.1)
│   ├── data/runs/                  # tagged freeze_run.py manifests (+ fold-in MC artifacts, §21)
│   └── sensitivity/robustness/monte_carlo scripts
└── hazard/                   # Reduced-form hazard framework
    ├── README.md             # Pipeline specs and equations
    ├── config.py              # re-exports QT window from common/ (§15 Fix 4)
    ├── ingest.py, hazard_fit.py, stratum.py, simulate.py   # Path A
    ├── loan_sample.py, microsim_engine.py, ...   # Path B; --band runs Rothstein sensitivity (§15 Fix 3)
    ├── literature_hazard.py, rate_gap.py   # β₁ + regime-specific rate gap (units fixed, §15 Fix 3)
    ├── permutation_test.py    # marginal-preserving joint-structure null test (§16)
    ├── no_lockin_null.py      # β₁=0 mechanical null — lock-in marginal $70.3B (§12)
    ├── bootstrap_se.py        # stratum block-bootstrap SEs for Path A (§21)
    └── data/                   # Parquet, JSON, PNG outputs
```

---

## Appendix B — ABM-Era Granular Archaeology

> Absorbed from the former `abm/TECHNICAL.md` on 2026-07-11 (full text in git
> history). This is the **pre-robustness-program record**: figures here (e.g.
> $101.2B / 13.2% share, ~47% Danish CPR, $672.9B-era comparisons) are
> superseded — current production is **$84.5B / 11.1%** with Danish CPR
> **3.4%** under the Berger recalibration (§12, §15–§20). §§3, 5–8 summarize
> this material; what follows is the granular detail those sections do not
> repeat.

### B.1 Benchmark accounting detail

**Why WSHOMCB diffs were wrong:** per the Fed's Financial Accounting Manual,
SOMA holdings (including `WSHOMCB`) are booked at **amortized cost on a
settlement-date basis** — not face value. The Fed's MBS were largely bought
at a premium, so `WSHOMCB` declines every period from premium amortization
on top of, and independent of, actual principal paydown. The NY Fed SOMA
current-face-value series moves only when principal is actually paid down.
Both series remain settlement-date accounting through the TBA forward market
(allocation only 2 business days before settlement, per the SIFMA schedule),
so switching to SOMA removes the amortized-cost confound but **not**
TBA-settlement lag.

**Scheduled amortization:** `scheduled_amortization_smm()` is calibrated to
the same mortgage assumptions as the ABM. At the time of the fix it accounted
for **$242.1B** of QT-window roll-off (SMM ≈ 0.213%/month ≈ 2.55%
annualized); the frozen `run-2026-07-04` records $224.1B (≈ 2.68% ann.) after
subsequent corrections.

**Empirical CPR back-out:** inverts the simulated-roll-off relationship —
`empirical_CPR = (|actual_rolloff| / holdings − sched_SMM) × 12`, clipped at
zero. Frozen ranges: empirical 0.00–14.02% (mean **5.53%**), ABM U.S.
7.55–21.72% (mean **11.98%**), Danish 36.26–51.26% (mean 47.21%; wedge mean
35.24pp). All headline CPR means must use `qt_active_frame()` (42 months);
`index >= QT_START` alone pulls in post-QT months and drifts means (U.S.
12.32%, empirical 5.45%). Multi-cohort runs use cohort-weighted
`Scheduled_Amort_SMM` so the back-out is apples-to-apples.

### B.2 Fit diagnostics (frozen `run-2026-07-04`)

| | R² | RMSE | MAE | r |
|---|---|---|---|---|
| Raw | −6.443 | 7.73pp | 6.58pp | −0.316 |
| Smoothed (3-mo) | −14.464 | 7.14pp | 6.41pp | −0.397 |

Smoothing makes fit *worse* — the "settlement noise" explanation was tested
directly and rejected. Full cross-correlation profile (N=42): −3: +0.192,
−2: −0.209, −1: −0.140, **0: −0.316**, +1: −0.206, +2: −0.033, +3: +0.103.
Temporal holdout (split at 2024-01-01): in-sample N=19, R² −10.990, RMSE
8.86pp, share −11.1%; out-of-sample N=23, R² −4.222, RMSE 6.66pp, share
32.5% — the model over-predicts roll-off early in QT and under-predicts late.

### B.3 Validation-suite detail

- **Sensitivity** (125 combinations: `BASE_FRICTION` 5–9%,
  `SEARCH_PENALTY_CAP` 0–400bp, `SENTIMENT_PENALTY_CAP` 0–300bp). Bug found:
  `aggregate_trapped()` compared the ABM to **itself** (trivially 100% share);
  fixed with an independent `empirical_trapped()` anchor. Post-fix ranges:
  trapped −$265.1B–$265.5B, share −34.7%–34.7%, R² −16.6 to −3.5, RMSE
  6.01–11.88pp.
- **Robustness**: Panel B (data source) — SOMA $764.7B vs WSHOMCB $763.7B
  (0.1% apart). Panel C (18 cap-schedule scenarios: ramp 2/3/4 months, cap
  $30/$35B, end Jun/Sep/Dec 2025) — empirical $479.6–782.2B, share
  −24.6%–15.2%.
- **Monte Carlo** (historical; superseded by the fold-in-spec MC, §22.1):
  50 seeds, population and CPR surface rebuilt per draw — mean $113.5B, std
  $24.8B, CI [$106.6B, $120.4B]. An earlier fixed-CSV-surface run (std ≈ $0)
  was a bug: surfaces must be rebuilt per seed.

### B.4 Behavioral extensions — parameters and outcome

Sources: DTI 43% front-end (CFPB QM/ATR, 12 CFR 1026.43(e)(2)(vi); the
regulatory threshold is back-end — the gate is QM-*inspired*); loss aversion
2.25× (Kahneman–Tversky); wait-and-see 150bp/20% (stated assumptions; a fixed
per-agent patience draw keeps the surface deterministic). The velocity axis
(−1.0% to +3.5%, 0.5% steps) turned the surface 3D; vectorization
(`_precompute_arrays` + `_cpr_vec`) gave a ~120× speedup (~6.7 min → ~3 s per
surface; 50-seed MC ~5.5 h → ~46 s).

| Metric | Rational only | Behavioral |
|---|---|---|
| U.S. trapped | $544.0B (80.8%) | **$419.6B (62.3%)** |
| Danish trapped | −$359.7B | −$764.2B |
| Institutional gap | $903.8B | $1,183.8B |
| U.S. CPR mean | 6.62% | 7.92% |
| CPR R² (raw) | −0.590 | −1.586 |

Why the wrong direction: maintaining the 4–5% involuntary floor under a
steeper penalty forced `MOBILITY_DESIRE_SCALE` from ~12,500 to ~36,086,
raising CPR at **all** rate levels — including 5–7% where most QT data lives.
(Historical $672.9B-era figures.)

### B.5 Curtailment channel

Pre-registered: curtailment is additive-only and near-zero in stress months
(over-prediction bias vs `DSPIC96` YoY growth: r = −0.487), so adding it
should **worsen** the match by $60–90B. Result: trapped fell **$75.0B**
($419.6B → $344.6B, 51.2% share; curtailment contribution $74.9B); CPR-path
diagnostics unchanged. Implementation: macro-layer only —
`CURTAILMENT_CPR_HEALTHY = 0.012`, scaled continuously from 0% at −2% income
growth to full at +4%.

### B.6 Multi-vintage coupon cohorts

CUSIP-level parse of `securityDescription` (30-year pass; origin =
maturity − 360 months; `min_share = 2%` folding). Verified cohort table
(as-of 2026-06-24, $1,769.6B of 30yr face): 1.50% $53.6B / 3.0%; **2.00%
$703.1B / 39.7%**; 2.50% $518.4B / 29.3%; 3.00% $209.4B / 11.8%; 3.50%
$143.0B / 8.1%; 4.00% $90.6B / 5.1%; 4.50%+ $51.5B / 2.9%. Architecture:
`attach_cohort()` decouples household economics from mortgage terms;
per-cohort 3D surfaces (23,660 rows); weighted U.S. roll-off sum; independent
per-cohort Danish declining-balance loops. Result: **hypothesis falsified** —
trapped fell $87.0B (51.2% → 38.3%, historical) and weighted CPR rose to
8.67%; slower low-coupon amortization is dominated by younger seasoning on
the dominant buckets and per-coupon surface effects.

### B.7 Vintage burnout (survivor selection) — pre-registered, failed

| Configuration | U.S. trapped | Share | QT-window CPR |
|---|---|---|---|
| Surface baseline | $117.7B | 15.4% | 8.41% |
| Survivor burnout | **$1,123.9B** | **147.0%** | ~0.00% |

Pandemic-era cohorts deplete their mobile mass in the 2020–21 low-rate
window; survivors are exclusively never-movers — an absorbing state
incompatible with a real pool that retains involuntary turnover and ongoing
origination. Production: `use_burnout=False`; code retained.

### B.8 Settlement-lag kernel — pre-registered, null

Mass-conserving `[0.10, 0.60, 0.30]` convolution over lags 0/1/2 (documented
UMBS ~55-day / GNMA II ~50-day remittance delays, not tuned):

| Configuration | U.S. trapped | Share | Peak cross-corr |
|---|---|---|---|
| Surface only | $117.7B | 15.4% | +0.192 at lag −3 |
| Surface + kernel | $101.2B | 13.2% | **+0.192 at lag −3 (unchanged)** |

Timing alignment did not improve; the kernel is kept in production as a
documented null with modest aggregate effect.

### B.9 Frozen reference: `run-2026-07-04`

Headline rows (full table: `abm/data/runs/run-2026-07-04/manifest.json`;
**stale** — see §12 for current): empirical $764.7B; ABM U.S. trapped $101.2B
(13.2%; surface-only $117.7B / 15.4%); Danish −$829.1B (path $2,535B →
$428B); institutional gap $930.3B; SOMA 30yr WAC 2.55% (7 buckets); reference
cohort 2.00% at 39.7% weight; dynamic friction 8.23–9.96% (mean 8.95%).

---

*Last updated: July 2026. Hazard spec v3: stratum FE (295 pools), burnout sign fixed (−0.13). Post robustness-fix program (§15): Path B at 107.0% trapped (band 105.9%–108.2%) after the β₁ units fix; ABM at 11.1% after the native 15-year gate (§19); cross-design test with real Freddie covariates recovers 59.3% (recalibrated) / 20.9% (frozen). Follow-on analyses: permutation test (§16, n=999, exact p=0.001) — Path B's recovery is a marginal-distribution result, moved only 0.27% ($2.2B) by scrambling joint structure, interaction-dominated across axes with the CPR-path signal localized to origination-time; Path A's fitted coefficients are far more structure-dependent (β can flip sign). Cross-foundation (§17): the institutional gap collapses $925.5B→$61.2B under a shared accounting layer; full-book SOMA weighting lifts Path B to 109.1%, Path A to 126.1%. Symmetric companion (§18): Path B recovers 106.0% on a fully synthetic population (zero Freddie data) — the hazard survival structure recovers the benchmark independent of data source, while the ABM needs real covariates to reach 59.3%. Berger recalibration (§20): importing estimated Danish elasticities (3.2% flat moving + tax-attenuated refi, ≈0 under U.S. taxes) collapses the institutional gap from +$925.5B to −$99.9B (Path B hybrid) — the large gap was an artifact of extrapolating a U.S.-calibrated mobility function to a Danish rate gap. Sweeping the refi channel (§20.1) shows the gap's *magnitude* stays small across [0, 18%] but its *sign* is not robust in Path B under that anchor (breakeven at just 1.4% refi vs 12.6% for the ABM). Referee round 13 (§23) then established that §20's 3.2% import is Denmark's descriptive LEVEL (rule+country bundle; Danish CPR below the 4% involuntary floor) and restated production to the U.S.-intercept anchor — Berger's flatness fact at the U.S. zero-gap hazard — which reproduces the §17 hybrid leg for leg: gap **+$61.2B (8.0%)**, signed positive at every refi sweep point, the counterfactual image of the +9.2pp lock-in marginal; the dk_level rows are retained as a labeled bracketing case. Round 13 also added the floor functional-form test (additive marginal +11.25pp at 4%, nearly floor-invariant — the floor sweep's failed ±2pp gate was max-form censoring, not elasticity instability) and the Path B stratified loan-level bootstrap (200 reps: central 95% [106.96, 107.10]%, paired marginal [+9.17, +9.23]pp — sampling noise negligible; uncertainty is calibration). July 2026 verification round (§21): Path A coefficients now carry stratum-bootstrap CIs (rate-gap sign-stable in 99.5% of replications; burnout/friction not distinguishable from zero), the fold-in-spec Monte Carlo (mean $103.7B; seed 42 = $90.98B exactly) and the β₁=0 no-lock-in null ($748.2B / 97.8%) are committed artifacts, and manuscript v14 aligns the paper with all of the above. Referee rounds 2–12 (§22) took the manuscript to v15r5 on the shared accounting basis; on 2026-07-11 the former `abm/TECHNICAL.md` and `REVISION_VERIFICATION.md` were consolidated into this file (Appendix B, §22).*
