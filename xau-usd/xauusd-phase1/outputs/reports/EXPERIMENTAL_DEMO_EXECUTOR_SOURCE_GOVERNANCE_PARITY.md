# Experimental Demo Executor Source/Governance Parity

Overall status: PASS

This audit checks experimental demo executor source/governance parity only. It does not authorize canonical Phase 2, demo execution, broker execution, or live capital.

Source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5`
Governance doc: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md`
Failed checks: 0

| Check | Status | Evidence |
|---|---|---|
| account_login_whitelist_input | PASS | doc_has=True; source_has=True; token=InpAllowedAccountLoginsCsv |
| experimental_authorization_token_input | PASS | doc_has=True; source_has=True; token=InpExperimentalAuthorizationToken |
| candidate_runtime_allowlist_input | PASS | doc_has=True; source_has=True; token=InpAuthorizedCandidatesCsv |
| account_daily_order_cap_input | PASS | doc_has=True; source_has=True; token=InpMaxAccountOrdersPerDay |
| account_open_exposure_cap_input | PASS | doc_has=True; source_has=True; token=InpMaxAccountOpenPositions |
| kill_switch_input | PASS | doc_has=True; source_has=True; token=InpKillSwitchFileName |
| globalvariable_account_counter_logic | PASS | all required source tokens present |
| account_level_exposure_counter_logic | PASS | all required source tokens present |
| kill_switch_file_read_logic | PASS | all required source tokens present |
| candidate_authorization_guard | PASS | all required source tokens present |
| startup_refuses_blank_or_invalid_token | PASS | all required source tokens present |
| startup_refuses_unlisted_account | PASS | all required source tokens present |
| startup_refuses_unauthorized_candidate | PASS | all required source tokens present |
| startup_refuses_kill_switch | PASS | all required source tokens present |
| no_live_real_server_allowed | PASS | all required source tokens present |
| cost_r_pre_order_guard | PASS | all required source tokens present |
| spread_pre_order_guard | PASS | all required source tokens present |
| order_log_account_order_count | PASS | all required source tokens present |
| order_log_account_open_exposure | PASS | all required source tokens present |
| order_log_estimated_cost_r | PASS | all required source tokens present |
| order_log_mode_truthfulness | PASS | all required source tokens present |
| experimental_magic_namespace | PASS | all required source tokens present |
| fixed_lot_default_lte_0_01 | PASS | InpFixedLot=0.01 |

## Boundary

A PASS here means the quarantined experimental executor source matches the documented guard set. It does not make the executor canonical Phase 2 evidence.
