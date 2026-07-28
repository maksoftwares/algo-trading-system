# EURUSD Neutral London-fix reversal preregistration

## Status

`LOCK_BEFORE_CENSUS_AND_OUTCOME`

This is one finite, structural-flow family that was not present in the prior
Neutral experiments. Generic local-price sweeps, session breakouts, opening
drives, and unconstrained reversals remain closed.

## Mechanism

Benchmark hedging and portfolio rebalancing concentrate around the
WM/Reuters 16:00 Europe/London fix. A sufficiently large pre-fix EURUSD move
that begins reversing during the completed fix M5 bar may represent temporary
benchmark flow unwinding rather than a durable directional signal.

Two mutually exclusive experts are declared:

1. `ORDINARY_FIX_REVERSAL` owns non-month-end weekdays.
2. `MONTH_END_FIX_REVERSAL` owns the final Monday-to-Friday calendar date of
   each month.

Both own only dates classified Neutral using information available at 00:00
UTC.

## Frozen causal rule

- Convert 16:00 Europe/London with the IANA timezone database, so the UTC clock
  changes causally with UK daylight saving.
- Measure the midpoint move across the twelve completed M5 bars ending at the
  fix.
- Require its absolute size to be at least the median of the preceding 20
  Neutral fix observations. The current observation is excluded.
- Require the completed fix M5 bar to move opposite the pre-fix displacement.
- Enter at the next M5 open in that opposite direction.
- The entry bar is forbidden from signal construction.
- Missing, holiday, zero, ambiguous, or quarantined observations mean cash.

The stop is beyond the completed fix-bar executable extreme plus 0.5 pip, with
a 4-pip floor and 25-pip ceiling. Target is 1.5R; maximum hold is 12 hours.
Execution uses bid/ask, a 0.7-pip retail spread floor, 0.1-pip slippage per
side, stop-first same-bar resolution, and one open position.

## Evaluation order

1. Build and report the outcome-blind census.
2. Open outcomes only through 2022.
3. Select each expert independently only if it passes both 2019-2020 and
   2021-2022, at least eight trades per block, positive expectancy and PF at
   least 1.0 in each block, plus combined PF at least 1.10.
4. If neither passes, forward P&L is forbidden.
5. If any pass, hash-lock the exact selection and development artifacts before
   opening 2023-2026 outcomes.

No clock, lookback, magnitude threshold, month definition, direction, stop,
target, hold, side, or year is changed after seeing results.

Passing historical gates would still require untouched prospective
confirmation and would not authorize broker action.
