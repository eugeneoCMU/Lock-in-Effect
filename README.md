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
python3 abm/freeze_run.py --tag <run-name>       # frozen manifest for docs/paper
                                                  # (current: run-2026-07-05-berger)

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

## Headline results (current, post §15–§20 robustness program)

See [TECHNICAL.md §12](TECHNICAL.md#12-current-headline-numbers) for the full table and [§15–§20](TECHNICAL.md#15-robustness-fix-program-july-2026) for what changed and why.

| Framework | Trapped | Share of $764.7B |
|---|---|---|
| **Empirical benchmark** (SOMA) | $764.7B | 100% |
| **ABM** (native 15yr gate, `run-2026-07-05-berger`) | $84.5B | 11.1% |
| **Hazard Path B** (literature microsim, post-β₁-fix) | $818.5B | **107.0%** (band 105.9–108.2%) |
| **Hazard Path A** (empirical cohort GLM, spec v3) | $915B | 119.7% |

Key follow-on findings (§16–§20.1): Path B's recovery is a **marginal-distribution result** (permutation p=0.001, effect only 0.27%) and holds at **106.0% on a fully synthetic population** — the survival structure, not the Freddie data, recovers the benchmark; the ABM needs real covariates to reach even 59.3%. The **Danish institutional gap collapses to ≈0** once Berger et al.'s estimated elasticities replace the U.S.-extrapolated mobility function (+$925.5B → −$99.9B, sign not robust). See [TECHNICAL.md §16–§20.1](TECHNICAL.md#16-permutation-test--does-path-b-depend-on-joint-covariate-structure).
