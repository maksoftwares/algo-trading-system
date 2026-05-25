# Phase 1 Would-Signal Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| would_signal_rows | PASS | Would-signal rows observed: 18. |
| would_signal_clusters | PASS | Setup clusters observed: 18. |
| would_signal_dry_run | PASS | All would-signal rows stayed dry-run. |
| would_signal_permission_lock | PASS | All would-signal rows kept permission false. |

## Summary

- Would-signal rows: 18
- Setup clusters: 18
- Directions observed: LONG, SHORT
- Level kinds observed: latest_swing_high, latest_swing_low
- Observers observed: breakout_retest, swing_breakout_retest_v0
- Review CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv`

## Setup Clusters

| Cluster | Observer | Rows | Direction | Level Kind | Level | Entry | Stop | Target | First Bar | Last Bar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WS001 | breakout_retest | 1 | SHORT | latest_swing_low | 4514.67 | 4511.74 | 4516.09 | 4505.22 | 2026.05.22 11:25:00 | 2026.05.22 11:25:00 |
| WS002 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4514.67 | 4511.74 | 4516.09 | 4505.22 | 2026.05.22 11:25:00 | 2026.05.22 11:25:00 |
| WS003 | breakout_retest | 1 | LONG | latest_swing_high | 4517.11 | 4522.94 | 4516.58 | 4532.47 | 2026.05.22 11:50:00 | 2026.05.22 11:50:00 |
| WS004 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4517.11 | 4522.94 | 4516.58 | 4532.47 | 2026.05.22 11:50:00 | 2026.05.22 11:50:00 |
| WS005 | breakout_retest | 1 | LONG | latest_swing_high | 4517.11 | 4518.58 | 4514.30 | 4525.01 | 2026.05.22 12:45:00 | 2026.05.22 12:45:00 |
| WS006 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4517.11 | 4518.58 | 4514.30 | 4525.01 | 2026.05.22 12:45:00 | 2026.05.22 12:45:00 |
| WS007 | breakout_retest | 1 | LONG | latest_swing_high | 4517.11 | 4519.58 | 4515.40 | 4525.85 | 2026.05.22 12:50:00 | 2026.05.22 12:50:00 |
| WS008 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4517.11 | 4519.58 | 4515.40 | 4525.85 | 2026.05.22 12:50:00 | 2026.05.22 12:50:00 |
| WS009 | breakout_retest | 1 | SHORT | latest_swing_low | 4514.87 | 4511.45 | 4517.35 | 4502.59 | 2026.05.22 14:05:00 | 2026.05.22 14:05:00 |
| WS010 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4514.87 | 4511.45 | 4517.35 | 4502.59 | 2026.05.22 14:05:00 | 2026.05.22 14:05:00 |
| WS011 | breakout_retest | 1 | SHORT | latest_swing_low | 4559.47 | 4555.14 | 4561.13 | 4546.16 | 2026.05.25 05:50:00 | 2026.05.25 05:50:00 |
| WS012 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4559.47 | 4555.14 | 4561.13 | 4546.16 | 2026.05.25 05:50:00 | 2026.05.25 05:50:00 |
| WS013 | breakout_retest | 1 | SHORT | latest_swing_low | 4559.47 | 4553.95 | 4562.05 | 4541.80 | 2026.05.25 07:40:00 | 2026.05.25 07:40:00 |
| WS014 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4559.47 | 4553.95 | 4562.05 | 4541.80 | 2026.05.25 07:40:00 | 2026.05.25 07:40:00 |
| WS015 | breakout_retest | 1 | SHORT | latest_swing_low | 4567.36 | 4566.19 | 4569.52 | 4561.19 | 2026.05.25 12:50:00 | 2026.05.25 12:50:00 |
| WS016 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4567.36 | 4566.19 | 4569.52 | 4561.19 | 2026.05.25 12:50:00 | 2026.05.25 12:50:00 |
| WS017 | breakout_retest | 1 | SHORT | latest_swing_low | 4567.36 | 4562.45 | 4568.88 | 4552.81 | 2026.05.25 13:20:00 | 2026.05.25 13:20:00 |
| WS018 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4567.36 | 4562.45 | 4568.88 | 4552.81 | 2026.05.25 13:20:00 | 2026.05.25 13:20:00 |

## Direction Counts

| Value | Count |
| --- | --- |
| LONG | 6 |
| SHORT | 12 |

## Level Kind Counts

| Value | Count |
| --- | --- |
| latest_swing_high | 6 |
| latest_swing_low | 12 |

## Would-Signal Rows

| Observer | Broker Time | Bar Time | Direction | Level Kind | Level | Entry | Stop | Target | Spread | Risk | Execution | Permission | Dry Run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout_retest | 2026.05.22 11:25:01 | 2026.05.22 11:25:00 | SHORT | latest_swing_low | 4514.67 | 4511.74 | 4516.09 | 4505.22 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.22 11:25:01 | 2026.05.22 11:25:00 | SHORT | latest_swing_low | 4514.67 | 4511.74 | 4516.09 | 4505.22 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.22 11:50:01 | 2026.05.22 11:50:00 | LONG | latest_swing_high | 4517.11 | 4522.94 | 4516.58 | 4532.47 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.22 11:50:01 | 2026.05.22 11:50:00 | LONG | latest_swing_high | 4517.11 | 4522.94 | 4516.58 | 4532.47 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.22 12:45:00 | 2026.05.22 12:45:00 | LONG | latest_swing_high | 4517.11 | 4518.58 | 4514.30 | 4525.01 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.22 12:45:00 | 2026.05.22 12:45:00 | LONG | latest_swing_high | 4517.11 | 4518.58 | 4514.30 | 4525.01 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.22 12:50:00 | 2026.05.22 12:50:00 | LONG | latest_swing_high | 4517.11 | 4519.58 | 4515.40 | 4525.85 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.22 12:50:00 | 2026.05.22 12:50:00 | LONG | latest_swing_high | 4517.11 | 4519.58 | 4515.40 | 4525.85 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.22 14:05:00 | 2026.05.22 14:05:00 | SHORT | latest_swing_low | 4514.87 | 4511.45 | 4517.35 | 4502.59 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.22 14:05:00 | 2026.05.22 14:05:00 | SHORT | latest_swing_low | 4514.87 | 4511.45 | 4517.35 | 4502.59 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.25 05:50:00 | 2026.05.25 05:50:00 | SHORT | latest_swing_low | 4559.47 | 4555.14 | 4561.13 | 4546.16 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.25 05:50:00 | 2026.05.25 05:50:00 | SHORT | latest_swing_low | 4559.47 | 4555.14 | 4561.13 | 4546.16 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.25 07:40:00 | 2026.05.25 07:40:00 | SHORT | latest_swing_low | 4559.47 | 4553.95 | 4562.05 | 4541.80 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.25 07:40:00 | 2026.05.25 07:40:00 | SHORT | latest_swing_low | 4559.47 | 4553.95 | 4562.05 | 4541.80 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.25 12:50:00 | 2026.05.25 12:50:00 | SHORT | latest_swing_low | 4567.36 | 4566.19 | 4569.52 | 4561.19 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.25 12:50:00 | 2026.05.25 12:50:00 | SHORT | latest_swing_low | 4567.36 | 4566.19 | 4569.52 | 4561.19 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.25 13:20:00 | 2026.05.25 13:20:00 | SHORT | latest_swing_low | 4567.36 | 4562.45 | 4568.88 | 4552.81 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.25 13:20:00 | 2026.05.25 13:20:00 | SHORT | latest_swing_low | 4567.36 | 4562.45 | 4568.88 | 4552.81 | 50.00 | NORMAL | EXECUTION_OK | false | true |
