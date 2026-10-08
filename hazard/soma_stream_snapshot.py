"""Build one pre-QT Freddie snapshot from a streamed orig/perf quarter.

Reads the performance file line by line and keeps only each loan's latest
pre-June-2022 observation in memory. This avoids copying the raw file into
the project and bounds the working set to the loans in one origination quarter.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl


def build(orig: Path, perf: Path, output: Path) -> dict[str, int]:
    quarter = orig.stem.removeprefix("orig_")
    if perf.stem != f"perf_{quarter}":
        raise ValueError("Origination and performance quarters differ")
    orig_rows: dict[str, tuple] = {}
    with orig.open("r", encoding="utf-8", errors="replace") as source:
        for line in source:
            cols = line.rstrip("\n\r").split("|")
            if len(cols) < 22:
                continue
            try:
                fico = int(cols[0])
                upb = float(cols[10])
                ltv = float(cols[11])
                rate = float(cols[12])
                term = int(cols[21])
            except ValueError:
                continue
            if not (300 <= fico <= 850 and upb > 0 and 1 <= ltv <= 200
                    and cols[15] == "FRM" and term == 360):
                continue
            loan_id = cols[19]
            if not loan_id:
                continue
            orig_rows[loan_id] = (fico, upb, ltv, rate, cols[16], term)

    latest: dict[str, tuple] = {}
    rows_scanned = 0
    with perf.open("r", encoding="utf-8", errors="replace") as source:
        for line in source:
            rows_scanned += 1
            cols = line.rstrip("\n\r").split("|")
            if len(cols) < 29:
                continue
            loan_id, period = cols[0], cols[1]
            if loan_id not in orig_rows or not ("200001" <= period < "202206"):
                continue
            try:
                balance = float(cols[2])
                age = float(cols[4])
            except ValueError:
                continue
            if balance < 0:
                continue
            previous = latest.get(loan_id)
            if previous is None or period >= previous[0]:
                latest[loan_id] = (period, balance, age, cols[3], cols[8], cols[28])

    records = []
    for loan_id, (period, balance, age, delinquency, zb, assistance) in latest.items():
        # A historical positive balance is not evidence that the loan was
        # still present immediately before QT. Require the May-2022 record.
        if period != "202205" or balance <= 0 or zb:
            continue
        fico, upb, ltv, rate, property_state, term = orig_rows[loan_id]
        # A zero-balance code denotes a terminated loan even if a reporting
        # row retains an UPB. Keep the same state ordering as ingest.py.
        if zb == "01":
            state = "Prepaid"
        elif zb in {"02", "03", "09", "15"} or delinquency in {"RA", "RP"}:
            state = "Defaulted"
        elif assistance == "F":
            state = "Forbearance"
        elif delinquency == "1":
            state = "D30"
        elif delinquency == "2":
            state = "D60"
        elif delinquency in {"3", "4", "5", "6", "7", "8", "9"}:
            state = "D90+"
        else:
            state = "Current"
        coupon = rate / 100.0
        vintage = int(loan_id[1:3]) + 2000
        fico_bucket = "<680" if fico < 680 else "680-740" if fico < 740 else "740+"
        ltv_bucket = "≤80" if ltv <= 80 else ">80"
        coupon_bucket = round(coupon / 0.005) * 0.005
        stratum_id = f"{vintage}_{round(coupon_bucket * 10000)}_{fico_bucket}"
        records.append((loan_id, stratum_id, fico, property_state, ltv,
                        coupon, upb, balance, age, state, vintage,
                        fico_bucket, ltv_bucket, term, period))

    columns = ["loan_id", "stratum_id", "fico", "property_state", "orig_ltv",
               "coupon", "orig_upb", "balance", "loan_age", "state", "vintage",
               "fico_bucket", "ltv_bucket", "original_loan_term", "reporting_period"]
    output.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(records, schema=columns, orient="row").write_parquet(output)
    return {"orig_eligible_30yr": len(orig_rows), "perf_rows_scanned": rows_scanned,
            "pre_qt_survivors": len(records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("orig", type=Path)
    parser.add_argument("perf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(build(args.orig, args.perf, args.output))
