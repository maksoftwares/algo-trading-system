# A3 ML Observer Deploy Status

Overall status: DEPLOYED_PASSIVE_OBSERVER
Mode: DEPLOY

## Authorization

- Passive observer deploy requested: true.
- Passive observer deploy attempted: true.
- EA attachment authorized: false.
- Chart or profile change authorized: false.
- Python demo predictions authorized: false.
- Broker action authorized: false.

## Targets

| Account | Login | Data root | Expert | Include | Preset |
| --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\A3MlPredictionObserver.mq5 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3MlEaHandoff.mqh | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A2 | 1033030 | C:\MT5PortableTier1BestEA | C:\MT5PortableTier1BestEA\MQL5\Experts\A3MlPredictionObserver.mq5 | C:\MT5PortableTier1BestEA\MQL5\Include\A3MlEaHandoff.mqh | C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A3 | 1033669 | C:\MT5PortableRepairLane | C:\MT5PortableRepairLane\MQL5\Experts\A3MlPredictionObserver.mq5 | C:\MT5PortableRepairLane\MQL5\Include\A3MlEaHandoff.mqh | C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |

## Compile

- Attempted: true.
- Passed: true.
- MetaEditor: C:\Program Files\MetaTrader 5\MetaEditor64.exe.
- Scratch source: C:\MT5CompileScratch\A3MlPredictionObserverC09\run_2026_06_21T18_20_10Z\MQL5\Experts\A3MlPredictionObserver.mq5.
- EX5 path: C:\MT5CompileScratch\A3MlPredictionObserverC09\run_2026_06_21T18_20_10Z\MQL5\Experts\A3MlPredictionObserver.ex5.
- Log path: C:\MT5CompileScratch\A3MlPredictionObserverC09\run_2026_06_21T18_20_10Z\compile_A3MlPredictionObserver.log.
- Detail: scratch compile produced EX5 with 0 errors.

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| registry_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\config\ml\mt5_accounts.yaml |
| registry_parses | true | accounts=A1,A2,A3 |
| all_accounts_have_data_roots | true | A1=C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075; A2=C:/MT5PortableTier1BestEA; A3=C:/MT5PortableRepairLane |
| all_target_paths_safe | true | A1=True; A2=True; A3=True |
| observer_source_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\A3MlPredictionObserver.mq5 |
| handoff_include_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Include\A3MlEaHandoff.mqh |
| passive_preset_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| scratch_compile_passed | true | scratch compile produced EX5 with 0 errors |

## Deployed Files

- C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\A3MlPredictionObserver.mq5
- C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3MlEaHandoff.mqh
- C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\A3MlPredictionObserver.ex5
- C:\MT5PortableTier1BestEA\MQL5\Experts\A3MlPredictionObserver.mq5
- C:\MT5PortableTier1BestEA\MQL5\Include\A3MlEaHandoff.mqh
- C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- C:\MT5PortableTier1BestEA\MQL5\Experts\A3MlPredictionObserver.ex5
- C:\MT5PortableRepairLane\MQL5\Experts\A3MlPredictionObserver.mq5
- C:\MT5PortableRepairLane\MQL5\Include\A3MlEaHandoff.mqh
- C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- C:\MT5PortableRepairLane\MQL5\Experts\A3MlPredictionObserver.ex5

## Boundary

- MT5 connection attempted: false.
- Terminal runtime change authorized: false.
- Profile or chart change authorized: false.
- EA source deploy attempted: true.
- Broker action authorized: false.

## Next

Passive observer files are copied. Attach only with the passive preset; Python predictions still require C03 PASS, C05 trained model, C04 shadow bridge, and C06 handoff.
