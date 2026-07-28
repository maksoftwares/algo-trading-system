# EURUSD Neutral Binance EURUSDT source audit

Date: 2026-07-28

Decision: `SOURCE_ACCEPTED_FOR_FROZEN_CAUSAL_TEST`

## Why this source

The CME SPAN signup could not deliver the user's OTP. This audit therefore
looked for a login-free source containing genuinely executed directional
flow rather than another transformation of Dukascopy quotes.

Binance maintains an [official public-data archive](https://github.com/binance/binance-public-data)
that requires no authentication. Its spot kline schema contains:

- traded base and quote volume;
- number of executed trades;
- taker-buy base and quote volume;
- open, high, low, and close;
- exchange timestamps.

The source is not EURUSD interbank order flow. EURUSDT is a crypto-venue
proxy whose base asset is EUR and quote asset is USDT. Its taker-buy sign is
nevertheless a genuinely different, transaction-derived decision-time
feature: buyer-initiated EUR flow is positive and seller-initiated EUR flow
is negative.

## Acquisition

`download_neutral_binance_eurusdt.py` downloaded monthly 5-minute spot kline
archives for `EURUSDT` from 2020-01 through 2026-06.

Each archive and its official `.CHECKSUM` file were acquired directly from:

`https://data.binance.vision/data/spot/monthly/klines/EURUSDT/5m/`

The downloader:

- validates every official SHA-256 checksum before accepting an archive;
- requires exactly one CSV per archive;
- validates five-minute UTC alignment, unique timestamps, OHLC geometry,
  nonnegative executed volume and trade count, and taker-buy volume not
  exceeding total volume;
- handles Binance's documented switch from millisecond to microsecond spot
  timestamps on 2025-01-01;
- derives taker-sell quote volume and normalized taker imbalance;
- writes one source-hashed Parquet file and a detailed manifest.

## Coverage and integrity

| Field | Result |
|---|---:|
| Monthly archives | 78 |
| Official checksum failures | 0 |
| Archive chain SHA-256 | `aa380ef80b3144873d089972d85699844904874bee3717bd3e8a894b626a3952` |
| Normalized rows | 682,290 |
| First M5 open | 2020-01-03 08:00 UTC |
| Last M5 open | 2026-06-30 23:55 UTC |
| Millisecond archives | 60 |
| Microsecond archives | 18 |
| Missing five-minute intervals | 462 |
| Zero quote-volume rows | 20,231 |
| Normalized SHA-256 | `7ba02f67f3278038a81095b90bceee402ffdce6bd4fb5d465b7c0a6e408aeb41` |

The 462 missing intervals are 0.068% of the expected sequence from first to
last timestamp. The strategy does not forward-fill them. A signal requires
three consecutive completed M5 bars and positive aggregate quote volume.

## Outcome-blind strategy coverage

Before reading EURUSD outcomes:

- the fixed parent schedule contained 2,568 paired decision points;
- 2,118 had valid completed EURUSDT flow;
- 450 were missing or invalid, mostly before the 2020 listing start;
- requiring all four clocks left 519 complete Neutral dates and 2,076
  forced trade candidates;
- every retained date has exactly four decisions.

No EURUSD result, target-first label, oracle membership, direction reversal,
flow threshold, or subgroup was inspected or selected during this census.

## Limitations

- EURUSDT trades on one crypto venue and is not a consolidated EUR/USD
  foreign-exchange tape.
- USDT basis and venue-specific participant behavior may dominate the
  signal.
- Early history is relatively illiquid, as shown by zero-volume bars.
- Historical source availability does not make the subsequent adaptive
  research pristine out-of-sample.

These limitations are handled by conservative source labeling, strict
completed-bar timing, no missing-data fill, chronological windows, exact
cost execution, and a required post-lock prospective sample for any
historical pass.
