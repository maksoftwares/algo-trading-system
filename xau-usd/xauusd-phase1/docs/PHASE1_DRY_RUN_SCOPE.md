# Phase 1 Dry-Run Scope

This is the active Phase 1 dry-run scope after Phase 0 closure.

## Current Boundary

`breakout_retest` has a final Phase 0 PASS. `swing_breakout_retest_v0` also passed its research matrix, decile, multisymbol, intrabar, and Gate 9 manual adversarial checks, but it is same-family with `breakout_retest`. The Phase 1 shell remains dry-run only.

## Allowed

- lifecycle state handling
- magic-number allocation plan
- one-active-expert router contract
- centralized risk gate contract
- simulated daily/weekly/monthly risk caps
- spread and session telemetry
- server-time validation
- magic-number namespace checks
- expert lifecycle state
- feature telemetry
- breakout_retest dry-run signal-state observation
- swing_breakout_retest_v0 dry-run signal-state observation
- dry-run CSV logging
- startup and shutdown CSV logging
- restart-resilience log verification
- review bundle generation
- review index generation
- runtime health and gap reporting
- soak-history ledger generation
- soak-history report generation
- static safety tests

## Blocked

- live expert signal implementation
- broker-side execution
- position management
- strategy parameter tuning
- live pilot settings
- any `.set` file that enables real trading

## Phase 1 Exit Criteria

Phase 1 can advance beyond dry-run when the shell has run cleanly on demo for five trading days and the logs prove:

- dry-run mode could not be disabled from inputs
- one heartbeat row was written per M5 bar
- spread gate state was logged
- lifecycle state was logged
- no expert was active without explicit approval evidence
- soak-history rows show clean recurring verification over the full period
- runtime-health reports show fresh rows, no exact duplicate rows, and no unexpected M5 gaps
