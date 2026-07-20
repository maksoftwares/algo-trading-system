# Capital R4 Chop Forward V34 Preregistration

## Purpose

V34 is a read-only transport adapter for the already frozen R4 chop composite in
`chop-three-mechanism-rawtick-v26`. It does not create, select, tune, or modify a
strategy. Its only economic output is an append-only candidate stream.

## Timing and contamination statement

The V26 strategy rules and historical candidate stream were frozen before the
forward boundary of 2026-07-20 00:00:00 UTC. V34 is being locked after that
boundary because the need for a Capital quote-to-M5 transport adapter was found
during operational integration. No post-boundary R4 P&L, labels, exits, or other
economic outcomes may be opened while designing or locking V34.

This makes V34 valid as an engineering adapter, but it does not reset or improve
the selection-bias status already acknowledged by V26. Only prospective results
collected after this lock can provide new economic evidence.

## Frozen rule identity

V34 imports the V26 signal function and V26 component parameters directly.
Historical parity must reproduce all 521 V26 candidates and all signal-used
feature columns before the forward process can run.

The three frozen mechanics are:

1. `CHOP_Z_EXPANSION_DUAL_WINDOW_ENVELOPE`
2. `CHOP_FAILED_REVERSION_DUAL_MODE_ENVELOPE`
3. `CHOP_COUNTERFLOW_TIERED_ENVELOPE`

Their priority, sessions, thresholds, stop, target, and holding geometry remain
unchanged.

## Causal Capital transport

Long price context comes from read-only Capital MT5 M5 history. Completed live
M5 bars are reconstructed from Capital bid/ask quote CSV files using the exact
historical Dukascopy bucket semantics:

- five-minute UTC buckets;
- first, maximum, minimum, and last quote OHLC;
- mid-price changes reset at each bucket boundary;
- signed tick imbalance uses nonzero within-bucket mid-price changes;
- 15-minute imbalance uses exactly three contiguous M5 buckets.

A live M5 bar replaces the corresponding MT5 history bar only after it passes
all preregistered structural quote-quality gates. A candidate additionally
requires three contiguous quality-passed quote M5 bars. The current incomplete
M5 bar is excluded.

Capital book-volume fields are not available and are not fabricated. The frozen
V26 R4 signal masks do not consume them. Historical bars receive `NaN` tick
imbalance, preventing MT5 tick-volume proxies from being represented as quote
direction data.

## Fixed quality gates

- At least 20 unique quote milliseconds per M5 bar.
- First quote no later than 60 seconds after bucket start.
- Last quote no earlier than 60 seconds before bucket end.
- Maximum internal quote gap no greater than 60 seconds.
- Three contiguous quality-passed M5 bars for a signal.
- Completed bars only.

These gates are structural and were set without opening post-boundary economic
outcomes. Same-version threshold tuning is forbidden.

## Forward windows

- Boundary: 2026-07-20 00:00:00 UTC.
- Validation: first 20 complete eligible weekdays after adapter lock.
- Confirmation: next 20 complete eligible weekdays.

Calendar duration may be longer than 40 weekdays when feed-quality failures or
market holidays make a day ineligible.

## Authority

V34 cannot place, check, modify, or close orders. It does not resolve outcomes,
train a model, authorize Python predictions, or authorize demo/live trading.
Any later outcome evaluator must be separately preregistered and locked.
