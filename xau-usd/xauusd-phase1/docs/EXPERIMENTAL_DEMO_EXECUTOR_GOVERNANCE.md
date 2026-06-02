# Experimental Demo Executor Governance

Last updated: 2026-06-02

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
| Candidate execution allowlist | `InpAuthorizedCandidatesCsv`; default generated charts authorize only `breakout_retest`. |
| Account daily order cap | `InpMaxAccountOrdersPerDay`; tracked across chart instances with MT5 GlobalVariables. |
| Account open exposure cap | `InpMaxAccountOpenPositions`; counts experimental magic-number positions/orders across symbols. |
| Per-instance caps | Fixed lot, one open exposure per instance, min seconds between orders, and per-instance order cap. |
| Kill switch | `InpKillSwitchFileName`; if the file contains `KILL`, new orders are blocked immediately. |
| Mode truthfulness | Order logs use `order_mode=MARKET_PROXY` when market orders approximate stop-entry logic. |
| Cost telemetry | Order logs include spread, slippage, stop distance, and estimated cost in R. |

## Experimental Candidate Policy

| Candidate class | Default execution state | Requirement to enable |
| --- | --- | --- |
| `breakout_retest` | Allowed only with owner token and account whitelist | Explicit owner experimental authorization. |
| Same-family approved variants | Blocked by default | Add candidate to `InpAuthorizedCandidatesCsv` and record authorization. |
| Provisional candidates | Blocked by default | Separate per-candidate owner authorization plus Gate 9 status disclosure. |
| Rejected candidates | Blocked | New versioned hypothesis required before any future use. |

## Logging Requirements

Every order attempt, guard block, or send result must log:

```text
candidate
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

## Non-Authority Statement

This governance packet does not approve broker-side execution. It only documents the minimum rules required if the owner continues the experimental demo lane. Canonical paper-mode implementation remains blocked while `PHASE2_READINESS_REPORT.md` is FAIL.
