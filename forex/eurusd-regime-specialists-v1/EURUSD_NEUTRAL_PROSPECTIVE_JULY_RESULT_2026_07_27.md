# EURUSD Regime 1 Neutral prospective July result

Date: 2026-07-27

Decision: `ACCUMULATING_PROSPECTIVE_EVIDENCE`

This was a one-shot diagnostic of the frozen, historically rejected
volatility-scaled tick model. It is not an admitted strategy and cannot
authorize demo or live trading.

## Frozen test

- The preregistration and configuration were SHA-256 locked before bulk
  acquisition of the July FX ticks.
- The probability threshold remained 0.375, selected only on the
  2021-2022 development period.
- Training used 83,611 rows whose complete target/stop outcomes ended
  strictly before 2026-07-01 00:00 UTC.
- Inference covered 2026-07-01 00:00 through 2026-07-27 02:59 UTC.
- No feature, threshold, model, direction, hour, or lifecycle parameter was
  repaired after seeing July.
- Execution retained exact bid/ask prices, a 0.70-pip minimum spread,
  0.10-pip adverse slippage per side, stop-first ambiguous bars, one open
  position, and a maximum of four trades per UTC day.

## Result

| Metric | July prospective value | Gate |
|---|---:|---:|
| Completed trades | 19 | At least 100 |
| Calendar days | 27 | At least 60 |
| Active weekdays | 19 | Diagnostic |
| Win rate | 31.58% | 45%-55% |
| Realized payoff ratio | 1.459 | 1.35-1.75 |
| Profit factor | 0.673 | At least 1.10 |
| Net result | -4.317R | Positive |
| Expectancy | -0.227R/trade | Positive |
| Maximum drawdown | 4.783R | Diagnostic |
| Frequency | 1.00 trade/active weekday | Diagnostic |

The payoff shape remained close to the requested 1.50, but the win rate was
far below the approximately 41% break-even level for this realized payoff.
The model generated 18 long trades and one short trade, concentrated on only
eight UTC dates. Six trades won and thirteen lost.

Both the sample gate and the metric gate failed. Because the sample gate is
incomplete, these metrics are explicitly non-promotional. They also point in
the same negative direction as the 2023-2026 H1 chronological result
(PF 0.791).

## Source coverage

The run downloaded 639 hourly files per symbol for EURUSD, GBPUSD, and
USDJPY. Weekend/closed-market hours were retained as empty files; each symbol
had 447 populated hours.

| Symbol | Ticks | First tick UTC | Last tick UTC | Source-chain SHA-256 |
|---|---:|---|---|---|
| EURUSD | 1,083,228 | 2026-07-01 00:00:00.240 | 2026-07-27 14:59:59.092 | `ab3b3e6454d2ca074d8ca0753c3980977f6b6e6a34f573c6278f2d0f3e7d0266` |
| GBPUSD | 1,729,387 | 2026-07-01 00:00:00.552 | 2026-07-27 14:59:59.823 | `68728ecd7ce4ff703067aecf45353d70e8e810cf9d31ec39e06ff704e189b03d` |
| USDJPY | 1,577,803 | 2026-07-01 00:00:00.188 | 2026-07-27 14:59:59.966 | `baa1a5ce72a096eb08207ecd88c8226bdab209a2caeeca201768ee745efab1e9` |

The DXY and U.S. Treasury-bond context archives both extended through
2026-07-27 14:00 UTC and are source-hashed in `RESULT.json`.

## Interpretation and next action

This result does not solve or materially improve Regime 1. Retuning on these
19 trades would convert the prospective sample into another retrospective
optimization set.

The locked model may continue accumulating untouched observations until both
the 100-trade and 60-calendar-day gates are met, but its status remains
research diagnostic only. A new candidate strategy requires a separately
preregistered hypothesis and a future holdout that this campaign has not
seen. Until a causal candidate clears those gates, Regime 1 remains `CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_prospective.py
```
