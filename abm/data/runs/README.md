# Frozen ABM production runs

Headline dollar and CPR figures cited in `TECHNICAL.md` and the paper must match a tagged manifest here — not ad-hoc `compute_metrics()` calls with the wrong QT window filter.

## Current production tag

**`run-2026-07-04`**

```bash
cd abm
python3 freeze_run.py --tag run-2026-07-04
```

## Per-run artifacts

| File | Purpose |
|---|---|
| `manifest.json` | All headline scalars + pipeline metadata + input hashes |
| `metrics_monthly.csv` | 42-row active QT slice for audit/plots |
| `mbs_extension_risk_dashboard.png` | Copy of dashboard at freeze time |
| `cpr_diagnostic.png` | Copy of CPR diagnostic at freeze time |

`abm/data/latest_run_manifest.json` always points to the most recent freeze.

## QT window rule

Aggregations use `qt_active_frame()` — months where `QT_START <= t < QT_END` (June 2022 – November 2025, **N=42**).

**Do not** average CPR with `index >= QT_START` alone; that includes eight post-QT months (December 2025 onward) and drifts means (e.g. US 12.32% vs 11.98%, empirical 5.45% vs 5.53%).

## API

- `fed_mbs_extension_risk.export_headline_metrics(df)` — programmatic access to manifest scalars
- `fed_mbs_extension_risk.build_production_metrics()` — production data fetch + `compute_metrics()` path
