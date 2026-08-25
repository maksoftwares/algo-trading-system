# V60/V2 Dukascopy Cross-Feed Veto Audit

Generated: 2026-08-25T05:29:28Z

This transplants the exact V60 runtime entry and exit timestamps onto independent Dukascopy bid/ask ticks. It tests price-path portability; it does not replay the strategy on Dukascopy and cannot authorize deployment.

Common quote coverage: 1,366/1,390 trades (98.27%); veto coverage 12/12.

| Metric | V60 same timing | V2 same timing | Change |
|---|---:|---:|---:|
| Trades | 1,366 | 1,354 | -12 |
| Net spread-only P/L | $4330.78 | $4369.58 | $+38.80 |
| Profit factor | 2.0013 | 2.0203 | +0.0190 |
| Win rate | 50.59% | 50.89% | +0.30 pp |
| Closed drawdown | $180.66 | $180.66 | $+0.00 |

## Rejected cohort

The 12 V2 vetoes produce $-38.80 at PF 0.0841 on Dukascopy using the same timestamps. Capital/Dukascopy outcome-sign agreement is 91.67%.

| Year | V60 P/L | V2 P/L | Change |
|---:|---:|---:|---:|
| 2021 | $327.81 | $334.88 | $+7.07 |
| 2022 | $135.71 | $141.20 | $+5.49 |
| 2023 | $399.92 | $401.28 | $+1.36 |
| 2024 | $813.87 | $823.58 | $+9.71 |
| 2025 | $1390.29 | $1405.47 | $+15.18 |
| 2026 | $1263.18 | $1263.18 | $+0.00 |

## Quote-lag sensitivity

| Maximum lag | Covered trades | Covered vetoes | Veto P/L | Veto PF | V2 P/L change |
|---:|---:|---:|---:|---:|---:|
| 250 ms | 769 | 9 | $-30.67 | 0.0859 | $+30.67 |
| 500 ms | 1,013 | 9 | $-30.67 | 0.0859 | $+30.67 |
| 1000 ms | 1,164 | 9 | $-30.67 | 0.0859 | $+30.67 |
| 2000 ms | 1,289 | 11 | $-39.48 | 0.0681 | $+39.48 |
| 5000 ms | 1,366 | 12 | $-38.80 | 0.0841 | $+38.80 |

## Interpretation

Cross-feed mechanism support: **TRUE**.
The audit uses the Capital-derived holding intervals, so it remains historically exposed and post-selected. Dukascopy spread is included, but commission, swap, and broker-specific stop triggering are not. The locked clean prospective broker test remains the deployment gate.
