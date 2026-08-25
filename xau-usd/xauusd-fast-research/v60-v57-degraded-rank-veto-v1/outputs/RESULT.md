# V60 V57 Degraded-Rank Veto V1 Result

Decision: **HISTORICAL_CHALLENGER_PASSES_PROSPECTIVE_CONFIRMATION_REQUIRED**

Retrospective research only. No demo or live deployment is authorized.

| Metric | Deployed V60 | Challenger | Change |
|---|---:|---:|---:|
| Trades | 1390 | 1382 | -8 |
| Net P/L | $3603.57 | $3636.77 | $+33.20 |
| Profit factor | 1.7107 | 1.7223 | +0.0116 |
| Win rate | 48.49% | 48.70% | +0.21 pp |
| Closed drawdown | $223.28 | $223.28 | $+0.00 |
| Equity drawdown | $238.28 | $238.28 | $+0.00 |
| Trades/weekday | 0.970 | 0.964 | -0.006 |

Veto decisions: `8`. Veto endpoint PF: `0.0`.

## Gates

- `baseline_trade_identity`: PASS
- `baseline_net_identity`: PASS
- `net_not_below_baseline`: PASS
- `profit_factor_not_below_baseline`: PASS
- `closed_drawdown_not_above_baseline`: PASS
- `equity_drawdown_not_above_baseline`: PASS
- `trade_retention`: PASS
- `frequency_retention`: PASS
- `no_negative_calendar_year_delta`: PASS
- `recent_windows_not_worse`: PASS
- `veto_cohort_large_enough`: PASS
- `veto_cohort_profit_factor_below_one`: PASS
