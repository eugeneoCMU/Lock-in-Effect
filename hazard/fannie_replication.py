#!/usr/bin/env python3
"""
Fannie Mae SF LPH external replication — production runner (round-14 W4).

SPEC (fixed ex ante; committed BEFORE the production run, per repo convention
— the floor_sweep.py strong form). Author sign-offs 2026-07-15: ZBC treatment
ratified, license posture ratified (code-only replication package), pull
green-lit.

UNIVERSE
  Acquisition quarters 2017Q1–2022Q4 (24 files, one per quarter; the API's
  quarterly endpoint slices by ACQUISITION quarter with full performance
  history — probe-verified on 2019Q1). Origination universe = vintages
  2017–2021 (config.VINTAGE_YEARS), enforced by an explicit vintage filter at
  panel-combine and Path B snapshot time: Freddie ships vintage-sliced files,
  Fannie acquisition files carry a short seasoned origination tail
  (probe: 2-year, 0.04% of loans), so the filter IS the Freddie universe
  definition, not a new modeling choice.

ZERO-BALANCE-CODE TREATMENT (ratified; checklist item 6)
  01 = voluntary prepay (== Freddie); {02,03,09,15} = credit events
  (Defaulted); {06,16} = non-credit removals with NO Freddie counterpart,
  treated as CENSORING — they self-censor out of the dollar-denominated risk
  set at removal and are never counted as prepay. Worst-case bracket, from
  the 2019Q1 full-file cross-tab: all 06+16 removals recoded as prepay would
  move 0.38% of removals — negligible at the paper's reporting precision.
  {96,97,98} asserted absent at stage time.

CROSS-AGENCY LEVEL CAVEAT (checklist item 8, stated ex ante)
  Whether Freddie's ZBC 01 absorbs exits Fannie codes as 06/16 is not
  settled by public documentation; given the 0.38% bracket the confound is
  small, but the replication claim is SIGN + floor/band-conditional marginal
  consistency, NOT a hazard-level match. No Fannie delinquency-transition
  exhibit is produced (checklist item 7): the Markov transition layer stays
  the production Freddie-estimated one, a shared-layer invariant.

CONSTRUCTION (production conventions held fixed)
  Ingestion: common/fannie_{key,auth,lph}.py + hazard/prepare_fannie.py with
  probe-frozen constants (pipe delimiter, headerless, 113-wire-column assert,
  2-digit ZBC, early-UPB unmask ON) → Freddie-coded staged pairs consumed by
  UNMODIFIED ingest.build_panel_from_files. Disk protocol per quarter
  (~5 GB peak vs single-digit free): download zip (~0.25 GB) → extract
  (~3.5 GB) → delete zip → stage pair (~1.4 GB) → delete native → per-quarter
  cohort-month cells + Path B pool piece → delete staged pair. Free-disk
  guard: abort below MIN_FREE_GIB before each quarter; the loop is
  resume-safe (a quarter with cells+pool pieces on disk is skipped; a
  surviving native file forces a fresh overwrite staging).
  Panel: per-quarter cells recombined by combine_quarter_cells(), which
  replicates ingest.py's combine stage (ingest.py:246-276) verbatim — sums
  for exposure_upb/orig_upb_sum/prepaid_upb/loan_count, mean of
  mean_loan_age, first of mode_state, then monthly_prepay_rate/period/burnout
  derived on the combined frame — in spec quarter order. Equality with the
  one-shot build is gated by tests/test_fannie_replication.py (synthetic
  two-pair identity), and end-to-end staging+ingest determinism by the
  2019Q1 gate: production cells for FNMA2019Q1 must equal the probe panel.
  Path A: hazard_fit.fit_hazard_glm(panel=<Fannie panel>, seasonal=True
  [spec v4], ridge grid default) with output to a Fannie-only artifact path;
  the frozen Freddie HAZARD_COEF_PATH is never written.
  Path B: 75k stratified sample via loan_sample.py logic UNCHANGED, drawn as
  per-quarter pool pieces (per_file = max(1000, 4*75000 // 24) = 12,500;
  piece seed = RNG_SEED + spec-index of quarter; final _stratified_sample
  seed = RNG_SEED). Microsim: run_qt_microsim defaults exactly as
  no_lockin_null.py — central p_q shock 6.5% and null 0.0%, RNG_SEED 42,
  regimes ("US","Danish"), literature hazard, raw-basis scoring via
  extension_risk.score_extension_risk against the empirical benchmark.

GATES (numeric; withdraw-not-reinterpret on failure)
  parity_freddie   Re-score the committed Freddie central+null microsim
                   parquets against the freshly fetched empirical frame:
                   must reproduce no_lockin_null_results.json
                   {null,central}×{trapped_b, share_pct} within ±$0.01B /
                   ±0.01pp, else ABORT (scoring environment drifted).
  gate_2019q1      Production FNMA2019Q1 cells == probe panel on every
                   deterministic column, when the probe panel is present
                   locally. AMENDED 2026-07-15 after the first production
                   attempt (gate as originally committed demanded full-frame
                   equality and failed): mode_state is excluded from strict
                   equality because ingest.py's mode().first() breaks modal
                   ties in nondeterministic order — a latent property of the
                   frozen Freddie path, surfaced here as 19/9,534 cells, each
                   verified an exact modal tie of the underlying loan-month
                   state distribution, with every estimator-relevant column
                   equal on the first attempt. A mode_state divergence passes
                   only if verified as a modal tie recomputed from the staged
                   pair. mode_state feeds only the secondary Markov exhibit,
                   declined for Fannie ex ante (checklist item 7). Amendment
                   recorded before the run resumed; the pre-registered
                   acceptance gate (gate_envelope) is untouched.
  gate_envelope    PRE-REGISTERED ACCEPTANCE: Fannie lockin_marginal_share_pp
                   is (a) positive and (b) inside [min, max] of
                   box_marginals_pp in the committed
                   floor_band_cross_results.json (2.11–13.17pp at spec
                   freeze). Pass ⇒ the W4 replication claim is supported at
                   the level stated in the caveat above. Fail ⇒ reported as
                   discordant in the limitations section; the spec is not
                   reinterpreted after the fact.

EXPECTED ARTIFACT
  hazard/data/fannie_replication_results.json (committed). License posture
  (ratified): the replication package ships CODE ONLY — no Fannie data and,
  conservatively, no derived cells. Everything loan- or cell-level stays
  local and gitignored (fannie_native/, staged pairs, *fannie*.parquet,
  fannie_quarters/, hazard_coefficients_fannie.json); the committed artifact
  carries only headline statistics of the kind reported in the manuscript.

Run:  cd hazard && python3 fannie_replication.py
      (resume-safe; --skip-pull / --quarters / --rescore for diagnostics)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import polars as pl

from config import (
    DATA_DIR,
    HAZARD_COEF_PATH,
    MICROSIM_RESULTS_PATH,
    N_LOANS,
    RNG_SEED,
    ROTHSTEIN_Q_DECLINE_MID,
    VINTAGE_YEARS,
)
from ingest import build_panel_from_files
from loan_sample_fannie import (
    FANNIE_LOAN_SAMPLE_PATH,
    finalize_fannie_sample,
    write_pool_piece,
)
from prepare_fannie import (
    FANNIE_NATIVE_DIR,
    FANNIE_PANEL_PATH,
    FANNIE_RAW_DIR,
    fetch_lph_native_files,
    stage_native_file,
)

# ---- spec constants (fixed ex ante) ---------------------------------------
QUARTERS: list[tuple[int, str]] = [
    (y, q) for y in range(2017, 2023) for q in ("Q1", "Q2", "Q3", "Q4")
]
POOL_PER_FILE = max(1000, (N_LOANS * 4) // len(QUARTERS))   # 12,500
MIN_FREE_GIB = 5.5
DOWNLOAD_ATTEMPTS = 3
PARITY_TOL_B = 0.01
PARITY_TOL_PP = 0.01

FANNIE_QUARTER_DIR = DATA_DIR / "fannie_quarters"
MANIFEST_PATH = FANNIE_QUARTER_DIR / "manifest.json"
FANNIE_COEF_PATH = DATA_DIR / "hazard_coefficients_fannie.json"
FANNIE_CENTRAL_CACHE = DATA_DIR / "microsim_results_fannie_central.parquet"
FANNIE_NULL_CACHE = DATA_DIR / "microsim_results_fannie_pq0.0.parquet"
FLOOR_BAND_PATH = DATA_DIR / "floor_band_cross_results.json"
FREDDIE_NULL_RESULTS = DATA_DIR / "no_lockin_null_results.json"
FREDDIE_NULL_CACHE = DATA_DIR / "microsim_results_pq0.0.parquet"
RESULTS_JSON = DATA_DIR / "fannie_replication_results.json"

_PANEL_KEYS = ["vintage", "coupon", "fico_bucket", "ltv_bucket", "reporting_period"]
_DERIVED_COLS = ["monthly_prepay_rate", "period", "burnout"]


# ---------------------------------------------------------------------------
# Panel: recombine per-quarter cells exactly as ingest.py's combine stage
# ---------------------------------------------------------------------------
def combine_quarter_cells(
    cell_paths: Sequence[Path],
    output: Path,
    vintage_years: Sequence[int] | None = VINTAGE_YEARS,
) -> pl.DataFrame:
    """
    Concatenate per-quarter cohort-month cells (each a single-pair
    build_panel_from_files output) and re-run the combine stage of
    ingest.build_panel_from_files (ingest.py:246-276) verbatim. Per-quarter
    derived columns are dropped and re-derived on the combined frame; the
    optional vintage filter (applied before deriving, equivalent for kept
    cohorts since all derives are within-cohort) enforces the origination
    universe. Identity with the one-shot build over the same pairs is gated
    by tests/test_fannie_replication.py.
    """
    frames = [pl.read_parquet(p).drop(_DERIVED_COLS) for p in cell_paths]
    panel = pl.concat(frames)
    panel = panel.group_by(_PANEL_KEYS).agg([
        pl.col("exposure_upb").sum(),
        pl.col("orig_upb_sum").sum(),
        pl.col("prepaid_upb").sum(),
        pl.col("mean_loan_age").mean(),
        pl.col("mode_state").first(),
        pl.col("loan_count").sum(),
    ])
    if vintage_years is not None:
        panel = panel.filter(pl.col("vintage").is_in(list(vintage_years)))
    panel = (
        panel
        .sort(_PANEL_KEYS)
        .with_columns([
            (pl.col("prepaid_upb") / pl.col("exposure_upb").clip(lower_bound=1))
            .alias("monthly_prepay_rate"),
        ])
    )
    panel = panel.with_columns([
        pl.col("reporting_period").str.to_datetime("%Y%m").alias("period"),
    ])
    panel = panel.sort(["vintage", "coupon", "fico_bucket", "ltv_bucket", "period"])
    panel = panel.with_columns([
        (pl.col("prepaid_upb").cum_sum().over(
            ["vintage", "coupon", "fico_bucket", "ltv_bucket"]
        ) / pl.col("orig_upb_sum").clip(lower_bound=1))
        .alias("burnout"),
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(output)
    print(f"Combined Fannie panel saved: {output} ({len(panel):,} rows)")
    return panel


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
def evaluate_envelope_gate(
    marginal_pp: float, box_min: float, box_max: float
) -> dict:
    """Pre-registered acceptance gate: positive AND inside the Freddie box."""
    positive = marginal_pp > 0.0
    in_envelope = box_min <= marginal_pp <= box_max
    return {
        "marginal_pp": marginal_pp,
        "box_min": box_min,
        "box_max": box_max,
        "positive": positive,
        "in_envelope": in_envelope,
        "pass": positive and in_envelope,
    }


def load_freddie_envelope() -> tuple[float, float]:
    box = json.load(open(FLOOR_BAND_PATH))["box_marginals_pp"]
    vals = [c["marginal_pp"] for c in box]
    return min(vals), max(vals)


def freddie_parity_gate(empirical) -> dict:
    """Re-score committed Freddie microsim caches; must reproduce the
    committed no_lockin_null_results.json within tolerance, else the scoring
    environment (live macro/SOMA frame) has drifted and the run aborts."""
    import pandas as pd

    from extension_risk import score_extension_risk

    ref = json.load(open(FREDDIE_NULL_RESULTS))
    null = score_extension_risk(pd.read_parquet(FREDDIE_NULL_CACHE), empirical)
    central = score_extension_risk(pd.read_parquet(MICROSIM_RESULTS_PATH), empirical)
    checks = {
        "null_trapped_b": (null["hazard_trapped_b"], ref["null_trapped_b"], PARITY_TOL_B),
        "null_share_pct": (null["share_explained_pct"], ref["null_share_pct"], PARITY_TOL_PP),
        "central_trapped_b": (central["hazard_trapped_b"], ref["central_trapped_b"], PARITY_TOL_B),
        "central_share_pct": (central["share_explained_pct"], ref["central_share_pct"], PARITY_TOL_PP),
    }
    out = {}
    for k, (got, want, tol) in checks.items():
        out[k] = {"got": float(got), "want": float(want), "tol": tol,
                  "pass": abs(float(got) - float(want)) <= tol}
    out["pass"] = all(v["pass"] for v in out.values() if isinstance(v, dict))
    return out


def _verify_mode_ties(
    diff_cells: pl.DataFrame, orig_path: Path, perf_path: Path
) -> bool:
    """Each mode_state divergence must be an exact modal tie of the
    underlying loan-month servicer-state distribution (recomputed from the
    staged pair through the same ingest scans)."""
    from ingest import _scan_orig, _scan_perf

    joined = _scan_perf(perf_path).join(
        _scan_orig(orig_path), on="loan_sequence_number", how="inner"
    )
    dist = (
        joined.join(diff_cells.select(_PANEL_KEYS).lazy(), on=_PANEL_KEYS, how="inner")
        .group_by(_PANEL_KEYS + ["servicer_state"])
        .agg(pl.len().alias("n"))
        .collect()
    )
    for row in diff_cells.iter_rows(named=True):
        cell = dist
        for k in _PANEL_KEYS:
            cell = cell.filter(pl.col(k) == row[k])
        counts = dict(zip(cell["servicer_state"].to_list(), cell["n"].to_list()))
        mx = max(counts.values(), default=0)
        if not (counts.get(row["got_mode"], 0) == mx
                and counts.get(row["want_mode"], 0) == mx):
            return False
    return True


def gate_2019q1_cells(
    cells_path: Path, probe_panel: Path, staged_pair: tuple[Path, Path] | None = None
) -> dict:
    """Production 2019Q1 cells must equal the probe panel built one-shot from
    the same native file (end-to-end staging+ingest determinism), on every
    deterministic column. mode_state is excluded from strict equality —
    ingest.py's mode().first() (ingest.py:236) breaks modal TIES in
    nondeterministic order, a latent property of the frozen Freddie path that
    the 2026-07-15 production run surfaced (19/9,534 cells, all verified
    exact ties; every estimator-relevant column matched exactly). A
    mode_state divergence passes only if it is a verified modal tie
    recomputed from the staged pair; mode_state feeds only the secondary
    Markov exhibit, which the spec already declines for Fannie (item 7)."""
    from polars.testing import assert_frame_equal

    got = pl.read_parquet(cells_path).sort(_PANEL_KEYS)
    want = pl.read_parquet(probe_panel).sort(_PANEL_KEYS)
    non_mode = [c for c in got.columns if c != "mode_state"]
    try:
        # exact: this is a determinism gate, not a numeric-tolerance gate
        assert_frame_equal(got.select(non_mode), want.select(non_mode),
                           check_exact=True)
    except AssertionError as e:
        return {"pass": False, "cells": len(got),
                "mode_state_diffs": None, "mode_diffs_all_ties": None,
                "detail": str(e)[:400]}

    mask = got["mode_state"] != want["mode_state"]
    n_diff = int(mask.sum())
    if n_diff == 0:
        return {"pass": True, "cells": len(got),
                "mode_state_diffs": 0, "mode_diffs_all_ties": True}

    diff_cells = (
        got.filter(mask)
        .select(_PANEL_KEYS + ["mode_state"]).rename({"mode_state": "got_mode"})
        .with_columns(want.filter(mask)["mode_state"].alias("want_mode"))
    )
    all_ties = (
        _verify_mode_ties(diff_cells, *staged_pair) if staged_pair else False
    )
    return {"pass": bool(all_ties), "cells": len(got),
            "mode_state_diffs": n_diff, "mode_diffs_all_ties": bool(all_ties)}


# ---------------------------------------------------------------------------
# Per-quarter production loop
# ---------------------------------------------------------------------------
def _free_gib() -> float:
    return shutil.disk_usage(DATA_DIR).free / 2**30


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.load(open(MANIFEST_PATH))
    return {}


def _save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def process_quarter(year: int, quarter: str, spec_index: int, manifest: dict) -> None:
    tag = f"FNMA{year}{quarter}"
    cells_out = FANNIE_QUARTER_DIR / f"cells_{tag}.parquet"
    pool_out = FANNIE_QUARTER_DIR / f"pool_{tag}.parquet"
    if cells_out.exists() and pool_out.exists():
        print(f"[{tag}] complete (cells + pool piece on disk) — skipping")
        return

    free = _free_gib()
    if free < MIN_FREE_GIB:
        raise RuntimeError(
            f"[{tag}] free disk {free:.1f} GiB < {MIN_FREE_GIB} GiB guard — "
            "aborting (loop is resume-safe; free space and rerun)."
        )

    t0 = time.perf_counter()
    # 1. download + extract (skips when the native .txt survives)
    native_existed = (FANNIE_NATIVE_DIR / f"lph_{tag}.txt").exists()
    fetched = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            fetched = fetch_lph_native_files([year], [quarter])
            break
        except Exception as e:  # fresh signed URL on each retry
            for leftover in FANNIE_NATIVE_DIR.glob(f"lph_{tag}*"):
                leftover.unlink()
            if attempt == DOWNLOAD_ATTEMPTS:
                raise
            print(f"[{tag}] download attempt {attempt} failed ({e}); retrying …")
            time.sleep(30)
    if len(fetched) != 1:
        raise ValueError(
            f"[{tag}] expected exactly one file for the acquisition quarter, "
            f"got {len(fetched)}: {[t for t, _ in fetched]}. Spec assumes one "
            "file per quarter (FAQ #11); investigate before proceeding."
        )
    _, native_path = fetched[0]
    (FANNIE_NATIVE_DIR / f"lph_{tag}.zip").unlink(missing_ok=True)

    # 2. stage; a surviving native means the staged pair's completeness is
    # unknown (or probe-era) — restage fresh rather than trust it. The
    # low-memory path (auto for refi-wave-sized natives) frees the native as
    # soon as its last scan completes so the on-disk sort spill fits.
    orig, perf = stage_native_file(native_path, tag, overwrite=native_existed,
                                   delete_native_after_scan=True)
    staged_loans = int(
        pl.scan_csv(orig, separator="|", has_header=False, infer_schema_length=0)
        .select(pl.len()).collect().item()
    )
    staged_rows = int(
        pl.scan_csv(perf, separator="|", has_header=False, infer_schema_length=0)
        .select(pl.len()).collect().item()
    )

    # 3. native no longer needed (already gone if staging deleted it early)
    native_path.unlink(missing_ok=True)

    # 4. per-quarter cohort-month cells (unfiltered; vintage filter at combine)
    FANNIE_QUARTER_DIR.mkdir(parents=True, exist_ok=True)
    cells = build_panel_from_files([(orig, perf)], output=cells_out)

    gate = None
    if tag == "FNMA2019Q1" and FANNIE_PANEL_PATH.exists():
        gate = gate_2019q1_cells(cells_out, FANNIE_PANEL_PATH,
                                 staged_pair=(orig, perf))
        print(f"[{tag}] 2019Q1 determinism gate: "
              f"{'PASS' if gate['pass'] else 'FAIL'}")
        if not gate["pass"]:
            raise RuntimeError(
                f"[{tag}] production cells != probe panel: {gate['detail']}"
            )

    # 5. Path B pool piece (seed tied to spec index, not processing order)
    n_pool = write_pool_piece(
        orig, perf,
        per_file=POOL_PER_FILE,
        seed=RNG_SEED + spec_index,
        output=pool_out,
        vintage_years=VINTAGE_YEARS,
    )

    # 6. staged pair no longer needed
    orig.unlink()
    perf.unlink()

    manifest[tag] = {
        "spec_index": spec_index,
        "staged_loans": staged_loans,
        "staged_rows": staged_rows,
        "cells_rows": len(cells),
        "pool_rows": n_pool,
        "gate_2019q1": gate,
        "runtime_s": round(time.perf_counter() - t0, 1),
        "completed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save_manifest(manifest)
    print(f"[{tag}] done in {manifest[tag]['runtime_s']}s "
          f"({staged_loans:,} loans, {staged_rows:,} rows, "
          f"{len(cells):,} cells, {n_pool:,} pool rows; "
          f"free {_free_gib():.1f} GiB)")


# ---------------------------------------------------------------------------
# Replication legs
# ---------------------------------------------------------------------------
def run_path_a(panel: pl.DataFrame) -> dict:
    """FE-Poisson (spec v4) on the Fannie panel; compare the lock-in
    covariate against the frozen Freddie artifact."""
    from hazard_fit import fit_hazard_glm

    fit = fit_hazard_glm(panel=panel, output=FANNIE_COEF_PATH, seasonal=True)
    freddie = json.load(open(HAZARD_COEF_PATH))
    f_coef = fit["coefficients"]["rate_gap_bps"]
    w_coef = freddie["coefficients"]["rate_gap_bps"]
    # coefficients are on standardized covariates; per-bps effects divide by
    # each agency's own standardization std
    f_per_bps = f_coef / fit["rate_gap_bps_std"]
    w_per_bps = w_coef / freddie["rate_gap_bps_std"]
    return {
        "fannie_rate_gap_coef_std": f_coef,
        "freddie_rate_gap_coef_std": w_coef,
        "fannie_rate_gap_per_bps": f_per_bps,
        "freddie_rate_gap_per_bps": w_per_bps,
        "sign_match": (f_per_bps > 0) == (w_per_bps > 0),
        "per_bps_ratio_fannie_over_freddie": f_per_bps / w_per_bps,
        "fannie_n_train": fit["n_train"],
        "fannie_n_holdout": fit["n_holdout"],
        "fannie_n_strata": fit["n_strata"],
        "fannie_holdout_r2": fit.get("holdout_r2"),
        "spec_version": fit["spec_version"],
        "coef_artifact": str(FANNIE_COEF_PATH.name) + " (local only, not committed)",
    }


def run_path_b(loans: pl.DataFrame, empirical) -> dict:
    """Central + beta1=0 null microsim on the Fannie sample, scored exactly
    as no_lockin_null.py scores the Freddie production runs."""
    import pandas as pd

    from extension_risk import score_extension_risk
    from microsim_engine import run_qt_microsim

    if not FANNIE_CENTRAL_CACHE.exists():
        print("Fannie central microsim (P_q 6.5%) …")
        run_qt_microsim(
            loan_sample=loans, output=FANNIE_CENTRAL_CACHE,
            p_q_shock_pct=ROTHSTEIN_Q_DECLINE_MID * 100,
        )
    if not FANNIE_NULL_CACHE.exists():
        print("Fannie no-lock-in null microsim (P_q 0%) …")
        run_qt_microsim(
            loan_sample=loans, output=FANNIE_NULL_CACHE, p_q_shock_pct=0.0,
        )
    central = score_extension_risk(pd.read_parquet(FANNIE_CENTRAL_CACHE), empirical)
    null = score_extension_risk(pd.read_parquet(FANNIE_NULL_CACHE), empirical)
    return {
        "central_trapped_b": central["hazard_trapped_b"],
        "central_share_pct": central["share_explained_pct"],
        "null_trapped_b": null["hazard_trapped_b"],
        "null_share_pct": null["share_explained_pct"],
        "lockin_marginal_b": central["hazard_trapped_b"] - null["hazard_trapped_b"],
        "lockin_marginal_share_pp": (
            central["share_explained_pct"] - null["share_explained_pct"]
        ),
    }


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--skip-pull", action="store_true",
                        help="Skip the quarter loop (cells/pool pieces must exist)")
    parser.add_argument("--quarters", nargs="+", default=None,
                        help="Diagnostic subset, e.g. 2019Q1 (production = all 24)")
    parser.add_argument("--rescore", action="store_true",
                        help="Delete Fannie microsim caches before scoring")
    args = parser.parse_args()

    t_run = time.perf_counter()
    manifest = _load_manifest()

    todo = QUARTERS
    if args.quarters:
        wanted = set(args.quarters)
        todo = [(y, q) for (y, q) in QUARTERS if f"{y}{q}" in wanted]

    if not args.skip_pull:
        for y, q in todo:
            process_quarter(y, q, QUARTERS.index((y, q)), manifest)

    # ---- panel + Path A ----------------------------------------------------
    cell_paths = sorted(FANNIE_QUARTER_DIR.glob("cells_FNMA*.parquet"))
    if args.quarters is None and len(cell_paths) != len(QUARTERS):
        raise RuntimeError(
            f"{len(cell_paths)}/{len(QUARTERS)} quarter cell files present — "
            "production combine requires all quarters."
        )
    panel = combine_quarter_cells(
        cell_paths, output=FANNIE_PANEL_PATH, vintage_years=VINTAGE_YEARS
    )

    # ---- Path B sample -----------------------------------------------------
    pool_paths = sorted(FANNIE_QUARTER_DIR.glob("pool_FNMA*.parquet"))
    sample = finalize_fannie_sample(
        pool_paths, n_loans=N_LOANS, seed=RNG_SEED, output=FANNIE_LOAN_SAMPLE_PATH
    )

    # ---- scoring environment parity, then the replication legs -------------
    from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

    print("Fetching macro + SOMA benchmark …")
    empirical = build_empirical_metrics(fetch_data(), soma_rolloff=fetch_soma_mbs_monthly())

    parity = freddie_parity_gate(empirical)
    print(f"Freddie scoring parity gate: {'PASS' if parity['pass'] else 'FAIL'}")
    if not parity["pass"]:
        raise RuntimeError(
            "Freddie parity gate failed — the live macro/SOMA frame no longer "
            f"reproduces the committed artifact: {json.dumps(parity, indent=1)}"
        )

    path_a = run_path_a(panel)
    if args.rescore:
        FANNIE_CENTRAL_CACHE.unlink(missing_ok=True)
        FANNIE_NULL_CACHE.unlink(missing_ok=True)
    path_b = run_path_b(sample, empirical)

    box_min, box_max = load_freddie_envelope()
    envelope = evaluate_envelope_gate(
        path_b["lockin_marginal_share_pp"], box_min, box_max
    )

    payload = {
        "mode": "fannie_replication",
        "spec": "hazard/fannie_replication.py module docstring (fixed ex ante)",
        "git_commit": _git_head(),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "acquisition_quarters": [f"{y}{q}" for y, q in QUARTERS],
        "vintage_years": VINTAGE_YEARS,
        "zbc_treatment": {
            "prepay": ["01"],
            "credit_event": ["02", "03", "09", "15"],
            "censored_non_credit": ["06", "16"],
            "asserted_absent": ["96", "97", "98"],
            "bracket_06_16_share_of_removals_2019q1": 0.0038,
        },
        "level_comparison_caveat": (
            "Replication claim is sign + floor/band-conditional marginal "
            "consistency, not a hazard-level match (Freddie ZBC-01 absorption "
            "of Fannie 06/16-type exits unresolved; bracket 0.38% of removals)."
        ),
        "universe": {
            "quarters_processed": len([t for t in manifest.values() if "cells_rows" in t]),
            "staged_loans_total": sum(t["staged_loans"] for t in manifest.values()),
            "staged_rows_total": sum(t["staged_rows"] for t in manifest.values()),
            "panel_cells": len(panel),
            "sample_n_loans": len(sample),
            "sample_n_strata": int(sample["stratum_id"].n_unique()),
            "pool_rows_total": sum(t["pool_rows"] for t in manifest.values()),
        },
        "path_a": path_a,
        "path_b": path_b,
        "gates": {
            "parity_freddie": parity,
            "gate_2019q1": manifest.get("FNMA2019Q1", {}).get("gate_2019q1"),
            "gate_envelope": envelope,
        },
        "runtime_s": round(time.perf_counter() - t_run, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=float)
        f.write("\n")

    print(
        f"\nFannie replication: central ${path_b['central_trapped_b']:.1f}B "
        f"({path_b['central_share_pct']:.1f}%), null "
        f"${path_b['null_trapped_b']:.1f}B ({path_b['null_share_pct']:.1f}%) "
        f"→ lock-in marginal ${path_b['lockin_marginal_b']:.1f}B "
        f"({path_b['lockin_marginal_share_pp']:.2f}pp of benchmark)"
    )
    print(
        f"Envelope gate [{box_min:.2f}, {box_max:.2f}]pp: "
        f"{'PASS' if envelope['pass'] else 'FAIL'}   "
        f"Path A sign match: {path_a['sign_match']}"
    )
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
