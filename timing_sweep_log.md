# Timing-phrase-family sweep log — round 10 (2026-07-11)

LEGEND: round-5 dispositions recorded ACTIONS taken in that revision; rounds 6+ record
STEADY STATE (a RETAINED row may have been demoted in an earlier round).
Matcher: word-boundary regex with an optional trailing 's'; EVERY family phrase on a
line records its own row — the round-6 log's one-row-per-line design silently dropped
'trails' and 'moves first' when they followed 'ahead' on the same source line (panel
finding, confirmed); dispositions are evaluated on a ±200-char window around each hit.
The generator is committed at tools/timing_sweep.py and must pass the golden-fixture
test (tools/test_timing_sweep.py) — three matcher generations produced three distinct
silent defects (round-6 first-match-per-line; round-6 'flags' false positive; round-8
suffix-s truncation), so the tool is now tested against a hand-enumerated hit set.
CORRECTED ROUND-8 RECONCILIATION (panel finding, round 9): the round-8 letter presented
v4→v5 as +22 additive (60→82: paragraph splits, new sentences, errata). The true
movement was two-sided: 60 − 6 + 28 = 82 — the round-8 matcher rewrite silently DROPPED
six suffix-s rows ('offsets' tex 255/420 + docx 155/285; 'leads' tex 278 + docx 185,
v4 numbering) while adding 28. v6 restored the six (82 + 6 = 88); this log carries them.

Family: {timing, lead, path diagnostics, nonnegative, not outright negative, materially better, offset, ahead, trails, moves first, precedes, lags}.

