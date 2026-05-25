# Gold FX Proxy Export Presets

These MT5 presets collect the four missing H1 proxy feeds required by `gold_fx_proxy_divergence_v0`.

Use them with:

```text
mt5/PassiveBarExporter_Phase0.mq5
```

## Presets

| Preset | Broker | Symbol | Window |
| --- | --- | --- | --- |
| `EURUSD_H1_20190101_20211231_pepperstone.set` | pepperstone | EURUSD | 2019.01.01 00:00 through 2021.12.31 23:59 |
| `USDJPY_H1_20190101_20211231_pepperstone.set` | pepperstone | USDJPY | 2019.01.01 00:00 through 2021.12.31 23:59 |
| `EURUSD_H1_20220101_20241231_dukascopy.set` | dukascopy | EURUSD | 2022.01.01 00:00 through 2024.12.31 23:59 |
| `USDJPY_H1_20220101_20241231_dukascopy.set` | dukascopy | USDJPY | 2022.01.01 00:00 through 2024.12.31 23:59 |

## Offset Check

The presets use:

```text
InpServerToUtcOffsetHours=0
```

Keep this only when the exported MT5 server timestamps are already UTC-aligned. If the broker server uses a fixed offset, adjust the preset before export. If the broker offset changes during daylight saving periods, export separate date ranges with the correct fixed offset for each range or use broker portal data with UTC timestamps.

## Expected Raw Files

Copy completed exports into:

```text
data/raw/pepperstone/EURUSD_H1_20190101_20211231_pepperstone.csv
data/raw/pepperstone/USDJPY_H1_20190101_20211231_pepperstone.csv
data/raw/dukascopy/EURUSD_H1_20220101_20241231_dukascopy.csv
data/raw/dukascopy/USDJPY_H1_20220101_20241231_dukascopy.csv
```

Then normalize:

```powershell
.\.venv\Scripts\phase0.exe normalize-bars --broker pepperstone --symbol EURUSD --timeframe H1 --input-file data\raw\pepperstone\EURUSD_H1_20190101_20211231_pepperstone.csv
.\.venv\Scripts\phase0.exe normalize-bars --broker pepperstone --symbol USDJPY --timeframe H1 --input-file data\raw\pepperstone\USDJPY_H1_20190101_20211231_pepperstone.csv
.\.venv\Scripts\phase0.exe normalize-bars --broker dukascopy --symbol EURUSD --timeframe H1 --input-file data\raw\dukascopy\EURUSD_H1_20220101_20241231_dukascopy.csv
.\.venv\Scripts\phase0.exe normalize-bars --broker dukascopy --symbol USDJPY --timeframe H1 --input-file data\raw\dukascopy\USDJPY_H1_20220101_20241231_dukascopy.csv
```

Finally verify:

```powershell
.\.venv\Scripts\phase0.exe generate-gold-fx-proxy-data-readiness
```
