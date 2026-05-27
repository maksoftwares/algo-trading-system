# Phase 0 Reality Check Interpretation

Overall status: BLOCKING_REVIEW_REQUIRED

Generated at UTC: 2026-05-27

## Current D2 Result

| Field | Value |
| --- | --- |
| Canonical report | `outputs/reports/PHASE0_REALITY_CHECK.md` |
| Report status | FAIL |
| Approved expert under test | `breakout_retest` |
| Non-empty candidate universe | 66 |
| Winner | `breakout_retest` |
| White Reality Check p-value | 0.0002 |
| Effective accepted p-value | 0.01 |
| Max pairwise SPA p-value | 0.0174 |
| Failing alternatives | `round_number_retest_v0`, `symbol_normalized_round_retest_v0` |

## Required Questions

| Question | Answer |
| --- | --- |
| Is D2 failing because another same-family variant is statistically close to `breakout_retest`? | Yes. The failing SPA alternatives are same-family level/retest variants, not independent diversification candidates. |
| Should D2 be evaluated at family level instead of individual candidate level? | Possibly, but not retroactively. A family-clustered D2 method would need to be pre-registered, reviewer-visible, and rerun as a new canonical statistical decision. |
| Does current D2 invalidate `breakout_retest` as the selected Phase 2 candidate? | It blocks Phase 2 readiness. It does not invalidate Phase 1 dry-run observation, but it means the individual-candidate D2 gate is not currently PASS. |
| Should same-family candidates be consolidated before D2? | Only after a written method decision. Same-family consolidation is statistically defensible for portfolio-family questions, but using it after seeing a failing individual-candidate D2 would be a process change requiring explicit approval. |
| What exact gate must be PASS before Phase 2 readiness can pass? | Either the current individual-candidate D2 report returns PASS, or a pre-registered family-clustered D2 interpretation is approved and its rerun returns PASS. Until then, `PHASE2_READINESS_REPORT.md` must keep D2 as FAIL. |

## Interpretation

`breakout_retest` remains the best-performing candidate in the fixed-notional monthly R-series universe, and the White Reality Check result remains strong. The blocker is narrower: the expanded universe now includes highly related retest variants that are close enough to fail the stricter SPA threshold of 0.01.

That should be read as a same-family selection ambiguity, not as proof that the breakout-retest family has no edge. It also should not be softened into a PASS. For Phase 2 purposes, the current statistical gate remains failed until the project chooses and documents a valid D2 rule.

## Phase Boundary

- Phase 1 dry-run may continue.
- Passive spread logging may continue.
- No paper-mode broker execution is authorized.
- No same-family variant may be counted as diversification.
- No live trading is authorized.
