# A3 Repair-Lane Account History Reconciliation - 2026-06-19

Status: `PASS`

Read-only MT5 query against A3 portable terminal. No runtime, EA, preset, chart, order, or position change.

Closed rows CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_19_CLOSED_ROWS.csv`
Open rows CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_REPAIR_LANE_ACCOUNT_HISTORY_2026_06_19_OPEN_ROWS.csv`

## Account Reconciliation

| balance_aed | equity_aed | floating_profit_aed | balance_ops_aed | closed_trade_gross_profit_aed | closed_trade_net_profit_aed | closed_positions | wins | losses | win_rate_pct | open_positions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3261.62 | 3261.62 | 0.00 | 4000.00 | -738.28 | -738.38 | 75 | 22 | 53 | 29.33% | 0 |

Interpretation: A3 balance is reconciled from fresh MT5 history. Net PnL includes commissions/fees/swap where MT5 reports them; gross trade profit is shown separately because older CSV exports often used gross profit only.

## By Symbol

| group | rows | wins | losses | win_rate_pct | gross_profit_aed | net_profit_aed |
| --- | --- | --- | --- | --- | --- | --- |
| XAUUSD | 75 | 22 | 53 | 29.33% | -738.28 | -738.38 |

## By Candidate

| group | rows | wins | losses | win_rate_pct | gross_profit_aed | net_profit_aed |
| --- | --- | --- | --- | --- | --- | --- |
| UNKNOWN | 2 | 1 | 1 | 50.00% | -68.67 | -68.67 |
| a3_breakout_improved | 8 | 1 | 7 | 12.50% | -157.26 | -156.04 |
| a3_breakout_plain | 14 | 0 | 14 | 0.00% | -509.12 | -510.44 |
| a3_round_retest_guarded_v1 | 26 | 10 | 16 | 38.46% | -38.20 | -38.20 |
| a3_round_retest_structured_v1 | 25 | 10 | 15 | 40.00% | 34.97 | 34.97 |

## By Session

| group | rows | wins | losses | win_rate_pct | gross_profit_aed | net_profit_aed |
| --- | --- | --- | --- | --- | --- | --- |
| Afternoon 12:00-15:59 | 16 | 2 | 14 | 12.50% | -234.30 | -234.30 |
| Evening 16:00-19:59 | 9 | 3 | 6 | 33.33% | -161.79 | -161.79 |
| Morning 06:00-11:59 | 27 | 7 | 20 | 25.93% | -180.14 | -180.14 |
| Night 20:00-05:59 | 23 | 10 | 13 | 43.48% | -162.05 | -162.15 |

## Boundary

Read-only reconciliation. No MT5 runtime, EA, preset, chart, order, position, profile, or account setting was changed.
