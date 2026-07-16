#!/usr/bin/env python3
"""
Curtailment-rate stress on the Danish legs (pre-committed; spec fixed in
this header before any run executed).

Manuscript residual: the curtailment-stress passage (round 14,
sec:robustness-hybrid) derives the U.S. side of the +/-25% stress exactly —
the netted flow is computed on the ACTUAL WSHOMCB holdings path, so it is
exactly proportional to the assumed rate ($69.56B -> $52.17B / $86.95B) —
but then asserts, from first-order arithmetic alone, that the Danish legs'
curtailment differential "stays immaterial (below $1 billion) across the
same range". That Danish claim is not exact by construction: the Danish
dynamic-balance loop (fed_mbs_extension_risk.compute_metrics, microsim
branch) drains a COUNTERFACTUAL balance by monthly_cpr_dk + sched_smm +
curtailment_smm each month, so a higher curtailment rate also lowers the
balances that later months' curtailment applies to — the Danish leg is only
first-order linear in the rate, and the sub-$1B claim was never verified by
a run. This script is that run; its exact figures replace the phrase.

SPEC (fixed ex ante):
- Scales {0.75, 1.0, 1.25} on CURTAILMENT_CPR_HEALTHY = 0.012 (rate-only
  stress; the income-scaled fraction — CURTAILMENT_INCOME_HEALTHY_PCT /
  CURTAILMENT_INCOME_STRESSED_PCT — is untouched). 1.0x doubles as the
  parity gate.
- Machinery: the committed production Path B CPR paths, read from
  data/microsim_results.parquet exactly as shared_layer_scoring.py reads
  them (_paths_from_combined_cache). No microsim re-run: the curtailment
  rate is consumed by the ABM accounting layer only (no hazard/ module
  reads it), so the simulated CPR paths cannot move; the scored frames'
  US and Danish CPR columns are asserted bit-identical across scales.
  Scoring = the shared accounting layer exactly as shared_layer_scoring.py:
  fed.compute_metrics(use_hazard_microsim=True) with
  _load_hazard_microsim_paths patched to the cached paths. Live FRED + SOMA
  fetched once; no new data downloads.
- Rate patch: fed.curtailment_series is wrapped so healthy_cpr =
  scale * 0.012 (patch-and-restore per scale, the danish_discount_bound /
  floor_form pattern). Patching the fed.CURTAILMENT_CPR_HEALTHY global
  ALONE would be a silent no-op — the constant is consumed only as a
  def-time-bound default argument of curtailment_series — so the function
  wrap is the operative patch (the global is set too, for any introspective
  consumer, and restored).
- Quantities per scale, all on the 42-month qt_active_frame: US common
  netting (actual WSHOMCB holdings x curtailment SMM; must equal
  export_headline_metrics curtailment_b.total — asserted), Danish-leg
  curtailment (Danish counterfactual balance x curtailment SMM), their
  differential, and the shared-layer Danish trapped / U.S. trapped /
  institutional gap.
- Parity gates at 1.0x (withdraw-not-reinterpret on failure):
    us_netting_b                 $69.5622B +/- $0.01B (anchor read from
                                 shared_layer_scoring_results.json)
    danish_leg_curtailment_b     $70.33B   +/- $0.01B (anchor read from
                                 danish_discount_bound.json)
    danish_trapped_printed_cell  Table 1 Danish cell $848.9B within $1.0B
                                 (danish_discount_bound.py's own gate width
                                 for the rounded printed cell)
    curtailment_differential_b   +$0.77B   +/- $0.01B
  Residual differences at these gates are live-FRED input revisions,
  common to all runs here (the danish_discount_bound convention).
- Structural assertions (not gates; must hold by construction): US netting
  exactly x scale (|got - scale * baseline| < 1e-6 B, float-associativity
  headroom only); US and Danish CPR paths bit-identical across scales;
  empirical benchmark invariant across scales.
- Interpretive threshold, stated ex ante: if the exact Danish differential
  stays below $1.0B at BOTH endpoints (0.75x, 1.25x), the manuscript's
  "stays immaterial (below $1 billion)" phrase is upgraded to the exact
  figures with no claim change; if it exceeds $1.0B anywhere, the sentence
  must be restated with the exact value.

Run:  cd hazard && python3 curtailment_danish_scaling.py
      -> data/curtailment_danish_scaling_results.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "abm", _REPO / "hazard"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "curtailment_danish_scaling_results.json"
SHARED_ANCHOR_ARTIFACT = DATA_DIR / "shared_layer_scoring_results.json"
BOUND_ANCHOR_ARTIFACT = DATA_DIR / "danish_discount_bound.json"

SCALES = [0.75, 1.0, 1.25]
BASE_CURTAILMENT_CPR = 0.012         # production CURTAILMENT_CPR_HEALTHY
PRINTED_TABLE1_DANISH_B = 848.9      # Table 1 row (c), shared-accounting basis
DIFFERENTIAL_ANCHOR_B = 0.77         # sec:robustness-hybrid: 70.33 vs 69.56
PARITY_TOL_B = 0.01                  # $0.01B gates (floor_form convention)
PRINTED_CELL_TOL_B = 1.0             # danish_discount_bound.py's Table 1 gate
MATERIALITY_THRESHOLD_B = 1.0        # the manuscript's "below $1 billion"
LINEARITY_TOL_B = 1e-6               # float-associativity headroom only


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _make_scaled_curtailment(original, scaled_rate: float):
    """curtailment_series with healthy_cpr pinned to scaled_rate.

    The income-fraction parameters (healthy_pct / stressed_pct) pass through
    untouched, so only the rate is stressed. This wrap — not the module
    global — is the operative patch: CURTAILMENT_CPR_HEALTHY is consumed
    only as a def-time-bound default argument of curtailment_series.
    """
    def patched(real_income_yoy_pct, **kwargs):
        kwargs.setdefault("healthy_cpr", scaled_rate)
        return original(real_income_yoy_pct, **kwargs)

    return patched


def main() -> None:
    import fed_mbs_extension_risk as fed

    from config import MICROSIM_RESULTS_PATH
    from shared_layer_scoring import _paths_from_combined_cache

    t0 = time.perf_counter()

    print("Fetching ABM macro + SOMA (once; live FRED) …")
    macro_abm = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()

    print("Loading committed production microsim cache …")
    micro_paths = _paths_from_combined_cache(MICROSIM_RESULTS_PATH)

    base_rate = fed.CURTAILMENT_CPR_HEALTHY
    assert base_rate == BASE_CURTAILMENT_CPR, (
        f"production CURTAILMENT_CPR_HEALTHY drifted ({base_rate}) — "
        "re-fix the spec before running"
    )

    original_series = fed.curtailment_series
    original_loader = fed._load_hazard_microsim_paths

    frames: dict[float, pd.DataFrame] = {}
    runs: list[dict] = []
    for scale in SCALES:
        scaled_rate = scale * base_rate
        fed.curtailment_series = _make_scaled_curtailment(
            original_series, scaled_rate
        )
        fed.CURTAILMENT_CPR_HEALTHY = scaled_rate  # introspection only
        fed._load_hazard_microsim_paths = lambda df: micro_paths
        try:
            m = fed.compute_metrics(
                macro_abm.copy(),
                soma_rolloff=soma,
                use_hazard_microsim=True,
                apply_settlement_lag_kernel=True,  # auto-off in microsim mode
            )
        finally:
            fed.curtailment_series = original_series
            fed.CURTAILMENT_CPR_HEALTHY = base_rate
            fed._load_hazard_microsim_paths = original_loader

        qt = fed.qt_active_frame(m)
        assert len(qt) == fed.expected_qt_active_months(), (
            f"qt_active_frame has {len(qt)} months; expected "
            f"{fed.expected_qt_active_months()}"
        )
        hm = fed.export_headline_metrics(m)
        d = hm["dollars_b"]

        # US common netting: curtailment on the ACTUAL holdings path —
        # by definition identical to the layer's own curtailment_b.total.
        us_netting = float(
            (qt["WSHOMCB"] / 1_000 * qt["Curtailment_SMM"]).sum()
        )
        assert abs(us_netting - hm["curtailment_b"]["total"]) < 1e-9, (
            "window convention drift: frame-based US netting != "
            "export_headline_metrics curtailment_b.total"
        )
        # Danish-leg curtailment: same SMM on the Danish loop's
        # counterfactual (begin-of-month) balances.
        dk_curt = float(
            (qt["Danish_Balance_Billions"] * qt["Curtailment_SMM"]).sum()
        )

        frames[scale] = m
        run = {
            "scale": scale,
            "curtailment_cpr_healthy": scaled_rate,
            "curtailment_smm_mean_annualized_pct": (
                hm["curtailment_b"]["annualized_pct"]
            ),
            "us_netting_b": us_netting,
            "danish_leg_curtailment_b": dk_curt,
            "curtailment_differential_b": dk_curt - us_netting,
            "us_trapped_b": d["us_trapped"],
            "danish_trapped_b": d["danish_trapped"],
            "institutional_gap_b": d["institutional_gap"],
            "share_explained_pct": d["share_explained_pct"],
            "empirical_trapped_b": d["empirical_trapped"],
        }
        runs.append(run)
        print(
            f"scale {scale:4.2f}x ({scaled_rate * 100:.2f}% CPR):  "
            f"US netting ${us_netting:6.2f}B   "
            f"Danish curtailment ${dk_curt:6.2f}B   "
            f"differential ${dk_curt - us_netting:+5.2f}B   "
            f"Danish trapped ${d['danish_trapped']:6.1f}B   "
            f"inst. gap ${d['institutional_gap']:+6.1f}B"
        )
    runtime_s = time.perf_counter() - t0

    # ---- Structural assertions (hold by construction) -----------------------
    base = next(r for r in runs if r["scale"] == 1.0)
    m_base = frames[1.0]
    for r in runs:
        m_s = frames[r["scale"]]
        dk_diff = float(np.abs(
            m_s["Danish_CPR_Pct"].to_numpy()
            - m_base["Danish_CPR_Pct"].to_numpy()).max())
        us_diff = float(np.abs(
            m_s["US_CPR_Pct"].to_numpy()
            - m_base["US_CPR_Pct"].to_numpy()).max())
        r["max_abs_danish_cpr_diff_vs_baseline_pp"] = dk_diff
        r["max_abs_us_cpr_diff_vs_baseline_pp"] = us_diff
        assert dk_diff == 0.0 and us_diff == 0.0, (
            f"CPR path moved under a curtailment-rate change at scale "
            f"{r['scale']} (dk {dk_diff}, us {us_diff}) — the rate has "
            "leaked into the simulation; do not cite"
        )
        assert abs(
            r["empirical_trapped_b"] - base["empirical_trapped_b"]
        ) < 1e-9, "empirical benchmark moved across scales"

        r["us_netting_linear_departure_b"] = (
            r["us_netting_b"] - r["scale"] * base["us_netting_b"]
        )
        assert abs(r["us_netting_linear_departure_b"]) < LINEARITY_TOL_B, (
            f"US netting not exactly proportional at scale {r['scale']} "
            f"({r['us_netting_linear_departure_b']})"
        )
        # Danish second-order feedback: exact minus (scale x baseline).
        r["danish_linear_departure_b"] = (
            r["danish_leg_curtailment_b"]
            - r["scale"] * base["danish_leg_curtailment_b"]
        )
        r["differential_first_order_b"] = (
            r["scale"] * base["curtailment_differential_b"]
        )

    # ---- Parity gates at 1.0x -----------------------------------------------
    shared_anchor = json.load(open(SHARED_ANCHOR_ARTIFACT))
    bound_anchor = json.load(open(BOUND_ANCHOR_ARTIFACT))
    us_anchor = (
        shared_anchor["results"]["path_b_central"]["curtailment_netted_b"]
    )
    dk_anchor = (
        bound_anchor["reconciliation"]["basis_difference_components"]
        ["danish_leg_curtailment_b"]
    )

    gates = {
        "us_netting_b": (
            base["us_netting_b"], us_anchor, PARITY_TOL_B),
        "danish_leg_curtailment_b": (
            base["danish_leg_curtailment_b"], dk_anchor, PARITY_TOL_B),
        "danish_trapped_printed_cell_b": (
            base["danish_trapped_b"], PRINTED_TABLE1_DANISH_B,
            PRINTED_CELL_TOL_B),
        "curtailment_differential_b": (
            base["curtailment_differential_b"], DIFFERENTIAL_ANCHOR_B,
            PARITY_TOL_B),
    }
    gate_report = {}
    for name, (got, want, tol) in gates.items():
        ok = abs(got - want) < tol
        gate_report[name] = {
            "got": got, "want": want, "tol": tol, "pass": bool(ok),
        }
        print(f"parity gate {name}: got {got:.4f} want {want:.4f} "
              f"(tol {tol:g}) [{'PASS' if ok else 'FAIL'}]")
    parity_pass = all(v["pass"] for v in gate_report.values())

    # ---- Ex-ante interpretive threshold -------------------------------------
    endpoint_differentials = {
        f"{r['scale']:g}x": r["curtailment_differential_b"]
        for r in runs if r["scale"] != 1.0
    }
    max_abs_differential = max(
        abs(r["curtailment_differential_b"]) for r in runs
    )
    verdict = (
        "Danish curtailment differential stays below $1.0B at both +/-25% "
        "endpoints — the manuscript's 'stays immaterial (below $1 billion)' "
        "phrase is upgraded to the exact figures, no claim change"
        if max_abs_differential < MATERIALITY_THRESHOLD_B
        else "Danish curtailment differential reaches $1.0B — restate the "
        "manuscript sentence with the exact value"
    )

    payload = {
        "mode": "curtailment_danish_scaling",
        "spec": ("hazard/curtailment_danish_scaling.py module docstring "
                 "(fixed ex ante)"),
        "git_commit": _git_head(),
        "created_utc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"),
        "layer": ("fed_mbs_extension_risk.compute_metrics("
                  "use_hazard_microsim=True) over the committed production "
                  "microsim cache (data/microsim_results.parquet)"),
        "scales": SCALES,
        "curtailment_cpr_healthy_base": BASE_CURTAILMENT_CPR,
        "runs": runs,
        "anchors": {
            "us_netting_b": {
                "value": us_anchor,
                "source": ("shared_layer_scoring_results.json: results."
                           "path_b_central.curtailment_netted_b"),
            },
            "danish_leg_curtailment_b": {
                "value": dk_anchor,
                "source": ("danish_discount_bound.json: reconciliation."
                           "basis_difference_components."
                           "danish_leg_curtailment_b"),
            },
            "danish_trapped_printed_cell_b": PRINTED_TABLE1_DANISH_B,
            "curtailment_differential_b": DIFFERENTIAL_ANCHOR_B,
        },
        "parity_gates": gate_report,
        "parity_gates_all_pass": parity_pass,
        "endpoint_differentials_b": endpoint_differentials,
        "max_abs_differential_b": max_abs_differential,
        "materiality_threshold_b": MATERIALITY_THRESHOLD_B,
        "ex_ante_verdict": verdict,
        "manuscript_sentence": (
            "paper/v16/revised_paper_v16.tex, sec:robustness-hybrid: 'The "
            "Danish legs, which compute curtailment on their own "
            "counterfactual balances, scale only to first order, and their "
            "differential stays immaterial (below $1 billion) across the "
            "same range.'"),
        "runtime_s": round(runtime_s, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=float)
        f.write("\n")

    print(f"\nmax |differential| across scales: "
          f"${max_abs_differential:.4f}B (threshold "
          f"${MATERIALITY_THRESHOLD_B:.1f}B)")
    print(f"ex-ante verdict: {verdict}")
    if not parity_pass:
        raise SystemExit(
            "PARITY GATE FAILURE — results written to "
            f"{RESULTS_JSON} for diagnosis but must be withdrawn, not "
            "reinterpreted."
        )
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
