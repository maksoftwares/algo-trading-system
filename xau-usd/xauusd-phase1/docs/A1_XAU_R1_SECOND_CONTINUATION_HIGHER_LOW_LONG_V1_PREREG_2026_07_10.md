# A1 XAU R1 Second-Continuation Higher-Low Long V1 Preregistration

Date: `2026-07-10`

Status: `PREREGISTERED_COMPLETE_FAIL_CLOSED_RUNNER_MODE26_NOT_IMPLEMENTED_NOT_RUN`

## Purpose

Test one genuinely new, materially higher-frequency R1 owner for mature native
XAUUSD uptrends after the prior-D1-high first-retest family was killed. This is the
directional structural counterpart of the preregistered mature-R2 lower-high
second-continuation design. Its parameters are mirrored before any result is seen.

The hypothesis is that after an established uptrend produces one completed-H1 upside
displacement, the first meaningful M15 pullback pivot should remain a higher low. The
specialist acts only on the first later attempt to accept above the first leg's high.
It therefore owns a repeated *second continuation* within a mature trend, not the
transition into R1, a prior-day breakout, a D1 box expansion, or a generic EMA touch.

A literal lower-low pullback is not used: it would break the mature-uptrend geometry
and turn this into a failed-break/reclaim family adjacent to killed mode 23. The
directional counterpart to an R2 lower high is an R1 higher low.

## Pre-Implementation Administrative Renumbering

This scaffold was initially assigned proposed mode 25 while it was being drafted.
Before any EA implementation, compile, historical run, or result, R3 was refrozen as
the append-only owner of mode 25:
`SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK = 25`.

This R1 scaffold is therefore administratively renumbered from proposed mode 25 to
proposed mode 26. Only `InpSignalMode`, the append-only enum/token expectation, and
the resulting frozen-input hash change. Signal geometry, thresholds, ownership,
windows, gates, and decision discipline are unchanged. There is no mode-25 R1 result
and no result-conditioned selection behind this change.

## Mode-23 Exact Failure and Attrition Diagnosis

The exact mode-23 signal and order CSVs were read directly. Counts below are observed
logged outcomes, not estimates from the final trade ledger.

| Window | M15 decisions | Generic no-candidate | Observed setup outcomes | Expired | First-touch rejected | Invalidated | `WOULD_SIGNAL` | Executed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016-2021 | 141,048 | 140,940 (99.92%) | 108 | 69 (63.89%) | 35 (32.41%) | 2 (1.85%) | 2 (1.85%) | 0 |
| 2022-2026 | 94,223 | 94,096 (99.87%) | 127 | 97 (76.38%) | 24 (18.90%) | 4 (3.15%) | 2 (1.57%) | 1 |

Additional exact findings:

- In prehistory, both would-signals were blocked by cost: `0.2254R` and `0.2392R`
  versus the frozen `0.10R` cap.
- In primary, one signal executed on `2024-10-22` and lost `$31.60`; the other was
  blocked because its stop was `1.06 * H1 ATR`, above the frozen `1.00` cap.
- Of the 35 prehistory first-touch rejects, 30 failed at least one visible candle-form
  condition; 20 were not bullish, 15 had body/range below `0.50`, and 25 closed below
  the top quartile. The counts overlap.
- Of the 24 primary rejects, 20 failed at least one visible candle-form condition; 12
  were not bullish, 11 had body/range below `0.50`, and 16 closed below the top
  quartile. The counts overlap.
- Five prehistory and four primary rejects passed the visible direction/body/location
  checks. The rejection rows do not retain the frozen anchor, so reclaim-distance-only
  attrition cannot be separated exactly from those CSVs.
- The logs do not emit every H1 arm, and scalar state can supersede an earlier arm, so
  the 108/127 observed outcomes are a lower bound on accepted H1 events. They are the
  exact observable terminal outcomes.

The failure is therefore primarily signal incidence and event conversion, not order
execution. Changing the cost cap, stop cap, retest distance, or candle thresholds
could produce at most two pre-guard candidates per window from this evidence. Mode 23
is frozen rejected; this preregistration is not a repair or relaxation of it.

## Runtime Boundary

