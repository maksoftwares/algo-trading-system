# Phase 2X Demo Preflight Report

Overall status: PENDING

Phase 2X demo preflight. Can approve only quarantined experimental demo execution; cannot approve canonical Phase 2, live trading, or real capital.

Created at UTC: `2026-06-08T11:29:07.646439Z`

## Boundary

- Phase 2X can approve only quarantined experimental demo execution.
- Phase 2X cannot approve canonical Phase 2.
- Phase 2X cannot approve live trading or real capital.
- Phase 2X cannot unsuspend the cost-suspended breakout-retest family.
- Phase 2X cannot create same-family diversification claims.

- Phase 2X demo execution authorized: `False`
- Local preset: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\local\Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set`

## Checks

| Check | Status | Evidence |
|---|---|---|
| canonical_phase2_readiness_is_fail_or_blocked | PASS | PHASE2_READINESS_REPORT.md status=FAIL |
| cost_suspended_lifecycle_acknowledged | PASS | status=COST_SUSPENDED_CANONICAL; expected=COST_SUSPENDED_CANONICAL |
| source_governance_parity | PASS | status=PASS |
| magic_collision_audit | PASS | status=PASS |
| clean_clone_reconciliation | PASS | status=PASS |
| safe_preset_non_executing | PASS | status=PASS; expected=PASS |
| owner_authorization_status | PASS | status=PASS; expected=PASS |
| owner_authorization_local_file_present | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\local\Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set |
| owner_local_preset_uses_931000 | PASS | InpMagicNumber='931000' |
| owner_local_preset_fixed_lot_lte_0_01 | PASS | InpFixedLot='0.01' |
| owner_local_preset_max_orders_per_day_lte_3 | PASS | InpMaxOrdersPerDay='2' |
| owner_local_preset_max_account_orders_per_day_lte_3 | PASS | InpMaxAccountOrdersPerDay='3' |
| owner_local_preset_max_family_open_positions_eq_1 | PASS | InpMaxFamilyOpenPositions='1' |
| owner_local_preset_cost_r_lte_0_15 | PASS | InpMaxEstimatedCostR='0.15' |
| owner_local_preset_spread_lte_75 | PASS | InpMaxMeasuredSpreadPoints='75.0' |
| target_symbol_xauusd | PASS | InpTargetSymbol='XAUUSD' |
| owner_local_preset_not_committed | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\local\Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set |
| old_magic_930101_not_allowed_for_new_deployment | PASS | preset_magic=931000 |
| runtime_cleanup_report_pass | PENDING_RUNTIME_EVIDENCE | status=PENDING; expected=PASS |
| kill_switch_block_test_pass | PENDING_RUNTIME_EVIDENCE | status=PENDING; expected=PASS |
| demo_account_isolation_evidence | PASS | owner authorization masks account when available |
| server_marker_demo | PASS | server_marker='Capital.ComMena-Demo' |
| no_live_server_marker_in_authorized_runtime | PASS | server_marker='Capital.ComMena-Demo' |
| no_canonical_promotion | PASS | Phase 2X does not change PHASE2_READINESS_REPORT.md or cost-suspension reports. |
| runtime_attachment_audit_available | PASS | P2WEAKNESS runtime attachment audit is used as evidence. |
