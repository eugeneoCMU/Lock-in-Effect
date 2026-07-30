# SPEC — R32 / C-79: the Danish leg with an interest-only share

**Status: PRE-COMMITTED. Committed BEFORE the runner, and both before the run.**
Run tag: `danish_interest_only_share`. Runner: `tools/danish_interest_only_share_run.py`
(not yet written; this spec lands first and stands on its own). New artifact:
`hazard/data/danish_interest_only_share_results.json`.

---

## 1. The condition

C-79 (DA:A5 second limb, MAJOR, RUN). The concession is verbatim in the manuscript — live at
**`.tex:627`** (the inventory's `.tex:590` is stale):

> "…it does not import […] the Danish product mix — in particular the large interest-only share,
> which would cut scheduled amortization, the null's largest component, and so move the shortfall
> in the opposite direction from the payoff rule. Each omission is a held-fixed feature of the U.S.
> leg, not a measured invariance."

DA's point: if the Danish claim is **institutional**, the transplant must change something the
marginal does not already encode. The interest-only share is the obvious candidate and is not run.

## 2. SOURCEABILITY — determined FIRST, as this condition requires

**(a) Nothing in this repo.** A repo-wide search for `interest-only`, `interest only`, `io_share`
and `afdragsfri` across `*.py`, `*.json`, `*.md`, `*.bib`, `*.tex` returns **no Danish IO-share
value anywhere**. The single `io_indicator` hit is `hazard/schema_fannie.py:87` — a **U.S.**
Fannie/Freddie loan-schema field, absent from `cohort_month_panel.parquet`'s fourteen columns and
irrelevant to a Danish leg regardless. The inventory's judgement ("no committed source in this
repo") is **confirmed**.

**(b) An external source exists and WAS VERIFIED against the source this session** — not written
from memory, and not taken from a search-engine summary. Fetched and read directly:

> **Danmarks Nationalbank**, *"Expiring interest-only mortgages have implications for household
> expenditure"*, **4 February 2020**.
> Verbatim: **"Interest-only mortgages are very popular in Denmark, currently making up 45 per cent
> of outstanding mortgage volumes."**
> `https://www.nationalbanken.dk/en/news-and-knowledge/publications-and-speeches/archive-publications/2020/expiring-interest-only-mortgages-have-implications-for-household-expenditure`

So C-79 is **NOT INFEASIBLE**. It has a defensible, citable, primary-source input. Three limits on
that input are stated now, before it is used, and must travel with it everywhere:

1. **It is pre-window.** February 2020 sits before the June 2022 – November 2025 evaluation
   window. It is an approximation for the window, not a window measurement.
2. **Denmark's "interest-only" is *deferred amortisation* (`afdragsfrihed`), not permanent IO** —
   conventionally capped at ten years. The 45% is the share of outstanding volume **currently in**
   an interest-only period, which is the right object for a 42-month window but is **not** a
   permanent product feature and must not be described as one.
3. **The population is "outstanding mortgage volumes"**, not specifically the owner-occupied
   30-year callable segment the transplant models. That is a population seam, and it is named
   rather than papered over.

**Because of (1)–(3), the primary deliverable is a break-even, not a point** (§4). A single
imported share is reported *against* that break-even, never as the answer on its own.

## 3. What is already known — DECLARED, NOT PREDICTED

Computed at scoping from committed values, *before this spec existed*:

| object | source | value |
|---|---|---|
| par gap | `danish_us_intercept_results.json:point` | `institutional_gap_shared_b = 61.18833737010482` |
| scheduled component | `microsim_results_us_intercept.parquet`, $\sum$ `weighted_sched_b` | **198.66568741255054** |
| **first-order break-even IO share** | derived | $\sigma^{*} = 61.18833737010482 / 198.66568741255054 = \mathbf{0.307996504918}$ |
| gap at the verified 45% | derived | $61.188 - 0.45 \times 198.666 = \mathbf{-\$28.21\text{bn}}$ |

The chain is $\text{gap}(\sigma) = 61.18833737010482 - \sigma \times 198.66568741255054$ — the same
shape as the buyback chain of C-75, and for the same structural reason the committed bracket gives:
trapped liquidity is a **net monthly sum against the redemption targets**, so the target cancels
from differences.

**The direction is already the manuscript's own** (`.tex:627` says the IO share moves the shortfall
"in the opposite direction from the payoff rule"), so **this run gets no credit for the sign.**
What is new is the **magnitude and the crossing**. Nothing in scoping computed the second-order
balance feedback of §4.2, which is the genuinely open limb.

## 4. Construction

### 4.1 First order (primary)

