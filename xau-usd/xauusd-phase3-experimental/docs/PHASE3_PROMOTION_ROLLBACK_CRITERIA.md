# Phase 3 Promotion And Rollback Criteria

Status: REVIEW_READY_EXPERIMENTAL

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

## Purpose

This document converts the Phase 3 experimental findings into future promotion and rollback rules. It is a design artifact only. It does not authorize demo, paper, broker-side, or live execution.

## Promotion Ladder

| Step | State | Required evidence |
| --- | --- | --- |
| 1 | `EXPERIMENT_ONLY` | Current repo-only Phase 3 sandbox. |
| 2 | `PAPER_ELIGIBLE_DESIGN` | Phase 1 acceptance PASS, Phase 2 readiness PASS, measured-cost revalidation PASS, VPS evidence PASS, owner approval signed. |
| 3 | `PAPER_SHADOW` | Paper-shadow ledger implementation reviewed, safety audit PASS, no broker-action path, owner approves paper-only observation. |
| 4 | `MICRO_READY_REVIEW` | Future paper-shadow evidence passes cost, drift, logging, restart, and owner-review gates. |
| 5 | `SUSPENDED` | Any cost, safety, drift, or owner-lock trigger fails. |

## Phase 3 Entry Criteria

Phase 3 can be considered real only after every gate below is already PASS:

| Gate | Required result |
| --- | --- |
| Phase 1 acceptance | PASS |
| Phase 2 readiness | PASS |
| Measured-cost model | PASS |
| Measured-cost revalidation | PASS with net expectancy `>= +0.15R` |
| Measured-cost assumption delta | PASS |
| VPS selection | PASS |
| VPS latency evidence | PASS |
| Owner approval | Signed and explicitly paper/demo scoped |
| Source safety audit | PASS |
| Phase 3 manifest | PASS |

## Future Paper-Shadow Acceptance Gates

| Gate | Required result |
| --- | --- |
| Paper-shadow duration | At least 20 active market days. |
| Primary family paper events | At least 100, unless owner accepts a documented lower-count waiver. |
| Median measured paper net | `>= +0.15R`. |
| P95-cost stress | Must not make median net negative. |
| Suspend-family review | All `SUSPEND_FAMILY` rows classified and explained. |
| Duplicate observer handling | Same-family duplicates create no extra exposure. |
| Runtime safety | Dry-run/paper locks remain correct. |
| Logging | Paper ledger has one complete row for every candidate event/block. |
| Restart behavior | Restart does not corrupt ledgers or reset state incorrectly. |
| Owner approval | Separate approval for any later micro review. |

## Cost Blocks To Carry Forward

| Rule | Future implementation requirement |
| --- | --- |
| Cost floor | Block family if projected/measured net after cost is `< +0.15R`. |
| Cost watch | Flag family if projected/measured net after cost is below `+0.1888R`. |
| Tight stop guard | Review or block stops below `250` points until paper evidence proves survival. |
| Wide spread guard | Review or block events where spread regime is near or above P95. |
| Duplicate guard | Observer duplicate rows cannot create independent paper events. |
| Conflict guard | Direction conflicts force review, not execution. |

## Rollback Triggers

| Trigger | Required response |
| --- | --- |
| Median measured net below `+0.15R` | Set family state to `SUSPENDED`; stop promotion. |
| P95 stress turns median net negative | Keep paper-shadow only; require owner review. |
| Any live-capital path appears | Fail safety review immediately. |
| Any broker-action code appears before authorization | Fail safety review immediately. |
| Paper ledger missing rows | Stop evidence clock until fixed. |
| Unexpected run_id reset | Pause continuity clock and investigate. |
| Server time drift | Block affected events. |
| Owner manual lock | Suspend all family events. |

## Current Experimental Conclusion

Current Phase 3 evidence is useful but cautionary: the breakout-retest family is cost-sensitive. The future demo/paper path must measure cost first and must include cost-aware blocking before any order-like path exists.
