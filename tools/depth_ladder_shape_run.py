#!/usr/bin/env python3
"""R32 / C-80: the 2018 depth ladder's shape.

Run tag: depth_ladder_shape.  Spec: specs/SPEC_R32_c80_depth_ladder_shape.md, committed before
this script was written, and this script committed before it ran.

Re-bins the committed NESTED depth reads into PER-BIN CPRs by exposure-weighted differencing,
so the ladder's shape can be read.  No new estimation: every input is a committed artifact.

Writes ONLY hazard/data/depth_ladder_shape_results.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "hazard" / "data" / "matched_depth_reconciliation_results.json"
OUT = ROOT / "hazard" / "data" / "depth_ladder_shape_results.json"

LEG = "OFF_2018_rising_rate"
# Spec section 2, declared at scoping.
DECLARED_BIN_CPR = {
    "(-0.0025,+0.0000]": 7.092, "(-0.0050,-0.0025]": 6.986,
    "(-0.0075,-0.0050]": 4.669, "(-0.0100,-0.0075]": 4.654,
    "(-0.0150,-0.0100]": 5.143, "(-0.0200,-0.0150]": 4.347,
    "(-0.0250,-0.0200]": 3.606,
}


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    t0 = time.time()
    g = json.loads(SRC.read_text())["step2_matched_depth_grid"][LEG]
    depths = g["depths"]
    ks = sorted(depths, key=lambda k: -depths[k]["gap_threshold"])

    # --- P3: nested sets -> exposure shares decrease, shallowest is 1.0 -------
    shares = [depths[k]["exposure_share_of_gap0"] for k in ks]
    if abs(shares[0] - 1.0) > 1e-12:
        stop("P3", f"shallowest exposure share is {shares[0]}, not 1.0")
    if not all(a > b for a, b in zip(shares, shares[1:])):
        stop("P3", f"exposure shares not decreasing with depth: {shares}")

    bins, prev = [], None
    for k in ks:
        c = depths[k]
        if prev is not None:
            E = prev["exposure_upb"] - c["exposure_upb"]
            num = (prev["exposure_upb"] * prev["cpr_pct"]
                   - c["exposure_upb"] * c["cpr_pct"])
            label = f"({c['gap_threshold']:+.4f},{prev['gap_threshold']:+.4f}]"
            bins.append({
                "bin": label,
                "gap_lo": c["gap_threshold"], "gap_hi": prev["gap_threshold"],
                "cpr_pct": num / E,
                "exposure_upb": E,
                "exposure_share_of_gap0": E / depths["+0.0000"]["exposure_upb"],
                # a bin is well supported only if BOTH its edges are
                "well_supported": bool(c["well_supported"] and prev["well_supported"]),
                "n_cohort_months_hi_edge": prev["n_cohort_months"],
            })
        prev = c
    deepest = {"nested_threshold": prev["gap_threshold"], "cpr_pct": prev["cpr_pct"],
               "exposure_share_of_gap0": prev["exposure_share_of_gap0"],
               "well_supported": bool(prev["well_supported"])}

    # --- P2: declared values ---------------------------------------------------
    for b in bins:
        d = DECLARED_BIN_CPR.get(b["bin"])
        if d is not None and round(b["cpr_pct"], 3) != d:
            stop("P2", f"bin {b['bin']} moved: {b['cpr_pct']:.6f} != declared {d}")

    # --- P1: differencing must INVERT back to the committed nested reads ------
    inversion = {}
    for k in ks:
        thr = depths[k]["gap_threshold"]
        sel = [b for b in bins if b["gap_hi"] <= thr] if thr < 0 else bins
        # all bins at or below this threshold, plus the deepest nested remainder
        sel = [b for b in bins if b["gap_lo"] >= thr - 1e-12 or b["gap_hi"] <= thr]
        sel = [b for b in bins if b["gap_hi"] <= thr]
        E = sum(b["exposure_upb"] for b in sel) + (
            depths[ks[-1]]["exposure_upb"] if True else 0.0)
        num = sum(b["exposure_upb"] * b["cpr_pct"] for b in sel) + (
            depths[ks[-1]]["exposure_upb"] * depths[ks[-1]]["cpr_pct"])
        got = num / E
        want = depths[k]["cpr_pct"]
        inversion[k] = {"got": got, "want": want, "abs_diff": abs(got - want)}
        if abs(got - want) > 1e-9:
            stop("P1", f"differencing does not invert at {k}: {got!r} != {want!r}")

    ws = [b for b in bins if b["well_supported"]]
    plateau = ws[2:] if len(ws) >= 3 else []
    plateau_cov = sum(b["exposure_share_of_gap0"] for b in plateau)
    tail = [b for b in bins if not b["well_supported"]]
    tail_cov = sum(b["exposure_share_of_gap0"] for b in tail)

    payload = {
        "mode": "depth_ladder_shape", "run_tag": "depth_ladder_shape",
        "spec": {"spec_file": "specs/SPEC_R32_c80_depth_ladder_shape.md",
                 "leg": LEG, "window": g["window"],
                 "min_gap_observed": g["min_gap_observed"],
                 "method": "exposure-weighted differencing of the committed nested reads",
                 "no_new_estimation": True},
        "parity": {"differencing_inverts_to_nested_reads": True,
                   "declared_bins_reproduced": True,
                   "exposure_shares_decrease_with_depth": True},
        "inversion_check": inversion,
        "bins": bins,
        "deepest_nested_remainder": deepest,
        "shape": {
            "reading": ("step then plateau: CPR falls from ~7.0 to ~4.66 between the second "
                        "and third bins and then stops falling"),
            "plateau_bins": [b["bin"] for b in plateau],
            "plateau_cpr_pct": [b["cpr_pct"] for b in plateau],
            "plateau_exposure_share": plateau_cov,
            "tail_bins": [b["bin"] for b in tail],
            "tail_cpr_pct": [b["cpr_pct"] for b in tail],
            "tail_exposure_share": tail_cov,
            "form_fork": ("a floor on TOTAL turnover censors the voluntary hazard and predicts "
                          "step-then-plateau; an ADDITIVE competing-risks form never censors "
                          "and predicts continued decline. The plateau is consistent with the "
                          "production max form."),
            "support_conditional": ("the ladder does eventually fall, but every declining cell "
                                    "below the plateau is flagged well_supported=false by the "
                                    "source artifact's own rule and they hold "
                                    f"{tail_cov*100:.2f}% of gap<=0 exposure between them"),
        },
        "runtime_s": round(time.time() - t0, 3),
    }

    blob = json.dumps(payload, indent=2) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write")
    OUT.write_text(blob)

    print(f"{'bin':>22}{'CPR %':>9}{'exposure $bn':>15}{'share':>9}  support")
    for b in bins:
        print(f"{b['bin']:>22}{b['cpr_pct']:>9.3f}{b['exposure_upb']/1e9:>15.2f}"
              f"{b['exposure_share_of_gap0']*100:>8.2f}%  "
              f"{'yes' if b['well_supported'] else 'NO'}")
    print(f"\nplateau {['%.3f' % c for c in payload['shape']['plateau_cpr_pct']]} "
          f"covering {plateau_cov*100:.1f}% of exposure")
    print(f"tail    {['%.3f' % c for c in payload['shape']['tail_cpr_pct']]} "
          f"covering {tail_cov*100:.2f}%")
    print(f"P1 inversion max |diff| = "
          f"{max(v['abs_diff'] for v in inversion.values()):.2e}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
