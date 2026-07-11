# Figures

Publication figures for the lock-in paper, generated entirely from committed
result artifacts — no live data fetch needed. Regenerate with:

```bash
python3 figures/make_figures.py
```

Style: Okabe-Ito colorblind-safe palette; paradigms are color-coded throughout
(vermillion = household choice / ABM, blue = loan-level survival / hazard,
purple = cross-design hybrids).

| File | What it shows | Data source |
|---|---|---|
| `fig1_recovery_by_estimator.png` | Benchmark recovery (% of $764.7B) per estimator, dot plot with 100% reference line, on the shared accounting basis. Paradigm colors only — marker-fill semantics were removed in the v15 round; lag-0 correlations are reference-only ([TECHNICAL.md §22.3b](../TECHNICAL.md#22-manuscript-verification-record-referee-rounds-july-2026)). | run manifests, `extension_risk_results_*.json`, `cross_design_results.json`, `synthetic_companion_results.json` |
| `fig2_ccf.png` | Cross-correlation functions, lags −6…+6, all three estimators. Under the corrected convention (§22.3b), the −3/−4 peaks mean the simulated paths **trail** the empirical series; no estimator shows positive contemporaneous alignment, and the peaks are not distinguishable from zero under block-bootstrap bands. | `ccf_data.json` (see below) |
| `fig3_abm_waterfall.png` | ABM falsification bridge: rational baseline 71.1% → behavioral gates 54.9% → curtailment 45.1% → multi-vintage 33.7% → 15yr fold-in 11.9% → production (native gate) 11.1%. Every pre-registered extension moves away from 100%. | stage levels 71.1/54.9/45.1/33.7 as supplied from the paper's falsification table; final two stages from `run-2026-07-04-15yr-foldin` / `run-2026-07-05-berger` manifests |
| `fig4_institutional_gap_sensitivity.png` | Institutional gap vs assumed U.S.-transplant refi-in-place CPR (0–18%), zero line, breakevens (ABM 12.6%, Path B 1.4%), Berger best-estimate ≈0 marked. The "sign is fragile, magnitude is not" chart (§20.1). | `abm/data/refi_sweep_results.json` |
| `fig5_cross_design.png` | Cross-design variants as paired panels: (a) level recovery with the pre-registered 50% threshold and 10–35% synthetic band; (b) lag-0 path correlation — **all negative**, so 59.3% cannot be read as "the ABM basically works" (§VIII.D). | `abm/data/cross_design_results.json` (synthetic control at its contemporaneous 11.9% baseline) |
| `fig6_elasticity_band.png` | Path B trapped liquidity across the Liebersohn–Rothstein P_q band (5.5–7.7%), central 6.5% marked, benchmark line. | `hazard/data/extension_risk_band_literature.json` |
| `fig7_architecture.png` | One-panel roadmap: data sources → three estimators → shared macro accounting → $764.7B benchmark, with the two robustness cross-links (cross-design §15, symmetric companion §18). | schematic (numbers from §12) |

## `ccf_data.json`

±6-lag cross-correlations recomputed once from committed artifacts (stored
result JSONs only cover ±3; their overlapping values match exactly):

- ABM: `abm/data/runs/run-2026-07-05-berger/metrics_monthly.csv`
  (`Empirical_CPR_Pct` vs `US_CPR_Pct`)
- Path A / Path B: `hazard/data/simulation_results.parquet` /
  `hazard/data/microsim_results.parquet` against the hazard scorer's own
  empirical series (`macro.build_empirical_metrics`), 42-month QT window,
  `cpr_cross_correlation(max_lag=6)`

Sign convention (corrected in the v15 referee round, [TECHNICAL.md §22.3b](../TECHNICAL.md#22-manuscript-verification-record-referee-rounds-july-2026)): a peak at negative lag means the **empirical series leads and the model CPR trails** under the implemented `cpr_cross_correlation` convention.

## Numbers cited (for cross-checking against TECHNICAL.md)

- Benchmark: $764.7B (§12) · ABM production: $84.5B / 11.1%, r₀ = −0.315
  (`run-2026-07-05-berger`)
- Path A: $915.1B / 119.7%, r₀ = −0.444 · Path B: $818.5B / 107.0%, r₀ = +0.190,
  band $810–828B (§15 Fix 3)
- Cross-design: 59.3% (recal., r₀ = −0.336) / 20.9% (frozen, r₀ = −0.311) vs
  11.9% contemporaneous control (§15 Fix 1)
- Synthetic companion Path B: 106.0%, r₀ = −0.063 (§18)
- Refi sweep: breakeven ABM 12.6%, Path B 1.4% (§20.1)
