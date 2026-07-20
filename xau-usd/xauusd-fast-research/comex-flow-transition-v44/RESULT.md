# COMEX Flow-Transition V44 Result

## Decision

`V44_DEVELOPMENT_FAIL_TERMINAL`

The family reached the missing frequency but failed economics decisively. It is
permanently rejected. Validation and exam remain sealed. Same-version tuning,
threshold repair, direction mirroring, and economic-rule changes are forbidden.

## Outcome-Blind Calibration

- Eligible full weekdays: 20.
- Registered policies: exactly 1,000.
- Selected candidate rows: 58, or 2.90/full weekday.
- Active-day share: 90%.
- Direction: 31 long and 27 short.
- Selected policy: `PV220__PI25__IE10__CV50__CI20`.
- Calibration opened no spot price, label, return, or P/L.
- Calibration audit payload SHA-256:
  `e3f8cdd4acdbfdc8abde1c8584bf1b0cb4a41fc54ee639b1388fadb318171a08`.
- Immutable contract SHA-256:
  `3f0fa32f8b5d70c2abdcd93b0eb4bb1823912ab7780dee34f9e5d611294ebcf6`.

## Development Evidence

- Period: 2022-08-01 through 2024-07-01.
- Eligible full weekdays: 491.
- Resolved trades: 1,615.
- Frequency: 3.2892/full weekday.
- Direction: 878 long and 737 short.
- Base net: `-$1,050.65`.
- Stress net: `-$1,168.09`.
- Base PF: `0.4695`.
- Stress PF: `0.4333`.
- Mean stress P/L: `-$0.7233/trade`.
- Profitable-day share: 22.20%.
- Positive-month share: 0%.
- First-half stress PF: `0.4164`.
- Second-half stress PF: `0.4508`.
- Stress net after removing the five largest winners: `-$1,194.37`.
- Closed-trade stress drawdown: `$1,168.09` versus the frozen `$250` maximum.
- Centered-null block-bootstrap p-value: `1.0`.

The family passed only minimum sample size, frequency interval, maximum
frequency, and direction balance. Every profitability, stability, significance,
winner-concentration, and drawdown gate failed.

## Interpretation And Authority

One-sided flow with weak price response followed by a confirmed opposite-flow
flip occurs often enough, but following the new flow direction has strongly
negative expectancy under executable XAUUSD prices and costs. This result does
not justify testing the hindsight mirror. V44 cannot enter the Core, a shared
account, model training, Python prediction, an EA, demo/live trading, or any
broker action.
