# EURUSD Neutral Kraken EUR/USD executed-flow source audit

Date: 2026-07-28

Decision: `SOURCE_ACCEPTED_FOR_ONE_FROZEN_MULTIVENUE_TEST`

## Source

Kraken exposes a public, unauthenticated EUR/USD Trades endpoint. Its
[official API documentation](https://docs.kraken.com/api-reference/market-data/get-recent-trades)
shows exact trade time, price, volume, reported buy/sell side, market/limit
order type, and trade ID. Kraken states that one public request per second or
less remains within its
[REST market-data rate limits](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-).

Unlike Binance EURUSDT, this venue trades the actual EUR/USD currency pair.
It is still a single electronic venue rather than consolidated interbank FX.

## Outcome-blind acquisition

The downloader read only the already frozen four-clock Neutral timestamps;
it did not read EURUSD outcomes, target-first labels, oracle membership, or
exit timestamps.

For each candidate date it requested only trades from 23:45 UTC on the
previous date through 00:45 UTC on the entry date. This is exactly the
decision-time hour needed for the four prior-15-minute signals at 00:00,
00:15, 00:30, and 00:45 UTC. It never requested the future EURUSD holding
path.

The downloader:

- uses the login-free `public/Trades` endpoint with a 1.05-second minimum
  interval;
- paginates from Kraken's nanosecond continuation cursor until the required
  hour is covered;
- validates increasing trade IDs and timestamps, positive price and volume,
  and the expected reported-side and order-type values;
- writes every raw JSON response atomically and caches it by date and page;
- aggregates trades into five-minute OHLC and executed buy/sell volume;
- does not synthesize or forward-fill any empty bar;
- hash-chains all raw pages and writes a deterministic source manifest.

## Integrity and coverage

| Field | Result |
|---|---:|
| Outcome-blind Neutral dates requested | 518 |
| Raw API pages | 699 |
| Raw page chain SHA-256 | `8c871c2e4647900d6b719650b18bfd01a50c393e929fbff6bd483126acd3d9ce` |
| Trades inside required windows | 398,079 |
| First retained trade | 2020-03-26 00:40:09 UTC |
| Last retained trade | 2026-06-30 00:44:48 UTC |
| Populated M5 bars | 5,958 |
| Missing required M5 buckets | 258 |
| Dates with all 12 required bars | 453 |
| Normalized Parquet bytes | 692,283 |
| Normalized Parquet SHA-256 | `bc1ccfeb50f227b86f187f9f5f28f5ca4e566c3cf9576a600c207c1a3a1a8295` |
| Manifest SHA-256 | `b5378ead91fe5a786b1cb5a3fe4610bd92f6e577f3b3b7f5f2e736aa897c5aac` |

Two complete cache-only rebuilds produced identical manifest and Parquet
hashes.

## Relationship to the existing venue

Before outcomes, the 453 complete Kraken dates also had valid Binance flow.
Across their 1,812 decision points:

- Kraken/Binance flow-imbalance correlation was 0.0603;
- 15-minute return correlation was 0.4428;
- flow signs agreed on 51.93% of decisions;
- the frozen equal-weight score predicted LONG on 51.77%;
- no exact score tie occurred.

The very low imbalance correlation establishes that Kraken adds a materially
different executed-flow observation rather than duplicating Binance.

## Limitations

- Kraken-reported side is an exchange field, but this audit does not claim
  the venue represents the consolidated institutional EUR/USD market.
- Early EUR/USD venue liquidity was sparse; 65 candidate dates fail the
  strict all-12-bar requirement.
- The source was acquired after other EURUSD outcomes were already inspected,
  so the next campaign remains adaptive historical research.
- Historical success, if any, would still require a new prospective sample
  before broker use.
