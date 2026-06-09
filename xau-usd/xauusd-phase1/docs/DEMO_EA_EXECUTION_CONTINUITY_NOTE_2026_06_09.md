# Demo EA Execution Continuity Note

```text
owner_instruction_date: 2026-06-09
scope: experimental demo execution lanes only
canonical_phase2_status: unchanged
live_trading_authorized: false
real_capital_authorized: false
```

## Owner Instruction

The owner instructed that the active experimental demo EAs should not be stopped from placing trades.

Operational meaning:

- Do not detach active demo EA charts.
- Do not switch active demo EAs back to dry-run mode.
- Do not create or leave kill-switch files that block active demo execution.
- Do not reduce lots, disable broker action, or add new caps/guards that suppress valid signal-based orders.
- Do not reintroduce per-instance exposure caps, daily order caps, min-seconds throttles, cost-R guards, or spread guards into the active demo runtime unless the owner explicitly asks.
- Do not deploy shadow filters, duplicate mutexes, weak-EA quarantines, session blocks, or router guards to the active demo terminal unless the owner explicitly approves that runtime change.
- Reporting, dashboard refreshes, exports, review bundles, and audits must remain read-only unless the owner has asked for a runtime change.

## Allowed Exceptions

The only acceptable reasons to stop or block active demo execution without a fresh owner instruction are:

- The terminal/account is not the approved demo account.
- A live/real-money server marker is detected.
- The account login does not match the approved demo login.
- The owner explicitly asks to pause, stop, detach, kill-switch, or reduce execution.
- A technical action is required to prevent accidental live trading or wrong-account trading.

## Current Runtime Interpretation

As of the 2026-06-09 execution-unblock update, active demo EAs should be allowed to place orders whenever their own strategy signal fires. This note does not require fake/blind trades when no signal exists; it only prevents agent-side or automation-side suppression of valid signal-based demo orders.

## Boundary

This note applies only to experimental demo execution. It does not authorize canonical Phase 2, live trading, or real capital.
