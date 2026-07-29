#!/usr/bin/env python3
"""
coupon_convention_reweight.py — G2-A of WP-G: the full-book reweight and the
composed-basis cell, re-run with the sample's NOTE rates converted to
PASS-THROUGH equivalents before they are bucketed against the SOMA book.

PRE-COMMITTED SPEC. Everything below is fixed BEFORE any run, and it is a
transcription of specs/SPEC_round28_G2_coupon_convention.md (sections named
inline) plus PRE-RUN AMENDMENT G2-AM1. Where this header and the spec differ,
the spec governs and the difference is a defect in this file.
Requires specs/PATCH_G2A.md applied (the `coupon_convert` seam); without it
the import of run_qt_microsim's new keyword fails immediately.

=======================================================================
THE DEFECT (WP-G1, verified independently; SPEC section 0.1)
=======================================================================
Two coupon conventions are bucketed against each other on one 0.5% grid:

  SOMA side  abm/fed_mbs_extension_risk.py:561-565 parses the security
             PASS-THROUGH coupon out of securityDescription and rounds it to
             the 0.5% grid at :573.
  Sample side agents.py:187 buckets loan_sample.parquet's `coupon` — the
             borrower NOTE rate (agents.py:119) — on the same grid, with NO
             conversion. Path A repeats it at simulate.py:90,96.

Note rate minus pass-through is the guarantee fee plus base servicing: about
0.80pp on this book's vintages, i.e. about 1.6 buckets on a 0.5pp grid. The
full-book reweight therefore up-weights loans that are roughly a bucket and a
half more deeply locked than the SOMA collateral it is matching, and the
+2.1pp composition effect it reports is part units and part composition.

The manuscript sentence carrying it (tex 263, tex 580, tex 1177) compounds the
error with a WEIGHTING mismatch: "sample WAC 3.9%" is the UNWEIGHTED mean of
NOTE rates (full_book_weighting.py:94, sample_wac_pct 3.864892813333334) while
"the book's 2.49%" is the FACE-WEIGHTED mean of PASS-THROUGH coupons
(composition_shift.py:334/:858).

=======================================================================
DESIGN CHOICES, AND WHAT WAS REJECTED (SPEC section G2.1.1)
=======================================================================
PICKED  convert the SAMPLE side, on a LOCAL COPY, inside the two bucketing
        routines only. phi_v(c_note) = c_note - (g_v + 0.0025).
REJECTED convert the SOMA side upward: the parser carries no per-bucket
        vintage the reweight consumes (its origin date is face-weighted
        WITHIN a (term, coupon) bucket and smears vintages -- the same
        limitation wal_anchor_results.json discloses), and shifting the
        target grid would change the object the committed 2.49% anchor and
        gate #38's PSI describe.
REJECTED mutate self.coupon and restore in a finally: pool.coupon is read by
        compute_rate_gap, rate_stress and the Danish berger_calibration
        branches (competing_risks.py:120-168). The safe design is one where
        the unsafe outcome is UNREACHABLE, not one where it is undone. Gate
        G3 below tests that unreachability directly.

WHAT phi DELIBERATELY DOES NOT MODEL: excess servicing above the 25bp base;
buy-up/buy-down to the 50bp TBA grid; LLPAs delivered as upfront points. The
realized note-to-pass-through distance is therefore >= phi's, so phi is a
LOWER bound on the wedge and the converted composition effect it produces is
an UPPER bound on what survives the correction. That is the conservative
direction and it is stated ex ante.

=======================================================================
THE g-FEE SCHEDULE (SPEC section G2.1.2 + AMENDMENT G2-AM1)
=======================================================================
FLAT 55bp for every vintage 2017-2021, plus 25bp base servicing => 0.80pp.
Flat is the PRIMARY, not a fallback, and the argument is arithmetic: the
bucket grid is 50bp and the entire plausible 2017-2021 g-fee dispersion is
<= ~12bp = 0.24 of one bucket, so a per-vintage refinement can move at most
~24% of a vintage's mass by one bucket, which the +/-10bp legs bound. Per-
vintage FHFA figures are NOT hard-coded here: the spec forbids writing
numbers that cannot be cited to a report year and table, and PER_VINTAGE_GFEE
below is empty by design. If it is filled at run time it must be filled from
a citable table and GFEE_PROVENANCE updated in the same edit.

AMENDMENT G2-AM1 (coordinator, 2026-07-29): the leg set widens to
delta in {0.60, 0.70, 0.80, 0.90}; 0.60 brackets the G1 diagnosis's reading
(2.49 + ~0.6 ~ 3.1) which was an assumption, not a derivation. The PRIMARY
quoted leg remains 0.80. The distance between the 0.60 and 0.80 legs is
reported as the conversion-uncertainty span.

=======================================================================
LEGS (SPEC section G2-A.3, as amended)
=======================================================================
Path B, two-regime (US,Danish) so the shared layer can score, soma_cohorts
passed, seed 42, floor 4.0%, committed 75k sample, one shared macro frame:
  B1 phi_id   p_q 6.5   PARITY leg (G4/G5)
  B2 phi_0    p_q 6.5   PRIMARY (delta 0.80)
  Bl phi_060  p_q 6.5   amendment leg
  B3 phi_lo   p_q 6.5   delta 0.70
  B4 phi_hi   p_q 6.5   delta 0.90
  B5 phi_ref  p_q 6.5   delta 1.00 -- MECHANISM ONLY. A clean 2-bucket
                        translation; it isolates the level shift from the
                        within-bucket split that a non-integer wedge causes
                        (SPEC section 0.6). NEVER printed as an economic result.
  B6 phi_id   p_q 0.0   reweighted null
  B7 phi_0    p_q 0.0   reweighted null
Path A (cohort GLM), soma_cohorts passed, own temp parquet:
  A1 phi_id, A2 phi_0. Skipped with an explicit artifact status if
  cohort_month_panel.parquet is absent -- disclosed, never approximated.
INVARIANCE (leg B8, SPEC section G2.4), soma_cohorts NOT passed, US-only:
  production central/null at floors 4.0% and 4.991%. Run AFTER every
  converted leg so that leaked state would be present if it existed.

One two-regime reweight leg produces BOTH committed cells: its US frame
scores 109.13914436574825 standalone and 100.04305273304554 shared. This is
verified, not assumed -- shared_layer_scoring.py:160 derives the standalone
figure from the same two-regime run whose shared score is the composed cell,
and it equals full_book_weighting.py's US-only run bit-for-bit (the
regime-tuple invariance burnout_ablation G6 established).

=======================================================================
PARITY AND IDENTITY GATES (SPEC section G2-A.6). Bit-exact, < 1e-9, on every
dollar and share anchor. Any FAIL raises SystemExit; free-gate failures
raise BEFORE any engine time and write NO artifact (the run is VOID, not a
result).
=======================================================================
  G0  benchmark frame == $764.7482532227002B (input-drift detector: separates
      a FRED/SOMA revision from an engine change)
  G0b/G0c committed central/null caches rescore to 818.5300844066606 /
      748.1850239867648
  G1  SOMA parse invariance: face-weighted 30yr cohort WAC == 2.49 +/- 0.05
      (composition_shift A1_WAC_TOL) and the parsed cohort list is IDENTICAL
      across legs -- the conversion must not touch the SOMA side
  G2  phi arithmetic, analytic: phi_0(c) == c - 0.0080 to 1e-15 on a fixed
      probe vector for every vintage; phi_id(c) == c bit-exactly
  G3  NON-LEAKAGE, the run's most important gate, three parts:
      G3a pool.coupon bit-identical (np.array_equal) before and after a
          converted reweight
      G3b with coupon_convert=phi_id the bucket vector is bit-identical to
          the vector with coupon_convert=None -- the seam is inert at
          identity, so any movement in B2..B5 is the WEDGE and not the patch
      G3c leg B8: the production central and null reproduce their committed
          values at BOTH floors, run after the converted legs
  G4  phi_id standalone parity: 834.6397001192607 / 109.13914436574825 /
      r_lag0 0.27823879699900067 / peak lag -3
  G5  phi_id composed parity: 765.0774982466306 / 100.04305273304554 /
      danish 846.6912914390132 / curtailment 69.56220187263008
  G6  Path A phi_id parity: 121.46388911324269 unreweighted (read from the
      committed artifact, not re-run) and 127.45487776525697 reweighted;
      composed 118.35878613255424
  G7  basis identity: shared == standalone - 9.096091632702699 to 1e-9 on
      EVERY leg, with the offset read from calibration_reconciliation and
      re-derived as curtailment/cap*100
  G8  bucket-coverage disclosure (reported, not gated): sample balance share
      landing in a bucket absent from SOMA (zeroed), and SOMA weight landing
      in a bucket absent from the sample (renormalized away). These move
      under phi and are the first-order explanation of any deviation.
  G9  committed-artifact integrity: full_book_weighting_results.json,
      shared_layer_scoring_results.json, wal_table_results.json and
      composition_shift_results.json byte-identical (sha256) post-run. Three
      committed gates read these files (liveness_gates.py:1268-1284 #44,
      :3155 and :3801, :1136-1146 #38) and a naive re-run would break them.
  G10 restoration: INVOLUNTARY_CPR_ANNUAL == 0.04 and LITERATURE_COEFS equal
      to production after every leg; no temp parquet left on disk.

=======================================================================
PRE-COMMITTED EXPECTATION (SPEC section G2-A.5). Derived, signed, falsifiable.
=======================================================================
The reweight matches SOMA balance shares by bucket and SOMA is heavy at low
coupons (book <3.0% is 73.9% of face against the sample's 18.0%). Unconverted,
the loans lifted into the book's 2.0-2.5% buckets are loans whose NOTE rate is
2.0-2.5%, i.e. gaps near -4.5 to -4.0pp: deeply locked, slow, so trapped
liquidity rises by +2.107pp. Converted, the loans mapped into those same
buckets have note rates near 2.8-3.3%, gaps of -3.7 to -3.2: less locked,
faster, so LESS trapped. The composition effect must therefore SHRINK and
STAY POSITIVE -- positive because even converted the sample's pass-through-
equivalent WAC (3.78 - 0.80 = 2.98) still sits above the book's 2.49.

Linear-in-the-closed-gap projection, g0 = 3.78 - 2.49 = 1.29pp:
  delta 0.60 -> ratio 0.5349 -> full-book 108.160 -> composed 99.064
  delta 0.70 -> ratio 0.4574 -> full-book 107.996 -> composed 98.900
  delta 0.80 -> ratio 0.3798 -> full-book 107.833 -> composed 98.737  PRIMARY
  delta 0.90 -> ratio 0.3023 -> full-book 107.669 -> composed 98.573
Under the UNWEIGHTED sample WAC instead (g0 = 1.3749) the 0.80 leg gives
107.913 / 98.817 -- 0.08pp away, an order of magnitude inside the band, which
is why the unverified 3.78 does not block the run. It is re-derived at step 0
and written to the artifact either way.

MATERIALITY BAND: +/-0.5pp on the converted composed cell. Justified ex ante:
a quarter of the committed composition effect, 5x the printed precision, and
wider than the 0.33pp span the whole +/-10bp g-fee band produces -- so a
landing inside the band cannot be manufactured by the g-fee choice.

WHY THE PROJECTION MAY BE WRONG, stated before the run: prepay_hazard is
exponential in the gap, so a given bucket displacement is worth more at
shallow gaps (argues the realized effect is LARGER than projected); the hard
maximum censors 36.3% of central-leg loan-months at the 4.0% floor and
censored months absorb the perturbation entirely (argues SMALLER); and the
reweight redistributes mass, not just the mean. The net is NOT signed and
nothing is read into its direction after the fact.

C1 ORDERING CHECK (non-parity, BLOCKING as a wiring alarm):
  107.0326190295068 < fullbook(any converted leg) < 109.13914436574825, and
  fullbook strictly decreasing in delta over {0.60, 0.70, 0.80, 0.90}.
A violation means phi is wired backwards or applied to the wrong side:
status CHECK_FAILURE, nothing lands.

=======================================================================
LANDING RULE (SPEC section G2-A.8), branching on the Path B converted
COMPOSED cell at the PRIMARY leg. classify_landing() below is a pure
function so the rule is testable without a run.
=======================================================================
  A  [99.5, 100.5]  the composed cell survives at one decimal. Label only;
     no claim changes.
  B  [97.9365..., 99.5)  THE PROJECTION'S BRANCH (98.74). The cell moves by
     ~1.3pp and falls below 100. tex 432's "within 0.05\\% composed" is
     STRUCK or requalified; tex 576's "100.0\\% at one decimal" is RETAINED
     but relabeled as the mixed-basis measurement it is, with the converted
     companion beside it; tex 79/398/416/679 gain the labeled companion;
     tex 263/580 gain the convention parenthetical and the converted figure.
  C  < 97.9365...  (below the leg's own SHARED figure: the composition
     effect turned NEGATIVE). Contradicts C1 and the WAC arithmetic at once.
     STOP. Land nothing.
  D  > 100.5  the effect GREW under conversion. Converting the sample toward
     the book cannot enlarge the distance the reweight closes. STOP.

=======================================================================
MUST NOT CHANGE (SPEC section G2-A.9)
=======================================================================
The committed 2.49 / 3.9 artifact values (they are correct measurements under
their own conventions; the fix is a LABEL plus a converted COMPANION, never a
restatement); the headline marginal at every floor and every calibration-box
cell (G3c enforces); FLOOR values and FLOOR_MODE; tab:assembly and gate #98's
spans; the abstract (verified to carry no coupon literal and no composed
figure); the shared central 97.9 and null 88.7; the off-window 91.3 / 100.4;
gate #38's PSI literals including 2.29; the four committed artifacts (G9);
config.py; any .tex file -- this script writes ONLY its own artifact.

Run:  cd hazard && python3 coupon_convention_reweight.py
      cd hazard && python3 coupon_convention_reweight.py --selftest
      -> data/coupon_convention_reweight_results.json
         (+ temp parquets under data/coupon_convention/, deleted on exit)

Runtime budget: 8 two-regime reweight legs + 4 US-only invariance legs + 2
Path A sims + one FRED/SOMA fetch. Evidence: shared_layer_scoring runs one
two-regime microsim plus five shared-layer scorings; oos_identification
records 10.8s per regime-leg WITH bind instrumentation (none here). Expect
15-25 minutes; hard ceiling 60.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "abm", _REPO / "hazard"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fed_mbs_extension_risk as fed  # noqa: E402

import literature_hazard  # noqa: E402
from agents import MicrosimPool  # noqa: E402
from config import (  # noqa: E402
    LITERATURE_COEFS,
    LOAN_SAMPLE_PATH,
    MICROSIM_RESULTS_PATH,
    PANEL_PATH,
    RNG_SEED,
)
from extension_risk import score_extension_risk  # noqa: E402
from literature_hazard import rothstein_beta1  # noqa: E402
from macro import (  # noqa: E402
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data as fetch_data_hazard,
    fetch_soma_mbs_monthly,
)
from microsim_engine import run_qt_microsim  # noqa: E402
from shared_layer_scoring import score_on_shared_layer  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "coupon_convention"
RESULTS_JSON = DATA_DIR / "coupon_convention_reweight_results.json"

FULLBOOK_ARTIFACT = DATA_DIR / "full_book_weighting_results.json"
SHAREDLAYER_ARTIFACT = DATA_DIR / "shared_layer_scoring_results.json"
WALTAB_ARTIFACT = DATA_DIR / "wal_table_results.json"
COMPSHIFT_ARTIFACT = DATA_DIR / "composition_shift_results.json"
CALIB_ARTIFACT = DATA_DIR / "calibration_reconciliation_results.json"
NULL_ARTIFACT = DATA_DIR / "no_lockin_null_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
NULL_CACHE = DATA_DIR / "microsim_results_pq0.0.parquet"

# Byte-identity is asserted over exactly these four: three committed gates read
# them (#44 -> wal_table; :3155 and :3801 -> shared_layer; #38 -> composition
# _shift) and full_book_weighting is composition_shift's committed anchor.
FROZEN_ARTIFACTS = (FULLBOOK_ARTIFACT, SHAREDLAYER_ARTIFACT,
                    WALTAB_ARTIFACT, COMPSHIFT_ARTIFACT)

# ---- production convention --------------------------------------------------
PRODUCTION_FLOOR = 0.04
# Decimal literal, not percent/100: oos_identification quantized on the decimal
# and simulated exactly the double 0.04991, whereas 4.991/100.0 is a different
# double. The percent is asserted equal to the committed value at runtime.
OFFWINDOW_POINT_FLOOR = 0.04991
CENTRAL_PQ = 6.5
NULL_PQ = 0.0
COUPON_STEP = 0.005

# ---- the conversion (SPEC G2.1.2 + AMENDMENT G2-AM1) ------------------------
BASE_SERVICING = 0.0025            # 25bp, contractual conventional minimum
FLAT_GFEE = 0.0055                 # 55bp flat, 2017-2021 acquisitions
SAMPLE_VINTAGES = (2017, 2018, 2019, 2020, 2021)
# Empty BY DESIGN. Filling it is a spec amendment: SPEC G2.1.2 forbids writing
# a per-vintage g-fee that cannot be cited to an FHFA report year and table.
PER_VINTAGE_GFEE: dict[int, float] = {}
GFEE_PROVENANCE = {
    "primary": ("FLAT 55bp + 25bp base servicing = 0.80pp. FHFA Annual Report "
                "on Guarantee Fees Charged by Fannie Mae and Freddie Mac "
                "(HERA 1601 series), single-family acquisitions 2017-2021: "
                "the series sits in the mid-50s bp across 2017-2020 and is "
                "materially lower for 2021 acquisitions, but the per-year "
                "integers were NOT sourced at spec time and are deliberately "
                "not asserted."),
    "why_flat_is_primary": ("bucket grid 50bp; whole plausible 2017-2021 "
                            "dispersion <= ~12bp = 0.24 of a bucket, bounded "
                            "by the +/-10bp legs"),
    "per_vintage": "NOT SOURCED — flat primary carries",
    "report_year": None,
    "table": None,
    "omitted_from_phi": ("excess servicing above the 25bp base; buy-up/"
                         "buy-down to the 50bp TBA grid; LLPAs delivered as "
                         "upfront points — so phi is a LOWER bound on the "
                         "wedge and the converted effect an UPPER bound"),
}

# label -> total wedge in DECIMAL (g-fee + servicing)
DELTA_LEGS = {
    "phi_id": 0.0,
    "phi_060": 0.0060,
    "phi_lo": 0.0070,
    "phi_0": 0.0080,     # PRIMARY
    "phi_hi": 0.0090,
    "phi_ref": 0.0100,   # mechanism only; never printed as an economic result
}
PRIMARY_LEG = "phi_0"
ECONOMIC_LEGS = ("phi_060", "phi_lo", "phi_0", "phi_hi")   # phi_ref excluded

# ---- tolerances -------------------------------------------------------------
TOL_EXACT = 1e-9        # bit-exact replay of committed artifacts
TOL_ANALYTIC = 1e-15    # phi arithmetic
TOL_SOMA_WAC = 0.05     # composition_shift.py:340 A1_WAC_TOL
MATERIALITY_PP = 0.5    # on the converted composed cell
BOUNDARY_EPS = 1e-9

# ---- committed anchors (re-read at runtime; these pin them ex ante) ---------
COMMITTED_CENTRAL_B = 818.5300844066606
COMMITTED_NULL_B = 748.1850239867648
COMMITTED_CENTRAL_SHARE = 107.0326190295068
COMMITTED_FULLBOOK_B = 834.6397001192607
COMMITTED_FULLBOOK_SHARE = 109.13914436574825
COMMITTED_FULLBOOK_R_LAG0 = 0.27823879699900067
COMMITTED_FULLBOOK_PEAK_LAG = -3
COMMITTED_COMPOSED_B = 765.0774982466306
COMMITTED_COMPOSED_SHARE = 100.04305273304554
COMMITTED_COMPOSED_DANISH_B = 846.6912914390132
COMMITTED_SHARED_CENTRAL_SHARE = 97.9365273968041
COMMITTED_PATHA_BALANCE_SHARE = 121.46388911324269
COMMITTED_PATHA_FULLBOOK_SHARE = 127.45487776525697
COMMITTED_PATHA_COMPOSED_SHARE = 118.35878613255424
COMMITTED_CAP_BENCHMARK_B = 764.7482532227002
COMMITTED_CURTAILMENT_B = 69.56220187263008
COMMITTED_OFFSET_PP = 9.096091632702699
COMMITTED_OFFWINDOW_CENTRAL_B = 767.5264524465003
COMMITTED_OFFWINDOW_NULL_B = 724.9180585654117
COMMITTED_SAMPLE_WAC_UNWEIGHTED_PCT = 3.864892813333334
COMMITTED_BOOK_WAC_PCT = 2.49

# ---- the projection, fixed ex ante (SPEC G2-A.5) ---------------------------
PLAN_BALANCE_WEIGHTED_WAC_PCT = 3.78   # RE-VERIFY at step 0; see SPEC G2.9 #1
PROJECTED_COMPOSED_PCT = {
    "phi_060": 99.064, "phi_lo": 98.900, "phi_0": 98.737, "phi_hi": 98.573,
}
PROJECTED_FULLBOOK_PCT = {
    "phi_060": 108.160, "phi_lo": 107.996, "phi_0": 107.833, "phi_hi": 107.669,
}

# ---- landing branch edges --------------------------------------------------
BRANCH_A_LO, BRANCH_A_HI = 99.5, 100.5


def _json_default(x):
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gate(name: str, got, want, tol: float, report: dict) -> None:
    ok = abs(float(got) - float(want)) < tol
    report[name] = {"got": float(got), "want": float(want), "tol": tol,
                    "pass": bool(ok)}
    print(f"parity gate {name}: got {float(got):.10f} want {float(want):.10f} "
          f"[{'PASS' if ok else 'FAIL'}]")


def _flag(name: str, ok: bool, report: dict, detail: dict | None = None) -> None:
    report[name] = {"pass": bool(ok), **(detail or {})}
    print(f"parity gate {name}: [{'PASS' if ok else 'FAIL'}]"
          + (f"  {detail}" if detail else ""))


# ======================================================================
# phi — the conversion. Pure, vectorized, vintage-aware, side-effect free.
# ======================================================================
def make_converter(delta_total: float):
    """note rate -> pass-through equivalent, per vintage.

    Returns None for the identity so that callers can pass it straight through
    to reweight_to_soma_coupons and exercise the UNPATCHED code path — which is
    what makes G4/G5 a parity gate on the committed artifacts rather than on a
    reimplementation of them.
    """
    if delta_total == 0.0:
        return None

    def phi(coupon, vintage=None):
        c = np.asarray(coupon, dtype=np.float64)
        if PER_VINTAGE_GFEE and vintage is not None:
            v = np.asarray(vintage)
            g = np.full(c.shape, FLAT_GFEE, dtype=np.float64)
            for year, gfee in PER_VINTAGE_GFEE.items():
                g = np.where(v == year, gfee, g)
            out = c - (g + BASE_SERVICING)
        else:
            out = c - delta_total
        return float(out) if np.ndim(coupon) == 0 else out

    return phi


def bucket_of(coupon, step: float = COUPON_STEP):
    """agents.py:187's grid, transcribed for the diagnostics only."""
    return np.round(np.round(np.asarray(coupon, dtype=np.float64) / step)
                    * step, 4)


