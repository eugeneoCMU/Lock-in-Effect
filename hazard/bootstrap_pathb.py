#!/usr/bin/env python3
"""
Path B loan-level (stratified) bootstrap — sampling uncertainty for the
microsimulation recovery and the lock-in marginal.

The manuscript concedes that Path B's recovery is reported across the
elasticity calibration band rather than with estimated sampling uncertainty:
the production figure is computed on a single stratified 75,000-loan draw
from the Freddie Mac performance files. This script estimates that sampling
uncertainty directly: it resamples loans WITH replacement WITHIN each
stratum (preserving each stratum's loan count, i.e. respecting the
stratified design), reruns the production central (p_q 6.5) and beta1=0 null
legs on each replicate, and reports percentile intervals for the central
recovery, the null recovery, and their difference (the lock-in marginal,
paired within replicate).

SPEC (fixed ex ante):
- Replicates: 200 (the Path A cluster-bootstrap convention).
- Resampling: within-stratum with replacement, stratum sizes preserved;
  replicate r uses numpy default_rng(r) for the resample only.
- Simulation: production convention otherwise — engine RNG_SEED 42 held
  fixed across replicates (the default-channel draws are not the object of
  interest), US regime only (the US leg's RNG offset is zero under the
  production tuple, so US results are draw-identical to the production
  convention), shared macro frame fetched once, raw-basis scoring via
  extension_risk.score_extension_risk.
- Reported: 2.5/50/97.5 percentiles for central share, null share, and the
  paired marginal (pp of benchmark); same for dollars. The shared-basis
  figures follow by subtracting the flat basis wedge, which is common to
  both legs of every replicate, so the marginal interval is basis-invariant.
- Incremental output: per-replicate rows appended to
  data/bootstrap_pathb_draws.csv as they complete; summary JSON written at
  the end to data/bootstrap_pathb_results.json.

Run:  cd hazard && python3 bootstrap_pathb.py [--reps 200]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
DRAWS_CSV = DATA_DIR / "bootstrap_pathb_draws.csv"
RESULTS_JSON = DATA_DIR / "bootstrap_pathb_results.json"
TMP_PARQUET = DATA_DIR / "_bootstrap_pathb_tmp.parquet"

CENTRAL_PQ = 6.5
NULL_PQ = 0.0


def stratified_resample(loans: pl.DataFrame, rng: np.random.Generator) -> pl.DataFrame:
    """Within-stratum resample with replacement, stratum sizes preserved."""
    pdf = loans.to_pandas()
    idx_parts = []
    for _, grp in pdf.groupby("stratum_id", sort=False):
        take = rng.integers(0, len(grp), size=len(grp))
        idx_parts.append(grp.index.to_numpy()[take])
    idx = np.concatenate(idx_parts)
    return pl.from_pandas(pdf.loc[idx].reset_index(drop=True))


def _run_leg(loans_r: pl.DataFrame, macro: pd.DataFrame,
             empirical: pd.DataFrame, pq: float) -> tuple[float, float]:
    res = run_qt_microsim(
        loan_sample=loans_r, macro=macro, regimes=("US",),
        output=TMP_PARQUET, p_q_shock_pct=pq,
    )
    score = score_extension_risk(res["US"], empirical)
    return float(score["hazard_trapped_b"]), float(score["share_explained_pct"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    args = ap.parse_args()

    print("Fetching shared macro frame + empirical benchmark …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    rows = []
    t0 = time.perf_counter()
    for rep in range(1, args.reps + 1):
        rng = np.random.default_rng(rep)
        loans_r = stratified_resample(loans, rng)
        c_b, c_pct = _run_leg(loans_r, macro, empirical, CENTRAL_PQ)
        n_b, n_pct = _run_leg(loans_r, macro, empirical, NULL_PQ)
        row = {
            "rep": rep,
            "central_trapped_b": c_b, "central_share_pct": c_pct,
            "null_trapped_b": n_b, "null_share_pct": n_pct,
            "marginal_b": c_b - n_b, "marginal_pp": c_pct - n_pct,
        }
        rows.append(row)
        pd.DataFrame([row]).to_csv(
            DRAWS_CSV, mode="a", header=not DRAWS_CSV.exists(), index=False,
        )
        if rep % 10 == 0 or rep == 1:
            el = time.perf_counter() - t0
            print(f"rep {rep:4d}/{args.reps}  central {c_pct:6.2f}%  "
                  f"null {n_pct:6.2f}%  marginal {c_pct - n_pct:+5.2f}pp  "
                  f"[{el / rep:.1f}s/rep, ~{el / rep * (args.reps - rep) / 60:.0f}m left]",
                  flush=True)
    runtime_s = time.perf_counter() - t0
    if TMP_PARQUET.exists():
        TMP_PARQUET.unlink()

    df = pd.DataFrame(rows)

    def pcts(col: str) -> dict:
        q = np.percentile(df[col], [2.5, 50.0, 97.5])
        return {
            "p2_5": float(q[0]), "median": float(q[1]), "p97_5": float(q[2]),
            "mean": float(df[col].mean()), "sd": float(df[col].std(ddof=1)),
        }

    payload = {
        "mode": "bootstrap_pathb",
        "spec": (
            "within-stratum loan resample with replacement, stratum sizes "
            "preserved; resample rng seed = replicate index; engine seed 42 "
            "fixed; US regime only; central (p_q 6.5) + null (p_q 0) per "
            "replicate; raw-basis scoring; percentile intervals"
        ),
        "n_reps": int(len(df)),
        "central_share_pct": pcts("central_share_pct"),
        "null_share_pct": pcts("null_share_pct"),
        "marginal_pp": pcts("marginal_pp"),
        "central_trapped_b": pcts("central_trapped_b"),
        "null_trapped_b": pcts("null_trapped_b"),
        "marginal_b": pcts("marginal_b"),
        "runtime_s": round(runtime_s, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    print("\nCentral share:  "
          f"[{payload['central_share_pct']['p2_5']:.2f}, "
          f"{payload['central_share_pct']['p97_5']:.2f}]%  "
          f"median {payload['central_share_pct']['median']:.2f}%")
    print("Null share:     "
          f"[{payload['null_share_pct']['p2_5']:.2f}, "
          f"{payload['null_share_pct']['p97_5']:.2f}]%  "
          f"median {payload['null_share_pct']['median']:.2f}%")
    print("Marginal (pp):  "
          f"[{payload['marginal_pp']['p2_5']:+.2f}, "
          f"{payload['marginal_pp']['p97_5']:+.2f}]  "
          f"median {payload['marginal_pp']['median']:+.2f}")
    print(f"Saved: {RESULTS_JSON}")


if __name__ == "__main__":
    main()
