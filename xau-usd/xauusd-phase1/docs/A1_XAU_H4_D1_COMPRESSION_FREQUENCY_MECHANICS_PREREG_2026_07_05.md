# A1 XAU H4 D1 Compression Frequency Mechanics Preregistration

Date: 2026-07-05

## Purpose

The exact MT5 H4 independent observer probe found one core-shape clue:

- `d1_compression_h4_expansion_rr2p0`
- 19 closed trades from 2022-07-01 through 2026-06-30
- 52.63% win rate
- 2.9284 realized average win / average loss
- 3.2538 profit factor
- 1.82% active weekdays

The order and signal ledgers show that the low frequency is partly mechanical:

- 107 `WOULD_SIGNAL` rows
- 19 `ORDER_SEND_OK`
- 86 `GUARD_BLOCK` rows with `own_position_exists`
- Average holding time about 20.6 days, max about 82.3 days

This preregistered probe tests whether the core shape survives when the one-position bottleneck is relaxed. It does not change the signal premise, stop/target shape, direction rule, or thresholds.

## Exact MT5 Boundary

All headline results must come only from MetaTrader 5 Strategy Tester launched through the isolated root:

`C:\MT5A1M5MomentumBacktest`

No live/demo terminal, chart, preset, account, position, order, or broker runtime state may be touched.

Python may only orchestrate the isolated Strategy Tester run and parse exported ledgers.

## Frozen Source

Expert:

`xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5`

Signal:

`InpSignalMode = 7`

This is the D1 compression box with H4 expansion close mode added for exact tester research.

## Date Range

`2022.07.01` through `2026.06.30`

## Fixed Execution Shape

All variants use:

- `InpRiskReward = 2.00`
- `InpDirectionMode = 0`
- `InpUseH1TrendFilter = false`
- `InpUseH4TrendFilter = false`
- `InpMaxEstimatedCostR = 0.15`
- `InpStopCeilingPoints = 0`
- `InpMaxTradesPerDay = 6`
- `InpCooldownMinutes = 0`

## Variants

Only the max-open-position cap changes:

| Variant | One-position rule | Max open positions |
| --- | --- | ---: |
| `d1_compression_h4_expansion_rr2p0_max2` | false | 2 |
| `d1_compression_h4_expansion_rr2p0_max4` | false | 4 |
| `d1_compression_h4_expansion_rr2p0_max8` | false | 8 |
| `d1_compression_h4_expansion_rr2p0_max16` | false | 16 |

The prior exact baseline remains the comparison row:

`A1_XAU_H4_INDEPENDENT_OBSERVER_FAMILIES_EXACT_PROBE_202207_202606`

## Acceptance Rules

This is a frequency-mechanics probe, not a demo-ready promotion gate.

Report:

- closed trades
- win rate
- realized average win / average loss
- profit factor
- manual P&L from exported closed trades
- active weekday percentage
- last-12-month metrics
- order action counts
- guard-block reason counts
- signal counts

Interpretation:

- If no expanded variant keeps WR >= 50% and realized W/L >= 2.0, reject this branch for owner-goal use.
- If one or more expanded variants keeps WR >= 50% and realized W/L >= 2.0 but remains far below daily frequency, retain it only as a component clue.
- Do not spend the reviewer unless an expanded variant materially improves frequency while preserving core shape.

## Reviewer Budget Rule

The reviewer is limited to one serious request per day. This probe should not consume that review by default. It should only be packaged for review if the result creates a realistic next decision, not merely another tiny-sample clue.
