# P2WEAKNESS BR V1 Clean-Clone Reconciliation

Status: PASS

Remote clean-clone proof for P2WEAKNESS_BR_V1. This clones the configured branch and validates the pushed source, presets, scripts, and parser boundaries. It does not deploy, attach charts, touch MT5 runtime, authorize canonical Phase 2, or authorize real capital.

Created at UTC: `2026-06-08T08:26:01.892626Z`

- Repo URL: `https://github.com/maksoftwares/algo-trading-system.git`
- Branch: `main`
- Clean-clone commit hash: `3290211102f59f8002dd73f21a39bc91a9b3cfec`
- Local repo HEAD: `3290211102f59f8002dd73f21a39bc91a9b3cfec`
- Clone working tree status: ``
- Local parity status: `PASS`
- Local magic collision status: `PASS`
- Clone parity status: `PASS`
- Clone magic collision status: `PASS`
- Source path: `xau-usd/xauusd-phase1/mt5/Experts/Phase2WeaknessBreakoutRetestExecutor.mq5`
- Source SHA256: `aa92344a8b3e8c74a21443073333a2381e939187b4a5b874287c65fb5f4ec2a7`
- Clone source SHA256: `aa92344a8b3e8c74a21443073333a2381e939187b4a5b874287c65fb5f4ec2a7`
- Owner template SHA256: `018ec324bfdf8904998d927adc7654da8fb22ef5529ec71fea24f5cab9c3ee66`
- Clone owner template SHA256: `018ec324bfdf8904998d927adc7654da8fb22ef5529ec71fea24f5cab9c3ee66`
- Failed checks: `0`

## Checks

| Check | Status | Evidence |
|---|---|---|
| clone_working_tree_clean | PASS | git status --short='' |
| clone_parity_pass | PASS | clone parity=PASS |
| clone_magic_pass | PASS | clone magic=PASS |
| legacy_owner_authorized_set_absent | PASS | legacy executing preset absent |
| owner_template_committed_non_executing | PASS | template dry-run=true; broker action=false |
| deploy_script_report_only_default | PASS | all required tokens present |
| deploy_script_requires_preconditions | PASS | all required tokens present |
| portable_setup_no_runtime_defaults | PASS | all required tokens present |
| dashboard_includes_p2weakness_actual_trades | PASS | all required tokens present |

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

## Boundary

This proof validates the pushed clean clone only. It does not deploy, attach charts, touch MT5 runtime, authorize canonical Phase 2, or authorize real capital.
