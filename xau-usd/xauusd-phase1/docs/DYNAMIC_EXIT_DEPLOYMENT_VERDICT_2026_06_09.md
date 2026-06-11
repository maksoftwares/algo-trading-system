# Dynamic Exit Deployment Verdict - 2026-06-09

Status: `PARTIAL_BE_REJECTED_BE_ONLY_REJECTED_ATR_TRAIL_BLOCKED_PENDING_BAR_ATR_BACKTEST`

## Scope

This verdict covers the offline dynamic-exit experiment on actual closed XAUUSD same-family demo trades entered from 2026-06-01 through 2026-06-07.

No MT5 terminal, chart, preset, EA source, running EA, order, or open position was changed by this verdict.

Canonical Phase 2 remains blocked. This document does not approve paper trading, live trading, real capital, or any dynamic-exit broker-action EA.

## Evidence Used

- Exact logged-path replay: `xau-usd/xauusd-phase1/outputs/reports/DYNAMIC_EXIT_LAST_WEEK_EXACT_LOGGED_PATH_REPLAY.md`
- Trade-level replay CSV: `xau-usd/xauusd-phase1/outputs/reports/DYNAMIC_EXIT_LAST_WEEK_EXACT_LOGGED_PATH_REPLAY.csv`
- Offline replay script: `xau-usd/xauusd-phase1/scripts/backtest_dynamic_exit_variants.py`
- Test coverage: `xau-usd/xauusd-phase1/tests/test_dynamic_exit_backtest.py`

The exact replay matches actual broker trade timestamps to signal-log `timestamp_local` and uses actual broker PnL as the control baseline. Logged bid/ask snapshots are used only to prove whether a losing trade visibly reached +1R before closing negative.

## Result

| Variant | Duplicate-hidden PnL AED | Raw PnL AED | Verdict | Reason |
|---|---:|---:|---|---|
| Actual broker control | +420.28 | +865.04 | Baseline | Actual closed broker trades |
| Partial close at +1R plus breakeven | +286.14 | +617.76 | REJECTED_FOR_DEPLOYMENT | Reduced duplicate-hidden PnL by 134.14 AED and dragged 21 winners while saving 0 logged losers |
| Breakeven-only after +1R | +420.28 | +865.04 | REJECTED_FOR_DEPLOYMENT | No net improvement; saved 0 logged losers |
| ATR trail | n/a | n/a | BLOCKED_PENDING_BAR_ATR_BACKTEST | Existing signal logs do not contain M5 high/low candles or ATR values |

## Deployment Decision

`DYNEXIT_PartialBE_v0` must not be attached as a broker-action EA.

`DYNEXIT_BEOnly_v0` must not be attached as a broker-action EA.

`DYNEXIT_ATRTrail_v0` remains research-only until it beats the plain 1.5R hold on net-R-after-measured-cost using bar history that includes M5 high, low, close, and ATR.

Win rate is diagnostic only. The promotion KPI remains `net_expectancy_R_after_measured_cost`.

## Next Data Requirement For ATR Trail

To fairly test ATR trail, provide or generate a read-only bar file with at least:

```text
timestamp_local or timestamp_utc
symbol
timeframe
open
high
low
close
atr14
bid/ask or spread if available
```

Until that exists, ATR trail cannot be compared honestly against the actual broker control.
