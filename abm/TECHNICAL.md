# Technical Narrative — Corrections, Validation, and Final Numbers

This document is a chronological record of the investigation that took the project's headline "trapped liquidity" figure from an unsupported **$972.3B** to a validated **$764.7B** (active QT window), fixed aggregation and multi-cohort correctness bugs, tested vintage burnout (failed, §20) and a settlement-lag kernel (null, §21), and documents the full validation suite. Historical milestones along the way include the **$672.9B** figure (pre QT-window fix) and **$257.6B / 38.3%** ABM share (pre reference-cohort calibration).

For the high-level project description and how to run the code, see [README.md](README.md). This document assumes familiarity with that overview and focuses on *why* each number is what it is.

---

## Table of Contents

1. [Origin of the $972.3B Figure and Why It Was Wrong](#1-origin-of-the-9723b-figure-and-why-it-was-wrong)
2. [Fix 1 — Phased QT Cap](#2-fix-1--phased-qt-cap)
3. [Fix 2 — Net Accumulation](#3-fix-2--net-accumulation)
4. [Fix 3 — SOMA Data Source](#4-fix-3--soma-data-source)
5. [Corrected Empirical Benchmark: $672.9B](#5-corrected-empirical-benchmark-6729b)
6. [ABM Structural Omission — Scheduled Amortization](#6-abm-structural-omission--scheduled-amortization)
7. [Empirical CPR Extraction](#7-empirical-cpr-extraction)
8. [Goodness-of-Fit Methodology](#8-goodness-of-fit-methodology)
9. [Sensitivity Analysis](#9-sensitivity-analysis)
10. [Robustness Analysis](#10-robustness-analysis)
11. [Monte Carlo Population-Draw Robustness](#11-monte-carlo-population-draw-robustness)
12. [The Danish Counterfactual Bug History](#12-the-danish-counterfactual-bug-history)
13. [Cross-Correlation Diagnostic](#13-cross-correlation-diagnostic)
14. [Out-of-Sample Holdout Split](#14-out-of-sample-holdout-split)
15. [Behavioral Extensions — DTI, Loss Aversion, Wait-and-See](#15-behavioral-extensions--dti-loss-aversion-wait-and-see)
16. [Curtailment Prepayment Channel](#16-curtailment-prepayment-channel)
17. [Final Numbers Table](#17-final-numbers-table)
18. [Known Limitations and Open Items](#18-known-limitations-and-open-items)
19. [Multi-Vintage Coupon Cohorts](#19-multi-vintage-coupon-cohorts)

---

## 1. Origin of the $972.3B Figure and Why It Was Wrong

The original pipeline computed "trapped liquidity" as the cumulative shortfall between the Fed's QT roll-off target and actual roll-off, and reported **$972.3 billion**. Independent reasoning from the Fed's reported ~$600B in actual MBS redemptions since June 2022 suggested the true cap-based shortfall should be closer to **$800-870B**, not $972.3B. Investigating the gap turned up three compounding errors:

1. **Flat QT cap assumption**: the code assumed a flat **-$35B/month** target starting immediately in June 2022. In reality, the Fed announced a **three-month ramp-up** at $17.5B/month (half-pace) before reaching the full $35B/month pace in September 2022. Treating the ramp months as if they were already at full pace overstated the "shortfall" in every one of those early months.
2. **`WSHOMCB` TBA-settlement noise**: the actual roll-off was computed as `WSHOMCB.diff()` (week-over-week change in the Fed's reported MBS holdings, resampled to monthly). This FRED series reflects **settlement-date** accounting for TBA (to-be-announced) MBS trades, which introduces timing noise — some early QT months even showed the balance *increasing* due to settlement lag, which inflated the apparent shortfall in surrounding months once smoothed into a monthly cadence.
3. **One-sided accumulation logic**: the cumulative trapped-liquidity sum only accumulated *positive* deltas (months where actual roll-off fell short of the target), via `.clip(lower=0)`, ignoring months where roll-off *exceeded* the target. This turned out not to materially affect the U.S. empirical figure by itself (no month ever exceeded the cap), but the same logic pattern, applied to the Danish counterfactual, caused a much more serious bug — see [Section 12](#12-the-danish-counterfactual-bug-history).

---

## 2. Fix 1 — Phased QT Cap

```133:169:fed_mbs_extension_risk.py
def compute_qt_target_series(index: pd.DatetimeIndex) -> pd.Series:
    ...
```

Introduced `QT_TARGET_RAMP_B = -17.5` and `QT_TARGET_FULL_B = -35.0`, with `QT_RAMP_END = 2022-09-01` marking the transition. `compute_qt_target_series()` now returns `-17.5` during the June-August 2022 ramp, `-35.0` from September 2022 through the end of QT, and `0.0` after QT ends (December 2025). This alone removed a meaningful chunk of the inflation in the early months of the sample.

---

## 3. Fix 2 — Net Accumulation

Cumulative trapped liquidity now sums the **net** monthly delta (`Extension_Delta_Billions.fillna(0.0)`, no clipping) rather than only positive deltas:

```484:490:fed_mbs_extension_risk.py
    trapped = df["Extension_Delta_Billions"].fillna(0.0)
    trapped = trapped.where(qt_active, 0.0)
    df["Cumulative_Trapped_Liquidity"] = trapped.cumsum()
```

For the U.S. empirical series this had negligible numerical effect (no month in the sample exceeded the cap), but it is the correct general formula, and it became essential once applied consistently to the Danish counterfactual (Section 12).

---

## 4. Fix 3 — SOMA Data Source

```345:385:fed_mbs_extension_risk.py
def fetch_soma_mbs_monthly(start: str = START_DATE,
                           url: str = SOMA_SUMMARY_URL) -> Optional[pd.Series]:
    ...
```

Added a direct pull from the NY Fed Markets API (`markets.newyorkfed.org/api/soma/summary.json`), which reports the System Open Market Account's weekly MBS **current face value** — the remaining unpaid principal balance of the underlying mortgage pools. `compute_metrics()` prefers this source when available and falls back to `WSHOMCB` diffs automatically if the API is unreachable — the resulting `Rolloff_Source` column records which was used.

This is a real accounting distinction, not just a data-cleanliness preference. Per the Fed's own Financial Accounting Manual, SOMA holdings (including `WSHOMCB`) are booked at **amortized cost, on a settlement-date basis** — not fair value, and not raw face value. Because the Fed's MBS purchases were largely executed at a premium (bought when mortgage rates, and therefore coupons, were near record lows relative to prevailing prices), `WSHOMCB`'s amortized cost declines every period from **premium amortization** on top of, and independent of, actual mortgage principal being repaid. Differencing `WSHOMCB` month-over-month therefore conflates two distinct things: real principal paydown (what matters for CPR/roll-off) and pure accounting amortization drift. The NY Fed's SOMA current-face-value series does not have this confound, since current face value only moves when principal is actually paid down (or securities are purchased/sold) — it is not adjusted for premium/discount accretion.

Both series remain **settlement-date** accounting, and both flow through the same To-Be-Announced (TBA) forward market, where a trade can be agreed weeks before it settles (allocation day is only 2 business days before settlement, per the SIFMA schedule). So switching to SOMA removes the amortized-cost confound but does **not** remove TBA-settlement lag — that limitation is shared by both sources.

---

## 5. Corrected Empirical Benchmark: $764.7B (active QT window)

The headline empirical trapped-liquidity figure is the **net sum of monthly extension deltas** during the **active QT window only** (`QT_START` ≤ month < `QT_END`, i.e. June 2022 through November 2025). Post-QT months are excluded because the QT target is $0 and continuing to accumulate deltas would dilute the headline with spurious negatives as the ABM keeps simulating roll-off.

```
Net Trapped Liquidity (sum of monthly deltas): $764.7B
```

**QT-window bug (fixed July 2026):** prior versions summed every month `>= QT_START` without an upper bound. QT ended December 2025, but the data series now extends ~7 months past it; each post-QT month added a large negative delta while the cumulative series correctly flatlined via `qt_active`. This understated both the empirical total (previously **$672.9B**) and the ABM share-explained ratio. All headline aggregations in `print_summary()`, `monte_carlo_simulation.py`, `sensitivity_analysis.py`, and `robustness_analysis.py` now use `qt_active_mask()` / `qt_active_frame()`.

Earlier methodological fixes (phased ramp cap, SOMA current-face roll-off) remain documented in Sections 1–4; the $672.9B figure in historical comparison tables (Sections 15–19) predates this QT-window correction. With phased cap and SOMA in place, the corrected active-window total is **$764.7B** — up from $672.9B because the prior headline was diluted by post-QT months rather than because the underlying roll-off series changed materially.

---

## 6. ABM Structural Omission — Scheduled Amortization

The ABM's CPR surface captures **prepayment** behavior (a household selling or refinancing) but says nothing about **scheduled amortization** — the routine principal component of every mortgage payment that flows through every month whether or not anyone prepays. The macro model was applying only the ABM's CPR to the portfolio, ignoring a real and substantial cash-flow component.

The fix adds a matching scheduled-amortization model, calibrated to the **same** mortgage assumptions the ABM uses (3.0% coupon, 30-year term, mid-2020 origination — see `ORIGINAL_RATE`/`TERM_YEARS` in `abm_lockin_simulation.py` and `PORTFOLIO_COUPON`/`PORTFOLIO_TERM`/`PORTFOLIO_ORIGIN` in `fed_mbs_extension_risk.py`):

```59:102:fed_mbs_extension_risk.py
def scheduled_amortization_smm(annual_rate: float, term_months: int,
                               months_elapsed: int) -> float:
    ...

def scheduled_amortization_series(index: pd.DatetimeIndex, ...) -> pd.Series:
    ...
```

Every simulated roll-off calculation (`US_Simulated_Monthly_Rolloff_Billions`, `Danish_Simulated_Monthly_Rolloff_Billions`) now applies `CPR/12 + scheduled_SMM` to the balance, not `CPR/12` alone. Over the QT window this scheduled-amortization component alone accounts for **$242.1B** of roll-off (SMM ≈ 0.213%/month, ≈ 2.55% annualized) — a component the ABM-only figure was previously missing entirely.

---

## 7. Empirical CPR Extraction

To compare the ABM's predicted CPR against reality month-by-month (rather than only comparing aggregate trapped-liquidity totals), the empirical CPR is backed out of actual roll-off by inverting the same relationship used for the simulated series:

```
actual_rolloff = -holdings * (empirical_CPR/12 + scheduled_SMM)
=> empirical_CPR = (|actual_rolloff| / holdings - scheduled_SMM) * 12
```

```523:526:fed_mbs_extension_risk.py
    actual_abs = df["Actual_Monthly_Rolloff_Billions"].abs()
    empirical_smm = (actual_abs / holdings_b) - sched_smm
    df["Empirical_CPR_Pct"] = (empirical_smm.clip(lower=0) * 12 * 100)
```

This produces an `Empirical_CPR_Pct` series ranging from 0.00% to 14.02% (mean 5.53%) over the active QT window, directly comparable to the ABM's `US_CPR_Pct` (7.55%-21.72%, mean 11.98%). Multi-cohort runs now use **cohort-weighted** `Scheduled_Amort_SMM` (not the legacy single 3.0% coupon series) so the empirical CPR back-out is apples-to-apples with the simulation. The `cpr_diagnostic.png` chart (via `plot_cpr_diagnostic()`) visualizes this month-by-month, both as a time series and as a scatter against the prevailing mortgage rate.

---

## 8. Goodness-of-Fit Methodology

```105:130:fed_mbs_extension_risk.py
def cpr_goodness_of_fit(empirical: pd.Series, predicted: pd.Series,
                        smooth_window: int = 3) -> dict:
    ...
```

Reports R² (`1 - SS_res/SS_tot`), RMSE (`sqrt(mean((actual-pred)^2))`), MAE, and Pearson r, both on the raw monthly series and on a 3-month centered rolling average ("smoothed", intended to filter out settlement-timing noise). **Current results** (N=42 active QT months, surface interpolation + settlement-lag kernel):

| | R² | RMSE | MAE | r |
|---|---|---|---|---|
| Raw | -6.443 | 7.73pp | 6.58pp | -0.316 |
| Smoothed | -14.464 | 7.14pp | 6.41pp | -0.397 |

A negative R² means the ABM's month-to-month CPR path is a *worse* predictor than simply using the empirical mean every month — i.e., the ABM's aggregate **level** understates trapped liquidity (13.2% share explained) while its **monthly path** over-predicts CPR volatility. Section 13 investigates why smoothing makes R²/r *worse* rather than better; Section 21 tests whether settlement-lag convolution fixes the weak cross-correlation peak.

---

## 9. Sensitivity Analysis

`sensitivity_analysis.py` sweeps all 5×5×5 = 125 combinations of the three dynamic-friction parameters (`BASE_FRICTION` 5-9%, `SEARCH_PENALTY_CAP` 0-400bps, `SENTIMENT_PENALTY_CAP` 0-300bps).

**Bug found and fixed**: the original `aggregate_trapped()` helper computed "empirical trapped liquidity" as `US_Missed_Rolloff_Billions.sum()` — which is the **ABM's own simulated** trapped liquidity, not the actual empirical figure. This made the baseline "share explained" trivially **100%** (the ABM compared against itself) and inflated the sensitivity range accordingly (0%-136%).

**Fix**: added an `empirical_trapped()` helper that sums `Extension_Delta_Billions` (the true SOMA-vs-cap empirical anchor, independent of the ABM), and passes this fixed value into every scenario's share-explained calculation:

```38:48:sensitivity_analysis.py
def empirical_trapped(df: pd.DataFrame) -> float:
    """Actual SOMA/WSHOMCB roll-off vs QT cap — independent of the ABM."""
    ...
```

**Current results** (post correctness fixes, surface + settlement lag): baseline U.S. trapped = **$101.2B** against empirical **$764.7B** = **13.2%** share explained. Across all 125 scenarios: trapped liquidity ranges **-$265.1B–$265.5B**, share explained ranges **-34.7%–34.7%**, CPR R² ranges -16.575 to -3.498, RMSE ranges 6.01–11.88pp. The ABM now **over-predicts** aggregate prepayment (CPR mean 11.98% vs empirical 5.53%), so the baseline sits below the historical 38–80% share-explained range documented in Sections 15–19.

---

## 10. Robustness Analysis

`robustness_analysis.py` holds the ABM fixed and varies the *empirical* side of the comparison across two panels:

**Panel B — data source** (current):

| Source | Empirical | ABM Share |
|---|---|---|
| SOMA | $764.7B | 13.2% (R²=-6.443) |
| WSHOMCB | $763.7B | 13.2% (R²=-5.250) |

The two data sources agree to within 0.1%. SOMA remains the preferred source (current face value; see Section 4).

**Panel C — cap-schedule sensitivity** (current): 18 scenarios sweeping ramp duration (2/3/4 months), full-pace cap ($30B/$35B), and QT-end date (Jun/Sep/Dec 2025). The empirical benchmark ranges from **$479.6B to $782.2B** and the ABM's share-explained ranges from **-24.6% to 15.2%** — the baseline (3-month ramp, $35B cap, Dec 2025 end) sits at **$764.7B empirical / 13.2% share**.

---

## 11. Monte Carlo Population-Draw Robustness

`monte_carlo_simulation.py` reruns the entire ABM→macro pipeline 50 times, each time re-seeding NumPy/`random` and rebuilding both the 10,000-household population and the CPR surface from scratch (`abm.HousingMarketEngine(seed=i, ...)`), then recomputing U.S. trapped liquidity against the shared, runtime-computed empirical benchmark.

**Current result** (50 seeds, CPR surface rebuilt per draw, settlement-lag kernel): mean **$113.5B**, std **$24.8B**, 95% CI **[ $106.6B, $120.4B ]** against empirical **$764.7B**. Runtime **4.6 min** (~5.5 s/seed). Population-draw variance is material; the fixed-CSV-surface run (std ≈ $0) was a bug — surfaces must be rebuilt per seed.

---

## 12. The Danish Counterfactual Bug History

This was the most serious bug found in the session, and it went through three distinct stages before landing on a defensible number.

### Stage 0 — the original `clip(lower=0)` bug: Danish trapped = $0B

The original code computed Danish "missed roll-off" the same way as the (then also buggy) empirical figure — via one-sided clipping:

```python
df["Danish_Missed_Rolloff_Billions"] = (
    df["Danish_Extension_Delta_Billions"].clip(lower=0)
)
```

Because the Danish CPR is always high (borrowers can profitably prepay at a discount whenever rates rise above their coupon — roughly 21-27% CPR throughout the QT window), the simulated Danish roll-off **always exceeded** the QT cap. That means `Danish_Extension_Delta_Billions` was **negative every single month** (overshoot, never a shortfall). `.clip(lower=0)` turned every one of those negative values to zero, so summing 42 months of zeros gave **exactly $0.0B** — not because the Danish counterfactual didn't matter economically, but because the accumulation formula structurally couldn't register overshoot at all.

This silently collapsed the "institutional gap" claim:

```
Institutional Gap = US Trapped - Danish Trapped = US Trapped - 0 = US Trapped
```

The gap figure being cited in early drafts (e.g., "$924.5B") was therefore just the U.S. ABM figure under a different friction calibration — the Danish side was contributing nothing mathematically, even though the argument required it to be doing real independent work.

### Stage 1 — net accumulation without dynamic balance: -$1,132B

Fixing the one-sided clip (Section 3) let overshoot register as a negative contribution, which is correct in principle. But the Danish roll-off was still being computed as `-holdings_b * (danish_CPR/12 + scheduled_SMM)`, where `holdings_b` is the **actual U.S. balance path** (`WSHOMCB / 1000`) — i.e., applying a ~24% annual prepayment rate to a balance that hadn't actually shrunk by that much. Compounding this error over 42 months of QT produced an economically implausible **-$1,132B** Danish trapped liquidity, and an inflated **$1,676.1B** institutional gap.

### Stage 2 — dynamic-balance simulation (superseded; see Section 17 for current)

The fix simulates the Danish balance **forward month-by-month** starting from the actual balance at QT start. **Historical result** at the time of writing: Danish trapped **-$359.7B**, institutional gap **$903.8B**. **Current result** (multi-cohort + correctness fixes + settlement lag): Danish trapped **-$829.1B** ($2,535B → $428B), institutional gap **$930.3B**.

### Summary of the evolution

| Stage | Danish Trapped | Institutional Gap | Bug |
|---|---|---|---|
| 0 (original) | $0.0B | ≈ US-only figure | One-sided `clip(lower=0)` zeroed every month |
| 1 (intermediate) | -$1,132.0B | $1,676.1B | Danish CPR applied to static U.S. balance |
| 2 (current) | -$359.7B | $903.8B | Dynamic declining-balance simulation |

---

## 13. Cross-Correlation Diagnostic

The negative correlation between ABM and empirical CPR (Section 8) initially suggested a "settlement noise" explanation — the idea that SOMA settlement timing introduces month-to-month jitter that a rolling average should smooth away, revealing a better underlying fit. This was tested directly and rejected.

```132:152:fed_mbs_extension_risk.py
def cpr_cross_correlation(empirical: pd.Series, predicted: pd.Series,
                          max_lag: int = 3) -> dict:
    ...
```

**Current cross-correlation** (settlement-lag kernel applied; N=42):

| Lag (months) | Raw r |
|---|---|
| -3 | +0.192 |
| -2 | -0.209 |
| -1 | -0.140 |
| **0** | **-0.316** |
| +1 | -0.206 |
| +2 | -0.033 |
| +3 | +0.103 |

Peak remains at lag **-3** (r = +0.192) — weak and unchanged in direction from pre-kernel diagnostics. Section 21 reports the settlement-lag kernel as a **null** timing fix.

---

## 14. Out-of-Sample Holdout Split

Because the three dynamic-friction parameters could in principle be tuned to fit the full QT-period sample, a temporal holdout split checks whether the model's fit degrades on data it didn't implicitly "see":

- **In-sample**: June 2022 - December 2023 (N=19 months)
- **Out-of-sample**: January 2024 - November 2025 (N=30 months)

```905:926:fed_mbs_extension_risk.py
        holdout_date = pd.Timestamp("2024-01-01")
        in_mask = ecpr.index < holdout_date
        out_mask = ecpr.index >= holdout_date
        ...
```

**Current result** (surface + settlement lag):

| | N | R² | RMSE | Share Explained |
|---|---|---|---|---|
| In-sample | 19 | -10.990 | 8.86pp | -11.1% |
| Out-of-sample | 23 | -4.222 | 6.66pp | 32.5% |

Out-of-sample share explained is higher than in-sample, but both R² values are deeply negative and in-sample share is negative — the model **over-predicts** simulated roll-off in the early QT period (net negative trapped contribution) and under-predicts in the later period. This is no longer the "better out-of-sample" pattern seen in earlier single-cohort calibrations (historical table above); the max-weight 2.0% reference cohort and cohort-weighted amortization shifted the CPR surface upward.

---

## 15. Behavioral Extensions — DTI, Loss Aversion, Wait-and-See

Three behavioral mechanisms were added to `Household.evaluate_move()` to test whether the 19.2% residual ($128.9B gap between the ABM's $544.0B and the empirical $672.9B) could be explained by credit constraints, prospect-theory loss aversion, and rate-shock paralysis. All parameters were set from external sources — no parameter was tuned to match $672.9B.

### 15.1 Mechanisms

1. **DTI hard wall** — if the new mortgage payment exceeds 43% of gross monthly income, the move is vetoed (the bank rejects the loan). Source: CFPB Qualified Mortgage / Ability-to-Repay rule, 12 CFR 1026.43(e)(2)(vi). This is a front-end-only ratio (mortgage payment / income) since the model has no data on other household debts; the true regulatory threshold is a back-end ratio.

2. **Asymmetric loss aversion** — payment *increases* are perceived at 2.25x their dollar value; payment *decreases* are unscaled. Source: Kahneman & Tversky (1979, 1992) prospect-theory loss-aversion coefficient. This preserves the asymmetry that is the core of prospect theory: losses hurt more than equivalent gains feel good.

3. **Wait-and-see freeze** — when the trailing 6-month rate change exceeds 150 bps, 20% of otherwise-cleared movers freeze. The freeze is implemented as a fixed per-agent trait (`patience_draw ~ U[0,1]`), not a per-evaluation random roll, so the CPR surface remains deterministic for a given population. The threshold and probability are stated assumptions, not empirically sourced, and should be sensitivity-tested in future work.

### 15.2 3D CPR surface

The wait-and-see gate depends on rate velocity, which varies by month. To preserve the surface-interpolation architecture (rather than moving to online per-month ABM calls), the CPR surface was extended from 2D `(rate × friction)` to 3D `(rate × friction × velocity)`. The velocity grid spans -1.0% to +3.5% in 0.5% steps (10 grid points), covering the observed range of 6-month MORTGAGE30US changes during 2021-2025.

`load_cpr_surface()` and `interp_cpr_surface()` in `fed_mbs_extension_risk.py` were updated to handle both 2D (legacy) and 3D surfaces automatically, using trilinear nested `np.interp` (no SciPy dependency added). `compute_metrics()` computes `Rate_6M_Change = MORTGAGE30US.diff(6) / 100` and passes it as the velocity axis.

### 15.3 Vectorization

The 3D grid expanded the surface from 338 to 3,380 grid points. A per-household Python loop across 10,000 agents per grid point made the Monte Carlo suite infeasible (~5.5 hours). `HousingMarketEngine` was refactored to precompute population attributes as NumPy arrays (`_precompute_arrays`) and evaluate all three behavioral gates vectorially (`_cpr_vec`). This reduced the full ABM surface build from ~6.7 minutes to ~3 seconds (~120x speedup) and the 50-seed Monte Carlo from projected ~5.5 hours to ~46 seconds.

### 15.4 Results — the honest outcome

The behavioral extensions did **not** close the gap; they **widened** it.

| Metric | Before (rational only) | After (behavioral) |
|---|---|---|
| ABM U.S. trapped liquidity | $544.0B (80.8%) | **$419.6B (62.3%)** |
| ABM Danish trapped liquidity | -$359.7B | **-$764.2B** |
| Institutional gap | $903.8B | **$1,183.8B** |
| ABM U.S. CPR (mean) | 6.62% | **7.92%** |
| CPR R² (raw) | -0.590 | **-1.586** |
| Monte Carlo mean | $570.4B | **$438.9B** |
| Monte Carlo 95% CI | [$564.4B, $576.4B] | **[$432.2B, $445.6B]** |

**Why the model moved in the wrong direction**: Loss aversion steepens the penalty function, making the cost of moving at any given rate higher. But the ABM is calibrated to maintain the 4-5% involuntary-turnover floor at 8% rates (death, divorce, default). To hit that floor under a steeper penalty function, `calibrate_mobility_scale()` had to increase `MOBILITY_DESIRE_SCALE` from ~12,500 to ~36,086. That higher desire scale increased CPR at *all* rate levels — including the intermediate rates (5-7%) where most of the QT-period data falls — producing more mobility, faster roll-off, and therefore *less* trapped liquidity.

This is not a bug; it is an honest, pre-committed finding. The calibration target (4-5% floor) is independently grounded in real-world involuntary turnover data — it would be illegitimate to drop or adjust it just because the outcome was surprising. The result demonstrates that adding behavioral frictions to a model that is already calibrated to a turnover anchor can **increase** predicted mobility if the recalibration effect dominates the direct friction effect.

### 15.5 Implications

- The 19.2% residual is **not explained** by DTI constraints, loss aversion, or wait-and-see paralysis, at least not at literature-grounded parameter values without retuning other model parameters.
- The residual likely reflects mechanisms *outside* the household decision function entirely: vintage/seasoning effects, geographic heterogeneity, servicer behavior, or structural features of the MBS pool composition that a representative-coupon model cannot capture.
- The behavioral extensions do strengthen the **institutional gap** claim ($1,183.8B vs $903.8B), since the Danish system's high CPR benefits more from the increased desire scale than the U.S. system's suppressed CPR does.

---

## 16. Curtailment Prepayment Channel

### 16.1 Motivation and pre-registered diagnostic

Partial voluntary prepayments ("curtailments") — extra principal payments beyond the scheduled amount — are a separate channel from move/refinance-driven CPR. Literature suggests curtailment tracks **disposable income availability** (SSRN 4949187, "Understanding Excess Repayment"), not inflation or mortgage rate directly. GSE daily-prepayment-report analysis estimates curtailment at roughly **1.1–1.3% CPR** annualized for recent cohorts (machinesp.com, Sept-2024).

Before building the mechanism, a diagnostic was run: correlation between the ABM's CPR over-prediction (`US_CPR_Pct - Empirical_CPR_Pct`) and Real Disposable Personal Income YoY growth (FRED `DSPIC96`) over the QT window was **r = -0.487**. The worst over-prediction months (Jun–Sep 2022, bias +9.6 to +14.8pp) coincide with the most negative income growth (-3% to -4.6%). **Pre-registered expectation**: because curtailment is additive-only (extra roll-off, never less than zero) and near-zero during stress months where the model is worst, adding curtailment would likely **worsen** the aggregate trapped-liquidity match (estimated $60–90B of extra simulated roll-off → ABM trapped liquidity toward ~$330–360B, down from $419.6B).

### 16.2 Implementation

Curtailment lives entirely in the macro layer ([fed_mbs_extension_risk.py](fed_mbs_extension_risk.py)) — no ABM or calibration changes:

- **Data**: FRED `DSPIC96` (real disposable personal income), merged in `fetch_data()`.
- **Scaling**: `curtailment_series()` maps real-income YoY growth continuously from 0% curtailment at -2% income growth to full curtailment at +4% income growth.
- **Magnitude**: `CURTAILMENT_CPR_HEALTHY = 0.012` (~1.2% CPR annualized at full scale).
- **Roll-off**: added to U.S. and Danish simulated monthly drain alongside CPR and scheduled amortization. Empirical CPR back-out is unchanged (historical roll-off already embeds whatever curtailment occurred).

### 16.3 Results — expectation confirmed

| Metric | Before curtailment | After curtailment |
|---|---|---|
| ABM U.S. trapped liquidity | $419.6B (62.3%) | **$344.6B (51.2%)** |
| Curtailment contribution (QT window) | — | **$74.9B** |
| ABM Danish trapped liquidity | -$764.2B | **-$779.0B** |
| Institutional gap | $1,183.8B | **$1,123.6B** |
| CPR R² / Pearson r (unchanged) | -1.586 / -0.309 | -1.586 / -0.309 |
| Monte Carlo mean | $438.9B | **$364.0B** |
| Monte Carlo 95% CI | [$432.2B, $445.6B] | **[$357.3B, $370.7B]** |

The aggregate trapped-liquidity figure fell by **$75.0B**, squarely within the pre-registered $60–90B band. Share explained dropped from 62.3% to **51.2%** — a worse match to the $672.9B empirical benchmark, exactly as predicted. CPR-path diagnostics did not change, because curtailment affects simulated roll-off only, not the ABM CPR surface or the empirical CPR extraction.

**Interpretation**: curtailment is a real prepayment channel, but modeling it as an *additive* boost to ABM-simulated roll-off pushes the counterfactual further from reality when the ABM already over-predicts mobility. The residual is not explained by "missing curtailment in the simulation"; if anything, the ABM path already implies too much roll-off, and adding more voluntary prepayment during healthy-income months deepens that bias. Closing the gap likely requires mechanisms that *reduce* simulated roll-off (vintage burnout, pool selection) or improve the CPR path itself, not channels that only add principal repayment.

---

## 19. Multi-Vintage Coupon Cohorts

The prior model assumed every household held a **flat 3.0% coupon** with a single origination date (`PORTFOLIO_COUPON = 0.03`, `PORTFOLIO_ORIGIN = 2020-06-01`). The Fed's actual SOMA MBS book is dominated by **2.0–2.5% pandemic-era coupons** (weighted-average coupon ≈ **2.55%** on the 30-year slice). Since a lower coupon implies a larger rate gap at today's ~6.5–7% market rate, the natural hypothesis was that replacing the flat assumption with the real composition would push the ABM's trapped-liquidity prediction **up** toward the $672.9B empirical benchmark.

### 19.1 Data source and parsing

CUSIP-level holdings are fetched live from the NY Fed (distinct from the `summary.json` endpoint used for monthly roll-off):

```
GET https://markets.newyorkfed.org/api/soma/asofdates/latest.json
GET https://markets.newyorkfed.org/api/soma/agency/get/all/asof/{date}.json
```

Each MBS record embeds coupon and maturity in `securityDescription` (e.g. `"UMBS MORTPASS 2% 10/51"`), not as separate fields. `fetch_soma_mbs_cohorts()` in `fed_mbs_extension_risk.py` parses 30-year MBS only, buckets by 0.5%-step coupon, back-derives `origin_date` as `maturity_date − 360 months`, and folds buckets below 2% share into the nearest survivor. **15-year term MBS (~9% of total face value) are excluded** in this pass.

Verified cohort table (as-of 2026-06-24, $1,769.6B of 30yr face value):

| Coupon | Value | Share of 30yr book | Avg months elapsed | Implied origination |
|---|---|---|---|---|
| 1.50% | $53.6B | 3.0% | 62 | 2021.3 |
| 2.00% | $703.1B | 39.7% | 59 | 2021.1 |
| 2.50% | $518.4B | 29.3% | 60 | 2021.0 |
| 3.00% | $209.4B | 11.8% | 100 | 2017.7 |
| 3.50% | $143.0B | 8.1% | 104 | 2017.3 |
| 4.00% | $90.6B | 5.1% | 91 | 2018.4 |
| 4.50%+ | $51.5B | 2.9% | 80 | 2019.8 |

Falls back to a single legacy 3.0% cohort if the API is unreachable.

### 19.2 Architecture changes

1. **`HousingMarketEngine.attach_cohort()`** — decouples household economics (income, home value, desire, txn cost, patience) from mortgage terms. One RNG draw serves all cohorts; `attach_cohort(coupon, months_elapsed)` rebuilds every `Mortgage` in place and re-runs `_precompute_arrays()`.
2. **Per-cohort CPR surfaces** — `build_multi_cohort_surfaces()` loops cohorts, builds a full 3D surface per bucket, and writes one long-format `abm_cpr_surface.csv` with a `Cohort_Coupon` column (23,660 rows = 7 × 3,380).
3. **`load_cpr_surface()`** — returns `{coupon: (rates, frictions, velocities, z_us, z_dk), ...}` when `Cohort_Coupon` is present.
4. **`compute_metrics()`** — weighted sum over cohorts for U.S. simulated rolloff; independent declining-balance Danish loops per cohort summed together. Curtailment remains cohort-agnostic (income-driven). Empirical CPR back-out still uses single `PORTFOLIO_COUPON` scheduled amort (unchanged).

### 19.3 Results — hypothesis falsified

| Metric | Flat 3.0% cohort (Section 16) | Multi-cohort (Section 19) | Direction vs. hypothesis |
|---|---|---|---|
| ABM U.S. trapped liquidity | **$344.6B** (51.2%) | **$257.6B** (38.3%) | ↓ $87.0B — **opposite** of predicted |
| Danish trapped (dynamic balance) | -$779.0B | **-$805.5B** | slightly more overshoot |
| Institutional gap (U.S. − Danish) | $1,123.6B | **$1,063.1B** | ↓ $60.5B |
| ABM U.S. CPR mean (QT window) | 7.92% | **8.67%** | ↑ — model predicts *more* prepayment |
| CPR R² (raw) | -1.586 | **-2.166** | worse path fit |
| Monte Carlo mean (50 seeds) | $364.0B | **$275.7B** (95% CI: $269.3–$282.2B) | ↓ $88.3B |
| Monte Carlo runtime | ~46 s total | **16.1 min** (~19.3 s/seed) | 7 cohorts × surface rebuild |
| Sensitivity range (125 scenarios) | $31.4B–$479.5B | **-$95.7B–$414.2B** | baseline now $257.6B |

The lower-weighted-average coupon did **not** increase trapped liquidity. The weighted multi-cohort model predicts **more** simulated roll-off ($87B less trapped liquidity), not less. CPR path fit also **worsened** (R² from -1.59 to -2.17).

### 19.4 Interpretation

Three compounding effects explain the counter-intuitive direction:

1. **Per-cohort scheduled amortization** — lower-coupon loans amortize principal more slowly (more interest, less SMM). The flat 3.0% model used one amort schedule; the multi-cohort blend uses slower schedules for the dominant 2.0–2.5% buckets, but this is dominated by the CPR effect below.
2. **Younger seasoning on dominant buckets** — the 2.0% cohort (40% weight) has ~59 months elapsed vs. the legacy flat model's ~68 months. Younger loans have higher remaining principal and higher baseline turnover in the ABM's turnover anchor.
3. **CPR surface re-build per coupon** — each cohort gets its own 3D surface at its own coupon gap. The weighted CPR series averages **8.67%** vs empirical **5.62%**, meaning the multi-cohort ABM still **over-predicts** monthly prepayment — and does so more than the single-cohort model did.

**Conclusion**: pool composition is real and measurable, but simply swapping in the Fed's actual coupon/vintage weights **does not** close the $328B residual. The ABM's household-level lock-in mechanism, even when applied cohort-by-cohort with correct coupons and seasoning, produces too much aggregate mobility. The remaining gap is not explained by "wrong average coupon"; it likely reflects loan-level heterogeneity (FICO/LTV/geography), servicer forbearance/modification, and burnout dynamics that a 10,000-agent representative model cannot capture from coupon buckets alone.

### 19.5 Known limitations (cohort pass)

- **15-year MBS excluded** (~9% of SOMA face value); different amortization schedule.
- **Maturity-string parsing** approximates true origination date (assumes 360-month term from parsed MM/YY maturity).
- **`min_share = 0.02` bucket-folding** merges tiny tails into nearest coupon bucket.
- **Mobility calibration unchanged** — still anchored at 8% rate on default cohort; not re-calibrated per coupon bucket.
- **Monte Carlo cost** — 7× surface rebuild per seed (~16 min for 50 seeds vs ~46 s single-cohort).
- **Figures in Section 19.4 comparison table predate the QT-active aggregation fix** (Section 5) and the max-weight reference-cohort calibration; see Section 17 for current headline numbers.

---

## 17. Final Numbers Table

Single source of truth for every headline figure, **current as of the correctness-fix + settlement-lag pipeline re-run (July 2026)**. Historical figures in Sections 15–19 predate the QT-window aggregation fix (Section 5).

| Metric | Value | Source |
|---|---|---|
| Empirical trapped liquidity (SOMA, phased cap, active QT window) | **$764.7B** | `print_summary()`, "Net Trapped Liquidity" |
| ABM U.S. trapped liquidity (surface + settlement lag) | **$101.2B** (13.2% of empirical) | `print_summary()`, "U.S. System Trapped Liquidity" |
| ABM U.S. trapped (surface only, no lag) | **$117.7B** (15.4%) | `compute_metrics(apply_settlement_lag_kernel=False)` |
| ABM Danish trapped liquidity (dynamic balance) | **-$829.1B** | `print_summary()`, "Danish System Trapped Liquidity" |
| Danish portfolio path | $2,535B → $428B | `print_summary()`, "Danish Portfolio" |
| Institutional gap (U.S. − Danish) | **$930.3B** | `print_summary()`, "Institutional Gap" |
| Scheduled amortization during QT | $224.1B (≈2.68% ann.) | `print_summary()`, "Sched. amortization" |
| Curtailment during QT | $69.6B (≈0.84% ann. avg SMM) | `print_summary()`, "Curtailment during QT" |
| SOMA 30yr WAC (live cohort fetch) | **2.55%** (7 buckets) | `fetch_soma_mbs_cohorts()` |
| Reference calibration cohort | **2.00%** coupon, 39.7% weight | `reference_cohort()` |
| Empirical CPR range | 0.00% - 14.02% (mean 5.53%) | `print_summary()`, "CPR DIAGNOSTIC" |
| ABM U.S. CPR range | 7.55% - 21.72% (mean 11.98%) | `print_summary()`, "CPR DIAGNOSTIC" |
| CPR goodness-of-fit (raw) | R²=-6.443, RMSE=7.73pp, MAE=6.58pp, r=-0.316 | `cpr_goodness_of_fit()` |
| CPR goodness-of-fit (smoothed) | R²=-14.464, RMSE=7.14pp, MAE=6.41pp, r=-0.397 | `cpr_goodness_of_fit()` |
| Cross-correlation (best lag) | +0.192 at lag -3 (not meaningful) | `cpr_cross_correlation()` |
| Holdout split — in-sample | R²=-10.990, RMSE=8.86pp, share=-11.1% | `print_summary()`, "Holdout split" |
| Holdout split — out-of-sample | R²=-4.222, RMSE=6.66pp, share=32.5% | `print_summary()`, "Holdout split" |
| Sensitivity sweep range (125 scenarios) | Trapped -$265.1B–$265.5B; Share -34.7%–34.7% | `sensitivity_analysis.py` |
| Robustness — data source | SOMA $764.7B vs WSHOMCB $763.7B (<0.2% diff) | `robustness_analysis.py`, Panel B |
| Robustness — cap schedule (18 scenarios) | Empirical $479.6B–$782.2B; Share -24.6%–15.2% | `robustness_analysis.py`, Panel C |
| Monte Carlo (50 population draws) | Mean $113.5B, Std $24.8B, 95% CI [$106.6B, $120.4B] | `monte_carlo_simulation.py` |
| Monte Carlo runtime (multi-cohort) | 4.6 min total (~5.5 s/seed) | `monte_carlo_simulation.py` |
| Vintage burnout (survivor selection) | **$1,123.9B** (147%) — failed pre-registration | Section 20 |
| Dynamic friction range | 8.23% - 10.26% (mean 9.05%) | `print_summary()`, "DYNAMIC MACROECONOMIC FRICTION" |

---

## 18. Known Limitations and Open Items

- **Monthly CPR path fit remains weak.** The aggregate share explained is **13.2%** (Section 17) and month-to-month R² is negative under every friction specification tested (Section 9). Settlement-lag convolution (Section 21) did not fix the cross-correlation peak.
- **The Danish counterfactual still uses U.S.-calibrated friction.** The -$829.1B / $930.3B figures (Section 17) should be read as an **upper bound** on the institutional gap under U.S.-style frictions.
- **No confidence interval on the empirical trapped-liquidity figure itself.** The Monte Carlo suite (Section 11) puts a CI on the *ABM's* prediction; the robustness suite (Section 10) shows how the *empirical* $764.7B moves under cap-schedule assumptions.
- **Vintage burnout via survivor selection failed** (Section 20) — parameter-free implementation drove QT-window CPR to ~0% and trapped liquidity to 147% of empirical (wrong direction). Production defaults use surface interpolation.
- **Behavioral extensions, curtailment, and multi-cohort composition** (Sections 15–19) are historical falsification tests; current headline numbers are in Section 17.
- **15-year MBS excluded from cohort modeling** (~9% of SOMA face value); maturity-string parsing approximates origination dates.
- **DTI constraint is front-end only.** The 43% DTI check uses only the mortgage payment, not total household debt.

---

## 20. Vintage Burnout (Survivor Selection) — Pre-Registered Test, Failed

### Mechanism

Rather than a tuned hazard-decay parameter, burnout was implemented as **survivor selection**: `HousingMarketEngine.simulate_cohort_path()` walks each cohort's historical rate path from origination; each month evaluates `_movers_mask()` on the surviving population, records CPR = movers/survivors, and permanently removes movers. US and Danish survivor sets are tracked separately. In `compute_metrics(use_burnout=True)`, per-cohort paths replace static surface interpolation for the historical window.

### Pre-registered expectations

1. Burnout lowers late-sample ABM CPR → trapped liquidity **rises** toward $764.7B.
2. Path fit (R², correlation) **improves** via monotone time-decay.

### Actual results (July 2026 re-run)

| Configuration | U.S. Trapped | Share | QT-window CPR mean |
|---|---|---|---|
| Surface baseline (no burnout) | $117.7B | 15.4% | 8.41% |
| Survivor burnout | **$1,123.9B** | **147.0%** | **~0.00%** |

**Diagnosis:** pandemic-era cohorts (2.0–2.5% coupons, 70% of weight) experience massive first-month prepayment when the path enters the 2020–21 low-rate window. Survivors after selection are exclusively **low-desire, never-movers** — an absorbing state with ~0% CPR at lock-in rates, not the calibrated 4–5% involuntary floor. The closed 10,000-agent population depletes its mobile mass before the QT window; this is a structural mismatch with a real MBS pool that retains involuntary turnover and ongoing origination.

**Production decision:** `use_burnout=False` in `fed_mbs_extension_risk.py` `main()` and all downstream scripts. Code retained for reproducibility.

---

## 21. Settlement-Lag Kernel — Pre-Registered Test, Null

### Mechanism

Household prepayment decisions and SOMA cash receipt are separated by TBA settlement + servicer remittance (UMBS ~55-day, GNMA II ~50-day standard delays). `apply_settlement_lag()` convolves `US_Simulated_Monthly_Rolloff_Billions` (and Danish, symmetrically) with a fixed mass-conserving kernel **`[0.10, 0.60, 0.30]`** over lags 0/1/2 months (documented remittance-cycle weights, not tuned).

### Pre-registered expectation

Cross-correlation peak (weak r = +0.19 at lag -3) should shift toward lag 0; monthly R² should improve.

### Actual results

| Configuration | U.S. Trapped | Share | Peak cross-corr |
|---|---|---|---|
| Surface only | $117.7B | 15.4% | +0.192 at lag -3 |
| Surface + lag kernel | **$101.2B** | **13.2%** | **+0.192 at lag -3** |

Aggregate trapped liquidity changes modestly (-$16.5B) because the kernel is mass-conserving over the full QT window; timing alignment **did not improve** (peak unchanged, R² worse: -6.443 vs -2.166 pre-lag on the earlier surface). **Conclusion:** timing lag is not the binding residual; the kernel is kept in production as a documented null result with negligible directional effect on the headline figure.
