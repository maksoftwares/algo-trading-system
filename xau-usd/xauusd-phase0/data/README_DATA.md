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

## Commands

```powershell
python -m phase0 validate-data --broker capital_com --symbol XAUUSD
python -m phase0 normalize-data --broker capital_com --symbol XAUUSD
python -m phase0 build-bars --broker capital_com --symbol XAUUSD --timeframes M1,M5,M15,H1,H4,D1
python -m phase0 generate-data-readiness
python -m phase0 check-data-availability
```

These commands write validation artifacts and `outputs/manifests/PHASE0_DATA_MANIFEST.md`.
`check-data-availability` requires each mandatory broker/symbol/timeframe folder to contain at least one non-empty bar CSV with the locked Phase 0 bar schema.
`generate-data-readiness` writes `outputs/manifests/PHASE0_DATA_READINESS.md` with the exact missing or malformed broker/symbol/timeframe sets.

## Snapshot Policy

Raw tick data is excluded from snapshot zip files by default. Use this only when an audit requires bundling raw market data:

```powershell
python -m phase0 generate-snapshot --include-raw-data
```
