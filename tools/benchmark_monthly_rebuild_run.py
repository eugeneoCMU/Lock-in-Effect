#!/usr/bin/env python3
"""R32 / C-127: rebuilding the benchmark's monthly series at monthly frequency.

Run tag: benchmark_monthly_rebuild.  Spec: specs/SPEC_R32_c127_benchmark_monthly_rebuild.md,
committed before this script was written, and this script committed before it ran.

R2 asked for the benchmark's monthly roll-off to be rebuilt from published monthly SOMA
principal-payment data, or from CUSIP factor changes, on the grounds that differencing weekly
Wednesday levels manufactures four clip-zero months.  Scoping established that no monthly
principal-payment endpoint exists (HTTP 400) and that the per-CUSIP file carries the IDENTICAL
staleness at the 2023-02 clip.  This run tests the other three clip months, reconstructs the
window total from per-CUSIP paydowns, and checks whether the reconstruction retires the zeros.

Writes ONLY hazard/data/benchmark_monthly_rebuild_results.json.
No engine.  Network reads and arithmetic only.  Touches no .tex file.

Usage:  python3 tools/benchmark_monthly_rebuild_run.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAZ = ROOT / "hazard"
OUT = HAZ / "data" / "benchmark_monthly_rebuild_results.json"
ZERO_DIAG = HAZ / "data" / "h1_zero_months_diagnosis.json"          # FROZEN, read only
SMB = HAZ / "data" / "settlement_months_benchmark_results.json"     # FROZEN, read only

API = "https://markets.newyorkfed.org/api/soma"
CACHE = Path(os.environ.get("C127_CACHE", "/tmp/c127_soma_cache"))
WINDOW = ("2022-05-01", "2025-12-31")     # one month of lead-in for the first diff
E4_TOL_FRAC = 0.01                        # spec section 4: 1% of the committed benchmark


def stop(gate: str, msg: str) -> None:
    print(f"STOP [{gate}] {msg}", file=sys.stderr)
    raise SystemExit(2)


def get(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def holdings(asof: str) -> dict[str, float] | None:
    """Per-CUSIP current face at one as-of date, cached outside the repo."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{asof}.json"
    if f.exists():
        return json.loads(f.read_text())
    try:
        rows = get(f"{API}/mbs/get/asof/{asof}.json")["soma"]["holdings"]
    except Exception as exc:                      # non-fatal, recorded (P4)
        print(f"  {asof}: FETCH FAILED {type(exc).__name__}", file=sys.stderr)
        return None
    agg: dict[str, float] = defaultdict(float)
    for r in rows:
        agg[r["cusip"]] += float(r["currentFaceValue"])
    d = {k: v for k, v in agg.items()}
    f.write_text(json.dumps(d))
    return d