# ======================================================================
# Bucket diagnostics + the non-leakage gate, both on the REAL patched code
# path (a MicrosimPool is built and reweight_to_soma_coupons is called), so
# this is an exercise of the patch and not a copy of it.
# ======================================================================
def bucket_diagnostics(loans: pl.DataFrame, cohorts: list,
                       delta_total: float, report: dict,
                       tag: str) -> dict:
    phi = make_converter(delta_total)
    pool = MicrosimPool(loans, regime="US", rng=np.random.default_rng(RNG_SEED))
    coupon_before = pool.coupon.copy()

    soma_share: dict[float, float] = {}
    for c in cohorts:
        if int(c.get("term_months", 360)) != 360:
            continue
        b = round(round(float(c["coupon"]) / COUPON_STEP) * COUPON_STEP, 4)
        soma_share[b] = soma_share.get(b, 0.0) + float(c["weight"])
    tot = sum(soma_share.values())
    soma_share = {k: v / tot for k, v in soma_share.items()}

    src = pool.coupon if phi is None else np.asarray(
        phi(pool.coupon, pool.vintage), dtype=np.float64)
    buckets = bucket_of(src)
    bal = pool.balance
    total_bal = float(bal.sum())
    pre_share: dict[float, float] = {}
    for b in np.unique(buckets):
        pre_share[float(b)] = float(bal[buckets == b].sum()) / total_bal

    zeroed = sum(v for b, v in pre_share.items()
                 if not any(abs(b - s) < 1e-9 for s in soma_share))
    unreachable = sum(w for b, w in soma_share.items()
                      if not any(abs(b - s) < 1e-9 for s in pre_share))

    # realized bucket-shift split against the unconverted assignment
    base_buckets = bucket_of(pool.coupon)
    shift = np.round((buckets - base_buckets) / COUPON_STEP).astype(int)
    split = {int(k): float(bal[shift == k].sum()) / total_bal
             for k in np.unique(shift)}

    # G3a NON-LEAKAGE: reweight through the REAL routine, then check the note
    # rate never moved. A converted run that mutated pool.coupon would move the
    # rate gap and every number in this file would be void.
    pool.reweight_to_soma_coupons(cohorts, coupon_convert=phi)
    leak_free = bool(np.array_equal(pool.coupon, coupon_before))
    post_share: dict[float, float] = {}
    post_total = float(pool.balance.sum())
    for b in np.unique(buckets):
        post_share[float(b)] = (float(pool.balance[buckets == b].sum())
                                / post_total) if post_total > 0 else 0.0
    # the routine's own contract: reweighted balance share == SOMA share on
    # every bucket the sample can reach
    contract_err = max(
        (abs(post_share.get(b, 0.0) - w) for b, w in soma_share.items()
         if any(abs(b - s) < 1e-9 for s in pre_share)),
        default=0.0,
    ) if post_total > 0 else float("nan")

    _flag(f"G3a_no_leak_pool_coupon[{tag}]", leak_free, report,
          {"delta_total": delta_total})
    return {
        "delta_total": delta_total,
        "sample_share_by_bucket_pre": {f"{b:.4f}": v
                                       for b, v in sorted(pre_share.items())},
        "sample_share_by_bucket_post": {f"{b:.4f}": v
                                        for b, v in sorted(post_share.items())},
        "soma_share_by_bucket": {f"{b:.4f}": v
                                 for b, v in sorted(soma_share.items())},
        "zeroed_balance_share": float(zeroed),
        "unreachable_soma_weight_share": float(unreachable),
        "shift_split_buckets": {str(k): v for k, v in sorted(split.items())},
        "renormalized_share_contract_max_abs_err": float(contract_err),
        "pool_coupon_bit_identical": leak_free,
        "converted_balance_weighted_wac_pct": float(
            np.average(src, weights=bal) * 100.0),
    }


