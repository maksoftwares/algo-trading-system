# A1 XAU Weekly-Damage H1 V14 Freeze Note

Date: 2026-07-07

## Exact MT5 Runs

Two exact-MT5 batches were completed over `2022-07-01 -> 2026-06-30`:

- V14 six-cell weekly-damage H1 source:
  - report: `outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V14_WEEKLY_DAMAGE_H1_202207_202606.md`
  - weekly review: `outputs/reports/A1_XAU_WEEKLY_DAMAGE_H1_V0_EXACT_MT5_REVIEW_202207_202606.md`
- V14B direction split of the reversal source:
  - report: `outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V14B_WEEKLY_DAMAGE_H1_DIRECTION_SPLIT_202207_202606.md`
  - weekly review: `outputs/reports/A1_XAU_WEEKLY_DAMAGE_H1_V14B_DIRECTION_SPLIT_EXACT_MT5_REVIEW_202207_202606.md`

## Best Standalone Reads

| Source | Trades | WR | W/L | PF | Net USD | Positive weeks | Read |
|---|---:|---:|---:|---:|---:|---:|---|
| V14 reversal 2.0R move10 | 351 | 34.19% | 2.1037 | 1.0928 | 247.49 | 33.17% | positive but sparse/noisy |
| V14B reversal 2.0R move10 long-only | 146 | 39.73% | 2.2024 | 1.4516 | 435.11 | 20.67% | best standalone quality, too sparse |
| V14B reversal 1.5R move08 long-only | 173 | 45.09% | 1.5637 | 1.2839 | 299.84 | 21.15% | higher WR, payoff too low |

Short-only direction splits were standalone-negative.

## Hybrid Weekly Target Reads

Against the current baseline, the best V14/V14B hybrid reached only `56.73%` positive calendar weeks. Best row details:

- `v14_weekly_damage_reversal_rr2_move10`: hybrid positive weeks `56.73%`, active weekdays `89.36%`, red weeks touched/flipped/worsened `63/14/24`.
- `v14b_weekly_damage_reversal_rr15_move08_short_only`: hybrid positive weeks `56.73%`, active weekdays `87.82%`, but standalone net `-216.01 USD`.

Against the prior best weekly-state rescue base, the best combined ceiling was:

- base: `weekly_state_best`
- add-on: `v14_weekly_damage_reversal_rr15_move08`
- hybrid positive weeks: `59.52%`
- hybrid active weekdays: `90.03%`
- hybrid WR/W-L: `50.00% / 1.7708`
- worst week: `-879.28 USD`

This improves activity, but it remains far below the relaxed `70-80%` positive-week target and still fails payoff/stress shape.

## Decision

`FREEZE_WEEKLY_DAMAGE_H1_SOURCE_CLASS`

Do not continue tuning V14 with hour masks, extra thresholds, or direction-specific rescue rules. It does not have enough red-week repair power: best baseline hybrid flips too few red weeks and worsens too many, while best weekly-state combo tops out at only `59.52%` positive calendar weeks.
