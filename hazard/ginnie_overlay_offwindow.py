#!/usr/bin/env python3
"""
ginnie_overlay_offwindow.py — the published-series Ginnie overlay composed
with the off-window (headline) floor, a cell the committed overlay run
(in-sample floor only) never produced.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
ginnie_cpr_overlay.py / floor_form_offwindow.py).

Referee objection (round 21, finding MF-9 / hazard-mc "Ginnie overlay never
composed" PARTIAL): the manuscript computes and endorses the observed-speed
Ginnie overlay ("what runoff accounting requires of a passthrough holder"),
which at the in-sample floor moves the shared central 97.9->89.3, the null
88.7->81.9, and the marginal to +7.3pp (scaling with the conventional face
share, 0.797) — then never composes it with the off-window headline
quantities. No off-window x overlay cell exists. This script computes it.

SPEC (fixed ex ante)
- Inputs: the fresh max-form off-window parquets from the committed
  floor_form_offwindow run (floor 4.991%, p_q {0, 6.5}), whose values
  reproduced the committed oos_identification rows bit-exactly (G3 of that
  run). This script re-anchors them again via its own G1.
- Overlay machinery: imported unmodified from ginnie_cpr_overlay
  (load_series, overlay_leg, GINNIE_SHARE 0.204, shared-basis constants).
- Variants per leg: primary (Ginnie CPR), gse_placebo (GSE-mean series,
  isolating the common observed-series component), crr_only (voluntary-only
  Ginnie series) — the committed run's variant set, unchanged.
- Legs: central (pq 6.5) and null (pq 0) at floor 4.991%; marginal =
  central - null per variant (netting cancels; basis-invariant).

PARITY GATES:
  G1 (own-series identity): overlaying each 4.991% leg with its own
     annualized CPR series must reproduce that leg's committed
     oos_identification value to 1e-9 $B (central $767.5264524B, null
     $724.9180586B) — validates both the parquets and the overlay wiring.
  G2 (cross-artifact): the committed in-sample overlay artifact's primary
     central/null shared values are re-read and the in-sample overlay
     marginal recomputed from them; it must equal the committed +7.3pp to
     +/-0.05pp.

EX-ANTE INTERPRETIVE FRAME (no discretion after the run):
  - Report the off-window headline pair on the shared basis: conventional
    (central 91.27%, null 85.70%, marginal +5.57pp) beside overlay-corrected
    (computed here), plus the Ginnie-specific component (primary minus
    placebo) at the off-window floor.
  - The revision carries the pair (or the conservative member) wherever the
    off-window level/marginal is quoted as a headline, with the overlay
    labeled as an accounting correction bounded by the static $20-47B bound.
  - Expected direction (not a gate): overlay lowers both legs and the
    marginal scales toward the conventional share (~0.8x), as at the
    in-sample floor.

Run:  cd hazard && python3 ginnie_overlay_offwindow.py   (~seconds; no engine run)
      -> data/ginnie_overlay_offwindow_results.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from extension_risk import score_extension_risk  # noqa: F401 (parity of import path)
from ginnie_cpr_overlay import (
    BENCHMARK_B,
    GINNIE_SHARE,
    NETTING_B,
    load_series,
    overlay_leg,
)
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
IN_DIR = DATA_DIR / "floor_form_offwindow"
RESULTS_JSON = DATA_DIR / "ginnie_overlay_offwindow_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
OVERLAY_ARTIFACT = DATA_DIR / "ginnie_cpr_overlay_results.json"

OFF_FLOOR_PCT = 4.991
PARITY_TOL_B = 1e-9
G2_TOL_PP = 0.05


def own_series(sim: pd.DataFrame) -> pd.Series:
    smm = sim["hazard_cpr_pct"] / 1200.0
    ann = (1.0 - (1.0 - smm) ** 12) * 100.0
    return pd.Series(ann.to_numpy(), index=sim.index.to_period("M"))


def shared(trapped_b: float) -> float:
    return (trapped_b - NETTING_B) / BENCHMARK_B * 100.0


def main() -> None:
    with open(OOS_ARTIFACT) as f:
        oos = json.load(f)
    row = next(r for r in oos["instrument1_marginal_table"]
               if abs(r["floor_annual_cpr_pct"] - OFF_FLOOR_PCT) < 1e-9)
    want_central = row["band"]["6.5"]["central_trapped_b"]
    want_null = row["null_trapped_b"]

    series, idx = load_series()
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    central = pd.read_parquet(IN_DIR / "microsim_max_floor4.991pct_pq6.5.parquet")
    null = pd.read_parquet(IN_DIR / "microsim_max_floor4.991pct_pq0.parquet")

    report = {}
    g1c = overlay_leg(central, empirical, own_series(central), GINNIE_SHARE)
    g1n = overlay_leg(null, empirical, own_series(null), GINNIE_SHARE)
    report["G1_central"] = {"diff_b": g1c["trapped_b"] - want_central,
                            "pass": abs(g1c["trapped_b"] - want_central) <= PARITY_TOL_B}
    report["G1_null"] = {"diff_b": g1n["trapped_b"] - want_null,
                         "pass": abs(g1n["trapped_b"] - want_null) <= PARITY_TOL_B}
    for k, v in report.items():
        print(f"parity gate {k}: diff {v['diff_b']:+.2e} "
              f"[{'PASS' if v['pass'] else 'FAIL'}]")

    with open(OVERLAY_ARTIFACT) as f:
        comm = json.load(f)
    comm_central = comm["variants"]["primary"]["central"]
    comm_null = comm["variants"]["primary"]["null"]
    comm_marg_pp = (comm_central["share_pct_shared"]
                    - comm_null["share_pct_shared"]) \
        if "share_pct_shared" in comm_central else None
    if comm_marg_pp is None:
        comm_marg_pp = shared(comm_central["trapped_b"]) - shared(comm_null["trapped_b"])
    g2_ok = abs(comm_marg_pp - 7.3) <= G2_TOL_PP
    report["G2_committed_insample_marginal"] = {"got_pp": comm_marg_pp,
                                                "pass": bool(g2_ok)}
    print(f"parity gate G2: committed in-sample overlay marginal "
          f"{comm_marg_pp:+.3f}pp (want +7.3 +/- {G2_TOL_PP}) "
          f"[{'PASS' if g2_ok else 'FAIL'}]")

    hard_fail = [k for k, v in report.items() if not v["pass"]]
    if hard_fail:
        RESULTS_JSON.write_text(json.dumps(
            {"status": "GATE_FAILURE", "gates": report}, indent=2,
            default=float) + "\n")
        raise SystemExit(f"PARITY FAILURE — variants not run: {hard_fail}")

    gse_mean = [(f + fr) / 2 for f, fr in
                zip(series["cpr"]["fannie"], series["cpr"]["freddie"])]
    variants = {
        "primary": pd.Series(series["cpr"]["ginnie"], index=idx),
        "crr_only": pd.Series(series["crr"]["ginnie"], index=idx),
        "gse_placebo": pd.Series(gse_mean, index=idx),
    }
    out = {}
    for name, s in variants.items():
        c = overlay_leg(central, empirical, s, GINNIE_SHARE)
        n = overlay_leg(null, empirical, s, GINNIE_SHARE)
        out[name] = {
            "central": {**c, "share_pct_shared": shared(c["trapped_b"])},
            "null": {**n, "share_pct_shared": shared(n["trapped_b"])},
            "marginal_b": c["trapped_b"] - n["trapped_b"],
            "marginal_pp": shared(c["trapped_b"]) - shared(n["trapped_b"]),
        }
        print(f"{name:>12}: central {shared(c['trapped_b']):6.2f}% shared, "
              f"null {shared(n['trapped_b']):6.2f}%, marginal "
              f"{out[name]['marginal_pp']:+5.2f}pp "
              f"(${out[name]['marginal_b']:+.2f}B)")

    conventional = {
        "central_shared_pct": shared(want_central),
        "null_shared_pct": shared(want_null),
        "marginal_pp": shared(want_central) - shared(want_null),
    }
    ginnie_specific_marginal_pp = (out["primary"]["marginal_pp"]
                                   - out["gse_placebo"]["marginal_pp"])
    payload = {
        "mode": "ginnie_overlay_offwindow",
        "spec": ("committed overlay machinery on the fresh max-form 4.991% "
                 "legs; variants primary/crr_only/gse_placebo; gates G1 "
                 "(own-series identity vs committed oos values, 1e-9) and "
                 "G2 (committed in-sample overlay marginal +7.3pp)"),
        "floor_annual_cpr_pct": OFF_FLOOR_PCT,
        "parity_gates": {k: {kk: float(vv) if isinstance(vv, (int, float))
                             else vv for kk, vv in v.items()}
                         for k, v in report.items()},
        "conventional_offwindow": conventional,
        "overlay_offwindow": out,
        "ginnie_specific_marginal_component_pp": ginnie_specific_marginal_pp,
        "marginal_scale_vs_conventional": (out["primary"]["marginal_pp"]
                                           / conventional["marginal_pp"]),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=1, default=float) + "\n")
    print(f"\nheadline pair at the off-window floor (shared basis): "
          f"conventional {conventional['central_shared_pct']:.2f}%/"
          f"{conventional['null_shared_pct']:.2f}%/"
          f"{conventional['marginal_pp']:+.2f}pp  |  overlay "
          f"{out['primary']['central']['share_pct_shared']:.2f}%/"
          f"{out['primary']['null']['share_pct_shared']:.2f}%/"
          f"{out['primary']['marginal_pp']:+.2f}pp")


if __name__ == "__main__":
    main()
