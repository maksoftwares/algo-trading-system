# A3 Profit-Lock Manager Status - 2026-06-18

Status: `PASS`

Read-only A3 review follow-up. No MT5 runtime, EA, chart, preset, order, position, or profile setting was changed.

Startup log: `C:\MT5PortableRepairLane\MQL5\Files\a3_profit_lock_exit_manager_startup.csv`
Startup latest row: `2026.06.18 05:47:37,A3_PROFIT_LOCK_EXIT_MANAGER_V1_ARMED_20260618,Capital.ComMena-Demo,1033669,XAUUSD,XAUUSD,"933200,933400",false,true,A3_KILL.txt,true,1.25,0.80,false,false,ATTACHED_A3_PROFIT_LOCK_EXIT_MANAGER,OK`
Action CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_PROFIT_LOCK_ACTION_LOG_2026_06_18.csv`

| managed_magics | excluded_magic | managed_closed_trades_in_window | managed_open_positions_now | action_log_exists | SL_moves_sent | SL_moves_failed | dry_run_would_move | DEFER_STOPS_LEVEL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 933200,933400 | 933300 | 15 | 0 | False | 0 | 0 | 0 | 0 |

Interpretation: no profit-lock SLTP move has been logged yet. That is expected when managed trades do not reach the `+1.25R` trigger before closing.
