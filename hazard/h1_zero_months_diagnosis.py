#!/usr/bin/env python3
"""h1_zero_months_diagnosis.py — mechanism trace for the four exact-zero months
in the SOMA back-out (round-28 WP-H1; spec specs/SPEC_round28_H1_zero_months.md,
committed before this run). Read-only on the repo; one frozen artifact out.

Construction mirrors macro.fetch_soma_mbs_monthly (macro.py:150-177) and the
CPR back-out arithmetic of macro.build_empirical_metrics (macro.py:240-247)
without importing the engine. Landing per the spec's pre-committed rule.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

import macro as mz

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "h1_zero_months_diagnosis.json"
ZERO_MONTHS = ["2022-06", "2023-02", "2024-04", "2025-09"]
SPIKE_FOLLOWED = ["2023-02", "2024-04", "2025-09"]
TOL_ZERO_B = 0.005
WANT_SPIKE_PCT = 14.01


def main() -> None:
    t0 = time.perf_counter()
    req = urllib.request.Request(mz.SOMA_SUMMARY_URL,
                                 headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())["soma"]["summary"]
    rec = [{"date": pd.Timestamp(r["asOfDate"]), "mbs_b": float(r["mbs"]) / 1e9}
           for r in payload if r.get("mbs") and r["mbs"] != "0.00"]
    weekly = (pd.DataFrame(rec).set_index("date").sort_index()
              .loc[mz.START_DATE:])["mbs_b"]
    monthly = weekly.resample("ME").last()
    diff = monthly.diff()

    p1_rows, p1_ok = {}, True
    for zm in ZERO_MONTHS:
        d = float(diff.loc[zm].iloc[0])
        ok = abs(d) < TOL_ZERO_B
        p1_ok &= ok
        p1_rows[zm] = {"me_last_diff_b": d, "abs_lt_tol": ok}
    print(f"P1 zeros reproduce: {p1_rows} [{'PASS' if p1_ok else 'FAIL'}]")

    # P2 — the 14.01% spike, back-out arithmetic replicated on the spot
    sched = mz.scheduled_amortization_series(
        monthly.index, coupon=0.025, origin=pd.Timestamp("2020-06-01"))
    holdings = monthly  # this probe's holdings ARE the SOMA series
    emp_cpr = (((diff.abs() / holdings) - sched).clip(lower=0) * 12 * 100)
    spikes = {}
    for zm in SPIKE_FOLLOWED:
        nxt = (pd.Period(zm, "M") + 1).strftime("%Y-%m")
        spikes[f"{zm}->{nxt}"] = float(emp_cpr.loc[nxt].iloc[0])
    max_spike = max(spikes.values())
    # NOTE: production divides by WSHOMCB holdings, not the SOMA level; the
    # 14.01 target is only reproducible to the extent the two balance series
    # agree (~1-2% level difference). Gate at +-0.75 on that ground, with the
    # exact production replication left to the committed exhibits.
    p2_ok = abs(max_spike - WANT_SPIKE_PCT) < 0.75
    print(f"P2 post-zero spikes {spikes} max {max_spike:.2f} vs "
          f"{WANT_SPIKE_PCT} [{'PASS' if p2_ok else 'FAIL'}]")

    months = {}
    n_artifact = 0
    trail = diff.abs().rolling(6).mean()
    for zm in ZERO_MONTHS:
        per = pd.Period(zm, "M")
        prev_last = weekly.loc[:str(per - 1)].index.max()
        this_last = weekly.loc[:zm].index.max()
        span = weekly.loc[prev_last:this_last]
        steps = span.diff().dropna()
        max_step = float(steps.abs().max()) if len(steps) else 0.0
        me_diff = float(diff.loc[zm].iloc[0])
        nxt = (per + 1).strftime("%Y-%m")
        nxt_diff = float(diff.loc[nxt].iloc[0]) if nxt in diff.index.strftime("%Y-%m") else np.nan
        tmean = float(trail.loc[zm].iloc[0])
        if max_step < TOL_ZERO_B:
            cls = "F"
        elif abs(me_diff) < TOL_ZERO_B:
            cls = "A"
        else:
            spike = abs(nxt_diff) >= 1.5 * tmean if np.isfinite(nxt_diff) else False
            cls = "G" if not spike else "A"
        if cls in ("F", "A"):
            n_artifact += 1
        months[zm] = {
            "span_first_asof": str(prev_last.date()),
            "span_last_asof": str(this_last.date()),
            "weekly_obs_b": {str(k.date()): float(v) for k, v in span.items()},
            "n_weekly_steps": int(len(steps)),
            "max_abs_step_b": max_step,
            "me_last_diff_b": me_diff,
            "next_month_diff_b": nxt_diff,
            "pair_total_b": me_diff + (nxt_diff if np.isfinite(nxt_diff) else 0.0),
            "trailing6_mean_abs_diff_b": tmean,
            "classification": cls,
        }
        print(f"  {zm}: {len(steps)} steps, max|step| ${max_step:.3f}B, "
              f"next-month ${nxt_diff:+.1f}B, trail ${tmean:.1f}B -> {cls}")

    spike_zeros_artifact = all(months[z]["classification"] in ("F", "A")
                               for z in SPIKE_FOLLOWED)
    outcome = ("ARTIFACT" if (n_artifact >= 3 and spike_zeros_artifact)
               else "MIXED_GENUINE")
    all_pass = bool(p1_ok and p2_ok)
    status = "OK" if all_pass else "GATE_FAILURE"
    payload = {
        "mode": "h1_zero_months_diagnosis", "status": status,
        "spec": "specs/SPEC_round28_H1_zero_months.md (committed pre-run)",
        "parity_gates": {
            "P1_zeros_reproduce": {"rows": p1_rows, "tol_b": TOL_ZERO_B,
                                   "pass": bool(p1_ok)},
            "P2_spike_consistent": {"spikes_pct": spikes,
                                    "max_pct": max_spike,
                                    "want_pct": WANT_SPIKE_PCT, "tol": 0.75,
                                    "holdings_note": "SOMA-level holdings, "
                                    "not production WSHOMCB; tol widened on "
                                    "that ground in-spec",
                                    "pass": bool(p2_ok)},
        },
        "parity_gates_all_pass": all_pass,
        "zero_months": months,
        "classification_summary": {
            "n_artifact": n_artifact, "n_total": len(ZERO_MONTHS),
            "spike_followed_all_artifact": bool(spike_zeros_artifact),
        },
        "verdict": {
            "outcome": outcome,
            "manuscript_action": (
                "Outcome ARTIFACT: wording-class only — appendix mechanism "
                "clause + promote the cannot-adjudicate-timing concession to "
                "the III.B / VI.B descriptor sites; NO re-score; no committed "
                "number moves." if outcome == "ARTIFACT" else
                "Outcome MIXED_GENUINE: weaken the artifact framing for the "
                "G months; concession stands on the five diagnostics alone; "
                "same promotion; NO re-score."),
        },
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=lambda o: o.item())
        f.write("\n")
    print(f"\nstatus {status}; outcome {outcome}; frozen -> {RESULTS_JSON}")
    if not all_pass:
        raise SystemExit("GATE_FAILURE — nothing lands.")


if __name__ == "__main__":
    main()
