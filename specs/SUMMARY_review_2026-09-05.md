# What I did, and what is still open

Session of 2026-09-05/06, against `main` at `1fc54d4`. Six commits landed, taking
`main` to **21 unpushed**. Nothing was pushed. No model was run and no artifact
regenerated: every number written into the paper was read out of a committed
artifact or recomputed from one.

Companion documents: `specs/RECORD_review_2026-09-05.md` is the formal record in
the repo's usual style; `specs/PLAN_review_2026-09-05.md` is the working plan
(gitignored, local only). This file is the plain account.

---

## 1. How the review was done

A read-only sweep of the whole tree by 22 agents — the manuscript section by
section, the letter, the replication appendices, the docs, the gates, the tests,
the figures, the bibliography, repo hygiene, the records, the alternative edition,
the roadmap — with every finding then put to two adversarial verifiers on
different lenses (does the text say what the finding claims; is it actually a
defect or disclosed history; is the proposed fix safe against the gates).

206 raw findings, 186 after dedup, 106 survived both verifiers, 17 contested, 1
refuted outright, 62 left unverified because verifier agents stalled.

**Treat those numbers as a soft signal, not a verdict.** The first fan-out died on
a session usage limit; the resumed run finished but 16 verifiers stalled. I
re-derived every finding myself before acting on it, and six did not survive that
— they are listed in §6 so nobody re-raises them. The lesson worth keeping is that
agent agreement is evidence, not proof.

---

## 2. The most important thing found: a gate that could not see its own defect

`tools/render_gate.py` exists because a previous round shipped ~919 text items
rendering off the page while every source gate passed. It tests each glyph's
**origin** against the page box.

An origin test cannot see a width. A table row that begins inside the text block
and runs off the right-hand edge has every origin legal. Five tables were clipped
by the paper's edge in a build the gate called clean:

| Table | Page | What was lost |
|---|---|---|
| `tab:ladder` | 137 | the Status column **on the binding-layer row** |
| `tab:params` | 114 | the provenance column |
| `tab:assembly` | 51 | overflowed the page, last row printed over the footer |
| `tab:seasonalfloor` | 145 | caption, notes, last column |
| `tab:crossdesign` | 76 | last column at the sheet edge |

This had never been caught because the gate had never run against a build. Both
August records say the PDF could not be rebuilt, "no tectonic on PATH" — but a
working **tectonic 0.15.0 sits at `~/Downloads/texbuild/tectonic`**. It is simply
off `PATH`.

**Fixed.** `tab:assembly` became a `longtable` (breaking across pages as
`tab:headline` already did); the other four took explicit column widths. No
table's structure was pinned by any gate or test, checked by grep first.

**The hole is closed.** `render_gate.py` gained `overrun()`, which reads span
bounding boxes and fails when text extends past the sheet. Run against the
pre-fix build it flags exactly pages 76, 114, 137 and 145 while the origin check
reports PASS on the same file. Three tests pin it, one asserting precisely that
the origin check misses the page the extent check catches. It reports `SKIP`
rather than passing when PyMuPDF is absent, because a check that goes quiet when
its dependency is missing is how the first one failed.

---

## 3. What was wrong in the paper

74 counted replacements, each applied to both editions, each dry-run first and
aborted on any count mismatch, after a pin scan over the literal and its
replacement.

**The claim that did not need a run.** Line 336 read "all but one above the
$+8.7$ upper edge of the binding interval". +8.7 is the demoted Webb rung's edge;
the binding edge has been +9.1 since N1. The August record deferred this as
needing the `h0_reanchor` replicate set — but that set is committed. It gives
**106 of 107 above +8.7 and 93 of 107 above +9.1**. The sentence now names both
edges and both counts, and a new gate recomputes them.

**A placement claim that had become false.** "The headline sits just below its
midpoint" was verified at N1's interval (midpoint 5.70) and never re-verified when
Batch B moved the lower endpoint. The midpoint is now 5.49 and the +5.57 headline
sits **above** it.

**A table note still describing the demoted construction** as the binding layer,
and giving the unrestricted bootstrap as its construction. The binding layer is
the restricted inversion; the unrestricted description belongs to the rungs
reported beside it.

**A rule that read as self-contradicting.** The selection rule picks "the
narrowest construction clearing the bar", yet CR2 at Bell–McCaffrey prints
narrower than the rung it selects. The rule ranks on *mean simulated width in
floor units* (0.001397 against 0.002318), where the ordering is the other way.
That metric was nowhere stated; it is now stated once at the rule and once in the
ladder note.

