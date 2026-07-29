# EURUSD Neutral prior-24-hour extreme fade preregistration

Status: `FROZEN_BEFORE_FIRST_CANDIDATE_COUNT_AND_ANY_OUTCOME`

## Motivation

The Regime 1 hindsight oracle is dominated by 00:00 UTC entries. This family
targets that timing directly, but its direction is determined only by the
fully completed prior 24-hour EURUSD session.

This is oracle-timing-informed research, not pristine discovery. No oracle
side, target/stop path, return, P&L, or prior result selects the direction.

## Fixed signal

At exactly 00:00 UTC on a weekday:

1. Require all 288 M5 bars from the prior 24 hours.
2. Build the prior-window midpoint open, high, low, and close.
3. Require a candle body of at least 25% of its range.
4. If the close is in the top 20% and above the open, enter short.
5. If the close is in the bottom 20% and below the open, enter long.
6. Otherwise remain in cash.
7. Require the latest fully known hourly regime state to be Neutral,
   unresolved, non-shock, non-compressed, and no more than four hours stale.

There is no threshold sweep and no direction alternative.

## Fixed risk

- Exact 00:00 M5 open with a 0.7-pip spread floor and 0.1-pip adverse entry
  slippage.
- Structure stop beyond the prior-window extreme and at least the larger of
  one quarter of the prior range or eight pips.
- Maximum risk 40 pips.
- Target 1.5R and maximum hold 12 hours.
- Stop first on an ambiguous M5 bar.
- One open position and at most one trade per UTC date.

## Stage boundary

The first pass is capacity-only. It may count completed prior windows,
causal Neutral ownership, sides, timestamps, and decision-time risk.
It may not load any forward path, exit, return, P&L, or oracle row.

If every capacity gate passes, execution remains prohibited until a separate
implementation is hash-locked, committed, and pushed. Failure retires the
exact family without post-outcome repair.
