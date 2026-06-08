# P2WEAKNESS BR V1 Runtime Reconciliation

Status: REVIEW_ONLY_RUNTIME_RECONCILED

Runtime reconciliation for existing P2WEAKNESS_BR_V1 evidence. This report reads CSV/log files only; it does not attach charts, change presets, deploy files, close terminals, or authorize canonical Phase 2.

Created at UTC: `2026-06-08T08:26:01.892626Z`

- New deployments paused: `True`
- Order log exists: `True`
- Startup log exists: `True`
- Kill switch exists: `False`
- Order rows: `11`
- Startup rows: `1`
- Latest order broker time: `2026.06.08 07:45:00`
- Latest order action: `GUARD_BLOCK`
- Latest order symbol: `XAUUSD`
- Latest order magic: `930101`
- Latest guard reason: `family_open_exposure_cap_reached`
- Latest family open exposure: `4`
- Latest account orders today: `0`
- Latest startup status: `ATTACHED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED`
- Latest startup account/server: `1025742` / `Capital.ComMena-Demo`
- Runtime magics observed: `[930101]`
- Runtime previous-magic warning: `True`
- Current committed source magic: `931000`
- Chart attachment evidence: `NOT_OBSERVABLE_FROM_CSV_LOGS`
- Runtime preset snapshot evidence: `NOT_OBSERVABLE_FROM_CSV_LOGS`

## Interpretation

If runtime logs still show 930101, that is historical/runtime evidence from before the repo hardening; the committed source and presets now use 931000 and remain non-executing by default.
