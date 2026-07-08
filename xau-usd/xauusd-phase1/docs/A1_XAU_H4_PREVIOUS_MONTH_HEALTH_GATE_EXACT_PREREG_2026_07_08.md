# A1 XAU H4 Previous-Month Health Gate Exact-MT5 Preregistration

Date: 2026-07-08

## Goal

Convert the previous-month H4 source-health watchlist clue into an exact-MT5 component rerun.

The offline clue was:

> If H4/D1 source net was below `-$50` in the previous closed month, pause H4/D1 entries in the
> next month.

It improved the long+V2 portfolio from `29/19` positive/negative closing months to `31/17`,
while preserving net, WR, W/L, stress W/L, and activity.

## Boundary

- Exact MT5 Strategy Tester rerun only for the H4/D1 components.
- Recompose the exact H4 rerun with existing exact-MT5 frequency and V2 short hedge ledgers.
- No live/demo runtime, chart, preset, order, position, or broker state changes.
- No demo claim from this pass.

## Implementation Note

The current exact-MT5 H4 runner executes H4 components separately. Therefore this pass tests the
implementable component-local version of the gate:

- each H4 component pauses itself if its own previous closed month net is below `-$50`;
- the broad H4 component is still rerun, but the box2 component is expected to dominate because
  the broad component contributes only sparse trades in the current frontier.

If this component-local exact run materially diverges from the offline group-gate clue, do not
promote it. Instead, either accept the component-local result or build a true combined H4 runtime.

## Fixed MT5 Inputs

Common H4 inputs:

- `InpSignalMode=7`
- `InpDirectionMode=1`
- `InpRiskReward=2.00`
- `InpMaxEstimatedCostR=0.15`
- `InpStopCeilingPoints=0`
- `InpStopCapPoints=0`
- `InpMaxTradesPerDay=6`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=32`
- `InpBlockedEntryDayHoursCsv=5:20`
- `InpBlockedLongEntryHoursCsv=3,10,13,14`
- `InpH4D1SupportiveStateGuardEnabled=true`
- `InpH4D1SupportiveEmaPeriod=20`
- `InpH4D1SupportiveSlopeLagBars=5`
- `InpH4D1PrevMonthHealthGateEnabled=true`
- `InpH4D1PrevMonthNetMinUsd=-50.00`

Components:

- `box2`: ATR percentile `80`, box days `2`, range median max `1.50`, min H4 body `0.35`
- `broad`: ATR percentile `60`, box days `3`, range median max `1.25`, min H4 body `0.35`

## Metrics

Compare against the existing long+V2 no-source-health-gate ledger:

- signals, WR, W/L, PF, net;
- stressed W/L and stressed net at `$0.30` per ticket;
- max closed drawdown ordered by trade close time;
- active weekday percentage;
- positive and negative closing months;
- positive calendar-week percentage;
- worst month and worst week;
- H4 gate guard-block counts.

## Decision Rules

- `EXACT_SOURCE_HEALTH_REVIEW_CANDIDATE`: positive closing months `>= 32`, net `>= 19000`,
  WR `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, active weekdays `>= 84%`, and max drawdown
  improves by at least `10%` versus baseline.
- `EXACT_SOURCE_HEALTH_WATCHLIST`: positive closing months improve by at least `2` while
  preserving net `>= 19000`, WR `>= 48%`, W/L `>= 2.0`, stressed W/L `>= 1.90`, and active
  weekdays `>= 84%`.
- `EXACT_MONTHLY_IMPROVES_CORE_BREAKS`: positive months improve, but core/net/activity breaks.
- `EXACT_REJECT_NO_MONTHLY_REPAIR`: no useful monthly repair.

Any pass remains research-only pending reviewer approval.
