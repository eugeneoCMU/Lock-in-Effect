# PLAN — v20 Phase-3b compression budget (per-section, for the dedicated sessions)

**Status:** planning document, 2026-08-04. This is the recipe the compression
sessions execute; nothing here is a run. Companion to `improvement_plan_v19.md`
(Phase 3) and `RESPONSE_v20_panel_draft.md` (PHASE-3b section).

**The arithmetic.** Main text at HEAD is ~56,000 words (~90pp rendered with
exhibits). The EIC's target (≤45–50pp) implies ~28–30k words of main-text prose:
a ~45% reduction. That is an editorial rewrite, not an editing pass — done per
section against the pinned-span inventory, never by regex (see the Phase-2
mid-sentence incident, TECHNICAL §46).

## Per-section budget (words at HEAD → target, with the cut's character)

| Section | HEAD | Target | How |
|---|---|---|---|
| I Introduction | 4,671 | 2,600 | One statement of each result (the results box carries the numbers); cut the second and third restatements of sign-forcing and identification status; contributions list to 4 items |
| II Literature | 2,991 | 2,000 | Keep the four-front coverage; compress per-paper summaries to clause length; the Na et al. reconciliation keeps its full paragraph |
| III Method | 2,709 | 2,000 | III.B keeps benchmark + standing paragraph + cap note; allocation-sweep detail → appendix |
| IV ABM | 1,680 | 1,100 | Lead paragraph untouchable (8 pins, gate #100); trim abm-results run inventory to the seed-distribution sentence + falsification; Interpretation folds into the lead |
| V.A–B hazard | 9,139 | 4,500 | Largest single cut: keep motivation ¶, Path B construction, floor semantics, elasticity import + attenuation; move parameterization detail, bootstrap-scheme history, and per-run tags to appendix |
| V.C–D | 1,787 | 1,000 | Fannie reproduction to one paragraph (the gate's deflation sentence stays); Path A to one paragraph + exclusion statement |
| V.E identification | 9,564 | 5,000 | The paper's core — cut by consolidation, not deletion: the seven qualifications become one enumerated block; Tables 5/9 relocate HERE (from wherever declared) and absorb prose that restates their rows; the v20 companions passage stays |
| V.F interpretation | 2,703 | 1,200 | Keep the renormalization/what-recovery-certifies discussion; drop restatements of V.E content |
| VI Discussion | 6,792 | 4,200 | VI.A keeps welfare + carry ¶; VI.B keeps ex-ante arithmetic + non-bindingness + designer take-away; VI.D Danish keeps rule-only vs anchor + incidence bracket, moves fine-grid mechanics to appendix |
| VII Robustness | 8,256 | 4,000 | Each check states claim + result + pointer; VII.C keeps the cross-design result + post-hoc label; VII.F keeps the derivation role (it makes the headline) but hands its sweep tables to the appendix |
| VIII Conclusion+Lim | 5,703 | 3,400 | Conclusion ~40% cut (it restates V.E/VI.D at length); Limitations keeps every named limitation at one sentence each |
| **Total** | **55,995** | **~31,000** | ~46% reduction → ~50–55pp rendered |

## Structural moves that ride along (same sessions)

1. **Audit-appendix migration** (EIC-W1, R2-W5): `app:ledger` (superseded
   figures) + `app:verdicts` (adjudications) → a standalone
   `REPLICATION_APPENDICES` document in the package. 21 in-text `\ref`s reworded
   to "the replication package's ledger"; gate #104 and the superseded-unless-
   labeled gate rescoped to read the migrated file. Do this DURING the prose
   pass — refs get touched anyway.
2. **Tables 5 (tab:assembly) and 9 (tab:ladder) relocate** adjacent to §V.E's
   discussion; the prose that duplicates their rows is the cut.
3. **Run tags out of prose**: every `run \texttt{...}` moves to table notes or
   the appendix run index; keep them where a gate's span includes the tag
   (grep the gate file first, per tag).
4. **"How to read this paper" shortcut deleted** once the structure carries it.
5. **Editions + split recut LAST**, after pagination settles.

## Invariants (the non-negotiables the sessions inherit)

- Every pinned span in `tools/liveness_gates.py` either survives verbatim or its
  pin is re-synced in the same commit with a documented V20 comment. Run the
  suite after every section, not at the end.
- Hedge scope is load-bearing: a cut may delete a RESTATEMENT of a hedge, never
  the last instance of one. When in doubt, the hedge stays.
- Both variants get identical body edits; the long-abstract variant keeps its
  archived abstract.
- No regex sentence surgery. Anchored literal replacements only, with expected
  counts asserted.
- Rebuild + 0-undefined + full suite + gates before each commit.

## Session sizing

Three sessions of ~2 sections each (V.A–B and V.E are a session each), plus one
closing session for the structural moves, editions, split, and the response
letter's final fill. Each session ends green and committed.
