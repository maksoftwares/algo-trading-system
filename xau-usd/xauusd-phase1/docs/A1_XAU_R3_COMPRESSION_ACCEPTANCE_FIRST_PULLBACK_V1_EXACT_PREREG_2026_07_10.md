# A1 XAU R3 Compression Acceptance / First Pullback V1 Exact-MT5 Preregistration

Date: `2026-07-10`

Status: `PREREGISTERED_IMPLEMENTATION_PENDING_NOT_RUN`

Administrative revision: signal mode `24` was found to be already frozen for the
mature R2 second-continuation family. Before R3 implementation and before any history
run, this preregistration was renumbered to the next append-only mode, `25`. This is an
administrative collision fix only; setup, entry, risk, windows, and gates did not
change as a result of the renumbering.

## Purpose

Test one genuinely new third specialist owned by a completed D1-compression event and
an explicit compression-release transition. The entry is not the raw breakout: it
requires a completed-H1 acceptance beyond the frozen compression box, followed by the
first completed-M15 pullback/rejection at that boundary.

This replaces, rather than tunes, the killed completed-H4 release cell. That cell took
the release bar itself, produced only 18 executions, repeated 85 one-position blocks
across 107 would-signals, and had a weak short leg. V1 changes the causal event and
entry mechanism: one registered compression event, one H1 acceptance, one first-touch
M15 decision, and permanent event consumption. It is not an H4 threshold sibling.

One frozen candidate is allowed. Failure retires this family; it does not authorize a
second box length, acceptance threshold, pullback window, direction mask, or calendar
filter.

## Frozen exact cells

The identical candidate and inputs must run in two independent exact-MT5 cells:

| Cell | From | To | Starting deposit |
| --- | --- | --- | ---: |
| `prehistory_2016_2021` | `2016-01-01` | `2021-12-31` | `$10,000 USD` |
| `current_2022_2026` | `2022-07-01` | `2026-06-30` | `$10,000 USD` |

- Symbol/tester chart: `XAUUSD`, `M5`.
- Decisions: completed D1, H1, and M15 bars only.
- Tester: every tick, local agent only.
- Both cells are mandatory; neither is a design window.

## Causal event definition

At the first eligible completed-H1 decision of a new D1 trading date, register one
setup only when the immediately preceding completed D1 data satisfy all of the
following:

1. D1 ATR14 percentile over 252 completed observations, evaluated at shift `1`, is
   `<= 30`.
2. The frozen box is the high/low of exactly five completed D1 bars, shifts `[1..5]`.
3. `box_width / 5 <= 1.00 * median(D1 high-low)` over 20 completed D1 bars.
4. The existing completed-bar shock detector is false.

The setup stores an immutable event ID, setup timestamp, box high/low, compression
features, and expires after 24 completed H1 bars. Only one unconsumed R3 event may
exist. A later compressed date may not overwrite an active event.

Lifetimes are completed-bar counters, not wall-clock durations: weekend and XAUUSD
maintenance gaps consume no H1 or M15 slots. The H1 bar that registers the setup is
acceptance decision 1 of 24. After acceptance, the first M15 decision whose close is
strictly later than the acceptance timestamp is pullback decision 1 of 12.

## Completed-H1 acceptance

The first completed H1 bar that accepts outside the frozen box fixes direction:

- long: close is at least `0.10 * H1 ATR14` above box high, body/range is at least
  `0.50`, and close location is at least `0.75`;
- short: the exact mirror below box low, with close location no more than `0.25`.

Acceptance stores its H1 ATR and timestamp and opens a 12-completed-M15-bar pullback
window. If both sides would qualify because of invalid data, the event is consumed as
ambiguous with no trade. No established R1/R2 trend filter grants permission.

If the canonical direction becomes established `UP` or `DOWN` before entry, the event
is consumed as `established_trend_handoff`; R3 may not steal an established R1/R2
entry. Shock at setup, acceptance, or entry consumes the event with no trade.

## First completed-M15 pullback

