# RECORD — `berger2026` citation currency, verified against the authors' drafts — 2026-07-31

The manuscript on `main` asserted that Berger et al.'s general-equilibrium counterfactual
"shifts the equilibrium mortgage rate by only about one basis point, economically
negligible." R32's citation fact-check had already flagged this as superseded and
recorded the current value as **20 bps**. Neither figure is right for the current draft.

## Evidence

SSRN itself returns HTTP 403 to this environment, but the authors host both drafts:

| draft | URL | what it says |
|---|---|---|
| January 2026 (the version cited) | `fabricetourre.com/wp-content/uploads/2026/01/draft_20260127.pdf` | "rates under the two systems are remarkably similar --- differing by only **1 bp** on average"; "on average only **1 bps** higher with the option than without it". Section **4.9.1**. |
| March 2026 (current) | `fabricetourre.com/wp-content/uploads/2026/03/household_response_liability_shocks-2026-03-19t155333.098.pdf` | "is on average only **18 bps** higher than under the current system"; §**4.10.2** "How much would mortgage rates increase by?" --- "only 18 bps higher with the option than without it", "only 18bps higher (on average)". |

Corroboration: Marginal Revolution's March 2026 write-up of the paper reports "mortgage
interest rates in the US would rise by only 18 basis points on average."

The March draft also carries a sensitivity — **22 bps** when the arrival intensity of
moving opportunities is raised 25% — which is the likeliest source of a mis-recorded
"20 bps": it is neither the baseline nor a rounding of it.

## Findings

1. **The manuscript's 1 bp was correct for the draft it cited** and is stale for the
   current one. The estimate moved by **more than an order of magnitude**.
2. **"Economically negligible" is no longer the authors' characterization.** The March
   draft calls the 18 bp cost "non-trivial" in the same paragraph.
3. **§4.9.1 became §4.10.2**, so the pin in the `\citep` was also stale — R32 was right
   that the old section no longer exists.
4. **R32's fact-check value of 20 bps is wrong.** This matters at merge time: R32 landed
   20 bps in its manuscript *and gated it*, so that branch carries a wrong number behind
   a green gate. Correct it to 18 bps when R32 lands.

## Landed here

Both editions now read 18 basis points with the `\S4.10.2` pin, say plainly that the
one-basis-point figure was the January draft's and that the estimate moved, and drop
"economically negligible" in favour of a characterization the authors would accept. The
`references.bib` note records both drafts and both section numbers.

**No computed quantity moves.** The figure is a price statement the paper explicitly
declines to read as a volume statement — §VI.D already argues that reading is contradicted
by realized Danish redemption data (26.4%/yr on deep-discount bonds) — so the correction
touches characterization only, not the Danish gap, the band, or any estimator.

Gate **#128** pins the corrected magnitude and section, and holds the retired
one-basis-point forms at zero occurrences.
