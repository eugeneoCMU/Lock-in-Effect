# Technical Narrative — Lock-In Effect Project

This document is the **repository-level** technical history: what was built, what broke, what was fixed, what was falsified, and why the codebase now has two frameworks (`abm/` and `hazard/`). It is written for a reader who wants the full causal chain from the original **$972.3B** headline to the current validated **$764.7B** empirical benchmark, the **11.9%** ABM share explained (post 15-year MBS fold-in), and the newer reduced-form hazard pipelines. A July 2026 robustness-fix program (§15) revised three of the four headline figures — see that section for what changed and why.

For module-level runbooks, see [README.md](README.md). For granular ABM bug archaeology (line-level citations, section-by-section), see [abm/TECHNICAL.md](abm/TECHNICAL.md). For hazard pipeline specs, see [hazard/README.md](hazard/README.md).

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

---

## 1. Economic Question

When the Federal Reserve began **Quantitative Tightening (QT)** in June 2022, it targeted a phased reduction in its Mortgage-Backed Securities (MBS) holdings. The plan assumed mortgages would prepay at something close to historical turnover rates. Instead, the post-2022 rate shock created a **lock-in effect**: households with below-market fixed coupons faced punitive par-payoff math if they moved or refinanced, crushing voluntary prepayment.

The empirical signature is **extension risk** — actual MBS roll-off consistently fell short of the QT cap, trapping liquidity on the Fed's balance sheet far longer than planned.

This project quantifies that shortfall and asks two structural questions:

1. **How much liquidity was trapped, and is the measurement defensible?**
2. **How much of the shortfall is explained by household lock-in under U.S. mortgage rules, versus other mechanisms (pool composition, servicer pipelines, income stress, institutional design)?**

The **Danish counterfactual** isolates institutional design: Danish borrowers can buy back mortgage debt at **market price** rather than par, neutralizing lock-in when rates rise. Contrasting U.S. and Danish simulated roll-off paths separates *rate dynamics* from *contract design*.

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

The original pipeline reported **$972.3B** in cumulative trapped liquidity. Independent reasoning (Fed ~$600B actual redemptions vs. cap-implied shortfall) suggested the true figure was closer to **$800–870B**. Investigation found **three compounding errors**:

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

1. **DTI hard wall** — 43% front-end payment/income (CFPB QM/ATR)
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
| **1** | **-$1,132B** | $1,676B | ~47% Danish CPR (current surface) applied to static U.S. balance |
| **2 (current)** | **-$829.1B** | **$930.3B** | Dynamic declining-balance simulation per cohort |

**Why Stage 0 happened:** Danish CPR is always high under market-value buyback (**36–51%** on the current production surface, mean **47.2%** over the 42-month active QT window; the older rational-only calibration was ~21–27%). Simulated roll-off consistently **exceeded** the QT cap, producing negative extension deltas every month. One-sided clipping turned all negatives to zero.

**Why Stage 2 is correct:** Danish balance is simulated forward month-by-month from QT-start holdings, applying Danish CPR + scheduled amort + curtailment to the *already-shrunk* balance each month.

**Interpretation caveat:** Danish friction is still U.S.-calibrated. The $930.3B institutional gap is an **upper bound** under U.S.-style transaction costs.

---

## 8. Why the Residual Persisted

