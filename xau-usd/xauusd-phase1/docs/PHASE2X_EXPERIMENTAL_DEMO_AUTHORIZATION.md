# Phase 2X Experimental Demo Authorization

Status: NOT_APPROVED

Phase 2X is a quarantined owner-authorized demo-only execution lane for `P2WEAKNESS_BR_V1`.

## Boundary

- This does not authorize canonical Phase 2.
- This does not authorize live trading or real capital.
- This does not fix measured-cost revalidation failure.
- This does not unsuspend the `breakout_retest` family.
- This does not claim same-family diversification.
- This does not permit parameter tuning, compounding, grid, martingale, recovery mode, or averaging down.

## Allowed

- Demo/practice server only.
- Owner-approved demo account only.
- `XAUUSD` only.
- `P2WEAKNESS_BR_V1` only.
- Magic number `931000` only.
- Fixed lot `0.01` only.
- Local/private owner-authorized preset only.

## Approval Gate

Phase 2X execution may be considered only when `PHASE2X_DEMO_PREFLIGHT_REPORT.md` is `PASS`, the kill-switch block test is `PASS`, runtime cleanup is `PASS`, and owner authorization is complete. The committed repo must keep normal presets non-executing.
