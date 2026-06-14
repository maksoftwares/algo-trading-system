# TIER1 BREAKOUT SOLO ACTIVATION REPORT 2026-06-14

Created at Dubai time: `2026-06-14 18:26 +04:00`

Authority: `CODEX_WORK_ORDER_TIER1_BREAKOUT_SOLO_ACTIVATION_2026_06_14.md`

## Plain Answer

Yes: the best EA was already running separately before this work order.

- A2 solo terminal: `C:\MT5PortableTier1BestEA`
- Account: `1033030 / Capital.ComMena-Demo / AED`
- EA: `Phase2ExperimentalDemoExecutor`
- Candidate: `breakout_retest`
- Symbol/timeframe: `XAUUSD,M5`
- Magic: `920101`
- Runtime arming: `InpDryRunOnly=false`, `InpBrokerActionAllowed=true`
- Latest clean attach after verification: `2026-06-14 18:24:19 Dubai`, startup status `ATTACHED_DEMO_EXECUTOR_ENABLED`
- Current open A2 positions/orders after verification: `0 / 0`

No activation flag change was required because the local owner preset was already armed. A2 was restarted only for the kill-switch proof, then restored. A1 and A3 were not modified.

## Acceptance Status

| Item | Status | Evidence |
|---|---|---|
| A2 account/path assumption | PASS | `C:\MT5PortableTier1BestEA` is login `1033030`, server `Capital.ComMena-Demo` |
| A2 solo breakout attached | PASS | Startup CSV final row `ATTACHED_DEMO_EXECUTOR_ENABLED` |
| A2 XAUUSD-only | PASS | Startup config `Symbol=XAUUSD`; preset `InpTargetSymbol=XAUUSD`, `InpQualifiedSymbolsCsv=XAUUSD` |
| A2 armed on demo | PASS | Local preset `InpDryRunOnly=false`, `InpBrokerActionAllowed=true`; server marker `Demo`; live/real refused in source |
| A2 kill switch | PASS | With kill file present, init failed/EA removed; after removal, attached cleanly |
| A1 untouched | PASS | Account `1025742` still kitchen-sink, 8 positions, no process/profile change by this work |
| A3 untouched | PASS | Account `1033669` still repair lane with exactly two A3 EAs, 0 positions/orders |
| Execution-enabled preset committed | PASS | Local owner preset is outside repo; git status shows no committed executing preset |
| Separate A2 AccountEquityGuardianShadow | NOT PRESENT | No guardian files/logs in `C:\MT5PortableTier1BestEA`; not attached to avoid violating one-EA lane without a clearer owner instruction |

## Terminal Inventory

| Terminal path | Login/server | Purpose / EA evidence | Exposure |
|---|---|---|---|
| `C:\Program Files\MetaTrader 5\terminal64.exe` | `1025742 / Capital.ComMena-Demo` | A1 kitchen-sink; many Phase2/WR50/repair/equity-guardian EAs loaded | 8 positions, 0 orders |
| `C:\MT5PortableTier1BestEA\terminal64.exe` | `1033030 / Capital.ComMena-Demo` | A2 solo breakout; `Phase2ExperimentalDemoExecutor (XAUUSD,M5)` | 0 positions, 0 orders |
| `C:\MT5PortableTier1PathObserver\terminal64.exe` | `1033030 / Capital.ComMena-Demo` | A2 read-only path observer; `Phase2PositionPathObserver (XAUUSD,M5)` | 0 positions, 0 orders |
| `C:\MT5PortableRepairLane\terminal64.exe` | `1033669 / Capital.ComMena-Demo` | A3 repair lane; `Account3RoundRetestGuardedExecutor` + `Account3RoundRetestStructuredExecutor` | 0 positions, 0 orders |
| `C:\MT5PortablePositionPathObserver\terminal64.exe` | `1025742 / Capital.ComMena-Demo` | A1 read-only position path observer | 8 positions, 0 orders |
| `C:\MT5PortableShadowFixObservers\terminal64.exe` | `1025742 / Capital.ComMena-Demo` | A1 shadow fix observers | 8 positions, 0 orders |
| `C:\MT5PortableTrendGuardedFixObservers\terminal64.exe` | `1025742 / Capital.ComMena-Demo` | A1 trend guarded observers | 8 positions, 0 orders |
| `C:\MT5PortableGoldMission\terminal64.exe` | `1033669 / Capital.ComMena-Demo` | Phase1 dry-run shell/support terminal | 0 positions, 0 orders |
| `C:\MT5PortableSpreadLogger\terminal64.exe` | `121409 / Capital.ComMena-Live` | Passive spread logger/support terminal | 0 positions, 0 orders |

