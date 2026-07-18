# XAUUSD M5 High-Volatility Chop Portability V2 Preregistration

## Purpose

This package tests one fixed, post-discovery Capital.com subtype on an
independent Dukascopy bid/ask feed. It does not search parameters or subtypes.

The original Chop V1 diagnostics reported that
`CHOP_RANGE_ROTATION_CONTINUATION_V1` on M5 was negative across all chop states,
but its already-defined `HIGH_VOL_CHOP` subset contained 111 Capital.com trades
and remained +10.609R after the registered stress deduction. That is selection
evidence, not validation. V2 therefore replays only that frozen subset on
Dukascopy. The other subtype rows remain visible in the source evidence and no
alternative subtype may replace it after outcomes.

## Fixed mechanism

- Owner: H4 `CHOP` only.
- H4 regime thresholds and hysteresis are unchanged from Chop V1.
- Volatility subtype: `HIGH_VOL_CHOP` only, defined causally from the existing
  H4 ATR percentile logic.
- Signal timeframe: M5.
- Mechanic: range-rotation continuation.
- Center: one-day EMA of M5 typical price.
- Scale: one-day rolling standard deviation of M5 typical price.
- Required prior excursion: at least 1.50 standard deviations on the opposite
  side during the prior six hours.
- Trigger: completed-bar cross back through the center.
- Confirmation: two-hour return and candle body direction agree with the trade.
- Target: center plus/minus 1.25 standard deviations, frozen at signal time.
- Stop: 1.25 ATR.
- Maximum hold: 12 elapsed hours.
- Direction cooldown: six elapsed hours.
- Entry: next executable Dukascopy M5 bid/ask open.
- Same-bar ambiguity: stop first.
- Stress: observed Dukascopy spread, 0.05R slippage, $0.30 ticket cost, and
  $0.35 per 24 hours of holding cost at one ounce.

## Frozen windows and gates

- Train: 2016-07-01 through 2021-07-01, end exclusive.
- Validation: 2021-07-01 through 2024-07-01, end exclusive.
- Exam: 2024-07-01 through 2026-07-01, end exclusive.
- Full: 2016-07-01 through 2026-07-01, end exclusive.

Every chronological stage must pass its registered trade-count, frequency,
profit-factor, stress-profit-factor, average-stress-R, drawdown, and
winner-removal gates. The full window also requires at least 60% of active years
to be stress-profitable. A pass remains retrospective cross-feed evidence and
requires exact MT5 parity plus prospective shadow confirmation before any demo
decision.

## Research controls

- Parameter search count: zero.
- Tested strategy/subtype pairs: exactly one.
- No post-outcome filter, direction, hour, year, stop, target, or cost change.
- Shock and non-chop states abstain.
- Paid data, Databento, model training, and broker actions are not used.
- No result authorizes Python predictions, EA consumption, demo, or live trades.
