#!/usr/bin/env python3
"""
floor_inference_correction.py — small-sample-corrected inference for the
floor reads (round-26 panel item B2; referee R1-W1 / DA-C1).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention
of floor_sweep.py / floor_uncertainty.py; this file is committed before its
first execution and its artifact is committed separately after).

Referee objection (round-26 panel, verified CONFIRMED): the manuscript's
binding uncertainty layer [+3.0, +8.0]pp is a 1000-replicate percentile
cluster bootstrap on 31 clusters; percentile cluster bootstraps under-cover
at that cluster count, the tablenote concedes it ("better read as lower
bounds on sampling uncertainty"), and no wild-cluster or small-sample
correction is reported anywhere.

DESIGN (fixed ex ante). NO microsim engine runs anywhere in this script.
Selection, aggregation, cluster unit, and floor->marginal mapping are all
IMPORTED from the committed floor_uncertainty.py / matched_depth_
reconciliation.py machinery, not reimplemented. The floor read is treated as
what it is: a cluster-ratio estimator on the SMM scale,
    R = sum_g A_g / sum_g W_g,   A_g = prepaid_upb, W_g = exposure_upb
summed within cluster g (4-way stratum via stratum.build_stratum_id), with
CPR% = 100*(1-(1-R)^12) a monotone transform applied to interval ENDPOINTS.

Corrections computed per read (reads R1-R4 of floor_uncertainty.py; R5 is
Part-B population support, not an interval input, and is excluded ex ante):
  1. Linearized cluster influences  u_g = (A_g - R*W_g) / sum(W),
     leverages h_g = W_g / sum(W)  (intercept-only WLS leverage).
  2. CR1 variance = G/(G-1) * sum u_g^2 (reported; the uncorrected base).
     CR2: u_g / sqrt(1-h_g).  CR3: u_g / (1-h_g).
     t-intervals: R +/- t_{0.975, G-1} * SE_CRk, endpoints -> CPR%.
  3. Wild-cluster bootstrap-t, Rademacher weights, B = 9999,
     fresh np.random.default_rng(42) per read (per-read determinism):
       A*_g = W_g*R + s_g*(A_g - R*W_g),  s_g in {-1,+1}
       R*   = sum A*_g / sum W_g
       u*_g = (A*_g - R**W_g) / sum(W);  SE* = sqrt(G/(G-1) * sum u*_g^2)
       t*   = (R* - R) / SE*
     Equal-tailed percentile-t CI:
       [ R - q_{0.975}(t*)*SE_CR1 ,  R - q_{0.025}(t*)*SE_CR1 ]
     endpoints -> CPR%.
  4. Each corrected floor CI is mapped through the committed FloorMapping
     PCHIP (grid [2.0, 6.0]% CPR; NEVER extrapolated) to the marginal at the
     central elasticity 6.5. An endpoint falling outside the grid is mapped
     AT the nearest grid edge and flagged truncated_at_grid_edge, with the
     direction stated (the marginal decreases in the floor, so a floor
     endpoint above 6.0% yields a marginal edge that is an UPPER bound on
     the truncated true edge). This differs from the committed percentile
     convention (which excludes out-of-grid draws); the artifact reports the
     flag wherever it fires and the comparison rule below is applied to the
     as-reported values with the flag disclosed.

PRIMARY OBJECT (fixed ex ante): the R2 anchor's wild-cluster bootstrap-t
interval, mapped to marginal pp at 6.5 — compared against the committed
percentile interval [+2.974329560125351, +8.01850965353176] pp
(floor_uncertainty_results.json, mf4_binding_uncertainty.sampling_ci95_pp,
the manuscript's [+3.0, +8.0]). CR2-t and CR3-t are SECONDARY (reported,
no rule attached).

EX-ANTE INTERPRETIVE RULE (verbatim; no discretion after the run):
  Let [L*, U*] = primary corrected interval (pp), [Lp, Up] = committed
  percentile interval above.
  CONFIRMS  if |L*-Lp| <= 0.5pp AND |U*-Up| <= 0.5pp.
            Manuscript action is then LIMITED to: (i) one clause in the
            tab:uncertainty tablenote reporting that the wild-cluster
            bootstrap-t interval confirms the percentile layer (numbers
            quoted from this artifact); (ii) the round-26 three-site
            few-cluster qualifier labels (abstract, tab:headline,
            conclusion), which are warranted under either verdict.
            The binding-layer language and every [+3.0, +8.0] literal
            stay unchanged.
  MOVES     otherwise. The artifact is committed and the result REPORTED;
            no manuscript number is restated in the same session — how to
            restate the binding layer is the author's call, made against
            this artifact. The three-site qualifier labels still land
            (they are strictly more warranted under MOVES).
  Also reported, both verdicts: whether L* > 0 and whether L* >= +3.0
  (the committed lower edge), and max leverage per read.

PARITY GATES (BLOCKING; on any failure the JSON is written with status
GATE_FAILURE and the run stops):
  P1  R1-R4 point reads reproduce the frozen floor_uncertainty artifact's
      point_cpr_pct to 1e-9 with equal n_cohort_months and n_clusters
      (5.334239649398553/155/31, 4.990624060575566/137/31,
       4.695495330057254/125/25, 3.9719264231555695/2838/226).
  P2  The committed percentile bootstrap is reproduced BIT-EXACTLY for R2
      via the imported floor_uncertainty.cluster_bootstrap_cpr (rng 42):
      se_pp = 0.3933971547430653, ci95_pct = [4.368576777908708,
      6.003552252675821], and the mapped ci95_pp equals
      [2.974329560125351, 8.01850965353176] (all 1e-9), via the imported
      floor_uncertainty._map_draws.
  P3  FloorMapping reproduces the committed floor_sweep grid exactly and
      max |mapped - engine| <= $0.69B on the committed oos rows (asserted
      from the frozen artifact's own mapping_fidelity block).

Run:  cd hazard && python3 floor_inference_correction.py
      -> data/floor_inference_correction_results.json  (frozen)
No engine runs; runtime seconds (one FRED MORTGAGE30US fetch via
build_panel). Does NOT change config.py production defaults. Does NOT edit
any .tex file.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import floor_uncertainty as fu
import matched_depth_reconciliation as mdr
from stratum import build_stratum_id

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "floor_inference_correction_results.json"
FU_ARTIFACT = DATA_DIR / "floor_uncertainty_results.json"

B_WILD = 9999
SEED = 42
CENTRAL_PQ = "6.5"
RULE_TOL_PP = 0.5

# committed values quoted ex ante (asserted vs the frozen artifact at runtime)
COMMITTED_POINTS = {  # read -> (point_cpr_pct, n_cohort_months, n_clusters)
    "R1_2018_gap<=+0.0000_age>=12": (5.334239649398553, 155, 31),
    "R2_2018_gap<=-0.0025_age>=12": (4.990624060575566, 137, 31),
    "R3_2018_gap<=-0.0050_age>=12": (4.695495330057254, 125, 25),
    "R4_inwindow_calib_202206_202312_gap<=-0.02_age>=12":
        (3.9719264231555695, 2838, 226),
}
R2 = "R2_2018_gap<=-0.0025_age>=12"
COMMITTED_R2_SE_PP = 0.3933971547430653
COMMITTED_R2_CI95_PCT = (4.368576777908708, 6.003552252675821)
COMMITTED_PERCENTILE_PP = (2.974329560125351, 8.01850965353176)
GRID_LO, GRID_HI = 2.0, 6.0

READ_SELECTIONS = {  # read -> (rp_lo, rp_hi, gap_thr, age_min)
    "R1_2018_gap<=+0.0000_age>=12": (*fu.LEG_2018, 0.0, 12),
    "R2_2018_gap<=-0.0025_age>=12": (*fu.LEG_2018, -0.0025, 12),
    "R3_2018_gap<=-0.0050_age>=12": (*fu.LEG_2018, -0.005, 12),
    "R4_inwindow_calib_202206_202312_gap<=-0.02_age>=12":
        (*fu.CALIB_WINDOW, -0.02, 12),
}


def cpr_pct_of_smm(smm: float) -> float:
    return 100.0 * (1.0 - (1.0 - smm) ** 12)


def cluster_sums(sel: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    g = sel.groupby("stratum", sort=True)[["prepaid_upb", "exposure_upb"]].sum()
    return (g["prepaid_upb"].to_numpy(np.float64),
            g["exposure_upb"].to_numpy(np.float64))


def cr_ses(A: np.ndarray, W: np.ndarray) -> dict:
    Wtot = W.sum()
    R = A.sum() / Wtot
    u = (A - R * W) / Wtot
    h = W / Wtot
    G = len(A)
    fac = G / (G - 1)
    return {
        "R_smm": R, "G": G, "max_leverage": float(h.max()),
        "se_cr1": float(np.sqrt(fac * np.sum(u ** 2))),
        "se_cr2": float(np.sqrt(fac * np.sum((u / np.sqrt(1.0 - h)) ** 2))),
        "se_cr3": float(np.sqrt(fac * np.sum((u / (1.0 - h)) ** 2))),
        "_u": u, "_h": h,
    }


def wild_t_ci(A: np.ndarray, W: np.ndarray, se_cr1_smm: float,
              rng: np.random.Generator) -> tuple[float, float, np.ndarray]:
    Wtot = W.sum()
    R = A.sum() / Wtot
    G = len(A)
    fac = G / (G - 1)
    resid = A - R * W                     # (G,)
    s = rng.choice([-1.0, 1.0], size=(B_WILD, G))
    Astar = W[None, :] * R + s * resid[None, :]          # (B, G)
    Rstar = Astar.sum(axis=1) / Wtot                     # (B,)
    ustar = (Astar - Rstar[:, None] * W[None, :]) / Wtot
    sestar = np.sqrt(fac * np.sum(ustar ** 2, axis=1))
    tstar = (Rstar - R) / sestar
    q_lo, q_hi = np.percentile(tstar, [2.5, 97.5])
    return (R - q_hi * se_cr1_smm, R - q_lo * se_cr1_smm), tstar, R


def map_endpoint(mapping: mdr.FloorMapping, floor_pct: float) -> dict:
    trunc = not mapping.in_grid(floor_pct)
    x = min(max(floor_pct, GRID_LO), GRID_HI)
    b, pp = mapping(x)
    return {"floor_pct": float(floor_pct), "mapped_at_pct": float(x),
            "truncated_at_grid_edge": bool(trunc),
            "marginal_b": float(b), "marginal_pp": float(pp)}


def map_floor_ci(mapping: mdr.FloorMapping, lo_pct: float, hi_pct: float) -> dict:
    # marginal decreases in the floor: floor lo -> pp hi, floor hi -> pp lo
    hi_end = map_endpoint(mapping, lo_pct)
    lo_end = map_endpoint(mapping, hi_pct)
    return {
        "floor_ci95_pct": [float(lo_pct), float(hi_pct)],
        "marginal_ci95_pp": [lo_end["marginal_pp"], hi_end["marginal_pp"]],
        "marginal_ci95_b": [lo_end["marginal_b"], hi_end["marginal_b"]],
        "lower_pp_edge": lo_end, "upper_pp_edge": hi_end,
    }


def main() -> None:
    t0 = time.perf_counter()
    with open(FU_ARTIFACT) as f:
        fua = json.load(f)
    assert fua.get("status") == "OK" and fua.get("parity_gates_all_pass")
    fu_reads = fua["part_a_sampling_uncertainty"]["reads"]
    mf4 = fua["part_a_sampling_uncertainty"]["mf4_binding_uncertainty"]
    assert abs(mf4["sampling_ci95_pp"][0] - COMMITTED_PERCENTILE_PP[0]) < 1e-9
    assert abs(mf4["sampling_ci95_pp"][1] - COMMITTED_PERCENTILE_PP[1]) < 1e-9

    print("PANEL — matched_depth_reconciliation.build_panel")
    df = mdr.build_panel()
    df["stratum"] = [
        build_stratum_id(v, c, fb, lb)
        for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                df["fico_bucket"], df["ltv_bucket"])
    ]

    gate_report: dict = {}
    selections: dict[str, pd.DataFrame] = {}
    # ---- P1 ---------------------------------------------------------------
    for name, (lo, hi, gthr, amin) in READ_SELECTIONS.items():
        sel = fu._select(df, lo, hi, gthr, amin)
        selections[name] = sel
        cpr, _exp, n = mdr.cpr_of(sel)
        n_cl = sel["stratum"].nunique()
        want_cpr, want_n, want_cl = COMMITTED_POINTS[name]
        art = fu_reads[name]
        ok = (abs(cpr - want_cpr) < 1e-9 and n == want_n and n_cl == want_cl
              and abs(art["point_cpr_pct"] - want_cpr) < 1e-9)
        gate_report[f"P1_{name}"] = {
            "got_cpr_pct": float(cpr), "want_cpr_pct": want_cpr,
            "got_n": int(n), "want_n": want_n,
            "got_clusters": int(n_cl), "want_clusters": want_cl, "pass": ok}
        print(f"  P1 {name}: {cpr:.9f}% n={n} G={n_cl} "
              f"[{'PASS' if ok else 'FAIL'}]")
    # ---- P2 (bit-exact percentile reproduction, R2) -----------------------
    draws, n_cl = fu.cluster_bootstrap_cpr(selections[R2])
    se_pp = float(np.std(draws, ddof=1))
    ci = np.percentile(draws, [2.5, 97.5])
    mapping = mdr.FloorMapping()
    mapped = fu._map_draws(mapping, draws)
    p2_ok = (abs(se_pp - COMMITTED_R2_SE_PP) < 1e-9
             and abs(ci[0] - COMMITTED_R2_CI95_PCT[0]) < 1e-9
             and abs(ci[1] - COMMITTED_R2_CI95_PCT[1]) < 1e-9
             and abs(mapped["ci95_pp"][0] - COMMITTED_PERCENTILE_PP[0]) < 1e-9
             and abs(mapped["ci95_pp"][1] - COMMITTED_PERCENTILE_PP[1]) < 1e-9)
    gate_report["P2_percentile_bitexact_R2"] = {
        "got_se_pp": se_pp, "want_se_pp": COMMITTED_R2_SE_PP,
        "got_ci95_pct": [float(ci[0]), float(ci[1])],
        "want_ci95_pct": list(COMMITTED_R2_CI95_PCT),
        "got_mapped_pp": mapped["ci95_pp"],
        "want_mapped_pp": list(COMMITTED_PERCENTILE_PP), "pass": p2_ok}
    print(f"  P2 R2 percentile bit-exact: [{'PASS' if p2_ok else 'FAIL'}]")
    # ---- P3 ---------------------------------------------------------------
    mfid = fua["mapping_fidelity"]
    p3_ok = (mfid["reproduces_committed_grid_exactly"]
             and mfid["max_abs_err_b_inside_grid"] <= 0.69)
    gate_report["P3_mapping_fidelity"] = {
        "reproduces_committed_grid_exactly":
            mfid["reproduces_committed_grid_exactly"],
        "max_abs_err_b_inside_grid": mfid["max_abs_err_b_inside_grid"],
        "tol_b": 0.69, "pass": bool(p3_ok)}
    print(f"  P3 mapping fidelity: [{'PASS' if p3_ok else 'FAIL'}]")

    if not all(v["pass"] for v in gate_report.values()):
        payload = {"mode": "floor_inference_correction",
                   "status": "GATE_FAILURE", "parity_gates": gate_report}
        with open(RESULTS_JSON, "w") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        raise SystemExit("PARITY GATE FAILURE — STOP. "
                         f"Diagnostics in {RESULTS_JSON}.")

    # ---- corrections ------------------------------------------------------
    out_reads: dict = {}
    for name, sel in selections.items():
        A, W = cluster_sums(sel)
        c = cr_ses(A, W)
        G = c["G"]
        tcrit = float(stats.t.ppf(0.975, G - 1))
        read: dict = {"n_clusters": G, "t_crit_G_minus_1": tcrit,
                      "max_leverage": c["max_leverage"],
                      "point_cpr_pct": cpr_pct_of_smm(c["R_smm"])}
        for k in ("cr1", "cr2", "cr3"):
            se = c[f"se_{k}"]
            lo, hi = c["R_smm"] - tcrit * se, c["R_smm"] + tcrit * se
            read[f"{k}_t_interval"] = map_floor_ci(
                mapping, cpr_pct_of_smm(lo), cpr_pct_of_smm(hi))
            read[f"{k}_se_pp_approx"] = (cpr_pct_of_smm(c["R_smm"] + se)
                                         - cpr_pct_of_smm(c["R_smm"]))
        rng = np.random.default_rng(SEED)
        (lo_smm, hi_smm), tstar, _R = wild_t_ci(A, W, c["se_cr1"], rng)
        read["wild_t"] = {
            "B": B_WILD, "seed": SEED, "weights": "rademacher",
            "t_star_q": [float(np.percentile(tstar, 2.5)),
                         float(np.percentile(tstar, 97.5))],
            **map_floor_ci(mapping, cpr_pct_of_smm(lo_smm),
                           cpr_pct_of_smm(hi_smm)),
        }
        out_reads[name] = read

    # ---- the rule ---------------------------------------------------------
    prim = out_reads[R2]["wild_t"]["marginal_ci95_pp"]
    Lp, Up = COMMITTED_PERCENTILE_PP
    dL, dU = abs(prim[0] - Lp), abs(prim[1] - Up)
    confirms = dL <= RULE_TOL_PP and dU <= RULE_TOL_PP
    verdict = {
        "primary": "R2 wild-cluster bootstrap-t, mapped, pp at 6.5",
        "corrected_pp": prim,
        "committed_percentile_pp": [Lp, Up],
        "delta_lower_pp": float(dL), "delta_upper_pp": float(dU),
        "rule_tol_pp": RULE_TOL_PP,
        "code": "CONFIRMS" if confirms else "MOVES",
        "lower_edge_above_zero": bool(prim[0] > 0.0),
        "lower_edge_at_or_above_committed_3.0": bool(prim[0] >= 3.0),
        "truncation_flags": {
            "lower": out_reads[R2]["wild_t"]["lower_pp_edge"][
                "truncated_at_grid_edge"],
            "upper": out_reads[R2]["wild_t"]["upper_pp_edge"][
                "truncated_at_grid_edge"]},
        "manuscript_action": (
            "CONFIRMS: add one tab:uncertainty tablenote clause quoting this "
            "interval as confirming the percentile layer; land the three-site "
            "qualifier labels; binding-layer language unchanged."
            if confirms else
            "MOVES: artifact committed and reported; no manuscript number "
            "restated this session; three-site qualifier labels still land."),
    }
    payload = {
        "mode": "floor_inference_correction", "status": "OK",
        "spec": ("CR1/CR2/CR3 t(G-1) intervals + Rademacher wild-cluster "
                 "bootstrap-t (B=9999, rng 42/read) on the cluster-ratio "
                 "floor reads R1-R4, endpoints transformed SMM->CPR% and "
                 "mapped through the committed FloorMapping PCHIP "
                 "(extrapolation refused, endpoints truncated at grid edge "
                 "and flagged); primary object R2 wild-t vs committed "
                 "percentile [+2.9743, +8.0185]pp; ex-ante rule at 0.5pp."),
        "parity_gates": gate_report, "parity_gates_all_pass": True,
        "reads": out_reads, "verdict": verdict,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda x: float(x)
                  if isinstance(x, (np.floating, np.integer)) else x)
        f.write("\n")
    print(json.dumps(verdict, indent=2))
    print(f"\nfrozen -> {RESULTS_JSON}")


if __name__ == "__main__":
    main()
