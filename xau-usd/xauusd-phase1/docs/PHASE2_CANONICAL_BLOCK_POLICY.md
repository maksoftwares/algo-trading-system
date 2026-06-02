# Phase 2 Canonical Block Policy

Status: ACTIVE

Canonical Phase 2 is blocked whenever measured-cost revalidation is not PASS for the candidate/family intended for execution.

## Rules

```text
if measured_cost_revalidation.status != PASS:
    canonical_phase2_authorized = false
```

```text
if candidate_family_status == COST_SUSPENDED_CANONICAL:
    paper_mode_execution_allowed = false
    demo_execution_as_phase2_evidence_allowed = false
    live_execution_allowed = false
```

Experimental demo fills, logs, or PnL cannot override `PHASE2_READINESS_REPORT.md`, measured-cost revalidation, measured-cost assumption delta, cost suspension decisions, or owner approval gates.

## Current Lock

| Field | Value |
| --- | --- |
| canonical_phase2_status | BLOCKED_BY_MEASURED_COST |
| breakout_retest_family_status | COST_SUSPENDED_CANONICAL |
| measured_cost_model_status | PASS |
| measured_cost_revalidation_status | FAIL |
| measured_cost_sanity_status | CALCULATION_CONFIRMED |
| experimental_demo_executor_status | QUARANTINE_REVIEW_ONLY |
| demo_execution_as_phase2_evidence | false |
| live_trading_authorized | false |

## Same-Family Boundary

`breakout_retest`, `swing_breakout_retest_v0`, `symbol_normalized_round_retest_v0`, `quarter_round_retest_v0`, `round_number_retest_v0`, `session_extreme_retest_v0`, and future level/retest variants are one correlated family for execution governance.
