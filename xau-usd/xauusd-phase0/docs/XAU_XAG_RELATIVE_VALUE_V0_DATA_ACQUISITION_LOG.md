# xau_xag_relative_value_v0 Data Acquisition Log

Date: 2026-05-25

Purpose: document XAGUSD H1 data acquisition for the `xau_xag_relative_value_v0` research lane.

## Boundary

This data acquisition supports a blocked research-only candidate. It does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, trade permissions, or live/dry-run execution paths.

## Acquired Files

| Broker | Symbol | Source | Raw file | Processed file | Rows | Coverage |
| --- | --- | --- | --- | --- | ---: | --- |
| capital_com | XAGUSD | Existing Capital.com MT5 terminal, read-only Python export | `data/raw/capital_com/XAGUSD_H1_20160101_20181231_capital_com.csv` | `data/processed/bars/capital_com/XAGUSD/H1/XAGUSD_capital_com_H1_20160103_20181231.csv` | 17,623 raw rows | 2016-01-03 22:00 through 2018-12-31 17:00 bar starts |
| pepperstone | XAGUSD | Local MT5 terminal connected to `Pepperstone-Demo` | `data/raw/pepperstone/XAGUSD_H1_20190101_20211231_pepperstone.csv` | `data/processed/bars/pepperstone/XAGUSD/H1/XAGUSD_pepperstone_H1_20190102_20220101.csv` | 17,748 raw rows | 2019-01-02 01:00 through 2021-12-31 23:00 bar starts |
| dukascopy | XAGUSD | Dukascopy public historical data via `dukascopy-node` H1 bid candles | `data/raw/dukascopy/XAGUSD_H1_20220101_20241231_dukascopy.csv` | `data/processed/bars/dukascopy/XAGUSD/H1/XAGUSD_dukascopy_H1_20220103_20241231.csv` | 17,740 raw rows | 2022-01-03 00:00 through 2024-12-31 21:00 bar starts |

The small start/end boundary gaps are accepted by the existing H1 readiness gate and reflect normal market-closed periods near New Year.

## Blocker Resolution

The missing Capital.com XAGUSD H1 slice has been acquired. Broker-consistent XAGUSD H1 data is now present for all three matrix windows.

## Verification

Readiness command:

```powershell
.\.venv\Scripts\phase0.exe generate-xau-xag-relative-data-readiness
```

Current result:

```text
xau_xag_relative_value_v0 data readiness: PASS
Ready: 3/3 XAGUSD H1 set(s)
```
