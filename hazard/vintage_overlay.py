#!/usr/bin/env python3
"""
vintage_overlay.py — SPEC S8: the vintage-overlay analogue of the Ginnie
published-series overlay, composed with the off-window (headline) floor.

PRE-COMMITTED SPEC. Everything in this header is fixed BEFORE any run and is a
transcription of specs/SPEC_round28_D_F1_I1_I3_J2_S8.md section
"SPEC S8 — vintage overlay analogue (`vintage_overlay`) + the tex-263
characterization fix".  Where this header and that spec differ, the spec
governs and the difference is a defect in this file.

=======================================================================
SPEC
=======================================================================
QUESTION.  The committed vintage work bounds the 2022 / pre-2017 vintage
extrapolation at the LEVEL (vintage_residual_bound.py: +0.1419pp book-CPR
error x $82.8B/pp = $11.75B).  The Ginnie work has both a level bound and a
MARGINAL overlay (ginnie_overlay_offwindow.py: the 20.4% agency share scored
at its observed speeds in BOTH legs, so it contributes zero marginal and the
identified marginal is confined to the conventional 79.6% share).  The vintage
dimension has no marginal counterpart.  This run builds it.

CONSTRUCTION (post-hoc arithmetic; NO microsim run, no engine, no RNG).
  1. Observed monthly speeds, from the local Fannie per-quarter cell files,
     over the QT window QT_START (2022-06-01) <= period < QT_END (2025-12-01),
     42 months, from common/qt_window.py — the single source of truth.
     Segmentation is vintage_residual_bound.py's, unchanged:
         vintage_2022      vintage == 2022
         pre_2017          vintage <= 2016
         sampled_2017_2021 vintage in config.VINTAGE_YEARS (the placebo leg)
     Per month, per segment (the house convention for OBSERVED speeds —
     vintage_residual_bound.py step 3, and ginnie_cpr_overlay.py's SMM<->CPR
     pair; the engine's x12 convention is model-internal and is NOT used for
     observed series):
         SMM_t = sum(prepaid_upb) / sum(exposure_upb)     (pooled dollar SMM)
         CPR_t = (1 - (1 - SMM_t)^12) * 100               (compound)
  2. ONE blended series, ONE overlay_leg call, at share 0.337.
     ##  WHY SEQUENTIAL OVERLAYS ARE WRONG (the spec's own derivation).  ##
     overlay_leg's speed line (ginnie_cpr_overlay.py:121) is
         cpr' = (1 - s) * cpr + s * S
     so applying share s1 with series S1 and THEN share s2 with series S2 to
     the returned frame yields
         (1-s1)(1-s2)*CPR_m + s1(1-s2)*S1 + s2*S2
     which is NOT the intended
         (1-s1-s2)*CPR_m + s1*S1 + s2*S2.
     The first overlay's own contribution is re-diluted by (1-s2), and the
     model leg is double-discounted.  The same error compounds in the
     rolloff line (:118-120), where the second call's exposure_b is rebuilt
     from an ALREADY-overlaid smm_model.  Two overlay_leg calls are therefore
     forbidden.  Instead the two vintage legs are blended in SMM space and
     converted back with the compound form:
         smm_blend_t = (0.231*smm_2022_t + 0.106*smm_pre2017_t) / 0.337
         cpr_blend_t = (1 - (1 - smm_blend_t)^12) * 100
     which makes overlay_leg's internal de-annualization
     (ginnie_cpr_overlay.py:116, smm_g = 1-(1-cpr_g/100)^(1/12)) invert
     cpr_blend_t EXACTLY back to smm_blend_t — gate G2 asserts it at 1e-12.
     The single call with share 0.337 then delivers exactly
         (1 - 0.337)*CPR_m + 0.231*S_2022 + 0.106*S_pre2017
     in SMM-weighted terms, the face-share-correct object.
  3. Both legs at floor 4.991% (the off-window / headline floor): central
     p_q 6.5 and null p_q 0, the committed floor_form_offwindow parquets,
     unmodified.  marginal = central - null, reported on the shared basis
     with ginnie_cpr_overlay's committed constants
     (NETTING_B 69.56220187263008, BENCHMARK_B 764.7482532227002); netting
     cancels in the marginal, so the marginal is basis-invariant.
  4. PLACEBO (mandatory, mirroring the Ginnie design's gse_placebo).  The
     same overlay at the same 0.337 share, scored with the SAMPLED 2017-2021
     observed series.  The sampled segment IS the estimation universe, so the
     placebo carries only the common observed-series-vs-model component
     (full-universe-vs-SOMA composition + model level calibration).
         vintage_specific_component_pp = primary_marginal_pp - placebo_marginal_pp
     the exact analogue of ginnie_specific_marginal_component_pp (0.00212pp).

WHY THE MARGINAL SHOULD SIMPLY SCALE.  The SAME series is applied to BOTH
legs, so the overlaid share contributes identically in each and cancels in
the difference.  The identified marginal is therefore confined to the
retained in-window-vintage face share.  The Ginnie run is the template's own
validation: realized marginal_scale_vs_conventional 0.7975182199226121
against a nominal conventional share of 1 - 0.204 = 0.796.

=======================================================================
BLOCKING PRE-START INPUT CHECK (before the macro fetch, before anything)
=======================================================================
Required and gitignored — absent from a fresh worktree, present in the main
checkout; they were staged into this worktree:
  data/floor_form_offwindow/microsim_max_floor4.991pct_pq{6.5,0}.parquet
      (.gitignore:70)
  data/fannie_quarters/cells_FNMA{2017Q1..2022Q4}.parquet  (24) + manifest.json
  data/cohort_month_panel_fannie.parquet
      (Fannie block, .gitignore:55-59 — LICENSE prohibits redistribution)
Required and committed:
  data/oos_identification_results.json      (G1/G6 anchors)
  data/fannie_replication_results.json      (G4 universe tie)
  data/ginnie_bound.json                    (G7 sensitivity 82.8 $B/pp)
If ANY is missing: write status "INPUT_MISSING", STOP, exit nonzero.  Do NOT
substitute the committed microsim_results*.parquet — those are the IN-SAMPLE
legs (floor 4.0%), a different cell entirely.

=======================================================================
GATES (blocking; artifact with results only if all pass, else a GATE_FAILURE
artifact and a nonzero exit)
=======================================================================
G1 own-series identity — overlaying each 4.991% leg with its OWN annualized
   CPR series must reproduce that leg's committed oos_identification value
   (central $767.5264524B, null $724.9180586B) to 1e-9 $B.  This is
   ginnie_overlay_offwindow.py's own G1 and its own tolerance; own_series()
   and shared() are IMPORTED from that module so the driver is mirrored
   literally rather than re-typed.  The identity holds for any share (when
   smm_g == smm_model, delta == 0 and the speed line is a no-op), and it is
   run here at THIS run's share (0.337) so the share wiring is under test.
   Targets are read from the committed artifact, not from the spec's printed
   7-decimal roundings — a 1e-9 gate against a rounded literal would fail on
   arithmetic that is in fact exact; the roundings are separately asserted as
   a display check.
G2 blend inversion — max|overlay_leg's smm_g - smm_blend| < 1e-12, computed
   by mirroring ginnie_cpr_overlay.py:116 on the series this run passes in
   (overlay_leg does not return smm_g and is MUST-NOT-CHANGE).  Checked for
   the blend AND the placebo series.
G3 segment pooled window CPRs from the cells, <= 1e-6 pp:
   2022 4.475590534559171%, pre-2017 5.264339724557043%,
   sampled 4.302657826519651%   (vintage_residual_bound_results.json).
   Plus month coverage: every segment 42 months, index identical to the
   simulation legs' period index (overlay_leg's reindex would otherwise
   silently produce NaN and trip its own assert).
G4 cell integrity (vintage_residual_bound's G2, exact) — 24 cell files and
   24 manifest tags FNMA2017Q1..FNMA2022Q4, per-file rows == manifest
   cells_rows, manifest staged totals 17,606,999 loans / 825,814,383 rows
   (tied to the committed fannie_replication_results.json universe block),
   observed vintage range within [2010, 2022].  Plus the panel
   reconciliation that gives cohort_month_panel_fannie.parquet — named a
   blocking input by the spec — its stated purpose: the cells' 2017-2021
   QT-window exposure_upb / prepaid_upb sums must match the committed
   combined panel to rel 1e-9 and loan_count exactly (vintage_residual_bound
   G1, observed there at ~5e-16).
G5 shares — wal_table.VINTAGE_SHARES["2022"/"pre2017"] == (0.231, 0.106)
   exactly, combined == 0.337 and retained == 0.663 exactly (both hold in
   IEEE double: 0.231 + 0.106 == 0.337 and 1.0 - 0.337 == 0.663).
G6 conventional off-window baseline, 1e-9 — central 91.26719121391939%,
   null 85.69563303100965%, marginal 5.57155818290974pp, rebuilt from the
   oos artifact through shared().
G7 level-bound consistency, 0.01 $B —
   0.231*d_2022 + 0.106*d_pre2017 = +0.1419pp, x82.8 = $11.75B, the committed
   vintage residual bound; the sensitivity is read from ginnie_bound.json and
   tied to 82.8.  Both per-leg differentials must be POSITIVE: the overlay
   must agree in SIGN with the level bound (out-of-window vintages prepaid
   FASTER, 4.4756% and 5.2643% vs 4.3027%).

=======================================================================
PRE-COMMITTED EXPECTATION (fixed ex ante; no discretion after the run)
=======================================================================
Nominal retained share 1 - 0.337 = 0.663.  By the Ginnie precedent:
    marginal_scale_vs_conventional in [0.655, 0.672]
    marginal = 5.5716 x 0.663 ~ +3.69pp ($28.25B), range +3.64 to +3.75pp
INVARIANCE (the Ginnie run's strongest property, realized there as a
ginnie_specific component of just 0.0021pp): the scale factor must be
near-identical across the primary and placebo variants.  A spread above 0.01
is a wiring alarm, not a finding.
The two BRANCH-BINDING conditions are exactly the spec's: scale in band, and
variant spread <= 0.01.  The +3.64/+3.75pp window is implied by the band
(0.655 x 5.5716 = 3.650; 0.672 x 5.5716 = 3.744) and is reported, not
separately gated.

=======================================================================
LANDING (per branch; the tex strings are pre-committed here and emitted into
the artifact — this script performs NO .tex edit)
=======================================================================
PASS (gates hold, scale in [0.655, 0.672], variant-invariant within 0.01):
  * tab:assembly (tex 313-334) gains
      "Vintage overlay at the corrected floor | $+3.7$ | below |
       change of estimand (re-scoping), not a correction"
    and the EXISTING Ginnie row is relabelled the same way
      "Ginnie overlay at the corrected floor | $+4.4$ | below |
       change of estimand, not a correction"
    Both rows measure a RE-SCOPED estimand (the marginal confined to a
    sub-book), not an error in the headline.
  * tex 263 gains the overlay beside the existing $11.7B level bound (clause
    carried verbatim in the artifact's verdict block).
  * NO composed Ginnie x vintage cell is specified or claimed.  Verified at
    paper/v18/revised_paper_v18.tex:1156 (the spec cites 1148; the sentence
    sits at 1156 in the current file): of the 2022 vintage's 23.1% of book
    face, 20.7% is conventional and 2.4% is the Ginnie intersection, so
    vintage and agency marginals cannot be added without double-counting that
    cell; the pre-2017 x Ginnie intersection is not in the committed artifact
    at all.  The artifact
    therefore carries composed_with_ginnie = NOT_COMPUTED with that reason.
    Flag it; do not run it.
OUT-OF-RANGE (scale outside the band, or variant spread > 0.01):
  status "CHECK_FAILURE", NO landing, nonzero exit.  A scale that is not the
  retained share means the overlay is not cancelling in both legs, i.e. the
  construction is not the Ginnie template.  The full artifact is still
  written so the failure is inspectable.
INPUT_MISSING / any gate failure: STOP as above, nothing lands.

The spec's S8 RIDER — the tex-263 "originated near or above prevailing market
rates" wording fix — is unconditional, needs no run, and is NOT this script's
business.  Nothing here asserts or edits it.

=======================================================================
MUST NOT CHANGE
=======================================================================
  * ginnie_cpr_overlay.overlay_leg, NETTING_B, BENCHMARK_B — imported
    unmodified; ginnie_overlay_offwindow.own_series / shared likewise.
  * The committed floor_form_offwindow parquets (read-only) and the 4.991%
    off-window floor.
  * common/qt_window.py's half-open window; config.VINTAGE_YEARS.
  * vintage_residual_bound.py's segmentation and pooled-CPR convention.
  * wal_table.VINTAGE_SHARES.
  * No config.py edit, no .tex edit, no engine run, no RNG (the script is
    seed-free: deterministic arithmetic on committed frames only).

PROVENANCE NOTE (a deliberate, spec-mandated widening).  Unlike
vintage_residual_bound_results.json, which ships window-level headline
statistics only, this artifact carries the 42 monthly segment CPR/SMM series
the spec's Artifact section names.  These are month-by-segment aggregates of
the same kind the manuscript's overlay figures already rest on; NO
per-quarter, per-cell, or loan-level value is emitted.

Run:  cd hazard && python3 vintage_overlay.py    (~seconds plus one macro
      fetch; no engine run)  -> data/vintage_overlay_results.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from config import DATA_DIR, QT_END, QT_START, VINTAGE_YEARS  # noqa: I001
from common.qt_window import expected_qt_active_months  # noqa: E402
from ginnie_cpr_overlay import BENCHMARK_B, NETTING_B, overlay_leg  # noqa: E402
from ginnie_overlay_offwindow import own_series, shared  # noqa: E402
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly  # noqa: E402
from wal_table import VINTAGE_SHARES  # noqa: E402

# ---------------------------------------------------------------- paths ----
IN_DIR = DATA_DIR / "floor_form_offwindow"
CENTRAL_PARQUET = IN_DIR / "microsim_max_floor4.991pct_pq6.5.parquet"
NULL_PARQUET = IN_DIR / "microsim_max_floor4.991pct_pq0.parquet"
QUARTER_DIR = DATA_DIR / "fannie_quarters"
MANIFEST_PATH = QUARTER_DIR / "manifest.json"
PANEL_PATH = DATA_DIR / "cohort_month_panel_fannie.parquet"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
REPLICATION_JSON = DATA_DIR / "fannie_replication_results.json"
GINNIE_BOUND_JSON = DATA_DIR / "ginnie_bound.json"
RESULTS_JSON = DATA_DIR / "vintage_overlay_results.json"

TAGS = [f"FNMA{y}{q}" for y in range(2017, 2023) for q in ("Q1", "Q2", "Q3", "Q4")]

# ------------------------------------------------------------ constants ----
MODE = "vintage_overlay"
SPEC_REF = ("SPEC S8, specs/SPEC_round28_D_F1_I1_I3_J2_S8.md — vintage overlay "
            "analogue: the 33.7% out-of-window vintage face share scored by its "
            "observed Fannie speeds in BOTH 4.991% legs (single blend-in-SMM-space "
            "overlay_leg call), plus the sampled-2017-2021 placebo")
OFF_FLOOR_PCT = 4.991

SHARE_2022 = VINTAGE_SHARES["2022"]        # 0.231 — tex "23.1% of book face"
SHARE_PRE2017 = VINTAGE_SHARES["pre2017"]  # 0.106 — "pre-2017 vintages another 10.6%"
COMBINED_SHARE = SHARE_2022 + SHARE_PRE2017          # 0.337 exactly in IEEE double
RETAINED_SHARE = 1.0 - COMBINED_SHARE                # 0.663 exactly

# G1/G6 display anchors (the spec's printed roundings; the 1e-9 gates run
# against the committed artifact's full-precision values, see header).
G1_CENTRAL_DISPLAY_B = 767.5264524
G1_NULL_DISPLAY_B = 724.9180586
G6_CENTRAL_SHARED_PCT = 91.26719121391939
G6_NULL_SHARED_PCT = 85.69563303100965
G6_MARGINAL_PP = 5.57155818290974

# G3 committed segment CPRs (vintage_residual_bound_results.json)
G3_CPR_2022_PCT = 4.475590534559171
G3_CPR_PRE2017_PCT = 5.264339724557043
G3_CPR_SAMPLED_PCT = 4.302657826519651

# G4 committed universe (fannie_replication_results.json, artifact d8199eb)
G4_STAGED_LOANS = 17_606_999
G4_STAGED_ROWS = 825_814_383
VINTAGE_RANGE = (2010, 2022)

# G7 level-bound crosscheck
SENSITIVITY_B_PER_PP = 82.8          # ginnie_bound.json trapped_sensitivity_b_per_pp
G7_BOUND_B = 11.75                   # committed vintage residual bound

# Ginnie precedent (ginnie_overlay_offwindow_results.json) — diagnostic only
GINNIE_REALIZED_SCALE = 0.7975182199226121
GINNIE_NOMINAL_SHARE = 0.796
GINNIE_SPECIFIC_COMPONENT_PP = 0.0021157340096635835
GINNIE_MARGINAL_PP = 4.443419164229439

# Tolerances
G1_TOL_B = 1e-9
G1_DISPLAY_TOL_B = 5e-8              # the spec's 7-decimal printed roundings
G2_TOL_SMM = 1e-12
G3_TOL_PP = 1e-6
G4_REL_TOL = 1e-9
G6_TOL = 1e-9
G7_TOL_B = 0.01

# Pre-committed expectation
SCALE_BAND = (0.655, 0.672)
VARIANT_INVARIANCE_TOL = 0.01
EXPECTED_MARGINAL_PP_RANGE = (3.64, 3.75)
EXPECTED_MARGINAL_PP_POINT = 3.69
EXPECTED_MARGINAL_B_POINT = 28.25

COMPOSED_WITH_GINNIE = {
    "status": "NOT_COMPUTED",
    "reason": ("agency x vintage cross-tab incomplete: the 2022 x Ginnie "
               "intersection is 2.4pp of book face (tex 1148 per SPEC S8; the "
               "sentence sits at revised_paper_v18.tex:1156) but the pre-2017 "
               "x Ginnie intersection is not in the committed artifact"),
}

SENTENCES = {
    "PASS": (
        "The vintage overlay confines the identified marginal to the "
        "in-window-vintage share: {M:+.2f} points (${B:+.2f}B) against the "
        "conventional off-window {C:+.2f} points, a scale of {S:.4f}x on a "
        "nominal retained face share of 0.663 — pure share scaling, the "
        "vintage counterpart of the Ginnie overlay's {GM:+.2f} points "
        "({GS:.4f}x). The placebo scores {PS:.4f}x (spread {D:.4f}), so the "
        "vintage-specific component is {V:+.4f} points: the overlay is a "
        "change of estimand (re-scoping the marginal onto a sub-book), not a "
        "correction to the headline."
    ),
    "OUT_OF_RANGE": (
        "The vintage overlay's marginal scale is {S:.4f}x (placebo {PS:.4f}x, "
        "spread {D:.4f}) against the pre-committed band "
        "[{L:.3f}, {U:.3f}] and invariance tolerance {T:.2f}. The overlaid "
        "share is therefore not cancelling identically in both legs — the "
        "construction is not the Ginnie template. No landing; status "
        "CHECK_FAILURE, and the marginal {M:+.2f} points is not to be quoted."
    ),
}

TAB_ASSEMBLY_ROW_VINTAGE = ("Vintage overlay at the corrected floor | $+{M:.1f}$ | "
                            "below | change of estimand (re-scoping), not a correction")
TAB_ASSEMBLY_ROW_GINNIE_RELABEL = ("Ginnie overlay at the corrected floor | $+4.4$ | "
                                   "below | change of estimand, not a correction")
TEX263_CLAUSE = (
    "The same template applied as a marginal overlay --- scoring the 33.7\\% "
    "out-of-window vintage share by its observed Fannie speeds in \\emph{{both}} "
    "legs, so it contributes zero marginal --- confines the identified marginal "
    "to the in-window-vintage share: $+{M:.1f}$ points, pure share scaling "
    "(${S:.2f}\\times$), the vintage counterpart of the Ginnie overlay's $+4.4$."
)


# ---------------------------------------------------------------- utils ----
def _json_default(x):
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (pd.Period, pd.Timestamp, Path)):
        return str(x)
    return x


def _write(payload: dict) -> None:
    RESULTS_JSON.write_text(
        json.dumps(payload, indent=1, default=_json_default) + "\n")


def _stop_input_missing(missing: dict, t0: float) -> None:
    _write({"mode": MODE, "status": "INPUT_MISSING", "spec": SPEC_REF,
            "missing": missing,
            "note": ("gitignored inputs (.gitignore:55-59) live in the main "
                     "checkout; run there or stage them first. Do NOT "
                     "substitute the committed microsim_results*.parquet — "
                     "those are the in-sample 4.0% legs, a different cell."),
            "runtime_s": time.perf_counter() - t0})
    print(f"INPUT_MISSING: {missing}")
    raise SystemExit("INPUT_MISSING — required inputs absent; nothing run.")


def _fail_gate(gates: dict, failed: list[str], t0: float) -> None:
    _write({"mode": MODE, "status": "GATE_FAILURE", "spec": SPEC_REF,
            "parity_gates": gates, "parity_gates_all_pass": False,
            "failed": failed, "runtime_s": time.perf_counter() - t0})
    raise SystemExit(f"GATE FAILURE — results not written: {failed}")


def _report(name: str, gate: dict, detail: str) -> None:
    print(f"{name}: {detail}  [{'PASS' if gate['pass'] else 'FAIL'}]")


def pooled_cpr_pct(frame: pl.DataFrame) -> float:
    """Compound-annualized pooled dollar SMM (vintage_residual_bound step 3)."""
    smm = frame["prepaid_upb"].sum() / frame["exposure_upb"].sum()
    return (1.0 - (1.0 - smm) ** 12) * 100.0


def monthly_smm(frame: pl.DataFrame) -> tuple[pd.PeriodIndex, np.ndarray]:
    """Per-month pooled dollar SMM, month-sorted, on a monthly PeriodIndex."""
    m = (frame.group_by("period")
         .agg(pl.col("prepaid_upb").sum(), pl.col("exposure_upb").sum())
         .sort("period"))
    idx = pd.PeriodIndex(pd.to_datetime(m["period"].to_numpy()), freq="M")
    smm = m["prepaid_upb"].to_numpy() / m["exposure_upb"].to_numpy()
    return idx, smm


def smm_to_cpr_pct(smm: np.ndarray) -> np.ndarray:
    """House convention for OBSERVED speeds: compound annualization."""
    return (1.0 - (1.0 - smm) ** 12) * 100.0


def cpr_pct_to_smm(cpr_pct: np.ndarray) -> np.ndarray:
    """Mirror of ginnie_cpr_overlay.py:116 (overlay_leg's own inversion)."""
    return 1.0 - (1.0 - cpr_pct / 100.0) ** (1.0 / 12.0)


# ----------------------------------------------------------------- main ----
def main() -> None:
    t0 = time.perf_counter()

    # === BLOCKING pre-start input check (before the macro fetch) ============
    gitignored = {
        "central_offwindow_parquet": CENTRAL_PARQUET,
        "null_offwindow_parquet": NULL_PARQUET,
        "fannie_quarters_manifest": MANIFEST_PATH,
        "cohort_month_panel_fannie": PANEL_PATH,
    }
    committed = {
        "oos_identification_results": OOS_ARTIFACT,
        "fannie_replication_results": REPLICATION_JSON,
        "ginnie_bound": GINNIE_BOUND_JSON,
    }
    cell_paths = {t: QUARTER_DIR / f"cells_{t}.parquet" for t in TAGS}
    missing = {
        "gitignored_inputs": [k for k, p in gitignored.items() if not p.exists()],
        "committed_artifacts": [k for k, p in committed.items() if not p.exists()],
        "fannie_cells": [t for t, p in cell_paths.items() if not p.exists()],
    }
    if any(missing.values()):
        _stop_input_missing(missing, t0)
    print(f"input check: {len(cell_paths)} Fannie cells, manifest, panel, "
          f"2 off-window legs, 3 committed artifacts — all present")

    gates: dict = {}

    # === G5 shares =========================================================
    g5 = {
        "vintage_2022": {"got": SHARE_2022, "want": 0.231},
        "pre_2017": {"got": SHARE_PRE2017, "want": 0.106},
        "combined": {"got": COMBINED_SHARE, "want": 0.337},
        "retained": {"got": RETAINED_SHARE, "want": 0.663},
        "source": "hazard/wal_table.py VINTAGE_SHARES (SOMA CUSIP tabulation)",
    }
    g5["pass"] = bool(SHARE_2022 == 0.231 and SHARE_PRE2017 == 0.106
                      and COMBINED_SHARE == 0.337 and RETAINED_SHARE == 0.663)
    gates["G5_shares"] = g5
    _report("G5 shares", g5, f"{SHARE_2022}/{SHARE_PRE2017} -> combined "
                             f"{COMBINED_SHARE}, retained {RETAINED_SHARE}")

    # === load cells + manifest; G4 cell integrity ==========================
    manifest = json.loads(MANIFEST_PATH.read_text())
    replication = json.loads(REPLICATION_JSON.read_text())
    frames = {t: pl.read_parquet(p) for t, p in cell_paths.items()}
    cells = pl.concat(list(frames.values()))

    manifest_tags_ok = sorted(manifest.keys()) == sorted(TAGS)
    per_file_ok = all(f.height == manifest.get(t, {}).get("cells_rows")
                      for t, f in frames.items())
    staged_loans = sum(m["staged_loans"] for m in manifest.values())
    staged_rows = sum(m["staged_rows"] for m in manifest.values())
    uni = replication["universe"]
    totals_ok = (staged_loans == G4_STAGED_LOANS == uni["staged_loans_total"]
                 and staged_rows == G4_STAGED_ROWS == uni["staged_rows_total"])
    vmin, vmax = int(cells["vintage"].min()), int(cells["vintage"].max())
    vintage_ok = VINTAGE_RANGE[0] <= vmin and vmax <= VINTAGE_RANGE[1]

    # QT mask (half-open, common/qt_window.py) and the spec's segmentation
    qt = cells.filter((pl.col("period") >= QT_START.to_pydatetime())
                      & (pl.col("period") < QT_END.to_pydatetime()))
    segments = {
        "vintage_2022": qt.filter(pl.col("vintage") == 2022),
        "pre_2017": qt.filter(pl.col("vintage") <= 2016),
        "sampled_2017_2021": qt.filter(pl.col("vintage").is_in(list(VINTAGE_YEARS))),
    }

    # panel reconciliation — the stated purpose of cohort_month_panel_fannie
    panel = pl.read_parquet(PANEL_PATH)
    panel_qt = panel.filter((pl.col("period") >= QT_START.to_pydatetime())
                            & (pl.col("period") < QT_END.to_pydatetime()))
    recon = {}
    sampled = segments["sampled_2017_2021"]
    for col in ("exposure_upb", "prepaid_upb"):
        got, want = float(sampled[col].sum()), float(panel_qt[col].sum())
        recon[col] = {"got": got, "want": want,
                      "rel_diff": abs(got - want) / abs(want),
                      "pass": abs(got - want) <= G4_REL_TOL * abs(want)}
    lc_got, lc_want = int(sampled["loan_count"].sum()), int(panel_qt["loan_count"].sum())
    recon["loan_count"] = {"got": lc_got, "want": lc_want, "pass": lc_got == lc_want}
    recon["pass"] = all(v["pass"] for v in recon.values() if isinstance(v, dict))

    g4 = {
        "files_present": len(frames), "files_expected": len(TAGS),
        "manifest_tags_match_spec": manifest_tags_ok,
        "per_file_rows_match_manifest": per_file_ok,
        "cells_rows_total": int(cells.height),
        "staged_loans_total": {"got": staged_loans, "want": G4_STAGED_LOANS,
                               "committed": uni["staged_loans_total"]},
        "staged_rows_total": {"got": staged_rows, "want": G4_STAGED_ROWS,
                              "committed": uni["staged_rows_total"]},
        "committed_universe_tie": totals_ok,
        "vintage_range": [vmin, vmax], "vintage_range_ok": vintage_ok,
        "panel_reconciliation": recon, "rel_tol": G4_REL_TOL,
    }
    g4["pass"] = bool(len(frames) == len(TAGS) and manifest_tags_ok and per_file_ok
                      and totals_ok and vintage_ok and recon["pass"])
    gates["G4_cell_integrity"] = g4
    _report("G4 cell integrity", g4,
            f"{len(frames)}/{len(TAGS)} cells, rows {int(cells.height):,}, staged "
            f"{staged_loans:,} loans / {staged_rows:,} rows, vintages [{vmin}, {vmax}], "
            f"panel rel {recon['exposure_upb']['rel_diff']:.1e}/"
            f"{recon['prepaid_upb']['rel_diff']:.1e} loan_count {lc_got - lc_want:+d}")

    # === observed series ====================================================
    idx_2022, smm_2022 = monthly_smm(segments["vintage_2022"])
    idx_pre, smm_pre = monthly_smm(segments["pre_2017"])
    idx_smp, smm_smp = monthly_smm(segments["sampled_2017_2021"])

    smm_blend = (SHARE_2022 * smm_2022 + SHARE_PRE2017 * smm_pre) / COMBINED_SHARE
    cpr_blend = smm_to_cpr_pct(smm_blend)

    # === load the legs (needed for the G3 index check) =====================
    central = pd.read_parquet(CENTRAL_PARQUET)
    null = pd.read_parquet(NULL_PARQUET)
    sim_periods = central.index.to_period("M")
    n_months_expected = expected_qt_active_months()  # 42

    # === G3 pooled window CPRs + coverage ==================================
    pooled = {name: pooled_cpr_pct(f) for name, f in segments.items()}
    g3_targets = {"vintage_2022": G3_CPR_2022_PCT, "pre_2017": G3_CPR_PRE2017_PCT,
                  "sampled_2017_2021": G3_CPR_SAMPLED_PCT}
    g3_cpr = {n: {"got": pooled[n], "want": w, "abs_diff_pp": abs(pooled[n] - w),
                  "pass": abs(pooled[n] - w) <= G3_TOL_PP}
              for n, w in g3_targets.items()}
    idx_ok = (len(idx_2022) == n_months_expected
              and idx_2022.equals(idx_pre) and idx_2022.equals(idx_smp)
              and idx_2022.equals(pd.PeriodIndex(sim_periods))
              and len(central) == len(null) == n_months_expected
              and central.index.equals(null.index))
    g3 = {"pooled_cpr_pct": g3_cpr, "tol_pp": G3_TOL_PP,
          "expected_months": n_months_expected,
          "segment_months": {n: int(f["period"].n_unique()) for n, f in segments.items()},
          "series_index_matches_sim_legs": bool(idx_ok),
          "window": {"start": str(QT_START.date()), "end_exclusive": str(QT_END.date()),
                     "source": "common/qt_window.py (half-open, production convention)"}}
    g3["pass"] = bool(all(v["pass"] for v in g3_cpr.values()) and idx_ok)
    gates["G3_segment_cprs"] = g3
    _report("G3 segment CPRs", g3,
            f"2022 {pooled['vintage_2022']:.9f}% pre-2017 {pooled['pre_2017']:.9f}% "
            f"sampled {pooled['sampled_2017_2021']:.9f}% (max diff "
            f"{max(v['abs_diff_pp'] for v in g3_cpr.values()):.2e}pp), "
            f"{n_months_expected}mo index aligned {idx_ok}")

    # === G2 blend inversion ================================================
    cpr_smp = smm_to_cpr_pct(smm_smp)
    inv_blend = float(np.max(np.abs(cpr_pct_to_smm(cpr_blend) - smm_blend)))
    inv_smp = float(np.max(np.abs(cpr_pct_to_smm(cpr_smp) - smm_smp)))
    g2 = {"max_abs_smm_g_minus_smm_blend": inv_blend,
          "max_abs_smm_g_minus_smm_sampled": inv_smp,
          "tol": G2_TOL_SMM,
          "note": ("overlay_leg does not return smm_g and is MUST-NOT-CHANGE; "
                   "ginnie_cpr_overlay.py:116 is mirrored in cpr_pct_to_smm"),
          "pass": bool(inv_blend < G2_TOL_SMM and inv_smp < G2_TOL_SMM)}
    gates["G2_blend_inversion"] = g2
    _report("G2 blend inversion", g2,
            f"blend {inv_blend:.2e} sampled {inv_smp:.2e} (tol {G2_TOL_SMM:.0e})")

    # === G7 level-bound consistency ========================================
    ginnie_bound = json.loads(GINNIE_BOUND_JSON.read_text())
    sensitivity = ginnie_bound["trapped_sensitivity_b_per_pp"]
    d_2022 = pooled["vintage_2022"] - pooled["sampled_2017_2021"]
    d_pre = pooled["pre_2017"] - pooled["sampled_2017_2021"]
    book_err_pp = SHARE_2022 * d_2022 + SHARE_PRE2017 * d_pre
    bound_b = book_err_pp * sensitivity
    signs_ok = bool(d_2022 > 0 and d_pre > 0)
    g7 = {"differential_2022_pp": d_2022, "differential_pre2017_pp": d_pre,
          "book_cpr_error_pp": book_err_pp,
          "sensitivity_b_per_pp": {"got": sensitivity, "want": SENSITIVITY_B_PER_PP,
                                   "source": "ginnie_bound.json"},
          "bound_b": {"got": bound_b, "want": G7_BOUND_B, "tol_b": G7_TOL_B},
          "out_of_window_vintages_faster": signs_ok,
          "pass": bool(sensitivity == SENSITIVITY_B_PER_PP
                       and abs(bound_b - G7_BOUND_B) <= G7_TOL_B and signs_ok)}
    gates["G7_level_bound_consistency"] = g7
    _report("G7 level bound", g7,
            f"d2022 {d_2022:+.6f}pp d_pre2017 {d_pre:+.6f}pp -> e {book_err_pp:+.4f}pp "
            f"x {sensitivity} = ${bound_b:.2f}B (want ${G7_BOUND_B}B +/- {G7_TOL_B})")

    # === macro frame (one fetch, as ginnie_overlay_offwindow does) =========
    oos = json.loads(OOS_ARTIFACT.read_text())
    row = next(r for r in oos["instrument1_marginal_table"]
               if abs(r["floor_annual_cpr_pct"] - OFF_FLOOR_PCT) < 1e-9)
    want_central = row["band"]["6.5"]["central_trapped_b"]
    want_null = row["null_trapped_b"]

    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    # === G1 own-series identity, at THIS run's share =======================
    g1c = overlay_leg(central, empirical, own_series(central), COMBINED_SHARE)
    g1n = overlay_leg(null, empirical, own_series(null), COMBINED_SHARE)
    d_c, d_n = g1c["trapped_b"] - want_central, g1n["trapped_b"] - want_null
    g1 = {"share_used": COMBINED_SHARE,
          "central": {"got": g1c["trapped_b"], "want": want_central, "diff_b": d_c,
                      "spec_display_b": G1_CENTRAL_DISPLAY_B,
                      "display_ok": abs(want_central - G1_CENTRAL_DISPLAY_B) <= G1_DISPLAY_TOL_B},
          "null": {"got": g1n["trapped_b"], "want": want_null, "diff_b": d_n,
                   "spec_display_b": G1_NULL_DISPLAY_B,
                   "display_ok": abs(want_null - G1_NULL_DISPLAY_B) <= G1_DISPLAY_TOL_B},
          "tol_b": G1_TOL_B}
    g1["pass"] = bool(abs(d_c) <= G1_TOL_B and abs(d_n) <= G1_TOL_B
                      and g1["central"]["display_ok"] and g1["null"]["display_ok"])
    gates["G1_own_series_identity"] = g1
    _report("G1 own-series identity", g1,
            f"central diff {d_c:+.2e} null diff {d_n:+.2e} (tol {G1_TOL_B:.0e})")

    # === G6 conventional off-window baseline ===============================
    conv = {"central_shared_pct": shared(want_central),
            "null_shared_pct": shared(want_null),
            "marginal_pp": shared(want_central) - shared(want_null),
            "marginal_b": want_central - want_null}
    g6 = {"central": {"got": conv["central_shared_pct"], "want": G6_CENTRAL_SHARED_PCT},
          "null": {"got": conv["null_shared_pct"], "want": G6_NULL_SHARED_PCT},
          "marginal_pp": {"got": conv["marginal_pp"], "want": G6_MARGINAL_PP},
          "tol": G6_TOL}
    g6["pass"] = bool(abs(conv["central_shared_pct"] - G6_CENTRAL_SHARED_PCT) <= G6_TOL
                      and abs(conv["null_shared_pct"] - G6_NULL_SHARED_PCT) <= G6_TOL
                      and abs(conv["marginal_pp"] - G6_MARGINAL_PP) <= G6_TOL)
    gates["G6_conventional_offwindow"] = g6
    _report("G6 conventional off-window", g6,
            f"central {conv['central_shared_pct']:.9f}% null {conv['null_shared_pct']:.9f}% "
            f"marginal {conv['marginal_pp']:+.9f}pp")

    # === gate disposition ===================================================
    failed = [k for k, v in gates.items() if not v["pass"]]
    gates_all_pass = not failed
    print(f"\nparity gates: {len(gates) - len(failed)}/{len(gates)} PASS")
    if failed:
        _fail_gate(gates, failed, t0)

    # === the overlay ========================================================
    series = {
        "primary": pd.Series(cpr_blend, index=idx_2022),
        "sampled_placebo": pd.Series(cpr_smp, index=idx_smp),
    }

    def run_overlay(ser: pd.Series) -> dict:
        c = overlay_leg(central, empirical, ser, COMBINED_SHARE)
        n = overlay_leg(null, empirical, ser, COMBINED_SHARE)
        marg_b = c["trapped_b"] - n["trapped_b"]
        marg_pp = shared(c["trapped_b"]) - shared(n["trapped_b"])
        return {"central": {**c, "share_pct_shared": shared(c["trapped_b"])},
                "null": {**n, "share_pct_shared": shared(n["trapped_b"])},
                "marginal_b": marg_b, "marginal_pp": marg_pp,
                "marginal_sign_positive": bool(marg_b > 0),
                "scale_vs_conventional": marg_pp / conv["marginal_pp"]}

    overlay = {name: run_overlay(ser) for name, ser in series.items()}
    for name, r in overlay.items():
        print(f"{name:>16}: central {r['central']['share_pct_shared']:6.2f}% shared, "
              f"null {r['null']['share_pct_shared']:6.2f}%, marginal "
              f"{r['marginal_pp']:+5.2f}pp (${r['marginal_b']:+.2f}B), scale "
              f"{r['scale_vs_conventional']:.4f}x")

    primary, placebo = overlay["primary"], overlay["sampled_placebo"]
    scale = primary["scale_vs_conventional"]
    scale_placebo = placebo["scale_vs_conventional"]
    spread = abs(scale - scale_placebo)
    vintage_specific_pp = primary["marginal_pp"] - placebo["marginal_pp"]

    # === pre-committed expectation =========================================
    in_band = bool(SCALE_BAND[0] <= scale <= SCALE_BAND[1])
    invariant = bool(spread <= VARIANT_INVARIANCE_TOL)
    expectation = {
        "scale_band": list(SCALE_BAND),
        "scale_primary": scale, "scale_placebo": scale_placebo,
        "scale_in_band": in_band,
        "variant_spread": spread,
        "variant_invariance_tol": VARIANT_INVARIANCE_TOL,
        "variant_invariant": invariant,
        "nominal_retained_share": RETAINED_SHARE,
        "scale_relative_deviation_vs_retained_pct": (scale / RETAINED_SHARE - 1.0) * 100.0,
        "expected_marginal_pp_range": list(EXPECTED_MARGINAL_PP_RANGE),
        "expected_marginal_pp_point": EXPECTED_MARGINAL_PP_POINT,
        "expected_marginal_b_point": EXPECTED_MARGINAL_B_POINT,
        "marginal_pp_in_expected_range": bool(
            EXPECTED_MARGINAL_PP_RANGE[0] <= primary["marginal_pp"]
            <= EXPECTED_MARGINAL_PP_RANGE[1]),
        "ginnie_precedent": {
            "realized_scale": GINNIE_REALIZED_SCALE,
            "nominal_conventional_share": GINNIE_NOMINAL_SHARE,
            "relative_deviation_pct": (GINNIE_REALIZED_SCALE / GINNIE_NOMINAL_SHARE - 1.0) * 100.0,
            "ginnie_specific_marginal_component_pp": GINNIE_SPECIFIC_COMPONENT_PP,
            "marginal_pp": GINNIE_MARGINAL_PP,
        },
        "note": ("the two BRANCH-BINDING conditions are scale_in_band and "
                 "variant_invariant; the pp range is implied by the band "
                 "(0.655 x 5.5716 = 3.650, 0.672 x 5.5716 = 3.744) and is "
                 "reported, not separately gated"),
        "pass": bool(in_band and invariant),
    }
    print(f"expectation: scale {scale:.4f}x in {list(SCALE_BAND)} -> {in_band}; "
          f"variant spread {spread:.4f} <= {VARIANT_INVARIANCE_TOL} -> {invariant}; "
          f"vintage-specific component {vintage_specific_pp:+.4f}pp  "
          f"[{'PASS' if expectation['pass'] else 'FAIL'}]")

    # === branch =============================================================
    if expectation["pass"]:
        branch, status = "PASS", "OK"
        sentence = SENTENCES["PASS"].format(
            M=primary["marginal_pp"], B=primary["marginal_b"],
            C=conv["marginal_pp"], S=scale, GM=GINNIE_MARGINAL_PP,
            GS=GINNIE_REALIZED_SCALE, PS=scale_placebo, D=spread,
            V=vintage_specific_pp)
        landing = {
            "tab_assembly_new_row": TAB_ASSEMBLY_ROW_VINTAGE.format(M=primary["marginal_pp"]),
            "tab_assembly_ginnie_row_relabel": TAB_ASSEMBLY_ROW_GINNIE_RELABEL,
            "tex263_clause": TEX263_CLAUSE.format(M=primary["marginal_pp"], S=scale),
            "note": ("pre-committed landing text; this script performs NO .tex "
                     "edit. Both rows are a change of estimand (re-scoping the "
                     "marginal onto a sub-book), not a correction."),
        }
    else:
        branch, status = "OUT_OF_RANGE", "CHECK_FAILURE"
        sentence = SENTENCES["OUT_OF_RANGE"].format(
            S=scale, PS=scale_placebo, D=spread, L=SCALE_BAND[0], U=SCALE_BAND[1],
            T=VARIANT_INVARIANCE_TOL, M=primary["marginal_pp"])
        landing = {"note": "no landing under branch OUT-OF-RANGE"}
    print(f"\nbranch {branch} (status {status})\n{sentence}")

    # === artifact ===========================================================
    months = [str(p) for p in idx_2022]
    observed_series = {
        "months": months, "n_months": len(months),
        "convention": ("per month, per segment: SMM_t = sum(prepaid_upb)/"
                       "sum(exposure_upb); CPR_t = (1-(1-SMM_t)^12)*100 — the "
                       "house convention for observed speeds "
                       "(vintage_residual_bound step 3 / ginnie_cpr_overlay)"),
        "cpr_pct": {
            "vintage_2022": smm_to_cpr_pct(smm_2022).tolist(),
            "pre_2017": smm_to_cpr_pct(smm_pre).tolist(),
            "sampled_2017_2021": cpr_smp.tolist(),
            "blend": cpr_blend.tolist(),
        },
        "smm": {
            "vintage_2022": smm_2022.tolist(),
            "pre_2017": smm_pre.tolist(),
            "sampled_2017_2021": smm_smp.tolist(),
            "blend": smm_blend.tolist(),
        },
        "pooled_window_cpr_pct": pooled,
        "blend_formula": ("smm_blend_t = (0.231*smm_2022_t + 0.106*smm_pre2017_t)"
                          "/0.337; cpr_blend_t = (1-(1-smm_blend_t)^12)*100 — ONE "
                          "overlay_leg call at share 0.337; sequential calls are "
                          "forbidden (see module header)"),
    }

    payload = {
        "mode": MODE,
        "status": status,
        "spec": SPEC_REF,
        "floor_annual_cpr_pct": OFF_FLOOR_PCT,
        "shares": {"vintage_2022": SHARE_2022, "pre_2017": SHARE_PRE2017,
                   "combined": COMBINED_SHARE, "retained": RETAINED_SHARE,
                   "source": "hazard/wal_table.py VINTAGE_SHARES"},
        "committed_anchors": {
            "netting_b": NETTING_B, "benchmark_b": BENCHMARK_B,
            "source": "ginnie_cpr_overlay.py:93-94 (imported unmodified)",
            "offwindow_central_trapped_b": want_central,
            "offwindow_null_trapped_b": want_null,
            "offwindow_source": ("oos_identification_results.json "
                                 "instrument1_marginal_table @ floor 4.991%"),
            "sensitivity_b_per_pp": sensitivity,
        },
        "parity_gates": gates,
        "parity_gates_all_pass": gates_all_pass,
        "observed_series": observed_series,
        "series": observed_series,  # spec Artifact name; same object
        "conventional_offwindow": conv,
        "overlay_offwindow": {"primary": primary, "sampled_placebo": placebo},
        "primary": primary,   # task-facing alias of overlay_offwindow.primary
        "placebo": placebo,   # task-facing alias of overlay_offwindow.sampled_placebo
        "marginal_scale_vs_retained": scale,
        "vintage_specific_marginal_component_pp": vintage_specific_pp,
        "vintage_specific_component_pp": vintage_specific_pp,
        "level_bound_crosscheck_b": bound_b,
        "expectation_check": expectation,
        "composed_with_ginnie": COMPOSED_WITH_GINNIE,
        "verdict": {"branch": branch, "sentence": sentence, "landing": landing},
        "caveats": [
            ("Fannie observed speeds proxy the SOMA book's segment behaviour — "
             "the same single-agency-proxy posture as the GMAR overlay and the "
             "Freddie production calibration itself."),
            ("The pre-2017 leg is the seasoned/selected 2-year tail of the 2017+ "
             "acquisition files, not a random draw of pre-2017 originations; the "
             "10.6% face share is applied to it as-is."),
            ("The 2022 leg is a full-year-2022 acquisition speed applied to an "
             "H1-2022-tilted face (Q10 settlement-aware allocation caveat)."),
            ("The vintage face shares span the full book INCLUDING Ginnie "
             "collateral, so this overlay and the Ginnie overlay overlap on "
             "Ginnie's out-of-window vintages; they are not additive — see "
             "composed_with_ginnie."),
            ("This is a change of ESTIMAND (the marginal re-scoped onto the "
             "in-window-vintage sub-book), not a correction to the headline "
             "marginal."),
        ],
        "runtime_s": time.perf_counter() - t0,
    }
    _write(payload)
    print(f"Results saved to {RESULTS_JSON}  ({payload['runtime_s']:.1f}s)")

    if status != "OK":
        raise SystemExit(f"CHECK FAILURE (branch {branch}) — do not build on this: "
                         f"scale {scale:.4f}x, variant spread {spread:.4f}")


if __name__ == "__main__":
    main()
