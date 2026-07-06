# A1 XAU H4 D1 Compression Raw-Frequency Ladder Preregistration

Date: 2026-07-05

## Purpose

The D1-compression/H4-expansion clue is the current best exact-MT5 Gold shape:

- `d1_compression_h4_expansion_rr2p0_max16`
- 103 closed trades from 2022-07-01 through 2026-06-30
- 53.40% win rate
- 2.7193 realized average win / average loss
- 3.1159 profit factor
- 7.48% active weekdays

This is still far below the owner frequency target. The prior frequency-mechanics run proved that the one-position bottleneck was not the final blocker: the raw signal population itself was only 107 signals over the full window.

This preregistered ladder tests whether raw signal frequency can be increased by broadening the D1/H4 premise in a small, auditable way.

## Exact MT5 Boundary

All headline results must come only from MetaTrader 5 Strategy Tester launched through the isolated root:

`C:\MT5A1M5MomentumBacktest`

No live/demo terminal, chart, preset, account, position, order, or broker runtime state may be touched.

Python may only orchestrate the isolated Strategy Tester run and parse exported ledgers.

## Default-Safe EA Inputs

The EA gains default-preserving inputs for the D1/H4 compression signal:

- `InpD1CompressionAtrPercentileMax = 30.00`
- `InpD1CompressionBoxDays = 5`
- `InpD1CompressionRangeMedianMax = 1.00`
- `InpD1CompressionH4MinBodyFraction = 0.50`

Those defaults reproduce the prior core-shape clue.

## Date Range

`2022.07.01` through `2026.06.30`

## Fixed Execution Shape

All variants use:

- `InpSignalMode = 7`
- `InpRiskReward = 2.00`
- `InpDirectionMode = 0`
- `InpUseH1TrendFilter = false`
- `InpUseH4TrendFilter = false`
- `InpMaxEstimatedCostR = 0.15`
- `InpStopCeilingPoints = 0`
- `InpMaxTradesPerDay = 6`
- `InpCooldownMinutes = 0`
- `InpOnePositionPerMagic = false`
- `InpMaxOpenPositionsPerMagic = 16`

## Variants

| Variant | ATR percentile cap | Box days | Range median max | H4 body min |
| --- | ---: | ---: | ---: | ---: |
| `d1_comp_max16_atr45` | 45 | 5 | 1.00 | 0.50 |
| `d1_comp_max16_atr60` | 60 | 5 | 1.00 | 0.50 |
| `d1_comp_max16_box3_atr45` | 45 | 3 | 1.00 | 0.50 |
| `d1_comp_max16_range125_atr45` | 45 | 5 | 1.25 | 0.50 |
| `d1_comp_max16_body035_atr45` | 45 | 5 | 1.00 | 0.35 |
| `d1_comp_max16_broad_box3_atr60_range125_body035` | 60 | 3 | 1.25 | 0.35 |

The prior exact row `d1_compression_h4_expansion_rr2p0_max16` is the comparison row.

## Acceptance Rules

This is not a demo promotion gate. It is a raw-frequency expansion test.

Report for each row:

- raw signal count
- order-send count and guard-block reasons
- closed trades
- win rate
- realized average win / average loss
- profit factor
- manual P&L from exported closed trades
- active weekday percentage
- last-12-month metrics

Interpretation:

- If no expanded row preserves WR >= 50% and W/L >= 2.0, reject this expansion branch.
- If a row preserves WR >= 50% and W/L >= 2.0 but remains far below daily frequency, retain it only as a component clue.
- If a row materially increases active days while preserving core shape, package it for careful internal review before using the external reviewer token.

## Reviewer Budget Rule

Do not spend the one-per-day reviewer token on this ladder unless it creates a realistic next decision. A sparse component clue is not enough.
