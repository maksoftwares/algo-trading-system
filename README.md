# algo-trading-system

Research and validation workspace for algorithmic trading systems.

The repository is organized by symbol or instrument family so future symbols can be added without mixing research artifacts, data contracts, or reports.

## Current Packages

- `xau-usd/xauusd-phase0`: Phase 0 statistical validation package for the XAUUSD Master EA project.
- `xau-usd/xauusd-phase1`: Phase 1 dry-run shell for MT5 telemetry and lifecycle/risk/router contracts.

## XAUUSD Phase 0

The XAUUSD package tests candidate expert behavior before any live-trading EA logic is built. It includes:

- hypothesis SHA256 locking
- raw tick validation and normalization
- bar generation
- indicators and mechanical strategy simulators
- event-driven backtesting
- matrix, decile, multisymbol, and adversarial validation
- reference, holdout, intrabar, and real-artifact audit checks
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

## XAUUSD Phase 1

Phase 1 has started as a dry-run-only shell. It does not include an approved expert module or broker-side execution. The shell logs one heartbeat per M5 bar and records lifecycle, spread, router, risk, and blocked-reason fields.

`breakout_retest` remains `PENDING_MANUAL_REVIEW`, so expert logic stays blocked until Gate 9 is complete and the final Phase 0 verdict becomes `PASS`.

## Latest Review Status

As of 2026-05-21, the XAUUSD Phase 0 real-data workflow has imported all required broker/timeframe bar sets and completed an exploratory `phase0 run-all`.

- Data readiness: `25/25` required timeframe sets ready.
- Verification: `128 passed`; passive safety audit passed.
- Current leading candidate: `breakout_retest`.
- Audit status: previous real-data results are exploratory only because the hash-registered hypothesis files still contained placeholders at run time.
- Reviewer-prompt cleanup: reference status, hypothesis completeness checks, holdout manifest fields, review bundle generation, intrabar ambiguity reporting, and real artifact verification commands are now part of the package.
- Current verdict from exploratory evidence: `breakout_retest` passed automated matrix, decile, multisymbol, and hash gates, but remains `PENDING` until Gate 9 manual adversarial review is completed.
- EA coding status: blocked until completed hypotheses are re-registered, Phase 0 is rerun, Gate 9 passes, `verify-real-artifacts` passes, and the final verdict becomes `PASS`.

Generated market data, reports, manifests, and snapshots are intentionally ignored by Git because they can be large and environment-specific. The current local handoff in `agent.md` records the latest artifact paths and regeneration commands.
