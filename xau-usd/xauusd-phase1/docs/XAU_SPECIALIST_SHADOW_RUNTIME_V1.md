# XAU Specialist Shadow Runtime V1

## Purpose

This runtime observes the frozen `R1_UPTREND_LONG_V1` specialist on completed
UTC bars and converts future candidates into broker-specific tick outcomes. It
does not place, modify, or close orders.

The evaluator imports the locked R1 research module and configuration directly.
It hashes the base implementation, R1 implementation, and configuration into
every evaluation and candidate record. A changed contract therefore creates a
different ID instead of silently changing an existing experiment.

## Runtime Files

The default external runtime directory is:

`C:\MT5PortableProspectiveCollector\MQL5\Files\specialist_shadow_v1`

- `r1_evaluations.jsonl`: one immutable decision state per completed H4 bucket.
- `r1_candidates.jsonl`: one immutable record per exact R1 candidate.
- `r1_outcomes_latest.json`: current entry, open-path, or closed outcome state.
- `runtime_status.json`: fail-closed health and authority status.

Entry labels use the first observed Ask tick after the signal. Long exits use
Bid ticks. Spread, ticket cost, holding cost, and frozen slippage stress are
included. This prospective ledger is the clean label source; broker bar history
is used only to establish the current frozen state.

## Run

From `xau-usd/xauusd-phase0` with its Python environment active:

```powershell
python ..\xauusd-phase1\scripts\run_xau_specialist_shadow.py --once
python ..\xauusd-phase1\scripts\run_xau_specialist_shadow.py
```

The runtime hard-fails unless account `1033669` is connected to a demo-marked
server in `C:\MT5PortableProspectiveCollector`. Python execution, broker action,
and trade permission remain false in every output record.
