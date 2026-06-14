# TIER1 SESSION AND GUARDIAN FOLLOW-UP REPORT 2026-06-14

Created at Dubai time: `2026-06-14 18:45 +04:00`

Authority: `CODEX_FOLLOWUP_TIER1_SESSION_AND_GUARDIAN_2026_06_14.md`

Scope: diagnostic/options only. No live preset, hour, chart, EA, or account attachment was changed.

## Verdict

The A2 session gate is correct.

- A2 server time is effectively `UTC+0`.
- `InpTradeSessionStartHour=12` and `InpTradeSessionEndHour=15` means server hours `12:00:00-15:59:59`.
- Because Dubai is `UTC+4`, this maps to `16:00:00-19:59:59 Dubai`.
- That is the intended evening edge window, not the losing Dubai afternoon.

Trade placement evidence also matches: all 7 A2 `1033030` / magic `920101` entries map into Dubai evening by server-time conversion; 0 map into Dubai 12:00-16:00 afternoon.

Recommendation: leave the A2 session gate unchanged; for account-level protection, approve a separate non-trading Guardian Stage A chart only if the "one EA/one chart" rule is explicitly relaxed for a supervisor.

## TA - Session Gate Check

### Current Diagnostic Time

Command:

```powershell
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
```

Output:

```text
2026-06-14 18:41:40 +04:00
```

### A2 Server Offset Evidence

Command:

```powershell
@'
import csv
from pathlib import Path
from datetime import datetime
from collections import Counter

path = Path(r'C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_order_log_xauusd.csv')
fmt = '%Y.%m.%d %H:%M:%S'
rows = list(csv.DictReader(path.open(newline='', encoding='utf-8-sig')))
print('order_log', path)
print('rows', len(rows))
active = []
for r in rows:
    try:
        broker = datetime.strptime(r['timestamp_broker'], fmt)
        utc = datetime.strptime(r['timestamp_utc'], fmt)
    except Exception:
        continue
    if r.get('account_login') == '1033030' and r.get('magic') == '920101':
        delta = broker - utc
        active.append((r, broker, utc, delta))
print('a2_magic920101_rows', len(active))
print('broker_minus_utc_seconds_counter', Counter(round(delta.total_seconds()) for _,_,_,delta in active))
print('broker_minus_utc_hour_counter', Counter(round(delta.total_seconds()/3600) for _,_,_,delta in active))
print('\nAll A2 magic 920101 order-log rows with offsets:')
for r, broker, utc, delta in active:
    print(broker, 'UTCcol', utc, 'delta_sec', int(delta.total_seconds()), r['action'], r['direction'], r['guard_reason'], r['order_ticket'])
'@ | & 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' -
```

Output:

