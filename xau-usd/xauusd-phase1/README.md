# XAUUSD Phase 1

Phase 1 is the dry-run Master EA shell for the XAUUSD system.

This package is intentionally passive:

- no broker-side execution
- no position management
- no trade modification
- no approved expert module yet
- CSV telemetry only

Phase 0 currently leaves `breakout_retest` at `PENDING_MANUAL_REVIEW`. Because Gate 9 is not final, Phase 1 starts with infrastructure only: lifecycle, magic-number planning, router/risk contracts, spread gating, and dry-run logging.

## Scope

| Area | Phase 1 Status |
| --- | --- |
| Dry-run shell | Implemented |
| CSV telemetry | Implemented |
| Lifecycle state | Implemented |
| Risk gate contract | Implemented |
| Router contract | Implemented |
| Expert modules | Blocked until Phase 0 final PASS |
| Live pilot | Out of scope |

## Files

- `mt5/Experts/Phase1DryRunShell.mq5`
- `mt5/Config/phase1_dry_run_startup.ini`
- `mt5/Include/Phase1/Phase1Types.mqh`
- `mt5/Include/Phase1/Phase1Logger.mqh`
- `mt5/Include/Phase1/Phase1Risk.mqh`
- `mt5/Include/Phase1/Phase1Router.mqh`
- `mt5/Presets/Phase1DryRunShell.safe.set`
- `docs/PHASE1_DRY_RUN_SCOPE.md`
- `docs/MAGIC_NUMBERS.md`
- `docs/EXPERT_LIFECYCLE.md`
- `scripts/audit_phase1_safety.py`

## Expected MT5 Layout

Copy files into MT5 using this shape:

```text
MQL5/
  Experts/
    Phase1DryRunShell.mq5
  Include/
    Phase1/
      Phase1Types.mqh
      Phase1Logger.mqh
      Phase1Risk.mqh
      Phase1Router.mqh
  Presets/
    Phase1DryRunShell.safe.set
```

Attach `Phase1DryRunShell.mq5` to an XAUUSD demo chart. It writes one heartbeat row per new M5 bar when dry-run mode is locked.

## Validation

From this folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase1_safety.py
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests
```

From the repo root, the existing Phase 0 checks should still pass.