*(Figures below are as of the pre-15yr-foldin, synthetic-population ABM. Current production figures are $91.0B / 11.9% — see [§12](#12-current-headline-numbers) and [§15](#15-robustness-fix-program-july-2026), which also reports that swapping in real Freddie structural covariates recovers 59.3% under recalibration — a result that revisits the diagnosis below.)*

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

| Metric | Value |
|---|---|
| Trapped liquidity | **$915B (119.7%)** |
| β(rate_gap_bps) | +0.67 (OK, standardized) |
| β(burnout_orth) | **−0.13 (OK)** |
| β(friction) | −0.037 (OK) |
| CPR r (lag 0) | −0.444 |
| Holdout RMSE | ~38pp |

### Forward simulation

`simulate.py` drains cohort balances deterministically: `balance × hazard` each month. Fractional prepay settles **directly** to SOMA roll-off — **no settlement-lag convolution** in the hazard path (by design; see CPR timing in [hazard/README.md](hazard/README.md)).

### CPR timing and settlement lag

| Path | CPR r (lag 0) | Peak lag | Peak r |
|---|---|---|---|
| Literature microsim | +0.368 | **−3** | **+0.444** |
| Empirical cohort GLM (spec v3) | −0.444 | 0 | −0.444 |

**Literature peak lag −3** is the primary timing diagnostic: hazard CPR leads SOMA empirical CPR by ~3 months, consistent with the 45–90 day TBA settlement pipeline between Freddie loan-level prepay and NY Fed SOMA cash receipt.

The ABM tested a `[0.10, 0.60, 0.30]` settlement kernel and found it **null for timing** ([`abm/TECHNICAL.md` §21](abm/TECHNICAL.md)). The hazard path routes voluntary prepay directly to SOMA — lag −3 is **expected**, not a bug. Empirical cohort lag-0 negative r reflects contemporaneous alignment misspecification, not a failure to model settlement delay.

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
5. Prepay UPB routed through `route_through_pipeline()` (replaces ABM settlement kernel)

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

Replaces CPR surface interpolation with microsim paths. Disables ABM settlement-lag kernel (Markov routing already handles pipeline delay). Danish dynamic balance loop unchanged.

### Real-data results (Freddie 2017–2021 sample; post-β₁-units-fix, see §15)

| Metric | Value |
|---|---|
| Trapped liquidity | **$818.5B (107.0%)** — band $810B–$828B at P_q 5.5%–7.7% |
| CPR r (lag 0) | +0.190 |
| **Peak cross-corr** | **lag −3, r = +0.404** (stable across band) |
| Runtime | ~15s cached / ~23s per band point (75k loans × 42 months × 2 regimes) |

Literature microsim is calibrated via defendable bounds (PSA speed, Rothstein band, involuntary floor) — not fitted to $764.7B. Peak lag −3 confirms hazard leads SOMA by ~3 months (TBA pipeline). The earlier $747B (97.7%) figure predates the β₁ units fix (§15) and is reproducible from the `pre-fix-2026-07` baseline.

---

## 12. Current Headline Numbers

### Empirical anchor (all frameworks)

| Metric | Value |
|---|---|
| Empirical trapped liquidity (SOMA, active QT) | **$764.7B** |
| QT window | June 2022 – November 2025 |
| Empirical CPR mean | 5.53% (30yr-only back-out) / 5.14% (30yr+15yr, current default) |
| SOMA WAC | 2.55% (7 buckets, 30yr-only, 90.6% coverage) / 2.49% (11 buckets, 30yr+15yr, 99.8% coverage) |

### ABM (production: surface + settlement lag + 15yr fold-in, **`run-2026-07-04-15yr-foldin`**)

| Metric | Value |
|---|---|
| U.S. trapped liquidity | **$91.0B** (**11.9%** of empirical) |
| Danish trapped (dynamic balance) | **-$834.5B** |
| Institutional gap (U.S. − Danish) | **$925.5B** |
| U.S. CPR mean | 11.68% |
| Empirical CPR back-out | 5.14% (15yr scheduled amort now weighted in; see §15 Fix 2) |
| Danish CPR mean | 47.14% (range 36.18%–51.17%) |
| Institutional wedge (DK − US) | 35.46pp mean |
| CPR R² (raw) | -6.984 |
| Monte Carlo (50 seeds) | not re-run post-fold-in; prior estimate ($113.5B, 30yr-only book) is stale |

Superseded run `run-2026-07-04` (30yr-only, $101.2B / 13.2%) remains reproducible via `terms=("30yr",)` — see §15 Fix 2.

Reproduce: `cd abm && python3 freeze_run.py --tag <name>` → `data/runs/<name>/manifest.json`. All CPR means use the 42-month active QT window (`qt_active_frame`), not `index >= QT_START` alone.

### Hazard Path A — cohort fractional (Freddie 2017–2021, spec v3)

| Metric | Value |
|---|---|
| Trapped liquidity | **$915B (119.7%)** |
| β(rate_gap_bps) | +0.67 (OK, standardized) |
| β(burnout_orth) | **−0.13 (OK)** |
| β(friction) | −0.037 (OK) |
| CPR r (lag 0) | −0.444 |
| Holdout RMSE | ~38pp |
| Stratum FE | 295 four-way pools |

### Hazard Path B — literature microsim (Freddie 2017–2021, post-β₁-fix)

| Metric | Value |
|---|---|
| Trapped liquidity | **$818.5B (107.0%)** |
| Rothstein band (5.5%–7.7%) | $810B – $828B (105.9%–108.2%) |
| CPR r (lag 0) | +0.190 |
| **Peak cross-corr** | **lag −3, r = +0.404** |

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
| Settlement timing | Markov pipeline (hazard) vs lag kernel (ABM) | ABM kernel tested null (§21); hazard routes prepay directly — document lag −3, do not convolve |
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
- **15-year MBS folded in structurally** (weights + scheduled amortization;
  coverage 99.8%). Voluntary CPR for 15yr cohorts uses the same-coupon
  30-year surface — the ABM payment-delta gate is unreliable for
  short-amortization loans (see §15 Fix 2).
- **FRED API key** resolved via `common/fred_key.py` from the `FRED_API_KEY`
  env var or a gitignored `.env` (see `.env.example`); no key in committed
  source.

### Model

- ABM monthly CPR path fit remains weak (negative R²) despite 11.9% aggregate share (post 15yr fold-in; see §15 Fix 2).
- Danish counterfactual uses U.S.-calibrated friction.
- DTI check is front-end only (no total debt).
- Empirical lag-0 CPR correlation remains negative for the ABM and Path A (structural timing mismatch with SOMA settlement, not fixed with GLM lag terms); Path B's lag-0 correlation is positive (+0.19) with peak at lag −3, r=+0.40 — the two hazard paths disagree on contemporaneous alignment even though both lead SOMA by ~3 months at peak.
- Hazard Path A uses Poisson GLM with stratum FE (295 dummies) and mild Ridge (α=1e-5); plain IRLS is ill-conditioned at this FE dimensionality.
- Cross-design test (§15 Fix 1) only swaps structural covariates; the recalibrated-vs-frozen calibration gap ($294B) shows aggregate share is highly sensitive to how the mobility anchor is set, not just to which population feeds it.

### Next steps (priority order)

1. **Symmetric companion test** (§15 Fix 1, optional PR6 in the original plan): run the hazard framework on a synthetic-only population to fully separate "paradigm" from "data source" — required by §VII.A before the cross-design result can be treated as conclusive.
2. **Reconcile the cross-design result with the paper's paradigm claim.** The recalibrated primary variant recovers 59.3%, above the pre-registered 50% "undercuts" threshold — Table 1/abstract framing needs to address this directly rather than cite only the synthetic-population 11.9%.
3. **Re-run Monte Carlo (50 seeds)** against the 15yr-foldin production tag; the $113.5B estimate on file is 30yr-only and stale.

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
trapped liquidity to −$169B. Production therefore uses a **structural-only**
fold-in: 15yr cohorts contribute real weights and 15-year scheduled
amortization, but voluntary CPR comes from the same-coupon 30-year surface.
Native 15yr surfaces remain in `abm_cpr_surface.csv` for inspection. Movers
now refinance same-term (was: hardcoded fresh 30-year — identical behavior
for the 30-year book).

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
population — still open).

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
(Rothstein 6.5% midpoint), same competing-risks logic, same draw seed. 100
independent permutations, matching the 50-seed Monte Carlo convention.

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

---

## 17. Cross-Foundation Checks — Hybrid Pipeline and Full-Book Weighting

### 17.1 Hybrid pipeline: shared accounting, hazard micro-foundation (roadmap 3.2)

**What.** [`abm/hybrid_pipeline.py`](abm/hybrid_pipeline.py) runs the ABM's
macro-accounting layer (SOMA balance tracking, phased-cap netting, curtailment,
scheduled amortization, Danish dynamic-balance loop) but replaces the ABM CPR
surface with Path B's literature microsim CPR (`use_hazard_microsim=True`; the
ABM settlement kernel auto-disables since Markov routing already handles the
pipeline lag). Only the micro-foundation for loan behavior varies; the
accounting is held identical.

