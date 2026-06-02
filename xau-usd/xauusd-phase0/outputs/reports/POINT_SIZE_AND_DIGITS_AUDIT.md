# Point Size And Digits Audit

Overall status: PASS
Generated at UTC: 2026-06-02T11:45:09Z
Symbol: `XAUUSD`

| Check | Status | Evidence |
| --- | --- | --- |
| Point size and digits | PASS | ledger_point_sizes=[0.01]; logger_point_sizes=[0.01]; logger_digits=['2'] |
| Historical ledger symbol metadata | PASS | symbol=XAUUSD; inferred_point_size=0.0100; inferred_digits=2 |
| Measured logger symbol metadata | PASS | symbol=XAUUSD; logger_points=['0.01']; logger_digits=['2'] |

This report verifies symbol metadata for cost-R conversion only. It does not authorize Phase 2.
