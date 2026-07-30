# DRAFT — R32 Wave 2, cluster C-formfork (C-04, C-22, C-23, C-28, C-32)

Region: §III.B, §V (the form fork), §VIII. Baseline read: `paper/v18/revised_paper_v18.tex`,
1,435 lines (the inventory's `a785f3d` baseline is 1,429 lines; the shift is **+0 for lines
≤373, +3 for 374--406, +6 for ≥407**, measured with `difflib` against `git show a785f3d:`).
So the inventory's `.tex:150` = 150, `.tex:227` = 227, `.tex:333` = 333, `.tex:433` = 439,
`.tex:526` = 532, `.tex:528` = 534, `.tex:546` = 552, `.tex:709` = 715, `.tex:725` = 731,
`.tex:731` = 737.

Every OLD below was measured with `str.count` on the canonical file **and** on
`revised_paper_v18_long_abstract.tex`: **1 in each**, so the coordinator's mirror is a
straight second application. No edit touches line 31.

---

## Edit 1 — form-label the two null recoveries at the §III.B convergence withdrawal (C-04)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
and I now report the projection range and the null's recovery as two separately stated quantities.
NEW:
and I now report the projection range and the null's recovery as two separately stated quantities. Both null recoveries quoted here are read under the production floor form; under the additive form of Section~\ref{sec:robustness-floor} the null recovers 35.6\% at the headline floor, so the projection is being compared against one form's null rather than against a form-invariant object.
RATIONALE: §III.B (line 150) quotes both 88.7\% and 85.7\% bare, and the whole
convergence-withdrawal argument is a comparison against the null's level — the one place where
an unlabelled null is doing the most work. One clause conditions both quotations and supplies
the additive counterpart in the same breath.
LITERALS_INTRODUCED: `35.6\%` — `floor_form_mixture_results.json` `cells["4.991|1|0"].share_pct
= 44.6996` standalone, netted by the committed `shared_layer_scoring_results.json`
`curtailment_netted_b = 69.56220187263008` over `764.7482532227` = 35.6035 shared, i.e. the
same basis as the 85.7\%/88.7\% beside it. Reuses the abstract's committed literal.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none inside this OLD. The two gate-#63 literals on the same line
(`they require the uniform-spread allocation, because the settlement-aware allocation puts the
anticipated share at 75.6\%` and `clears by 13.2 points in-sample and 10.1 points`) sit before
it and are untouched (both re-measured 1 → 1).

---

## Edit 2 — name the mechanical majority as a cap-placement fact in §III.B (C-32)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
The agreement that survives is coarse and is the one I rely on: both objects put the anticipated mechanical component in the large majority of the shortfall.
NEW:
The agreement that survives is coarse and is the one I rely on: both objects put the anticipated mechanical component in the large majority of the shortfall. That is a fact about where the Committee set the ceiling rather than about how households responded to rates, since the majority is large because the caps were set above any prepayment path this book could have delivered; leading with it therefore understates lock-in, and the reading that is about mortgage markets is the expectations-based share reported below.
RATIONALE: C-32's verified note is that the cap-placement point is already made here but the
*inference* is not — that leading with the majority understates lock-in against the
E-benchmark. The pointer lands on the 49\%/80\% ratios stated later in the same paragraph, so
no literal is duplicated.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none.

---