Only the first completed M15 bar that enters the frozen boundary touch band is
eligible. The touch band is `+/- 0.25 * M15 ATR14` around the accepted box boundary.

For long, the first-touch bar must close at least `0.10 * M15 ATR14` back above the
boundary, have body/range at least `0.50`, and close location at least `0.75`. Short is
the exact mirror with close location at most `0.25`.

- If the first touch lacks confirmation, consume the event as `first_touch_failed`.
- If a completed M15 close crosses `0.10 * frozen acceptance H1 ATR` through the wrong
  side of the boundary, consume it as `invalidated`.
- If 12 M15 bars elapse, consume it as `expired`.
- On a qualifying signal, consume the event before position, risk, or broker guards
  run. A blocked or failed order may never cause the same event to signal again.

The structural stop is beyond the first-touch M15 extreme plus `0.20 * M15 ATR14`.
Reject the signal if stop distance exceeds `1.00 * frozen acceptance H1 ATR`. Target is
fixed at `2.00R`. Absolute stop floors, ceilings, and caps are disabled.

## Native ownership and mandatory event telemetry

Setup ownership is completed `COMPRESSED`; entry ownership is registered
`TRANSITION`, non-shock, and not established `UP` or `DOWN`. The entry-time legacy
flat label is diagnostic only.

The signal ledger must encode a stable event ID and log exactly one lifecycle:

1. `R3_EVENT_REGISTERED` with `setup=COMPRESSED`;
2. zero or one `R3_H1_ACCEPTED`;
3. exactly one `R3_EVENT_CONSUMED` with reason `entry`, `first_touch_failed`,
   `invalidated`, `expired`, `shock`, `established_trend_handoff`, `ambiguous`, or
   the non-strategy right-censoring reason `window_end_incomplete`;
4. at most one `WOULD_SIGNAL` per event.

`window_end_incomplete` is emitted only when a finite tester window deinitializes with
an event whose applicable 24-H1 setup or 12-M15 pullback lifetime has not elapsed. It
is audited separately, is limited to at most one event per window, and is not counted
as an alpha failure or as an expiry.

Every executed entry must join by timestamp to a `WOULD_SIGNAL` record containing:

```text
event_id=<id>|setup=COMPRESSED|phase=TRANSITION|shock=0|established=0
```

Blocked attempts may occur outside ownership, but no executed entry may. Reports must
show registered, accepted, consumed, duplicate-signal, missing-consumption, and
native-state-purity counts. PnL concentration by event ID is mandatory.

## Frozen EA contract and inputs

The implementation must add one default-off signal mode:

```text
SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK = 25
```

The existing R3 shock-block router mode `5` must accept only the old diagnostic H4
mode or this new mode; the runner selects only mode `25`.

