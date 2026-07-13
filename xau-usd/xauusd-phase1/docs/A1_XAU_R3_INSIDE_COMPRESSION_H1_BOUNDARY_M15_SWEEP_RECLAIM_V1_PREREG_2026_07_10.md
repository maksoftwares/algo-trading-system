# A1 XAU R3 Inside-Compression H1-Boundary / M15 Sweep-Reclaim V1 Preregistration

Date: `2026-07-10`

Status: `PREREGISTERED_LOCKED_NOT_IMPLEMENTED_NOT_RUN`

Signal mode: proposed append-only mode `28`

Runner: `scripts/run_a1_r3_inside_compression_h1_boundary_m15_sweep_reclaim_v1_exact.py`

## Decision and evidence boundary

This document freezes one exact-MT5 candidate before its EA implementation or any
mode-28 history run. It does not authorize demo or live trading. Historical execution
remains locked in the runner until a separate implementation/readiness review.

Mode 25 is killed. It registered completed-D1 compression once, waited for an H1
release acceptance, then waited for the first M15 pullback. It produced only three
would-signals and zero executions in 2016-2021, then one would-signal and one executed
loss in 2022-2026. No acceptance, release, pullback-window, or boundary-threshold
sibling is authorized.

Mode 28 is a different owner and different event process. It trades *inside* an
eligible compression episode. It registers a fresh completed-H1 rolling-range event
each hour and gives only the next four completed M15 bars one first-sweep/reclaim
attempt. It never requires an outside-box H1 release, acceptance, or pullback.

The older R4 failed-break control is also different: it used an M5 rolling range,
the legacy chop projection, absolute stop floors/ceilings, stacking, and only the
recent era. Mode 28 uses completed-D1 compression ownership, completed-H1 frozen
boundaries, scalar M15 events, normalized risk, one position, and both frozen eras.
Overlap against that closest control is mandatory in the recent era.

There is exactly one candidate. No grid, threshold sibling, direction-only rescue,
calendar mask, session mask, previous-PnL gate, or post-result management repair is
authorized by a failure.

## Frozen causal owner

### Completed-D1 compression context

On the first newly completed H1 decision of each broker D1 date, mode 28 evaluates
only completed D1 bars:

1. D1 ATR14 percentile is computed from a frozen 252-completed-D1 lookback and must
   be no more than `30.00`;
2. `box_high` and `box_low` are the high and low of completed D1 shifts `1..5`;
3. the five-day average box width divided by the median completed-D1 high-low range
   over shifts `1..20` must be no more than `1.00`.

The context owns a date only when all of the following are true at that completed-H1
decision:

- volatility is `COMPRESSED`;
- canonical direction is `NEUTRAL`;
- canonical phase is not `TRANSITION`;
- shock is false;
- established `UP` and `DOWN` are both false.

Compression may coexist with direction under the canonical contract, so compression
alone is not permission. An established trend is an immediate handoff.

An eligible date logs `R3_CHOP_CONTEXT_DECISION` with stable `context_id`, completed
D1 timestamp, compression features, `episode_id`, and every ownership dimension.
Consecutive eligible D1 dates belong to one compression episode. An ineligible date
or intraday shock/trend/transition handoff ends the episode. After an intraday handoff,
the date is suspended permanently; ownership cannot reactivate until the next D1
context decision.

Initialization records the current completed H1/D1 cursors only. It cannot backfill a
context or event that completed before initialization.

### Repeated completed-H1 boundary event

While the daily context remains active, each newly completed H1 bar with valid frozen
boundary data must register one event. Every H1 evaluation logs
`R3_CHOP_H1_DECISION`; an event registration must join to exactly one prior H1 row
with `action=registered`. The event freezes:

- `setup_time`: the close timestamp of completed H1 shift `1`;
- `boundary_high`: highest high of completed H1 shifts `1..4`;
- `boundary_low`: lowest low of completed H1 shifts `1..4`;
- H1 ATR14 at shift `1`;
- the active compression `episode_id` and context ID.

The just-completed H1 bar is included and no forming H1 value is allowed. Event ID is
`R3CHOP_<setup_time_epoch>`. Only one scalar event may exist. A new H1 event cannot
overwrite an active event.

