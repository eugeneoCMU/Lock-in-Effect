#!/usr/bin/env python3
"""V20-B: floor sampling interval on the rate-inelastic null's recovery
(run tag: null_floor_interval).

Spec: specs/SPEC_V20_B_null_floor_interval_2026-08-04.md (see amendment V20-B-A1 in
the spec header) — adopted and committed before this script; this script committed
before it ran. Guarded-runner pattern: sha-pinned inputs, frozen artifacts read-only,
single JSON output, gates that ABORT. NO engine runs and NO new sampling: the
sampling layer enters exclusively through the committed floor-scale interval
endpoints of floor_inference_correction_results.json (the binding R2 read whose
marginal-scale image was the paper's [+2.9, +8.7] when this ran; that image is
[+1.9, +9.1] since FP2 Batch B decensored the lower endpoint on 2026-08-29, the
floor-unit endpoints themselves unmoved), mapped through a PCHIP built on
the committed floor-sweep grid exactly as floor_uncertainty.py maps the marginal
(same grid, same edge-truncation convention, same $B tolerance for off-node
agreement with committed engine rows).

Writes ONLY data/null_floor_interval_results.json.

Run:  cd hazard && python3 null_floor_interval.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

HAZ = Path(__file__).resolve().parent
if str(HAZ) not in sys.path:
    sys.path.insert(0, str(HAZ))

PINS = {
    "calibration_reconciliation.py": "027f1dbb088520aeb725db9648f6ba89b366a6d7bcb4cea5f4068a71f4070191",
    "floor_uncertainty.py": "ab8bb3b4df49890c0c9fb7dcc0e250f5e4c427f11b557122f4b4d6e43875c02c",
}
ARTIFACT_PINS_RECORDED_AT_RUN = [
    "data/floor_sweep_results.json",
    "data/floor_inference_correction_results.json",
    "data/oos_identification_results.json",
]
for fname, want in PINS.items():
    got = hashlib.sha256((HAZ / fname).read_bytes()).hexdigest()
    if got != want:
        sys.exit(f"ABORT pin mismatch: {fname}")

import calibration_reconciliation as cr        # noqa: E402
from floor_uncertainty import MAPPING_MAX_ERR_B   # noqa: E402

DATA = HAZ / "data"
OUT = DATA / "null_floor_interval_results.json"
BINDING_READ = "R2_2018_gap<=-0.0025_age>=12"   # the committed binding read (v3 spec)
HEADLINE_FLOOR_PCT = 4.991
CAP_B = 764.748253


def main() -> None:
    t0 = time.perf_counter()
    art_hashes = {p: hashlib.sha256((HAZ / p).read_bytes()).hexdigest()
                  for p in ARTIFACT_PINS_RECORDED_AT_RUN}

    sweep = json.loads((DATA / "floor_sweep_results.json").read_text())
    v1 = json.loads((DATA / "floor_inference_correction_results.json").read_text())
    oosr = json.loads((DATA / "oos_identification_results.json").read_text())

    shared = cr._load(cr.SHARED_LAYER)
    bmap = cr.derive_basis_map(shared)
    if not bmap["path_invariance_gate"]["pass"]:
        sys.exit("ABORT: shared-layer path-invariance gate failed")

    # ---- committed grid: floor -> shared null share ------------------------
    floors, shares_shared, trapped_shared = [], [], []
    for row in sweep["rows"]:
        f = float(row["floor_annual_cpr_pct"])
        t_sh, s_sh = cr.to_shared(float(row["null"]["trapped_b"]), bmap)
        floors.append(f); trapped_shared.append(t_sh); shares_shared.append(s_sh)
    order = np.argsort(floors)
    floors = np.array(floors)[order]
    shares_shared = np.array(shares_shared)[order]
    pchip = PchipInterpolator(floors, shares_shared)

    # ---- G-B1a: interpolant reproduces grid nodes exactly ------------------
    node_err = float(np.max(np.abs(pchip(floors) - shares_shared)))
    if node_err > 1e-12:
        sys.exit(f"ABORT G-B1a: node reproduction error {node_err}")

    # ---- G-B1b: off-node agreement with the committed engine rows ----------
    # oos_identification ran the null at floors inside the grid (4.0/4.695/
    # 4.991/5.334); PCHIP must agree within the same $B tolerance
    # floor_uncertainty commits for the marginal mapping (MAPPING_MAX_ERR_B).
    tol_pp = MAPPING_MAX_ERR_B / CAP_B * 100.0
    checks, max_err_pp = {}, 0.0
    for row in oosr["instrument1_marginal_table"]:
        f = float(row["floor_annual_cpr_pct"])
        if not (floors[0] <= f <= floors[-1]):
            continue
        _, s_sh = cr.to_shared(float(row["null_trapped_b"]), bmap)
        err = abs(float(pchip(f)) - s_sh)
        checks[f"{f:.3f}"] = {"engine_shared_pct": s_sh,
                              "pchip_shared_pct": float(pchip(f)),
                              "abs_err_pp": err}
        max_err_pp = max(max_err_pp, err)
    if max_err_pp > tol_pp:
        sys.exit(f"ABORT G-B1b: PCHIP-vs-engine max err {max_err_pp:.4f}pp "
                 f"> tol {tol_pp:.4f}pp")

    point = float(pchip(HEADLINE_FLOOR_PCT))

    # ---- map the committed ladder's floor-scale endpoints ------------------
    reads = v1["reads"][BINDING_READ]
    ladder = {}
    for rung in ("wild_t", "cr1_t_interval", "cr2_t_interval", "cr3_t_interval"):
        f_hi = float(reads[rung]["lower_pp_edge"]["floor_pct"])  # low marginal = high floor
        f_lo = float(reads[rung]["upper_pp_edge"]["floor_pct"])  # high marginal = low floor
        if not (floors[0] <= f_lo <= floors[-1] and floors[0] <= f_hi <= floors[-1]):
            sys.exit(f"ABORT: {rung} endpoint outside committed grid")
        s_at_flo = float(pchip(f_lo))   # null share is DECREASING in floor
        s_at_fhi = float(pchip(f_hi))
        lo, hi = min(s_at_flo, s_at_fhi), max(s_at_flo, s_at_fhi)
        ladder[rung] = {
            "floor_endpoints_pct": [f_lo, f_hi],
            "null_shared_share_interval_pct": [lo, hi],
            "contains_point": bool(lo <= point <= hi),
        }

    # ---- landing branch ----------------------------------------------------
    binding = ladder["wild_t"]
    branch = "L1_lands" if binding["contains_point"] else "L2_STOP_wiring"
    if branch != "L1_lands":
        sys.exit(f"ABORT L2: binding interval {binding} does not contain {point:.2f}")

    payload = {
        "mode": "null_floor_interval",
        "run_tag": "null_floor_interval",
        "spec": "specs/SPEC_V20_B_null_floor_interval_2026-08-04.md",
        "pins": PINS,
        "artifact_hashes": art_hashes,
        "binding_read": BINDING_READ,
        "grid_floors_pct": floors.tolist(),
        "grid_null_shared_share_pct": shares_shared.tolist(),
        "gates": {
            "G_B1a_node_err": node_err,
            "G_B1b_offnode": {"tol_pp": tol_pp, "max_err_pp": max_err_pp,
                              "rows": checks},
            "no_new_sampling": True,
        },
        "point_shared_share_pct_at_headline_floor": point,
        "ladder": ladder,
        "binding_interval_pct": ladder["wild_t"]["null_shared_share_interval_pct"],
        "landing_branch": branch,
        "runtime_s": round(time.perf_counter() - t0, 2),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    b = ladder["wild_t"]["null_shared_share_interval_pct"]
    print(f"== null recovery at 4.991: {point:.2f}% shared; wild-t "
          f"[{b[0]:.1f}, {b[1]:.1f}]%; CR3-BM "
          f"{ladder['cr3_t_interval']['null_shared_share_interval_pct']}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
