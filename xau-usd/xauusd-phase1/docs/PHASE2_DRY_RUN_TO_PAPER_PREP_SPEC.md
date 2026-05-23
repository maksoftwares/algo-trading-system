# Phase 2 Dry-Run To Paper Preparation Spec

This document prepares the next phase without changing the current Phase 1 safety boundary.

## Objective

Phase 2 preparation defines the evidence, interfaces, logs, and operator controls required before any paper-mode broker bridge is considered. The current repo remains dry-run only until Phase 1 acceptance is complete and the project owner explicitly approves the next milestone.

## Entry Gates

Phase 2 preparation can continue while the soak runs, but Phase 2 implementation cannot begin until:

- `PHASE1_ACCEPTANCE_REPORT.md` is `PASS`
- `PHASE1_REVIEW_INDEX.md` is `PASS`
- five trading days of clean dry-run telemetry are present
- would-signal clusters have been reviewed for obvious router or observer defects
- the safety scanner passes for all Phase 1 and preparation files

## Allowed Preparation Work

- paper-mode interface design
- shadow ledger schema
- projected fill and cost model schema
- operator checklist
- kill-switch and lockout specification
- dry-run replay acceptance criteria
- reviewer signoff checklist
- deployment rollback checklist

## Blocked Until Explicit Approval

- broker-side actions
- real position lifecycle changes
- account-affecting behavior
- active expert enablement
- production preset files
- any platform-specific broker-action call

## Proposed Phase 2 Components

| Component | Purpose | Phase 2 Prep Status |
| --- | --- | --- |
| PaperBridge | Converts dry-run decisions into paper ledger events only | Spec only |
| ShadowLedger | Records projected entries, exits, costs, and state transitions | Spec only |
| FillModel | Applies spread, slippage, and adverse sequencing assumptions | Spec only |
| OperatorLocks | Keeps manual, daily, weekly, monthly, and emergency lockouts central | Spec only |
| DriftMonitor | Compares Phase 0 expectation against live dry-run observations | Spec only |
| ReviewExporter | Produces reviewer CSV and markdown packets | Spec only |

## Paper Ledger Columns

```text
event_id
run_id
timestamp_broker
timestamp_utc
timestamp_local
symbol
expert
decision_bar_time
paper_event_type
direction
entry_price_projected
stop_price_projected
target_price_projected
spread_points
slippage_points_assumed
cost_model_id
risk_state
execution_state
news_state
router_state
permission_state
dry_run_source_row
operator_lock_state
review_status
review_notes
```

## Transition Decision Rule

```text
IF Phase 1 acceptance = PASS
AND review index = PASS
AND project owner approval is recorded
THEN create Phase 2 paper-mode implementation branch.

ELSE keep working in Phase 1 dry-run and evidence preparation.
```

## First Phase 2 Milestone

The first milestone should be a paper ledger only. It should read the same dry-run decision stream and produce shadow events, but it should not affect the account. The shell must keep the same central lockouts and the same review-bundle discipline.

## Review Questions Before Build

- Did the five-day soak show any stale runtime gaps?
- Did any would-signal cluster look mechanically invalid?
- Did spread or session state frequently block expected conditions?
- Did restart behavior preserve CSV integrity?
- Did the dashboard and logs agree on mode, lock state, and latest bar?
- Is the operator able to disable paper projection without touching code?

## Current Status

Phase 2 preparation is allowed. Phase 2 implementation is not yet authorized because Phase 1 acceptance remains pending until both the five-trading-day soak gate and the 72-hour uninterrupted active-market streak gate close.

The machine-checkable preflight artifact for this boundary is:

```text
outputs/reports/PHASE2_READINESS_REPORT.md
```

The paper-ledger evidence contract is defined in:

```text
docs/PHASE2_PAPER_LEDGER_SCHEMA.md
```

Its machine-checkable schema report and generated column template are:

```text
outputs/reports/PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md
outputs/reports/PHASE2_PAPER_LEDGER_COLUMNS.csv
```