## Raw Evidence

### Current Time

Command:

```powershell
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

Output:

```text
2026-06-14 18:20:27 +04:00
```

### Running Terminal Processes

Command:

```powershell
Get-CimInstance Win32_Process -Filter "name='terminal64.exe'" |
  Select-Object ProcessId, ExecutablePath, CommandLine, CreationDate |
  Sort-Object ExecutablePath | Format-List
```

Output excerpt:

```text
ProcessId      : 8780
ExecutablePath : C:\MT5PortableTier1BestEA\terminal64.exe
CommandLine    : "C:\MT5PortableTier1BestEA\terminal64.exe" /portable
                 /config:C:\MT5PortableTier1BestEA\Config\tier1_bestea_startup.ini
CreationDate   : 6/13/2026 3:00:57 AM

ProcessId      : 21660
ExecutablePath : C:\MT5PortableRepairLane\terminal64.exe
CommandLine    : "C:\MT5PortableRepairLane\terminal64.exe" /portable
                 /config:C:\MT5PortableRepairLane\Config\a3_arm_attach_startup.ini
CreationDate   : 6/14/2026 3:02:27 AM

ProcessId      : 17676
ExecutablePath : C:\Program Files\MetaTrader 5\terminal64.exe
CommandLine    : "C:\Program Files\MetaTrader 5\terminal64.exe"
CreationDate   : 6/14/2026 12:18:49 AM
```

Full process set also included `C:\MT5PortableGoldMission`, `C:\MT5PortablePositionPathObserver`, `C:\MT5PortableShadowFixObservers`, `C:\MT5PortableSpreadLogger`, `C:\MT5PortableTier1PathObserver`, and `C:\MT5PortableTrendGuardedFixObservers`.

### MT5 Account/Exposure Query

Command:

```powershell
@'
import MetaTrader5 as mt5
paths = {
 'A1_installed_kitchen_sink': r'C:\Program Files\MetaTrader 5\terminal64.exe',
 'A2_tier1_best_ea': r'C:\MT5PortableTier1BestEA\terminal64.exe',
 'A2_tier1_path_observer': r'C:\MT5PortableTier1PathObserver\terminal64.exe',
 'A3_repair_lane': r'C:\MT5PortableRepairLane\terminal64.exe',
}
for name,path in paths.items():
    print('===', name, path)
    ok = mt5.initialize(path=path)
    print('initialize', ok, 'last_error', mt5.last_error())
    info = mt5.account_info() if ok else None
    if info:
        print('login', info.login, 'server', info.server, 'currency', info.currency, 'balance', info.balance, 'equity', info.equity, 'trade_allowed', info.trade_allowed, 'trade_expert', getattr(info,'trade_expert',None))
    positions = mt5.positions_get() if ok else None
    orders = mt5.orders_get() if ok else None
    print('positions_count', None if positions is None else len(positions))
    print('orders_count', None if orders is None else len(orders))
    mt5.shutdown()