| src | line | phrase | context | disposition |
|---|---|---|---|---|
| tex | 129 | lead | …$3-month window exceeding the +0.19 at the three-month lead. (A fifty-seed Monte Carlo re-draw under the same spec… | RETAINED - raw correlogram / convention bookkeeping, guarded in-line |
| tex | 131 | timing | …tes on the level of simulated mobility rather than its timing. Full mechanism-level detail for each extension is rep… | RETAINED - ABM mechanism description, hedged in-line |
| tex | 131 | lead | …$\pm$3-month window --- the $+0.19$ at the three-month lead noted above --- is weak and statistically indistinguis… | RETAINED - ABM mechanism description, hedged in-line |
| tex | 188 | offset | …he model is a discrete-time hazard with a log-exposure offset, | RETAINED - econometric term of art |
| tex | 192 | nonnegative | …led object is the prepayment rate $y_{s,t}/n_{s,t}$, a nonnegative fraction, so the model is estimated by Poisson pseudo-… | RETAINED - econometric term of art |
| tex | 192 | offset | …outcome is dollars, not a count: with the log-exposure offset the modeled object is the prepayment rate $y_{s,t}/n_{… | RETAINED - econometric term of art |
| tex | 248 | timing | …ecovery as evidence about the aggregate level only. No timing claim rests on Path B either: its apparent levels adva… | RETAINED - states the retraction / carries the guard |
| tex | 268 | offset | …quivalent units, so that the buyback discount properly offsets the locked-in spread --- $g_{\mathrm{DK}} = g_{\mathrm… | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| tex | 270 | ahead | …SOMA-derived CPR path moves approximately three months ahead of the simulated path (a peak selected across the seve… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 270 | trails | …tation a peak at $k=-3$ means the simulated path \emph{trails} the empirical path by three months --- the empirical … | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 270 | moves first | …mpirical path by three months --- the empirical series moves first. At this peak, the empirical SOMA-derived CPR path mov… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 270 | lags | …ulated path (a peak selected across the seven examined lags, so its nominal significance overstates; no inference … | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 272 | timing | …l --- not merely on Path B's specification --- but the timing is not part of that evidence: as Section~\ref{sec:haza… | RETAINED - states the retraction / carries the guard |
| tex | 272 | lead | …elasticity set to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from t… | RETAINED - states the retraction / carries the guard |
| tex | 272 | lead | …t to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from the mechanical… | RETAINED - states the retraction / carries the guard |
| tex | 274 | timing | …e therefore attach no settlement interpretation to the timing alignment. | RETAINED - states the retraction / carries the guard |
| tex | 274 | offset | …onths later, predicts the \emph{opposite} direction of offset. We therefore attach no settlement interpretation to t… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 274 | moves first | … (verified against synthetic data), the empirical path moves first --- a settlement-delay mechanism, in which loan-level … | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 276 | timing | A direct input-timing diagnosis rules out the dating of the rate input and n… | RETAINED - input-timing diagnosis description, credential-free |
| tex | 278 | timing | …nction is the accuracy of its aggregate level, not its timing. (In levels, which are trend-contaminated over the win… | RETAINED - states the retraction / carries the guard |
| tex | 278 | lead | …ag 0 (it reaches $-1$ under a two-to-three-month input lead) while moving recovered trapped liquidity by less than… | RETAINED - input-shift scan bookkeeping, credential-free |
| tex | 278 | offset | …ath is contemporaneous.) No single channel carries the offset: the $\beta_b = 0$ and $\beta_1 = 0$ ablations both le… | RETAINED - mechanism-not-isolated statement, credential-free |
| tex | 278 | offset | …by less than \$1.5 billion across the entire scan. The offset is therefore a property of the fitted path's smooth ag… | RETAINED - mechanism-not-isolated statement, credential-free |
| tex | 280 | lags | … the lag-0 correlation at $[-0.13, +0.44]$; with seven lags searched, individual band-point differences in peak $r… | RETAINED - lag-search bookkeeping |
| tex | 294 | path diagnostics | …d liquidity & \% of benchmark & CPR path corr. (lag) & Path diagnostics \\ | RETAINED - open-question statement, credential-free |
| tex | 299 | lead | …76\%; $r = +0.190$ at lag 0; 3-month offset (empirical leads; reference only, Section~\ref{sec:pathb}) \\ | RETAINED - states the retraction / carries the guard |
| tex | 299 | offset | …-3$) & mean CPR 4.76\%; $r = +0.190$ at lag 0; 3-month offset (empirical leads; reference only, Section~\ref{sec:pat… | RETAINED - states the retraction / carries the guard |
| tex | 307 | timing | …ation choices; neither reproduces the empirical path's timing (no estimator does; see above), but the recalibrated v… | RETAINED - states the retraction / carries the guard |
| tex | 307 | timing | …-0.20$ to $-0.30$; Section~\ref{sec:pathb}) --- and no timing evidence is claimed for any estimator. Block-length se… | RETAINED - states the retraction / carries the guard |
| tex | 314 | timing | …cation we tested lands within 45\% of it. We attach no timing credential to this: Path B's raw $+0.190$ lag-0 correl… | RETAINED - states the retraction / carries the guard |
| tex | 314 | timing | …ef{tab:estimators} counsel against weighing any single timing coefficient, including Path B's lag $-3$ peak, whose i… | RETAINED - states the retraction / carries the guard |
| tex | 314 | timing | …ing Path B's lag $-3$ peak, whose interval spans zero. Timing alone, however, does not identify the lock-in channel:… | RETAINED - states the retraction / carries the guard |
| tex | 382 | lead | ….195$ at lag $-3$ --- the ``$+0.19$ at the three-month lead'' of Section~\ref{sec:abm-results}; the two convention… | RETAINED - raw correlogram / convention bookkeeping, guarded in-line |
| tex | 389 | timing | …c:pathb}); Path B's distinction is level accuracy, not timing. The timing critique of Section~\ref{sec:abm} therefor… | RETAINED - open-question statement, credential-free |
| tex | 389 | timing | …ath B's distinction is level accuracy, not timing. The timing critique of Section~\ref{sec:abm} therefore survives r… | RETAINED - open-question statement, credential-free |
| tex | 393 | timing | …h paradigms still depend on real structure for correct timing. We treat the aggregate-level paradigm claim of Sectio… | RETAINED - open-question statement, credential-free |
| tex | 443 | offset | …equivalent units so that the buyback discount properly offsets the locked-in spread. Section~\ref{sec:pathb} reports … | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| tex | 449 | timing | …g within 2.1\% --- a level-accuracy distinction, not a timing one: no estimator's monthly co-movement survives detre… | RETAINED - states the retraction / carries the guard |
| tex | 449 | timing | …M's share is calibration-sensitive, and the path-level timing question remains open. | RETAINED - open-question statement, credential-free |
| tex | 467 | timing | … matching its real-data recovery, while its path-level timing does not transfer to synthetic data. Also complete as … | RETAINED - open-question statement, credential-free |
| tex | 467 | timing | … the Danish counterfactual's description; and (iv) the timing-sweep generator's golden-fixture test (\texttt{tools/t… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| tex | 467 | timing | …p generator's golden-fixture test (\texttt{tools/test\_timing\_sweep.py}) must pass at the freeze, three matcher gen… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| tex | 467 | timing | …od-frictions}); and the monthly-frequency question the timing diagnosis leaves --- the empirical path's variation at… | RETAINED - open-question statement, credential-free |
| tex | 469 | timing | …n choice and data source --- and leaves the path-level timing question as the one part that remains genuinely open. | RETAINED - open-question statement, credential-free |
| tex | 496 | trails | … = -3$. Every direction claim in that draft (simulated trails; empirical moves first) was computed under, and verifi… | RETAINED - Appendix A erratum record of the corrected convention definition (round 8), guarded by construction |
| tex | 496 | moves first | …ction claim in that draft (simulated trails; empirical moves first) was computed under, and verified against synthetic da… | RETAINED - Appendix A erratum record of the corrected convention definition (round 8), guarded by construction |
| docx | 51 | lead | …±3-month window exceeding the +0.19 at the three-month lead. (A fifty-seed Monte Carlo re-draw under the same spec… | RETAINED - raw correlogram / convention bookkeeping, guarded in-line |
| docx | 52 | timing | …tes on the level of simulated mobility rather than its timing. Full mechanism-level detail for each extension is rep… | RETAINED - ABM mechanism description, hedged in-line |
| docx | 52 | lead | … in the ±3-month window — the +0.19 at the three-month lead noted above — is weak and statistically indistinguisha… | RETAINED - ABM mechanism description, hedged in-line |
| docx | 92 | offset | …he model is a discrete-time hazard with a log-exposure offset, | RETAINED - econometric term of art |
| docx | 94 | nonnegative | …the modeled object is the prepayment rate ys,t/ns,t, a nonnegative fraction, so the model is estimated by Poisson pseudo-… | RETAINED - econometric term of art |
| docx | 94 | offset | …outcome is dollars, not a count: with the log-exposure offset the modeled object is the prepayment rate ys,t/ns,t, a… | RETAINED - econometric term of art |
| docx | 171 | timing | …ecovery as evidence about the aggregate level only. No timing claim rests on Path B either: its apparent levels adva… | RETAINED - states the retraction / carries the guard |
| docx | 181 | offset | …quivalent units, so that the buyback discount properly offsets the locked-in spread — gDK = gUS + Δybuyback ≈ 0 whene… | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| docx | 182 | ahead | …SOMA-derived CPR path moves approximately three months ahead of the simulated path (a peak selected across the seve… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 182 | trails | …implementation a peak at k=−3 means the simulated path trails the empirical path by three months — the empirical ser… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 182 | moves first | … empirical path by three months — the empirical series moves first. At this peak, the empirical SOMA-derived CPR path mov… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 182 | lags | …ulated path (a peak selected across the seven examined lags, so its nominal significance overstates; no inference … | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 183 | timing | …small — not merely on Path B’s specification — but the timing is not part of that evidence: as Section V.D reports, … | RETAINED - states the retraction / carries the guard |
| docx | 183 | lead | …elasticity set to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from t… | RETAINED - states the retraction / carries the guard |
| docx | 183 | lead | …t to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from the mechanical… | RETAINED - states the retraction / carries the guard |
| docx | 184 | timing | …e therefore attach no settlement interpretation to the timing alignment. | RETAINED - states the retraction / carries the guard |
| docx | 184 | offset | …three months later, predicts the opposite direction of offset. We therefore attach no settlement interpretation to t… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 184 | moves first | … (verified against synthetic data), the empirical path moves first — a settlement-delay mechanism, in which loan-level pr… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 185 | timing | A direct input-timing diagnosis rules out the dating of the rate input and n… | RETAINED - input-timing diagnosis description, credential-free |
| docx | 186 | timing | …nction is the accuracy of its aggregate level, not its timing. (In levels, which are trend-contaminated over the win… | RETAINED - states the retraction / carries the guard |
| docx | 186 | lead | … lag 0 (it reaches −1 under a two-to-three-month input lead) while moving recovered trapped liquidity by less than… | RETAINED - input-shift scan bookkeeping, credential-free |
| docx | 186 | offset | …ath is contemporaneous.) No single channel carries the offset: the βb = 0 and β1 = 0 ablations both leave the peak a… | RETAINED - mechanism-not-isolated statement, credential-free |
| docx | 186 | offset | … by less than $1.5 billion across the entire scan. The offset is therefore a property of the fitted path’s smooth ag… | RETAINED - mechanism-not-isolated statement, credential-free |
| docx | 187 | lags | …on the lag-0 correlation at [−0.13, +0.44]; with seven lags searched, individual band-point differences in peak r … | RETAINED - lag-search bookkeeping |
| docx | 195 | path diagnostics | Path diagnostics | RETAINED - open-question statement, credential-free |
| docx | 215 | lead | … 4.76%; r = +0.190 at lag 0; 3-month offset (empirical leads; reference only, Section V.C) | RETAINED - states the retraction / carries the guard |
| docx | 215 | offset | mean CPR 4.76%; r = +0.190 at lag 0; 3-month offset (empirical leads; reference only, Section V.C) | RETAINED - states the retraction / carries the guard |
| docx | 227 | timing | …ation choices; neither reproduces the empirical path’s timing (no estimator does; see above), but the recalibrated v… | RETAINED - states the retraction / carries the guard |
| docx | 227 | timing | …ators cluster at −0.20 to −0.30; Section V.C) — and no timing evidence is claimed for any estimator. Block-length se… | RETAINED - states the retraction / carries the guard |
| docx | 228 | timing | …cation we tested lands within 45% of it . We attach no timing credential to this: Path B’s raw +0.190 lag-0 correlat… | RETAINED - states the retraction / carries the guard |
| docx | 228 | timing | …tervals of Table 4 counsel against weighing any single timing coefficient, including Path B’s lag −3 peak, whose int… | RETAINED - states the retraction / carries the guard |
| docx | 228 | timing | …uding Path B’s lag −3 peak, whose interval spans zero. Timing alone, however, does not identify the lock-in channel:… | RETAINED - states the retraction / carries the guard |
| docx | 277 | lead | …nt is +0.195 at lag −3 — the “+0.19 at the three-month lead” of Section IV.A; the two conventions summarize the sa… | RETAINED - raw correlogram / convention bookkeeping, guarded in-line |
| docx | 279 | timing | …tion V.C); Path B’s distinction is level accuracy, not timing. The timing critique of Section IV therefore survives … | RETAINED - open-question statement, credential-free |
| docx | 279 | timing | …ath B’s distinction is level accuracy, not timing. The timing critique of Section IV therefore survives regardless o… | RETAINED - open-question statement, credential-free |
| docx | 281 | timing | …h paradigms still depend on real structure for correct timing. We treat the aggregate-level paradigm claim of Sectio… | RETAINED - open-question statement, credential-free |
| docx | 317 | offset | …equivalent units so that the buyback discount properly offsets the locked-in spread. Section V.C reports the correcte… | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| docx | 320 | timing | …ding within 2.1% — a level-accuracy distinction, not a timing one: no estimator’s monthly co-movement survives detre… | RETAINED - states the retraction / carries the guard |
| docx | 320 | timing | …M’s share is calibration-sensitive, and the path-level timing question remains open. | RETAINED - open-question statement, credential-free |
| docx | 329 | timing | … matching its real-data recovery, while its path-level timing does not transfer to synthetic data. Also complete as … | RETAINED - open-question statement, credential-free |
| docx | 329 | timing | … the Danish counterfactual’s description; and (iv) the timing-sweep generator’s golden-fixture test (tools/test_timi… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| docx | 329 | timing | …ming-sweep generator’s golden-fixture test (tools/test_timing_sweep.py) must pass at the freeze, three matcher gener… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| docx | 329 | timing | …Section III.C); and the monthly-frequency question the timing diagnosis leaves — the empirical path’s variation at t… | RETAINED - open-question statement, credential-free |
| docx | 330 | timing | …ion choice and data source — and leaves the path-level timing question as the one part that remains genuinely open. | RETAINED - open-question statement, credential-free |
| docx | 343 | trails | …k = −3. Every direction claim in that draft (simulated trails; empirical moves first) was computed under, and verifi… | RETAINED - Appendix A erratum record of the corrected convention definition (round 8), guarded by construction |
| docx | 343 | moves first | …ction claim in that draft (simulated trails; empirical moves first) was computed under, and verified against synthetic da… | RETAINED - Appendix A erratum record of the corrected convention definition (round 8), guarded by construction |

Total: 92 rows. Tally (computed from table rows): {'RETAINED': 92}.
