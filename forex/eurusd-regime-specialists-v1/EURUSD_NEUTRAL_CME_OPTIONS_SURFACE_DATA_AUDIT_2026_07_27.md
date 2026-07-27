# EURUSD Neutral CME options-surface data audit

Date: 2026-07-27

Decision: `DATA_ROUTE_VALID_BUT_HISTORICAL_ACCESS_BLOCKED`

## What was established

The exact official dataset exists and is structurally sufficient for a
non-proxy EUR/USD skew specialist:

| Item | Verified value |
|---|---|
| Dataset | `EOD_XCME_EUU_OPT_0` |
| Product | Premium Quoted European Style Options on Euro/US Dollar Futures |
| Dataset ID | `0e3d0545a67b165bfb2ea9adf6f3f0c6` |
| Catalog range | 2016-08-09 to 2026-07-24 |
| Files | 7,524 |
| Frequency / format | Daily / gzip |
| Final release | 10:00 CT on T+1 |
| Complete-history list price observed | USD 2,249 |

The downloadable public schema has 71 columns. The required fields are
explicit rather than inferred from PDF layout: trade date, put/call,
strike, expiry, settlement, open interest, total volume, delta, and
implied volatility.

The public sample `xcme-eode-euu-opt-20250701-sample.csv.gz` was fetched
and decompressed in memory. It contains 100 records, 89 calls and 11 puts,
and 11 same-strike call/put pairs. All sample delta and implied-volatility
cells are empty, so the frozen parser includes put-call-parity forward
inference and Black-76 inversion. This is an outcome-blind format
fallback, not a trading-rule repair.

The schema and sample were also preserved outside Git at
`D:/AlgoTradingData/research/eurusd-neutral-cme-options-surface-v1/public-sample/`.
Their SHA-256 values are:

- schema: `51fb3c4fea80440367dc113735275686334d4ea6f551160b494705a173617e09`;
- sample: `1b590c32102344a00a758bf001fb3b700b5e4a31f82c998729ba6d11bca2135e`.

## Why the free bulletin is not a historical substitute

CME's Daily Bulletin page exposes the current Section 39 PDF and that PDF
contains Euro FX futures settlements plus option strike, settlement,
delta, volume, and open-interest rows.

However, CME's Daily Bulletin dataset documentation says files are
available for the top day only and are overwritten when the next day's
files are posted. It therefore cannot reconstruct 2019-2026 after the
fact. The two December 2023 files are samples, not a retained research
archive.

## What is now frozen

- a strict EUU EOD parser;
- explicit call/put and strike normalization;
- parity-based forward and discount inference;
- reported-IV use with Black-76 fallback;
- 20-45 DTE, closest-to-30-day expiry selection;
- nearest 25-delta call and put with a fixed 0.08 maximum miss;
- sign-only RR25 direction;
- final-file-only availability and next-UTC-midnight lag;
- unchanged 4-pip / 1.50R / 12-hour execution and chronological gates.

Unit tests validate schema enforcement, parity recovery, skew direction,
and decision-time lag without using any oracle outcome.

## Required handoff

Supply licensed final files for `EOD_XCME_EUU_OPT_0` covering
2019-01-01 through 2026-06-30, plus the actual file publication timestamp
or delivery manifest for every trade date.

The files should be placed below:

```text
D:/AlgoTradingData/research/eurusd-neutral-cme-options-surface-v1/
  EOD_XCME_EUU_OPT_0/
```

After acquisition, the next steps are mechanical:

1. hash every source file;
2. run the outcome-blind coverage and surface census;
3. freeze the exact candidate ledger;
4. execute 2019-2022 development once;
5. if and only if development passes, open 2023-2026 H1 chronological
   outcomes and oracle imitation metrics.

Until that handoff, Regime 1 remains `CASH`. Buying data was not
authorized and no purchase or cart action was performed.