'@ | & 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' -
```

Output:

```text
=== A1_installed_kitchen_sink C:\Program Files\MetaTrader 5\terminal64.exe
initialize True last_error (1, 'Success')
login 1025742 server Capital.ComMena-Demo currency AED balance 2367.9 equity 2387.1 trade_allowed True trade_expert True
positions_count 8
orders_count 0
=== A2_tier1_best_ea C:\MT5PortableTier1BestEA\terminal64.exe
initialize True last_error (1, 'Success')
login 1033030 server Capital.ComMena-Demo currency AED balance 4055.21 equity 4055.21 trade_allowed True trade_expert True
positions_count 0
orders_count 0
=== A2_tier1_path_observer C:\MT5PortableTier1PathObserver\terminal64.exe
initialize True last_error (1, 'Success')
login 1033030 server Capital.ComMena-Demo currency AED balance 4055.21 equity 4055.21 trade_allowed True trade_expert True
positions_count 0
orders_count 0
=== A3_repair_lane C:\MT5PortableRepairLane\terminal64.exe
initialize True last_error (1, 'Success')
login 1033669 server Capital.ComMena-Demo currency AED balance 4000.0 equity 4000.0 trade_allowed True trade_expert True
positions_count 0
orders_count 0
```

### A2 Startup Config

Command:

```powershell
Get-Content -Path 'C:\MT5PortableTier1BestEA\Config\tier1_bestea_startup.ini'
```

Output:

```ini
[Common]
Login=1033030
Server=Capital.ComMena-Demo
ProxyEnable=0
NewsEnable=0

[Charts]
MaxBars=999999999

[Experts]
AllowLiveTrading=1
AllowDllImport=0
Enabled=1
Account=0
Profile=0

[StartUp]
Expert=Phase2ExperimentalDemoExecutor
ExpertParameters=Phase2ExperimentalDemoExecutor.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set
Symbol=XAUUSD
Period=M5
ShutdownTerminal=0
```

### A2 Local Owner Preset Key Inputs

Command:

```powershell
Select-String -Path 'C:\MT5PortableTier1BestEA\MQL5\Presets\Phase2ExperimentalDemoExecutor.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set' `
  -Pattern 'InpDryRunOnly|InpBrokerActionAllowed|InpCandidate=|InpTargetSymbol|InpQualifiedSymbolsCsv|InpAllowedAccountLoginsCsv|InpExpectedServerMarker|InpFixedLot|InpMaxOpenPositionsPerInstance|InpTradeSessionGateEnabled|InpTradeSessionStartHour|InpTradeSessionEndHour|InpKillSwitchFileName'
```

Output:

```text
InpDryRunOnly=false
InpBrokerActionAllowed=true
InpCandidate=breakout_retest
InpTargetSymbol=XAUUSD
InpQualifiedSymbolsCsv=XAUUSD
InpExpectedServerMarker=Demo
InpAllowedAccountLoginsCsv=1033030
InpKillSwitchFileName=tier1_bestea_kill_switch.txt
InpFixedLot=0.01
InpMaxOpenPositionsPerInstance=1
InpTradeSessionGateEnabled=true
InpTradeSessionStartHour=12
InpTradeSessionEndHour=15
```

### Committed Safe Template vs Local Owner Preset

Command:

```powershell
@'
from pathlib import Path
repo = Path(r'xau-usd\xauusd-phase1\mt5\Presets\Phase2ExperimentalDemoExecutor.tier1_breakout_retest_demo_xauusd.template.set')
local = Path(r'C:\MT5PortableTier1BestEA\MQL5\Presets\Phase2ExperimentalDemoExecutor.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set')
def parse(p):
    out = {}
    for line in p.read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k,v=line.split('=',1)
        out[k]=v
    return out
r=parse(repo); l=parse(local)
print('repo_template', repo)
print('local_owner_preset', local)
print('changed_keys_count', sum(1 for k in sorted(set(r)|set(l)) if r.get(k)!=l.get(k)))
for k in sorted(set(r)|set(l)):
    if r.get(k)!=l.get(k):
        print(k, 'repo=', r.get(k), 'local=', l.get(k))
'@ | & 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' -
```

Output:

```text
repo_template xau-usd\xauusd-phase1\mt5\Presets\Phase2ExperimentalDemoExecutor.tier1_breakout_retest_demo_xauusd.template.set
local_owner_preset C:\MT5PortableTier1BestEA\MQL5\Presets\Phase2ExperimentalDemoExecutor.tier1_breakout_retest.owner_authorized_demo_xauusd.local.set
changed_keys_count 5
InpAllowedAccountLoginsCsv repo= <OWNER_TO_FILL> local= 1033030
InpBrokerActionAllowed repo= false local= true
InpCostSuspensionAcknowledgementToken repo= <OWNER_TO_FILL> local= I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT
InpDryRunOnly repo= true local= false
InpExperimentalAuthorizationToken repo= <OWNER_TO_FILL> local= EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY
```

