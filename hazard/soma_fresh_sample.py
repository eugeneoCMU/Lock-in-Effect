"""Draw a new Freddie 30-year sample from all streamed pre-QT snapshots.

The sample is allocated to the listed June 2022 UMBS 30-year coupon by
vintage cells. The source remains Freddie servicing data, so this is a
composition sensitivity rather than a probability draw from SOMA collateral.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "hazard"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from joint_soma_pair import targets  # noqa: E402

SNAPSHOTS = ROOT / "hazard/data/soma_stream_quarters"
BOOK = ROOT / "hazard/data/composition_shift_results.json"
OUTPUT = ROOT / "hazard/data/soma_fresh_umbs30_sample.parquet"
REPORT = ROOT / "hazard/data/soma_fresh_umbs30_sample_report.json"
QUARTERS = [f"{year}Q{quarter}" for year in range(2017, 2022)
            for quarter in range(1, 5)]


def allocate_counts(target: dict[tuple[float, str], float], n: int) -> dict:
    """Largest-remainder allocation gives exactly n observations."""
    raw = {cell: share * n for cell, share in target.items()}
    counts = {cell: int(np.floor(value)) for cell, value in raw.items()}
    left = n - sum(counts.values())
    for cell in sorted(raw, key=lambda c: (-(raw[c] - counts[c]), c))[:left]:
        counts[cell] += 1
    return counts


def draw(snapshot_dir: Path = SNAPSHOTS, output: Path = OUTPUT,
         report_path: Path = REPORT, n: int = 75_000, seed: int = 42) -> dict:
    missing = [q for q in QUARTERS if not (snapshot_dir / f"{q}.parquet").exists()]
    if missing:
        raise FileNotFoundError(f"Missing quarter snapshots: {', '.join(missing)}")
    frames = [pl.read_parquet(snapshot_dir / f"{q}.parquet") for q in QUARTERS]
    universe = pl.concat(frames)
    if universe["loan_id"].n_unique() != len(universe):
        raise ValueError("Duplicate loan IDs in snapshot universe")
    if universe.filter((pl.col("reporting_period") != "202205") |
                       (pl.col("original_loan_term") != 360) |
                       (pl.col("balance") <= 0)).height:
        raise ValueError("Snapshot has a non-May-2022, non-30-year, or exited loan")

    target, mass = targets(json.loads(BOOK.read_text()))
    counts = allocate_counts(target, n)
    # The SOMA coupon is a pass-through rate. Apply the manuscript's 80 bp
    # note-to-pass-through bridge before matching loan rows to target cells.
    universe = universe.with_columns([
        (((pl.col("coupon") - 0.008) / 0.005).round(0) * 0.005)
         .round(4).alias("soma_coupon_bucket"),
        pl.when(pl.col("vintage") <= 2019).then(pl.lit("2017-19"))
        .otherwise(pl.col("vintage").cast(pl.Utf8)).alias("soma_vintage_group"),
    ])
    samples = []
    cell_report = {}
    for i, (cell, count) in enumerate(sorted(counts.items())):
        coupon, vintage = cell
        pool = universe.filter((pl.col("soma_coupon_bucket") == coupon) &
                               (pl.col("soma_vintage_group") == vintage))
        if len(pool) < count:
            raise ValueError(f"Target cell {cell} needs {count:,} loans; "
                             f"Freddie snapshot has {len(pool):,}")
        selected = pool.sample(n=count, seed=seed + i, shuffle=True)
        samples.append(selected)
        cell_report[f"{coupon:.4f}|{vintage}"] = {
            "freddie_universe_loans": len(pool),
            "freddie_universe_balance_b": float(pool["balance"].sum() / 1e9),
            "target_share_within_supported_cells": target[cell],
            "sample_loans": count,
        }
    sample = pl.concat(samples).with_columns(pl.lit(1.0).alias("weight"))
    if len(sample) != n or sample["loan_id"].n_unique() != n:
        raise RuntimeError("Fresh draw failed size or uniqueness check")
    sample = sample.drop("soma_coupon_bucket", "soma_vintage_group")
    output.parent.mkdir(parents=True, exist_ok=True)
    sample.write_parquet(output)
    report = {
        "mode": "fresh_freddie_umbs30_cell_targeted_sample",
        "n": n, "seed": seed,
        "source_quarters": QUARTERS,
        "source_universe_30yr_survivors": len(universe),
        "source_universe_balance_b": float(universe["balance"].sum() / 1e9),
        "listed_cells_total_soma_face_share": mass,
        "cell_report": cell_report,
        "scope": "Freddie 30-year survivors at May 2022, drawn from all 2017-2021 quarterly files. Cell shares follow listed June 2022 UMBS 30-year SOMA coupon-by-vintage cells after an assumed 80 bp note-to-pass-through conversion. No Fannie, Ginnie, 15-year, pre-2017, or 2022 direct loan draw.",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    result = draw()
    print(f"Drawn {result['n']:,} from "
          f"{result['source_universe_30yr_survivors']:,} Freddie survivors")
