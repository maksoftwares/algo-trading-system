# Phase 1 Dry-Run Scope

Phase 1 builds the shell that will eventually host approved experts. It does not approve or implement a trading expert.

## Current Boundary

`breakout_retest` has strong automated Phase 0 evidence but remains `PENDING_MANUAL_REVIEW`. Until Gate 9 is scored and the consolidated verdict becomes `PASS`, the Phase 1 shell must stay infrastructure-only.

## Allowed

- lifecycle state handling
- magic-number allocation plan
- one-active-expert router contract
- centralized risk gate contract
- spread and session telemetry
- dry-run CSV logging
- static safety tests

## Blocked

- expert signal implementation
- broker-side execution
- position management
- strategy parameter tuning
- live pilot settings
- any `.set` file that enables real trading

## Phase 1 Exit Criteria

Phase 1 can advance when the dry-run shell has run cleanly on demo for five trading days and the logs prove:

- dry-run mode could not be disabled from inputs
- one heartbeat row was written per M5 bar
- spread gate state was logged
- lifecycle state was logged
- no expert was active without explicit approval evidence