No strategy parameter, lot, symbol, session, spread/cost, or exposure guard difference was found in this comparison.

### A2 Startup CSV Evidence

Command:

```powershell
Get-Content -Path 'C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_startup_xauusd.csv' -Tail 4
```

Output:

```text
2026.06.12 20:59:57,2026.06.12 23:00:59,2026.06.13 03:00:59,TIER1_BREAKOUT_RETEST_SEPARATE_DEMO_2026_06_10,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
2026.06.12 20:59:57,2026.06.14 14:23:46,2026.06.14 18:23:46,TIER1_BREAKOUT_RETEST_SEPARATE_DEMO_2026_06_10,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,tier1_bestea_kill_switch.txt,REMOVED_REASON_9
2026.06.12 20:59:57,2026.06.14 14:23:57,2026.06.14 18:23:57,TIER1_BREAKOUT_RETEST_SEPARATE_DEMO_2026_06_10,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,tier1_bestea_kill_switch.txt,REMOVED_REASON_8
2026.06.12 20:59:57,2026.06.14 14:24:19,2026.06.14 18:24:19,TIER1_BREAKOUT_RETEST_SEPARATE_DEMO_2026_06_10,Capital.ComMena-Demo,XAUUSD,breakout_retest,EXPERIMENTAL_QUARANTINE_REVIEW_ONLY,COST_SUSPENDED_CANONICAL,XAUUSD,1033030,1033030,breakout_retest,false,true,true,true,true,0,UNLIMITED,0.3000,75.00,tier1_bestea_kill_switch.txt,ATTACHED_DEMO_EXECUTOR_ENABLED
```

Interpretation:

- `18:23:46 Dubai` removal was the intentional restart for kill-switch test setup.
- `18:23:57 Dubai REMOVED_REASON_8` occurred while the kill-switch file was present.
- `18:24:19 Dubai ATTACHED_DEMO_EXECUTOR_ENABLED` confirms final restored live state.

### A2 Kill-Switch Proof

Command:

```powershell
# created C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_kill_switch.txt
# restarted A2, then removed it and restarted A2 again
```

Output excerpt:

```text
A2 kill-switch proof started 2026-06-14 18:23:46 +04:00
targetPath=C:\MT5PortableTier1BestEA\terminal64.exe
startupConfig=C:\MT5PortableTier1BestEA\Config\tier1_bestea_startup.ini
killFile=C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_kill_switch.txt
kill_exists_after_create=True
closing_pid_with_kill=8780
after_kill_restart_process=

Id        : 20692
Path      : C:\MT5PortableTier1BestEA\terminal64.exe
StartTime : 6/14/2026 6:23:54 PM

RN	2	18:23:57.361	Experts	initializing of Phase2ExperimentalDemoExecutor (XAUUSD,M5) failed with code 1
FQ	0	18:23:57.375	Experts	expert Phase2ExperimentalDemoExecutor (XAUUSD,M5) removed

kill_exists_after_remove=False
closing_pid_after_remove=20692
after_restore_process=

Id        : 16408
Path      : C:\MT5PortableTier1BestEA\terminal64.exe
StartTime : 6/14/2026 6:24:16 PM

2026.06.14 18:24:19 ... ATTACHED_DEMO_EXECUTOR_ENABLED
A2 kill-switch proof finished 2026-06-14 18:24:32 +04:00
```

Final kill-switch file check:

```text
False
```

### A2 Trade Ledger / Last Order

Command:

```powershell
# MT5 history query for C:\MT5PortableTier1BestEA\terminal64.exe from 2026-06-10 to 2026-06-14
```

Output excerpt:

```text
account 1033030 Capital.ComMena-Demo AED balance 4055.21 equity 4055.21
open_positions 0
open_orders 0
history_orders_total 14 xau_or_magic920101 14
ORDER 2026-06-12T14:20:00+00:00 2026-06-12 18:20:00 Dubai ticket 4047945 symbol XAUUSD type 1 state 4 magic 920101 vol_initial 0.01 price_open 0.0 comment P2DEMO_br_XAUUSD
ORDER 2026-06-12T14:52:56+00:00 2026-06-12 18:52:56 Dubai ticket 4049362 symbol XAUUSD type 0 state 4 magic 920101 vol_initial 0.01 price_open 4199.5 comment [sl 4199.50]
history_deals_total 15 xau_or_magic920101 14
DEAL 2026-06-12T14:20:00+00:00 2026-06-12 18:20:00 Dubai ticket 3734620 order 4047945 position 4047945 symbol XAUUSD type 1 entry 0 magic 920101 vol 0.01 price 4190.11 profit 0.0 comment P2DEMO_br_XAUUSD
DEAL 2026-06-12T14:52:56+00:00 2026-06-12 18:52:56 Dubai ticket 3735744 order 4049362 position 4047945 symbol XAUUSD type 0 entry 1 magic 920101 vol 0.01 price 4200.51 profit -38.21 comment [sl 4199.50]
```

### A1 Kitchen-Sink Evidence

Command:

```powershell
Select-String -Path 'C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\Logs\20260614.log' `
  -Pattern "'1025742'|expert .* loaded successfully|terminal synchronized|trading has been enabled"
```

Output excerpt:

```text
Experts	expert Phase2ExperimentalDemoExecutor (EURUSD,M5) loaded successfully
Experts	expert Phase2ExperimentalDemoExecutor (GBPUSD,M5) loaded successfully
Experts	expert Phase2ExperimentalDemoExecutor (XAUUSD,M5) loaded successfully
Experts	expert WR50_BreakoutExit1R_v0 (XAUUSD,M5) loaded successfully
Experts	expert Phase2ExperimentalDemoRepairExecutor (XAUUSD,M5) loaded successfully
Experts	expert Phase2ExperimentalDemoRepairExecutor (EURUSD,M5) loaded successfully
Experts	expert WR50_BreakoutWideStop_v0 (XAUUSD,M5) loaded successfully
Experts	expert AccountEquityGuardianShadow (XAUUSD,M5) loaded successfully
Network	'1025742': authorized on Capital.ComMena-Demo through Access Point 2
Network	'1025742': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 8 positions, 0 orders, 232 symbols, 0 spreads
Network	'1025742': trading has been enabled - hedging mode
```

### A3 Repair Lane Evidence

Command:

```powershell
Get-Content -Path 'C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_startup.csv' -Tail 5
Get-Content -Path 'C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_startup.csv' -Tail 5
```

Output excerpt:

```text
2026.06.12 20:59:57,2026.06.13 23:02:29,2026.06.14 03:02:29,A3_RDGUARD_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933000,RDGUARD_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDGUARD_V1
2026.06.12 20:59:57,2026.06.13 23:02:29,2026.06.14 03:02:29,A3_RDSTRUCT_V1_SAFE,Capital.ComMena-Demo,1033669,XAUUSD,933100,RDSTRUCT_V1,1033669,false,true,0.01,1,0.1500,0.2000,0.3000,75.00,60,A3_KILL.txt,ATTACHED_A3_RDSTRUCT_V1
```

Terminal log excerpt:

```text
03:02:28.930	Experts	expert Account3RoundRetestGuardedExecutor (XAUUSD,M5) loaded successfully
03:02:28.950	Experts	expert Account3RoundRetestStructuredExecutor (XAUUSD,M5) loaded successfully
03:02:29.316	Network	'1033669': authorized on Capital.ComMena-Demo through Access Point 2
03:02:29.711	Network	'1033669': terminal synchronized with Capital Com Mena Securities Trading L.L.C: 0 positions, 0 orders, 232 symbols, 0 spreads
```

### Account Equity Guardian Check

Command:

```powershell
Get-ChildItem -Path 'C:\MT5PortableTier1BestEA\MQL5' -Recurse -Filter '*Guardian*'
Select-String -Path 'C:\MT5PortableTier1BestEA\Logs\*.log','C:\MT5PortableTier1PathObserver\Logs\*.log' -Pattern 'AccountEquityGuardian|EquityGuardian|Guardian'
rg -n "AccountEquityGuardian|EquityGuardian|equity guard|risk guard" xau-usd\xauusd-phase1 C:\MT5PortableTier1BestEA\MQL5 -S
```

Output:

```text
# No A2 Guardian files or A2 Guardian log hits found.
xau-usd\xauusd-phase1\mt5\Experts\AccountEquityGuardianShadow.mq5:2://| AccountEquityGuardianShadow.mq5
xau-usd\xauusd-phase1\docs\ACCOUNT_EQUITY_GUARDIAN_SPEC.md:5:Artifact: `mt5/Experts/AccountEquityGuardianShadow.mq5`
...
```

Decision: I did not attach `AccountEquityGuardianShadow` to A2 because the work order also repeatedly defines this lane as one EA, one symbol, one chart. Attaching a second EA to A2 needs a clearer owner decision.

### A2 Daily/Session Monitor Generated

Command:

```powershell
& 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' `
  'xau-usd\xauusd-phase1\scripts\tier1_breakout_retest_daily_report.py' `
  --root 'xau-usd\xauusd-phase1' `
  --date '2026_06_14' `
  --order-log 'C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_order_log_xauusd.csv' `
  --output-json 'xau-usd\xauusd-phase1\outputs\reports\TIER1_BREAKOUT_RETEST_DAILY_REPORT_2026_06_14.json'