# ======================================================================
# One scored reweight leg (two regimes; standalone AND shared in one pass)
# ======================================================================
def run_reweight_leg(loans, macro_h, macro_abm, soma, empirical, cohorts,
                     delta_label: str, pq: float, tag: str) -> dict:
    phi = make_converter(DELTA_LEGS[delta_label])
    out_path = OUT_DIR / f"microsim_{tag}.parquet"
    try:
        res = run_qt_microsim(
            loan_sample=loans,
            macro=macro_h,
            seed=RNG_SEED,
            output=out_path,
            p_q_shock_pct=pq,
            soma_cohorts=cohorts,
            coupon_convert=phi,
        )
    finally:
        if out_path.exists():
            out_path.unlink()
    # G10 restoration, in line: a leaked floor or coefficient would silently
    # contaminate every later leg.
    assert literature_hazard.INVOLUNTARY_CPR_ANNUAL == PRODUCTION_FLOOR
    assert LITERATURE_COEFS["beta_burnout"] == -0.5

    standalone = score_extension_risk(res["US"], empirical)
    shared = score_on_shared_layer(macro_abm, soma,
                                   {"US": res["US"], "Danish": res["Danish"]})
    return {
        "tag": tag,
        "phi_label": delta_label,
        "delta_pp": DELTA_LEGS[delta_label] * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(standalone["hazard_trapped_b"]),
        "share_pct_standalone": float(standalone["share_explained_pct"]),
        "share_pct_shared": float(shared["share_pct"]),
        "shared_us_trapped_b": float(shared["us_trapped_b"]),
        "danish_trapped_b": float(shared["danish_trapped_b"]),
        "curtailment_netted_b": float(shared.get("curtailment_netted_b",
                                                 float("nan"))),
        "empirical_trapped_b": float(standalone["empirical_trapped_b"]),
        "cpr_r_lag0": (None if standalone["cross_correlation"].get(0) is None
                       else float(standalone["cross_correlation"][0])),
        "best_lag": (None if standalone.get("best_lag") is None
                     else int(standalone["best_lag"])),
        "peak_lag_r": float(standalone["peak_lag_r"]),
        "mean_us_cpr_pct": float(res["US"]["hazard_cpr_pct"].mean()),
        "_us_frame": res["US"],          # popped before serialization
        "_dk_frame": res["Danish"],
    }


