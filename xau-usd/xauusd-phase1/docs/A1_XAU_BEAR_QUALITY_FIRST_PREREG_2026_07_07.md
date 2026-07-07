# A1 XAU Bear Quality-First Preregistration

Date: 2026-07-07

## Objective

Shift the bearish branch away from trade-count chasing.

The prior bearish-D1 short clue can preserve payoff, but it is too low-WR:

- Reference: `down_m5_ema_h1h4_short_rr2`
- Exact MT5 standalone: 438 trades, WR 33.11%, W/L 2.1595, PF 1.0687, net +137.34 USD
- Best prior improvement diagnostic: `bear_break_run_h1h4_rr2`, 445 trades, WR 32.13%, W/L 2.3536, PF 1.1144, net +208.00 USD

Owner direction: accept fewer trades if they are cleaner. This pass therefore prioritizes WR, W/L, PF, and cost robustness over activity.

## Fixed Boundary

Use exact MT5 Strategy Tester only, isolated root `C:\MT5A1M5MomentumBacktest`.

No live/demo runtime, chart, preset, profile, order, position, or broker-action state may be changed.

Use the existing default-off bearish D1 gate:

- `InpD1SupportStateGateMode=3`
- `InpD1SupportStateEmaPeriod=20`
- `InpD1SupportStateSlopeLagBars=5`

Bearish state:

- `D1 close[1] < D1 EMA(20)[1]`
- `D1 EMA(20)[1] <= D1 EMA(20)[6]`

Shared:

- `InpDirectionMode=2`
- `InpRiskReward=2.00`
- `InpMaxSpreadPoints=75`
- `InpBlockedEntryDayHoursCsv=5:20`
- no hour/month post-filtering

## Variants

Run exactly these six structural variants over `2022.07.01 -> 2026.06.30`, USD tester currency.

### 1. `bear_quality_m5_ema_slope50`

High-quality M5 EMA continuation under bearish D1/H1/H4:

- `InpSignalMode=5`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpH1TrendMinSlopePoints=50`
- `InpH4TrendMinSlopePoints=50`
- `InpM5TrendMinSlopeAtr=0.08`
- `InpM5TrendMaxDistanceAtr=0.80`
- `InpMinRangeAtr=0.50`
- `InpMinBodyFraction=0.45`
- `InpShortCloseLocation=0.35`
- `InpMinThreeBarMoveAtr=0.25`
- `InpMaxThreeBarMoveAtr=2.50`
- `InpMaxEstimatedCostR=0.04`

### 2. `bear_quality_m5_ema_slope100`

Same as variant 1, but require stronger H1/H4 trend slope:

- `InpH1TrendMinSlopePoints=100`
- `InpH4TrendMinSlopePoints=100`
- `InpM5TrendMinSlopeAtr=0.10`
- `InpM5TrendMaxDistanceAtr=0.75`

### 3. `bear_quality_break_run_tight`

Tight break-and-run short, avoiding weak breaks and exhaustion:

- `InpSignalMode=0`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpH1TrendMinSlopePoints=50`
- `InpH4TrendMinSlopePoints=50`
- `InpBreakLookbackBars=12`
- `InpBreakAtrMultiple=0.30`
- `InpMinBreakDistanceAtr=0.10`
- `InpMaxBreakDistanceAtr=0.80`
- `InpMinRangeAtr=0.55`
- `InpMinBodyFraction=0.50`
- `InpShortCloseLocation=0.30`
- `InpMinThreeBarMoveAtr=0.40`
- `InpMaxThreeBarMoveAtr=2.20`
- `InpMaxEstimatedCostR=0.04`

### 4. `bear_quality_compression_break`

Compression then downside expansion under bearish D1/H1/H4:

- `InpSignalMode=2`
- `InpUseH1TrendFilter=true`
- `InpUseH4TrendFilter=true`
- `InpH1TrendMinSlopePoints=50`
- `InpH4TrendMinSlopePoints=50`
- `InpCompressionLookbackBars=8`
- `InpCompressionMaxRangeAtr=0.80`
- `InpCompressionBreakAtrMultiple=0.15`
- `InpMinRangeAtr=0.50`
- `InpMinBodyFraction=0.45`
- `InpShortCloseLocation=0.35`
- `InpMinThreeBarMoveAtr=0.25`
- `InpMaxThreeBarMoveAtr=2.50`
- `InpMaxEstimatedCostR=0.04`

### 5. `bear_quality_h4_pullback_d1bias`

H4 pullback continuation with D1 bearish bias:

- `InpSignalMode=8`
- `InpUseH1TrendFilter=false`
- `InpUseH4TrendFilter=false`
- `InpOnePositionPerMagic=true`
- `InpMaxEstimatedCostR=0.08`

### 6. `bear_quality_weekly_rejection`

Weekly resistance rejection in bearish D1 state:

- `InpSignalMode=9`
- `InpUseH1TrendFilter=false`
- `InpUseH4TrendFilter=false`
- `InpOnePositionPerMagic=true`
- `InpMaxEstimatedCostR=0.10`

## Quality Gates

A standalone bear review candidate must keep:

- trades >= 60
- WR >= 50.00%
- W/L >= 2.00
- PF >= 1.20
- net > 0
- stress W/L at -0.30 USD/ticket >= 1.90

A standalone watchlist-quality clue must keep:

- trades >= 60
- WR >= 45.00%
- W/L >= 2.00
- PF >= 1.10
- net > 0
- stress W/L at -0.30 USD/ticket >= 1.90

A combined uptrend+bear row is only a review candidate if:

- combined WR >= 50.00%
- combined W/L >= 2.00
- active weekdays >= 85.00%
- stress W/L >= 1.90
- positive weeks improve vs `supportive_guard`

Anything below this is research-only. Do not tune hours, weekdays, months, or thresholds from the output.
