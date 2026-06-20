# XAU H1/H4 Trend Continuation Pullback V0.1 Screen - 2026-06-19

Status: `PASS`
Decision: `FAIL_INSUFFICIENT_BOTH_DIRECTION_SAMPLE`

Offline Phase 0R screen only. No MT5 terminal, profile, chart, preset, order, position, or broker runtime state was touched.

## Hypothesis Lock

- Path: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0r\hypotheses\hypothesis_xau_h1_h4_trend_continuation_pullback_v0_1.md`
- Manifest status: `FOUND`
- SHA256: `5af38049a3c511732a9efc2bdaa3f238ad68dceb5b105b59aad1700a0233b672`

## Metrics

| Metric | Value |
| --- | ---: |
| Closed trades | 7 |
| Long / Short | 6 / 1 |
| Win rate | 28.57% |
| Net PF | 0.5256 |
| Net expectancy R | -0.3723 |
| Total net R | -2.6061 |
| Stress PF | 0.5068 |
| Stress expectancy R | -0.395 |
| P95 cost R | 0.1174 |
| Max cost R | 0.1189 |
| Max DD R | 4.0488 |
| Worst day R | -1.1189 |
| Best 2 days removed R | -5.494 |
| Up-day / Down-day R | 0.3238 / -2.9299 |
| t-stat | -0.7938 |

## Stage Funnel

Counts are direction-candidate checks through the locked V0.1 rule, ordered by the reviewer-requested funnel. `Cost-passed` should match the unscheduled signal count; `opened` is after the one-position scheduling rule.

| Stage | Count |
| --- | ---: |
| Candidate direction checks | 76446 |
| Trend-eligible | 31875 |
| Pullback-eligible | 210 |
| M5-trigger-eligible | 31 |
| Cost-passed raw signals | 19 |
| Opened after one-position scheduling | 7 |
| Scheduled out by one-position rule | 12 |

| Direction Split | Cost-Passed | Opened |
| --- | ---: | ---: |
| LONG | 18 | 6 |
| SHORT | 1 | 1 |

- Cost-passed count matches signal count: `True`.

## Gates

| Gate | Status |
| --- | --- |
| `sample_gate_pass` | `False` |
| `net_gate_pass` | `False` |
| `stress_gate_pass` | `False` |
| `cost_gate_pass` | `False` |
| `drawdown_gate_pass` | `True` |
| `worst_day_gate_pass` | `False` |
| `best_days_removed_gate_pass` | `False` |
| `both_regime_gate_pass` | `False` |
| `significance_gate_pass` | `False` |

## Interpretation

- Screen-window status: `INSUFFICIENT_BOTH_DIRECTION_SAMPLE`.
- Failure reasons: `sample_gate_pass, net_gate_pass, stress_gate_pass, cost_gate_pass, worst_day_gate_pass, best_days_removed_gate_pass, both_regime_gate_pass, significance_gate_pass`.
- This is an offline Phase 0R screen only. Passing would not authorize broker action.
- V0.1 fails discovery and is not forward-validation eligible. Because the sample is only seven opened trades, this is recorded as an insufficient-frequency/both-direction failure, not as a mature trend-continuation expectancy falsification.
- Per the locked no-tuning rule, do not loosen V0.1 after seeing this screen just to increase trade count.

## Outputs

- json: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0r\outputs\reports\XAU_H1_H4_TREND_CONTINUATION_PULLBACK_V0_1_SCREEN_2026_06_19.json`
- markdown: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0r\outputs\reports\XAU_H1_H4_TREND_CONTINUATION_PULLBACK_V0_1_SCREEN_2026_06_19.md`
- trades_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0r\outputs\reports\XAU_H1_H4_TREND_CONTINUATION_PULLBACK_V0_1_TRADES_2026_06_19.csv`
