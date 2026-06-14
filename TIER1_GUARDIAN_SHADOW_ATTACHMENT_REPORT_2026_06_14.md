# TIER1 GUARDIAN SHADOW ATTACHMENT REPORT 2026-06-14

Created at Dubai time: `2026-06-14 18:55 +04:00`

Owner instruction: attach Guardian Protection to A2 only, watch/log only, no trading interference.

## Result

Guardian Shadow is attached on A2 and logging.

- Account: `1033030 / Capital.ComMena-Demo`
- Terminal: `C:\MT5PortableTier1BestEA`
- Trading EA still attached: `Phase2ExperimentalDemoExecutor`, candidate `breakout_retest`, `XAUUSD,M5`, magic `920101`
- Guardian EA attached as second observer chart: `AccountEquityGuardianShadow`, `XAUUSD,M5`
- Guardian status: `ATTACHED_GUARDIAN_SHADOW_STAGE_A`
- Guardian mode: shadow/log only; no order-send or position-close code present
- A2 open positions/orders after attach: `0 / 0`
- A1 and A3 were not changed

## Answer: Did We Replace The Trading EA?

No. We did not replace the trading EA.

The same trading EA is still running:

```text
Phase2ExperimentalDemoExecutor
candidate=breakout_retest
symbol=XAUUSD
magic=920101
```

The Guardian was added beside it as a watcher. It does not trade, close, modify, or block orders.

## Files Added/Changed In A2

- Deployed source: `C:\MT5PortableTier1BestEA\MQL5\Experts\AccountEquityGuardianShadow.mq5`
- Compiled binary: `C:\MT5PortableTier1BestEA\MQL5\Experts\AccountEquityGuardianShadow.ex5`
- Added chart: `C:\MT5PortableTier1BestEA\MQL5\Profiles\Charts\Default\chart02.chr`
- Profile backup: `C:\MT5PortableTier1BestEA\_codex_quarantine\profile_backups\default_profile_before_a2_guardian_20260614_185207`
- Guardian startup log: `C:\MT5PortableTier1BestEA\MQL5\Files\A2_EQUITY_GUARDIAN_SHADOW_STARTUP.csv`
- Guardian watch log: `C:\MT5PortableTier1BestEA\MQL5\Files\A2_EQUITY_GUARDIAN_SHADOW_LOG.csv`

## Raw Evidence

### Compile

```text
C:\MT5PortableTier1BestEA\MQL5\Experts\AccountEquityGuardianShadow.mq5 : information: compiling C:\MT5PortableTier1BestEA\MQL5\Experts\AccountEquityGuardianShadow.mq5
Result: 0 errors, 0 warnings, 333 ms elapsed, cpu='X64 Regular'
```

### Terminal Load

```text
18:52:52.132 Experts expert AccountEquityGuardianShadow (XAUUSD,M5) loaded successfully
18:52:52.311 Experts expert Phase2ExperimentalDemoExecutor (XAUUSD,M5) loaded successfully
18:52:52.983 Network '1033030': authorized on Capital.ComMena-Demo through Access Point 2
```

### Breakout EA Still Attached

```text
2026.06.14 18:52:53 ... 1033030 ... XAUUSD ... breakout_retest ... false,true ... 0.3000,75.00 ... ATTACHED_DEMO_EXECUTOR_ENABLED
```

The `false,true` values in that row are:

```text
InpDryRunOnly=false
InpBrokerActionAllowed=true
```

### Guardian Startup

```text
timestamp_broker,timestamp_utc,account_login,server,trade_mode,enable_shadow_logging,timer_seconds,daily_loss_limit_aed,peak_arm_at_aed,giveback_pct,profit_target_aed,max_same_direction_count,kill_switch_file,log_file,status
2026.06.12 20:59:57,2026.06.14 14:52:53,1033030,Capital.ComMena-Demo,0,true,10,150.00,150.00,0.4000,300.00,2,A2_GUARDIAN_SHADOW_KILL.txt,A2_EQUITY_GUARDIAN_SHADOW_LOG.csv,ATTACHED_GUARDIAN_SHADOW_STAGE_A
```

Note: the broker timestamp is stale because XAUUSD is closed on Sunday; UTC timestamp confirms the attach time.

### Guardian Watch Log

```text
timestamp,balance,equity,total_floating,session_peak_floating,day_realized,open_positions,max_same_dir_count,rule_fired,would_action,hypothetical_locked_pnl_at_trigger
2026.06.12 20:59:57,4055.21,4055.21,0.00,0.00,-38.21,0,0,none,NONE,0.00
```

### No Broker-Action Calls In Guardian

Command checked for:

```text
OrderSend, OrderSendAsync, CTrade, trade.Buy, trade.Sell, PositionOpen, PositionModify, PositionClose, TRADE_ACTION
```

Output:

```text
# no matches
```

### Final Account State

```text
=== A1 C:\Program Files\MetaTrader 5\terminal64.exe
login 1025742 server Capital.ComMena-Demo equity 2387.1
positions 8
orders 0

=== A2 C:\MT5PortableTier1BestEA\terminal64.exe
login 1033030 server Capital.ComMena-Demo equity 4055.21
positions 0
orders 0

=== A3 C:\MT5PortableRepairLane\terminal64.exe
login 1033669 server Capital.ComMena-Demo equity 4000.0
positions 0
orders 0
```

### Kill Files

```text
C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_kill_switch.txt = absent
C:\MT5PortableTier1BestEA\MQL5\Files\A2_GUARDIAN_SHADOW_KILL.txt = absent
```

## What Guardian Will Do Now

It only watches and logs. It will log what it would have done under these rules:

- Daily loss reaches `-150 AED`: would log `FLATTEN_ALL_AND_HALT`
- Floating profit reaches `+150 AED`, then gives back `40%`: would log `FLATTEN_ALL`
- Floating profit reaches `+300 AED`: would log `FLATTEN_ALL`
- Too many same-direction positions: would log `WOULD_HAVE_BLOCKED_ENTRY`

It will not actually flatten or halt unless a future Stage B version is separately approved.

