# Phase 0 Data Folders

Phase 0 expects broker tick exports under `data/raw/`, normalized tick files under `data/processed/ticks/`, and generated bars under `data/processed/bars/`.

## Raw Input Layout

Place raw CSV exports in broker-specific folders:

```text
data/raw/capital_com/
data/raw/pepperstone/
data/raw/dukascopy/
```

Raw files may use broker-native column names. The normalizer recognizes common timestamp, bid, ask, and volume aliases, then writes the locked Phase 0 schema.
Broker OHLC bar exports are also accepted. Use filenames that include the symbol and timeframe, for example `XAUUSD_M5_2016_2025_capital.csv`.
`mt5/PassiveBarExporter_Phase0.mq5` can export MT5 history into compatible OHLC files. Use it only for passive file export, then copy completed CSVs into `data/raw/{broker}/`.

## Processed Output Layout

Normalized ticks are written to:

```text
data/processed/ticks/{broker}/{symbol}/
```

Bars are written to:

```text
data/processed/bars/{broker}/{symbol}/{timeframe}/
```

Bar timestamps use the Phase 0 convention: `timestamp_utc` equals `bar_end_utc`.
Processed bar files must be sorted ascending, duplicate-free by `timestamp_utc`, and each row's `broker`, `symbol`, and `timeframe` values must match its folder.
Each row's `bar_end_utc - bar_start_utc` must match its declared timeframe.
Real-data runs load and validate every CSV in each required timeframe folder as one combined bar stream, so broker exports may be split into date chunks as long as the combined stream is continuous and duplicate-free.
Overlapping split files are rejected because duplicate `timestamp_utc` values would make the backtest path ambiguous.

## Commands

```powershell
python -m phase0 validate-data --broker capital_com --symbol XAUUSD
python -m phase0 normalize-data --broker capital_com --symbol XAUUSD
python -m phase0 build-bars --broker capital_com --symbol XAUUSD --timeframes M1,M5,M15,H1,H4,D1
python -m phase0 normalize-bars --broker capital_com --symbol XAUUSD --timeframe M5
python -m phase0 generate-data-requirements
python -m phase0 import-required-bars
python -m phase0 import-required-bars --fail-on-missing
python -m phase0 generate-data-manifest
python -m phase0 generate-data-readiness
python -m phase0 check-data-availability
```

These commands write validation artifacts and `outputs/manifests/PHASE0_DATA_MANIFEST.md`.
Use `generate-data-requirements` to write `outputs/manifests/PHASE0_DATA_REQUIREMENTS.csv`, a broker/symbol/timeframe acquisition checklist with required coverage windows and suggested raw filenames.
Use `normalize-data` plus `build-bars` for tick exports. Use `normalize-bars` for direct OHLC bar exports from MT5 History Center or a broker portal. By default, source bar timestamps are interpreted as bar starts; pass `--timestamp-is bar_end` only for exports that already use bar-close timestamps.
If a direct bar export filename does not include the symbol and timeframe, pass `--input-file path\to\export.csv` to `normalize-bars`.
For MT5 server-time exports, confirm the UTC offset before import. If the broker changes offset across the requested history window, export separate date ranges with the correct fixed offset or prefer a broker portal export with UTC timestamps.
Use `import-required-bars` after placing bar CSVs in `data/raw/{broker}/`; it batch-imports every required broker/symbol/timeframe whose filename includes both the symbol and timeframe, then writes `outputs/manifests/PHASE0_BAR_IMPORT_REPORT.csv`.
Pass `--fail-on-missing` when using `import-required-bars` in automation so missing required exports return a non-zero exit code after reports are written.
Use `generate-data-manifest` to seal `outputs/manifests/PHASE0_DATA_MANIFEST.md` across all required broker/symbol inputs, including raw and processed file SHA256 values.
`check-data-availability` requires each mandatory broker/symbol/timeframe folder to contain at least one non-empty bar CSV with the locked Phase 0 bar schema, enough `bar_start_utc` / `bar_end_utc` coverage for the configured matrix, decile, and multi-symbol windows, and no large internal timestamp gaps for the declared timeframe.
`generate-data-readiness` writes `outputs/manifests/PHASE0_DATA_READINESS.md` with the exact missing, malformed, or coverage-blocked broker/symbol/timeframe sets.

## Snapshot Policy

Raw tick data is excluded from snapshot zip files by default. Use this only when an audit requires bundling raw market data:

```powershell
python -m phase0 generate-snapshot --include-raw-data
```
