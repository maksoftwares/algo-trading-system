# A3 ML Intraday Macro Source V1 Preregistration

Date: 2026-07-16

## Purpose

Earlier price-only and lagged daily-macro campaigns did not produce a qualified
high-frequency gold specialist. This source-only stage tests whether materially new
intraday information is available with sufficient integrity for one further formal
research iteration. It does not inspect gold outcomes and cannot authorize a strategy.

## Locked Official Sources

Dukascopy's official range-of-markets page identifies `DOLLAR.IDX/USD` as a US Dollar
Index CFD and `USTBOND.TR/USD` as a US government-bond CFD. Dukascopy also states that
its CFD quotes are its own prices and are not precise exchange quotes. The research
will therefore use them only as causal intraday cross-asset proxies. It will not call
them ICE DXY, Treasury yield, exchange trade, futures volume, or order-book data.

The official Jetta instrument metadata and hourly tick endpoints are locked in the
machine-readable contract. Metadata was archived outside Git:

- `DOLLAR.IDX/USD`: metadata SHA256
  `b596ab8a33b3c2bf41e042e4d92e01d9e71220ae40793eb5d6530c2039339bec`;
- `USTBOND.TR/USD`: metadata SHA256
  `b75bcc2b0f0e0b722d47004456da6af8a25978664647a9eee3c4ac9bc169ebee`.

Dollar-index tick metadata starts on 2017-12-01. The T-Bond minute history begins on
2018-12-18, and direct hourly probes show active ticks in 2019. The locked common
window is therefore 2019-01-01 through 2026-06-30, 90 calendar months per instrument.

The activity comparison uses the already verified 708,538-row XAUUSD M5 Bid/Ask
feature artifact with SHA256
`e587306f530a615dfdc6f869c4f79f881cfa0b572e078fd26d3c9995fbc66228`.

## Acquisition

Every calendar hour is requested from the official HTTPS Jetta endpoint. Raw JSON
bytes are retained outside Git. Acquisition uses at most four concurrent requests and
one retry after the initial attempt. A cached hour is resumed only after its hash,
schema, instrument identity, and timestamp range validate. Empty market-closed hours
are valid source responses; missing, malformed, cross-symbol, or out-of-hour responses
are not.

The decoder cumulatively applies the source `times`, `bids`, and `asks` arrays to the
base timestamp and prices. It preserves every source row in source order. Best-side
quote volume remains quote volume.

## Normalization

The only derived timeframe in V1 is UTC-aligned M5. Bid, Ask, and Mid OHLC are built
from completed source ticks. The combined feature artifact will retain native spread,
tick count, and quote-volume fields separately for each instrument. Two independent
normalizations must produce identical Parquet hashes.

## Source Gates

The source passes only when:

- both archived metadata files match their locked hashes and identities;
- all 180 instrument-month partitions contain every expected hourly response;
- every nonempty tick is finite, nonnegative in volume, inside its requested UTC hour,
  and has Ask greater than or equal to Bid;
- conflicting same-timestamp observations remain below 0.01% per instrument;
- each instrument is active on at least 80% of XAUUSD active source days in the common
  window;
- the two normalized rebuilds are byte-for-byte deterministic.

Failure is recorded as `INTRADAY_MACRO_SOURCE_INVALID` or
`INTRADAY_MACRO_SOURCE_PARTIAL_NOT_READY`. Only a complete pass may unlock a separate
event-census preregistration.

## Research Firewall

This packet authorizes source acquisition and source-quality measurement only. It does
not authorize joining the new features to gold returns, choosing strategy thresholds,
training a model, emitting Python predictions, consuming signals in an EA, or placing
broker orders.