# ======================================================================
# Invariance leg B8 (SPEC G2.4): production central/null, NO reweight.
# ======================================================================
def run_production_leg(loans, macro_h, empirical, floor: float, pq: float,
                       tag: str) -> dict:
    out_path = OUT_DIR / f"microsim_{tag}.parquet"
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    try:
        run_qt_microsim(
            loan_sample=loans,
            macro=macro_h,
            regimes=("US",),
            seed=RNG_SEED,
            output=out_path,
            p_q_shock_pct=pq,
        )
        sim = pd.read_parquet(out_path)
    finally:
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
        if out_path.exists():
            out_path.unlink()
    assert literature_hazard.INVOLUNTARY_CPR_ANNUAL == PRODUCTION_FLOOR
    score = score_extension_risk(sim, empirical)
    return {
        "tag": tag,
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
    }


# ======================================================================
# The pre-committed landing rule, as a pure function (the
# abstract_hedge_check convention in tools/liveness_gates.py: tests exercise
# THE RULE, not a copy of it).
# ======================================================================
def classify_landing(composed_pct: float,
                     shared_central_pct: float = COMMITTED_SHARED_CENTRAL_SHARE
                     ) -> str:
    if composed_pct > BRANCH_A_HI + BOUNDARY_EPS:
        return "D"
    if composed_pct >= BRANCH_A_LO - BOUNDARY_EPS:
        return "A"
    if composed_pct >= shared_central_pct - BOUNDARY_EPS:
        return "B"
    return "C"


