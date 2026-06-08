# Phase 2X Kill-Switch Test Procedure

Status: PROCEDURE_ONLY

The kill-switch test proves `P2WEAKNESS_BR_V1` blocks broker action while the kill-switch file exists. It does not authorize canonical Phase 2, live trading, real capital, cost-suspension removal, or same-family diversification claims.

## Procedure

1. Ensure the EA is attached in demo/practice only.
2. Create `p2weakness_br_v1_kill_switch.txt` in the MT5 `MQL5/Files` directory.
3. Observe at least one would-trade or guard-evaluation interval.
4. Confirm the order log shows a kill-switch block and no broker order was sent.
5. Remove the kill-switch file only if execution is intended and preflight is otherwise PASS.
6. Generate `PHASE2X_KILL_SWITCH_BLOCK_TEST_REPORT.md`.

The report status is `PASS` only when block behavior is documented. It is `PENDING` before the test and `FAIL` if any order is sent while the kill switch is active.
