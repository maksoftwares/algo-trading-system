# Phase 0 Reality Check Interpretation

Overall status: D2_PASS_VIA_ACCEPTED_FAMILY_METHOD

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
| Does current D2 invalidate `breakout_retest` as the selected Phase 2 candidate? | No. Candidate-level D2 remains FAIL, but owner accepted the family-clustered method, so D2 no longer blocks Phase 2 readiness. |
| Should same-family candidates be consolidated before D2? | Only after a written method decision. Same-family consolidation is statistically defensible for portfolio-family questions, but using it after seeing a failing individual-candidate D2 would be a process change requiring explicit approval. |
| What exact gate must be PASS before Phase 2 readiness can pass? | This is now satisfied by accepted `D2_FAMILY_CLUSTERED_V0` PASS. Other non-D2 readiness gates still must pass. |

## Method Decision

`docs/D2_METHOD_DECISION_2026_05_27.md` keeps the current fixed-notional candidate-level D2 report as preserved evidence and accepts `D2_FAMILY_CLUSTERED_V0` as the project-level D2 readiness method.

## Family-Clustered Diagnostic

`outputs/reports/PHASE0_REALITY_CHECK_FAMILY_CLUSTERED.md` now reports `PASS`. The breakout-retest family remained the winner with White Reality Check p-value 0.0002 and max pairwise SPA p-value 0.0002 across 62 family representatives. Owner acceptance is recorded, so D2 no longer blocks Phase 2 readiness.

## Interpretation

`breakout_retest` remains the best-performing candidate in the fixed-notional monthly R-series universe, and the White Reality Check result remains strong. The blocker is narrower: the expanded universe now includes highly related retest variants that are close enough to fail the stricter SPA threshold of 0.01.

That should be read as a same-family selection ambiguity, not as proof that the breakout-retest family has no edge. The accepted family-clustered method resolves the Phase 2 D2 gate while preserving the candidate-level FAIL for audit history.

## Phase Boundary

- Phase 1 dry-run may continue.
- Passive spread logging may continue.
- No paper-mode broker execution is authorized.
- No same-family variant may be counted as diversification.
- No live trading is authorized.