```text
order_log C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_order_log_xauusd.csv
rows 29
a2_magic920101_rows 29
broker_minus_utc_seconds_counter Counter({0: 7, 1: 7, 3: 6, 4: 6, 2: 1, 5: 1, -5: 1})
broker_minus_utc_hour_counter Counter({0: 29})

All A2 magic 920101 order-log rows with offsets:
2026-06-10 06:40:00 UTCcol 2026-06-10 06:39:57 delta_sec 3 GUARD_BLOCK SHORT server_hour_session_gate 0
2026-06-10 06:45:00 UTCcol 2026-06-10 06:44:57 delta_sec 3 GUARD_BLOCK SHORT server_hour_session_gate 0
2026-06-10 13:00:00 UTCcol 2026-06-10 13:00:00 delta_sec 0 ORDER_SEND_OK SHORT pass 3932302
2026-06-10 13:20:00 UTCcol 2026-06-10 13:20:00 delta_sec 0 ORDER_SEND_OK SHORT pass 3932934
2026-06-10 15:10:00 UTCcol 2026-06-10 15:10:00 delta_sec 0 ORDER_SEND_OK SHORT pass 3937166
2026-06-10 15:30:00 UTCcol 2026-06-10 15:30:00 delta_sec 0 GUARD_BLOCK SHORT open_instance_exposure_exists 0
2026-06-10 16:30:00 UTCcol 2026-06-10 16:30:00 delta_sec 0 GUARD_BLOCK SHORT server_hour_session_gate 0
2026-06-11 04:45:00 UTCcol 2026-06-11 04:44:58 delta_sec 2 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-11 04:50:01 UTCcol 2026-06-11 04:49:58 delta_sec 3 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-11 06:25:00 UTCcol 2026-06-11 06:24:57 delta_sec 3 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-11 06:45:00 UTCcol 2026-06-11 06:44:57 delta_sec 3 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-11 08:45:00 UTCcol 2026-06-11 08:44:57 delta_sec 3 GUARD_BLOCK SHORT server_hour_session_gate 0
2026-06-11 11:00:00 UTCcol 2026-06-11 10:59:56 delta_sec 4 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-11 11:05:00 UTCcol 2026-06-11 11:04:56 delta_sec 4 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-11 12:00:00 UTCcol 2026-06-11 11:59:56 delta_sec 4 ORDER_SEND_OK SHORT pass 3980810
2026-06-11 12:10:00 UTCcol 2026-06-11 12:09:56 delta_sec 4 ORDER_SEND_OK SHORT pass 3981028
2026-06-11 12:15:00 UTCcol 2026-06-11 12:14:56 delta_sec 4 GUARD_BLOCK SHORT open_instance_exposure_exists 0
2026-06-11 14:00:01 UTCcol 2026-06-11 13:59:56 delta_sec 5 ORDER_SEND_OK SHORT pass 3989274
2026-06-11 14:05:00 UTCcol 2026-06-11 14:04:56 delta_sec 4 GUARD_BLOCK SHORT open_instance_exposure_exists 0
2026-06-11 17:35:00 UTCcol 2026-06-11 17:35:05 delta_sec -5 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-11 23:00:00 UTCcol 2026-06-11 22:59:59 delta_sec 1 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-12 00:35:00 UTCcol 2026-06-12 00:34:59 delta_sec 1 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-12 00:55:00 UTCcol 2026-06-12 00:54:59 delta_sec 1 GUARD_BLOCK SHORT server_hour_session_gate 0
2026-06-12 14:20:00 UTCcol 2026-06-12 14:20:00 delta_sec 0 ORDER_SEND_OK SHORT pass 4047945
2026-06-12 14:25:00 UTCcol 2026-06-12 14:25:00 delta_sec 0 GUARD_BLOCK SHORT open_instance_exposure_exists 0
2026-06-12 18:35:01 UTCcol 2026-06-12 18:35:00 delta_sec 1 GUARD_BLOCK LONG server_hour_session_gate 0
2026-06-12 19:10:00 UTCcol 2026-06-12 19:09:59 delta_sec 1 GUARD_BLOCK SHORT server_hour_session_gate 0
2026-06-12 19:15:01 UTCcol 2026-06-12 19:15:00 delta_sec 1 GUARD_BLOCK SHORT server_hour_session_gate 0
2026-06-12 19:20:01 UTCcol 2026-06-12 19:20:00 delta_sec 1 GUARD_BLOCK SHORT server_hour_session_gate 0
```

Interpretation: the hour offset is consistently `0`. The few-second deltas are normal tick/log timing noise, not a timezone shift.

### Sunday Tick Caveat

Command:

```powershell
@'
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
path = r'C:\MT5PortableTier1BestEA\terminal64.exe'
print('initialize', mt5.initialize(path=path), 'last_error', mt5.last_error())
info = mt5.account_info()
if info:
    print('account', info.login, info.server, info.currency, 'trade_allowed', info.trade_allowed, 'trade_expert', getattr(info,'trade_expert',None))
symbol = 'XAUUSD'
mt5.symbol_select(symbol, True)
tick = mt5.symbol_info_tick(symbol)
now_utc = datetime.now(timezone.utc)
now_dubai = now_utc.astimezone(timezone(timedelta(hours=4)))
print('now_utc', now_utc.isoformat(timespec='seconds'))
print('now_dubai', now_dubai.isoformat(timespec='seconds'))
if tick:
    print('tick_raw_time', tick.time, 'time_msc', tick.time_msc)
    print('tick_datetime_as_utc', datetime.fromtimestamp(tick.time, timezone.utc).isoformat())
    print('tick_age_seconds_vs_utc_now', int((now_utc - datetime.fromtimestamp(tick.time, timezone.utc)).total_seconds()))
    print('bid', tick.bid, 'ask', tick.ask)
mt5.shutdown()
'@ | & 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' -
```

