# A1 XAU R3 Compression Long V1 Exact-MT5 Preregistration

Date: 2026-07-09

## Purpose

Open a separate R3 compression specialist lane after R4 chop fades failed to produce a durable edge.

Existing exact-MT5 compression evidence showed a consistent directional split across the D1-compression/H4-expansion ladder: long trades carried the edge, while shorts diluted it. This pass tests that structural split directly with one long-only exact-MT5 run.

This is not a parameter grid. The thresholds are copied from the prior preregistered broad compression cell that produced the strongest full-window directional clue.

## Signal

Use the existing EA D1-compression/H4-expansion signal:

- `InpSignalMode=7`
- `InpDirectionMode=1`
- fixed `2.00R`
- no breakeven, partial, trailing, weekly governor, previous-month health gate, hour-mining, day-mining, month-mining, or router override

Fixed inputs:

- `InpRiskReward=2.00`
- `InpMaxEstimatedCostR=0.15`
- `InpStopCeilingPoints=0`
- `InpMaxTradesPerDay=6`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=16`
- `InpD1CompressionAtrPercentileMax=60.00`
- `InpD1CompressionBoxDays=3`
- `InpD1CompressionRangeMedianMax=1.25`
- `InpD1CompressionH4MinBodyFraction=0.35`
- `InpUseH1TrendFilter=false`
- `InpUseH4TrendFilter=false`

## Variant

Only one exact-MT5 variant is permitted:

- `r3_compression_long_v1_broad_box3_atr60_range125_body035`

## Standalone Gates

- full-window trades >= 150
- full-window WR >= 50%
- full-window W/L >= 2.00
- full-window PF >= 2.00
- stress PF after -$0.30/ticket >= 1.50
- stress W/L after -$0.30/ticket >= 1.90
- full-window net > 0
- 2023+2024 net >= 0
- top 10 winning trades removed net > 0
- top 3 winning days removed net > 0

Recent 3-month activity is diagnostic, not a hard failure, because this is a compression-regime specialist and should be silent outside compression.

## Combined Gates

Combine with the current R1 book:

- `A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv`

Deduplicate same-direction overlap using the existing 5-minute portfolio dedupe.

Combined candidate gates:

- net > current R1 book net
- WR >= 50%
- W/L >= 2.00 or stress W/L >= 1.90
- PF >= 2.00
- max closed drawdown not worse than current R1 book by more than 25%
- top 10 winning trades removed net > 0
- top 3 winning days removed net > 0

## Decision

- If standalone and combined gates pass: `R3_COMPRESSION_LONG_V1_REVIEW_CANDIDATE`.
- If standalone passes but combined gates fail: `R3_COMPRESSION_LONG_V1_STANDALONE_SHADOW`.
- Otherwise: `R3_COMPRESSION_LONG_V1_NO_SURVIVOR`.

All outputs remain research-only and require reviewer approval before any demo spec.
