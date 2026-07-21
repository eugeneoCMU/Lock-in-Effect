#!/usr/bin/env python3
"""
cross_design_reweight.py — the composition component of the cross-design
59.3%: post-stratification of the real-covariate ABM population to the SOMA
book's coupon x vintage mix, scored against the same $764.7B benchmark.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; ex-ante convention
of hazard/floor_form_offwindow.py / abm/dti_threshold_sweep.py).

Referee objection (round 21, panel finding MF-12 CONFIRMED): the cross-design
test's 59.3% (recalibrated real-covariate ABM, cross_design_test.py, quoted in
the abstract) substitutes Freddie-sample draws (sample WAC 3.86%) for the
SOMA-parse draws (book WAC 2.49%) with NO composition reweighting, while
Path B receives exactly that correction (+2.1pp, VII.F full-book
reweighting). The modeled book's coupon/vintage composition therefore drifts
away from the SOMA book the $764.7B benchmark is measured on, and an
unquantified part of 11.9% -> 59.3% is composition, not "real structural
heterogeneity". The manuscript hedges but does not quantify. This script
quantifies the composition component. No new behavioral modeling: the
decision rules, behavioral draws (production seed 42), scoring path, and the
$764.7B benchmark are untouched; only the population's cell weights move.

TARGET SHARES (pinned; the exact SOMA table this run commits to)
  hazard/data/composition_shift_results.json ->
      soma_book.latest.joint_cells_min_share_0p1pct
  — the committed CUSIP-parse joint agency x term x coupon x vintage-group
  table (as-of 2026-07-15), tabulated by hazard/composition_shift.py from the
  same NY Fed SOMA CUSIP endpoint, description-parse regexes, and 0.5pp
  coupon rounding convention the production ABM's fetch_soma_mbs_cohorts
  consumes, and anchor-gated there (its G5) to the frozen manifest's book WAC
  2.49. Filtered to 30yr rows (the cross-design universe: the Freddie sample
  is 30-year fixed), summed over agency, renormalized (30yr mass 90.29% of
  the table; the table itself covers 99.18% of parsed book face — the
  renormalization over the 0.1%-min-share cells is disclosed, not hidden).
  VINTAGE AXIS GRANULARITY (disclosed ex ante): the committed joint table
  carries the five committed vintage GROUPS {pre2017, 2017-19, 2020, 2021,
  2022} (hazard/wal_table.py VINTAGE_SHARES; Table 22), not origination
  years; no year-level joint coupon x vintage table is committed anywhere, so
  the reweight cells are coupon(0.5pp, round(c/0.005)*0.005) x vintage-group.
  Agents map to cells by their real Freddie coupon and vintage year
  (<=2016 -> pre2017; 2017-2019 -> '2017-19'; else the year's own group).

REWEIGHT DESIGN (post-stratification; no re-draw in the primary variant)
  Source shares: agent-count shares of the production 10k draw
  (load_freddie_structural_sample, balance-weighted, seed 42 — agents are
  UPB-representative by construction, so count shares meet the face-value
  targets on the same basis the ABM's count-rate CPR uses).
  FOLD RULE for target cells without sample support (fixed ex ante, mirrors
  fetch_soma_mbs_cohorts' nearest-surviving-bucket fold): a target cell whose
  population cell is empty folds (1) to the nearest SUPPORTED vintage group
  within the same coupon bucket (group-order distance on
  pre2017 < 2017-19 < 2020 < 2021 < 2022; ties to the earlier group), else
  (2) to the nearest supported coupon bucket by |coupon distance| (ties to
  the lower coupon), then rule (1) within it. Folds are logged in the
  artifact. Population cells with zero target mass get weight 0.
  w_i = folded_target(cell_i) / source_count_share(cell_i), normalized;
  weighted CPR = sum(w_i * mover_i) / sum(w_i) at every surface grid point
  (WeightedHousingMarketEngine below; the Danish leg is population-
  independent under the production 'dk_level' anchor and is untouched).
  Scheduled-amortization coupling (stated ex ante): run_variant derives the
  sched series from the population's WAC and mean age; the reweighted
  variants use the importance-WEIGHTED WAC and age (the composition
  correction must propagate to sched exactly as the population does). The
  $764.7B benchmark is sched-invariant by construction (Extension_Delta =
  actual rolloff minus QT target; compute_metrics never routes sched into
  it), so the benchmark cannot move — only the model-side recovery does.
  ESS TRIGGER: if effective sample size (sum w)^2 / sum w^2 < 30% of
  N=10,000, say so and ALSO run the re-draw sensitivity: allocate the 10,000
  agents across folded-target cells (largest-remainder rounding; fold
  evaluated against the FULL 75k sample's support, which is wider than the
  10k draw's), then draw loans within each cell balance-weighted WITH
  replacement, single rng seed 42, cells in sorted order; behavioral draws
  stay the production seed-42 synthetics; aggregation is unweighted.
  PRIMARY ex ante: the IMPORTANCE-WEIGHT variants (deterministic, no new
  draw); the re-draw pair is sensitivity only. Measured at spec time from
  the two committed composition tables: ESS = 1,332 / 10,000 (13.3%), 388
  zero-weight agents, max normalized weight 14.2 — the re-draw sensitivity
  is therefore EXPECTED to run; the primary designation does not move.

VARIANTS (all scored against the same $764.7B benchmark via the production
scoring path of cross_design_test.run_variant: fresh 3,380-point CPR surface
-> fed.load_cpr_surface -> fed.compute_metrics(use_burnout=False,
apply_settlement_lag_kernel=True, sched_smm_override=population sched) ->
fed.export_headline_metrics; caches NEVER consulted — every surface is
rebuilt into data/cross_design_reweight/ this run):
  V1 parity      — committed populations/scales, no reweight: recalibrated
                   (scale 36,085.9375) and frozen (scale 43,882.8125) must
                   reproduce the committed 59.30299434493775% and
                   20.856293209339483% EXACTLY (gate G3, +/-0.01pp).
  V2 reweighted-frozen        — frozen scale 43,882.8125, Freddie-draw
                   population, importance weights to the SOMA mix (weights on
                   agents; no re-draw), recovery recomputed.
  V3 reweighted-recalibrated  — same weighted population, mobility scale
                   RE-DERIVED under the paper's own recalibration rule
                   (III.C: binary-search the mobility scale so the WEIGHTED
                   population hits the 4-5% involuntary floor at 8% market
                   rate, zero velocity, static 7% friction — the rule the
                   paper commits to whenever the population facing the
                   household changes). The new scale is reported.
  V2R / V3R      — re-draw sensitivity pair (frozen scale / re-derived scale
                   on the re-drawn population via the same III.C search),
                   run only if the ESS trigger fires.

DELIVERABLES (fixed ex ante — THE numbers this run exists to produce):
  C_frozen = V2.share - 20.856293209339483  (composition component, frozen)
  C_recal  = V3.share - 59.30299434493775   (composition component, recal)
  and the composition-adjusted cross-design pair (V2.share, V3.share) as the
  numbers that answer "real heterogeneity at SOMA composition".

PARITY GATES (blocking; HALT with a GATE_FAILURE artifact before any
downstream quantity is interpreted):
  G0 committed-state identity:
     a. cross_design_results.json variants reproduce the quoted committed
        values to 1e-9 (scales 36,085.9375 / 43,882.8125; shares
        59.30299434493775 / 20.856293209339483; trapped 453.5186133616682 /
        159.49813800542833; benchmark 764.7482532227002) and its
        preregistration bands == {>50 undercut, [10,35] corroborate} — the
        committed VII.D bands this run's thresholds are keyed to;
     b. production constants: RNG_SEED 42, N_HOUSEHOLDS 10,000, DTI_MAX
        0.43, WAIT_AND_SEE 0.20/0.015; latest_run_manifest run_tag ==
        run-2026-07-05-berger; manifest medians 83,730 / 403,200 pinned as
        calibration inputs (live FRED medians reported, never used);
     c. draw replication: the in-script re-draw of the 10k population (needed
        to carry vintage, which load_freddie_structural_sample drops)
        reproduces the library draw bit-exactly on coupon/loan_age/orig_ltv.
  G1 target-share pin: composition_shift artifact echoes book WAC 2.49 and
     sample WAC 3.864892813333334; the pinned 30yr target table's
     bucket-label WAC reproduces the production multi-vintage 30yr WAC 2.55
     (paper v15r5 L106 / TECHNICAL.md L429) to +/-0.02; 30yr mass >= 0.85 of
     the table.
  G2 scale reproduction (pinned manifest medians): abm.calibrate_mobility_
     scale at the manifest reference cohort (coupon 0.02, 60mo) ==
     43,882.8125 +/- 1e-6; cross_design_test.calibrate_mobility_scale_freddie
     on the production draw == 36,085.9375 +/- 1e-6.
  G3 V1 score parity: recalibrated and frozen shares within +/-0.01pp of the
     committed values (both variants; the ex-ante tolerance of this spec),
     and the benchmark within +/-0.05B of 764.7482532227002 (absorbs only
     upstream FRED/SOMA revision noise; observed HEAD drift is ~0.025B).
  G4 recalibration determinism: every III.C floor search that produces a NEW
     scale (V3; V3R if run) is executed twice end-to-end and must return
     bit-identical scales (the search is seed-deterministic by construction;
     this asserts it).
  G5 floor retention: each re-derived scale's floor CPR at 8% (weighted for
     V3, unweighted for V3R) lies in [4%, 5%] — the III.C discipline itself.

EX-ANTE INTERPRETIVE THRESHOLDS (verbatim; keyed to the committed VII.D
bands: >50% undercuts the paradigm reading, <35% corroborates, between =
ambiguous; applied to V3, the primary composition-adjusted recovery):
  T1: V3 >= 50% -> the undercut verdict survives composition adjustment;
      manuscript quantifies the composition component and keeps VII.D's
      reading, replacing the "isolates real structural heterogeneity"
      sentence with the quantified statement.
  T2: 35% <= V3 < 50% -> the undercut verdict was partly composition:
      VII.D's verdict moves to the pre-committed "ambiguous" band; the
      abstract's 59.3% must carry the composition-adjusted value beside it.
  T3: V3 < 35% -> the undercut was primarily composition; VII.D's conclusion
      reverts to corroborating the paradigm reading, and every site quoting
      59.3% must requalify.
  No further discretion is exercised after the runs.

Output:  abm/data/cross_design_reweight_results.json (+ fresh per-variant
         surface CSVs under abm/data/cross_design_reweight/, regenerable,
         not committed; no committed artifact is modified)
Run:     cd abm && python3 cross_design_reweight.py
Runtime: surface-based scoring, no per-agent monthly simulation — 4 fresh
         3,380-point surface sweeps (6 with the re-draw pair) at minutes per
         sweep (the freeze_sensitivity/dti_threshold_sweep measured scale)
         plus <=5 binary floor searches of <=30 single-point engine
         evaluations each: estimate 20-60 minutes end-to-end, printed at
         start.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import abm_lockin_simulation as abm
import cross_design_test as cdt
import fed_mbs_extension_risk as fed
from freddie_population import (
    LOAN_SAMPLE_PARQUET,
    attach_freddie_covariates,
    load_freddie_structural_sample,
)
from paths import ABM_DIR, LATEST_RUN_MANIFEST, RUNS_DIR

_REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSITION_SHIFT_JSON = (_REPO_ROOT / "hazard" / "data"
                          / "composition_shift_results.json")
CROSS_DESIGN_JSON = ABM_DIR / "data" / "cross_design_results.json"
RESULTS_JSON = ABM_DIR / "data" / "cross_design_reweight_results.json"
OUT_DIR = ABM_DIR / "data" / "cross_design_reweight"

REFERENCE_RUN_TAG = "run-2026-07-05-berger"

# --- committed cross-design values (quoted here ex ante; asserted vs the
# --- committed artifact at runtime to 1e-9, floor_form_offwindow convention)
COMMITTED = {
    "recalibrated": {"mobility_scale": 36085.9375,
                     "trapped_b": 453.5186133616682,
                     "share_pct": 59.30299434493775},
    "frozen": {"mobility_scale": 43882.8125,
               "trapped_b": 159.49813800542833,
               "share_pct": 20.856293209339483},
    "empirical_trapped_b": 764.7482532227002,
}
COMMITTED_PREREG = {"undercuts_paradigm_above_pct": 50.0,
                    "corroborates_band_pct": [10.0, 35.0]}
COMMITTED_BOOK_WAC_PCT = 2.49           # frozen manifest, full 30yr+15yr book
COMMITTED_SAMPLE_WAC_PCT = 3.864892813333334
SOMA_30YR_WAC_ANCHOR_PCT = 2.55         # paper v15r5 L106 / TECHNICAL.md L429

# --- gate tolerances (ex ante) ---------------------------------------------
QUOTE_TOL = 1e-9
PARITY_TOL_PP = 0.01        # G3: V1 share parity, both variants (the spec)
EMPIRICAL_TOL_B = 0.05      # G3: benchmark reproduction
SCALE_TOL = 1e-6            # G2: committed-scale reproduction
WAC_TOL = 0.02              # G1: pinned-table 30yr WAC vs 2.55
MIN_30YR_TABLE_MASS = 0.85  # G1: sanity on the 30yr filter

# --- reweight conventions (ex ante) ----------------------------------------
COUPON_STEP = 0.005                       # 0.5pp cells, the book's convention
VGROUP_ORDER = ("pre2017", "2017-19", "2020", "2021", "2022")
ESS_MIN_FRACTION = 0.30                   # re-draw trigger
PRIMARY_VARIANT = "importance_weights"    # fixed ex ante
REDRAW_SEED = 42

# --- III.C floor-search convention (production anchor semantics) -----------
FLOOR_RATE = 0.08
FLOOR_BAND = (0.04, 0.05)
FLOOR_SEARCH_LO, FLOOR_SEARCH_HI, FLOOR_SEARCH_ITERS = 1_000.0, 500_000.0, 30

# --- ex-ante interpretive thresholds (verbatim, applied to V3) -------------
T1_MIN_PCT = 50.0
T2_MIN_PCT = 35.0
THRESHOLD_TEXT = {
    "T1": ("V3 >= 50% -> the undercut verdict survives composition "
           "adjustment; manuscript quantifies the composition component and "
           "keeps VII.D's reading, replacing the 'isolates real structural "
           "heterogeneity' sentence with the quantified statement."),
    "T2": ("35% <= V3 < 50% -> the undercut verdict was partly composition: "
           "VII.D's verdict moves to the pre-committed 'ambiguous' band; the "
           "abstract's 59.3% must carry the composition-adjusted value "
           "beside it."),
    "T3": ("V3 < 35% -> the undercut was primarily composition; VII.D's "
           "conclusion reverts to corroborating the paradigm reading, and "
           "every site quoting 59.3% must requalify."),
}


# ---------------------------------------------------------------------------
# Gate plumbing (dti_threshold_sweep convention): HALT with a GATE_FAILURE
# artifact before any downstream quantity is produced or interpreted.
# ---------------------------------------------------------------------------
def gate_fail(gate: str, detail: dict) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"status": "GATE_FAILURE", "gate": gate, "detail": detail,
         "generated_utc": datetime.now(timezone.utc).isoformat()},
        indent=2, default=str) + "\n")
    raise SystemExit(f"{gate} FAILURE — run halted before interpretation. "
                     f"Detail written to {RESULTS_JSON}")


def check(gate: str, ok: bool, detail: dict, msg: str) -> None:
    print(f"{gate}: {msg} {'PASS' if ok else 'FAIL'}")
    if not ok:
        gate_fail(gate, detail)


# ---------------------------------------------------------------------------
# Cell machinery
# ---------------------------------------------------------------------------
def coupon_bucket_pct(coupon_decimal: np.ndarray) -> np.ndarray:
    """0.5pp coupon cells, the book's convention: round(c/0.005)*0.005."""
    return np.round(np.round(np.asarray(coupon_decimal, dtype=float)
                             / COUPON_STEP) * COUPON_STEP * 100.0, 2)


