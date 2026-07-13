# A1 XAU R2 Second-Continuation Lower-High Short V1 Preregistration

Date: `2026-07-10`

Status: `PREREGISTERED_SCAFFOLD_ONLY_NOT_IMPLEMENTED_NOT_RUN`

## Purpose

Test one genuinely new R2 owner for mature, native XAUUSD downtrends after the
prior-D1-low first-retest family was killed. This is not a threshold sibling or a
calendar repair of that result.

The hypothesis is narrower: after an established downtrend produces one completed-H1
downside displacement, the first meaningful M15 relief pivot should remain a lower
high. The specialist acts only on the first later attempt to accept below the first
leg's low. It therefore owns a *second continuation*, not the transition into a
downtrend, the first break, or a generic relief-rally touch.

## Runtime Boundary

This turn authorizes only this preregistration, a fail-closed runner scaffold, and
static tests. It does **not** authorize an EA edit, compile, exact-history launch,
demo/live attachment, chart, preset, profile, account, order, position, registry, or
broker-state change.

Historical execution remains locked until a later review confirms the state-machine
implementation and explicitly changes `HISTORICAL_RUN_AUTHORIZED` from `False`.

## Frozen Identity and Ownership

- Source: `r2_second_continuation_lower_high_short_v1`
- Variant: `r2_lhf_second_continuation_structural_v1`
- Proposed appended signal mode:
  `SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT = 24`
- Direction: short only
- Setup and accepted-entry owner: canonical direction `DOWN`, phase `ESTABLISHED`,
  volatility other than `SHOCK`
- Compatibility label at setup and entry: `downtrend`
- Exactly one parameter cell; no grid, sensitivity sibling, or directional mirror
- One same-magic position maximum; no event stacking

Mode 23 is already reserved by the preregistered R1 prior-D1-high family. A later EA
implementation must append mode 24 without renumbering modes 0 through 23.

## Why This Is a New Family

This source is structurally distinct from the rejected and diagnostic R2 paths:

- It does not use a prior-D1 low, so it is not the killed first-retest family.
- It does not use H1 EMA20/EMA50 touches, so it is not the R2 pullback-rejection
  family.
- It does not act on a one-bar M5 breakdown/retest or impulse threshold, so it is not
  the R2 continuation V1/V2/V4 family.
- It does not use an absolute ATR floor, an hour/session/day/month mask, previous-PnL
  state, or an outcome-derived threshold.
- It requires a causal multi-event sequence: H1 leg one, first confirmed M15 lower
  high, then first M15 second-break attempt.

Entry overlap within 15 minutes must nevertheless be measured against every available
R2 pullback, continuation, and killed prior-low control. Structural novelty alone does
not prove event independence.

## Completed-Bar State Machine

All regime, setup, pivot, signal, stop, and invalidation inputs use completed bars.
Bar 0 is forbidden. State is keyed by the completed-H1 leg-one close time.

### State 0: `IDLE`

At each newly completed H1 bar, arm leg one only if all conditions hold:

1. The canonical regime at the H1 close is direction `DOWN`, phase `ESTABLISHED`,
   volatility not `SHOCK`, compatibility label `downtrend`.
2. The strict R2 completed-D1 predicate is true for each of D1 shifts 1, 2, and 3,
   and completed-H4 confirmation is still down. This three-D1 requirement makes the
   state mature; a new transition cannot be relabeled as R2.
3. The H1 bar is bearish.
4. Its close is at least `0.10 * H1 ATR(14)` below the lowest low of the preceding 12
   completed H1 bars, excluding the leg-one bar.
5. Its range is at least `1.00 * H1 ATR(14)`.
6. Its body/range is at least `0.50`.
7. Its close is in the bottom `0.25` of its range.

Freeze:

- `leg_one_low`: the completed leg-one H1 low;
- `leg_one_close`: the completed leg-one H1 close;
- `origin_high`: the highest high of the preceding 12 completed H1 bars;
- `leg_one_h1_atr`: completed H1 ATR(14);
- the canonical setup regime dimensions/timestamps; and
- a unique setup ID derived from the leg-one close time.

Transition to `WAIT_FIRST_PIVOT`. While any state is active, newer leg-one candidates
are ignored; they cannot overwrite or stack the event.

### State 1: `WAIT_FIRST_PIVOT`

Observe at most the next 16 completed M15 bars after leg one.

