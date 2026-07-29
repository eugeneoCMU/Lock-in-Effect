Worktree root: `/Users/eugene/somthing/Lock In effect/Lock-in-Effect/.claude/worktrees/paper-v18-review-plan-5b7b5e`

---

# PATCH G2-A — the `coupon_convert` seam

**Status:** draft. **This file changes nothing.** It is the pre-committed patch of
`SPEC_round28_G2_coupon_convention.md` §G2-A.2, written out so the coordinator applies it with
count-asserted replacements. Three files, seven hunks. `hazard/coupon_convention_reweight.py`
does not import cleanly until all seven are applied.

**The one property every hunk preserves, and the reason the patch is shaped this way:**

> With `coupon_convert=None` — the default everywhere, and the value every existing caller
> supplies by omission — the executed arithmetic is *expression-for-expression identical* to
> HEAD. The conversion is applied to a **local copy**; `self.coupon` and the `coupons` dict are
> never reassigned. Spec §G2.1.1 rejected in-place mutation with a `finally` restore precisely
> so that the unsafe outcome is **unreachable** rather than merely undone. Gate **G3** of the
> run script tests that unreachability against `pool.coupon` directly.

**Verification note on hunk 1 (resolves spec §G2.9 item 3):** I read `MicrosimPool.__init__`
(`hazard/agents.py:95-158`) and it does **not** retain `vintage`. The contingency in §G2.9 item 3
therefore fires and hunk 1 is **required**, not optional. `vintage` *is* present in the frame
(`hazard/loan_sample.py:74` selects it; `MicrosimPool` is constructed from the unmodified sample
at `hazard/microsim_engine.py:42`), so it is available to `pdf` and needs only to be carried.

**Verification note on hunk 6 (resolves spec §G2.9 item 7, better than the spec proposed):** the
spec proposed parsing the vintage off `stratum_id`. That is unnecessary. `hazard/simulate.py:45-46`
defines `_cohort_key(row) = (row["vintage"], row["coupon"], row["fico_bucket"], row["ltv_bucket"])`,
so **the cohort key's first element is the vintage**. Hunk 6 uses `key[0]`. No string parsing, no
format assumption, and the Path A leg is no longer at risk of being dropped.

**Apply order:** 1 → 7 (file order is irrelevant; hunks within a file are independent). After
applying, run `tools/liveness_gates.py` before running anything else: with the defaults in place
every committed artifact is still reproducible, so **a red gate after this patch means the patch
is wrong, not that the numbers moved.**

---

## File 1 — `hazard/agents.py` (3 hunks)

### Hunk 1 — carry the vintage onto the pool

**Expected occurrences of the old string in the file: 1.**

OLD
```python
        self.coupon = coupon_to_decimal(pdf["coupon"].values.astype(np.float64))
```

NEW
```python
        self.coupon = coupon_to_decimal(pdf["coupon"].values.astype(np.float64))
        # G2 (coupon-convention, round 28): origination year, carried ONLY so
        # that the full-book reweight can convert note rates to pass-through
        # equivalents per vintage. Read by reweight_to_soma_coupons and by
        # nothing else — no hazard, rate-gap, stress, or scoring path consumes
        # it. None when the frame predates the column (Path A fixtures).
        self.vintage = (
            pdf["vintage"].values.astype(np.int64)
            if "vintage" in pdf.columns else None
        )
```

*Inertness:* adds one attribute. Nothing reads it unless `coupon_convert` is passed.

---

### Hunk 2 — the signature

**Expected occurrences: 1.**

OLD
```python
    def reweight_to_soma_coupons(self, soma_cohorts: list) -> None:
```

NEW
```python
    def reweight_to_soma_coupons(self, soma_cohorts: list,
                                 coupon_convert=None) -> None:
```

*Inertness:* new keyword-with-default; every existing call site is unchanged and still valid.

---

### Hunk 3 — bucket on the pass-through basis when a converter is supplied

**Expected occurrences: 1** (this is the only `np.round(np.round(` in `hazard/agents.py`).

OLD
```python
        buckets = np.round(np.round(self.coupon / step) * step, 4)
```