def vintage_group(years: np.ndarray) -> np.ndarray:
    y = np.asarray(years, dtype=int)
    out = y.astype(str).astype(object)
    out[y <= 2016] = "pre2017"
    out[(y >= 2017) & (y <= 2019)] = "2017-19"
    return out


def load_target_shares() -> tuple[dict, dict]:
    """Pinned 30yr coupon x vintage-group target shares + provenance echo."""
    art = json.loads(COMPOSITION_SHIFT_JSON.read_text())
    latest = art["soma_book"]["latest"]
    cells = latest["joint_cells_min_share_0p1pct"]
    joint30 = defaultdict(float)
    table_mass = 0.0
    for key, share in cells.items():
        agency, term, cp, vg = key.split("|")
        table_mass += share
        if term == "30yr":
            joint30[(round(float(cp), 2), vg)] += share
    mass30 = sum(joint30.values())
    target = {k: v / mass30 for k, v in joint30.items()}
    wac30 = sum(cp * s for (cp, _), s in target.items())
    provenance = {
        "source": (str(COMPOSITION_SHIFT_JSON.relative_to(_REPO_ROOT))
                   + " -> soma_book.latest.joint_cells_min_share_0p1pct"),
        "book_as_of": latest["as_of"],
        "table_mass_of_parsed_face": table_mass,
        "mass_30yr_of_table": mass30,
        "n_cells_30yr": len(target),
        "target_wac_30yr_pct_bucket_labels": wac30,
        "artifact_committed_book_wac_pct":
            art["committed_anchors"]["book_cohort_wac_pct"],
        "artifact_committed_sample_wac_pct":
            art["committed_anchors"]["sample_wac_pct"],
    }
    return target, provenance


