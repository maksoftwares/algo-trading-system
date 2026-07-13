# A1 XAU R2 M15-Impulse / M5-Continuation Short V1 Preregistration

Date: `2026-07-10`

Status: `PREREGISTERED_RUNNER_LOCKED_NOT_IMPLEMENTED_NOT_RUN`

## Purpose

Test one genuinely different, higher-frequency R2 source for repeated continuation
cycles inside mature native XAUUSD downtrends. The candidate is not a pivot, retest,
window, stop, cost, or calendar sibling of modes 22 or 24.

Mode 24 reported the following signal-starvation shape:

| Frozen window | Leg-one setups | Confirmed pivots | First second-break attempts | Would-signals | Executions |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2016-2021 | 120 | 40 | 25 | 3 | 0 |
| 2022-2026 | 82 | 28 | 15 | 5 | 2 |

Its dominant reported consumption outcome was continuation before a reset: `66/120` setups
(`55.0%`) in prehistory and `50/82` (`61.0%`) in primary. Of the few surviving
signals, prehistory lost two to the structural-stop cap and one to cost; primary lost
three to the stop cap. The two primary executions both lost. A later exactness audit
proved that mode 24 used a wall-clock M15 lifetime where its contract required
completed-M15 counters. Its counts remain diagnosis only; they are not conforming
lifecycle or overlap evidence and no claim that its causality audit was clean survives.

This family tests the opposite microstructure hypothesis: a mature downtrend often
continues directly after a completed M15 displacement. Each qualifying M15 impulse
may authorize exactly one first M5 continuation attempt. A new impulse later in the
same mature-DOWN episode may create a new independent event after the prior event is
consumed or expires.

## Runtime Boundary

This turn authorizes only this preregistration, a complete but fail-closed exact runner
and evaluator, and focused tests. It does **not** authorize an EA edit, compilation,
historical execution, demo/live attachment, chart, preset, profile, account, order,
position, registry, or broker-state change.

The runner must keep `HISTORICAL_RUN_AUTHORIZED = False`. A later implementation and
review must explicitly unlock it.

## Frozen Identity and Ownership

- Source: `r2_m15_impulse_m5_continuation_short_v1`
- Variant: `r2_icr_m15_impulse_m5_first_continuation_v1`
- Reserved appended signal mode:
  `SIGNAL_R2_M15_IMPULSE_M5_CONTINUATION_SHORT = 27`
- Direction: short only
- Setup and entry owner: direction `DOWN`, phase `ESTABLISHED`, volatility not
  `SHOCK`, compatibility label `downtrend`
- Mature ownership: strict R2 predicate on completed D1 shifts 1, 2, and 3 plus
  completed-H4 down confirmation
- Exactly one parameter cell; no threshold grid or sibling
- One same-magic position maximum

Modes 25 and 26 are reserved elsewhere. Mode 27 must be appended without renumbering
or altering modes 0 through 26 or router modes 0 through 5.

## Structural Independence

This family is different by event definition, not by a looser threshold:

- Mode 22 waited around a prior-completed-D1 low. Mode 27 uses no prior-D1 level.
- Mode 24 required H1 leg one, the first confirmed two-sided M15 pivot, and a later
  second break. Mode 27 has no H1 leg, pivot, lower-high, or reset state.
- Legacy modes 15 and 19 are M5 breakdown/retest candidates. Mode 27 registers a
  completed M15 structural impulse, then consumes exactly one later M5 continuation
  attempt under mature three-D1 ownership.
- No hour, session, weekday, month, previous-PnL, loss-streak, absolute-ATR, or
  post-result mask is used.
- The deterministic holding horizon is part of the event hypothesis and is frozen
  before any mode-27 result; it is not a repair selected from mode-24 trades.

Same-direction entry overlap within 15 minutes must be measured against the five
counter-compliant R2 pullback/continuation controls frozen in the runner. The
nonconforming mode-22 prior-D1-low and mode-24 ledgers are forbidden as overlap
evidence. Path existence alone is insufficient: `CONTROL_PROVENANCE` must mark a
control ready. Missing or non-ready required evidence fails closed.

After later implementation and explicit authorization, the runner must preflight every
required control before launching either MT5 window. A missing/non-ready control stops
the run rather than spending history and merely failing the report afterward.

## Completed-Bar Event Contract

All regime, signal, stop, and exit decisions use completed bars. Bar 0 is forbidden.

### 1. Mature-DOWN ownership

At both M15 impulse registration and M5 entry authorization require:

