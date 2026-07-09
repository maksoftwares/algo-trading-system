# A1 XAU R1 Long Expansion R3 Reclass Exact-MT5 Preregistration

Date: 2026-07-09

Status: preregistered research-only test. No demo/live runtime, chart, preset, order, position, account, broker, or profile state is authorized to change.

## Purpose

The R3 D1-compression/H4-expansion long source looked strong in full-window exact-MT5 results, but the router-alignment audit showed it is not a true compression specialist. Most of its edge was tagged to EA-router R1 uptrend states.

This test asks one narrow question:

Can the frozen R3 signal be reclassified as a strict R1 long-expansion module when executed directly through the EA-side R1 router?

## Hypothesis

The existing D1-compression/H4-expansion long source is not a compression specialist. It is a second long-expansion module that performs primarily during EA-router R1 uptrend states.

If routed through strict R1 only, it should preserve the majority of the audited uptrend profit, avoid the recent chop loss, improve the current R1+R2 full-window book, and not worsen drawdown beyond the predeclared limit.

## Exact-MT5 Test Scope

Window:

```text
2022-07-01 through 2026-06-30
```

Run exactly one candidate variant:

```text
A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709
```

No R4, no frequency filler, no parameter grid, no recomposed snapshot subset as promotion evidence.

## Frozen Inputs

Signal:

```text
InpSignalMode = 7
InpDirectionMode = 1
InpRiskReward = 2.00
```

Router:

```text
InpRegimeRouterMode = 1
Use EA-side Router V1 R1 state only
Do not use the 10-year D1 regime map for execution
```

Router V1 parameters:

```text
InpRegimeFastEmaPeriod = 20
InpRegimeSlowEmaPeriod = 50
InpRegimeSlopeLagBars = 5
InpRegimePersistenceD1Bars = 2
InpRegimeRequireH4Confirm = true
InpRegimeShockH1RangeAtrMultiple = 3.00
InpRegimeShockD1AtrPercentileMin = 95.00
InpRegimeShockD1AtrLookback = 60
InpRegimeCompressionD1AtrPercentileMax = 30.00
InpRegimeCompressionBoxDays = 5
InpRegimeCompressionRangeMedianMax = 1.00
```

Risk, position, and frozen R3 thresholds:

```text
InpMaxEstimatedCostR = 0.15
InpStopCeilingPoints = 0
InpMaxTradesPerDay = 6
InpCooldownMinutes = 0
InpOnePositionPerMagic = false
InpMaxOpenPositionsPerMagic = 16
InpD1CompressionAtrPercentileMax = 60.00
InpD1CompressionBoxDays = 3
InpD1CompressionRangeMedianMax = 1.25
InpD1CompressionH4MinBodyFraction = 0.35
InpUseH1TrendFilter = false
InpUseH4TrendFilter = false
```

Explicit disabled layers:

```text
InpH4D1SupportiveStateGuardEnabled = false
InpH4D1WeeklyLossGovernorEnabled = false
InpH4D1PrevMonthHealthGateEnabled = false
InpH4D1NegativeStackGuardEnabled = false
InpH4D1ThirdEntryQualityGateEnabled = false
InpProfitProtectionEnabled = false
InpPartialCloseEnabled = false
InpSplitEntryEnabled = false
InpBlockedEntryHoursCsv =
InpBlockedEntryDayHoursCsv =
InpBlockedLongEntryHoursCsv =
InpBlockedShortEntryHoursCsv =
InpUseDirectionalSessionFilter = false
```

## Forbidden

```text
No threshold changes
No second candidate variant
No R1 relaxation
No uptrend+shock variant
No uptrend+transition variant
No session/hour/day/month filter
No break-even, partial close, or trailing stop
No RR change
No R4 inclusion
No R2 modification
No portfolio grid
```

## Current Baseline

Combine only with the current R1+R2 baseline:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv
```

Reference metrics from the reviewer:

```text
Net:        +$9,640.05
Stress net: +$9,436.65
Recent3:    +$764.92
Max DD:     $889.69
```

The script must recompute these from the baseline CSV rather than trusting text.

## Standalone Pass Gate

The R1-routed R3 source is a standalone review candidate only if all are true:

```text
Trades >= 100
WR >= 55%
W/L >= 2.00
PF >= 2.50
Stress PF after -$0.30/trade >= 2.25
Net >= +$5,000
Stress net >= +$4,500
2023-2024 net >= 0
Top10-removed net > 0
Top3-days-removed net > 0
Max closed DD <= $900
Best-month share <= 35%
Recent3 net >= -$50
```

## Combined Pass Gate

Combined with current R1+R2 passes only if all are true:

```text
Combined net >= current R1+R2 net + $2,000
Combined stress net >= current R1+R2 stress net + $2,000
Combined WR >= 50%
Combined W/L >= 2.00
Combined PF >= 2.50
Combined max DD <= 115% of current R1+R2 max DD
Combined recent3 net >= current R1+R2 recent3 net - $50
Top10-removed net > 0
Top3-days-removed net > 0
Best-month share <= 30%
Positive months >= current R1+R2 positive months
```

## Decision Labels

Use exactly one:

```text
R1_LONG_EXPANSION_R3_RECLASS_REVIEW_CANDIDATE
R1_LONG_EXPANSION_R3_RECLASS_SHADOW_ONLY
R1_LONG_EXPANSION_R3_RECLASS_NO_SURVIVOR
R1_LONG_EXPANSION_R3_RECLASS_INVALID_TEST
```

Review candidate: standalone and combined gates pass.

Shadow only: standalone passes but combined fails, or combined improves net but fails drawdown or recent-three-month limits.

No survivor: standalone fails the main quality gates.

Invalid test: router not strict R1, thresholds changed, extra regime allowed, R4 included, R2 modified, RR changed, management layers enabled, session/hour/day/month filters introduced, raw MT5 evidence missing, or snapshot/recomposition is used instead of exact-MT5 for the candidate.

## Kill Rules

If this test fails, freeze R3 as a compression specialist and as an R1 reclassification candidate. Do not run R3 threshold variants, uptrend+shock variants, uptrend+transition variants, session variants, or portfolio grids. Do not add R3 to the current portfolio.