NEW
```python
        # G2 (coupon-convention, round 28). SOMA's `coupon` is the security
        # PASS-THROUGH rate, parsed from securityDescription
        # (abm/fed_mbs_extension_risk.py:561-565); self.coupon is the borrower
        # NOTE rate (loan_sample.parquet). Bucketing them against each other on
        # the same 0.5% grid is a ~0.8pp basis mismatch, about 1.6 buckets. When
        # a converter is supplied the SAMPLE side is mapped onto the
        # pass-through basis so both sides are bucketed on one convention.
        #
        # The conversion is applied to a LOCAL COPY. self.coupon is never
        # reassigned, so no hazard input can move: compute_rate_gap,
        # rate_stress and the Danish berger_calibration branches all read
        # self.coupon (competing_risks.py:120-168) and see the note rate
        # unchanged. This is the design in SPEC_round28_G2 §G2.1.1 and it is
        # what makes the marginal's invariance structural rather than restored.
        src = self.coupon
        if coupon_convert is not None:
            src = np.asarray(
                coupon_convert(self.coupon, self.vintage), dtype=np.float64
            )
            if src.shape != self.coupon.shape:
                raise ValueError(
                    "coupon_convert changed array shape "
                    f"({self.coupon.shape} -> {src.shape})"
                )
        buckets = np.round(np.round(src / step) * step, 4)
```

*Inertness:* with `coupon_convert=None`, `src is self.coupon` and the final line is the OLD line
with `self.coupon` spelled `src`.

**Optional hunk 3b (documentation only, no behaviour).** If the coordinator wants the docstring to
carry the convention, append to `reweight_to_soma_coupons`'s docstring, immediately before the
closing `"""`, expected occurrences of the anchor string: **1**.

ANCHOR (end of the existing docstring)
```python
        their share is renormalized away. Call BEFORE scale_to_holdings, which
        then restores the total to Fed holdings.
        """
```

NEW
```python
        their share is renormalized away. Call BEFORE scale_to_holdings, which
        then restores the total to Fed holdings.

        CONVENTIONS. soma_cohorts carry the security PASS-THROUGH coupon;
        self.coupon is the borrower NOTE rate. `coupon_convert(coupon, vintage)
        -> array` maps the sample side onto the pass-through basis (note rate
        minus vintage g-fee minus base servicing). It is applied to a local
        copy only; self.coupon is never modified. Default None reproduces the
        historical mixed-basis matching bit-for-bit.
        """
```

---

## File 2 — `hazard/microsim_engine.py` (3 hunks)

### Hunk 4 — `_simulate_regime` signature

**Expected occurrences: 1** (the docstring line makes the anchor unique; the bare
`soma_cohorts: Optional[list] = None,` occurs twice in this file).

OLD
```python
    soma_cohorts: Optional[list] = None,
) -> pd.DataFrame:
    """Walk one regime pool through QT window."""
```

NEW
```python
    soma_cohorts: Optional[list] = None,
    coupon_convert=None,
) -> pd.DataFrame:
    """Walk one regime pool through QT window."""
```

---

### Hunk 5 — forward the converter into the reweight

**Expected occurrences: 1.**

OLD
```python
        pool.reweight_to_soma_coupons(soma_cohorts)  # full-book weighting (3.1)
```

NEW
```python
        pool.reweight_to_soma_coupons(  # full-book weighting (3.1)
            soma_cohorts, coupon_convert=coupon_convert)
```

---

### Hunk 6 — `run_qt_microsim` signature and forward

Two edits, both in `run_qt_microsim`.

**6a. Expected occurrences: 1** (the return annotation makes it unique).

OLD
```python
    soma_cohorts: Optional[list] = None,
) -> dict[str, pd.DataFrame]:
```

NEW
```python
    soma_cohorts: Optional[list] = None,
    coupon_convert=None,
) -> dict[str, pd.DataFrame]:
```

**6b. Expected occurrences: 1** (`soma_cohorts=soma_cohorts,` appears once in the file).

OLD
```python
            soma_cohorts=soma_cohorts,
        )
```

NEW
```python
            soma_cohorts=soma_cohorts,
            coupon_convert=coupon_convert,
        )
```

---

## File 3 — `hazard/simulate.py` (3 hunks — the Path A side, defect instance (a-ii))