## Edit 3 — state the form-selection rule once, in §V.B, and settle the additive branch's standing (C-22)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
The max-form marginal's floor-dependence is censoring-driven rather than evidence about the elasticity.
NEW:
The max-form marginal's floor-dependence is censoring-driven rather than evidence about the elasticity. Which of the two forms the headline is reported at is settled by rule rather than by fit, and the rule belongs here because every headline figure in this paper inherits it. The calibration anchor does not discriminate: on deep-discount cohorts, where the voluntary hazard is near zero, the two forms nearly coincide (Section~\ref{sec:robustness-floor}). What discriminates is conservatism on the identified object. The measured curve between the forms rises steeply in the share of the floor entering as a competing involuntary cause and plateaus near the additive end, so the hard maximum is that curve's minimum, and the share itself is not identified anywhere in this design, which carries no decomposition of realized turnover into voluntary and involuntary parts. I therefore report the marginal at the minimum, report no interior point, and carry the additive endpoint --- $+11.2$ points at the off-window anchors, nearly floor-invariant --- beside every quotation of the headline. On that rule the additive branch is a measured member of the same curve rather than a demoted one; what the rule declines to do is choose between the forms on aggregate level, which this design does not identify.
RATIONALE: C-22 asks for a *stated rule*, not a disclosure. §V.B is the form's home (it defines
$\underline{h}$, names the max form, and already says the semantics choices "are conventions
consistent with that premise, not consequences of a strictly-involuntary decomposition"), and
§VII.F's two scattered justifications (semantics at the deep-discount anchor; "the conservative
endpoint of a measured curve") are unified into one rule here. The rule is **conservatism on
the mixture curve plus non-identification of the mixture share** — it does *not* appeal to
aggregate fit (which the paper refuses) and it does *not* appeal to the strictly-involuntary
share (which §VII.F concedes points the other way). That concession is therefore left standing
rather than contradicted: I concede the anchor does not discriminate. The additive branch's
standing is settled explicitly — a measured member carried at every headline site, not a second
headline and not a demoted cell.
LITERALS_INTRODUCED: `$+11.2$` (already 9× in the file; `floor_form_offwindow_results.json`
additive rows `marginal_pp` = 11.2193 / 11.2070 / 11.1929 at floors 4.695/4.991/5.334, i.e.
"nearly floor-invariant"). "the hard maximum is that curve's minimum" is
`floor_form_mixture_results.json` `monotonicity["4.991"] = {peak_s: 0.8, rising_to_peak: true,
plateau_within_0.1pp: true}` with `cells["4.991|0|6.5"].marginal_pp = 5.5716` the smallest cell
on the curve (same at floor 4: peak_s 0.7, $+9.198$ at $s=0$).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. **Notation check:** I deliberately do not name the mixture share
$s$ here — §V.B already uses $s(i)$ for the stratum index on the same line, so the symbol would
collide. §VII.F introduces $s$ where there is no collision.

---

