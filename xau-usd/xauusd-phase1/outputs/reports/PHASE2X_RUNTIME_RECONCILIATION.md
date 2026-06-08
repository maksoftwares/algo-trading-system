# Phase 2X Runtime Reconciliation

Overall status: PASS

Phase 2X runtime reconciliation. Report-only; no MT5 runtime is modified.

Created at UTC: `2026-06-08T11:46:17.577794Z`

## Boundary

- Phase 2X can approve only quarantined experimental demo execution.
- Phase 2X cannot approve canonical Phase 2.
- Phase 2X cannot approve live trading or real capital.
- Phase 2X cannot unsuspend the cost-suspended breakout-retest family.
- Phase 2X cannot create same-family diversification claims.

- Signal rows: `2`
- Startup rows: `1`
- Order summary: `{'rows': 0, 'actions': {}, 'order_send_ok': 0, 'guard_blocks': 0, 'estimated_cost_r_min': None, 'estimated_cost_r_mean': None, 'estimated_cost_r_max': None}`
- Runtime attachment status: `NO_ACTIVE_P2WEAKNESS_RUNTIME_RISK_OBSERVED`

## Checks

| Check | Status | Evidence |
|---|---|---|
| signal_log_present | PASS | C:\MT5PortableP2WeaknessDryRunProof\MQL5\Files\p2weakness_br_v1_signal_log_xauusd.csv |
| order_log_present | PASS | C:\MT5PortableP2WeaknessDryRunProof\MQL5\Files\p2weakness_br_v1_order_log_xauusd.csv |
| startup_log_present | PASS | C:\MT5PortableP2WeaknessDryRunProof\MQL5\Files\p2weakness_br_v1_startup_xauusd.csv |
| new_runtime_magic_931000 | PASS | latest_order_magic=; latest_startup_magic=931000; old 930101 may be historical only |
| runtime_attachment_audit_present | PASS | P2WEAKNESS runtime attachment audit |