def fold_target(target: dict, supported_cells: set) -> tuple[dict, list]:
    """Ex-ante fold rule: unsupported target cells -> nearest supported cell
    (vintage-group distance within coupon first, then coupon distance)."""
    sup_coupons = sorted({c for c, _ in supported_cells})
    folded = defaultdict(float)
    log = []

    def nearest_cell(cp: float, vg: str) -> tuple:
        candidates = [c for c in sup_coupons
                      if any((c, v) in supported_cells for v in VGROUP_ORDER)]
        c = min(candidates, key=lambda x: (abs(x - cp), x))
        sup_v = [v for v in VGROUP_ORDER if (c, v) in supported_cells]
        gi = VGROUP_ORDER.index(vg)
        v = min(sup_v, key=lambda x: (abs(VGROUP_ORDER.index(x) - gi),
                                      VGROUP_ORDER.index(x)))
        return (c, v)

    for (cp, vg) in sorted(target,
                           key=lambda k: (k[0], VGROUP_ORDER.index(k[1]))):
        mass = target[(cp, vg)]
        if (cp, vg) in supported_cells:
            folded[(cp, vg)] += mass
        else:
            dest = nearest_cell(cp, vg)
            folded[dest] += mass
            log.append({"from": [cp, vg], "to": list(dest),
                        "mass_pct": mass * 100.0})
    return dict(folded), log


