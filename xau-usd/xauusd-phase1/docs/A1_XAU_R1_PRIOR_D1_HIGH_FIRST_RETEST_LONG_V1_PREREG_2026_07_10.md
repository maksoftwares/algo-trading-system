# A1 XAU R1 Prior-D1-High First-Retest Long V1 Preregistration

Date: 2026-07-10

Status: `PREREGISTERED_IMPLEMENTED_COMPILE_VALIDATED_NOT_RUN`

## Purpose

Test one genuinely new R1 structural family after both frozen R1 owners failed the
2016-2021 durability exam:

- the clean R1 box produced `48.04%` WR and `1.86` PF;
- the long-expansion replacement produced `47.59%` WR and `1.63` PF.

This candidate is the causal directional mirror of the preregistered R2 prior-D1-low
family. Its thresholds are mirrored before any R1 result is observed; they are not a
new R1 parameter search.

The source is not a repair of either rejected R1 owner and is not an R3 compression
release. It uses a single prior-D1 structural level, a completed-H1 acceptance event,
and exactly the first completed-M15 retest attempt.

## Runtime Boundary

Research-only exact MT5 Strategy Tester work. No demo/live attachment, chart, preset,
profile, account, position, order, registry, or broker-state change is authorized.

Do not launch historical tests until the EA implementation, causal-consumption tests,
and frozen runner static checks have passed review.

## Frozen Source Identity

- Source: `r1_prior_d1_high_first_retest_long_v1`
- Variant: `r1_pdh_first_retest_structural_v1`
- Proposed signal mode: `SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG = 23`
- Direction: long only
- Setup and executed-entry owner: established native `R1/uptrend`
- Exactly one parameter cell; no grid, sensitivity variant, or directional sibling

## Causal Signal

Every decision uses completed bars only.

1. At each newly completed H1 bar, require the native completed-bar router to be
   established `R1/uptrend`. Do not backfill earlier H1 breaks at initialization.
2. Use the prior completed D1 high relative to that H1 bar as the structural resistance
   anchor.
3. Arm acceptance only when that completed H1 bar:
   - is bullish;
   - closes at least `0.10 * H1 ATR(14)` above the anchor;
   - has range at least `1.00 * H1 ATR(14)`;
   - has body/range at least `0.50`;
   - closes in the top `0.25` of its range (`close_location >= 0.75`); and
   - has H1 ATR(14) percentile from `40.00` through `90.00`, inclusive, over
     480 completed H1 observations.
4. Observe only the next eight completed M15 bars after the H1 acceptance closes.
5. The first completed M15 bar whose low reaches
   `anchor + 0.25 * M15 ATR(14)` or lower is the only eligible retest bar.
6. Invalidate and consume the setup if any completed M15 close is below
   `anchor - 0.10 * H1 ATR(14)`.
7. The first retest bar qualifies as a failed-breakdown/reclaim long only when it:
   - is bullish;
   - closes at least `0.10 * M15 ATR(14)` above the anchor;
   - has body/range at least `0.50`; and
   - closes in the top `0.25` of its range (`close_location >= 0.75`).
8. Stop below the lowest completed M15 low since acceptance minus
   `0.20 * M15 ATR(14)`.
9. Block the opportunity if stop distance exceeds `1.00 * H1 ATR(14)`.
10. The setup is consumed by the first M15 retest touch whether that bar qualifies or
    fails. A qualifying signal is consumed before later router, cost, position, or risk
    guards run. There is no retry and no second entry from the same H1 acceptance.
11. The strict native R1 router is checked again at entry. A state change consumes and
    blocks the setup rather than reassigning it to another specialist.

The first-touch consumption rule is mandatory. Waiting through a failed first retest
for a later attractive candle would introduce outcome-conditioned selection and would
not be this candidate.

## Independence From Rejected R1 and R3 Families

This family is structurally independent by construction:

- it does not use D1 compression ATR percentile, a multi-day D1 box, or H4 expansion;
- it does not use signal mode 7;
- it does not use the rejected box2/broad-box thresholds;
- it does not use the R3 compression setup or transition router permission;
- it requires a completed H1 acceptance above one prior-D1 high and a later M15 reclaim;
- it consumes one acceptance event and cannot stack repeated entries from the same event.

