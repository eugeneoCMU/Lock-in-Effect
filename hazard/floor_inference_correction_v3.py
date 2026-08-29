#!/usr/bin/env python3
"""R32 / C-72: month-clustered and two-way (stratum x month) ladder rungs.

Run tag: floor_inference_correction_v3.  Spec: specs/SPEC_R32_c72_month_and_twoway_clusters.md,
committed before this script was written, and this script committed before it ran.

The committed cluster unit is cross-sectional only.  This run prices the month-level common shock
the current scheme cannot see, or shows it does not matter.

TWO FRAMING CORRECTIONS the spec records and this runner enforces:
  (a) the cluster unit is NOT a function parameter -- floor_uncertainty.py:206 and
      floor_inference_correction_v2.cluster_sums both hard-code groupby("stratum").  Month
      clustering is a DATA SUBSTITUTION, performed explicitly and recorded per rung (P3).
  (b) two-way FIXED EFFECTS (unidentified) is not two-way CLUSTERING (computable; its failure
      modes are a non-positive-definite variance and a tiny df).  NC-2 refuses the standard
      zero-truncation fix rather than manufacturing a usable SE from an unusable estimate.

v1 and v2 and their artifacts are FROZEN: read, never written.  No engine runs; one FRED fetch
inside the imported build_panel.

Writes ONLY data/floor_inference_correction_v3_results.json (+ v3_-prefixed t* CSVs).

Run:  cd hazard && python3 floor_inference_correction_v3.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HAZ = Path(__file__).resolve().parent
ROOT = HAZ.parent
if str(HAZ) not in sys.path:
    sys.path.insert(0, str(HAZ))

import floor_uncertainty as fu                      # noqa: E402
import floor_inference_correction_v2 as v2          # noqa: E402
import matched_depth_reconciliation as mdr          # noqa: E402
from stratum import build_stratum_id                # noqa: E402

DATA = HAZ / "data"
OUT = DATA / "floor_inference_correction_v3_results.json"
V2_ARTIFACT = DATA / "floor_inference_correction_v2_results.json"     # FROZEN
FU_ARTIFACT = DATA / "floor_uncertainty_results.json"                 # FROZEN

PINS = {
    HAZ / "floor_uncertainty.py":
        "ab8bb3b4df49890c0c9fb7dcc0e250f5e4c427f11b557122f4b4d6e43875c02c",
    HAZ / "floor_inference_correction.py":
        "df6592dacda71d323c597d1d48a2328c6753a14032509b80acb5a16e4a87f969",
    # v2.py / mdr.py / V2_ARTIFACT re-pinned 2026-08-29 to the FP2-B1-amended
    # sources and the regenerated (extended-grid) v2 artifact; fu.py and v1
    # are untouched by FP2-B1 and keep their original pins.
    HAZ / "floor_inference_correction_v2.py":
        "2ecff971f96cd1f679a22eb058b8e008c9853142ff6d50a6a825ff37e1e40909",
    HAZ / "matched_depth_reconciliation.py":
        "96fd5f2764c42bbd0ca4852b1ec7e1b7d972e339134655f47d924f0852b91e89",
    FU_ARTIFACT: "83a90ee247315ca771fb6dec512578c012434f67c5d216acdf019d3783beb4f3",
    V2_ARTIFACT: "bc622a83d42fc1701bd3d4fa56eac80d6758dc3054462945207f743159387e5e",
}

R2 = "R2_2018_gap<=-0.0025_age>=12"
R2_SELECTION = (201801, 201812, -0.0025, 12)
PIN_POINT_CPR = 4.990624060575566
PIN_N = 137
PIN_G_STRATUM = 31

NC1_MIN_MONTH_CLUSTERS = 5          # spec section 6
NC4_RADEMACHER_G = 8                # resolution-floor disclosure threshold
CR1_COMMITTED_WIDTH_PP = None       # filled live from v2 (E3's bar)


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _is_syspath_bootstrap(node: ast.If) -> bool:
    """The repo's standard `if str(DIR) not in sys.path: sys.path.insert(...)` idiom.

    Accepted because it mutates sys.path and nothing else -- it computes no value, reads no
    artifact and calls into no engine. Anything else in a top-level If is still rejected.
    """
    if "sys.path" not in ast.unparse(node.test):
        return False
    if node.orelse:
        return False
    for stmt in node.body:
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
            return False
        fn = ast.unparse(stmt.value.func)
        if fn not in ("sys.path.insert", "sys.path.append"):
            return False
    return True


def ast_binds_names_only(path: Path) -> bool:
    tree = ast.parse(path.read_text())
    binding = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
               ast.ClassDef, ast.Assign, ast.AnnAssign)
    for node in tree.body:
        if isinstance(node, binding):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.If):
            if ast.unparse(node.test) == "__name__ == '__main__'":
                continue
            if _is_syspath_bootstrap(node):
                continue
            return False
        return False
    return True


def rung(sel: pd.DataFrame, cluster_col: str, mapping) -> dict:
    """v2's per-read block, replicated with the cluster unit made explicit.

    The substitution is visible: when cluster_col != 'stratum' the frame's 'stratum' column is
    OVERWRITTEN with that column before v2.cluster_sums (which hard-codes groupby('stratum'))
    is called, and the column actually grouped on is recorded in the output.
    """
    work = sel.copy()
    if cluster_col != "stratum":
        work["stratum"] = work[cluster_col].astype(str)
    A, W = v2.cluster_sums(work)
    c = v2.cr_ses(A, W)
    G, h = c["G"], c["_h"]
    tcrit = float(stats.t.ppf(0.975, G - 1))
    g_star, sum_h_sq = v2.css_effective_clusters(h)
    df_bm = {k: v2.bm_ik_df(h, p) for k, p in (("cr1", 0.0), ("cr2", 0.5), ("cr3", 1.0))}
    tcrit_bm = {k: float(stats.t.ppf(0.975, v)) for k, v in df_bm.items()}

    out: dict = {
        "cluster_column_grouped_on": cluster_col,
        "n_clusters": G,
        "n_cohort_months": int(len(work)),
        "cluster_labels": sorted(work["stratum"].unique().tolist())[:60],
        "point_cpr_pct": v2.cpr_pct_of_smm(c["R_smm"]),
        "R_smm": float(c["R_smm"]),
        "se_cr1_smm": c["se_cr1"], "se_cr2_smm": c["se_cr2"], "se_cr3_smm": c["se_cr3"],
        "t_crit_G_minus_1": tcrit, "max_leverage": c["max_leverage"],
        "sum_h": float(h.sum()), "sum_h_sq": sum_h_sq, "h_max": float(h.max()),
        "G_star_css": g_star,
        "df_bm": df_bm["cr2"], "t_crit_df_bm": tcrit_bm["cr2"],
        "df_bm_by_estimator": df_bm, "t_crit_df_bm_by_estimator": tcrit_bm,
    }
    for k in ("cr1", "cr2", "cr3"):
        se = c[f"se_{k}"]
        lo, hi = c["R_smm"] - tcrit * se, c["R_smm"] + tcrit * se
        out[f"{k}_t_interval"] = {
            **v2.map_floor_ci(mapping, v2.cpr_pct_of_smm(lo), v2.cpr_pct_of_smm(hi)),
            "df_used": float(G - 1), "df_kind": "G_minus_1", "t_crit": tcrit}
        lo_b = c["R_smm"] - tcrit_bm[k] * se
        hi_b = c["R_smm"] + tcrit_bm[k] * se
        out[f"{k}_t_interval_df_bm"] = {
            **v2.map_floor_ci(mapping, v2.cpr_pct_of_smm(lo_b), v2.cpr_pct_of_smm(hi_b)),
            "df_used": df_bm[k], "df_kind": "bell_mccaffrey_imbens_kolesar",
            "t_crit": tcrit_bm[k]}
    for scheme, tag in (("rademacher", "wild_t_rademacher"), ("webb", "wild_t_webb")):
        rng = np.random.default_rng(v2.SEED)
        (lo_smm, hi_smm), tstar, _s, _R = v2.wild_t_ci(A, W, c["se_cr1"], rng, scheme)
        out[tag] = {
            **v2.map_floor_ci(mapping, v2.cpr_pct_of_smm(lo_smm), v2.cpr_pct_of_smm(hi_smm)),
            "scheme": scheme, "B": v2.B_WILD,
            "t_star_q025": float(np.percentile(tstar, 2.5)),
            "t_star_q975": float(np.percentile(tstar, 97.5)),
        }
        if scheme == "rademacher":
            out[tag]["distinct_sign_vectors"] = float(2.0 ** G)
            out[tag]["resolution_floor_p"] = float(2.0 ** -G)
            out[tag]["NC4_resolution_disclosure"] = bool(G <= NC4_RADEMACHER_G)
    out["_A"], out["_W"] = A, W
    return out


def main() -> None:
    t0 = time.perf_counter()

    # ---- P0 / P0a / P0b ----------------------------------------------------
    for p, want in PINS.items():
        got = sha(p)
        if got != want:
            stop("P0", f"{p.relative_to(ROOT)} sha256 {got} != pinned {want}")
    pre = {str(p.relative_to(ROOT)): sha(p) for p in PINS}
    for p in (HAZ / "floor_uncertainty.py", HAZ / "floor_inference_correction_v2.py",
              HAZ / "matched_depth_reconciliation.py"):
        if not ast_binds_names_only(p):
            stop("P0a", f"{p.name} does more than bind names at top level")

    v2art = json.loads(V2_ARTIFACT.read_text())
    if v2art.get("status") != "OK" or not v2art.get("parity_gates_all_pass"):
        stop("P1", "v2 artifact is not a clean OK/all-pass run")
    v2r2 = v2art["reads"][R2]

    # ---- P5: BM df self-test at the new G, replayed -------------------------
    p5 = {}
    for G in (2, 3, 5, 6, 8, 12, 31):
        for power, tag in ((0.0, "cr1"), (0.5, "cr2"), (1.0, "cr3")):
            got = v2.bm_ik_df(np.full(G, 1.0 / G), power)
            p5[f"G{G}_{tag}"] = {"df": got, "want": G - 1, "abs_err": abs(got - (G - 1))}
    p5_max = max(v["abs_err"] for v in p5.values())
    if p5_max > 1e-9:
        stop("P5", f"BM df self-test max err {p5_max:.3e}")

    # ---- panel + selection --------------------------------------------------
    print("PANEL — matched_depth_reconciliation.build_panel (one FRED fetch)")
    df = mdr.build_panel()
    df["stratum"] = [build_stratum_id(v, c, fb, lb)
                     for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                             df["fico_bucket"], df["ltv_bucket"])]
    sel = fu._select(df, *R2_SELECTION)
    cpr, _e, n = mdr.cpr_of(sel)
    g_str = int(sel["stratum"].nunique())
    if abs(cpr - PIN_POINT_CPR) > 1e-9 or n != PIN_N or g_str != PIN_G_STRATUM:
        stop("P2", f"R2 selection moved: {cpr!r}/{n}/{g_str} != "
                   f"{PIN_POINT_CPR!r}/{PIN_N}/{PIN_G_STRATUM}")
    print(f"  P2 R2: {cpr:.9f}%  n={n}  G_stratum={g_str}  [PASS]")

    mapping = mdr.FloorMapping(extended=True)   # FP2-B1 extended grid
    v2.mapping_global = mapping

    # ---- P4: truncation, not exclusion --------------------------------------
    # deliberately outside [2.0, 7.0] (FP2-B1 extended grid; edge was 6.0)
    probe = v2.map_endpoint(mapping, 7.5)
    if not probe["truncated_at_grid_edge"] or abs(probe["mapped_at_pct"] - 7.0) > 1e-12:
        stop("P4", f"grid-edge convention is not v1's truncation: {probe}")

    # ---- E2 (STOP): feasibility BEFORE any interval is read ------------------
    sel = sel.copy()
    sel["month"] = sel["rp"].astype(int).astype(str)
    months = sorted(sel["month"].unique().tolist())
    g_month = len(months)
    per_month = {m: int((sel["month"] == m).sum()) for m in months}
    cells = sel.groupby(["stratum", "month"]).size()
    feasibility = {
        "G_stratum": g_str, "G_month": g_month,
        "months": months, "cohort_months_per_month": per_month,
        "n_stratum_month_cells": int(len(cells)),
        "computed_before_any_interval_was_read": True,
        "ceiling_note": ("the selection is calendar 2018 so G_month <= 12 by construction; the "
                         "realized count is measured here, not asserted"),
    }
    print(f"  E2 feasibility: G_month = {g_month} ({months[0]}..{months[-1]}), "
          f"{len(cells)} stratum-month cells")

    nc1 = g_month < NC1_MIN_MONTH_CLUSTERS

    # ---- P1: the stratum rung replays v2 bit-identically ---------------------
    strat = rung(sel, "stratum", mapping)
    p1 = {}
    for field in ("cr1_t_interval", "cr1_t_interval_df_bm", "cr3_t_interval"):
        got = strat[field]["marginal_ci95_pp"]
        want = v2r2[field]["marginal_ci95_pp"]
        p1[field] = {"got": got, "want": want, "exact": got == want}
        if got != want:
            stop("P1", f"{field} does not replay v2: {got!r} != {want!r}")
    got_w = strat["wild_t_webb"]["floor_ci95_pct"]
    want_w = v2r2["wild_t_webb"]["floor_ci95_pct"]
    p1["wild_t_webb_floor_ci95_pct"] = {"got": got_w, "want": want_w, "exact": got_w == want_w}
    if got_w != want_w:
        stop("P1", f"wild_t_webb floor CI does not replay v2: {got_w!r} != {want_w!r}")
    for k, v in v2r2["df_bm_by_estimator"].items():
        if abs(strat["df_bm_by_estimator"][k] - v) > 1e-12:
            stop("P1", f"df_bm {k} does not replay v2")
    p1["df_bm_by_estimator"] = {"got": strat["df_bm_by_estimator"],
                                "want": v2r2["df_bm_by_estimator"]}
    print("  P1 stratum rung replays v2 bit-identically  [PASS]")

    cr1_pp = strat["cr1_t_interval"]["marginal_ci95_pp"]
    committed_width = abs(cr1_pp[1] - cr1_pp[0])

    # ---- the month rung -----------------------------------------------------
    month_rung = None if nc1 else rung(sel, "month", mapping)

    # ---- two-way (stratum x month), Cameron-Gelbach-Miller ------------------
    def v_cr1(labels: pd.Series) -> tuple[float, int]:
        w = sel.copy()
        w["stratum"] = labels.astype(str)
        A, W = v2.cluster_sums(w)
        Wt = W.sum()
        R = A.sum() / Wt
        u = (A - R * W) / Wt
        G = len(A)
        return float(G / (G - 1) * np.sum(u ** 2)), G

    v_s, gs = v_cr1(sel["stratum"])
    v_m, gm = v_cr1(sel["month"])
    v_i, gi = v_cr1(sel["stratum"].astype(str) + "|" + sel["month"].astype(str))
    v_2way = v_s + v_m - v_i
    df_2way = min(gs, gm) - 1
    A0, W0 = v2.cluster_sums(sel)
    R0 = A0.sum() / W0.sum()

    twoway: dict = {
        "method": "Cameron-Gelbach-Miller: V_2way = V_stratum + V_month - V_intersection",
        "V_stratum": v_s, "V_month": v_m, "V_intersection": v_i, "V_2way": v_2way,
        "G_stratum": gs, "G_month": gm, "G_intersection_cells": gi,
        "df_2way": df_2way,
        "framing_note": ("two-way FIXED EFFECTS is a different object from two-way CLUSTERING; "
                         "limb_c's 'EXACTLY unidentified' is about the former and does not carry "
                         "over here"),
    }
    if v_2way <= 0:
        twoway["computable"] = False
        twoway["NC2"] = (
            "NOT_COMPUTABLE: the two-way variance estimate is non-positive. The standard "
            "zero-truncation fix is REFUSED, not overlooked -- truncating a negative variance "
            "to zero manufactures a usable standard error out of an unusable estimate, and a "
            "rung built that way would look like inference without being it. The eigenvalue "
            "correction is likewise not substituted.")
    else:
        se_2way = float(np.sqrt(v_2way))
        tcrit2 = float(stats.t.ppf(0.975, df_2way))
        lo, hi = R0 - tcrit2 * se_2way, R0 + tcrit2 * se_2way
        twoway["computable"] = True
        twoway["se_2way_smm"] = se_2way
        twoway["t_crit"] = tcrit2
        twoway["t_interval"] = v2.map_floor_ci(
            mapping, v2.cpr_pct_of_smm(lo), v2.cpr_pct_of_smm(hi))

    # ---- expectations --------------------------------------------------------
    e3 = e4 = None
    nc3 = False
    if month_rung is not None:
        m_pp = month_rung["cr1_t_interval"]["marginal_ci95_pp"]
        month_width = abs(m_pp[1] - m_pp[0])
        e3 = bool(month_width > committed_width)
        edges = month_rung["cr1_t_interval"]
        e4 = bool(edges["upper_pp_edge"]["truncated_at_grid_edge"]
                  or edges["lower_pp_edge"]["truncated_at_grid_edge"])
        nc3 = bool(edges["upper_pp_edge"]["truncated_at_grid_edge"]
                   and edges["lower_pp_edge"]["truncated_at_grid_edge"])

    for r in (strat, month_rung):
        if r is not None:
            r.pop("_A", None)
            r.pop("_W", None)

    payload = {
        "mode": "floor_inference_correction_v3", "run_tag": "floor_inference_correction_v3",
        "status": "OK",
        "spec": {
            "spec_file": "specs/SPEC_R32_c72_month_and_twoway_clusters.md",
            "read": R2, "selection": list(R2_SELECTION),
            "cluster_unit_is_a_column_not_an_argument": (
                "floor_uncertainty.py:206 and v2.cluster_sums both hard-code "
                "groupby('stratum'); month clustering is a visible data substitution"),
            "grid_convention": ("v1's grid-edge TRUNCATION (map at the nearest edge, flag it), "
                                "never _map_draws's exclusion convention"),
            "frozen": "v1, v2 and their artifacts are read, never written",
            "no_engine_runs": True,
        },
        "parity": {
            "P0_sha_pins": {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
            "P0a_modules_bind_names_only": True,
            "P1_stratum_rung_replays_v2": p1,
            "P2_selection": {"point_cpr_pct": float(cpr), "n": int(n), "G": g_str},
            "P4_truncation_probe": probe,
            "P5_bm_df_selftest_max_err": p5_max, "P5_cells": p5,
        },
        "feasibility": feasibility,
        "rungs": {"stratum_committed": strat, "month": month_rung},
        "two_way": twoway,
        "not_computable": {
            "NC1_too_few_month_clusters": {"triggered": nc1,
                                           "threshold": NC1_MIN_MONTH_CLUSTERS,
                                           "G_month": g_month},
            "NC2_two_way_variance_non_positive": {"triggered": not twoway["computable"]},
            "NC3_both_endpoints_off_grid": {"triggered": nc3},
            "NC4_rademacher_resolution_floor": {
                "triggered": bool(g_month <= NC4_RADEMACHER_G),
                "note": ("Webb six-point is PRIMARY; the Rademacher variant carries a hard "
                         "p-value resolution floor of 2^-G_month and is reported with it"),
            },
        },
        "expectations": {
            "E1_stratum_replay_bit_identical": True,
            "E2_feasibility_before_outcome": True,
            "E3_month_widens": e3,
            "E3_committed_cr1_width_pp": committed_width,
            "E3_month_cr1_width_pp": (abs(month_rung["cr1_t_interval"]["marginal_ci95_pp"][1]
                                          - month_rung["cr1_t_interval"]["marginal_ci95_pp"][0])
                                      if month_rung else None),
            "E4_upper_endpoint_truncates": e4,
            "E5_two_way_computability_not_predicted": twoway["computable"],
        },
        "runtime_s": round(time.perf_counter() - t0, 3),
    }

    for p in PINS:
        if sha(p) != pre[str(p.relative_to(ROOT))]:
            stop("P0b", f"{p.name} changed during the run")

    blob = json.dumps(payload, indent=2, default=float) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k not in ("runtime_s",)}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write")
    OUT.write_text(blob)

    print(f"\ncommitted stratum rung CR1 t({g_str - 1}): "
          f"{cr1_pp[0]:+.3f} to {cr1_pp[1]:+.3f} pp (width {committed_width:.3f})")
    if month_rung:
        mp = month_rung["cr1_t_interval"]["marginal_ci95_pp"]
        mf = month_rung["cr1_t_interval"]["floor_ci95_pct"]
        print(f"month rung CR1 t({g_month - 1}): {mp[0]:+.3f} to {mp[1]:+.3f} pp "
              f"(width {abs(mp[1]-mp[0]):.3f}); floor {mf[0]:.3f}% to {mf[1]:.3f}%")
        print(f"  BM df {month_rung['df_bm']:.3f}, G*_css {month_rung['G_star_css']:.3f}, "
              f"h_max {month_rung['h_max']:.4f}")
        wb = month_rung["wild_t_webb"]["marginal_ci95_pp"]
        print(f"  Webb wild-t: {wb[0]:+.3f} to {wb[1]:+.3f} pp")
        print(f"  truncated: lower={month_rung['cr1_t_interval']['lower_pp_edge']['truncated_at_grid_edge']}"
              f" upper={month_rung['cr1_t_interval']['upper_pp_edge']['truncated_at_grid_edge']}")
    else:
        print(f"month rung NOT_COMPUTABLE (NC1: G_month = {g_month} < {NC1_MIN_MONTH_CLUSTERS})")
    print(f"\ntwo-way CGM: V_s {v_s:.6e} + V_m {v_m:.6e} - V_i {v_i:.6e} = {v_2way:.6e}")
    if twoway["computable"]:
        tp = twoway["t_interval"]["marginal_ci95_pp"]
        print(f"  computable, df {df_2way}: {tp[0]:+.3f} to {tp[1]:+.3f} pp")
    else:
        print("  NOT_COMPUTABLE (NC2) -- zero-truncation REFUSED")
    print(f"\nE3 {e3}   E4 {e4}   NC1 {nc1}  NC3 {nc3}  "
          f"NC4 {g_month <= NC4_RADEMACHER_G}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
