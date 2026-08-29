#!/usr/bin/env python3
"""
concave_hull_band_ends.py — close the {form x transform} hull over the FULL
off-window floor x band grid, so that "not shown complete" can become a
statement of fact in either direction.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention of
concave_marginal.py / floor_form_offwindow.py / concave_additive_marginal.py,
whose machinery this script imports rather than reimplements).

HANDOFF_round22.md §6.3 / PLAN_remaining_work.md §5. Liveness gate #95.

WHAT IS OPEN, AND WHERE THE MANUSCRIPT SAYS SO
----------------------------------------------
paper/final/paper_final_v1.tex L789, verbatim:
  "The hull is not shown \\emph{complete} over form $\\times$ transform---this
   cell was run at the central elasticity, and its band ends are not"
That sentence is the whole reason this run exists. It is honest today and this
run makes it either unnecessary or wrong; the .tex must move whichever way the
result falls.

The designated hull "$+3.9$ to $+13.1$" (floor_form_offwindow_results.json
designated_interval_pp = [3.891507360127463, 13.09774126267503]) is quoted at
five .tex sites (abstract; tab:headline L68; V.E L473; tab:uncertainty L509;
VII.I L797) and pinned by liveness gate #69. Its two endpoints are:
  lo 3.891507360127463 = MAX form, floor 5.334%, band 5.5
     [oos_identification_results.json instrument1_marginal_table -> the
      5.334 row -> band["5.5"].marginal_pp]
  hi 13.09774126267503 = ADDITIVE form, floor 4.695%, band 7.7
     [floor_form_offwindow_results.json rows -> (additive, 4.695) ->
      band["7.7"].marginal_pp]
Both are LOG-LINEAR-transform cells.

COVERAGE AUDIT (established by reading the committed artifacts before this
header was written, so the scope rests on no assumption):
  LOG-LINEAR transform, off-window grid {4.695, 4.991, 5.334} x {5.5, 6.5, 7.7}
    max form      -> COMPLETE (oos_identification instrument1_marginal_table,
                     9 floor rows each carrying the full 3-point band)
    additive form -> COMPLETE (floor_form_offwindow rows, 3 floors x 3 band)
  CONCAVE transform, same grid
    max form      -> 1 of 9 run: (4.991, 6.5) = +5.056147332383432
                     [concave_marginal_results.json
                      concave_marginal_pp_at_offwindow_point]
    additive form -> 1 of 9 run: (4.991, 6.5) = +9.221867107123714
                     [concave_additive_marginal_results.json
                      concave_additive_marginal_pp_at_offwindow_point]
So the unrun set is exactly 16 concave central cells. This script runs all 18
concave cells fresh (the 2 already-committed ones double as parity anchors
rather than being skipped) plus the 6 nulls the differences need.

WHY THIS CAN MOVE A HEADLINE LITERAL — stated ex ante, not discovered after
--------------------------------------------------------------------------
The concave transform is signed: concave_additive_marginal measured its effect
as -1.3243243462743806pp under the max form and -1.993847000320855pp under the
additive form at the production floor. The hull's LOW endpoint is a max-form
cell at the band's low edge and the highest defensible floor — precisely the
corner a downward-signed transform is most likely to push below. A widening at
the bottom is therefore the live risk, it is headline-adjacent (the lower edge
is quoted in the ABSTRACT), and the branch that governs it is fixed below
BEFORE any number is seen.

SPEC (fixed ex ante)
- Grid: transform=concave x form {max, additive} x floor {4.695, 4.991, 5.334}
  x p_q {5.5, 6.5, 7.7} = 18 central legs. Floors are READ from
  oos_identification_results.json / floor_form_offwindow_results.json at
  runtime and asserted against the literals here to 1e-9; they are never
  hard-coded alone.
- Nulls: p_q = 0 at each (form, floor) = 6 legs. The null does not depend on
  the band point (beta1(0) = 0) and is asserted, not assumed, to be
  transform-invariant (G3).
- Scoring, sample, seed, regime, macro frame: unchanged from
  concave_additive_marginal.py, whose _run_scored this script imports. US-only
  regime, committed 75k loan sample, RNG_SEED 42, one shared macro frame
  fetched once, raw-basis score_extension_risk, fresh microsim runs into
  data/concave_hull_band_ends/ (a SEPARATE directory; G4 asserts the sibling's
  output directory is untouched).
- The 4.0% production floor is OUT OF SCOPE by construction: the hull under
  audit is an OFF-WINDOW hull and 4.0% is the in-sample calibration point.

PARITY GATES (run first, block all interpretation; tolerance 1e-9 on points
and dollars, matching the sibling; each records bit-exactness separately)
  G0 concave x max @4.991 @6.5 marginal == +5.056147332383432
     [concave_marginal_results.json concave_marginal_pp_at_offwindow_point]
  G1 concave x additive @4.991 @6.5 marginal == +9.221867107123714
     [concave_additive_marginal_results.json
      concave_additive_marginal_pp_at_offwindow_point]
  G2 the two committed LOG-LINEAR endpoints replay off THIS harness's null
     legs: the max-form null at 5.334% and the additive-form null at 4.695%
     must equal the committed null_trapped_b to 1e-9
     [oos instrument1_marginal_table 5.334 null_trapped_b;
      floor_form_offwindow (additive, 4.695) null_trapped_b]
  G3 beta1 = 0 transform invariance: at every (form, floor) the concave null
     equals the committed log-linear null to 1e-9. Failure means the concave
     patch leaks into a non-elasticity channel and BLOCKS everything.
  G4 no-overwrite: sha256 of every file in
     data/concave_additive_marginal/ and of the four consumed artifacts is
     unchanged between start and end of this run.
  Any G0-G4 failure raises SystemExit and fixes the verdict at T3.

EX-ANTE INTERPRETIVE PARTITION (fixed here before any result is seen)
  T1 (HULL COMPLETE): all 18 concave cells lie inside the closed committed
     hull [3.891507360127463, 13.09774126267503]. Then the off-window
     {form x transform} x {floor x band} product is CLOSED — 36 of 36 cells
     run — the five .tex literals and gate #69 stand unchanged, and L789's
     "The hull is not shown complete over form x transform---this cell was run
     at the central elasticity, and its band ends are not" is REPLACED by a
     completeness statement naming the 36-cell grid. This is the only branch
     that licenses the word "complete", and it licenses it only over the
     off-window grid, never over the in-sample floor.
  T2 (HULL WIDENS): any concave cell falls outside that closed interval. Then
     the designated hull is incomplete as published. The artifact emits
     new_hull_pp = [min, max] over the committed hull UNION all 36 off-window
     cells (18 concave measured here + the 18 committed log-linear ones read
     from their artifacts). Pre-committed: because this run closes the last
     unrun transform on the full off-window grid, new_hull_pp is the
     REPLACEMENT literal, not a lower bound — the sibling's
     "lower-bound-only" caveat was forced by its central-elasticity-only
     scope and does not apply here. The literal "$+3.9$ to $+13.1$" must then
     move at all five .tex sites, gate #69's designated_interval_pp must be
     re-pinned, and the abstract's uncertainty sentence re-checked. Nothing
     may be reported until every site moves together, in one commit.
  T3 (DEGENERATE / PARITY FAILURE): any G0-G4 fails, or any leg returns a
     non-finite trapped_b or share_pct, or any concave marginal is inert
     (|marginal_pp| < 1e-6). Nothing interpretive is reported; the .tex and
     gates are left alone and the failure is recorded.

WHAT THIS RUN STILL DOES NOT SETTLE (stated ex ante so no successor overreads
a T1): completeness is asserted only over the off-window floor x band grid at
the two transforms and two forms the paper defines. It says nothing about
floor values outside {4.695, 4.991, 5.334}, elasticities outside the
Liebersohn-Rothstein band, a third transform, or the in-sample 4.0% floor.

Run:  cd hazard && python3 concave_hull_band_ends.py
Runtime: ~2.5 min (24 legs at the sibling's measured 5.7 s/leg, from its
committed runtime_s 90.4 over 16 legs).
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

import concave_additive_marginal as cam
import literature_hazard
from config import LOAN_SAMPLE_PATH
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "concave_hull_band_ends"
RESULTS_JSON = DATA_DIR / "concave_hull_band_ends_results.json"

OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
FFO_ARTIFACT = DATA_DIR / "floor_form_offwindow_results.json"
CM_ARTIFACT = DATA_DIR / "concave_marginal_results.json"
CAM_ARTIFACT = DATA_DIR / "concave_additive_marginal_results.json"
CONSUMED = (OOS_ARTIFACT, FFO_ARTIFACT, CM_ARTIFACT, CAM_ARTIFACT)

FLOORS_PCT = (4.695, 4.991, 5.334)
BAND_PQ = (5.5, 6.5, 7.7)
FORMS = ("max", "additive")
NULL_PQ = 0.0

TOL = 1e-9
INERT_PP = 1e-6
COMMITTED_HULL_PP = [3.891507360127463, 13.09774126267503]

GATES: dict = {}


def _gate(name: str, got: float, want: float, tol: float = TOL) -> None:
    diff = abs(got - want)
    GATES[name] = {"got": got, "want": want, "diff": diff, "tol": tol,
                   "bit_exact": diff == 0.0, "pass": bool(diff < tol)}
    print(f"parity gate {name}: got {got:.12f} want {want:.12f} "
          f"diff {diff:.3e} [{'PASS' if diff < tol else 'FAIL'}"
          f"{', bit-exact' if diff == 0.0 else ''}]")


def _flag(name: str, ok: bool, detail) -> None:
    GATES[name] = {"pass": bool(ok), "detail": detail}
    print(f"parity gate {name}: [{'PASS' if ok else 'FAIL'}] {detail}")


def _halt(reason: str) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"mode": "concave_hull_band_ends", "status": "GATE_FAILURE",
         "reason": reason, "gates": GATES, "interpretive_verdict": "T3",
         "generated_utc": datetime.now(timezone.utc).isoformat()}, indent=1))
    raise SystemExit(f"[T3 / GATE FAILURE] {reason}")


def _sha_tree(paths) -> dict:
    out = {}
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    out[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()
        elif p.is_file():
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> None:
    assert literature_hazard.FLOOR_MODE == cam.PRODUCTION_FORM
    assert literature_hazard.INVOLUNTARY_CPR_ANNUAL == cam.PRODUCTION_FLOOR
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    watched = (DATA_DIR / "concave_additive_marginal",) + CONSUMED
    sha_before = _sha_tree(watched)

    oos = json.loads(OOS_ARTIFACT.read_text())
    ffo = json.loads(FFO_ARTIFACT.read_text())
    cm = json.loads(CM_ARTIFACT.read_text())
    camr = json.loads(CAM_ARTIFACT.read_text())

    for i, want in enumerate(COMMITTED_HULL_PP):
        if abs(ffo["designated_interval_pp"][i] - want) > 1e-12:
            _halt(f"committed hull endpoint {i} moved under this script")

    # committed log-linear cells, read (never hard-coded alone)
    oos_rows = {round(r["floor_annual_cpr_pct"], 3): r
                for r in oos["instrument1_marginal_table"]}
    ffo_rows = {round(r["floor_annual_cpr_pct"], 3): r
                for r in ffo["rows"] if r["form"] == "additive"}
    for f in FLOORS_PCT:
        if round(f, 3) not in oos_rows or round(f, 3) not in ffo_rows:
            _halt(f"floor {f} absent from a committed artifact")

    loglinear_cells, committed_nulls = {}, {}
    for f in FLOORS_PCT:
        k = round(f, 3)
        committed_nulls[("max", f)] = float(oos_rows[k]["null_trapped_b"])
        committed_nulls[("additive", f)] = float(ffo_rows[k]["null_trapped_b"])
        for pq in BAND_PQ:
            loglinear_cells[("max", f, pq)] = float(
                oos_rows[k]["band"][str(pq)]["marginal_pp"])
            loglinear_cells[("additive", f, pq)] = float(
                ffo_rows[k]["band"][str(pq)]["marginal_pp"])

    print("Scoring empirical benchmark (shared macro frame, fetched once) …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    if not LOAN_SAMPLE_PATH.exists():
        raise FileNotFoundError(f"{LOAN_SAMPLE_PATH} missing")
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    cam_out_dir = cam.OUT_DIR
    cam.OUT_DIR = OUT_DIR          # keep this run's parquets out of the sibling's dir
    legs: dict = {}
    try:
        for form in FORMS:
            for f in FLOORS_PCT:
                key = f"concave_{form}_{f:g}_null"
                legs[key] = cam._run_scored(loans, macro, empirical,
                                            "concave", form, f / 100.0, NULL_PQ)
                for pq in BAND_PQ:
                    k2 = f"concave_{form}_{f:g}_pq{pq:g}"
                    legs[k2] = cam._run_scored(loans, macro, empirical,
                                               "concave", form, f / 100.0, pq)
                    print(f"  {k2}: trapped ${legs[k2]['trapped_b']:.4f}B")
    finally:
        cam.OUT_DIR = cam_out_dir

    for k, leg in legs.items():
        for fld in ("trapped_b", "share_pct"):
            v = leg[fld]
            if v is None or v != v or abs(v) == float("inf"):
                _halt(f"non-finite {fld} in leg {k}")

    # The benchmark literal every committed artifact scores against. It is
    # asserted rather than trusted, and asserted rather than DERIVED: rebuilding
    # it as trapped_b / share_pct * 100 returns 764.7482532227001, one ULP low,
    # and substituting that would perturb every marginal_pp at 1e-13 and cost
    # G0/G1 their bit-exactness against the committed cells for no gain.
    bench = 764.7482532227002
    _ref = camr["legs"]["loglinear_max_4_central"]
    if abs(_ref["trapped_b"] / _ref["share_pct"] * 100.0 - bench) > 1e-9:
        _halt("benchmark literal disagrees with the committed artifact")
    cells, marginals = {}, []
    for form in FORMS:
        for f in FLOORS_PCT:
            null_b = legs[f"concave_{form}_{f:g}_null"]["trapped_b"]
            for pq in BAND_PQ:
                c = legs[f"concave_{form}_{f:g}_pq{pq:g}"]
                mb = c["trapped_b"] - null_b
                mp = mb / bench * 100.0
                if abs(mp) < INERT_PP:
                    _halt(f"inert marginal at concave/{form}/{f}/{pq}")
                cells[f"{form}|{f:g}|{pq:g}"] = {
                    "form": form, "floor_annual_cpr_pct": f, "p_q_shock_pct": pq,
                    "central_trapped_b": c["trapped_b"],
                    "null_trapped_b": null_b,
                    "marginal_b": mb, "marginal_pp": mp,
                    "central_share_pct": c["share_pct"],
                    "inside_committed_hull": (COMMITTED_HULL_PP[0] <= mp
                                              <= COMMITTED_HULL_PP[1]),
                }
                marginals.append(mp)

    # ---- parity gates -----------------------------------------------------
    _gate("G0_concave_max_4991_65",
          cells["max|4.991|6.5"]["marginal_pp"],
          float(cm["concave_marginal_pp_at_offwindow_point"]))
    _gate("G1_concave_additive_4991_65",
          cells["additive|4.991|6.5"]["marginal_pp"],
          float(camr["concave_additive_marginal_pp_at_offwindow_point"]))
    _gate("G2a_null_max_5334", legs["concave_max_5.334_null"]["trapped_b"],
          committed_nulls[("max", 5.334)])
    _gate("G2b_null_additive_4695",
          legs["concave_additive_4.695_null"]["trapped_b"],
          committed_nulls[("additive", 4.695)])
    for form in FORMS:
        for f in FLOORS_PCT:
            _gate(f"G3_null_transform_invariance_{form}_{f:g}",
                  legs[f"concave_{form}_{f:g}_null"]["trapped_b"],
                  committed_nulls[(form, f)])
    sha_after = _sha_tree(watched)
    _flag("G4_no_overwrite", sha_before == sha_after,
          {"n_watched": len(sha_before),
           "changed": sorted(set(sha_before) ^ set(sha_after))
                      or [k for k in sha_before
                          if sha_after.get(k) != sha_before[k]]})

    if not all(g["pass"] for g in GATES.values()):
        _halt("one or more parity gates failed: "
              + ", ".join(k for k, g in GATES.items() if not g["pass"]))

    # ---- verdict ----------------------------------------------------------
    outside = {k: v for k, v in cells.items() if not v["inside_committed_hull"]}
    all_off_window = list(loglinear_cells.values()) + marginals
    new_hull = [min(COMMITTED_HULL_PP + all_off_window),
                max(COMMITTED_HULL_PP + all_off_window)]

    if outside:
        verdict = "T2"
        detail = (f"HULL WIDENS — {len(outside)} of 18 concave cells fall "
                  f"outside the committed hull "
                  f"[{COMMITTED_HULL_PP[0]:.4f}, {COMMITTED_HULL_PP[1]:.4f}]pp. "
                  f"Replacement hull over all 36 off-window cells: "
                  f"[{new_hull[0]:.4f}, {new_hull[1]:.4f}]pp. The literal "
                  f"'$+3.9$ to $+13.1$' must move at all five .tex sites and "
                  f"gate #69 must be re-pinned, in one commit.")
    else:
        verdict = "T1"
        detail = (f"HULL COMPLETE — all 18 concave cells lie inside the "
                  f"committed hull [{COMMITTED_HULL_PP[0]:.4f}, "
                  f"{COMMITTED_HULL_PP[1]:.4f}]pp. The off-window "
                  f"{{form x transform}} x {{floor x band}} product is now "
                  f"closed at 36 of 36 cells; the five .tex literals and gate "
                  f"#69 stand, and L789's 'not shown complete' sentence is "
                  f"replaced by a completeness statement over this grid.")

    payload = {
        "mode": "concave_hull_band_ends",
        "spec": ("concave transform x {max, additive} x floors "
                 "{4.695, 4.991, 5.334}% x band {5.5, 6.5, 7.7}; 18 central "
                 "legs + 6 nulls; US regime; committed 75k sample; seed 42; "
                 "gates G0-G4; ex-ante T1/T2/T3 fixed before the run"),
        "pre_committed": True,
        "committed_hull_pp": COMMITTED_HULL_PP,
        "cells": cells,
        "legs": legs,
        "loglinear_cells_committed_pp": {f"{k[0]}|{k[1]:g}|{k[2]:g}": v
                                         for k, v in loglinear_cells.items()},
        "concave_marginal_range_pp": [min(marginals), max(marginals)],
        "n_cells_outside_committed_hull": len(outside),
        "cells_outside_committed_hull": outside,
        "new_hull_pp_all_36_offwindow_cells": new_hull,
        "new_hull_is_replacement_not_lower_bound": True,
        "t1_hull_complete": verdict == "T1",
        "t2_hull_widens": verdict == "T2",
        "interpretive_verdict": f"{verdict}: {detail}",
        "residual_scope_not_settled": (
            "Completeness is asserted only over the off-window floor x band "
            "grid at the two transforms and two forms this paper defines. It "
            "says nothing about floors outside {4.695, 4.991, 5.334}, "
            "elasticities outside the Liebersohn-Rothstein band, a third "
            "transform, or the in-sample 4.0% floor."),
        "parity_gates": GATES,
        "parity_gates_all_pass": True,
        "parity_gates_all_bit_exact": all(
            g.get("bit_exact", True) for g in GATES.values()),
        "benchmark_b": bench,
        "runtime_s": time.perf_counter() - t0,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=1))

    print(f"\nconcave marginal range over 18 cells: "
          f"[{min(marginals):.4f}, {max(marginals):.4f}]pp")
    print(f"committed hull: [{COMMITTED_HULL_PP[0]:.4f}, "
          f"{COMMITTED_HULL_PP[1]:.4f}]pp")
    print(f"hull over all 36 off-window cells: [{new_hull[0]:.4f}, "
          f"{new_hull[1]:.4f}]pp")
    print(f"\n{verdict}: {detail}")
    print(f"wrote {RESULTS_JSON}  ({payload['runtime_s']:.0f}s)")


if __name__ == "__main__":
    main()