This turn authorizes only this preregistration, a complete fail-closed exact
runner/evaluator, and evaluator tests. Completing the evaluator changes no frozen
signal geometry or tester input. It does **not** authorize an EA edit, compile,
exact-history launch, demo/live attachment, chart, preset, profile, account, order,
position, registry, or broker-state change.

Historical execution remains locked until a later review confirms the state-machine
implementation and explicitly changes `HISTORICAL_RUN_AUTHORIZED` from `False`.

## Frozen Identity and Ownership

- Source: `r1_second_continuation_higher_low_long_v1`
- Variant: `r1_hlf_second_continuation_structural_v1`
- Proposed appended signal mode:
  `SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG = 26`
- Direction: long only
- Setup and accepted-entry owner: canonical direction `UP`, phase `ESTABLISHED`,
  volatility other than `SHOCK`
- Compatibility label at setup and entry: `uptrend`
- Exactly one parameter cell; no grid, sensitivity sibling, or directional sibling
- One same-magic position maximum; no event stacking

Mode 23 remains reserved by the killed R1 prior-D1-high family, mode 24 by the
mature-R2 lower-high scaffold, and mode 25 by the refrozen R3 compression-acceptance
first-pullback family. A future implementation must append mode 26 without renumbering
modes 0 through 25.

## Why This Is a New Family and More Frequent by Construction

- It does not use a prior-D1 high or first retest, so it is not mode 23.
- It does not use D1 compression, a multi-day box, or H4 expansion, so it is not the
  rejected box/long-expansion family or R3.
- It does not use H1 EMA20/EMA50 touches or any hour window, so it is not the
  session-masked H1-pullback family.
- It does not use an absolute ATR floor, calendar mask, previous-PnL state, or
  outcome-derived threshold.
- It requires a causal multi-event sequence: a rolling-H1 leg one, the first confirmed
  M15 higher low, and the first M15 second-break attempt.
- A rolling 12-H1 displacement can recur within one mature R1 episode; it is not
  limited to a new prior-day structural high. Its reset and second-break windows total
  up to 32 M15 bars rather than mode 23's eight-bar retest window.

The exact admission gate remains at least 100 executed trades in **each** window.
Higher frequency is a falsifiable requirement, not a reason to weaken alpha or risk
gates. Entry overlap within 15 minutes must be strictly below 20% against every
required available R1/R3 control.

## Completed-Bar State Machine

All regime, setup, pivot, signal, stop, and invalidation inputs use completed bars.
Bar 0 is forbidden. State is keyed by the completed-H1 leg-one close time.

### State 0: `IDLE`

At each newly completed H1 bar, arm leg one only if all conditions hold:

1. The canonical regime at the H1 close is direction `UP`, phase `ESTABLISHED`,
   volatility not `SHOCK`, compatibility label `uptrend`.
2. The strict R1 completed-D1 predicate is true for each of D1 shifts 1, 2, and 3,
   and completed-H4 confirmation is still up. This makes the state mature; a new
   transition cannot be relabeled as R1.
3. The H1 bar is bullish.
4. Its close is at least `0.10 * H1 ATR(14)` above the highest high of the preceding
   12 completed H1 bars, excluding the leg-one bar.
5. Its range is at least `1.00 * H1 ATR(14)`.
6. Its body/range is at least `0.50`.
7. Its close is in the top `0.25` of its range.

Freeze `leg_one_high`, `leg_one_close`, the lowest low of the preceding 12 H1 bars as
`origin_low`, completed `leg_one_h1_atr`, canonical setup dimensions/timestamps, and a
unique setup ID from the leg-one close time. Transition to `WAIT_FIRST_PIVOT`.

While any state is active, newer leg-one candidates are ignored. They cannot overwrite
or stack the event.

### State 1: `WAIT_FIRST_PIVOT`

Observe at most the next 16 completed M15 bars after leg one.

The first causally confirmed pivot low is the first pivot bar whose low is strictly
lower than the lows of its two completed bars on the left and two completed bars on
the right. At confirmation, the pivot and all four comparison bars are completed.
The first chronological confirmed pivot is consumed even when it fails the conditions
below; the code may not wait for a prettier pivot.

The first pivot qualifies as the higher-low reset only if:

- `leg_one_close - pivot_low >= 0.35 * leg_one_h1_atr`; and
- `pivot_low >= origin_low + 0.10 * leg_one_h1_atr`.

