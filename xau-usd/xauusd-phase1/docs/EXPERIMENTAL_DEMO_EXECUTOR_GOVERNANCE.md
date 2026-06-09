# Experimental Demo Executor Governance

Last updated: 2026-06-08

Overall status: QUARANTINE_REVIEW_ONLY

## Authority Boundary

`Phase2ExperimentalDemoExecutor.mq5` is not canonical Phase 2. It is an owner-requested experimental demo lane and must not be used as evidence that Phase 2 readiness has passed.

| Rule | Status | Meaning |
| --- | --- | --- |
| Not canonical Phase 2 | ACTIVE | `PHASE2_READINESS_REPORT.md` remains the sole Phase 2 readiness authority. |
| Cannot create Phase 2 PASS evidence | ACTIVE | Experimental fills, logs, or PnL do not override measured-cost revalidation. |
| Cannot override measured-cost failure | ACTIVE | The breakout-retest family remains blocked while measured-cost revalidation is FAIL. |
| Cannot authorize live trading | ACTIVE | No live or real-capital use is allowed. |
| Demo-account-only | ACTIVE | Startup refuses non-demo server markers and non-whitelisted account logins. |
| Same-family is not diversification | ACTIVE | Breakout-retest variants are one correlated family for planning and risk. |

## Required Runtime Guards

| Guard | Implementation |
| --- | --- |
| Account login whitelist | `InpAllowedAccountLoginsCsv`; startup and order guards refuse unlisted account logins. |
| Authorization token | `InpExperimentalAuthorizationToken`; startup refuses unless it matches the required token. |
| Cost-suspension acknowledgement token | `InpCostSuspensionAcknowledgementToken`; startup and order guards refuse a cost-suspended family unless it matches `InpRequiredCostSuspensionAcknowledgementToken`. |
| Candidate status default | `InpCandidateStatus` defaults to `EXPERIMENTAL_QUARANTINE_REVIEW_ONLY`, not `ACCEPTED`. |
| Family lifecycle status | `InpFamilyLifecycleStatus` defaults to `COST_SUSPENDED_CANONICAL` and is logged with startup, signal, and order rows. |
| Candidate execution allowlist | `InpAuthorizedCandidatesCsv`; default generated charts authorize only `breakout_retest`. |
| Account daily order cap | `InpMaxAccountOrdersPerDay`; tracked across chart instances with MT5 GlobalVariables. |
| Account open exposure policy | No account-level open-position cap is enforced in the standard demo executor. Startup/order telemetry still logs account open exposure for review. |
| Per-instance caps | Fixed lot, one open exposure per instance, min seconds between orders, and per-instance order cap. |
| Kill switch | `InpKillSwitchFileName`; if the file contains `KILL`, new orders are blocked immediately. |
| Cost-R pre-order guard | `InpMaxEstimatedCostR`; estimated spread cost in R must remain below the configured threshold before `OrderSend`. |
| Spread pre-order guard | `InpMaxMeasuredSpreadPoints`; current spread must remain below the configured point threshold before `OrderSend`. |
| Mode truthfulness | Order logs use `order_mode=MARKET_PROXY` when market orders approximate stop-entry logic. |
| Cost telemetry | Order logs include spread, slippage, stop distance, and estimated cost in R. |

## Experimental Candidate Policy

| Candidate class | Default execution state | Requirement to enable |
| --- | --- | --- |
| `breakout_retest` | Quarantined by default | Explicit owner experimental authorization plus cost-suspension acknowledgement token. |
| Same-family approved variants | Quarantined and blocked by default | Add candidate to `InpAuthorizedCandidatesCsv`, record authorization, and acknowledge `COST_SUSPENDED_CANONICAL`. |
| Provisional candidates | Quarantined and blocked by default | Separate per-candidate owner authorization, Gate 9 status disclosure, and cost-suspension acknowledgement if same-family. |
| Rejected candidates | Blocked | New versioned hypothesis required before any future use. |

## Logging Requirements

Every order attempt, guard block, or send result must log:

```text
candidate
candidate_status
family_lifecycle_status
candidate_family_status
experimental_quarantine
canonical_phase2_evidence
phase2_readiness_override
symbol
action
direction
retcode
request_price
result_price
spread_at_signal_points
spread_at_order_points
slippage_points
estimated_cost_R
stop_distance_points
order_mode
guard_reason
account_orders_today
account_open_exposure
```

The expected quarantine labels are `experimental_quarantine=true`, `canonical_phase2_evidence=false`, `phase2_readiness_override=false`, and `candidate_family_status=COST_SUSPENDED_CANONICAL`.

## Non-Authority Statement

This governance packet does not approve broker-side execution. It only documents the minimum rules required if the owner continues the experimental demo lane. Canonical paper-mode implementation remains blocked while `PHASE2_READINESS_REPORT.md` is FAIL.
