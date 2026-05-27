# XAUUSD Phase 3 Experimental Sandbox

This package is a repo-only experiment. It assumes Phase 2 might pass later, but it does not change the real project gate state.

## Boundary

- Real Phase 2 remains PENDING until the objective readiness reports pass.
- This sandbox is not deployable to MT5.
- It must not touch `C:\MT5PortableGoldMission` or `C:\MT5PortableSpreadLogger`.
- It must not contain broker-action code.
- It reads Phase 1 dry-run evidence and writes offline reports only.
- It is excluded from the owner approval flow for real Phase 2 or real Phase 3.

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

## Purpose

The experiment lets us design and test Phase 3 concepts while Phase 2 evidence continues to mature:

- execution lifecycle states
- kill-rule behavior
- cost-survival checks
- paper-to-micro promotion criteria
- emergency stop design
- reviewable experimental ledgers
- family-level observer de-duplication
- explicit cost-mode stress checks
- source-hash manifests

## Commands

From this directory:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\simulate_phase3_from_would_signals.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase3_experimental_safety.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_status.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_manifest.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_status.py
```

The status command is intentionally run again after the manifest so the dashboard can show the latest manifest state.

The default input is:

```text
..\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv
```

The default outputs are under:

```text
outputs\reports\
```

## Family De-Duplication

The simulator treats `breakout_retest` as the only primary stream. `swing_breakout_retest_v0` and `symbol_normalized_round_retest_v0` are observer-only streams in this experiment. Provisional or disabled variants are rejected from the experimental ledger.

Key output fields:

```text
family_event_id
family_duplicate_group_id
family_event_role
primary_stream_allowed
raw_observer_event_count
family_unique_event_count
observer_duplicate_count
observer_conflict_count
```

## Cost Modes

Default:

```text
entry_exit_proxy
```

Available modes:

```text
entry_only_proxy
entry_exit_proxy
p95_fresh_proxy
stress_2x_p95_proxy
```

## Current Real-Project Effect

None. This lane is informational and must remain separate from Phase 1 dry-run and Phase 2 readiness gates.
