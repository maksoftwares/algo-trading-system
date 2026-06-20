# EOD GOLD Scan Report - 2026-06-18

Generated UTC: 2026-06-18 20:00:00
Generated Dubai: 2026-06-19 00:00:00
Window UTC: 2026-06-17 20:00:00 through 2026-06-18 20:00:00
Entry lookup window UTC: 2026-06-01 00:00:00 through 2026-06-18 20:00:00

Boundary: read-only export. No EA, preset, chart, terminal, or broker setting was changed.

## Gold Day Context

| Date | Open | High | Low | Close | Net move pts | Day type | M5 rows | First bar UTC | Last bar UTC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-18 | 4235.43000 | 4329.84000 | 4201.26000 | 4216.52000 | -1891.00 | down | 277 | 2026-06-17 20:00:00 | 2026-06-18 20:00:00 |

Context CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_CONTEXT_20260618.csv`

## Summary

| Lane | Account | CSV | Closed XAUUSD rows | Closed PnL AED | Win rate | Best session | Worst session | Long PnL AED | Short PnL AED | Open XAUUSD | Would-signals | Orders sent | Orders filled | Guard-blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A1_20260618.csv | 22 | -138.83 | 27.27% | Evening 16:00-19:59 (107.56 AED, 14 trades) | Night 20:00-05:59 (-177.38 AED, 2 trades) | 48.57 | -187.40 | 0 | 94 | 21 | 21 | 73 |
| A2 | 1033030 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A2_20260618.csv | 1 | -44.12 | 0.00% | Evening 16:00-19:59 (-44.12 AED, 1 trades) | Evening 16:00-19:59 (-44.12 AED, 1 trades) | 0.00 | -44.12 | 0 | 12 | 1 | 1 | 11 |
| A3 | 1033669 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A3_20260618.csv | 12 | -299.97 | 16.67% | Morning 06:00-11:59 (-149.02 AED, 9 trades) | Night 20:00-05:59 (-150.95 AED, 3 trades) | 0.00 | -299.97 | 0 | 37 | 11 | 11 | 0 |

Total closed XAUUSD rows: 35
Observer/broker join input CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_OBSERVER_JOIN_INPUT_20260618.csv`

## Observer Evidence Refresh

- Observer refresh skipped by operator flag.

## Open XAUUSD Positions

No open XAUUSD positions found.

## Guard Blocks By Reason

### A1 - 1025742

| Reason | Count |
| --- | --- |
| WOULD_DUPLICATE_FAMILY_EVENT | 9 |
| kill_switch_active | 15 |
| repair_direction_filter | 27 |
| repair_time_bucket_filter_Afternoon 12:00-15:59 | 3 |
| repair_time_bucket_filter_Morning 06:00-11:59 | 5 |
| repair_time_bucket_filter_Night 20:00-05:59 | 14 |

### A2 - 1033030

| Reason | Count |
| --- | --- |
| open_instance_exposure_exists | 1 |
| server_hour_session_gate | 10 |

### A3 - 1033669

No guard-block rows in the requested window.

## Raw Broker Query Evidence

| Lane | Account | Server | Currency | Account trade allowed | Terminal trade allowed | Window deals queried | Wide deals queried | Wide orders queried | Terminal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | Capital.ComMena-Demo | AED | True | True | 215 | 4080 | 4084 | C:\Program Files\MetaTrader 5\terminal64.exe |
| A2 | 1033030 | Capital.ComMena-Demo | AED | True | True | 2 | 21 | 20 | C:\MT5PortableTier1BestEA\terminal64.exe |
| A3 | 1033669 | Capital.ComMena-Demo | AED | True | True | 23 | 151 | 150 | C:\MT5PortableRepairLane\terminal64.exe |

## Signal And Order Log Sources

| Lane | Signal files | Order files | Signal rows in window | Order rows in window | Files dir |
| --- | --- | --- | --- | --- | --- |
| A1 | 7 | 7 | 1249 | 94 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A2 | 1 | 1 | 276 | 12 | C:\MT5PortableTier1BestEA\MQL5\Files |
| A3 | 6 | 6 | 902 | 11 | C:\MT5PortableRepairLane\MQL5\Files |

## Latest Order Log Tails

### A1 - 1025742

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.17 09:49:56 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | SHORT | 0.01 | 4119131 | 3798672 | pass |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.17 10:49:56 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | LONG | 0.01 | 4119768 | 3799314 | pass |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.18 13:40:01 | session_extreme_retest_v0_repair_v1 | ORDER_SEND_OK | SHORT | 0.01 | 4150114 | 3827436 | pass |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.18 14:30:00 | session_extreme_retest_v0_repair_v1 | ORDER_SEND_OK | SHORT | 0.01 | 4151310 | 3828626 | pass |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.18 15:15:00 | session_extreme_retest_v0_repair_v1 | ORDER_SEND_OK | SHORT | 0.01 | 4152145 | 3829220 | pass |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.18 18:49:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | kill_switch_active |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.18 18:54:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | kill_switch_active |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.18 19:49:58 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | kill_switch_active |

### A2 - 1033030

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tier1_bestea_order_log_xauusd.csv | 2026.06.18 18:39:58 | breakout_retest | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | server_hour_session_gate |
| tier1_bestea_order_log_xauusd.csv | 2026.06.18 18:54:58 | breakout_retest | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | server_hour_session_gate |
| tier1_bestea_order_log_xauusd.csv | 2026.06.18 18:59:58 | breakout_retest | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | server_hour_session_gate |

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