`_reweight_balances_to_soma` is the **second, unnamed instance** of the same mismatch
(SPEC §0.1): SOMA pass-through coupons at `:79`, cohort note rates at `:90` and `:96`.

### Hunk 7 — `_reweight_balances_to_soma` signature

**Expected occurrences: 1.**

OLD
```python
def _reweight_balances_to_soma(balances: dict, coupons: dict,
                               soma_cohorts: list) -> dict:
```

NEW
```python
def _reweight_balances_to_soma(balances: dict, coupons: dict,
                               soma_cohorts: list,
                               coupon_convert=None) -> dict:
```

---

### Hunk 8 — bucket both loops through one converter

**Expected occurrences of the whole OLD block: 1.**

OLD
```python
    cur_share: dict = {}
    for key, bal in balances.items():
        b = round(round(float(coupons[key]) / step) * step, 4)
        cur_share[b] = cur_share.get(b, 0.0) + bal / total_bal

    out = {}
    for key, bal in balances.items():
        b = round(round(float(coupons[key]) / step) * step, 4)
        w = (soma_share.get(b, 0.0) / cur_share[b]) if cur_share.get(b, 0) > 0 else 0.0
        out[key] = bal * w
    return out
```

NEW
```python
    # G2 (coupon-convention, round 28). Same basis mismatch as
    # agents.reweight_to_soma_coupons, on the Path A cohort side: soma_share is
    # keyed by PASS-THROUGH coupon, coupons[key] is the cohort's NOTE rate.
    # The cohort key is (vintage, coupon, fico_bucket, ltv_bucket) — see
    # _cohort_key above — so key[0] IS the vintage and no stratum-id parsing is
    # needed. The converter is applied to a LOCAL value; `coupons` is never
    # mutated, and the hazard path (predict_hazard's rate gap) reads the
    # untouched dict.
    def _bucket(key) -> float:
        c = float(coupons[key])
        if coupon_convert is not None:
            c = float(coupon_convert(c, key[0]))
        return round(round(c / step) * step, 4)

    cur_share: dict = {}
    for key, bal in balances.items():
        b = _bucket(key)
        cur_share[b] = cur_share.get(b, 0.0) + bal / total_bal

    out = {}
    for key, bal in balances.items():
        b = _bucket(key)
        w = (soma_share.get(b, 0.0) / cur_share[b]) if cur_share.get(b, 0) > 0 else 0.0
        out[key] = bal * w
    return out
```

---

### Hunk 9 — `simulate_qt_window` signature and forward

**9a. Expected occurrences: 1.**

OLD
```python
    soma_cohorts: Optional[list] = None,
    coef_path: Path = HAZARD_COEF_PATH,
) -> pd.DataFrame:
```

NEW
```python
    soma_cohorts: Optional[list] = None,
    coef_path: Path = HAZARD_COEF_PATH,
    coupon_convert=None,
) -> pd.DataFrame:
```

**9b. Expected occurrences: 1.**

OLD
```python
        balances = _reweight_balances_to_soma(balances, coupons, soma_cohorts)
```

NEW
```python
        balances = _reweight_balances_to_soma(balances, coupons, soma_cohorts,
                                              coupon_convert=coupon_convert)
```

---

## Post-application checklist (before any G2 leg runs)

1. `python3 tools/liveness_gates.py` — **ALL GATES PASS**, unchanged. The patch is inert by
   construction; a failure means a hunk was mis-applied.
2. `cd hazard && python3 -c "import agents, simulate, microsim_engine"` — imports clean.
3. `cd hazard && python3 coupon_convention_reweight.py --selftest` — runs the free gates only
   (G0/G1/G2/G3 analytic legs), no engine, no artifact write. **This is the intended smoke test
   and it exercises hunks 1-3 and 7-8 directly** (it constructs a `MicrosimPool`, calls
   `reweight_to_soma_coupons` with `coupon_convert=None` and again with `φ_id`, and asserts the
   bucket assignment is bit-identical between them and that `pool.coupon` never moved).
4. Only then the full run.

**Rollback:** all nine hunks are additive; reverting is `git checkout -- hazard/agents.py
hazard/simulate.py hazard/microsim_engine.py`. No committed artifact is touched by the patch.