A share $\sigma$ of the **Danish** leg is in an interest-only period, so its scheduled amortization
is zero. Danish scheduled roll-off falls by $\sigma \times \sum_t \text{sched}_t$; Danish roll-off
falls by the same; Danish trapped rises by the same; and

$$\text{gap}(\sigma) \;=\; \text{gap\_par} \;-\; \sigma \sum_t \text{sched}_t.$$

**The IO share applies to the DANISH leg only, and this is a correction to the inventory's own
wording.** The inventory's fix says "applied to scheduled amortization on both legs". Applying it
to both would **exactly neutralize it** — the identical defect C-74 identifies in the Ginnie
overlay, where scoring a share the same way in both legs makes its marginal contribution zero. The
large IO share is a feature of the **Danish** product mix; the U.S. leg's own IO share stays at its
committed effective zero (the microsim amortizes level-payment throughout, and `io_indicator` is
not in the panel), and that stays disclosed as a held-fixed feature.

**Basis note, inherited not repaired.** $\sum$ `weighted_sched_b` is the **U.S. leg's** scheduled
path — the manuscript's own proxy for the scheduled component, the same convention
`buyback_credit_bracket.py` uses to form $E$. This run reproduces that convention so $\sigma$ is
the only thing that changes, and the artifact must say so.

### 4.2 Second order (required, engine-free, the genuinely open limb)

Deferring amortization leaves a **higher surviving balance**, so early prepayment dollars at a
given CPR rise, partially offsetting the first-order effect. This is **not** waved at: the runner
computes it explicitly from the committed monthly paths — the deferred-balance path accumulated
from $\sigma \times \text{sched}_t$, carried forward and multiplied by the leg's own
$\text{SMM}(\text{CPR\_Danish}_t)$ month by month, from the same parquet. Its sign is **known**
(it offsets), so the second-order-corrected break-even $\sigma^{**}$ is **above** $\sigma^{*}$; its
**size is not known** and is E3.

### 4.3 The grid

$\sigma \in \{0, 0.10, 0.20, 0.30, \sigma^{*}, 0.45, 0.50\}$, with $\sigma = 0$ the parity anchor
(it must return `gap_par` exactly) and 0.45 the verified Nationalbank read. Both break-evens are
reported.

## 5. Pre-commitments

**STOP-class:**

- **E1 — the anchor is exact.** $\sigma = 0$ returns `gap_par` = 61.18833737010482 to $10^{-12}$,
  and $\sum_t$ `weighted_sched_b` = 198.66568741255054 to $10^{-9}$, both **read live** from the
  committed artifact and parquet, never from literals in the runner. The buyback identity
  $\sum_t \lvert\text{Danish rolloff}_t\rvert - \sum_t \text{sched}_t = 470.6532528541021$ is
  re-derived as a cross-check that the same parquet columns are being read the same way.
- **E2 — monotonicity.** $\text{gap}(\sigma)$ is strictly decreasing in $\sigma$ at both orders.
  A violation means the sign convention is inverted.

**GENUINE predictions** (may fail; a miss lands with the miss named):

- **E3 — the second-order offset is material but not decisive.** The balance-feedback term moves
  the break-even from $\sigma^{*} = 0.3080$ to a $\sigma^{**}$ in **(0.3080, 0.400]** — i.e. it
  raises the bar by less than ten percentage points of IO share. Rough basis: over 42 months at
  $\sigma = 0.45$ the deferred balance averages roughly half of $0.45 \times 198.7 \approx 89$bn,
  and at the leg's 5.61% CPR that returns on the order of \$9bn against an \$89bn first-order
  effect — about a tenth. **I do not know the realized value and this may fail.**
- **E4 — the verified 45% clears both break-evens**, so the gap reverses sign under **face**
  accounting. This follows from E3 arithmetically if E3 holds; it is stated separately because it
  is the claim that would reach the manuscript, and it must be checked as it would be printed.

**The failure that would matter most, named in advance.** If E4 holds, then the Danish
counterfactual's $+\$61.2$bn institutional relief **reverses under face accounting alone** — not
only under the cash-haircut reading C-75 prices. That would mean the paper's face-denominated
Danish claim, which `.tex:658` currently rests on precisely because face is "the benchmark's own
denomination", does not survive importing one further piece of the Danish product mix. **That
result lands.** It is pre-authorised here, in writing, before the run.

## 6. Gates

- **P0** sha pins on `hazard/data/microsim_results_us_intercept.parquet`
  (`38041df75a57ff1e86f224e7085b5465e521f0b07b861ffcc9427139aa44b28a`),
  `hazard/data/danish_us_intercept_results.json`
  (`b810a1dae636617f9417c6a343c55d67ec6c8659b7a3dfcb55e134b804e1aca7`) and
  `hazard/data/buyback_credit_bracket_results.json`
  (`dba71c544f9b116848731d12983258538e697813388f7632887e1eaa84c35881`), asserted live;
  **P0b** byte-identical at exit.
