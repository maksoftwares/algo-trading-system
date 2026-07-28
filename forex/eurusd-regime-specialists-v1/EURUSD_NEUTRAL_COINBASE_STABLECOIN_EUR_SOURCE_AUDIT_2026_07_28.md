# EURUSD Neutral Coinbase stablecoin/EUR source audit

## Source decision

`USDC-EUR` and `USDT-EUR` on Coinbase Exchange are accepted as a genuinely
new, login-free decision-time source for one bounded Neutral campaign.

They are stablecoin/fiat order books, not broker EURUSD bars and not the
previously inspected Kraken EUR/USD or Binance EURUSDT sources. Both products
were reported `online` by the public product endpoint when acquired.

Official documentation:

- product metadata:
  <https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-single-product>
- historical product candles:
  <https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles>
- public REST rate limit:
  <https://docs.cdp.coinbase.com/exchange/rest-api/rate-limits>

The candle endpoint is public and requires no authentication. Coinbase
documents up to 300 candles per request, supports five-minute granularity,
and warns that historical intervals can be missing when there were no ticks.
The downloader therefore never fills or interpolates a missing candle.

## Outcome-blind acquisition

Only the hour needed for each existing Neutral decision date was requested:
23:45 UTC on the preceding date through 00:45 UTC on the decision date. The
normalized source retains the twelve possible completed M5 candles from
23:45 through 00:40.

| Item | Value |
|---|---:|
| Neutral dates requested | 334 |
| Products | 2 |
| Raw candle responses | 668 |
| Normalized M5 rows | 7,260 |
| Parquet bytes | 243,976 |
| Dates complete at both products | 180 |

Coverage:

| Product | Rows | Complete 12-bar positive-volume dates | Missing required bars | Zero-volume bars |
|---|---:|---:|---:|---:|
| USDC-EUR | 3,501 | 228 | 507 | 0 |
| USDT-EUR | 3,759 | 225 | 249 | 0 |

Individual decision clocks may still be valid on a date that is not complete
at all four clocks. Each decision independently requires the immediately
preceding three consecutive positive-volume candles at both products.

## Integrity

Outside-Git root:

`D:/AlgoTradingData/research/eurusd-neutral-coinbase-stablecoin-eur-v1`

Pinned artifacts:

- raw response chain:
  `7f6c307db8675ea688ee31d2a5665424d30bf2dec3969eeb8105dd1b427eae11`
- product metadata chain:
  `fa7bb9d45bcec9e84c6a8130be230415cd6db395034d59ecd79b0e30965b8f52`
- normalized Parquet:
  `d2f978e185534417a2f3f237983a9f97b90084b3d174b114e2f9df105130268a`
- deterministic manifest:
  `37b2dc54439a91dedc42919a7a80604b48fdffe6a7345397ca2b404828490090`

A cache-only rebuild reproduced the manifest and Parquet hashes exactly.

## Outcome-blind source behavior

At 963 parent decisions, both products have three consecutive completed
positive-volume candles. A volume-weighted candle-direction pressure is
defined in EUR terms by reversing the sign of each stablecoin/EUR candle.

- pressure correlation between products: 0.3741;
- return correlation between products: 0.8091;
- pressure-sign agreement: 63.76%;
- each product's pressure sign agrees with its own 15-minute return sign on
  75.29% of valid decisions.

The prices are strongly related, as expected, while volume-weighted pressure
contains materially different product-specific information. No EURUSD trade
outcome or oracle membership was loaded for these measurements.

## Limitations

- Candles expose OHLC and base volume, not aggressor-side or trade-count
  fields.
- A candle-direction signed-volume proxy is not true taker flow.
- Stablecoin demand, venue access, and product microstructure can differ from
  OTC EURUSD.
- Early coverage is sparse; missing observations remain missing.
- Existing EURUSD history has already been inspected by other campaigns, so a
  result is adaptive historical research even though this source is new.
