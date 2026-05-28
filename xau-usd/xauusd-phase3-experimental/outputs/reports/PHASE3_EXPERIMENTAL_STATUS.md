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
| Latest Phase 1 bar | 2026.05.27 22:05:00 |
| Latest Phase 1 dry run | true |
| Latest Phase 1 trade permission | false |

## Experimental Simulation

| Field | Value |
| --- | --- |
| Accepted events | 89 |
| Raw observer events | 89 |
| Family unique events | 49 |
| Observer duplicates | 40 |
| Observer conflicts | 0 |
| Rejected source rows | 2 |
| Cost mode | entry_exit_proxy |
| Gross expectancy R source | fixed_notional_phase0_baseline |
| Baseline assumed cost R | 0.3228 |
| Baseline net expectancy R | 0.1888 |
| Median proxy cost R | 0.2554 |
| Median net after proxy cost R | 0.2562 |
| Median net delta vs assumed baseline R | 0.0674 |
| Minimum net expectancy R | 0.15 |

## Safety And Manifest

| Field | Value |
| --- | --- |
| Safety status | PASS |
| Safety findings | 0 |
| Suspend review status | REVIEW_READY |
| Suspend unique family events | 11 |
| Suspend primary rows | 11 |
| Cost-mode comparison | REVIEW_READY |
| Stress suspend family events | 46 |
| Cost-gate review | REVIEW_READY |
| Cost-gate 0.25R blocked families | 28 |
| Spread P95 points | 75.0 |
| Kill-state summary | {'COST_WATCH': 2, 'NORMAL': 36, 'SUSPEND_FAMILY': 11} |
| De-dup audit | REVIEW_READY |
| De-dup classifications | {'TRUE_DUPLICATE': 49} |
| Manifest status | DIRTY_WORKTREE |
| Manifest commit | 10d18ef |
