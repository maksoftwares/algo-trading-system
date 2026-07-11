# A1 XAU R5 Pre-Downtrend Break Short V1 Preregistration

Date: 2026-07-11  
Status: `PREREGISTERED_NOT_RUN`  
Boundary: development Strategy Tester only; no broker action is authorized.

## Why a new specialist is required

The exact ten-year H4 long book had 307 entries, but the current short specialists
overlapped none of its position intervals.  In the shared 2022-07 through 2026-06
causal evidence window, H4 was exposed for 84,596 M5 snapshots: 46,539 were Router
`UPTREND`, 24,155 were `CHOP`, and zero were `DOWNTREND`.  A strict-R2 downtrend
short therefore cannot provide contemporaneous diversification.

The new specialist is a pre-downtrend transition short.  It is allowed only in
`UPTREND` or `CHOP`, but it still requires the existing q55 downside impulse,
support break, failed reclaim/retest, and bearish confirmation.  It never reads H4
positions, H4 P/L, equity drawdown, dates of H4 losses, or another strategy's state.

Outcome-blind availability research found 1,185 frozen q55 UPTREND/CHOP opportunity
rows.  After the rule's predeclared spread, cost, and stop ceilings, 767 remained;
324 occurred while H4 was exposed and touched 128 of the 145 common-window H4
positions.  These are pre-daily-cap and pre-position-cap opportunities, not expected
executions and not performance validation.

## One locked variant

Name: `r5_upchop_downside_impulse_retest_q55_v1`

```text
InpRegimeRouterMode                      = 5
InpDirectionMode                         = 2
InpSignalMode                            = 19
InpRiskReward                            = 2.00
InpFixedLots                             = 0.01
InpUseRiskNormalizedLots                 = false
InpMaxSpreadPoints                       = 75
InpMaxEstimatedCostR                     = 0.05
InpMaxTradesPerDay                       = 1
InpCooldownMinutes                       = 0
InpOnePositionPerMagic                   = true
InpMaxOpenPositionsPerMagic              = 1

InpBearRetestLookbackBars                = 10
InpBearRetestSupportLookbackBars         = 12
InpBearRetestBreakAtr                    = 0.10
InpBearRetestTouchAtr                    = 0.05
InpBearRetestReclaimAtr                  = 0.05
InpBearRetestStopBufferAtr               = 0.25
InpBearRetestMinBodyFraction             = 0.55
InpShortCloseLocation                    = 0.25
InpBearImpulseRetestImpulseBars          = 3
InpBearImpulseRetestMinImpulseAtr        = 1.50
InpBearImpulseRetestBreakMinBodyFraction = 0.55

InpStopFloorPoints                       = 350
InpStopCeilingPoints                     = 1000
InpStopCapPoints                         = 0
```

Router mode 5 allows `SHORT` only when causal Router V1 state is `UPTREND` or
`CHOP`.  It blocks `SHOCK`, `COMPRESSION`, `DOWNTREND`, and unknown states.  There
are no H1/H4/D1 add-on filters, session/hour/day/month masks, calendar or P/L
filters, break-even, trailing, partial close, split entry, or daily P/L governor.
The structural stop is skipped if wider than 1,000 points; it is never moved inside
the failed-retest structure.

## Seed evidence is not validation

The same q55 pattern in its old strict-`DOWNTREND` context produced 238 trades,
37.39% WR, 2.4803 realized W/L, 1.4815 PF, USD 367.60 net, 1.3665 stressed PF, and
15.73% native equity drawdown over 2022-07 through 2026-06.  It was negative in
2022 and 2024, inactive in 2025, and negative after removing its top three winning
entry days.  The new regime context must therefore pass from scratch; the old result
does not qualify or select it.

## Exact test and standalone gates

Run exactly one five-year and one ten-year MT5 test on USD 1,000 with fixed 0.01
lot.  Do not optimize or test a neighboring rule after seeing the result.  Both
horizons must have at least 98% history quality and zero order/management failures.

The specialist passes only if:

- ten-year trades are at least 150 and five-year trades are at least 75;
- both horizons have net profit above zero, WR at least 40%, realized W/L at least
  1.80, PF at least 1.30, and native relative equity drawdown no more than 12%;
- both remain net positive with stressed cost of USD 0.30 per trade and stressed PF
  at least 1.20;
- the early and late five-year halves are each nonnegative and at least seven of the
  ten non-overlapping July-through-June horizon-year buckets are positive (the exact
  decade runs from 2016-07-01 through 2026-06-30);
- net remains positive after removing the ten best winning trades and the three best
  winning entry days;
- every execution is tagged causal `UPTREND` or `CHOP`, with no router leakage;
- post-hoc Pearson correlation of daily closed USD P/L with H4 is no more than 0.30,
  using the union of broker exit dates and zero closed P/L when a book has no exit;
- valid signals occur in at least 8 of 13 common-window H4 exposure episodes and at
  least 20 of 39 full-decade H4 exposure episodes.  For this availability gate, a
  valid signal is an `ORDER_SEND_OK`/`ORDER_SEND_FAIL` row or a post-router,
  post-spread/cost/stop `GUARD_BLOCK` caused only by the one-entry-per-day or
  one-position cap.  This measures causal signal availability, not executions.

A standalone failure cannot be rescued by portfolio composition.  Only after every
standalone gate passes may the specialist enter a simultaneous exact-MT5 portfolio
test.  Portfolio admission remains ten-year net at least USD 7,000, native relative
equity drawdown at most 12%, and zero execution failures.

## Frozen evidence

- `outputs/reports/A1_XAU_R5_PRE_DOWNTREND_BREAK_RESEARCH_20260711/`
- `outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709.md`
- `outputs/reports/A1_XAU_ROUTER_ENTRY_HOLD_PATH_EXACT_20260711_FINAL/`

The preferred q55 lane is the only authorized first probe.  The lower-quality
break-and-run/H1-stack idea remains a documented fallback and must not be run in the
same batch as a selection sweep.
