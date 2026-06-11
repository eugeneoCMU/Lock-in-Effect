# Lock-in-Effect

Quantitative analyses of the mortgage "lock-in effect" under the high-interest-rate regime, from two angles:

1. **Empirical (FRED data)** — `fed_mbs_extension_risk.py` measures how rising mortgage rates have slowed prepayments, causing the Fed's Mortgage-Backed Securities to "lock in" well beyond the Quantitative Tightening (QT) roll-off targets.
2. **Agent-Based Model (simulation)** — `abm_lockin_simulation.py` simulates 10,000 rational households deciding whether to move under an interest-rate shock, comparing U.S. vs. Danish mortgage payoff rules.

## Quick Start

```bash
pip install -r requirements.txt
```

### Empirical analysis (FRED)

Set your FRED API key in `fed_mbs_extension_risk.py` (replace `YOUR_FRED_API_KEY`), then run:

```bash
python fed_mbs_extension_risk.py
```

The script will:
1. Pull weekly Fed MBS holdings and 30-year mortgage rate data from FRED (resampled to monthly frequency).
2. Compute the monthly roll-off pace, extension delta vs. the $35B QT target, and cumulative trapped liquidity.
3. Generate a three-panel dashboard saved to `mbs_extension_risk_dashboard.png`.
4. Print aggregate summary statistics to the console.

### Agent-based simulation (no API key required)

```bash
python abm_lockin_simulation.py
```

The simulation:
1. Generates 10,000 heterogeneous households, all locked into 3.0% 30-year mortgages.
2. Sweeps market rates from 2.0% to 8.0% (0.5% steps). At each rate, every household decides to move or stay under two payoff regimes:
   - **U.S. rule** — the mortgage must be paid off at par (outstanding principal), so a below-market mortgage is a golden handcuff.
   - **Danish rule** — the debt can be bought back at market price (PV of remaining cash flows at the current rate, capped at par), releasing the lock-in when rates rise.
3. Records the Conditional Prepayment Rate (CPR) for each system at every rate step.
4. Outputs a results table (`abm_lockin_results.csv`) and an S-curve chart (`abm_lockin_scurve.png`).

Expected result: the U.S. mobility curve collapses toward 0% as rates rise (lock-in), while the Danish curve flattens out at a steady natural-turnover baseline.

## Dependencies

- Python 3.9+
- pandas, numpy, matplotlib, fredapi (see `requirements.txt`)
- A free FRED API key from https://fred.stlouisfed.org/docs/api/api_key.html
