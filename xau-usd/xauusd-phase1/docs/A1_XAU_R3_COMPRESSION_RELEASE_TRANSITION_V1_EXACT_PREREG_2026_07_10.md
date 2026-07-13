# A1 XAU R3 Compression-Release Transition V1 Exact-MT5 Preregistration

Date: 2026-07-10

Status: `PREREGISTERED_NOT_RUN`

## Purpose

Test one symmetric third-specialist candidate whose setup is owned by completed D1
compression and whose entry is the first eligible completed-H4 expansion signal.

This replaces the earlier broad, long-only R3 interpretation. It is not an R1 uptrend
variant and it is not an R2 downtrend variant. Direction at entry may be long or short,
but ownership is determined by the compression setup that existed before the H4 break.

This is one frozen exact-MT5 candidate, not a parameter search. A failure retires this
cell; it does not authorize sibling thresholds, calendar masks, or a directional-only
rescue.

## Exact Window

- Symbol/timeframe: `XAUUSD`, tester chart `M5`
- Signal decision timeframe: completed `H4` bars
- From: `2022-07-01`
- To: `2026-06-30`
- Tester deposit/currency: `$10,000 USD`
- Research-only; no demo or live claim is permitted

## Frozen Setup Ownership

Use only completed bars.

The setup is `R3_COMPRESSION` when all of the following are true at the H4 decision:

1. D1 ATR14 percentile over 252 completed D1 observations is `<= 30`.
2. The box is the high/low of exactly five completed D1 bars, shifts `[1..5]`.
3. `box_width / 5 <= 1.00 * median completed-D1 range` over 20 bars.

The completed H4 expansion entry is:

- long when H4 close is above the frozen box high and above H4 open;
- short when H4 close is below the frozen box low and below H4 open; and
- H4 absolute body / H4 range is `>= 0.50` in either direction.

This definition is symmetric. No D1/H4 trend filter, R1 permission, R2 permission,
supportive-state filter, or direction-specific threshold is allowed.

## Shock Override and Router Ownership

The candidate requires a new default-off router mode:

```text
REGIME_ROUTER_R3_COMPRESSION_RELEASE_SHOCK_BLOCK = 5
```

The mode is evaluated only after the compression-release signal has passed its frozen
setup rules. It:

- allows either direction;
- does not require the flat entry-time router label to equal `compression`;
- blocks when the existing completed-bar shock detector is true; and
- blocks if used with a signal mode other than D1-compression/H4-expansion.

This separation is intentional: a genuine release can be labelled transition, uptrend,
or downtrend at entry even though its causal setup owner was compression. The new mode
must not grant R1 or R2 permission.

## Frozen EA Inputs

```text
InpSignalMode=7
InpDirectionMode=0
InpRegimeRouterMode=5

InpD1CompressionAtrPercentileMax=30.00
InpD1CompressionBoxDays=5
InpD1CompressionRangeMedianMax=1.00
InpD1CompressionH4MinBodyFraction=0.50

InpRegimeShockH1RangeAtrMultiple=3.00
InpRegimeShockD1AtrPercentileMin=95.00
InpRegimeShockD1AtrLookback=60

InpRiskReward=2.00
InpStopCeilingPoints=0
InpStopCapPoints=0
InpMaxEstimatedCostR=0.15

InpUseRiskNormalizedLots=true
InpRiskAmountUsd=100.00
InpMaxRiskLots=0.05
InpRejectRiskOvershootEnabled=true
InpMaxRiskOvershootPct=0.00

InpOnePositionPerMagic=true
InpMaxOpenPositionsPerMagic=1
InpMaxTradesPerDay=6
InpCooldownMinutes=0

InpBlockedEntryHoursCsv=
InpBlockedEntryDayHoursCsv=
InpBlockedLongEntryHoursCsv=
InpBlockedShortEntryHoursCsv=
InpUseDirectionalSessionFilter=false
InpMinAtrAbsoluteForEntry=0.00

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

The `$100` stop-risk budget is 1% of starting tester equity. Exact post-normalization
risk may not exceed it. If broker minimum lot or invalid symbol metadata would exceed
the budget, the signal is blocked; size is never rounded up into an oversize trade.

## Candidate

Exactly one candidate is permitted:

```text
r3_compression_release_transition_v1_strict_symmetric
```

No alternative ATR percentile, box length, range ratio, body threshold, risk/reward,
stop, session, hour, weekday, month, or performance governor may be run under this
preregistration.

## Standalone Admission Gates

All gates are required:

- trades `>= 100`;
- win rate `>= 50%`;
- realized win/loss ratio `>= 2.00`;
- profit factor `>= 2.00`;
- stressed profit factor after `-$0.30/ticket >= 1.75`;
- stressed net `> 0`;
- at least three positive calendar-year buckets with exposure;
- long and short sides each have at least 20 trades and positive stressed net;
- top 10 winners removed net `> 0`;
- top three winning days removed net `> 0`;
- best-month share `<= 30%`;
- MT5 maximal equity drawdown `<= 10%`;
- zero order-send failures;
- zero entries admitted through shock, an incompatible router mode, or a calendar mask.

Recent-quarter inactivity is diagnostic, not a failure: a compression specialist must
remain silent when its setup is absent.

## Kill Rules

Use `R3_COMPRESSION_RELEASE_TRANSITION_V1_NO_SURVIVOR` if any admission gate fails.

Use `R3_COMPRESSION_RELEASE_TRANSITION_V1_STANDALONE_SHADOW` only if every gate passes.
Passing does not authorize portfolio inclusion. It must next pass pairwise overlap and
one exact shared-equity portfolio test. Same-event overlap above 20% with R1 or R2 is a
kill unless replacement superiority is proven without breaching the portfolio equity-DD
cap.

## Required Evidence

- exact MT5 HTML report and extracted summary;
- normalized trade ledger;
- long/short standalone slices;
- yearly and monthly concentration rows;
- order/guard reconciliation, including shock and risk-overshoot blocks;
- maximal balance and equity DD in USD and percent;
- the preregistration SHA256 in the generated report.