**An appendix contradicting itself:** Path A's Theil figures in prose (26.5/63.0)
against its own table (30.6/58.8). The table is on the corrected basis.

Also: four legs described as "run in window only" that have committed off-window
re-runs cited in the same section; the off-window leg labelled 2017–2019 where the
headline read is the 2018 leg; a retracted interval printed unlabelled beside live
ones; 6.5% called the band's "midpoint" when the midpoint is 6.6%; "production
headline" attached to the frozen single draw at three sites; a caption crediting
all seven stage levels to run manifests when four are pre-manifest; "pre-registered"
used in the sense the paper explicitly reserves; four appendix cross-references
pointing at their own appendix; and a hedge deferring to a freeze that had already
happened.

---

## 4. Everything else that was fixed

**Letter and appendices.** `\externaldocument` still pointed at the manuscript
deleted in the rename, so every cross-reference resolved against nothing. The run
index had no row for either August run and described the superseded convolution as
current. The letter's supersession paragraph said the figures it retires sit
"above" when two of three sit below it.

*A mutation test caught me weakening a gate here.* A tag I added duplicated a
literal gate #101 pins, which defeated its deletion check. I re-worded the tag
rather than the test.

**Figures.** fig4 still annotated the superseded ~1bp Berger anchor while the text
gives ~20bp — a manuscript exhibit contradicting its own paper. fig1, fig2, fig3
and fig4 carried hard-coded section pointers that no longer resolve; those are
gone rather than renumbered, since hard-coded pointers rot by construction. fig6's
axis named a quantity the caption calls δ. fig3's label called the frozen draw the
headline. fig7 attributed Path A to the 75k sample when it is estimated on the
full universe. Regenerated from committed JSON only.

**A clone could not build the paper at all.** Thirteen bare `\includegraphics`
names, no `\graphicspath`, and `.gitignore` ships no PNG under `paper/`. All
thirteen are tracked elsewhere, so a `\graphicspath` now names them. Verified by
hiding every untracked PNG and building: 147 pages, zero errors.

**The split PDFs** were, in the gate's own words, "cut BY HAND after every rebuild
and nothing verified it". `tools/split_pdf.py` finds the boundary from the text —
the first page opening the Online Appendix banner — so the cut survives reflow as
a typed page number does not.

**A check that could never pass.** The render gate asserted the two editions have
equal page counts; the archived long abstract runs 629 words against 263 and costs
a page. It had never run to discover this. Now one page of slack, with body drift
still caught upstream.

**Documentation.** `TECHNICAL.md` — billed as the full technical narrative —
stopped at 2026-08-18 and told none of what followed, and carried a second heading
numbered 46 colliding with the real one. The roadmap's newest-first history still
ended at the superseded interval. README claimed 33 gates where there are 129.
Five superseded planning documents got dated banners rather than edits.

**New gates**, each mutation-proved red before being trusted, with hash-verified
restore: #127 rebuilds each grid-extension table row whole from its artifact, so a
floor paired with the wrong marginal cannot pass; #128 holds "pre-registered" to
the one sentence reserving it; #129 recomputes the replicate counts rather than
reading the printed ones. `ZERO_COUNT` gained the retired intervals, which nothing
had guarded — the August batch re-printed every site by hand and verified by grep,
and the grep missed one site, caught a round later.

**Twice I wrote a number that went stale within a day.** The README and CI test
counts I rewrote were wrong by the evening, because I had added three tests. That
is exactly what those lines exist to prevent, so they now carry no count at all
and point at the CI run. Adding the `\graphicspath` moved the abstract from line
31 to 38, and CI's editions check hard-coded 31 — it would have compared the wrong
line while reporting the editions in sync. It now finds the line itself.

---

## 5. Where it stands

| Check | Result |
|---|---|
| `pytest tests/` | **1173 passed, 0 skipped** |
| `tools/liveness_gates.py` | **ALL GATES PASS** |
| `tools/render_gate.py` | **ALL CHECKS PASS**, including the new extent check |
| `tools/tex_validate.py` | CLEAN on both editions and the letter |
| Editions | identical apart from the abstract; 263 words |
| Build | 147pp canonical, 148pp variant, split 99 + 48 |
| Clone build | 147pp from tracked files alone |

Rebuild with:

