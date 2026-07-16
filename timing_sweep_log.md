# Timing-phrase-family sweep log — round 15 (2026-07-16)

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
| tex | 144 | timing | …run manifests record it as applied; it is a documented timing null rather than a fit improvement: a pre-fold-in abla… | NEW round 15 - documented timing-null reference, no credential attached |
| tex | 144 | lead | …$3-month window exceeding the +0.19 at the three-month lead. (A fifty-seed Monte Carlo re-draw under the same spec… | RETAINED - raw correlogram / convention bookkeeping, guarded in-line |
| tex | 153 | timing | …tes on the level of simulated mobility rather than its timing. Full mechanism-level detail for each extension is rep… | RETAINED - ABM mechanism description, hedged in-line |
| tex | 153 | lead | …he $\pm$3-month window (the $+0.19$ at the three-month lead noted above) is weak and statistically indistinguishab… | NEW round 15 - ABM mechanism description, hedged in-line |
| tex | 241 | offset | $n_{s,t}$ & UPB exposure (log offset) & dollars & A \\ | NEW round 15 - econometric term of art (log-exposure offset) |
| tex | 282 | offset | Outcome; estimation & prepaid UPB with log-exposure offset; Poisson pseudo-maximum likelihood, log link \eqref{eq… | NEW round 15 - econometric term of art (log-exposure offset) |
| tex | 298 | offset | …he model is a discrete-time hazard with a log-exposure offset, | RETAINED - econometric term of art |
| tex | 302 | nonnegative | …led object is the prepayment rate $y_{s,t}/n_{s,t}$, a nonnegative fraction, so the model is estimated by Poisson pseudo-… | RETAINED - econometric term of art |
| tex | 302 | offset | …outcome is dollars, not a count: with the log-exposure offset the modeled object is the prepayment rate $y_{s,t}/n_{… | RETAINED - econometric term of art |
| tex | 358 | timing | …ecovery as evidence about the aggregate level only. No timing claim rests on Path B either: its apparent levels adva… | RETAINED - states the retraction / carries the guard |
| tex | 384 | offset | …quivalent units, so that the buyback discount properly offsets the locked-in spread; $g_{\mathrm{DK}} = g_{\mathrm{US… | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| tex | 401 | ahead | …SOMA-derived CPR path moves approximately three months ahead of the simulated path (a peak selected across the seve… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 401 | trails | …tation a peak at $k=-3$ means the simulated path \emph{trails} the empirical path by three months: the empirical ser… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 401 | moves first | …e empirical path by three months: the empirical series moves first. At this peak, the empirical SOMA-derived CPR path mov… | NEW round 15 - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 401 | lags | …ulated path (a peak selected across the seven examined lags, so its nominal significance overstates; no inference … | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 403 | timing | …he level validates the elasticity's magnitude. But the timing is not part of that evidence: as Section~\ref{sec:haza… | NEW round 15 - states the retraction / carries the guard |
| tex | 403 | lead | …elasticity set to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from t… | RETAINED - states the retraction / carries the guard |
| tex | 403 | lead | …t to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from the mechanical… | RETAINED - states the retraction / carries the guard |
| tex | 412 | timing | …e therefore attach no settlement interpretation to the timing alignment. | RETAINED - states the retraction / carries the guard |
| tex | 412 | offset | …onths later, predicts the \emph{opposite} direction of offset. We therefore attach no settlement interpretation to t… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 412 | moves first | … (verified against synthetic data), the empirical path moves first: a settlement-delay mechanism, in which loan-level pre… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| tex | 414 | timing | A direct input-timing diagnosis rules out the dating of the rate input and n… | RETAINED - input-timing diagnosis description, credential-free |
| tex | 416 | timing | …nction is the accuracy of its aggregate level, not its timing. (In levels, which are trend-contaminated over the win… | RETAINED - states the retraction / carries the guard |
| tex | 416 | lead | …ag 0 (it reaches $-1$ under a two-to-three-month input lead) while moving recovered trapped liquidity by less than… | RETAINED - input-shift scan bookkeeping, credential-free |
| tex | 416 | offset | …ath is contemporaneous.) No single channel carries the offset: the $\beta_b = 0$ and $\beta_1 = 0$ ablations both le… | RETAINED - mechanism-not-isolated statement, credential-free |
| tex | 416 | offset | …by less than \$1.5 billion across the entire scan. The offset is therefore a property of the fitted path's smooth ag… | RETAINED - mechanism-not-isolated statement, credential-free |
| tex | 421 | lead | …b}), a peak at negative lag means the empirical series leads and the simulated path trails. Path B's $-3$/$-4$ peak… | NEW round 15 - raw correlogram / convention bookkeeping, guarded in-line |
| tex | 421 | trails | …eans the empirical series leads and the simulated path trails. Path B's $-3$/$-4$ peak and Path A's and the ABM's ne… | NEW round 15 - direction-check / verified convention statement (empirical leads, sim trails); part of the settled retraction |
| tex | 421 | lags | …imulated CPR path and the empirical SOMA-derived path, lags $-6$ to $+6$. Under the implemented convention (Sectio… | NEW round 15 - lag-window convention bookkeeping (lags -6 to +6) |
| tex | 425 | lags | … the lag-0 correlation at $[-0.13, +0.44]$; with seven lags searched, individual band-point differences in peak $r… | RETAINED - lag-search bookkeeping |
| tex | 433 | timing | … is comparable in size to the marginal itself. Second, timing carries no credential: the $\beta_1 = 0$ null also pea… | NEW round 15 - no-credential guard statement (round-15/Q10 material) |
| tex | 433 | lead | … at lag $-3$ (Section~\ref{sec:hazard-interp}), so the lead cannot discriminate the elasticity from the mechanical… | NEW round 15 - states the retraction / carries the guard |
| tex | 474 | path diagnostics | …d liquidity & \% of benchmark & CPR path corr. (lag) & Path diagnostics \\ | RETAINED - open-question statement, credential-free |
| tex | 479 | lead | …76\%; $r = +0.190$ at lag 0; 3-month offset (empirical leads; reference only, Section~\ref{sec:pathb}) \\ | RETAINED - states the retraction / carries the guard |
| tex | 479 | offset | …-3$) & mean CPR 4.76\%; $r = +0.190$ at lag 0; 3-month offset (empirical leads; reference only, Section~\ref{sec:pat… | RETAINED - states the retraction / carries the guard |
| tex | 487 | timing | …ation choices; neither reproduces the empirical path's timing (no estimator does; see above), but the recalibrated v… | RETAINED - states the retraction / carries the guard |
| tex | 487 | timing | …t $-0.20$ to $-0.30$; Section~\ref{sec:pathb}), and no timing evidence is claimed for any estimator. | NEW round 15 - states the retraction / carries the guard |
| tex | 517 | timing | …cation we tested lands within 45\% of it. We attach no timing credential to this: Path B's raw $+0.190$ lag-0 correl… | RETAINED - states the retraction / carries the guard |
| tex | 517 | timing | …ef{tab:estimators} counsel against weighing any single timing coefficient, including Path B's lag $-3$ peak, whose i… | RETAINED - states the retraction / carries the guard |
| tex | 517 | timing | …ing Path B's lag $-3$ peak, whose interval spans zero. Timing alone, however, does not identify the lock-in channel:… | RETAINED - states the retraction / carries the guard |
| tex | 523 | timing | … \emph{candidates} for the modest residual and for the timing failure every estimator shares, not demonstrated drive… | NEW round 15 - shared-timing-failure candidates framing, explicitly hedged in-line ('candidates ... not demonstrated drivers') |
| tex | 570 | timing | …ve, so neither variant reproduces the empirical path's timing regardless of calibration choice, and after Section~\r… | NEW round 15 - states the retraction / carries the guard |
| tex | 592 | lead | …$+0.195$ at lag $-3$, the ``$+0.19$ at the three-month lead'' of Section~\ref{sec:abm-results}; the two convention… | RETAINED - raw correlogram / convention bookkeeping, guarded in-line |
| tex | 601 | timing | …c:pathb}); Path B's distinction is level accuracy, not timing. The timing critique of Section~\ref{sec:abm} therefor… | RETAINED - open-question statement, credential-free |
| tex | 601 | timing | …ath B's distinction is level accuracy, not timing. The timing critique of Section~\ref{sec:abm} therefore survives r… | RETAINED - open-question statement, credential-free |
| tex | 605 | timing | …h paradigms still depend on real structure for correct timing. We treat the aggregate-level paradigm claim of Sectio… | RETAINED - open-question statement, credential-free |
| tex | 657 | offset | …equivalent units so that the buyback discount properly offsets the locked-in spread (a correction live in the mechani… | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| tex | 690 | timing | …ding within 2.1\% (a level-accuracy distinction, not a timing one: no estimator's monthly co-movement survives detre… | NEW round 15 - states the retraction / carries the guard |
| tex | 690 | timing | …ly attributed to modeling paradigm; and the path-level timing question remains open for every estimator. | NEW round 15 - states the retraction / carries the guard |
| tex | 708 | timing | … matching its real-data recovery, while its path-level timing does not transfer to synthetic data. Also complete as … | RETAINED - open-question statement, credential-free |
| tex | 708 | timing | … the Danish counterfactual's description; and (iv) the timing-sweep generator's golden-fixture test (\texttt{tools/t… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| tex | 708 | timing | …p generator's golden-fixture test (\texttt{tools/test\_timing\_sweep.py}) must pass at the freeze, three matcher gen… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| tex | 708 | timing | …od-frictions}); and the monthly-frequency question the timing diagnosis leaves (the empirical path's variation at th… | RETAINED - open-question statement, credential-free |
| tex | 710 | timing | …er than to calibration and data source; the path-level timing question remains genuinely open for every estimator. T… | NEW round 15 - open-question statement, credential-free |
| tex | 717 | offset | …them under fixed seeds (engine seed 42 with per-regime offsets; every post-freeze run's specification is fixed ex ant… | NEW round 15 - RNG per-regime seed-offset description, no timing content |
| docx | 113 | timing | …run manifests record it as applied; it is a documented timing null rather than a fit improvement: a pre-fold-in abla… | NEW round 15 - documented timing-null reference, no credential attached |
| docx | 113 | lead | …$3-month window exceeding the +0.19 at the three-month lead. (A fifty-seed Monte Carlo re-draw under the same spec… | RETAINED - raw correlogram / convention bookkeeping, guarded in-line |
| docx | 117 | timing | …tes on the level of simulated mobility rather than its timing. Full mechanism-level detail for each extension is rep… | RETAINED - ABM mechanism description, hedged in-line |
| docx | 117 | lead | …he $\pm$3-month window (the $+0.19$ at the three-month lead noted above) is weak and statistically indistinguishab… | NEW round 15 - ABM mechanism description, hedged in-line |
| docx | 179 | offset | / $n_{s,t}$ / UPB exposure (log offset) / dollars / A / | NEW round 15 - econometric term of art (log-exposure offset) |
| docx | 207 | offset | / Outcome; estimation / prepaid UPB with log-exposure offset; Poisson pseudo-maximum likelihood, log link (2) / mon… | NEW round 15 - econometric term of art (log-exposure offset) |
| docx | 219 | offset | …he model is a discrete-time hazard with a log-exposure offset, | RETAINED - econometric term of art |
| docx | 223 | nonnegative | …led object is the prepayment rate $y_{s,t}/n_{s,t}$, a nonnegative fraction, so the model is estimated by Poisson pseudo-… | NEW round 15 - econometric term of art |
| docx | 223 | offset | …outcome is dollars, not a count: with the log-exposure offset the modeled object is the prepayment rate $y_{s,t}/n_{… | RETAINED - econometric term of art |
| docx | 255 | timing | …ecovery as evidence about the aggregate level only. No timing claim rests on Path B either: its apparent levels adva… | RETAINED - states the retraction / carries the guard |
| docx | 281 | offset | …quivalent units, so that the buyback discount properly offsets the locked-in spread; $g_{\mathrm{DK}} = g_{\mathrm{US… | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| docx | 291 | ahead | …SOMA-derived CPR path moves approximately three months ahead of the simulated path (a peak selected across the seve… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 291 | trails | …plementation a peak at $k=-3$ means the simulated path trails the empirical path by three months: the empirical seri… | NEW round 15 - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 291 | moves first | …e empirical path by three months: the empirical series moves first. At this peak, the empirical SOMA-derived CPR path mov… | NEW round 15 - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 291 | lags | …ulated path (a peak selected across the seven examined lags, so its nominal significance overstates; no inference … | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 293 | timing | …he level validates the elasticity's magnitude. But the timing is not part of that evidence: as Section V.E reports, … | NEW round 15 - states the retraction / carries the guard |
| docx | 293 | lead | …elasticity set to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from t… | RETAINED - states the retraction / carries the guard |
| docx | 293 | lead | …t to zero reproduces the same three-month lead, so the lead cannot discriminate the elasticity from the mechanical… | RETAINED - states the retraction / carries the guard |
| docx | 297 | timing | …e therefore attach no settlement interpretation to the timing alignment. | RETAINED - states the retraction / carries the guard |
| docx | 297 | offset | …three months later, predicts the opposite direction of offset. We therefore attach no settlement interpretation to t… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 297 | moves first | … (verified against synthetic data), the empirical path moves first: a settlement-delay mechanism, in which loan-level pre… | RETAINED - direction-check / raw correlogram description, guarded in-line by the adjacent retraction |
| docx | 299 | timing | A direct input-timing diagnosis rules out the dating of the rate input and n… | RETAINED - input-timing diagnosis description, credential-free |
| docx | 301 | timing | …nction is the accuracy of its aggregate level, not its timing. (In levels, which are trend-contaminated over the win… | RETAINED - states the retraction / carries the guard |
| docx | 301 | lead | …ag 0 (it reaches $-1$ under a two-to-three-month input lead) while moving recovered trapped liquidity by less than… | NEW round 15 - input-shift scan bookkeeping, credential-free |
| docx | 301 | offset | …ath is contemporaneous.) No single channel carries the offset: the $\beta_b = 0$ and $\beta_1 = 0$ ablations both le… | RETAINED - mechanism-not-isolated statement, credential-free |
| docx | 301 | offset | … by less than $1.5 billion across the entire scan. The offset is therefore a property of the fitted path's smooth ag… | RETAINED - mechanism-not-isolated statement, credential-free |
| docx | 303 | lead | ….C), a peak at negative lag means the empirical series leads and the simulated path trails. Path B's $-3$/$-4$ peak… | NEW round 15 - raw correlogram / convention bookkeeping, guarded in-line |
| docx | 303 | trails | …eans the empirical series leads and the simulated path trails. Path B's $-3$/$-4$ peak and Path A's and the ABM's ne… | NEW round 15 - direction-check / verified convention statement (empirical leads, sim trails); part of the settled retraction |
| docx | 303 | lags | …imulated CPR path and the empirical SOMA-derived path, lags $-6$ to $+6$. Under the implemented convention (Sectio… | NEW round 15 - lag-window convention bookkeeping (lags -6 to +6) |
| docx | 305 | lags | … the lag-0 correlation at $[-0.13, +0.44]$; with seven lags searched, individual band-point differences in peak $r… | NEW round 15 - lag-search bookkeeping |
| docx | 313 | timing | … is comparable in size to the marginal itself. Second, timing carries no credential: the $\beta_1 = 0$ null also pea… | NEW round 15 - no-credential guard statement (round-15/Q10 material) |
| docx | 313 | lead | …= 0$ null also peaks at lag $-3$ (Section V.E), so the lead cannot discriminate the elasticity from the mechanical… | NEW round 15 - states the retraction / carries the guard |
| docx | 335 | path diagnostics | …ed liquidity / % of benchmark / CPR path corr. (lag) / Path diagnostics / | NEW round 15 - table column header, no claim |
| docx | 340 | lead | ….76%; $r = +0.190$ at lag 0; 3-month offset (empirical leads; reference only, Section V.C) / | RETAINED - states the retraction / carries the guard |
| docx | 340 | offset | …$-3$) / mean CPR 4.76%; $r = +0.190$ at lag 0; 3-month offset (empirical leads; reference only, Section V.C) / | RETAINED - states the retraction / carries the guard |
| docx | 346 | timing | …ation choices; neither reproduces the empirical path's timing (no estimator does; see above), but the recalibrated v… | RETAINED - states the retraction / carries the guard |
| docx | 346 | timing | …rs cluster at $-0.20$ to $-0.30$; Section V.C), and no timing evidence is claimed for any estimator. | NEW round 15 - states the retraction / carries the guard |
| docx | 362 | timing | …ication we tested lands within 45% of it. We attach no timing credential to this: Path B's raw $+0.190$ lag-0 correl… | NEW round 15 - states the retraction / carries the guard |
| docx | 362 | timing | …tervals of Table 8 counsel against weighing any single timing coefficient, including Path B's lag $-3$ peak, whose i… | RETAINED - states the retraction / carries the guard |
| docx | 362 | timing | …ing Path B's lag $-3$ peak, whose interval spans zero. Timing alone, however, does not identify the lock-in channel:… | NEW round 15 - states the retraction / carries the guard |
| docx | 369 | timing | … remain candidates for the modest residual and for the timing failure every estimator shares, not demonstrated drive… | NEW round 15 - shared-timing-failure candidates framing, explicitly hedged in-line ('candidates ... not demonstrated drivers') |
| docx | 414 | timing | …ve, so neither variant reproduces the empirical path's timing regardless of calibration choice, and after Section V.… | NEW round 15 - states the retraction / carries the guard |
| docx | 426 | lead | … $+0.195$ at lag $-3$, the "$+0.19$ at the three-month lead" of Section IV.A; the two conventions summarize the sa… | NEW round 15 - raw correlogram / convention bookkeeping, guarded in-line |
| docx | 432 | timing | …tion V.C); Path B's distinction is level accuracy, not timing. The timing critique of Section IV therefore survives … | RETAINED - open-question statement, credential-free |
| docx | 432 | timing | …ath B's distinction is level accuracy, not timing. The timing critique of Section IV therefore survives regardless o… | RETAINED - open-question statement, credential-free |
| docx | 436 | timing | …h paradigms still depend on real structure for correct timing. We treat the aggregate-level paradigm claim of Sectio… | RETAINED - open-question statement, credential-free |
| docx | 477 | offset | …equivalent units so that the buyback discount properly offsets the locked-in spread (a correction live in the mechani… | RETAINED - Danish NPV identity (mechanism-substitution variant, scoped as non-production in round 9) |
| docx | 504 | timing | …nding within 2.1% (a level-accuracy distinction, not a timing one: no estimator's monthly co-movement survives detre… | NEW round 15 - states the retraction / carries the guard |
| docx | 504 | timing | …ly attributed to modeling paradigm; and the path-level timing question remains open for every estimator. | NEW round 15 - states the retraction / carries the guard |
| docx | 522 | timing | … matching its real-data recovery, while its path-level timing does not transfer to synthetic data. Also complete as … | RETAINED - open-question statement, credential-free |
| docx | 522 | timing | … the Danish counterfactual's description; and (iv) the timing-sweep generator's golden-fixture test (tools/test_timi… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| docx | 522 | timing | …ming-sweep generator's golden-fixture test (tools/test_timing_sweep.py) must pass at the freeze, three matcher gener… | RETAINED - process/tooling reference (freeze-gate item name), not a timing claim |
| docx | 522 | timing | …Section III.C); and the monthly-frequency question the timing diagnosis leaves (the empirical path's variation at th… | RETAINED - open-question statement, credential-free |
| docx | 524 | timing | …er than to calibration and data source; the path-level timing question remains genuinely open for every estimator. T… | NEW round 15 - open-question statement, credential-free |
| docx | 529 | offset | …them under fixed seeds (engine seed 42 with per-regime offsets; every post-freeze run's specification is fixed ex ant… | NEW round 15 - RNG per-regime seed-offset description, no timing content |
| docx | 675 | ahead | …. Balance sheet reduction: Progress to date and a look ahead. Remarks at the 2024 Annual Primary Dealer Meeting, Fe… | NEW round 15 - reference title (Perli 2024 'a look ahead'), not manuscript prose |

Total: 111 rows. Tally (computed from table rows): {'NEW round 15 (dispositioned)': 45, 'RETAINED': 66}.