def main() -> None:
    t0 = time.time()

    # ---- P1: committed anchors, live ---------------------------------------
    zd = json.loads(ZERO_DIAG.read_text())
    smb = json.loads(SMB.read_text())
    committed_bench = smb["committed_benchmark_b"]
    clip_months = sorted(zd["zero_months"])
    if len(clip_months) != 4:
        stop("P1", f"expected 4 clip months, artifact has {clip_months}")

    # ---- P3: the cap arithmetic, re-derived not asserted -------------------
    cap_total = 3 * 17.5 + 39 * 35.0
    if abs(cap_total - smb["cap_total_calendar_b"]) > 1e-9:
        stop("P3", f"cap arithmetic {cap_total} != {smb['cap_total_calendar_b']}")
    realized_implied = cap_total - committed_bench

    # ---- (2) sourceability, re-probed live so the record is this run's -----
    src = {"summary_fields": None, "monthly_endpoints": {}}
    try:
        rows = get(f"{API}/summary.json")["soma"]["summary"]
        src["summary_fields"] = sorted(rows[0].keys())
        src["summary_has_paydown_field"] = any(
            k.lower().startswith(("paydown", "principal", "factor"))
            for k in src["summary_fields"])
    except Exception as exc:
        stop("P4", f"summary endpoint unreachable: {exc}")
    for ep in ("mbs/get/monthly.json", "agency/get/monthly.json"):
        try:
            get(f"{API}/{ep}", timeout=25)
            src["monthly_endpoints"][ep] = "200"
        except urllib.error.HTTPError as e:
            src["monthly_endpoints"][ep] = str(e.code)
        except Exception as e:
            src["monthly_endpoints"][ep] = type(e).__name__
    src["monthly_principal_payment_series_available"] = (
        src["summary_has_paydown_field"]
        or any(v == "200" for v in src["monthly_endpoints"].values()))

    # ---- as-of dates in range ----------------------------------------------
    dates = [d for d in get(f"{API}/asofdates/list.json")["soma"]["asOfDates"]
             if WINDOW[0] <= d <= WINDOW[1]]
    if len(dates) < 100:
        stop("P4", f"only {len(dates)} as-of dates in range; expected ~180")
    print(f"as-of dates in range: {len(dates)}  ({dates[0]} .. {dates[-1]})")

    # ---- fetch + four-way decomposition ------------------------------------
    weeks, prev, prev_d, failed = [], None, None, []
    for i, d in enumerate(dates, 1):
        h = holdings(d)
        if h is None:
            failed.append(d)
            continue
        tot = sum(h.values()) / 1e9
        row = {"asof": d, "n_cusips": len(h), "total_b": tot}
        if prev is not None:
            pay = add = rem = inc = 0.0
            for c, v in h.items():
                p = prev.get(c)
                if p is None:
                    add += v
                elif v < p:
                    pay += p - v
                elif v > p:
                    inc += v - p
            for c, p in prev.items():
                if c not in h:
                    rem += p
            row.update(paydown_b=pay / 1e9, added_b=add / 1e9,
                       removed_b=rem / 1e9, increased_b=inc / 1e9,
                       delta_b=tot - weeks[-1]["total_b"],
                       stale=bool(len(h) == weeks[-1]["n_cusips"]
                                  and abs(tot - weeks[-1]["total_b"]) < 1e-9))
            # E2: the decomposition must be exhaustive
            recon = (-pay + add - rem + inc) / 1e9
            if abs(recon - row["delta_b"]) > 1e-6:
                stop("E2", f"{d}: decomposition {recon} != delta {row['delta_b']}")
        weeks.append(row)
        prev, prev_d = h, d
        if i % 20 == 0:
            print(f"  {i}/{len(dates)} ...")

    if failed:
        print(f"P4: {len(failed)} fetches failed: {failed[:5]}", file=sys.stderr)
    if len(weeks) < 100:
        stop("P4", f"only {len(weeks)} weeks retrieved; cannot reconstruct")

    # ---- monthly paydown reconstruction + the committed method -------------
    by_month: dict[str, float] = defaultdict(float)
    stale_by_month: dict[str, list] = defaultdict(list)
    for w in weeks[1:]:
        m = w["asof"][:7]
        by_month[m] += w["paydown_b"]
        if w["stale"]:
            stale_by_month[m].append(w["asof"])
    # committed method: month-end level, differenced
    me = {}
    for w in weeks:
        me[w["asof"][:7]] = w["total_b"]
    months = sorted(me)
    committed_method = {months[i]: me[months[i]] - me[months[i - 1]]
                        for i in range(1, len(months))}

    win = [m for m in sorted(by_month) if "2022-06" <= m <= "2025-11"]
    recon_total = sum(by_month[m] for m in win)

    e3_cells = {m: sorted(stale_by_month.get(m, [])) for m in clip_months}
    e3 = all(e3_cells[m] for m in clip_months)
    e4_diff = abs(recon_total - realized_implied)
    e4 = e4_diff / committed_bench < E4_TOL_FRAC
    # E5: does the reconstruction retire the zeros?
    still_low = {m: by_month.get(m, 0.0) for m in clip_months}
    med = sorted(by_month[m] for m in win)[len(win) // 2]
    e5 = all(still_low[m] < 0.5 * med for m in clip_months)

    payload = {
        "mode": "benchmark_monthly_rebuild", "run_tag": "benchmark_monthly_rebuild",
        "status": "OK",
        "spec": {
            "spec_file": "specs/SPEC_R32_c127_benchmark_monthly_rebuild.md",
            "condition": ("R2:M8, NOT ARBITRATED. This run settles the SOURCEABILITY leg; it does "
                          "not adjudicate the referee exchange."),
            "cap_side_untouched": True, "no_engine_runs": True,
            "window_months": len(win),
        },
        "sourceability": src,
        "parity": {
            "P1_committed_benchmark_b": committed_bench,
            "P1_clip_months": clip_months,
            "P3_cap_total_rederived_b": cap_total,
            "P3_realized_implied_b": realized_implied,
            "P4_asof_dates": len(dates), "P4_weeks_retrieved": len(weeks),
            "P4_fetch_failures": failed,
            "E2_decomposition_exhaustive": True,
        },
        "weeks": weeks,
        "monthly_paydown_b": {m: by_month[m] for m in sorted(by_month)},
        "committed_method_monthly_diff_b": committed_method,
        "stale_weeks_by_month": {m: v for m, v in sorted(stale_by_month.items())},
        "expectations": {
            "E3_all_clip_months_have_a_stale_week": bool(e3),
            "E3_stale_weeks_in_clip_months": e3_cells,
            "E4_tol_frac": E4_TOL_FRAC,
            "E4_reconstructed_window_total_b": recon_total,
            "E4_implied_realized_total_b": realized_implied,
            "E4_abs_diff_b": e4_diff, "E4_pass": bool(e4),
            "E5_reconstruction_still_shows_low_months": bool(e5),
            "E5_clip_month_paydowns_b": still_low,
            "E5_window_median_paydown_b": med,
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

    print(f"\nsourceability: monthly principal-payment series available = "
          f"{src['monthly_principal_payment_series_available']}  "
          f"(endpoints {src['monthly_endpoints']})")
    print(f"stale weeks in the four clip months:")
    for m in clip_months:
        print(f"  {m}: {e3_cells[m] or 'NONE'}   paydown ${still_low[m]:.4f}bn "
              f"(window median ${med:.4f}bn)")
    print(f"\nE4 reconstructed window total ${recon_total:.4f}bn vs implied realized "
          f"${realized_implied:.4f}bn  (diff ${e4_diff:.4f}bn, "
          f"{e4_diff/committed_bench*100:.3f}% of benchmark)")
    print(f"E3 {'PASS' if e3 else 'MISS'}   E4 {'PASS' if e4 else 'MISS'}   "
          f"E5 {'PASS' if e5 else 'MISS'}")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