```

Output:

```text
Tier-1 daily report: PENDING
```

Generated:

- `xau-usd\xauusd-phase1\outputs\reports\TIER1_BREAKOUT_RETEST_DAILY_REPORT_2026_06_14.md`
- `xau-usd\xauusd-phase1\outputs\reports\TIER1_BREAKOUT_RETEST_DAILY_REPORT_2026_06_14.json`

Report status is `PENDING` because 2026-06-14 is Sunday and there are no 2026-06-14 XAUUSD order-log rows.

### Git Status

Command:

```powershell
git status --short
```

Output:

```text
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md
?? .~lock.Breakout_Trades_By_Session_2026-06-14.xlsx#
?? Breakout_Trades_By_Session_2026-06-14.xlsx
?? CODEX_WORK_ORDER_TIER1_BREAKOUT_SOLO_ACTIVATION_2026_06_14.md
?? FX_EDGE_RESEARCH_PHASE1_FINDINGS_2026_06_14.md
?? TIER1_BREAKOUT_SOLO_ACTIVATION_REPORT_2026_06_14.md
?? TWO_WEEK_WEAKNESS_AND_FIX_AUDIT_2026_06_14.md
?? Two_Week_Trading_Review_2026-06-14.docx
```

No execution-enabled preset is tracked by git. The owner-authorized A2 preset lives under `C:\MT5PortableTier1BestEA\MQL5\Presets\...local.set`, outside the repository.

## Pause / Stop Procedure

Fast kill-switch pause for new A2 orders:

```powershell
Set-Content -LiteralPath 'C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_kill_switch.txt' -Value 'PAUSE' -Encoding ASCII
```

Then restart only:

```powershell
C:\MT5PortableTier1BestEA\terminal64.exe /portable /config:C:\MT5PortableTier1BestEA\Config\tier1_bestea_startup.ini
```

The kill-switch proof above shows that the EA refuses/removes itself with the file present. Remove the file and restart the same A2 terminal to re-enable:

```powershell
Remove-Item -LiteralPath 'C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_kill_switch.txt' -Force
```

Slower pause for future maintenance: flip the local owner preset back to `InpBrokerActionAllowed=false` and reattach/restart A2. Open positions are not automatically closed by either pause path and must be managed separately.

## Notes

- A2 already had real solo execution evidence before this work order: 7 XAUUSD/magic `920101` entries from 2026-06-10 through 2026-06-12.
- The latest A2 trade was Friday 2026-06-12 18:20 Dubai, closed at SL at 18:52:56 Dubai for `-38.21 AED`.
- The committed safe template is non-executing. The EA source itself currently defaults `InpDryRunOnly=false` and `InpBrokerActionAllowed=false`; broker action remains disabled by default, and I did not alter source during this work order.
- A2's separate AccountEquityGuardianShadow is not present. Adding it would create a second EA/chart on the solo lane, so I left it pending owner clarification instead of violating the one-EA boundary.

