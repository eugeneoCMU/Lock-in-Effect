# DRAFT R30 — D1: the E7 + CR1 package (one commit: tex + gates + tests)

Drafting agent. Nothing here was applied. Every OLD span below was counted in the
live file at draft time; every NEW numeric literal carries its full-precision
artifact source and its rounding derivation. All artifact paths are relative to
the repo root
`/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/agency-mbs-runoff-qt-424945`.

Counts at draft time: `paper/v18/revised_paper_v18.tex` = 1437 lines;
`paper/v18/revised_paper_v18_long_abstract.tex` = 1437 lines;
`tools/liveness_gates.py` = 4801 lines, 106 gates; `tests/` = 451 tests.

**Package total: 5 tex pairs (× 2 files) + 4 gates-file pairs + 1 new test file
(20 tests). One new gate (#107). 4 new numeric literals in the tex. 5 flags.**

---

## 0. Decisions taken, and why

**Two CR1 rows, not one.** The ladder's stated job (caption line 446) is that
"Every row prices one layer". Two dimensions are on display — the sandwich
(CR1→CR2→CR3, increasing conservatism) and the reference distribution
(conventional `G-1` vs data-driven Bell–McCaffrey) — and the table currently
carries the second dimension only for CR2 and CR3, so the grid is 2×2 with four
strays. CR1 is not a decorative third: it is the standard error the primary
construction studentizes with (`wild_t_webb.studentization_scale`: "CR1 in both
the numerator and the bootstrap denominator"; `wcr_inverted` lays its 401-point
grid out in ±5 CR1 standard errors; SPEC C1 line 44 "**CR1** in both numerator
and bootstrap denominator (matched, correct)"). Without a CR1 row a reader
cannot see what the bootstrap is correcting *from*. Printing both CR1 rows
completes the 3×2 grid and makes the baseline explicit.

**The collision is real and is handled in the tablenote, not by dropping a row.**
CR1 at Bell–McCaffrey df prints `$+2.8$ to $+8.8$`, byte-identical to the
committed CR3 `t(30)` row (whole-file count of that string is currently 1; after
the edit it is 2). At full precision they are **not** the same interval:

| | lower (pp) | upper (pp) |
|---|---|---|
| CR1 @ BM df 6.2462… | 2.753082197773479 | 8.79621469284935 |
| CR3 @ t(30) | 2.7732237922014704 | 8.774405758790092 |
| difference | −0.020142 | +0.021809 |

They agree to the printed digit and differ in the second decimal. That near-tie
is informative — the two ways of buying conservatism (leverage adjustment vs.
small-sample reference distribution) are near-substitutes at this leverage
profile — so it is stated in the tablenote and gated (`c1b != cr3` at full
precision, plus `abs diff < 0.05`, in the test), rather than being papered over
by suppressing a row. A **one-row fallback** is specified in §2.5 if Eugene
prefers the smaller surface.

**Rounding: plain round-to-nearest at 1dp.** `f"{x:+.1f}"` on the full-precision
artifact reproduces 15 of the 16 currently printed ladder endpoints. The single
exception is the committed CR2 @ BM upper (`9.149768955601752` prints as
`+9.2`); see **FLAG 1**. The two new rows are printed by the rule that 15/16 of
the table already obeys, and a referee recomputing from the artifact verifies
them directly. Nothing in this package prints a double-rounded digit.

**Floor percentages at 3dp.** Whole-file convention: `4.991`×15, `4.695`×5,
`5.334`×5, `3.972`×1, `6.910`×1 (trailing zero retained — `6.910` is the
precedent that makes `5.800` correct rather than `5.8`).

---

## 1. E7 — the designer-units clause at the cap-design site

Site: `paper/v18/revised_paper_v18.tex` line **581** (1715 chars; the sentence
occupies in-line chars 469–1060). Post-CR1 the line number becomes **583** (the
two inserted rows shift everything below line 455 by +2); the pair is anchored
on a unique string, so application order does not matter.

Sub-anchor used (`; the floor read's…` clause, whole-file count **1**, tools/
and tests/ hits **0**):

**OLD** (count 1 → 0)
```
; the floor read's own sampling error widens the identified margin further (Section~\ref{sec:robustness-floor}).
```

**NEW-A — the recon's clause verbatim (default; instruction-compliant)** (count 0 → 1)
```
; the floor read's own sampling error widens the identified margin further, and expressed in the units a cap designer would have to plug in, its wild-cluster interval runs from 4.177\% to 5.800\% (Section~\ref{sec:robustness-floor}).
```

**NEW-B — recommended one-noun-phrase precision variant** (identical except the pronoun)
```
; the floor read's own sampling error widens the identified margin further, and expressed in the units a cap designer would have to plug in, the mid-cut read's wild-cluster interval runs from 4.177\% to 5.800\% (Section~\ref{sec:robustness-floor}).
```

Why B is offered: in A, `its` sits after "the floor read's own sampling error",
whose head noun is *error*; "the error's wild-cluster interval" is the wrong
object (the interval is the *read's*, in floor units). "Mid-cut" is not a new
term — the same sentence already says "the depth at which out-of-the-moneyness
is cut … at the deepest cut … at the shallowest" — and it is exactly right: the
band 4.70–5.33 is R3's and R1's point reads (`point_cpr_pct` 4.695495330057254
and 5.334239649398553), while the wild-cluster interval is the **middle** read
R2's (`point_cpr_pct` 4.990624060575566, the manuscript's 4.991%). **Gate #107
is written to pass under either wording** — the pinned span excludes the
pronoun. Coordinator picks one; the singular "the floor read" is pre-existing
committed text (landed in 00b96d1), not introduced here.

### Value derivation

Source: `hazard/data/floor_inference_correction_v2_results.json`,
`reads["R2_2018_gap<=-0.0025_age>=12"].wild_t_webb.floor_ci95_pct`.

| printed | full precision | derivation |
|---|---|---|
| `4.177\%` | 4.176744144633416 | `f"{x:.3f}"` → `4.177` |
| `5.800\%` | 5.800284985839921 | `f"{x:.3f}"` → `5.800` (trailing zero kept, `6.910` precedent) |

Same object's `marginal_ci95_pp` = [2.8549950653913494, 8.677971792194077] —
i.e. this is the floor-units preimage of the paper's binding `[+2.9, +8.7]`, not
a new quantity. The map is inverse and neither endpoint is grid-truncated:
`upper_pp_edge.floor_pct` = 4.176744144633416 (marginal 8.678, `truncated_at_grid_edge`
false), `lower_pp_edge.floor_pct` = 5.800284985839921 (marginal 2.855, false).
B = 9999, seed 42, Webb weights, WCU-t DGP, endpoints mapped SMM→CPR%→PCHIP.

Consistency, checked: [4.177, 5.800] strictly encloses the depth-cut band
[4.70, 5.33] printed in the same sentence, which is precisely the paper's
committed posture that the floor read's sampling error is the binding layer and
is wider than the depth-cut band (gate #73's own comment says so). It also
encloses the age-standardized 5.508% and the Fannie 5.52% read, and 5.800 sits
inside the floor grid (edge 6.0), so no truncation caveat is owed.

---

## 2. CR1 — the ladder rungs

### 2.1 Pair C1 — the conventional-df rung

**OLD** (2-line anchor, whole-file count **1**)
```
Percentile cluster bootstrap & $+3.0$ to $+8.0$ & --- (1000-replicate) & demoted; under-covers at 31 clusters \\
CR2 $t$ & $+3.0$ to $+8.6$ & $t(30)$, $G-1$ & conventional df \\
```
**NEW**
```
Percentile cluster bootstrap & $+3.0$ to $+8.0$ & --- (1000-replicate) & demoted; under-covers at 31 clusters \\
CR1 $t$ & $+3.2$ to $+8.3$ & $t(30)$, $G-1$ & no leverage adjustment \\
CR2 $t$ & $+3.0$ to $+8.6$ & $t(30)$, $G-1$ & conventional df \\
```

### 2.2 Pair C2 — the Bell–McCaffrey rung

**OLD** (2-line anchor, whole-file count **1**)
```
Wild-$t$, Webb & $+2.9$ to $+8.7$ & bootstrap, $B = 9{,}999$ & primary; the binding layer \\
CR2 $t$, Bell--McCaffrey & $+2.4$ to $+9.2$ & $t(5.1)$, data-driven & small-sample df \\
```
**NEW**
```
Wild-$t$, Webb & $+2.9$ to $+8.7$ & bootstrap, $B = 9{,}999$ & primary; the binding layer \\
CR1 $t$, Bell--McCaffrey & $+2.8$ to $+8.8$ & $t(6.2)$, data-driven & small-sample df \\
CR2 $t$, Bell--McCaffrey & $+2.4$ to $+9.2$ & $t(5.1)$, data-driven & small-sample df \\
```

Placement keeps the table's existing block structure (percentile → conventional-df
sandwiches → the two wild rows → BM sandwiches → restricted inversion) and makes
both blocks read CR1, CR2, CR3. No gate or test pins ladder row order today
(verified: 0 hits in `tools/` and `tests/` for `tab:ladder`, `Webb`,
`Rademacher`, `McCaffrey`, `floor_inference_correction_v2`); gate #107 below
newly pins CR1-before-CR2 in both blocks.

**No column widens.** Column-4 max stays `demoted; under-covers at 31 clusters`
(35 chars) — the new `no leverage adjustment` is 22; `CR1 $t$, Bell--McCaffrey`
is glyph-for-glyph the width of the existing `CR2 $t$, Bell--McCaffrey`;
`$t(6.2)$, data-driven` matches `$t(5.1)$, data-driven`; the interval cells
match the existing shape. The float grows by two rows in height only — no
overfull-hbox exposure. Pagination on a 129pp build still wants the coordinator's
eye (`[!t]`).

### 2.3 Value derivations

Source: `hazard/data/floor_inference_correction_v2_results.json`,
`reads["R2_2018_gap<=-0.0025_age>=12"]`. Read identified as the 2018 leg's
mid-grid anchor by `n_clusters` = 31 and `point_cpr_pct` = 4.990624060575566.

| printed cell | key | full precision | derivation |
|---|---|---|---|
| `$+3.2$` | `cr1_t_interval.marginal_ci95_pp[0]` | 3.1532134720806244 | `f"{x:+.1f}"` → `+3.2` |
| `$+8.3$` | `cr1_t_interval.marginal_ci95_pp[1]` | 8.349880202430665 | `f"{x:+.1f}"` → `+8.3` |
| `$t(30)$, $G-1$` | `cr1_t_interval.df_used` / `.df_kind` | 30.0 / `"G_minus_1"` | exact; `t_crit` 2.0422724563012373 = `t_crit_G_minus_1` |
| `$+2.8$` | `cr1_t_interval_df_bm.marginal_ci95_pp[0]` | 2.753082197773479 | `f"{x:+.1f}"` → `+2.8` |
| `$+8.8$` | `cr1_t_interval_df_bm.marginal_ci95_pp[1]` | 8.79621469284935 | `f"{x:+.1f}"` → `+8.8` |
| `$t(6.2)$` | `cr1_t_interval_df_bm.df_used` = `df_bm_by_estimator.cr1` | 6.246229243215659 | `f"{x:.1f}"` → `6.2`; `t_crit` 2.423719191530971 |

`$+8.3$` is the one endpoint in this package where the two competing rounding
readings diverge (8.34988 → **8.3** by nearest; → 8.4 only under a
double-rounding-half-up rule). Nearest is what 15/16 of the committed table
already does; see FLAG 1.

Neither CR1 rung leans on a grid edge: all four
`{lower,upper}_pp_edge.truncated_at_grid_edge` are **false** (unlike the
committed CR3-BM and WCR rows, whose lower edges are `true` — FLAG 4).

Provenance for the caption credit: `cr1_t_interval` is **bit-identical** in v1
(`hazard/data/floor_inference_correction_results.json`) and v2 — verified
`==` on the list — so the `t(30)` rung credits to `floor_inference_correction`
exactly as CR2/CR3 do. `cr1_t_interval_df_bm` exists **only** in v2, which the
caption already credits with "Bell--McCaffrey degrees of freedom"; no new run
tag is needed. (SPEC source: `specs/SPEC_round28_C1_C2_C3_C6.md` SPEC C1;
artifact `status` = "OK", `parity_gates_all_pass` = true, all 10 parity gates
including `P6_bm_df_equal_cluster_selftest`.)

### 2.4 Pair C3 — the caption run-tag credit

**OLD** (whole-file count **1**; line 446)
```
\texttt{floor\_inference\_correction} (Rademacher wild-$t$; CR2/CR3 at $t(30)$)
```
**NEW**
```
\texttt{floor\_inference\_correction} (Rademacher wild-$t$; CR1--CR3 at $t(30)$)
```
One token. `floor\_inference\_correction` whole-file count is unchanged at 9
(gate #73 asserts its presence only).

### 2.5 Pair C4 — the tablenote

**OLD** (sub-span of line 465; whole-file count **1**)
```
both cluster-robust variants: the 5.1 shown is CR2's, and CR3's own is smaller. The effective cluster count
```
**NEW**
```
all three cluster-robust variants: the 6.2 and 5.1 shown are CR1's and CR2's, and CR3's own is smaller still. CR1 applies no leverage adjustment --- it is the narrowest of the three sandwiches --- and is the standard error the wild rows studentize with, so its two rows are the ladder's baseline rather than competing reads; its Bell--McCaffrey row printing CR3's conventional-df interval is an accident of this leverage profile, not an identity. The effective cluster count
```

Everything from "The effective cluster count is 5.9 …" to the end of the note is
byte-identical to the committed text (5.9 / 25.8 / 31 / 0.33 untouched). Note
length 530 → 866 chars.

Each new claim is measured, not asserted:

- *"all three … the 6.2 and 5.1 shown are CR1's and CR2's, and CR3's own is
  smaller still"* — `df_bm_by_estimator` = {cr1 6.246229243215659, cr2
  5.094518332742745, cr3 4.102961856265757}; the strict ordering is gated.
- *"the narrowest of the three sandwiches"* — `se_cr1_smm` 0.0003053670536820312
  < `se_cr2_smm` 0.00033057990461014727 < `se_cr3_smm` 0.000359463046358492;
  gated. (Marginal-scale widths, for the record: CR1 5.1967, CR2 5.5787, CR3
  6.0012; percentile 5.0442, Webb 5.8230.)
- *"the standard error the wild rows studentize with"* — both
  `wild_t_{rademacher,webb}.studentization_scale` read "CR1 in both the numerator
  and the bootstrap denominator". Scope is deliberately "the wild rows", not
  "the bootstrap rows": `wcr_inverted.studentizer` uses the unrestricted CR1 in
  the numerator but recomputes `SE*` on each restricted resample, so a claim
  covering it would over-reach. **Optional add-on** if Eugene wants the third
  row covered: append ", and the unit the restricted inversion's grid is laid
  out in" — supported by SPEC C1.2(4) ("±5 CR1-SEs") and
  `wcr_inverted.se_span` = 5.0. Not included by default; it lengthens the note
  and adds no printed literal.
- *"an accident of this leverage profile, not an identity"* — the two intervals
  differ by 0.0201/0.0218 pp (table in §0); `!=` at full precision is gated.

### 2.6 Fallback: one row only

If the twin-printing is judged not worth the tablenote sentence: keep pair C1
(the `t(30)` rung), drop pair C2, and use this shorter C4:

```
all three cluster-robust variants: the 6.2 shown for CR1's own sibling read is not the 5.1 shown here, which is CR2's, and CR3's own is smaller still.
```

I do not recommend it: it prints `6.2` while suppressing the row it belongs to,
and it leaves the BM column a 2-of-3 sample for no stated reason. The full
package is the coherent one.

---

## 3. GATES — new gate #107 in `tools/liveness_gates.py`

One gate covers both halves of the package: same artifact, same read. It is the
**first gate in the suite to open `floor_inference_correction_v2_results.json`
numerically** (today that file is touched only as a tex-literal substring in
gate #73's line 4449 and as a hard-coded `5.822976726802727` threshold copied
into gate #105's line 769).

Verified before drafting: **all four insertion anchors below have whole-file
count 1** in the 4801-line `tools/liveness_gates.py`.

### 3.1 Anchor A — the spans dict (current lines 721–726)

**OLD**
```python
    "conversion_def": "note rate less the vintage guarantee fee and base "
                      "servicing, $\\Delta = 0.80$ points",
}


def coupon_convention_check(tex: str) -> tuple[bool, dict]:
```
**NEW**
```python
    "conversion_def": "note rate less the vintage guarantee fee and base "
                      "servicing, $\\Delta = 0.80$ points",
}


FLOOR_LADDER_SPANS = {
    # ROUND-30 E7/CR1 (gate #107): the ladder's baseline rung and the floor
    # read's interval in the units a cap is set in. What the gate protects:
    # (a) both CR1 rungs, cell for cell, against the artifact they are rounded
    # from; (b) the tablenote's three claims about CR1 (df ownership, that it
    # is the narrowest sandwich and the wild rows' studentizer, and that its
    # Bell--McCaffrey row coinciding with CR3's conventional-df row is a
    # printed accident and not an identity) --- without that sentence the
    # table shows two rows with identical intervals and no reason; (c) the
    # run-tag credit, which is only honest because the t(30) rung is
    # bit-identical in the committed run; (d) the designer-units restatement,
    # which is the SAME read's Webb interval expressed in floor units, so a
    # drift between it and the $+2.9$ to $+8.7$ the paper quotes is a defect.
    "cr1_conventional": "CR1 $t$ & $+3.2$ to $+8.3$ & $t(30)$, $G-1$ & no "
                        "leverage adjustment",
    "cr1_bell_mccaffrey": "CR1 $t$, Bell--McCaffrey & $+2.8$ to $+8.8$ & "
                          "$t(6.2)$, data-driven & small-sample df",
    "df_ownership": "the 6.2 and 5.1 shown are CR1's and CR2's, and CR3's own "
                    "is smaller still",
    "cr1_is_the_baseline": "is the standard error the wild rows studentize "
                           "with, so its two rows are the ladder's baseline "
                           "rather than competing reads",
    "printed_tie_is_not_an_identity": "an accident of this leverage profile, "
                                      "not an identity",
    "run_credit": "\\texttt{floor\\_inference\\_correction} (Rademacher "
                  "wild-$t$; CR1--CR3 at $t(30)$)",
    "designer_frame": "in the units a cap designer would have to plug in",
    "designer_units": "wild-cluster interval runs from 4.177\\% to 5.800\\%",
}

FLOOR_LADDER_READ = "R2_2018_gap<=-0.0025_age>=12"


def coupon_convention_check(tex: str) -> tuple[bool, dict]:
```

Note `designer_units` deliberately starts at "wild-cluster", so the gate is
indifferent between E7 NEW-A (`its …`) and NEW-B (`the mid-cut read's …`) —
verified: both pass.

### 3.2 Anchor B — the check function (current lines 772–776)

**OLD**
```python
    info["artifact_ok"] = art_ok
    return (not missing) and art_ok, info


def buyback_bracket_check(tex: str) -> tuple[bool, dict]:
```
**NEW**
```python
    info["artifact_ok"] = art_ok
    return (not missing) and art_ok, info


def floor_ladder_check(tex: str) -> tuple[bool, dict]:
    """Gate #107's rule, as a function so a battery can exercise it."""
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    missing = sorted(k for k, v in FLOOR_LADDER_SPANS.items()
                     if v not in tex_nc)
    info: dict = {"missing": missing}
    if missing:
        return False, info
    ordered = (tex_nc.index(FLOOR_LADDER_SPANS["cr1_conventional"])
               < tex_nc.index("CR2 $t$ & $+3.0$ to $+8.6$")
               and tex_nc.index(FLOOR_LADDER_SPANS["cr1_bell_mccaffrey"])
               < tex_nc.index("CR2 $t$, Bell--McCaffrey"))
    info["ordered"] = ordered
    art = ROOT / "hazard" / "data" / "floor_inference_correction_v2_results.json"
    if not art.exists():
        return False, {**info, "artifact": "MISSING"}
    fi = json.loads(art.read_text())
    rd = fi.get("reads", {}).get(FLOOR_LADDER_READ, {})
    cr1 = rd.get("cr1_t_interval", {})
    cr1bm = rd.get("cr1_t_interval_df_bm", {})
    cr3 = rd.get("cr3_t_interval", {})
    webb = rd.get("wild_t_webb", {})
    c1 = cr1.get("marginal_ci95_pp") or [None, None]
    c1b = cr1bm.get("marginal_ci95_pp") or [None, None]
    wf = webb.get("floor_ci95_pct") or [None, None]
    dfbm = rd.get("df_bm_by_estimator", {})
    if None in (c1[0], c1b[0], wf[0]):
        return False, {**info, "artifact": "INCOMPLETE"}
    df1 = cr1bm.get("df_used", 0.0)
    art_ok = (
        fi.get("status") == "OK"
        and fi.get("parity_gates_all_pass") is True
        and rd.get("n_clusters") == 31
        # the two CR1 rungs reproduce their printed cells from full precision
        and f"${c1[0]:+.1f}$ to ${c1[1]:+.1f}$" == "$+3.2$ to $+8.3$"
        and f"${c1b[0]:+.1f}$ to ${c1b[1]:+.1f}$" == "$+2.8$ to $+8.8$"
        and cr1.get("df_used") == 30.0
        and cr1.get("df_kind") == "G_minus_1"
        and cr1bm.get("df_kind") == "bell_mccaffrey_imbens_kolesar"
        and f"$t({df1:.1f})$" == "$t(6.2)$"
        # neither CR1 rung is carried by a grid-edge truncation
        and not any(cell[edge]["truncated_at_grid_edge"]
                    for cell in (cr1, cr1bm)
                    for edge in ("lower_pp_edge", "upper_pp_edge"))
        # the tablenote's three claims about CR1
        and dfbm["cr1"] > dfbm["cr2"] > dfbm["cr3"]
        and rd["se_cr1_smm"] < rd["se_cr2_smm"] < rd["se_cr3_smm"]
        and c1b != cr3.get("marginal_ci95_pp")
        # the designer-units clause is the SAME read's Webb interval in floor
        # units, and the floor-to-marginal map is inverse
        and f"{wf[0]:.3f}\\% to {wf[1]:.3f}\\%" == "4.177\\% to 5.800\\%"
        and webb["upper_pp_edge"]["floor_pct"] < webb["lower_pp_edge"]["floor_pct"]
        and abs(webb["marginal_ci95_pp"][0] - 2.8549950653913494) < 1e-9
        and abs(webb["marginal_ci95_pp"][1] - 8.677971792194077) < 1e-9
    )
    info["artifact_ok"] = art_ok
    return ordered and art_ok, info


def buyback_bracket_check(tex: str) -> tuple[bool, dict]:
```

`re`, `json`, `ROOT` are already imported/defined in the module (used by
`convolved_line_check` and `coupon_convention_check` immediately above). The
`\%` in `designer_units` survives the comment-stripping regex because the
lookbehind `(?<!\\)` protects escaped percents — verified on the simulated file.

### 3.3 Anchor C — the call in `main()` (current lines 4772–4773)

**OLD**
```python
    cc_ok, _cc = coupon_convention_check(tex)
    failures += 0 if cc_ok else 1
```
**NEW**
```python
    cc_ok, _cc = coupon_convention_check(tex)
    failures += 0 if cc_ok else 1
    fl_ok, _fl = floor_ladder_check(tex)
    failures += 0 if fl_ok else 1
```

### 3.4 Anchor D — the print in `main()` (current lines 4782–4783)

**OLD**
```python
          f"artifact_ok={_cl.get('artifact_ok')}, "
          f"missing={_cl['missing'] or 'none'}")
```
**NEW**
```python
          f"artifact_ok={_cl.get('artifact_ok')}, "
          f"missing={_cl['missing'] or 'none'}")
    print(f"[{'PASS' if fl_ok else 'FAIL'}] floor-read ladder and designer "
          f"units (gate #107): "
          f"{len(FLOOR_LADDER_SPANS) - len(_fl['missing'])}/"
          f"{len(FLOOR_LADDER_SPANS)} spans present, "
          f"ordered={_fl.get('ordered')}, "
          f"artifact_ok={_fl.get('artifact_ok')}, "
          f"missing={_fl['missing'] or 'none'}")
```

### 3.5 Gate verification already done (standalone, on a scratchpad copy — the repo script was never executed)

The function body above was run verbatim against an in-memory simulation of the
post-edit manuscript:

| probe | result |
|---|---|
| post-edit main tex, E7 variant A | `(True, {'missing': [], 'ordered': True, 'artifact_ok': True})` |
| post-edit main tex, E7 variant B | `(True, …)` |
| post-edit long-abstract variant | `(True, …)` |
| **current** manuscript (pre-edit) | `False`, 7 spans missing — the gate is live, not vacuous |
| removal of each of the 8 spans | gate `False` in all 8 |
| CR1 row moved after CR2 | gate `False`, `ordered` `False` |
| `$+3.2$ to $+8.3$` → `$+3.3$ to $+8.3$` | `False` |
| `$+2.8$ to $+8.8$ & $t(6.2)$` → `…$+8.9$…` | `False` |
| `$t(6.2)$` → `$t(6.3)$` | `False` |
| `4.177\% to 5.800\%` → `…5.801\%` | `False` |

Gate #73 re-checked on the simulated post-edit tex: all seven of its tex-side
conditions still hold (`$+3.0$ to $+8.0$` count 5 ≥ 2; `$+2.9$ to $+8.7$` count
8 ≥ 4; the four literal presences).

### 3.6 Gate count

106 → **107**. No test or tool asserts the count. One stale-able doc reference:
`specs/DRAFT_R29_length_levers.md:594` says "106 gates, ALL PASS" — a superseded
draft, coordinator's call whether to touch it.

---

## 4. TESTS — new file `tests/test_floor_ladder_gate.py`

Structure copied from `tests/test_convolved_line_gate.py` (the #105 battery),
extended with the artifact-derivation block that no ladder test has today
(verified: 0 hits in `tests/` for `tab:ladder`, `Webb`, `Rademacher`,
`McCaffrey`, `floor_inference_correction_v2`). **20 tests; 451 → 471.**

```python
"""Battery for gate #107 (round-30 E7/CR1: the CR1 rungs and the designer units).

Same convention as the #105/#106 batteries: mutations remove ALL occurrences of
a span, and every mutation is verified non-vacuous before it is applied. The
artifact block is the first in the suite to open
floor_inference_correction_v2_results.json, so it also pins the derivations the
two new rows and the floor-units clause are printed from.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    FLOOR_LADDER_READ,
    FLOOR_LADDER_SPANS,
    floor_ladder_check,
)

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
ART = json.loads((ROOT / "hazard" / "data"
                  / "floor_inference_correction_v2_results.json").read_text())
RD = ART["reads"][FLOOR_LADDER_READ]


def test_gate_passes_on_the_manuscript():
    ok, info = floor_ladder_check(TEX)
    assert ok, f"gate #107 fails on the shipped manuscript: {info}"


@pytest.mark.parametrize("key", sorted(FLOOR_LADDER_SPANS))
def test_each_span_removal_fails(key):
    span = FLOOR_LADDER_SPANS[key]
    assert span in TEX, f"span {key!r} not in the manuscript (vacuous mutation)"
    ok, _ = floor_ladder_check(TEX.replace(span, ""))
    assert not ok, f"gate #107 survives removal of span {key!r}"


def test_variant_carries_the_spans_too():
    ok, info = floor_ladder_check(VARIANT)
    assert ok, f"gate #107 fails on the long-abstract variant: {info}"


def test_the_ladder_order_is_gated():
    row = FLOOR_LADDER_SPANS["cr1_conventional"] + " \\\\\n"
    assert TEX.count(row) == 1
    moved = TEX.replace(row, "", 1).replace(
        "CR3 $t$ & $+2.8$ to $+8.8$", row + "CR3 $t$ & $+2.8$ to $+8.8$", 1)
    ok, info = floor_ladder_check(moved)
    assert not ok and info["ordered"] is False


@pytest.mark.parametrize("printed,perturbed", [
    ("$+3.2$ to $+8.3$", "$+3.3$ to $+8.3$"),
    ("$+2.8$ to $+8.8$ & $t(6.2)$", "$+2.8$ to $+8.9$ & $t(6.2)$"),
    ("$t(6.2)$", "$t(6.3)$"),
    ("4.177\\% to 5.800\\%", "4.177\\% to 5.801\\%"),
])
def test_a_wrong_digit_fails(printed, perturbed):
    assert TEX.count(printed) == 1, f"{printed!r} is not the single site"
    ok, _ = floor_ladder_check(TEX.replace(printed, perturbed))
    assert not ok, f"gate #107 survives {printed!r} -> {perturbed!r}"


def test_the_printed_cr1_rungs_are_the_artifact_rounded():
    c1 = RD["cr1_t_interval"]["marginal_ci95_pp"]
    c1b = RD["cr1_t_interval_df_bm"]["marginal_ci95_pp"]
    assert f"${c1[0]:+.1f}$ to ${c1[1]:+.1f}$" == "$+3.2$ to $+8.3$"
    assert f"${c1b[0]:+.1f}$ to ${c1b[1]:+.1f}$" == "$+2.8$ to $+8.8$"
    assert f"$t({RD['cr1_t_interval_df_bm']['df_used']:.1f})$" == "$t(6.2)$"
    assert RD["cr1_t_interval"]["t_crit"] == RD["t_crit_G_minus_1"]
    assert (RD["cr1_t_interval_df_bm"]["t_crit"]
            == RD["t_crit_df_bm_by_estimator"]["cr1"])


def test_the_conventional_rung_is_the_committed_run_bit_for_bit():
    """The caption credits CR1--CR3 at t(30) to floor_inference_correction."""
    v1 = json.loads((ROOT / "hazard" / "data"
                     / "floor_inference_correction_results.json").read_text())
    assert (v1["reads"][FLOOR_LADDER_READ]["cr1_t_interval"]["marginal_ci95_pp"]
            == RD["cr1_t_interval"]["marginal_ci95_pp"])


def test_the_printed_tie_with_cr3_is_not_an_identity():
    c1b = RD["cr1_t_interval_df_bm"]["marginal_ci95_pp"]
    cr3 = RD["cr3_t_interval"]["marginal_ci95_pp"]
    assert c1b != cr3, "the tablenote calls the tie an accident, not an identity"
    assert all(abs(a - b) < 0.05 for a, b in zip(c1b, cr3)), \
        "the rows no longer agree to the printed digit; the note is stale"


def test_cr1_is_the_narrowest_sandwich_and_carries_the_largest_bm_df():
    assert RD["se_cr1_smm"] < RD["se_cr2_smm"] < RD["se_cr3_smm"]
    d = RD["df_bm_by_estimator"]
    assert d["cr1"] > d["cr2"] > d["cr3"]


def test_the_designer_units_clause_is_the_webb_interval_in_floor_units():
    w = RD["wild_t_webb"]
    lo, hi = w["floor_ci95_pct"]
    assert f"{lo:.3f}\\% to {hi:.3f}\\%" == "4.177\\% to 5.800\\%"
    # the map is inverse: the LOW floor carries the HIGH marginal
    assert w["upper_pp_edge"]["floor_pct"] < w["lower_pp_edge"]["floor_pct"]
    assert abs(w["marginal_ci95_pp"][0] - 2.8549950653913494) < 1e-9
    assert abs(w["marginal_ci95_pp"][1] - 8.677971792194077) < 1e-9
    assert not w["lower_pp_edge"]["truncated_at_grid_edge"]
    assert not w["upper_pp_edge"]["truncated_at_grid_edge"]
```

Every assertion in the artifact block was executed against the live artifact and
passes. The `test_a_wrong_digit_fails` `count == 1` guards were verified on the
simulated post-edit tex (all four are single-site).

---

## 5. Zero-slack ledger

### 5.1 New numeric literals (4)

| literal | count before → after | full-precision source | rounding |
|---|---|---|---|
| `4.177` | 0 → 1 | `wild_t_webb.floor_ci95_pct[0]` = 4.176744144633416 | `:.3f` |
| `5.800` | 0 → 1 | `wild_t_webb.floor_ci95_pct[1]` = 5.800284985839921 | `:.3f` |
| `$+3.2$` | 0 → 1 | `cr1_t_interval.marginal_ci95_pp[0]` = 3.1532134720806244 | `:+.1f` |
| `$+8.3$` | 0 → 1 | `cr1_t_interval.marginal_ci95_pp[1]` = 8.349880202430665 | `:+.1f` |

All in `hazard/data/floor_inference_correction_v2_results.json`,
`reads["R2_2018_gap<=-0.0025_age>=12"]`.

### 5.2 Re-used literals (already in the file; counts move)

| literal | before → after | where the new occurrence lands |
|---|---|---|
| `$+2.8$` | 4 → 5 | CR1-BM row, from 2.753082197773479 |
| `$+8.8$` | 1 → 2 | CR1-BM row, from 8.79621469284935 |
| `$+2.8$ to $+8.8$` | 1 → 2 | CR1-BM row (the flagged collision with CR3 `t(30)`) |
| `$+3.2$ to $+8.3$` | 0 → 1 | CR1 `t(30)` row |
| `t(6.2)` / `$t(6.2)$` | 0 → 1 | CR1-BM df cell, from 6.246229243215659 |
| `t(30)` / `$t(30)$` | 3 → 4 | CR1 `t(30)` df cell (`df_used` 30.0 exactly) |
| `6.2` | 5 → 7 | df cell + tablenote pointer |
| `CR1` | 0 → 5 | 2 rows, caption, 2 tablenote mentions |
| `CR2` | 4 → 3 | caption `CR2/CR3` → `CR1--CR3`; note now says "CR1's and CR2's" |
| `CR3` | 5 → 6 | tablenote gains "CR3's conventional-df interval" |

### 5.3 Verified unmoved (before = after)

`5.1` 36→36 · `t(5.1)` 1→1 · `$+3.0$ to $+8.0$` 5→5 · `$+2.9$ to $+8.7$` 8→8 ·
`$+3.0$ to $+8.6$` 1→1 · `$+2.8$ to $+8.7$` 1→1 · `$+2.4$ to $+9.2$` 1→1 ·
`$+2.3$ to $+9.6$` 1→1 · `$+2.3$ to $+9.1$` 1→1 · `4.70\%` 3→3 · `5.33\%` 7→7 ·
`open below $+4.3$` 3→3 · `binding layer` 10→10 · `floor\_uncertainty` 4→4 ·
`floor\_inference\_correction` 9→9 · `84.0\% of weight imputed` 1→1.

The tablenote's committed second half (5.9 / 25.8 / 31 nominal / 0.33 / "ten
times an equal 31-cluster share" / the demotion sentence) is byte-identical
before and after. Line count 1437 → 1439 in each of the two tex files.

### 5.4 And-forms and quoting sites, checked

- The binding interval is quoted in the `to`-form (`$+2.9$ to $+8.7$`, 8 sites)
  and the and-form (`between $+2.9$ and $+8.7$ points`, gate #99's
  `ABSTRACT_POSTURE["interval"]`) and the bracket-form (`$[+2.9, +8.7]$`, tab:headline).
  **This package touches none of them**: the E7 clause states the same interval
  in *floor* units (4.177–5.800), a different quantity in different units, so no
  and-form of a marginal is created. New-literal search for `and $+8.3$` /
  `and $+3.2$`: 0 before, 0 after.
- Gate #98 `posture_binding_layer` — "The widest layer that does have a coverage
  property is the floor reads' own sampling error, $+2.9$ to $+8.7$ points after
  wild-cluster correction" — is untouched and remains true: it ranks *layers*
  (floor sampling error vs. elasticity vs. baseline level), not constructions
  within the floor layer, and the table already prints wider-than-Webb
  constructions (CR2-BM, CR3-BM, WCR). CR1-BM at width 6.043 joins that set;
  CR1 `t(30)` at width 5.197 is narrower than Webb's 5.823, which is why its
  status cell says "no leverage adjustment" and the tablenote calls the CR1 rows
  the ladder's baseline rather than competing reads.
- tab:headline tablenote (line 438) — "the small-sample degrees of freedom and
  the restricted inversion are wider" — still true with CR1-BM (6.043 > 5.823),
  and CR1 `t(30)` is not a small-sample-df row, so the sentence needs no edit.
- Gate #73's `tex.count` thresholds re-verified on the simulated post-edit file
  (§3.5). Gate #105's hard-coded `5.822976726802727` is untouched.

### 5.5 Nothing else moves

No other `.tex` line, no figure, no bib entry, no run tag, no artifact. No
existing gate span string changes. `paper/v18/revised_paper_v18_long_abstract.tex`
takes the **identical five pairs** (§6).

---

## 6. Variant note

All five tex pairs apply byte-for-byte to
`paper/v18/revised_paper_v18_long_abstract.tex`: every OLD anchor has whole-file
count **1** there, the ladder label sits at the same line 447 and the E7
sentence at the same line 581, and the file goes 1437 → 1439 lines. Simulated
post-edit variant passes gate #107: `(True, {'missing': [], 'ordered': True,
'artifact_ok': True})`. The battery's `test_variant_carries_the_spans_too`
covers it.

---

## 7. Flags for the coordinator

**FLAG 1 — a pre-existing one-endpoint rounding defect, adjacent to this work.**
The committed CR2 @ Bell–McCaffrey row prints `$+9.2$` for
`cr2_t_interval_df_bm.marginal_ci95_pp[1]` = **9.149768955601752**, which rounds
to **9.1** at 1dp. It is the only endpoint of the sixteen that `f"{x:+.1f}"`
does not reproduce; the commit that landed it (1e59852) records "CR2 +2.4..+9.2"
in its message, so it looks like a transcription slip, not a different source
(no other read produces ≈9.2: R1's is 8.556, R3's 9.941). **This package does
not touch it.** I print `$+8.3$` for the new CR1 rung by the nearest-1dp rule
that 15/16 of the table obeys; adopting the alternative double-rounding reading
to "match" would print `+8.4` and propagate the defect to a second cell. If
Eugene wants the repair, it is one literal (count 1, pinned by nothing in
`tools/` or `tests/`):
- OLD: `CR2 $t$, Bell--McCaffrey & $+2.4$ to $+9.2$ & $t(5.1)$, data-driven & small-sample df \\`
- NEW: `CR2 $t$, Bell--McCaffrey & $+2.4$ to $+9.1$ & $t(5.1)$, data-driven & small-sample df \\`
- ledger: `$+2.4$ to $+9.2$` 1→0, `$+2.4$ to $+9.1$` 0→1, `$+9.2$` 26→25 (the
  other 25 are the in-sample point and its relatives — check them before
  assuming the count is inert), `$+9.1$` 1→2.
This is a separate decision from D1 and I have kept it out of the package.

**FLAG 2 — the printed collision is deliberate.** `$+2.8$ to $+8.8$` goes 1 → 2.
Two ladder rows will print the same interval from different constructions, with
the df cell (`$t(30)$` vs `$t(6.2)$`) as the only visible discriminator. The
tablenote sentence and gate #107's `printed_tie_is_not_an_identity` span exist
precisely so the duplicate never appears unexplained. If that sentence is cut in
a later compression pass the gate fails — by design.

**FLAG 3 — E7 wording.** NEW-A is the recon's clause verbatim; NEW-B fixes the
`its` antecedent at the cost of three words. Gate and tests pass under both.
Recommend B.

**FLAG 4 — out of scope, observed in passing.** Two *committed* ladder rows rest
on a grid-edge truncation the table does not disclose: `cr3_t_interval_df_bm`
and `wcr_inverted` both have `lower_pp_edge.truncated_at_grid_edge = true`
(floor 6.116% and 6.181% mapped at the 6.0% grid edge), so their printed `+2.3`
lower endpoints are censored, not measured. Both print `+2.3` for that reason —
another silent coincidence. The two new CR1 rows are clean on all four edges,
and gate #107 asserts it. Worth its own round.

**FLAG 5 — pagination.** The float grows by two rows and the tablenote by ~336
characters, on a `[!t]` table in a 129pp build. No column widens (§2.2), so
there is no overfull-hbox exposure, but the coordinator should confirm the page
count and that tab:ladder still lands where it did.
