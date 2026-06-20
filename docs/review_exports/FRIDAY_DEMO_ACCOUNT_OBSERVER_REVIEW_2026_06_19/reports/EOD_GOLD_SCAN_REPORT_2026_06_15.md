# EOD GOLD Scan Report - 2026-06-15

Generated UTC: 2026-06-15 20:03:17
Generated Dubai: 2026-06-16 00:03:17
Window UTC: 2026-06-14 22:00:00 through 2026-06-15 20:03:17
Entry lookup window UTC: 2026-06-01 00:00:00 through 2026-06-15 20:03:17

Boundary: read-only export. No EA, preset, chart, terminal, or broker setting was changed.

## Gold Day Context

| Date | Open | High | Low | Close | Net move pts | Day type | M5 rows | First bar UTC | Last bar UTC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-15 | 4236.31000 | 4369.18000 | 4236.31000 | 4320.03000 | 8372.00 | up | 265 | 2026-06-14 22:00:00 | 2026-06-15 20:00:00 |

Context CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_CONTEXT_20260615.csv`

## Summary

| Lane | Account | CSV | Closed XAUUSD rows | Closed PnL AED | Win rate | Best session | Worst session | Long PnL AED | Short PnL AED | Open XAUUSD | Would-signals | Orders sent | Orders filled | Guard-blocks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A1_20260615.csv | 66 | 426.30 | 45.45% | Evening 16:00-19:59 (306.02 AED, 17 trades) | Afternoon 12:00-15:59 (-197.48 AED, 13 trades) | 659.85 | -233.55 | 2 | 180 | 66 | 66 | 110 |
| A2 | 1033030 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A2_20260615.csv | 1 | 49.71 | 100.00% | Evening 16:00-19:59 (49.71 AED, 1 trades) | Evening 16:00-19:59 (49.71 AED, 1 trades) | 49.71 | 0.00 | 0 | 10 | 1 | 1 | 9 |
| A3 | 1033669 | C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_A3_20260615.csv | 36 | 62.20 | 38.89% | Night 20:00-05:59 (145.30 AED, 11 trades) | Afternoon 12:00-15:59 (-106.13 AED, 9 trades) | 394.85 | -332.65 | 2 | 100 | 38 | 38 | 0 |

Total closed XAUUSD rows: 103
Observer/broker join input CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/EOD_GOLD_OBSERVER_JOIN_INPUT_20260615.csv`

## Observer Evidence Refresh

- DirectionState scoreboard refreshed: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/DIRECTION_STATE_SHADOW_SCOREBOARD_2026_06_15.json`
- DirectionState scoreboard status: `PASS`; rows: `18`
- Observer outcome resolution refreshed as dated broker-joined-only output: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/OBSERVER_OUTCOME_RESOLUTION_REPORT_2026_06_15.json`
- Resolution status: `PARTIAL_REVIEW_NEEDS_FRESH_M5_BARS`; signals: `1645`; broker-joined: `64`; unresolved: `1581`
- Replay bars were not supplied for this nightly scan; unresolved rows remain unresolved rather than replay-filled.

## Open XAUUSD Positions

| Lane | Account | Ticket | Candidate | Magic | Direction | Lots | Entry | Floating PnL AED |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | 4087306 | symbol_normalized_round_retest_v0 | 920301 | BUY | 0.01000 | 4321.05000 | -3.75 |
| A1 | 1025742 | 4089437 | symbol_normalized_round_retest_v0 | 920301 | SELL | 0.01000 | 4321.49000 | 3.52 |
| A3 | 1033669 | 4089439 | a3_round_retest_guarded_v1 | 933000 | SELL | 0.01000 | 4321.51000 | 3.60 |
| A3 | 1033669 | 4089440 | a3_round_retest_structured_v1 | 933100 | SELL | 0.01000 | 4321.51000 | 3.60 |

## Guard Blocks By Reason

### A1 - 1025742

