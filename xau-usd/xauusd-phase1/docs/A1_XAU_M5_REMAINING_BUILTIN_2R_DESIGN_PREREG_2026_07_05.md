# A1 XAU M5 Remaining Built-In 2R Design Preregistration

Date: 2026-07-05

## Purpose

After Step 1-3 recombination and the M5 EMA HTF frequency source failed the owner Gold objective, this probe checks whether any remaining built-in M5 signal family can produce a design-window high-WR / 2R shape.

This is a Step-4-style design screen. It does not claim a candidate unless the design window earns one.

## Boundary

- Exact MT5 Strategy Tester only in isolated root `C:\MT5A1M5MomentumBacktest`.
- Design window only: `2016.01.01 -> 2021.12.31`.
- No live/demo runtime attach.
- No chart, preset, order, position, or broker state mutation.
- Existing EA source only; no new MQL behavior.
- Four fixed variants, no optimizer, no post-result threshold selection.

## Variants

Common settings:

- `InpRiskReward=2.00`
- `InpMaxEstimatedCostR=0.15`
- `InpStopCeilingPoints=0`
- `InpMaxTradesPerDay=24`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=16`

Fixed variants:

1. `ema_pullback_long_h1h4_rr2p0`: `SIGNAL_EMA_PULLBACK`, long-only, H1+H4 trend filters.
2. `compression_long_h1h4_rr2p0`: `SIGNAL_COMPRESSION_EXPANSION`, long-only, H1+H4 trend filters.
3. `sweep_reclaim_long_h1_rr2p0`: `SIGNAL_SWEEP_RECLAIM`, long-only, H1 trend filter, fixed V9-style sweep/reclaim thresholds.
4. `sweep_reclaim_both_nohtf_rr2p0`: `SIGNAL_SWEEP_RECLAIM`, both directions, no HTF filter, fixed V9-style sweep/reclaim thresholds.

## Promotion Rule

- Design owner hit: WR >= 50%, realized W/L >= 2.0, active weekdays >= 90%.
- Design core-shape frequency gap: WR >= 50%, realized W/L >= 2.0, active weekdays < 90%.
- Design near-frontier: WR >= 48%, realized W/L >= 1.8, active weekdays >= 30%, PF >= 1.30.

Only design owner/core/near rows may be frozen into a separate 2022-2026 exam. Otherwise this branch is rejected and no reviewer token is spent.
