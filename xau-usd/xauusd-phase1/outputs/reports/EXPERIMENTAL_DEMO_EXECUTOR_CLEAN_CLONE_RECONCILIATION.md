# Experimental Demo Executor Clean-Clone Reconciliation

Overall status: PASS

This clean-clone reconciliation proves the public GitHub source at the recorded commit. It does not authorize canonical Phase 2, demo execution, broker execution, or live capital.

Repo URL: `https://github.com/maksoftwares/algo-trading-system.git`
Branch: `main`
Clean-clone commit hash: `0363fe40a1b6c42cba294b69b46858ad773dd254`
Source path: `xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5`
Source SHA256: `cc2d330876ee9376e154a5133ebcbc01d1c15ec033aecd48d19db57ee76bf5cd`
Governance doc SHA256: `7766c50c0a75c2f94a7671466dd8781b57a2a32ccb15f85fe3f488eb63ea0cd8`
Parity report SHA256: `848c100282522d374b2e07893e3decd1682fe96c4e30f382b42c8b1965012083`

## Required Source Tokens

| Token | Status | Line |
| --- | --- | --- |
| InpAllowedAccountLoginsCsv | PASS | 20 |
| InpExperimentalAuthorizationToken | PASS | 21 |
| InpAuthorizedCandidatesCsv | PASS | 23 |
| InpMaxAccountOrdersPerDay | PASS | 30 |
| InpMaxAccountOpenPositions | PASS | 33 |
| InpKillSwitchFileName | PASS | 27 |
| InpMaxEstimatedCostR | PASS | 35 |
| InpMaxMeasuredSpreadPoints | PASS | 36 |
| OrderSend | PASS | 1132 |

## Packaging Proof

| Check | Status | Evidence |
| --- | --- | --- |
| canonical_deploy_excludes_experimental_executor | PASS | xau-usd/xauusd-phase1/scripts/deploy_phase1_mt5.py |
| parity_report_committed | PASS | xau-usd/xauusd-phase1/outputs/reports/EXPERIMENTAL_DEMO_EXECUTOR_SOURCE_GOVERNANCE_PARITY.md |
| governance_doc_committed | PASS | xau-usd/xauusd-phase1/docs/EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md |

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

Experimental demo executor lane remains QUARANTINE / NO DEPLOYMENT / REVIEW ONLY.