def replicate_production_draw(n: int = abm.N_HOUSEHOLDS,
                              seed: int = 42) -> pd.DataFrame:
    """Bit-exact replica of load_freddie_structural_sample that also carries
    vintage (gated bit-equal to the library draw in G0c)."""
    loans = pd.read_parquet(LOAN_SAMPLE_PARQUET)
    rng = np.random.default_rng(seed)
    weights = loans["balance"].clip(lower=1.0).to_numpy()
    weights = weights / weights.sum()
    n = min(n, len(loans))
    idx = rng.choice(len(loans), size=n, replace=False, p=weights)
    sample = loans.iloc[idx].reset_index(drop=True)
    coupon = sample["coupon"].to_numpy(dtype=float)
    coupon = np.where(coupon > 1.0, coupon / 100.0, coupon)
    return pd.DataFrame({
        "coupon": coupon,
        "loan_age": sample["loan_age"].fillna(36).astype(int),
        "orig_ltv": sample["orig_ltv"].fillna(80).astype(float),
        "fico": sample["fico"].fillna(700).astype(float),
        "state": sample.get("property_state", pd.Series(["CA"] * n)),
        "stratum_id": sample["stratum_id"].astype(str),
        "vintage": sample["vintage"].astype(int),
    })


def agent_cells(frame: pd.DataFrame) -> list:
    cb = coupon_bucket_pct(frame["coupon"].to_numpy())
    vg = vintage_group(frame["vintage"].to_numpy())
    return list(zip(cb.tolist(), vg.tolist()))


def importance_weights(frame: pd.DataFrame,
                       target: dict) -> tuple[np.ndarray, dict, list]:
    """Post-stratification weights on the production 10k draw."""
    cells = agent_cells(frame)
    n = len(cells)
    counts = defaultdict(int)
    for c in cells:
        counts[c] += 1
    source = {k: v / n for k, v in counts.items()}
    folded, fold_log = fold_target(target, set(source))
    w = np.array([folded.get(c, 0.0) / source[c] for c in cells], dtype=float)
    wn = w / w.mean()
    ess = float(wn.sum() ** 2 / (wn ** 2).sum())
    diag = {
        "ess": ess,
        "ess_fraction_of_n": ess / n,
        "n_agents": n,
        "n_zero_weight_agents": int((w == 0).sum()),
        "max_normalized_weight": float(wn.max()),
        "weighted_wac_pct": float(
            np.average(frame["coupon"].to_numpy(), weights=w) * 100.0),
        "weighted_mean_loan_age_mo": float(
            np.average(frame["loan_age"].to_numpy(), weights=w)),
        "unweighted_wac_pct": float(frame["coupon"].mean() * 100.0),
        "unweighted_mean_loan_age_mo": float(frame["loan_age"].mean()),
    }
    return w, diag, fold_log


def build_redraw_population(target: dict,
                            n: int = abm.N_HOUSEHOLDS,
                            seed: int = REDRAW_SEED) -> tuple[pd.DataFrame,
                                                              dict]:
    """Re-draw sensitivity: allocate n agents across folded-target cells
    (largest remainder), draw balance-weighted WITH replacement within each
    cell of the FULL 75k sample, single rng, sorted cell order."""
    loans = pd.read_parquet(LOAN_SAMPLE_PARQUET)
    coupon = loans["coupon"].to_numpy(dtype=float)
    coupon = np.where(coupon > 1.0, coupon / 100.0, coupon)
    cb = coupon_bucket_pct(coupon)
    vg = vintage_group(loans["vintage"].to_numpy())
    cell_rows = defaultdict(list)
    for i, key in enumerate(zip(cb.tolist(), vg.tolist())):
        cell_rows[key].append(i)
    folded, fold_log = fold_target(target, set(cell_rows))

    keys = sorted(folded, key=lambda k: (k[0], VGROUP_ORDER.index(k[1])))
    raw = np.array([folded[k] * n for k in keys])
    alloc = np.floor(raw).astype(int)
    remainder = raw - alloc
    short = n - int(alloc.sum())
    for j in sorted(range(len(keys)), key=lambda j: (-remainder[j], j))[:short]:
        alloc[j] += 1

    rng = np.random.default_rng(seed)
    balances = loans["balance"].clip(lower=1.0).to_numpy()
    chosen = []
    for k, cnt in zip(keys, alloc):
        if cnt == 0:
            continue
        rows = np.array(cell_rows[k])
        p = balances[rows] / balances[rows].sum()
        chosen.append(rng.choice(rows, size=cnt, replace=True, p=p))
    chosen = np.concatenate(chosen)
    sample = loans.iloc[chosen].reset_index(drop=True)
    coupon = sample["coupon"].to_numpy(dtype=float)
    coupon = np.where(coupon > 1.0, coupon / 100.0, coupon)
    frame = pd.DataFrame({
        "coupon": coupon,
        "loan_age": sample["loan_age"].fillna(36).astype(int),
        "orig_ltv": sample["orig_ltv"].fillna(80).astype(float),
        "fico": sample["fico"].fillna(700).astype(float),
        "state": sample.get("property_state", pd.Series(["CA"] * n)),
        "stratum_id": sample["stratum_id"].astype(str),
        "vintage": sample["vintage"].astype(int),
    })
    diag = {
        "seed": seed,
        "n_agents": int(len(frame)),
        "n_target_cells": len(keys),
        "wac_pct": float(frame["coupon"].mean() * 100.0),
        "mean_loan_age_mo": float(frame["loan_age"].mean()),
        "fold_log_75k_support": fold_log,
        "allocation": {f"{k[0]}|{k[1]}": int(c)
                       for k, c in zip(keys, alloc) if c > 0},
    }
    return frame, diag


