# Reduced-Form Hazard Framework (Freddie Mac Loan-Level Data)

> **Currency note (July 2026):** figures in this runbook predate the β₁ units
> fix and follow-on analyses. Path B is currently **$818.5B / 107.0%** (band
> 105.9–108.2%), Path A **$928.9B / 121.5%** (spec v4 calendar-month,
> `run-2026-07-14-pathA-seasonal`; spec v3 prior $915B / 119.7%, full-book
> variant 126.1%); the Danish regime now uses the Berger two-channel
> calibration. See the root
> [TECHNICAL.md §15–§25](../TECHNICAL.md#15-robustness-fix-program-july-2026).

Complements the archived agent-based pipeline in [`../abm/`](../abm/) with two hazard paths:

1. **Cohort fractional hazard** — loan-level → cohort-month → proportional hazards (no utility functions)
2. **Literature microsim** — 75k Freddie-sampled loan agents with competing prepay/default risks, cohort-level burnout, and U.S. vs Danish rate-gap counterfactual

## Data acquisition

1. Register (free) at [Freddie Mac Clarity Data Intelligence](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset)
2. Download the **sample dataset** or Standard Dataset for vintages **2017–2021**:
   - `orig_YYYY.txt` / `orig_YYYYQn.txt` (origination, 32 pipe-delimited columns)
   - `perf_YYYY.txt` / `perf_YYYYQn.txt` (monthly performance, 32 columns)
3. Place files in `hazard/data/raw/`

Without real files, the pipeline auto-generates a **synthetic fixture** (`orig_2020.txt` + `perf_2020.txt`, 5,000 loans) so all modules are runnable immediately.

## Compute strategy

| Stage | Rows | Method |
|---|---|---|
| Raw loan-months | Millions | Polars `scan_csv` (lazy, never materialized) |
| Cohort-month panel | ~50k–200k | Immediate `group_by` aggregation |
| Hazard fit | Same panel | Poisson GLM + log(exposure) offset (seconds) |

Covariates (RateGap, Burnout, Friction) vary at **cohort-month** level; FICO/LTV/vintage are cohort **dimensions**, not per-loan regression features.

## Architecture

### Path A — Empirical cohort hazard

```
data/raw/  →  ingest.py  →  cohort_month_panel.parquet
                ↓
         hazard_fit.py  ←  macro.py (FRED/SOMA/QT)
         markov.py
                ↓
         simulate.py  →  simulation_results.parquet
                ↓
         extension_risk.py  →  score vs $764.7B benchmark
```

### Path B — Literature microsim (competing risks)

```
data/raw/  →  loan_sample.py  →  loan_sample.parquet (stratum_id per loan)
                ↓
         microsim_engine.py  ←  literature_hazard.py (PSA h0, Rothstein β1)
                ↓              rate_gap.py (US par vs Danish market-value)
                ↓              competing_risks.py (normalized hazards + Markov)
         microsim_results.parquet
                ↓
         extension_risk.py --mode literature
                ↓
         abm/fed_mbs_extension_risk.py  (use_hazard_microsim=True bridge)
```

## Model specification

### Cohort fractional hazard (Path A)

**Discrete-time Poisson GLM** (grouped cohort-month cells, spec v3):

$$\log(h_{c,t}) = \text{spline}(\text{loan\_age}) + \beta_1 \cdot \text{RateGap\_bps}_t + \beta_2 \cdot \text{Burnout\_orth}_{c,t} + \beta_3 \cdot \text{Friction}_t + \text{FE}(\text{stratum})$$

- **RateGap_bps**: `(coupon − market_rate) × 10,000` — basis-point scaling stabilizes IRLS
- **Burnout_orth**: within-stratum demeaned cumulative prepaid share, orthogonalized on age spline (measures adverse selection within each pool over time)
- **Friction**: z-scored dynamic macro friction from FRED inventory + sentiment
- **Stratum FE**: 295 dummies for 4-way cross-sections `(vintage, coupon, fico_bucket, ltv_bucket)` — absorbs baseline pool "fastness"; reference stratum = lexicographic min
- **Ridge**: `RIDGE_ALPHA=1e-5` (IRLS ill-conditioned with 295 FE); grid `[1e-5, 1e-4]` on holdout RMSE

`predict_hazard` accepts `rate_gap` in **decimal** (callers unchanged) and converts internally to bps.

**Markov servicer pipeline** replaces the ABM's `[0.10, 0.60, 0.30]` convolution kernel:

`Current → D30 → D60 → D90+ → Forbearance → Defaulted → Liquidated` (+ absorbing `Prepaid`)

Fractional prepay in `simulate.py` routes directly to SOMA roll-off (no settlement-lag convolution in the hazard path).

### Literature microsim (Path B)

**Agent state:** `MortgageAgent` backed by vectorized `MicrosimPool` (75k loans sampled from Freddie ingest with `stratum_id`).

**Prepay hazard:**

$$h_i^{prep}(t) = h_0(t) \cdot \exp\big(\beta_1 \Delta r_i(t) + \mathbf{\beta}_x^\top X_i + \beta_b \cdot \text{burnout}_{s(i)}\big)$$

**Default hazard (competing risk):**

$$h_i^{def}(t) = h_0^{def} \cdot \exp\big(\gamma_1 \cdot \text{rate\_stress}_i + \mathbf{\gamma}_x^\top X_i\big)$$

**Burnout is cohort-level only:** `cohort_burnout[stratum_id]` accumulates monthly stratum CPR; broadcast to all active agents in that stratum before each month's hazard evaluation. Individual loans prepay entirely (absorbing) or stay active — no per-loan fractional burnout.

**Rothstein β₁ conversion (not ÷3):** quarterly mobility probability \(P_q\) maps to monthly hazard via constant-hazard compounding:

$$h_m = 1 - (1 - P_q)^{1/3}$$

For a 100bp rate-gap shock reducing \(P_q\) by 6.5%:

$$\beta_1 = \ln\left(\frac{h_{m,\text{shocked}}}{h_{m,\text{baseline}}}\right)$$

Implemented in `literature_hazard.py` with sensitivity band 5.5%–7.7%.

**Competing risks:** single uniform draw per agent per month; hazards normalized row-wise when \(h_{prep} + h_{def} > 1\).

**Danish counterfactual:** identical \(h_0\), \(\beta_1\), \(X_i\), and draw logic — only `rate_gap_danish()` swaps (market-value PV gap vs U.S. par-payoff gap).

## Run

```bash
pip install -r ../requirements.txt
export FRED_API_KEY="your_key"

cd hazard
python3 extension_risk.py                      # Path A: empirical cohort pipeline
python3 extension_risk.py --mode literature    # Path B: literature microsim
```

Literature microsim step-by-step:

```bash
python3 loan_sample.py          # 75k stratified sample with stratum_id
python3 microsim_engine.py      # US + Danish QT walk
python3 extension_risk.py --mode literature
```

Bridge into ABM macro pipeline:

```python
# abm/fed_mbs_extension_risk.py
df = compute_metrics(df, use_hazard_microsim=True)  # skips settlement-lag kernel (Markov routing)
```

Path A individual modules:

```bash
python3 ingest.py
python3 hazard_fit.py
python3 markov.py
python3 simulate.py
```

## Outputs

| File | Description |
|---|---|
| `data/cohort_month_panel.parquet` | Aggregated cohort-month cells |
| `data/hazard_coefficients.json` | Fitted β coefficients (spec v3: stratum FE, scaling metadata) |
| `data/markov_transition_matrix.parquet` | Servicer state transitions |
| `data/simulation_results.parquet` | QT-window simulated roll-off |
| `data/extension_risk_results.json` | Headline trapped-liquidity score |
| `data/extension_risk_dashboard.png` | Extension delta + CPR charts |
| `data/microsim_results.parquet` | Literature microsim QT paths (US + Danish) |
| `data/loan_sample.parquet` | Stratified 75k loan sample with `stratum_id` |
| `data/marginal_decomposition_results.json` | Round-15 Q3 marginal decomposition (liveness-gated) |
| `data/ginnie_cpr_overlay_results.json` | Round-15 Q2 Ginnie overlay + `gmar_dec25_cpr_series.json` provenance (liveness-gated) |
| `data/expectation_benchmark_results.json` | Q10 expectations benchmark (liveness-gated) |

## CPR timing and SOMA settlement

Freddie Mac `prepaid_upb` records the **economic prepayment month** (loan-level voluntary payoff). NY Fed SOMA `Actual_Monthly_Rolloff` records **settled cash** (current face value registered on the Fed's balance sheet). These are not contemporaneous:

1. **TBA forward market** — MBS pools are allocated ~2 business days before settlement; standard UMBS/GNMA remittance cycles run **45–55 days** from loan closing to investor cash receipt.
2. **Hazard path** — voluntary prepay in `simulate.py` and literature `competing_risks.py` settles to SOMA in the **same month** as the hazard draw (no pipeline delay by design).
3. **ABM path** — tested a `[0.10, 0.60, 0.30]` settlement kernel; **null for timing** ([TECHNICAL.md Appendix B.8](../TECHNICAL.md#b8-settlement-lag-kernel--pre-registered-null)).

### Primary timing diagnostic: peak cross-correlation lag (pre-β₁-fix / spec v3, historical; production values in TECHNICAL.md §12)

| Path | CPR r (lag 0) | Peak lag | Peak r |
|---|---|---|---|
| Literature microsim | +0.368 | **−3 months** | **+0.444** |
| Empirical cohort GLM (spec v3) | −0.444 | 0 | −0.444 |

**Interpretation (corrected in the v15 referee round — see [TECHNICAL.md §22.3b](../TECHNICAL.md#22-manuscript-verification-record-referee-rounds-july-2026)):** under the implemented convention, a peak at lag −3 means the **empirical path leads and the simulated path trails** — a synthetic-data test of `cpr_cross_correlation` proved the direction. The earlier settlement-pipeline reading (sim leads SOMA by the TBA delay) had the two series interchanged and is **retracted**; the β₁=0 null shares the −3 peak and the peak correlation is not distinguishable from zero under block-bootstrap bands, so no timing credential attaches to any estimator.

The empirical cohort path shows wrong-sign contemporaneous correlation (lag 0). This likely reflects GLM misspecification at same-month alignment, **not** a timing failure to fix with month-lag GLM terms.

`extension_risk.py` writes `lag_interpretation` and `peak_lag_r` to JSON and prints both lag-0 and peak-lag correlations.

## Pre-β₁-fix results (Freddie Mac 2017–2021, 20 quarters — historical; superseded, see currency note)

| Path | Trapped | Share | β(rate_gap) | β(burnout) | β(friction) |
|---|---|---|---|---|---|
| **Literature microsim** | $747B | **97.7%** | Rothstein band | −0.5 (prior) | — |
| **Empirical cohort GLM** | $915B | **119.7%** | +0.67 (OK) | **−0.13 (OK)** | −0.037 (OK) |

All three pre-registered coefficient signs pass on the empirical path after **spec v3** (stratum FE + within-stratum demeaned burnout). Vintage-year FE (spec v2) left burnout positive (+0.76); tightening FE to 295 four-way strata fixed the sign.

**Spec evolution:** v1 (decimal rate gap, unstable β≈40) → v2 (bps scaling + vintage FE) → v3 (stratum FE + demeaned burnout + mild Ridge α=1e-5–1e-4) → **v4** (v3 + eleven calendar-month seasonal dummies; production since the 2026-07-14 freeze — [TECHNICAL.md §22.5](../TECHNICAL.md#225-pre-submission-freeze-execution-2026-07-14-path-a-spec-v4-adoption-and-restatement)). The §"Model specification" formula above describes v3; the ridge is a numerical no-op at production magnitudes (manuscript App. C).

## Pre-registered expectations

| Hypothesis | Expected sign | Empirical (spec v3) | ABM benchmark |
|---|---|---|---|
| β₁ (RateGap) | > 0 | **+0.67 OK** | — |
| β₂ (Burnout) | < 0 | **−0.13 OK** | — |
| β₃ (Friction) | < 0 | **−0.037 OK** | — |
| Monthly CPR path R² | Beat ABM | R² = −1.11, r = −0.44 | R² = −6.44, r = −0.32 |
| Share explained | Exceed ABM | **119.7%** | 13.2% |

**Synthetic fixture:** auto-generated when `data/raw/` is empty (5,000 loans). Results on the fixture are not meaningful for hypothesis testing. The headline numbers above use real Freddie Mac 2017–2021 quarterly files in `data/raw/`.

## Modules

| File | Purpose |
|---|---|
| `config.py` | Paths, cohort buckets, QT constants |
| `schema.py` | Freddie origination/performance column layouts |
| `macro.py` | FRED/SOMA fetch, QT cap, friction, CPR diagnostics |
| `ingest.py` | Polars lazy scan → cohort-month panel |
| `stratum.py` | 4-way stratum_id helper (`vintage_couponBps_fico_ltv`) |
| `hazard_fit.py` | Poisson GLM (bps rate gap, stratum FE, mild Ridge) |
| `markov.py` | Servicer transition matrix |
| `simulate.py` | Fractional-cohort forward simulation |
| `loan_sample.py` | Stratified Freddie loan sample for microsim |
| `agents.py` | `MortgageAgent` + vectorized `MicrosimPool` |
| `literature_hazard.py` | PSA \(h_0\), Rothstein β₁ survival conversion, default γ |
| `rate_gap.py` | U.S. par vs Danish market-value rate gap |
| `competing_risks.py` | Monthly competing-risks step + cohort burnout update |
| `microsim_engine.py` | Dual-regime QT forward walk |
| `extension_risk.py` | End-to-end pipeline + scoring (`--mode literature`) |
| `marginal_decomposition.py` | Round-15 Q3: lock-in marginal decomposed by vintage × coupon cell (group ablation, per-loan β₁ vector) |
| `ginnie_cpr_overlay.py` | Round-15 Q2: published-CPR Ginnie composition overlay (GMAR Dec-2025 series) |
| `expectation_benchmark.py` | Q10: NY Fed ex-ante projection benchmark (OMO-2021 Chart 34) |
