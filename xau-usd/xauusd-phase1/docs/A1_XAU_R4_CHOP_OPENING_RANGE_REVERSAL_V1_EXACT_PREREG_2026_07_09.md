# A1 XAU R4 Chop Opening-Range Reversal V1 Exact-MT5 Preregistration

Date: 2026-07-09

## Purpose

Test whether the existing opening-range reversal source can become a useful R4 chop specialist when it is routed through the EA-side chop regime guard.

This is a research-only exact-MT5 test. It must not touch live/demo charts, profiles, presets, orders, positions, account state, or broker runtime state.

## Background

The 10-year regime map and current-candidate attribution showed:

- R1 long is the strongest uptrend engine, but it naturally has no recent activity when the market is no longer in the R1 regime.
- R2 continuation short is the useful recent defender, especially during downtrend/transition.
- Prior R4 chop attempts did not earn their keep:
  - failed-break/sweep-reclaim was roughly breakeven and weak standalone.
  - daily-extreme reclaim was negative.
  - prior-day reclaim was weak and lost inside chop.
- Older opening-range reversal research was not good enough as a standalone family, but the London firm variant had high activity and near-2R realized payoff. A non-uptrend OR-reversal overlay also showed that this source can sometimes add small portfolio value without breaking core shape.

The missing piece is still an R4/chop specialist that can trade during the March-June 2026 style market without diluting the portfolio.

## Fixed Hypothesis

In chop regimes, a London opening-range false break and reclaim should be a better structural source than generic failed-break or prior-day reclaim because it anchors entries to a fresh intraday reference range instead of stale daily levels.

## Fixed MT5 Configuration

All variants:

- `InpRegimeRouterMode = 4` (R4 chop-only)
- `InpSignalMode = 6` (opening-range reversal)
- `InpRiskReward = 2.00`
- `InpUseH1TrendFilter = false`
- `InpUseH4TrendFilter = false`
- `InpUseDirectionalSessionFilter = false`
- `InpProfitProtectionEnabled = false`
- `InpPartialCloseEnabled = false`
- `InpSplitEntryEnabled = false`
- `InpOpeningRangeStartHour = 7`
- `InpOpeningRangeMinutes = 60`
- `InpOpeningTradeWindowHours = 5`
- `InpOpeningBreakAtrMultiple = 0.10`
- `InpReclaimAtrMultiple = 0.05`
- `InpMinRangeAtr = 0.40`
- `InpMinBodyFraction = 0.35`
- `InpLongCloseLocation = 0.60`
- `InpShortCloseLocation = 0.40`
- `InpStopAtrMultiple = 1.50`
- `InpStopFloorPoints = 250`
- `InpStopCeilingPoints = 1400`
- `InpMaxEstimatedCostR = 0.08`
- `InpMaxSpreadPoints = 75`
- `InpMaxTradesPerDay = 24`
- `InpCooldownMinutes = 0`
- `InpOnePositionPerMagic = true`

## Variants

Exactly three variants:

1. `r4_chop_orrev_london_firm_both`
   - both directions
2. `r4_chop_orrev_london_firm_long`
   - long-only
3. `r4_chop_orrev_london_firm_short`
   - short-only

This is a direction-diagnostic pass, not a parameter grid.

## Evaluation Window

Use the existing exact-MT5 research window:

- Start: 2022-07-01
- End: 2026-06-30

The recent-three-month window is:

- 2026-04-01 through 2026-06-30

## Baseline

Compare against the current best R1+R2 combined book:

`A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv`

This baseline is the current best portfolio, so R4 only matters if it improves that book.

## Standalone Pass Checks

A standalone R4 row must satisfy:

- trades >= 150
- win rate >= 45%
- realized W/L >= 1.80
- profit factor >= 1.30
- stressed W/L after -0.30 USD/ticket >= 1.65
- stressed PF after -0.30 USD/ticket >= 1.15
- net > 0
- recent-three-month trades >= 20
- recent-three-month net > 0
- 2023-2024 net >= 0
- top-10-trades-removed net > 0
- top-3-days-removed net > 0

## Combined Pass Checks

The R4 plus current R1+R2 book must satisfy:

- net > current R1+R2 baseline net
- recent-three-month net > current R1+R2 baseline recent-three-month net
- win rate >= 50%
- realized W/L >= 2.00 or stressed W/L after -0.30 USD/ticket >= 1.90
- PF >= 2.00
- stressed net after -0.30 USD/ticket > 0
- max closed drawdown <= 115% of current R1+R2 baseline max closed drawdown
- top-10-trades-removed net > 0
- top-3-days-removed net > 0

## Decision Rule

- If any variant passes standalone and combined checks: `R4_CHOP_ORREV_V1_REVIEW_CANDIDATE`.
- If no variant passes all checks but at least one variant is standalone positive and improves recent-three-month combined net: `R4_CHOP_ORREV_V1_SHADOW_ONLY`.
- Otherwise: `R4_CHOP_ORREV_V1_NO_SURVIVOR`.

No threshold or hour tuning is allowed after seeing this output.

