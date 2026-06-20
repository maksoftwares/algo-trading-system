# GOLD Daily Scan - 2026-06-16

Status: `READ_ONLY_SCAN_COMPLETE`

Scan created UTC: `2026-06-16 19:48:04`
Dubai window requested: `2026-06-16 00:00:00` to `2026-06-16 23:59:59`
UTC query window: `2026-06-15 20:00:00` to `2026-06-16 19:59:59`

Demo only. This scan read MT5 broker history/log files and wrote repo reports only. It did not change EA settings, presets, arming flags, profiles, orders, or positions.

## Sample Sizes

| metric | value |
| --- | --- |
| raw_closed_xauusd_rows | 89 |
| unique_signal_count | 76 |
| broker_closed_rows | 89 |
| replay_only_rows | 0 |
| open_xau_positions_at_scan | 9 |

## Gold Context

- Behavior: `UP`
- open 4320.55 -> latest/close 4337.54 (+16.99), high 4354.84, low 4305.71

## T1 - Authoritative Real Broker Fills

CSV: `C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/xauusd-phase1/outputs/reports/XAUUSD_DAILY_ROWS_2026_06_16.csv`

### Raw Per Account

| group | trades | wins | losses | win_rate | pnl_aed_001 |
| --- | --- | --- | --- | --- | --- |
| A1 | 74 | 28 | 46 | 37.84% | -75.48 |
| A3 | 15 | 4 | 11 | 26.67% | -155.49 |

### Deduped Whole Book

| group | trades | wins | losses | win_rate | pnl_aed_001 |
| --- | --- | --- | --- | --- | --- |
| ALL | 76 | 29 | 47 | 38.16% | -230.97 |

### Raw By Session

| group | trades | wins | losses | win_rate | pnl_aed_001 |
| --- | --- | --- | --- | --- | --- |
| Afternoon 12:00-15:59 | 16 | 3 | 13 | 18.75% | -181.26 |
| Evening 16:00-19:59 | 28 | 14 | 14 | 50.00% | 184.99 |
| Morning 06:00-11:59 | 22 | 8 | 14 | 36.36% | -65.03 |
| Night 20:00-05:59 | 23 | 7 | 16 | 30.43% | -169.67 |

## T2 - A3 A/B Head-To-Head

A3 breakout A/B went live around 15:23 Dubai. Today only the plain lane produced broker orders; improved lane has no closed broker fills yet.

### A/B Summary

| group | trades | wins | losses | win_rate | pnl_aed_001 |
| --- | --- | --- | --- | --- | --- |
| 933200 plain | 2 | 0 | 2 | 0.00% | -30.28 |
| 933300 improved | 0 | 0 | 0 | n/a | 0.00 |

### A/B Closed Rows

| account | position_ticket | magic | candidate | direction | entry_time_dubai | exit_time_dubai | session | profit_aed_001 | exit_reason | cost_r | mfe_r | mae_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A3 | 4100993 | 933200 | a3_breakout_plain | SELL | 2026-06-16 15:23:38 | 2026-06-16 15:29:02 | Afternoon 12:00-15:59 | -12.79 | SL | 0.1487 | 0.0000 | 0.9201 |
| A3 | 4101166 | 933200 | a3_breakout_plain | SELL | 2026-06-16 15:40:01 | 2026-06-16 16:08:36 | Afternoon 12:00-15:59 | -17.49 | SL | 0.1130 | 0.2739 | 1.4459 |

### A/B Co-Fired Signals

- Plain would-signals today: `5`
- Improved would-signals today: `5`
- Co-fired plain+improved signals: `5`

### Lane B Management Events

| event | count |
| --- | --- |
| none | 0 |

- `PARTIAL_SKIP_MIN_VOLUME` expected at 0.01 lot if partial logic fires; today no Lane B management event fired. BE is therefore the only practical live modifier, but it also did not fire today.

### Net Of Improvements

No Lane B broker fills and no Lane B management events occurred today, so saved-vs-clipped is `0.00R / 0.00 AED_001` for this scan.

## T3 - Round Shutdown Reconciliation

### Retired Round Magics 933000/933100 Closed Today

