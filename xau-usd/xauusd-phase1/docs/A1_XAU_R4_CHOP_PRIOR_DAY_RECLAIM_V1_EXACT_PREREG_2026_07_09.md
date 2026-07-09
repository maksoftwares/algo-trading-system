# A1 XAU R4 Chop Prior-Day Reclaim V1 Exact-MT5 Preregistration

Date: 2026-07-09

## Purpose

Open a new R4 chop specialist lane after the R2 pullback/rejection work was frozen.

The previous broad prior-day level families were rejected as activity fillers. This test is narrower: it only allows failed breaks of the previous daily high/low when the EA-side Router V1 classifies the market as `chop`. The hypothesis is that prior-day extremes may be cleaner chop boundaries than tiny M5 sweeps or same-day daily extremes.

This is not a tuning pass over the old V15/V15B family. It is a router-specific specialist test with fixed inputs and exact-MT5 execution.

## Router

Use the existing EA router mode:

- `InpRegimeRouterMode=4`
- allow trades only when `CurrentXauRegime() == XAU_REGIME_CHOP`
- block shock, uptrend, downtrend, compression, and unknown
- keep Router V1 parameters unchanged

## Signal

Use the existing EA prior-day level reversal signal:

- `InpSignalMode=13`
- `InpPriorDayLevelMode=1`
- fade failed breaks of previous D1 high/low
- fixed `2.00R` target
- no breakeven, partial, trailing, weekly governor, previous-month health gate, hour-mining, day-mining, or month-mining filters

Fixed inputs:

- `InpRiskReward=2.00`
- `InpMaxSpreadPoints=75`
- `InpMaxEstimatedCostR=0.10`
- `InpPriorDayLevelStartHour=6`
- `InpPriorDayLevelEndHour=22`
- `InpPriorDayLevelBreakAtr=0.10`
- `InpPriorDayLevelTouchAtr=0.05`
- `InpPriorDayLevelReclaimAtr=0.10`
- `InpPriorDayLevelStopBufferAtr=0.25`
- `InpPriorDayLevelMinBodyFraction=0.35`
- `InpLongCloseLocation=0.60`
- `InpShortCloseLocation=0.40`
- `InpStopFloorPoints=250`
- `InpStopCeilingPoints=1400`
- `InpStopCapPoints=0`
- `InpMaxTradesPerDay=12`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=true`

## Variants

Direction split is allowed as structural diagnostics, not threshold tuning:

- `r4_chop_prior_day_reclaim_v1_both`
- `r4_chop_prior_day_reclaim_v1_long`
- `r4_chop_prior_day_reclaim_v1_short`

No other variants are allowed in this pass.

## Standalone Gates

- full-window trades >= 150
- full-window WR >= 50%
- full-window W/L >= 1.80
- full-window PF >= 1.50
- stress PF after -$0.30/ticket >= 1.30
- stress W/L after -$0.30/ticket >= 1.65
- full-window net > 0
- recent 3 months trades >= 30
- recent 3 months net > 0
- 2023+2024 net >= 0
- top 10 winning trades removed net > 0
- top 3 winning days removed net > 0

## Combined Gates

Combine each candidate with the current R1 book:

- `A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv`

Deduplicate same-direction overlap using the existing 5-minute portfolio dedupe.

Combined candidate gates:

- net > current R1 book net
- recent 3 months trades > 0
- recent 3 months net >= 0
- WR >= 50%
- W/L >= 2.00 or stress W/L >= 1.90
- PF >= 2.00
- max closed drawdown not worse than current R1 book by more than 15%
- top 10 winning trades removed net > 0
- top 3 winning days removed net > 0

## Decision

- If any variant passes standalone and combined gates: `R4_CHOP_PRIOR_DAY_RECLAIM_V1_REVIEW_CANDIDATE`.
- If no variant passes all gates but at least one is standalone positive or gives non-negative recent combined coverage without breaking WR: `R4_CHOP_PRIOR_DAY_RECLAIM_V1_SHADOW_ONLY`.
- Otherwise: `R4_CHOP_PRIOR_DAY_RECLAIM_V1_NO_SURVIVOR`.

All outputs remain research-only and require reviewer approval before any demo spec.
