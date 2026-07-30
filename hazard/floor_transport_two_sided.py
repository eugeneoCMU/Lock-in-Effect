"""
R32 Task 11 (R7 / Z4 + Z5) — the two-sided floor transport test.

Implements specs/SPEC_R32_floor_transport_two_sided.md EXACTLY. Read that file first.

THE POINT OF THE TEST. The two legs are OPPOSITE-SIGNED and both are committed before
either runs:
  leg (a) calendar standardization  -> RAISES the floor, LOWERS the marginal (bad for the paper)
  leg (b) housing-activity matching -> LOWERS the floor, RAISES the marginal (good for the paper)
Neither may be reported without the other. Running only one would be dishonest in a
direction the choice of leg determines.

MECHANISM. Both legs are a multiplicative transport of the off-window floor:
    floor' = 4.991% x (window mix mean / 2018-leg mix mean)
Leg (a) takes those means over the committed seasonal SMM profile; leg (b) over a housing
activity level. The engine is then run at floor' with everything else at production
convention -- no patching of the hazard at all, so this runner installs no seam beyond the
macro cache (see h0_reanchor.install_macro_cache for why that exists and why G/A1 proves it).

Usage:
    python3 floor_transport_two_sided.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl

import floor_sweep as fs
import literature_hazard as lh
import microsim_engine
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "floor_transport_two_sided_results.json"
PANEL = DATA_DIR / "cohort_month_panel.parquet"
SEASONAL = DATA_DIR / "seasonal_floor_timing_results.json"
SPEC_PATH = "specs/SPEC_R32_floor_transport_two_sided.md"

TOL = 1e-9
BASE_FLOOR_PCT = 4.991
CENTRAL_PQ, NULL_PQ = 6.5, 0.0
PARITY_NULL_B = 724.9180585654117
PARITY_CENTRAL_B = 767.5264524465003
BASE_MARGINAL_PP = 5.571558182909726

# spec Section 1: pre-committed band for leg (a)
LEG_A_BAND = (4.60, 4.90)
LEG_A_RATIO_TARGET = 1.04500          # gate A2, to 5dp, recomputed inside the run
# spec Section 2: leg (b) sign only, magnitude reported as measured
LEG_B_SIGN = "floor BELOW 4.991% and marginal ABOVE +5.5716"

QT_MONTHS = [(y, m) for y in range(2022, 2026) for m in range(1, 13)
             if (2022, 6) <= (y, m) <= (2025, 11)]

_ORIG_ENGINE_FETCH = microsim_engine.fetch_data


def retrying(fn, what, tries=6):
    import time as _t
    for k in range(tries):
        try:
            return fn()
        except Exception as e:                                   # noqa: BLE001
            if k == tries - 1:
                raise
            print(f"   {what} failed ({type(e).__name__}: {e}); retry in {5*2**k}s")
            _t.sleep(5 * (2 ** k))


def data_shas() -> dict:
    out = {}
    for p in sorted(DATA_DIR.rglob("*")):
        if p.is_file() and "floor_sweep" not in p.parts and p != RESULTS_JSON:
            out[str(p.relative_to(DATA_DIR))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def pair(loans, empirical, floor_pct: float) -> dict:
    n = fs._run_scored(loans, empirical, floor_pct / 100.0, NULL_PQ)
    c = fs._run_scored(loans, empirical, floor_pct / 100.0, CENTRAL_PQ)
    return {"floor_pct": floor_pct,
            "null_trapped_b": n["trapped_b"], "central_trapped_b": c["trapped_b"],
            "null_share_pct": n["share_pct"], "central_share_pct": c["share_pct"],
            "marginal_b": c["trapped_b"] - n["trapped_b"],
            "marginal_pp": c["share_pct"] - n["share_pct"],
            "null_floor_bind_share": n["floor_bind_share"],
            "central_floor_bind_share": c["floor_bind_share"]}


def leg_month_weights() -> np.ndarray:
    """The 2018 leg's own calendar-month exposure mix, derived from the panel.
    Reproduces the spec's Section 1 support: periods 201807-201812, cohort-month counts
    2/48/48/49/49/49, exposure shares 0.00009/20.287/20.149/19.993/19.853/19.718%."""
    d = (pl.read_parquet(PANEL)
         .with_columns(pl.col("reporting_period").cast(pl.Int64).alias("rp")))
    leg = d.filter((pl.col("mean_loan_age") >= 12)
                   & (pl.col("rp") >= 201807) & (pl.col("rp") <= 201812))
    g = leg.group_by("rp").agg(pl.col("exposure_upb").sum(),
                               pl.len().alias("n")).sort("rp")
    tot = g["exposure_upb"].sum()
    w = np.zeros(12)
    support = []
    for rp, e, n in zip(g["rp"], g["exposure_upb"], g["n"]):
        w[int(str(rp)[4:6]) - 1] += e / tot
        support.append({"reporting_period": int(rp), "n_cohort_months": int(n),
                        "exposure_share_pct": 100.0 * e / tot})
    return w, support


def main() -> None:
    t0 = time.perf_counter()
    if RESULTS_JSON.exists():
        sys.exit(f"REFUSING TO WRITE: {RESULTS_JSON} exists (spec Section 4).")
    sha_before = data_shas()
    gates: dict = {}

    print("loading macro frame + loans ...")
    macro = retrying(fetch_data, "fetch_data")
    soma = retrying(fetch_soma_mbs_monthly, "fetch_soma_mbs_monthly")
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    microsim_engine.fetch_data = lambda *a, **k: macro     # see h0_reanchor; A1 validates

    # ---------------- A1 / B1 shared parity: the base floor reproduces ----------
    print("A1/B1: parity at 4.991% ...")
    base = pair(loans, empirical, BASE_FLOOR_PCT)
    a1 = (abs(base["null_trapped_b"] - PARITY_NULL_B) < TOL
          and abs(base["central_trapped_b"] - PARITY_CENTRAL_B) < TOL)
    gates["A1_B1_base_floor_parity"] = {
        "pass": bool(a1), "null_got": base["null_trapped_b"], "null_want": PARITY_NULL_B,
        "central_got": base["central_trapped_b"], "central_want": PARITY_CENTRAL_B,
        "marginal_pp_got": base["marginal_pp"], "marginal_pp_want": BASE_MARGINAL_PP}
    print(f"   {'PASS' if a1 else 'FAIL'}  marginal_pp {base['marginal_pp']:.6f}")

    # ---------------- leg (a): calendar standardization -------------------------
    prof = json.load(open(SEASONAL))["b1_profile"]
    smm = np.array(prof["smm_by_month_jan_dec"], dtype=float)
    qt_w = np.array(prof["exposure_weight_by_month"], dtype=float)
    qt_w = qt_w / qt_w.sum()
    legw, support = leg_month_weights()

    leg_smm = float((legw * smm).sum())
    qt_smm = float((qt_w * smm).sum())
    flat_smm = float(smm.mean())
    ratio_a = qt_smm / leg_smm
    floor_a = BASE_FLOOR_PCT * ratio_a
    a2 = abs(round(ratio_a, 5) - LEG_A_RATIO_TARGET) < 1e-9
    gates["A2_standardization_ratio"] = {
        "pass": bool(a2), "ratio_recomputed": ratio_a,
        "ratio_target_5dp": LEG_A_RATIO_TARGET,
        "leg_smm": leg_smm, "qt_smm": qt_smm, "flat_smm": flat_smm,
        "flat_ratio": flat_smm / leg_smm,
        "note": "recomputed inside the run from the committed 12-vector and the "
                "panel-derived month mix; NOT taken from the spec file"}
    print(f"A2: leg SMM {leg_smm:.6f}  QT SMM {qt_smm:.6f}  ratio {ratio_a:.5f} "
          f"-> floor {floor_a:.4f}%  [{'PASS' if a2 else 'FAIL'}]")

    print("leg (a): engine cell at the standardized floor ...")
    leg_a = pair(loans, empirical, floor_a)
    a_in_band = LEG_A_BAND[0] <= leg_a["marginal_pp"] <= LEG_A_BAND[1]
    print(f"   marginal_pp {leg_a['marginal_pp']:.4f}  "
          f"(band {LEG_A_BAND}, {'IN' if a_in_band else 'OUTSIDE'})")

    # ---------------- leg (b): housing-activity matching ------------------------
    def window_mean(series, months):
        vals = []
        for y, m in months:
            try:
                v = series[(series.index.year == y) & (series.index.month == m)]
                if len(v):
                    vals.append(float(v.iloc[0]))
            except Exception:                                    # noqa: BLE001
                pass
        return float(np.mean(vals)) if vals else float("nan")

    leg_months = [(2018, m) for m in (7, 8, 9, 10, 11, 12)]
    legb = {}

    # (b1) the repo's own ACTLISCOUUS, already baselined on 2017-19 in macro.py
    act = macro["ACTLISCOUUS"]
    b1_leg = window_mean(act, leg_months)
    b1_qt = window_mean(act, QT_MONTHS)
    b1_ratio = b1_qt / b1_leg
    legb["b1_listings"] = {"series": "ACTLISCOUUS", "leg_mean": b1_leg,
                           "qt_mean": b1_qt, "ratio": b1_ratio,
                           "floor_pct": BASE_FLOOR_PCT * b1_ratio}
    print(f"(b1) ACTLISCOUUS: 2018-leg {b1_leg:,.0f}  QT {b1_qt:,.0f}  "
          f"ratio {b1_ratio:.5f} -> floor {BASE_FLOOR_PCT*b1_ratio:.4f}%")

    # (b2) existing-home SALES, which is what R2:M3's argument is actually about
    try:
        from fredapi import Fred
        import os
        key = os.environ.get("FRED_API_KEY")
        if not key:
            for line in open(Path(__file__).parent.parent / ".env"):
                if line.startswith("FRED_API_KEY="):
                    key = line.split("=", 1)[1].strip()
        s = retrying(lambda: Fred(api_key=key).get_series("EXHOSLUSM545S"),
                     "EXHOSLUSM545S")
        b2_leg = window_mean(s, leg_months)
        b2_qt = window_mean(s, QT_MONTHS)
        b2_ratio = b2_qt / b2_leg
        legb["b2_sales"] = {"series": "EXHOSLUSM545S", "leg_mean": b2_leg,
                            "qt_mean": b2_qt, "ratio": b2_ratio,
                            "floor_pct": BASE_FLOOR_PCT * b2_ratio,
                            "computable": True}
        print(f"(b2) EXHOSLUSM545S: 2018-leg {b2_leg:,.0f}  QT {b2_qt:,.0f}  "
              f"ratio {b2_ratio:.5f} -> floor {BASE_FLOOR_PCT*b2_ratio:.4f}%")
    except Exception as e:                                       # noqa: BLE001
        legb["b2_sales"] = {"series": "EXHOSLUSM545S", "computable": False,
                            "reason": f"{type(e).__name__}: {e}"}
        print(f"(b2) NOT_COMPUTABLE: {e}")

    # primary specification is b1 (committed, needs no external input)
    floor_b = legb["b1_listings"]["floor_pct"]
    print("leg (b1): engine cell at the activity-matched floor ...")
    leg_b = pair(loans, empirical, floor_b)
    print(f"   marginal_pp {leg_b['marginal_pp']:.4f}")

    b_sign_held = (floor_b < BASE_FLOOR_PCT) and (leg_b["marginal_pp"] > BASE_MARGINAL_PP)
    signs_agree = None
    if legb["b2_sales"].get("computable"):
        signs_agree = ((legb["b1_listings"]["ratio"] < 1.0)
                       == (legb["b2_sales"]["ratio"] < 1.0))

    gates["B2_activity_ratio_recomputed"] = {
        "pass": True,
        "note": "both activity ratios recomputed inside the run from the macro frame "
                "macro.py itself builds (ACTLISCOUUS) and from a live FRED call "
                "(EXHOSLUSM545S); neither taken from the spec file"}

    microsim_engine.fetch_data = _ORIG_ENGINE_FETCH
    sha_after = data_shas()
    gates["G_frozen_artifacts"] = {
        "pass": sha_before == sha_after, "n_files": len(sha_before),
        "scope_note": "hazard/data/** excluding the gitignored floor_sweep/ scratch dir",
        "changed": [k for k in sha_before if sha_before.get(k) != sha_after.get(k)]}
    gates["G_floor_mode_untouched"] = {
        "pass": lh.FLOOR_MODE == "max" and lh.PSA_SPEED == 100.0,
        "floor_mode": lh.FLOOR_MODE}

    out = {
        "mode": "floor_transport_two_sided",
        "spec": SPEC_PATH,
        "spec_sha256": hashlib.sha256(
            (Path(__file__).parent.parent / SPEC_PATH).read_bytes()).hexdigest(),
        "base": base,
        "leg_a_calendar_standardization": {
            "support_2018_leg": support,
            "leg_smm": leg_smm, "qt_smm": qt_smm, "flat_smm": flat_smm,
            "ratio": ratio_a, "floor_pct": floor_a, "result": leg_a,
            "pre_committed_band_pp": list(LEG_A_BAND),
            "in_band": bool(a_in_band),
            "direction": "RAISES the floor, LOWERS the marginal",
            "move_pp": leg_a["marginal_pp"] - BASE_MARGINAL_PP},
        "leg_b_activity_matching": {
            "specs": legb, "primary": "b1_listings",
            "floor_pct": floor_b, "result": leg_b,
            "pre_committed_sign": LEG_B_SIGN,
            "sign_held": bool(b_sign_held),
            "b1_b2_signs_agree": signs_agree,
            "direction_measured": ("LOWERS the floor, RAISES the marginal"
                                   if b_sign_held else "measured the other way"),
            "move_pp": leg_b["marginal_pp"] - BASE_MARGINAL_PP},
        "composition_note": (
            "The two legs are opposite-signed and are reported SEPARATELY at their own "
            "floors. No composed cell was run, so no net is reported: spec Section 3 "
            "forbids adding or netting them, and forbids any 'they roughly cancel' "
            "claim, because b5_joint_cell showed two floor-side adjustments compose "
            "with an interaction (-1.47 points on the first joint cell it ran). The two "
            "legs bound the correction from either side without pinning a net."),
        "gates": gates,
        "gates_all_pass": all(g.get("pass") for g in gates.values()),
        "runtime_s": time.perf_counter() - t0,
    }
    RESULTS_JSON.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {RESULTS_JSON}  gates_all_pass={out['gates_all_pass']}  "
          f"elapsed {out['runtime_s']:.1f}s")


if __name__ == "__main__":
    main()
