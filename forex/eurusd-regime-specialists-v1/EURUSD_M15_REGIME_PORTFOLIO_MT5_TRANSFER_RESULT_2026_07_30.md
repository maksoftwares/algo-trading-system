# EURUSD M15 regime-portfolio MT5 transfer result

Status: **BROKER_TRANSFER_PASSED_PROSPECTIVE_SHADOW_ONLY**

The frozen M15 first-break portfolio compiled with zero errors and zero
warnings and completed a Capital.com every-real-tick transfer without any rule
change.

| Window | Trades | Trades/weekday | Win rate | Payoff | PF | Executable P&L | Research-equivalent P&L |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full two years | 106 | 0.203 | 49.06% | 1.465 | 1.411 | $+61.60 | $+30.80 |
| First 12 months | 45 | - | 48.89% | 1.414 | 1.352 | $+22.72 | $+11.36 |
| Second 12 months | 61 | - | 49.18% | 1.503 | 1.454 | $+38.88 | $+19.44 |
| Chop | 74 | - | 54.05% | 1.350 | 1.588 | $+67.06 | $+33.53 |
| Compression | 32 | - | 37.50% | 1.414 | 0.849 | $-5.46 | $-2.73 |

Broker history quality was `98%`.
Maximum balance/equity drawdown was
`25.77 (0.26%)` /
`26.79 (0.27%)`.

After removing the best 6 trades, PF was
1.107.

## Frozen gates

| Gate | Passed |
|---|---|
| minimum_trades | True |
| minimum_trades_per_weekday | True |
| minimum_full_profit_factor | True |
| minimum_each_12_month_profit_factor | True |
| minimum_latest_12_month_profit_factor | True |
| minimum_net_pnl_usd | True |
| minimum_best_5pct_removed_profit_factor | True |
| maximum_balance_drawdown_percent | True |

## Audit note

The frozen EA's CSV writer omitted the header row, but every one of the
`218` data rows has the exact frozen 18-column schema.
The verifier supplies that fixed schema without changing or rerunning the
strategy. There were `106` signals,
`106` successful entries, zero failed sends, and
zero initialization failures.

## Decision

The unchanged rule passes the preregistered broker-transfer gates and may move
to prospective **shadow observation only**. Demo orders remain disallowed until
fresh evidence passes its separate admission protocol. Its broker frequency is
only 0.203 trades per weekday, so it preserves the
edge core but does not by itself achieve the final one-trade-per-day goal.
