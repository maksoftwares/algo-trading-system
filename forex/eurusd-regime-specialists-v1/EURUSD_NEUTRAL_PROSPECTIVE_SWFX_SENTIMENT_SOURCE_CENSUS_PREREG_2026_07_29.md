# EURUSD Neutral prospective SWFX sentiment source census

## Purpose

This is a source-only prospective census of the public Dukascopy SWFX
sentiment widget. It tests whether the EUR/USD row is available, stable,
timestampable at observation time, and sufficiently varied to justify a later,
separately locked strategy experiment.

It is not a strategy and cannot create a trade.

## Prospective boundary

- The immutable prospective start is `2026-07-29T06:30:00Z`.
- Captures occur on UTC weekdays at minute `02` and `32` of every hour.
- A request may start no more than 300 seconds after its scheduled clock.
- A late or missed clock is not backfilled.
- No response observed before the prospective start is part of this census.
- Historical EURUSD prices, returns, oracle rows, outcomes, and P&L are
  forbidden throughout the census.

## Source contract

The request uses the official no-login Dukascopy public endpoint, the fixed
`liquidity=consumers` and `type=swfx` query, a browser-compatible user agent,
and the official widget as referer. It sends no cookie, account identifier,
token, or broker credential.

Every successful attempt preserves:

- the exact raw JSONP body;
- all response headers;
- local UTC request-start and response-completion times;
- HTTP status, URL, and fixed request policy;
- raw and normalized SHA-256 hashes;
- the one exact case-sensitive `EUR/USD` row; and
- an explicit null provider settlement time because the payload does not
  publish one.

The capture fails closed if HTTP access fails, the body exceeds 2,000,000
bytes, JSONP cannot be parsed, the response is not a list, there is not exactly
one `EUR/USD` row, a required number is missing or non-finite, or a long/short
pair is not additive inverse within `0.0001`.

## Frozen census gates

Evaluation is prohibited until at least 27 calendar days and 20 distinct UTC
weekdays have elapsed. The source qualifies only if all of these hold:

- at least 800 valid captures;
- at least 90% of scheduled clocks have an immutable manifest;
- at least 90% of scheduled clocks are valid source captures;
- at least 18 days contain a valid capture;
- at least 30 distinct EUR/USD value states are observed;
- no more than six consecutive scheduled captures fail; and
- at least three observations on separate occasions are manually compared
  with an official visible Dukascopy widget or timestamped JForex observation.

The manual comparisons may establish schema meaning, but they cannot add
EURUSD price or outcome information.

## Decision after the census

Passing only permits design of a new prospective Regime-1 specialist. The
direction mapping, threshold, entry time, stop, target, and admission gates
must be frozen in a new preregistration after this census. They may not be
selected from EURUSD outcomes observed during this census.

Failing keeps this source out of the strategy. Frequency is descriptive and
is not repaired by lowering gates after inspection.

## Safety

No demo order, live order, broker connection, or terminal action is allowed.
The helper performs public source downloads only.
