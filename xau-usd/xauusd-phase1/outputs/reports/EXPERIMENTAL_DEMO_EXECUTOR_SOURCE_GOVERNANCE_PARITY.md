# Experimental Demo Executor Source/Governance Parity

Overall status: PASS

This audit checks experimental demo executor source/governance parity only. It does not authorize canonical Phase 2, demo execution, broker execution, or live capital.

Source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5`
Governance doc: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md`
Repo commit hash: `4c92f8671c07dc370147b2e8be1e20e17bd37f4c`
Source SHA256: `0efef32e0e26fc900b7cac146a2dfb73a23bf7229e37fd27c356dec046bfce46`
Governance doc SHA256: `e4af355f4fe4d5fdf8d34f983bd19969593d6cb4ba37d1f04b9b22759c435048`
Failed checks: 0

| Check | Status | Evidence |
|---|---|---|
| source_file_tracked_by_git | PASS | tracked path: mt5/Experts/Phase2ExperimentalDemoExecutor.mq5 |
| non_canonical_banner | PASS | all required source tokens present |
| account_login_whitelist_input | PASS | doc_has=True; source_has=True; token=InpAllowedAccountLoginsCsv |
| experimental_authorization_token_input | PASS | doc_has=True; source_has=True; token=InpExperimentalAuthorizationToken |
| cost_suspension_acknowledgement_token_input | PASS | doc_has=True; source_has=True; token=InpCostSuspensionAcknowledgementToken |
| candidate_status_default_quarantined | PASS | InpCandidateStatus=EXPERIMENTAL_QUARANTINE_REVIEW_ONLY; allowed=EXPERIMENTAL_QUARANTINE_REVIEW_ONLY |
| family_lifecycle_default_cost_suspended | PASS | InpFamilyLifecycleStatus=COST_SUSPENDED_CANONICAL; allowed=COST_SUSPENDED_CANONICAL |
| candidate_runtime_allowlist_input | PASS | doc_has=True; source_has=True; token=InpAuthorizedCandidatesCsv |
| account_daily_order_cap_input | PASS | doc_has=True; source_has=True; token=InpMaxAccountOrdersPerDay |
| account_open_exposure_cap_input | PASS | doc_has=True; source_has=True; token=InpMaxAccountOpenPositions |
| kill_switch_input | PASS | doc_has=True; source_has=True; token=InpKillSwitchFileName |
| globalvariable_account_counter_logic | PASS | all required source tokens present |
| account_level_exposure_counter_logic | PASS | all required source tokens present |
| kill_switch_file_read_logic | PASS | all required source tokens present |
| candidate_authorization_guard | PASS | all required source tokens present |
| startup_refuses_blank_or_invalid_token | PASS | all required source tokens present |
| startup_refuses_missing_cost_suspension_ack | PASS | all required source tokens present |
| startup_refuses_unlisted_account | PASS | all required source tokens present |
| startup_refuses_unauthorized_candidate | PASS | all required source tokens present |
| startup_refuses_kill_switch | PASS | all required source tokens present |
| no_live_real_server_allowed | PASS | all required source tokens present |
| cost_r_pre_order_guard | PASS | all required source tokens present |
| spread_pre_order_guard | PASS | all required source tokens present |
| order_log_account_order_count | PASS | all required source tokens present |
| order_log_account_open_exposure | PASS | all required source tokens present |
| order_log_family_lifecycle_status | PASS | all required source tokens present |
| order_guard_cost_suspension_ack | PASS | all required source tokens present |
| order_log_estimated_cost_r | PASS | all required source tokens present |
| order_log_mode_truthfulness | PASS | all required source tokens present |
| experimental_magic_namespace | PASS | all required source tokens present |
| fixed_lot_default_lte_0_01 | PASS | InpFixedLot=0.01 |

## Input Declaration Block

```mql5
12: input string InpRunId = "phase2-experimental-demo-executor-v0.2";
13: input bool InpDryRunOnly = false;
14: input bool InpBrokerActionAllowed = false;
15: input string InpCandidate = "breakout_retest";
16: input string InpCandidateStatus = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY";
17: input string InpFamilyLifecycleStatus = "COST_SUSPENDED_CANONICAL";
18: input string InpTargetSymbol = "XAUUSD";
19: input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,USDJPY";
20: input string InpExpectedServerMarker = "Demo";
21: input string InpAllowedAccountLoginsCsv = "";
22: input string InpExperimentalAuthorizationToken = "";
23: input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
24: input string InpCostSuspensionAcknowledgementToken = "";
25: input string InpRequiredCostSuspensionAcknowledgementToken = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT";
26: input string InpAuthorizedCandidatesCsv = "breakout_retest";
27: input string InpAttachmentLogFileName = "experimental_demo_executor_signal_log_v02.csv";
28: input string InpStartupLogFileName = "experimental_demo_executor_startup_v02.csv";
29: input string InpOrderLogFileName = "experimental_demo_executor_order_log_v02.csv";
30: input string InpKillSwitchFileName = "experimental_demo_kill_switch.txt";
31: input double InpFixedLot = 0.01;
32: input int InpMaxOrdersPerDay = 12;
33: input int InpMaxAccountOrdersPerDay = 24;
34: input int InpMinSecondsBetweenOrders = 300;
35: input int InpMaxOpenPositionsPerInstance = 1;
36: input int InpMaxAccountOpenPositions = 3;
37: input int InpDeviationPoints = 50;
38: input double InpMaxEstimatedCostR = 0.30;
39: input double InpMaxMeasuredSpreadPoints = 75.0;
```

## Boundary

A PASS here means the quarantined experimental executor source matches the documented guard set. It does not make the executor canonical Phase 2 evidence.