The implementation must process the active event before registering a newly completed
H1 event at the same timestamp. Thus the fourth M15 decision of the old event is
evaluated and consumed before the next H1 event can be registered.

An open position does not change the alpha event stream. Events continue to register,
and a qualifying first sweep is consumed before the downstream one-position guard.
This exposes, rather than hides, opportunity blocked by the risk layer.

### Four completed-M15 decisions

The window contains the first four newly completed M15 bars whose close timestamps are
strictly later than `setup_time`. It is a completed-bar counter. Weekend, maintenance,
and missing-market gaps consume no decision slots; elapsed seconds are never converted
to H1 or M15 bars.

Every eligible decision logs `R3_CHOP_M15_DECISION` with a unique completed-bar
timestamp and contiguous ordinal `1..4`. The first bar to sweep either frozen boundary
is the event's only attempt:

- lower-side sweep: M15 low is at least `0.05 * M15 ATR14` below `boundary_low`;
- upper-side sweep: M15 high is at least `0.05 * M15 ATR14` above `boundary_high`.

If neither side sweeps, the event remains active until ordinal 4. If ordinal 4 has no
sweep, consume `expired` after evaluating it. If both sides sweep on the same M15 bar,
consume `ambiguous`. No later bar may retry.

The lower-side event qualifies a long only when the same completed M15 bar:

- closes above its open;
- closes at least `0.05 * M15 ATR14` back above `boundary_low`;
- has body/range at least `0.35`;
- has close location at least `0.65`.

The upper-side event is the exact short mirror:

- close below open;
- close at least `0.05 * M15 ATR14` back below `boundary_high`;
- body/range at least `0.35`;
- close location at most `0.35`.

The structural long stop is the sweep low minus `0.10 * M15 ATR14`; the short stop is
the sweep high plus the same buffer. The actual ask/bid entry-to-stop distance must be
positive and no more than `0.75 * frozen H1 ATR14`. Invalid geometry, failed reclaim,
failed candle quality, or an excessive stop consumes `first_sweep_failed`.

On a qualifying bar, copy immutable event fields, consume the event as `entry`, and
only then expose `WOULD_SIGNAL`. Position, cost, router, sizing, risk, claim, and broker
guards run afterward and can never cause the same event to retry.

## Ownership loss and precedence

Ownership is checked before every M15 attempt and before each new H1 registration.
The active event and the entire daily context are terminated immediately as:

1. `shock` if the canonical completed-bar shock rule is true;
2. `trend_handoff` if canonical direction is established `UP` or `DOWN`;
3. `transition_handoff` if the canonical phase is `TRANSITION`;
4. `compression_lost` at the next D1 context decision if completed-D1 compression is
   no longer true.

No entry may execute after one of those handoffs. Mode 28 does not steal release,
transition, or established-trend trades.

## Frozen lifecycle and telemetry

Every registered event has exactly one lifecycle:

1. one preceding owned `R3_CHOP_CONTEXT_DECISION` for the active D1 context;
2. one causal `R3_CHOP_H1_DECISION` with the same event, context, episode,
   H1 timestamp, and setup timestamp;
3. `R3_CHOP_EVENT_REGISTERED`, `IDLE -> WAIT_FIRST_M15_SWEEP`;
4. zero to four `R3_CHOP_M15_DECISION` rows with contiguous completed-bar ordinals;
5. exactly one `R3_CHOP_EVENT_CONSUMED`, `WAIT_FIRST_M15_SWEEP -> IDLE`;
6. at most one `WOULD_SIGNAL`, after consumption.

Allowed terminal outcomes are:

`entry`, `first_sweep_failed`, `ambiguous`, `expired`, `shock`, `trend_handoff`,
`transition_handoff`, `compression_lost`, and `window_end_incomplete`.

`window_end_incomplete` is non-strategy right-censoring. It is allowed only at tester
deinitialization when fewer than four eligible M15 decisions have completed, is audited
separately, carries `deinit=1`, and is limited to at most one event per exact window.
It is not an expiry or alpha failure.

Every lifecycle reason contains:

