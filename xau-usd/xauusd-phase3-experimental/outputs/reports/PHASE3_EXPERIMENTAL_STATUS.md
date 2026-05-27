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
| Latest Phase 1 bar | 2026.05.27 19:20:00 |
| Latest Phase 1 dry run | true |
| Latest Phase 1 trade permission | false |

## Experimental Simulation

| Field | Value |
| --- | --- |
| Accepted events | 87 |
| Raw observer events | 87 |
| Family unique events | 47 |
| Observer duplicates | 40 |
| Observer conflicts | 0 |
| Rejected source rows | 2 |
| Cost mode | entry_exit_proxy |
| Median proxy cost R | 0.2554 |
| Median net after proxy cost R | 0.2562 |
| Minimum net expectancy R | 0.15 |

## Safety And Manifest

| Field | Value |
| --- | --- |
| Safety status | PASS |
| Safety findings | 0 |
| Manifest status | PASS |
| Manifest commit | eb9c667 |
