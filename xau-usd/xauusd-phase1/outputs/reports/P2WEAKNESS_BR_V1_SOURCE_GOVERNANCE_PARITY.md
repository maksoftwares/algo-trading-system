# P2WEAKNESS BR V1 Source Governance Parity

Status: PASS

P2WEAKNESS_BR_V1 governance parity only; no canonical Phase 2, paper-mode, live, or real-capital authorization.

Created at UTC: `2026-06-08T08:24:30.265166Z`

- Source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2WeaknessBreakoutRetestExecutor.mq5`
- Safe preset: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Presets\Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set`
- Owner-authorized template: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Presets\Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.template.set`
- Failed checks: `0`

| Check | Status | Evidence |
|---|---|---|
| non_canonical_banner | PASS | all required tokens present |
| InpDryRunOnly_default | PASS | actual='true'; expected='true' |
| InpBrokerActionAllowed_default | PASS | actual='false'; expected='false' |
| InpAllowedAccountLoginsCsv_default | PASS | actual=''; expected='' |
| InpExperimentalAuthorizationToken_default | PASS | actual=''; expected='' |
| InpCostSuspensionAcknowledgementToken_default | PASS | actual=''; expected='' |
| InpCandidateStatus_default | PASS | actual='EXPERIMENTAL_QUARANTINE_REVIEW_ONLY'; expected='EXPERIMENTAL_QUARANTINE_REVIEW_ONLY' |
| InpFamilyLifecycleStatus_default | PASS | actual='COST_SUSPENDED_CANONICAL'; expected='COST_SUSPENDED_CANONICAL' |
| InpMagicNumber_default | PASS | actual='931000'; expected='931000' |
| safe_preset_dry_run | PASS | InpDryRunOnly='true'; expected='true' |
| safe_preset_broker_action_disabled | PASS | InpBrokerActionAllowed='false'; expected='false' |
| owner_template_dry_run | PASS | InpDryRunOnly='true'; expected='true' |
| owner_template_broker_action_disabled | PASS | InpBrokerActionAllowed='false'; expected='false' |
| owner_template_account_placeholder | PASS | InpAllowedAccountLoginsCsv='<OWNER_TO_FILL>'; expected='<OWNER_TO_FILL>' |
| owner_template_auth_placeholder | PASS | InpExperimentalAuthorizationToken='<OWNER_TO_FILL>'; expected='<OWNER_TO_FILL>' |
| owner_template_cost_ack_placeholder | PASS | InpCostSuspensionAcknowledgementToken='<OWNER_TO_FILL>'; expected='<OWNER_TO_FILL>' |
| owner_template_magic | PASS | InpMagicNumber='931000'; expected='931000' |
| cost_suspension_ack_guard | PASS | all required tokens present |
| kill_switch_present | PASS | all required tokens present |
| demo_server_refusal | PASS | all required tokens present |
| cost_r_guard | PASS | all required tokens present |
| spread_guard | PASS | all required tokens present |
| market_proxy_logged | PASS | all required tokens present |
| duplicate_family_suppression | PASS | all required tokens present |
| startup_safe_default_flags | PASS | all required tokens present |
| runtime_notes_updated | PASS | all required tokens present |
| registry_updated | PASS | all required tokens present |
| fixed_lot_lte_0_01 | PASS | InpFixedLot=0.01 |

## Input Declaration Block

```mql5
11: input string InpRunId = "P2WEAKNESS_BR_V1";
12: input bool InpDryRunOnly = true;
13: input bool InpBrokerActionAllowed = false;
14: input string InpTargetSymbol = "XAUUSD";
15: input string InpExpectedServerMarker = "Demo";
16: input string InpAllowedAccountLoginsCsv = "";
17: input string InpExperimentalAuthorizationToken = "";
18: input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
19: input string InpCostSuspensionAcknowledgementToken = "";
20: input string InpRequiredCostSuspensionAcknowledgementToken = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT";
21: input string InpCandidateStatus = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY";
22: input string InpFamilyLifecycleStatus = "COST_SUSPENDED_CANONICAL";
23: input string InpKillSwitchFileName = "p2weakness_br_v1_kill_switch.txt";
24: input string InpSignalLogFileName = "p2weakness_br_v1_signal_log_xauusd.csv";
25: input string InpStartupLogFileName = "p2weakness_br_v1_startup_xauusd.csv";
26: input string InpOrderLogFileName = "p2weakness_br_v1_order_log_xauusd.csv";
27: input double InpFixedLot = 0.01;
28: input int InpMagicNumber = 931000;
29: input int InpMaxOrdersPerDay = 6;
30: input int InpMaxAccountOrdersPerDay = 12;
31: input int InpMinSecondsBetweenOrders = 300;
32: input int InpMaxOpenPositionsPerInstance = 1;
33: input int InpMaxFamilyOpenPositions = 3;
34: input int InpDuplicateLockBars = 12;
35: input int InpDeviationPoints = 50;
36: input double InpMaxEstimatedCostR = 0.30;
37: input double InpMaxMeasuredSpreadPoints = 75.0;
```
