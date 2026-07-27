# EURUSD Neutral CME SPAN free-source audit

Date: 2026-07-27

Decision: `FREE_ROUTE_VALID; FULL_ARCHIVE_AWAITS_CME_LOGIN`

## Outcome

CME DataMine has an official, zero-cost historical route that contains
the exact `EUU` long-dated EUR/USD option surface needed by the frozen
Regime 1 experiment:

| Item | Verified value |
|---|---|
| Dataset | All CME Group Exchanges - SPAN Risk Parameter Files |
| Dataset code | `SPAN_ALL_GRP_EXCG` |
| Dataset ID | `aadb2ba35cb546798659c206bb63dc9a` |
| Catalog range observed | 2021-11-19 to 2026-07-27 |
| Files observed | 35,682 |
| Format / frequency | PA2/XML in daily ZIP files |
| Complete-history price observed | USD 0.00 |
| Permission metadata | `permissioned=N`, `restricted=N` |

The public sample and dataset metadata were downloaded to:

```text
D:/AlgoTradingData/research/eurusd-neutral-free-source-audit-v1/
```

The sample ZIP is 22,219,874 bytes and has SHA-256:

```text
4d27adfd8841528f3eb25a698cb8dd7ae7e0df63e113a0bc464a19622d01f6f8
```

It expands to one 224,932,928-byte PA2/XML `.spn` file.

## Exact EUU content verified

The sample's `EUU` product has:

- product ID `22181`;
- name `EUR/USD OPTIONS Long dated`;
- European exercise;
- underlying Euro FX futures product `EC`;
- 20 expiries and 2,562 option contracts;
- expiry, strike, call/put, full premium, precise delta, option
  volatility, series volatility, and underlying-contract identifiers.

For the 28-day expiry on 2025-07-18, the nearest 25-delta contracts are:

| Side | Strike | Delta | Premium | Option volatility |
|---|---:|---:|---:|---:|
| Call | 1.1875 | 0.245710 | 0.00390 | 0.082977 |
| Put | 1.1525 | -0.264750 | 0.00420 | 0.080780 |

This is enough to build the preregistered 25-delta risk reversal without
oracle outcomes. Premium-based Black-76 inversion remains available when
option volatility is absent.

## Safety boundary

The public sample is an `a6` file with `isSetl=0`. It validates only the
format and field mapping. It is not admitted as historical settlement
evidence. The new parser rejects any file whose `isSetl` value is not
`1` unless a caller explicitly selects sample-audit mode.

Cabinet or alternate quote records (`pq != 0`) are also rejected rather
than treated as full option premiums.

## Remaining access step

CME decommissioned anonymous public FTP distribution in July 2025.
DataMine now requires a CME Login ID and completion of its self-service
licence workflow even when the cart total is USD 0.00.

The full archive cannot be downloaded anonymously. The user must sign in
to the CME DataMine tab, complete the USD 0.00 checkout/licence, and then
return control. No purchase, account creation, credential entry, or
licence acceptance was performed by Codex.

Once entitlement is present, the remaining work is mechanical:

1. download and hash the settlement/complete-cycle files;
2. run the outcome-blind EUU coverage census;
3. freeze a revised chronology beginning 2021-11-19;
4. create the candidate ledger without outcomes;
5. run development first and open forward windows only if it passes.

The existing paid `EOD_XCME_EUU_OPT_0` preregistration remains unchanged
and hash-locked. This free-source route is a separate acquisition and
normalization lane.

## EURUSD spot-data status

Spot execution data is not the current blocker. A Dukascopy-derived
bid/ask M5 cache is already present outside Git at:

```text
D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/
  research/eurusd-regime-specialists-v2/
  EURUSD_M5_BIDASK_2024_07_2026_06.csv.gz
```

It covers 2024-07-01 through 2026-06-30, contains 149,326 M5 rows built
from 17,518 hourly source files, and has SHA-256:

```text
c347517be57f8147b5461d5d5ccd3c7ea6f683516a54050f06ea103e50cc0a61
```
