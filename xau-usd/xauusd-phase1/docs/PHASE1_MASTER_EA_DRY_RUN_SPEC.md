# Phase 1 Master EA Dry-Run Spec

Last updated: 2026-05-21

This document is the active Phase 1 dry-run build spec after `breakout_retest` received a final Phase 0 PASS and real-artifact verification passed.

## Objective

The dry-run Master EA proves that the platform shell can observe, classify, log, and enforce state without broker-side execution. It does not prove profitability and does not activate any expert.

## Event Flow

```text
OnInit()
    Load inputs
    Validate symbol
    Validate server time
    Initialize module state
    Validate magic namespace
    Initialize CSV logs
    Initialize dashboard
    Start timer
    Lock mode to DRY_RUN
    Log startup snapshot

OnTick()
    Refresh latest tick
    Refresh spread
    Refresh market cache
    Do not submit broker actions

OnTimer()
    Detect new M5 bar
    If new M5 bar:
        Build market snapshot
        Compute features
        Detect session
        Detect news state
        Classify regime
        Evaluate risk state
        Evaluate execution state
        Produce decision row
        Update dashboard
        Write decision_log.csv

OnDeinit()
    Log shutdown reason
    Flush logs
    Save shutdown snapshot
```

## Required Modules

| Module | Responsibility |
| --- | --- |
| `MasterEA.mq5` | Own EA lifecycle and module orchestration. |
| `CommonEnums.mqh` | Shared states for sessions, regimes, risk, news, execution, and lifecycle. |
| `CommonTypes.mqh` | Shared snapshots and decision-row contracts. |
| `MarketDataEngine.mqh` | Tick, spread, candle, symbol, and stale-data snapshots. |
| `FeatureEngine.mqh` | ATR, ADX, EMA, slopes, swings, ranges, candle ratios, volatility and spread features. |
| `SessionEngine.mqh` | Asia, London, New York, rollover, weekend, and thin-liquidity windows. |
| `RegimeRouter.mqh` | Regime classification only; no expert activation. |
| `BreakoutRetestObserver.mqh` | Dry-run setup-stage observation for the approved future expert. |
| `RiskManager.mqh` | Equity-state tracking and simulated daily/weekly/monthly caps. |
| `ExecutionGuard.mqh` | Spread, stale tick, tradeability, and market-open classification. |
| `NewsGuard.mqh` | Manual blackout windows and news state classification. |
| `PositionManager.mqh` | Dry-run interface only; no live position changes. |
| `Logger.mqh` | CSV writing, flushes, startup/shutdown snapshots, and error logging. |
| `Dashboard.mqh` | On-chart status display. |
| `MagicNumberAllocator.mqh` | Namespace reservation and duplicate checks. |
| `ExpertLifecycleManager.mqh` | Keep expert state disabled or dry-run only. |
| `DryRunMode.mqh` | Lock all decisions to observation-only behavior. |
| `ServerTimeValidator.mqh` | Broker, UTC, and local time offset checks. |

## Required Decision Log Columns

```text
timestamp_broker
timestamp_utc
timestamp_local
symbol
bid
ask
spread_points
session
regime
router_version
risk_state
execution_state
news_state
allowed_expert
would_have_allowed_experts
trade_permission
block_reason
dry_run
```

## Required Dashboard Fields

```text
symbol
broker server
account number
EA mode
current spread
current session
current regime
allowed expert
risk state
news state
execution state
daily P/L state
weekly P/L state
monthly P/L state
trade permission
block reason
router version
EA version
last log write time
```

## Initial State Sets

Regimes:

```text
TREND_WITH_PULLBACK
RANGE
COMPRESSION
BREAKOUT_RETEST
ABNORMAL_MARKET
NEWS_BLACKOUT
NO_TRADE
```

Risk states:

```text
NORMAL
REDUCED_RISK
DEFENSIVE
LOCKED_DAILY_LOSS
LOCKED_WEEKLY_LOSS
LOCKED_MONTHLY_LOSS
MANUAL_LOCK
```

Execution states:

```text
EXECUTION_OK
SPREAD_TOO_HIGH
SLIPPAGE_TOO_HIGH
STALE_TICK
SYMBOL_NOT_TRADEABLE
MARKET_CLOSED
BROKER_ERROR
```

News states:

```text
NO_NEWS_RISK
PRE_NEWS_BLACKOUT
POST_NEWS_COOLDOWN
MANUAL_NEWS_LOCKDOWN
```

Lifecycle states:

```text
DISABLED
DRY_RUN_ONLY
ACTIVE
SUSPENDED
RETIRED
```

In the first accepted build, every expert must remain `DISABLED` or `DRY_RUN_ONLY`.

## Acceptance Criteria

1. EA compiles with zero warnings.
2. EA starts in `DRY_RUN` mode only.
3. Safety audit finds no broker-action API usage.
4. Demo run lasts five continuous trading days.
5. `decision_log.csv` has one row per M5 bar.
6. Dashboard updates each bar.
7. Session detection is logged.
8. Regime classification is logged.
9. Spread state is logged.
10. News state is logged.
11. Risk caps can be triggered through simulation inputs.
12. Server-time drift detection can be tested.
13. Startup and shutdown snapshots are logged.
14. Restart does not corrupt existing logs.
15. No expert is active beyond the approved dry-run scope.
