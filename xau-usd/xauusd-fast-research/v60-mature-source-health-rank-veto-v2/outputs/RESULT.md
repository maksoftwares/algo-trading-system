# V60 Mature Source-Health Rank Veto V2 Result

Decision: **HISTORICAL_CHALLENGER_PASSES_PROSPECTIVE_CONFIRMATION_REQUIRED**

Retrospective research only. No demo or live deployment is authorized.

| Metric | Deployed V60 | Challenger | Change |
|---|---:|---:|---:|
| Trades | 1390 | 1378 | -12 |
| Net P/L | $3603.57 | $3655.75 | $+52.19 |
| Profit factor | 1.7107 | 1.7289 | +0.0181 |
| Win rate | 48.49% | 48.84% | +0.35 pp |
| Closed drawdown | $223.28 | $217.46 | $-5.82 |
| Equity drawdown | $238.28 | $238.28 | $+0.00 |
| Trades/weekday | 0.970 | 0.962 | -0.008 |

Veto decisions: `12`. Veto endpoint PF: `0.0`.

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