**Result.**

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
framework encodes the same institution through the NPV identity (§15 Fix 3):
when rates rise above coupon the buyback discount exactly offsets the locked-in
spread, so prepaying is economically *neutral* and the Danish hazard resets to
the ~6% PSA baseline rather than a refi wave. Under that (more economically
coherent) encoding the Danish and U.S. books behave similarly and the gap nearly
vanishes ($61.2B).

This does not overturn the *sign* of the lock-in story (U.S. par-payoff still
traps more than a market-value system in every specification), but it shows the
*magnitude* of the institutional gap is a micro-foundation artifact, not a
robust structural number. The ABM's $925.5B should be read as an upper bound
under its specific behavioral encoding, and the paper should cite the hybrid
$61.2B alongside it. (The U.S.-side recovery also rises from Path B's standalone
107% to 97.9% here because the shared layer additionally nets ~$70B of
curtailment and term-aware scheduled amortization that Path B's own scorer omits.)

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

## Appendix — File Map

```
Lock-in-Effect/
├── README.md                 # Quick start and index
├── TECHNICAL.md              # this document
├── requirements.txt
├── common/                   # Shared QT window config (§15 Fix 4)
│   └── qt_window.py           # single source of truth, imported by abm/ and hazard/
├── tests/                     # Cross-framework regression tests
│   └── test_qt_window.py      # 7 tests incl. post-QT-drift regression
├── runs/                      # Frozen baseline snapshots (§15 Step 0)
│   └── pre-fix-2026-07/       # pre-robustness-fix manifest + builder script
├── abm/                      # Agent-based pipeline (frozen archive)
│   ├── README.md
│   ├── TECHNICAL.md          # Granular ABM bug history (§1–§21)
│   ├── abm_lockin_simulation.py   # --population={synthetic,freddie} (§15 Fix 1)
│   ├── fed_mbs_extension_risk.py   # + use_hazard_microsim bridge; term-aware cohorts (§15 Fix 2)
│   ├── freddie_population.py       # structural-covariate loader (§15 Fix 1)
│   ├── cross_design_test.py        # both calibration variants + report (§15 Fix 1)
│   ├── data/runs/                  # tagged freeze_run.py manifests
│   └── sensitivity/robustness/monte_carlo scripts
└── hazard/                   # Reduced-form hazard framework
    ├── README.md             # Pipeline specs and equations
    ├── config.py              # re-exports QT window from common/ (§15 Fix 4)
    ├── ingest.py, hazard_fit.py, stratum.py, simulate.py   # Path A
    ├── loan_sample.py, microsim_engine.py, ...   # Path B; --band runs Rothstein sensitivity (§15 Fix 3)
    ├── literature_hazard.py, rate_gap.py   # β₁ + regime-specific rate gap (units fixed, §15 Fix 3)
    ├── permutation_test.py    # marginal-preserving joint-structure null test (§16)
    └── data/                   # Parquet, JSON, PNG outputs
```

---

*Last updated: July 2026. Hazard spec v3: stratum FE (295 pools), burnout sign fixed (−0.13). Post robustness-fix program (§15): Path B at 107.0% trapped (band 105.9%–108.2%) after the β₁ units fix; ABM at 11.9% after the 15-year MBS fold-in; cross-design test with real Freddie covariates recovers 59.3% (recalibrated) / 20.9% (frozen). Permutation test (§16, n=999, exact p=0.001): Path B's recovery is a marginal-distribution result — scrambling the joint covariate structure moves it only 0.27% ($2.2B); the trapped-level effect is interaction-dominated across axes and the CPR-path signal localizes to origination-time.*
