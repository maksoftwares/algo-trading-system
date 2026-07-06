# A1 XAU H4 D1 Long-Only Frequency Stress Preregistration

Date: 2026-07-05

## Purpose

The raw-frequency ladder found a broad D1/H4 breakout row that nearly reached the owner core:

- `d1_comp_max16_broad_box3_atr60_range125_body035`
- 335 trades
- 49.55% win rate
- 2.2456 realized average win / average loss
- 2.2057 profit factor
- 20.33% active weekdays

Exact-ledger direction diagnostics showed the miss was directional:

- Long trades only: 203 trades, WR 61.58%, W/L 2.2942, PF 3.6766, +11522.78 USD
- Short trades only: 132 trades, WR 31.06%, W/L 1.9881, PF 0.8957, -503.98 USD

This is a post-diagnostic stress, not a clean first-pass discovery. It tests whether the long-side structural edge can keep the owner core while raw frequency is broadened further. It is not reviewer-worthy by itself unless frequency improves materially.

## Exact MT5 Boundary

All headline results must come only from MetaTrader 5 Strategy Tester launched through the isolated root:

`C:\MT5A1M5MomentumBacktest`

No live/demo terminal, chart, preset, account, position, order, or broker runtime state may be touched.

Python may only orchestrate the isolated Strategy Tester run and parse exported ledgers.

## Date Range

`2022.07.01` through `2026.06.30`

## Fixed Execution Shape

All variants use:

- `InpSignalMode = 7`
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

The max-open cap is raised from 16 to 32 so the stress measures raw long signal frequency rather than queue blocking. Guard-block counts must still be reported.

## Variants

| Variant | ATR percentile cap | Box days | Range median max | H4 body min |
| --- | ---: | ---: | ---: | ---: |
| `long_broad_box3_atr60_range125_body035` | 60 | 3 | 1.25 | 0.35 |
| `long_box2_atr60_range125_body035` | 60 | 2 | 1.25 | 0.35 |
| `long_box2_atr80_range150_body035` | 80 | 2 | 1.50 | 0.35 |
| `long_box2_atr100_range200_body025` | 100 | 2 | 2.00 | 0.25 |
| `long_box2_atr100_norange_body010` | 100 | 2 | 999.00 | 0.10 |
| `long_box2_atr100_norange_body000` | 100 | 2 | 999.00 | 0.00 |

## Acceptance Rules

This remains a frequency stress, not a demo promotion gate.

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

- If broadening destroys WR >= 50% and W/L >= 2.0, stop this long-only branch.
- If one or more rows preserve WR >= 50% and W/L >= 2.0 but active days remain far below 90%, keep only as a component clue.
- If a row materially improves active days while preserving core shape, run a robustness package before using the reviewer token.

## Reviewer Budget Rule

Do not spend the one-per-day reviewer token on a post-diagnostic direction-selection run unless it creates a realistic demo-readiness decision. A low-frequency component clue is not enough.
