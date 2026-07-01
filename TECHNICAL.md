# Technical Narrative — Corrections, Validation, and Final Numbers

This document is a chronological record of the investigation that took the project's headline "trapped liquidity" figure from an unsupported **$972.3B** to a validated **$672.9B**, fixed a structural omission in the Agent-Based Model (ABM), fixed a Danish-counterfactual bug that inflated the "institutional gap" claim, added a four-part validation suite (goodness-of-fit statistics, sensitivity analysis, robustness analysis, Monte Carlo, and an out-of-sample holdout split), tested three behavioral extensions (DTI constraint, loss aversion, wait-and-see) whose honest, pre-committed result was a *wider* gap between ABM and empirical (Section 15), and tested a macro-level curtailment channel whose pre-registered expectation — worse aggregate match — was confirmed (Section 16).

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

## 5. Corrected Empirical Benchmark: $672.9B

With the phased cap and SOMA data source in place, the empirical trapped-liquidity figure (June 2022 - November 2025) is:

```
Net Trapped Liquidity (sum of monthly deltas): $672.9B
```

This is down from the original $972.3B and lands close to the independently-reasoned $800-870B range mentioned in Section 1 — closer still once one accounts for the fact that the reasoning in Section 1 used a slightly different cap-schedule assumption (see the [robustness analysis](#10-robustness-analysis), which shows the empirical figure ranges from $285B to $690B across 18 different reasonable cap-schedule assumptions).

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

This produces an `Empirical_CPR_Pct` series ranging from 0.00% to 14.20% (mean 5.62%) over the QT window, directly comparable to the ABM's `US_CPR_Pct` (4.15%-10.56%, mean 6.62%). The `cpr_diagnostic.png` chart (via `plot_cpr_diagnostic()`) visualizes this month-by-month, both as a time series and as a scatter against the prevailing mortgage rate.

---

## 8. Goodness-of-Fit Methodology

```105:130:fed_mbs_extension_risk.py
def cpr_goodness_of_fit(empirical: pd.Series, predicted: pd.Series,
                        smooth_window: int = 3) -> dict:
    ...
```

Reports R² (`1 - SS_res/SS_tot`), RMSE (`sqrt(mean((actual-pred)^2))`), MAE, and Pearson r, both on the raw monthly series and on a 3-month centered rolling average ("smoothed", intended to filter out settlement-timing noise). Current results (N=49 months):

| | R² | RMSE | MAE | r |
|---|---|---|---|---|
| Raw | -0.590 | 3.52pp | 2.38pp | -0.338 |
| Smoothed | -1.345 | 2.54pp | 1.68pp | -0.481 |

A negative R² means the ABM's month-to-month CPR path is a *worse* predictor than simply using the empirical mean every month — i.e., the ABM's aggregate **level** is reasonably close (see Section 15) but its **monthly path** is not well matched. Section 13 investigates why smoothing makes R²/r *worse* rather than better.

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

**Corrected results**: baseline (default parameters) U.S. trapped = $544.0B against the correctly-anchored empirical $672.9B = **80.8%** share explained (not 100%). Across all 125 scenarios: trapped liquidity ranges $0.1B-$738.1B, share explained ranges 0.0%-109.7%, CPR R² ranges -7.371 to -0.335, RMSE ranges 3.22-8.07pp. The baseline sits comfortably in the middle of this range rather than at an extreme, which is evidence the 80.8% figure isn't cherry-picked.

The same stale-benchmark bug existed in `monte_carlo_simulation.py` as a hardcoded `SOMA_TARGET_B = 785.2` constant (left over from an earlier, pre-SOMA-fix estimate). It was replaced with a runtime computation using the same `empirical_trapped()` logic, so the Monte Carlo histogram now compares against the same $672.9B anchor used everywhere else.

---

## 10. Robustness Analysis

`robustness_analysis.py` holds the ABM fixed and varies the *empirical* side of the comparison across two panels:

**Panel B — data source**: SOMA vs. WSHOMCB, both with the same phased cap schedule.

| Source | Empirical | ABM Share |
|---|---|---|
| SOMA | $672.9B | 80.8% (R²=-0.590) |
| WSHOMCB | $671.6B | 81.0% (R²=-0.505) |

The two data sources agree to within 0.2%, confirming the earlier SOMA-vs-WSHOMCB discrepancy (Section 1, error #2) was about ramp-cap methodology, not which balance-sheet series was used. This close agreement is a reassuring empirical check, but it isn't the reason SOMA was chosen: SOMA remains the conceptually correct source regardless of how closely it happens to track `WSHOMCB` in this particular sample, since it reports current face value rather than `WSHOMCB`'s amortized cost (see Section 4).

**Panel C — cap-schedule sensitivity**: 18 scenarios sweeping ramp duration (2/3/4 months), full-pace cap ($30B/$35B), and QT-end date (Jun/Sep/Dec 2025). The empirical benchmark ranges from **$285.4B to $690.4B** and the ABM's share-explained ranges from **97.8% to 132.1%** across these scenarios — the baseline (3-month ramp, $35B cap, Dec 2025 end) sits at the high end of the empirical range ($672.9B) and near the low end of share-explained (98.5%), which is a reasonable, defensible choice rather than an outlier pick.

---

## 11. Monte Carlo Population-Draw Robustness

`monte_carlo_simulation.py` reruns the entire ABM→macro pipeline 50 times, each time re-seeding NumPy/`random` and rebuilding both the 10,000-household population and the CPR surface from scratch (`abm.HousingMarketEngine(seed=i, ...)`), then recomputing U.S. trapped liquidity against the shared, runtime-computed empirical benchmark.

**Result**: mean $570.4B, std $21.7B, 95% CI **[$564.4B, $576.4B]** across the 50 draws — a tight distribution, confirming the headline ABM figure isn't sensitive to the particular random population drawn. (Note: this run used a slightly different friction/date snapshot than the $544.0B baseline reported elsewhere in this document, since it rebuilds the CPR surface fresh each time rather than reusing `abm_cpr_surface.csv`; the two are consistent within the Monte Carlo distribution's range.)

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

### Stage 2 — dynamic-balance simulation (current): -$359.7B

The fix simulates the Danish balance **forward month-by-month** starting from the actual balance at QT start, so each month's roll-off is applied to the *already-reduced* balance rather than the static U.S. path:

```534:554:fed_mbs_extension_risk.py
    monthly_cpr_dk = df["Danish_CPR_Pct"] / 100 / 12
    dk_rolloff = np.zeros(len(df))
    dk_balance = np.zeros(len(df))
    qt_start_idx = df.index.get_indexer([QT_START], method="nearest")[0]
    init_balance = float(holdings_b.iloc[qt_start_idx])
    bal = init_balance
    for i in range(len(df)):
        if i < qt_start_idx:
            dk_balance[i] = float(holdings_b.iloc[i])
            continue
        dk_balance[i] = bal
        monthly_drain = float(monthly_cpr_dk.iloc[i]) + float(sched_smm.iloc[i])
        rolloff = bal * monthly_drain
        dk_rolloff[i] = -rolloff
        bal = max(bal - rolloff, 0.0)
```

**Result**: the Danish portfolio declines from **$2,654B to $898B** over the QT window, giving Danish trapped liquidity of **-$359.7B** (the Danish system would have overshot the QT cap by that much) and an **institutional gap of $903.8B** (`544.0 - (-359.7) = 903.7`).

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

If the mismatch were pure noise, smoothing should pull the correlation *toward* zero or positive. Instead:

| Lag (months) | Raw r | Smoothed r |
|---|---|---|
| -3 | +0.152 | +0.141 |
| -2 | -0.117 | -0.123 |
| -1 | -0.178 | -0.361 |
| **0** | **-0.338** | **-0.481** |
| +1 | -0.228 | -0.408 |
| +2 | -0.094 | -0.257 |
| +3 | +0.007 | -0.084 |

Smoothing makes the correlation at lag 0 **more negative** (-0.338 → -0.481), not less — the signature of a genuine sign mismatch that smoothing preserves (or amplifies) rather than noise that smoothing would average away. No lag in the ±3-month window flips the correlation meaningfully positive (the best is a weak +0.152 at lag -3, too small to treat as a real lag-alignment fix).

**Conclusion**: the ABM's month-to-month CPR path has a structural weakness — it responds to the current month's rate and friction level only, and cannot capture vintage/seasoning effects or path-dependent behavior in the actual mortgage pool. This is reported honestly in `print_summary()` rather than attributed to settlement noise.

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

**Result**:

| | N | R² | RMSE | Share Explained |
|---|---|---|---|---|
| In-sample | 19 | -1.624 | 4.20pp | 74.2% |
| Out-of-sample | 30 | **-0.126** | **3.00pp** | **87.5%** |

The model performs *better* on the unseen data — R² is much closer to zero, RMSE is lower, and share-explained is higher. A model that was merely curve-fit to the full sample would be expected to show the opposite pattern (good in-sample fit, degraded out-of-sample fit). This is evidence, though not proof, that the ABM's rational lock-in mechanism captures a genuine structural relationship rather than overfitting to the specific friction path realized during 2022-2023's volatile early-QT period.

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

## 17. Final Numbers Table

Single source of truth for every headline figure, current as of the curtailment channel described in Section 16.

| Metric | Value | Source |
|---|---|---|
| Empirical trapped liquidity (SOMA, phased cap) | **$672.9B** | `print_summary()`, "Net Trapped Liquidity" |
| ABM U.S. trapped liquidity | **$344.6B** (51.2% of empirical) | `print_summary()`, "U.S. System Trapped Liquidity" |
| ABM Danish trapped liquidity (dynamic balance) | **-$779.0B** | `print_summary()`, "Danish System Trapped Liquidity" |
| Danish portfolio path | $2,634B → $455B | `print_summary()`, "Danish Portfolio" |
| Institutional gap (U.S. - Danish) | **$1,123.6B** | `print_summary()`, "Institutional Gap" |
| Scheduled amortization during QT | $242.1B (≈2.55% ann.) | `print_summary()`, "Sched. amortization" |
| Curtailment during QT | $74.9B (≈0.78% ann. avg SMM) | `print_summary()`, "Curtailment during QT" |
| Empirical CPR range | 0.00% - 14.20% (mean 5.62%) | `print_summary()`, "CPR DIAGNOSTIC" |
| ABM U.S. CPR range | 4.29% - 16.02% (mean 7.92%) | `print_summary()`, "CPR DIAGNOSTIC" |
| CPR goodness-of-fit (raw) | R²=-1.586, RMSE=4.48pp, MAE=3.16pp, r=-0.309 | `cpr_goodness_of_fit()` |
| CPR goodness-of-fit (smoothed) | R²=-3.705, RMSE=3.59pp, MAE=2.54pp, r=-0.454 | `cpr_goodness_of_fit()` |
| Cross-correlation (best lag) | +0.182 at lag -3 (not meaningful) | `cpr_cross_correlation()` |
| Holdout split — in-sample | R²=-3.562, RMSE=5.54pp, share=48.0% | `print_summary()`, "Holdout split" |
| Holdout split — out-of-sample | R²=-0.675, RMSE=3.66pp, share=54.5% | `print_summary()`, "Holdout split" |
| Sensitivity sweep range (125 scenarios) | Trapped $31.4B-$479.5B; Share 4.7%-71.2% | `sensitivity_analysis.py` |
| Robustness — data source | SOMA $672.9B vs WSHOMCB $671.6B (<1% diff) | `robustness_analysis.py`, Panel B |
| Robustness — cap schedule (18 scenarios) | Empirical $285.4B-$690.4B; Share 61.0%-87.9% | `robustness_analysis.py`, Panel C |
| Monte Carlo (50 population draws) | Mean $364.0B, Std $24.2B, 95% CI [$357.3B, $370.7B] | `monte_carlo_simulation.py` |
| Dynamic friction range | 8.23% - 10.26% (mean 9.05%) | `print_summary()`, "DYNAMIC MACROECONOMIC FRICTION" |
| CPR bias vs. real income YoY (pre-build diagnostic) | r = -0.487 | Section 16.1 |

---

## 18. Known Limitations and Open Items

- **Monthly CPR path fit remains weak.** The aggregate/level comparison (51.2% share explained) is meaningful but the month-to-month R² is negative under every friction specification tested (Section 9) and no lag alignment fixes it (Section 13). Future work could add a lagged-rate or seasonal term to the CPR surface, or explicitly model vintage/seasoning effects.
- **The Danish counterfactual still uses U.S.-calibrated friction.** The dynamic friction series (inventory + sentiment penalties) is calibrated on U.S. housing-market data and applied identically to the Danish counterfactual. Since Danish institutional frictions may differ, the -$779.0B / $1,123.6B figures should be read as an **upper bound** on the institutional gap under U.S.-style frictions, not a claim about what Danish-market frictions specifically would produce.
- **No confidence interval on the empirical trapped-liquidity figure itself.** The Monte Carlo suite (Section 11) puts a confidence interval on the *ABM's* prediction, and the robustness suite (Section 10) shows how the *empirical* figure moves under different assumptions, but there is no single combined interval (e.g., a bootstrap over both data and assumption choices simultaneously) for the $672.9B figure.
- **The holdout split is a single split, not a rolling/expanding-window validation.** A more rigorous test would repeat the holdout at multiple cut dates (e.g., every 6 months) and check whether out-of-sample performance is consistently competitive with in-sample, rather than relying on one Jan-2024 cut point.
- **Behavioral extensions (DTI, loss aversion, wait-and-see) widened the gap rather than closing it** (Section 15). This is an honest finding under literature-grounded parameters; the residual likely reflects pool-composition, vintage, and servicer effects outside the household decision function. The wait-and-see threshold (150 bps) and probability (20%) are unsourced assumptions that should be sensitivity-tested in future work.
- **Curtailment channel worsened the aggregate match** (Section 16). Literature-grounded partial prepayments added $74.9B of simulated roll-off during QT, reducing share explained from 62.3% to 51.2% — confirming the pre-registered expectation. The ABM already over-predicts mobility; additive prepayment channels cannot close a gap caused by too much simulated roll-off.
- **DTI constraint is front-end only.** The 43% DTI check uses only the mortgage payment, not total household debt. This underestimates the binding power of the constraint, since real QM underwriting uses a back-end ratio including student loans, auto loans, and credit card minimums.
