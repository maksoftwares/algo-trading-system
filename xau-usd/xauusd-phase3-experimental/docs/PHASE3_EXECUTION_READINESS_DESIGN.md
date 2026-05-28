# Phase 3 Execution Readiness Design

Status: REVIEW_READY_EXPERIMENTAL

This is a design target for a future Phase 3 if Phase 2 later passes. It is not an implementation authorization.

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

## Lifecycle

| State | Meaning |
| --- | --- |
| `EXPERIMENT_ONLY` | Repo-only simulation, current state. |
| `PAPER_ELIGIBLE_DESIGN` | Design may be reused after Phase 2 PASS. |
| `PAPER_SHADOW` | Future paper-mode shadow state, not active now. |
| `MICRO_READY_REVIEW` | Future readiness state after paper evidence. |
| `SUSPENDED` | Edge family blocked by cost, drift, or owner lock. |

## Future Paper Shadow Scope

The first real reuse of this design, after Phase 2 passes, must be paper-shadow only:

| Area | Rule |
| --- | --- |
| Account impact | None. |
| Live capital | Not allowed. |
| Broker-side order placement | Not allowed in this Phase 3 design package. |
| Primary stream | `breakout_retest` only unless a later approval explicitly changes this. |
| Same-family variants | Observer-only until separate paper evidence proves they add value. |
| Cost state | Family-level. If the family is suspended, all same-family variants inherit suspension. |
| Ledger | Every would-open, block, cost state, and family decision must be written to a paper-shadow ledger. |

## Kill Rules

| Rule | Experimental trigger |
| --- | --- |
| Cost floor | Net expectancy after measured-cost proxy below `+0.15R`. |
| Safety boundary | Any source row not `dry_run=true` and `trade_permission=false`. |
| Clock health | Source server-time state not `CLOCK_OK`. |
| Execution health | Source execution state not `EXECUTION_OK`. |
| Family state | Breakout-retest family remains cost-revalidation-pending in the real project. |

## Cost-Aware Entry Rules

These rules are design requirements copied from the current Phase 3 evidence. They are not live execution permission.

| Rule | Initial value | Reason |
| --- | --- | --- |
| Minimum expected net after cost | `+0.15R` | Preserves the already accepted continuation floor. |
| Cost-watch threshold | Net after cost below Phase 0 baseline `+0.1888R` | Flags erosion before hard suspension. |
| Suspend threshold | Net after cost below `+0.15R` | Family must not be promoted while below floor. |
| Cost-in-R review caps | `0.20R`, `0.25R`, `0.30R`, `0.35R` | Used to stress possible paper blocking choices. |
| Tight-stop review bucket | Stop distance `<250` points | Current evidence shows this bucket is cost dominated. |
| Spread regime reference | Median `50` points, P95 `75` points in current Phase 3 ledger | Used only as offline design evidence until measured cost passes. |

## Observer And Family Rules

| Rule | Required behavior |
| --- | --- |
| Family de-duplication | Same-bar same-family observations collapse to one family event for review. |
| Primary execution eligibility | Only rows with `primary_stream_allowed=true` may ever become paper-shadow candidates. |
| Observer duplicates | Must never create additional exposure. |
| Direction conflicts | Must force `NO_TRADE_REVIEW_REQUIRED` until manually resolved. |
| Distinct same-bar levels | Must remain review-only unless a later spec defines portfolio handling. |
| Provisional candidates | Excluded from the paper-shadow ledger until independently promoted. |

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

After those gates pass, this design can only move to `PAPER_ELIGIBLE_DESIGN`. It still cannot move directly to broker-side execution or live trading.

## Paper-To-Micro Promotion Criteria

This design can move from paper-shadow evidence to a later micro-ready review only if all rows below are satisfied in a future paper phase.

| Gate | Required result |
| --- | --- |
| Paper runtime span | At least 20 active market days. |
| Paper event count | At least 100 primary family paper-shadow events, or a documented lower-count waiver. |
| Paper measured net | Median net after measured paper cost remains `>= +0.15R`. |
| Cost tail | P95 cost mode does not make median net negative. |
| Kill-state rate | `SUSPEND_FAMILY` rows remain explainable and below a separately approved cap. |
| Observer duplication | Duplicate observer rows do not add exposure. |
| Drift | Trade frequency, spread state, and signal distribution stay within approved review bands. |
| Operations | Restart, logging, owner lock, and emergency stop checks pass. |
| Owner approval | Explicit approval for micro-ready review, not live capital. |

## Rollback Criteria

Any future Phase 3 implementation must be rolled back or suspended if cost, drift, safety, or owner controls fail.

| Trigger | Required response |
| --- | --- |
| Measured net below `+0.15R` | Set family state to `SUSPENDED`. |
| Any broker-action path appears before authorization | Stop implementation and fail safety review. |
| `trade_permission=true` appears outside the approved phase | Stop and investigate. |
| Server time not `CLOCK_OK` | Block paper-shadow event and log clock fault. |
| Execution state not `EXECUTION_OK` | Block paper-shadow event and log execution fault. |
| Unexpected observer conflict | Block family event and require review. |
| Owner manual lock | Suspend all family events. |
| Missing ledger write | Stop promotion clock until logging is restored. |
