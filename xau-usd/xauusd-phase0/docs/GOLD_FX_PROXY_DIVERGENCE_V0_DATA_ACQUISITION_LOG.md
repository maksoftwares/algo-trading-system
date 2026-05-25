# gold_fx_proxy_divergence_v0 Data Acquisition Log

Date: 2026-05-25

Purpose: document how the missing broker-consistent H1 proxy feeds were acquired for the `gold_fx_proxy_divergence_v0` research matrix.

## Boundary

This data acquisition unblocked a research-only Phase 0 candidate. It did not alter the active Phase 1 soak, Phase 2 readiness, approved expert list, trade permissions, or live/dry-run execution path.

## Acquired Files

| Broker | Symbol | Source | Raw file | Processed file | Rows | Coverage |
| --- | --- | --- | --- | --- | ---: | --- |
| pepperstone | EURUSD | Local MT5 terminal connected to `Pepperstone-Demo` | `data/raw/pepperstone/EURUSD_H1_20190101_20211231_pepperstone.csv` | `data/processed/bars/pepperstone/EURUSD/H1/EURUSD_pepperstone_H1_20190102_20220101.csv` | 18,694 raw rows | 2019-01-02 00:00 through 2021-12-31 23:00 bar starts |
| pepperstone | USDJPY | Local MT5 terminal connected to `Pepperstone-Demo` | `data/raw/pepperstone/USDJPY_H1_20190101_20211231_pepperstone.csv` | `data/processed/bars/pepperstone/USDJPY/H1/USDJPY_pepperstone_H1_20190102_20220101.csv` | 18,694 raw rows | 2019-01-02 00:00 through 2021-12-31 23:00 bar starts |
| dukascopy | EURUSD | Dukascopy public historical data via `dukascopy-node` H1 bid candles | `data/raw/dukascopy/EURUSD_H1_20220101_20241231_dukascopy.csv` | `data/processed/bars/dukascopy/EURUSD/H1/EURUSD_dukascopy_H1_20220103_20241231.csv` | 18,685 raw rows | 2022-01-03 00:00 through 2024-12-31 21:00 bar starts |
| dukascopy | USDJPY | Dukascopy public historical data via `dukascopy-node` H1 bid candles | `data/raw/dukascopy/USDJPY_H1_20220101_20241231_dukascopy.csv` | `data/processed/bars/dukascopy/USDJPY/H1/USDJPY_dukascopy_H1_20220103_20241231.csv` | 18,685 raw rows | 2022-01-03 00:00 through 2024-12-31 21:00 bar starts |

The small start/end boundary gaps are accepted by the existing H1 readiness gate and reflect normal market-closed periods near New Year.

## Verification

Readiness command:

```powershell
.\.venv\Scripts\phase0.exe generate-gold-fx-proxy-data-readiness
```

Result:

```text
gold_fx_proxy_divergence_v0 data readiness: PASS
Ready: 6/6 proxy H1 set(s)
```

Authoritative Phase 0 research matrix was then allowed to run for this candidate only.