```text
event_id=<id>|episode_id=<id>|context_id=<id>|setup_time=<epoch>|
setup=COMPRESSED|entry=COMPRESSED|direction_state=NEUTRAL|
shock=0|established=0|transition=0
```

The joined context row contains `owned=1`, `compressed=1`, `d1_time`, `d1_shift=1`,
and `backfill=0`. The joined H1 row and registration contain `h1_bar_time`,
`h1_shift=1`, `backfill=0`, `boundary_lookback=4`, the frozen boundaries, and H1 ATR.
M15 decisions contain
`decision_bar_time` and `m15_bar_ordinal`. Consumption contains `m15_bars_seen`,
`attempt_ordinal` when applicable, and outcome. `WOULD_SIGNAL` contains the attempt
timestamp and ordinal.

Signal prefixes are frozen exactly:

```text
R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_LONG
R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_SHORT
```

The evaluator rejects overwrite, backfill, forming-bar input, duplicate registration,
non-contiguous counters, duplicate consumption, missing consumption, duplicate signal,
signal-before-consumption, execution without one native signal, entry outside the
owned state, broken episode continuity, and reuse of a terminated episode ID.

## Frozen EA identity and tester inputs

The future implementation must append without renumbering:

```text
SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM = 28
REGIME_ROUTER_R3_INSIDE_COMPRESSION_TREND_SHOCK_BLOCK = 6
```

Router 6 is default-off and may authorize only mode 28. It must fail closed on shock,
established `UP`/`DOWN`, transition, non-compression, unknown, or ambiguous state.

The one frozen tester cell uses:

```text
InpSignalMode=28
InpRegimeRouterMode=6
InpDirectionMode=0
InpRiskReward=2.00
InpMaxSpreadPoints=75
InpMaxEstimatedCostR=0.10

InpR3ChopD1AtrPeriod=14
InpR3ChopD1AtrPercentileLookback=252
InpR3ChopD1AtrPercentileMax=30.00
InpR3ChopD1BoxDays=5
InpR3ChopD1RangeMedianLookback=20
InpR3ChopD1RangeMedianMax=1.00
InpR3ChopH1BoundaryLookback=4
InpR3ChopEventWindowM15Bars=4
InpR3ChopSweepM15Atr=0.05
InpR3ChopReclaimM15Atr=0.05
InpR3ChopMinBodyFraction=0.35
InpR3ChopLongCloseLocationMin=0.65
InpR3ChopShortCloseLocationMax=0.35
InpR3ChopStopBufferM15Atr=0.10
InpR3ChopMaxStopH1Atr=0.75
InpR3ChopConsumeFirstSweep=true

InpMinAtrAbsoluteForEntry=0.00
InpStopFloorPoints=0
InpStopCeilingPoints=0
InpStopCapPoints=0
InpUseRiskNormalizedLots=true
InpRiskAmountUsd=50.00
InpMaxRiskLots=0.10
InpRejectRiskOvershootEnabled=true
InpMaxRiskOvershootPct=0.00
InpOnePositionPerMagic=true
InpMaxOpenPositionsPerMagic=1
InpMaxTradesPerDay=0
InpCooldownMinutes=0
```

All calendar/session strings are empty; directional-session filtering is false. All
previous-day/week/month PnL governors, feature-loss filters, supportive-state guards,
partial/split entries, profit protection, and early-adverse exits are false. H1/H4
legacy trend-entry filters are false because native ownership is enforced by mode 28.

The runner's full `FROZEN_INPUTS` dictionary and SHA256 are authoritative. Both eras
use the identical dictionary. Frozen tester-input SHA256:
`bb8f93fc783b0c08f6a08340310f3197fd9402f1556ccbdb2c890adb95ea47b3`.

## Hard risk and execution contract

- Tester deposit and currency: `$10,000 USD`.
- Initial risk request: `$50.00` (`0.50%`) per position.
- Target: fixed `2.00R` from normalized entry and stop.
- One position per magic, maximum one; no stacking.
- No absolute stop floor, ceiling, or cap.
- No daily trade cap or cooldown.
- No calendar, session, or previous-PnL mask.