Diagnostic same-direction entry overlap within 15 minutes must be reported against both
rejected R1 owners and every available R3 compression-release ledger. Overlap must be
below `20%` before the source can enter a portfolio. A structurally distinct source that
still reproduces an incumbent's events is not independent enough for portfolio use.

## Frozen Tester Inputs

| Input | Value |
| --- | ---: |
| `InpSignalMode` | `23` |
| `InpRegimeRouterMode` | `1` |
| `InpDirectionMode` | `1` |
| `InpRiskReward` | `2.00` |
| `InpR1PdhAtrPeriod` | `14` |
| `InpR1PdhH1AtrPercentileLookback` | `480` |
| `InpR1PdhH1AtrPercentileMin` | `40.00` |
| `InpR1PdhH1AtrPercentileMax` | `90.00` |
| `InpR1PdhBreakMarginH1Atr` | `0.10` |
| `InpR1PdhBreakMinRangeH1Atr` | `1.00` |
| `InpR1PdhBreakMinBodyFraction` | `0.50` |
| `InpR1PdhBreakCloseLocationMin` | `0.75` |
| `InpR1PdhRetestWindowM15Bars` | `8` |
| `InpR1PdhRetestTouchM15Atr` | `0.25` |
| `InpR1PdhInvalidBreakdownH1Atr` | `0.10` |
| `InpR1PdhReclaimDistanceM15Atr` | `0.10` |
| `InpR1PdhReclaimMinBodyFraction` | `0.50` |
| `InpR1PdhReclaimCloseLocationMin` | `0.75` |
| `InpR1PdhStopBufferM15Atr` | `0.20` |
| `InpR1PdhMaxStopH1Atr` | `1.00` |
| `InpMinAtrAbsoluteForEntry` | `0.00` |
| `InpStopFloorPoints` | `0` |
| `InpStopCeilingPoints` | `0` |
| `InpStopCapPoints` | `0` |
| `InpMaxEstimatedCostR` | `0.10` |
| `InpUseRiskNormalizedLots` | `true` |
| `InpRiskAmountUsd` | `50.00` |
| `InpMaxRiskLots` | `0.10` |
| `InpRejectRiskOvershootEnabled` | `true` |
| `InpMaxRiskOvershootPct` | `10.00` |
| `InpOnePositionPerMagic` | `true` |
| `InpMaxOpenPositionsPerMagic` | `1` |
| `InpMaxTradesPerDay` | `0` |
| `InpCooldownMinutes` | `0` |
| `InpUseDirectionalSessionFilter` | `false` |
| all blocked-hour/day CSV inputs | empty |
| all previous-PnL and portfolio-daily governors | disabled |
| profit protection / early exit / partial / split entry | disabled |

Tester deposit is `$10,000 USD`. Intended risk is `$50` per trade, or `0.50%` of
starting equity. The default-off risk overshoot guard blocks if broker volume
normalization produces actual stop risk above `$55`. Size is not rounded into a larger
unbounded risk.

## Exact Evidence Windows

Run the identical frozen candidate, with a fresh EA/tester process for each window:

- prehistory durability: `2016.01.01 -> 2021.12.31`;
- primary: `2022.07.01 -> 2026.06.30`.

Both windows are exams. The candidate must not be changed between them. Only
post-2026-07 forward evidence is genuinely untouched.

## Admission Gates

Both exact windows must independently pass the global specialist gates:

- trades `>= 100`;
- at least three years with exposure and three profitable calendar-year buckets;
- at least three independently separated activity episodes;
- WR `>= 50%`;
- realized average-win/average-loss `>= 2.00`;
- PF `>= 2.00`;
- stressed PF after `-$0.30/ticket >= 1.75` and stressed net `> 0`;
- top-ten-winners-removed net and top-three-days-removed net both `> 0`;
- best-month share `<= 30%`;
- no activity episode contributes more than `50%` of positive episode net;
- `100%` native R1 setup and accepted-entry purity;
- zero forbidden calendar/performance guard blocks;
- successful orders, MT5 trades, and normalized rows reconcile with zero unexplained
  order-send failures;
