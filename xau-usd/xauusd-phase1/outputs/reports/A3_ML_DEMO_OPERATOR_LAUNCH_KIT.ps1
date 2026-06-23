$ErrorActionPreference = 'Stop'
$Python = 'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$Root = 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'

Write-Host 'A3 ML demo attach kit'
Write-Host 'This script does not launch MT5, change profiles, or authorize broker action.'
Write-Host ''
Write-Host 'Attach matrix:'
Write-Host @'
A1 1025742
  Terminal: C:/Program Files/MetaTrader 5/terminal64.exe
  Observer: A3MlPredictionObserver
  Observer preset: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
  Broker-shadow:
    - Phase2ExperimentalDemoExecutor using Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set
    - Phase2ExperimentalDemoRepairExecutor using Phase2ExperimentalDemoRepairExecutor.A1.a3_ml_shadow_readonly.set
  Watch log: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a3_ml_broker_shadow_tap.csv

A2 1033030
  Terminal: C:/MT5PortableTier1BestEA/terminal64.exe
  Observer: A3MlPredictionObserver
  Observer preset: C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
  Broker-shadow:
    - Phase2ExperimentalDemoExecutor using Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set
  Watch log: C:\MT5PortableTier1BestEA\MQL5\Files\a3_ml_broker_shadow_tap.csv

A3 1033669
  Terminal: C:/MT5PortableRepairLane/terminal64.exe
  Observer: A3MlPredictionObserver
  Observer preset: C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
  Broker-shadow:
    - Account3BreakoutImprovedExecutor using Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set
    - Account3BreakoutPlainExecutor using Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set
    - Account3BreakoutTier1CompatExecutor using Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set
    - Account3SoftRetestExecutor using Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set
  Watch log: C:\MT5PortableRepairLane\MQL5\Files\a3_ml_broker_shadow_tap.csv
'@
Write-Host ''
Write-Host 'Current C31 status: WAITING_FOR_MANUAL_ATTACH'
Write-Host 'Start/continue MT5 manual attach, then leave this watcher running.'
& $Python 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c31_watch_demo_attach.py' --root $Root --timeout-seconds 300 --poll-seconds 5
Write-Host ''
Write-Host 'If C31 reports ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS, run the final C28 proof:'
Write-Host ("& 'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c28_wait_for_demo_shadow_post_attach.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --timeout-seconds 300 --poll-seconds 5")
