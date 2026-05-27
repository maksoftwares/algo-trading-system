# XAUUSD Phase 3 Experimental Sandbox

This package is a repo-only experiment. It assumes Phase 2 might pass later, but it does not change the real project gate state.

## Boundary

- Real Phase 2 remains PENDING until the objective readiness reports pass.
- This sandbox is not deployable to MT5.
- It must not touch `C:\MT5PortableGoldMission` or `C:\MT5PortableSpreadLogger`.
- It must not contain broker-action code.
- It reads Phase 1 dry-run evidence and writes offline reports only.

## Purpose

The experiment lets us design and test Phase 3 concepts while Phase 2 evidence continues to mature:

- execution lifecycle states
- kill-rule behavior
- cost-survival checks
- paper-to-micro promotion criteria
- emergency stop design
- reviewable experimental ledgers

## Commands

From this directory:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\simulate_phase3_from_would_signals.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_status.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase3_experimental_safety.py
```

The default input is:

```text
..\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv
```

The default outputs are under:

```text
outputs\reports\
```

## Current Real-Project Effect

None. This lane is informational and must remain separate from Phase 1 dry-run and Phase 2 readiness gates.