Output:

```text
initialize True last_error (1, 'Success')
account 1033030 Capital.ComMena-Demo AED trade_allowed True trade_expert True
now_utc 2026-06-14T14:42:43+00:00
now_dubai 2026-06-14T18:42:43+04:00
tick_raw_time 1781297936 time_msc 1781297936102
tick_datetime_as_utc 2026-06-12T20:58:56+00:00
tick_age_seconds_vs_utc_now 150227
bid 4218.54 ask 4219.29
```

Interpretation: Sunday live tick time is stale from Friday close, so the order/signal logs are the reliable evidence for active-session timezone mapping.

### Exact Window Mapping

Given:

- A2 broker server offset: `UTC+0`
- Dubai offset: `UTC+4`
- EA gate: `InpTradeSessionStartHour=12`, `InpTradeSessionEndHour=15`

Mapping:

| EA server-time gate | UTC | Dubai |
|---|---|---|
| `12:00:00-15:59:59` | `12:00:00-15:59:59 UTC` | `16:00:00-19:59:59 Dubai` |

No corrected hour recommendation is needed. If the desired Dubai window remains `16:00-20:00`, the existing server-hour inputs should stay:

```text
InpTradeSessionStartHour=12
InpTradeSessionEndHour=15
```

### Every A2 Entry Trade

Command:

```powershell
@'
import csv
from pathlib import Path
from datetime import datetime, timedelta

path = Path(r'C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_order_log_xauusd.csv')
fmt = '%Y.%m.%d %H:%M:%S'
DUBAI_OFFSET = timedelta(hours=4)
entries = []
with path.open(newline='', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r.get('account_login') == '1033030' and r.get('magic') == '920101' and r.get('action') == 'ORDER_SEND_OK':
            server = datetime.strptime(r['timestamp_broker'], fmt)
            utc = datetime.strptime(r['timestamp_utc'], fmt)
            logged_local = datetime.strptime(r['timestamp_local'], fmt)
            dubai_from_server = server + DUBAI_OFFSET
            h = dubai_from_server.hour + dubai_from_server.minute/60 + dubai_from_server.second/3600
            evening = 16 <= h < 20
            afternoon = 12 <= h < 16
            entries.append((server, utc, logged_local, dubai_from_server, r, evening, afternoon))
print('| # | Server entry | UTC column | Dubai from server | Logged local | Direction | Order | Deal | Price | Session |')
print('|---:|---|---|---|---|---|---:|---:|---:|---|')
for i,(server,utc,local,dubai,r,evening,afternoon) in enumerate(entries,1):
    sess = 'EVENING_16_20' if evening else ('AFTERNOON_12_16' if afternoon else 'OTHER')
    print(f"| {i} | {server} | {utc} | {dubai} | {local} | {r['direction']} | {r['order_ticket']} | {r['deal_ticket']} | {r['result_price']} | {sess} |")
print('entries_total', len(entries))
print('evening_16_20_count_by_server_to_dubai', sum(e for *_, e, a in entries))
print('afternoon_12_16_count_by_server_to_dubai', sum(a for *_, e, a in entries))
raw_evening=sum(16 <= local.hour + local.minute/60 + local.second/3600 < 20 for _,_,local,_,_,_,_ in entries)
raw_afternoon=sum(12 <= local.hour + local.minute/60 + local.second/3600 < 16 for _,_,local,_,_,_,_ in entries)
print('evening_16_20_count_by_logged_local_column', raw_evening)
print('afternoon_12_16_count_by_logged_local_column', raw_afternoon)
'@ | & 'xau-usd\xauusd-phase0\.venv\Scripts\python.exe' -
```

Output:

