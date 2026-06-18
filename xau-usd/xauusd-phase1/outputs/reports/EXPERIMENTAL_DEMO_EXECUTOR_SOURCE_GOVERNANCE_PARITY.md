# Experimental Demo Executor Source/Governance Parity

Overall status: PASS

This audit checks experimental demo executor source/governance parity only. It does not authorize canonical Phase 2, demo execution, broker execution, or live capital.

Source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5`
Governance doc: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md`
Repo commit hash: `b7ea9823ff6c6a78c05a01034498eaeeaccc2d98`
Source SHA256: `5d67933fa6673ac21488a98b3be780cf671781846e22238f27783af7b5a582a0`
Governance doc SHA256: `eb4b933db56d0de8d45706bb30aabd1e68177d028721ad57529e96ed0bcf2d05`
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
| account_open_exposure_cap_removed | PASS | all forbidden source tokens absent |
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
| order_log_non_authoritative_flags | PASS | all required source tokens present |
| order_guard_cost_suspension_ack | PASS | all required source tokens present |
| order_log_estimated_cost_r | PASS | all required source tokens present |
| order_log_mode_truthfulness | PASS | all required source tokens present |
| experimental_magic_namespace | PASS | all required source tokens present |
| fixed_lot_default_lte_0_01 | PASS | InpFixedLot=0.01 |

## Input Declaration Block

```mql5
13: input string InpRunId = "phase2-experimental-demo-executor-v0.2";
14: input bool InpDryRunOnly = false;
15: input bool InpBrokerActionAllowed = false;
16: input string InpCandidate = "breakout_retest";
17: input string InpCandidateStatus = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY";
18: input string InpFamilyLifecycleStatus = "COST_SUSPENDED_CANONICAL";
19: input string InpTargetSymbol = "XAUUSD";
20: input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,GBPUSD,BTCUSD";
21: input string InpExpectedServerMarker = "Demo";
22: input string InpAllowedAccountLoginsCsv = "";
23: input string InpExperimentalAuthorizationToken = "";
24: input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
25: input string InpCostSuspensionAcknowledgementToken = "";
26: input string InpRequiredCostSuspensionAcknowledgementToken = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT";
27: input string InpAuthorizedCandidatesCsv = "breakout_retest";
28: input string InpAttachmentLogFileName = "experimental_demo_executor_signal_log_v02.csv";
29: input string InpStartupLogFileName = "experimental_demo_executor_startup_v02.csv";
30: input string InpOrderLogFileName = "experimental_demo_executor_order_log_v02.csv";
31: input string InpDirectionStateFileName = "dirstate_xauusd.csv";
32: input string InpKillSwitchFileName = "experimental_demo_kill_switch.txt";
33: input double InpFixedLot = 0.01;
34: input double InpEURUSDFixedLot = 0.01;
35: input double InpGBPUSDFixedLot = 0.01;
36: input int InpMaxOrdersPerDay = 0;
37: input int InpMaxAccountOrdersPerDay = 0;
38: input int InpMinSecondsBetweenOrders = 0;
39: input int InpMaxOpenPositionsPerInstance = 0;
40: input int InpDeviationPoints = 50;
41: input double InpMaxEstimatedCostR = 0.00;
42: input double InpMaxMeasuredSpreadPoints = 0.0;
43: input bool InpTradeSessionGateEnabled = false;
44: input int InpTradeSessionStartHour = 0;
45: input int InpTradeSessionEndHour = 23;
```

## Boundary

A PASS here means the quarantined experimental executor source matches the documented guard set. It does not make the executor canonical Phase 2 evidence.
