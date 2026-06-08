# Phase 2X Demo Operating Procedure

Status: PROCEDURE_ONLY

This procedure does not authorize canonical Phase 2, live trading, real capital, cost-suspension removal, or same-family diversification claims.

## Step 1 - Prepare

1. Pull latest repo.
2. Confirm working tree clean.
3. Run tests and Phase 2X safe-default validation.
4. Run P2WEAKNESS governance, magic, clean-clone, runtime attachment, and runtime cleanup reports.
5. Confirm normal committed preset remains non-executing.
6. Fill `xau-usd/xauusd-phase1/local/phase2x_owner_authorization.local.json`.
7. Generate the local owner-authorized preset.
8. Generate `PHASE2X_NO_TOUCH_STAGING_REPORT.md` and confirm it is `PASS`.
9. Generate `PHASE2X_DEMO_PREFLIGHT_REPORT.md`.

The no-touch staging report is the last step that can be completed without touching any running MT5 terminal. It confirms the safe committed startup config, the safe committed preset, the local owner preset SHA256, and the isolated portable preparation report. It does not launch MT5, attach a chart, close a terminal, or authorize broker execution.

## Step 2 - Dry-Run Attach First

Attach `P2WEAKNESS_BR_V1` with the normal safe preset:

```text
InpDryRunOnly=true
InpBrokerActionAllowed=false
```

Required evidence: startup log, signal log, no orders sent, demo server detected, authorized login detected, and kill-switch block test completed.

## Step 3 - Owner-Authorized Demo Attach

Only after preflight PASS:

1. Detach the dry-run chart.
2. Attach the EA with the local owner-authorized demo preset.
3. Confirm demo account, `XAUUSD`, magic `931000`, and fixed lot `0.01`.

## Step 4 - Daily Review

Every day generate `PHASE2X_DAILY_DEMO_REVIEW_YYYY_MM_DD.md`. Stop immediately on live/real marker, wrong magic, wrong symbol, lot above `0.01`, order-cap breach, family exposure breach, cost R above `0.15`, kill-switch failure, or unreconciled logs.

## Step 5 - End Of Week

Generate the Phase 2X evidence bundle. Decision options are `CONTINUE_EXPERIMENT`, `STOP_EXPERIMENT`, or `RETURN_TO_RESEARCH`. Do not promote to canonical Phase 2 from one week of demo evidence.
