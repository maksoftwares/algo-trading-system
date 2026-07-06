# A1 XAU H4/D1 Stop-Ceiling One-Iteration Preregistration

Date: 2026-07-06

## Purpose

Run one exact-MT5 iteration against the current H4/D1 long-only component that contributes most of the current frontier profit but also creates unacceptable weekly loss shape.

This is intentionally not a grid. The owner asked to save tokens and do one iteration only.

## Frozen Cell

Base component:

- `InpSignalMode=7`
- `InpDirectionMode=1`
- `InpRiskReward=2.00`
- `InpD1CompressionAtrPercentileMax=80.00`
- `InpD1CompressionBoxDays=2`
- `InpD1CompressionRangeMedianMax=1.50`
- `InpD1CompressionH4MinBodyFraction=0.35`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=32`
- `InpMaxTradesPerDay=6`
- `InpCooldownMinutes=0`

One change:

- `InpStopCeilingPoints=3000`

Important interpretation: this EA input is a stop-ceiling **filter**, not a geometric stop rewrite. It rejects entries whose estimated stop exceeds the ceiling. It does not tighten accepted stops.

## Judgment

Report both:

1. Standalone exact-MT5 component metrics.
2. Recomposition where the new component replaces `h4_d1_long_best_box2_atr80` in the current best hybrid while all other sources remain unchanged.

Required fields:

- signal count
- win rate
- realized average win/loss
- active weekday percentage
- profit factor
- net USD
- max closed drawdown
- last-12-month WR/W-L/active
- ex-top-1% and ex-top-2% winner removal
- positive week percentage
- worst week
- positive month percentage
- worst month
- June 2026 net

No reviewer token is spent unless recomposition preserves WR >= 50%, W/L >= 2.0, active weekdays near the current frontier, and improves weekly/monthly loss shape materially.
