# gold_fx_proxy_divergence_v0 Blocker Fix

Date: 2026-05-25

## Goal

Unblock the next research step for `gold_fx_proxy_divergence_v0` without changing the active Phase 1 soak, Phase 2 readiness gates, approved expert list, or any production/dry-run execution path.

## Current Blockers

| Blocker | Current state | Process-safe fix |
| --- | --- | --- |
| Missing cross-symbol venue data | Capital.com has XAUUSD/EURUSD/USDJPY H1; Pepperstone and Dukascopy only have XAUUSD H1 locally. | Export or import EURUSD and USDJPY H1 bars for Pepperstone and Dukascopy for their exact matrix windows. |
| Strategy implementation absent | Fixed: research-only strategy and synthetic smoke path exist. | Keep it only in the research registry. Do not add to active `EXPERTS`. |
| Matrix data context lacks proxy series | The standard matrix loader supplies one target symbol context. | Add an optional research-only intermarket context loader keyed by expert name, or keep implementation blocked until proxy context exists. |
| Result-run authorization | Registration report correctly says result runs are not allowed yet. | Keep result runs disabled until data readiness and synthetic smoke pass. |

## Safe Fix

Use broker-consistent FX proxy inputs. Do not reuse Capital.com EURUSD/USDJPY as a substitute inside Pepperstone or Dukascopy cells for any authoritative Phase 0 result.

The strict data fix is:

```text
Pepperstone cells 4-6:
  EURUSD H1, 2019-01-01T00:00:00Z through 2021-12-31T23:59:59Z
  USDJPY H1, 2019-01-01T00:00:00Z through 2021-12-31T23:59:59Z

Dukascopy cells 7-9:
  EURUSD H1, 2022-01-01T00:00:00Z through 2024-12-31T23:59:59Z
  USDJPY H1, 2022-01-01T00:00:00Z through 2024-12-31T23:59:59Z
```

Capital.com already has the H1 proxy inputs for cells 1-3.

## Exact Data Requirements

The machine-readable checklist is:

```text
docs/GOLD_FX_PROXY_DIVERGENCE_V0_DATA_REQUIREMENTS.csv
```

Suggested raw export destinations:

```text
data/raw/pepperstone/
data/raw/dukascopy/
```

Ready-to-run MT5 exporter presets are tracked here:

```text
mt5/gold_fx_proxy_export_presets/
```

The preset manifest maps each missing dataset to the expected raw CSV and processed folder:

```text
mt5/gold_fx_proxy_export_presets/MANIFEST.csv
```

Suggested processed destinations after import:

```text
data/processed/bars/pepperstone/EURUSD/H1/
data/processed/bars/pepperstone/USDJPY/H1/
data/processed/bars/dukascopy/EURUSD/H1/
data/processed/bars/dukascopy/USDJPY/H1/
```

## Import Path

Use the existing passive bar-export/import process. For direct OHLC bar exports, place the raw CSVs in the broker raw folder, then normalize them with explicit broker, symbol, and timeframe:

```powershell
.\.venv\Scripts\phase0.exe normalize-bars --broker pepperstone --symbol EURUSD --timeframe H1 --input-file data\raw\pepperstone\EURUSD_H1_20190101_20211231_pepperstone.csv
.\.venv\Scripts\phase0.exe normalize-bars --broker pepperstone --symbol USDJPY --timeframe H1 --input-file data\raw\pepperstone\USDJPY_H1_20190101_20211231_pepperstone.csv
.\.venv\Scripts\phase0.exe normalize-bars --broker dukascopy --symbol EURUSD --timeframe H1 --input-file data\raw\dukascopy\EURUSD_H1_20220101_20241231_dukascopy.csv
.\.venv\Scripts\phase0.exe normalize-bars --broker dukascopy --symbol USDJPY --timeframe H1 --input-file data\raw\dukascopy\USDJPY_H1_20220101_20241231_dukascopy.csv
```

If exports are split into smaller date chunks, keep the same broker/symbol/timeframe tokens in each filename and ensure there is no overlapping `timestamp_utc` coverage after normalization.

## What Is Allowed Before Full Data Exists

Allowed:

- keep the hypothesis registered
- maintain the backlog/search documents
- write implementation behind the research-only registry
- run synthetic smoke once implementation exists
- run a Capital.com-only exploratory loader check clearly labelled exploratory

Not allowed:

- use Capital.com proxy data for Pepperstone/Dukascopy authoritative cells
- add the candidate to active `EXPERTS`
- include this candidate in `phase0 run-matrix --expert all`
- mark Phase 2 readiness improved because of this candidate
- treat any partial or exploratory result as Phase 0 approval

## Implementation Fix Sequence

1. Add a cross-symbol data-readiness check for `gold_fx_proxy_divergence_v0`.
2. Add a research-only strategy implementation using `data_context["intermarket_proxy"]`. Done.
3. Add synthetic context support for one proxy-divergence signal. Done.
4. Register the strategy only in `RESEARCH_STRATEGY_CLASSES` and `RESEARCH_EXPERTS`. Done.
5. Run `run-research-candidate-smoke` only after the implementation exists. Done: synthetic smoke passed.
6. Run real `run-research-matrix` only after the missing H1 proxy data is present and validated.

Machine-checkable readiness command:

```powershell
.\.venv\Scripts\phase0.exe generate-gold-fx-proxy-data-readiness
```

This writes:

```text
outputs/manifests/GOLD_FX_PROXY_DIVERGENCE_V0_DATA_READINESS.md
outputs/manifests/GOLD_FX_PROXY_DIVERGENCE_V0_DATA_REQUIREMENTS.csv
```

## Status

The process-safe fix and research-only implementation were completed. The four missing H1 proxy datasets were acquired and normalized:

```text
gold_fx_proxy_divergence_v0 data readiness: PASS
Ready: 6/6 proxy H1 set(s)
```

The unblocked first-pass matrix then rejected the locked v0 hypothesis:

```text
REJECTED_FIRST_PASS
```

Do not tune `gold_fx_proxy_divergence_v0` in place.
