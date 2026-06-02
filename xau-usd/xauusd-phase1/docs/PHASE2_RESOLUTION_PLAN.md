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

The experimental demo broker ledger now has an early review note: `xau-usd/xauusd-phase1/docs/PHASE2_ACTUAL_BROKER_TRADE_REVIEW_2026_06_02.md`. The accepted-only deduplicated broker sample is positive, while `session_extreme_retest_v0` is the main drag. This is review-only evidence and does not reopen canonical Phase 2 by itself.

## Resolution Tracks

| Track | Purpose | Boundary |
| --- | --- | --- |
| Phase 2A measured-cost forensics | Confirm whether the failure is reproducible | Does not authorize Phase 2 |
| Phase 2B passive paper observer | Observe would-signal cost_R without orders | No `OrderSend`, no broker execution |
| Phase 0R replacement research | Find lower-cost, wider-stop candidates | New locked hypotheses only |
| Phase 2Q experimental quarantine | Keep owner-requested demo execution isolated | Not canonical evidence |

## Phase 2B Passive Observer Tooling

| Artifact | Purpose | Current state |
| --- | --- | --- |
| `docs/PHASE2B_PASSIVE_OBSERVER_SAMPLE_REQUIREMENTS.md` | Minimum sample standard for passive cost feasibility. | ACTIVE |
| `scripts/generate_phase2b_passive_observer_reports.py` | Generates the Phase 2B cost, stop-distance, spread-regime, session, hour, and candidate-decision reports. | IMPLEMENTED |
| `outputs/reports/PHASE2B_COST_FEASIBILITY_REPORT.md` | Current passive cost feasibility report. | PENDING; no passive observer rows yet |
| `outputs/reports/PHASE2B_CANDIDATE_FEASIBILITY_DECISION.md` | Candidate-level passive read. | PENDING; no passive observer rows yet |

Phase 2B reports read `outputs/paper_observer/passive_cost_observer_log.csv` only. They do not read experimental demo order logs and cannot authorize Phase 2.

## Boundary Validators

| Script | Required result | Purpose |
| --- | --- | --- |
| `scripts/verify_no_cost_suspended_family_promotion.py` | PASS | Fails if a `COST_SUSPENDED_CANONICAL` family is promoted to execution eligibility, paper-mode approval, demo-evidence approval, live approval, or diversification eligibility. |
| `scripts/verify_phase3_proxy_non_authoritative.py` | PASS | Fails if Phase 3 proxy evidence is used to set Phase 2 readiness, owner approval, paper-mode execution, or canonical authorization. |

Latest expected generated outputs:

```text
outputs/reports/COST_SUSPENDED_PROMOTION_BLOCKER_REPORT.md = PASS
outputs/reports/PHASE3_PROXY_NON_AUTHORITATIVE_VERIFICATION.md = PASS
```

## New Candidate Draft

The current draft for a future cost-aware candidate is `xau-usd/xauusd-phase0/docs/hypothesis_breakout_retest_cost_aware_v2_DRAFT.md`. It is not hash-locked and is not approved for matrix testing until humans review and finalize it.

## Reopening Criteria

Canonical Phase 2 can be reconsidered only if one path is satisfied:

| Path | Required evidence |
| --- | --- |
| Cost bug found and fixed | forensic bug proof, regenerated measured-cost artifacts, reviewer acceptance |
| New candidate passes | locked hypothesis, cost feasibility PASS, Phase 0 PASS, measured-cost revalidation PASS, owner approval |
| Broker cost improves | 5 fresh observed market days from intended execution environment, measured-cost revalidation PASS |

Do not weaken gates, do not add rescue filters to `breakout_retest_v1.0`, and do not treat experimental demo PnL as Phase 2 evidence.
