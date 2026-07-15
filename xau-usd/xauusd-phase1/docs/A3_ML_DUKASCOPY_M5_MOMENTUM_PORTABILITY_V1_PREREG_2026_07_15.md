# A3 ML Dukascopy M5 Momentum Portability V1 Preregistration

Date locked: `2026-07-15`

## Objective

Independently replay the already frozen exact-MT5 clean long/short M5 momentum portfolio on verified Dukascopy bid/ask ticks. This is a cross-feed portability test, not a parameter search.

The prior MT5 package reported `1,317` trades, `64.54%` wins, PF `1.43`, and `2.46` trades per active day. Those numbers are historically selected and use the MT5 feed. They are context only and are not accepted as proof.

## Source Lock

- EA: `A1XauM5MomentumContinuationExecutor.mq5`.
- EA SHA-256: `c590adabc92fe4b63dac22812e4ac9a12882b23b6ed8242848470f90fd01e265`.
- Portfolio spec SHA-256: `e5d7a0fe3283820ac73800bd8562eab9f098d70e5747346c2e8e7cca07d8576a`.
- Candidate package: `v5_v4_move12 + freq_h1_h4_short_rr0p7_v1_core_1_5_15_19`.

No lane, hour, threshold, stop, target, or filter may change after Dukascopy outcomes are read.

## Data and Time

- Verified Dukascopy XAUUSD raw bid/ask ticks from July 2018 through June 2024.
- M5 bid/ask bars are derived directly from raw ticks and bound to the verified monthly source manifests.
- H1 bars use the existing verified cache; H4 bars use UTC four-hour boundaries.
- Capital.ComMena server time is frozen as UTC+4, based on repository runtime logs where broker timestamps are four hours ahead of UTC.
- The UTC+4 offset also preserves H4 boundaries because it is divisible by four.

## Common Trigger

On each completed M5 bid bar:

1. Calculate Wilder-style ATR14 using the repository convention.
2. Use the previous 12 completed M5 bars for recent high and low.
3. Require signal range at least `0.60 ATR` and body fraction at least `0.45`.
4. Long close location must be at least `0.72`; short close location at most `0.28`.
5. Long must close at least `0.20 ATR` above the recent high; short is symmetric below the recent low.
6. Three-bar move is the signal close minus the close three completed M5 bars earlier, divided by ATR.
7. Require completed H1 and H4 trend alignment: close above EMA20 above EMA50 with nonnegative three-bar EMA20 slope for long; symmetric for short.

## Frozen Lanes

### Clean Long V5 Move12

- Long only.
- Three-bar move at least `1.20 ATR`.
- Block server hours `2,9,10,11,12,13,17,19,21,23`.
- Target `0.70R`.

### Clean Short Core

- Short only.
- Three-bar move no greater than `-0.70 ATR`.
- Allowed server hours are `1,2,3,4,5,15,19`; all others are blocked.
- Target `0.70R`.

## Risk and Execution

- Stop is `2.50 M5 ATR`, floored at `350` points and rejected above `1,800` points.
- XAUUSD point size is frozen at `$0.01`.
- Reject entry spread above `75` points.
- Reject estimated spread cost above `0.05R`.
- Entry uses the first raw quote within five minutes of the M5 decision.
- Long enters at Ask and exits on Bid; short enters at Bid and exits on Ask.
- Raw tick order resolves stop versus target.
- Fixed lot is `0.01`.
- Additional stress is `$0.30` per selected trade plus `$0.35` per 24 hours held.
- Maximum research replay horizon is 720 hours. Selected timeout exits above `0.5%` invalidate portability.
- Each lane permits one open position, five-minute cooldown, and at most 12 entries per UTC+4 server day.
- The two lanes may overlap, but total concurrency must not exceed two.
- A source day must contain at least `100` derived M5 bars before it enters frequency denominators.

## Frozen Evidence Windows

- `prehistory`: July 2018 through June 2022.
- `replication`: July 2022 through June 2024.

The package was historically selected using MT5 dates beginning in July 2022. Therefore:

- prehistory is an independent earlier-date backcast, not prospective evidence;
- replication is a different-feed replay over calendar dates that overlap prior MT5 research;
- even a full pass authorizes only a research survivor and a later frozen demo-forward exam.

## Acceptance Gates

All source-quality and strategy gates in the machine contract must pass, including:

- at least `600` prehistory and `250` replication trades;
- at least `0.50` trades per source day;
- at least `2.0` trades per active trade day;
- active trade-day coverage at least `35%`;
- win rate at least `55%` in both windows;
- stress PF at least `1.15` prehistory and `1.20` replication;
- positive exit-month share at least `55%`;
- closed drawdown no more than `$150` prehistory and `$100` replication at fixed `0.01` lot;
- each lane net nonnegative in both windows;
- net remains positive after removing the top 25 winners in each window;
- calendar-month bootstrap lower 2.5% average-R bound above zero in each window.

## Decision

- `DUKASCOPY_M5_MOMENTUM_PORTABILITY_RESEARCH_SURVIVOR`: every gate passes.
- `DUKASCOPY_M5_MOMENTUM_PORTABILITY_NO_SURVIVOR`: source quality is valid but at least one strategy gate fails.
- `DUKASCOPY_M5_MOMENTUM_PORTABILITY_INVALID`: source, cache, resolution, identity, timeout, or protocol quality fails.

No result authorizes demo prediction, EA consumption, broker action, shared-account sizing, or deployment.
