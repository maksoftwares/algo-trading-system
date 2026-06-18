# A1 BTC Breakout Relaxed Filter Update - 2026-06-18

Status: `APPLIED_TO_A1_DEMO`

Owner requested the A1 BTCUSD breakout experiment be made less restrictive so it can generate demo trades for evidence collection. This update changes only the BTCUSD branch of the `breakout_retest` observer. XAUUSD, EURUSD, and GBPUSD keep the original observer parameters.

## Boundary

- Account: `1025742 / Capital.ComMena-Demo`
- Symbol: `BTCUSD`
- Candidate: `breakout_retest`
- Magic: `920105`
- Lot: `0.01`
- Scope: owner-requested demo experiment only
- Canonical Phase 2: unchanged
- Live/real capital: not authorized

## What Was Relaxed

The chart-level BTC guards were already open before this change:

- `InpMaxMeasuredSpreadPoints=0.0`
- `InpMaxEstimatedCostR=0.00`
- `InpMaxOrdersPerDay=0`
- `InpMaxAccountOrdersPerDay=0`
- `InpMaxOpenPositionsPerInstance=0`
- `InpTradeSessionGateEnabled=false`

The actual blocker was the strategy observer continuing to use XAU-style breakout/retest geometry on BTC. The old retest tolerance was `5 points`, which is only `$0.05` on BTCUSD when the observed spread is about `$50.00`.

BTCUSD now uses a BTC-only relaxed observer profile:

| Setting | Original | BTCUSD relaxed |
|---|---:|---:|
| Break lookback window | 20 M5 bars | 48 M5 bars |
| Break distance threshold | 0.30 ATR | 0.10 ATR |
| Retest tolerance | 5 points | max(5000 points, 0.25 ATR) |
| Stop/target model | unchanged | unchanged |
| Order guards | unchanged | unchanged |

BTC relaxed rows are audit-labelled with:

- `no_long_btc_relaxed_breakout_retest_candidate`
- `no_short_btc_relaxed_breakout_retest_candidate`
- `BTC_RELAXED_BREAKOUT_RETEST_LONG_DEMO`
- `BTC_RELAXED_BREAKOUT_RETEST_SHORT_DEMO`

## Deployment Evidence

- Patched source: `xau-usd/xauusd-phase1/mt5/Include/Phase1/Phase1BreakoutRetest.mqh`
- Patched executor call: `xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5`
- Terminal source updated under: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5`
- Compile log: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_Phase2ExperimentalDemoExecutor_btc_relaxed.log`
- Compile result: `0 errors / 0 warnings`
- Standard A1 terminal was restarted after compile so the attached BTC chart loaded the new EX5.

## Runtime Evidence

Startup log after restart:

```text
ATTACHED_DEMO_EXECUTOR_ENABLED
```

Latest BTC signal log after restart shows the relaxed BTC branch is active:

```text
no_long_btc_relaxed_breakout_retest_candidate
```

No BTC order had fired at the time of this report. The EA is now less restrictive, but it still waits for a BTC breakout/retest event instead of firing a forced/random trade.
