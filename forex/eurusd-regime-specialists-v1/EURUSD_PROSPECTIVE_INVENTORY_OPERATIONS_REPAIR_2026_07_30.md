# EURUSD prospective inventory operations repair

## Outcome

Both disarmed inventory-unwind prospective campaigns are now owned by
restartable Windows tasks:

| Task | State at verification | Broker actions |
|---|---|---|
| `Codex-EURUSD-Inventory-0005-Shadow` | Running | Prohibited |
| `Codex-EURUSD-Inventory-Clock-Shadow` | Running | Prohibited |

Both tasks had zero missed runs. Task result `267009` is the Task Scheduler
code for an instance that is still running. Their newest startup logs contained
the expected frozen campaign identity and had empty stderr logs.

## Defect and repair boundary

The original 06:05/12:05 helper exited during its first prewarm operation.
Strategy execution had succeeded, but the console logger attempted to pass a
Python `datetime` directly to `json.dumps`. The resulting `TypeError` stopped
the process before later clocks could be captured.

The frozen strategy module and every preregistration hash remain unchanged.
The repair is an external wrapper that:

1. calls the unchanged locked scheduler and operation functions;
2. converts only log-output datetimes, paths, and NumPy scalars to JSON-safe
   values;
3. records operational exceptions and continues fail-closed;
4. cannot authorize orders or alter signal, side, stop, target, clock,
   ownership, or selection logic.

The already-running 00:05 process was migrated to Task Scheduler so tomorrow's
daily trigger cannot create a second unmanaged collector. No evidence file was
deleted or rewritten.

## Current prospective state

- The 00:05 campaign recorded its first immutable 2026-07-30 source and
  decision. The source displacement was eligible, but causal ownership was not
  Neutral, so the locked decision was correctly `CASH`.
- The pooled 06:05/12:05 status is
  `ACCUMULATING_PROSPECTIVE_EVIDENCE` with zero decisions and zero trades at
  verification.
- Both campaigns remain research-only and shadow-only.
- Neither historical backtesting nor automatic demo activation is allowed.

## Verification

- Original clock-transfer preregistration status:
  `FROZEN_BEFORE_FIRST_TRANSFER_SOURCE_WINDOW`
- Focused frozen-campaign and wrapper tests: 25 passed.
- Wrapper Ruff check: passed.
- PowerShell task scripts: parser clean.
- Safe wrapper SHA-256:
  `eaf2203b803e17b049783e9c4c406b80f8b718a9fd3ca342c9992cb398f0d693`
- Task runner SHA-256:
  `f8eee916bbfb38808931a9040897423d7e132a3e588822785f2d18ed137cba20`
- Task installer SHA-256:
  `2775a0003b5aa1c6e0a3fc27319f27a3f326ae7da51b387d66025627302e9543`

This repair restores evidence collection. It does not promote either campaign
or solve the remaining EURUSD frequency gap by itself.
