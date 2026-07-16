#!/usr/bin/env python3
"""
Round-15 Q2: Ginnie Mae published-CPR overlay on the 20.4% SOMA face share.

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------
Reviewer question (round 15, Q2): how sensitive are the 97.9%/88.7% headline
figures to Ginnie-specific prepayment behavior; can published CPR series
approximate Ginnie behavior?  The paper's standing answer is the static
composition bound (ginnie_bound.json: 20.4% face x 1.2-2.8pp snapshot CPR
differentials x $82.8B/pp => $20-47B, signed toward OVERSTATING trapped).
This run upgrades the static bound to a time-varying overlay built from a
PUBLISHED, single-methodology monthly Ginnie CPR series, while structural
Ginnie inclusion remains formally declined (2026-07-15; servicer-buyout CDR
channel non-comparability — the response of record).

Data
----
data/gmar_dec25_cpr_series.json — monthly CPR/CDR/CRR for Fannie/Freddie/
Ginnie, Jun-2017..Nov-2025, extracted from the December 2025 GMAR chart
vector paths (tools/extract_gmar_dec25.py; Recursion data, weighted-average
UPB methodology per the Dec-2025 revision note).  Extraction validation
embedded in the artifact: endpoint residuals vs printed labels <= 0.05pp;
independent CRR/CDR charts reproduce CPR to <= 0.21pp max.  The single
Dec-2025 issue is used rather than stitching 42 issues' endpoint labels,
which span three chart/aggregation regimes (pre-Jul-2025, the Jul-Nov-2025
interim design, and the Dec-2025 UPB-weighted revision).

Construction
------------
For each committed leg (central microsim_results.parquet, null
microsim_results_pq0.0.parquet), on the QT window Jun-2022..Nov-2025:
  SMM_model_t = hazard_cpr_pct_t / 1200            (engine's x12 convention)
  SMM_g_t     = 1 - (1 - CPR_series_t/100)^(1/12)  (compound; disclosed)
  E_t [$B]    = weighted_settled_b_t / SMM_model_t (scaled book exposure)
  Delta_t     = s * (SMM_g_t - SMM_model_t) * E_t,  s = 0.204
  rolloff'_t  = simulated_rolloff_b_t - Delta_t
scored through the production scorer (score_extension_risk) unchanged.
The overlay replaces the Ginnie share's model speed with the observed
series in BOTH legs; the corrected marginal is therefore the elasticity's
contribution confined to the conventional 79.6% share, with the Ginnie
share held at data — the coverage-robustness object the reviewer asks for.

Variants (all pre-specified)
----------------------------
  primary        CPR series (total: voluntary + buyout CDR; the
                 runoff-relevant speed for a passthrough holder)
  crr_only       CRR series (voluntary only; strips the buyout channel)
  gse_placebo    GSE-mean CPR series on the same 20.4% share (placebo:
                 isolates same-source calibration drift from the Ginnie-
                 specific differential)

Gates (must PASS before variants are interpreted)
-------------------------------------------------
G1 parity: with the series set identically to each leg's own model CPR the
   scorer reproduces the committed anchors exactly (|diff| <= 1e-9 B):
   central 818.5300844066606, null 748.1850239867648.
G2 extraction validation: asserted on artifact read (thresholds above).
G3 static-bound consistency: the primary central-leg adjustment
   sum(Delta_t) must land inside the committed bound [20.3, 47.3] $B
   -> verdict "inside_static_bound"; outside -> "bound_revision"
   (reported either way, with the window-mean differential printed).
Sign expectation (pre-registered): the corrected lock-in marginal remains
positive under every variant; a sign flip is reported as a finding, not
suppressed.

Basis
-----
Standalone scorer plus shared-basis restatement using the committed
constants: netting 69.56220187263008 $B (bit-identical across legs,
shared_layer_scoring_results.json), benchmark 764.7482532227002 $B.

Output: data/ginnie_cpr_overlay_results.json
Run:    cd hazard && python3 ginnie_cpr_overlay.py   (~seconds; no engine run)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from extension_risk import score_extension_risk
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "ginnie_cpr_overlay_results.json"

GINNIE_SHARE = 0.204
CENTRAL_TRAPPED_B = 818.5300844066606
NULL_TRAPPED_B = 748.1850239867648
NETTING_B = 69.56220187263008
BENCHMARK_B = 764.7482532227002
STATIC_BOUND_B = (20.3, 47.3)
PARITY_TOL_B = 1e-9


def load_series():
    s = json.loads((DATA_DIR / "gmar_dec25_cpr_series.json").read_text())
    v = s["validation"]
    for chart in ("cpr", "cdr", "crr"):
        assert all(abs(r) <= 0.05 for r in v[f"{chart}_endpoint_residual_pp"].values())
    assert v["cpr_vs_crr_cdr_identity_pp"]["max_abs"] <= 0.25
    idx = pd.PeriodIndex(s["months"], freq="M")
    return s, idx


def overlay_leg(sim: pd.DataFrame, empirical: pd.DataFrame,
                series_pct: pd.Series, share: float) -> dict:
    sim = sim.copy()
    per = sim.index.to_period("M")
    cpr_g = series_pct.reindex(per).to_numpy()
    assert not np.isnan(cpr_g).any(), "series does not cover the QT window"
    smm_model = sim["hazard_cpr_pct"].to_numpy() / 1200.0
    smm_g = 1.0 - (1.0 - cpr_g / 100.0) ** (1.0 / 12.0)
    exposure_b = sim["weighted_settled_b"].to_numpy() / np.maximum(smm_model, 1e-12)
    delta = share * (smm_g - smm_model) * exposure_b
    mean_diff_pp = float(np.mean(cpr_g - sim["hazard_cpr_pct"].to_numpy()))
    sim["simulated_rolloff_b"] = sim["simulated_rolloff_b"] - delta
    sim["hazard_cpr_pct"] = (1 - share) * sim["hazard_cpr_pct"] + share * (smm_g * 1200.0)
    res = score_extension_risk(sim, empirical)
    return {
        "trapped_b": res["hazard_trapped_b"],
        "share_pct": res["share_explained_pct"],
        "adjustment_sum_b": float(delta.sum()),
        "mean_series_minus_model_pp": mean_diff_pp,  # diagnostic only
    }


def main() -> None:
    series, idx = load_series()
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    central = pd.read_parquet(DATA_DIR / "microsim_results.parquet")
    null = pd.read_parquet(DATA_DIR / "microsim_results_pq0.0.parquet")

    # --- G1 parity: series == model CPR (annualized back with the engine's
    # x12 convention so smm_g == smm_model identically) => Delta == 0.
    def own_series(sim):
        smm = sim["hazard_cpr_pct"] / 1200.0
        ann = (1.0 - (1.0 - smm) ** 12) * 100.0
        return pd.Series(ann.to_numpy(), index=sim.index.to_period("M"))

    g1c = overlay_leg(central, empirical, own_series(central), GINNIE_SHARE)
    g1n = overlay_leg(null, empirical, own_series(null), GINNIE_SHARE)
    g1 = {
        "central_diff_b": g1c["trapped_b"] - CENTRAL_TRAPPED_B,
        "null_diff_b": g1n["trapped_b"] - NULL_TRAPPED_B,
    }
    g1["pass"] = (abs(g1["central_diff_b"]) <= PARITY_TOL_B
                  and abs(g1["null_diff_b"]) <= PARITY_TOL_B)
    print(f"G1 parity: central diff {g1['central_diff_b']:+.2e}  "
          f"null diff {g1['null_diff_b']:+.2e}  {'PASS' if g1['pass'] else 'FAIL'}")
    if not g1["pass"]:
        RESULTS_JSON.write_text(json.dumps({"status": "GATE_FAILURE", "g1": g1}, indent=2) + "\n")
        raise SystemExit("G1 parity failure — variants not run.")

    gse_mean = [(f + fr) / 2 for f, fr in zip(series["cpr"]["fannie"], series["cpr"]["freddie"])]
    variants = {
        "primary": pd.Series(series["cpr"]["ginnie"], index=idx),
        "crr_only": pd.Series(series["crr"]["ginnie"], index=idx),
        "gse_placebo": pd.Series(gse_mean, index=idx),
    }

    def shared(trapped_b):
        return (trapped_b - NETTING_B) / BENCHMARK_B * 100.0

    results = {}
    for name, ser in variants.items():
        c = overlay_leg(central, empirical, ser, GINNIE_SHARE)
        n = overlay_leg(null, empirical, ser, GINNIE_SHARE)
        marg_b = c["trapped_b"] - n["trapped_b"]
        results[name] = {
            "central": {**c, "share_shared_pct": shared(c["trapped_b"])},
            "null": {**n, "share_shared_pct": shared(n["trapped_b"])},
            "marginal_b": marg_b,
            "marginal_pp": marg_b / BENCHMARK_B * 100.0,
            "marginal_sign_positive": marg_b > 0,
        }
        print(f"{name:>12}: central {c['share_pct']:.1f}% ({shared(c['trapped_b']):.1f}% shared)  "
              f"null {n['share_pct']:.1f}% ({shared(n['trapped_b']):.1f}%)  "
              f"marginal {marg_b:+.2f}B ({marg_b/BENCHMARK_B*100:+.2f}pp)  "
              f"adj {c['adjustment_sum_b']:+.2f}B")

    adj = results["primary"]["central"]["adjustment_sum_b"]
    i0 = series["months"].index("2022-06")
    g = np.array(series["cpr"]["ginnie"][i0:])
    fr = np.array(series["cpr"]["freddie"][i0:])
    fa = np.array(series["cpr"]["fannie"][i0:])
    g3 = {
        "primary_central_adjustment_b": adj,
        "static_bound_b": list(STATIC_BOUND_B),
        "verdict": ("inside_static_bound"
                    if STATIC_BOUND_B[0] <= adj <= STATIC_BOUND_B[1]
                    else "bound_revision"),
        "window_mean_ginnie_minus_freddie_pp": float(np.mean(g - fr)),
        "window_mean_ginnie_minus_gse_mean_pp": float(np.mean(g - (fa + fr) / 2)),
        "static_bound_snapshot_differentials_pp": [1.2, 2.8],
    }
    print(f"G3: primary adjustment {adj:+.2f}B vs bound {STATIC_BOUND_B} -> {g3['verdict']}; "
          f"window-mean G-FRE diff {g3['window_mean_ginnie_minus_freddie_pp']:.2f}pp")

    payload = {
        "mode": "ginnie_cpr_overlay",
        "spec": "round-15 Q2; 20.4% share scored by published Ginnie series in both legs",
        "series_source": series["source"],
        "series_validation": series["validation"],
        "committed_anchors": {
            "central_trapped_b": CENTRAL_TRAPPED_B, "null_trapped_b": NULL_TRAPPED_B,
            "netting_b": NETTING_B, "benchmark_b": BENCHMARK_B,
        },
        "gates": {"G1_parity": g1, "G3_static_bound": g3},
        "variants": results,
        "note": ("Published series is full-universe Ginnie collateral; SOMA's Ginnie "
                 "holdings are seasoned/low-coupon, so the overlay if anything "
                 "OVERSTATES the correction — same signed direction as the static bound. "
                 "Structural Ginnie inclusion remains formally declined (2026-07-15)."),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