Mode 28 must use a direction-aware, fail-closed `OrderCalcProfit` calculation after
lot normalization and price normalization. Long uses `ORDER_TYPE_BUY`; short uses
`ORDER_TYPE_SELL`. Account currency must be USD. Missing, failed, zero, negative, or
greater-than-`$50.0000001` calculated loss blocks the order. Broker minimum-lot
overshoot is never permitted. Every `ORDER_SEND_OK` row logs positive
`actual_risk_usd <= 50.0000001`.

The event remains consumed on position, cost, spread, risk, order-send, or broker
failure. Every send failure must retain timestamp, retcode, and description.

## Frozen exact eras and costs

Both cells use XAUUSD M5 Strategy Tester with mode-28 decisions on completed H1/M15
bars, every-tick modeling, `$10,000 USD`, and the identical frozen inputs:

| Window | From | To | Pre-recent cutoff |
| --- | --- | --- | --- |
| `prehistory_201601_202112` | `2016.01.01` | `2021.12.31` | `2021.06.30` |
| `primary_202207_202606` | `2022.07.01` | `2026.06.30` | `2025.12.31` |

Stress subtracts `$0.30` per executed ticket from normalized PnL. Raw HTML, tester
configuration, signal, event, context, order, deal, normalized trade, overlap, risk,
and equity-drawdown artifacts are mandatory.

## Frozen controls and independence

All available controls named in the runner are mandatory. Missing files fail closed.
Same-direction entry overlap uses the existing five-minute exact matching rule and
must remain strictly below `20%` for every control.

Prehistory controls are clean R1 and corrected-counter killed mode 25. Primary adds the
killed raw-H4 R3 release and the closest killed R4 M5 failed-break family. The
nonconforming mode-24 ledgers are explicitly forbidden as overlap evidence because
their wall-clock M15 lifetime did not satisfy their completed-bar contract. Path
existence alone is insufficient: the runner's `CONTROL_PROVENANCE` must mark every
control ready or availability fails closed. The overlap gate is diagnostic independence
evidence; none of the killed controls is an admitted portfolio component.

## Per-window admission gates

Every era must independently pass:

- at least `100` executed trades, including at least `25` long and `25` short;
- long and short stressed net each positive;
- at least three traded owned episodes, three exposure years, and three profitable
  years;
- WR `>=50%`, realized W/L `>=2.00`, PF `>=2.00`, stress PF `>=1.75`, stressed net
  positive, and pre-recent net positive;
- top-ten-winners-removed and top-three-entry-days-removed net positive;
- best-month share `<=30%` and maximum positive compression-episode share `<=50%`;
- `100%` native setup and executed-entry purity;
- every required overlap control available and overlap strictly below `20%`;
- zero future-bar, retrospective-entry, overwrite, duplicate-consumption, lifecycle,
  counter, or right-censor-count violation;
- successful sends = MT5 trades = normalized trades; zero unexplained send failures,
  open-at-end positions, forbidden guard blocks, or missing risk calculations;
- maximum executed initial risk `<= $50.0000001`;
- MT5 balance and equity DD relative each `<=20%`;
- net/maximal-equity-DD `>=2.00`;
- maximal-equity-DD/closed-ledger-DD `<=2.00`.

## Global gates and decision

The combined two-era ledger must also have at least `200` trades, at least `50` per
direction, positive stressed net in each direction, WR `>=50%`, W/L `>=2.00`, PF
`>=2.00`, stress PF `>=1.75`, positive stressed net, three exposure/profitable years,
positive top-ten/top-three removal nets, best-month share `<=30%`, episode share
`<=50%`, and zero missing episode IDs.

Global DD/purity means both exact windows must pass every native-state, execution-risk,
overlap, balance-DD, equity-DD, net/equity-DD, and equity/closed-DD gate. A recent-era
pass cannot cover prehistory.

Decision classes are frozen:

- any static, alpha, robustness, ownership, purity, overlap, lifecycle, counter, or
  execution failure: `R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_REJECT`;
- all non-DD gates pass but a DD/capital-efficiency gate fails:
  `R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_ALPHA_ONLY_RISK_REPAIR_REQUIRED`;
- every gate passes: `R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_FULLY_QUALIFIED`.

A rejection freezes mode 28. It does not authorize a lookback, sweep, reclaim, candle,
stop, event-window, direction, cost, or ownership sibling.