The first causally confirmed M15 pivot high is the first pivot bar whose high is
strictly greater than the highs of its two completed bars on the left and two
completed bars on the right. At the confirmation decision, the pivot and all four
comparison bars are completed. The first chronological confirmed pivot is consumed
even when it fails the conditions below; the code may not wait for a prettier pivot.

The first pivot qualifies as the lower-high reset only if:

- `pivot_high - leg_one_close >= 0.35 * leg_one_h1_atr`; and
- `pivot_high <= origin_high - 0.10 * leg_one_h1_atr`.

Before a qualifying pivot is confirmed, consume the setup without a trade if:

- any completed M15 close is below
  `leg_one_low - 0.10 * M15 ATR(14)` (`continuation_without_reset`);
- any completed M15 close is above `origin_high`;
- the regime is no longer established, non-shock `DOWN`; or
- the 16-bar window expires.

An invalid first pivot emits `r2_lhf_first_pivot_rejected` and consumes the setup.
There is no later-pivot retry.

### State 2: `LOWER_HIGH_CONFIRMED`

The pivot is known only after its two right-side M15 bars have closed. If either of
those already-completed confirmation bars touched `leg_one_low`, consume the setup as
`r2_lhf_second_break_before_arm`; never enter retrospectively.

Otherwise, observe at most the next 16 completed M15 bars. Consume and invalidate if
the regime leaves established, non-shock `DOWN`, or if a completed M15 close is above
`pivot_high + 0.10 * leg_one_h1_atr`.

The first completed M15 bar whose low is at or below
`leg_one_low + 0.10 * M15 ATR(14)` is the only second-break attempt. Consume it
immediately, before checking candle quality or any later execution guard.

That consumed bar becomes a short signal only if it:

- is bearish;
- closes at least `0.10 * M15 ATR(14)` below `leg_one_low`;
- has body/range at least `0.50`; and
- closes in the bottom `0.25` of its range.

A nonqualifying first attempt emits `r2_lhf_first_second_break_rejected`. There is no
retry from the same leg-one event.

### Stop, Target, and Final Consumption

- Entry follows the existing market-style path after the qualifying completed M15
  bar.
- Stop is `pivot_high + 0.20 * M15 ATR(14)`.
- Block if entry-to-stop distance exceeds `1.00 * leg_one_h1_atr`, with reason
  `r2_lhf_stop_h1_atr_exceeded`.
- Target is fixed at `2.00R`.
- The strict canonical R2 owner is checked again immediately before authorization.
  A regime change consumes and blocks; it is not reassigned to transition or R3.
- A qualifying attempt is already consumed if cost, position, risk, or broker guards
  later block it.

## Frozen Tester Inputs

| Input | Value |
| --- | ---: |
| `InpSignalMode` | `24` |
| `InpRegimeRouterMode` | `2` |
| `InpDirectionMode` | `2` |
| `InpRiskReward` | `2.00` |
| `InpR2LhfAtrPeriod` | `14` |
| `InpR2LhfMaturityD1Bars` | `3` |
| `InpR2LhfLeg1LookbackH1Bars` | `12` |
| `InpR2LhfLeg1BreakMarginH1Atr` | `0.10` |
| `InpR2LhfLeg1MinRangeH1Atr` | `1.00` |
| `InpR2LhfLeg1MinBodyFraction` | `0.50` |
| `InpR2LhfLeg1CloseLocationMax` | `0.25` |
| `InpR2LhfResetWindowM15Bars` | `16` |
| `InpR2LhfPivotLeftBars` | `2` |
| `InpR2LhfPivotRightBars` | `2` |
| `InpR2LhfResetMinDepthH1Atr` | `0.35` |
| `InpR2LhfLowerHighMarginH1Atr` | `0.10` |
| `InpR2LhfSecondBreakWindowM15Bars` | `16` |
| `InpR2LhfSecondTouchM15Atr` | `0.10` |
| `InpR2LhfSecondCloseM15Atr` | `0.10` |
| `InpR2LhfSecondMinBodyFraction` | `0.50` |
| `InpR2LhfSecondCloseLocationMax` | `0.25` |
| `InpR2LhfInvalidReclaimH1Atr` | `0.10` |
| `InpR2LhfStopBufferM15Atr` | `0.20` |
| `InpR2LhfMaxStopH1Atr` | `1.00` |
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
future EA implementation must calculate the loss from normalized entry to stop using
`OrderCalcProfit(ORDER_TYPE_SELL, ...)`. If that calculation fails, is non-finite, or
its absolute loss exceeds `$50.00`, block with `risk_amount_overshoot`. A broker
minimum lot that risks more than `$50.00` is blocked, not rounded up. The frozen
overshoot percentage is zero; no `$55` tolerance applies to this family.