```text
| # | Server entry | UTC column | Dubai from server | Logged local | Direction | Order | Deal | Price | Session |
|---:|---|---|---|---|---|---:|---:|---:|---|
| 1 | 2026-06-10 13:00:00 | 2026-06-10 13:00:00 | 2026-06-10 17:00:00 | 2026-06-10 17:00:00 | SHORT | 3932302 | 3629545 | 4146.83 | EVENING_16_20 |
| 2 | 2026-06-10 13:20:00 | 2026-06-10 13:20:00 | 2026-06-10 17:20:00 | 2026-06-10 17:20:00 | SHORT | 3932934 | 3630113 | 4134.78 | EVENING_16_20 |
| 3 | 2026-06-10 15:10:00 | 2026-06-10 15:10:00 | 2026-06-10 19:10:00 | 2026-06-10 19:10:00 | SHORT | 3937166 | 3633794 | 4126.18 | EVENING_16_20 |
| 4 | 2026-06-11 12:00:00 | 2026-06-11 11:59:56 | 2026-06-11 16:00:00 | 2026-06-11 15:59:56 | SHORT | 3980810 | 3673694 | 4080.88 | EVENING_16_20 |
| 5 | 2026-06-11 12:10:00 | 2026-06-11 12:09:56 | 2026-06-11 16:10:00 | 2026-06-11 16:09:56 | SHORT | 3981028 | 3673886 | 4079.62 | EVENING_16_20 |
| 6 | 2026-06-11 14:00:01 | 2026-06-11 13:59:56 | 2026-06-11 18:00:01 | 2026-06-11 17:59:56 | SHORT | 3989274 | 3681854 | 4082.78 | EVENING_16_20 |
| 7 | 2026-06-12 14:20:00 | 2026-06-12 14:20:00 | 2026-06-12 18:20:00 | 2026-06-12 18:20:00 | SHORT | 4047945 | 3734620 | 4190.11 | EVENING_16_20 |
entries_total 7
evening_16_20_count_by_server_to_dubai 7
afternoon_12_16_count_by_server_to_dubai 0
evening_16_20_count_by_logged_local_column 6
afternoon_12_16_count_by_logged_local_column 1
```

Note on row 4: the logged local wall-clock column is `15:59:56`, but the EA's server timestamp is exactly `12:00:00`. Since the EA gate is driven by server time, row 4 is correctly classified as `16:00:00 Dubai` by server-to-Dubai conversion. This is a seconds-level tick/log artifact, not a timezone defect.

## TB - Equity Guardian Options Memo

### Existing Executor Inputs

Command:

```powershell
$path='xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5'
$lines=Get-Content -Path $path
for($i=1;$i -le 55;$i++){ '{0}:{1}' -f $i,$lines[$i-1] }
```

Output excerpt:

```text
12:input string InpRunId = "phase2-experimental-demo-executor-v0.2";
13:input bool InpDryRunOnly = false;
14:input bool InpBrokerActionAllowed = false;
15:input string InpCandidate = "breakout_retest";
18:input string InpTargetSymbol = "XAUUSD";
19:input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,GBPUSD";
20:input string InpExpectedServerMarker = "Demo";
21:input string InpAllowedAccountLoginsCsv = "";
30:input string InpKillSwitchFileName = "experimental_demo_kill_switch.txt";
31:input double InpFixedLot = 0.01;
34:input int InpMaxOrdersPerDay = 0;
35:input int InpMaxAccountOrdersPerDay = 0;
36:input int InpMinSecondsBetweenOrders = 0;
37:input int InpMaxOpenPositionsPerInstance = 0;
38:input int InpDeviationPoints = 50;
39:input double InpMaxEstimatedCostR = 0.00;
40:input double InpMaxMeasuredSpreadPoints = 0.0;
41:input bool InpTradeSessionGateEnabled = false;
42:input int InpTradeSessionStartHour = 0;
43:input int InpTradeSessionEndHour = 23;
```

Command:

```powershell
Select-String -Path 'xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5' `
  -Pattern 'input .*Equity|input .*Loss|input .*Drawdown|input .*Daily|input .*Max|input .*Floor|ACCOUNT_EQUITY|ACCOUNT_BALANCE|HistoryDealGetDouble|profit|Profit' |
  Select-Object -First 120
