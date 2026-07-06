# A1 XAU H4 D1 Long-Only Pre-2022 Robustness Preregistration

Date: 2026-07-05

## Purpose

The current best exact-MT5 Gold component clue is:

- `long_box2_atr80_range150_body035`
- 2022-07-01 through 2026-06-30
- 344 trades
- 57.56% win rate
- 2.2812 realized average win / average loss
- 3.0937 profit factor
- +16084.99 USD manual P&L
- 19.56% active weekdays

The same row has robustness gaps in the 2022-2026 audit, so this preregistered run checks an older untouched window without changing any inputs.

## Exact MT5 Boundary

All headline results must come only from MetaTrader 5 Strategy Tester launched through the isolated root:

`C:\MT5A1M5MomentumBacktest`

No live/demo terminal, chart, preset, account, position, order, or broker runtime state may be touched.

Python may only orchestrate the isolated Strategy Tester run and parse exported ledgers.

## Date Range

`2016.01.01` through `2021.12.31`

## Frozen Variant

| Variant | Signal mode | Direction | ATR percentile cap | Box days | Range median max | H4 body min | RR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `long_box2_atr80_range150_body035_pre2022` | 7 | long-only | 80 | 2 | 1.50 | 0.35 | 2.00 |

Other fixed execution inputs:

- `InpUseH1TrendFilter = false`
- `InpUseH4TrendFilter = false`
- `InpMaxEstimatedCostR = 0.15`
- `InpStopCeilingPoints = 0`
- `InpMaxTradesPerDay = 6`
- `InpCooldownMinutes = 0`
- `InpOnePositionPerMagic = false`
- `InpMaxOpenPositionsPerMagic = 32`

## Acceptance Rules

This is not a demo promotion gate.

Report:

- raw signal count
- order-send count and guard-block reasons
- closed trades
- win rate
- realized average win / average loss
- profit factor
- manual P&L from exported closed trades
- active weekday percentage
- +0.10 USD and +0.30 USD per-closed-trade stress

Interpretation:

- If the older window fails WR >= 50% or W/L >= 2.0, stop treating the H4 long-only clue as a robust component.
- If it passes both but remains low-frequency, keep it as a component clue only.
- Do not spend the reviewer token on this extension alone.
