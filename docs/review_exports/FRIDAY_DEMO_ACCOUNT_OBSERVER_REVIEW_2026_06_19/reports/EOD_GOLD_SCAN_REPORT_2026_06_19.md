# EOD GOLD Scan Report - 2026-06-19

Generated UTC: 2026-06-19 19:31:20
Generated Dubai: 2026-06-19 23:31:20
Window UTC: 2026-06-18 20:00:00 through 2026-06-19 19:31:20
Entry lookup window UTC: 2026-06-01 00:00:00 through 2026-06-19 19:31:20

Boundary: read-only export. No EA, preset, chart, terminal, or broker setting was changed.

## Gold Day Context

| Date | Open | High | Low | Close | Net move pts | Day type | M5 rows | First bar UTC | Last bar UTC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-19 | 4216.81000 | 4219.41000 | 4121.71000 | 4155.26000 | -6155.00 | down | 240 | 2026-06-18 20:00:00 | 2026-06-19 16:55:00 |

Context CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_CONTEXT_20260619.csv`

## Summary

| Lane | Account | CSV | Closed XAUUSD rows | Closed PnL AED | Win rate | Best session | Worst session | Long PnL AED | Short PnL AED | Open XAUUSD | Would-signals | Orders sent | Orders filled | Guard-blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A1_20260619.csv | 3 | 90.30 | 66.67% | Evening 16:00-19:59 (90.30 AED, 3 trades) | Evening 16:00-19:59 (90.30 AED, 3 trades) | 0.00 | 90.30 | 0 | 38 | 3 | 3 | 35 |
| A2 | 1033030 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A2_20260619.csv | 2 | -23.47 | 0.00% | Evening 16:00-19:59 (-23.47 AED, 2 trades) | Evening 16:00-19:59 (-23.47 AED, 2 trades) | -23.47 | 0.00 | 0 | 9 | 2 | 2 | 7 |
| A3 | 1033669 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A3_20260619.csv | 0 | 0.00 | n/a | n/a | n/a | 0.00 | 0.00 | 0 | 28 | 0 | 0 | 0 |

Total closed XAUUSD rows: 5
Observer/broker join input CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_OBSERVER_JOIN_INPUT_20260619.csv`

## Observer Evidence Refresh

- DirectionState scoreboard refreshed: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/DIRECTION_STATE_SHADOW_SCOREBOARD_2026_06_19.json`
- DirectionState scoreboard status: `PASS`; rows: `18`
- Observer outcome resolution refreshed as dated broker-joined-only output: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/OBSERVER_OUTCOME_RESOLUTION_REPORT_2026_06_19.json`
- Resolution status: `PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS`; signals: `2643`; broker-joined: `2`; unresolved: `2641`
- Replay bars were not supplied for this nightly scan; unresolved rows remain unresolved rather than replay-filled.

## Open XAUUSD Positions

No open XAUUSD positions found.

## Guard Blocks By Reason

### A1 - 1025742

| Reason | Count |
| --- | --- |
| kill_switch_active | 10 |
| repair_direction_filter | 5 |
| repair_time_bucket_filter_Night 20:00-05:59 | 8 |
| server_hour_session_gate | 12 |

### A2 - 1033030

| Reason | Count |
| --- | --- |
| server_hour_session_gate | 7 |

### A3 - 1033669

No guard-block rows in the requested window.

## Raw Broker Query Evidence

| Lane | Account | Server | Currency | Account trade allowed | Terminal trade allowed | Window deals queried | Wide deals queried | Wide orders queried | Terminal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | Capital.ComMena-Demo | AED | True | True | 38 | 4118 | 4122 | C:\Program Files\MetaTrader 5\terminal64.exe |
| A2 | 1033030 | Capital.ComMena-Demo | AED | True | True | 4 | 25 | 24 | C:\MT5PortableTier1BestEA\terminal64.exe |
| A3 | 1033669 | Capital.ComMena-Demo | AED | True | True | 0 | 151 | 150 | C:\MT5PortableRepairLane\terminal64.exe |

## Signal And Order Log Sources

| Lane | Signal files | Order files | Signal rows in window | Order rows in window | Files dir |
| --- | --- | --- | --- | --- | --- |
| A1 | 7 | 7 | 478 | 38 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A2 | 1 | 1 | 239 | 9 | C:\MT5PortableTier1BestEA\MQL5\Files |
| A3 | 6 | 6 | 964 | 0 | C:\MT5PortableRepairLane\MQL5\Files |

## Latest Order Log Tails

### A1 - 1025742

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.17 09:49:56 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | SHORT | 0.01 | 4119131 | 3798672 | pass |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.17 10:49:56 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | LONG | 0.01 | 4119768 | 3799314 | pass |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.18 15:15:00 | session_extreme_retest_v0_repair_v1 | ORDER_SEND_OK | SHORT | 0.01 | 4152145 | 3829220 | pass |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.19 16:10:00 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | kill_switch_active |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.19 16:14:59 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | kill_switch_active |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.19 15:45:00 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | kill_switch_active |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.19 15:59:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | kill_switch_active |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.19 16:10:00 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | kill_switch_active |

### A2 - 1033030

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tier1_bestea_order_log_xauusd.csv | 2026.06.19 16:10:00 | breakout_retest | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | server_hour_session_gate |
| tier1_bestea_order_log_xauusd.csv | 2026.06.19 16:14:59 | breakout_retest | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | server_hour_session_gate |
| tier1_bestea_order_log_xauusd.csv | 2026.06.19 16:50:00 | breakout_retest | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | server_hour_session_gate |

### A3 - 1033669

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a3_breakout_tier1_compat_order_log.csv | 2026.06.17 14:55:00 | A3_BREAKOUT_TIER1_COMPAT | ORDER_SEND_OK | LONG | 0.01 | 4125123 | 3804656 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.16 05:39:57 | RDGUARD_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4096674 | 3778766 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.16 07:04:57 | RDGUARD_V1 | ORDER_SEND_OK | LONG | 0.01 | 4097928 | 3779914 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.16 09:39:57 | RDGUARD_V1 | ORDER_SEND_OK | LONG | 0.01 | 4099954 | 3781914 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.16 08:44:56 | RDSTRUCT_V1 | ORDER_SEND_OK | LONG | 0.01 | 4099362 | 3781321 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.16 09:39:56 | RDSTRUCT_V1 | ORDER_SEND_OK | LONG | 0.01 | 4099953 | 3781913 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.16 11:14:57 | RDSTRUCT_V1 | ORDER_SEND_OK | LONG | 0.01 | 4100781 | 3782725 | PASS |
| a3_soft_retest_v2_order_log.csv | 2026.06.18 18:59:59 | A3_SOFT_RETEST_V2 | ORDER_SEND_OK | SHORT | 0.01 | 4155136 | 3831855 | PASS |

