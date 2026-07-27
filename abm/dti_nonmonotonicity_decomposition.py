#!/usr/bin/env python3
"""
dti_nonmonotonicity_decomposition.py — is the DTI sweep's non-monotonicity a
mechanism, or an artifact of the re-calibration switching on at one threshold?

PRE-COMMITTED SPEC (fixed in this header BEFORE any run).

HANDOFF_round22.md §6.3 (round-21 R10 leftover, never started). Liveness gate #97.

THE AWKWARD FACT

dti_threshold_sweep (round 18, gate #49) reports trapped liquidity against the
front-end DTI wall:
    36%  ->  $153.350B      43%  ->  $84.531B      50%  ->  $119.696B
Production sits at 43%, i.e. at the MINIMUM. A referee reads that as: the
paper's own parameter choice is the one that minimises the estimate. The sweep
measured the non-monotonicity; it never decomposed it.

THE HYPOTHESIS, READ OFF THE COMMITTED ARTIFACT BEFORE THIS HEADER WAS WRITTEN

dti_threshold_sweep_results.json floor_retention.per_dti records, per leg, both
the re-calibrated scale and the floor the PRODUCTION scale would have produced:

    dti    recalibrated_scale   recalibrated_floor   fixed_scale_floor
    0.36   43882.8125           0.0442               0.0442      <- no-op
    0.43   43882.8125           0.0483               0.0483      <- no-op
    0.50   41933.59375          0.0447               0.0509      <- FIRED

Only the 50% leg was actually re-calibrated. Loosening the wall to 50% lets more
households clear the DTI gate, which lifts the 8% floor CPR to 0.0509 — outside
the [4,5]% retention band — so the binary search cut the mobility scale from
43,882.81 to 41,933.59 to pull it back to 0.0447. A lower desire scale means
fewer movers, hence LESS prepayment and MORE trapped liquidity. The 50% leg's
rebound from $84.5B to $119.7B may therefore be the re-calibration, not the DTI
wall.

If so this is the same class of finding the paper already names elsewhere: V.A
attributes a 54.9% behavioural-extension figure to "a mechanical recalibration
artifact rather than to loss aversion as a mechanism."

THE TEST

Run the 3 x 2 grid: DTI {0.36, 0.43, 0.50} x scale {FROZEN at the production
43,882.8125, RE-CALIBRATED per the sweep's floor-retention rule}. The
re-calibrated row reproduces the committed sweep; the frozen row is new and
isolates the DTI wall with the absorbing free parameter held still. The
difference at a fixed DTI is the re-calibration channel; the movement along the
frozen row is the DTI channel.

Machinery is IMPORTED from dti_threshold_sweep (build_dti_surface,
calibrate_and_floor, floor_cpr_at) so the two runs cannot drift apart.

UPSTREAM-DRIFT HANDLING, FIXED EX ANTE

The committed sweep is on run-2026-07-05-berger accounting; this run scores on a
live FRED/SOMA frame, which has since moved (a same-day probe put the production
ABM at 11.068% against the committed 11.050%). Levels will therefore NOT replay
bit-exactly, and the round-22 C1 rule forbids widening a tolerance after seeing a
result. So the tolerance is set here, before the run:
  - G1 replays the three committed re-calibrated legs at a DISCLOSED $1.0B
    tolerance, and records the realised offset per leg. This is a sanity check on
    the harness, not a bit-exact parity claim, and it is labelled as such.
  - The REPORTED quantities are all WITHIN-FRAME DIFFERENCES (frozen vs
    re-calibrated at the same DTI; frozen leg vs frozen leg across DTI). Upstream
    drift is common to both arms of every difference and cancels from it, which
    is the same argument B4's fresh-baseline design rests on.
  - If G1's offset is not roughly UNIFORM across the three legs (max minus min
    offset > $1.0B), the drift is not a common level shift, the cancellation
    argument fails, and the run HALTS at T3.

PARITY / INTEGRITY GATES
  G0 the production constants are unmutated at entry: abm.DTI_MAX == 0.43,
     manifest mobility_scale == 43882.8125, and the committed sweep's
     fixed_scale_floor values are as quoted above.
  G1 the three committed re-calibrated legs replay within $1.0B, with a
     roughly uniform offset (see above).
  G2 the frozen and re-calibrated legs COINCIDE at 36% and 43% to 1e-9, because
     the artifact says re-calibration was a no-op there. This is the sharpest
     available check that the frozen path is wired correctly: it must reproduce
     the re-calibrated path exactly wherever the sweep says the two are the same
     thing, and differ only at 50%.
  G3 no committed artifact is overwritten (sha256 before/after).

EX-ANTE INTERPRETIVE PARTITION
  T1 (ARTIFACT) the frozen-scale row is MONOTONE in the DTI wall — trapped
     strictly decreasing as the wall loosens 36 -> 43 -> 50. Then the published
     non-monotonicity is produced by the re-calibration, not by the DTI gate,
     the manuscript says so in VII, and the run ledger gains a row. The
     production 43% is then no longer "the minimum of the sweep" but a point on
     a monotone curve whose 50% end was displaced by the floor-retention rule.
  T2 (MECHANISM) the frozen-scale row is ALSO non-monotone. Then the
     non-monotonicity survives with the free parameter held still, it is a
     property of the DTI gate interacting with the payment-penalty gate, and the
     manuscript must own it as a mechanism result rather than explain it away.
  T3 (DEGENERATE) any gate fails, or the drift is non-uniform, or any leg
     returns a non-finite level. Nothing interpretive is reported.

Neither branch touches a headline: the ABM is a falsification device and the
+5.6pp hazard marginal carries no DTI gate. That is pre-committed here so a T1
cannot be spun into a headline improvement.

Run:  cd abm && python3 dti_nonmonotonicity_decomposition.py
Runtime: ~4 min (6 surface builds x 11 cohorts x 3,380 nodes + 6 scoring passes).
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
import monte_carlo_simulation as mc
from dti_threshold_sweep import build_dti_surface, calibrate_and_floor, floor_cpr_at
from paths import ABM_DIR, LATEST_RUN_MANIFEST

DATA_DIR = ABM_DIR / "data"
RESULTS_JSON = DATA_DIR / "dti_nonmonotonicity_decomposition_results.json"
SWEEP_ARTIFACT = DATA_DIR / "dti_threshold_sweep_results.json"

DTIS = (0.36, 0.43, 0.50)
PROD_DTI = 0.43
PROD_SCALE = 43882.8125
DRIFT_TOL_B = 1.0
GATES: dict = {}


def _flag(name, ok, detail):
    GATES[name] = {"pass": bool(ok), "detail": detail}
    print(f"gate {name}: [{'PASS' if ok else 'FAIL'}] {detail}")


def _halt(reason):
    RESULTS_JSON.write_text(json.dumps(
        {"mode": "dti_nonmonotonicity_decomposition", "status": "GATE_FAILURE",
         "reason": reason, "gates": GATES, "interpretive_verdict": "T3",
         "generated_utc": datetime.now(timezone.utc).isoformat()}, indent=1))
    raise SystemExit(f"[T3 / GATE FAILURE] {reason}")


def _sha(paths):
    return {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in paths if Path(p).is_file()}


def score(surf_df, df0, soma, cohorts) -> dict:
    surface = mc.surface_df_to_surfaces(surf_df)
    m = fed.compute_metrics(df0.copy(), surface=surface, soma_rolloff=soma,
                            cohorts=cohorts, use_burnout=False,
                            apply_settlement_lag_kernel=True)
    hm = fed.export_headline_metrics(m)
    d = hm["dollars_b"]
    return {"us_trapped_b": float(d["us_trapped"]),
            "share_explained_pct": float(d["share_explained_pct"]),
            "mean_cpr_pct": float(hm["cpr_pct"]["us_abm"]["mean"])}


def main() -> None:
    t0 = time.perf_counter()
    watched = [SWEEP_ARTIFACT, LATEST_RUN_MANIFEST]
    sha_before = _sha(watched)

    sweep = json.loads(SWEEP_ARTIFACT.read_text())
    per = sweep["floor_retention"]["per_dti"]
    man = json.loads(LATEST_RUN_MANIFEST.read_text())
    _flag("G0_production_constants",
          abs(abm.DTI_MAX - PROD_DTI) < 1e-15
          and abs(float(man["pipeline"]["mobility_scale"]) - PROD_SCALE) < 1e-9
          and abs(per["dti_0.50"]["fixed_scale_floor_cpr"] - 0.0509) < 1e-9
          and abs(per["dti_0.36"]["fixed_scale_floor_cpr"] - 0.0442) < 1e-9,
          {"DTI_MAX": abm.DTI_MAX, "scale": man["pipeline"]["mobility_scale"]})
    if not GATES["G0_production_constants"]["pass"]:
        _halt("production constants mutated at entry")

    income = float(man["pipeline"]["median_income"])
    home_value = float(man["pipeline"]["median_home_value"])
    df0 = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()
    cohorts = fed.fetch_soma_mbs_cohorts()
    ref = abm.reference_cohort(cohorts)

    legs, offsets = {}, {}
    for dti in DTIS:
        old = abm.DTI_MAX
        abm.DTI_MAX = dti
        try:
            scale_recal, floor_recal = calibrate_and_floor(
                income, home_value, ref["coupon"], ref["months_elapsed"])
            floor_frozen = floor_cpr_at(PROD_SCALE, income, home_value,
                                        ref["coupon"], ref["months_elapsed"])
            for tag, sc, fl in (("recalibrated", scale_recal, floor_recal),
                                ("frozen", PROD_SCALE, floor_frozen)):
                surf = build_dti_surface(dti, sc, income, home_value, cohorts)
                r = score(surf, df0, soma, cohorts)
                r.update({"dti_max": dti, "scale_mode": tag,
                          "mobility_scale": float(sc),
                          "floor_cpr_at_8pct": float(fl)})
                legs[f"dti{dti:g}_{tag}"] = r
                print(f"  dti {dti:.2f} {tag:12s} scale {sc:11.4f} "
                      f"floor {fl:.4f}  trapped ${r['us_trapped_b']:.4f}B")
        finally:
            abm.DTI_MAX = old

    for k, v in legs.items():
        if not all(isinstance(v[f], float) and v[f] == v[f]
                   for f in ("us_trapped_b", "share_explained_pct")):
            _halt(f"non-finite level in leg {k}")

    # G1: replay the committed re-calibrated legs (disclosed tolerance, drift)
    for dti in DTIS:
        want = float(sweep["legs"][f"dti_{dti:.2f}"]["trapped_b"])
        got = legs[f"dti{dti:g}_recalibrated"]["us_trapped_b"]
        offsets[f"dti_{dti:.2f}"] = got - want
    spread = max(offsets.values()) - min(offsets.values())
    _flag("G1_committed_legs_replay_within_drift",
          all(abs(o) < DRIFT_TOL_B for o in offsets.values()) and spread < DRIFT_TOL_B,
          {"offsets_b": offsets, "spread_b": spread, "tol_b": DRIFT_TOL_B,
           "note": "disclosed drift tolerance, not a bit-exact parity claim"})
    if not GATES["G1_committed_legs_replay_within_drift"]["pass"]:
        _halt(f"upstream drift not a uniform level shift (spread ${spread:.4f}B); "
              "the difference-cancellation argument fails")

    # G2: frozen == recalibrated wherever the sweep says re-calibration was a no-op
    noop_ok = True
    noop_detail = {}
    for dti in (0.36, 0.43):
        d = (legs[f"dti{dti:g}_frozen"]["us_trapped_b"]
             - legs[f"dti{dti:g}_recalibrated"]["us_trapped_b"])
        noop_detail[f"dti_{dti:.2f}_diff_b"] = d
        noop_ok = noop_ok and abs(d) < 1e-9
    d50 = (legs["dti0.5_frozen"]["us_trapped_b"]
           - legs["dti0.5_recalibrated"]["us_trapped_b"])
    noop_detail["dti_0.50_diff_b"] = d50
    _flag("G2_frozen_matches_recal_where_noop",
          noop_ok and abs(d50) > 1e-9, noop_detail)
    if not GATES["G2_frozen_matches_recal_where_noop"]["pass"]:
        _halt("frozen path does not reproduce the re-calibrated path where the "
              "sweep records a no-op, or does not differ at 50%")

    _flag("G3_no_overwrite", _sha(watched) == sha_before, {"n": len(sha_before)})
    if not GATES["G3_no_overwrite"]["pass"]:
        _halt("a committed artifact was modified")

    frozen = [legs[f"dti{d:g}_frozen"]["us_trapped_b"] for d in DTIS]
    monotone = frozen[0] > frozen[1] > frozen[2]
    verdict = "T1" if monotone else "T2"
    label = ("ARTIFACT — with the mobility scale held at the production value the "
             "sweep is monotone in the DTI wall; the published non-monotonicity is "
             "produced by the floor-retention re-calibration, which fires only at 50%"
             if monotone else
             "MECHANISM — the non-monotonicity survives with the free parameter held "
             "still, so it is a property of the DTI gate itself")

    payload = {
        "mode": "dti_nonmonotonicity_decomposition",
        "pre_committed": True,
        "question": ("Is the DTI sweep's non-monotonicity a mechanism, or an "
                     "artifact of re-calibration firing at only one threshold?"),
        "legs": legs,
        "frozen_row_trapped_b": dict(zip([f"{d:g}" for d in DTIS], frozen)),
        "frozen_row_monotone": monotone,
        "recalibration_channel_b": {
            f"{d:g}": (legs[f"dti{d:g}_frozen"]["us_trapped_b"]
                       - legs[f"dti{d:g}_recalibrated"]["us_trapped_b"])
            for d in DTIS},
        "committed_sweep_trapped_b": {
            f"{d:g}": float(sweep["legs"][f"dti_{d:.2f}"]["trapped_b"])
            for d in DTIS},
        "upstream_drift_offsets_b": offsets,
        "upstream_drift_spread_b": spread,
        "headline_untouched": True,
        "headline_note": ("The ABM is a falsification device and the +5.6pp hazard "
                          "marginal carries no DTI gate; neither branch moves a "
                          "headline quantity."),
        "t1_artifact": verdict == "T1",
        "t2_mechanism": verdict == "T2",
        "interpretive_verdict": f"{verdict}: {label}",
        "gates": GATES,
        "gates_all_pass": all(g["pass"] for g in GATES.values()),
        "runtime_s": time.perf_counter() - t0,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=1))
    print(f"\nfrozen-scale row: " + "  ".join(
        f"{d:g}%->${v:.3f}B" for d, v in zip(DTIS, frozen)))
    print(f"{verdict}: {label}")
    print(f"wrote {RESULTS_JSON}  ({payload['runtime_s']:.0f}s)")


if __name__ == "__main__":
    main()
