# A1 XAU R1 Pullback Long V2 Session Repair Exact-MT5 Preregistration

Date: 2026-07-08

## Purpose

Repair the V1 R1 pullback-long specialist by filtering it to the primary server-hour liquidity continuation window, while keeping the validated R1 router and the M15 pullback logic unchanged.

V1 proved the M15 pullback is positive and robust after top-winner removal, but it failed the win-rate gate. The repair hypothesis is that the edge is strongest during the main London/New York continuation window and weaker during thin or late sessions.

## Frozen From V1

- Signal mode: `SIGNAL_R1_H1_PULLBACK_LONG`
- Confirmation timeframe: M15 only.
- Router: Router V1 R1 uptrend-only, unchanged.
- H1 trend: H1 close > H1 EMA20 > H1 EMA50, EMA20 not falling versus 5 H1 bars ago.
- Pullback zone: completed bars touch H1 EMA20 within 0.25 * H1 ATR14.
- Confirmation candle: bullish, close above H1 EMA20, body/range >= 0.35, close location >= 0.65.
- Stop: below pullback swing low by 0.25 * M15 ATR14.
- Target: fixed 2R.
- No breakeven, partial, trailing, day masks, month masks, weekly governor, or threshold grid.

## New Repair Filter

One broad session filter only:

- `InpUseDirectionalSessionFilter=true`
- `InpLongSessionStartHour=9`
- `InpLongSessionEndHour=15`

This means long entries are allowed only when server hour is `09, 10, 11, 12, 13, or 14`.

## Variant

Only one exact-MT5 variant is permitted:

- `r1_pullback_long_v2_m15_session_09_15`

## Gates

Standalone gates remain the V1 gates:

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

Combined-with-R1-box gates remain the V1 gates:

- full-window net > routed R1 box baseline
- active weekday percentage improves by at least 5 points over routed R1 box baseline
- raw W/L >= 2.00 or stress W/L >= 1.90
- PF >= 2.00
- max closed drawdown is not worse than routed R1 box baseline by more than 10%
- top 10 winning trades removed net > 0
- top 3 winning days removed net > 0
- no single month contributes more than 30% of net

## Decision

- If standalone and combined gates pass: `R1_PULLBACK_LONG_V2_SESSION_REVIEW_CANDIDATE`.
- If positive but one gate fails: `R1_PULLBACK_LONG_V2_SESSION_SHADOW_ONLY`.
- Otherwise: `R1_PULLBACK_LONG_V2_SESSION_NO_SURVIVOR`.

All outputs remain research-only and require reviewer approval before any demo spec.
