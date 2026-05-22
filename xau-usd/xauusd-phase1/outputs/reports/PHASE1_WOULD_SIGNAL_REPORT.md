# Phase 1 Would-Signal Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| would_signal_rows | PASS | Would-signal rows observed: 4. |
| would_signal_clusters | PASS | Setup clusters observed: 4. |
| would_signal_dry_run | PASS | All would-signal rows stayed dry-run. |
| would_signal_permission_lock | PASS | All would-signal rows kept permission false. |

## Summary

- Would-signal rows: 4
- Setup clusters: 4
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

## Direction Counts

| Value | Count |
| --- | --- |
| LONG | 2 |
| SHORT | 2 |

## Level Kind Counts

| Value | Count |
| --- | --- |
| latest_swing_high | 2 |
| latest_swing_low | 2 |

## Would-Signal Rows

| Observer | Broker Time | Bar Time | Direction | Level Kind | Level | Entry | Stop | Target | Spread | Risk | Execution | Permission | Dry Run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breakout_retest | 2026.05.22 11:25:01 | 2026.05.22 11:25:00 | SHORT | latest_swing_low | 4514.67 | 4511.74 | 4516.09 | 4505.22 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.22 11:25:01 | 2026.05.22 11:25:00 | SHORT | latest_swing_low | 4514.67 | 4511.74 | 4516.09 | 4505.22 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.22 11:50:01 | 2026.05.22 11:50:00 | LONG | latest_swing_high | 4517.11 | 4522.94 | 4516.58 | 4532.47 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.22 11:50:01 | 2026.05.22 11:50:00 | LONG | latest_swing_high | 4517.11 | 4522.94 | 4516.58 | 4532.47 | 50.00 | NORMAL | EXECUTION_OK | false | true |
