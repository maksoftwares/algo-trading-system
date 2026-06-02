# Phase 2 Resolution Plan

Status: ACTIVE

This plan locks the current Phase 2 decision after measured-cost revalidation failed for the breakout-retest family.

## Canonical Decision

| Lane | Decision |
| --- | --- |
| Phase 1 dry-run acceptance | PASS |
| Continue Phase 1 telemetry/spread logging | GO |
| Continue Phase 0R replacement research | GO |
| Continue Phase 2 documentation/prep | LIMITED GO |
| Canonical Phase 2 paper-mode implementation | NO-GO |
| Canonical broker-side execution | NO-GO |
| Demo execution as Phase 2 evidence | NO-GO |
| Live trading / real capital | ABSOLUTE NO-GO |
| Experimental demo executor lane | QUARANTINE / REVIEW ONLY |

## Required State

```text
PHASE2_CANONICAL_STATUS = BLOCKED_BY_MEASURED_COST
BREAKOUT_RETEST_FAMILY_STATUS = COST_SUSPENDED_CANONICAL
EXPERIMENTAL_DEMO_EXECUTOR_STATUS = QUARANTINE_REVIEW_ONLY
```

## Evidence

The measured-cost model is PASS, but `BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` is FAIL, `MEASURED_COST_ASSUMPTION_DELTA.md` is FAIL, and `MEASURED_COST_REVALIDATION_SANITY_CHECK.md` is `CALCULATION_CONFIRMED`.

That means the current failure is treated as real unless a future reproducible forensic audit proves a calculation, unit-conversion, data-freshness, or symbol-specification bug.

## Resolution Tracks

| Track | Purpose | Boundary |
| --- | --- | --- |
| Phase 2A measured-cost forensics | Confirm whether the failure is reproducible | Does not authorize Phase 2 |
| Phase 2B passive paper observer | Observe would-signal cost_R without orders | No `OrderSend`, no broker execution |
| Phase 0R replacement research | Find lower-cost, wider-stop candidates | New locked hypotheses only |
| Phase 2Q experimental quarantine | Keep owner-requested demo execution isolated | Not canonical evidence |

## Reopening Criteria

Canonical Phase 2 can be reconsidered only if one path is satisfied:

| Path | Required evidence |
| --- | --- |
| Cost bug found and fixed | forensic bug proof, regenerated measured-cost artifacts, reviewer acceptance |
| New candidate passes | locked hypothesis, cost feasibility PASS, Phase 0 PASS, measured-cost revalidation PASS, owner approval |
| Broker cost improves | 5 fresh observed market days from intended execution environment, measured-cost revalidation PASS |

Do not weaken gates, do not add rescue filters to `breakout_retest_v1.0`, and do not treat experimental demo PnL as Phase 2 evidence.
