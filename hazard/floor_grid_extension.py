#!/usr/bin/env python3
"""
floor_grid_extension.py — floor→marginal grid extension past 6.0% annual CPR.

SPEC: specs/SPEC_fresh_panel2_B1_grid_extension_2026-08-29.md (ADOPTED
2026-08-29, committed before this file was first executed). The binding
interval's lower endpoint (restricted inversion, floor 6.1813%) is censored at
the committed floor_sweep grid's 6.0% edge; this run adds paired-leg rows at
{6.25, 6.50, 6.75, 7.00}% so the endpoint is measured, not clamped.

HARNESS: floor_sweep is IMPORTED and its _run_scored convention reused
verbatim (committed 75k loan sample, RNG_SEED 42, same regime tuple, one
shared macro frame, raw-basis scoring, fresh runs, caches not consulted).
config.py production defaults untouched; no .tex file touched.

PARITY GATES (abort, not warn; on any failure the artifact is written with
status GATE_FAILURE, exit NONZERO, and the disposition is STOP-and-report):
  P1 fresh paired legs at 6.0% reproduce the committed floor_sweep row
     bit-exactly (every shared numeric field of null/central + marginals).
  P2 marginal weakly decreasing over {6.0,...,7.0} and > 0 at every new row.
  P3 extended PCHIP at 6.91 within $0.69B / 0.0902pp of the committed
     INDEPENDENT engine read (oos_identification instrument1 row 6.91).
  P4 blast radius: pieces below 5.0 bit-invariant (probe set, incl. the
     binding upper endpoint 4.033460201564454); over the committed
     uncensored endpoints with floors in (5.0, 6.0), max |Δ| old-map vs
     extended-map <= $0.69B / 0.0902pp.
Ex-ante prediction bands (SPEC §3) are scored hit/miss, never gated.

Run:  cd hazard && python3 floor_grid_extension.py
      -> data/floor_grid_extension_results.json (frozen)
10 engine runs (~25s each). floor_sweep_results.json is read, never written.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl
from scipy.interpolate import PchipInterpolator

import floor_sweep as fs
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS_JSON = DATA_DIR / "floor_grid_extension_results.json"
RUN_DIR = DATA_DIR / "floor_grid_extension"
COMMITTED_SWEEP = DATA_DIR / "floor_sweep_results.json"
COMMITTED_OOS = DATA_DIR / "oos_identification_results.json"
V2_ARTIFACT = DATA_DIR / "floor_inference_correction_v2_results.json"
V3_ARTIFACT = DATA_DIR / "floor_inference_correction_v3_results.json"

SPEC = "specs/SPEC_fresh_panel2_B1_grid_extension_2026-08-29.md"

PARITY_FLOOR = 0.06
NEW_FLOORS = [0.0625, 0.065, 0.0675, 0.07]
CENTRAL_PQ, NULL_PQ = 6.5, 0.0

# fidelity tolerances: the committed mapping-fidelity dollar tolerance and its
# pp equivalent at the committed pair's implied scale $7.6475B/pp
TOL_B, TOL_PP = 0.69, 0.0902
BINDING_UPPER_FLOOR = 4.033460201564454

# SPEC §3 pre-committed prediction bands (slope anchor -2.7553, secant anchor
# -1.6895 pp per +1pp floor), scored hit/miss
PREDICTIONS = {
    "two_way_t_interval": {"floor_pct": 6.025832302768929, "band_pp": (2.21, 2.24)},
    "cr3_bm": {"floor_pct": 6.115977687298146, "band_pp": (1.96, 2.09)},
    "month_wild_t_rademacher": {"floor_pct": 6.141792853297579, "band_pp": (1.89, 2.04)},
    "restricted_inversion_binding": {"floor_pct": 6.181251547950084, "band_pp": (1.78, 1.97)},
    "r1_wcr_nonqualifying": {"floor_pct": 6.6733, "band_pp": (0.43, 1.14)},
}


def _committed_rows() -> list[dict]:
    with open(COMMITTED_SWEEP) as f:
        return sorted(json.load(f)["rows"],
                      key=lambda r: r["floor_annual_cpr_pct"])


def _pchip(rows: list[dict]) -> tuple[PchipInterpolator, PchipInterpolator]:
    x = np.array([r["floor_annual_cpr_pct"] for r in rows])
    yb = np.array([r["lockin_marginal_b"] for r in rows])
    yp = np.array([r["lockin_marginal_share_pp"] for r in rows])
    return PchipInterpolator(x, yb), PchipInterpolator(x, yp)


def _row(null: dict, central: dict) -> dict:
    return {
        "floor_annual_cpr_pct": central["floor_annual_cpr_pct"],
        "null": null, "central": central,
        "lockin_marginal_b": central["trapped_b"] - null["trapped_b"],
        "lockin_marginal_share_pp": central["share_pct"] - null["share_pct"],
    }


def _gate_p1(fresh: dict, committed: dict) -> dict:
    diffs = {}
    for leg in ("null", "central"):
        for k, want in committed[leg].items():
            got = fresh[leg].get(k)
            if isinstance(want, float):
                ok = bool(got == want)
            else:
                ok = bool(got == want)
            if not ok:
                diffs[f"{leg}.{k}"] = {"want": want, "got": got}
    for k in ("lockin_marginal_b", "lockin_marginal_share_pp"):
        if fresh[k] != committed[k]:
            diffs[k] = {"want": committed[k], "got": fresh[k]}
    return {"pass": not diffs, "bit_exact": True, "diffs": diffs}


def _endpoints_in_last_interval() -> list[dict]:
    """Committed uncensored endpoints with floor in (5.0, 6.0), from the
    frozen v2/v3 artifacts."""
    out = []

    def scan(o, path, src):
        if isinstance(o, dict):
            fp = o.get("floor_pct")
            if (fp is not None and 5.0 < fp < 6.0
                    and not o.get("truncated_at_grid_edge")):
                out.append({"src": src, "path": path, "floor_pct": fp,
                            "pp_old": o.get("marginal_pp"),
                            "b_old": o.get("marginal_b")})
            for k, v in o.items():
                scan(v, f"{path}/{k}", src)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan(v, f"{path}[{i}]", src)

    for art, name in ((V2_ARTIFACT, "v2"), (V3_ARTIFACT, "v3")):
        with open(art) as f:
            scan(json.load(f), "", name)
    return out


def main() -> None:
    assert rothstein_beta1(0.0) == 0.0
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    # write per-run parquets to this run's own dir, not the committed sweep's
    orig_sweep_dir = fs.SWEEP_DIR
    fs.SWEEP_DIR = RUN_DIR

    committed = _committed_rows()
    committed_60 = next(r for r in committed
                        if r["floor_annual_cpr_pct"] == 6.0)
    with open(COMMITTED_OOS) as f:
        oos = json.load(f)
    row691 = next(r for r in oos["instrument1_marginal_table"]
                  if abs(r["floor_annual_cpr_pct"] - 6.91) < 1e-9)
    oos691_b = row691["band"]["6.5"]["marginal_b"]
    oos691_pp = row691["band"]["6.5"]["marginal_pp"]

    print("Shared macro frame (fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    gates: dict = {}
    status = "OK"

    print("P1 parity pair at 6.0% (fresh, caches not consulted) …")
    parity_row = _row(
        fs._run_scored(loans, empirical, PARITY_FLOOR, NULL_PQ),
        fs._run_scored(loans, empirical, PARITY_FLOOR, CENTRAL_PQ))
    gates["P1_row6_bit_exact"] = _gate_p1(parity_row, committed_60)
    print(f"  P1 {'PASS' if gates['P1_row6_bit_exact']['pass'] else 'FAIL'}")

    rows = []
    for floor in NEW_FLOORS:
        null = fs._run_scored(loans, empirical, floor, NULL_PQ)
        central = fs._run_scored(loans, empirical, floor, CENTRAL_PQ)
        row = _row(null, central)
        rows.append(row)
        print(f"  floor {floor*100:5.2f}%:  null ${null['trapped_b']:7.2f}B  "
              f"central ${central['trapped_b']:7.2f}B  marginal "
              f"${row['lockin_marginal_b']:+7.3f}B / "
              f"{row['lockin_marginal_share_pp']:+6.4f}pp")
    fs.SWEEP_DIR = orig_sweep_dir

    marg = ([committed_60["lockin_marginal_share_pp"]]
            + [r["lockin_marginal_share_pp"] for r in rows])
    gates["P2_shape"] = {
        "weakly_decreasing": bool(all(a >= b for a, b in zip(marg, marg[1:]))),
        "all_positive": bool(all(m > 0 for m in marg[1:])),
        "marginals_pp": marg,
    }
    gates["P2_shape"]["pass"] = bool(gates["P2_shape"]["weakly_decreasing"]
                                     and gates["P2_shape"]["all_positive"])

    fb_old, fp_old = _pchip(committed)
    fb_new, fp_new = _pchip(committed + rows)

    err_b = abs(float(fb_new(6.91)) - oos691_b)
    err_pp = abs(float(fp_new(6.91)) - oos691_pp)
    gates["P3_oos691_fidelity"] = {
        "pass": bool(err_b <= TOL_B and err_pp <= TOL_PP),
        "mapped_b": float(fb_new(6.91)), "engine_b": oos691_b,
        "abs_err_b": err_b, "mapped_pp": float(fp_new(6.91)),
        "engine_pp": oos691_pp, "abs_err_pp": err_pp,
        "tol_b": TOL_B, "tol_pp": TOL_PP,
    }

    # P4a: bit-invariance below 5.0 (probe floors incl. the binding upper end)
    probe = [BINDING_UPPER_FLOOR, 3.9719, 4.0, 4.5, 4.695, 4.991, 5.0]
    p4a = {f"{x}": {"b_delta": float(fb_new(x)) - float(fb_old(x)),
                    "pp_delta": float(fp_new(x)) - float(fp_old(x))}
           for x in probe}
    p4a_ok = all(v["b_delta"] == 0.0 and v["pp_delta"] == 0.0
                 for v in p4a.values())
    # P4b: movement over the committed uncensored endpoints in (5.0, 6.0)
    moved = []
    for e in _endpoints_in_last_interval():
        e["pp_new"] = float(fp_new(e["floor_pct"]))
        e["b_new"] = float(fb_new(e["floor_pct"]))
        e["pp_delta"] = e["pp_new"] - float(fp_old(e["floor_pct"]))
        e["b_delta"] = e["b_new"] - float(fb_old(e["floor_pct"]))
        moved.append(e)
    max_dpp = max(abs(e["pp_delta"]) for e in moved)
    max_db = max(abs(e["b_delta"]) for e in moved)
    gates["P4_blast_radius"] = {
        "pass": bool(p4a_ok and max_dpp <= TOL_PP and max_db <= TOL_B),
        "below_5_bit_invariant": bool(p4a_ok), "probe": p4a,
        "n_endpoints_5_to_6": len(moved),
        "max_abs_pp_delta": max_dpp, "max_abs_b_delta": max_db,
        "endpoints": moved,
    }

    predictions = {}
    for name, p in PREDICTIONS.items():
        got = float(fp_new(p["floor_pct"]))
        lo, hi = p["band_pp"]
        predictions[name] = {**p, "band_pp": [lo, hi], "realized_pp": got,
                             "realized_b": float(fb_new(p["floor_pct"])),
                             "hit": bool(lo <= got <= hi)}

    if not all(g["pass"] for g in gates.values()):
        status = "GATE_FAILURE"

    payload = {
        "mode": "floor_grid_extension",
        "status": status,
        "spec_source": SPEC,
        "harness": ("floor_sweep._run_scored verbatim; committed 75k loan "
                    "sample; RNG_SEED 42; shared macro frame; raw-basis "
                    "scoring; fresh runs"),
        "parity_row_6_0": parity_row,
        "rows": rows,
        "parity_gates": gates,
        "parity_gates_all_pass": bool(status == "OK"),
        "predictions_hit_miss": predictions,
        "interpolation_rule": ("monotone PCHIP through the frozen grid — the "
                              "committed 7 rows plus these 4; no "
                              "extrapolation; refusal semantics unchanged at "
                              "[2.0, 7.0]"),
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=lambda o: o.item())
    print(f"\nstatus {status}; frozen -> {RESULTS_JSON}")
    if status != "OK":
        sys.exit(1)


if __name__ == "__main__":
    main()