1. canonical direction `DOWN`;
2. canonical phase `ESTABLISHED`;
3. canonical volatility not `SHOCK`;
4. compatibility label `downtrend`;
5. the strict R2 D1 stack on each of completed D1 shifts 1 through 3; and
6. completed-H4 down confirmation.

A transition into DOWN is not owned. Ownership loss consumes an unentered event and
blocks entry.

### 2. Register one completed-M15 impulse

On each newly completed M15 bar, when no impulse event is active, register an event
only when the bar:

- is bearish;
- closes strictly below the lowest low of the preceding eight completed M15 bars,
  excluding the impulse bar;
- has range at least `0.75 * M15 ATR(14)`;
- has body/range at least `0.50`; and
- closes in the bottom `0.30` of its range.

Freeze the impulse bar-open time, impulse close time/event ID, high, low, close, ATR,
and complete ownership telemetry. Registration must log `impulse_bar_time`,
`impulse_time=impulse_bar_time+900`, `m15_shift=1`, and `backfill=0`; event ID is
`R2ICR_<impulse_time>`. Initialization records the current completed-M15 cursor and may
not backfill an already completed impulse. Registered impulse times must be strictly
increasing.

Only one scalar impulse event may be active. A newer M15 bar cannot overwrite it. The
entry window is exactly the next three completed M5 bars; therefore an old event is
consumed or expired before the next M15 impulse can be considered.

The entry lifetime is a completed-bar counter, never a wall-clock duration. Initialize
`entry_m5_bars_seen=0` when the impulse is registered. On each distinct newly completed
M5 decision bar strictly after the impulse, increment it exactly once and assign
`entry_bar_ordinal=1,2,3`. Missing bars, market closures, maintenance gaps, and time
between ticks do not increment the counter. Evaluate the bar at each ordinal; if the
third bar has no attempt, consume `entry_window_expired` on that third decision, not on
a later fourth bar. Implementations based on `impulse_time + N * PeriodSeconds(...)`,
elapsed seconds, or nominal minute arithmetic are forbidden.

Each `R2_ICR_ENTRY_DECISION` must log `touch=0|1` and `owned=0|1`. For a
`first_break_attempt`, every earlier decision has `touch=0`, the consumed decision has
`touch=1`, and all observed decisions have `owned=1`. An expiry has three `touch=0`,
`owned=1` decisions. `ownership_lost` is allowed only when its last decision has
`owned=0`, all earlier decisions have `owned=1`, and no decision touched the impulse.

### 3. Consume the first M5 continuation attempt

Within those three completed M5 bars, the first bar whose low is at or below
`impulse_low + 0.05 * M5 ATR(14)` is the only attempt. Consume the event immediately,
before candle quality, stop, cost, position, risk, claim, or broker guards. Native
ownership is evaluated first for the decision itself: an unowned decision consumes
`ownership_lost` and can never become a first-break attempt.

The consumed attempt becomes a short signal only if it:

- is bearish;
- closes at least `0.05 * M5 ATR(14)` below the frozen impulse low;
- has body/range at least `0.45`; and
- closes in the bottom `0.30` of its range.

A failed first attempt is consumed with no retry. An event with no attempt in three
M5 bars expires. Once consumed or expired, a later completed M15 impulse may register
a new event even in the same mature-DOWN episode.

### 4. Stop, target, and structural holding horizon

- Entry follows the existing market-style path after the qualifying completed M5 bar.
- Stop is `impulse_high + 0.10 * M15 ATR(14)`.
- Block if entry-to-stop distance exceeds `1.50 * M15 ATR(14)`.
- Initial target remains fixed at `2.00R`.
- If neither stop nor target has closed the position after 12 subsequently completed
  M5 bars, close at market on the twelfth completed-bar evaluation with
  `r2_icr_structural_time_exit`.
- If mature-DOWN ownership is lost while the position remains open, close on the next
  completed-M5 evaluation with `r2_icr_ownership_exit`.
- Time and ownership exits are deterministic structural exits, not trailing,
  breakeven, partial-close, profit-lock, or outcome-adaptive management.

The realized average-win/loss gate remains `>= 2.00`; early exits do not relax it.

The holding horizon is also a completed-bar counter, not elapsed time. Initialize
`hold_m5_bars_seen=0` only after the position is confirmed open. Increment once for
each distinct completed M5 decision bar whose close follows entry, and close an open
position when ordinal 12 is processed. A weekend-spanning position with two newly
completed post-entry M5 bars has held two bars, regardless of elapsed wall time. No
mode-27 expiry or holding decision may use `entry_time + N * PeriodSeconds(...)`,
`TimeCurrent() - entry_time`, or division of elapsed seconds by 300.

