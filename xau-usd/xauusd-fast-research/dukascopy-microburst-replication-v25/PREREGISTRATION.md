# V25 Dukascopy Microburst Replication Preregistration

## Purpose

V25 asks one question: does the already frozen V24.1 Capital quote-microburst
mechanism transfer without modification to an independently sourced Dukascopy
XAUUSD bid/ask tick feed?

V25 is one replication attempt. It contains no threshold, feature, session,
direction, horizon, cost, label, or model grid. No same-version rescue is
allowed after any economic result is exposed.

## Prior Selection And Evidence Status

- V24.1 was frozen from outcome-blind candidate-frequency calibration on one
  Capital demo tick day.
- No V24/V24.1 post-candidate return or P&L was available when this replication
  was defined.
- The Dukascopy archive has supported earlier, different research hypotheses.
  It is therefore not described as an untouched dataset.
- The exact five-second tick-update mechanism was not selected from Dukascopy
  economic outcomes. V25 is cross-feed mechanism replication only.
- Untouched Capital quotes from 2026-07-20 onward remain the decisive forward
  evidence and cannot be replaced by V25.

## Frozen Source

- Free public Dukascopy XAUUSD bid/ask ticks only; no paid data.
- Inclusive start: `2016-07-01T00:00:00Z`.
- Exclusive end: `2026-07-01T00:00:00Z`.
- Exactly 120 complete frozen monthly partitions.
- Every loaded hourly JSON file must match the size and SHA-256 recorded in its
  locked monthly acquisition manifest.
- Each monthly acquisition and frozen manifest, and the existing 120-month
  source inventory, is hash-bound into the V25 contract.
- Duplicate millisecond quotes keep the last source row, exactly as in V24.1.

## Frozen Candidate And Label

The following dictionaries must be exactly equal to V24.1 at contract lock:

- source-quality thresholds;
- five-second causal feature rules;
- first false-to-true crossing and first event per fixed four-hour UTC block;
- continuation direction mapping;
- 120-second observed bid/ask execution label;
- base and stress slippage;
- all economic gates.

The candidate uses only quotes at or before its timestamp. Entry is the first
strictly later quote within two seconds. Exit is the first quote at or after 120
seconds from entry, also within two seconds. A stage-boundary purge excludes any
candidate whose maximum allowed label path could reach the next stage.

## Chronological Evidence Stages

1. `EARLY_REPLICATION`: 2016-07-01 through 2020-06-30.
2. `MIDDLE_VALIDATION`: 2020-07-01 through 2023-06-30.
3. `RECENT_FINAL_HOLDOUT`: 2023-07-01 through 2026-06-30.

Only the first unopened stage may run. A later stage cannot open in the same
invocation. It may open on a later invocation only when every prior stage has an
immutable passing audit. Failure ends V25 and later outcomes remain sealed.

## Frozen Complete-Day Rule

A weekday is eligible only when it has at least 100,000 unique millisecond
quotes, no more than 5% duplicate milliseconds, starts no later than 02:00 UTC,
ends no earlier than 22:00 UTC, and has a 99th-percentile interquote gap no more
than five seconds. This is the unchanged V24.1 source-quality rule.

## Frozen Gates Per Stage

Each stage independently requires:

- at least 40 executable trades;
- 2.0 through 6.0 trades per eligible full weekday;
- at least 20% of trades in each direction;
- positive base net and base PF at least 1.20;
- positive stress net and stress PF at least 1.05;
- at least 50% profitable eligible days;
- closed-trade drawdown no more than USD 100 at fixed 0.01 lot;
- recovery factor at least 1.0;
- PF at least 1.0 in both chronological halves;
- positive 90% one-sided day-bootstrap lower bound using 10,000 samples and
  seed 2401.

## Anti-Overfit And Authorization

- Hypothesis count: one exact replication.
- Parameter grids and outcome-driven edits: prohibited.
- Every exposed failure is preserved.
- Historical passage cannot authorize training or trading.
- A model may be considered only after stable high-quality labels exist and the
  untouched Capital forward protocol also passes.
- Model training, Python prediction, EA consumption, demo, live, paid data, and
  broker action are all false.
