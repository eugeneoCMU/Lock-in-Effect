#!/usr/bin/env python3
"""
fannie_floor_read.py — an INDEPENDENT-AGENCY read of the involuntary-turnover
floor, the parameter the manuscript itself calls binding.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run, per the convention of
out_of_window_floor.py / floor_form_offwindow.py / bootstrap_pathb_cluster.py).

=======================================================================
WHY
=======================================================================
The floor is the design's dominant level-setter, and floor_uncertainty records
that its SAMPLING error is the binding uncertainty on the headline marginal
(95% CI [+2.974, +8.019]pp, wider than the +4.3..+6.8 depth-cut band the
manuscript quotes). That parameter is read off ONE agency's book: Freddie Mac
2017--2019 out-of-the-money cohort-months, 31 clusters at the headline read,
with the mature-age leg unavailable (the oldest populated 2018 bucket is
[12,24) months) and an age-standardised read of 5.51% that sits ABOVE the clean
band's top on 84% imputed weight.

Meanwhile the project already stages a second agency in the identical layout:
hazard/data/cohort_month_panel_fannie.parquet, same fourteen columns, same
2017-01 start. The Fannie replication (fannie_replication) uses it to reproduce
the MARGINAL while holding the floor FIXED at the Freddie-derived value. Nothing
in the manuscript re-reads the floor there.

So the paper's most consequential parameter has never been given an
out-of-agency read, on data already on disk. That is the gap this run closes.
It is not a robustness flourish: if the Fannie floor lands outside the clean
band, the headline marginal's range is understated and the manuscript has to say
so.

=======================================================================
SPEC
=======================================================================
- Selection rule: IDENTICAL to out_of_window_floor.py, reused rather than
  re-implemented. coupon > 0 and exposure_upb > 0; market rate from FRED
  MORTGAGE30US resampled to month-end means; gap = coupon - market_rate;
  exposure-weighted annual CPR from summed prepaid_upb over summed exposure_upb
  via cpr = 1 - (1 - smm)**12.
- Windows: out-of-window 201701--201912, in-window validation 202301--202412.
- Grid: gap thresholds {0.0, -0.0025, -0.005} x minimum mean loan age {12, 24}.
- Deep-OTM in-window validation at gap <= -0.02, both age minima.
- Run on BOTH panels in the same process on the same fetched rate series, so
  any difference is the book and not the frame.

PARITY (G1, must hold before any Fannie number is reported): the FREDDIE panel
through this exact code path must reproduce every cell of the committed
out_of_window_floor_results.json grid to 0.001 percentage points, and every
cohort-month count exactly. If it does not, this script is not the committed
read and its Fannie numbers mean nothing; it halts and writes nothing.

=======================================================================
EX-ANTE VERDICT (fixed before the run)
=======================================================================
Reference: the manuscript's clean off-window band is [4.695, 5.334]% and the
production floor is 4.0%. The comparison cell is the headline one --
gap <= -0.0025, age >= 12, out-of-window -- which is 5.185% on Freddie.

  T1 CONFIRMS: the Fannie headline cell lands inside [4.695, 5.334].
     -> the floor's provenance survives an out-of-agency read; report it as
        corroboration and quote it wherever the floor's single-agency basis is
        currently conceded.
  T2 WIDENS: it lands outside that band but inside [4.0, 6.07] (the production
     floor to the disqualified refi-contaminated pooled anchor).
     -> the clean band understates the floor's uncertainty. The band, and
        therefore the +4.3..+6.8 marginal range, must be widened to span both
        agencies, and the abstract's range re-checked.
  T3 BREAKS: it lands outside [4.0, 6.07] entirely.
     -> the floor is agency-specific, the single-agency read cannot carry the
        headline, and the marginal's range is not identified by the current
        design. This would be the most consequential single result in the
        paper's revision history and must be reported as such.
  T4 DEGENERATE: the Fannie headline cell has fewer than 30 cohort-months or
     zero exposure -> the read is uninformative; report the count and stop.
     (Freddie's headline cell has 438 cohort-months, so a Fannie cell an order
     of magnitude smaller would be a staging artifact, not a finding.)

Reported in every branch, obliging only itself:
  R1 the age >= 24 cell on Fannie. Freddie cannot support a mature read at the
     off-window anchor; if Fannie can, that is new information about the
     seasoning limitation the manuscript concedes.
  R2 the in-window 2023--24 cells on both books, which is where the PRODUCTION
     4.0% floor came from. Agreement there and disagreement off-window would
     localise the discrepancy to the off-window leg specifically.
  R3 the two books' exposure and cohort-month counts side by side, so a reader
     can see which read is better supported rather than taking either on trust.

Run:  cd hazard && python3 fannie_floor_read.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FREDDIE_PANEL = DATA / "cohort_month_panel.parquet"
FANNIE_PANEL = DATA / "cohort_month_panel_fannie.parquet"
COMMITTED = DATA / "out_of_window_floor_results.json"
RESULTS_JSON = DATA / "fannie_floor_read_results.json"

GAP_THRESHOLDS = (0.0, -0.0025, -0.005)
AGE_MINIMA = (12, 24)
HEADLINE_CELL = "gap<=-0.0025_age>=12"
CLEAN_BAND = (4.695, 5.334)
PRODUCTION_FLOOR_PCT = 4.0
CONTAMINATED_POOLED_PCT = 6.07
TOL_CPR_PP = 0.001
MIN_COHORT_MONTHS = 30


def cpr_of(sel: pd.DataFrame) -> tuple[float, float, int]:
    """Exposure-weighted annual CPR, total exposure, n cohort-months.

    Byte-for-byte the committed definition in out_of_window_floor.py:63.
    """
    exp = sel["exposure_upb"].sum()
    if exp <= 0:
        return float("nan"), 0.0, 0
    smm = sel["prepaid_upb"].sum() / exp
    cpr = 1.0 - (1.0 - smm) ** 12
    return float(cpr), float(exp), int(len(sel))


def prep(panel: Path, rate_by_ym: dict) -> pd.DataFrame:
    df = pd.read_parquet(panel)
    df = df[(df["coupon"] > 0) & (df["exposure_upb"] > 0)].copy()
    df["rp"] = df["reporting_period"].astype(int)
    df["ym"] = df["reporting_period"].astype(str)
    df["market_rate"] = df["ym"].map(rate_by_ym)
    df = df[df["market_rate"].notna()].copy()
    df["gap"] = df["coupon"] - df["market_rate"]
    return df


def grid_for(df: pd.DataFrame, lo: int, hi: int) -> dict:
    w = df[(df["rp"] >= lo) & (df["rp"] <= hi)]
    out = {}
    for gthr in GAP_THRESHOLDS:
        for amin in AGE_MINIMA:
            sel = w[(w["gap"] <= gthr) & (w["mean_loan_age"] >= amin)]
            cpr, exp, n = cpr_of(sel)
            out[f"gap<={gthr:+.4f}_age>={amin}"] = {
                "cpr_pct": (round(100 * cpr, 3) if cpr == cpr else None),
                "exposure_upb": exp, "n_cohort_months": n}
    return out


def deep_otm(df: pd.DataFrame) -> dict:
    w = df[(df["rp"] >= 202301) & (df["rp"] <= 202412)]
    out = {}
    for amin in AGE_MINIMA:
        sel = w[(w["gap"] <= -0.02) & (w["mean_loan_age"] >= amin)]
        cpr, exp, n = cpr_of(sel)
        out[f"gap<=-0.02_age>={amin}"] = {
            "cpr_pct": (round(100 * cpr, 3) if cpr == cpr else None),
            "exposure_upb": exp, "n_cohort_months": n}
    return out


def classify(cpr_pct, n_cohort_months) -> str:
    if cpr_pct is None or n_cohort_months < MIN_COHORT_MONTHS:
        return "T4"
    if CLEAN_BAND[0] <= cpr_pct <= CLEAN_BAND[1]:
        return "T1"
    if PRODUCTION_FLOOR_PCT <= cpr_pct <= CONTAMINATED_POOLED_PCT:
        return "T2"
    return "T3"


def main() -> int:
    t0 = time.perf_counter()
    sys.path.insert(0, str(HERE))
    import config
    from fredapi import Fred

    print("Fetching MORTGAGE30US (same source and resampling as the "
          "committed read) ...")
    fred = Fred(api_key=config.FRED_API_KEY)
    rate = fred.get_series("MORTGAGE30US", observation_start="2016-12-01",
                           observation_end="2025-10-31").resample("ME").mean()
    rate_by_ym = {ix.strftime("%Y%m"): float(v) / 100.0
                  for ix, v in rate.items()}

    books = {}
    for tag, panel in (("freddie", FREDDIE_PANEL), ("fannie", FANNIE_PANEL)):
        if not panel.exists():
            raise SystemExit(f"panel missing: {panel}")
        df = prep(panel, rate_by_ym)
        books[tag] = {
            "panel": str(panel),
            "rows_after_filter": int(len(df)),
            "out_of_window_2017_2019": grid_for(df, 201701, 201912),
            "in_window_2023_2024": grid_for(df, 202301, 202412),
            "in_window_deep_OTM_validation": deep_otm(df),
        }
        print(f"  {tag}: {len(df):,} filtered cohort-months")

    # ---- G1 parity: the Freddie path must replay the committed grid ----------
    committed = json.loads(COMMITTED.read_text())
    mismatches = []
    for wname, cgrid in committed["grids"].items():
        for cell, cval in cgrid.items():
            got = books["freddie"][wname][cell]
            if cval["cpr_pct"] is None or got["cpr_pct"] is None:
                if cval["cpr_pct"] != got["cpr_pct"]:
                    mismatches.append(f"{wname}/{cell}: None mismatch")
                continue
            d = abs(got["cpr_pct"] - cval["cpr_pct"])
            if d > TOL_CPR_PP:
                mismatches.append(
                    f"{wname}/{cell}: cpr {got['cpr_pct']} vs committed "
                    f"{cval['cpr_pct']} (d={d:.4f}pp)")
            if got["n_cohort_months"] != cval["n_cohort_months"]:
                mismatches.append(
                    f"{wname}/{cell}: n {got['n_cohort_months']} vs committed "
                    f"{cval['n_cohort_months']}")
    g1 = not mismatches
    print(f"\nG1_freddie_parity: {'PASS' if g1 else 'FAIL'} "
          f"({len(mismatches)} mismatches)")
    for m in mismatches[:8]:
        print("   ", m)
    if not g1:
        raise SystemExit(
            "G1 parity FAILED — this code path is not the committed read, so "
            "its Fannie numbers carry no weight. Nothing written."
        )

    fan = books["fannie"]["out_of_window_2017_2019"][HEADLINE_CELL]
    fre = books["freddie"]["out_of_window_2017_2019"][HEADLINE_CELL]
    verdict = classify(fan["cpr_pct"], fan["n_cohort_months"])

    payload = {
        "mode": "fannie_floor_read",
        "spec": (
            "independent-agency read of the involuntary-turnover floor: the "
            "committed out_of_window_floor selection rule applied to the Fannie "
            "cohort-month panel, with the Freddie panel replayed through the "
            "same code path as parity"
        ),
        "headline_cell": HEADLINE_CELL,
        "books": books,
        "comparison": {
            "freddie_headline_cpr_pct": fre["cpr_pct"],
            "fannie_headline_cpr_pct": fan["cpr_pct"],
            "difference_pp": (None if (fan["cpr_pct"] is None
                                       or fre["cpr_pct"] is None)
                              else round(fan["cpr_pct"] - fre["cpr_pct"], 3)),
            "clean_band_pct": list(CLEAN_BAND),
            "fannie_inside_clean_band": (
                fan["cpr_pct"] is not None
                and CLEAN_BAND[0] <= fan["cpr_pct"] <= CLEAN_BAND[1]),
            "freddie_headline_n": fre["n_cohort_months"],
            "fannie_headline_n": fan["n_cohort_months"],
            "R1_fannie_mature_cell":
                books["fannie"]["out_of_window_2017_2019"]["gap<=-0.0025_age>=24"],
            "R1_freddie_mature_cell":
                books["freddie"]["out_of_window_2017_2019"]["gap<=-0.0025_age>=24"],
        },
        "parity_gates": {"G1_freddie_parity": {"pass": True,
                                               "n_mismatches": 0}},
        "parity_gates_all_pass": True,
        "verdict": verdict,
        "runtime_s": time.perf_counter() - t0,
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=1))

    print("\n" + "=" * 74)
    print(" INDEPENDENT-AGENCY FLOOR READ")
    print("=" * 74)
    print(f"  headline cell: {HEADLINE_CELL}, out-of-window 2017--2019")
    print(f"    Freddie {fre['cpr_pct']}%  (n={fre['n_cohort_months']})")
    print(f"    Fannie  {fan['cpr_pct']}%  (n={fan['n_cohort_months']})")
    print(f"    difference {payload['comparison']['difference_pp']}pp; clean band "
          f"{CLEAN_BAND[0]}--{CLEAN_BAND[1]}%; inside="
          f"{payload['comparison']['fannie_inside_clean_band']}")
    print(f"  R1 mature (age>=24): Freddie "
          f"{payload['comparison']['R1_freddie_mature_cell']['cpr_pct']}% "
          f"(n={payload['comparison']['R1_freddie_mature_cell']['n_cohort_months']})"
          f"  Fannie "
          f"{payload['comparison']['R1_fannie_mature_cell']['cpr_pct']}% "
          f"(n={payload['comparison']['R1_fannie_mature_cell']['n_cohort_months']})")
    print(f"  verdict: {verdict}")
    print(f"  runtime {payload['runtime_s']:.1f}s -> {RESULTS_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
