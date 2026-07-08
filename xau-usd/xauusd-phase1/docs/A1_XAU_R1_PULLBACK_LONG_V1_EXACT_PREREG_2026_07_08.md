# A1 XAU R1 Pullback Long V1 Exact-MT5 Preregistration

Date: 2026-07-08

## Purpose

Test the reviewers' highest-EV next direction: add a selective long pullback-continuation specialist that only trades inside the already validated R1 uptrend router state.

This is not a short repair and not a frequency filler. The question is whether the R1 long book can be made less sparse without diluting the existing routed long-box edge.

## Fixed Regime Router

Use the EA-side router from `A1_XAU_REGIME_ROUTER_V1_EXACT_PREREG_2026_07_08.md` unchanged:

- `InpRegimeRouterMode=1`
- `InpRegimeFastEmaPeriod=20`
- `InpRegimeSlowEmaPeriod=50`
- `InpRegimeSlopeLagBars=5`
- `InpRegimePersistenceD1Bars=2`
- `InpRegimeRequireH4Confirm=true`
- shock and compression inputs unchanged from Router V1.

## Signal

New EA signal mode: `SIGNAL_R1_H1_PULLBACK_LONG`.

Rules:

1. Direction is long-only.
2. The router must allow R1 uptrend exposure.
3. Completed H1 trend must be constructive: H1 close > H1 EMA20 > H1 EMA50, and H1 EMA20 is not falling versus 5 H1 bars ago.
4. Price must touch the completed H1 EMA20 zone during the confirmation lookback: bar low <= EMA20 + 0.25 * H1 ATR14 and bar high >= EMA20 - 0.25 * H1 ATR14.
5. Confirmation candle must close bullish above H1 EMA20.
6. Confirmation body/range must be >= 0.35.
7. Confirmation close location must be >= 0.65.
8. Stop is below the pullback swing low by 0.25 * confirmation-timeframe ATR14.
9. Target is fixed 2R.
10. No breakeven, partial close, trailing, hour masks, day masks, month masks, or weekly governor.

## Variants

Only two variants are permitted:

- `r1_pullback_long_v1_m5_confirm`
- `r1_pullback_long_v1_m15_confirm`

No grid search is allowed.

## Standalone Gates

A variant is a standalone review candidate only if all are true:

- trades >= 150
- win rate >= 50%
- raw W/L >= 1.90
- raw PF >= 1.50
- stress PF after -$0.30/ticket >= 1.30
- stress W/L after -$0.30/ticket >= 1.80
- net > 0
- Q2-2026 net >= 0 if trades exist in Q2
- positive in at least 3 yearly buckets with exposure
- top 10 winning trades removed net > 0
- top 3 winning days removed net > 0

## Combined-With-R1-Box Gates

Combine each variant with the existing routed R1 box baseline from Router V1, deduping same-direction overlap using the existing 5-minute portfolio dedupe.

A combined book is a review candidate only if all are true:

- full-window net > routed R1 box baseline
- active weekday percentage improves by at least 5 points over routed R1 box baseline
- raw W/L >= 2.00 or stress W/L >= 1.90
- PF >= 2.00
- max closed drawdown is not worse than routed R1 box baseline by more than 10%
- top 10 winning trades removed net > 0
- top 3 winning days removed net > 0
- no single month contributes more than 30% of net

## Decision

- If standalone and combined gates pass: `R1_PULLBACK_LONG_V1_REVIEW_CANDIDATE`.
- If the standalone variant is positive but dilutes the R1 box below combined gates: `R1_PULLBACK_LONG_V1_SHADOW_ONLY`.
- Otherwise: `R1_PULLBACK_LONG_V1_NO_SURVIVOR`.

All outputs remain research-only and require reviewer approval before any demo spec.