```bash
~/Downloads/texbuild/tectonic -o paper/final/build_split paper/final/paper_final_v1.tex
```

then `python3 tools/split_pdf.py` and `python3 tools/render_gate.py`.

---

## 6. Refuted during verification — do not re-raise

- `tab:bootstrap`'s mean/median cells "have no committed source" — `hazard/data/hazard_bootstrap_draws.csv` is tracked and is the source.
- The −0.438 vs −0.378 Path A correlation "conflict" — the table prints the peak-lag r, the text the lag-0 r; the artifact carries both and a test pins the pair.
- "any of 150 starts" at the cold-starts passage — 50 starts × 3 legs; correct as written.
- "The replication package is the public repository" — true. `gh repo view` reports PUBLIC, which also closes the handoff's private-visibility item.
- The timing correlations "appear in no committed artifact" — `rate_timing_scan_results.json` carries all five.
- "convexity-neutral … below" — three sites exist, one of them below; no edit needed.

---

## 7. What is still open

### Needs your decision, not mine

1. **Push.** 21 commits sit unpushed on a public repository; `origin/main` still prints the censored interval. Pushing publishes the working manuscript.
2. **The long-abstract edition.** Its abstract still names the Webb interval as the binding layer while its body prints the restricted inversion at thirteen sites. Gate #99 is canonical-scoped by design, so nothing catches this. Re-sync the one paragraph, or stop shipping the edition.
3. **`paper/alt_lead_version/`.** A tracked second manuscript frozen before the August work: the superseded interval at sixteen sites, the old convolution pair, the old ladder, the pre-standardization Path A wording, and 79 cross-references reading "Section" where the edition moved the target into an appendix. It has a dated staleness banner now. Re-sync, archive, or delete.
4. **The assembly rule's "basis" term.** The rule lists "basis" as a change that re-scores the marginal, while the paper states four times that every marginal is basis-invariant. I added a clarifying clause to the terminology table; the rule's own wording, and the same phrase in the abstract, are gate-pinned and yours.
5. **The panel's editorial items**, untouched: abstract length (263 against a 200 target), main-text length (99 pages before appendices), framing order, and the page-long paragraphs at `:144`, `:336` (~2,500 words) and `:594`.

### Real, unfixed, and cheap

6. **`paper/references.bib` is a stale 37-entry orphan** tracked beside the live 86-entry `paper/final/references.bib`. A recipient can pick the wrong one. Delete it or make it a pointer — I left it because deleting a tracked file is your call.
7. **The gates still cannot run on a clean clone.** They abort partway on the un-shipped Freddie parquet, so the replication package cannot reproduce its own gate claim. Making those specific gates skip-with-notice would let the rest run in CI, which today runs pytest only.
8. **Two artifact-backed literals remain unpinned**: the 30.8× in-window understatement and the interval `[+8.27, +10.19]` (`bootstrap_pathb_cluster_results_floor4.json`), and the five timing correlations (`rate_timing_scan_results.json`). Both artifacts are committed and read by no gate.
9. **Three headings and one table note still overhang the right margin** by 9–21pt on pages 20, 55 and 133. They stay on the sheet, so the new extent check passes them; they are pre-existing and cosmetic.

### Known, disclosed, and yours to weigh

10. **The synthetic-fixture fallback still fails open.** With no Freddie data, ingest builds fabricated data under the real filename and continues, and the manifests do not record it. Long-standing and disclosed; making it fail closed is a design change.
11. **The seed-noise layer of `tab:uncertainty` has no committed artifact**, script, or record — the one claim in the paper resting on an unfrozen diagnostic. Either a ten-seed paired rerun (cheap; the expected width is near zero) or relabel the four sites.
12. **The cap-grid band was run at the demoted rung's endpoints.** Now labelled as such; the binding rung's wider span was never run.
13. **Remaining citation questions** I did not act on without you: whether the Danish tax parameter at `:588` is presented as law when it is a model parameter, and whether the Ginnie "second bound" at `:50` assumes something `:239` denies. Three suggested references are still absent.

### Deliberately not done

14. Roughly a dozen findings were nits I judged not worth the edit risk — a duplicated sentence in the Conclusion, a restated figure in an appendix, a rounding reconciliation clause. They are listed in the plan's contested and unverified sections with my reasoning.
15. **62 findings carry no agent verdict** because verifiers stalled. I re-derived and acted on the ones that mattered; the remainder are listed in the plan under §G, and should be re-read at the site before anyone acts on them.
