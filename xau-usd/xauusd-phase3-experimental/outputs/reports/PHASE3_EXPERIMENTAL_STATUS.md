# Phase 3 Experimental Status

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: EXPERIMENTAL_COST_SUSPEND_SCENARIO

## Boundary

- Real Phase 2 remains governed by `PHASE2_READINESS_REPORT.md`.
- This sandbox assumes Phase 2 PASS for design only.
- MT5 runtime was not touched.
- Broker-action code is not allowed.
- This experiment is excluded from the owner approval flow for real Phase 2 or real Phase 3.

## Current Real Gate State

| Field | Value |
| --- | --- |
| Phase 1 acceptance | PENDING |
| Phase 2 readiness | PENDING |
| Latest Phase 1 bar | 2026.05.28 11:25:00 |
| Latest Phase 1 dry run | true |
| Latest Phase 1 trade permission | false |

## Experimental Simulation

| Field | Value |
| --- | --- |
| Accepted events | 108 |
| Raw observer events | 108 |
| Family unique events | 61 |
| Observer duplicates | 47 |
| Observer conflicts | 0 |
| Rejected source rows | 2 |
| Cost mode | entry_exit_proxy |
| Gross expectancy R source | fixed_notional_phase0_baseline |
| Baseline assumed cost R | 0.3228 |
| Baseline net expectancy R | 0.1888 |
| Median proxy cost R | 0.2452 |
| Median net after proxy cost R | 0.2664 |
| Median net delta vs assumed baseline R | 0.0776 |
| Minimum net expectancy R | 0.15 |

## Safety And Manifest

| Field | Value |
| --- | --- |
| Safety status | PASS |
| Safety findings | 0 |
| Suspend review status | REVIEW_READY |
| Suspend unique family events | 12 |
| Suspend primary rows | 12 |
| Suspend decision | REVIEW_READY_KEEP_SUSPENDED |
| Keep-suspended primary rows | 12 |
| Cost-mode comparison | REVIEW_READY |
| entry_exit_proxy median net R | 0.2664 |
| p95_fresh_proxy median net R | 0.1829 |
| stress_2x_p95_proxy median net R | -0.1253 |
| entry_exit_proxy SUSPEND_FAMILY rows | 22 |
| p95_fresh_proxy SUSPEND_FAMILY rows | 48 |
| stress_2x_p95_proxy SUSPEND_FAMILY rows | 98 |
| Stress suspend family events | 55 |
| Cost-gate review | REVIEW_READY |
| Cost-gate 0.25R blocked families | 30 |
| Spread P95 points | 75.0 |
| Kill-state summary | {'COST_WATCH': 2, 'NORMAL': 47, 'SUSPEND_FAMILY': 12} |
| De-dup audit | REVIEW_READY |
| De-dup classifications | {'SAME_BAR_DISTINCT_LEVEL': 1, 'TRUE_DUPLICATE': 60} |
| Paper-shadow status | SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS |
| Paper-shadow would-open | 49 |
| Paper-shadow cost-review opens | 2 |
| Paper-shadow blocked suspend | 12 |
| Paper-shadow observer no-exposure | 47 |
| Paper-shadow monthly estimate | 246.28 |
| Completion audit | REPO_SIDE_COMPLETE_WAITING_REAL_GATES |
| Phase 3 repo complete | True |
| Demo authorized | False |
| External blockers | 10 |
| Manifest status | PASS |
| Manifest commit | ccf6bee |
