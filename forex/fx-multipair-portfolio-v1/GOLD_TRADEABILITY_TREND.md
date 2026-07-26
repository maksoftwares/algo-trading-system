# Gold tradeability trend — the actionable byproduct of the FX lane

Measured while establishing why Forex cannot support a system. The metric is the
one all ten FX rejections reduce to: median daily range divided by round-trip
cost. The broker's XAUUSD spread is **fixed** at $0.30, so range is the only
moving part.

| Year | Gold price | Median daily range | Range % | Range / cost |
|---:|---:|---:|---:|---:|
| 2019 | $1,318 | $11.57 | 0.88% | **34x** |
| 2021 | $1,750 | $19.34 | 1.11% | 57x |
| 2023 | $1,942 | $19.03 | 0.98% | 56x |
| 2025 | $3,125 | $33.20 | 1.06% | 98x |
| 2026 | $4,464 | $105.15 | 2.36% | **309x** |

Source: Dukascopy tick archive, March + June of each year, decoded via
`src/fxdata.py`. Cost is the measured broker spread of $0.30 plus $0.04
slippage. The live July-2026 broker measurement independently gives 211.7x on a
one-week sample, so the direction is corroborated by two sources.

## What this means

**Gold is roughly 9x more tradeable today than when the XAU system was
developed.** Its daily range has grown 9x since 2019 while its cost has not moved
at all. A strategy with fixed stop and target geometry expressed in dollars is
therefore capturing a far smaller fraction of the available move than it was
designed to, and a fixed per-trade cost is now a far smaller drag.

Concretely, the same edge is worth several times more per trade than at
development time, and the cost hurdle that killed every Forex hypothesis is
proportionally trivial here.

## Caveats

- The 2026 sample is March and June 2026 only, and 2.36% daily range is an
  exceptional volatility regime that may not persist. Treat 309x as *current*
  conditions, not a durable constant — 2021 and 2023 sat at 56-57x.
- Higher volatility raises both opportunity and risk. Stop distances, position
  sizing and drawdown limits calibrated in a $19-range regime are not
  automatically appropriate in a $105-range one; the same dollar stop is now a
  much tighter fraction of daily movement and will be hit far more often.
- This says nothing about whether any particular XAU strategy still has an edge.
  It says the cost hurdle is low and falling, which is a necessary condition, not
  a sufficient one.

## Suggested follow-up in the XAU lane

Re-express the deployed sleeves' stop/target geometry in units of current ATR
rather than fixed points, and re-check position sizing against the current range.
A rule tuned when gold moved $19/day and now running unchanged while gold moves
$105/day is operating far outside its calibration.
