# A1 XAU Downtrend Short Engine Preregistration

Date: 2026-07-07

## Objective

Hunt for the missing downtrend half of the regime pair. The current strongest branch is an uptrend/gold-bull long engine. This pass tests whether a true bearish-D1 short engine can complement it without adding noisy activity filler.

This is exact MT5 Strategy Tester work only. It is not a demo spec.

## Bearish Regime Gate

Use the default-off generic D1 support-state gate with a new mode:

- `InpD1SupportStateGateMode=3`: require bearish D1 state
- `InpD1SupportStateEmaPeriod=20`
- `InpD1SupportStateSlopeLagBars=5`

Bearish state uses completed D1 data only:

- `D1 close[1] < D1 EMA(20)[1]`
- `D1 EMA(20)[1] <= D1 EMA(20)[6]`

Existing modes remain unchanged:

- `0`: off
- `1`: require supportive/uptrend
- `2`: require non-supportive

## Exact-MT5 Variants

Run exactly these four variants over `2022.07.01 -> 2026.06.30`, USD tester currency, isolated MT5 Strategy Tester root.

All variants share:

- `InpDirectionMode=2`
- `InpRiskReward=2.00`
- `InpMaxSpreadPoints=75`
- `InpD1SupportStateGateMode=3`
- `InpD1SupportStateEmaPeriod=20`
- `InpD1SupportStateSlopeLagBars=5`
- `InpBlockedEntryDayHoursCsv=5:20`
- No live/demo runtime change, no chart/profile/preset/order/position changes outside the tester.

### 1. `down_h4_d1_short_box2_atr80`

Bearish version of the known H4/D1 compression-expansion source:

- `InpSignalMode=7`
- `InpUseH1TrendFilter=false`
- `InpUseH4TrendFilter=false`
- `InpMaxEstimatedCostR=0.15`
- `InpStopCeilingPoints=0`
- `InpStopCapPoints=0`
- `InpMaxTradesPerDay=6`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=32`
- `InpD1CompressionAtrPercentileMax=80.00`
- `InpD1CompressionBoxDays=2`
- `InpD1CompressionRangeMedianMax=1.50`
- `InpD1CompressionH4MinBodyFraction=0.35`

### 2. `down_h1_d1_short_box2_atr80`

Same D1 compression premise, but H1 completion instead of H4, to test whether the short side needs more frequency:

- `InpSignalMode=10`
- Same D1 compression parameters as variant 1
- Same stop/trade caps as variant 1

### 3. `down_m5_ema_h1h4_short_rr2`

M5 bearish trend-continuation under H1/H4 alignment and bearish D1:

- `InpSignalMode=5`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpH1TrendMinSlopePoints=0`
- `InpH4TrendMinSlopePoints=0`
- `InpMaxEstimatedCostR=0.05`
- `InpM5TrendEmaFastPeriod=8`
- `InpM5TrendEmaSlowPeriod=21`
- `InpM5TrendSlopeBars=3`
- `InpM5TrendMinSlopeAtr=0.03`
- `InpM5TrendMaxDistanceAtr=1.20`
- `InpMinRangeAtr=0.35`
- `InpMinBodyFraction=0.30`
- `InpShortCloseLocation=0.42`
- `InpMinThreeBarMoveAtr=0.10`
- `InpMaxTradesPerDay=24`
- `InpCooldownMinutes=0`

### 4. `down_prior_day_cont_short_rr2`

Prior-day level continuation, short-only, under bearish D1:

- `InpSignalMode=13`
- `InpPriorDayLevelMode=0`
- `InpPriorDayLevelStartHour=6`
- `InpPriorDayLevelEndHour=22`
- `InpPriorDayLevelBreakAtr=0.05`
- `InpPriorDayLevelTouchAtr=0.05`
- `InpPriorDayLevelReclaimAtr=0.10`
- `InpPriorDayLevelStopBufferAtr=0.25`
- `InpPriorDayLevelMinBodyFraction=0.35`
- `InpMaxEstimatedCostR=0.08`
- `InpStopFloorPoints=250`
- `InpStopCeilingPoints=1400`
- `InpMaxTradesPerDay=8`
- `InpCooldownMinutes=15`

## Recomposition

Convert each exact-MT5 trade CSV into normalized composition rows with source priority `90` and family group `downtrend_short_engine`.

Evaluate:

- each candidate added to the corrected `supportive_guard` baseline
- all downtrend candidates together added to the same baseline

Baseline:

- `outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv`

Weekly P&L must be grouped by reconstructed exit week. Deduplicate with the existing 5-minute same-direction portfolio rule.

## Pass-Fail Gates

A combination is only a review candidate if all are true:

- Combined WR >= 50.00%
- Combined W/L >= 2.00
- Active weekdays >= 85.00%
- Stress W/L at -0.30 USD/ticket >= 1.90
- Positive weeks improve by at least +3.00pp vs baseline
- At least 8 baseline red weeks are flipped positive
- No more than 4 baseline red weeks are worsened
- Downtrend-source net in baseline red weeks >= +300 USD
- Worst week improves vs baseline

Standalone downtrend rows are diagnostic unless they are net-positive, W/L >= 2.0, and have enough sample to justify a separate review.

## Anti-Overfit Boundary

Do not tune hours, months, thresholds, or direction masks after seeing this run. If the bearish-D1 branch fails, freeze it or move to a materially different short-engine design.
