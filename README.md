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

Phase 1 dry-run is authorized for the reduced one-expert package. It does not include broker-side execution. The shell logs one heartbeat per M5 bar and records lifecycle, spread, router, risk, and blocked-reason fields.

`breakout_retest` is the only approved future expert. `trend_pullback` and `range_mr` remain rejected.

## Current Phase Label

The active project phase is:

```text
Phase 1 - Master EA dry-run shell
```

Phase 1 remains dry-run only. Live expert behavior stays out of scope until the dry-run shell has produced stable demo telemetry and a separate go/no-go review approves the next milestone.

## Latest Review Status

As of 2026-05-21, the XAUUSD Phase 0 real-data workflow has imported all required broker/timeframe bar sets and completed a fresh post-hypothesis-lock `phase0 run-all`.

- Data readiness: `25/25` required timeframe sets ready.
- Verification: Phase 0 and Phase 1 test suites pass locally; passive safety audits pass.
- Current leading candidate: `breakout_retest`.
- Audit status: older real-data results are exploratory only because the hash-registered hypothesis files still contained placeholders at run time; the latest run was regenerated after completing and locking hypotheses.
- Reviewer-prompt cleanup: reference status, hypothesis completeness checks, holdout manifest fields, review bundle generation, intrabar ambiguity reporting, and real artifact verification commands are now part of the package.
- Current verdict: `breakout_retest` passed automated matrix, decile, multisymbol, hash, and Gate 9 manual adversarial gates.
- Phase 0 closure: `outputs/reports/PHASE0_VERDICT.md` marks `breakout_retest` as `PASS`; `verify-real-artifacts` returns `PASS`.
- EA coding status: Phase 1 dry-run shell is authorized for `breakout_retest` as the only approved future expert. Live execution remains blocked.

Large generated market data remains intentionally ignored by Git because it can be environment-specific. Small review artifacts, selected reports, and bundles may be committed when they are useful for third-party review. The current local handoff in `agent.md` records the latest artifact paths and regeneration commands.

## Current Review Follow-Ups

The latest reviewer feedback is tracked in:

- `docs/REVIEW_02_REFLECTION_AND_ACTION_PLAN.md`
- `xau-usd/xauusd-phase0/docs/REVIEW_RESPONSE_2026_05_21.md`
- `xau-usd/xauusd-phase0/docs/COST_REPORTING_POLICY.md`
- `xau-usd/xauusd-phase0/docs/PHASE0_INDEPENDENT_VALIDATION.md`
- `xau-usd/xauusd-phase0/docs/SECOND_CANDIDATE_RESEARCH_PLAN.md`
- `xau-usd/xauusd-phase1/docs/REPORTING_POLICY.md`
- `xau-usd/xauusd-phase1/docs/WORKSPACE_OWNERSHIP.md`

Review #2 reframes `breakout_retest` as a high-frequency, cost-sensitive intraday strategy. Phase 2 remains blocked until the dry-run soak completes, measured cost evidence is available, and fixed-notional plus measured-cost revalidation gates are satisfied.