```

Output excerpt:

```text
InpMaxOrdersPerDay
InpMaxAccountOrdersPerDay
InpMaxOpenPositionsPerInstance
InpMaxEstimatedCostR
InpMaxMeasuredSpreadPoints
```

Finding: the current A2 executor supports entry/exposure/cost controls, but it does not currently expose an account equity floor, daily realized-loss stop, drawdown stop, or flatten-on-threshold input.

Current A2 local values relevant to entry risk:

```text
InpFixedLot=0.01
InpMaxOrdersPerDay=0
InpMaxAccountOrdersPerDay=0
InpMinSecondsBetweenOrders=60
InpMaxOpenPositionsPerInstance=1
InpMaxEstimatedCostR=0.30
InpMaxMeasuredSpreadPoints=75.0
InpKillSwitchFileName=tier1_bestea_kill_switch.txt
```

### Guardian Source Thresholds

Command:

```powershell
Select-String -Path 'xau-usd\xauusd-phase1\mt5\Experts\AccountEquityGuardianShadow.mq5' `
  -Pattern 'OrderSend|PositionClose|PositionModify|OrderSendAsync|trade\.|CTrade|TRADE_ACTION|HistoryDealGetDouble|InpDailyLossLimitAed|InpPeakArmAtAed|InpGivebackPct|InpProfitTargetAed|InpMaxSameDirectionCount'
```

Output:

```text
InpDailyLossLimitAed        = 150.0
InpPeakArmAtAed             = 150.0
InpGivebackPct              = 0.40
InpProfitTargetAed          = 300.0
InpMaxSameDirectionCount    = 2
HistoryDealGetDouble(...)
```

Command:

```powershell
Get-Content -Path 'xau-usd\xauusd-phase1\docs\ACCOUNT_EQUITY_GUARDIAN_SPEC.md' -TotalCount 260
```

Output excerpt:

```text
Status: STAGE_A_SOURCE_DELIVERED_NOT_ATTACHED

Stage A closes nothing by construction - the source contains no OrderSend, PositionClose,
PositionModify, or any trade-action call.

| Rule | Trigger | Would-action | v0 parameter |
| R1 hard daily loss stop | day_realized + floating <= -limit | FLATTEN_ALL_AND_HALT | 150 AED |
| R2 peak-giveback trail | peak >= arm AND floating <= peak x (1-giveback) | FLATTEN_ALL | arm 150 AED, giveback 0.40 |
| R3 profit target | floating >= target | FLATTEN_ALL | 300 AED |
| R5 correlation cap | same-symbol same-direction positions > cap | WOULD_HAVE_BLOCKED_ENTRY | cap 2 |
```

### Options Table

| Option | What it protects against | Cost / tradeoff | Breaks one-EA/one-chart lane? | Change needed |
|---|---|---|---|---|
| Attach `AccountEquityGuardianShadow.mq5` to A2 as a second chart/EA | Stage A logs when R1/R2/R3/R5 would fire: daily loss `150 AED`, peak giveback arm `150 AED` with `40%` giveback, profit target `300 AED`, same-direction cap `2` | Stage A is observer-only and does not actually flatten/halt. Useful for evidence and kill-drill readiness, not live protection. Stage B would need separate owner approval and broker-action code. | Yes, unless owner defines it as a non-trading supervisor exception | Deploy/compile to A2, attach separate chart, account allowlist `1033030`, run kill-drill |
| Use only existing `Phase2ExperimentalDemoExecutor` inputs | Limits new entries by cost/spread/session/time/exposure; current `InpMaxOpenPositionsPerInstance=1` prevents overlapping A2 breakout exposure | No true account-level loss stop or equity floor exists in current inputs. It cannot flatten current positions on account loss. | No | No source change if only tuning existing entry caps; source change required for daily loss/equity floor |
| External watchdog/script | Can monitor A2 balance/equity/positions externally; can create the EA kill-switch file to halt new entries; if owner authorizes broker action, can flatten on equity threshold | Extra running process, scheduling/restart reliability, broker connectivity risk. Flattening script is broker-action software and needs its own kill-drill and audit. | No chart/EA added, so no | New watchdog script/service with owner-approved thresholds |

## Recommended Proposal Pending Owner Sign-Off

1. Keep the A2 session gate exactly as-is: `12-15 server`, mapping to `16:00-19:59 Dubai`.
2. Do not attach a guardian during this diagnostic follow-up.
3. If owner wants account-level protection, first approve a non-trading A2 Guardian Stage A chart as a named supervisor exception to the one-chart rule, then evaluate Stage B or an external watchdog after a clean kill-drill.

## No-Change Confirmation

No live preset, session hour, chart, EA, or A1/A3 setting was changed by this follow-up. This report only proposes options for owner approval.

