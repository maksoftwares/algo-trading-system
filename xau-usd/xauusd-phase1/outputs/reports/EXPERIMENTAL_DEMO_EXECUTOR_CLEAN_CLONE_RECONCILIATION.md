# Experimental Demo Executor Clean-Clone Reconciliation

Overall status: PASS

This clean-clone reconciliation proves the public GitHub source at the recorded commit. It does not authorize canonical Phase 2, demo execution, broker execution, or live capital.

Repo URL: `https://github.com/maksoftwares/algo-trading-system.git`
Branch: `main`
Clean-clone commit hash: `082796fae4367dcad1d0e95ee1d494abbfe9f7d3`
Source path: `xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5`
Source SHA256: `765c66be2ad026e02625edf6a779884ab80a2cfd71cbe9d97256d5219972a451`
Governance doc SHA256: `fbf8ab5c25721ba62844dbfcf5142c1a50ad1109169a376b4448c5b7b7de06d3`
Parity report SHA256: `080e23aaeb3f06e7afdce46d5a8761ce75a350e86605b051176c00f50949a7bb`

## Required Source Tokens

| Token | Status | Line |
| --- | --- | --- |
| InpAllowedAccountLoginsCsv | PASS | 21 |
| InpExperimentalAuthorizationToken | PASS | 22 |
| InpCostSuspensionAcknowledgementToken | PASS | 24 |
| InpCandidateStatus | PASS | 16 |
| InpFamilyLifecycleStatus | PASS | 17 |
| InpAuthorizedCandidatesCsv | PASS | 26 |
| InpMaxAccountOrdersPerDay | PASS | 33 |
| InpMaxAccountOpenPositions | PASS | 36 |
| InpKillSwitchFileName | PASS | 30 |
| InpMaxEstimatedCostR | PASS | 38 |
| InpMaxMeasuredSpreadPoints | PASS | 39 |
| OrderSend | PASS | 1169 |

## Packaging Proof

| Check | Status | Evidence |
| --- | --- | --- |
| canonical_deploy_excludes_experimental_executor | PASS | xau-usd/xauusd-phase1/scripts/deploy_phase1_mt5.py |
| parity_report_committed | PASS | xau-usd/xauusd-phase1/outputs/reports/EXPERIMENTAL_DEMO_EXECUTOR_SOURCE_GOVERNANCE_PARITY.md |
| governance_doc_committed | PASS | xau-usd/xauusd-phase1/docs/EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md |

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

Experimental demo executor lane remains QUARANTINE / NO DEPLOYMENT / REVIEW ONLY.
