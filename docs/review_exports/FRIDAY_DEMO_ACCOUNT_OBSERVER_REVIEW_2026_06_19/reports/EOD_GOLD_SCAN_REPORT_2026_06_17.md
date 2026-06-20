# EOD GOLD Scan Report - 2026-06-17

Generated UTC: 2026-06-17 19:29:36
Generated Dubai: 2026-06-17 23:29:36
Window UTC: 2026-06-16 20:00:00 through 2026-06-17 19:29:36
Entry lookup window UTC: 2026-06-01 00:00:00 through 2026-06-17 19:29:36

Boundary: read-only export. No EA, preset, chart, terminal, or broker setting was changed.

## Gold Day Context

| Date | Open | High | Low | Close | Net move pts | Day type | M5 rows | First bar UTC | Last bar UTC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-17 | 4333.76000 | 4382.10000 | 4226.27000 | 4227.41000 | -10635.00 | down | 270 | 2026-06-16 20:00:00 | 2026-06-17 19:25:00 |

Context CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_CONTEXT_20260617.csv`

## Summary

| Lane | Account | CSV | Closed XAUUSD rows | Closed PnL AED | Win rate | Best session | Worst session | Long PnL AED | Short PnL AED | Open XAUUSD | Would-signals | Orders sent | Orders filled | Guard-blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A1_20260617.csv | 71 | -344.60 | 30.99% | Afternoon 12:00-15:59 (-8.31 AED, 13 trades) | Morning 06:00-11:59 (-203.17 AED, 25 trades) | -332.58 | -12.02 | 1 | 186 | 67 | 67 | 119 |
| A2 | 1033030 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A2_20260617.csv | 1 | -92.42 | 0.00% | Evening 16:00-19:59 (-92.42 AED, 1 trades) | Evening 16:00-19:59 (-92.42 AED, 1 trades) | -92.42 | 0.00 | 0 | 16 | 1 | 1 | 15 |
| A3 | 1033669 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A3_20260617.csv | 10 | -404.90 | 0.00% | Afternoon 12:00-15:59 (-16.46 AED, 1 trades) | Evening 16:00-19:59 (-184.95 AED, 2 trades) | -303.27 | -101.63 | 1 | 43 | 10 | 10 | 0 |

Total closed XAUUSD rows: 82
Observer/broker join input CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_OBSERVER_JOIN_INPUT_20260617.csv`

## Observer Evidence Refresh

- DirectionState scoreboard refreshed: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/DIRECTION_STATE_SHADOW_SCOREBOARD_2026_06_17.json`
- DirectionState scoreboard status: `PASS`; rows: `18`
- Observer outcome resolution refreshed as dated broker-joined-only output: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/OBSERVER_OUTCOME_RESOLUTION_REPORT_2026_06_17.json`
- Resolution status: `PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS`; signals: `2204`; broker-joined: `73`; unresolved: `2131`
- Replay bars were not supplied for this nightly scan; unresolved rows remain unresolved rather than replay-filled.

## Open XAUUSD Positions

| Lane | Account | Ticket | Candidate | Magic | Direction | Lots | Entry | Floating PnL AED |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | 4132283 | breakout_retest | 920101 | SELL | 0.01000 | 4271.75000 | 159.71 |
| A3 | 1033669 | 4132280 | breakout_retest | 933200 | SELL | 0.01000 | 4271.78000 | 160.15 |

## Guard Blocks By Reason

### A1 - 1025742

| Reason | Count |
| --- | --- |
| WOULD_DUPLICATE_FAMILY_EVENT | 49 |
| repair_cluster_filter_XAUUSD_Night 20:00-05:59 | 1 |
| repair_direction_filter | 44 |
| repair_time_bucket_filter_Afternoon 12:00-15:59 | 6 |
| repair_time_bucket_filter_Morning 06:00-11:59 | 7 |
| repair_time_bucket_filter_Night 20:00-05:59 | 12 |

### A2 - 1033030

| Reason | Count |
| --- | --- |
| open_instance_exposure_exists | 2 |
| server_hour_session_gate | 13 |

### A3 - 1033669

No guard-block rows in the requested window.

## Raw Broker Query Evidence

| Lane | Account | Server | Currency | Account trade allowed | Terminal trade allowed | Window deals queried | Wide deals queried | Wide orders queried | Terminal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | Capital.ComMena-Demo | AED | True | True | 283 | 3864 | 3868 | C:\Program Files\MetaTrader 5\terminal64.exe |
| A2 | 1033030 | Capital.ComMena-Demo | AED | True | True | 2 | 19 | 18 | C:\MT5PortableTier1BestEA\terminal64.exe |
| A3 | 1033669 | Capital.ComMena-Demo | AED | True | True | 20 | 128 | 127 | C:\MT5PortableRepairLane\terminal64.exe |

## Signal And Order Log Sources

| Lane | Signal files | Order files | Signal rows in window | Order rows in window | Files dir |
| --- | --- | --- | --- | --- | --- |
| A1 | 7 | 7 | 1694 | 186 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A2 | 1 | 1 | 269 | 16 | C:\MT5PortableTier1BestEA\MQL5\Files |
| A3 | 5 | 5 | 654 | 10 | C:\MT5PortableRepairLane\MQL5\Files |

## Latest Order Log Tails

### A1 - 1025742

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.17 09:49:56 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | SHORT | 0.01 | 4119131 | 3798672 | pass |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.17 10:49:56 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | LONG | 0.01 | 4119768 | 3799314 | pass |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.17 14:54:59 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | repair_direction_filter |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.17 15:24:59 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | repair_direction_filter |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.17 18:59:59 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | repair_cluster_filter_XAUUSD_Night 20:00-05:59 |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.17 18:59:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | repair_time_bucket_filter_Night 20:00-05:59 |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.17 19:04:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | repair_time_bucket_filter_Night 20:00-05:59 |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.17 19:09:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | repair_time_bucket_filter_Night 20:00-05:59 |

### A2 - 1033030

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tier1_bestea_order_log_xauusd.csv | 2026.06.17 17:34:59 | breakout_retest | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | server_hour_session_gate |
| tier1_bestea_order_log_xauusd.csv | 2026.06.17 18:24:59 | breakout_retest | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | server_hour_session_gate |
| tier1_bestea_order_log_xauusd.csv | 2026.06.17 19:04:59 | breakout_retest | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | server_hour_session_gate |

### A3 - 1033669

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a3_breakout_plain_order_log.csv | 2026.06.17 19:04:59 | A3_BREAKOUT_PLAIN | ORDER_SEND_OK | SHORT | 0.01 | 4132280 | 3811828 | PASS |
| a3_breakout_tier1_compat_order_log.csv | 2026.06.17 14:55:00 | A3_BREAKOUT_TIER1_COMPAT | ORDER_SEND_OK | LONG | 0.01 | 4125123 | 3804656 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.16 05:39:57 | RDGUARD_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4096674 | 3778766 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.16 07:04:57 | RDGUARD_V1 | ORDER_SEND_OK | LONG | 0.01 | 4097928 | 3779914 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.16 09:39:57 | RDGUARD_V1 | ORDER_SEND_OK | LONG | 0.01 | 4099954 | 3781914 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.16 08:44:56 | RDSTRUCT_V1 | ORDER_SEND_OK | LONG | 0.01 | 4099362 | 3781321 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.16 09:39:56 | RDSTRUCT_V1 | ORDER_SEND_OK | LONG | 0.01 | 4099953 | 3781913 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.16 11:14:57 | RDSTRUCT_V1 | ORDER_SEND_OK | LONG | 0.01 | 4100781 | 3782725 | PASS |

