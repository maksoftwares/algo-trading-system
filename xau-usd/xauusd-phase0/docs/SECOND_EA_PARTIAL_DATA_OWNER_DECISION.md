# Second EA Partial Data Owner Decision

decision_status: SIGNED
owner_decision: OWNER_ACCEPTED_PARTIAL_DATA
accepted_report: outputs/reports/SECOND_EA_DATA_EXTENSION_READINESS.md
accepted_readiness_content_sha256: dd131821017159735da9eb711dd934dcfbfe592488a68297a06a6425614f17e8

## Current State

`SECOND_EA_DATA_EXTENSION_READINESS.md` is PARTIAL because Pepperstone does not provide the requested full 2016-01-01 through 2025-06-30 offline broker window. Dukascopy now has full offline coverage through the true-holdout cutoff.

Candidate matrix runs remain blocked unless the owner explicitly accepts this asymmetry.

## How The Owner Would Sign

Only the owner may change this file to:

```text
decision_status: SIGNED
owner_decision: OWNER_ACCEPTED_PARTIAL_DATA
```

The `accepted_readiness_content_sha256` must equal the current stable content SHA256 shown in `outputs/reports/SECOND_EA_DATA_EXTENSION_READINESS.md`. Timestamp-only report regeneration does not require re-signing, but any data-window/status change does.

## Boundary

This file does not authorize observer deployment, demo execution, paper trading, live trading, MT5 runtime access, or broker action.