- MT5 balance and equity DD relative are each `<= 20%`;
- net / maximum MT5 equity DD `>= 2.00`;
- maximum MT5 equity DD `<= 2.0x` closed-ledger DD.

The primary window must also have positive pre-2026 net. Same-direction overlap with
each rejected R1 owner and available R3 ledger must be `<= 20%` before portfolio use.

## Decision

- Any alpha, durability, ownership, concentration, or execution failure:
  `R1_PDH_FIRST_RETEST_REJECT`.
- Alpha and ownership pass in both windows but a global DD gate fails:
  `R1_PDH_FIRST_RETEST_ALPHA_ONLY_RISK_REPAIR_REQUIRED`.
- Every standalone and DD gate passes:
  `R1_PDH_FIRST_RETEST_FULLY_QUALIFIED`.

No result authorizes a threshold sibling, second-retest variant, hour/session mask,
performance governor, combination with a rejected R1 owner, or demo/live deployment.

## Minimal EA Implementation Plan

Touch only `mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5` after the current R2
exact infrastructure is frozen.

1. Append `SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG = 23`; do not renumber modes
   `0..22`.
2. Add exactly the `InpR1Pdh*` inputs listed above, defaulted to the frozen values.
3. Add isolated `g_r1_pdh_*` state for last scanned H1, acceptance time, last counted
   completed M15 bar, eight-bar observation counter, consumed acceptance time, anchor,
   H1 ATR/percentile/acceptance close, first-touch outcome, and M15 audit fields. No
   elapsed-time expiry is permitted. Do not share or mutate `g_r2_pdl_*` state.
4. Implement these directionally mirrored helpers:
   - `ResetR1PriorD1HighBreakState()`;
   - `PriorCompletedD1HighAtTime()` using D1 `containing_shift + 1`;
   - `ArmR1PriorD1HighBreakAtH1Shift()`;
   - `RefreshR1PriorD1HighBreakState()` scanning only the newly completed H1 bar;
   - `R1PriorD1HighRetestLow()`; and
   - `TryR1PriorD1HighFirstRetestLongSignal()`.
5. `Arm...` must check `CurrentXauRegime() == XAU_REGIME_UPTREND` before storing the
   H1 event. This is setup ownership; router mode 1 remains the separate entry check.
6. Add signal mode 23 to `IsM15DecisionSignalMode()` and dispatch it once per completed
   M15 decision bar.
7. In `Try...`, set `g_r1_pdh_consumed_break_time` immediately on the first retest touch,
   before checking whether the candle qualifies. Emit `r1_pdh_first_retest_rejected`
   for a consumed nonqualifying touch, and never re-arm the same H1 acceptance.
8. Map the audit fields exactly as declared below and suffix the accepted signal reason
   with `RegimeStateName(CurrentXauRegime())`.
9. Apply the `InpR1PdhMaxStopH1Atr` guard after `WOULD_SIGNAL` and before any calendar,
   router, position, or broker action. Use reason `r1_pdh_stop_h1_atr_exceeded`.
10. Leave router modes, signal mode 7, all box/R3 functions, all R2 state/functions,
    and legacy defaults unchanged.

Compile with zero errors/warnings, run the new static/source tests, and review a short
snapshot trace proving one H1 acceptance can produce at most one consumed M15 attempt
before changing `HISTORICAL_RUN_AUTHORIZED` to `True`.

## Required Audit Semantics

For signal mode 23, map the existing signal log fields as follows:

- `recent_high`: completed H1 acceptance close;
- `recent_low`: frozen prior-completed-D1-high anchor;
- OHLC/body/close-location/ATR: the first completed M15 retest bar;
- `three_bar_move_atr`: H1 ATR percentile divided by 100;
- `break_distance_atr`: reclaim close distance above the anchor divided by H1 ATR;
- signal reason: `R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_STATE_uptrend`.

Report `r1_pdh_stop_h1_atr_exceeded`, `risk_amount_overshoot`, first-touch rejection,
invalidation, strict-router blocks, order-send failures, balance DD, and equity DD.