Every accepted and blocked attempt must log intended risk, calculated risk, lots,
entry, stop, tick metadata, and block reason. Every executed trade must reconcile to
calculated initial risk `<= $50.00`.

## Frozen Exact Windows

Run the identical one-cell candidate in a fresh isolated tester process for each:

1. `prehistory_201601_202112`: `2016.01.01 -> 2021.12.31`
2. `primary_202207_202606`: `2022.07.01 -> 2026.06.30`

Both windows are frozen exams. Neither result may change a signal threshold, add a
mask, or select a sibling in the other window. Only post-2026-07 forward evidence is
genuinely untouched.

The pre-recent bucket is through `2021.06.30` in prehistory and through `2025.12.31`
in primary; each must have positive net.

## Owned-Regime Episodes

An episode is a maximal causal run of completed D1 bars satisfying the strict mature
R2 predicate, separated from the next run by at least one completed D1 bar that does
not satisfy it. Assign a trade to the episode containing its leg-one setup timestamp.
This definition is frozen before results and is not based on profitable months.

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
- best-month share `<= 30%` of total positive net;
- no owned-regime episode contributes more than `50%` of positive episode net.

### Ownership and independence

- `100%` established, non-shock native-R2 setup purity;
- `100%` established, non-shock native-R2 accepted-entry purity;
- owned-state net `> 0`;
- zero future-bar, retrospective-pivot, state-overwrite, or multiple-consumption
  violations;
- same-direction entry overlap within 15 minutes is strictly below `20%` for every
  required available R2 control; missing required overlap evidence fails closed.

### Execution and risk integrity

- successful-order, MT5-trade, and normalized-ledger counts reconcile;
- zero unexplained order-send failures and zero open-at-end positions;
- zero forbidden calendar/session/previous-PnL guard blocks;
- zero missing initial-risk calculations;
- every executed position has calculated initial stop risk `<= $50.00`.

### Drawdown and capital efficiency

- MT5 balance drawdown relative `<= 20%`;
- MT5 equity drawdown relative `<= 20%`;
- net / maximum MT5 equity drawdown `>= 2.00`;
- maximum MT5 equity drawdown `<= 2.0x` closed-ledger drawdown.

All money and relative drawdown fields fail closed when missing.

## Decision and Kill Discipline

- Any alpha, durability, ownership, independence, concentration, execution, or risk
  failure: `R2_LHF_SECOND_CONTINUATION_REJECT`.
- Alpha/ownership pass in both windows but any drawdown gate fails:
  `R2_LHF_SECOND_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED`.
- Both windows pass every gate:
  `R2_LHF_SECOND_CONTINUATION_FULLY_QUALIFIED`.

A rejection freezes this family. It does not authorize alternate lookbacks, pivot
widths, ATR margins, event retries, session masks, loss governors, or combination with
another failed R2 source.

## Required Future Telemetry

For every setup and attempted transition, retain:

- setup ID and state (`IDLE`, `WAIT_FIRST_PIVOT`, `LOWER_HIGH_CONFIRMED`, `CONSUMED`);
- state-entry and state-exit timestamps and exact consumption reason;
- canonical direction/volatility/phase and compatibility label at setup, pivot
  confirmation, second-break attempt, entry, maximum adverse excursion, and exit;
- completed-bar timestamps used by the router and signal;
- leg-one low/close, origin high, H1 ATR, pivot time/high, M15 attempt OHLC/ATR;
- authorization owner/conflict result;
- intended/calculated position risk, same-specialist open risk, and portfolio open
  risk; and
- every order-send result and open-at-end disposition.

## Future Implementation Gate

Before any historical launch, a later authorized turn must:

1. append mode 24 without altering existing modes or defaults;
2. implement isolated `g_r2_lhf_*` state and explicit enum states;
3. prove through deterministic trace tests that one leg-one ID can consume at most one
   first pivot and one second-break attempt;
4. prove pivot confirmation uses two already-completed right-side bars and never
   enters retrospectively;
5. implement the hard `OrderCalcProfit` `$50.00` risk guard;
6. compile with zero errors and warnings;
7. pass source and scaffold tests; and
8. receive explicit review before changing `HISTORICAL_RUN_AUTHORIZED`.

