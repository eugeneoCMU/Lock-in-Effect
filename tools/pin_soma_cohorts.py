"""Pin a SOMA cohort book to a committed, sha-stamped file.

The 11-cohort table behind the production runs was frozen nowhere: the manifest
records only `n_cohorts`, `cohort_wac_pct` and a reference cohort, and
`fetch_soma_mbs_cohorts` re-fetched the *latest* book on every call. That made
the production scheduled-amortization series irreproducible, and it meant a
network hiccup could silently substitute a different book.

The NY Fed API serves historical as-of dates, so the book is recoverable rather
than merely pinnable. This tool fetches a named as-of, runs the repo's own
bucketing, and writes the derived cohort table with a sha256 over its canonical
form. It validates against a frozen manifest when one is named.

    python3 tools/pin_soma_cohorts.py --as-of 2026-07-01 \
        --validate-against abm/data/runs/run-2026-07-04-15yr-foldin/manifest.json
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "abm"))
os.environ.setdefault("FRED_API_KEY", "pin-soma-cohorts-no-fred-use")

import fed_mbs_extension_risk as fed  # noqa: E402


def canonical(cohorts) -> list:
    return [{"coupon": round(float(c["coupon"]), 10),
             "weight": round(float(c["weight"]), 12),
             "origin_date": str(c["origin_date"].date()),
             "months_elapsed": int(c["months_elapsed"]),
             "term_months": int(c["term_months"])}
            for c in cohorts]


def wac_pct(cohorts) -> float:
    return sum(float(c["coupon"]) * float(c["weight"]) for c in cohorts) * 100.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", required=True)
    ap.add_argument("--validate-against", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cohorts = fed.fetch_soma_mbs_cohorts(as_of=a.as_of)
    if len(cohorts) == 1 and cohorts[0]["weight"] == 1.0:
        print("FAILED: fetch fell back to the single legacy cohort; refusing "
              "to pin a fallback book.")
        return 2

    rows = canonical(cohorts)
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    out = {
        "mode": "soma_cohorts_pinned",
        "as_of": a.as_of,
        "source": fed.SOMA_CUSIP_URL.format(date=a.as_of),
        "n_cohorts": len(rows),
        "cohort_wac_pct": round(wac_pct(cohorts), 6),
        "sha256_of_cohorts": hashlib.sha256(blob.encode()).hexdigest(),
        "bucketing": {"min_share": 0.02, "coupon_step_pct": 0.5,
                      "terms": ["30yr", "15yr"]},
        "cohorts": rows,
    }

    if a.validate_against:
        import pandas as pd
        m = json.loads(Path(a.validate_against).read_text())
        pipe = m.get("pipeline", {})
        want_n = pipe.get("n_cohorts")
        want_wac = pipe.get("cohort_wac_pct")
        got_wac = out["cohort_wac_pct"]
        ref = pipe.get("reference_cohort", {})
        top = max(rows, key=lambda c: c["weight"])

        # The decisive check: rebuild the cohort-weighted, term-aware scheduled
        # series and compare its unweighted window mean to the manifest's. It
        # needs no holdings path, so it is exact rather than approximate, and
        # only the run's own cohort book can reproduce it.
        n_months = m["metrics"]["qt_window"]["n_months"]
        win = pd.date_range(fed.QT_START, periods=n_months, freq="ME")
        ser = pd.Series(0.0, index=win)
        for c in rows:
            ser = ser + c["weight"] * fed.scheduled_amortization_series(
                win, coupon=c["coupon"],
                origin=pd.Timestamp(c["origin_date"]), term=c["term_months"])
        got_smm = float(ser.mean()) * 100.0
        want_smm = m["metrics"]["scheduled_amort_b"]["smm_mean_pct"]

        checks = {
            "n_cohorts": {"want": want_n, "got": out["n_cohorts"],
                          "pass": want_n == out["n_cohorts"]},
            # the manifest rounds WAC to 2dp
            "cohort_wac_pct": {"want": want_wac, "got": got_wac,
                               "pass": want_wac is not None
                               and abs(round(got_wac, 2) - want_wac) < 5e-3},
            "reference_cohort_weight": {
                "want": ref.get("weight"), "got": top["weight"],
                "pass": ref.get("weight") is not None
                and abs(ref["weight"] - top["weight"]) < 1e-9},
            "reference_cohort_months_elapsed": {
                "want": ref.get("months_elapsed"), "got": top["months_elapsed"],
                "pass": ref.get("months_elapsed") == top["months_elapsed"]},
            "scheduled_smm_mean_pct": {
                "want": want_smm, "got": got_smm,
                "pass": abs(got_smm - want_smm) < 1e-9},
        }
        out["scheduled_series_parity"] = {
            "recomputed_smm_mean_pct": got_smm,
            "manifest_smm_mean_pct": want_smm,
            "recomputed_annualized_pct": got_smm * 12,
            "note": ("holdings-free: only the run's own cohort book "
                     "reproduces this series"),
        }
        out["validation"] = {"manifest": a.validate_against,
                             "checks": checks,
                             "all_pass": all(c["pass"] for c in checks.values())}

    path = Path(a.out) if a.out else (
        ROOT / "abm" / "data" / f"soma_cohorts_{a.as_of}.json")
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("as_of", "n_cohorts", "cohort_wac_pct",
                       "sha256_of_cohorts")
                      if k in out}, indent=1))
    if "validation" in out:
        print("validation:", json.dumps(out["validation"]["checks"], indent=1))
        print("ALL PASS" if out["validation"]["all_pass"] else "MISMATCH")
    try:
        print("written:", path.relative_to(ROOT))
    except ValueError:
        print("written:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