Every `R2_ICR_HOLD_DECISION` carries the immutable `entry_time`, `position_id`, and
ticket, plus `position_open=1`, `owned=0|1`, decision time, and ordinal. Decision times
must be strictly increasing and later than entry. An `owned=0` decision must have one
same-decision `ownership_exit`. Ordinal 12 must have one same-decision close attempt.
Every `R2_ICR_POSITION_EXIT` must join to exactly one hold decision by event, entry,
position, ticket, decision time, and ordinal; log `close_attempted=1` and
`close_succeeded=1`; and reconcile by broker timestamp to the normalized MT5 exit.

## Frozen Tester Inputs

| Input | Value |
| --- | ---: |
| `InpSignalMode` | `27` |
| `InpRegimeRouterMode` | `2` |
| `InpDirectionMode` | `2` |
| `InpRiskReward` | `2.00` |
| `InpR2IcrAtrPeriod` | `14` |
| `InpR2IcrMaturityD1Bars` | `3` |
| `InpR2IcrImpulseLookbackM15Bars` | `8` |
| `InpR2IcrImpulseMinRangeM15Atr` | `0.75` |
| `InpR2IcrImpulseMinBodyFraction` | `0.50` |
| `InpR2IcrImpulseCloseLocationMax` | `0.30` |
| `InpR2IcrEntryWindowM5Bars` | `3` |
| `InpR2IcrFirstBreakTouchM5Atr` | `0.05` |
| `InpR2IcrFirstBreakCloseM5Atr` | `0.05` |
| `InpR2IcrResumeMinBodyFraction` | `0.45` |
| `InpR2IcrResumeCloseLocationMax` | `0.30` |
| `InpR2IcrStopBufferM15Atr` | `0.10` |
| `InpR2IcrMaxStopM15Atr` | `1.50` |
| `InpR2IcrMaxHoldM5Bars` | `12` |
| `InpR2IcrExitOnOwnershipLoss` | `true` |
| `InpR2IcrConsumeFirstBreak` | `true` |
| `InpMinAtrAbsoluteForEntry` | `0.00` |
| `InpStopFloorPoints` / `InpStopCeilingPoints` / `InpStopCapPoints` | `0` |
| `InpMaxEstimatedCostR` | `0.10` |
| `InpUseRiskNormalizedLots` | `true` |
| `InpRiskAmountUsd` | `50.00` |
| `InpMaxRiskLots` | `0.10` |
| `InpRejectRiskOvershootEnabled` | `true` |
| `InpMaxRiskOvershootPct` | `0.00` |
| `InpOnePositionPerMagic` | `true` |
| `InpMaxOpenPositionsPerMagic` | `1` |
| `InpMaxTradesPerDay` / `InpCooldownMinutes` | `0` |
| all hour/day CSV masks | empty |
| directional session filter | disabled; full day |
| all previous-PnL and portfolio-daily governors | disabled |
| generic profit protection / early-adverse exit / partial / split entry | disabled |
| mode-specific lifecycle/ownership telemetry | enabled |

## Hard Risk Contract

Tester deposit is `$10,000 USD`. Maximum initial stop risk is `$50.00` (`0.50%`) per
executed position.

After broker volume-step normalization and before signal claim or order send, calculate
entry-to-stop loss with `OrderCalcProfit(ORDER_TYPE_SELL, ...)`. Block if account
currency is not USD, calculation fails, the value is missing/non-finite/non-positive,
the frozen risk inputs are not exactly `$50/0%`, or calculated loss exceeds `$50.00`.
A broker minimum lot that exceeds the cap is blocked. Every successful mode-27 order
row must persist machine-readable `actual_risk_usd`; missing values fail the evaluator.

## Frozen Exact Windows

Run the identical one-cell candidate in separate isolated tester runs:

1. `prehistory_201601_202112`: `2016.01.01 -> 2021.12.31`
2. `primary_202207_202606`: `2022.07.01 -> 2026.06.30`

Both are exams. Neither may alter the other. Pre-recent net is measured through
`2021.06.30` and `2025.12.31`, respectively.

## Required Lifecycle and Position Telemetry

The future EA must emit stable pipe-delimited reason fields with event ID and epoch
timestamps:

- `R2_ICR_D1_OWNERSHIP`: one row per newly completed D1 ownership observation;
- `R2_ICR_IMPULSE_REGISTERED`: exactly once per impulse event;
- `R2_ICR_ENTRY_DECISION`: exactly once for each newly completed M5 bar observed by
  an active event, with `decision_bar_time` and contiguous `entry_bar_ordinal`;
- `R2_ICR_EVENT_CONSUMED`: exactly once per event, with outcome;
- accepted reason prefix
  `R2_M15_IMPULSE_M5_CONTINUATION_SHORT_STATE_downtrend`;
