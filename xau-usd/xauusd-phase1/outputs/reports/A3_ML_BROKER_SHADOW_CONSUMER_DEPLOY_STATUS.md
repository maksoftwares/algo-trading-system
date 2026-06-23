# A3 ML Broker Shadow Consumer Deploy Status

Overall status: DEPLOYED_COMPILED_SHADOW_CONSUMERS
Dataset version: xauusd_c02_multiacct_202606211549_geffebb6d_c9221d066

## Authorization

- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Compile

- Attempted: true.
- Passed: true.
- MetaEditor: C:\Program Files\MetaTrader 5\MetaEditor64.exe.

| Source | Passed | Detail |
| --- | --- | --- |
| Account3BreakoutImprovedExecutor.mq5 | true | compiled with 0 errors |
| Account3BreakoutPlainExecutor.mq5 | true | compiled with 0 errors |
| Account3BreakoutTier1CompatExecutor.mq5 | true | compiled with 0 errors |
| Account3SoftRetestExecutor.mq5 | true | compiled with 0 errors |
| Phase2ExperimentalDemoExecutor.mq5 | true | compiled with 0 errors |
| Phase2ExperimentalDemoRepairExecutor.mq5 | true | compiled with 0 errors |

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| registry_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\config\ml\mt5_accounts.yaml |
| registry_parses | true | A1,A2,A3 |
| all_target_paths_safe | true | A1=True; A2=True; A3=True |
| repo_include_dir_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Include |
| source_exists_Account3BreakoutImprovedExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3BreakoutImprovedExecutor.mq5 |
| source_exists_Account3BreakoutPlainExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3BreakoutPlainExecutor.mq5 |
| source_exists_Account3BreakoutTier1CompatExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3BreakoutTier1CompatExecutor.mq5 |
| source_exists_Account3SoftRetestExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3SoftRetestExecutor.mq5 |
| source_exists_Phase2ExperimentalDemoExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5 |
| source_exists_Phase2ExperimentalDemoRepairExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoRepairExecutor.mq5 |
| shadow_tap_include_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Include\A3MlShadowTap.mqh |
| handoff_include_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Include\A3MlEaHandoff.mqh |
| scratch_compile_passed | true | all broker shadow consumers compiled with 0 errors |

## Deployed Files

- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3BreakoutExecutorBase.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3MlEaHandoff.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3MlShadowTap.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\DirectionStateShadow.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1BreakoutRetest.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Dashboard.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Execution.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1FeatureEngine.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Lifecycle.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Logger.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Magic.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1MarketData.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1News.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Risk.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Router.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1ServerTime.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Session.mqh
- A1 include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\Phase1\Phase1Types.mqh
- A1 expert_source: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Phase2ExperimentalDemoExecutor.mq5
- A1 compiled_ex5: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Phase2ExperimentalDemoExecutor.ex5
- A1 expert_source: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Phase2ExperimentalDemoRepairExecutor.mq5
- A1 compiled_ex5: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\Phase2ExperimentalDemoRepairExecutor.ex5
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\A3BreakoutExecutorBase.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\A3MlEaHandoff.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\A3MlShadowTap.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\DirectionStateShadow.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1BreakoutRetest.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Dashboard.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Execution.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1FeatureEngine.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Lifecycle.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Logger.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Magic.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1MarketData.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1News.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Risk.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Router.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1ServerTime.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Session.mqh
- A2 include: C:\MT5PortableTier1BestEA\MQL5\Include\Phase1\Phase1Types.mqh
- A2 expert_source: C:\MT5PortableTier1BestEA\MQL5\Experts\Phase2ExperimentalDemoExecutor.mq5
- A2 compiled_ex5: C:\MT5PortableTier1BestEA\MQL5\Experts\Phase2ExperimentalDemoExecutor.ex5
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\A3BreakoutExecutorBase.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\A3MlEaHandoff.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\A3MlShadowTap.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\DirectionStateShadow.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1BreakoutRetest.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Dashboard.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Execution.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1FeatureEngine.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Lifecycle.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Logger.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Magic.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1MarketData.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1News.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Risk.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Router.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1ServerTime.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Session.mqh
- A3 include: C:\MT5PortableRepairLane\MQL5\Include\Phase1\Phase1Types.mqh
- A3 expert_source: C:\MT5PortableRepairLane\MQL5\Experts\Account3BreakoutImprovedExecutor.mq5
- A3 compiled_ex5: C:\MT5PortableRepairLane\MQL5\Experts\Account3BreakoutImprovedExecutor.ex5
- A3 expert_source: C:\MT5PortableRepairLane\MQL5\Experts\Account3BreakoutPlainExecutor.mq5
- A3 compiled_ex5: C:\MT5PortableRepairLane\MQL5\Experts\Account3BreakoutPlainExecutor.ex5
- A3 expert_source: C:\MT5PortableRepairLane\MQL5\Experts\Account3BreakoutTier1CompatExecutor.mq5
- A3 compiled_ex5: C:\MT5PortableRepairLane\MQL5\Experts\Account3BreakoutTier1CompatExecutor.ex5
- A3 expert_source: C:\MT5PortableRepairLane\MQL5\Experts\Account3SoftRetestExecutor.mq5
- A3 compiled_ex5: C:\MT5PortableRepairLane\MQL5\Experts\Account3SoftRetestExecutor.ex5

## Boundary

- MT5 connection attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- Expert file deploy attempted: true.
- Compiled EX5 deploy attempted: true.
- Broker action authorized: false.

## Next

Rerun C16. The active broker EAs should now be able to read and log ML handoff in shadow-only mode; Python prediction authority still depends on C03/C05/C04/C06 readiness.
