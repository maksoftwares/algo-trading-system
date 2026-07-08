# A1 XAU R4 Chop Failed-Break V1 Exact-MT5 Preregistration

Date: 2026-07-08

## Purpose

The recent regime audit found that the last three completed months were dominated by Router V1 `chop`:

- Last 6 months: chop was 49.98% of M5 bars and 50.98% of days.
- Last 3 months: chop was 59.15% of M5 bars and 59.21% of days.
- April 2026 was 83.00% chop, May 2026 was 58.79% chop, and June 2026 shifted to 58.87% downtrend with 35.49% chop.

This test builds the missing R4 specialist without weakening the R1 uptrend long specialist.

## Router

Add and use `REGIME_ROUTER_R4_CHOP_ONLY`.

Rules:

- Allow both long and short only when `CurrentXauRegime() == XAU_REGIME_CHOP`.
- Block shock, uptrend, downtrend, compression, and unknown.
- Router parameters remain the Router V1 values.

## Signal

Use the existing EA `SIGNAL_SWEEP_RECLAIM` trigger as a failed-break/range-fade candidate.

Fixed inputs:

- `InpSignalMode=3`
- `InpDirectionMode=0`
- `InpRiskReward=2.00`
- `InpSweepLookbackBars=12`
- `InpSweepAtrMultiple=0.10`
- `InpReclaimAtrMultiple=0.05`
- `InpMinRangeAtr=0.60`
- `InpMinBodyFraction=0.45`
- `InpLongCloseLocation=0.72`
- `InpShortCloseLocation=0.28`
- `InpStopFloorPoints=350`
- `InpStopCeilingPoints=2200`
- no hour, day, month, news, breakeven, partial, trailing, weekly governor, or previous-month health filters.

## Variant

Only one exact-MT5 variant is permitted:

- `r4_chop_failed_break_v1_sweep_reclaim`

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

Combine with the current R1 book:

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

- If standalone and combined gates pass: `R4_CHOP_FAILED_BREAK_V1_REVIEW_CANDIDATE`.
- If standalone is positive or combined improves recent coverage without breaking core shape: `R4_CHOP_FAILED_BREAK_V1_SHADOW_ONLY`.
- Otherwise: `R4_CHOP_FAILED_BREAK_V1_NO_SURVIVOR`.

All outputs remain research-only and require reviewer approval before any demo spec.