- **P1** — E1, live.
- **P2 (source verification, BLOCKING).** The runner **re-fetches the Nationalbank page and
  asserts the verbatim sentence** — `"currently making up 45 per cent of outstanding mortgage
  volumes"` — is present, recording the URL, the fetch timestamp and the publication date
  (2020-02-04) in the artifact. **If the fetch fails or the sentence is absent, the run records
  `io_share_sourced: false` and STILL LANDS the break-even**, which needs no external input at all.
  The number is never taken from this spec's transcription alone.
- **P3** — the 42-month window and the leg's `mean_danish_cpr_pct = 5.613626373336359` re-read
  live and asserted to $10^{-12}$; `weighted_sched_b`$_t > 0$ for all 42 months.
- **P4** — the second-order term is reported **separately** from the first-order term, never
  folded into it, so a reader can see both and check the offset's size for themselves.
- **W1** — writes **only** `hazard/data/danish_interest_only_share_results.json`; refuses to
  overwrite a differing file; never rewrites any committed artifact; edits no `.tex`.
- **No engine.** Arithmetic on the committed parquet only; nothing under `hazard/data/floor_sweep/`.

## 7. Landing rules, per branch

- **Branch A — gates pass, source verified, E3 and E4 hold (the gap reverses at 45%).** Land the
  reversal. `.tex:627`'s concession is **replaced by a measurement**: the IO share's direction was
  already stated, and it now carries a magnitude and a crossing — the gap turns negative above an
  IO share of $\sigma^{**}$, and Denmark's verified share is above it. `.tex:658`'s
  "gross institutional relief under face accounting" sentence is re-scoped: face accounting no
  longer delivers unconditional relief once the product mix travels with the payoff rule. A
  **new bib entry** is required (`paper/references.bib` currently has 37 entries and **no
  Danmarks Nationalbank entry**), verified against the source at landing. New gate + test battery
  pinning both break-evens and the sourced share; `tab:runindex` row. **[posture] — this touches
  the Danish claim's headline framing; Eugene signs.**
- **Branch B — gates pass, source verified, E3 misses but E4 still holds.** Land the reversal with
  the pre-committed $\sigma^{**}$ band quoted beside the realized value and the miss named.
- **Branch C — gates pass and E4 FAILS** (the second-order offset is large enough that 45% does
  not clear $\sigma^{**}$). **Land that too.** It is the outcome most favourable to the paper: the
  face-accounting relief survives the product mix, the standing concession at `.tex:627` is
  **retired by measurement rather than merely restated**, and the break-even is reported so a
  reader can see how much headroom there is. Report it with the pre-committed direction quoted and
  flagged as having gone against my prediction.
- **Branch D — P2 fails (the source cannot be re-verified at run time).** **Land the break-even
  alone.** $\sigma^{*}$ and $\sigma^{**}$ need no external input, and "the gap reverses above an
  interest-only share of about 31–40%" is a complete, citable statement that sharpens `.tex:627`
  without importing any number. The concession stands but gains its magnitude. **This branch is
  the floor and it is always available.**
- **Branch E — P0/P1/P3 or E1/E2 fails.** Land nothing; commit the runner output and a failure
  record under `specs/`.

## 8. Scope limits this spec commits to stating

1. **This is an accounting-layer calculation, not a re-simulation.** The hazard is untouched; only
   the amortization path moves. The second-order balance feedback is computed, but a full
   re-simulation with a genuinely IO-amortizing book is the stronger test and is **out of scope**
   here (single-tenant engine, and no Danish loan panel exists in this design).
2. **The 45% is pre-window, deferred-amortisation, and whole-market.** All three limits from §2
   travel with every quotation of it. It is an **imported institutional parameter**, in exactly the
   sense the paper already uses for the mobility elasticity, and it is never described as measured
   here.
3. **One anchor only.** The production U.S.-intercept pair is the only committed pair with a
   monthly decomposition, so the off-window $+\$28.2$bn cell and the Danish-level bracketing anchor
   are out of scope, as they are for C-75.
4. **This is a different reversal from C-75's.** C-75 prices the buyback discount and reverses the
   gap under **cash** accounting. This reverses it under **face** accounting, by a different
   mechanism. If both land, the two must be reported as **separate channels that do not compose
   additively without argument** — and neither spec may quietly stack on the other.
5. **The U.S. leg's zero IO share is held fixed, not measured.** It stays a disclosed held-fixed
   feature of the U.S. leg, in the same sentence's own terms.
