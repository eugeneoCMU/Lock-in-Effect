# Technical Narrative — Lock-In Effect Project

This document is the **repository-level** technical history: what was built, what broke, what was fixed, what was falsified, and why the codebase now has two frameworks (`abm/` and `hazard/`). It is written for a reader who wants the full causal chain from the original **$972.3B** headline to the current validated **$764.7B** empirical benchmark, the **13.2%** ABM share explained, and the newer reduced-form hazard pipelines.

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

### Real-data results (Freddie 2017–2021 sample)

| Metric | Value |
|---|---|
| Trapped liquidity | **$747B (97.7%)** |
| CPR r (lag 0) | +0.368 |
| **Peak cross-corr** | **lag −3, r = +0.444** |
| Runtime | ~15s cached / ~2min full rebuild (75k loans × 42 months × 2 regimes) |

Literature microsim is calibrated via defendable bounds (PSA speed, Rothstein band, involuntary floor) — not fitted to $764.7B. Peak lag −3 confirms hazard leads SOMA by ~3 months (TBA pipeline).

---

## 12. Current Headline Numbers

### Empirical anchor (all frameworks)

| Metric | Value |
|---|---|
| Empirical trapped liquidity (SOMA, active QT) | **$764.7B** |
| QT window | June 2022 – November 2025 |
| Empirical CPR mean | 5.53% |
| SOMA 30yr WAC | 2.55% (7 buckets) |

### ABM (production: surface + settlement lag, **`run-2026-07-04`**)

| Metric | Value |
|---|---|
| U.S. trapped liquidity | **$101.2B** (**13.2%** of empirical) |
| Danish trapped (dynamic balance) | **-$829.1B** |
| Institutional gap (U.S. − Danish) | **$930.3B** |
| U.S. CPR mean | 11.98% |
| Danish CPR mean | 47.21% (range 36.26%–51.26%) |
| Institutional wedge (DK − US) | 35.24pp mean |
| CPR R² (raw) | -6.443 |
| Monte Carlo mean (50 seeds) | $113.5B [95% CI: $106.6B–$120.4B] |

Reproduce: `cd abm && python3 freeze_run.py --tag run-2026-07-04` → `data/runs/run-2026-07-04/manifest.json`. All CPR means use the 42-month active QT window (`qt_active_frame`), not `index >= QT_START` alone.

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

### Hazard Path B — literature microsim (Freddie 2017–2021)

| Metric | Value |
|---|---|
| Trapped liquidity | **$747B (97.7%)** |
| CPR r (lag 0) | +0.368 |
| **Peak cross-corr** | **lag −3, r = +0.444** |

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

---

## 14. Known Limitations and Next Steps

### Data

- **Freddie Mac 2017–2021** integrated via `prepare_freddie.py` (20 quarters in `hazard/data/raw/`).
- **15-year MBS excluded** from SOMA cohort modeling (~9% of face value).
- **FRED API key** hardcoded in config files; should be env var for production use.

### Model

- ABM monthly CPR path fit remains weak (negative R²) despite 13.2% aggregate share.
- Danish counterfactual uses U.S.-calibrated friction.
- DTI check is front-end only (no total debt).
- Literature microsim CPR magnitudes on synthetic data are not calibrated to empirical level.
- Empirical lag-0 CPR correlation remains negative — structural timing mismatch with SOMA settlement, not fixed with GLM lag terms.
- Hazard Path A uses Poisson GLM with stratum FE (295 dummies) and mild Ridge (α=1e-5); plain IRLS is ill-conditioned at this FE dimensionality.

### Next steps (priority order)

1. **Tune trapped liquidity** toward 90–115% band (SOMA cohort weighting or mild calibration)
2. **SOMA cohort weighting** in hazard simulation (partial via balance weights; full book alignment TBD)
3. **Optional:** Run `fed_mbs_extension_risk.py` with `use_hazard_microsim=True` and compare institutional gap to ABM surface path

---

## Appendix — File Map

```
Lock-in-Effect/
├── README.md                 # Quick start and index
├── TECHNICAL.md              # this document
├── requirements.txt
├── abm/                      # Agent-based pipeline (frozen archive)
│   ├── README.md
│   ├── TECHNICAL.md          # Granular ABM bug history (§1–§21)
│   ├── abm_lockin_simulation.py
│   ├── fed_mbs_extension_risk.py   # + use_hazard_microsim bridge
│   └── sensitivity/robustness/monte_carlo scripts
└── hazard/                   # Reduced-form hazard framework
    ├── README.md             # Pipeline specs and equations
    ├── ingest.py, hazard_fit.py, stratum.py, simulate.py   # Path A
    ├── loan_sample.py, microsim_engine.py, ...   # Path B
    └── data/                   # Parquet, JSON, PNG outputs
```

---

*Last updated: July 2026. Hazard spec v3: stratum FE (295 pools), burnout sign fixed (−0.13), literature microsim at 97.7% trapped.*
