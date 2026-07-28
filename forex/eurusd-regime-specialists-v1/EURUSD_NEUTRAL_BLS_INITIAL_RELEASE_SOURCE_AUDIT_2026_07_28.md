# EURUSD Neutral BLS initial-release source audit

## Result

`SOURCE_ACCEPTED_FOR_POINT_IN_TIME_CAUSAL_RESEARCH`

A login-free, revision-safe U.S. macro source is now available without the
failed CME signup or a FRED API key. It contains the value actually printed in
each archived Bureau of Labor Statistics PDF at the corresponding release
time, rather than the latest revised database value.

This audit authorizes the source for a new outcome-locked research rule. It
does not authorize a trade, a backtest pass, demo use, or live use.

## Source and coverage

The event clock comes from the already audited Dukascopy calendar archive.
For each exact CPI, PPI, and Nonfarm Payroll event date, the pipeline downloads
the corresponding official BLS archived PDF and extracts the first-page
headline metric.

| Family | Expected event dates | Parsed PDFs | Coverage |
|---|---:|---:|---:|
| CPI | 90 | 89 | 98.89% |
| PPI | 92 | 89 | 96.74% |
| Nonfarm Payrolls | 92 | 89 | 96.74% |
| Total | 274 | 267 | 97.45% |

Coverage runs from 4 January 2019 through 11 June 2026. Each family has 12
rows in every complete year from 2019 through 2024. The partial 2025-2026
counts reflect seven scheduled calendar dates for which the corresponding
official archive URL returned 404; those dates remain missing and are not
filled from revised databases.

There are zero duplicate family/release-date rows, zero duplicate
family/event-time rows, and zero parser errors among downloaded PDFs.

## Parsed metrics

- CPI: first-reported, seasonally adjusted monthly headline CPI change.
- PPI: first-reported, seasonally adjusted monthly final-demand PPI change.
- NFP: first-reported total nonfarm payroll monthly change, normalized to
  persons.

The parser explicitly handles positive and negative direction verbs,
unchanged releases, parenthetical "changed little" values, PDF word-spacing
artifacts, and thousand/million units.

The COVID-19 unit audit reproduces:

| Release | Initial NFP value |
|---|---:|
| 3 April 2020 | -701,000 |
| 8 May 2020 | -20,500,000 |
| 5 June 2020 | +2,500,000 |

This check prevents the April 2020 phrase "20.5 million" from being silently
treated as 20 persons.

## Outcome-blind directional capacity

Comparing each initial value only with the preceding initial value from the
same family gives balanced signs before any regime or trade filter:

| Family | Acceleration | Deceleration | Equal |
|---|---:|---:|---:|
| CPI | 39 | 39 | 10 |
| PPI | 45 | 40 | 3 |
| NFP | 40 | 47 | 1 |

These counts are source diagnostics only. No EURUSD return, stop/target path,
oracle membership, year result, or profit factor was loaded.

## Causality boundary

At a release timestamp, the current archived headline value and every earlier
archived headline value are known. Later revisions are not used. The proposed
research signal may therefore compare current initial value with the previous
same-family initial value.

This is a macro *acceleration* signal, not a consensus surprise. It should not
be described as actual-minus-forecast, and no archived Dukascopy actual,
forecast, previous, impact, normalized, historical-count, or effect field may
enter the strategy.

## PDF verification

The representative CPI PDF was checked in three ways:

1. `pdfinfo` verified a valid, unencrypted 38-page BLS release.
2. `pypdf` extracted the embargo time, release heading, and headline monthly
   value.
3. A Poppler rendering of page 1 was visually inspected and showed a legible
   BLS release with the same 0.1% August 2019 headline value.

## Integrity

Normalized source:

`D:/AlgoTradingData/research/eurusd-neutral-bls-initial-release-v1/BLS_INITIAL_RELEASES.parquet`

SHA-256:

`1fa88ef36dda61dba5ab711179283d6a2e77c11aaddde9f326f5444b5c1791fc`

Manifest SHA-256:

`7971ec2175f0958e80bd3e99dbe85641626cc2fc353f9bee1bf6808f6c8734e7`

Raw PDF chain SHA-256:

`05d06e91e43b942bf9a200faa6e5777d7f271255fbed09ba30e41612a3cf3a34`

Downloader SHA-256:

`7cf02a8ec4222d7c1d80cc956802473388c850fce227ea917aeae3a018e8a792`

Parser tests SHA-256:

`8e90d65c72a444b396ee3960365bd0d7bdebd9ab6d3f15256ec7b379d68aaa13`
