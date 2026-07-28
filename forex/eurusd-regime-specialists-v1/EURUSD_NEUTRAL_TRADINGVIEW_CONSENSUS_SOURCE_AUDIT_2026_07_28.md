# EURUSD Neutral TradingView consensus source audit

## Source decision

The public TradingView Economic Calendar JSON service is accepted as a
login-free source of historical CPI, PPI, and NFP consensus forecasts for one
bounded adaptive Regime 1 research campaign.

Provider page:

`https://www.tradingview.com/economic-calendar/`

Public JSON service:

`https://economic-calendar.tradingview.com/events`

The service supplies UTC event time, stable event ID, ticker, actual, forecast,
previous, importance, reference period, and agency metadata without an account,
API key, OTP, browser cookie, or form submission.

This acceptance is deliberately narrower than a pristine point-in-time claim.
The historical API responses were retrieved after the events. TradingView
defines the forecast as the expected value used to compare with the actual,
but the responses are not independently archived pre-release snapshots.
Historical results therefore remain adaptive research; every future forecast
must be captured and checksum-pinned before its release timestamp.

## Frozen series

Only three exact U.S. tickers are retained:

| Family | TradingView ticker | Official metric |
|---|---|---|
| CPI | `ECONOMICS:USIRMM` | headline CPI monthly change |
| PPI | `ECONOMICS:USPPIMM` | final-demand PPI monthly change |
| NFP | `ECONOMICS:USNFP` | total nonfarm payroll monthly change |

Core variants, year-over-year variants, speeches, derived releases, and every
other calendar series are excluded.

## Official-initial-print reconciliation

TradingView is never trusted as the actual-value authority. Each calendar row
must match both the UTC timestamp and the initial value parsed from the
checksum-pinned official BLS release PDF. Duplicate same-time rows are resolved
only by that equality; unmatched, revised, missing, or ambiguous rows are
quarantined.

| Family | Official BLS releases | Exact actual matches | Match rate | Forecast coverage of matches |
|---|---:|---:|---:|---:|
| CPI | 89 | 88 | 98.88% | 100.00% |
| PPI | 89 | 88 | 98.88% | 100.00% |
| NFP | 89 | 86 | 96.63% | 100.00% |
| Total | 267 | 262 | 98.13% | 100.00% |

Five official rows are excluded:

- PPI on 2021-04-09 is absent from the provider response;
- NFP on 2020-06-05, 2020-08-07, and 2020-09-04 has a provider actual that
  differs from the official initial PDF, consistent with later revision or
  alternate headline precision;
- CPI on 2025-12-18 has no provider actual.

No forecast from those rows is recovered, inferred, or copied from another
calendar.

The known Dukascopy corruption example also passes: for the 2024-01-05 NFP
release, TradingView records 216K actual, 170K forecast, and 173K previous,
matching the contemporaneous figures that exposed Dukascopy's invalid -29K
historical forecast.

## Outcome-blind source characteristics

The 262 accepted releases contain:

| Family | Above forecast | Below forecast | Equal |
|---|---:|---:|---:|
| CPI | 31 | 27 | 30 |
| PPI | 40 | 37 | 11 |
| NFP | 54 | 31 | 1 |

These are source-level signs only. No EURUSD return, exit, oracle membership,
or strategy candidate count was loaded during source construction.

## Acquisition and integrity

Coverage consists of 90 non-overlapping monthly responses from January 2019
through June 2026. Requests use a public GET endpoint with a conservative
inter-request delay.

Outside-Git root:

`D:/AlgoTradingData/research/eurusd-neutral-tradingview-consensus-v1`

Pinned artifacts:

- raw response files: 90;
- raw bytes: 13,071,342;
- raw response chain SHA-256:
  `d9558ac0016e94b7aaf6a7db19a1bec0540d945b420026c6eb94f7fb6c3f83ce`;
- normalized Parquet SHA-256:
  `90ee94228f7b9be6ca85de2ba1c1483a1d3d04957e4ab98c87134fcb432c4793`;
- manifest SHA-256:
  `3506cd392d9118c392c2d51e4fe00b24b43163dd3e874355faf012c3470a7e6e`.

A cache-only rebuild reproduced both the Parquet and manifest hashes exactly.

## Limitations and permitted use

- Forecasts are provider historical records retrieved after release, not
  independently timestamped pre-release files.
- Provider definitions and consensus methodology are not fully documented.
- The BLS equality gate validates the release identity and initial actual, not
  the forecast's collection methodology.
- Missing or mismatched releases can reduce sample size.
- All 2019-June 2026 EURUSD history has already influenced this research
  program and is not pristine out-of-sample evidence.

Permitted use is limited to a fully preregistered adaptive historical test
whose future equivalent captures the provider forecast before release.
Historical success alone cannot authorize demo or live trading.
