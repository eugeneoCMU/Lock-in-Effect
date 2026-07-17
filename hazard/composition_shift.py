#!/usr/bin/env python3
"""
Round-17 R17-B: formal covariate-shift / composition comparison — estimation
sample(s) vs the SOMA book (referee Q1, 4th recurrence; roadmap gate #38).

SPEC (committed before execution; metric, tolerances, contingencies, and
interpretation fixed ex ante in this header)
-----------------------------------------------------------------------------
PURPOSE
  The reviewer asks for "a formal covariate-shift analysis ... by coupon,
  vintage, geography, loan size, product mix" between the Freddie estimation
  sample and the Fed's SOMA MBS book, and for quantified residual overlay
  uncertainty.  The residual-uncertainty half is ALREADY at HEAD as five
  same-signed quantified layers (coupon ~2pp reweighting, agency static
  $20-47B + dynamic +$38.5B overlay, Fannie replication +8.68pp, vintage
  $11.75B) — this run adds the missing EXHIBIT: one side-by-side composition
  table with a pre-committed shift metric on every dimension both sides
  carry, the on-disk Freddie-vs-Fannie substitute on the dimensions the book
  cannot supply, and a per-dimension consequence column pointing at the
  committed bounds.  Nothing here can move a headline: shift size gates
  nothing; large shift on coupon/vintage/agency is the EXPECTED outcome the
  paper already discloses in prose (WAC 3.9 vs 2.49; 66.2% vintage coverage;
  20.4% Ginnie) — the run formalizes it, it does not discover it.

INPUTS
  Committed, on disk:
    data/loan_sample.parquet            Freddie 75,000 x 14 estimation sample
    data/cohort_month_panel.parquet     Freddie universe cohort-month panel
                                        (22,709 cells; exposure_upb)
    data/full_book_weighting_results.json, data/ginnie_bound.json,
    data/ginnie_cpr_overlay_results.json,
    data/vintage_residual_bound_results.json,
    data/fannie_replication_results.json,
    data/expectation_benchmark_results.json
                                        committed anchors quoted in the
                                        consequence map (G4 parity ties)
    hazard/wal_table.py VINTAGE_SHARES  SOMA CUSIP tabulation face shares
                                        (Table 6 note): 2022 .231 / 2021 .439
                                        / 2020 .163 / 2017-19 .060 /
                                        pre2017 .106  (sum .999)
  Local-only (gitignored; aggregates-only license posture as ratified for
  fannie_replication.py):
    data/loan_sample_fannie.parquet     Fannie 75,000 x 14 sample
    data/fannie_quarters/pool_FNMA{2017Q1..2022Q4}.parquet
                                        24 files, 267,996 loan rows with
                                        property_state and orig_upb
    data/fannie_quarters/manifest.json  per-quarter pool_rows tie
  Live network (REQUIRED; no offline snapshot of SOMA holdings exists in the
  repo — the run ABORTS nonzero if the fetch fails, no cached fallback):
    NY Fed markets API, the SAME endpoints the committed cohort parser uses
    (abm/fed_mbs_extension_risk.py: SOMA_LATEST_DATE_URL, SOMA_CUSIP_URL),
    plus the documented sibling endpoint
    https://markets.newyorkfed.org/api/soma/asofdates/list.json
    for the June-2022 as-of contingency below.  fetch_soma_mbs_cohorts is
    IMPORTED (not reimplemented) for the anchor-gated cohort WAC; the joint
    agency x term x coupon x vintage grid is tabulated in THIS script from
    the raw CUSIP rows using the module's exact parse conventions
    (securityDescription regexes, maturity-minus-term origin back-derivation,
    0.5pp coupon rounding).  No FRED call is made; FRED_API_KEY must still
    resolve because hazard/config.py and the abm module resolve it at import
    (house convention).

AS-OF HANDLING (contingency pre-committed, not improvised)
  The committed marginal anchors (cohort WAC 2.49 = abm/data/
  latest_run_manifest.json cohort_wac_pct; GNMA 20.4% vs UMBS 79.6% and term
  split 30yr 90.7% / 15yr 9.1% / other 0.2% = TECHNICAL.md ~L1552-1554;
  VINTAGE_SHARES = wal_table.py) were tabulated from the LATEST served
  as-of at the 2026-07-05 production freeze.  Therefore:
  (a) PRIMARY book grid = the latest served as-of at run time, anchor-gated
      (G5) with the drift tolerances below.  The book only runs off (no
      purchases), so composition drifts slowly; tolerances are sized ex ante
      to cover several months of differential runoff.
  (b) JUNE-2022 CONTINGENCY: the run queries asofdates/list.json and, if any
      as-of date in [2022-06-01, 2022-06-30] is served, fetches the LATEST
      such date and tabulates the same grid as a SECONDARY, NON-GATING block
      (soma_book.asof_june_2022) subject only to loose sanity screens
      (total MBS face in [$1T, $4T]; GNMA share in [0.05, 0.35]; parse
      coverage >= 0.90) — it is reported, never gated against the latest-book
      anchors, because the June-2022 book (H2-2022 settlements still
      arriving) can legitimately differ from them.
  (c) If no June-2022 as-of is served (or the list endpoint fails), the
      artifact DISCLOSES that (as_of.june_2022_served = false + provenance
      note) and the committed VINTAGE_SHARES / WAC 2.49 anchors stand as the
      June-2022 reference marginals (soma_book.reference_marginals block,
      always present) — both the fetched latest grid and the committed
      reference are reported side by side either way.

PRE-COMMITTED SHIFT METRIC (one primary, stated here, fixed ex ante)
  PRIMARY (per the roadmap's option B): per-bucket share difference in
  percentage points (the tex-table column) PLUS one Population Stability
  Index per dimension, PSI = sum_k (p_k - q_k) * ln(p_k / q_k) with an
  epsilon floor of 1e-6 on empty buckets over the union support.  Reading
  bands fixed ex ante at the standard cutoffs: PSI < 0.10 negligible,
  0.10-0.25 moderate, >= 0.25 large.
  SECONDARY (reported, never primary): total variation distance
  TV = 0.5 * sum_k |p_k - q_k| — bounded under structural zeros.
  DISCLOSED DEGENERACY: where the sample has structural zero mass on book
  support (vintage: no 2022 / pre-2017; agency: no GNMA), PSI inflates
  mechanically via the epsilon floor; those dimensions are flagged
  support_mismatch = true and the OUT-OF-SUPPORT BOOK MASS in pp is the
  number the tex table prints (e.g. 23.1 + 10.6 = 33.7pp on vintage), with
  the PSI carried alongside as-is.
  Scalar complement on coupon only: the committed WAC pair (sample 3.86 vs
  book cohort 2.49, in pct) restated as a difference in pct-pts.

DIMENSIONS AND SIDES (weighting conventions fixed ex ante)
  Sample-vs-book (dimensions the CUSIP level carries):
    coupon   PRIMARY Freddie side = universe panel June-2022 exposure_upb
             shares (period == 2022-06-01; the estimation universe at the
             QT start), 0.5pp buckets (the panel's own ingest bucketing);
             secondary variant = 75k-sample orig-UPB-weighted shares.
             Book side = latest-as-of face shares over parseable 30yr+15yr
             rows, round(coupon/0.005)*0.005 buckets (the committed
             parser's own convention).
    vintage  same Freddie sides mapped to the five VINTAGE_SHARES groups
             (2022 / 2021 / 2020 / 2017-19 / pre2017; sample mass in 2022
             and pre2017 is structurally zero — that IS the measured shift);
             book side = fetched latest grid AND the committed reference
             shares, both compared.
    agency   estimation sample = Freddie 100% (by construction); book =
             UMBS / GNMA / other face shares.  Formalizes the disclosed
             20.4pp GNMA non-coverage.  CUSIP-level UMBS does NOT identify
             Fannie vs Freddie — disclosed, so this margin is
             conventional-vs-GNMA only.
    term     BOOK-SIDE ONLY (30yr / 15yr / other face shares).  DEVIATION
             FROM A TWO-SIDED COMPARISON, disclosed ex ante: the committed
             loan samples retain no original_loan_term column (the ingest
             filter keeps amortization_type == FRM only, hazard/ingest.py
             ~L102), so the sample side does not exist on disk; the
             committed ~9.1% 15-year exclusion disclosure (tex L734) is the
             consequence pointer.
  Freddie-vs-Fannie cross-agency substitute (dimensions the book CANNOT
  supply at CUSIP level — geography, loan size, FICO, LTV):
    state          property_state shares (all states; top-10 + HHI + count
                   reported), Freddie 75k sample vs Fannie 75k sample plus
                   the 267,996-row pooled Fannie quarter pools.
    orig_upb       fixed ex-ante buckets: <100k / 100-200k / 200-300k /
                   300-400k / 400-550k / 550-750k / 750k+ (edges in $).
    fico_bucket    the panel's own <680 / 680-740 / 740+ buckets.
    ltv_bucket     the panel's own <=80 / >80 buckets.
    (coupon and vintage-year Freddie-vs-Fannie shares are reported in the
    same block as context, non-decisive.)
    Weighting: PRIMARY = orig-UPB-weighted shares (dollar composition,
    matching the face-share posture of every book margin); count-weighted
    shares reported secondary.  The substitute VERDICT (below) is decided
    on the four substitute dimensions under the primary weighting, sample
    vs sample (75k vs 75k; the pooled quarter pools are reported alongside,
    non-decisive, and are an equal-n-per-quarter draw pooled WITHOUT
    acquisition-volume reweighting — disclosed).

GATES (numbered; each HALTS the run — GATE_FAILURE stub written to the
artifact path, SystemExit nonzero — BEFORE any new quantity is printed.
G1-G4 are local and run first; G5 requires the network fetch and completes
before any composition number is computed or printed.)
  G1 freddie_sample_integrity — loan_sample.parquet exactly 75,000 rows x
     14 columns; vintages within 2017-2021; weight identically 1.0 (sum ==
     75,000); PARITY: unweighted mean coupon x 100 reproduces the committed
     full_book_weighting_results.json sample_wac_pct 3.864892813333334
     to abs 1e-9 (same construction: loans["coupon"].mean() * 100).
  G2 freddie_panel_integrity — cohort_month_panel.parquet exactly 22,709
     rows; the June-2022 snapshot (period == 2022-06-01) is non-empty with
     positive exposure_upb.
  G3 fannie_integrity — loan_sample_fannie.parquet exactly 75,000 rows x 14
     columns, vintages within 2017-2021; exactly the 24 spec pool files
     pool_FNMA{2017Q1..2022Q4} present; each file's row count == its
     manifest pool_rows; total pool rows == 267,996 == the COMMITTED
     fannie_replication_results.json universe.pool_rows_total (ties the
     local pools to the committed run of record); pool vintages within
     2017-2021.
  G4 constants_integrity — every committed value quoted in the consequence
     map / reference marginals equals its committed source (abs tol 1e-9
     unless exact):
       full_book_weighting_results.json: sample_wac_pct 3.864892813333334;
         path_b balance_weighted share_pct 107.0326190295068;
         path_b full_book_weighted share_pct 109.13914436574825
       ginnie_bound.json: ginnie_share_of_soma_face 0.204 (exact);
         bound_b == [20.3, 47.3] (exact)
       ginnie_cpr_overlay_results.json: variants.primary.marginal_pp
         7.335061460712228; variants.primary.central.adjustment_sum_b
         66.27510387196989; variants.gse_placebo.central.adjustment_sum_b
         27.811330250309656 (difference $38.46B = the tex L404 Ginnie-
         specific differential)
       vintage_residual_bound_results.json: results.bound_b
         11.748139002824871; results.bound_pct_of_benchmark
         1.536209981953856
       fannie_replication_results.json: path_b.lockin_marginal_share_pp
         8.682485610390856
       expectation_benchmark_results.json: cap_benchmark_b
         764.7482532227002
       wal_table.VINTAGE_SHARES == {2022: .231, 2021: .439, 2020: .163,
         2017-19: .060, pre2017: .106} exact; sum == 0.999 (tol 1e-12)
  G5 soma_anchor_parity — the latest-as-of fetch must reproduce the
     committed marginals before any composition is printed (tolerances
     absolute, chosen ex ante for slow runoff drift as argued above):
       A1 cohort WAC via the IMPORTED fetch_soma_mbs_cohorts (default
          args), sum(coupon x weight) x 100:      |x - 2.49|  <= 0.05
          (a single returned cohort == the module's silent network
          fallback and is itself a HALT: the fetch did not succeed)
       A2 GNMA face share, all MBS rows:          |x - 0.204| <= 0.010
       A3 term face shares, all MBS rows:         |x30 - 0.907| <= 0.010,
          |x15 - 0.091| <= 0.010, |xother - 0.002| <= 0.005
       A4 vintage-group face shares (parseable 30yr+15yr rows, origin
          back-derived) vs VINTAGE_SHARES:        each |dx|  <= 0.015
       A5 classification coverage: (GNMA + UMBS face) / all-MBS face
          >= 0.98 (the first-token agency rule below must span the book);
          securityDescription parse coverage >= 0.98 of 30yr+15yr face.
     Agency classification rule, fixed ex ante: first whitespace token of
     securityDescription, uppercased — GNMA iff it starts with "GN", UMBS
     iff it equals "UMBS", else "other" (token histogram recorded in the
     artifact diagnostics; A5 catches the rule breaking).

PRE-COMMITTED INTERPRETATION (every outcome has its reading; no post-hoc
reframing)
  Sample-vs-book: whatever PSI / delta values obtain, the reading is FIXED:
  each shifted dimension's headline consequence is the committed bound in
  consequence_map — large shift on coupon / vintage / agency confirms the
  disclosed composition facts and moves nothing; the run has no shift-size
  gate by design.  Per-dimension sentence template, filled at run time:
    "Composition shift on {dim}: PSI {psi} ({band}), max |dshare|
     {max_dpp}pp{oos}. Headline consequence already bounded: {consequence}."
  Freddie-vs-Fannie substitute verdict, decided on the four substitute
  dimensions (state, orig_upb, fico, ltv; primary weighting, sample vs
  sample):
    ALL four PSI < 0.10  -> verdict "cross_agency_stable":
      "The loan-level covariate mix is stable across the two conventional
       universes (all substitute-dimension PSI < 0.10); the Freddie-vs-
       Fannie comparison stands in for the CUSIP-undeliverable book margins
       on geography, loan size, FICO and LTV."
    ANY PSI >= 0.10      -> verdict "cross_agency_divergent_disclosed":
      "Dimensions {list} diverge across agencies (PSI >= 0.10); reported
       as-is. The hazard specification's exposure to loan-level covariates
       remains bracketed by the printed covariate-block sensitivity
       (99.2% / 92.2% shared-basis endpoints, tex L402)."
  Overall verdict string: "composition_shift_formalized_" + ("stable_" or
  "divergent_") + "substitute".

OUTPUT
  data/composition_shift_results.json — headline statistics ONLY: aggregate
  shares, differences, PSI/TV, HHI, counts.  NO loan-level rows; the Fannie
  side ships only bucket-level aggregate shares over >= 75,000-loan
  universes (identical license posture to fannie_replication_results.json,
  ratified).  The SOMA side is public Fed data; its joint grid is carried
  as aggregate face shares (cells >= 0.1% of included face).
  Top-level keys: mode, spec, reviewer_item, as_of, metric,
  committed_anchors, gates, freddie, fannie, soma_book, comparisons,
  disclosed_undeliverable, consequence_map, interpretation, caveats.

WHAT THIS RUN MAY NOT TOUCH
  No engine run, no hazard fit, no scorer, no FRED series fetch, no edit to
  abm/fed_mbs_extension_risk.py, no raw Freddie/Fannie loan file access
  (committed/local parquets only), no loan-level values in the artifact,
  and no headline quantity recomputed — every dollar/pp figure it cites is
  quoted from committed artifacts under G4 parity.

CAVEATS (fixed ex ante; carried in the artifact)
  * Book side is the latest served as-of, runoff-drifted from the June-2022
    reference; committed VINTAGE_SHARES / WAC 2.49 stand as the June-2022
    reference marginals; a served June-2022 as-of is reported alongside,
    non-gating.
  * CUSIP-level UMBS does not identify Fannie vs Freddie; the agency margin
    is conventional-vs-GNMA only.
  * Back-derived vintage = maturity date minus stated term; pool maturity
    conventions (notably GNMA II multi-issuer) can shift a derived origin
    by months around year boundaries.
  * The committed samples carry no term column (FRM-only ingest filter);
    the term margin is book-side only, with tex L734's 9.1% 15-year
    exclusion disclosure as its consequence pointer.
  * Fannie quarter pools are equal-n per-quarter stratified draws pooled
    without acquisition-volume reweighting; they are a composition proxy,
    reported alongside the volume-consistent 75k sample, non-decisive.
  * State / loan-size shares are orig-UPB-weighted primary (dollar
    composition, matching the book's face-share posture); count-weighted
    shares are reported secondary.

Run:  cd hazard && python3 composition_shift.py
      (~1-2 min: two or three NY Fed API calls + pandas/polars aggregation;
      no engine, no FRED series)
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd
import polars as pl

from config import COUPON_STEP, DATA_DIR, LOAN_SAMPLE_PATH, VINTAGE_YEARS
from wal_table import VINTAGE_SHARES  # SOMA CUSIP tabulation (Table 6 note)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ABM_DIR = _REPO_ROOT / "abm"
if str(_ABM_DIR) not in sys.path:
    sys.path.append(str(_ABM_DIR))  # abm has no __init__; module imports "paths"
import fed_mbs_extension_risk as fmer  # noqa: E402  (committed SOMA parser)

PANEL_PATH = DATA_DIR / "cohort_month_panel.parquet"
FANNIE_SAMPLE_PATH = DATA_DIR / "loan_sample_fannie.parquet"
QUARTER_DIR = DATA_DIR / "fannie_quarters"
MANIFEST_PATH = QUARTER_DIR / "manifest.json"
FULL_BOOK_JSON = DATA_DIR / "full_book_weighting_results.json"
GINNIE_BOUND_JSON = DATA_DIR / "ginnie_bound.json"
OVERLAY_JSON = DATA_DIR / "ginnie_cpr_overlay_results.json"
VINTAGE_BOUND_JSON = DATA_DIR / "vintage_residual_bound_results.json"
REPLICATION_JSON = DATA_DIR / "fannie_replication_results.json"
EXPECT_BENCH_JSON = DATA_DIR / "expectation_benchmark_results.json"
RESULTS_JSON = DATA_DIR / "composition_shift_results.json"

TAGS = [f"FNMA{y}{q}" for y in range(2017, 2023) for q in ("Q1", "Q2", "Q3", "Q4")]

# Documented sibling of the committed parser's asofdates/latest.json.
SOMA_ASOFDATES_LIST_URL = "https://markets.newyorkfed.org/api/soma/asofdates/list.json"
JUNE_2022_WINDOW = ("2022-06-01", "2022-06-30")
SNAPSHOT_DATE = pd.Timestamp("2022-06-01")  # panel June-2022 universe snapshot

# ---- committed anchors (quoted, not re-derived; G4 ties them to sources) ----
SAMPLE_WAC_PCT = 3.864892813333334        # full_book_weighting sample_wac_pct
PATH_B_BALANCE_SHARE = 107.0326190295068  # full_book path_b balance share_pct
PATH_B_FULLBOOK_SHARE = 109.13914436574825
GINNIE_SHARE = 0.204                      # ginnie_bound.json
STATIC_GINNIE_BOUND_B = (20.3, 47.3)
OVERLAY_MARGINAL_PP = 7.335061460712228   # overlay variants.primary.marginal_pp
OVERLAY_ADJ_PRIMARY_B = 66.27510387196989
OVERLAY_ADJ_PLACEBO_B = 27.811330250309656
VINTAGE_BOUND_B = 11.748139002824871
VINTAGE_BOUND_PCT = 1.536209981953856
FANNIE_MARGINAL_PP = 8.682485610390856
BENCHMARK_B = 764.7482532227002
POOL_ROWS_TOTAL = 267996
BOOK_WAC_PCT = 2.49                       # abm/data/latest_run_manifest.json
TERM_SHARES_REF = {"30yr": 0.907, "15yr": 0.091, "other": 0.002}  # TECHNICAL ~L1553

# ---- ex-ante tolerances -----------------------------------------------------
G1_WAC_TOL = 1e-9
G4_ABS_TOL = 1e-9
A1_WAC_TOL = 0.05
A2_GNMA_TOL = 0.010
A3_TERM_TOL = {"30yr": 0.010, "15yr": 0.010, "other": 0.005}
A4_VGROUP_TOL = 0.015
A5_MIN_COVERAGE = 0.98
PSI_EPS = 1e-6
PSI_BANDS = ((0.10, "negligible"), (0.25, "moderate"), (float("inf"), "large"))
SUBSTITUTE_PSI_THRESHOLD = 0.10
JOINT_CELL_MIN_SHARE = 0.001
UPB_EDGES = [100_000, 200_000, 300_000, 400_000, 550_000, 750_000]
UPB_LABELS = ["<100k", "100-200k", "200-300k", "300-400k",
              "400-550k", "550-750k", "750k+"]
STATE_TOP_N = 10
# June-2022 contingent block: loose NON-GATING sanity screens only.
JUNE_SANITY_FACE_RANGE = (1.0e12, 4.0e12)
JUNE_SANITY_GNMA_RANGE = (0.05, 0.35)
JUNE_SANITY_MIN_PARSE = 0.90

VGROUP_ORDER = ["pre2017", "2017-19", "2020", "2021", "2022"]

SHIFT_SENTENCE = ("Composition shift on {dim}: PSI {psi:.3f} ({band}), "
                  "max |dshare| {max_dpp:.1f}pp{oos}. Headline consequence "
                  "already bounded: {consequence}")
SUBSTITUTE_SENTENCES = {
    "cross_agency_stable": (
        "The loan-level covariate mix is stable across the two conventional "
        "universes (all substitute-dimension PSI < 0.10); the Freddie-vs-"
        "Fannie comparison stands in for the CUSIP-undeliverable book "
        "margins on geography, loan size, FICO and LTV."
    ),
    "cross_agency_divergent_disclosed": (
        "Dimensions {dims} diverge across agencies (PSI >= 0.10); reported "
        "as-is. The hazard specification's exposure to loan-level covariates "
        "remains bracketed by the printed covariate-block sensitivity "
        "(99.2% / 92.2% shared-basis endpoints, tex L402)."
    ),
}

CONSEQUENCE_MAP = {
    "coupon": ("full-book coupon reweighting: Path B 107.0% -> 109.1% of "
               "benchmark, ~2pp composition effect "
               "(hazard/data/full_book_weighting_results.json; tex "
               "sec:robustness-hybrid ~L650)"),
    "vintage": ("observed-speed residual bound $11.75B = 1.54% of the "
                "$764.7B benchmark, below the static agency bound's lower "
                "edge (hazard/data/vintage_residual_bound_results.json; "
                "tex ~L402)"),
    "agency": ("static Ginnie bound $20.3-47.3B = 2.6-6.2% of benchmark "
               "(hazard/data/ginnie_bound.json; tex ~L402); dynamic GMAR "
               "overlay isolates a Ginnie-specific differential of +$38.46B "
               "= 5.0% inside it (66.275 - 27.811; hazard/data/"
               "ginnie_cpr_overlay_results.json; tex ~L404); cross-agency "
               "Fannie replication reproduces the marginal at +8.68pp vs "
               "Freddie +9.20pp inside the pre-committed envelope "
               "(hazard/data/fannie_replication_results.json; tex ~L406)"),
    "term": ("15-year book (9.1% of face) is excluded from hazard-side "
             "cohort modeling — disclosed at tex ~L734; the ABM leg is "
             "term-aware (30yr+15yr fold-in, TECHNICAL.md)"),
    "geography_loansize_fico_ltv": (
        "book-side undeliverable at CUSIP level (see "
        "disclosed_undeliverable); loan-level covariate exposure is "
        "bracketed by the covariate-block sensitivity endpoints "
        "99.2% / 92.2% shared-basis (tex ~L402)"),
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _fail(gates: dict, msg: str) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"mode": "composition_shift", "status": "GATE_FAILURE",
         "gates": gates, "detail": msg}, indent=2, default=float) + "\n")
    raise SystemExit(f"GATE FAILURE — {msg} (results not written)")


def _fetch_json(url: str, timeout: int) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def psi(p: dict, q: dict, eps: float = PSI_EPS) -> float:
    total = 0.0
    for k in set(p) | set(q):
        a = max(float(p.get(k, 0.0)), eps)
        b = max(float(q.get(k, 0.0)), eps)
        total += (a - b) * math.log(a / b)
    return total


def tv_distance(p: dict, q: dict) -> float:
    return 0.5 * sum(abs(float(p.get(k, 0.0)) - float(q.get(k, 0.0)))
                     for k in set(p) | set(q))


def psi_band(x: float) -> str:
    for cutoff, name in PSI_BANDS:
        if x < cutoff:
            return name
    return "large"


def delta_table(p: dict, q: dict, order=None) -> dict:
    keys = order if order is not None else sorted(set(p) | set(q))
    return {str(k): {"a_pct": float(p.get(k, 0.0)) * 100.0,
                     "b_pct": float(q.get(k, 0.0)) * 100.0,
                     "delta_pp": (float(p.get(k, 0.0))
                                  - float(q.get(k, 0.0))) * 100.0}
            for k in keys}


def max_abs_delta_pp(p: dict, q: dict) -> float:
    return max(abs(float(p.get(k, 0.0)) - float(q.get(k, 0.0))) * 100.0
               for k in set(p) | set(q))


def compare(dim: str, a: dict, b: dict, order=None,
            support_mismatch: bool = False,
            out_of_support_keys=None) -> dict:
    p = psi(a, b)
    out = {
        "psi": p,
        "psi_band": psi_band(p),
        "tv_distance": tv_distance(a, b),
        "max_abs_delta_pp": max_abs_delta_pp(a, b),
        "table": delta_table(a, b, order),
        "support_mismatch": support_mismatch,
    }
    if support_mismatch and out_of_support_keys:
        out["out_of_support_book_mass_pp"] = sum(
            float(b.get(k, 0.0)) for k in out_of_support_keys) * 100.0
    return out


def shares_pl(df: pl.DataFrame, key: str, weight=None) -> dict:
    """Normalized shares over `key`; count-weighted when weight is None."""
    if weight is None:
        g = df.group_by(key).agg(pl.len().alias("w"))
    else:
        g = df.group_by(key).agg(pl.col(weight).sum().alias("w"))
    tot = float(g["w"].sum())
    return {str(k): float(w) / tot
            for k, w in sorted(zip(g[key].to_list(), g["w"].to_list()),
                               key=lambda kv: str(kv[0]))}


def coupon_bucket_expr() -> pl.Expr:
    # identical to hazard/ingest.py _coupon_bucket (panel parity)
    return ((pl.col("coupon") / COUPON_STEP).round(0) * COUPON_STEP)


def coupon_key(bucket: float) -> str:
    return f"{bucket * 100:.1f}"


def coupon_shares_fmt(raw: dict) -> dict:
    return {coupon_key(float(k)): v for k, v in raw.items()}


def upb_bucket_expr() -> pl.Expr:
    """Fixed ex-ante $ edges (UPB_EDGES/UPB_LABELS), explicit and auditable."""
    c = pl.col("orig_upb")
    expr = (pl.when(c < 100_000).then(pl.lit("<100k"))
            .when(c < 200_000).then(pl.lit("100-200k"))
            .when(c < 300_000).then(pl.lit("200-300k"))
            .when(c < 400_000).then(pl.lit("300-400k"))
            .when(c < 550_000).then(pl.lit("400-550k"))
            .when(c < 750_000).then(pl.lit("550-750k"))
            .otherwise(pl.lit("750k+")))
    return expr.alias("upb_bucket")


def vgroup(year: int) -> str:
    if year >= 2022:
        return "2022"
    if year == 2021:
        return "2021"
    if year == 2020:
        return "2020"
    if 2017 <= year <= 2019:
        return "2017-19"
    return "pre2017"


def vgroup_expr() -> pl.Expr:
    y = pl.col("vintage")
    return (pl.when(y >= 2022).then(pl.lit("2022"))
            .when(y == 2021).then(pl.lit("2021"))
            .when(y == 2020).then(pl.lit("2020"))
            .when(y >= 2017).then(pl.lit("2017-19"))
            .otherwise(pl.lit("pre2017"))).alias("vintage_group")


def hhi(share_map: dict) -> float:
    return sum(v * v for v in share_map.values())


def state_block(df: pl.DataFrame) -> dict:
    upb = shares_pl(df, "property_state", "orig_upb")
    cnt = shares_pl(df, "property_state", None)
    top = sorted(upb.items(), key=lambda kv: -kv[1])[:STATE_TOP_N]
    return {
        "n_states": len(upb),
        "hhi_upb_weighted": hhi(upb),
        "top10_upb_weighted_pct": {k: v * 100.0 for k, v in top},
        "shares_upb_weighted": upb,
        "shares_count_weighted": cnt,
    }


def sample_block(df: pl.DataFrame) -> dict:
    df = df.with_columns([coupon_bucket_expr().alias("coupon_bucket"),
                          upb_bucket_expr(), vgroup_expr()])
    return {
        "n_loans": df.height,
        "mean_coupon_pct": float(df["coupon"].mean()) * 100.0,
        "mean_orig_upb": float(df["orig_upb"].mean()),
        "median_orig_upb": float(df["orig_upb"].median()),
        "mean_fico": float(df["fico"].mean()),
        "mean_orig_ltv": float(df["orig_ltv"].mean()),
        "coupon_shares_upb_weighted":
            coupon_shares_fmt(shares_pl(df, "coupon_bucket", "orig_upb")),
        "coupon_shares_count_weighted":
            coupon_shares_fmt(shares_pl(df, "coupon_bucket", None)),
        "vintage_year_shares_upb_weighted": shares_pl(df, "vintage", "orig_upb"),
        "vintage_group_shares_upb_weighted":
            shares_pl(df, "vintage_group", "orig_upb"),
        "fico_shares_upb_weighted": shares_pl(df, "fico_bucket", "orig_upb"),
        "fico_shares_count_weighted": shares_pl(df, "fico_bucket", None),
        "ltv_shares_upb_weighted": shares_pl(df, "ltv_bucket", "orig_upb"),
        "ltv_shares_count_weighted": shares_pl(df, "ltv_bucket", None),
        "upb_bucket_shares_upb_weighted": shares_pl(df, "upb_bucket", "orig_upb"),
        "upb_bucket_shares_count_weighted": shares_pl(df, "upb_bucket", None),
        "state": state_block(df),
    }


# ---------------------------------------------------------------------------
# SOMA book tabulation (parse conventions mirror fed_mbs_extension_risk)
# ---------------------------------------------------------------------------
def classify_agency(desc: str) -> str:
    token = desc.split()[0].upper() if desc and desc.split() else ""
    if token.startswith("GN"):
        return "GNMA"
    if token == "UMBS":
        return "UMBS"
    return "other"


def tabulate_book(holdings: list, as_of: pd.Timestamp) -> dict:
    """Aggregate face shares by agency / term / coupon bucket / vintage group
    plus the joint grid, from raw CUSIP rows.  Regexes, maturity parse, origin
    back-derivation and 0.5pp coupon rounding are the committed parser's own
    conventions (abm/fed_mbs_extension_risk.fetch_soma_mbs_cohorts)."""
    step = COUPON_STEP
    total_face = 0.0
    n_rows = 0
    agency_face: dict = {}
    token_face: dict = {}
    term_face: dict = {}
    term3015_face = 0.0
    included_face = 0.0
    coupon_face: dict = {}
    vyear_face: dict = {}
    vgroup_face: dict = {}
    joint_face: dict = {}
    wac_num = 0.0
    skipped_value_rows = 0

    for row in holdings:
        if row.get("securityType") != "MBS":
            continue
        raw_val = row.get("currentFaceValue")
        if raw_val is None:
            skipped_value_rows += 1
            continue
        value = float(raw_val)
        n_rows += 1
        total_face += value
        desc = row.get("securityDescription", "") or ""
        agency = classify_agency(desc)
        agency_face[agency] = agency_face.get(agency, 0.0) + value
        token = desc.split()[0].upper() if desc.split() else "(empty)"
        token_face[token] = token_face.get(token, 0.0) + value

        term_label = row.get("term")
        term_key = (term_label
                    if term_label in fmer.TERM_MONTHS_BY_LABEL else "other")
        term_face[term_key] = term_face.get(term_key, 0.0) + value
        if term_key == "other":
            continue
        term3015_face += value
        term_months = fmer.TERM_MONTHS_BY_LABEL[term_label]

        mc = re.search(r"(\d+(?:\.\d+)?)%", desc)
        mm = re.search(r"(\d{1,2})/(\d{2})\b", desc)
        if not mc or not mm:
            continue
        coupon = float(mc.group(1)) / 100.0
        mo, yy = int(mm.group(1)), int(mm.group(2))
        mat_date = pd.Timestamp(year=2000 + yy, month=mo, day=1)
        origin = mat_date - pd.DateOffset(months=term_months)
        bucket = round(coupon / step) * step
        group = vgroup(origin.year)

        included_face += value
        wac_num += value * coupon
        ck = coupon_key(bucket)
        coupon_face[ck] = coupon_face.get(ck, 0.0) + value
        vyear_face[str(origin.year)] = vyear_face.get(str(origin.year), 0.0) + value
        vgroup_face[group] = vgroup_face.get(group, 0.0) + value
        jk = f"{agency}|{term_label}|{ck}|{group}"
        joint_face[jk] = joint_face.get(jk, 0.0) + value

    def norm(d: dict, denom: float) -> dict:
        return {k: v / denom for k, v in sorted(d.items())} if denom else {}

    joint_shares = norm(joint_face, included_face)
    return {
        "as_of": str(as_of.date()),
        "n_mbs_rows": n_rows,
        "skipped_missing_value_rows": skipped_value_rows,
        "total_mbs_face_b": total_face / 1e9,
        "agency_shares": norm(agency_face, total_face),
        "term_shares": {k: term_face.get(k, 0.0) / total_face
                        for k in ("30yr", "15yr", "other")},
        "parse_coverage_of_30_15_face":
            (included_face / term3015_face) if term3015_face else 0.0,
        "included_face_b": included_face / 1e9,
        "wac_face_weighted_pct":
            (wac_num / included_face * 100.0) if included_face else 0.0,
        "coupon_shares": norm(coupon_face, included_face),
        "vintage_year_shares": norm(vyear_face, included_face),
        "vintage_group_shares": {k: vgroup_face.get(k, 0.0) / included_face
                                 for k in VGROUP_ORDER} if included_face else {},
        "desc_token_face_shares": dict(sorted(
            norm(token_face, total_face).items(),
            key=lambda kv: -kv[1])[:8]),
        "joint_cells_min_share_0p1pct": {
            k: v for k, v in sorted(joint_shares.items(),
                                    key=lambda kv: -kv[1])
            if v >= JOINT_CELL_MIN_SHARE},
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    t0 = time.perf_counter()
    gates: dict = {}

    # ---- G1 freddie sample integrity ------------------------------------
    fs = pl.read_parquet(LOAN_SAMPLE_PATH)
    wac_got = float(fs["coupon"].mean()) * 100.0
    vmin, vmax = int(fs["vintage"].min()), int(fs["vintage"].max())
    g1 = {
        "rows": {"got": fs.height, "want": 75_000, "pass": fs.height == 75_000},
        "cols": {"got": fs.width, "want": 14, "pass": fs.width == 14},
        "vintage_range": {"got": [vmin, vmax],
                          "pass": vmin >= min(VINTAGE_YEARS)
                          and vmax <= max(VINTAGE_YEARS)},
        "weight_sum": {"got": float(fs["weight"].sum()), "want": 75_000.0,
                       "pass": float(fs["weight"].sum()) == 75_000.0},
        "sample_wac_parity": {"got": wac_got, "want": SAMPLE_WAC_PCT,
                              "tol": G1_WAC_TOL,
                              "pass": abs(wac_got - SAMPLE_WAC_PCT) <= G1_WAC_TOL},
    }
    gates["G1_freddie_sample_integrity"] = {
        **g1, "pass": all(v["pass"] for v in g1.values())}
    print(f"G1 freddie sample integrity: {fs.height:,} x {fs.width}, "
          f"WAC parity |{wac_got:.12f} - {SAMPLE_WAC_PCT:.12f}|  "
          f"{'PASS' if gates['G1_freddie_sample_integrity']['pass'] else 'FAIL'}")
    if not gates["G1_freddie_sample_integrity"]["pass"]:
        _fail(gates, "G1 freddie sample integrity failed")

    # ---- G2 freddie panel integrity --------------------------------------
    panel = pl.read_parquet(PANEL_PATH)
    snap = panel.filter(pl.col("period") == SNAPSHOT_DATE.to_pydatetime())
    g2 = {
        "rows": {"got": panel.height, "want": 22_709,
                 "pass": panel.height == 22_709},
        "june_2022_snapshot": {"cells": snap.height,
                               "exposure_positive":
                                   float(snap["exposure_upb"].sum()) > 0.0,
                               "pass": snap.height > 0
                               and float(snap["exposure_upb"].sum()) > 0.0},
    }
    gates["G2_freddie_panel_integrity"] = {
        **g2, "pass": all(v["pass"] for v in g2.values())}
    print(f"G2 freddie panel integrity: {panel.height:,} cells, June-2022 "
          f"snapshot {snap.height} cells  "
          f"{'PASS' if gates['G2_freddie_panel_integrity']['pass'] else 'FAIL'}")
    if not gates["G2_freddie_panel_integrity"]["pass"]:
        _fail(gates, "G2 freddie panel integrity failed")

    # ---- G3 fannie integrity ---------------------------------------------
    fns = pl.read_parquet(FANNIE_SAMPLE_PATH)
    manifest = json.load(open(MANIFEST_PATH))
    replication = json.load(open(REPLICATION_JSON))
    pool_paths = {t: QUARTER_DIR / f"pool_{t}.parquet" for t in TAGS}
    missing = [t for t, p in pool_paths.items() if not p.exists()]
    pools = {t: pl.read_parquet(p) for t, p in pool_paths.items()
             if p.exists()}
    manifest_tags_ok = sorted(manifest.keys()) == sorted(TAGS)
    per_file_ok = manifest_tags_ok and all(
        pools[t].height == manifest[t]["pool_rows"]
        for t in pools if t in manifest)
    pool_rows = sum(f.height for f in pools.values())
    committed_total = replication["universe"]["pool_rows_total"]
    pool_all = pl.concat(list(pools.values())) if pools else pl.DataFrame()
    pv = ([int(pool_all["vintage"].min()), int(pool_all["vintage"].max())]
          if pool_all.height else [0, 0])
    fvmin, fvmax = int(fns["vintage"].min()), int(fns["vintage"].max())
    g3 = {
        "sample_rows": {"got": fns.height, "want": 75_000,
                        "pass": fns.height == 75_000},
        "sample_cols": {"got": fns.width, "want": 14, "pass": fns.width == 14},
        "sample_vintage_range": {"got": [fvmin, fvmax],
                                 "pass": fvmin >= min(VINTAGE_YEARS)
                                 and fvmax <= max(VINTAGE_YEARS)},
        "pool_files": {"got": len(pools), "want": len(TAGS),
                       "missing": missing, "pass": not missing},
        "manifest_tags_match_spec": {"pass": manifest_tags_ok},
        "per_file_rows_match_manifest": {"pass": per_file_ok},
        "pool_rows_total": {"got": pool_rows, "want": POOL_ROWS_TOTAL,
                            "committed_source": committed_total,
                            "pass": pool_rows == POOL_ROWS_TOTAL
                            and committed_total == POOL_ROWS_TOTAL},
        "pool_vintage_range": {"got": pv,
                               "pass": pv[0] >= min(VINTAGE_YEARS)
                               and pv[1] <= max(VINTAGE_YEARS)},
    }
    gates["G3_fannie_integrity"] = {
        **g3, "pass": all(v["pass"] for v in g3.values())}
    print(f"G3 fannie integrity: sample {fns.height:,}, pools "
          f"{len(pools)}/{len(TAGS)} files / {pool_rows:,} rows vs committed "
          f"{committed_total:,}  "
          f"{'PASS' if gates['G3_fannie_integrity']['pass'] else 'FAIL'}")
    if not gates["G3_fannie_integrity"]["pass"]:
        _fail(gates, "G3 fannie integrity failed")

    # ---- G4 constants integrity ------------------------------------------
    full_book = json.load(open(FULL_BOOK_JSON))
    ginnie = json.load(open(GINNIE_BOUND_JSON))
    overlay = json.load(open(OVERLAY_JSON))
    vbound = json.load(open(VINTAGE_BOUND_JSON))
    bench = json.load(open(EXPECT_BENCH_JSON))
    shares_sum = sum(VINTAGE_SHARES.values())

    def near(got, want, tol=G4_ABS_TOL):
        return {"got": got, "want": want, "pass": abs(got - want) <= tol}

    g4 = {
        "sample_wac": near(full_book["sample_wac_pct"], SAMPLE_WAC_PCT),
        "path_b_balance_share": near(
            full_book["path_b"]["balance_weighted"]["share_pct"],
            PATH_B_BALANCE_SHARE),
        "path_b_fullbook_share": near(
            full_book["path_b"]["full_book_weighted"]["share_pct"],
            PATH_B_FULLBOOK_SHARE),
        "ginnie_share": {"got": ginnie["ginnie_share_of_soma_face"],
                         "want": GINNIE_SHARE,
                         "pass": ginnie["ginnie_share_of_soma_face"]
                         == GINNIE_SHARE},
        "static_bound": {"got": ginnie["bound_b"],
                         "want": list(STATIC_GINNIE_BOUND_B),
                         "pass": list(ginnie["bound_b"])
                         == list(STATIC_GINNIE_BOUND_B)},
        "overlay_marginal_pp": near(
            overlay["variants"]["primary"]["marginal_pp"], OVERLAY_MARGINAL_PP),
        "overlay_adjustment_primary_b": near(
            overlay["variants"]["primary"]["central"]["adjustment_sum_b"],
            OVERLAY_ADJ_PRIMARY_B),
        "overlay_adjustment_placebo_b": near(
            overlay["variants"]["gse_placebo"]["central"]["adjustment_sum_b"],
            OVERLAY_ADJ_PLACEBO_B),
        "vintage_bound_b": near(vbound["results"]["bound_b"], VINTAGE_BOUND_B),
        "vintage_bound_pct": near(vbound["results"]["bound_pct_of_benchmark"],
                                  VINTAGE_BOUND_PCT),
        "fannie_marginal_pp": near(
            replication["path_b"]["lockin_marginal_share_pp"],
            FANNIE_MARGINAL_PP),
        "benchmark": near(bench["cap_benchmark_b"], BENCHMARK_B),
        "vintage_shares": {"got": VINTAGE_SHARES,
                           "want": {"2022": 0.231, "2021": 0.439,
                                    "2020": 0.163, "2017-19": 0.060,
                                    "pre2017": 0.106},
                           "pass": VINTAGE_SHARES == {
                               "2022": 0.231, "2021": 0.439, "2020": 0.163,
                               "2017-19": 0.060, "pre2017": 0.106}},
        "vintage_shares_sum": {"got": shares_sum, "want": 0.999,
                               "pass": abs(shares_sum - 0.999) <= 1e-12},
    }
    gates["G4_constants_integrity"] = {
        **g4, "pass": all(v["pass"] for v in g4.values())}
    print(f"G4 constants integrity: {sum(v['pass'] for v in g4.values())}/"
          f"{len(g4)} committed anchors tie  "
          f"{'PASS' if gates['G4_constants_integrity']['pass'] else 'FAIL'}")
    if not gates["G4_constants_integrity"]["pass"]:
        _fail(gates, "G4 constants integrity failed")

    # ---- network: latest as-of fetch (REQUIRED) ---------------------------
    try:
        latest_str = _fetch_json(fmer.SOMA_LATEST_DATE_URL,
                                 15)["soma"]["asOfDates"][0]
        holdings_latest = _fetch_json(
            fmer.SOMA_CUSIP_URL.format(date=latest_str), 60)["soma"]["holdings"]
    except Exception as exc:  # noqa: BLE001 — abort on ANY fetch failure
        _fail(gates, f"NY Fed SOMA fetch failed ({exc!r}); network is "
                     "required and there is no offline snapshot")
    book_latest = tabulate_book(holdings_latest, pd.Timestamp(latest_str))

    cohorts = fmer.fetch_soma_mbs_cohorts()
    if len(cohorts) <= 1:
        _fail(gates, "fetch_soma_mbs_cohorts returned its single-cohort "
                     "network fallback; the anchor WAC cannot be gated")
    cohort_wac = sum(c["coupon"] * c["weight"] for c in cohorts) * 100.0

    # ---- G5 soma anchor parity -------------------------------------------
    ag = book_latest["agency_shares"]
    tm = book_latest["term_shares"]
    vg = book_latest["vintage_group_shares"]
    a1 = {"got": cohort_wac, "want": BOOK_WAC_PCT, "tol": A1_WAC_TOL,
          "n_cohorts": len(cohorts),
          "pass": abs(cohort_wac - BOOK_WAC_PCT) <= A1_WAC_TOL}
    a2 = {"got": ag.get("GNMA", 0.0), "want": GINNIE_SHARE, "tol": A2_GNMA_TOL,
          "pass": abs(ag.get("GNMA", 0.0) - GINNIE_SHARE) <= A2_GNMA_TOL}
    a3 = {k: {"got": tm[k], "want": TERM_SHARES_REF[k], "tol": A3_TERM_TOL[k],
              "pass": abs(tm[k] - TERM_SHARES_REF[k]) <= A3_TERM_TOL[k]}
          for k in ("30yr", "15yr", "other")}
    a4 = {k: {"got": vg.get(k, 0.0), "want": VINTAGE_SHARES[k],
              "tol": A4_VGROUP_TOL,
              "pass": abs(vg.get(k, 0.0) - VINTAGE_SHARES[k])
              <= A4_VGROUP_TOL}
          for k in VINTAGE_SHARES}
    class_cov = ag.get("GNMA", 0.0) + ag.get("UMBS", 0.0)
    a5 = {"agency_classification_coverage":
          {"got": class_cov, "min": A5_MIN_COVERAGE,
           "pass": class_cov >= A5_MIN_COVERAGE},
          "desc_parse_coverage":
          {"got": book_latest["parse_coverage_of_30_15_face"],
           "min": A5_MIN_COVERAGE,
           "pass": book_latest["parse_coverage_of_30_15_face"]
           >= A5_MIN_COVERAGE}}
    g5 = {"A1_cohort_wac": a1, "A2_gnma_share": a2, "A3_term_shares": a3,
          "A4_vintage_group_shares": a4, "A5_coverage": a5,
          "as_of_latest": book_latest["as_of"]}
    g5_pass = (a1["pass"] and a2["pass"]
               and all(v["pass"] for v in a3.values())
               and all(v["pass"] for v in a4.values())
               and all(v["pass"] for v in a5.values()))
    gates["G5_soma_anchor_parity"] = {**g5, "pass": g5_pass}
    print(f"G5 soma anchor parity (as-of {book_latest['as_of']}): "
          f"WAC {cohort_wac:.3f} vs {BOOK_WAC_PCT}, GNMA "
          f"{ag.get('GNMA', 0.0):.4f} vs {GINNIE_SHARE}, terms "
          f"{tm['30yr']:.3f}/{tm['15yr']:.3f}/{tm['other']:.3f}, vintage "
          f"groups max|d| "
          f"{max(abs(v['got'] - v['want']) for v in a4.values()):.4f}  "
          f"{'PASS' if g5_pass else 'FAIL'}")
    if not g5_pass:
        _fail(gates, "G5 soma anchor parity failed")

    # ---- June-2022 as-of contingency (non-gating, disclosed) --------------
    june_block = None
    june_served = False
    june_note = ""
    try:
        payload = _fetch_json(SOMA_ASOFDATES_LIST_URL, 15)
        node = payload.get("soma", payload)
        raw_dates = node.get("asOfDates", []) if isinstance(node, dict) else []
        dates = []
        for d in raw_dates:
            if isinstance(d, str):
                dates.append(d)
            elif isinstance(d, dict):
                for v in d.values():
                    if isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}", v):
                        dates.append(v)
                        break
        june = [d for d in dates
                if JUNE_2022_WINDOW[0] <= d <= JUNE_2022_WINDOW[1]]
        if june:
            target = max(june)
            holdings_june = _fetch_json(
                fmer.SOMA_CUSIP_URL.format(date=target),
                60)["soma"]["holdings"]
            candidate = tabulate_book(holdings_june, pd.Timestamp(target))
            face = candidate["total_mbs_face_b"] * 1e9
            sane = (JUNE_SANITY_FACE_RANGE[0] < face < JUNE_SANITY_FACE_RANGE[1]
                    and JUNE_SANITY_GNMA_RANGE[0]
                    <= candidate["agency_shares"].get("GNMA", 0.0)
                    <= JUNE_SANITY_GNMA_RANGE[1]
                    and candidate["parse_coverage_of_30_15_face"]
                    >= JUNE_SANITY_MIN_PARSE)
            if sane:
                june_block = candidate
                june_served = True
                june_note = (f"historical as-of {target} served and passed "
                             "the non-gating sanity screens; reported as a "
                             "secondary block, never anchor-gated")
            else:
                june_note = (f"historical as-of {target} served but FAILED "
                             "the non-gating sanity screens; block dropped, "
                             "disclosed here")
        else:
            june_note = ("API served no as-of date in "
                         f"[{JUNE_2022_WINDOW[0]}, {JUNE_2022_WINDOW[1]}]; "
                         "committed VINTAGE_SHARES / WAC 2.49 stand as the "
                         "June-2022 reference marginals (pre-committed "
                         "contingency)")
    except Exception as exc:  # noqa: BLE001 — contingency is non-gating
        june_note = (f"asofdates/list contingency fetch failed ({exc!r}); "
                     "committed VINTAGE_SHARES / WAC 2.49 stand as the "
                     "June-2022 reference marginals (pre-committed "
                     "contingency)")
    print(f"June-2022 as-of contingency: served={june_served} — {june_note}")

    # ---- compositions (all gates passed; new quantities from here) --------
    freddie_sample = sample_block(fs)
    fannie_sample = sample_block(fns)
    pool_state = state_block(pool_all)
    pool_upb = pool_all.with_columns(upb_bucket_expr())
    fannie_pools_block = {
        "n_loans": pool_all.height,
        "note": ("24 equal-n per-quarter stratified pools concatenated "
                 "without acquisition-volume reweighting; composition "
                 "proxy, non-decisive"),
        "state": pool_state,
        "upb_bucket_shares_upb_weighted":
            shares_pl(pool_upb, "upb_bucket", "orig_upb"),
        "upb_bucket_shares_count_weighted":
            shares_pl(pool_upb, "upb_bucket", None),
        "fico_shares_upb_weighted": shares_pl(pool_all, "fico_bucket", "orig_upb"),
        "ltv_shares_upb_weighted": shares_pl(pool_all, "ltv_bucket", "orig_upb"),
    }

    snap_b = snap.with_columns(vgroup_expr())
    qt_panel = panel.filter(
        (pl.col("period") >= pd.Timestamp("2022-06-01").to_pydatetime())
        & (pl.col("period") < pd.Timestamp("2025-12-01").to_pydatetime())
    ).with_columns(vgroup_expr())
    universe_panel = {
        "snapshot_date": str(SNAPSHOT_DATE.date()),
        "snapshot_cells": snap.height,
        "snapshot_exposure_usd_t": float(snap["exposure_upb"].sum()) / 1e12,
        "coupon_shares_exposure_weighted":
            coupon_shares_fmt(shares_pl(snap, "coupon", "exposure_upb")),
        "vintage_year_shares_exposure_weighted":
            shares_pl(snap, "vintage", "exposure_upb"),
        "vintage_group_shares_exposure_weighted":
            shares_pl(snap_b, "vintage_group", "exposure_upb"),
        "fico_shares_exposure_weighted":
            shares_pl(snap, "fico_bucket", "exposure_upb"),
        "ltv_shares_exposure_weighted":
            shares_pl(snap, "ltv_bucket", "exposure_upb"),
        "qt_window_variant": {
            "window": "2022-06-01 <= period < 2025-12-01 (exposure-month sums)",
            "coupon_shares_exposure_weighted":
                coupon_shares_fmt(shares_pl(qt_panel, "coupon", "exposure_upb")),
            "vintage_group_shares_exposure_weighted":
                shares_pl(qt_panel, "vintage_group", "exposure_upb"),
        },
    }

    # ---- sample-vs-book comparisons --------------------------------------
    univ_coupon = universe_panel["coupon_shares_exposure_weighted"]
    book_coupon = book_latest["coupon_shares"]
    univ_vgroup = universe_panel["vintage_group_shares_exposure_weighted"]
    book_vgroup = book_latest["vintage_group_shares"]
    ref_vgroup = {k: VINTAGE_SHARES[k] for k in VINTAGE_SHARES}
    agency_sample = {"UMBS": 1.0, "GNMA": 0.0, "other": 0.0}
    oos_keys = [k for k in VGROUP_ORDER if univ_vgroup.get(k, 0.0) == 0.0]

    sample_vs_book = {
        "book_side": ("soma_book.latest (anchor-gated, G5); committed "
                      "reference marginals reported alongside"),
        "coupon": {
            **compare("coupon", univ_coupon, book_coupon),
            "freddie_side": "universe panel June-2022 exposure shares (primary)",
            "wac_pair_pct": {"freddie_sample": SAMPLE_WAC_PCT,
                             "book_cohort": BOOK_WAC_PCT,
                             "difference_pp": SAMPLE_WAC_PCT - BOOK_WAC_PCT},
            "sample_variant": compare(
                "coupon",
                freddie_sample["coupon_shares_upb_weighted"], book_coupon),
        },
        "vintage": {
            **compare("vintage", univ_vgroup, book_vgroup,
                      order=VGROUP_ORDER, support_mismatch=True,
                      out_of_support_keys=oos_keys),
            "freddie_side": "universe panel June-2022 exposure shares (primary)",
            "vs_committed_reference": compare(
                "vintage", univ_vgroup, ref_vgroup, order=VGROUP_ORDER,
                support_mismatch=True, out_of_support_keys=oos_keys),
        },
        "agency": {
            **compare("agency", agency_sample,
                      book_latest["agency_shares"],
                      order=["UMBS", "GNMA", "other"],
                      support_mismatch=True, out_of_support_keys=["GNMA",
                                                                  "other"]),
            "note": ("estimation sample is Freddie 100% by construction, "
                     "mapped to the UMBS bucket; CUSIP-level UMBS does not "
                     "identify Fannie vs Freddie — margin is "
                     "conventional-vs-GNMA only"),
        },
        "term": {
            "book_only": True,
            "book_shares_pct": {k: v * 100.0
                                for k, v in book_latest["term_shares"].items()},
            "note": ("sample side undeliverable: original_loan_term not "
                     "retained by the FRM-only ingest (hazard/ingest.py); "
                     "consequence pointer = tex ~L734 9.1% 15-year "
                     "exclusion disclosure"),
        },
    }

    # ---- freddie-vs-fannie substitute block ------------------------------
    fvf = {
        "state": {
            **compare("state",
                      freddie_sample["state"]["shares_upb_weighted"],
                      fannie_sample["state"]["shares_upb_weighted"]),
            "freddie_hhi": freddie_sample["state"]["hhi_upb_weighted"],
            "fannie_hhi": fannie_sample["state"]["hhi_upb_weighted"],
            "fannie_pools_hhi": pool_state["hhi_upb_weighted"],
        },
        "orig_upb": {
            **compare("orig_upb",
                      freddie_sample["upb_bucket_shares_upb_weighted"],
                      fannie_sample["upb_bucket_shares_upb_weighted"],
                      order=UPB_LABELS),
            "mean_orig_upb": {"freddie": freddie_sample["mean_orig_upb"],
                              "fannie": fannie_sample["mean_orig_upb"]},
            "median_orig_upb": {"freddie": freddie_sample["median_orig_upb"],
                                "fannie": fannie_sample["median_orig_upb"]},
        },
        "fico": {
            **compare("fico",
                      freddie_sample["fico_shares_upb_weighted"],
                      fannie_sample["fico_shares_upb_weighted"]),
            "mean_fico": {"freddie": freddie_sample["mean_fico"],
                          "fannie": fannie_sample["mean_fico"]},
        },
        "ltv": {
            **compare("ltv",
                      freddie_sample["ltv_shares_upb_weighted"],
                      fannie_sample["ltv_shares_upb_weighted"]),
            "mean_orig_ltv": {"freddie": freddie_sample["mean_orig_ltv"],
                              "fannie": fannie_sample["mean_orig_ltv"]},
        },
        "coupon_context": compare(
            "coupon", freddie_sample["coupon_shares_upb_weighted"],
            fannie_sample["coupon_shares_upb_weighted"]),
        "vintage_year_context": compare(
            "vintage_year",
            freddie_sample["vintage_year_shares_upb_weighted"],
            fannie_sample["vintage_year_shares_upb_weighted"]),
    }
    substitute_dims = ("state", "orig_upb", "fico", "ltv")
    divergent = [d for d in substitute_dims
                 if fvf[d]["psi"] >= SUBSTITUTE_PSI_THRESHOLD]
    if not divergent:
        sub_verdict = "cross_agency_stable"
        sub_sentence = SUBSTITUTE_SENTENCES[sub_verdict]
    else:
        sub_verdict = "cross_agency_divergent_disclosed"
        sub_sentence = SUBSTITUTE_SENTENCES[sub_verdict].format(
            dims=", ".join(divergent))
    overall_verdict = ("composition_shift_formalized_"
                       + ("stable_" if not divergent else "divergent_")
                       + "substitute")

    dim_sentences = {}
    for dim, block, consequence in (
            ("coupon", sample_vs_book["coupon"], CONSEQUENCE_MAP["coupon"]),
            ("vintage", sample_vs_book["vintage"], CONSEQUENCE_MAP["vintage"]),
            ("agency", sample_vs_book["agency"], CONSEQUENCE_MAP["agency"])):
        oos = ""
        if block.get("support_mismatch") and \
                "out_of_support_book_mass_pp" in block:
            oos = (f"; out-of-support book mass "
                   f"{block['out_of_support_book_mass_pp']:.1f}pp")
        dim_sentences[dim] = SHIFT_SENTENCE.format(
            dim=dim, psi=block["psi"], band=block["psi_band"],
            max_dpp=block["max_abs_delta_pp"], oos=oos,
            consequence=consequence)

    # ---- artifact --------------------------------------------------------
    payload = {
        "mode": "composition_shift",
        "spec": ("round-17 R17-B; formal covariate-shift table, estimation "
                 "sample(s) vs SOMA book, with committed per-dimension "
                 "consequence bounds (module docstring, fixed ex ante)"),
        "reviewer_item": "R17-B (T2 + DC2 + Q1); roadmap gate #38",
        "as_of": {
            "latest": book_latest["as_of"],
            "june_2022_requested": True,
            "june_2022_served": june_served,
            "june_2022_date": june_block["as_of"] if june_block else None,
            "provenance_note": (
                "committed anchors (WAC 2.49, GNMA 0.204, term "
                "90.7/9.1/0.2, VINTAGE_SHARES) were tabulated from the "
                "latest served as-of at the 2026-07-05 production freeze; "
                "primary grid is the latest as-of, anchor-gated (G5). "
                + june_note),
        },
        "metric": {
            "primary": ("per-bucket share difference in pp + one PSI per "
                        "dimension (eps floor 1e-6, union support)"),
            "psi_bands": {"negligible": "<0.10", "moderate": "0.10-0.25",
                          "large": ">=0.25"},
            "secondary": "total variation distance 0.5*sum|dp|",
            "support_mismatch_note": (
                "where the sample has structural zero mass on book support "
                "(vintage, agency), PSI inflates via the eps floor; those "
                "dimensions carry out_of_support_book_mass_pp — the tex-"
                "table number — with PSI alongside"),
        },
        "committed_anchors": {
            "sample_wac_pct": SAMPLE_WAC_PCT,
            "book_cohort_wac_pct": BOOK_WAC_PCT,
            "ginnie_share_of_soma_face": GINNIE_SHARE,
            "term_shares": TERM_SHARES_REF,
            "vintage_shares": dict(VINTAGE_SHARES),
            "static_ginnie_bound_b": list(STATIC_GINNIE_BOUND_B),
            "vintage_bound_b": VINTAGE_BOUND_B,
            "fannie_marginal_pp": FANNIE_MARGINAL_PP,
            "benchmark_b": BENCHMARK_B,
            "sources": ("abm/data/latest_run_manifest.json; TECHNICAL.md "
                        "~L1552-1554; hazard/wal_table.py; committed "
                        "hazard/data artifacts under G4 parity"),
        },
        "gates": gates,
        "freddie": {"sample": freddie_sample, "universe_panel": universe_panel},
        "fannie": {"sample": fannie_sample, "pools": fannie_pools_block,
                   "license_note": ("aggregate bucket shares only; no "
                                    "loan-level values (ratified "
                                    "fannie_replication posture)")},
        "soma_book": {
            "latest": book_latest,
            "asof_june_2022": june_block,
            "reference_marginals": {
                "source": ("committed June-2022 reference: wal_table."
                           "VINTAGE_SHARES + WAC 2.49 + GNMA 0.204 + term "
                           "90.7/9.1/0.2 (see committed_anchors)"),
                "vintage_group_shares": dict(VINTAGE_SHARES),
                "wac_pct": BOOK_WAC_PCT,
                "agency_shares": {"UMBS": 1.0 - GINNIE_SHARE,
                                  "GNMA": GINNIE_SHARE},
                "term_shares": TERM_SHARES_REF,
            },
        },
        "comparisons": {"sample_vs_book": sample_vs_book,
                        "freddie_vs_fannie": fvf},
        "disclosed_undeliverable": {
            "dimensions": ["geography (state)", "loan size (orig UPB)",
                           "FICO", "LTV"],
            "reason": ("CUSIP-level SOMA holdings disclose par value and "
                       "securityDescription only (agency / coupon / term / "
                       "maturity); state, loan size, FICO and LTV do not "
                       "exist at the CUSIP level of the Fed's published "
                       "holdings and would require an external pool-level "
                       "collateral-disclosure ingest (agency disclosure "
                       "tapes / eMBS)"),
            "substitute": ("comparisons.freddie_vs_fannie — cross-agency "
                           "loan-level composition on exactly these "
                           "dimensions; hazard-side covariate exposure "
                           "already bracketed by the printed covariate-"
                           "block endpoints 99.2%/92.2% shared-basis "
                           "(tex ~L402)"),
            "additional": ("UMBS does not identify Fannie vs Freddie at "
                           "CUSIP level; original term not retained in the "
                           "committed samples (term margin book-side only, "
                           "tex ~L734 disclosure)"),
        },
        "consequence_map": CONSEQUENCE_MAP,
        "interpretation": {
            "expected_direction": (
                "large shift on coupon / vintage / agency is the EXPECTED "
                "outcome the paper already discloses (WAC 3.9 vs 2.49; "
                "66.2% vintage coverage; 20.4% Ginnie); shift size gates "
                "nothing and no headline moves under any measured value — "
                "each dimension's consequence is the committed bound in "
                "consequence_map"),
            "dimension_sentences": dim_sentences,
            "substitute_verdict": sub_verdict,
            "substitute_sentence": sub_sentence,
            "substitute_threshold_psi": SUBSTITUTE_PSI_THRESHOLD,
            "divergent_dimensions": divergent,
            "overall_verdict": overall_verdict,
        },
        "caveats": [
            ("book side is the latest served as-of, runoff-drifted from the "
             "June-2022 reference; committed VINTAGE_SHARES / WAC 2.49 stand "
             "as the June-2022 reference marginals; a served June-2022 as-of "
             "is reported alongside, non-gating"),
            ("CUSIP-level UMBS does not identify Fannie vs Freddie; agency "
             "margin is conventional-vs-GNMA only"),
            ("back-derived vintage = maturity minus stated term; pool "
             "maturity conventions (GNMA II multi-issuer) can shift derived "
             "origins by months around year boundaries"),
            ("committed samples carry no term column (FRM-only ingest); "
             "term margin is book-side only with the tex ~L734 9.1% "
             "exclusion disclosure"),
            ("Fannie quarter pools are equal-n per-quarter draws pooled "
             "without acquisition-volume reweighting; composition proxy, "
             "non-decisive"),
            ("state / loan-size shares are orig-UPB-weighted primary, "
             "count-weighted secondary"),
        ],
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")

    # ---- console summary --------------------------------------------------
    print("\nSample-vs-book (Freddie universe June-2022 vs SOMA latest "
          f"{book_latest['as_of']}):")
    for dim in ("coupon", "vintage", "agency"):
        b = sample_vs_book[dim]
        oos = (f", out-of-support {b['out_of_support_book_mass_pp']:.1f}pp"
               if "out_of_support_book_mass_pp" in b else "")
        print(f"  {dim:<8} PSI {b['psi']:8.3f} ({b['psi_band']}); "
              f"TV {b['tv_distance']:.3f}; max|d| "
              f"{b['max_abs_delta_pp']:.1f}pp{oos}")
    print(f"  term     book-only: "
          f"{sample_vs_book['term']['book_shares_pct']['30yr']:.1f}/"
          f"{sample_vs_book['term']['book_shares_pct']['15yr']:.1f}/"
          f"{sample_vs_book['term']['book_shares_pct']['other']:.1f} "
          "(30yr/15yr/other; sample term not retained)")
    print("Freddie-vs-Fannie substitute (sample vs sample, orig-UPB "
          "weighted):")
    for dim in substitute_dims:
        b = fvf[dim]
        print(f"  {dim:<8} PSI {b['psi']:8.4f} ({b['psi_band']}); "
              f"max|d| {b['max_abs_delta_pp']:.2f}pp")
    print(f"Substitute verdict: {sub_verdict}"
          + (f" (divergent: {', '.join(divergent)})" if divergent else ""))
    print(f"Overall: {overall_verdict}")
    print(f"Results saved to {RESULTS_JSON}  "
          f"({time.perf_counter() - t0:.1f}s)")


if __name__ == "__main__":
    main()
