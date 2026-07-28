# EURUSD Neutral precious-metals source audit

## Source

The source uses Dukascopy's public Jetta tick endpoint:

`https://jetta.dukascopy.com/v1/ticks/{INSTRUMENT}/{YEAR}/{MONTH}/{DAY}/{HOUR}`

No account, API key, OTP, or paid entitlement is required. The instruments are
`XAU-USD` and `XAG-USD`.

The source was discovered and verified from the existing acquisition
manifests. A direct missing-hour request returned HTTP 200 and the expected
timestamped bid/ask delta arrays.

## Scope

Only hours needed by the locked Neutral first-hour clocks were processed. For
each of 642 Neutral dates, the required set is:

- prior UTC date 22:00;
- prior UTC date 23:00;
- current UTC date 00:00.

This creates 1,926 distinct required hours for each metal. XAUUSD used 1,926
existing raw files. XAGUSD used 1,488 existing files and 438 newly downloaded
responses. Each metal contained 235 empty market-closed hours and 1,691
populated hours.

## Normalization

Tick times and bid/ask price changes are cumulative deltas from the hourly
base values. Prices are rounded to the provider multiplier before aggregation.
Ticks are resampled into left-labelled M5 bid/ask OHLC bars. An M5 row is
usable only at its timestamp plus five minutes.

The normalized source contains 40,481 M5 rows from
2019-01-24 23:00 UTC through 2026-06-30 00:55 UTC.

`D:/AlgoTradingData/research/eurusd-neutral-precious-metals-v1/PRECIOUS_METALS_FIRST_HOUR_M5.parquet`

SHA-256:

`64fbf4e9e0a77b37e738db48a256c230873fce29a532b87c8ed55148c728982f`

Manifest SHA-256:

`b2a14d3cf81a156016bcef642e063892d31751edefb84546f6612a25490aac83`

Raw-response chain SHA-256:

`5a13466c55b0b06237149c4d48bc08520c4ce1d6ac1fdb449d4e3ee61d41084b`

## Reproducibility and limitations

A network-disabled rebuild reproduced the same source chain, row count, and
parquet hash.

The quotes are Dukascopy OTC/CFD bid/ask ticks, not exchange metal futures or
central-limit-order-book trades. They are suitable as synchronized price
proxies, not as claims about centralized volume or order flow.
