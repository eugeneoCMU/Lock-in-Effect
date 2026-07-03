# Lock-In Effect

Quantitative research on mortgage lock-in, Fed MBS extension risk, and trapped liquidity during Quantitative Tightening.

This repository hosts **two complementary frameworks**:

| Folder | Approach | Status |
| --- | --- | --- |
| [`abm/`](abm/) | Agent-based model (10,000 households) + FRED/SOMA macro pipeline + validation suite | **Complete** — see [abm/README.md](abm/README.md) and [abm/TECHNICAL.md](abm/TECHNICAL.md) |
| [`hazard/`](hazard/) | Reduced-form prepayment hazard model (Freddie Mac loan-level) | **Implemented** — see [hazard/README.md](hazard/README.md) |

## Quick start

```bash
pip install -r requirements.txt
export FRED_API_KEY="your_key"

# ABM pipeline
python3 abm/abm_lockin_simulation.py
python3 abm/fed_mbs_extension_risk.py

# Hazard framework (reduced-form)
python3 hazard/extension_risk.py
```

## Layout

```
Lock-in-Effect/
├── README.md              # this file
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

## Headline results (ABM, current)

See [abm/TECHNICAL.md §17](abm/TECHNICAL.md) for the full table. Summary:

- **Empirical trapped liquidity** (SOMA, active QT window): **$764.7B**
- **ABM U.S. trapped** (surface + settlement lag): **$101.2B** (13.2%)
- **Institutional gap** (U.S. vs Danish counterfactual): **$930.3B**

The reduced-form hazard framework in `hazard/` is intended to address path-dependence and vintage effects that the static CPR surface cannot capture, without the closed-population limitations of survivor-selection burnout (see [abm/TECHNICAL.md §20](abm/TECHNICAL.md)).
