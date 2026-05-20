# XAUUSD Phase 0

Phase 0 statistical validation package for the XAUUSD Master EA project.

This repository tests candidate expert behavior before any live-trading EA logic is built. It contains research, validation, reporting, snapshot, and passive spread-logging tools only.

## Rules

- No live order placement, position management, or trade-modification logic in Phase 0.
- No parameter optimization after results are produced.
- Hypotheses must be registered and hash-locked before backtests.
- Outputs must be deterministic, auditable, and written to CSV, Markdown, or snapshot zip files.
- The reserved true holdout window is protected unless explicitly unlocked for final review.

## Setup

```powershell
cd xau-usd\xauusd-phase0
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python -m pytest
```

## Synthetic Smoke Workflow

```powershell
python -m phase0 hash-hypotheses --register --force
python -m phase0 run-all --synthetic-sample
python -m phase0 generate-snapshot
```

The synthetic workflow writes matrix, decile, multisymbol, adversarial, report, result-manifest, and snapshot artifacts without requiring broker data.

## Data Folders

Raw broker CSVs go under `data/raw/{broker}/`. Processed ticks are written under `data/processed/ticks/{broker}/{symbol}/`, and bars are written under `data/processed/bars/{broker}/{symbol}/{timeframe}/`.

See `data/README_DATA.md` for the folder contract, accepted workflow, and snapshot policy.

## Real Data Workflow

```powershell
python -m phase0 validate-config
python -m phase0 audit-safety
python -m phase0 hash-hypotheses
python -m phase0 validate-data --broker capital_com --symbol XAUUSD
python -m phase0 normalize-data --broker capital_com --symbol XAUUSD
python -m phase0 build-bars --broker capital_com --symbol XAUUSD --timeframes M1,M5,M15,H1,H4,D1
python -m phase0 normalize-bars --broker capital_com --symbol XAUUSD --timeframe M5
python -m phase0 normalize-bars --broker capital_com --symbol XAUUSD --timeframe M5 --input-file data\raw\capital_com\broker_export.csv
python -m phase0 import-required-bars
python -m phase0 generate-data-manifest
python -m phase0 generate-data-readiness
python -m phase0 check-data-availability
python -m phase0 run-matrix --expert all
python -m phase0 run-deciles --expert all
python -m phase0 run-multisymbol --expert all
python -m phase0 create-adversarial-packets --expert all
python -m phase0 aggregate-results --expert all
python -m phase0 generate-verdict
python -m phase0 generate-snapshot
```

## Passive Spread Logger

Attach `mt5/PassiveSpreadLogger_XAUUSD.mq5` to a demo MT5 chart and let it run for the measurement period. Copy completed CSV logs into `outputs/logs/`, then run:

```powershell
python -m phase0 analyze-spread-logs
```

This produces `outputs/reports/cost_model_measured.csv` and `outputs/reports/spread_distribution_report.md`.

Measured `median` and `p95` spread values are used by the cost engine when `cost_model_measured.csv` exists. Lookup prefers symbol/broker/hour, then symbol/broker/day, then symbol/broker/global, before falling back to configured spreads.

## Key Outputs

- `outputs/reports/phase0_{expert}_results.md`
- `outputs/reports/PHASE0_VERDICT.md`
- `outputs/reports/cost_model_measured.csv`
- `outputs/manifests/PHASE0_DATA_READINESS.md`
- `outputs/manifests/PHASE0_RESULT_MANIFEST.csv`
- `outputs/snapshots/phase0_snapshot_{YYYYMMDD_HHMMSS}.zip`

Snapshots include `git_commit.txt`, `git_status.txt`, and `snapshot_manifest.txt` for audit review.