| Reason | Count |
| --- | --- |
| WOULD_DUPLICATE_FAMILY_EVENT | 56 |
| repair_direction_filter | 26 |
| repair_time_bucket_filter_Afternoon 12:00-15:59 | 11 |
| repair_time_bucket_filter_Morning 06:00-11:59 | 11 |
| repair_time_bucket_filter_Night 20:00-05:59 | 6 |

### A2 - 1033030

| Reason | Count |
| --- | --- |
| open_instance_exposure_exists | 2 |
| terminal_or_account_trading_disabled | 7 |

### A3 - 1033669

No guard-block rows in the requested window.

## Raw Broker Query Evidence

| Lane | Account | Server | Currency | Account trade allowed | Terminal trade allowed | Window deals queried | Wide deals queried | Wide orders queried | Terminal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | Capital.ComMena-Demo | AED | True | True | 256 | 3279 | 3283 | C:\Program Files\MetaTrader 5\terminal64.exe |
| A2 | 1033030 | Capital.ComMena-Demo | AED | True | True | 2 | 17 | 16 | C:\MT5PortableTier1BestEA\terminal64.exe |
| A3 | 1033669 | Capital.ComMena-Demo | AED | True | True | 74 | 75 | 74 | C:\MT5PortableRepairLane\terminal64.exe |

## Signal And Order Log Sources

| Lane | Signal files | Order files | Signal rows in window | Order rows in window | Files dir |
| --- | --- | --- | --- | --- | --- |
| A1 | 7 | 7 | 1855 | 180 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A2 | 1 | 1 | 265 | 10 | C:\MT5PortableTier1BestEA\MQL5\Files |
| A3 | 2 | 2 | 530 | 38 | C:\MT5PortableRepairLane\MQL5\Files |

## Latest Order Log Tails

### A1 - 1025742

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.15 18:34:59 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | SHORT | 0.01 | 4087561 | 3770239 | pass |
| experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | 2026.06.15 19:09:59 | symbol_normalized_round_retest_v0 | ORDER_SEND_OK | SHORT | 0.01 | 4089437 | 3771812 | pass |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.15 12:35:00 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | repair_direction_filter |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.15 12:40:00 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | repair_direction_filter |
| phase2_demo_repair_executor_order_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | 2026.06.15 16:59:59 | session_extreme_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | repair_direction_filter |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.15 18:14:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | repair_direction_filter |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.15 18:34:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | repair_time_bucket_filter_Night 20:00-05:59 |
| phase2_demo_repair_executor_order_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | 2026.06.15 19:09:59 | symbol_normalized_round_retest_v0_repair_v1 | GUARD_BLOCK | SHORT | 0.00 | 0 | 0 | repair_time_bucket_filter_Night 20:00-05:59 |

### A2 - 1033030

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tier1_bestea_order_log_xauusd.csv | 2026.06.15 12:40:01 | breakout_retest | ORDER_SEND_OK | LONG | 0.01 | 4079369 | 3762867 | pass |
| tier1_bestea_order_log_xauusd.csv | 2026.06.15 12:45:00 | breakout_retest | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | open_instance_exposure_exists |
| tier1_bestea_order_log_xauusd.csv | 2026.06.15 13:15:00 | breakout_retest | GUARD_BLOCK | LONG | 0.00 | 0 | 0 | open_instance_exposure_exists |

### A3 - 1033669

| File | UTC | Candidate/comment | Action | Direction | Volume | Order | Deal | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a3_rdguard_v1_order_log.csv | 2026.06.15 17:55:00 | RDGUARD_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4087126 | 3769849 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.15 18:35:00 | RDGUARD_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4087562 | 3770240 | PASS |
| a3_rdguard_v1_order_log.csv | 2026.06.15 19:10:00 | RDGUARD_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4089439 | 3771814 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.15 17:55:00 | RDSTRUCT_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4087125 | 3769848 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.15 18:35:00 | RDSTRUCT_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4087563 | 3770241 | PASS |
| a3_rdstruct_v1_order_log.csv | 2026.06.15 19:10:00 | RDSTRUCT_V1 | ORDER_SEND_OK | SHORT | 0.01 | 4089440 | 3771815 | PASS |

