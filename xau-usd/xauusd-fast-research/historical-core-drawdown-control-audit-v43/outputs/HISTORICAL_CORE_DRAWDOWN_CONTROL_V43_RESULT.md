# Historical Core Drawdown Control Audit V43

Decision: **R1_STACKING_CONTROL_EFFECTIVE_ACCOUNT_NOT_READY**

This is a retrospective risk audit, not untouched confirmation and not order authority.

## Finding

The USD 889.69 closed drawdown was an R1 uptrend exposure-stacking event. The already-frozen two-position, one-entry-per-day R1 cap reduces the one-year closed drawdown to USD 259.53 (70.8% lower).

## Frozen Cap Windows

| Window | Policy | Trades | Trades/day | Net USD | PF | Closed DD USD |
|---|---|---:|---:|---:|---:|---:|
| 1Y | `ORIGINAL` | 160 | 0.613 | 4508.78 | 3.492 | 889.69 |
| 1Y | `FROZEN_R1_CAP` | 142 | 0.544 | 2478.19 | 3.195 | 259.53 |
| 2Y | `ORIGINAL` | 439 | 0.841 | 7332.55 | 2.708 | 889.69 |
| 2Y | `FROZEN_R1_CAP` | 379 | 0.726 | 3811.63 | 2.459 | 278.05 |
| 5Y | `ORIGINAL` | 930 | 0.713 | 9582.12 | 2.622 | 889.69 |
| 5Y | `FROZEN_R1_CAP` | 839 | 0.643 | 4920.23 | 2.268 | 289.53 |
| 10Y | `ORIGINAL` | 1165 | 0.447 | 9827.24 | 2.560 | 889.69 |
| 10Y | `FROZEN_R1_CAP` | 1074 | 0.412 | 5165.35 | 2.209 | 289.53 |

## Floating Equity

The independent ten-year Dukascopy replay of the same frozen cap has exact stress floating drawdown of USD 521.21. That is 17.38% of the current USD 2998.45 account, above the 15% ceiling.

R1 alone therefore requires at least USD 4343.45 with the frozen 25% capital buffer. At current equity, the buffered maximum lot is 0.0069; Capital's minimum is 0.01.

Until the full V42 shared-account forward curve supersedes the legacy evidence, the whole Core conservatively requires USD 14444.75.

## Required Action

- Keep the R1 cap at two concurrent positions and one entry per UTC day.
- Fail closed on the current account; do not attach a 0.01-lot executor.
- Use a larger adequately funded account or a broker with smaller lot sizing.
- Keep V42 collecting exact shared-account evidence before any demo decision.
