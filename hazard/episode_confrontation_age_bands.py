#!/usr/bin/env python3
"""R32 / C-78: the episode gradient within narrow age bands.

Run tag: episode_gradient_age_bands.  Spec: specs/SPEC_R32_c78_episode_gradient_age_bands.md,
committed before this script was written, and this script committed before it ran.

.tex:331 carries the paper's only realized-data exhibit that moves in the lock-in direction
(+4.20 CPR points).  Its composition limb has been tested on vintage x FICO x LTV, but NOT on age,
and the same sentence still lists "residual seasoning past the age cut" as open.  This run adds
loan age as 12-month strata.

age_band = floor(age0/12) on age0 -- the STRATUM-CONSTANT age at window start that
episode_confrontation.py:674 already computes -- not on the time-varying mean_loan_age, which
could not be a standardization cell.

episode_confrontation.py and episode_confrontation_within.py and BOTH their artifacts are FROZEN:
imported and read, never written, and neither main() is ever called.

Writes ONLY data/episode_gradient_age_bands_results.json.

Run:  cd hazard && python3 episode_confrontation_age_bands.py
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

HAZ = Path(__file__).resolve().parent
ROOT = HAZ.parent
if str(HAZ) not in sys.path:
    sys.path.insert(0, str(HAZ))

import episode_confrontation_within as ecw          # noqa: E402
import episode_confrontation as ec                  # noqa: E402

DATA = HAZ / "data"
OUT = DATA / "episode_gradient_age_bands_results.json"
WITHIN_ARTIFACT = DATA / "episode_confrontation_within_results.json"     # FROZEN
EC_ARTIFACT = DATA / "episode_confrontation_results.json"               # FROZEN

PINS = {
    HAZ / "episode_confrontation_within.py":
        "5dd6f7ae26bae021e771e41025141ad14c5aa965cf2b64e47cd2285273f88e01",
    HAZ / "episode_confrontation.py":
        "87a2fb4e34c54f253c08bbd0188b9e221f92be80e30e30ed7518fd11ba59fdf6",
    EC_ARTIFACT: "1ae1ec277eb183e955647f121a1afec388ecfdfd5f3aea3d68d534da868c1347",
    WITHIN_ARTIFACT: "c81bc3f22aed6f6ee50b46cf9b3b139fa685ae7e4d582967dd6f31f2a0a0cf6e",
}

BAND_MONTHS = 12
AXIS_AGE_FULL = ("vintage", "fico_bucket", "ltv_bucket", "age_band")
AXIS_AGE_ONLY = ("age_band", "fico_bucket", "ltv_bucket")
AXIS_AGE_SOLO = ("age_band",)
AXIS_VINTAGE_AGE = ("vintage", "age_band")

FG_MIN_COVERAGE = ecw.FG_MIN_COVERAGE            # 0.30, carried across UNCHANGED
FG_MIN_CELLS_FULL = ecw.FG_MIN_CELLS_FULL        # 10
FG_MIN_CELLS_FALLBACK = ecw.FG_MIN_CELLS_FALLBACK  # 2

E3_COLLINEARITY_MIN = 0.80                       # spec section 5
E4_E5_BAR_PP = 0.5 * ecw.REF_GRADIENT_PP         # 2.099089..., the committed run's own bar


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _syspath_bootstrap(node: ast.If) -> bool:
    if "sys.path" not in ast.unparse(node.test) or node.orelse:
        return False
    return all(isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
               and ast.unparse(s.value.func) in ("sys.path.insert", "sys.path.append")
               for s in node.body)


def binds_names_only(path: Path) -> bool:
    binding = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
               ast.ClassDef, ast.Assign, ast.AnnAssign)
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, binding):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.If):
            if ast.unparse(node.test) == "__name__ == '__main__'" or _syspath_bootstrap(node):
                continue
        return False
    return True


def age_ordinals(cell: str, axis: tuple) -> tuple:
    """ecw.cell_ordinals extended to age_band.

    ecw's own version falls through to 0.0 for an unrecognised axis name, which would make every
    age band equidistant and silently degrade the nearest-populated-cell rule. Age is ordinal, so
    it gets its band index.
    """
    coords = []
    for a, v in zip(axis, cell.split("|")):
        if a == "vintage":
            coords.append(float(int(v)))
        elif a == "fico_bucket":
            coords.append(float(ecw.FICO_ORDER.get(v, len(ecw.FICO_ORDER))))
        elif a == "ltv_bucket":
            coords.append(float(ecw.LTV_ORDER.get(v, len(ecw.LTV_ORDER))))
        elif a == "age_band":
            coords.append(float(int(v)))
        else:
            raise ValueError(f"unhandled axis component {a!r}")
    return tuple(coords)


def age_distance_matrix(cells: list, axis: tuple) -> np.ndarray:
    c = np.array([age_ordinals(x, axis) for x in cells], dtype=np.float64)
    return np.abs(c[:, None, :] - c[None, :, :]).sum(axis=2)


def limb_a_ext(primary: pd.DataFrame, sh: str, dp: str, axis: tuple,
               ec_draws: np.ndarray) -> dict:
    """ecw.limb_a's construction with the age-aware distance matrix substituted.

    Everything else -- the shallow-weight standardization, ratio imputation with the flat
    fallback, the joint_gradient_bootstrap index stream, per-replicate re-imputation -- is
    ecw's, called through ecw._standardize and asserted against the imported draws.
    """
    shal = primary[primary["bucket"] == sh].copy()
    deep = primary[primary["bucket"] == dp].copy()
    shal["cell"] = ecw.cell_ids(shal, axis)
    deep["cell"] = ecw.cell_ids(deep, axis)
    cells = sorted(set(shal["cell"]) | set(deep["cell"]))
    dist = age_distance_matrix(cells, axis)

    pre_s, ex_s = ecw._cell_arrays(shal, cells)
    pre_d, ex_d = ecw._cell_arrays(deep, cells)
    g_std, shal_std, deep_std, imp_w, table = ecw._standardize(
        pre_s, ex_s, pre_d, ex_d, dist)

    smm_s_pool = float(shal["prepaid_upb"].sum()) / float(shal["exposure_upb"].sum())
    smm_d_pool = float(deep["prepaid_upb"].sum()) / float(deep["exposure_upb"].sum())
    cpr_s_pool, cpr_d_pool = float(ecw._cpr(smm_s_pool)), float(ecw._cpr(smm_d_pool))

    gs = shal.groupby("stratum", sort=True).agg(
        pre=("prepaid_upb", "sum"), ex=("exposure_upb", "sum"), cell=("cell", "first"))
    gd = deep.groupby("stratum", sort=True).agg(
        pre=("prepaid_upb", "sum"), ex=("exposure_upb", "sum"), cell=("cell", "first"))
    code = {c: i for i, c in enumerate(cells)}
    cs = gs["cell"].map(code).to_numpy(dtype=np.int64)
    cd = gd["cell"].map(code).to_numpy(dtype=np.int64)
    ps, es = gs["pre"].to_numpy(np.float64), gs["ex"].to_numpy(np.float64)
    pdp, ed = gd["pre"].to_numpy(np.float64), gd["ex"].to_numpy(np.float64)

    rng = np.random.default_rng(ecw.SEED)
    idx_s = rng.integers(0, len(ps), size=(ecw.N_BOOT, len(ps)))
    idx_d = rng.integers(0, len(pdp), size=(ecw.N_BOOT, len(pdp)))
    raw = (ecw._cpr(ps[idx_s].sum(axis=1) / es[idx_s].sum(axis=1))
           - ecw._cpr(pdp[idx_d].sum(axis=1) / ed[idx_d].sum(axis=1)))
    stream_err = float(np.max(np.abs(raw - ec_draws)))
    if stream_err >= 1e-12:
        stop("LIMB-A", f"bootstrap stream diverged from joint_gradient_bootstrap "
                       f"(max |diff| {stream_err:g})")

    C = len(cells)
    draws = np.full(ecw.N_BOOT, np.nan)
    imp_draws = np.full(ecw.N_BOOT, np.nan)
    for k in range(ecw.N_BOOT):
        a, b = idx_s[k], idx_d[k]
        g_k, _, _, iw_k, _ = ecw._standardize(
            np.bincount(cs[a], weights=ps[a], minlength=C),
            np.bincount(cs[a], weights=es[a], minlength=C),
            np.bincount(cd[b], weights=pdp[b], minlength=C),
            np.bincount(cd[b], weights=ed[b], minlength=C), dist)
        draws[k] = g_k
        imp_draws[k] = iw_k
    ok = np.isfinite(draws)
    n_degen = int((~ok).sum())
    ci = ([float(np.percentile(draws[ok], 2.5)), float(np.percentile(draws[ok], 97.5))]
          if ok.any() else [None, None])
    se = float(np.std(draws[ok], ddof=1)) if ok.sum() > 1 else None

    def _n(v):
        return None if v is None or not np.isfinite(v) else float(v)

    return {
        "status": "OK" if np.isfinite(g_std) else "DEGENERATE",
        "standardization_axis": "|".join(axis),
        "standardized_gradient_pp": _n(g_std), "ci95_pp": ci, "se_pp": se,
        "imputed_weight_share": _n(imp_w),
        "shallow_standardized_cpr_pct": _n(shal_std),
        "deep_standardized_cpr_pct": _n(deep_std),
        "shallow_pooled_cpr_pct": cpr_s_pool, "deep_pooled_cpr_pct": cpr_d_pool,
        "raw_gradient_pp": cpr_s_pool - cpr_d_pool,
        "n_cells": len(cells),
        "n_common_cells": int(((ex_s > 0) & (ex_d > 0)).sum()),
        "bootstrap": {
            "n_reps": ecw.N_BOOT, "seed": ecw.SEED,
            "stream_parity_vs_joint_gradient_bootstrap_max_abs": stream_err,
            "mean_imputed_weight_share": _n(np.nanmean(imp_draws)) if ok.any() else None,
            "n_degenerate_reps": n_degen,
        },
        "distance_metric_note": ("age_band enters the nearest-populated-cell rule with its band "
                                 "index as an ordinal; ecw.cell_ordinals would have collapsed it "
                                 "to 0.0 and made every band equidistant"),
    }


def main() -> None:
    t0 = time.perf_counter()

    for p, want in PINS.items():
        got = sha(p)
        if got != want:
            stop("P0", f"{p.relative_to(ROOT)} sha256 {got} != pinned {want}")
    pre = {str(p.relative_to(ROOT)): sha(p) for p in PINS}
    for p in (HAZ / "episode_confrontation_within.py", HAZ / "episode_confrontation.py"):
        if not binds_names_only(p):
            stop("P0a", f"{p.name} does more than bind names at top level")

    committed = json.loads(WITHIN_ARTIFACT.read_text())
    if committed.get("status") != "OK" or not committed.get("parity_gates_all_pass"):
        stop("G6", "the committed within artifact is not a clean OK/all-pass run")

    # register display names for the new axes (a LABEL map only; no behaviour changes)
    for ax in (AXIS_AGE_FULL, AXIS_AGE_ONLY, AXIS_AGE_SOLO, AXIS_VINTAGE_AGE):
        ecw.AXIS_NAME[ax] = "|".join(ax)

    # ---- G0-G4, then selection + FG, then G5 -- ecw's own order ------------
    gates, df, betas, h_floor = ecw.run_committed_gates_g0_g4()
    win, info, bucketed, primary = ecw.build_selection(df)
    qualified, sh, dp = ecw.endpoints_exposure_only(primary)
    if sh is None:
        stop("G7", "fewer than two qualified endpoint buckets")

    # ---- G7: selection parity against the committed artifact --------------
    csel = committed["selection"]
    got_sel = {"n_strata_total": len(info),
               "n_strata_bucketed": int(info["bucket"].notna().sum()),
               "n_strata_primary": int((info["bucket"].notna()
                                        & (info["age0"] >= ecw.AGE0_MIN)).sum()),
               "n_rows_primary": int(len(primary))}
    for k, v in got_sel.items():
        if csel[k] != v:
            stop("G7", f"selection drift {k}: {v} != committed {csel[k]}")
    if csel["endpoints"] != {"shallow": sh, "deep": dp}:
        stop("G7", f"endpoint drift: {sh}/{dp} != {csel['endpoints']}")
    print(f"  G7 selection parity: {got_sel}  [PASS]")

    g5 = ecw.run_g5(primary, betas, h_floor, sh, dp, gates)

    # ---- age bands ---------------------------------------------------------
    primary = primary.copy()
    primary["age_band"] = np.floor(primary["age0"] / BAND_MONTHS).astype(int).astype(str)

    # ---- G6: the axis machinery reproduces the committed decomposition ----
    g6 = ecw._between_within(primary[primary["bucket"] == sh],
                             primary[primary["bucket"] == dp], ecw.AXIS_FULL)
    clb = committed["limb_b"]
    g6_checks = {}
    for k in ("total_pp", "between_composition_pp", "within_composition_pp",
              "identity_residual", "n_cells"):
        g6_checks[k] = {"got": g6[k], "want": clb[k], "exact": g6[k] == clb[k]}
        if abs(g6[k] - clb[k]) > 1e-12:
            stop("G6", f"{k}: {g6[k]!r} != committed {clb[k]!r}")
    for ax_name, ax in (("vintage_only", ("vintage",)),
                        ("fico_ltv_only", ecw.AXIS_FALLBACK)):
        got = ecw._between_within(primary[primary["bucket"] == sh],
                                  primary[primary["bucket"] == dp], ax)
        want = clb["between_by_axis"][ax_name]["between_composition_pp"]
        g6_checks[ax_name] = {"got": got["between_composition_pp"], "want": want,
                              "exact": got["between_composition_pp"] == want}
        if abs(got["between_composition_pp"] - want) > 1e-12:
            stop("G6", f"between_by_axis {ax_name} does not reproduce")
    print("  G6 axis machinery reproduces the committed decomposition  [PASS]")

    # ---- E3: how collinear are age and vintage? ---------------------------
    shal = primary[primary["bucket"] == sh]
    ex_by_v = shal.groupby("vintage")["exposure_upb"].sum()
    single_band_exposure = 0.0
    vintage_bands = {}
    for v, g in shal.groupby("vintage"):
        bands = sorted(g["age_band"].unique().tolist())
        vintage_bands[str(v)] = bands
        if len(bands) == 1:
            single_band_exposure += float(g["exposure_upb"].sum())
    collinearity = single_band_exposure / float(ex_by_v.sum())
    e3 = bool(collinearity >= E3_COLLINEARITY_MIN)
    print(f"  E3 collinearity: {100*collinearity:.2f}% of shallow exposure in "
          f"single-band vintages (bar {100*E3_COLLINEARITY_MIN:.0f}%)  "
          f"[{'PASS' if e3 else 'MISS'}]")

    # ---- FG' ---------------------------------------------------------------
    sel_sh = primary[primary["bucket"] == sh]
    sel_dp = primary[primary["bucket"] == dp]
    cov_full = ecw._coverage(sel_sh, sel_dp, AXIS_AGE_FULL)
    fg1 = (cov_full["shallow_exposure_covered_share"] >= FG_MIN_COVERAGE
           and cov_full["common_cells_n"] >= FG_MIN_CELLS_FULL)
    cov_only = ecw._coverage(sel_sh, sel_dp, AXIS_AGE_ONLY)
    if fg1:
        branch, axis_used = "FG-1'", AXIS_AGE_FULL
    else:
        fg2 = (cov_only["shallow_exposure_covered_share"] >= FG_MIN_COVERAGE
               and cov_only["common_cells_n"] >= FG_MIN_CELLS_FALLBACK)
        branch, axis_used = ("FG-2'", AXIS_AGE_ONLY) if fg2 else ("FG-3'", None)
    print(f"  FG' {branch}: full axis {cov_full['common_cells_n']} common cells / "
          f"{100*cov_full['shallow_exposure_covered_share']:.2f}% coverage; "
          f"age-only {cov_only['common_cells_n']} / "
          f"{100*cov_only['shallow_exposure_covered_share']:.2f}%")

    # ---- Limb B' (identity; always reports) -------------------------------
    def bw(ax):
        r = ecw._between_within(sel_sh, sel_dp, ax)
        if abs(r["identity_residual"]) > 1e-12:
            stop("E2", f"identity residual {r['identity_residual']:g} on axis {ax}")
        return {k: r[k] for k in ("between_composition_pp", "within_composition_pp",
                                  "n_cells", "identity_residual", "total_pp")}

    limb_b = {
        "full_cell_committed": bw(ecw.AXIS_FULL),
        "vintage_only": bw(("vintage",)),
        "fico_ltv_only": bw(ecw.AXIS_FALLBACK),
        "age_only": bw(AXIS_AGE_SOLO),
        "vintage_x_age": bw(AXIS_VINTAGE_AGE),
        "age_augmented_full": bw(AXIS_AGE_FULL),
        "age_fico_ltv": bw(AXIS_AGE_ONLY),
    }
    age_between = limb_b["age_only"]["between_composition_pp"]
    e4 = bool(age_between < E4_E5_BAR_PP)
    print(f"  Limb B' age_only between = {age_between:+.6f}pp "
          f"(bar {E4_E5_BAR_PP:+.6f})  [{'PASS' if e4 else 'MISS'}]")

    # ---- Limb A' -----------------------------------------------------------
    limb_a = None
    e5 = None
    if axis_used is not None:
        limb_a = limb_a_ext(primary, sh, dp, axis_used, g5["gradient_draws"])
        if limb_a["standardized_gradient_pp"] is not None:
            e5 = bool(limb_a["standardized_gradient_pp"] > E4_E5_BAR_PP)
        print(f"  Limb A' [{limb_a['standardization_axis']}] gradient "
              f"{limb_a['standardized_gradient_pp']}, CI {limb_a['ci95_pp']}, "
              f"imputed weight {limb_a['imputed_weight_share']}")

    # ---- branch ------------------------------------------------------------
    if axis_used is None and limb_b["age_only"]["n_cells"] < 2:
        branch_landed = "D"
    elif e4 and (e5 is None or e5):
        branch_landed = "A"
    elif (limb_a and limb_a["standardized_gradient_pp"] is not None
          and limb_a["standardized_gradient_pp"] <= g5["g_model"]):
        branch_landed = "C"
    else:
        branch_landed = "B"

    payload = {
        "mode": "episode_gradient_age_bands", "run_tag": "episode_gradient_age_bands",
        "status": "OK",
        "spec": {
            "spec_file": "specs/SPEC_R32_c78_episode_gradient_age_bands.md",
            "age_band": f"floor(age0/{BAND_MONTHS}) on the stratum-constant age at window start",
            "not_within_stratum": ("the literal within-stratum gradient stays NOT COMPUTABLE: the "
                                   "stratum id contains coupon and gap = coupon - market rate, so "
                                   "every stratum lives in exactly one bucket. Adding age changes "
                                   "nothing about that. This is composition control on an age "
                                   "axis, not a within-stratum estimator."),
            "limb_c_not_rerun": ("the committed limb_c.confounds_note already records the two-way "
                                 "(stratum + month) FE variant as EXACTLY unidentified, and age "
                                 "within a stratum is a deterministic function of calendar time, "
                                 "so re-running it would be an empty run"),
            "fg_thresholds_carried_across_unchanged": {
                "min_coverage": FG_MIN_COVERAGE,
                "min_cells_full_axis": FG_MIN_CELLS_FULL,
                "min_cells_fallback_axis": FG_MIN_CELLS_FALLBACK,
            },
            "age_cut_held": ecw.AGE0_MIN,
            "bands_cut_on_one_date": True,
            "frozen": ("episode_confrontation.py, episode_confrontation_within.py and both "
                       "artifacts: imported and read, never written; neither main() called"),
        },
        "parity_gates": {
            "P0_sha_pins": {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
            "P0a_modules_bind_names_only": True,
            "G0_G4": {k: v.get("pass") for k, v in gates.items() if k.startswith("G")},
            "G5_frozen_artifact_reproduction":
                gates["G5_frozen_artifact_reproduction"]["pass"],
            "G6_axis_machinery_reproduces_committed": g6_checks,
            "G7_selection_parity": got_sel,
        },
        "endpoints": {"shallow": sh, "deep": dp, "qualified": qualified},
        "age_bands": {
            "band_months": BAND_MONTHS,
            "bands_present_shallow": sorted(sel_sh["age_band"].unique().tolist()),
            "bands_present_deep": sorted(sel_dp["age_band"].unique().tolist()),
            "vintage_to_bands_shallow": vintage_bands,
            "E3_single_band_vintage_exposure_share": collinearity,
        },
        "feasibility_gate": {
            "branch": branch, "axis_used": "|".join(axis_used) if axis_used else "none",
            "axis_age_full": {k: cov_full[k] for k in
                              ("common_cells_n", "cells_shallow_n", "cells_deep_n",
                               "shallow_exposure_covered_share",
                               "deep_exposure_covered_share")},
            "axis_age_only": {k: cov_only[k] for k in
                              ("common_cells_n", "cells_shallow_n", "cells_deep_n",
                               "shallow_exposure_covered_share",
                               "deep_exposure_covered_share")},
        },
        "limb_b": limb_b,
        "limb_a": limb_a,
        "committed_reference": {
            "raw_gradient_pp": ecw.REF_GRADIENT_PP,
            "raw_ci95_pp": list(ecw.REF_CI95_PP),
            "model_implied_pp": ecw.REF_IMPLIED_MID_PP,
            "committed_standardized_pp":
                committed["limb_a"]["standardized_gradient_pp"],
            "half_raw_bar_pp": E4_E5_BAR_PP,
        },
        "expectations": {
            "E1_parity": True,
            "E2_identity_residual_zero_on_every_axis": True,
            "E3_collinearity_min": E3_COLLINEARITY_MIN,
            "E3_measured": collinearity, "E3_pass": e3,
            "E4_bar_pp": E4_E5_BAR_PP, "E4_age_only_between_pp": age_between,
            "E4_pass": e4,
            "E5_standardized_above_bar": e5,
        },
        "branch_landed": branch_landed,
        "runtime_s": round(time.perf_counter() - t0, 3),
    }

    for p in PINS:
        if sha(p) != pre[str(p.relative_to(ROOT))]:
            stop("W1", f"{p.name} changed during the run -- a frozen input was written")

    blob = json.dumps(payload, indent=2, default=ecw._json_default) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write")
    OUT.write_text(blob)

    print("\n" + "=" * 72)
    print(f"LIMB B' between-composition by axis (total {limb_b['age_only']['total_pp']:+.4f}pp)")
    print("=" * 72)
    for k, v in limb_b.items():
        print(f"  {k:<22} between {v['between_composition_pp']:+.4f}pp   "
              f"within {v['within_composition_pp']:+.4f}pp   cells {v['n_cells']}")
    print(f"\nE3 {'PASS' if e3 else 'MISS'} ({100*collinearity:.2f}%)   "
          f"E4 {'PASS' if e4 else 'MISS'} ({age_between:+.4f}pp vs bar {E4_E5_BAR_PP:+.4f})   "
          f"E5 {e5}")
    print(f"BRANCH {branch_landed}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
