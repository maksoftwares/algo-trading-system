# A1 XAU Non-Uptrend Range-Fade Red-Week Probe Preregistration

Date: 2026-07-07

## Objective

Test one constrained exact-MT5 source-family idea: range-fade behavior only when the D1 gold state is not supportive. The goal is to see whether a structurally different source can improve the corrected `supportive_guard` weekly shape without padding activity with near-breakeven frequency trades.

This is not a tuning sweep and not a demo specification. It is a small red-week repair probe.

## Current Baseline

Baseline for recomposition:

- `outputs/reports/A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv`

Known baseline shape from the corrected exact-MT5 H4/D1 review repair:

- Signals: 3,645
- WR: 50.40%
- W/L: 2.0895
- Active weekdays: 85.71%
- Net: +20,701.41 USD
- Stress W/L at -0.30 USD/ticket: 1.9720
- Positive weeks: 57.69%
- Worst week: -878.18 USD
- Recent3 net: +279.22 USD

## New Default-Off EA Input

Add a generic D1 support-state gate:

- `InpD1SupportStateGateMode=0`: off
- `InpD1SupportStateGateMode=1`: require D1 supportive state
- `InpD1SupportStateGateMode=2`: require D1 non-supportive state
- `InpD1SupportStateEmaPeriod=20`
- `InpD1SupportStateSlopeLagBars=5`

Supportive state is defined using only completed D1 data:

- `D1 close[1] > D1 EMA(20)[1]`
- `D1 EMA(20)[1] >= D1 EMA(20)[6]`

All existing behavior must remain unchanged when `InpD1SupportStateGateMode=0`.

## Exact-MT5 Variants

Run exactly these three variants over `2022.07.01 -> 2026.06.30`, USD tester currency, isolated MT5 Strategy Tester root.

All variants share:

- `InpDirectionMode=0`
- `InpUseH1TrendFilter=false`
- `InpUseH4TrendFilter=false`
- `InpRiskReward=2.00`
- `InpMaxSpreadPoints=75`
- `InpD1SupportStateGateMode=2`
- `InpD1SupportStateEmaPeriod=20`
- `InpD1SupportStateSlopeLagBars=5`
- `InpBlockedEntryDayHoursCsv=5:20`
- No live/demo runtime change, no chart/profile/preset/order/position changes outside the tester.

### 1. `nonup_daily_extreme_rr2`

Use existing daily-extreme reclaim signal:

- `InpSignalMode=11`
- `InpMaxEstimatedCostR=0.15`
- `InpStopFloorPoints=100`
- `InpStopCeilingPoints=0`
- `InpMaxTradesPerDay=24`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=16`
- `InpMinRangeAtr=0.20`
- `InpLongCloseLocation=0.58`
- `InpShortCloseLocation=0.42`
- `InpDailyExtremeMinMoveAtr=1.00`
- `InpDailyExtremeTouchAtr=0.06`
- `InpDailyExtremeReclaimAtr=0.10`
- `InpDailyExtremeStopBufferAtr=0.10`
- `InpDailyExtremeMinBodyFraction=0.25`
- `InpDailyExtremeMinBarsSinceOpen=24`
- `InpDailyExtremeStartHour=7`
- `InpDailyExtremeEndHour=22`

### 2. `nonup_prior_day_reversal_rr2`

Use existing prior-day level reversal signal:

- `InpSignalMode=13`
- `InpPriorDayLevelMode=1`
- `InpPriorDayLevelStartHour=6`
- `InpPriorDayLevelEndHour=22`
- `InpPriorDayLevelBreakAtr=0.10`
- `InpPriorDayLevelTouchAtr=0.05`
- `InpPriorDayLevelReclaimAtr=0.10`
- `InpPriorDayLevelStopBufferAtr=0.25`
- `InpPriorDayLevelMinBodyFraction=0.35`
- `InpMaxEstimatedCostR=0.10`
- `InpStopFloorPoints=250`
- `InpStopCeilingPoints=1400`
- `InpMaxTradesPerDay=24`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=true`

### 3. `nonup_orrev_london_rr2`

Use existing London opening-range reversal signal:

- `InpSignalMode=6`
- `InpOpeningRangeStartHour=7`
- `InpOpeningRangeMinutes=60`
- `InpOpeningTradeWindowHours=5`
- `InpOpeningBreakAtrMultiple=0.10`
- `InpReclaimAtrMultiple=0.05`
- `InpMinRangeAtr=0.40`
- `InpMinBodyFraction=0.35`
- `InpLongCloseLocation=0.60`
- `InpShortCloseLocation=0.40`
- `InpStopAtrMultiple=1.50`
- `InpStopFloorPoints=250`
- `InpStopCeilingPoints=1400`
- `InpMaxEstimatedCostR=0.08`
- `InpMaxTradesPerDay=24`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=true`

## Recomposition

Convert each exact-MT5 trade CSV into normalized composition rows with source priority 90 and family group `nonuptrend_range_fade_red_week`.

Evaluate these four combinations against the corrected `supportive_guard` baseline:

- `nonup_daily_extreme_rr2_only`
- `nonup_prior_day_reversal_rr2_only`
- `nonup_orrev_london_rr2_only`
- `nonup_all_range_fade_rr2`

Deduplicate with the existing portfolio dedupe rules. Weekly P&L must be grouped by reconstructed exit week.

## Pass-Fail Gates

A combination is only a review candidate if all are true:

- WR >= 50.00%
- W/L >= 2.00
- Active weekdays >= 85.00%
- Stress W/L at -0.30 USD/ticket >= 1.90
- Positive weeks improve by at least +3.00pp vs baseline
- At least 8 baseline red weeks are flipped positive
- No more than 4 baseline red weeks are worsened
- New-source net in baseline red weeks >= +300 USD
- Worst week improves vs baseline

Anything below this is research-only. Do not spend reviewer unless a row passes the above or produces an unusually clean structural clue worth review.

## Anti-Overfit Boundary

No thresholds may be changed after seeing results in this run. Do not block specific hours, months, weekdays, or isolated losing clusters based on the output. If all rows fail, freeze this source-family direction and move to a different structural source class.
