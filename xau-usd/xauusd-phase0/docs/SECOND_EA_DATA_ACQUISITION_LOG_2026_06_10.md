# Second EA Data Acquisition Log

Date: 2026-06-10

Purpose: extend offline data readiness for the second-EA Lane A / Lane B research campaign without MT5 runtime access, broker account access, demo execution, paper trading, live trading, or preset mutation.

## Boundary

This acquisition is research-only. It does not authorize candidate matrix runs, observer deployment, demo execution, paper trading, live trading, MT5 runtime access, or broker action.

## Acquired

Dukascopy XAUUSD bid candles were acquired through public `dukascopy-node` CSV downloads and placed in `data/raw/dukascopy/`.

| Broker | Symbol | Timeframe | Added coverage | Raw file pattern |
| --- | --- | --- | --- | --- |
| dukascopy | XAUUSD | M5 | 2016-01-01 through 2021-12-31; 2025-01-01 through 2025-06-30 | `XAUUSD_M5_*_dukascopy.csv` |
| dukascopy | XAUUSD | M15 | 2016-01-01 through 2021-12-31; 2025-01-01 through 2025-06-30 | `XAUUSD_M15_*_dukascopy.csv` |
| dukascopy | XAUUSD | H1 | 2016-01-01 through 2021-12-31; 2025-01-01 through 2025-06-30 | `XAUUSD_H1_*_dukascopy.csv` |
| dukascopy | XAUUSD | H4 | 2016-01-01 through 2021-12-31; 2025-01-01 through 2025-06-30 | `XAUUSD_H4_*_dukascopy.csv` |
| dukascopy | XAUUSD | D1 | 2016-01-01 through 2021-12-31; 2025-01-01 through 2025-06-30 | `XAUUSD_D1_*_dukascopy.csv` |

## Current Readiness Result

After regeneration, Dukascopy is PASS for M5, M15, H1, H4, and D1 from 2016-01-01 through the 2025-06-30 true-holdout cutoff.

`SECOND_EA_DATA_EXTENSION_READINESS.md` remains PARTIAL because Pepperstone still only has offline raw XAUUSD coverage from 2019-01-02 through 2021-12-31.

Current readiness content SHA256:

```text
dd131821017159735da9eb711dd934dcfbfe592488a68297a06a6425614f17e8
```

## Pepperstone Status

No non-MT5, repo-local Pepperstone acquisition path was found for the missing 2016-2018 and 2022-2025 XAUUSD M5/M15/H1/H4/D1 windows. The campaign goal forbids MT5 runtime access and the passive exporter for this task, so Pepperstone remains PARTIAL unless the owner supplies offline files or signs `OWNER_ACCEPTED_PARTIAL_DATA` for the current readiness hash.

## Verification

```powershell
.venv\Scripts\python.exe scripts\generate_second_ea_data_readiness.py
.venv\Scripts\python.exe scripts\validate_second_ea_partial_data_decision.py
```

Result:

```text
SECOND_EA_DATA_READINESS_PARTIAL
SECOND_EA_PARTIAL_DATA_DECISION_NOT_SIGNED
```

## Addendum 2026-06-10 (reviewer takeover): processed-bar completion and higher-timeframe derivation

Two gaps surfaced when the locked full-window Lane A rerun first loaded the extended windows:

1. The acquired raw Dukascopy files had not been imported into processed bars. Fixed with
   `python -m phase0 import-required-bars --skip-multisymbol` (40 M5 / 8 M15 / 4 H1 / 3 H4 / 3 D1
   files imported; `PHASE0_BAR_IMPORT_REPORT.csv` regenerated).
2. The downloaded Dukascopy M15/H1/H4/D1 exports for 2016-2021 and 2025-H1 contain multi-day
   holes (worst: 10 days around 2017-09-15) and fail the matrix loader continuity check, while
   the M5 series is continuity-clean for 2016-01-01 through 2025-06-30 (984,384 bars).
   Fix per brief step D2 ("derive M15/H1/H4/D1"): `scripts/derive_dukascopy_timeframes_from_m5.py`
   derives all four higher timeframes uniformly from M5 (identical schema, UTC bar-end
   convention); the downloaded higher-timeframe processed files were quarantined (not deleted)
   under `data/quarantine/dukascopy_downloaded_tf_2026_06_10/`. Uniform construction across eras
   also serves the G8 era-integrity comparison.

This addendum changes no rule, gate, window definition, or cost model and authorizes no runtime
or broker action.