- `R2_ICR_POSITION_EXIT`: structural time/ownership exit, event ID, position/ticket,
  entry time, exit decision time, `hold_bar_ordinal`, and outcome; and
- `R2_ICR_HOLD_DECISION`: exactly once for each distinct completed M5 bar observed
  while the position remains open, with `decision_bar_time` and contiguous
  `hold_bar_ordinal`.

Every event reason must include `event_id`, `setup_time`, `from`, `to`, `outcome`,
`setup=DOWN`, `phase=ESTABLISHED`, `shock=0`, `maturity=3`, and `impulse_time`; an
accepted attempt must also include its completed-M5 `attempt_time` and
`attempt_ordinal`. Every consumption includes `entry_bars_seen`; a first-break attempt
has ordinal 1 through 3, and `entry_window_expired` has exactly three observed entry
bars. The evaluator must derive overwrite, duplicate-consumption, contiguous bar
counters, future-bar, retrospective-entry, event-to-trade, holding-horizon, and
ownership-purity checks from real logs rather than constants or elapsed timestamps.

Each ownership observation logs `d1_time`, `d1_shift=1`, `backfill=0`, the completed
timestamps `d1_shift1_time > d1_shift2_time > d1_shift3_time`, completed `h4_time`,
`mature=0|1`, canonical direction/state, phase, shock, maturity, and completed-H4
confirmation. A registration must join the latest preceding mature downtrend ownership
observation, and that observation's H4 timestamp must precede setup; registration
fields cannot self-assert ownership.

Allowed event-consumption outcomes are `first_break_attempt`, `entry_window_expired`,
`ownership_lost`, and `tester_deinit`.

`tester_deinit` is non-strategy right-censoring, not an expiry. It requires `deinit=1`,
fewer than three observed entry decisions, no touch, and retained ownership on every
observed decision. It is audited separately and limited to at most one active scalar
event per exact window.

## Global Standalone Gates

Each exact window independently must pass:

### Alpha and breadth

- executed trades `>= 100`;
- at least three owned-regime episodes;
- exposure in at least three calendar years and at least three profitable years;
- WR `>= 50.00%`;
- realized average win/loss `>= 2.00`;
- PF `>= 2.00`;
- stress PF after `-$0.30/ticket >= 1.75` and stress net `> 0`;
- pre-recent net `> 0`.

### Robustness and concentration

- top-ten-winners-removed net `> 0`;
- top-three-entry-days-removed net `> 0`;
- best-month share `<= 30%`;
- no owned-regime episode contributes more than `50%` of positive episode net.

### Ownership, lifecycle, and independence

- `100%` mature, established, non-shock native-R2 setup purity;
- `100%` mature, established, non-shock native-R2 entry purity;
- owned-state net `> 0`;
- zero backfill, future-bar, retrospective-entry, active-event-overwrite,
  duplicate-consumption, or multi-signal-per-event violations;
- exactly one consumption per registered impulse, including tester-end cleanup;
- at most one truthful `tester_deinit` right-censored event per exact window;
- every mode-specific time/ownership exit matches an executed event/position;
- no position exceeds the 12-completed-M5 holding contract without a logged close
  attempt;
- same-direction entry overlap within 15 minutes is strictly below `20%` for every
  required control; missing control evidence fails closed.

### Execution and risk

- successful-order, MT5-trade, and normalized-ledger counts reconcile;
- zero unexplained order-send failures and zero open-at-end positions;
- zero forbidden calendar/session/previous-PnL guard blocks;
- zero missing initial-risk calculations;
- every executed position has `actual_risk_usd <= 50.00`.

### Drawdown and capital efficiency

- MT5 balance drawdown relative `<= 20%`;
- MT5 equity drawdown relative `<= 20%`;
- net / maximal MT5 equity drawdown `>= 2.00`;
- maximal MT5 equity drawdown `<= 2.0x` closed-ledger drawdown.

Missing fields fail closed.

## Decision and Kill Discipline

- Any alpha, breadth, ownership, lifecycle, independence, concentration, execution,
  holding, or risk failure: `R2_ICR_M15_M5_CONTINUATION_REJECT`.
- Both windows pass all non-DD gates but a DD gate fails:
  `R2_ICR_M15_M5_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED`.
- Both windows pass every gate: `R2_ICR_M15_M5_CONTINUATION_FULLY_QUALIFIED`.

A rejection freezes mode 27. It does not authorize alternate lookbacks, body/location
thresholds, entry windows, stop buffers, holding horizons, session masks, or combining
it with another rejected R2 source.
