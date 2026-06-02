# Experimental Demo Executor Clean-Clone Reconciliation

Overall status: PASS

This clean-clone reconciliation proves the public GitHub source at the recorded commit. It does not authorize canonical Phase 2, demo execution, broker execution, or live capital.

Repo URL: `https://github.com/maksoftwares/algo-trading-system.git`
Branch: `main`
Clean-clone commit hash: `78921f3f6143e4ec37e9adae10bffa307cf89020`
Source path: `xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5`
Source SHA256: `0073b43363117ebf442e85379b33f2a4df65515684049f5262b4d292059ca54f`
Governance doc SHA256: `7766c50c0a75c2f94a7671466dd8781b57a2a32ccb15f85fe3f488eb63ea0cd8`
Parity report SHA256: `6be387e8e3213fb3afeeeee36331190a39ced60d6688aa95f5cde2b5f87d594f`

## Required Source Tokens

| Token | Status | Line |
| --- | --- | --- |
| InpAllowedAccountLoginsCsv | PASS | 16 |
| InpExperimentalAuthorizationToken | PASS | 17 |
| InpAuthorizedCandidatesCsv | PASS | 19 |
| InpMaxAccountOrdersPerDay | PASS | 26 |
| InpMaxAccountOpenPositions | PASS | 29 |
| InpKillSwitchFileName | PASS | 23 |
| InpMaxEstimatedCostR | PASS | 31 |
| InpMaxMeasuredSpreadPoints | PASS | 32 |
| OrderSend | PASS | 1128 |

## Packaging Proof

| Check | Status | Evidence |
| --- | --- | --- |
| canonical_deploy_excludes_experimental_executor | PASS | xau-usd/xauusd-phase1/scripts/deploy_phase1_mt5.py |
| parity_report_committed | PASS | xau-usd/xauusd-phase1/outputs/reports/EXPERIMENTAL_DEMO_EXECUTOR_SOURCE_GOVERNANCE_PARITY.md |
| governance_doc_committed | PASS | xau-usd/xauusd-phase1/docs/EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md |

## Input Declaration Block

```mql5
8: input string InpRunId = "phase2-experimental-demo-executor-v0.1";
9: input bool InpDryRunOnly = false;
10: input bool InpBrokerActionAllowed = false;
11: input string InpCandidate = "breakout_retest";
12: input string InpCandidateStatus = "ACCEPTED";
13: input string InpTargetSymbol = "XAUUSD";
14: input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,USDJPY";
15: input string InpExpectedServerMarker = "Demo";
16: input string InpAllowedAccountLoginsCsv = "";
17: input string InpExperimentalAuthorizationToken = "";
18: input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
19: input string InpAuthorizedCandidatesCsv = "breakout_retest";
20: input string InpAttachmentLogFileName = "experimental_demo_executor_signal_log.csv";
21: input string InpStartupLogFileName = "experimental_demo_executor_startup.csv";
22: input string InpOrderLogFileName = "experimental_demo_executor_order_log.csv";
23: input string InpKillSwitchFileName = "experimental_demo_kill_switch.txt";
24: input double InpFixedLot = 0.01;
25: input int InpMaxOrdersPerDay = 12;
26: input int InpMaxAccountOrdersPerDay = 24;
27: input int InpMinSecondsBetweenOrders = 300;
28: input int InpMaxOpenPositionsPerInstance = 1;
29: input int InpMaxAccountOpenPositions = 3;
30: input int InpDeviationPoints = 50;
31: input double InpMaxEstimatedCostR = 0.30;
32: input double InpMaxMeasuredSpreadPoints = 75.0;
```

## Boundary

Experimental demo executor lane remains QUARANTINE / NO DEPLOYMENT / REVIEW ONLY.