def landing_text(branch: str, composed_pct: float) -> str:
    if branch == "A":
        return (
            "A: the composed cell survives at one decimal under a like-for-"
            f"like coupon basis ({composed_pct:.3f}%). Landing is LABELS ONLY "
            "— tex 79/398/416/576/679 keep their literals and gain the "
            "convention label; tex 263/580 gain the labeled pair. No claim "
            "changes; the run is reported as confirming that the mixed-basis "
            "comparison was not load-bearing."
        )
    if branch == "B":
        return (
            f"B: the composed cell moves to {composed_pct:.3f}% on a like-for-"
            "like coupon basis, below 100. LANDING (posture-adjacent): tex "
            "432's 'within 0.05\\% composed' is STRUCK or requalified — the "
            f"composed miss is {abs(100.0 - composed_pct):.2f} points, not "
            "0.05. tex 576's '100.0\\% at one decimal' and 'exactly 100.04\\%' "
            "are RETAINED but relabeled as the mixed-basis measurement they "
            "are, with the converted companion stated beside them; the "
            "sentence must not read as if 100.0% were the corrected number. "
            "tex 79/398/416/679 gain the labeled companion. tex 263/580 gain "
            "the convention parenthetical and the converted composition "
            "effect, and 580's 'bounds the sample-to-book extrapolation "
            "error' claim is re-checked: the bound TIGHTENS, which cuts for "
            "the paper and must be stated as such rather than quietly."
        )
    if branch == "C":
        return (
            f"C: converted composed {composed_pct:.3f}% sits BELOW the leg's "
            "own shared figure — the composition effect turned negative. This "
            "contradicts the C1 ordering check and the WAC arithmetic at once. "
            "STOP: land nothing, and treat it as evidence that the balance-"
            "weighted sample WAC is not what SPEC G2.9 #1 assumed, or that "
            "phi is applied to the wrong side."
        )
    return (
        f"D: converted composed {composed_pct:.3f}% EXCEEDS the committed "
        "cell — the effect grew under conversion. Converting the sample "
        "toward the book cannot enlarge the distance the reweight closes. "
        "STOP: wiring alarm, land nothing."
    )


# ======================================================================
def _selftest(report: dict) -> None:
    """--selftest: free gates only. No engine, no artifact, no network beyond
    the SOMA cohort fetch. Exercises PATCH_G2A hunks 1-3 end to end."""
    probe = np.array([0.0200, 0.0249, 0.0300, 0.0350,
                      0.0386, 0.0450, 0.0500])
    phi0 = make_converter(DELTA_LEGS[PRIMARY_LEG])
    for v in SAMPLE_VINTAGES:
        got = phi0(probe, np.full(probe.shape, v))
        _gate(f"G2_phi_primary_v{v}", float(np.max(np.abs(
            got - (probe - DELTA_LEGS[PRIMARY_LEG])))), 0.0, TOL_ANALYTIC,
            report)
    _flag("G2_phi_identity_is_none", make_converter(0.0) is None, report)

    loans = pl.read_parquet(LOAN_SAMPLE_PATH)
    cohorts = fed.fetch_soma_mbs_cohorts()
    # G3b SEAM INERTNESS: coupon_convert=phi_id must give a bucket vector
    # bit-identical to coupon_convert=None. Without this, a movement in the
    # converted legs could be the patch rather than the wedge.
    pool_a = MicrosimPool(loans, regime="US",
                          rng=np.random.default_rng(RNG_SEED))
    pool_b = MicrosimPool(loans, regime="US",
                          rng=np.random.default_rng(RNG_SEED))
    before = pool_a.coupon.copy()
    pool_a.reweight_to_soma_coupons(cohorts)
    pool_b.reweight_to_soma_coupons(cohorts, coupon_convert=None)
    _flag("G3b_seam_inert_at_identity",
          bool(np.array_equal(pool_a.balance, pool_b.balance)
               and np.array_equal(pool_a.coupon, before)
               and np.array_equal(pool_b.coupon, before)),
          report)
    print("\nselftest complete — free gates only, no artifact written.")


