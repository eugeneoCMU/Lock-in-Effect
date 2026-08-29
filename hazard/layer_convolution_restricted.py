#!/usr/bin/env python3
"""
layer_convolution_restricted.py — the convolved sampling pair RE-DERIVED on the
adjudicated restricted rung over the FP2-B1 extended grid.

SPEC: specs/SPEC_fresh_panel2_B2_convolution_rederivation_2026-08-29.md
(ADOPTED 2026-08-29, construction α, amendment FP2-B2-A1 applied; committed
before first execution). Supersedes data/layer_convolution_results.json — the
committed C2 artifact survives in git history; this run writes fresh.

WHY (fresh-panel-2 f3): the committed convolved pair [+2.7959, +8.9922] used
the DEMOTED Webb wild-t rung as its floor layer and was anti-conservative
(narrower than the binding interval a re-derivation must exceed). This run
convolves the ADJUDICATED restricted inversion's confidence distribution with
the committed loan/stratum layer.

FLOOR LAYER (α, per FP2-B2-A1) — the nested-CI confidence distribution of the
committed restricted Webb inversion, exact at every level:
  - the committed 401-point R0 grid (R_hat ± 5·SE_CR1, SMM), ONE Webb weight
    matrix from a fresh default_rng(42) — v2's wcr_invert conventions verbatim;
  - per grid point, U_i = the interpolated-percentile position of
    t_obs(R0_i) = (R_hat − R0_i)/SE_CR1 in the sorted restricted t* draws
    (the exact inverse of np.percentile's linear rule), α_i = min(U_i, 1−U_i);
  - retention at 5%: α_i >= 0.025 — IDENTICAL to v2's equal-tailed rule, so
    the retained set and its endpoints reproduce the committed inversion
    bit-exactly (gate Q2), and the layer quantile at u is the first (u < .5,
    mirrored above) grid point with α_i >= u — nested levels, monotone by
    construction;
  - M at u_b = (b − 0.5)/9999, b = 1..9999, mapped through the FP2-B1
    extended PCHIP (edge-truncation convention retained and counted;
    the R0 grid ceiling 6.7242% < 7.0, so the expected count is 0).

LOAN LAYER — C2 verbatim: d_j = m_j − 5.5715581829 (pp) and m_bj − CENTER_B
($B) over the 200 committed cluster draws; centering constants FIXED EX ANTE.

CONVOLVED — exact outer sum, 9,999 × 200; 2.5/97.5 pp and $B, median, sd,
width, width ratio vs the RE-DERIVED binding interval. Secondary percentile
companion and the dependence bracket carry over from C2 unchanged in form.

THE ONLY RNGs are the fresh default_rng(42) Webb matrix (v2's own) and the
committed default_rng(42) inside fu.cluster_bootstrap_cpr (C2's P0). No
microsim engine anywhere; everything read is frozen and never written.

PARITY GATES (abort, not warn; GATE_FAILURE + nonzero exit):
  Q0  C2's P0/P1 verbatim: percentile regeneration bit-exact at R2; loan CSV
      200 rows, committed percentiles and sd reproduced.
  Q1  input freshness: the regenerated v2 artifact is status OK / all-pass,
      its wcr smm CI is the committed [0.003425004498583382,
      0.005303011878727873], and the extended mapping's support ends at 7.0.
  Q2  construction ties to the adjudicated interval: {α_i >= 0.025} equals
      v2's retained set; layer quantiles at 0.025/0.975 reproduce the
      committed floor-unit CI bit-exactly and map to the re-derived binding
      interval to 1e-12.
  Q3  convolved width > the re-derived binding width (7.2384pp).

Run:  cd hazard && python3 layer_convolution_restricted.py
      -> data/layer_convolution_results.json (fresh; supersedes C2's)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HAZ = Path(__file__).resolve().parent
if str(HAZ) not in sys.path:
    sys.path.insert(0, str(HAZ))

import floor_uncertainty as fu                      # noqa: E402
import floor_inference_correction_v2 as v2          # noqa: E402
import layer_convolution as lc                      # noqa: E402
import matched_depth_reconciliation as mdr          # noqa: E402
from stratum import build_stratum_id                # noqa: E402

DATA = HAZ / "data"
RESULTS_JSON = DATA / "layer_convolution_results.json"
SPEC = ("specs/SPEC_fresh_panel2_B2_convolution_rederivation_2026-08-29.md "
        "(construction α, amendment A1)")

# FP2-B1: the mapping conventions in the imported C2 helpers follow the
# extended grid support
lc.GRID_LO, lc.GRID_HI = 2.0, 7.0

B_LEVELS = 9999
RETAIN_ALPHA = 0.025
# the re-derived binding interval (regenerated v2, R2 wcr_inverted)
REDERIVED_BINDING_PP = (1.8709537466170403, 9.109324011557733)
REDERIVED_BINDING_B = (14.308086095858464, 69.66339625878369)
COMMITTED_SMM_CI = (0.003425004498583382, 0.005303011878727873)
COMMITTED_N_RETAINED = 247
# SPEC §3 pre-committed prediction (hit/miss, never gated)
PREDICTED_CI95_PP = (1.2, 1.7, 9.6, 10.0)   # lower in [1.2,1.7], upper in [9.6,10.0]
PREDICTED_WIDTH_PP = (8.3, 8.7)


def fail(gates: dict, t0: float, msg: str) -> None:
    payload = {"mode": "layer_convolution_restricted", "status": "GATE_FAILURE",
               "spec_source": SPEC, "failure": msg, "parity_gates": gates,
               "runtime_s": round(time.perf_counter() - t0, 1)}
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=float)
    print(f"GATE_FAILURE: {msg}")
    sys.exit(1)


def quantile_position(sorted_t: np.ndarray, x: float) -> float:
    """Exact inverse of np.percentile's default linear interpolation: the u
    with q_u = x. 0 below the min, 1 above the max; at a tie the rightmost
    index (matches q_u <= x iff u <= U)."""
    n = sorted_t.size
    if x < sorted_t[0]:
        return 0.0
    if x >= sorted_t[-1]:
        return 1.0
    k = int(np.searchsorted(sorted_t, x, side="right")) - 1
    lo, hi = float(sorted_t[k]), float(sorted_t[k + 1])
    frac = 0.0 if hi == lo else (x - lo) / (hi - lo)
    return (k + frac) / (n - 1)


def main() -> None:
    t0 = time.perf_counter()
    gates: dict = {}

    # ---- Q1: input freshness ------------------------------------------------
    with open(DATA / "floor_inference_correction_v2_results.json") as f:
        v2art = json.load(f)
    wcr = v2art["reads"][lc.R2]["wcr_inverted"]
    mapping = mdr.FloorMapping(extended=True)
    q1_ok = (v2art["status"] == "OK" and v2art["parity_gates_all_pass"]
             and wcr["smm_ci95"] == list(COMMITTED_SMM_CI)
             and wcr["marginal_ci95_pp"] == list(REDERIVED_BINDING_PP)
             and float(mapping.x.max()) == 7.0
             and wcr["n_retained"] == COMMITTED_N_RETAINED)
    gates["Q1_input_freshness"] = {
        "pass": bool(q1_ok), "v2_status": v2art["status"],
        "wcr_smm_ci95": wcr["smm_ci95"],
        "wcr_marginal_ci95_pp": wcr["marginal_ci95_pp"],
        "mapping_support": [float(mapping.x.min()), float(mapping.x.max())]}
    if not q1_ok:
        fail(gates, t0, "Q1: regenerated v2 artifact / extended mapping")

    # ---- panel + selection (C2 step 0 path, v2 verbatim) --------------------
    print("PANEL — mdr.build_panel (one FRED fetch)")
    df = mdr.build_panel()
    df["stratum"] = [build_stratum_id(v_, c_, fb, lb)
                     for v_, c_, fb, lb in zip(df["vintage"], df["coupon"],
                                               df["fico_bucket"],
                                               df["ltv_bucket"])]
    sel = fu._select(df, *lc.R2_SELECTION)
    cpr, _e, n = mdr.cpr_of(sel)
    g_str = int(sel["stratum"].nunique())

    # ---- Q0a: C2's P0 — percentile regeneration bit-exact -------------------
    draws, _n_cl = fu.cluster_bootstrap_cpr(sel)
    se_pp = float(np.std(draws, ddof=1))
    ci_pct = np.percentile(draws, [2.5, 97.5])
    q0a_ok = (abs(cpr - lc.COMMITTED_R2_POINT_PCT) < 1e-9
              and n == lc.COMMITTED_R2_N_COHORT_MONTHS
              and g_str == lc.COMMITTED_R2_N_CLUSTERS
              and abs(se_pp - lc.COMMITTED_R2_SE_PP) < 1e-9
              and abs(ci_pct[0] - lc.COMMITTED_R2_CI95_PCT[0]) < 1e-9
              and abs(ci_pct[1] - lc.COMMITTED_R2_CI95_PCT[1]) < 1e-9)
    gates["Q0a_percentile_regeneration"] = {
        "pass": bool(q0a_ok), "se_pp": se_pp,
        "ci95_pct": [float(ci_pct[0]), float(ci_pct[1])],
        "point_cpr_pct": float(cpr), "n": int(n), "G": g_str}
    if not q0a_ok:
        fail(gates, t0, "Q0a: percentile regeneration missed the committed pins")

    # ---- Q0b: C2's P1 — loan layer ------------------------------------------
    loan = pd.read_csv(lc.LOAN_DRAWS_CSV)
    m_pp = loan["marginal_pp"].to_numpy(dtype=np.float64)
    m_b = loan["marginal_b"].to_numpy(dtype=np.float64)
    loan_ci = np.percentile(m_pp, [2.5, 97.5])
    sd1 = float(np.std(m_pp, ddof=1))
    sd0 = float(np.std(m_pp, ddof=0))
    sd_match = ("ddof1" if abs(sd1 - lc.COMMITTED_LOAN_SD_PP) < 1e-9 else
                "ddof0" if abs(sd0 - lc.COMMITTED_LOAN_SD_PP) < 1e-9 else None)
    q0b_ok = (len(loan) == lc.N_LOAN_REPS
              and abs(loan_ci[0] - lc.COMMITTED_LOAN_CI95_PP[0]) < 1e-9
              and abs(loan_ci[1] - lc.COMMITTED_LOAN_CI95_PP[1]) < 1e-9
              and sd_match is not None)
    gates["Q0b_loan_layer"] = {
        "pass": bool(q0b_ok), "n": len(loan), "sd_convention_matched": sd_match,
        "ci95_pp": [float(loan_ci[0]), float(loan_ci[1])]}
    if not q0b_ok:
        fail(gates, t0, "Q0b: loan draws missed the committed pins")

    # ---- restricted confidence distribution (v2 wcr conventions verbatim) ---
    print("RESTRICTED LAYER — 401-point nested-CI confidence distribution")
    A, W = v2.cluster_sums(sel)
    c = v2.cr_ses(A, W)
    se_cr1 = float(c["se_cr1"])
    assert float(c["R_smm"]) == lc.R_SMM and se_cr1 == lc.SE_CR1_SMM, \
        "R_smm/SE_CR1 differ from the committed values"
    G = len(A)
    Wtot = W.sum()
    fac = G / (G - 1)
    R_hat = A.sum() / Wtot
    rng = np.random.default_rng(v2.SEED)
    s = v2.draw_weights(rng, "webb", G)                 # ONE matrix, reused
    grid = np.linspace(R_hat - v2.WCR_SE_SPAN * se_cr1,
                       R_hat + v2.WCR_SE_SPAN * se_cr1, v2.WCR_N_GRID)
    alpha = np.zeros(v2.WCR_N_GRID)
    retained = np.zeros(v2.WCR_N_GRID, dtype=bool)
    for i, R0 in enumerate(grid):
        e = A - R0 * W
        Astar = R0 * W[None, :] + s * e[None, :]
        Rstar = Astar.sum(axis=1) / Wtot
        ustar = (Astar - Rstar[:, None] * W[None, :]) / Wtot
        sestar = np.sqrt(fac * np.sum(ustar ** 2, axis=1))
        tstar = (Rstar - R0) / sestar
        t_obs = (R_hat - R0) / se_cr1
        q_lo, q_hi = np.percentile(tstar, [2.5, 97.5])
        retained[i] = bool(q_lo <= t_obs <= q_hi)
        u = quantile_position(np.sort(tstar), t_obs)
        alpha[i] = min(u, 1.0 - u)

    # ---- Q2: ties to the adjudicated interval -------------------------------
    alpha_retained = alpha >= RETAIN_ALPHA
    idx = np.flatnonzero(retained)
    sets_equal = bool(np.array_equal(alpha_retained, retained))
    lo_smm, hi_smm = float(grid[idx[0]]), float(grid[idx[-1]])
    lo_pp = v2.map_endpoint(mapping, v2.cpr_pct_of_smm(hi_smm))
    hi_pp = v2.map_endpoint(mapping, v2.cpr_pct_of_smm(lo_smm))
    q2_ok = (sets_equal
             and lo_smm == COMMITTED_SMM_CI[0] and hi_smm == COMMITTED_SMM_CI[1]
             and int(idx.size) == COMMITTED_N_RETAINED
             and abs(lo_pp["marginal_pp"] - REDERIVED_BINDING_PP[0]) < 1e-12
             and abs(hi_pp["marginal_pp"] - REDERIVED_BINDING_PP[1]) < 1e-12)
    gates["Q2_ties_to_adjudicated_interval"] = {
        "pass": bool(q2_ok), "alpha_set_equals_retained_set": sets_equal,
        "n_retained": int(idx.size),
        "smm_ci95": [lo_smm, hi_smm],
        "mapped_pp": [lo_pp["marginal_pp"], hi_pp["marginal_pp"]],
        "want_pp": list(REDERIVED_BINDING_PP)}
    if not q2_ok:
        fail(gates, t0, "Q2: construction does not reproduce the committed "
                        "restricted inversion")
    print(f"  Q2 PASS — retained set ({idx.size}) and endpoints reproduce the "
          f"committed inversion")

    # ---- layer quantile enumeration (FP2-B2-A1) ------------------------------
    u_levels = (np.arange(1, B_LEVELS + 1) - 0.5) / B_LEVELS
    r0_of_u = np.empty(B_LEVELS)
    qualifying = alpha  # nested level sets: {alpha >= u}
    for b, u in enumerate(u_levels):
        thr = u if u < 0.5 else 1.0 - u
        ok_idx = np.flatnonzero(qualifying >= thr)
        # deep tails past the R0 grid's ±5·SE support clamp at the grid end
        if ok_idx.size == 0:
            r0_of_u[b] = grid[0] if u < 0.5 else grid[-1]
            continue
        r0_of_u[b] = grid[ok_idx[0]] if u < 0.5 else grid[ok_idx[-1]]
    n_clamped = int((r0_of_u == grid[0]).sum() + (r0_of_u == grid[-1]).sum())
    floors_pct = lc.cpr_pct_of_smm(np.asarray(r0_of_u, dtype=np.float64))
    fl = lc.map_edge_truncated(mapping, floors_pct)
    ext_convention = ("edge truncation: min(max(floor, 2.0), 7.0) on the "
                      "FP2-B1 extended grid, flagged and counted")
    fl["convention"] = ext_convention
    M_pp, M_b = fl["pp"], fl["b"]
    floor_ci_pp = lc.pct(M_pp)
    floor_width = floor_ci_pp[1] - floor_ci_pp[0]
    # diagnostic only (FP2-B2-A1): deviation of alpha from its unimodal hull
    hull = np.minimum(np.maximum.accumulate(alpha),
                      np.maximum.accumulate(alpha[::-1])[::-1])
    unimodal_dev = float(np.max(hull - alpha))

    # ---- convolution ---------------------------------------------------------
    d_pp = m_pp - lc.CENTER_PP
    d_b = m_b - lc.CENTER_B
    conv_pp = np.add.outer(M_pp, d_pp).ravel()
    conv_b = np.add.outer(M_b, d_b).ravel()
    conv_ci_pp = lc.pct(conv_pp)
    conv_ci_b = lc.pct(conv_b)
    conv_width = conv_ci_pp[1] - conv_ci_pp[0]
    binding_width = REDERIVED_BINDING_PP[1] - REDERIVED_BINDING_PP[0]

    gates["Q3_wider_than_binding"] = {
        "pass": bool(conv_width > binding_width),
        "convolved_width_pp": conv_width, "binding_width_pp": binding_width}
    if not gates["Q3_wider_than_binding"]["pass"]:
        fail(gates, t0, "Q3: convolved narrower than the binding interval")

    # ---- secondary percentile companion (extended map, both conventions) ----
    sec_edge = lc.map_edge_truncated(mapping, draws)
    sec_edge["convention"] = ext_convention
    sec_excl = lc.map_excluded(mapping, draws)
    sec_conv_pp = np.add.outer(sec_edge["pp"], d_pp).ravel()
    sec_ci_pp = lc.pct(sec_conv_pp)

    # ---- dependence bracket (C2's construction, recomputed) ------------------
    loan_width = float(np.percentile(m_pp, 97.5) - np.percentile(m_pp, 2.5))
    comonotone_width = float(floor_width + loan_width)

    predictions = {
        "lower_pp": {"band": PREDICTED_CI95_PP[:2], "realized": conv_ci_pp[0],
                     "hit": bool(PREDICTED_CI95_PP[0] <= conv_ci_pp[0]
                                 <= PREDICTED_CI95_PP[1])},
        "upper_pp": {"band": PREDICTED_CI95_PP[2:], "realized": conv_ci_pp[1],
                     "hit": bool(PREDICTED_CI95_PP[2] <= conv_ci_pp[1]
                                 <= PREDICTED_CI95_PP[3])},
        "width_pp": {"band": PREDICTED_WIDTH_PP, "realized": conv_width,
                     "hit": bool(PREDICTED_WIDTH_PP[0] <= conv_width
                                 <= PREDICTED_WIDTH_PP[1])},
    }

    payload = {
        "mode": "layer_convolution_restricted",
        "status": "OK",
        "spec_source": SPEC,
        "supersedes": ("the committed C2 layer_convolution artifact (Webb "
                       "wild-t floor layer, [2.0, 6.0] grid); it survives in "
                       "git history"),
        "parity_gates": gates,
        "parity_gates_all_pass": True,
        "layers": {
            "floor_restricted_cd": {
                "construction": ("nested-CI confidence distribution of the "
                                 "restricted Webb inversion (FP2-B2-A1); "
                                 "401-point R0 grid, one Webb matrix, "
                                 "default_rng(42)"),
                "ci95_pp": floor_ci_pp, "width_pp": floor_width,
                "n_levels": B_LEVELS,
                "n_levels_clamped_at_R0_grid": n_clamped,
                "alpha_unimodal_hull_max_dev": unimodal_dev,
                "n_truncated_at_edge": fl["n_truncated_at_edge"],
                "n_truncated_above_grid_hi": fl["n_truncated_above_grid_hi"],
                "median_pp": float(np.median(M_pp)),
            },
            "floor_percentile_secondary": {
                "ci95_pp_edge_truncation": lc.pct(sec_edge["pp"]),
                "n_truncated_at_edge": sec_edge["n_truncated_at_edge"],
                "ci95_pp_exclusion": lc.pct(sec_excl["pp"]) if
                    sec_excl["n_retained"] else None,
                "n_draws_outside_grid_excluded": sec_excl["n_draws_outside_grid"],
                "note": ("under the FP2-B1 extended grid the committed "
                         "26-draw clip decensors; the frozen fu artifact and "
                         "its 4 tex sites are UNTOUCHED (SPEC §5)"),
            },
            "loan_cluster": {
                "ci95_pp": [float(loan_ci[0]), float(loan_ci[1])],
                "width_pp": loan_width, "n_reps": len(loan),
                "center_pp": lc.CENTER_PP, "center_b": lc.CENTER_B,
                "sd_convention": sd_match,
            },
        },
        "convolved_primary": {
            "construction": ("exact enumeration of the full outer sum "
                             "{M_b + d_j}, 9,999 x 200, restricted rung"),
            "ci95_pp": conv_ci_pp, "ci95_b": conv_ci_b,
            "median_pp": float(np.median(conv_pp)),
            "sd_pp": float(np.std(conv_pp, ddof=1 if sd_match == "ddof1" else 0)),
            "n_pairs": int(conv_pp.size),
            "width_pp": conv_width,
            "width_ratio_vs_binding": conv_width / binding_width,
        },
        "convolved_percentile_secondary": {"ci95_pp": sec_ci_pp},
        "dependence_bracket": {
            "independent_sum_is_lower_bound": True,
            "comonotone_width_pp": comonotone_width,
            "comonotone_components_pp": {"floor_layer": floor_width,
                                         "loan_layer": loan_width},
        },
        "expectation_check": predictions,
        "verdict": {
            "wider_than_binding": True,
            "convolved_width_pp": conv_width,
            "binding_width_pp": binding_width,
            "width_excess_pp": conv_width - binding_width,
            "no_truncation_on_primary": bool(fl["n_truncated_at_edge"] == 0),
            "manuscript_action": (
                "REPLACE the labeled pair at :308/tab:uncertainty with this "
                "one; the 'lower bound on the re-derived pair' label "
                "RETIRES (truncation count 0) and the one-number "
                "recommendation returns, pointing here (SPEC §4)"),
        },
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=float)
    print(f"\nconvolved primary: [{conv_ci_pp[0]:+.4f}, {conv_ci_pp[1]:+.4f}] pp"
          f"  ([{conv_ci_b[0]:+.2f}, {conv_ci_b[1]:+.2f}] $B)"
          f"  width {conv_width:.4f}pp vs binding {binding_width:.4f}pp")
    for k, v in predictions.items():
        print(f"  prediction {k}: realized {v['realized']:.4f} band {v['band']}"
              f" -> {'HIT' if v['hit'] else 'MISS'}")
    print(f"status OK; fresh -> {RESULTS_JSON}")


if __name__ == "__main__":
    main()
