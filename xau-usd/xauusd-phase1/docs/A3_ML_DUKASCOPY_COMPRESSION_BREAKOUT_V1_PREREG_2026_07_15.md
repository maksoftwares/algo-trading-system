# A3 ML Dukascopy D1 Compression H4 Breakout V1 Preregistration

Date locked: `2026-07-15`

## Strategy Premise

Gold often alternates between compressed ranges and directional expansion. This experiment tests whether the first strong H4 close outside a compressed two-day range has positive expectancy when aligned with the completed-D1 trend.

This is a new orthogonal candidate family. It is not a threshold repair of the failed H1 EMA pullback family.

## Frozen Data

- Verified Dukascopy XAUUSD Bid/Ask ticks only.
- July 2018 through June 2024, `72` contiguous monthly partitions.
- H4 and D1 Bid bars are derived from the verified H1 cache.
- UTC boundaries are used.
- A D1 bar requires at least `12` active H1 bars.
- An H4 bar requires at least `2` active H1 bars.
- No empty market hours are filled.
- Entry and outcome replay uses raw Dukascopy bid/ask ticks.

## Frozen Signal

At the close of a completed H4 bar:

1. Use only D1 bars that completed before the H4 decision time.
2. Calculate Wilder D1 ATR14.
3. Require a full `252`-bar D1 ATR-percentile history and percentile no higher than `80`.
4. Build the box from the latest `2` completed D1 bars.
5. Require box width divided by two to be no more than `1.5` times the latest 20-day median D1 range.
6. Calculate D1 EMA20 and its five-bar slope.
7. Calculate H4 Wilder ATR14.
8. Require H4 candle body fraction at least `0.35`.

Long candidate:

- Latest completed D1 close is above EMA20 and EMA20 is nondecreasing over five D1 bars.
- Current H4 is bullish and closes above the D1 box high.
- Previous completed H4 close was at or below that same box high.

Short candidate:

- Latest completed D1 close is below EMA20 and EMA20 is nonincreasing over five D1 bars.
- Current H4 is bearish and closes below the D1 box low.
- Previous completed H4 close was at or above that same box low.

No session, weekday, news, month, previous-PnL, account, or direction-performance mask is permitted.

## Frozen Risk and Execution

- Stop distance is the larger of H4 ATR14 and the distance from the H4 signal close to the opposite D1 box boundary.
- Reject stop distances above `3.0 H4 ATR`.
- Target is fixed at `2R`.
- Maximum hold is `240` hours.
- Entry quote must arrive within five minutes of the H4 decision.
- Long enters at Ask and exits on Bid.
- Short enters at Bid and exits on Ask.
- Raw tick order resolves stop versus target.
- Fixed size is `0.01` lot.
- Observed spread is embedded.
- Additional execution stress is `$0.30` per trade.
- Holding stress is `$0.35` per 24 hours, applied pro rata.

## Frozen Splits

- Train: before July 2021.
- Validation: July 2021 through June 2023.
- Test: July 2023 through June 2024.

No parameter may change after outcomes are observed.

## Quality Gates

All must pass:

- `72` verified source months.
- At least `250` candidates.
- At least `99%` of entry-window-eligible candidates resolved.
- At least `40` resolved rows in each split.
- At least `60` resolved rows in each direction.
- Unique candidate IDs and family/time/direction keys.

## Strategy Gates

All must pass for a research survivor:

- Train stress PF at least `1.20`.
- Validation stress PF at least `1.20`.
- Test stress PF at least `1.10`.
- Train and validation average stress R at least `0.05`.
- Test average stress R nonnegative.
- Test maximum closed drawdown no more than `15R`.
- At least `60%` positive active exit months in validation and test.
- At least `15` test rows in each direction.
- Fixed-seed, `2,000`-sample calendar-month bootstrap lower 2.5% bound for test average stress R above zero.

## Decision

- `DUKASCOPY_COMPRESSION_BREAKOUT_RESEARCH_SURVIVOR`: every quality and strategy gate passes.
- `DUKASCOPY_COMPRESSION_BREAKOUT_NO_SURVIVOR`: quality passes but at least one strategy gate fails.
- `DUKASCOPY_COMPRESSION_BREAKOUT_INVALID`: any source, causality, identity, or quality gate fails.

No result authorizes demo prediction, EA consumption, broker action, or deployment.
