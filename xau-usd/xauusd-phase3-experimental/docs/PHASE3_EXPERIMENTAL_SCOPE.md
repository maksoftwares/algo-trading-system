# Phase 3 Experimental Scope

Status: EXPERIMENTAL_ACTIVE

This document defines the experimental Phase 3 lane requested by the owner while Phase 2 evidence continues to mature.

## Assumption

For design purposes only, this sandbox assumes:

```text
Phase 2 objective gates eventually pass.
```

That assumption is not written back into the real readiness reports. `PHASE2_READINESS_REPORT.md` remains the authority for the real project.

## Allowed Work

| Area | Allowed |
| --- | --- |
| Offline ledgers | Yes |
| Cost-survival simulation | Yes |
| Risk/kill-rule design | Yes |
| Promotion and rollback criteria | Yes |
| Docs and tests | Yes |
| MT5 deployment | No |
| Broker-action code | No |
| Live or paper account state changes | No |

## Inputs

| Input | Use |
| --- | --- |
| Phase 1 would-signal review CSV | Source of dry-run candidate events. |
| Phase 1 status summary | Confirms dry-run and permission boundary. |
| Phase 2 readiness report | Preserved as PENDING until real gates pass. |
| Measured-cost reports | Used only as context; no gate is force-passed here. |

## Outputs

| Output | Purpose |
| --- | --- |
| `PHASE3_EXPERIMENTAL_LEDGER.csv` | Offline event ledger built from already-blocked Phase 1 decisions. |
| `PHASE3_EXPERIMENTAL_SIMULATION.md` | Human-readable simulation summary. |
| `PHASE3_EXPERIMENTAL_STATUS.json` | Machine-readable status for the dashboard. |
| `PHASE3_EXPERIMENTAL_STATUS.md` | Reviewer-facing status summary. |

## Non-Negotiable Boundary

If a future implementation is copied from this sandbox into the real system, it must first pass the real Phase 2 gates and go through a separate implementation review.
