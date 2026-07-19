# V23 Preregistration

## Attempt

This is one new economic hypothesis and must be counted whether it passes or
fails. V22.2 failed its 2-4/day opportunity gate because its strictest threshold
still produced 15 validation candidates/day. No V22.2 outcome was opened.

## Frozen hypothesis

When the V22.2 lagged cross-venue residual reaches `absolute_residual_z >= 4.0`
and its direction agrees with the prior 60-second Dukascopy impulse, Capital
XAUUSD will continue in that direction over the next five minutes often enough
to overcome observed bid/ask spread and adverse slippage.

No session, hour, weekday subset, direction, regime, threshold, hold duration,
stop, take-profit, or feature may be selected after outcomes are opened.

## Causal candidate rule

- Primary safety lag: 15 seconds.
- Clock rejection lags: 20 and 30 seconds.
- Trailing basis window: 120 minutes, closed on the left.
- Warm-up: 360 observations; reset after a 15-minute source gap.
- Residual floor: 1.5 current Capital spreads.
- Dukascopy impulse floor: one current Capital spread.
- Maximum Capital spread: 0.75 price units.
- Episode cooldown: 20 minutes.
- Candidate threshold: z = 4.0.

## Execution simulation

- Evaluate only UTC weekdays containing at least 10,000 paired quotes.
- Entry is the first Capital paired quote strictly later than the candidate,
  no more than 10 seconds later.
- Exit is the first paired quote at or after entry plus exactly 300 seconds,
  no more than 10 seconds late.
- Long enters at ask and exits at bid; short enters at bid and exits at ask.
- Base adverse slippage: 0.05 price units on each side.
- Stress adverse slippage: 0.15 price units on each side.
- Fixed reference size: 0.01 lot, equal to $1 per XAUUSD price unit under the
  existing 100-ounce contract convention.
- No overlapping positions are expected because hold time is shorter than the
  candidate cooldown; any overlap is skipped deterministically.

## Evidence partitions

- Development: 2026-05-27 through 2026-06-30 from frozen V22.1/V22.2 artifacts.
- Sealed confirmation: 2026-07-01 through 2026-07-17 inclusive.
- July Capital files are hash-locked before acquisition.
- July Dukascopy data must be downloaded from the free public Dukascopy endpoint
  only after the V23 contract lock exists.

## Admission gates

All gates must pass:

- Development primary base PF >= 1.05 and net P&L > 0.
- Confirmation primary has at least 80 trades and 8-20 trades/full weekday.
- Confirmation primary base PF >= 1.20, stress PF >= 1.05, and net P&L > 0.
- Confirmation profitable-day share >= 50%.
- Confirmation closed-trade drawdown <= $200 and recovery factor >= 1.0.
- A deterministic 10,000-sample UTC-day bootstrap has a 90% lower confidence
  bound for mean daily base P&L greater than zero.
- Confirmation 20-second and 30-second safety-lag base PF are each >= 1.00.

No aggregate result may conceal a failed confirmation gate. No gate may be
loosened after outcomes are opened.

## Authorization

Even a full pass cannot authorize an EA, Python execution, demo, live, account,
terminal, or broker action. It permits only forward shadow collection beginning
after 2026-07-20 and a later untouched admission review.
