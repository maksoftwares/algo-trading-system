# algo-trading-system

Research and validation workspace for algorithmic trading systems.

The repository is organized by symbol or instrument family so future symbols can be added without mixing research artifacts, data contracts, or reports.

## Current Packages

- `xau-usd/xauusd-phase0`: Phase 0 statistical validation package for the XAUUSD Master EA project.

## XAUUSD Phase 0

The XAUUSD package tests candidate expert behavior before any live-trading EA logic is built. It includes:

- hypothesis SHA256 locking
- raw tick validation and normalization
- bar generation
- indicators and mechanical strategy simulators
- event-driven backtesting
- matrix, decile, multisymbol, and adversarial validation
- markdown reports and consolidated verdict
- audit snapshot generation
- passive MT5 spread logger and spread-log analyzer

## Quick Start

```powershell
cd xau-usd\xauusd-phase0
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m phase0 run-all --synthetic-sample
.venv\Scripts\python.exe -m phase0 generate-snapshot
```

See `xau-usd/xauusd-phase0/README.md` for the full workflow.

Agent handoff and current gate status are maintained in `agent.md`.
