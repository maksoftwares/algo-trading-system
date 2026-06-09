# Dynamic Exit Last-Week Exact Logged-Path Replay

Scope: closed XAUUSD same-family demo trades entered in the previous completed week. Broker trade times are matched to signal-log `timestamp_local`. No MT5 terminal, EA, chart, preset, or runtime state was changed.

Important limit: this is exact against the available logged bid/ask snapshots. ATR-trail cannot be exact from these files because the logs do not contain M5 high/low candles or ATR values.

| View | Trades | Win rate | Actual broker PnL AED | Partial + BE PnL AED | Delta AED | BE-only PnL AED | Delta AED | Losses proven saved | Partial winner drag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Duplicate-hidden | 43 | 48.84% | 420.28 | 286.14 | -134.14 | 420.28 | 0.00 | 0 | 21 |
| Raw incl duplicates | 77 | 50.65% | 865.04 | 617.76 | -247.28 | 865.04 | 0.00 | 0 | 38 |

## Candidate Breakdown Duplicate-Hidden

| Candidate | Trades | Actual AED | Partial + BE AED | Delta AED | BE-only AED | Delta AED | Saved losses |
|---|---:|---:|---:|---:|---:|---:|---:|
| WR50_BreakoutEvening_v0 | 1 | -21.13 | -21.13 | 0.00 | -21.13 | 0.00 | 0 |
| breakout_retest | 41 | 377.49 | 253.58 | -123.91 | 377.49 | 0.00 | 0 |
| swing_breakout_retest_v0 | 1 | 63.92 | 53.70 | -10.22 | 63.92 | 0.00 | 0 |

## Saved Losing Trades Duplicate-Hidden

| Entry local | Ticket | Candidate | Side | Actual AED | Max favorable R logged | Partial + BE AED | BE-only AED |
|---|---:|---|---|---:|---:|---:|---:|

Artifacts: `DYNAMIC_EXIT_LAST_WEEK_EXACT_LOGGED_PATH_REPLAY.csv`.
