#!/usr/bin/env python3
"""R32 / C-77: the Aladangady reconciliation re-solved under the ADDITIVE floor form.

Run tag: scaled_null_housing_activity_additive.  Spec: specs/SPEC_R32_c77_aladangady_additive.md,
committed before this script was written, and this script committed before it ran.

Same calibration condition, same mapping M1, same bisection parameters -- only the floor form
changes:

    find phi* with  trapped_null(phi*) - trapped_null(1) = (0.56/0.44)*[central(1) - null(1)]

THIS IS A REAL ENGINE RUN and the engine is SINGLE-TENANT (hazard/data/floor_sweep/).  Do not run
it concurrently with any other engine run.

scaled_null_housing_activity.py and floor_form_mixture.py and both their artifacts are FROZEN:
imported and read, never written, and neither main() is called.

Writes ONLY data/scaled_null_housing_activity_additive_results.json.

Run:  cd hazard && python3 scaled_null_housing_activity_additive.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl

HAZ = Path(__file__).resolve().parent
ROOT = HAZ.parent
if str(HAZ) not in sys.path:
    sys.path.insert(0, str(HAZ))

import floor_sweep as fs                              # noqa: E402
import literature_hazard as lh                        # noqa: E402
import scaled_null_housing_activity as snha           # noqa: E402
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly  # noqa: E402

DATA = HAZ / "data"
OUT = DATA / "scaled_null_housing_activity_additive_results.json"
MAX_ARTIFACT = DATA / "scaled_null_housing_activity_results.json"     # FROZEN
MIX_ARTIFACT = DATA / "floor_form_mixture_results.json"               # FROZEN
OOS_ARTIFACT = DATA / "oos_identification_results.json"
LOCK = DATA / "floor_sweep" / ".c77_additive.lock"

PINS = {
    HAZ / "scaled_null_housing_activity.py":
        "c8641a7ee97ffb53a2e71f31778a0f83376cb96d94417b1b3a60963749d293d7",
    HAZ / "literature_hazard.py":
        "c75a653b53cbc0ea033dc7b54cb62804b630a701c2a044d6a8288838decb9540",
    HAZ / "competing_risks.py":
        "08be5b3c74c75f5c543fb857e52c4d54e9fd6bb31f4cbd29b21989acbf4aa29a",
    HAZ / "config.py":
        "faae6a5c0c2a83083aa9cee990836f4d544cd0ea55fb920e83f0df36d009168e",
    MAX_ARTIFACT: "265a665e9dc081c2dee2d64fed4bbf22ccaad0e2358309de0e41c22ecca9740e",
    MIX_ARTIFACT: "527a74e4c3bb31c8b68ddcf03e1754fc16db8ad2aaeea5ecf3529e3260472d29",
}

E3_MARGINAL_BAR_PP = 4.0        # spec section 4: additive root marginal > this
BENCH_B = 764.7482532227002     # benchmark for pp conversion


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_additive(loans, empirical, floor: float, pq: float, phi: float) -> dict:
    """snha.run_cell (mapping M1: phi scales h0 in both legs, floor untouched) with the
    production ADDITIVE floor form selected -- the same code path floor_form_mixture uses for
    its s = 1 endpoint. The form is restored in finally."""
    cur = lh.FLOOR_MODE
    lh.FLOOR_MODE = "additive"
    try:
        return snha.run_cell(loans, empirical, floor, pq, phi)
    finally:
        lh.FLOOR_MODE = cur


def main() -> None:
    t_wall = time.perf_counter()

    # ---- P0 ----------------------------------------------------------------
    for p, want in PINS.items():
        got = sha(p)
        if got != want:
            stop("P0", f"{p.relative_to(ROOT)} sha256 {got} != pinned {want}")
    pre = {str(p.relative_to(ROOT)): sha(p) for p in PINS}

    # ---- SINGLE-TENANCY: fail closed --------------------------------------
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        stop("TENANCY", f"{LOCK} exists -- another C-77 run may be in flight. The engine is "
                        f"single-tenant; remove the lock only if you are certain no run is live")
    LOCK.write_text(f"pid {os.getpid()}\n")

    try:
        # ---- P5: anchor integrity, ratio RECOMPUTED not hard-coded ---------
        ratio = snha.NON_RATE_SHARE / snha.RATE_SHARE
        if abs(ratio - 1.272727272727273) > 1e-15 or abs(ratio - snha.RATIO_SPEC) > 1e-6:
            stop("P5", f"ratio drifted: {ratio!r}")
        off = json.load(open(OOS_ARTIFACT))["headline_oos_marginal"]["clean_floor_point_pct"]
        if abs(off - 4.991) > 1e-9:
            stop("P5", f"off-window floor moved: {off}")
        floors = {"4": 0.04, "4.991": off / 100.0}

        # ---- P3: baseline identity at phi = 1, before any run --------------
        age = np.arange(0, 361, dtype=np.float64)
        p1 = snha.scaled_baseline(1.0)
        d_h0 = float(np.max(np.abs(p1(age) - lh.h0_psa(age))))
        d_base = float(np.max(np.abs(p1(age) - snha._ORIG_BASELINE(age))))
        if d_h0 != 0.0 or d_base != 0.0:
            stop("P3", f"baseline identity broken: {d_h0}/{d_base}")
        print(f"P3 baseline identity at phi=1: {d_h0:.1e} / {d_base:.1e}  [PASS]")

        maxart = json.load(open(MAX_ARTIFACT))
        mixart = json.load(open(MIX_ARTIFACT))
        if maxart.get("status") != "OK" or not maxart.get("parity_gates_all_pass"):
            stop("P2", "the committed max-form artifact is not a clean OK/all-pass run")
        if not mixart.get("parity_gates_all_pass"):
            stop("P1", "the committed mixture artifact is not a clean all-pass run")

        print("Shared macro frame (fetched once) ...")
        macro = fetch_data()
        soma = fetch_soma_mbs_monthly()
        empirical = build_empirical_metrics(macro, soma_rolloff=soma)
        loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

        # ---- P2: the four committed MAX legs re-run, before the form switch -
        print("\nP2 — max-form parity (environment certification, before the switch)")
        p2 = {}
        for fk, fl in floors.items():
            for pq in (snha.NULL_PQ, snha.CENTRAL_PQ):
                want = snha.ANCHORS[(round(fl, 5), pq)]
                got = snha.run_cell(loans, empirical, fl, pq, 1.0)["trapped_b"]
                ok = abs(got - want) < snha.TOL
                p2[f"{fk}|{pq:g}"] = {"got": got, "want": want, "pass": ok}
                print(f"  P2 max {fk}%|pq{pq:g}: {got:.10f} vs {want:.10f} "
                      f"[{'PASS' if ok else 'FAIL'}]")
                if not ok:
                    stop("P2", f"max-form leg {fk}|{pq:g} does not reproduce")

        # ---- P1: the additive phi = 1 cells ARE the committed s = 1 legs ----
        print("\nP1 — additive-endpoint parity vs floor_form_mixture s=1 (live)")
        p1g, add1 = {}, {}
        for fk, fl in floors.items():
            for pq in (snha.NULL_PQ, snha.CENTRAL_PQ):
                want = mixart["cells"][f"{fk}|1|{pq:g}"]["trapped_b"]
                got = run_additive(loans, empirical, fl, pq, 1.0)["trapped_b"]
                ok = abs(got - want) < snha.TOL
                p1g[f"{fk}|{pq:g}"] = {"got": got, "want": want, "pass": ok}
                add1[(fk, pq)] = got
                print(f"  P1 add {fk}%|pq{pq:g}: {got:.10f} vs {want:.10f} "
                      f"[{'PASS' if ok else 'FAIL'}]")
                if not ok:
                    stop("P1", f"additive phi=1 leg {fk}|{pq:g} does not reproduce "
                               f"floor_form_mixture's s=1 endpoint")

        # ---- the re-solve ---------------------------------------------------
        roots = {}
        for fk, fl in floors.items():
            null1 = add1[(fk, snha.NULL_PQ)]
            cent1 = add1[(fk, snha.CENTRAL_PQ)]
            marg1 = cent1 - null1
            req = ratio * marg1
            print(f"\nfloor {fk}%: additive null(1) {null1:.4f}, central(1) {cent1:.4f}, "
                  f"marginal {marg1:.4f} -> required lift ${req:.4f}B")

            lo, hi = snha.BISECT_LO, snha.BISECT_HI
            cache = {1.0: null1}

            def lift(phi: float) -> float:
                if phi not in cache:
                    cache[phi] = run_additive(loans, empirical, fl,
                                              snha.NULL_PQ, phi)["trapped_b"]
                return cache[phi] - null1

            lo_lift = lift(lo)
            if lo_lift < req:
                roots[fk] = {"no_root": True, "converged": False,
                             "required_lift_b": req,
                             "achievable_lift_at_bracket_lo_b": lo_lift,
                             "bracket": [lo, hi],
                             "note": ("NO ROOT inside the committed bracket: the additive form "
                                      "cannot be calibrated to Aladangady's 44% share within the "
                                      "achievable range of phi. Landed as a form-conditional "
                                      "finding (spec Branch C).")}
                print(f"  NO ROOT: achievable lift at phi={lo} is ${lo_lift:.4f}B "
                      f"< required ${req:.4f}B")
                continue

            # ---- LADDER SEEDING (spec section 3: "a ladder is run first to seed the
            # bracket, exactly as the committed run does").  The committed max-form run
            # records bracket_seeded_from_ladder=true against a drafted [0.3, 1.0]; that
            # seeding is what makes MAX_ITERS=10 sufficient.  The first version of this
            # runner omitted it and exhausted 10 iterations from the full bracket with a
            # residual above tolerance -- a spec-compliance defect, repaired here.  The
            # bisection parameters themselves are NOT re-tuned.
            ladder_phis = sorted(set(snha.PHIS
                                     + ([snha.XROUTE_PHI] if snha.CROSS_ROUTE else [])))
            ladder = {p: lift(p) for p in ladder_phis}       # lift DECREASES in phi
            for a, b in zip(ladder_phis, ladder_phis[1:]):
                if ladder[a] >= req >= ladder[b]:
                    lo, hi = a, b
                    break
            print(f"  ladder {[f'{p:.2f}:{ladder[p]:.2f}' for p in ladder_phis]} "
                  f"-> seeded bracket [{lo}, {hi}]")

            it, resid, mid = 0, None, None
            while it < snha.MAX_ITERS:
                it += 1
                mid = 0.5 * (lo + hi)
                resid = lift(mid) - req
                print(f"  iter {it}: phi {mid:.8f}  lift {lift(mid):.4f}  "
                      f"resid {resid:+.4f}")
                if abs(resid) <= snha.ROOT_TOL_B:
                    break
                if resid > 0:
                    lo = mid
                else:
                    hi = mid
            cent_root = run_additive(loans, empirical, fl,
                                     snha.CENTRAL_PQ, mid)
            null_root = cache[mid]
            marg_root_b = cent_root["trapped_b"] - null_root
            roots[fk] = {
                "no_root": False,
                "phi_star": mid, "psa_speed_effective": 100.0 * mid,
                "iterations": it, "residual_b": resid,
                "converged": bool(abs(resid) <= snha.ROOT_TOL_B),
                "tolerance_b": snha.ROOT_TOL_B, "max_iters": snha.MAX_ITERS,
                "bracket_final": [lo, hi],
                "bracket_drafted": [snha.BISECT_LO, snha.BISECT_HI],
                "bracket_seeded_from_ladder": True,
                "ladder_null_lift_b": {f"{p:.2f}": ladder[p] for p in ladder_phis},
                "required_lift_b": req, "realized_lift_b": lift(mid),
                "null_trapped_b": null_root,
                "central_trapped_b": cent_root["trapped_b"],
                "null_mean_cpr_pct": cent_root.get("null_mean_cpr_pct"),
                "marginal_b": marg_root_b,
                "marginal_pp": marg_root_b / BENCH_B * 100.0,
                "floor_bind_share": cent_root.get("floor_bind_share"),
                "additive_marginal_at_phi1_b": marg1,
                "additive_marginal_at_phi1_pp": marg1 / BENCH_B * 100.0,
            }
            print(f"  ROOT phi* = {mid:.8f}, surviving marginal "
                  f"${marg_root_b:.4f}B = {marg_root_b / BENCH_B * 100:.4f}pp")

        # ---- P4: restoration + bind anchors --------------------------------
        if not snha.restoration_ok():
            stop("P4", f"state not restored: FLOOR_MODE={lh.FLOOR_MODE}, "
                       f"PSA_SPEED={lh.PSA_SPEED}")
        bind_probe = snha.run_cell(loans, empirical, floors["4.991"],
                                   snha.CENTRAL_PQ, 1.0)
        want_bind = snha.BINDS[(0.04991, snha.CENTRAL_PQ)]
        got_bind = bind_probe.get("floor_bind_share")
        bind_ok = got_bind is not None and abs(got_bind - want_bind) < 1e-12
        print(f"\nP4 restoration OK; max-form bind share {got_bind} vs {want_bind} "
              f"[{'PASS' if bind_ok else 'FAIL'}]")
        if not bind_ok:
            stop("P4", "max-form bind-share anchor does not reproduce after the form switch")

        # ---- expectations ---------------------------------------------------
        # E2 as the spec states it: no_root == false AND converged == true AND the residual
        # inside tolerance. The first version tested only no_root and reported E2 PASS on a
        # weaker condition than the spec; that omission is the reason this run was repeated.
        e2 = all((not r["no_root"]) and r.get("converged") is True
                 and abs(r.get("residual_b", 1e9)) <= snha.ROOT_TOL_B
                 for r in roots.values())
        e3_cells = {fk: (r.get("marginal_pp") if not r["no_root"] else None)
                    for fk, r in roots.items()}
        e3 = bool(e2 and all(v is not None and v > E3_MARGINAL_BAR_PP
                             for v in e3_cells.values()))

        payload = {
            "mode": "scaled_null_housing_activity_additive",
            "run_tag": "scaled_null_housing_activity_additive",
            "status": "OK",
            "spec": {
                "spec_file": "specs/SPEC_R32_c77_aladangady_additive.md",
                "calibration_condition": snha.CALIBRATION_CONDITION,
                "ratio": ratio, "rate_share": snha.RATE_SHARE,
                "non_rate_share": snha.NON_RATE_SHARE,
                "mapping": ("M1 unchanged: phi scales the PSA baseline h0 in BOTH legs, floor "
                            "untouched. M2/M3/M4 stay rejected -- re-opening the mapping under a "
                            "different form would change the estimand and break comparability "
                            "with the max-form row this run sits beside."),
                "floor_form": ("production ADDITIVE code path -- the same lh.FLOOR_MODE switch "
                               "floor_form_mixture uses for its s=1 endpoint"),
                "bisection": {"bracket": [snha.BISECT_LO, snha.BISECT_HI],
                              "tol_b": snha.ROOT_TOL_B, "max_iters": snha.MAX_ITERS,
                              "not_retuned": True},
                "danish_leg_disclosure": ("competing_risks.py:148 calls prepay_hazard on the "
                                          "Danish us_intercept branch too, so the Danish leg "
                                          "simulated in the same run also carries the scaled "
                                          "baseline. Only the U.S. leg is scored."),
                "engine_run": True, "engine_is_single_tenant": True,
            },
            "parity_gates": {
                "P0_sha_pins": {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
                "P1_additive_endpoint_parity": p1g,
                "P2_max_form_parity": p2,
                "P3_baseline_identity": {"vs_h0_psa": d_h0, "vs_baseline_hazard": d_base},
                "P4_restoration_and_bind_anchor": {"restored": True,
                                                   "bind_share": got_bind,
                                                   "want": want_bind},
                "P5_ratio_recomputed": ratio, "P5_floor_read_live_pct": off,
            },
            "committed_max_form": {
                fk: {k: maxart["root"][fk][k] for k in
                     ("phi_star", "marginal_pp", "floor_bind_share", "required_lift_b")}
                for fk in ("4", "4.991")},
            "roots_additive": roots,
            "expectations": {
                "E2_root_exists_both_floors": e2,
                "E3_bar_pp": E3_MARGINAL_BAR_PP,
                "E3_marginal_pp_by_floor": e3_cells, "E3_pass": e3,
                "E4_phi_star_direction_deliberately_not_predicted": {
                    "additive": {fk: r.get("phi_star") for fk, r in roots.items()},
                    "max_committed": {fk: maxart["root"][fk]["phi_star"]
                                      for fk in ("4", "4.991")},
                    "note": ("either direction lands and neither is scored as a miss; the "
                             "spec declined to guess a direction it could not derive"),
                },
            },
            "runtime_s": round(time.perf_counter() - t_wall, 3),
        }

        for p in PINS:
            if sha(p) != pre[str(p.relative_to(ROOT))]:
                stop("W1", f"{p.name} changed during the run -- a frozen input was written")

        blob = json.dumps(payload, indent=2, default=float) + "\n"
        if OUT.exists():
            old = json.loads(OUT.read_text())
            drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
            if drop(old) == drop(payload):
                print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
                return
            stop("W1", f"{OUT} exists and differs -- frozen on write")
        OUT.write_text(blob)

        print("\n" + "=" * 72)
        for fk, r in roots.items():
            if r["no_root"]:
                print(f"floor {fk}%: NO ROOT (required ${r['required_lift_b']:.2f}B, "
                      f"achievable ${r['achievable_lift_at_bracket_lo_b']:.2f}B)")
            else:
                mx = maxart["root"][fk]
                print(f"floor {fk}%: additive phi* {r['phi_star']:.6f} -> marginal "
                      f"{r['marginal_pp']:+.4f}pp   |   max-form phi* {mx['phi_star']:.6f} -> "
                      f"{mx['marginal_pp']:+.4f}pp (bind {mx['floor_bind_share']:.4f})")
        print(f"E2 {'PASS' if e2 else 'MISS'}   E3 {'PASS' if e3 else 'MISS'} "
              f"(bar {E3_MARGINAL_BAR_PP}pp)")
        print(f"Saved: {OUT}")
    finally:
        lh.FLOOR_MODE = "max"
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
