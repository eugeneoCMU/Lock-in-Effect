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
    ├── ingest.py, hazard_fit.py, markov.py, simulate.py, macro.py
    └── data/              # panel, coefficients, results (raw/ gitignored)
```

## Headline results (current)

See [TECHNICAL.md §12](TECHNICAL.md#12-current-headline-numbers) for the full table across all frameworks. ABM summary:

- **Empirical trapped liquidity** (SOMA, active QT window): **$764.7B**
- **ABM U.S. trapped** (surface + settlement lag): **$101.2B** (13.2%)
- **Institutional gap** (U.S. vs Danish counterfactual): **$930.3B**

The reduced-form hazard framework in `hazard/` addresses path-dependence, competing risks, and loan-level heterogeneity that the static CPR surface cannot capture. See [TECHNICAL.md §9–§11](TECHNICAL.md#9-pivot-to-the-hazard-framework).
