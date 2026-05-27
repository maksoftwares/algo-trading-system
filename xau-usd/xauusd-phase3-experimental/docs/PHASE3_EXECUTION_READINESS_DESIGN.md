# Phase 3 Execution Readiness Design

Status: DRAFT_EXPERIMENTAL

This is a design target for a future Phase 3 if Phase 2 later passes. It is not an implementation authorization.

## Lifecycle

| State | Meaning |
| --- | --- |
| `EXPERIMENT_ONLY` | Repo-only simulation, current state. |
| `PAPER_ELIGIBLE_DESIGN` | Design may be reused after Phase 2 PASS. |
| `PAPER_SHADOW` | Future paper-mode shadow state, not active now. |
| `MICRO_READY_REVIEW` | Future readiness state after paper evidence. |
| `SUSPENDED` | Edge family blocked by cost, drift, or owner lock. |

## Kill Rules

| Rule | Experimental trigger |
| --- | --- |
| Cost floor | Net expectancy after measured-cost proxy below `+0.15R`. |
| Safety boundary | Any source row not `dry_run=true` and `trade_permission=false`. |
| Clock health | Source server-time state not `CLOCK_OK`. |
| Execution health | Source execution state not `EXECUTION_OK`. |
| Family state | Breakout-retest family remains cost-revalidation-pending in the real project. |

## Promotion Criteria

Phase 3 experimental work can only be considered for real implementation after:

| Gate | Required result |
| --- | --- |
| Phase 1 acceptance | PASS |
| Phase 2 readiness | PASS |
| Measured-cost model | PASS |
| Measured-cost revalidation | PASS |
| VPS latency evidence | PASS |
| Owner approval | Signed and explicit |
| Safety audit | PASS |

## Rollback Criteria

Any future Phase 3 implementation must be rolled back or suspended if cost, drift, safety, or owner controls fail.
