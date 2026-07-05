#!/usr/bin/env python3
"""
3.2 — Shared macro-accounting layer with the hazard microsim substituted for
the ABM CPR surface.

Runs the SAME macro-accounting pipeline (SOMA balance tracking, phased-cap
netting, Danish dynamic-balance loop) but replaces the ABM's CPR-surface
interpolation with Path B's literature microsim CPR path
(`use_hazard_microsim=True`). This isolates the institutional-gap comparison
under a single shared accounting layer, varying only the micro-foundation for
loan behavior.

Reports the institutional gap against the ABM-native figure
($925.5B, run-2026-07-04-15yr-foldin).
"""

from __future__ import annotations

import json
from pathlib import Path

import fed_mbs_extension_risk as fed

ABM_NATIVE_GAP_B = 925.5  # run-2026-07-04-15yr-foldin
OUT = Path(__file__).resolve().parent / "data" / "hybrid_pipeline_results.json"


def main() -> None:
    print("Fetching macro + SOMA …")
    df = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()

    print("Computing metrics with use_hazard_microsim=True "
          "(settlement kernel auto-disabled; Markov routing handles lag) …")
    df = fed.compute_metrics(
        df,
        soma_rolloff=soma,
        use_hazard_microsim=True,
        apply_settlement_lag_kernel=True,  # ignored when use_hazard_microsim
    )
    m = fed.export_headline_metrics(df)
    d = m["dollars_b"]
    c = m["cpr_pct"]

    payload = {
        "pipeline": "hybrid (shared macro-accounting + Path B microsim CPR)",
        "us_trapped_b": d["us_trapped"],
        "danish_trapped_b": d["danish_trapped"],
        "institutional_gap_b": d["institutional_gap"],
        "share_explained_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "us_cpr_mean_pct": c["us_abm"]["mean"],
        "danish_cpr_mean_pct": c["danish"]["mean"],
        "abm_native_gap_b": ABM_NATIVE_GAP_B,
        "gap_delta_vs_abm_native_b": d["institutional_gap"] - ABM_NATIVE_GAP_B,
    }
    OUT.write_text(json.dumps(payload, indent=2))

    print("\n" + "=" * 64)
    print(" HYBRID PIPELINE — shared accounting, Path B micro-foundation")
    print("=" * 64)
    print(f"  US trapped:            ${d['us_trapped']:.1f}B "
          f"({d['share_explained_pct']:.1f}% of ${d['empirical_trapped']:.1f}B)")
    print(f"  Danish trapped:       ${d['danish_trapped']:.1f}B")
    print(f"  Institutional gap:    ${d['institutional_gap']:.1f}B")
    print(f"  US / Danish CPR mean: {c['us_abm']['mean']:.2f}% / "
          f"{c['danish']['mean']:.2f}%")
    print("-" * 64)
    print(f"  ABM-native gap:       ${ABM_NATIVE_GAP_B:.1f}B")
    print(f"  Hybrid − ABM-native:  ${payload['gap_delta_vs_abm_native_b']:+.1f}B")
    print(f"\n  Saved: {OUT}")


if __name__ == "__main__":
    main()