Before a qualifying pivot is confirmed, consume without a trade if:

- any completed M15 close is above
  `leg_one_high + 0.10 * M15 ATR(14)` (`continuation_without_reset`);
- any completed M15 close is below `origin_low`;
- the regime is no longer established, non-shock `UP`; or
- the 16-bar window expires.

An invalid first pivot emits `r1_hlf_first_pivot_rejected` and consumes the setup.
There is no later-pivot retry.

### State 2: `HIGHER_LOW_CONFIRMED`

The pivot is known only after its two right-side M15 bars have closed. If either of
those already-completed confirmation bars touched `leg_one_high`, consume as
`r1_hlf_second_break_before_arm`; never enter retrospectively.

Otherwise, observe at most the next 16 completed M15 bars. Consume and invalidate if
the regime leaves established, non-shock `UP`, or if a completed M15 close is below
`pivot_low - 0.10 * leg_one_h1_atr`.

The first completed M15 bar whose high is at or above
`leg_one_high - 0.10 * M15 ATR(14)` is the only second-break attempt. Consume it
immediately, before checking candle quality or any later execution guard.

That consumed bar becomes a long signal only if it:

- is bullish;
- closes at least `0.10 * M15 ATR(14)` above `leg_one_high`;
- has body/range at least `0.50`; and
- closes in the top `0.25` of its range.

A nonqualifying first attempt emits `r1_hlf_first_second_break_rejected`. There is no
retry from the same leg-one event.

### Stop, Target, and Final Consumption

- Stop is `pivot_low - 0.20 * M15 ATR(14)`.
- Block if entry-to-stop distance exceeds `1.00 * leg_one_h1_atr`, with reason
  `r1_hlf_stop_h1_atr_exceeded`.
- Target is fixed at `2.00R`.
- The strict canonical R1 owner is checked again immediately before authorization.
  A regime change consumes and blocks; it is not reassigned to transition or R3.
- A qualifying attempt is already consumed if cost, position, risk, or broker guards
  later block it.

## Frozen Tester Inputs

| Input | Value |
| --- | ---: |
| `InpSignalMode` | `26` |
| `InpRegimeRouterMode` | `1` |
| `InpDirectionMode` | `1` |
| `InpRiskReward` | `2.00` |
| `InpR1HlfAtrPeriod` | `14` |
| `InpR1HlfMaturityD1Bars` | `3` |
| `InpR1HlfLeg1LookbackH1Bars` | `12` |
| `InpR1HlfLeg1BreakMarginH1Atr` | `0.10` |
| `InpR1HlfLeg1MinRangeH1Atr` | `1.00` |
| `InpR1HlfLeg1MinBodyFraction` | `0.50` |
| `InpR1HlfLeg1CloseLocationMin` | `0.75` |
| `InpR1HlfResetWindowM15Bars` | `16` |
| `InpR1HlfPivotLeftBars` | `2` |
| `InpR1HlfPivotRightBars` | `2` |
| `InpR1HlfResetMinDepthH1Atr` | `0.35` |
| `InpR1HlfHigherLowMarginH1Atr` | `0.10` |
| `InpR1HlfSecondBreakWindowM15Bars` | `16` |
| `InpR1HlfSecondTouchM15Atr` | `0.10` |
| `InpR1HlfSecondCloseM15Atr` | `0.10` |
| `InpR1HlfSecondMinBodyFraction` | `0.50` |
| `InpR1HlfSecondCloseLocationMin` | `0.75` |
| `InpR1HlfInvalidBreakdownH1Atr` | `0.10` |
| `InpR1HlfStopBufferM15Atr` | `0.20` |
| `InpR1HlfMaxStopH1Atr` | `1.00` |
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
| profit protection / early exit / partial / split entry | disabled |

## Hard Risk Contract

Tester deposit is `$10,000 USD`; intended and maximum initial stop risk is `$50.00`
(`0.50%`) per executed position.

After broker volume-step normalization and before claiming or sending an order, the
future implementation must calculate normalized entry-to-stop loss using
`OrderCalcProfit(ORDER_TYPE_BUY, ...)`. If it fails, is non-finite, or absolute loss
exceeds `$50.00`, block with `risk_amount_overshoot`. A broker minimum lot that risks
more than `$50.00` is blocked. The overshoot percentage is zero.

