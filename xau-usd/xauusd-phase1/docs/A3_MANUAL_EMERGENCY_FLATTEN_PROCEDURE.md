# A3 Manual Emergency Flatten Procedure

Status: OPERATOR_RUNBOOK_ONLY

EA-T1 and EA-T2 are entry-blocking only. They must not contain `PositionClose`, `PositionModify`, or `OrderDelete`. Any emergency flatten is manual owner/operator action outside the EA source.

## Trigger Examples

- Wrong account or non-demo server is detected.
- A3 kill switch or Guardian instruction requires human intervention.
- Account-level drawdown or operational issue exceeds owner tolerance.

## Manual Steps

1. Confirm account login is A3 `1033669` and server is demo/practice.
2. Disable Algo Trading in the terminal.
3. Create `A3_KILL.txt` in the terminal `MQL5/Files` folder with the text `KILL`.
4. Use the MT5 terminal Trade tab to close A3 positions manually if the owner decides flattening is required.
5. Record ticket IDs, close times, reason, screenshots if available, and account equity before/after.
6. Do not edit EA source, committed presets, or locked hypotheses during the active window.
7. Regenerate `A3_RUNTIME_RECONCILIATION.md` and the next daily guard-attribution report.

This procedure is intentionally outside EA code to preserve the no-position-closing source boundary.