def main() -> None:
    selftest = "--selftest" in sys.argv
    assert RNG_SEED == 42, f"RNG_SEED must be 42, got {RNG_SEED}"
    assert literature_hazard.FLOOR_MODE == "max", "production floor form is max"
    assert literature_hazard.INVOLUNTARY_CPR_ANNUAL == PRODUCTION_FLOOR
    assert abs(FLAT_GFEE + BASE_SERVICING - DELTA_LEGS[PRIMARY_LEG]) < 1e-15, (
        "the primary leg must equal the pinned g-fee plus base servicing"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict = {}

    if selftest:
        _selftest(report)
        return

    t0 = time.perf_counter()
    frozen_before = {p.name: _sha256(p) for p in FROZEN_ARTIFACTS}

    # ---- committed anchors, read at runtime and pinned --------------------
    fullbook = json.loads(FULLBOOK_ARTIFACT.read_text())
    sharedlayer = json.loads(SHAREDLAYER_ARTIFACT.read_text())["results"]
    calib = json.loads(CALIB_ARTIFACT.read_text())
    anchor = json.loads(NULL_ARTIFACT.read_text())
    oos = json.loads(OOS_ARTIFACT.read_text())

    for got, want in (
        (fullbook["sample_wac_pct"], COMMITTED_SAMPLE_WAC_UNWEIGHTED_PCT),
        (fullbook["path_b"]["balance_weighted"]["share_pct"],
         COMMITTED_CENTRAL_SHARE),
        (fullbook["path_b"]["full_book_weighted"]["trapped_b"],
         COMMITTED_FULLBOOK_B),
        (fullbook["path_b"]["full_book_weighted"]["share_pct"],
         COMMITTED_FULLBOOK_SHARE),
        (fullbook["path_a"]["balance_weighted"]["share_pct"],
         COMMITTED_PATHA_BALANCE_SHARE),
        (fullbook["path_a"]["full_book_weighted"]["share_pct"],
         COMMITTED_PATHA_FULLBOOK_SHARE),
        (sharedlayer["path_b_fullbook_composed"]["us_trapped_b"],
         COMMITTED_COMPOSED_B),
        (sharedlayer["path_b_fullbook_composed"]["share_pct"],
         COMMITTED_COMPOSED_SHARE),
        (sharedlayer["path_b_central"]["share_pct"],
         COMMITTED_SHARED_CENTRAL_SHARE),
        (sharedlayer["path_a_fullbook_composed"]["share_pct"],
         COMMITTED_PATHA_COMPOSED_SHARE),
        (anchor["central_trapped_b"], COMMITTED_CENTRAL_B),
        (anchor["null_trapped_b"], COMMITTED_NULL_B),
    ):
        assert abs(got - want) < TOL_EXACT, (got, want)

    off_point = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off_point - OFFWINDOW_POINT_FLOOR * 100) < TOL_EXACT
    off_row = next(r for r in oos["instrument1_marginal_table"]
                   if abs(r["floor_annual_cpr_pct"] - off_point) < TOL_EXACT)
    off_central_committed = off_row["band"]["6.5"]["central_trapped_b"]
    off_null_committed = off_row["null_trapped_b"]
    assert abs(off_central_committed - COMMITTED_OFFWINDOW_CENTRAL_B) < TOL_EXACT
    assert abs(off_null_committed - COMMITTED_OFFWINDOW_NULL_B) < TOL_EXACT

    basis = calib["basis_map"]
    offset_pp = float(basis["offset_pp"])
    cap_b = float(basis["cap_benchmark_b"])
    curtail_b = float(basis["curtailment_netted_b"])
    assert abs(offset_pp - COMMITTED_OFFSET_PP) < TOL_EXACT

    # ------------------------------------------------------------------
    # FREE GATES — no engine. Fail here rather than after 20 minutes.
    # ------------------------------------------------------------------
    print("\n--- free gates (no microsim) ---")
    _gate("G7_offset_pp_internal", offset_pp, curtail_b / cap_b * 100.0,
          TOL_EXACT, report)
    probe = np.array([0.0200, 0.0249, 0.0300, 0.0350, 0.0386, 0.0450, 0.0500])
    for label, d in DELTA_LEGS.items():
        phi = make_converter(d)
        if phi is None:
            continue
        for v in SAMPLE_VINTAGES:
            err = float(np.max(np.abs(
                phi(probe, np.full(probe.shape, v)) - (probe - d))))
            _gate(f"G2_phi[{label}]_v{v}", err, 0.0, TOL_ANALYTIC, report)
    _flag("G2_phi_identity_is_none", make_converter(0.0) is None, report)

    print("\nFetching macro frames, SOMA rolloff, and SOMA coupon cohorts …")
    macro_h = calculate_dynamic_friction(fetch_data_hazard())
    macro_abm = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro_h,
                                        soma_rolloff=fetch_soma_mbs_monthly())
    cohorts = fed.fetch_soma_mbs_cohorts()
    cohorts_fingerprint = json.dumps(
        [(round(float(c["coupon"]), 6), round(float(c["weight"]), 12),
          int(c.get("term_months", 360))) for c in cohorts], sort_keys=True)

    soma_wac_30 = (sum(c["coupon"] * c["weight"] for c in cohorts) * 100.0)
    _gate("G1_soma_cohort_wac_pct", soma_wac_30, COMMITTED_BOOK_WAC_PCT,
          TOL_SOMA_WAC, report)

    for p in (MICROSIM_RESULTS_PATH, NULL_CACHE, LOAN_SAMPLE_PATH):
        if not p.exists():
            raise FileNotFoundError(f"{p} missing — build via production first")
    cache_central = score_extension_risk(
        pd.read_parquet(MICROSIM_RESULTS_PATH), empirical)
    cache_null = score_extension_risk(pd.read_parquet(NULL_CACHE), empirical)
    _gate("G0_benchmark_frame_b", cache_central["empirical_trapped_b"],
          COMMITTED_CAP_BENCHMARK_B, TOL_EXACT, report)
    _gate("G0b_committed_central_cache_b", cache_central["hazard_trapped_b"],
          COMMITTED_CENTRAL_B, TOL_EXACT, report)
    _gate("G0c_committed_null_cache_b", cache_null["hazard_trapped_b"],
          COMMITTED_NULL_B, TOL_EXACT, report)

    loans = pl.read_parquet(LOAN_SAMPLE_PATH)
    # SPEC G2.9 #1: re-derive the balance-weighted sample WAC rather than
    # trusting the PLAN's 3.78. It sets g0 in the projection.
    _c = loans["coupon"].to_numpy().astype(np.float64)
    _bal = loans["balance"].to_numpy().astype(np.float64)
    sample_wac = {
        "unweighted_note_pct": float(_c.mean() * 100.0),
        "balance_weighted_note_pct": float(np.average(_c, weights=_bal) * 100.0),
        "book_face_weighted_passthrough_pct": float(soma_wac_30),
        "plan_assumed_balance_weighted_pct": PLAN_BALANCE_WEIGHTED_WAC_PCT,
    }
    sample_wac["balance_weighted_passthrough_equivalent_pct"] = (
        sample_wac["balance_weighted_note_pct"]
        - DELTA_LEGS[PRIMARY_LEG] * 100.0)
    _gate("G0d_sample_wac_unweighted_parity", sample_wac["unweighted_note_pct"],
          COMMITTED_SAMPLE_WAC_UNWEIGHTED_PCT, TOL_EXACT, report)
    print(f"  balance-weighted sample WAC (re-derived): "
          f"{sample_wac['balance_weighted_note_pct']:.6f}%  "
          f"(PLAN assumed {PLAN_BALANCE_WEIGHTED_WAC_PCT})")

    # ---- G3a/G3b + bucket diagnostics, on the real patched code path -----
    print("\n--- seam and bucket diagnostics (no engine) ---")
    pool_a = MicrosimPool(loans, regime="US",
                          rng=np.random.default_rng(RNG_SEED))
    pool_b = MicrosimPool(loans, regime="US",
                          rng=np.random.default_rng(RNG_SEED))
    coupon_before = pool_a.coupon.copy()
    pool_a.reweight_to_soma_coupons(cohorts)
    pool_b.reweight_to_soma_coupons(cohorts, coupon_convert=None)
    _flag("G3b_seam_inert_at_identity",
          bool(np.array_equal(pool_a.balance, pool_b.balance)
               and np.array_equal(pool_a.coupon, coupon_before)
               and np.array_equal(pool_b.coupon, coupon_before)),
          report)
    diagnostics = {
        label: bucket_diagnostics(loans, cohorts, d, report, label)
        for label, d in DELTA_LEGS.items()
    }

    free_fail = [k for k, v in report.items() if not v["pass"]]
    if free_fail:
        raise SystemExit(
            "PRECONDITION FAILURE (free gates) — run is VOID, no artifact "
            f"written: {free_fail}"
        )

    # ------------------------------------------------------------------
    # ENGINE LEGS — Path B reweight, two regimes
    # ------------------------------------------------------------------
    legs: dict[str, dict] = {}
    print("\n--- Path B reweight legs (two regimes; standalone + shared) ---")
    for label in DELTA_LEGS:
        print(f"  leg central [{label}] delta {DELTA_LEGS[label]*100:.2f}pp …")
        legs[f"central_{label}"] = run_reweight_leg(
            loans, macro_h, macro_abm, soma, empirical, cohorts,
            label, CENTRAL_PQ, f"central_{label}")
    for label in ("phi_id", PRIMARY_LEG):
        print(f"  leg null    [{label}] …")
        legs[f"null_{label}"] = run_reweight_leg(
            loans, macro_h, macro_abm, soma, empirical, cohorts,
            label, NULL_PQ, f"null_{label}")

    _flag("G1_soma_cohorts_unchanged_across_legs",
          cohorts_fingerprint == json.dumps(
              [(round(float(c["coupon"]), 6), round(float(c["weight"]), 12),
                int(c.get("term_months", 360))) for c in cohorts],
              sort_keys=True),
          report)

    idc = legs["central_phi_id"]
    _gate("G4_phi_id_fullbook_b", idc["trapped_b"], COMMITTED_FULLBOOK_B,
          TOL_EXACT, report)
    _gate("G4_phi_id_fullbook_share", idc["share_pct_standalone"],
          COMMITTED_FULLBOOK_SHARE, TOL_EXACT, report)
    _gate("G4_phi_id_fullbook_r_lag0", idc["cpr_r_lag0"],
          COMMITTED_FULLBOOK_R_LAG0, TOL_EXACT, report)
    _flag("G4_phi_id_fullbook_peak_lag",
          idc["best_lag"] == COMMITTED_FULLBOOK_PEAK_LAG, report,
          {"got": idc["best_lag"], "want": COMMITTED_FULLBOOK_PEAK_LAG})
    _gate("G5_phi_id_composed_b", idc["shared_us_trapped_b"],
          COMMITTED_COMPOSED_B, TOL_EXACT, report)
    _gate("G5_phi_id_composed_share", idc["share_pct_shared"],
          COMMITTED_COMPOSED_SHARE, TOL_EXACT, report)
    _gate("G5_phi_id_composed_danish_b", idc["danish_trapped_b"],
          COMMITTED_COMPOSED_DANISH_B, TOL_EXACT, report)
    _gate("G5_phi_id_curtailment_b", idc["curtailment_netted_b"],
          COMMITTED_CURTAILMENT_B, TOL_EXACT, report)
    _gate("G5_phi_id_empirical_b", idc["empirical_trapped_b"],
          COMMITTED_CAP_BENCHMARK_B, TOL_EXACT, report)
    for name, leg in legs.items():
        _gate(f"G7_basis_identity[{name}]",
              leg["share_pct_standalone"] - leg["share_pct_shared"],
              offset_pp, TOL_EXACT, report)

    # ------------------------------------------------------------------
    # ENGINE LEGS — Path A (cohort GLM). Skipped-and-disclosed if the panel
    # is absent; never approximated (SPEC G2.9 #7).
    # ------------------------------------------------------------------
    path_a: dict = {}
    path_a_status = "ok"
    if not PANEL_PATH.exists():
        path_a_status = (f"SKIPPED — {PANEL_PATH.name} absent; the Path A "
                         "converted leg is disclosed as not run, not "
                         "approximated")
        print(f"\n--- Path A: {path_a_status} ---")
    else:
        from simulate import simulate_qt_window  # noqa: E402  (needs the panel)
        print("\n--- Path A reweight legs ---")
        for label in ("phi_id", PRIMARY_LEG):
            tmp = OUT_DIR / f"patha_{label}.parquet"
            try:
                sim = simulate_qt_window(
                    soma_cohorts=cohorts, output=tmp,
                    coupon_convert=make_converter(DELTA_LEGS[label]))
            finally:
                if tmp.exists():
                    tmp.unlink()
            standalone = score_extension_risk(sim, empirical)
            # shared_layer_scoring.py:145 borrows Path B's Danish leg at the
            # SAME phi purely to satisfy the layer's two-regime interface;
            # only Path A's U.S. numbers are reported. Mirrored exactly, or
            # the committed 118.35878613255424 is not reproducible.
            shared = score_on_shared_layer(
                macro_abm, soma,
                {"US": sim, "Danish": legs[f"central_{label}"]["_dk_frame"]})
            path_a[label] = {
                "phi_label": label,
                "delta_pp": DELTA_LEGS[label] * 100.0,
                "trapped_b": float(standalone["hazard_trapped_b"]),
                "share_pct_standalone": float(standalone["share_explained_pct"]),
                "share_pct_shared": float(shared["share_pct"]),
            }
        _gate("G6_patha_phi_id_fullbook_share",
              path_a["phi_id"]["share_pct_standalone"],
              COMMITTED_PATHA_FULLBOOK_SHARE, TOL_EXACT, report)
        _gate("G6_patha_phi_id_composed_share",
              path_a["phi_id"]["share_pct_shared"],
              COMMITTED_PATHA_COMPOSED_SHARE, TOL_EXACT, report)

    # ------------------------------------------------------------------
    # INVARIANCE LEG B8 (SPEC G2.4) — run AFTER every converted leg, so
    # leaked state would be present if it existed.
    # ------------------------------------------------------------------
    print("\n--- invariance leg B8: production central/null, NO reweight ---")
    inv = {
        "central_floor4": run_production_leg(loans, macro_h, empirical,
                                             PRODUCTION_FLOOR, CENTRAL_PQ,
                                             "inv_central_floor4"),
        "null_floor4": run_production_leg(loans, macro_h, empirical,
                                          PRODUCTION_FLOOR, NULL_PQ,
                                          "inv_null_floor4"),
        "central_floor4991": run_production_leg(loans, macro_h, empirical,
                                                OFFWINDOW_POINT_FLOOR,
                                                CENTRAL_PQ,
                                                "inv_central_floor4991"),
        "null_floor4991": run_production_leg(loans, macro_h, empirical,
                                             OFFWINDOW_POINT_FLOOR, NULL_PQ,
                                             "inv_null_floor4991"),
    }
    _gate("G3c_invariance_central_4pct", inv["central_floor4"]["trapped_b"],
          COMMITTED_CENTRAL_B, TOL_EXACT, report)
    _gate("G3c_invariance_null_4pct", inv["null_floor4"]["trapped_b"],
          COMMITTED_NULL_B, TOL_EXACT, report)
    _gate("G3c_invariance_central_4991", inv["central_floor4991"]["trapped_b"],
          COMMITTED_OFFWINDOW_CENTRAL_B, TOL_EXACT, report)
    _gate("G3c_invariance_null_4991", inv["null_floor4991"]["trapped_b"],
          COMMITTED_OFFWINDOW_NULL_B, TOL_EXACT, report)
    _gate("G3c_invariance_marginal_b_4pct",
          inv["central_floor4"]["trapped_b"] - inv["null_floor4"]["trapped_b"],
          anchor["lockin_marginal_b"], TOL_EXACT, report)
    _gate("G3c_invariance_marginal_pp_4pct",
          inv["central_floor4"]["share_pct"] - inv["null_floor4"]["share_pct"],
          anchor["lockin_marginal_share_pp"], TOL_EXACT, report)
    _gate("G3c_invariance_marginal_b_4991",
          (inv["central_floor4991"]["trapped_b"]
           - inv["null_floor4991"]["trapped_b"]),
          COMMITTED_OFFWINDOW_CENTRAL_B - COMMITTED_OFFWINDOW_NULL_B,
          TOL_EXACT, report)

    runtime_s = time.perf_counter() - t0

    # ---- G9: the committed artifacts must be byte-identical ---------------
    frozen_after = {p.name: _sha256(p) for p in FROZEN_ARTIFACTS}
    for name, before_hash in frozen_before.items():
        _flag(f"G9_frozen_artifact[{name}]",
              frozen_after[name] == before_hash, report,
              {"sha256_before": before_hash, "sha256_after": frozen_after[name]})
    _flag("G10_no_temp_parquet_left",
          not list(OUT_DIR.glob("*.parquet")), report)

    # ------------------------------------------------------------------
    # Projection, ordering check, landing branch
    # ------------------------------------------------------------------
    committed_effect_pp = COMMITTED_FULLBOOK_SHARE - COMMITTED_CENTRAL_SHARE
    g0 = (sample_wac["balance_weighted_note_pct"]
          - sample_wac["book_face_weighted_passthrough_pct"])
    projection = {}
    for label in ECONOMIC_LEGS:
        d_pp = DELTA_LEGS[label] * 100.0
        g1 = g0 - d_pp
        ratio = g1 / g0 if g0 else float("nan")
        proj_fb = COMMITTED_CENTRAL_SHARE + committed_effect_pp * ratio
        realized_fb = legs[f"central_{label}"]["share_pct_standalone"]
        realized_comp = legs[f"central_{label}"]["share_pct_shared"]
        projection[label] = {
            "delta_pp": d_pp,
            "g0_pp": g0,
            "g1_pp": g1,
            "ratio_g1_over_g0": ratio,
            "projected_effect_pp": committed_effect_pp * ratio,
            "projected_fullbook_pct_rederived": proj_fb,
            "projected_fullbook_pct_ex_ante": PROJECTED_FULLBOOK_PCT[label],
            "projected_composed_pct_ex_ante": PROJECTED_COMPOSED_PCT[label],
            "realized_fullbook_pct": realized_fb,
            "realized_composed_pct": realized_comp,
            "realized_effect_pp": realized_fb - COMMITTED_CENTRAL_SHARE,
            "deviation_vs_ex_ante_pp": (realized_comp
                                        - PROJECTED_COMPOSED_PCT[label]),
            "within_materiality_band_0p5": bool(
                abs(realized_comp - PROJECTED_COMPOSED_PCT[label])
                <= MATERIALITY_PP + BOUNDARY_EPS),
        }

    fb = {lbl: legs[f"central_{lbl}"]["share_pct_standalone"]
          for lbl in ECONOMIC_LEGS}
    bracket_ok = all(COMMITTED_CENTRAL_SHARE < v < COMMITTED_FULLBOOK_SHARE
                     for v in fb.values())
    ordered = [fb[lbl] for lbl in ("phi_060", "phi_lo", "phi_0", "phi_hi")]
    monotone_ok = all(ordered[i] > ordered[i + 1] for i in range(len(ordered) - 1))
    _flag("C1_ordering_bracket", bracket_ok, report, {"fullbook_by_leg": fb})
    _flag("C1_ordering_monotone_in_delta", monotone_ok, report,
          {"phi_060_to_phi_hi": ordered})

    primary_composed = legs[f"central_{PRIMARY_LEG}"]["share_pct_shared"]
    branch = classify_landing(primary_composed, COMMITTED_SHARED_CENTRAL_SHARE)
    hard_fail = [k for k, v in report.items() if not v["pass"]]
    status = ("OK" if not hard_fail
              else ("CHECK_FAILURE"
                    if all(k.startswith("C1_") for k in hard_fail)
                    else "GATE_FAILURE"))

    reweighted_marginal = {}
    for label in ("phi_id", PRIMARY_LEG):
        c, n = legs[f"central_{label}"], legs[f"null_{label}"]
        reweighted_marginal[label] = {
            "marginal_b": c["trapped_b"] - n["trapped_b"],
            "marginal_pp": (c["share_pct_standalone"]
                            - n["share_pct_standalone"]),
        }
    reweighted_marginal["note"] = (
        "A reweighted pool is a DIFFERENT POPULATION and its marginal is a "
        "different object. This is NOT the identified marginal, it is NOT "
        "required to be invariant, and no headline quantity may be restated "
        "from it. It is reported because the natural referee question — did "
        "the coupon-convention error contaminate the identified quantity? — "
        "deserves a measured answer and not only the unreachability argument "
        "that G3c tests."
    )

    for leg in legs.values():
        leg.pop("_us_frame", None)
        leg.pop("_dk_frame", None)

    payload = {
        "mode": "coupon_convention_reweight",
        "status": status,
        "spec": (
            "SPEC_round28_G2_coupon_convention.md section G2-A as amended by "
            "G2-AM1: sample NOTE rates converted to PASS-THROUGH equivalents "
            "(flat 55bp g-fee + 25bp base servicing = 0.80pp primary; legs "
            "0.60/0.70/0.80/0.90 economic, 1.00 mechanism-only) on a LOCAL "
            "COPY inside reweight_to_soma_coupons / _reweight_balances_to_soma "
            "only; full-book standalone and composed shared cells from one "
            "two-regime run per leg; seed 42, committed 75k sample, floor "
            "4.0%, hard-max floor form, one shared macro frame per basis; "
            "bit-exact parity G0-G7, non-leakage G3a/G3b, invariance G3c at "
            "both floors, byte-identity G9 on four committed artifacts; "
            "landing branches A/B/C/D on the primary converted composed cell "
            "with materiality +/-0.5pp"
        ),
        "parity_tolerance": TOL_EXACT,
        "conversion": {
            "rule": "c_pt = c_note - (g_v + 0.0025)",
            "gfee_provenance": GFEE_PROVENANCE,
            "flat_gfee_decimal": FLAT_GFEE,
            "servicing_decimal": BASE_SERVICING,
            "legs_delta_decimal": DELTA_LEGS,
            "primary_leg": PRIMARY_LEG,
            "economic_legs": list(ECONOMIC_LEGS),
            "mechanism_only_leg": "phi_ref",
            "vintage_column": "vintage",
            "vintages_expected": list(SAMPLE_VINTAGES),
            "per_vintage_gfee_used": PER_VINTAGE_GFEE or None,
            "amendment": ("G2-AM1 2026-07-29: leg set widened to include "
                          "delta 0.60, which brackets the G1 diagnosis's "
                          "assumed ~0.5-0.6pp; primary remains 0.80"),
        },
        "basis_map": {
            "curtailment_netted_b": curtail_b,
            "cap_benchmark_b": cap_b,
            "offset_pp": offset_pp,
            "note": ("shared = standalone - offset_pp; the composed cell IS "
                     "the full-book cell minus this flat wedge, verified "
                     "against the committed pair to 2e-14"),
        },
        "sample_wac": sample_wac,
        "legs": legs,
        "path_a": path_a,
        "path_a_status": path_a_status,
        "invariance": inv,
        "reweighted_marginal": reweighted_marginal,
        "bucket_diagnostics": diagnostics,
        "projection": projection,
        "committed": {
            "central_share_standalone": COMMITTED_CENTRAL_SHARE,
            "fullbook_share_standalone": COMMITTED_FULLBOOK_SHARE,
            "composed_share_shared": COMMITTED_COMPOSED_SHARE,
            "shared_central_share": COMMITTED_SHARED_CENTRAL_SHARE,
            "composition_effect_pp": committed_effect_pp,
        },
        "materiality_pp": MATERIALITY_PP,
        "parity_gates": report,
        "parity_gates_all_pass": not hard_fail,
        "landing_branch": branch,
        "landing_rule": landing_text(branch, primary_composed),
        "frozen_artifact_sha256": {"before": frozen_before,
                                   "after": frozen_after},
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1, default=_json_default)

    # ------------------------------------------------------------------
    print("\n" + "=" * 78)
    print(" COUPON-CONVENTION REWEIGHT — committed vs converted")
    print("=" * 78)
    print(f"  {'leg':<10}{'delta pp':>10}{'full-book %':>14}"
          f"{'composed %':>13}{'proj composed':>15}{'dev':>8}")
    print(f"  {'committed':<10}{0.0:>10.2f}{COMMITTED_FULLBOOK_SHARE:>14.4f}"
          f"{COMMITTED_COMPOSED_SHARE:>13.4f}{'--':>15}{'--':>8}")
    for label in DELTA_LEGS:
        leg = legs[f"central_{label}"]
        pr = projection.get(label)
        print(f"  {label:<10}{leg['delta_pp']:>10.2f}"
              f"{leg['share_pct_standalone']:>14.4f}"
              f"{leg['share_pct_shared']:>13.4f}"
              + (f"{pr['projected_composed_pct_ex_ante']:>15.3f}"
                 f"{pr['deviation_vs_ex_ante_pp']:>+8.3f}"
                 if pr else f"{'mechanism only':>15}{'--':>8}"))
    print("-" * 78)
    print(f"  conversion-uncertainty span (0.60 vs 0.80 legs): "
          f"{abs(legs['central_phi_060']['share_pct_shared'] - primary_composed):.4f}pp")
    print(f"  balance-weighted sample WAC "
          f"{sample_wac['balance_weighted_note_pct']:.4f}% note -> "
          f"{sample_wac['balance_weighted_passthrough_equivalent_pct']:.4f}% "
          f"pass-through vs book {sample_wac['book_face_weighted_passthrough_pct']:.4f}%")
    print(f"  INVARIANCE (G3c): marginal "
          f"{inv['central_floor4']['trapped_b'] - inv['null_floor4']['trapped_b']:.10f}B "
          f"@4.0%, "
          f"{inv['central_floor4991']['trapped_b'] - inv['null_floor4991']['trapped_b']:.10f}B "
          f"@4.991%  (must be bit-exact)")
    print(f"  reweighted marginal (reported, obliging only itself): "
          f"{reweighted_marginal['phi_id']['marginal_pp']:+.4f}pp at identity, "
          f"{reweighted_marginal[PRIMARY_LEG]['marginal_pp']:+.4f}pp converted")
    print("=" * 78)
    print(f"landing branch {branch}: {payload['landing_rule']}")
    print(f"status {status}   gates all pass: {not hard_fail}   "
          f"runtime {runtime_s:,.0f}s")
    print(f"Saved: {RESULTS_JSON}")
    if hard_fail:
        raise SystemExit(f"PARITY/CHECK FAILURE — do not build on this: "
                         f"{hard_fail}")


if __name__ == "__main__":
    main()
