# A1 XAU H1 D1 Long Expansion Frequency Stress Preregistration

Date: 2026-07-05

## Purpose

The best exact-MT5 Gold clue so far is H4 decision frequency:

- `long_box2_atr80_range150_body035`
- 344 trades
- 57.56% win rate
- 2.2812 realized average win / average loss
- 3.0937 profit factor
- 19.56% active weekdays

The owner goal still needs much higher activity. This preregistered stress keeps the same long-side D1 breakout premise but evaluates expansion on completed H1 bars instead of completed H4 bars.

This is a frequency test, not a demo promotion gate.

## Exact MT5 Boundary

All headline results must come only from MetaTrader 5 Strategy Tester launched through the isolated root:

`C:\MT5A1M5MomentumBacktest`

No live/demo terminal, chart, preset, account, position, order, or broker runtime state may be touched.

Python may only orchestrate the isolated Strategy Tester run and parse exported ledgers.

## Date Range

`2022.07.01` through `2026.06.30`

## Fixed Execution Shape

All variants use:

- `InpSignalMode = 10`
- `InpDirectionMode = 1`
- `InpRiskReward = 2.00`
- `InpUseH1TrendFilter = false`
- `InpUseH4TrendFilter = false`
- `InpMaxEstimatedCostR = 0.15`
- `InpStopCeilingPoints = 0`
- `InpMaxTradesPerDay = 6`
- `InpCooldownMinutes = 0`
- `InpOnePositionPerMagic = false`
- `InpMaxOpenPositionsPerMagic = 32`

## Variants

| Variant | ATR percentile cap | Box days | Range median max | H1 body min |
| --- | ---: | ---: | ---: | ---: |
| `h1_long_box2_atr80_range150_body035` | 80 | 2 | 1.50 | 0.35 |
| `h1_long_box2_atr60_range125_body035` | 60 | 2 | 1.25 | 0.35 |
| `h1_long_box3_atr60_range125_body035` | 60 | 3 | 1.25 | 0.35 |
| `h1_long_box2_atr80_range200_body025` | 80 | 2 | 2.00 | 0.25 |
| `h1_long_box2_atr100_range200_body025` | 100 | 2 | 2.00 | 0.25 |

The prior H4 exact row `long_box2_atr80_range150_body035` is the comparison row.

## Acceptance Rules

Report:

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

- If no H1 row preserves WR >= 50% and W/L >= 2.0, reject the H1 frequency branch.
- If H1 preserves core shape but remains far below daily frequency, keep it as a stronger component clue only.
- If H1 materially improves frequency while preserving core shape, run robustness diagnostics before using the reviewer token.

## Reviewer Budget Rule

Do not spend the one-per-day reviewer token on this stress unless it creates a realistic next decision. A component clue is not enough.
