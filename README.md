# Lock-In Effect

Quantitative research on mortgage lock-in, Fed MBS extension risk, and trapped liquidity during Quantitative Tightening.

> **Full technical narrative** (benchmark corrections, ABM falsifications, hazard pivot, architectural decisions): **[TECHNICAL.md](TECHNICAL.md)**

This repository hosts **two complementary frameworks**:

| Folder | Approach | Status |
| --- | --- | --- |
| [`abm/`](abm/) | Agent-based model (10,000 households) + FRED/SOMA macro pipeline + validation suite | **Complete** — see [abm/README.md](abm/README.md) and [abm/TECHNICAL.md](abm/TECHNICAL.md) |
| [`hazard/`](hazard/) | Reduced-form prepayment hazard (Freddie Mac loan-level) + literature microsim | **Implemented** — see [hazard/README.md](hazard/README.md) |

## Quick start

```bash
pip install -r requirements.txt
export FRED_API_KEY="your_key"

# ABM pipeline
python3 abm/abm_lockin_simulation.py
python3 abm/fed_mbs_extension_risk.py
python3 abm/freeze_run.py --tag run-2026-07-04   # frozen manifest for docs/paper

# Hazard framework (cohort hazard)
python3 hazard/extension_risk.py

# Hazard framework (literature microsim)
python3 hazard/extension_risk.py --mode literature
```

## Layout

```
Lock-in-Effect/
├── README.md              # quick start and index
├── TECHNICAL.md           # full project technical narrative
├── requirements.txt
├── abm/                   # agent-based lock-in pipeline (scripts, outputs, docs)
│   ├── README.md
│   ├── TECHNICAL.md
│   ├── paths.py           # anchored output paths
│   └── *.py, *.csv, *.png
└── hazard/                # reduced-form hazard framework
    ├── README.md
    ├── extension_risk.py  # end-to-end pipeline entry point
    ├── ingest.py, hazard_fit.py, stratum.py, simulate.py, macro.py
    └── data/              # panel, coefficients, results (raw/ gitignored)
```

## Headline results (current)

See [TECHNICAL.md §12](TECHNICAL.md#12-current-headline-numbers) for the full table across all frameworks.

| Framework | Trapped | Share of $764.7B |
|---|---|---|
| **Empirical benchmark** (SOMA) | $764.7B | 100% |
| **ABM** (surface + settlement lag) | $101.2B | 13.2% |
| **Hazard Path B** (literature microsim) | $747B | **97.7%** |
| **Hazard Path A** (empirical cohort GLM, spec v3) | $915B | 119.7% |

The reduced-form hazard framework in `hazard/` addresses path-dependence, competing risks, and loan-level heterogeneity that the static CPR surface cannot capture. Literature microsim lands near the empirical benchmark without fitting to it; the empirical GLM passes all pre-registered coefficient sign checks after stratum-level fixed effects. See [TECHNICAL.md §9–§11](TECHNICAL.md#9-pivot-to-the-hazard-framework).
