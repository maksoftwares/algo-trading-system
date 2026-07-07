# A1 XAU Bear Engine Improvement Preregistration

Date: 2026-07-07

## Objective

Improve the first bearish-D1 short clue without post-result hour picking.

Reference clue:

- `down_m5_ema_h1h4_short_rr2`
- Exact MT5 standalone: 438 trades, WR 33.11%, W/L 2.1595, PF 1.0687, net +137.34 USD
- Combined with `supportive_guard`: WR 48.74%, W/L 2.1343, active 87.82%, recent3 +414.85 USD, positive weeks 57.42%

Owner request: more trades and better WR, ideally closer to the uptrend engine shape.

## Fixed Boundary

Use exact MT5 Strategy Tester only, isolated root `C:\MT5A1M5MomentumBacktest`.

No live/demo runtime, chart, preset, profile, order, position, or broker-action state may be changed.

Use the existing bearish D1 gate:

- `InpD1SupportStateGateMode=3`
- `InpD1SupportStateEmaPeriod=20`
- `InpD1SupportStateSlopeLagBars=5`

Bearish state:

- `D1 close[1] < D1 EMA(20)[1]`
- `D1 EMA(20)[1] <= D1 EMA(20)[6]`

## Variants

Run exactly these five structural variants over `2022.07.01 -> 2026.06.30`, USD tester currency.

Shared:

- `InpDirectionMode=2`
- `InpRiskReward=2.00`
- `InpMaxSpreadPoints=75`
- `InpBlockedEntryDayHoursCsv=5:20`
- no hour/month post-filtering

### 1. `bear_m5_ema_h1_only_rr2_morefreq`

Loosen HTF confirmation to H1 only to test more trades:

- `InpSignalMode=5`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=false`
- M5 EMA inputs same as clue

### 2. `bear_m5_ema_h1h4_rr2_strict_body`

Increase entry quality:

- `InpSignalMode=5`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpMinRangeAtr=0.50`
- `InpMinBodyFraction=0.45`
- `InpShortCloseLocation=0.35`
- `InpMinThreeBarMoveAtr=0.25`

### 3. `bear_m5_ema_h1h4_rr2_fast_slope`

Require faster M5 bearish momentum:

- `InpSignalMode=5`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpM5TrendMinSlopeAtr=0.08`
- `InpM5TrendMaxDistanceAtr=1.00`

### 4. `bear_ema_pullback_h1h4_rr2`

Test pullback continuation instead of already-extended momentum:

- `InpSignalMode=1`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpPullbackTouchAtr=0.25`
- `InpMinRangeAtr=0.35`
- `InpMinBodyFraction=0.30`
- `InpShortCloseLocation=0.42`
- `InpMinThreeBarMoveAtr=0.10`

### 5. `bear_break_run_h1h4_rr2`

Test direct break-and-run under the same bearish D1/H1/H4 regime:

- `InpSignalMode=0`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpBreakLookbackBars=12`
- `InpBreakAtrMultiple=0.20`
- `InpMinRangeAtr=0.35`
- `InpMinBodyFraction=0.30`
- `InpShortCloseLocation=0.42`
- `InpMinThreeBarMoveAtr=0.10`

## Improvement Gates

A standalone bear improvement clue must beat the reference clue on both:

- trades > 438
- WR > 33.11%

and must also keep:

- W/L >= 2.00
- PF > 1.05
- net > +137.34 USD
- stress W/L at -0.30 USD/ticket >= 1.90

A combined uptrend+bear row is only a review candidate if:

- combined WR >= 50.00%
- combined W/L >= 2.00
- active weekdays >= 85.00%
- stress W/L >= 1.90
- positive weeks improve vs `supportive_guard`

Anything below this is research-only. Do not tune hours from the output.
