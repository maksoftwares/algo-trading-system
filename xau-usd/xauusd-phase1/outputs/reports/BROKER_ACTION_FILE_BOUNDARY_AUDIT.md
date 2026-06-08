# Broker Action File Boundary Audit

Overall status: PASS

This audit classifies broker-action MQL files. A PASS does not authorize Phase 2, demo execution, broker execution, or live capital.

Findings: 0

## MQL File Classification

| File | Classification | Terms | Status | Evidence |
| --- | --- | --- | --- | --- |
| xau-usd\xauusd-phase0\mt5\PassiveBarExporter_Phase0.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase0\mt5\PassiveSpreadLogger_XAUUSD.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Experts\Phase1DryRunShell.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5 | approved_experimental_quarantined | OrderSend | PASS | guarded experimental broker-action file |
| xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoObserver.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Experts\Phase2ShadowFixObserver.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Experts\Phase2WeaknessBreakoutRetestExecutor.mq5 | approved_experimental_quarantined | OrderSend | PASS | guarded experimental broker-action file |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1BreakoutRetest.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Dashboard.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Execution.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1FeatureEngine.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Lifecycle.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Logger.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Magic.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1MarketData.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1News.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Risk.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Router.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1ServerTime.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Session.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase1\mt5\Include\Phase1\Phase1Types.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Experts\Phase2B_D1CompressionH4Expansion_Observer.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Experts\Phase2B_H4TrendPullbackD1Bias_Observer.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Experts\Phase2B_WeeklyLevelH4Rejection_Observer.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Include\CandidateCostProjection.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Include\CandidateCsvLogger.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Include\CandidateObserverCommon.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Include\CandidateSafetyGuard.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-phase2b-passive-observers\mt5\Include\CandidateSessionClock.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Experts\WR50_BreakoutEvening_v0.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Experts\WR50_BreakoutExit1R_v0.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Experts\WR50_BreakoutQuality_v0.mq5 | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_AccountGuard.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_BreakoutRetestSignal.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_Common.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_FileUtil.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_MagicNumbers.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_OrderExecutor.mqh | approved_experimental_quarantined | OrderSend | PASS | guarded experimental broker-action file |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_RiskGuard.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_SessionFilter.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_SpreadGuard.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_TradeLogger.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |
| xau-usd\xauusd-wr50-experimental\mt5\Include\WR50_Types.mqh | canonical_or_passive_no_broker_action | none | PASS | No broker-action tokens. |

## Packaging Checks

| Check | Status | Evidence |
| --- | --- | --- |
| canonical_deploy_excludes_experimental_executor | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\deploy_phase1_mt5.py |
| phase1_review_bundle_is_non_authorizing_if_it_contains_sources | PASS | Phase 1 review bundle is evidence-only; canonical deploy script is the deploy authority. |

## Boundary

Experimental broker-action code remains quarantined and non-canonical.
