#!/usr/bin/env python3
"""R32 / C-128: pricing the realized-side window-boundary allocation.

Run tag: realized_boundary_allocation.  Spec:
specs/SPEC_R32_c128_realized_boundary_allocation.md, committed before this script was written, and
this script committed before it ran.

settlement_months_benchmark convolved the CAP with the committed settlement-lag kernel and left the
realized series untouched, losing $42.0bn at the window's END only -- the pre-QT cap is ZERO, so the
window's start loses nothing.  The realized series is NOT zero before the window, so it can settle
INTO the window.  That asymmetry is what C-128 names and what this run prices.

Same machinery, opposite leg.  No engine.  Writes ONLY
data/realized_boundary_allocation_results.json.

Run:  cd hazard && python3 realized_boundary_allocation.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HAZ = Path(__file__).resolve().parent
ROOT = HAZ.parent
for p in (str(HAZ), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly   # noqa: E402
from common.qt_window import compute_qt_target_series, qt_active_mask           # noqa: E402

DATA = HAZ / "data"
OUT = DATA / "realized_boundary_allocation_results.json"
SMB = DATA / "settlement_months_benchmark_results.json"          # FROZEN, read only

ROLLOFF = "Actual_Monthly_Rolloff_Billions"
QT_START = pd.Timestamp("2022-06-01")
E4_MAX_SHARE = 0.10        # spec section 4: stays a T2 disclosed sensitivity
# spec section 5, P4. A length-3 kernel actually REACHES BACK len(k)-1 = 2
# months; 3 is a conservative floor, not the reach. The distinction matters:
# 17 pre-window months exist, but only 2 can ever contribute, and an earlier
# draft of the manuscript quoted the 17 as though all of them settled in.
MIN_PRE_MONTHS = 3


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def convolve(s: pd.Series, kernel, zero_before=None) -> pd.Series:
    """x_settle[t] = sum_l k[l] * x[t-l].

    zero_before=None keeps the series' OWN pre-window values, which is the whole point on the
    realized leg. The cap leg passes zero_before=QT_START only to document that the committed
    run's fill_value=0.0 and the cap's genuine pre-QT zero are the same thing here.
    """
    base = s.fillna(0.0)
    if zero_before is not None:
        base = base.where(base.index >= zero_before, 0.0)
    out = pd.Series(0.0, index=s.index)
    for lag, w in enumerate(kernel):
        out = out + w * base.shift(lag, fill_value=0.0)
    return out


def trapped(realized: pd.Series, cap: pd.Series, mask: pd.Series) -> float:
    """settlement_months_benchmark.trapped_total, with the realized leg made a parameter."""
    delta = (realized - cap).where(mask)
    return float(delta.fillna(0.0).where(mask, 0.0).sum())


def boundary_masses(realized: pd.Series, kernel, mask: pd.Series):
    """(mass_in, mass_out) for the realized leg, each computed DIRECTLY.

    REPAIRED 2026-07-30.  The first version weighted the month at distance d
    before the window start by k[d] and then defined mass_out as the residual
    r_tot_cal + mass_in - r_tot_set.  Both were wrong, and the second error
    concealed the first.

    Under x_settle[t] = sum_l k[l] * x[t-l], a source month s reaches window
    month t = s + l.  So a month d places BEFORE the window start enters with
    the kernel's TAIL weight sum(k[d:]) -- it settles into every window month
    from s+d onward -- not with the single tap k[d].  With k = [0.1, 0.6, 0.3]
    the last pre-window month enters at 0.6 + 0.3 = 0.9, not 0.6.

    Symmetrically, the month i places before the window END loses sum(k[i+1:])
    past the end: the final window month loses 0.9, the one before it 0.3.

    Because mass_out was a residual, mass_in - mass_out collapsed to
    r_tot_set - r_tot_cal for ANY mass_in, which made the run's own P5 and the
    liveness gate that re-derived it vacuous with respect to mass_in.  Both
    masses are now independent, so P5 below is a real constraint that can fail.
    """
    idx = realized.index
    pre = idx[idx < QT_START]
    # qt_active_mask returns a bare ndarray aligned to df.index, not a Series
    win = idx[np.asarray(getattr(mask, "to_numpy", lambda: mask)(), dtype=bool)]
    reach = len(kernel) - 1          # how far back the kernel can actually see
    mass_in = sum(float(realized.get(pre[-d], 0.0)) * sum(kernel[d:])
                  for d in range(1, reach + 1) if d <= len(pre))
    mass_out = sum(float(realized.get(win[-1 - i], 0.0)) * sum(kernel[i + 1:])
                   for i in range(reach) if i < len(win))
    return mass_in, mass_out


def main() -> None:
    t0 = time.perf_counter()
    smb = json.loads(SMB.read_text())
    if not smb.get("gates_all_pass"):
        stop("P1", "the committed settlement_months_benchmark artifact is not all-pass")
    committed = smb["committed_benchmark_b"]
    cap_only_committed = smb["legs"]["production"]["benchmark_b"]
    kernel = list(smb["kernel_production"])

    # ---- P3: the kernel and the active-month count, live -------------------
    if kernel != [0.1, 0.6, 0.3] or abs(sum(kernel) - 1.0) > 1e-12:
        stop("P3", f"kernel drifted: {kernel}")

    df = build_empirical_metrics(fetch_data(), soma_rolloff=fetch_soma_mbs_monthly())
    cap_cal = compute_qt_target_series(df.index)
    mask = qt_active_mask(df.index)
    if int(mask.sum()) != smb["n_qt_active_months"]:
        stop("P3", f"active months {int(mask.sum())} != {smb['n_qt_active_months']}")

    realized_cal = df[ROLLOFF]

    # ---- P4: the pre-window months a 3-tap kernel needs must EXIST ---------
    pre = realized_cal.index[realized_cal.index < QT_START]
    if len(pre) < MIN_PRE_MONTHS:
        stop("P4", f"only {len(pre)} pre-window months; convolving against zeros would "
                   f"FABRICATE the asymmetry this run measures")

    # ---- P1/E1: both committed legs reproduce ------------------------------
    bench_cal = trapped(realized_cal, cap_cal, mask)
    if abs(bench_cal - committed) > 1e-9:
        stop("E1", f"calendar benchmark {bench_cal!r} != committed {committed!r} "
                   f"(drift {bench_cal - committed:+.3e}); tolerance is NOT widened")
    cap_settle = convolve(cap_cal, kernel, zero_before=QT_START)
    bench_cap_only = trapped(realized_cal, cap_settle, mask)
    if abs(bench_cap_only - cap_only_committed) > 1e-9:
        stop("E1", f"cap_only {bench_cap_only!r} != committed {cap_only_committed!r}")

    # ---- E2: the cap-side edge loss re-derives -----------------------------
    cap_tot_cal = float(cap_cal.where(mask).fillna(0.0).sum())
    cap_tot_settle = float(cap_settle.where(mask).fillna(0.0).sum())
    edge_loss = abs(cap_tot_settle - cap_tot_cal)
    want_edge = 0.30 * 35.0 + 0.90 * 35.0
    if abs(edge_loss - want_edge) > 1e-6:
        stop("E2", f"cap edge loss {edge_loss} != {want_edge} (0.30x35 + 0.90x35)")

    # ---- the new object: BOTH legs aligned ---------------------------------
    legs = {}
    for name, k in (("production", kernel),
                    ("slower", smb["legs"]["slower"]["kernel"]),
                    ("faster", smb["legs"]["faster"]["kernel"])):
        r_set = convolve(realized_cal, k)                       # keeps pre-window mass
        c_set = convolve(cap_cal, k, zero_before=QT_START)
        both = trapped(r_set, c_set, mask)
        cap_leg = trapped(realized_cal, c_set, mask)
        r_tot_cal = float(realized_cal.where(mask).fillna(0.0).sum())
        r_tot_set = float(r_set.where(mask).fillna(0.0).sum())
        # boundary decomposition of the realized leg -- both sides computed
        # directly from the kernel's tail weights, neither as the other's
        # residual, so the P5 identity below is a real check
        mass_in, mass_out = boundary_masses(realized_cal, k, mask)
        legs[name] = {
            "kernel": list(k),
            "benchmark_both_aligned_b": both,
            "benchmark_cap_only_b": cap_leg,
            "shift_both_b": both - committed,
            "shift_cap_only_b": cap_leg - committed,
            "shift_both_pct_of_committed": (both - committed) / committed * 100.0,
            "realized_total_calendar_b": r_tot_cal,
            "realized_total_settled_b": r_tot_set,
            "realized_boundary_mass_in_b": mass_in,
            "realized_boundary_mass_out_b": mass_out,
            "cap_total_calendar_b": cap_tot_cal,
            "cap_edge_loss_b": abs(
                float(convolve(cap_cal, k, zero_before=QT_START)
                      .where(mask).fillna(0.0).sum()) - cap_tot_cal),
        }

    p = legs["production"]
    # ---- P5: the boundary decomposition must sum, for EVERY kernel ----------
    # Now that mass_out is computed rather than back-solved, this identity has
    # content: it fails if either tail weighting is wrong.
    for name, L in legs.items():
        recon = (L["realized_total_calendar_b"] + L["realized_boundary_mass_in_b"]
                 - L["realized_boundary_mass_out_b"])
        if abs(recon - L["realized_total_settled_b"]) > 1e-6:
            stop("P5", f"{name}: boundary decomposition does not sum: {recon} vs "
                       f"{L['realized_total_settled_b']}")

    e3 = abs(p["shift_both_b"]) < abs(p["shift_cap_only_b"])
    e4 = abs(p["shift_both_b"]) / committed < E4_MAX_SHARE

    payload = {
        "mode": "realized_boundary_allocation", "run_tag": "realized_boundary_allocation",
        "status": "OK", "pre_committed": True,
        "spec": {
            "spec_file": "specs/SPEC_R32_c128_realized_boundary_allocation.md",
            "construction": ("same machinery, opposite leg: the committed settlement-lag kernel "
                             "applied to the REALIZED series as well as the cap, with the "
                             "realized leg keeping its own pre-window values"),
            "why_the_legs_differ": ("the pre-QT cap is zero, so the cap leg loses mass only at "
                                    "the window's end; the realized series is non-zero before "
                                    "the window, so it also GAINS mass at the start"),
            "production_convention_stays_calendar": True,
            "month_alignment_only": ("revisits neither the cap schedule, the SOMA series' "
                                     "construction (that is C-127), the window bounds, nor the "
                                     "reinvestment-ceiling reading of the cap"),
            "kernel_imported_not_estimated": True,
            "no_engine_runs": True,
        },
        "parity": {
            "P1_calendar_reproduces": bench_cal,
            "P1_cap_only_reproduces": bench_cap_only,
            "P2_committed_calendar": committed,
            "P2_committed_cap_only": cap_only_committed,
            "P3_kernel": kernel, "P3_n_qt_active_months": int(mask.sum()),
            "P4_pre_window_months": int(len(pre)),
            "P5_boundary_decomposition_sums": True,
            "E2_cap_edge_loss_b": edge_loss,
        },
        "legs": legs,
        "expectations": {
            "E3_both_moves_less_than_cap_only": bool(e3),
            "E3_shift_both_b": p["shift_both_b"],
            "E3_shift_cap_only_b": p["shift_cap_only_b"],
            "E3_sign_deliberately_not_predicted": True,
            "E4_max_share": E4_MAX_SHARE,
            "E4_shift_share_of_committed": abs(p["shift_both_b"]) / committed,
            "E4_pass": bool(e4),
        },
        "runtime_s": round(time.perf_counter() - t0, 3),
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

    print(f"\nP1 calendar {bench_cal:.10f} == committed  |  cap_only "
          f"{bench_cap_only:.10f} == committed")
    print(f"P4 pre-window months: {len(pre)}   E2 cap edge loss ${edge_loss:.3f}bn")
    print(f"\n{'kernel':>18}{'both-aligned':>15}{'shift':>11}{'cap-only shift':>16}"
          f"{'mass in':>10}{'mass out':>10}")
    for n, L in legs.items():
        print(f"{n:>18}{L['benchmark_both_aligned_b']:>15.4f}{L['shift_both_b']:>11.4f}"
              f"{L['shift_cap_only_b']:>16.4f}{L['realized_boundary_mass_in_b']:>10.3f}"
              f"{L['realized_boundary_mass_out_b']:>10.3f}")
    print(f"\nE3 {'PASS' if e3 else 'MISS'} (|{p['shift_both_b']:.3f}| vs "
          f"|{p['shift_cap_only_b']:.3f}|)   "
          f"E4 {'PASS' if e4 else 'MISS'} ({abs(p['shift_both_b'])/committed*100:.3f}% of benchmark)")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