| account | position_ticket | magic | candidate | direction | entry_time_dubai | exit_time_dubai | profit_aed_001 | exit_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A3 | 4093038 | 933000 | a3_round_guard_v1 | BUY | 2026-06-16 04:40:01 | 2026-06-16 04:56:31 | 22.58 | TP |
| A3 | 4093603 | 933100 | a3_round_structure_v1 | SELL | 2026-06-16 05:10:00 | 2026-06-16 07:41:48 | -35.67 | SL |
| A3 | 4093605 | 933000 | a3_round_guard_v1 | SELL | 2026-06-16 05:10:01 | 2026-06-16 07:41:49 | -36.63 | SL |
| A3 | 4095943 | 933100 | a3_round_structure_v1 | SELL | 2026-06-16 08:10:03 | 2026-06-16 08:27:10 | 18.36 | TP |
| A3 | 4096255 | 933000 | a3_round_guard_v1 | BUY | 2026-06-16 09:10:00 | 2026-06-16 09:32:31 | -17.52 | SL |
| A3 | 4096257 | 933100 | a3_round_structure_v1 | BUY | 2026-06-16 09:10:01 | 2026-06-16 09:32:31 | -17.64 | SL |
| A3 | 4096674 | 933000 | a3_round_guard_v1 | SELL | 2026-06-16 09:40:01 | 2026-06-16 11:04:57 | -39.20 | SL |
| A3 | 4097928 | 933000 | a3_round_guard_v1 | BUY | 2026-06-16 11:05:00 | 2026-06-16 12:07:33 | 31.21 | TP |
| A3 | 4097926 | 933100 | a3_round_structure_v1 | BUY | 2026-06-16 11:05:00 | 2026-06-16 12:06:34 | 30.73 | TP |
| A3 | 4099362 | 933100 | a3_round_structure_v1 | BUY | 2026-06-16 12:45:00 | 2026-06-16 13:29:33 | -17.60 | SL |
| A3 | 4099953 | 933100 | a3_round_structure_v1 | BUY | 2026-06-16 13:40:00 | 2026-06-16 13:45:54 | -21.83 | SL |
| A3 | 4099954 | 933000 | a3_round_guard_v1 | BUY | 2026-06-16 13:40:01 | 2026-06-16 13:45:54 | -20.98 | SL |
| A3 | 4100781 | 933100 | a3_round_structure_v1 | BUY | 2026-06-16 15:15:01 | 2026-06-16 15:36:35 | -21.02 | SL |

- Residual ticket `4100781`: closed today as SL with PnL -21.02 AED_001.
- New 933000/933100 entries after ~15:23 Dubai: `0` => CLEAN

## T4 - A1/A2 Usual Lanes

### A1/A2 Per Magic And Session

#### A1

| group | trades | wins | losses | win_rate | pnl_aed_001 |
| --- | --- | --- | --- | --- | --- |
| 920101 | 6 | 3 | 3 | 50.00% | 23.01 |
| 920201 | 7 | 2 | 5 | 28.57% | -48.74 |
| 920301 | 15 | 4 | 11 | 26.67% | -68.56 |
| 920401 | 34 | 14 | 20 | 41.18% | 5.62 |
| 920501 | 2 | 1 | 1 | 50.00% | -11.58 |
| 921101 | 10 | 4 | 6 | 40.00% | 24.77 |

By session:

| group | trades | wins | losses | win_rate | pnl_aed_001 |
| --- | --- | --- | --- | --- | --- |
| Afternoon 12:00-15:59 | 10 | 3 | 7 | 30.00% | -69.55 |
| Evening 16:00-19:59 | 28 | 14 | 14 | 50.00% | 184.99 |
| Morning 06:00-11:59 | 16 | 5 | 11 | 31.25% | -70.97 |
| Night 20:00-05:59 | 20 | 6 | 14 | 30.00% | -119.95 |

#### A2

_No rows._

By session:

_No rows._

### A1/A2 Process/Account Snapshot

| account | login | terminal | initialize | server | trade_allowed | expert_allowed | connected |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | C:\Program Files\MetaTrader 5\terminal64.exe | OK | Capital.ComMena-Demo | True | True | True |
| A2 | 1033030 | C:\MT5PortableTier1BestEA\terminal64.exe | OK | Capital.ComMena-Demo | True | True | True |
| A3 | 1033669 | C:\MT5PortableRepairLane\terminal64.exe | OK | Capital.ComMena-Demo | True | True | True |

No preset, arming, profile, or EA config file was edited by this scan.

## T5 - Daily Deduped Totals

### Raw vs Unique

| view | rows | pnl_aed_001 |
| --- | --- | --- |
| raw broker rows | 89 | -230.97 |
| unique-signal groups | 76 | -230.97 |

Single-day warning: all numbers above are one day only. They are useful for tracking and debugging; they are not edge proof.

## Hypothesis Tags

| hypothesis | tag |
| --- | --- |
| H1 round entry has no edge | support |
| H2 afternoon is weak | support |
| H3 counter-trend loses | n/a |
| H4 cost predicts losers | n/a - cost needs multi-day aggregation |
| H5 structure/guard beats alternative | n/a - improved Lane B had no broker fills today |

## What Happened Today

- Gold behavior was `UP`: open 4320.55 -> latest/close 4337.54 (+16.99), high 4354.84, low 4305.71.
- A1 traded actively; A2 had no closed XAU trades today; A3 transitioned away from round lanes toward breakout A/B.
- A3 plain breakout `933200` placed `2` closed trade(s); improved `933300` produced no broker-closed trades today.
- Round shutdown is clean after switchover.
