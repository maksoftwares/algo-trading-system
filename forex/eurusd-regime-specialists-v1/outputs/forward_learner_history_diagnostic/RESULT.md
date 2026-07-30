# Frozen forward learner historical diagnostic

Status: **RETROSPECTIVE DIAGNOSTIC ONLY -- NO ADMISSION**

| Metric | Result |
|---|---:|
| Validation weekdays after warmup | 2,571 |
| Eligible trades | 34 |
| Trades/validation weekday | 0.0132 |
| Win rate | 38.24% |
| Payoff ratio | 1.469135802469136 |
| Profit factor | 0.9095 |
| Stressed PF (+0.5 pip) | 0.8206 |
| Net at 0.01 lot | $-1.54 |
| Projected M15 + daily frequency before overlap caps | 0.2163 |

The exact frozen learner was replayed causally from zero weights. No
parameter was changed. These already-mined historical prices cannot
count toward forward admission or demo-order authorization.

The source bars contain bid/ask OHLC but not intrabar tick-mean spread.
The adapter therefore uses the mean of each bar's open and close spread
for the spread feature; trade outcomes use the native bid/ask highs and lows.
