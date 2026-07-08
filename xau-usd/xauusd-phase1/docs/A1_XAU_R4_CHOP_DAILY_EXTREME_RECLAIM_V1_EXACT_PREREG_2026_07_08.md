# A1 XAU R4 Chop Daily-Extreme Reclaim V1 Exact-MT5 Preregistration

Date: 2026-07-08

## Purpose

The R4 chop audit showed recent chop dominance, while the first R4 failed-break test showed that tiny M5 sweeps are too noisy. This test tries a cleaner R4 mean-reversion idea: fade a stretched broker-day extreme only after price reclaims away from that extreme.

## Router

Use `REGIME_ROUTER_R4_CHOP_ONLY` with Router V1 parameters unchanged.

## Signal

Use existing EA signal mode `SIGNAL_DAILY_EXTREME_RECLAIM`.

Fixed inputs:

- `InpSignalMode=11`
- `InpDirectionMode=0`
- `InpRiskReward=2.00`
- `InpDailyExtremeStartHour=7`
- `InpDailyExtremeEndHour=22`
- `InpDailyExtremeMinMoveAtr=1.00`
- `InpDailyExtremeTouchAtr=0.06`
- `InpDailyExtremeReclaimAtr=0.10`
- `InpDailyExtremeStopBufferAtr=0.10`
- `InpDailyExtremeMinBodyFraction=0.25`
- `InpDailyExtremeMinBarsSinceOpen=24`
- `InpMinRangeAtr=0.20`
- `InpLongCloseLocation=0.58`
- `InpShortCloseLocation=0.42`
- `InpStopFloorPoints=100`
- `InpStopCeilingPoints=0`
- no hour masks beyond the declared liquid window; no day/month masks, breakeven, partial, trailing, or weekly governor.

## Variant

Only one exact-MT5 variant is permitted:

- `r4_chop_daily_extreme_reclaim_v1_liquid`

## Gates

Use the same standalone and combined gates as `A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_PREREG_2026_07_08.md`.

All outputs remain research-only and require reviewer approval before any demo spec.