```text
InpSignalMode=25
InpDirectionMode=0
InpRegimeRouterMode=5
InpRegimeSnapshotLogEnabled=true

InpR3CompressionAtrPeriod=14
InpR3CompressionAtrPercentileLookback=252
InpR3CompressionAtrPercentileMax=30.00
InpR3CompressionBoxDays=5
InpR3CompressionRangeMedianLookback=20
InpR3CompressionRangeMedianMax=1.00
InpR3SetupLifetimeH1Bars=24

InpR3AcceptBreakMarginH1Atr=0.10
InpR3AcceptMinBodyFraction=0.50
InpR3AcceptLongCloseLocationMin=0.75
InpR3AcceptShortCloseLocationMax=0.25
InpR3RetestWindowM15Bars=12
InpR3RetestTouchM15Atr=0.25
InpR3InvalidationH1Atr=0.10
InpR3RejectDistanceM15Atr=0.10
InpR3RejectMinBodyFraction=0.50
InpR3RejectLongCloseLocationMin=0.75
InpR3RejectShortCloseLocationMax=0.25
InpR3StopBufferM15Atr=0.20
InpR3MaxStopH1Atr=1.00
InpR3ConsumeOnFirstTouch=true

InpRiskReward=2.00
InpStopFloorPoints=0
InpStopCeilingPoints=0
InpStopCapPoints=0
InpMaxEstimatedCostR=0.15

InpUseRiskNormalizedLots=true
InpRiskAmountUsd=50.00
InpMaxRiskLots=0.50
InpRejectRiskOvershootEnabled=true
InpMaxRiskOvershootPct=0.00

InpOnePositionPerMagic=true
InpMaxOpenPositionsPerMagic=1
InpMaxTradesPerDay=0
InpCooldownMinutes=0

InpBlockedEntryHoursCsv=
InpBlockedEntryDayHoursCsv=
InpBlockedLongEntryHoursCsv=
InpBlockedShortEntryHoursCsv=
InpUseDirectionalSessionFilter=false
InpLongSessionStartHour=0
InpLongSessionEndHour=24
InpShortSessionStartHour=0
InpShortSessionEndHour=24
InpMinAtrAbsoluteForEntry=0.00

InpFeatureLossFilterEnabled=false
InpUseH1TrendFilter=false
InpUseH4TrendFilter=false
InpH4D1SupportiveStateGuardEnabled=false
InpD1SupportStateGateMode=0
InpD1StructuralDownGateEnabled=false
InpPortfolioDailyGuardEnabled=false
InpH4D1WeeklyLossGovernorEnabled=false
InpH4D1PrevMonthHealthGateEnabled=false
InpH4D1NegativeStackGuardEnabled=false
InpH4D1ThirdEntryQualityGateEnabled=false
InpProfitProtectionEnabled=false
InpPartialCloseEnabled=false
InpSplitEntryEnabled=false
InpEarlyAdverseExitEnabled=false
```

`InpMaxTradesPerDay=0` disables the daily-frequency guard. One-position ownership is
the only concurrency limit.

Risk qualification is fail-closed and may not rely only on tick-value arithmetic. The
implementation must add `R3TransitionHardRiskAllowed`, calculate the normalized
entry-to-stop loss using `OrderCalcProfit` for BUY or SELL as appropriate, require USD
account currency, reject missing/invalid/non-positive calculator evidence, and reject
any actual initial risk above `$50.00`. The guard reason is frozen as
`r3_normalized_entry_to_stop_risk_overshoot`. Every successful order row must log the
calculated `actual_risk_usd`; the exact report must show count, minimum, mean, maximum,
missing count, and above-budget count.

Frozen tester-input SHA256 (canonical sorted compact JSON):

```text
ca53d3b0e4b19df61b45c110943452178f3b45b547ff154860b517d2c02bfc5f
```

## Frozen admission gates

Both exact cells must contain at least `100` executed trades and positive stressed net.
The two ledgers are then joined for global admission without changing either tester
result.

Global gates:

- win rate `>= 50%`;
- realized average win/loss `>= 2.00`;
- profit factor `>= 2.00`;
- profit factor after `-$0.30` per ticket `>= 1.75` and stressed net positive;
- at least three calendar years with exposure and three profitable calendar years;
- long and short each have at least 50 trades and positive stressed net;
- top-ten-winners-removed net positive;
- top-three-entry-days-removed net positive;
- best-month share `<= 30%`;
- no single event contributes more than `50%` of positive global net;
- both exact cells have balance and equity drawdown relative `<= 20%`;
- in both cells, net / maximal MT5 equity drawdown `>= 2.00` and maximal equity DD is
  no more than `2.0x` closed-ledger DD;
- 100% native setup/entry purity, exactly one consumption per registered event, and at
  most one signal per event;
- successful sends, MT5 trades, and normalized rows reconcile in each cell;
- zero unexplained order failures, zero open-at-end positions, and zero forbidden
  calendar/session/previous-PnL guard blocks.

Risk-overshoot blocks and one-position blocks are reported diagnostics. They are not
alpha filters, and the consumed event may not retry after either block.

## Decision

- `R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_STANDALONE_SHADOW` only if every gate
  passes.
- `R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_NO_SURVIVOR` for any gate failure.

Passing remains research-only. Portfolio inclusion requires a later preregistered
same-event overlap audit and exact shared-equity portfolio run.
