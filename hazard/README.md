# Reduced-Form Hazard Framework (Freddie Mac Loan-Level Data)

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
| Hazard fit | Same panel | WLS logit with exposure weights (seconds) |

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

**Discrete-time logistic hazard** (grouped cohort-month cells):

$$\text{logit}(h_{c,t}) = \text{spline}(\text{loan\_age}) + \beta_1 \cdot \text{RateGap}_t + \beta_2 \cdot \text{Burnout}_{c,t} + \beta_3 \cdot \text{Friction}_t$$

- **RateGap**: cohort coupon − market rate (financial incentive)
- **Burnout**: cumulative voluntary prepaid share of cohort original balance (dynamic state — fixes ABM survivor-selection failure, see [`../abm/TECHNICAL.md` §20](../abm/TECHNICAL.md))
- **Friction**: dynamic macro friction from FRED inventory + sentiment

**Markov servicer pipeline** replaces the ABM's `[0.10, 0.60, 0.30]` convolution kernel:

`Current → D30 → D60 → D90+ → Forbearance → Defaulted → Liquidated` (+ absorbing `Prepaid`)

Cash reaches SOMA only from `Prepaid` / `Liquidated` absorbing states.

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
| `data/hazard_coefficients.json` | Fitted β coefficients |
| `data/markov_transition_matrix.parquet` | Servicer state transitions |
| `data/simulation_results.parquet` | QT-window simulated roll-off |
| `data/extension_risk_results.json` | Headline trapped-liquidity score |
| `data/extension_risk_dashboard.png` | Extension delta + CPR charts |
| `data/microsim_results.parquet` | Literature microsim QT paths (US + Danish) |
| `data/loan_sample.parquet` | Stratified 75k loan sample with `stratum_id` |

## Pre-registered expectations (before fitting on real data)

| Hypothesis | Expected sign | ABM benchmark |
|---|---|---|
| β₁ (RateGap) | > 0 | — |
| β₂ (Burnout) | < 0 | — |
| β₃ (Friction) | < 0 | — |
| Monthly CPR path R² | Beat ABM | R² = −6.44, r = −0.32 |
| Share explained | Exceed ABM | 13.2% |

**Note:** Results on the synthetic fixture are **not** meaningful for hypothesis testing — coefficients and trapped-liquidity shares reflect fixture limitations, not model failure. Re-run after placing real Freddie Mac files in `data/raw/`.

**Literature microsim on synthetic fixture:** over-predicts CPR (~50% vs empirical ~5.5%) because the 5k-loan fixture lacks real rate-lock heterogeneity; the pipeline is structurally correct and runs in ~15s on 75k agents.

## Modules

| File | Purpose |
|---|---|
| `config.py` | Paths, cohort buckets, QT constants |
| `schema.py` | Freddie origination/performance column layouts |
| `macro.py` | FRED/SOMA fetch, QT cap, friction, CPR diagnostics |
| `ingest.py` | Polars lazy scan → cohort-month panel |
| `hazard_fit.py` | WLS logit hazard estimation |
| `markov.py` | Servicer transition matrix |
| `simulate.py` | Fractional-cohort forward simulation |
| `loan_sample.py` | Stratified Freddie loan sample for microsim |
| `agents.py` | `MortgageAgent` + vectorized `MicrosimPool` |
| `literature_hazard.py` | PSA \(h_0\), Rothstein β₁ survival conversion, default γ |
| `rate_gap.py` | U.S. par vs Danish market-value rate gap |
| `competing_risks.py` | Monthly competing-risks step + cohort burnout update |
| `microsim_engine.py` | Dual-regime QT forward walk |
| `extension_risk.py` | End-to-end pipeline + scoring (`--mode literature`) |
