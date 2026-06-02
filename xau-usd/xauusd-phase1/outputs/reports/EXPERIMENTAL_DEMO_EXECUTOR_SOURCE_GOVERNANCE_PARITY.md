# Experimental Demo Executor Source/Governance Parity

Overall status: PASS

This audit checks experimental demo executor source/governance parity only. It does not authorize canonical Phase 2, demo execution, broker execution, or live capital.

Source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5`
Governance doc: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md`
Repo commit hash: `78921f3f6143e4ec37e9adae10bffa307cf89020`
Source SHA256: `cc2d330876ee9376e154a5133ebcbc01d1c15ec033aecd48d19db57ee76bf5cd`
Governance doc SHA256: `7766c50c0a75c2f94a7671466dd8781b57a2a32ccb15f85fe3f488eb63ea0cd8`
Failed checks: 0

| Check | Status | Evidence |
|---|---|---|
| source_file_tracked_by_git | PASS | tracked path: mt5/Experts/Phase2ExperimentalDemoExecutor.mq5 |
| non_canonical_banner | PASS | all required source tokens present |
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

## Input Declaration Block

```mql5
12: input string InpRunId = "phase2-experimental-demo-executor-v0.1";
13: input bool InpDryRunOnly = false;
14: input bool InpBrokerActionAllowed = false;
15: input string InpCandidate = "breakout_retest";
16: input string InpCandidateStatus = "ACCEPTED";
17: input string InpTargetSymbol = "XAUUSD";
18: input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,USDJPY";
19: input string InpExpectedServerMarker = "Demo";
20: input string InpAllowedAccountLoginsCsv = "";
21: input string InpExperimentalAuthorizationToken = "";
22: input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
23: input string InpAuthorizedCandidatesCsv = "breakout_retest";
24: input string InpAttachmentLogFileName = "experimental_demo_executor_signal_log.csv";
25: input string InpStartupLogFileName = "experimental_demo_executor_startup.csv";
26: input string InpOrderLogFileName = "experimental_demo_executor_order_log.csv";
27: input string InpKillSwitchFileName = "experimental_demo_kill_switch.txt";
28: input double InpFixedLot = 0.01;
29: input int InpMaxOrdersPerDay = 12;
30: input int InpMaxAccountOrdersPerDay = 24;
31: input int InpMinSecondsBetweenOrders = 300;
32: input int InpMaxOpenPositionsPerInstance = 1;
33: input int InpMaxAccountOpenPositions = 3;
34: input int InpDeviationPoints = 50;
35: input double InpMaxEstimatedCostR = 0.30;
36: input double InpMaxMeasuredSpreadPoints = 75.0;
```

## Boundary

A PASS here means the quarantined experimental executor source matches the documented guard set. It does not make the executor canonical Phase 2 evidence.
