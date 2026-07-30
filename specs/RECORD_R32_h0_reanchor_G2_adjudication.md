# RECORD — Task 9 (C-08): gate G2 reported FAIL, and why that verdict is an instrumentation defect rather than a frozen-artifact violation

**Status: adjudicated, with independent evidence. The run LANDS on Branch B.**

`hazard/data/h0_reanchor_results.json` records `gates_all_pass: false`. Exactly one gate is
responsible — `G2_frozen_artifacts` — and this file establishes what happened, because a
failed anti-overwrite gate is precisely the kind of thing that must not be waved through.

## What the artifact says

```
G2_frozen_artifacts   pass = false   n_files = 201   changed = []
```

A FAIL with an **empty** `changed` list is self-contradictory on its face, and that
contradiction is the tell.

## The cause, located in my own code

`data_shas()` excluded two things: the gitignored `floor_sweep/` scratch directory and the
run's own output path. It did **not** exclude `hazard/data/h0_reanchor_partial.jsonl` — the
per-replicate checkpoint file added during the hardening pass (`b14f58f`) **after** that
exclusion list was written, in response to the transient FRED 502 that killed the first
attempt.

So the checkpoint is a **new key** in `sha_after` that is absent from `sha_before`:

- `sha_before` = 201 files (taken before the replicate loop began writing the checkpoint)
- `sha_after` = 202 files
- `sha_before != sha_after` → verdict False
- but `changed` only iterates keys **present in `sha_before`**, so a purely additive
  difference produces an empty list

The gate was therefore testing set equality while reporting only value inequality.

## The independent evidence that no frozen artifact was touched

The gate's *substantive* requirement is the spec's Section 5 G2: "never overwrite a frozen
artifact." That is verified here by git, which is independent of the gate and of the runner:

```
$ git diff --stat HEAD -- hazard/data/
(empty)

$ git status --porcelain hazard/data/
?? hazard/data/h0_reanchor_partial.jsonl
?? hazard/data/h0_reanchor_results.json
```

- **177 tracked artifacts under `hazard/data/` are byte-identical to HEAD.** Not one is
  modified.
- The only two entries git reports are **additions**, both this run's own: the checkpoint
  and the new output path, which is the one path the spec authorises.
- The 24 untracked `concave_hull_band_ends/*.parquet` files predate this run and are in
  both `sha_before` and `sha_after` unchanged.

203 files in scope now, minus the output path the function excludes, is 202; minus the
checkpoint is 201, which is exactly `sha_before`. The arithmetic closes with no residual.

## Why this does not move the branch

The branch is computed in the runner from `u` and the three **parity** gates that must hold
before any substituted leg is believed:

```
parity_ok = G1a and G1b and G5
branch    = A if (u >= 0.60 and parity_ok) else B if (u >= 0.40 and parity_ok) else C
```

All three PASS, and so do G1b′, G1c, G3 and G4:

| gate | verdict | evidence |
|---|---|---|
| G1a unpatched parity | PASS | null 724.9180585654117, central 767.5264524465003, `marginal_pp` 5.571558182909726 — bit-exact against `psa_level_sweep` |
| G1b identity patch, run patched | PASS | `max|Δh₀|` over ages 0–360 = **0.0 exactly** |
| G5 cross-route φ = 0.75 | PASS | `marginal_pp` 0.8560355409769471, the value two committed artifacts already agree on by different routes |
| G1b′ bind tally moves | PASS | null bind 0.3579 (production) → 0.5038–0.5816 (substituted) |
| G1c no-op detection | PASS | minimum |Δ null trapped| = **74.279 \$B**, against a 1 \$B floor |
| G3 level invariance | PASS | max relative deviation **7.08e-16**, against 1e-12 |
| G4 floor untouched | PASS | floor 4.991%, `FLOOR_MODE` unchanged |

`u = 0.5350` → **Branch B**, which is what the artifact records.

## What was done about it

1. `data_shas()` now excludes the checkpoint file, with the reason in a comment.
2. The gate now reports `added` and `removed` alongside `changed`, so a set difference can
   never again read as "nothing changed" while the verdict is False.
3. The produced artifact is **left exactly as the run wrote it**. It is the honest record of
   what the run reported, and rewriting a result after the fact to make a gate green is the
   one thing this round's rules most clearly forbid. The correction lives here and in the
   runner, not in the output.

## The residual honest caveat

The corrected gate has **not** been re-executed, because doing so means re-running 214
engine cells (~53 minutes) and the runner refuses to overwrite an existing output. The claim
"no frozen artifact was overwritten" therefore rests on the git evidence above, which is
stronger than the gate would have been — git compares the working tree against the committed
tree for all 177 tracked artifacts, whereas the gate only compared a snapshot against itself
within one process.
