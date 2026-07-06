# A1 XAU M5 EMA HTF Frequency Source Preregistration

Date: 2026-07-05

## Purpose

Test one new frequency source for the owner Gold goal after exact-ledger recombination failed to join WR >= 50%, realized W/L >= 2.0, and near-daily activity.

This is not a tuning continuation of the high-payout A1/ORREV frontier. It uses the existing default-off `SIGNAL_M5_EMA_TREND_CONTINUATION` mode as a lower-timeframe frequency source, with higher-timeframe trend gating.

## Boundary

- Exact MT5 Strategy Tester only, isolated root `C:\MT5A1M5MomentumBacktest`.
- No live/demo runtime attach.
- No chart, preset, order, position, or broker state mutation.
- Existing EA source only; no new MQL behavior for this probe.
- Three fixed variants, no optimizer and no further parameter selection inside this probe.

## Window

- Exam: `2022.07.01 -> 2026.06.30`
- Symbol/timeframe: `XAUUSD`, `M5`
- Tester currency: `USD`

## Variants

All variants use:

- `InpSignalMode=5` (`SIGNAL_M5_EMA_TREND_CONTINUATION`)
- `InpDirectionMode=1` (long-only)
- `InpRiskReward=2.00`
- `InpMaxEstimatedCostR=0.15`
- `InpStopCeilingPoints=0`
- `InpMaxTradesPerDay=24`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=16`

Fixed variants:

1. `m5ema_long_h4_rr2p0`: H4 trend filter only, default M5 EMA trigger quality.
2. `m5ema_long_h1h4_rr2p0`: H1 + H4 trend filters, default M5 EMA trigger quality.
3. `m5ema_long_h4_quality_rr2p0`: H4 trend filter only, stricter M5 trigger quality (`MinRangeAtr=0.80`, `MinBodyFraction=0.55`, `LongCloseLocation=0.78`, `MinThreeBarMoveAtr=0.90`).

## Pass / Stop Rules

- Owner hit: WR >= 50%, realized W/L >= 2.0, active weekdays >= 90%.
- Core-shape frequency gap: WR >= 50% and realized W/L >= 2.0, but active weekdays < 90%.
- Near-owner frontier: WR >= 48%, realized W/L >= 1.8, active weekdays >= 70%, PF >= 1.30.
- Otherwise reject and do not spend reviewer.

Any pass is still at most a research candidate until reviewer reconstruction and owner approval.