# ---------------------------------------------------------------------------
# Weighted engine: agent-weighted CPR aggregation, decision rules untouched.
# ---------------------------------------------------------------------------
class WeightedHousingMarketEngine(abm.HousingMarketEngine):
    """Production engine with importance-weighted US CPR aggregation.

    Only the aggregation changes: weighted mover share instead of the plain
    count share. The Danish leg under the production 'dk_level' anchor is
    population-independent and delegates to the parent; the 'us_intercept'
    branch (not active in production) is weighted symmetrically.
    """

    _agent_weights = None

    def set_agent_weights(self, weights) -> None:
        w = np.asarray(weights, dtype=float)
        if w.shape != (self.n_households,) or w.min() < 0 or w.sum() <= 0:
            raise ValueError("invalid agent weights")
        self._agent_weights = w / w.sum()

    def _weighted_move_share(self, rate, system_type, friction,
                             rate_velocity) -> float:
        mask = self._movers_mask(rate, system_type, friction, rate_velocity)
        return float(self._agent_weights @ mask)

    def _cpr_vec(self, rate, system_type, friction, rate_velocity) -> float:
        if self._agent_weights is None:
            return super()._cpr_vec(rate, system_type, friction,
                                    rate_velocity)
        if system_type == "US":
            return self._weighted_move_share(rate, "US", friction,
                                             rate_velocity)
        from common.berger_calibration import (
            danish_refi_in_place_cpr_annual,
            get_danish_moving_anchor,
        )
        if get_danish_moving_anchor() == "us_intercept":
            move = self._weighted_move_share(self._cohort_rate, "US",
                                             friction, rate_velocity)
            refi = float(danish_refi_in_place_cpr_annual(
                np.array([self._cohort_rate]), rate,
                np.array([self._cohort_months_elapsed]), regime="US",
                term_months=self._cohort_term_years * 12)[0])
            return 1.0 - (1.0 - move) * (1.0 - refi)
        return super()._cpr_vec(rate, system_type, friction, rate_velocity)


def build_engine(scale: float, income: float, home_value: float,
                 loans: pd.DataFrame,
                 weights: np.ndarray | None = None) -> abm.HousingMarketEngine:
    """Plain engine when weights is None (bit-identical to
    cross_design_test._build_engine); weighted engine otherwise."""
    if weights is None:
        return cdt._build_engine(scale, income, home_value, loans)
    engine = WeightedHousingMarketEngine(
        median_income=income,
        median_home_value=home_value,
        mobility_scale=scale,
    )
    attach_freddie_covariates(engine, loans)
    engine.set_agent_weights(weights)
    return engine


def calibrate_scale(income: float, home_value: float, loans: pd.DataFrame,
                    weights: np.ndarray | None) -> tuple[float, float]:
    """III.C floor search on the (weighted) population: binary-search the
    mobility scale to the 4-5% floor at 8% market rate, zero velocity,
    static friction — calibrate_mobility_scale_freddie semantics with the
    population's own aggregation."""
    target_mid = (FLOOR_BAND[0] + FLOOR_BAND[1]) / 2
    lo, hi = FLOOR_SEARCH_LO, FLOOR_SEARCH_HI
    scale, cpr = abm.MOBILITY_DESIRE_SCALE, float("nan")
    for _ in range(FLOOR_SEARCH_ITERS):
        scale = (lo + hi) / 2
        engine = build_engine(scale, income, home_value, loans, weights)
        cpr = engine.cpr_at(FLOOR_RATE, "US")
        if FLOOR_BAND[0] <= cpr <= FLOOR_BAND[1]:
            break
        if cpr < target_mid:
            lo = scale
        else:
            hi = scale
    return scale, cpr


# ---------------------------------------------------------------------------
# Production scoring path (run_variant's pipeline, caches never consulted)
# ---------------------------------------------------------------------------
def sched_series(index: pd.DatetimeIndex, loans: pd.DataFrame,
                 weights: np.ndarray | None = None) -> pd.Series:
    """_population_sched_series with optional importance weights."""
    wac = float(np.average(loans["coupon"].to_numpy(), weights=weights))
    mean_age = float(np.average(loans["loan_age"].to_numpy(), weights=weights))
    origin = fed.QT_START - pd.DateOffset(months=int(round(mean_age)))
    return fed.scheduled_amortization_series(index, coupon=wac, origin=origin,
                                             term=360)


def build_and_score(name: str, scale: float, income: float, home_value: float,
                    loans: pd.DataFrame, weights: np.ndarray | None,
                    df0: pd.DataFrame, soma_rolloff: pd.Series) -> dict:
    """Fresh surface build (never cached) -> production scoring path."""
    print(f"\n[{name}] Building fresh 3,380-point CPR surface "
          f"(scale {scale:,.4f}, "
          f"{'weighted' if weights is not None else 'unweighted'}) …")
    engine = build_engine(scale, income, home_value, loans, weights)
    surf = engine.build_cpr_surface()
    csv_path = OUT_DIR / f"surface_{name}.csv"
    surf.to_csv(csv_path, index=False)

    surface = fed.load_cpr_surface(csv_path)
    sched = sched_series(df0.index, loans, weights)
    df = fed.compute_metrics(
        df0.copy(),
        surface=surface,
        soma_rolloff=soma_rolloff,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
        sched_smm_override=sched,
    )
    m = fed.export_headline_metrics(df)
    qt = fed.qt_active_frame(df)
    xcorr = fed.cpr_cross_correlation(qt["Empirical_CPR_Pct"],
                                      qt["US_CPR_Pct"])
    best_lag = max(xcorr, key=lambda k: abs(xcorr[k])) if xcorr else 0
    d = m["dollars_b"]
    out = {
        "variant": name,
        "mobility_scale": scale,
        "weighted": weights is not None,
        "trapped_b": d["us_trapped"],
        "share_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "us_cpr_mean_pct": m["cpr_pct"]["us_abm"]["mean"],
        "empirical_cpr_mean_pct": m["cpr_pct"]["empirical"]["mean"],
        "sched_wac_pct": float(
            np.average(loans["coupon"].to_numpy(), weights=weights) * 100.0),
        "sched_mean_age_mo": float(
            np.average(loans["loan_age"].to_numpy(), weights=weights)),
        "cpr_r_lag0": xcorr.get(0),
        "peak_lag": best_lag,
        "peak_lag_r": xcorr.get(best_lag),
    }
    print(f"[{name}] trapped ${out['trapped_b']:.2f}B  "
          f"share {out['share_pct']:.3f}%  "
          f"mean US CPR {out['us_cpr_mean_pct']:.2f}%")
    return out


