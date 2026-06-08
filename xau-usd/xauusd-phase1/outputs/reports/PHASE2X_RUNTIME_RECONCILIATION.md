# Phase 2X Runtime Reconciliation

Overall status: PENDING

Phase 2X runtime reconciliation. Report-only; no MT5 runtime is modified.

Created at UTC: `2026-06-08T11:24:28.874005Z`

## Boundary

- Phase 2X can approve only quarantined experimental demo execution.
- Phase 2X cannot approve canonical Phase 2.
- Phase 2X cannot approve live trading or real capital.
- Phase 2X cannot unsuspend the cost-suspended breakout-retest family.
- Phase 2X cannot create same-family diversification claims.

- Signal rows: `162`
- Startup rows: `1`
- Order summary: `{'rows': 12, 'actions': {'GUARD_BLOCK': 11, 'ORDER_SEND_OK': 1}, 'order_send_ok': 1, 'guard_blocks': 11, 'estimated_cost_r_min': 0.0437, 'estimated_cost_r_mean': 0.084892, 'estimated_cost_r_max': 0.1385}`
- Runtime attachment status: `QUARANTINE_RUNTIME_RISK_FOUND`

## Checks

| Check | Status | Evidence |
|---|---|---|
| signal_log_present | PASS | C:\MT5PortableP2WeaknessDemo\MQL5\Files\p2weakness_br_v1_signal_log_xauusd.csv |
| order_log_present | PASS | C:\MT5PortableP2WeaknessDemo\MQL5\Files\p2weakness_br_v1_order_log_xauusd.csv |
| startup_log_present | PASS | C:\MT5PortableP2WeaknessDemo\MQL5\Files\p2weakness_br_v1_startup_xauusd.csv |
| new_runtime_magic_931000 | PENDING_RUNTIME_EVIDENCE | latest_order_magic=930101; latest_startup_magic=930101; old 930101 may be historical only |
| runtime_attachment_audit_present | PASS | P2WEAKNESS runtime attachment audit |