Every attempted and executed entry must log intended/calculated risk, lots, entry,
stop, tick metadata, and reason. Every executed trade must reconcile to calculated
initial risk `<= $50.00`.

## Frozen Exact Windows and Frequency Gate

Run the identical one-cell candidate in a fresh isolated tester process for each:

1. `prehistory_201601_202112`: `2016.01.01 -> 2021.12.31`
2. `primary_202207_202606`: `2022.07.01 -> 2026.06.30`

Both are frozen exams. The pre-recent bucket ends `2021.06.30` in prehistory and
`2025.12.31` in primary; each must have positive net. Any window with fewer than 100
executed trades rejects the family without threshold repair.

## Owned-Regime Episodes

An episode is a maximal causal run of completed D1 bars satisfying the strict mature
R1 predicate, separated by at least one completed D1 bar that does not satisfy it.
Assign a trade to the episode containing its leg-one setup timestamp.

## Global Standalone Gates

Each exact window must independently pass every gate:

### Alpha and sample

- executed trades `>= 100`;
- owned-regime episodes `>= 3`;
- exposure in at least three calendar years and at least three profitable years;
- WR `>= 50.00%`;
- realized average win/loss `>= 2.00`;
- PF `>= 2.00`;
- stress PF after `-$0.30/ticket >= 1.75` and stress net `> 0`;
- frozen pre-recent net `> 0`.

### Robustness and concentration

- top-ten-winners-removed net `> 0`;
- top-three-entry-days-removed net `> 0`;
- best-month share `<= 30%` of positive net;
- no owned-regime episode contributes more than `50%` of positive episode net.

### Ownership and independence

- `100%` established, non-shock native-R1 setup purity;
- `100%` established, non-shock native-R1 accepted-entry purity;
- owned-state net `> 0`;
- zero future-bar, retrospective-pivot, state-overwrite, or multiple-consumption
  violations;
- same-direction entry overlap within 15 minutes strictly below `20%` for every
  required available R1/R3 control; missing evidence fails closed.

### Execution and risk integrity

- successful-order, MT5-trade, and normalized-ledger counts reconcile;
- zero unexplained send failures and zero open-at-end positions;
- zero forbidden calendar/session/previous-PnL guard blocks;
- zero missing initial-risk calculations;
- every executed position has calculated initial stop risk `<= $50.00`.

### Drawdown and capital efficiency

- MT5 balance drawdown relative `<= 20%`;
- MT5 equity drawdown relative `<= 20%`;
- net / maximum MT5 equity drawdown `>= 2.00`;
- maximum MT5 equity drawdown `<= 2.0x` closed-ledger drawdown.

All missing money, ownership, overlap, and drawdown fields fail closed.

## Decision and Kill Discipline

- Any non-drawdown failure: `R1_HLF_SECOND_CONTINUATION_REJECT`.
- Both windows pass alpha/ownership but any drawdown gate fails:
  `R1_HLF_SECOND_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED`.
- Both windows pass every gate: `R1_HLF_SECOND_CONTINUATION_FULLY_QUALIFIED`.

A rejection freezes this family. It does not authorize alternate lookbacks, pivot
widths, ATR margins, retries, session masks, loss governors, or combination with a
failed R1 source.

## Required Future Telemetry and Implementation Gate

Retain setup/state IDs, exact state transitions and consumption reasons, canonical
regime dimensions at setup/pivot/attempt/entry/MAE/exit, completed-bar timestamps,
leg-one high/close, origin low, H1 ATR, pivot time/low, attempt OHLC/ATR, owner/conflict
result, intended/calculated position risk, same-specialist and portfolio open risk,
every order result, and open-at-end disposition.

Before historical launch, a later authorized turn must append mode 26, implement
isolated `g_r1_hlf_*` state, prove the first two-sided pivot is causal, prove no setup
overwrite or multiple consumption, implement the hard `OrderCalcProfit` buy-side risk
guard, compile with zero errors/warnings, pass deterministic trace/source/scaffold
tests, and receive explicit review before changing `HISTORICAL_RUN_AUTHORIZED`.