## Edit 4 — form-label the in-sample mechanical-null level quoted in §V.B (C-04)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
which shows the mechanical model recovers 97.8\% of the benchmark under the standalone scorer (88.7\% on the shared accounting basis).
NEW:
which shows the mechanical model recovers 97.8\% of the benchmark under the standalone scorer (88.7\% on the shared accounting basis). Both are production-floor-form levels: under the additive form the same null recovers 44.7\% under the standalone scorer at the off-window anchor (Section~\ref{sec:robustness-floor}), so the null's level is as form-dependent as the marginal.
RATIONALE: this sentence is the §V.B statement that "a substantial share of the aggregate level
rides on the floor rather than the elasticity", and it quotes the null's level bare four
sentences after the form fork is introduced. The companion is quoted **standalone**, matching
the 97.8\% it sits beside, and at the anchor where the additive null was actually run.
LITERALS_INTRODUCED: `44.7\%` — `floor_form_offwindow_results.json` additive row at floor 4.991,
`null_share_pct = 44.69959732600039`, standalone. Already present once at line 715 ("against a
44.7\% null"), so this is a second printing of a committed literal, not a new one.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none.
NOTE FOR THE COORDINATOR: I deliberately did **not** quote the additive null's *in-sample*
counterpart. Its shared value is 46.83\% (`floor_form_results.json` additive@4.0
`null.share_pct = 55.92743732152105` minus 9.0964) and its standalone 55.93\% — and both
collide with committed figures for a *different* object (the convention list's `55.907 -> 46.8`
is the additive **central** leg at 4.991). Printing either would create a same-literal /
different-object collision.

---

## Edit 5 — report the null's recovery at 75 and 100 PSA beside the PSA span (C-28)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
(run \texttt{psa\_level\_sweep}), a span with no coverage property --- it is a range over a convention I did not estimate, and its endpoints are not draws from anything.
NEW:
(run \texttt{psa\_level\_sweep}), a span with no coverage property --- it is a range over a convention I did not estimate, and its endpoints are not draws from anything. Aggregate fit is not available as a defense of the 100 PSA convention either: at the headline floor the $\beta_1 = 0$ null recovers 101.9\% of the benchmark under the standalone scorer at 75 PSA against 94.8\% at the production 100, so the ramp the paper runs is the worse-fitting of the two.
RATIONALE: C-28 exactly — the sweep's PSA entry prints only the marginal span, so aggregate fit
is silently available as an implicit defense of the 100 PSA convention. It is not: the null fits
*better* at 75 PSA. Placed inside the §V.E ¶7 assembly, where the span is already the widest
disclosed layer, so the reader meets the fit fact where the convention is being weighed.
LITERALS_INTRODUCED: `101.9\%` — `psa_level_sweep_results.json` `cells["4.991|75|0"].share_pct =
101.9415`, standalone (count 0 → 1). `94.8\%` — `cells["4.991|100|0"].share_pct = 94.7917`,
standalone; already 3× in the file (lines 323, 521, 802), count 3 → 4.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: this OLD is inside the gate-#98 assembly paragraph (line 333, scoped by
`ASSEMBLY_OPENER = "A seventh qualification"`). Re-measured after the edit: the paragraph is
still **one** line, and all twelve `ASSEMBLY_SPANS` are present — in particular
`posture_binding_layer` ("The widest layer that does have a coverage property is the floor
reads' own sampling error, $+2.9$ to $+8.7$ points after wild-cluster correction") begins in the
sentence immediately after my insertion and is byte-identical.

---

## Edit 6 — form-label the null's two levels in §V.F's timing paragraph (C-04)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
and 85.7\% at the off-window floor (Table~\ref{tab:bases}).
NEW:
and 85.7\% at the off-window floor (Table~\ref{tab:bases}), both under the production floor form and 35.6\% at that floor under the additive one (Section~\ref{sec:robustness-floor}).
RATIONALE: C-04's named §V.F site (`.tex:526` = 532). The `\ref{tab:bases}` pointer stays
attached to the max-form figures, because tab:bases carries no additive rows.
LITERALS_INTRODUCED: `35.6\%` (same provenance as Edit 1).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. The gate-#63 literal `a miss of 8.7 points` is elsewhere on the same
line and untouched (1 → 1).

---

## Edit 7 — §VIII's opening sentence: form label + cap-placement naming (C-04, C-32)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
interacting with a prepayment environment mostly mechanical relative to the caps: the $\beta_1 = 0$ null recovers 85.7\% of the benchmark at the headline calibration under any rate response above the baseline turnover it embeds, and
NEW:
interacting with a prepayment environment mostly mechanical relative to the caps: under the production floor form the $\beta_1 = 0$ null recovers 85.7\% of the benchmark at the headline calibration under any rate response above the baseline turnover it embeds (35.6\% under the additive form), which is a statement about where the Committee set the ceiling rather than about how households behaved, and
RATIONALE: this is the conclusion's *first* statement of the mechanical majority, and it carried
neither the form condition (C-04) nor the cap-placement reading (C-32). One clause each; the
"under any rate response above the baseline turnover it embeds" hedge is untouched and now
correctly scoped by the form label it always needed.
LITERALS_INTRODUCED: `(35.6\% under the additive form)` — byte-identical reuse of the
already-landed abstract parenthetical (count 1 → 2).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none.

---

## Edit 8 — form-label the null's two levels where §VIII disciplines the contrast (C-04)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
The composition of that recovery, however, disciplines what the contrast can mean: the $\beta_1 = 0$ null recovers 85.7\% on the same basis at the headline floor and 88.7\% in-sample,
NEW:
The composition of that recovery, however, disciplines what the contrast can mean: under the production floor form the $\beta_1 = 0$ null recovers 85.7\% on the same basis at the headline floor and 88.7\% in-sample (35.6\% at the headline floor under the additive form),
RATIONALE: C-04's §VIII site (`.tex:725` = 731). The clause "on the same basis" already labels
the accounting basis; the form label is the missing half.
LITERALS_INTRODUCED: `35.6\%` (same provenance as Edit 1).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none inside this OLD.

---

## Edit 9 — name the "mostly mechanical" concession as cap placement (C-32)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
because the caps sat far above what any plausible prepayment environment would have delivered---though
NEW:
because the caps sat far above what any plausible prepayment environment would have delivered, which is a fact about where the ceiling was set and not about how households behaved---though
RATIONALE: C-32's second §VIII site. The cap-placement *fact* was already here; the *inference*
was not, and the E-benchmark counterweight follows immediately in the existing "---though"
clause, so the reordering C-32 asks for is achieved by naming rather than by moving text.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: the gate-#98/#63 span `projection rather than the non-binding cap, the
lock-in channel accounts for roughly half the genuine surprise under the central allocation`
(`RELOCATED_TO_BODY["surprise_denominator_body"]`) begins immediately after my `---though`
and is byte-identical; re-measured 1 → 1. My insertion ends before the em-dash so no second
dash is created.

---

## Edit 10 — put the form condition in the trilemma paragraph's opening clause (C-23)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
and this paper's evidence is that they do not form the strict trilemma a three-way ``trade-off'' would imply:
NEW:
and this paper's evidence---under its production floor form, and not under the additive form, where the margin at issue roughly doubles---is that they do not form the strict trilemma a three-way ``trade-off'' would imply:
RATIONALE: C-23's live defect is *ordering* — the 4,470-character paragraph opened with the flat
claim ~2,900 characters before the qualification arrived. The condition now sits in the opening
clause, in the abstract's own committed wording ("the additive form roughly doubles the
margin"), so the paragraph can no longer be read flat.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none. `dissolution_scope` ("trade off sharply under face accounting") and
`trilemma_conditional` ("while its effect on (3) is incidence-conditional") are later on the
line and untouched (each 1 → 1).

---

## Edit 11 — move the additive pointer to the concession itself (C-23)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
reduces to ``the marginal is small''---and under the production floor form the marginal is bounded small by construction. Because \eqref{eq:pathB} combines the turnover floor with the voluntary hazard by a hard maximum, switching the elasticity off can raise the hazard by no more than the excess of the $\beta_1 = 0$ hazard over the floor, and by nothing at all where the floor binds on the $\beta_1 = 0$ leg itself, 14.3\% of loan-months at the in-sample calibration point (Section~\ref{sec:identification}). The dissolution is therefore a statement about a calibrated ceiling, not an independent finding, and it is form-conditional: under the disclosed additive form, which never censors the elasticity, the same counterfactual roughly doubles to about $+11$ points (Section~\ref{sec:robustness-floor}).
NEW:
reduces to ``the marginal is small''---and under the production floor form the marginal is bounded small by construction; under the disclosed additive form, which never censors the elasticity, the same counterfactual is about $+11$ points and nearly floor-invariant (Section~\ref{sec:robustness-floor}). Because \eqref{eq:pathB} combines the turnover floor with the voluntary hazard by a hard maximum, switching the elasticity off can raise the hazard by no more than the excess of the $\beta_1 = 0$ hazard over the floor, and by nothing at all where the floor binds on the $\beta_1 = 0$ leg itself, 14.3\% of loan-months at the in-sample calibration point (Section~\ref{sec:identification}). The dissolution is therefore a statement about a calibrated ceiling, not an independent finding, and it is form-conditional.
RATIONALE: C-23's second half — the additive counterweight must sit *at the concession*. Nothing
is deleted: the additive clause is moved from the fourth sentence to the second, "and it is
form-conditional" stays as the sentence that names the dimension, and "roughly doubles" is not
lost (Edit 10 puts it in the paragraph's opening clause). "nearly floor-invariant" is added
because a floor-invariant counterweight is what makes the concession bite. No paragraph split:
the split at "What this dissolution rests on is thinner than the framing suggests" that C-23
offers is C-87's business and would move a float on a 130pp build.
LITERALS_INTRODUCED: none. `$+11$` count is unchanged at 3 (one occurrence moved, none added).
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: `bounded small by construction` (C-23's own verbatim quote) preserved
byte-identically, 1 → 1. `and it is form-conditional` preserved, 1 → 1; whole-file
`form-conditional` count unchanged at 12 (gate #69 wants ≥3). `14.3\%` unchanged at 2.

---

## Edit 12 — carry the condition into the policy sentence that leans on smallness (C-23)
FILE: paper/v18/revised_paper_v18.tex
OLD_COUNT_ASSERT: 1
OLD:
The binding constraint against adopting such a rule is therefore not a mobility--cash-flow trade-off but the TBA liquidity premium described above.
NEW:
The binding constraint against adopting such a rule is therefore, on either form, not a mobility--cash-flow trade-off but the TBA liquidity premium described above.
RATIONALE: C-23's last requirement — the §VIII policy sentence that leans on smallness must
carry the condition explicitly. "on either form" is the claim the paragraph already commits to
one sentence earlier ("What survives across forms is that the trade-off is modest, not that it
is absent"), so this makes the inheritance explicit without asserting anything new.
LITERALS_INTRODUCED: none.
LITERALS_REMOVED: none.
PINNED_SPANS_CROSSED: none.

---

## NOT DRAFTED

### NOT DRAFTED — C-04, the three sites outside my region
`tab:headline`'s mechanical-null row and its uncertainty cell (`.tex:78` = **78**, plus the
same catalogue at `tab:uncertainty` line **438**, "85.7\% shared at the off-window floor,
83.9--86.9\% across its range"), §VI.B (`.tex:546` = **552**) and §VII.F (`.tex:709` = **715**)
all still quote the majority without a form label. They are **not premise failures** — they are
sibling drafters' regions and my OLD spans would collide. The label wording that lands here and
should be reused verbatim: `under the production floor form` + `(35.6\% under the additive
form)`. `tab:bases` rows at lines 520--521 also print the max-form pair with no form column;
that is an exhibits (wave-4) call, not a wording one.

### NOT DRAFTED — C-22, resolution option (ii)
The inventory offers promoting the form-robust `roughly +9 to +11 points at the production
floor` to headline status. I did not draft it: it is a **posture change**, it abandons the
off-window headline the paper spent rounds establishing (the form-robust band exists only at the
*production* floor — at the off-window anchors the two forms return $+5.6$ and $+11.2$ and no
form-robust point exists), and it would rewrite the abstract, which gate #101 ties to the
response letter's word count. This is Eugene's call, not a drafting one. Edit 3 takes the third
admissible route in a form that does not use fit as the selection rule.

### NOT DRAFTED — the PSA sweep's expectation record
`psa_level_sweep_results.json` `expectation_check` is **3-for-3 inside band at floor 4.0 and
0-for-3 off window** (4.991: realized 0.856 vs band [1.5, 2.5]; 11.419 vs [8.5, 10.0]; 15.626
vs [11.0, 14.0]). C-28's note warns only against *describing the off-window cells as having met
expectation*, and the current sentence makes no such claim, so no repair is required. Available
as a one-clause addition to Edit 5 if the coordinator wants the pre-committed miss on the record:
`and all three off-window cells landed outside their pre-committed bands`. Verified, but out of
C-28's scope, so not drafted.

---

## CENSUS

Measured with `str.count` on the canonical file and on the in-memory result of applying all
twelve edits in order (`scratchpad/sim.py`, output written to `scratchpad/after.tex`).

| literal / pinned span | before | after |
|---|---|---|
| `85.7\%` | 21 | 21 |
| `88.7\%` | 20 | 20 |
| `35.6\%` | 1 | 5 |
| `(35.6\% under the additive form)` | 1 | 2 |
| `44.7\%` | 1 | 2 |
| `97.8\%` | 6 | 6 |
| `94.8\%` | 3 | 4 |
| `101.9\%` | 0 | 1 |
| `$+11.2$` | 9 | 10 |
| `$+11$` | 3 | 3 |
| `$+11.5$` | 4 | 4 |
| `production floor form` | 4 | 9 |
| `under the production floor form` | 2 | 6 |
| `additive form` | 21 | 26 |
| `form-conditional` | 12 | 12 |
| `$+3.5$ to $+13.1$` | 7 | 7 |
| `$+3.9$ to $+13.1$` | 0 | 0 |
| `$+2.9$ to $+8.7$` | 8 | 8 |
| `$+3.0$ to $+8.0$` | 5 | 5 |
| `mostly mechanical` | 5 | 5 |
| `bounded small by construction` | 1 | 1 |
| `and it is form-conditional` | 1 | 1 |
| `14.3\%` | 2 | 2 |
| `(run \texttt{psa\_level\_sweep})` | 2 | 2 |
| `projection rather than the non-binding cap, the lock-in channel accounts for roughly half the genuine surprise under the central allocation` | 1 | 1 |
| `they require the uniform-spread allocation, because the settlement-aware allocation puts the anticipated share at 75.6\%` | 1 | 1 |
| `clears by 13.2 points in-sample and 10.1 points` | 1 | 1 |
| `while its effect on (3) is incidence-conditional` | 1 | 1 |
| `trade off sharply under face accounting` | 1 | 1 |
| `the par windfall it would otherwise have extracted from moving households` | 1 | 1 |
| `a household-to-bondholder transfer, not an added resource cost` | 1 | 1 |
| `the balance-adjustment reading is the benchmark-consistent one` | 1 | 1 |
| `The gap's sign is therefore incidence-conditional` | 1 | 1 |
| `a miss of 8.7 points` | 1 | 1 |
| `the miss is 8.7 points on the headline calibration and 2.1 points on the in-sample one` | 1 | 1 |
| `recovers 91.3\% of the benchmark on the shared basis at the off-window floor` | 1 | 1 |
| `The widest layer that does have a coverage property is the floor reads' own sampling error, $+2.9$ to $+8.7$ points after wild-cluster correction` | 1 | 1 |
| `no interior member is privileged, and the range rather than any point is what the design delivers` | 1 | 1 |
| `every correction listed above falls in its lower half` | 1 | 1 |
| `the additive form returns $+11.2$ points at the same off-window anchors` | 1 | 1 |
| `truncated at the floor rather than erased` | 1 | 1 |
| `pinned to the floor in 68.8\% of evaluated loan-months, against 36.3\%` | 1 | 1 |
| `unweighted loan-month counts rather than balance-weighted shares` | 1 | 1 |
| `point to a larger lock-in channel, not a smaller one` | 1 | 1 |
| `Table~\ref{tab:assembly} tabulates this assembly` | 1 | 1 |
| `$+3.53$` | 2 | 2 |
| `$+10.83$` | 1 | 1 |
| `$+270.4$` | 1 | 1 |
| `$-105.3$` | 1 | 1 |
| `35.8\%` | 3 | 3 |
| `12.6\%` | 5 | 5 |
| `$-1.47$` | 7 | 7 |
| `-\$89.4$ to $-\$117.7$ billion` | 4 | 4 |
| `60.2\%` | 9 | 9 |
| `76.3\%` | 7 | 7 |
| `98.1\%` | 8 | 8 |
| `$[+2.80, +8.99]$` | 2 | 2 |
| `\texttt{layer\_convolution}` | 3 | 3 |
| `floor\_form\_offwindow` | 2 | 2 |
| `wild-cluster interval runs from 4.177\% to 5.800\%` | 1 | 1 |
| `in the units a cap designer would have to plug in` | 1 | 1 |
| `A green gate suite is therefore not self-certifying` | 1 | 1 |
| `the instability is the max form's censoring mechanics` | 1 | 1 |

Structural invariants re-measured on the result:
- gate #98 scoping: exactly **1** line starts with `A seventh qualification`; all 12
  `ASSEMBLY_SPANS` present.
- line count **1,435 → 1,435** (no paragraph split, no new line).
- abstract word count **294 → 294** (no edit touches line 31).

---

## UNVERIFIED

1. **Suite green.** I did not run `tools/liveness_gates.py` or pytest (prohibited). Every
   gate/test span I could locate by reading `tools/liveness_gates.py` (4,997 lines) and
   `tests/*.py` was re-measured above, but I cannot rule out a gate whose span I did not find.
   Confirmed by: the coordinator running the suite after applying.
2. **Float placement.** Edit 3 adds ~1,150 characters to the §V.B paragraph at line 227, which
   sits immediately before `tab:params` (`[H]`) and the §V.B float stack. On a 130pp build that
   can move a float. Confirmed by: a `tectonic` build and a page-count / 0-undefined check.
3. **`101.9\%` collision.** New literal, count 0 → 1. It is not in `SHARE_LITERALS` (which
   binds figure scripts, not the tex) and I found no gate on it, but I could not verify that no
   figure caption or markdown edition prints 101.9 for a different object. Confirmed by: a
   repo-wide fixed-string grep for `101.9` outside the .tex.
4. **`44.7\%` basis reading.** Edit 4 quotes it as the additive **null** at the off-window
   anchor on the standalone scorer, from `floor_form_offwindow_results.json` additive@4.991
   `null_share_pct = 44.69959732600039`. Line 715 already prints "against a 44.7\% null" in that
   sense, so the reading is the manuscript's own — but the artifact does not carry an explicit
   `basis` field, so the standalone attribution rests on the parity chain
   (`P_leg_4.991_s1_pq6.5 = 427.545` / `764.748` = 55.907, matching the tex's "55.9\%" standalone).

---

## WORD_COUNT_IMPACT

**No edit touches line 31.** The abstract is unchanged at **294 words** (measured on the result),
so gate #101's letter-vs-abstract word-count tie is untouched. Edit 10's opening-clause condition
is the abstract's own committed wording, so the abstract already inherits the §V.B rule of Edit 3
("under its production floor form"; "the additive form roughly doubles the margin") and needs no
change.

Net prose added across the twelve edits, measured as `len(after) - len(before)` on the whole
file: **+2,996 characters / +469 words**, all in the body. Per edit (chars / words):
1 +290/+42, 2 +364/+58, 3 +1,201/+191, 4 +242/+32, 5 +293/+53, 6 +123/+16, 7 +170/+27,
8 +87/+14, 9 +86/+16, 10 +112/+16, 11 +11/+1, 12 +17/+3. By section: §III.B +654,
§V.B +1,443, §V.E +293, §V.F +123, §VIII +483 characters. Edit 3 is 40\% of the total and is
the only one that adds a new argument rather than a label; if the coordinator needs the page
count held, it is the one to compress, and the two sentences it cannot lose are "The calibration
anchor does not discriminate" and "the share itself is not identified anywhere in this design".
