# Phase 1 Would-Signal Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| would_signal_rows | PASS | Would-signal rows observed: 12. |
| would_signal_clusters | PASS | Setup clusters observed: 12. |
| would_signal_dry_run | PASS | All would-signal rows stayed dry-run. |
| would_signal_permission_lock | PASS | All would-signal rows kept permission false. |

## Summary

- Would-signal rows: 12
- Setup clusters: 12
- Directions observed: LONG, SHORT
- Level kinds observed: latest_swing_high, latest_swing_low, previous_weekly_low
- Review CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv`

## Setup Clusters

| Cluster | Rows | Direction | Level Kind | Level | Entry | Stop | Target | First Bar | Last Bar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WS001 | 1 | SHORT | previous_weekly_low | 4511.36 | 4505.48 | 4516.07 | 4489.59 | 2026.05.21 14:10:00 | 2026.05.21 14:10:00 |
| WS002 | 1 | SHORT | previous_weekly_low | 4511.36 | 4499.30 | 4516.09 | 4474.11 | 2026.05.21 15:20:00 | 2026.05.21 15:20:00 |
| WS003 | 1 | SHORT | previous_weekly_low | 4511.36 | 4506.95 | 4512.17 | 4499.12 | 2026.05.21 15:25:00 | 2026.05.21 15:25:00 |
| WS004 | 1 | LONG | latest_swing_high | 4515.35 | 4519.82 | 4514.02 | 4528.52 | 2026.05.21 16:20:00 | 2026.05.21 16:20:00 |
| WS005 | 1 | SHORT | latest_swing_low | 4542.79 | 4541.03 | 4544.44 | 4535.92 | 2026.05.21 20:10:00 | 2026.05.21 20:10:00 |
| WS006 | 1 | SHORT | latest_swing_low | 4542.79 | 4540.97 | 4543.47 | 4537.22 | 2026.05.21 20:20:00 | 2026.05.21 20:20:00 |
| WS007 | 1 | SHORT | latest_swing_low | 4539.67 | 4536.67 | 4540.59 | 4530.80 | 2026.05.21 23:40:00 | 2026.05.21 23:40:00 |
| WS008 | 1 | SHORT | latest_swing_low | 4539.67 | 4537.20 | 4541.23 | 4531.16 | 2026.05.22 00:50:00 | 2026.05.22 00:50:00 |
| WS009 | 1 | SHORT | latest_swing_low | 4530.10 | 4525.96 | 4536.50 | 4510.15 | 2026.05.22 01:10:00 | 2026.05.22 01:10:00 |
| WS010 | 1 | SHORT | latest_swing_low | 4530.10 | 4526.13 | 4532.49 | 4516.59 | 2026.05.22 01:35:00 | 2026.05.22 01:35:00 |
| WS011 | 1 | SHORT | latest_swing_low | 4530.10 | 4526.49 | 4532.40 | 4517.62 | 2026.05.22 02:00:00 | 2026.05.22 02:00:00 |
| WS012 | 1 | LONG | latest_swing_high | 4526.84 | 4529.29 | 4525.85 | 4534.45 | 2026.05.22 04:00:00 | 2026.05.22 04:00:00 |

## Direction Counts

| Value | Count |
| --- | --- |
| LONG | 2 |
| SHORT | 10 |

## Level Kind Counts

| Value | Count |
| --- | --- |
| latest_swing_high | 2 |
| latest_swing_low | 7 |
| previous_weekly_low | 3 |

## Would-Signal Rows

| Broker Time | Bar Time | Direction | Level Kind | Level | Entry | Stop | Target | Spread | Risk | Execution | Permission | Dry Run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026.05.21 14:10:00 | 2026.05.21 14:10:00 | SHORT | previous_weekly_low | 4511.36 | 4505.48 | 4516.07 | 4489.59 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.21 15:20:00 | 2026.05.21 15:20:00 | SHORT | previous_weekly_low | 4511.36 | 4499.30 | 4516.09 | 4474.11 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.21 15:25:00 | 2026.05.21 15:25:00 | SHORT | previous_weekly_low | 4511.36 | 4506.95 | 4512.17 | 4499.12 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.21 16:20:00 | 2026.05.21 16:20:00 | LONG | latest_swing_high | 4515.35 | 4519.82 | 4514.02 | 4528.52 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.21 20:10:00 | 2026.05.21 20:10:00 | SHORT | latest_swing_low | 4542.79 | 4541.03 | 4544.44 | 4535.92 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.21 20:20:00 | 2026.05.21 20:20:00 | SHORT | latest_swing_low | 4542.79 | 4540.97 | 4543.47 | 4537.22 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.21 23:40:00 | 2026.05.21 23:40:00 | SHORT | latest_swing_low | 4539.67 | 4536.67 | 4540.59 | 4530.80 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.22 00:50:00 | 2026.05.22 00:50:00 | SHORT | latest_swing_low | 4539.67 | 4537.20 | 4541.23 | 4531.16 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.22 01:10:00 | 2026.05.22 01:10:00 | SHORT | latest_swing_low | 4530.10 | 4525.96 | 4536.50 | 4510.15 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.22 01:35:00 | 2026.05.22 01:35:00 | SHORT | latest_swing_low | 4530.10 | 4526.13 | 4532.49 | 4516.59 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.22 02:00:00 | 2026.05.22 02:00:00 | SHORT | latest_swing_low | 4530.10 | 4526.49 | 4532.40 | 4517.62 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| 2026.05.22 04:00:01 | 2026.05.22 04:00:00 | LONG | latest_swing_high | 4526.84 | 4529.29 | 4525.85 | 4534.45 | 50.00 | NORMAL | EXECUTION_OK | false | true |
