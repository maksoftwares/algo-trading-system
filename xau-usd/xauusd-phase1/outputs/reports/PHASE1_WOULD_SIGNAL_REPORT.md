# Phase 1 Would-Signal Report

Overall status: PASS

Files directory: `C:\MT5PortableGoldMission\MQL5\Files`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| would_signal_rows | PASS | Would-signal rows observed: 110. |
| would_signal_clusters | PASS | Setup clusters observed: 110. |
| would_signal_dry_run | PASS | All would-signal rows stayed dry-run. |
| would_signal_permission_lock | PASS | All would-signal rows kept permission false. |

## Summary

- Would-signal rows: 110
- Setup clusters: 110
- Directions observed: LONG, SHORT
- Level kinds observed: latest_swing_high, latest_swing_low, previous_daily_low, previous_weekly_low
- Observers observed: breakout_retest, swing_breakout_retest_v0
- Review CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv`

## Observer Conflict Counts

| Bucket | Count |
| --- | --- |
| BR only | 14 |
| SBR only | 0 |
| Both same direction | 48 |
| Both opposite direction | 0 |

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
| WS019 | breakout_retest | 1 | LONG | latest_swing_high | 4565.43 | 4566.87 | 4564.95 | 4569.75 | 2026.05.25 15:05:00 | 2026.05.25 15:05:00 |
| WS020 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4565.43 | 4566.87 | 4564.95 | 4569.75 | 2026.05.25 15:05:00 | 2026.05.25 15:05:00 |
| WS021 | breakout_retest | 1 | LONG | latest_swing_high | 4565.43 | 4568.04 | 4565.21 | 4572.29 | 2026.05.25 15:15:00 | 2026.05.25 15:15:00 |
| WS022 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4565.43 | 4568.04 | 4565.21 | 4572.29 | 2026.05.25 15:15:00 | 2026.05.25 15:15:00 |
| WS023 | breakout_retest | 1 | LONG | latest_swing_high | 4570.39 | 4571.01 | 4569.24 | 4573.67 | 2026.05.25 16:45:00 | 2026.05.25 16:45:00 |
| WS024 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4570.39 | 4571.01 | 4569.24 | 4573.67 | 2026.05.25 16:45:00 | 2026.05.25 16:45:00 |
| WS025 | breakout_retest | 1 | LONG | latest_swing_high | 4570.39 | 4572.27 | 4569.98 | 4575.71 | 2026.05.25 16:50:00 | 2026.05.25 16:50:00 |
| WS026 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4570.39 | 4572.27 | 4569.98 | 4575.71 | 2026.05.25 16:50:00 | 2026.05.25 16:50:00 |
| WS027 | breakout_retest | 1 | LONG | latest_swing_high | 4572.59 | 4574.04 | 4571.76 | 4577.46 | 2026.05.25 22:20:00 | 2026.05.25 22:20:00 |
| WS028 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4572.59 | 4574.04 | 4571.76 | 4577.46 | 2026.05.25 22:20:00 | 2026.05.25 22:20:00 |
| WS029 | breakout_retest | 1 | LONG | latest_swing_high | 4571.28 | 4573.37 | 4569.19 | 4579.63 | 2026.05.25 22:45:00 | 2026.05.25 22:45:00 |
| WS030 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4571.28 | 4573.37 | 4569.19 | 4579.63 | 2026.05.25 22:45:00 | 2026.05.25 22:45:00 |
| WS031 | breakout_retest | 1 | SHORT | previous_daily_low | 4550.23 | 4544.51 | 4552.17 | 4533.02 | 2026.05.26 00:55:00 | 2026.05.26 00:55:00 |
| WS032 | breakout_retest | 1 | SHORT | latest_swing_low | 4529.75 | 4527.70 | 4533.13 | 4519.56 | 2026.05.26 05:50:00 | 2026.05.26 05:50:00 |
| WS033 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4529.75 | 4527.70 | 4533.13 | 4519.56 | 2026.05.26 05:50:00 | 2026.05.26 05:50:00 |
| WS034 | breakout_retest | 1 | SHORT | latest_swing_low | 4528.04 | 4522.83 | 4530.14 | 4511.87 | 2026.05.26 07:40:00 | 2026.05.26 07:40:00 |
| WS035 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4528.04 | 4522.83 | 4530.14 | 4511.87 | 2026.05.26 07:40:00 | 2026.05.26 07:40:00 |
| WS036 | breakout_retest | 1 | SHORT | latest_swing_low | 4528.04 | 4525.98 | 4530.32 | 4519.46 | 2026.05.26 08:30:00 | 2026.05.26 08:30:00 |
| WS037 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4528.04 | 4525.98 | 4530.32 | 4519.46 | 2026.05.26 08:30:00 | 2026.05.26 08:30:00 |
| WS038 | breakout_retest | 1 | SHORT | latest_swing_low | 4511.97 | 4510.47 | 4516.04 | 4502.11 | 2026.05.26 12:00:00 | 2026.05.26 12:00:00 |
| WS039 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4511.97 | 4510.47 | 4516.04 | 4502.11 | 2026.05.26 12:00:00 | 2026.05.26 12:00:00 |
| WS040 | breakout_retest | 1 | SHORT | latest_swing_low | 4511.97 | 4506.21 | 4512.59 | 4496.64 | 2026.05.26 12:15:00 | 2026.05.26 12:15:00 |
| WS041 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4511.97 | 4506.21 | 4512.59 | 4496.64 | 2026.05.26 12:15:00 | 2026.05.26 12:15:00 |
| WS042 | breakout_retest | 1 | SHORT | latest_swing_low | 4511.97 | 4507.95 | 4513.28 | 4499.96 | 2026.05.26 12:30:00 | 2026.05.26 12:30:00 |
| WS043 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4511.97 | 4507.95 | 4513.28 | 4499.96 | 2026.05.26 12:30:00 | 2026.05.26 12:30:00 |
| WS044 | breakout_retest | 1 | LONG | latest_swing_high | 4515.76 | 4522.42 | 4515.02 | 4533.53 | 2026.05.26 13:20:00 | 2026.05.26 13:20:00 |
| WS045 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4515.76 | 4522.42 | 4515.02 | 4533.53 | 2026.05.26 13:20:00 | 2026.05.26 13:20:00 |
| WS046 | breakout_retest | 1 | SHORT | latest_swing_low | 4515.71 | 4514.70 | 4520.85 | 4505.48 | 2026.05.26 14:15:00 | 2026.05.26 14:15:00 |
| WS047 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4515.71 | 4514.70 | 4520.85 | 4505.48 | 2026.05.26 14:15:00 | 2026.05.26 14:15:00 |
| WS048 | breakout_retest | 1 | LONG | latest_swing_high | 4515.76 | 4517.25 | 4511.57 | 4525.76 | 2026.05.26 14:30:00 | 2026.05.26 14:30:00 |
| WS049 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4515.76 | 4517.25 | 4511.57 | 4525.76 | 2026.05.26 14:30:00 | 2026.05.26 14:30:00 |
| WS050 | breakout_retest | 1 | SHORT | latest_swing_low | 4515.71 | 4515.46 | 4519.95 | 4508.73 | 2026.05.26 15:00:00 | 2026.05.26 15:00:00 |
| WS051 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4515.71 | 4515.46 | 4519.95 | 4508.73 | 2026.05.26 15:00:00 | 2026.05.26 15:00:00 |
| WS052 | breakout_retest | 1 | SHORT | latest_swing_low | 4515.71 | 4512.45 | 4516.62 | 4506.19 | 2026.05.26 15:05:00 | 2026.05.26 15:05:00 |
| WS053 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4515.71 | 4512.45 | 4516.62 | 4506.19 | 2026.05.26 15:05:00 | 2026.05.26 15:05:00 |
| WS054 | breakout_retest | 1 | SHORT | latest_swing_low | 4507.59 | 4504.70 | 4508.69 | 4498.72 | 2026.05.26 15:35:00 | 2026.05.26 15:35:00 |
| WS055 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4507.59 | 4504.70 | 4508.69 | 4498.72 | 2026.05.26 15:35:00 | 2026.05.26 15:35:00 |
| WS056 | breakout_retest | 1 | SHORT | latest_swing_low | 4507.59 | 4505.95 | 4509.94 | 4499.96 | 2026.05.26 16:05:00 | 2026.05.26 16:05:00 |
| WS057 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4507.59 | 4505.95 | 4509.94 | 4499.96 | 2026.05.26 16:05:00 | 2026.05.26 16:05:00 |
| WS058 | breakout_retest | 1 | SHORT | latest_swing_low | 4507.59 | 4505.20 | 4508.77 | 4499.85 | 2026.05.26 16:10:00 | 2026.05.26 16:10:00 |
| WS059 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4507.59 | 4505.20 | 4508.77 | 4499.85 | 2026.05.26 16:10:00 | 2026.05.26 16:10:00 |
| WS060 | breakout_retest | 1 | SHORT | latest_swing_low | 4507.59 | 4505.97 | 4509.09 | 4501.29 | 2026.05.26 16:50:00 | 2026.05.26 16:50:00 |
| WS061 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4507.59 | 4505.97 | 4509.09 | 4501.29 | 2026.05.26 16:50:00 | 2026.05.26 16:50:00 |
| WS062 | breakout_retest | 1 | LONG | latest_swing_high | 4504.51 | 4506.46 | 4503.52 | 4510.87 | 2026.05.26 22:00:00 | 2026.05.26 22:00:00 |
| WS063 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4504.51 | 4506.46 | 4503.52 | 4510.87 | 2026.05.26 22:00:00 | 2026.05.26 22:00:00 |
| WS064 | breakout_retest | 1 | LONG | latest_swing_high | 4504.51 | 4510.11 | 4500.06 | 4525.19 | 2026.05.26 22:20:00 | 2026.05.26 22:20:00 |
| WS065 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4504.51 | 4510.11 | 4500.06 | 4525.19 | 2026.05.26 22:20:00 | 2026.05.26 22:20:00 |
| WS066 | breakout_retest | 1 | LONG | latest_swing_high | 4513.55 | 4517.33 | 4512.05 | 4525.26 | 2026.05.27 01:15:00 | 2026.05.27 01:15:00 |
| WS067 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4513.55 | 4517.33 | 4512.05 | 4525.26 | 2026.05.27 01:15:00 | 2026.05.27 01:15:00 |
| WS068 | breakout_retest | 1 | SHORT | latest_swing_low | 4497.68 | 4496.22 | 4500.36 | 4490.01 | 2026.05.27 06:05:00 | 2026.05.27 06:05:00 |
| WS069 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4497.68 | 4496.22 | 4500.36 | 4490.01 | 2026.05.27 06:05:00 | 2026.05.27 06:05:00 |
| WS070 | breakout_retest | 1 | SHORT | previous_daily_low | 4482.54 | 4477.70 | 4484.29 | 4467.81 | 2026.05.27 07:55:00 | 2026.05.27 07:55:00 |
| WS071 | breakout_retest | 1 | LONG | latest_swing_high | 4489.04 | 4492.69 | 4487.80 | 4500.02 | 2026.05.27 08:45:00 | 2026.05.27 08:45:00 |
| WS072 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4489.04 | 4492.69 | 4487.80 | 4500.02 | 2026.05.27 08:45:00 | 2026.05.27 08:45:00 |
| WS073 | breakout_retest | 1 | LONG | latest_swing_high | 4489.04 | 4492.27 | 4488.02 | 4498.64 | 2026.05.27 09:15:00 | 2026.05.27 09:15:00 |
| WS074 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4489.04 | 4492.27 | 4488.02 | 4498.64 | 2026.05.27 09:15:00 | 2026.05.27 09:15:00 |
| WS075 | breakout_retest | 1 | LONG | latest_swing_high | 4489.04 | 4490.62 | 4486.31 | 4497.08 | 2026.05.27 09:40:00 | 2026.05.27 09:40:00 |
| WS076 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4489.04 | 4490.62 | 4486.31 | 4497.08 | 2026.05.27 09:40:00 | 2026.05.27 09:40:00 |
| WS077 | breakout_retest | 1 | LONG | latest_swing_high | 4489.04 | 4489.79 | 4487.67 | 4492.97 | 2026.05.27 09:55:00 | 2026.05.27 09:55:00 |
| WS078 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4489.04 | 4489.79 | 4487.67 | 4492.97 | 2026.05.27 09:55:00 | 2026.05.27 09:55:00 |
| WS079 | breakout_retest | 1 | SHORT | latest_swing_low | 4442.48 | 4438.79 | 4445.41 | 4428.86 | 2026.05.27 11:55:00 | 2026.05.27 11:55:00 |
| WS080 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4442.48 | 4438.79 | 4445.41 | 4428.86 | 2026.05.27 11:55:00 | 2026.05.27 11:55:00 |
| WS081 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4444.51 | 4454.29 | 4429.84 | 2026.05.27 12:45:00 | 2026.05.27 12:45:00 |
| WS082 | breakout_retest | 1 | SHORT | latest_swing_low | 4435.37 | 4432.76 | 4441.56 | 4419.55 | 2026.05.27 15:50:00 | 2026.05.27 15:50:00 |
| WS083 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4435.37 | 4432.76 | 4441.56 | 4419.55 | 2026.05.27 15:50:00 | 2026.05.27 15:50:00 |
| WS084 | breakout_retest | 1 | LONG | latest_swing_high | 4441.36 | 4445.62 | 4440.92 | 4452.66 | 2026.05.27 17:20:00 | 2026.05.27 17:20:00 |
| WS085 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4441.36 | 4445.62 | 4440.92 | 4452.66 | 2026.05.27 17:20:00 | 2026.05.27 17:20:00 |
| WS086 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4449.77 | 4453.56 | 4444.08 | 2026.05.27 17:40:00 | 2026.05.27 17:40:00 |
| WS087 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4450.76 | 4454.54 | 4445.10 | 2026.05.27 17:45:00 | 2026.05.27 17:45:00 |
| WS088 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4450.47 | 4453.92 | 4445.30 | 2026.05.27 18:00:00 | 2026.05.27 18:00:00 |
| WS089 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4450.10 | 4454.19 | 4443.96 | 2026.05.27 18:05:00 | 2026.05.27 18:05:00 |
| WS090 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4449.73 | 4454.16 | 4443.08 | 2026.05.27 19:30:00 | 2026.05.27 19:30:00 |
| WS091 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4451.70 | 4453.80 | 4448.54 | 2026.05.27 19:55:00 | 2026.05.27 19:55:00 |
| WS092 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4450.67 | 4454.12 | 4445.50 | 2026.05.27 23:50:00 | 2026.05.27 23:50:00 |
| WS093 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4443.76 | 4454.23 | 4428.06 | 2026.05.28 00:25:00 | 2026.05.28 00:25:00 |
| WS094 | breakout_retest | 1 | SHORT | previous_weekly_low | 4453.16 | 4445.47 | 4459.17 | 4424.92 | 2026.05.28 01:10:00 | 2026.05.28 01:10:00 |
| WS095 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4455.11 | 4445.47 | 4459.17 | 4424.92 | 2026.05.28 01:10:00 | 2026.05.28 01:10:00 |
| WS096 | breakout_retest | 1 | SHORT | latest_swing_low | 4396.23 | 4391.51 | 4397.86 | 4381.99 | 2026.05.28 03:20:00 | 2026.05.28 03:20:00 |
| WS097 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4396.23 | 4391.51 | 4397.86 | 4381.99 | 2026.05.28 03:20:00 | 2026.05.28 03:20:00 |
| WS098 | breakout_retest | 1 | LONG | latest_swing_high | 4375.03 | 4387.50 | 4374.37 | 4407.20 | 2026.05.28 05:40:00 | 2026.05.28 05:40:00 |
| WS099 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4375.03 | 4387.50 | 4374.37 | 4407.20 | 2026.05.28 05:40:00 | 2026.05.28 05:40:00 |
| WS100 | breakout_retest | 1 | LONG | latest_swing_high | 4375.03 | 4381.41 | 4373.91 | 4392.66 | 2026.05.28 06:20:00 | 2026.05.28 06:20:00 |
| WS101 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4375.03 | 4381.41 | 4373.91 | 4392.66 | 2026.05.28 06:20:00 | 2026.05.28 06:20:00 |
| WS102 | breakout_retest | 1 | LONG | latest_swing_high | 4375.03 | 4380.16 | 4373.43 | 4390.25 | 2026.05.28 06:25:00 | 2026.05.28 06:25:00 |
| WS103 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4375.03 | 4380.16 | 4373.43 | 4390.25 | 2026.05.28 06:25:00 | 2026.05.28 06:25:00 |
| WS104 | breakout_retest | 1 | LONG | latest_swing_high | 4385.30 | 4389.19 | 4382.19 | 4399.69 | 2026.05.28 08:00:00 | 2026.05.28 08:00:00 |
| WS105 | swing_breakout_retest_v0 | 1 | LONG | latest_swing_high | 4385.30 | 4389.19 | 4382.19 | 4399.69 | 2026.05.28 08:00:00 | 2026.05.28 08:00:00 |
| WS106 | breakout_retest | 1 | SHORT | previous_daily_low | 4401.21 | 4393.44 | 4401.73 | 4381.00 | 2026.05.28 10:15:00 | 2026.05.28 10:15:00 |
| WS107 | breakout_retest | 1 | SHORT | previous_daily_low | 4401.21 | 4395.42 | 4402.67 | 4384.54 | 2026.05.28 10:35:00 | 2026.05.28 10:35:00 |
| WS108 | breakout_retest | 1 | SHORT | previous_daily_low | 4401.21 | 4397.91 | 4402.76 | 4390.64 | 2026.05.28 10:40:00 | 2026.05.28 10:40:00 |
| WS109 | breakout_retest | 1 | SHORT | latest_swing_low | 4389.67 | 4386.49 | 4390.90 | 4379.88 | 2026.05.28 11:25:00 | 2026.05.28 11:25:00 |
| WS110 | swing_breakout_retest_v0 | 1 | SHORT | latest_swing_low | 4389.67 | 4386.49 | 4390.90 | 4379.88 | 2026.05.28 11:25:00 | 2026.05.28 11:25:00 |

## Direction Counts

| Value | Count |
| --- | --- |
| LONG | 46 |
| SHORT | 64 |

## Level Kind Counts

| Value | Count |
| --- | --- |
| latest_swing_high | 46 |
| latest_swing_low | 49 |
| previous_daily_low | 5 |
| previous_weekly_low | 10 |

## Would-Signal Rows

| Observer | Broker Time | Bar Time | Direction | Level Kind | Level | Entry | Stop | Target | Spread | Risk | Execution | Permission | Dry Run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| swing_breakout_retest_v0 | 2026.05.26 16:50:00 | 2026.05.26 16:50:00 | SHORT | latest_swing_low | 4507.59 | 4505.97 | 4509.09 | 4501.29 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.26 22:00:02 | 2026.05.26 22:00:00 | LONG | latest_swing_high | 4504.51 | 4506.46 | 4503.52 | 4510.87 | 180.00 | NORMAL | SPREAD_TOO_HIGH | false | true |
| swing_breakout_retest_v0 | 2026.05.26 22:00:02 | 2026.05.26 22:00:00 | LONG | latest_swing_high | 4504.51 | 4506.46 | 4503.52 | 4510.87 | 180.00 | NORMAL | SPREAD_TOO_HIGH | false | true |
| breakout_retest | 2026.05.26 22:20:00 | 2026.05.26 22:20:00 | LONG | latest_swing_high | 4504.51 | 4510.11 | 4500.06 | 4525.19 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.26 22:20:00 | 2026.05.26 22:20:00 | LONG | latest_swing_high | 4504.51 | 4510.11 | 4500.06 | 4525.19 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 01:15:01 | 2026.05.27 01:15:00 | LONG | latest_swing_high | 4513.55 | 4517.33 | 4512.05 | 4525.26 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 01:15:01 | 2026.05.27 01:15:00 | LONG | latest_swing_high | 4513.55 | 4517.33 | 4512.05 | 4525.26 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 06:05:00 | 2026.05.27 06:05:00 | SHORT | latest_swing_low | 4497.68 | 4496.22 | 4500.36 | 4490.01 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 06:05:00 | 2026.05.27 06:05:00 | SHORT | latest_swing_low | 4497.68 | 4496.22 | 4500.36 | 4490.01 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 07:55:00 | 2026.05.27 07:55:00 | SHORT | previous_daily_low | 4482.54 | 4477.70 | 4484.29 | 4467.81 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 08:45:00 | 2026.05.27 08:45:00 | LONG | latest_swing_high | 4489.04 | 4492.69 | 4487.80 | 4500.02 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 08:45:00 | 2026.05.27 08:45:00 | LONG | latest_swing_high | 4489.04 | 4492.69 | 4487.80 | 4500.02 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 09:15:00 | 2026.05.27 09:15:00 | LONG | latest_swing_high | 4489.04 | 4492.27 | 4488.02 | 4498.64 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 09:15:00 | 2026.05.27 09:15:00 | LONG | latest_swing_high | 4489.04 | 4492.27 | 4488.02 | 4498.64 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 09:40:00 | 2026.05.27 09:40:00 | LONG | latest_swing_high | 4489.04 | 4490.62 | 4486.31 | 4497.08 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 09:40:00 | 2026.05.27 09:40:00 | LONG | latest_swing_high | 4489.04 | 4490.62 | 4486.31 | 4497.08 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 09:55:03 | 2026.05.27 09:55:00 | LONG | latest_swing_high | 4489.04 | 4489.79 | 4487.67 | 4492.97 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 09:55:03 | 2026.05.27 09:55:00 | LONG | latest_swing_high | 4489.04 | 4489.79 | 4487.67 | 4492.97 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 11:55:00 | 2026.05.27 11:55:00 | SHORT | latest_swing_low | 4442.48 | 4438.79 | 4445.41 | 4428.86 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 11:55:00 | 2026.05.27 11:55:00 | SHORT | latest_swing_low | 4442.48 | 4438.79 | 4445.41 | 4428.86 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 12:45:00 | 2026.05.27 12:45:00 | SHORT | previous_weekly_low | 4453.16 | 4444.51 | 4454.29 | 4429.84 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 15:50:00 | 2026.05.27 15:50:00 | SHORT | latest_swing_low | 4435.37 | 4432.76 | 4441.56 | 4419.55 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 15:50:00 | 2026.05.27 15:50:00 | SHORT | latest_swing_low | 4435.37 | 4432.76 | 4441.56 | 4419.55 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 17:20:00 | 2026.05.27 17:20:00 | LONG | latest_swing_high | 4441.36 | 4445.62 | 4440.92 | 4452.66 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.27 17:20:00 | 2026.05.27 17:20:00 | LONG | latest_swing_high | 4441.36 | 4445.62 | 4440.92 | 4452.66 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 17:40:00 | 2026.05.27 17:40:00 | SHORT | previous_weekly_low | 4453.16 | 4449.77 | 4453.56 | 4444.08 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 17:45:00 | 2026.05.27 17:45:00 | SHORT | previous_weekly_low | 4453.16 | 4450.76 | 4454.54 | 4445.10 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 18:00:00 | 2026.05.27 18:00:00 | SHORT | previous_weekly_low | 4453.16 | 4450.47 | 4453.92 | 4445.30 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 18:05:00 | 2026.05.27 18:05:00 | SHORT | previous_weekly_low | 4453.16 | 4450.10 | 4454.19 | 4443.96 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 19:30:01 | 2026.05.27 19:30:00 | SHORT | previous_weekly_low | 4453.16 | 4449.73 | 4454.16 | 4443.08 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 19:55:00 | 2026.05.27 19:55:00 | SHORT | previous_weekly_low | 4453.16 | 4451.70 | 4453.80 | 4448.54 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.27 23:50:00 | 2026.05.27 23:50:00 | SHORT | previous_weekly_low | 4453.16 | 4450.67 | 4454.12 | 4445.50 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 00:25:00 | 2026.05.28 00:25:00 | SHORT | previous_weekly_low | 4453.16 | 4443.76 | 4454.23 | 4428.06 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 01:10:00 | 2026.05.28 01:10:00 | SHORT | previous_weekly_low | 4453.16 | 4445.47 | 4459.17 | 4424.92 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.28 01:10:00 | 2026.05.28 01:10:00 | SHORT | latest_swing_low | 4455.11 | 4445.47 | 4459.17 | 4424.92 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 03:20:00 | 2026.05.28 03:20:00 | SHORT | latest_swing_low | 4396.23 | 4391.51 | 4397.86 | 4381.99 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.28 03:20:00 | 2026.05.28 03:20:00 | SHORT | latest_swing_low | 4396.23 | 4391.51 | 4397.86 | 4381.99 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 05:40:01 | 2026.05.28 05:40:00 | LONG | latest_swing_high | 4375.03 | 4387.50 | 4374.37 | 4407.20 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.28 05:40:01 | 2026.05.28 05:40:00 | LONG | latest_swing_high | 4375.03 | 4387.50 | 4374.37 | 4407.20 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 06:20:00 | 2026.05.28 06:20:00 | LONG | latest_swing_high | 4375.03 | 4381.41 | 4373.91 | 4392.66 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.28 06:20:00 | 2026.05.28 06:20:00 | LONG | latest_swing_high | 4375.03 | 4381.41 | 4373.91 | 4392.66 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 06:25:00 | 2026.05.28 06:25:00 | LONG | latest_swing_high | 4375.03 | 4380.16 | 4373.43 | 4390.25 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.28 06:25:00 | 2026.05.28 06:25:00 | LONG | latest_swing_high | 4375.03 | 4380.16 | 4373.43 | 4390.25 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 08:00:00 | 2026.05.28 08:00:00 | LONG | latest_swing_high | 4385.30 | 4389.19 | 4382.19 | 4399.69 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.28 08:00:00 | 2026.05.28 08:00:00 | LONG | latest_swing_high | 4385.30 | 4389.19 | 4382.19 | 4399.69 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 10:15:00 | 2026.05.28 10:15:00 | SHORT | previous_daily_low | 4401.21 | 4393.44 | 4401.73 | 4381.00 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 10:35:00 | 2026.05.28 10:35:00 | SHORT | previous_daily_low | 4401.21 | 4395.42 | 4402.67 | 4384.54 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 10:40:01 | 2026.05.28 10:40:00 | SHORT | previous_daily_low | 4401.21 | 4397.91 | 4402.76 | 4390.64 | 50.00 | NORMAL | EXECUTION_OK | false | true |
| breakout_retest | 2026.05.28 11:25:00 | 2026.05.28 11:25:00 | SHORT | latest_swing_low | 4389.67 | 4386.49 | 4390.90 | 4379.88 | 75.00 | NORMAL | EXECUTION_OK | false | true |
| swing_breakout_retest_v0 | 2026.05.28 11:25:00 | 2026.05.28 11:25:00 | SHORT | latest_swing_low | 4389.67 | 4386.49 | 4390.90 | 4379.88 | 75.00 | NORMAL | EXECUTION_OK | false | true |
