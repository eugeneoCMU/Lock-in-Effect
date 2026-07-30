"""
R32 C-73 (analytic) — recompute the implied cross-sectional gap gradient at the
headline floor and under the additive form, at 75/100/125 PSA.

Implements specs/SPEC_R32_c73_gradient_recompute.md EXACTLY.

NOTHING IS RE-FITTED. The realized side is the committed panel; the implied side is the
paper's own eq. (2) evaluated analytically. Gate E1 proves the reconstruction reproduces
the committed realized gradient, E2 proves the arithmetic reproduces the committed implied
gradient at the production cell, so any movement in the new cells is attributable to the
calibration change alone.

Usage: python3 episode_gradient_recompute.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "abm", _REPO / "hazard"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import episode_confrontation as ec          # noqa: E402  (has a __main__ guard)
import literature_hazard as lh              # noqa: E402
import matched_depth_reconciliation as mdr  # build_panel  # noqa: E402
from stratum import build_stratum_id        # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "episode_gradient_recompute_results.json"
COMMITTED = DATA_DIR / "episode_confrontation_results.json"
SPEC_PATH = "specs/SPEC_R32_c73_gradient_recompute.md"

TOL = 1e-9
FLOORS = {"production_4pct": 0.04, "headline_4.991pct": 0.04991}
FORMS = ("max", "additive")
PSAS = (75.0, 100.0, 125.0)

PREDICTION = (
    "under the MAX form at the 4.991% headline floor the implied gradient FALLS below the "
    "committed 0.9371 and realized/implied RISES above 4.48 (a higher floor censors more "
    "deep-gap exposure, and censored cells contribute zero gradient); under the ADDITIVE "
    "form at the same floor the implied gradient RISES above 0.9371 (that form never "
    "clips the voluntary term). Signs only -- no band is committed.")


def data_shas() -> dict:
    return {str(p.relative_to(DATA_DIR)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(DATA_DIR.rglob("*"))
            if p.is_file() and "floor_sweep" not in p.parts and p != RESULTS_JSON}


def implied_stats(rows: pd.DataFrame, beta1_signed: float, h_floor: float,
                  form: str, psa: float) -> dict:
    """ec.implied_bucket_stats, generalised over form and PSA. The max branch is
    byte-for-byte the committed arithmetic when form='max' and psa=100."""
    age = rows["mean_loan_age"].to_numpy(dtype=np.float64)
    gap = rows["gap"].to_numpy(dtype=np.float64)
    h0 = lh.h0_psa(age, psa_speed=psa)
    h_vol = h0 * np.exp((-beta1_signed) * (gap * 100.0))
    if form == "additive":
        combined = 1.0 - (1.0 - h_floor) * (1.0 - h_vol)
        bind = np.zeros_like(h_vol, dtype=bool)
    else:
        combined = np.maximum(h_floor, h_vol)
        bind = h_floor >= h_vol
    h = np.clip(combined, 0.0, 1.0)
    w = rows["exposure_upb"].to_numpy(dtype=np.float64)
    smm = float((h * w).sum() / w.sum())
    return {"smm": smm, "cpr_pct": (1.0 - (1.0 - smm) ** 12) * 100.0,
            "floor_bind_exposure_share": float((w * bind).sum() / w.sum())}


def main() -> None:
    t0 = time.perf_counter()
    if RESULTS_JSON.exists():
        sys.exit(f"REFUSING TO WRITE: {RESULTS_JSON} exists (spec Section 5).")
    sha_before = data_shas()
    gates: dict = {}

    committed = json.load(open(COMMITTED))
    cv = committed["verdict"]["inputs"]
    G_REAL = cv["realized_gradient_pp"]
    G_IMPL = cv["model_implied_gradient_pp_at_0.069"]
    print("committed: realized %.15f | implied@production %.15f" % (G_REAL, G_IMPL))

    # ---- rebuild the committed selection, exactly as ec.main does ----------
    print("rebuilding the panel selection ...")
    df = mdr.build_panel()
    df["stratum"] = [build_stratum_id(v, c, fb, lb)
                     for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                             df["fico_bucket"], df["ltv_bucket"])]
    win = df[(df["rp"] >= ec.WINDOW[0]) & (df["rp"] <= ec.WINDOW[1])].copy()
    assert int(win["rp"].nunique()) == ec.T_MONTHS, "window month count moved"
    win["_gx"] = win["gap"] * win["exposure_upb"]
    agg = win.groupby("stratum").agg(gx=("_gx", "sum"), ex=("exposure_upb", "sum"))
    wmg_pp = (agg["gx"] / agg["ex"]) * 100.0
    first = win.sort_values("rp").groupby("stratum").first()
    age0 = first["mean_loan_age"] - ec._months_since_window_start(first["rp"])
    info = pd.DataFrame({"wmg_pp": wmg_pp, "age0": age0})
    info["bucket"] = info["wmg_pp"].map(ec.gap_bucket)
    win = win.drop(columns=["_gx"]).merge(info, left_on="stratum",
                                          right_index=True, how="left")
    sel = win[win["bucket"].notna()].copy()
    sel = sel[sel["age0"] >= ec.AGE0_MIN].copy()

    # qualified endpoints, by the committed support rule
    total_exp = float(sel["exposure_upb"].sum())
    per = {}
    for b in ec.BUCKET_ORDER:
        rows = sel[sel["bucket"] == b]
        st = ec.pooled_stats(rows)
        if st.get("computable"):
            per[b] = {"rows": rows, "st": st,
                      "share": st["exposure_upb"] / total_exp}
    qualified = [b for b in ec.BUCKET_ORDER
                 if b in per and per[b]["share"] >= ec.SUPPORT_MIN_SHARE
                 and per[b]["st"]["n_strata"] >= ec.SUPPORT_MIN_STRATA]
    shallow, deep = qualified[0], qualified[-1]
    g_real = per[shallow]["st"]["cpr_pct"] - per[deep]["st"]["cpr_pct"]

    e1 = (abs(g_real - G_REAL) < TOL
          and qualified == committed["part_a"]["primary_age_matched"]["qualified_buckets"])
    gates["E1_panel_bucket_parity"] = {
        "pass": bool(e1), "realized_gradient_got": g_real, "want": G_REAL,
        "qualified_got": qualified,
        "qualified_want": committed["part_a"]["primary_age_matched"]["qualified_buckets"],
        "endpoints": {"shallow": shallow, "deep": deep}}
    print("  E1 %s  realized gradient %.15f" % ("PASS" if e1 else "FAIL", g_real))
    if not e1:
        sys.exit("E1 FAILED — reconstruction does not reproduce the committed selection")

    b_mid = lh.rothstein_beta1(ec.ROTHSTEIN_Q_DECLINE_MID)
    h_floor_prod = float(lh.cpr_annual_to_monthly_hazard(np.array([0.04]))[0])
    g_prod = (implied_stats(per[shallow]["rows"], b_mid, h_floor_prod, "max", 100.0)["cpr_pct"]
              - implied_stats(per[deep]["rows"], b_mid, h_floor_prod, "max", 100.0)["cpr_pct"])
    e2 = abs(g_prod - G_IMPL) < TOL
    gates["E2_implied_parity"] = {"pass": bool(e2), "got": g_prod, "want": G_IMPL}
    print("  E2 %s  implied@production %.15f" % ("PASS" if e2 else "FAIL", g_prod))
    if not e2:
        sys.exit("E2 FAILED — implied arithmetic does not reproduce the committed value")

    # ---- the grid ---------------------------------------------------------
    grid = {}
    binds = {}
    for fname, fcpr in FLOORS.items():
        hf = float(lh.cpr_annual_to_monthly_hazard(np.array([fcpr]))[0])
        for form in FORMS:
            for psa in PSAS:
                s = implied_stats(per[shallow]["rows"], b_mid, hf, form, psa)
                d = implied_stats(per[deep]["rows"], b_mid, hf, form, psa)
                g = s["cpr_pct"] - d["cpr_pct"]
                key = "%s|%s|%g" % (fname, form, psa)
                grid[key] = {
                    "implied_gradient_pp": g,
                    "realized_over_implied": (g_real / g) if g != 0 else None,
                    "bind_share_shallow": s["floor_bind_exposure_share"],
                    "bind_share_deep": d["floor_bind_exposure_share"]}
                binds[key] = d["floor_bind_exposure_share"]
                r = grid[key]["realized_over_implied"]
                print("   %-34s implied %7.4f  ratio %9s  bind(deep) %.4f  bind(shallow) %.4f"
                      % (key, g, ("%.3f" % r) if r is not None else "UNDEFINED",
                         d["floor_bind_exposure_share"], s["floor_bind_exposure_share"]))

    # E3: under max, deep-bucket bind share non-decreasing in the floor
    e3 = all(binds["headline_4.991pct|max|%g" % p] >= binds["production_4pct|max|%g" % p]
             for p in PSAS)
    gates["E3_censoring_monotone"] = {"pass": bool(e3)}
    e4 = all(grid[k]["bind_share_deep"] == 0.0 for k in grid if "|additive|" in k)
    gates["E4_additive_never_binds"] = {"pass": bool(e4)}
    sha_after = data_shas()
    gates["E5_frozen_artifacts"] = {
        "pass": sha_before == sha_after,
        "changed": [k for k in sha_before if sha_before.get(k) != sha_after.get(k)],
        "added": sorted(set(sha_after) - set(sha_before))}

    g_max = grid["headline_4.991pct|max|100"]["implied_gradient_pp"]
    g_add = grid["headline_4.991pct|additive|100"]["implied_gradient_pp"]
    held = {"max_form_falls": bool(g_max < G_IMPL),
            "additive_form_rises": bool(g_add > G_IMPL)}
    ratios = [v["realized_over_implied"] for v in grid.values()
              if v["realized_over_implied"] is not None]
    degenerate = sorted(k for k, v in grid.items()
                        if v["realized_over_implied"] is None)

    out = {
        "mode": "episode_gradient_recompute",
        "spec": SPEC_PATH,
        "spec_sha256": hashlib.sha256((_REPO / SPEC_PATH).read_bytes()).hexdigest(),
        "committed_reference": {"realized_gradient_pp": G_REAL,
                                "implied_at_production": G_IMPL,
                                "realized_over_implied_committed": cv.get(
                                    "realized_over_implied_mid",
                                    committed["part_a"]["primary_age_matched"]["realized_over_implied_mid"])},
        "endpoints": {"shallow": shallow, "deep": deep, "qualified": qualified},
        "grid": grid,
        "ratio_min": min(ratios), "ratio_max": max(ratios),
        "all_finite_ratios_above_one": bool(min(ratios) > 1.0),
        "degenerate_cells_implied_gradient_zero": degenerate,
        "degenerate_note": ("cells where the implied gradient is EXACTLY zero because the "
                            "floor censors BOTH endpoint buckets, so the model implies no "
                            "cross-sectional gradient at all and realized/implied is "
                            "undefined rather than large"),
        "gates": gates,
        "gates_all_pass": all(g.get("pass") for g in gates.values()),
        "prediction": PREDICTION,
        "prediction_held": held,
        "runtime_s": time.perf_counter() - t0,
    }
    RESULTS_JSON.write_text(json.dumps(out, indent=1))
    print("\nwrote %s  gates_all_pass=%s  finite ratios %.3f..%.3f  degenerate cells %d  prediction %s"
          % (RESULTS_JSON, out["gates_all_pass"], out["ratio_min"], out["ratio_max"],
             len(degenerate), held))


if __name__ == "__main__":
    main()