def classify_v3(share_pct: float) -> tuple[str, str]:
    if share_pct >= T1_MIN_PCT:
        return "T1", THRESHOLD_TEXT["T1"]
    if share_pct >= T2_MIN_PCT:
        return "T2", THRESHOLD_TEXT["T2"]
    return "T3", THRESHOLD_TEXT["T3"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    t0 = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 68)
    print(" CROSS-DESIGN REWEIGHT — composition component of the 59.3%")
    print("=" * 68)
    print("Runtime estimate (printed ex ante): surface-based scoring, no "
          "per-agent\nmonthly simulation. 4 fresh 3,380-point surface sweeps "
          "(6 if the ESS\ntrigger fires, which spec-time measurement says it "
          "will: ESS ~13.3%) at\nminutes per sweep, plus <=5 III.C floor "
          "searches (<=30 single-point engine\nevaluations each, some run "
          "twice for the determinism gate): expect\n~20-60 minutes "
          "end-to-end.\n")

    # =======================================================================
    # G0 — committed-state identity
    # =======================================================================
    cd = json.loads(CROSS_DESIGN_JSON.read_text())
    g0a_deltas = {}
    for var in ("recalibrated", "frozen"):
        for field in ("mobility_scale", "trapped_b", "share_pct"):
            g0a_deltas[f"{var}.{field}"] = abs(
                cd["variants"][var][field] - COMMITTED[var][field])
    g0a_deltas["empirical_trapped_b"] = abs(
        cd["variants"]["recalibrated"]["empirical_trapped_b"]
        - COMMITTED["empirical_trapped_b"])
    prereg_ok = (
        cd["preregistration"]["undercuts_paradigm_above_pct"]
        == COMMITTED_PREREG["undercuts_paradigm_above_pct"]
        and list(cd["preregistration"]["corroborates_band_pct"])
        == COMMITTED_PREREG["corroborates_band_pct"]
    )
    check("G0a_committed_quotes",
          max(g0a_deltas.values()) < QUOTE_TOL and prereg_ok,
          {"deltas": g0a_deltas, "prereg_ok": prereg_ok,
           "artifact": str(CROSS_DESIGN_JSON)},
          "cross_design_results.json reproduces the quoted committed values "
          "and VII.D bands")

    latest = json.loads(LATEST_RUN_MANIFEST.read_text())
    manifest = json.loads(
        (RUNS_DIR / REFERENCE_RUN_TAG / "manifest.json").read_text())
    pipe = manifest["pipeline"]
    g0b_ok = (
        latest.get("run_tag") == REFERENCE_RUN_TAG
        and abm.RNG_SEED == 42
        and abm.N_HOUSEHOLDS == 10000
        and abs(abm.DTI_MAX - 0.43) < 1e-15
        and abs(abm.WAIT_AND_SEE_PROB - 0.20) < 1e-15
        and abs(abm.WAIT_AND_SEE_RATE_THRESHOLD - 0.015) < 1e-15
        and abs(pipe["mobility_scale"]
                - COMMITTED["frozen"]["mobility_scale"]) < QUOTE_TOL
    )
    check("G0b_production_constants", g0b_ok,
          {"latest_tag": latest.get("run_tag"), "rng_seed": abm.RNG_SEED,
           "n_households": abm.N_HOUSEHOLDS, "dti_max": abm.DTI_MAX,
           "manifest_scale": pipe["mobility_scale"]},
          f"constants + manifest tag {REFERENCE_RUN_TAG!r} + frozen scale "
          "cross-check")

    # Calibration inputs pinned to the frozen manifest (dti_sweep convention).
    income = float(pipe["median_income"])
    home_value = float(pipe["median_home_value"])
    man_ref = pipe["reference_cohort"]
    try:
        live_income, live_home = abm.fetch_macro_from_fred()
    except Exception:
        live_income = live_home = None
    print(f"Pinned manifest medians: income ${income:,.0f}, home "
          f"${home_value:,.0f} (live FRED: {live_income}, {live_home}; "
          "reported, never used)")

    print("\nLoading production Freddie draw (library) + vintage replica …")
    loans = load_freddie_structural_sample(abm.N_HOUSEHOLDS)
    replica = replicate_production_draw()
    g0c_ok = (
        len(loans) == len(replica) == abm.N_HOUSEHOLDS
        and np.array_equal(loans["coupon"].to_numpy(),
                           replica["coupon"].to_numpy())
        and np.array_equal(loans["loan_age"].to_numpy(),
                           replica["loan_age"].to_numpy())
        and np.array_equal(loans["orig_ltv"].to_numpy(),
                           replica["orig_ltv"].to_numpy())
    )
    check("G0c_draw_replication", g0c_ok,
          {"n_library": len(loans), "n_replica": len(replica)},
          "in-script vintage-carrying draw bit-equals the library draw "
          "(coupon/loan_age/orig_ltv)")

    # =======================================================================
    # G1 — pinned SOMA target shares
    # =======================================================================
    target, provenance = load_target_shares()
    wac30 = provenance["target_wac_30yr_pct_bucket_labels"]
    g1_ok = (
        abs(provenance["artifact_committed_book_wac_pct"]
            - COMMITTED_BOOK_WAC_PCT) < QUOTE_TOL
        and abs(provenance["artifact_committed_sample_wac_pct"]
                - COMMITTED_SAMPLE_WAC_PCT) < QUOTE_TOL
        and abs(wac30 - SOMA_30YR_WAC_ANCHOR_PCT) <= WAC_TOL
        and provenance["mass_30yr_of_table"] >= MIN_30YR_TABLE_MASS
    )
    check("G1_target_share_pin", g1_ok,
          provenance,
          f"pinned 30yr table WAC {wac30:.4f} vs production multi-vintage "
          f"{SOMA_30YR_WAC_ANCHOR_PCT} (+/-{WAC_TOL}); book/sample WAC echoes")

    # =======================================================================
    # G2 — committed-scale reproduction (pinned medians)
    # =======================================================================
    print("\nReproducing the committed frozen scale (production anchor) …")
    frozen_scale = abm.calibrate_mobility_scale(
        income, home_value,
        cohort_rate=float(man_ref["coupon"]),
        cohort_months=int(man_ref["months_elapsed"]),
    )
    print("Reproducing the committed recalibrated scale (freddie anchor) …")
    recal_scale = cdt.calibrate_mobility_scale_freddie(income, home_value,
                                                       loans)
    g2_ok = (
        abs(frozen_scale - COMMITTED["frozen"]["mobility_scale"]) <= SCALE_TOL
        and abs(recal_scale
                - COMMITTED["recalibrated"]["mobility_scale"]) <= SCALE_TOL
    )
    check("G2_scale_reproduction", g2_ok,
          {"frozen": {"got": frozen_scale,
                      "want": COMMITTED["frozen"]["mobility_scale"]},
           "recalibrated": {"got": recal_scale,
                            "want": COMMITTED["recalibrated"]
                            ["mobility_scale"]},
           "pinned_inputs": {"income": income, "home_value": home_value,
                             "ref": man_ref}},
          f"frozen {frozen_scale:,.4f} / recal {recal_scale:,.4f} == "
          "committed 43,882.8125 / 36,085.9375")

    # =======================================================================
    # Importance weights + ESS (reported before any variant runs)
    # =======================================================================
    weights, w_diag, fold_log = importance_weights(replica, target)
    redraw_needed = w_diag["ess_fraction_of_n"] < ESS_MIN_FRACTION
    print(f"\nImportance weights: ESS {w_diag['ess']:.1f} "
          f"({w_diag['ess_fraction_of_n']*100:.2f}% of N) — "
          f"{'EXTREME (< 30%): re-draw sensitivity WILL run' if redraw_needed else 'within the 30% trigger'}")
    print(f"  zero-weight agents {w_diag['n_zero_weight_agents']}, "
          f"max normalized weight {w_diag['max_normalized_weight']:.2f}, "
          f"weighted WAC {w_diag['weighted_wac_pct']:.3f}% "
          f"(unweighted {w_diag['unweighted_wac_pct']:.3f}%)")

    # =======================================================================
    # Macro frames (production fetch path, fetched once, shared)
    # =======================================================================
    print("\nFetching macro data (production fetch path) …")
    df0 = fed.fetch_data()
    soma_rolloff = fed.fetch_soma_mbs_monthly()
    if soma_rolloff is None:
        gate_fail("G3_precondition",
                  {"reason": "SOMA monthly rolloff unavailable; the $764.7B "
                             "benchmark cannot be reproduced"})

    # =======================================================================
    # V1 + G3 — parity: committed populations/scales, fresh evaluation
    # =======================================================================
    print("\n" + "=" * 68)
    print(" V1 — parity (committed scales, no reweight, caches not consulted)")
    print("=" * 68)
    v1_recal = build_and_score("v1_recalibrated", recal_scale, income,
                               home_value, loans, None, df0, soma_rolloff)
    v1_frozen = build_and_score("v1_frozen", frozen_scale, income, home_value,
                                loans, None, df0, soma_rolloff)
    g3_detail = {
        "recal_share_delta_pp": v1_recal["share_pct"]
        - COMMITTED["recalibrated"]["share_pct"],
        "frozen_share_delta_pp": v1_frozen["share_pct"]
        - COMMITTED["frozen"]["share_pct"],
        "recal_trapped_delta_b": v1_recal["trapped_b"]
        - COMMITTED["recalibrated"]["trapped_b"],
        "frozen_trapped_delta_b": v1_frozen["trapped_b"]
        - COMMITTED["frozen"]["trapped_b"],
        "empirical_delta_b": v1_recal["empirical_trapped_b"]
        - COMMITTED["empirical_trapped_b"],
    }
    g3_ok = (
        abs(g3_detail["recal_share_delta_pp"]) <= PARITY_TOL_PP
        and abs(g3_detail["frozen_share_delta_pp"]) <= PARITY_TOL_PP
        and abs(g3_detail["empirical_delta_b"]) <= EMPIRICAL_TOL_B
    )
    check("G3_v1_score_parity", g3_ok,
          {"replayed": {"recalibrated": v1_recal, "frozen": v1_frozen},
           "committed": COMMITTED, "deltas": g3_detail},
          f"recal {v1_recal['share_pct']:.5f}% vs 59.30299 "
          f"(d{g3_detail['recal_share_delta_pp']:+.5f}pp), frozen "
          f"{v1_frozen['share_pct']:.5f}% vs 20.85629 "
          f"(d{g3_detail['frozen_share_delta_pp']:+.5f}pp), benchmark "
          f"d{g3_detail['empirical_delta_b']:+.4f}B")

    # =======================================================================
    # V2 — reweighted-frozen (importance weights, frozen scale)
    # =======================================================================
    print("\n" + "=" * 68)
    print(" V2 — reweighted-frozen (importance weights to the SOMA mix)")
    print("=" * 68)
    v2 = build_and_score("v2_reweighted_frozen", frozen_scale, income,
                         home_value, loans, weights, df0, soma_rolloff)

    # =======================================================================
    # V3 — reweighted-recalibrated (III.C floor search on the weighted pop)
    # =======================================================================
    print("\n" + "=" * 68)
    print(" V3 — reweighted-recalibrated (III.C search on the weighted pop)")
    print("=" * 68)
    v3_scale_1, v3_floor_1 = calibrate_scale(income, home_value, loans,
                                             weights)
    v3_scale_2, v3_floor_2 = calibrate_scale(income, home_value, loans,
                                             weights)
    check("G4_v3_search_determinism",
          v3_scale_1 == v3_scale_2 and v3_floor_1 == v3_floor_2,
          {"run1": [v3_scale_1, v3_floor_1], "run2": [v3_scale_2, v3_floor_2]},
          f"weighted floor search run twice: scale {v3_scale_1:,.4f} "
          f"bit-identical")
    check("G5_v3_floor_retention",
          FLOOR_BAND[0] <= v3_floor_1 <= FLOOR_BAND[1],
          {"floor_cpr": v3_floor_1, "band": list(FLOOR_BAND),
           "scale": v3_scale_1},
          f"weighted floor CPR {v3_floor_1:.4%} in [4%,5%]")
    v3 = build_and_score("v3_reweighted_recalibrated", v3_scale_1, income,
                         home_value, loans, weights, df0, soma_rolloff)
    v3["floor_cpr_at_8pct"] = v3_floor_1

    # =======================================================================
    # Re-draw sensitivity (only if the ESS trigger fired; never primary)
    # =======================================================================
    v2r = v3r = None
    redraw_diag = None
    if redraw_needed:
        print("\n" + "=" * 68)
        print(" V2R/V3R — re-draw sensitivity (ESS trigger fired)")
        print("=" * 68)
        redraw_loans, redraw_diag = build_redraw_population(target)
        v2r = build_and_score("v2r_redraw_frozen", frozen_scale, income,
                              home_value, redraw_loans, None, df0,
                              soma_rolloff)
        v3r_scale_1 = cdt.calibrate_mobility_scale_freddie(income, home_value,
                                                           redraw_loans)
        v3r_scale_2 = cdt.calibrate_mobility_scale_freddie(income, home_value,
                                                           redraw_loans)
        check("G4_v3r_search_determinism", v3r_scale_1 == v3r_scale_2,
              {"run1": v3r_scale_1, "run2": v3r_scale_2},
              f"re-draw floor search run twice: scale {v3r_scale_1:,.4f} "
              "bit-identical")
        v3r_engine = build_engine(v3r_scale_1, income, home_value,
                                  redraw_loans, None)
        v3r_floor = v3r_engine.cpr_at(FLOOR_RATE, "US")
        check("G5_v3r_floor_retention",
              FLOOR_BAND[0] <= v3r_floor <= FLOOR_BAND[1],
              {"floor_cpr": v3r_floor, "band": list(FLOOR_BAND),
               "scale": v3r_scale_1},
              f"re-draw floor CPR {v3r_floor:.4%} in [4%,5%]")
        v3r = build_and_score("v3r_redraw_recalibrated", v3r_scale_1, income,
                              home_value, redraw_loans, None, df0,
                              soma_rolloff)
        v3r["floor_cpr_at_8pct"] = v3r_floor

    # =======================================================================
    # Deliverables + ex-ante threshold verdict (no further discretion)
    # =======================================================================
    c_frozen = v2["share_pct"] - COMMITTED["frozen"]["share_pct"]
    c_recal = v3["share_pct"] - COMMITTED["recalibrated"]["share_pct"]
    band, verdict = classify_v3(v3["share_pct"])
    runtime_s = time.perf_counter() - t0

    report = {
        "mode": "cross_design_reweight",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "spec": (
            "MF-12 composition component of the cross-design 59.3%: "
            "post-stratification of the real-covariate ABM population to the "
            "pinned SOMA 30yr coupon(0.5pp) x vintage-group mix "
            "(composition_shift_results.json soma_book.latest joint cells); "
            "V1 parity +/-0.01pp to committed 59.30299/20.85629; V2 frozen "
            "scale + importance weights; V3 III.C-recalibrated scale on the "
            "weighted population; re-draw sensitivity iff ESS<30%N; primary "
            "= importance weights ex ante; thresholds T1/T2/T3 on V3 keyed "
            "to the committed VII.D bands (>50 undercut / <35 corroborate); "
            "same $764.7B benchmark (sched-invariant by construction); no "
            "new behavioral modeling; no committed artifact modified"
        ),
        "pinned": {
            "target_shares": provenance,
            "committed_cross_design": COMMITTED,
            "committed_prereg_bands": COMMITTED_PREREG,
            "reference_run_tag": REFERENCE_RUN_TAG,
            "manifest_medians": {"income": income, "home_value": home_value},
            "live_fred_medians_reported_only": [live_income, live_home],
            "soma_30yr_wac_anchor_pct": SOMA_30YR_WAC_ANCHOR_PCT,
        },
        "target_shares_30yr": {f"{k[0]}|{k[1]}": v
                               for k, v in sorted(target.items())},
        "importance_weights": {**w_diag,
                               "fold_log_10k_support": fold_log,
                               "ess_trigger_fired": bool(redraw_needed),
                               "ess_min_fraction": ESS_MIN_FRACTION},
        "primary_variant": PRIMARY_VARIANT,
        "variants": {
            "v1_recalibrated": v1_recal,
            "v1_frozen": v1_frozen,
            "v2_reweighted_frozen": v2,
            "v3_reweighted_recalibrated": v3,
            **({"v2r_redraw_frozen": v2r,
                "v3r_redraw_recalibrated": v3r} if redraw_needed else {}),
        },
        "redraw_population": redraw_diag,
        "v3_recalibrated_scale": v3_scale_1,
        "composition_components_pp": {
            "c_frozen": c_frozen,
            "c_recal": c_recal,
        },
        "composition_adjusted_pair_pct": {
            "frozen": v2["share_pct"],
            "recalibrated": v3["share_pct"],
        },
        "interpretive_threshold": {
            "applied_to": "v3_reweighted_recalibrated.share_pct",
            "band": band,
            "verdict": verdict,
            "thresholds": THRESHOLD_TEXT,
        },
        "runtime_s": runtime_s,
    }
    RESULTS_JSON.write_text(json.dumps(
        report, indent=2,
        default=lambda x: float(x) if hasattr(x, "item") else str(x)) + "\n")

    print("\n" + "=" * 68)
    print(" CROSS-DESIGN REWEIGHT — RESULTS")
    print("=" * 68)
    print(f" Benchmark (unchanged): "
          f"${v1_recal['empirical_trapped_b']:.1f}B")
    print(f" V1 parity: recal {v1_recal['share_pct']:.3f}% "
          f"(committed 59.303), frozen {v1_frozen['share_pct']:.3f}% "
          f"(committed 20.856)")
    print(f" V2 reweighted-frozen:        ${v2['trapped_b']:.1f}B "
          f"({v2['share_pct']:.2f}%)   C_frozen {c_frozen:+.2f}pp")
    print(f" V3 reweighted-recalibrated:  ${v3['trapped_b']:.1f}B "
          f"({v3['share_pct']:.2f}%)   C_recal  {c_recal:+.2f}pp "
          f"(scale {v3_scale_1:,.4f})")
    if redraw_needed:
        print(f" V2R re-draw (sensitivity):   ${v2r['trapped_b']:.1f}B "
              f"({v2r['share_pct']:.2f}%)")
        print(f" V3R re-draw (sensitivity):   ${v3r['trapped_b']:.1f}B "
              f"({v3r['share_pct']:.2f}%)")
    print(f"\n verdict [{band}]: {verdict}")
    print(f" runtime {runtime_s:,.0f}s   report saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
