# Lock-In Effect

Quantitative research on mortgage lock-in, Fed MBS extension risk, and trapped liquidity during Quantitative Tightening.

> **Full technical narrative** (benchmark corrections, ABM falsifications, hazard pivot, architectural decisions): **[TECHNICAL.md](TECHNICAL.md)**

This repository hosts **two complementary frameworks**:

| Folder | Approach | Status |
| --- | --- | --- |
| [`abm/`](abm/) | Agent-based model (10,000 households) + FRED/SOMA macro pipeline + validation suite | **Complete** — see [abm/README.md](abm/README.md) and [TECHNICAL.md Appendix B](TECHNICAL.md#appendix-b--abm-era-granular-archaeology) |
| [`hazard/`](hazard/) | Reduced-form prepayment hazard (Freddie Mac loan-level) + literature microsim | **Implemented** — see [hazard/README.md](hazard/README.md) |

## Quick start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up FRED API (for macroeconomic data)
```bash
export FRED_API_KEY="your_key"
# Or add to .env: FRED_API_KEY=your_fred_api_key_here
# Get a free key: https://fred.stlouisfed.org/docs/api/api_key.html
```

### 3. Set up Google Drive (for Freddie Mac & SOMA data)
If using Freddie Mac loan-level or SOMA data from Google Drive:

1. **Get a Google Drive API key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a project or select an existing one
   - Go to **APIs & Services** → **Credentials**
   - Click **+ Create Credentials** → **API Key**
   - Enable the **Google Drive API** for your project

2. **Configure credentials:**
   - Copy `.env.example` to `.env`
   - Set `GOOGLE_DRIVE_API_KEY` to your API key
   - Set `DATA_FOLDER_ID` to your Google Drive folder ID (from the folder URL: `https://drive.google.com/drive/folders/{FOLDER_ID}`)

### 4. Run pipelines

```bash
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

**Note:** If Freddie Mac files are not found locally, they will be automatically downloaded from Google Drive on first use. Subsequent runs use the cached copies. To force a fresh download, run with the environment variable `FORCE_REFRESH=1` or manually clear the cache in `./data/cache/`.

## Layout

```
Lock-in-Effect/
├── README.md              # quick start and index
├── TECHNICAL.md           # full project technical narrative
├── requirements.txt
├── abm/                   # agent-based lock-in pipeline (scripts, outputs, docs)
│   ├── README.md
│   ├── paths.py           # anchored output paths
│   └── *.py, *.csv, *.png
├── hazard/                # reduced-form hazard framework
│   ├── README.md
│   ├── extension_risk.py  # end-to-end pipeline entry point
│   ├── ingest.py, hazard_fit.py, stratum.py, simulate.py, macro.py
│   └── data/              # panel, coefficients, results (raw/ gitignored)
├── common/                # shared calibration + Fannie ingestion helpers
├── figures/               # gated publication figures (artifact-fed)
├── tools/                 # liveness_gates.py (33 manuscript-vs-artifact
│                          # gates), timing_sweep.py (+ golden-fixture test)
└── tests/                 # unit tests + frozen-run golden fixtures
```

## Headline results (current, post §15–§25 robustness and referee-round program)

See [TECHNICAL.md §12](TECHNICAL.md#12-current-headline-numbers) for the full table and [§15–§25](TECHNICAL.md#15-robustness-fix-program-july-2026) for what changed and why (referee rounds 13–15 and the expectations benchmark are §23–§25).

| Framework | Trapped | Share of $764.7B |
|---|---|---|
| **Empirical benchmark** (SOMA) | $764.7B | 100% |
| **ABM** (native 15yr gate, `run-2026-07-05-berger`) | $84.5B | 11.1% |
| **Hazard Path B** (literature microsim, post-β₁-fix) | $818.5B | **107.0%** (band 105.9–108.2%) |
| **Hazard Path A** (empirical cohort GLM, spec v4 calendar-month, `run-2026-07-14-pathA-seasonal`) | $928.9B | 121.5% (spec v3 prior: $915B / 119.7%) |

Key follow-on findings (§16–§25): Path B's recovery is a **marginal-distribution result** (permutation p=0.001, effect only 0.27%) and holds at **106.0% on a fully synthetic population** — the survival structure, not the Freddie data, recovers the benchmark; the ABM needs real covariates to reach even 59.3%. The **Danish institutional gap collapses to ≈0** once Berger et al.'s estimated elasticities replace the U.S.-extrapolated mobility function (+$925.5B → −$99.9B, sign not robust). See [TECHNICAL.md §16–§20.1](TECHNICAL.md#16-permutation-test--does-path-b-depend-on-joint-covariate-structure).
