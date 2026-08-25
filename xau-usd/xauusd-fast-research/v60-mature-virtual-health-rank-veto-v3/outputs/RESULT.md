# V60 Mature Virtual-Health Rank Veto V3 Result

Decision: **KEEP_DEPLOYED_V60**

Retrospective research only. No demo or live deployment is authorized.

| Metric | Deployed V60 | Challenger | Change |
|---|---:|---:|---:|
| Trades | 1390 | 1397 | +7 |
| Net P/L | $3603.57 | $3632.18 | $+28.61 |
| Profit factor | 1.7107 | 1.7155 | +0.0048 |
| Win rate | 48.49% | 48.53% | +0.04 pp |
| Closed drawdown | $223.28 | $218.91 | $-4.37 |
| Equity drawdown | $238.28 | $236.21 | $-2.07 |
| Trades/weekday | 0.970 | 0.975 | +0.005 |

Veto decisions: `16`; baseline-executed cohort: `14`. Baseline runtime PF: `0.7376929949186495`. Candidate endpoint PF: `1.046066391442134`.

## Gates

- `baseline_trade_identity`: PASS
- `baseline_net_identity`: PASS
- `net_not_below_baseline`: PASS
- `profit_factor_not_below_baseline`: PASS
- `closed_drawdown_not_above_baseline`: PASS
- `equity_drawdown_not_above_baseline`: PASS
- `trade_retention`: PASS
- `frequency_retention`: PASS
- `no_negative_calendar_year_delta`: FAIL
- `recent_windows_not_worse`: FAIL
- `veto_cohort_large_enough`: PASS
- `veto_cohort_profit_factor_below_one`: PASS
