#!/usr/bin/env python3
"""
floor_inference_correction_v2.py — the floor-read inference layer re-run with
Webb six-point weights, a data-driven Bell-McCaffrey/Imbens-Kolesar df, the
Carter-Schnepel-Steigerwald effective cluster count, and a restricted (WCR)
inversion CI (round-28 WP-C1; REVIEW2 R1-W1 / DA-C1: the committed correction
reports neither its weight scheme's alternatives, nor a small-sample df, nor
an effective cluster count, nor the restricted construction MacKinnon-Webb
recommend, and its leverage vector and t* draws were computed and discarded).

PRE-COMMITTED SPEC (fixed in this header BEFORE any run; committed before
first execution; full drafting spec at specs/SPEC_round28_C1_C2_C3_C6.md
SPEC C1, whose gates, expectations and landing rule are adopted unchanged).

V1 IS FROZEN. hazard/floor_inference_correction.py and
hazard/data/floor_inference_correction_results.json are the committed
provenance for tex 592/677. This script reads the v1 artifact and never
writes to it; it writes only to the three v2 paths named under Run below.

DESIGN. NO microsim engine runs anywhere. One FRED MORTGAGE30US fetch via
mdr.build_panel. Selection, aggregation, cluster unit and the floor->marginal
PCHIP are IMPORTED from the committed machinery (fu._select, fu.LEG_2018,
fu.CALIB_WINDOW, fu.cluster_bootstrap_cpr, fu._map_draws; mdr.build_panel,
mdr.cpr_of, mdr.FloorMapping; stratum.build_stratum_id), not reimplemented.
cpr_pct_of_smm, cluster_sums, cr_ses, map_endpoint, map_floor_ci and the four
READ_SELECTIONS are VERBATIM copies of v1's; wild_t_ci is v1's with the weight
scheme switchable and nothing else touched, which is what gate P4 verifies.
Reads R1-R4 as in v1 (R5 excluded ex ante). Primary object stays R2
(G=31, point 4.990624060575566% -> +5.5716pp).

THE FIVE CHANGES (SPEC C1.2):
 (1) WEBB six-point weights, primary. s in {-sqrt(3/2), -1, -sqrt(1/2),
     +sqrt(1/2), +1, +sqrt(3/2)} each w.p. 1/6 (Webb 2014; E[s]=0, E[s^2]=1,
     E[s^4]=7/6, verified numerically as gate P7). B=9999, fresh
     default_rng(42) per read per procedure. The Rademacher interval is
     recomputed in the same run under the same convention and REPORTED
     ALONGSIDE, gated bit-exact against the v1 artifact (P4). Both reported;
     the Webb line is primary. Webb's few-distinct-sign-patterns motivation
     does NOT bind here (2^31 ~ 2.1e9 >> B); the operative term is
     (E[s^4]-1)/G_eff.
 (2) BM/IK data-driven df, computed FROM THE CONSTRUCTION, never from a
     closed-form recollection. Working model A_g = R*W_g + eps_g with
     Var(eps_g) prop-to W_g; its WLS leverage is h_g = W_g/sum(W), exactly
     the h v1 already computes, so CR2's u_g/sqrt(1-h_g) is the correct BM
     adjustment for that model. V = sum_g (g_g'A)^2 with
     g_g[j] = (delta_gj - h_g)/(sumW*(1-h_g)^p); under the working
     Omega = diag(W)/sumW = diag(h) the cross terms collapse via sum_j h_j=1
     to  M_gk prop-to (delta_gk*h_g - h_g*h_k)/((1-h_g)^p (1-h_k)^p), and
     df = (tr M)^2/tr(M M') = (sum lambda)^2/(sum lambda^2). p = 0/0.5/1 gives
     CR1/CR2/CR3; the headline df_bm is CR2's. MANDATORY BLOCKING SELF-TEST
     (P6): h == 1/G must return df = G-1 to 1e-8, else STOP and report no df.
     df enters CR2/CR3 only (secondary, no rule attached, as in v1).
 (3) CSS effective clusters. G* = G/(1+Gamma), Gamma = (1/G)sum((g_g-gbar)
     /gbar)^2; for this intercept-only estimator gamma_g prop-to h_g and
     sum h = 1, so Gamma = G*sum(h^2) - 1 and G* = 1/sum(h^2) exactly — the
     Herfindahl-inverse convention already used for the loan/stratum scheme
     (bootstrap_pathb_cluster.py:44-48, committed effective_n_clusters
     25.77710660741266). Using ONE convention in both places is a hard
     requirement: otherwise tab:uncertainty's tablenote compares two
     different objects. Reported for all four reads with sum(h^2) and h_max.
     Ex-ante bound, derivable with no run: sum(h^2) >= h_max^2, so R2's
     G* <= 1/0.33233^2 = 9.05 on G=31; R3 <= 6.87 on 25; R4 <= 36.3 on 226.
 (4) WCR restricted-inversion CI, reported, no rule attached. 401 candidate
     R0 over R_hat +/- 5*SE_CR1 on the SMM scale; restricted residuals
     A_g - R0*W_g; Webb weights (ONE draw set reused across the grid);
     retain R0 iff t(R0) in [q2.5, q97.5](t*(R0)); the retained set's
     endpoints mapped through the PCHIP. LABELED: per SPEC C1.2(4) literal,
     the observed statistic is studentized by the UNRESTRICTED SE_CR1 while
     SE* is recomputed on each restricted resample — recorded in the artifact
     so it is not mistaken for the symmetric textbook variant.
 (5) v1's truncation convention KEPT: an endpoint outside the grid is mapped
     AT the nearest edge and flagged truncated_at_grid_edge, never
     extrapolated and never excluded (that is _map_draws's convention,
     deliberately not adopted). Flags reported. FP2-B1 (2026-08-29): the
     grid is the committed sweep PLUS the frozen floor_grid_extension rows —
     support [2.0, 7.0]% CPR; every committed censored endpoint (max 6.6733)
     now maps inside. Same PCHIP rule, extended support.

STRUCTURAL POINT, FIXED BEFORE THE RUN: the df change CANNOT move the primary
interval — the wild bootstrap-t reads its critical values off the t*
quantiles, not a t table. G* is a diagnostic with no interval. THE ONLY
CHANNEL THAT CAN MOVE THE BINDING LITERAL IS THE WEBB WEIGHT CHANGE.

PARITY GATES (BLOCKING; on any failure the JSON is written with status
GATE_FAILURE and the run stops. Nothing lands in the manuscript.):
  P1 R1-R4 point reads reproduce 5.334239649398553 / 4.990624060575566 /
     4.695495330057254 / 3.9719264231555695 %, n = 155/137/125/2838,
     G = 31/31/25/226, to 1e-9 (v1's P1 unchanged).
  P2 percentile bootstrap bit-exact at R2 via fu.cluster_bootstrap_cpr
     (rng 42): se_pp 0.3933971547430653, ci95_pct [4.368576777908708,
     6.003552252675821], mapped [2.974329560125351, 8.01850965353176].
  P3 FloorMapping fidelity asserted from floor_uncertainty_results.json
     .mapping_fidelity: grid exact and max|mapped-engine| <= $0.69B
     (committed 0.6867374936622994).
  P4 RADEMACHER REPLAY, load-bearing: with weights="rademacher" every field
     of v1's per-read block reproduces to 1e-12 on all four reads
     (n_clusters, t_crit_G_minus_1, max_leverage, point_cpr_pct,
     cr1/cr2/cr3_t_interval.*, crk_se_pp_approx, wild_t.* incl. t_star_q and
     floor_ci95_pct). This is what licenses reading any Webb-vs-Rademacher
     difference as the WEIGHT CHANGE rather than a refactor. FP2-B1: mapped
     leaves (MAPPED_LEAF_KEYS) are excluded — they are a deterministic
     function of the floor-unit values and the adopted extended mapping,
     and their movement is gated in floor_grid_extension_results.json.
  P5 sum_g h_g = 1 to 1e-12 per read; h_max reproduces the committed
     .reads.*.max_leverage to 1e-12 (0.27808/0.33233/0.38163/0.16608).
  P6 BM/IK equal-cluster self-test returns df = G-1 to 1e-8, at every read's
     G and at all three powers. A failure means STOP, report no df.
  P7 Webb weight moments over the realized draw matrix, every read:
     |mean| < 0.01, |E[s^2]-1| < 0.01, |E[s^4]-7/6| < 0.02.

PRE-COMMITTED EXPECTATIONS (SPEC C1.3, adopted verbatim):
  Webb's E[s^4]=7/6 vs Rademacher's 1 makes t* slightly more dispersed, so a
  small WIDENING. Leading order (E[s^4]-1)/G_eff: 0.167/31 ~ 0.5% (~0.03pp on
  the 5.9268pp width) at nominal G, 0.167/9 ~ 1.9% (~0.11pp) at the effective
  G* <= 9. EXPECTATION: a widening of 0.03-0.15pp, CONCENTRATED AT THE UPPER
  EDGE (the committed correction already "widens it mostly at the top",
  tex 592).
  Printing slack, computed ex ante against committed [+2.796265669289897,
  +8.723086701307457]: the lower literal +2.8 survives while L in [2.75,2.85)
  = 0.0463pp of downward slack; the upper literal +8.7 survives while U in
  [8.65,8.75) = 0.0269pp of upward slack. The expected widening STRADDLES the
  0.027pp upper slack, so the MODAL BRANCH IS (a'), not (a) or (b).
  Secondary: t_{.975,30} = 2.0423; at df_bm near G* ~ 8-9 the critical value
  rises to ~2.26-2.31, inflating CR2/CR3 by ~11-13% (CR2 [+2.974,+8.553] ->
  roughly [+2.7,+8.9]; CR3 [+2.773,+8.774] -> roughly [+2.5,+9.1]).

LANDING RULE (fixed ex ante; pure function of the R2 Webb interval [L*,U*]
against [Lc,Uc] = [2.796265669289897, 8.723086701307457]. ALL tex landings
queue for Eugene. Before ANY tex edit the 12-occurrence / 11-line literal
census of SPEC §0 is re-derived and the gate SOURCE read — the and-form x2 and
bracket-form x3 are gate-invisible.):
  (a) CONFIRM_NO_PRINT — |dL| <= 0.10 and |dU| <= 0.10 and L* in [2.75,2.85)
      and U* in [8.65,8.75). One tablenote clause; ALL 12 INTERVAL LITERALS
      UNTOUCHED; only the tablenote-content gate gains its literal.
  (a') CONFIRM_PRINT_MOVE — both within 0.10pp but at least one crosses a
      rounding boundary. The new pair replaces the old at all 12 occurrences
      on 11 lines in ONE commit, with gate #98's posture_binding_layer span,
      gate #99's ABSTRACT_POSTURE["interval"] AND its ordering assert, the
      count gate, the letter literal list, test_headline_posture_gate.py:79
      and :151, and the letter recount. Prose says MATERIALLY UNCHANGED AND
      RE-PRINTED, never "widened" — a 0.03pp move is a printing artifact and
      calling it a widening would misstate the result.        [posture]
  (b) WIDENS — either endpoint moves OUTWARD by >0.10pp. Same one-commit
      list, PLUS the characterizing prose re-derived (not re-numbered) at
      tex 592, tex 312 and tex 30, and the midpoint-dependent clauses at
      tex 312/316 re-derived.                                  [posture]
  (c) NARROWS — inward by >0.10pp; not expected. DO NOT ADOPT the narrower
      interval. Keep the committed pair as the quoted binding layer and
      report the Webb interval as narrower. Narrowing a disclosed uncertainty
      on a rerun of one's own machinery is adjudication in one's own favor.
                                                               [posture]
  UNCONDITIONAL in every branch: G* and sum(h^2) land in the tablenote in the
  loan/stratum scheme's convention; the CR2/CR3 numbers are stated at df_bm;
  and the bootstrap DGP (unrestricted, point-imposed), B=9999 and the
  SMM-scale studentization are stated — R1 asked for exactly those three and
  they are currently nowhere in the tex. NOTE for the coordinator: the
  tablenote sentence "No single cluster dominates the primary read..." that
  SPEC C1.4 assigns to this run appears to have ALREADY been removed under
  PLAN item A7 — VERIFY, do not re-edit (C1 and A7 must not both touch it).

MUST NOT CHANGE: hazard/floor_inference_correction.py and its artifact
(frozen); hazard/floor_uncertainty.py and its artifact; hazard/config.py; the
percentile layer [+3.0,+8.0] and its 4 tex sites; the PCHIP grid and the
$0.69B fidelity tolerance; tab:oosfloor's floor->marginal grid; the point
+5.5716pp / +$42.6B; any .tex file.

Run:  cd hazard && python3 floor_inference_correction_v2.py
      -> data/floor_inference_correction_v2_results.json      (frozen)
      -> data/floor_inference_v2_tstar_R2_webb.csv            (REQUIRED by C2)
      -> data/floor_inference_v2_tstar_R2_rademacher.csv      (REQUIRED by C2)
No engine runs; one FRED fetch. v1's runtime was 9.1s; the 401-point WCR
inversion on four reads dominates here (~1 minute total).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import floor_uncertainty as fu
import matched_depth_reconciliation as mdr
from stratum import build_stratum_id

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "floor_inference_correction_v2_results.json"
V1_ARTIFACT = DATA_DIR / "floor_inference_correction_results.json"   # FROZEN
FU_ARTIFACT = DATA_DIR / "floor_uncertainty_results.json"            # FROZEN
TSTAR_WEBB_CSV = DATA_DIR / "floor_inference_v2_tstar_R2_webb.csv"
TSTAR_RADE_CSV = DATA_DIR / "floor_inference_v2_tstar_R2_rademacher.csv"

B_WILD = 9999
SEED = 42
CENTRAL_PQ = "6.5"
GRID_LO, GRID_HI = 2.0, 7.0   # FP2-B1: grid extended past 6.0 (2026-08-29)

# Webb (2014) six-point weights, each w.p. 1/6: E[s]=0, E[s^2]=1, E[s^4]=7/6.
WEBB_POINTS = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5),
                        np.sqrt(0.5), 1.0, np.sqrt(1.5)], dtype=np.float64)
WEBB_E_S4 = 7.0 / 6.0

WCR_N_GRID = 401
WCR_SE_SPAN = 5.0

PARITY_TOL = 1e-12          # P4/P5
DF_SELFTEST_TOL = 1e-8      # P6
P7_TOL_MEAN, P7_TOL_S2, P7_TOL_S4 = 0.01, 0.01, 0.02

# ---- the ex-ante landing rule's constants (SPEC C1.4) -----------------------
ENDPOINT_TOL_PP = 0.10
COMMITTED_WILD_T_PP = (2.796265669289897, 8.723086701307457)
PRINT_LOWER_BAND = (2.75, 2.85)      # the printed +2.8 survives inside this
PRINT_UPPER_BAND = (8.65, 8.75)      # the printed +8.7 survives inside this
WIDTH_EQUIV_BAND = (5.727, 6.127)    # C1.4's equivalent width threshold
EXPECT_WIDENING_PP = (0.03, 0.15)
EXPECT_MODAL_BRANCH = "CONFIRM_PRINT_MOVE"

# ---- committed values quoted ex ante (asserted vs frozen artifacts) ---------
COMMITTED_POINTS = {  # read -> (point_cpr_pct, n_cohort_months, n_clusters)
    "R1_2018_gap<=+0.0000_age>=12": (5.334239649398553, 155, 31),
    "R2_2018_gap<=-0.0025_age>=12": (4.990624060575566, 137, 31),
    "R3_2018_gap<=-0.0050_age>=12": (4.695495330057254, 125, 25),
    "R4_inwindow_calib_202206_202312_gap<=-0.02_age>=12":
        (3.9719264231555695, 2838, 226),
}
R2 = "R2_2018_gap<=-0.0025_age>=12"
COMMITTED_R2_SE_PP = 0.3933971547430653
COMMITTED_R2_CI95_PCT = (4.368576777908708, 6.003552252675821)
COMMITTED_PERCENTILE_PP = (2.974329560125351, 8.01850965353176)
COMMITTED_MAX_LEVERAGE = {  # P5 (v1 .reads.*.max_leverage)
    "R1_2018_gap<=+0.0000_age>=12": 0.27808349473916866,
    "R2_2018_gap<=-0.0025_age>=12": 0.3323311750696546,
    "R3_2018_gap<=-0.0050_age>=12": 0.3816308768794999,
    "R4_inwindow_calib_202206_202312_gap<=-0.02_age>=12": 0.16607689897035868,
}
# the loan/stratum scheme's committed effective-count convention (must match)
LOAN_STRATUM_EFFECTIVE_N = 25.77710660741266

READ_SELECTIONS = {  # read -> (rp_lo, rp_hi, gap_thr, age_min)   [v1 VERBATIM]
    "R1_2018_gap<=+0.0000_age>=12": (*fu.LEG_2018, 0.0, 12),
    "R2_2018_gap<=-0.0025_age>=12": (*fu.LEG_2018, -0.0025, 12),
    "R3_2018_gap<=-0.0050_age>=12": (*fu.LEG_2018, -0.005, 12),
    "R4_inwindow_calib_202206_202312_gap<=-0.02_age>=12":
        (*fu.CALIB_WINDOW, -0.02, 12),
}

# the per-read v1 fields P4 replays bit-exactly (wild_t handled separately)
P4_READ_FIELDS = ("n_clusters", "t_crit_G_minus_1", "max_leverage",
                  "point_cpr_pct",
                  "cr1_t_interval", "cr1_se_pp_approx",
                  "cr2_t_interval", "cr2_se_pp_approx",
                  "cr3_t_interval", "cr3_se_pp_approx")


# =========================================================================
# VERBATIM COPIES FROM v1 (floor_inference_correction.py) — do not edit
# =========================================================================
def cpr_pct_of_smm(smm: float) -> float:
    return 100.0 * (1.0 - (1.0 - smm) ** 12)


def cluster_sums(sel: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    g = sel.groupby("stratum", sort=True)[["prepaid_upb", "exposure_upb"]].sum()
    return (g["prepaid_upb"].to_numpy(np.float64),
            g["exposure_upb"].to_numpy(np.float64))


def cr_ses(A: np.ndarray, W: np.ndarray) -> dict:
    Wtot = W.sum()
    R = A.sum() / Wtot
    u = (A - R * W) / Wtot
    h = W / Wtot
    G = len(A)
    fac = G / (G - 1)
    return {
        "R_smm": R, "G": G, "max_leverage": float(h.max()),
        "se_cr1": float(np.sqrt(fac * np.sum(u ** 2))),
        "se_cr2": float(np.sqrt(fac * np.sum((u / np.sqrt(1.0 - h)) ** 2))),
        "se_cr3": float(np.sqrt(fac * np.sum((u / (1.0 - h)) ** 2))),
        "_u": u, "_h": h,
    }


def map_endpoint(mapping: mdr.FloorMapping, floor_pct: float) -> dict:
    trunc = not mapping.in_grid(floor_pct)
    x = min(max(floor_pct, GRID_LO), GRID_HI)
    b, pp = mapping(x)
    return {"floor_pct": float(floor_pct), "mapped_at_pct": float(x),
            "truncated_at_grid_edge": bool(trunc),
            "marginal_b": float(b), "marginal_pp": float(pp)}


def map_floor_ci(mapping: mdr.FloorMapping, lo_pct: float, hi_pct: float) -> dict:
    # marginal decreases in the floor: floor lo -> pp hi, floor hi -> pp lo
    hi_end = map_endpoint(mapping, lo_pct)
    lo_end = map_endpoint(mapping, hi_pct)
    return {
        "floor_ci95_pct": [float(lo_pct), float(hi_pct)],
        "marginal_ci95_pp": [lo_end["marginal_pp"], hi_end["marginal_pp"]],
        "marginal_ci95_b": [lo_end["marginal_b"], hi_end["marginal_b"]],
        "lower_pp_edge": lo_end, "upper_pp_edge": hi_end,
    }


# =========================================================================
# NEW MACHINERY (SPEC C1.2)
# =========================================================================
def draw_weights(rng: np.random.Generator, scheme: str, G: int) -> np.ndarray:
    """(B_WILD, G) weight matrix. The rademacher branch is v1's line 181
    VERBATIM — bit-exact replay under a fresh default_rng(42) is gate P4."""
    if scheme == "rademacher":
        return rng.choice([-1.0, 1.0], size=(B_WILD, G))
    if scheme == "webb":
        return rng.choice(WEBB_POINTS, size=(B_WILD, G))
    raise ValueError(f"unknown weight scheme {scheme!r}")


def wild_t_ci(A: np.ndarray, W: np.ndarray, se_cr1_smm: float,
              rng: np.random.Generator, scheme: str
              ) -> tuple[tuple[float, float], np.ndarray, np.ndarray, float]:
    """v1's wild_t_ci with the weight scheme switchable and NOTHING else
    changed. Unrestricted (WCU-t) DGP: the point estimate is imposed as the
    DGP truth and the UNRESTRICTED residuals are perturbed —
        A*_g = W_g*R + s_g*(A_g - R*W_g)
    — studentized on the FLOOR (SMM) scale by CR1 on both sides, then the
    equal-tailed percentile-t endpoints [R - q975*SE_CR1, R - q025*SE_CR1]
    are mapped SMM->CPR% and through the PCHIP. Not post-PCHIP."""
    Wtot = W.sum()
    R = A.sum() / Wtot
    G = len(A)
    fac = G / (G - 1)
    resid = A - R * W                                    # (G,)
    s = draw_weights(rng, scheme, G)                     # (B, G)
    Astar = W[None, :] * R + s * resid[None, :]          # (B, G)
    Rstar = Astar.sum(axis=1) / Wtot                     # (B,)
    ustar = (Astar - Rstar[:, None] * W[None, :]) / Wtot
    sestar = np.sqrt(fac * np.sum(ustar ** 2, axis=1))
    tstar = (Rstar - R) / sestar
    q_lo, q_hi = np.percentile(tstar, [2.5, 97.5])
    return (R - q_hi * se_cr1_smm, R - q_lo * se_cr1_smm), tstar, s, R


def bm_ik_df(h: np.ndarray, power: float) -> float:
    """Bell-McCaffrey / Imbens-Kolesar data-driven df, DERIVED FROM THIS
    ESTIMATOR'S CONSTRUCTION (SPEC C1.2(2)); no closed form is recalled.

    R = sum(A)/sum(W) is the WLS estimator of A_g = R*W_g + eps_g under the
    working Var(eps_g) prop-to W_g, whose leverage is h_g = W_g/sum(W) — the
    h cr_ses already computes. The CRk variance is the quadratic form
    V = sum_g (g_g'A)^2 with g_g[j] = (delta_gj - h_g)/(sumW*(1-h_g)^power).
    Under the working Omega = diag(W)/sum(W) = diag(h), and using sum_j h_j=1
    to collapse the cross terms,

        (G Omega G')_{gk} = [delta_gk*h_g - h_g*h_k]
                            / (sumW^2 * (1-h_g)^power * (1-h_k)^power),

    so V/sigma^2 ~ sum_i lambda_i chi^2_1 with lambda the eigenvalues of that
    matrix, and Satterthwaite matching gives
        df = (tr M)^2 / tr(M M') = (sum lambda)^2 / (sum lambda^2).
    The 1/sumW^2 prefactor is a common scale and cancels in the ratio, so it
    is omitted. power = 0 -> CR1, 0.5 -> CR2 (the BM adjustment), 1 -> CR3.

    Equal clusters h == 1/G give M prop-to (I - J/G), eigenvalues {1 x (G-1),
    0}, hence df = G-1 exactly. That identity is blocking gate P6."""
    h = np.asarray(h, dtype=np.float64)
    d = (1.0 - h) ** power
    M = (np.diag(h) - np.outer(h, h)) / np.outer(d, d)
    lam = np.linalg.eigvalsh(0.5 * (M + M.T))            # M is symmetric
    s1 = float(lam.sum())
    s2 = float((lam ** 2).sum())
    return float(s1 * s1 / s2)


def css_effective_clusters(h: np.ndarray) -> tuple[float, float]:
    """Carter-Schnepel-Steigerwald G* = G/(1+Gamma) with
    Gamma = (1/G) sum_g ((gamma_g - gbar)/gbar)^2 and gamma_g the cluster's
    variance share. For this intercept-only estimator gamma_g prop-to h_g and
    sum h = 1, so gbar = 1/G and Gamma = G*sum(h^2) - 1, hence
        G* = G / (G*sum(h^2)) = 1 / sum(h^2)
    — the Herfindahl-inverse convention already committed for the loan/stratum
    scheme (effective_n_clusters 25.777...). Same convention in both places is
    a hard requirement (SPEC C1.2(3))."""
    sum_h_sq = float(np.sum(np.asarray(h, dtype=np.float64) ** 2))
    return 1.0 / sum_h_sq, sum_h_sq


def wcr_invert(A: np.ndarray, W: np.ndarray, se_cr1_smm: float,
               rng: np.random.Generator) -> dict:
    """Restricted (WCR) CI by test inversion (SPEC C1.2(4)); reported, no rule
    attached. 401 candidate R0 over R_hat +/- 5*SE_CR1 on the SMM scale. For
    each R0 the null is IMPOSED in the DGP:
        A*_g = R0*W_g + s_g*(A_g - R0*W_g),  s Webb,
        t*_b = (R*_b - R0)/SE*_b  with SE*_b the CR1 SE of the resample,
    and R0 is retained iff t(R0) = (R_hat - R0)/SE_CR1 lies inside
    [q2.5, q97.5](t*). LABELED: the numerator's studentizer is the
    UNRESTRICTED SE_CR1, per the spec's literal statement — not the
    restricted SE the symmetric textbook variant would use. ONE Webb weight
    matrix is drawn and reused across the whole grid (MacKinnon-Webb
    practice; redrawing would put simulation noise into the retained set)."""
    G = len(A)
    Wtot = W.sum()
    fac = G / (G - 1)
    R_hat = A.sum() / Wtot
    s = draw_weights(rng, "webb", G)                     # reused across grid
    grid = np.linspace(R_hat - WCR_SE_SPAN * se_cr1_smm,
                       R_hat + WCR_SE_SPAN * se_cr1_smm, WCR_N_GRID)
    retained = np.zeros(WCR_N_GRID, dtype=bool)
    for i, R0 in enumerate(grid):
        e = A - R0 * W                                   # restricted residuals
        Astar = R0 * W[None, :] + s * e[None, :]
        Rstar = Astar.sum(axis=1) / Wtot
        ustar = (Astar - Rstar[:, None] * W[None, :]) / Wtot
        sestar = np.sqrt(fac * np.sum(ustar ** 2, axis=1))
        tstar = (Rstar - R0) / sestar
        q_lo, q_hi = np.percentile(tstar, [2.5, 97.5])
        t_obs = (R_hat - R0) / se_cr1_smm
        retained[i] = bool(q_lo <= t_obs <= q_hi)
    idx = np.flatnonzero(retained)
    out = {
        "grid_lo_smm": float(grid[0]), "grid_hi_smm": float(grid[-1]),
        "grid_lo_pct": cpr_pct_of_smm(float(grid[0])),
        "grid_hi_pct": cpr_pct_of_smm(float(grid[-1])),
        "n_grid": int(WCR_N_GRID), "se_span": WCR_SE_SPAN,
        "weights": "webb", "B": B_WILD, "seed": SEED,
        "weights_reused_across_grid": True,
        "studentizer": ("unrestricted SE_CR1 in the numerator (SPEC C1.2(4) "
                        "literal); SE* recomputed on each restricted resample"),
        "n_retained": int(idx.size),
    }
    if idx.size == 0:
        out.update({"computable": False,
                    "reason": "empty retained set over the +/-5 SE_CR1 grid"})
        return out
    contiguous = bool(int(idx[-1] - idx[0] + 1) == int(idx.size))
    lo_smm, hi_smm = float(grid[idx[0]]), float(grid[idx[-1]])
    out.update({
        "computable": True,
        "retained_contiguous": contiguous,
        "open_at_grid_lo": bool(retained[0]),
        "open_at_grid_hi": bool(retained[-1]),
        "smm_ci95": [lo_smm, hi_smm],
        **map_floor_ci(mapping_global, cpr_pct_of_smm(lo_smm),
                       cpr_pct_of_smm(hi_smm)),
    })
    return out


def weight_moments(s: np.ndarray) -> dict:
    return {"n": int(s.size), "mean": float(s.mean()),
            "e_s2": float((s ** 2).mean()), "e_s4": float((s ** 4).mean())}


# =========================================================================
# PARITY PLUMBING
# =========================================================================
MAPPED_LEAF_KEYS = frozenset({
    "marginal_ci95_pp", "marginal_ci95_b", "marginal_pp", "marginal_b",
    "mapped_at_pct", "truncated_at_grid_edge",
})  # FP2-B1: mapped leaves are a deterministic function of the floor-unit
    # values and the ADOPTED extended mapping; the replay's license (reading
    # Webb-vs-Rademacher as the weight change) rests on floor-unit equality,
    # which stays bit-exact. Mapped-value movement is priced and gated in
    # floor_grid_extension_results.json (P4 blast radius).


def _parity_walk(want, got, path: str, diffs: list) -> None:
    """Recursive bit-exact comparison of a committed v1 sub-tree against the
    v2 counterpart. Every numeric leaf must agree to PARITY_TOL; bools,
    strings and None must be equal. Every mismatch is named by its full path
    so a P4 failure is diagnosable without a rerun. Mapped leaves
    (MAPPED_LEAF_KEYS) are skipped under the FP2-B1 extended mapping; the
    floor-unit leaves (floor_ci95_pct, *_pp_edge.floor_pct) remain compared
    and are the load-bearing content."""
    if isinstance(want, dict):
        if not isinstance(got, dict):
            diffs.append({"path": path, "want": "dict", "got": type(got).__name__})
            return
        for k, v in want.items():
            if k in MAPPED_LEAF_KEYS:
                continue
            if k not in got:
                diffs.append({"path": f"{path}.{k}", "want": v, "got": "<MISSING>"})
                continue
            _parity_walk(v, got[k], f"{path}.{k}", diffs)
    elif isinstance(want, list):
        if not isinstance(got, list) or len(got) != len(want):
            diffs.append({"path": path, "want": f"list[{len(want)}]",
                          "got": f"{type(got).__name__}"})
            return
        for i, v in enumerate(want):
            _parity_walk(v, got[i], f"{path}[{i}]", diffs)
    elif isinstance(want, bool) or want is None:
        if got != want:
            diffs.append({"path": path, "want": want, "got": got})
    elif isinstance(want, (int, float)):
        try:
            d = abs(float(got) - float(want))
        except (TypeError, ValueError):
            diffs.append({"path": path, "want": want, "got": got})
            return
        if not (d <= PARITY_TOL):
            diffs.append({"path": path, "want": want, "got": got, "abs_diff": d})
    else:
        if got != want:
            diffs.append({"path": path, "want": want, "got": got})


def _fail_out(gate_report: dict, reads_unverified: dict | None,
              t0: float) -> None:
    payload = {
        "mode": "floor_inference_correction_v2",
        "status": "GATE_FAILURE",
        "spec": "SPEC_round28_C1_C2_C3_C6.md SPEC C1",
        "parity_gates": gate_report,
        "parity_gates_all_pass": False,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    if reads_unverified is not None:
        # deliberately NOT named `reads`: these are diagnostics, not results
        payload["reads_unverified"] = reads_unverified
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=lambda o: o.item())
        f.write("\n")
    failed = [k for k, v in gate_report.items()
              if isinstance(v, dict) and not v.get("pass", True)]
    raise SystemExit(
        f"PARITY GATE FAILURE {failed} — STOP. Nothing lands in the "
        f"manuscript. Diagnostics in {RESULTS_JSON}."
    )


mapping_global: mdr.FloorMapping | None = None   # bound in main(); used by wcr


# =========================================================================
def main() -> None:
    global mapping_global
    t0 = time.perf_counter()

    with open(FU_ARTIFACT) as f:
        fua = json.load(f)
    assert fua.get("status") == "OK" and fua.get("parity_gates_all_pass")
    fu_reads = fua["part_a_sampling_uncertainty"]["reads"]
    mf4 = fua["part_a_sampling_uncertainty"]["mf4_binding_uncertainty"]
    assert abs(mf4["sampling_ci95_pp"][0] - COMMITTED_PERCENTILE_PP[0]) < 1e-9
    assert abs(mf4["sampling_ci95_pp"][1] - COMMITTED_PERCENTILE_PP[1]) < 1e-9

    with open(V1_ARTIFACT) as f:                 # FROZEN — read only, never written
        v1 = json.load(f)
    assert v1.get("status") == "OK" and v1.get("parity_gates_all_pass")
    assert v1["mode"] == "floor_inference_correction"
    v1_reads = v1["reads"]
    for name, want_hmax in COMMITTED_MAX_LEVERAGE.items():
        assert abs(v1_reads[name]["max_leverage"] - want_hmax) < 1e-15, name
    assert abs(v1_reads[R2]["wild_t"]["marginal_ci95_pp"][0]
               - COMMITTED_WILD_T_PP[0]) < 1e-15
    assert abs(v1_reads[R2]["wild_t"]["marginal_ci95_pp"][1]
               - COMMITTED_WILD_T_PP[1]) < 1e-15

    gate_report: dict = {}

    # ---- P6 FIRST: data-free, and it licenses reporting any df at all ------
    print("=" * 72)
    print("P6 — BM/IK equal-cluster self-test (BLOCKING; no df is reported "
          "unless this passes)")
    print("=" * 72)
    p6_cells, p6_max_err = {}, 0.0
    for G in (2, 3, 5, 25, 31, 226):
        for power, tag in ((0.0, "cr1"), (0.5, "cr2"), (1.0, "cr3")):
            got = bm_ik_df(np.full(G, 1.0 / G), power)
            err = abs(got - (G - 1))
            p6_max_err = max(p6_max_err, err)
            p6_cells[f"G{G}_{tag}"] = {"df": got, "want": G - 1, "abs_err": err}
    p6_ok = bool(p6_max_err <= DF_SELFTEST_TOL)
    gate_report["P6_bm_df_equal_cluster_selftest"] = {
        "cells": p6_cells, "max_abs_err": p6_max_err,
        "tol": DF_SELFTEST_TOL, "pass": p6_ok}
    print(f"  P6 max |df - (G-1)| = {p6_max_err:.3e} (tol {DF_SELFTEST_TOL}) "
          f"[{'PASS' if p6_ok else 'FAIL'}]")
    if not p6_ok:
        _fail_out(gate_report, None, t0)

    # ---- panel --------------------------------------------------------------
    print("\nPANEL — matched_depth_reconciliation.build_panel")
    df = mdr.build_panel()
    df["stratum"] = [
        build_stratum_id(v, c, fb, lb)
        for v, c, fb, lb in zip(df["vintage"], df["coupon"],
                                df["fico_bucket"], df["ltv_bucket"])
    ]

    selections: dict[str, pd.DataFrame] = {}
    # ---- P1 ----------------------------------------------------------------
    print("\nP1 — point reads")
    for name, (lo, hi, gthr, amin) in READ_SELECTIONS.items():
        sel = fu._select(df, lo, hi, gthr, amin)
        selections[name] = sel
        cpr, _exp, n = mdr.cpr_of(sel)
        n_cl = sel["stratum"].nunique()
        want_cpr, want_n, want_cl = COMMITTED_POINTS[name]
        art = fu_reads[name]
        ok = (abs(cpr - want_cpr) < 1e-9 and n == want_n and n_cl == want_cl
              and abs(art["point_cpr_pct"] - want_cpr) < 1e-9)
        gate_report[f"P1_{name}"] = {
            "got_cpr_pct": float(cpr), "want_cpr_pct": want_cpr,
            "got_n": int(n), "want_n": want_n,
            "got_clusters": int(n_cl), "want_clusters": want_cl, "pass": ok}
        print(f"  P1 {name}: {cpr:.9f}% n={n} G={n_cl} "
              f"[{'PASS' if ok else 'FAIL'}]")

    # ---- P2 (bit-exact percentile reproduction, R2) -------------------------
    draws, _n_cl = fu.cluster_bootstrap_cpr(selections[R2])
    se_pp = float(np.std(draws, ddof=1))
    ci = np.percentile(draws, [2.5, 97.5])
    # FP2-B1: the parity reproduction of the COMMITTED percentile pair must
    # run under the COMMITTED mapping (a parity gate reproduces committed
    # values); the corrections below use the extended map.
    mapping_committed = mdr.FloorMapping()
    mapping = mdr.FloorMapping(extended=True)
    mapping_global = mapping
    mapped = fu._map_draws(mapping_committed, draws)
    p2_ok = (abs(se_pp - COMMITTED_R2_SE_PP) < 1e-9
             and abs(ci[0] - COMMITTED_R2_CI95_PCT[0]) < 1e-9
             and abs(ci[1] - COMMITTED_R2_CI95_PCT[1]) < 1e-9
             and abs(mapped["ci95_pp"][0] - COMMITTED_PERCENTILE_PP[0]) < 1e-9
             and abs(mapped["ci95_pp"][1] - COMMITTED_PERCENTILE_PP[1]) < 1e-9)
    gate_report["P2_percentile_bitexact_R2"] = {
        "got_se_pp": se_pp, "want_se_pp": COMMITTED_R2_SE_PP,
        "got_ci95_pct": [float(ci[0]), float(ci[1])],
        "want_ci95_pct": list(COMMITTED_R2_CI95_PCT),
        "got_mapped_pp": mapped["ci95_pp"],
        "want_mapped_pp": list(COMMITTED_PERCENTILE_PP),
        "n_draws_outside_grid": mapped.get("n_draws_outside_grid"),
        "pass": p2_ok}
    print(f"  P2 R2 percentile bit-exact: [{'PASS' if p2_ok else 'FAIL'}]")

    # ---- P3 -----------------------------------------------------------------
    mfid = fua["mapping_fidelity"]
    p3_ok = bool(mfid["reproduces_committed_grid_exactly"]
                 and mfid["max_abs_err_b_inside_grid"] <= 0.69)
    gate_report["P3_mapping_fidelity"] = {
        "reproduces_committed_grid_exactly":
            mfid["reproduces_committed_grid_exactly"],
        "max_abs_err_b_inside_grid": mfid["max_abs_err_b_inside_grid"],
        "tol_b": 0.69, "pass": p3_ok}
    print(f"  P3 mapping fidelity: [{'PASS' if p3_ok else 'FAIL'}]")

    if not all(v["pass"] for v in gate_report.values()):
        _fail_out(gate_report, None, t0)
    print("  P1/P2/P3/P6 PASS — safe to compute the corrections.")

    # =====================================================================
    # CORRECTIONS
    # =====================================================================
    print("\n" + "=" * 72)
    print("CORRECTIONS — Webb primary, Rademacher replay, BM/IK df, CSS G*, WCR")
    print("=" * 72)
    out_reads: dict = {}
    webb_moment_cells: dict = {}
    rade_moment_cells: dict = {}
    leverage_cells: dict = {}
    for name, sel in selections.items():
        A, W = cluster_sums(sel)
        c = cr_ses(A, W)
        G = c["G"]
        h = c["_h"]
        strata = sorted(sel["stratum"].unique().tolist())
        tcrit = float(stats.t.ppf(0.975, G - 1))
        g_star, sum_h_sq = css_effective_clusters(h)
        df_bm = {k: bm_ik_df(h, p)
                 for k, p in (("cr1", 0.0), ("cr2", 0.5), ("cr3", 1.0))}
        tcrit_bm = {k: float(stats.t.ppf(0.975, v)) for k, v in df_bm.items()}

        read: dict = {
            "n_clusters": G,
            "n_cohort_months": int(len(sel)),
            "point_cpr_pct": cpr_pct_of_smm(c["R_smm"]),
            "R_smm": float(c["R_smm"]),
            "se_cr1_smm": c["se_cr1"], "se_cr2_smm": c["se_cr2"],
            "se_cr3_smm": c["se_cr3"],
            "t_crit_G_minus_1": tcrit,
            "max_leverage": c["max_leverage"],
            "leverages_h": [float(x) for x in h],
            "cluster_strata": strata,
            "sum_h": float(h.sum()),
            "sum_h_sq": sum_h_sq,
            "h_max": float(h.max()),
            "G_star_css": g_star,
            "G_star_css_upper_bound_from_hmax": float(1.0 / c["max_leverage"] ** 2),
            "df_bm": df_bm["cr2"],
            "t_crit_df_bm": tcrit_bm["cr2"],
            "df_bm_by_estimator": df_bm,
            "t_crit_df_bm_by_estimator": tcrit_bm,
        }
        leverage_cells[name] = {
            "sum_h": read["sum_h"], "h_max": read["h_max"],
            "want_h_max": COMMITTED_MAX_LEVERAGE[name],
            "sum_h_sq": sum_h_sq, "G_star_css": g_star}

        # --- CR t-intervals at BOTH df variants (v1's is the parity-bearing one)
        for k in ("cr1", "cr2", "cr3"):
            se = c[f"se_{k}"]
            lo, hi = c["R_smm"] - tcrit * se, c["R_smm"] + tcrit * se
            read[f"{k}_t_interval"] = {
                **map_floor_ci(mapping, cpr_pct_of_smm(lo), cpr_pct_of_smm(hi)),
                "df_used": float(G - 1), "df_kind": "G_minus_1",
                "t_crit": tcrit}
            lo_b = c["R_smm"] - tcrit_bm[k] * se
            hi_b = c["R_smm"] + tcrit_bm[k] * se
            read[f"{k}_t_interval_df_bm"] = {
                **map_floor_ci(mapping, cpr_pct_of_smm(lo_b),
                               cpr_pct_of_smm(hi_b)),
                "df_used": df_bm[k], "df_kind": "bell_mccaffrey_imbens_kolesar",
                "t_crit": tcrit_bm[k]}
            read[f"{k}_se_pp_approx"] = (cpr_pct_of_smm(c["R_smm"] + se)
                                         - cpr_pct_of_smm(c["R_smm"]))

        # --- wild-t, both weight schemes, fresh default_rng(42) each --------
        for scheme, tag in (("rademacher", "wild_t_rademacher"),
                            ("webb", "wild_t_webb")):
            rng = np.random.default_rng(SEED)
            (lo_smm, hi_smm), tstar, s_mat, _R = wild_t_ci(
                A, W, c["se_cr1"], rng, scheme)
            csv_path = None
            if name == R2:
                csv_path = (TSTAR_WEBB_CSV if scheme == "webb"
                            else TSTAR_RADE_CSV)
                np.savetxt(csv_path, tstar, fmt="%.17g",
                           header="t_star", comments="")
            block = {
                "B": B_WILD, "seed": SEED, "weights": scheme,
                "dgp": ("unrestricted (WCU-t): A*_g = W_g*R_hat + s_g*"
                        "(A_g - R_hat*W_g); the point estimate is imposed as "
                        "the DGP truth and the unrestricted residuals are "
                        "perturbed"),
                "studentization_scale": ("floor (SMM) scale; CR1 in both the "
                                         "numerator and the bootstrap "
                                         "denominator; endpoints mapped "
                                         "SMM->CPR%->PCHIP, not post-PCHIP"),
                "t_star_q": [float(np.percentile(tstar, 2.5)),
                             float(np.percentile(tstar, 97.5))],
                "t_star_draws_path": (str(csv_path) if csv_path else None),
                **map_floor_ci(mapping, cpr_pct_of_smm(lo_smm),
                               cpr_pct_of_smm(hi_smm)),
            }
            read[tag] = block
            mom = weight_moments(s_mat)
            (webb_moment_cells if scheme == "webb"
             else rade_moment_cells)[name] = mom

        # --- WCR restricted inversion --------------------------------------
        rng_wcr = np.random.default_rng(SEED)
        read["wcr_inverted"] = wcr_invert(A, W, c["se_cr1"], rng_wcr)

        out_reads[name] = read
        w = read["wild_t_webb"]["marginal_ci95_pp"]
        r = read["wild_t_rademacher"]["marginal_ci95_pp"]
        print(f"  {name}: G={G} h_max={read['h_max']:.5f} "
              f"sum_h2={sum_h_sq:.5f} G*={g_star:.2f} df_bm={df_bm['cr2']:.2f}")
        print(f"    webb  [{w[0]:+.4f}, {w[1]:+.4f}]pp   "
              f"rade  [{r[0]:+.4f}, {r[1]:+.4f}]pp")

    # =====================================================================
    # P4 / P5 / P7
    # =====================================================================
    print("\n" + "=" * 72)
    print("P4 / P5 / P7")
    print("=" * 72)
    # ---- P4 Rademacher replay, bit-exact vs the frozen v1 artifact --------
    p4_diffs: list = []
    for name in READ_SELECTIONS:
        want = v1_reads[name]
        got = out_reads[name]
        for fld in P4_READ_FIELDS:
            _parity_walk(want[fld], got.get(fld), f"{name}.{fld}", p4_diffs)
        _parity_walk(want["wild_t"], got["wild_t_rademacher"],
                     f"{name}.wild_t->wild_t_rademacher", p4_diffs)
    p4_ok = bool(not p4_diffs)
    gate_report["P4_rademacher_replay_bitexact"] = {
        "tol": PARITY_TOL, "n_fields_compared": len(READ_SELECTIONS)
        * (len(P4_READ_FIELDS) + 1),
        "compared": list(P4_READ_FIELDS) + ["wild_t->wild_t_rademacher"],
        "n_diffs": len(p4_diffs), "diffs": p4_diffs[:40], "pass": p4_ok}
    print(f"  P4 rademacher replay vs frozen v1: {len(p4_diffs)} diffs "
          f"[{'PASS' if p4_ok else 'FAIL'}]")

    # ---- P5 leverages -----------------------------------------------------
    p5_ok = True
    for name, cell in leverage_cells.items():
        ok = (abs(cell["sum_h"] - 1.0) <= PARITY_TOL
              and abs(cell["h_max"] - cell["want_h_max"]) <= PARITY_TOL)
        cell["pass"] = bool(ok)
        p5_ok = p5_ok and ok
    gate_report["P5_leverages"] = {
        "tol": PARITY_TOL, "cells": leverage_cells,
        "loan_stratum_effective_n_convention_reference": LOAN_STRATUM_EFFECTIVE_N,
        "pass": bool(p5_ok)}
    print(f"  P5 sum_h == 1 and h_max vs committed max_leverage: "
          f"[{'PASS' if p5_ok else 'FAIL'}]")

    # ---- P7 Webb weight moments ------------------------------------------
    p7_ok = True
    for name, m in webb_moment_cells.items():
        ok = (abs(m["mean"]) < P7_TOL_MEAN
              and abs(m["e_s2"] - 1.0) < P7_TOL_S2
              and abs(m["e_s4"] - WEBB_E_S4) < P7_TOL_S4)
        m["pass"] = bool(ok)
        p7_ok = p7_ok and ok
    gate_report["P7_webb_weight_moments"] = {
        "target": {"mean": 0.0, "e_s2": 1.0, "e_s4": WEBB_E_S4},
        "tol": {"mean": P7_TOL_MEAN, "e_s2": P7_TOL_S2, "e_s4": P7_TOL_S4},
        "webb": webb_moment_cells,
        "rademacher_for_contrast": rade_moment_cells,
        "pass": bool(p7_ok)}
    print(f"  P7 webb moments (E[s^4] target {WEBB_E_S4:.6f}): "
          f"[{'PASS' if p7_ok else 'FAIL'}]")

    if not all(v["pass"] for v in gate_report.values()):
        _fail_out(gate_report, out_reads, t0)
    print("  ALL PARITY GATES PASS.")

    # =====================================================================
    # THE EX-ANTE LANDING RULE (SPEC C1.4) — no discretion after the run
    # =====================================================================
    webb_pp = out_reads[R2]["wild_t_webb"]["marginal_ci95_pp"]
    L, U = float(webb_pp[0]), float(webb_pp[1])
    Lc, Uc = COMMITTED_WILD_T_PP
    dL, dU = L - Lc, U - Uc                      # SIGNED
    width, width_c = U - L, Uc - Lc
    within = (abs(dL) <= ENDPOINT_TOL_PP) and (abs(dU) <= ENDPOINT_TOL_PP)
    printed_lower_unchanged = bool(PRINT_LOWER_BAND[0] <= L < PRINT_LOWER_BAND[1])
    printed_upper_unchanged = bool(PRINT_UPPER_BAND[0] <= U < PRINT_UPPER_BAND[1])
    moves_out = bool(dL < -ENDPOINT_TOL_PP or dU > ENDPOINT_TOL_PP)
    moves_in = bool(dL > ENDPOINT_TOL_PP or dU < -ENDPOINT_TOL_PP)
    if within:
        code = ("CONFIRM_NO_PRINT"
                if (printed_lower_unchanged and printed_upper_unchanged)
                else "CONFIRM_PRINT_MOVE")
    elif moves_out:
        # WIDENS takes precedence over NARROWS when both fire: the paper's own
        # convention forbids adjudicating in its own favour (SPEC C1.4(c)).
        code = "WIDENS"
    else:
        code = "NARROWS"

    ACTION = {
        "CONFIRM_NO_PRINT": (
            "CONFIRM_NO_PRINT: one clause in tab:uncertainty's tablenote "
            "reporting the Webb interval, df_bm and G*; ALL 12 interval "
            "literals on 11 lines UNTOUCHED; only the tablenote-content gate "
            "gains its literal; gates #98/#99/#101 untouched. Unconditional "
            "items still land: G*/sum(h^2) in the loan-stratum convention, "
            "CR2/CR3 restated at df_bm, and the DGP + B=9999 + SMM-scale "
            "studentization stated."),
        "CONFIRM_PRINT_MOVE": (
            "CONFIRM_PRINT_MOVE: substance confirmed, printed literal moves. "
            "The new pair replaces the old at ALL 12 occurrences on 11 lines "
            "(30, 45, 76x2, 106, 301, 312, 357, 592, 605, 611, 677) in ONE "
            "commit, with gate #98's posture_binding_layer span, gate #99's "
            "ABSTRACT_POSTURE['interval'] AND its ordering assert, the count "
            "gate, the letter literal list, tests/test_headline_posture_gate"
            ".py:79 and :151, and the letter recount. Prose says MATERIALLY "
            "UNCHANGED AND RE-PRINTED, never 'widened'. RE-DERIVE the census "
            "first; the and-form x2 and bracket-form x3 are gate-invisible. "
            "[posture]"),
        "WIDENS": (
            "WIDENS: material widening. Same one-commit literal list as "
            "CONFIRM_PRINT_MOVE, PLUS the characterizing prose RE-DERIVED "
            "(not re-numbered) at tex 592 (incl. the 'widens it mostly at the "
            "top' clause re-checked against the new asymmetry), tex 312 (gate "
            "#98's pinned span) and tex 30 (the abstract parenthetical gains "
            "the effective cluster count), and the midpoint-dependent clauses "
            "at tex 312/316 re-derived. [posture]"),
        "NARROWS": (
            "NARROWS: DO NOT ADOPT the narrower interval. Keep the committed "
            "pair as the quoted binding layer, report the Webb interval in "
            "the tablenote as narrower, and state that the wider construction "
            "is retained. Narrowing a disclosed uncertainty on a rerun of "
            "one's own machinery is adjudication in one's own favour, which "
            "this paper's convention forbids. Flag to Eugene either way. "
            "[posture]"),
    }
    verdict = {
        "primary": "R2 Webb wild-t, mapped, pp at 6.5",
        "corrected_pp": [L, U],
        "committed_pp": list(COMMITTED_WILD_T_PP),
        "committed_percentile_pp": list(COMMITTED_PERCENTILE_PP),
        "rademacher_replay_pp": out_reads[R2]["wild_t_rademacher"][
            "marginal_ci95_pp"],
        "delta_lower_pp": float(dL), "delta_upper_pp": float(dU),
        "abs_delta_lower_pp": float(abs(dL)), "abs_delta_upper_pp": float(abs(dU)),
        "endpoint_tol_pp": ENDPOINT_TOL_PP,
        "width_pp": float(width), "committed_width_pp": float(width_c),
        "width_change_pp": float(width - width_c),
        "width_equivalent_band_pp": list(WIDTH_EQUIV_BAND),
        "width_within_equivalent_band": bool(
            WIDTH_EQUIV_BAND[0] <= width <= WIDTH_EQUIV_BAND[1]),
        "printed_lower_unchanged": printed_lower_unchanged,
        "printed_upper_unchanged": printed_upper_unchanged,
        "printed_lower_band": list(PRINT_LOWER_BAND),
        "printed_upper_band": list(PRINT_UPPER_BAND),
        "moves_outward_gt_tol": moves_out,
        "moves_inward_gt_tol": moves_in,
        "mixed_outward_and_inward_move": bool(moves_out and moves_in),
        "lower_edge_above_zero": bool(L > 0.0),
        "truncation_flags": {
            "webb_lower": out_reads[R2]["wild_t_webb"]["lower_pp_edge"][
                "truncated_at_grid_edge"],
            "webb_upper": out_reads[R2]["wild_t_webb"]["upper_pp_edge"][
                "truncated_at_grid_edge"]},
        "code": code,
        "manuscript_action": ACTION[code],
    }

    widening = float(width - width_c)
    expectation_check = {
        "predicted_widening_pp": list(EXPECT_WIDENING_PP),
        "realized_widening_pp": widening,
        "inside_prediction": bool(EXPECT_WIDENING_PP[0] <= widening
                                  <= EXPECT_WIDENING_PP[1]),
        "widening_at_lower_edge_pp": float(-dL),
        "widening_at_upper_edge_pp": float(dU),
        "predicted_concentrated_at_upper": True,
        "realized_concentrated_at_upper": bool(dU > -dL),
        "predicted_modal_branch": EXPECT_MODAL_BRANCH,
        "realized_branch": code,
        "modal_branch_realized": bool(code == EXPECT_MODAL_BRANCH),
        "printing_slack_pp": {"lower_downward": 0.0463, "upper_upward": 0.0269},
        "cr_secondary_predicted": {
            "t_crit_G_minus_1": 2.0422724563012373,
            "t_crit_df_bm_expected_range": [2.26, 2.31],
            "cr2_expected_pp": [2.7, 8.9], "cr3_expected_pp": [2.5, 9.1]},
        "cr_secondary_realized": {
            "t_crit_df_bm": out_reads[R2]["t_crit_df_bm"],
            "df_bm": out_reads[R2]["df_bm"],
            "cr2_pp": out_reads[R2]["cr2_t_interval_df_bm"]["marginal_ci95_pp"],
            "cr3_pp": out_reads[R2]["cr3_t_interval_df_bm"]["marginal_ci95_pp"]},
    }

    payload = {
        "mode": "floor_inference_correction_v2",
        "status": "OK",
        "spec": (
            "Webb six-point wild-cluster bootstrap-t (B=9999, fresh "
            "default_rng(42) per read per procedure) as the PRIMARY floor-read "
            "interval, with the committed Rademacher construction replayed "
            "bit-exactly alongside (gate P4); Bell-McCaffrey/Imbens-Kolesar "
            "data-driven df derived from the intercept-only WLS construction "
            "(h_g = W_g/sum(W); df = (sum lambda)^2/sum(lambda^2) over the "
            "eigenvalues of G Omega G'), self-tested against df = G-1 at equal "
            "clusters (blocking P6); Carter-Schnepel-Steigerwald effective "
            "clusters G* = 1/sum(h^2), the same Herfindahl-inverse convention "
            "as the committed loan/stratum 25.777; restricted (WCR) CI by "
            "401-point test inversion over +/-5 SE_CR1 under Webb weights; "
            "v1's grid-edge truncation convention kept and flagged, never "
            "_map_draws's exclusion convention. Reads R1-R4 (R5 excluded ex "
            "ante), primary object R2. Parity gates P1-P7 blocking. NO engine "
            "runs; PCHIP mapping only. v1 and its artifact are FROZEN and are "
            "read, never written."),
        "spec_source": "specs/SPEC_round28_C1_C2_C3_C6.md SPEC C1",
        "spec_deviations": [
            "SPEC's singular df_BM: the Satterthwaite quadratic form differs "
            "between CR2 ((1-h)^-1/2) and CR3 ((1-h)^-1), so one df cannot "
            "serve both. df_bm_by_estimator carries all three; the headline "
            "df_bm/t_crit_df_bm is CR2's, which is the BM adjustment the spec "
            "derives. Each interval uses its own estimator's df.",
            "crk_t_interval is kept at t(G-1) so gate P4 can replay v1 "
            "bit-exactly; the BM/IK variant is the sibling "
            "crk_t_interval_df_bm. Both carry df_used.",
            "WCR studentizes the observed statistic with the UNRESTRICTED "
            "SE_CR1 per SPEC C1.2(4)'s literal formula, while SE* is "
            "recomputed on each restricted resample; recorded as "
            "wcr_inverted.studentizer so it is not read as the symmetric "
            "textbook variant.",
            "One Webb weight matrix is drawn per read and reused across the "
            "401-point WCR grid (MacKinnon-Webb practice; the spec is silent).",
            "Verdict precedence when one endpoint moves outward >0.10pp and "
            "the other inward >0.10pp: WIDENS, with "
            "mixed_outward_and_inward_move recorded.",
            "Added beyond the literal schema because C2 cannot consume the t* "
            "CSVs without them: R_smm, se_cr1/2/3_smm, cluster_strata, "
            "n_cohort_months, sum_h.",
            "t_star_draws_path is populated for R2 only; SPEC C1.6 requires "
            "exactly the two R2 CSVs and no others.",
        ],
        "parity_gates": gate_report,
        "parity_gates_all_pass": True,
        "reads": out_reads,
        "verdict": verdict,
        "expectation_check": expectation_check,
        "tstar_csv": {"webb": str(TSTAR_WEBB_CSV),
                      "rademacher": str(TSTAR_RADE_CSV),
                      "read": R2, "n_rows": B_WILD,
                      "format": "one header line 't_star' then 9999 rows, %.17g",
                      "consumed_by": "layer_convolution (SPEC C2)"},
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=lambda o: o.item())
        f.write("\n")

    print("\n" + "=" * 72)
    print(json.dumps(verdict, indent=2, default=lambda o: o.item()))
    print(f"\nfrozen -> {RESULTS_JSON}")
    print(f"t* draws -> {TSTAR_WEBB_CSV}")
    print(f"t* draws -> {TSTAR_RADE_CSV}")


if __name__ == "__main__":
    main()
