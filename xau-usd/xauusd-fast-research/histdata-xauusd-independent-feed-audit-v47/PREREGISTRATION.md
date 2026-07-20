# V47 HistData XAUUSD Independent-Feed Audit Preregistration

## Purpose

Determine whether the zero-cost HistData XAU/USD tick archive is sufficiently
valid, complete, and non-duplicate to justify a separately preregistered
cross-venue feature experiment. V47 is a data-foundation audit only. It cannot
calculate a trade outcome, train a model, create a signal, or authorize execution.

The archive schema, fixed-EST timestamp convention, file-status report, and
January 2024 row examples were inspected before this contract was written. No
HistData-versus-Dukascopy price comparison was opened before the gates below were
frozen.

## Frozen Sources

- HistData Generic ASCII XAU/USD tick archive for January 2024.
- HistData's status report bundled in the same archive.
- The existing immutable Dukascopy XAUUSD M5 bid/ask feature cache.
- HistData timestamps are interpreted as fixed EST (`UTC-05:00`) with no DST, so
  exactly five hours are added for this January sample.

Only a single month is used to decide source admissibility. More HistData history
may be acquired only if V47 passes.

## Frozen Processing

1. Require exactly timestamp, bid, ask, and volume fields.
2. Reject non-monotonic timestamps, nonpositive quotes, and crossed quotes.
3. Aggregate ticks into five-minute bars with a separate availability timestamp
   at the end of each bar. A future experiment may consume a bar only at or after
   that availability time.
4. Join HistData and Dukascopy on identical UTC five-minute bar starts.
5. Compare close-to-close price changes only across consecutive five-minute bars.
6. Do not shift either feed, optimize a timezone offset, or search a lead/lag.

## Frozen Gates

All gates must pass:

- at least 1,000,000 HistData rows;
- at least 25 calendar days spanned;
- monotonic timestamps;
- zero nonpositive or crossed quotes;
- median spread greater than zero and 99th-percentile spread no greater than USD
  10;
- at least 90% coverage of active Dukascopy five-minute bars;
- at least 5,000 matched bars;
- contemporaneous five-minute price-change correlation at least 0.95;
- median absolute midpoint basis no greater than USD 5;
- exact midpoint-close match fraction below 95%; and
- midpoint-basis standard deviation greater than USD 0.01.

Passing these gates establishes only that the source is a plausible,
non-bit-identical XAUUSD quote path. It does not establish a tradable edge.

## Governance

No same-version gate change is permitted. V47 contains no labels, future prices,
directions, P/L, trades, or model fields. The Core remains read-only. Demo, live,
EA, account, terminal, payment, subscription, and broker actions are prohibited.
