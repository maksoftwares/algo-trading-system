# A2 Tier-1 Account History Reconciliation - 2026-06-19

Status: `PASS`

Read-only MT5 query against A2 portable terminal. No runtime, EA, preset, chart, order, or position change.

Rows CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A2_TIER1_ACCOUNT_HISTORY_2026_06_19_ROWS.csv`

## Account Reconciliation

| balance_aed | equity_aed | floating_profit_aed | balance_ops_aed | closed_trade_profit_aed | closed_positions | wins | losses | win_rate_pct | open_positions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3944.91 | 3944.91 | 0.00 | 4000.00 | -55.09 | 12 | 4 | 8 | 33.33% | 0 |

Interpretation: `balance = balance_ops + closed_trade_profit`. Current A2 balance `3944.91` equals `4000.00` demo deposit/balance operations plus `-55.09` closed trade PnL.

## By Symbol

| group | rows | wins | losses | win_rate_pct | pnl_aed |
| --- | --- | --- | --- | --- | --- |
| XAUUSD | 12 | 4 | 8 | 33.33% | -55.09 |

## By Candidate

| group | rows | wins | losses | win_rate_pct | pnl_aed |
| --- | --- | --- | --- | --- | --- |
| breakout_retest | 12 | 4 | 8 | 33.33% | -55.09 |

## Boundary

Read-only reconciliation. No MT5 runtime, EA, preset, chart, order, position, profile, or account setting was changed.
