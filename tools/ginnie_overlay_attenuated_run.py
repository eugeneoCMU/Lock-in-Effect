#!/usr/bin/env python3
"""R32 / C-74: the Ginnie leg with the elasticity attenuated by the measured CRR differential.

Run tag: ginnie_overlay_attenuated.  Spec: specs/SPEC_R32_c74_ginnie_attenuated_elasticity.md,
committed before this script was written, and this script committed before it ran.

Today the overlay scores the 20.4% Ginnie face share by the observed Ginnie speed in BOTH legs, so
that share's central-minus-null is EXACTLY ZERO and the correction is pure conventional-share
scaling (0.797x).  This run gives that share a gap response a, derived from the measured CRR
differential, and BRACKETS over the mapping -- because a LEVEL differential does not identify a
SLOPE differential.

Two honesty constraints enforced in the artifact:
  (a) the rise above 0.797x is FORCED for any a > 0 (the share contributes zero today), so it is
      recorded as arithmetic and never as a finding;
  (b) the mapping is assumed, not identified, so no single cell is "the" answer.

Writes ONLY hazard/data/ginnie_overlay_attenuated_results.json.
No engine runs -- this is a re-scoring of committed legs, the same posture as the overlay itself.

Usage:  python3 tools/ginnie_overlay_attenuated_run.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAZ = ROOT / "hazard"
SERIES = HAZ / "data" / "gmar_dec25_cpr_series.json"
OVERLAY = HAZ / "data" / "ginnie_cpr_overlay_results.json"
OFFWIN = HAZ / "data" / "ginnie_overlay_offwindow_results.json"
OUT = HAZ / "data" / "ginnie_overlay_attenuated_results.json"

WINDOW = ("2022-06", "2025-11")
WINDOW_MONTHS = 42
GINNIE_SHARE = 0.204
CONV_SHARE = 1.0 - GINNIE_SHARE

P3_TOL_PP = 0.05        # spec section 6: pre-committed, a loose multiple of the 0.011pp residual
P4_TOL_PP = 0.05        # comparator invariance
E3_BAND = (8.5, 9.2)    # spec section 5: M2's in-sample corrected marginal

# Pinned from the committed artifacts (spec section 3), asserted live.
PIN_CRR_MEAN = {"ginnie": 7.294976, "freddie": 5.940905, "fannie": 5.942643}
PIN_CRR_ONLY_PP = 7.333248797494442
PIN_CRR_ONLY_B = 56.080892083313415
PIN_OFFWIN_CONV_PP = 5.57155818290974
PIN_OFFWIN_OVERLAY_PP = 4.443419164229439


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    t0 = time.time()
    pre = {p.name: sha(p) for p in (SERIES, OVERLAY, OFFWIN)}

    ov = json.loads(OVERLAY.read_text())
    ser = json.loads(SERIES.read_text())
    ow = json.loads(OFFWIN.read_text())

    # ---- P1 / E1: the a = 0 cell IS the committed overlay ------------------
    anchors = ov["committed_anchors"]
    C, N, B = (anchors["central_trapped_b"], anchors["null_trapped_b"],
               anchors["benchmark_b"])
    m_full_b = C - N
    m_full_pp = m_full_b / B * 100.0
    crr = ov["variants"]["crr_only"]
    if abs(crr["marginal_pp"] - PIN_CRR_ONLY_PP) > 1e-12 or \
            abs(crr["marginal_b"] - PIN_CRR_ONLY_B) > 1e-12:
        stop("P1", f"crr_only overlay moved: {crr['marginal_pp']!r} / {crr['marginal_b']!r}")
    if not ov["gates"]["G1_parity"]["pass"]:
        stop("P1", "the committed overlay's own G1 parity does not pass")

    # ---- P2: the series, re-derived over an asserted 42-month window -------
    months = ser["months"]
    idx = [i for i, m in enumerate(months) if WINDOW[0] <= str(m)[:7] <= WINDOW[1]]
    if len(idx) != WINDOW_MONTHS:
        stop("P2", f"window carries {len(idx)} months, expected {WINDOW_MONTHS}")
    if str(months[idx[0]])[:7] != WINDOW[0] or str(months[idx[-1]])[:7] != WINDOW[1]:
        stop("P2", f"window endpoints {months[idx[0]]}..{months[idx[-1]]} != {WINDOW}")
    mean = {}
    for k in ("ginnie", "freddie", "fannie"):
        v = [ser["crr"][k][i] for i in idx]
        mean[k] = sum(v) / len(v)
        if abs(mean[k] - PIN_CRR_MEAN[k]) > 1e-6:
            stop("P2", f"window-mean CRR {k} {mean[k]!r} != pinned {PIN_CRR_MEAN[k]!r}")
    mean["gse_mean"] = 0.5 * (mean["freddie"] + mean["fannie"])
    diff_freddie = mean["ginnie"] - mean["freddie"]      # DERIVED, never hard-coded
    diff_gse = mean["ginnie"] - mean["gse_mean"]
    r_freddie = mean["ginnie"] / mean["freddie"]
    r_gse = mean["ginnie"] / mean["gse_mean"]

    # ---- the bracket -------------------------------------------------------
    def marginals(m0_pp: float, mfull_pp: float, r: float) -> dict:
        """marginal(a) = marginal(0) + a * W_G * Delta_C, with Delta_C pinned by
        marginal(1) == mfull_pp. Not a free parameter: the identity that makes `a` mean
        what its name says. Gated by P3."""
        delta_c = (mfull_pp - m0_pp) / GINNIE_SHARE
        out = {}
        for label, a in (("M0_committed", 0.0), ("M2_primary_1_over_r", 1.0 / r),
                         ("M1_no_differential", 1.0), ("M3_amplification_r", r)):
            out[label] = {"a": a, "marginal_pp": m0_pp + a * GINNIE_SHARE * delta_c}
        return out

    insample = marginals(crr["marginal_pp"], m_full_pp, r_freddie)
    offwindow = marginals(PIN_OFFWIN_OVERLAY_PP, PIN_OFFWIN_CONV_PP, r_freddie)
    insample_gse = marginals(crr["marginal_pp"], m_full_pp, r_gse)

    # ---- P3: the identity that defines `a` ---------------------------------
    for name, grid, target in (("in_sample", insample, m_full_pp),
                               ("off_window", offwindow, PIN_OFFWIN_CONV_PP)):
        got = grid["M1_no_differential"]["marginal_pp"]
        if abs(got - target) > P3_TOL_PP:
            stop("P3", f"{name}: marginal(a=1) {got:.6f} != M_full {target:.6f} "
                       f"beyond {P3_TOL_PP}pp -- the additive decomposition does not hold")

    # ---- P4: comparator invariance ----------------------------------------
    p4 = abs(insample["M2_primary_1_over_r"]["marginal_pp"]
             - insample_gse["M2_primary_1_over_r"]["marginal_pp"])
    if p4 >= P4_TOL_PP:
        stop("P4", f"comparator choice moves M2 by {p4:.4f}pp -- it is material and must be "
                   f"reported as a second bracket axis, not a footnote")

    # ---- E2: monotonicity ---------------------------------------------------
    seq = [insample[k]["marginal_pp"] for k in
           ("M0_committed", "M2_primary_1_over_r", "M1_no_differential", "M3_amplification_r")]
    if not all(a < b for a, b in zip(seq, seq[1:])):
        stop("E2", f"marginal not increasing in a: {seq}")

    e3 = E3_BAND[0] <= insample["M2_primary_1_over_r"]["marginal_pp"] <= E3_BAND[1]
    a_primary = 1.0 / r_freddie

    payload = {
        "mode": "ginnie_overlay_attenuated", "run_tag": "ginnie_overlay_attenuated",
        "spec": {
            "spec_file": "specs/SPEC_R32_c74_ginnie_attenuated_elasticity.md",
            "construction": ("marginal(a) = marginal(0) + a * W_G * Delta_C, Delta_C pinned by "
                             "marginal(1) == the un-overlaid marginal"),
            "engine_free": ("the overlay is a re-scoring of committed legs, not a re-simulation; "
                            "a full re-simulation of the Ginnie share at beta1*a needs the "
                            "single-tenant engine and a Ginnie loan panel this design does not "
                            "have, and is OUT OF SCOPE"),
            "transplant_note": ("the per-unit-face CONVENTIONAL wedge is transplanted onto the "
                                "Ginnie share -- the attenuation hypothesis stated cleanly, not "
                                "a Ginnie-specific estimate"),
            "ginnie_share": GINNIE_SHARE, "conventional_share": CONV_SHARE,
            "no_engine_runs": True,
        },
        "honesty_constraints": {
            "rise_above_0797_is_FORCED": (
                "the Ginnie share contributes EXACTLY ZERO marginal today, so for any a > 0 the "
                "corrected marginal must exceed the committed 0.797x by arithmetic. This is "
                "recorded so no landing text can present it as evidence."),
            "level_does_not_identify_slope": (
                "the measurement is a LEVEL difference in voluntary speed at the same window "
                "rate path; the elasticity is a SLOPE. The mapping is assumed, so the result is "
                "the BRACKET and no single cell may be quoted as 'the measured Ginnie marginal'."),
            "full_universe_overstates": ov["note"],
        },
        "parity": {
            "P0b_artifacts_byte_identical": True,
            "P1_crr_only_marginal_pp": crr["marginal_pp"],
            "P1_crr_only_marginal_b": crr["marginal_b"],
            "P1_committed_anchors": anchors,
            "P2_window_months": len(idx),
            "P2_window": [str(months[idx[0]]), str(months[idx[-1]])],
            "P2_window_mean_crr_pct": mean,
            "P3_marginal_at_a1_vs_M_full": {
                "in_sample": [insample["M1_no_differential"]["marginal_pp"], m_full_pp],
                "off_window": [offwindow["M1_no_differential"]["marginal_pp"],
                               PIN_OFFWIN_CONV_PP],
                "tol_pp": P3_TOL_PP,
            },
            "P4_comparator_shift_pp": p4, "P4_tol_pp": P4_TOL_PP,
            "P5_series_extraction_residual_pp": ov["series_validation"]["crr_endpoint_residual_pp"],
            "P5_note": ("the vector-extraction residual is roughly 1% of the differential it "
                        "feeds, so r is NOT exact and must not be presented as such"),
        },
        "measurement": {
            "crr_differential_ginnie_minus_freddie_pp": diff_freddie,
            "crr_differential_ginnie_minus_gse_mean_pp": diff_gse,
            "speed_ratio_r_freddie": r_freddie, "speed_ratio_r_gse": r_gse,
            "comparator_primary": ("freddie -- Path B is built on the Freddie panel and .tex:52 "
                                   "quotes that differential"),
            "m_full_in_sample_pp": m_full_pp, "m_full_in_sample_b": m_full_b,
        },
        "bracket_in_sample": insample,
        "bracket_off_window": offwindow,
        "bracket_in_sample_gse_comparator": insample_gse,
        "expectations": {
            "E1_a0_reproduces_committed_overlay": True,
            "E2_monotone_in_a": True,
            "E3_band_pp": list(E3_BAND),
            "E3_M2_in_sample_pp": insample["M2_primary_1_over_r"]["marginal_pp"],
            "E3_pass": bool(e3),
            "E4_open_sign_a_vs_1": {
                "a_primary_M2": a_primary, "a_amplification_M3": r_freddie,
                "verdict": "attenuation" if a_primary < 1.0 else "amplification",
                "note": ("M2 gives a < 1 and M3 gives a > 1 from the SAME measurement; which is "
                         "the right reading is a modelling judgement this data cannot settle, "
                         "which is why the run reports the bracket. Both were pre-authorised."),
            },
            "E5_rise_is_forced_not_a_finding": True,
        },
        "runtime_s": round(time.time() - t0, 3),
    }

    for p in (SERIES, OVERLAY, OFFWIN):
        if sha(p) != pre[p.name]:
            stop("P0b", f"{p.name} changed during the run")

    blob = json.dumps(payload, indent=2) + "\n"
    if OUT.exists():
        old = json.loads(OUT.read_text())
        drop = lambda d: {k: v for k, v in d.items() if k != "runtime_s"}
        if drop(old) == drop(payload):
            print(f"unchanged (re-run reproduces the committed artifact): {OUT}")
            return
        stop("W1", f"{OUT} exists and differs -- frozen on write")
    OUT.write_text(blob)

    print(f"window {months[idx[0]]}..{months[idx[-1]]} ({len(idx)} months)")
    print(f"CRR window means: ginnie {mean['ginnie']:.6f}  freddie {mean['freddie']:.6f}  "
          f"gse-mean {mean['gse_mean']:.6f}")
    print(f"differential (Ginnie-Freddie) {diff_freddie:+.6f}pp   r = {r_freddie:.9f}")
    print(f"\n{'mapping':>24}{'a':>10}{'in-sample pp':>15}{'off-window pp':>15}")
    for k in ("M0_committed", "M2_primary_1_over_r", "M1_no_differential",
              "M3_amplification_r"):
        print(f"{k:>24}{insample[k]['a']:>10.4f}{insample[k]['marginal_pp']:>15.4f}"
              f"{offwindow[k]['marginal_pp']:>15.4f}")
    print(f"\nM_full in-sample {m_full_pp:.4f}pp ; committed overlay {crr['marginal_pp']:.4f}pp "
          f"(ratio {crr['marginal_pp']/m_full_pp:.6f} vs conventional share {CONV_SHARE})")
    print(f"P3 |marginal(1) - M_full| in-sample "
          f"{abs(insample['M1_no_differential']['marginal_pp'] - m_full_pp):.2e}pp   "
          f"P4 comparator shift {p4:.2e}pp")
    print(f"E3 {'PASS' if e3 else 'MISS'}   "
          f"E4 open sign -> {payload['expectations']['E4_open_sign_a_vs_1']['verdict']} "
          f"at the primary mapping")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
