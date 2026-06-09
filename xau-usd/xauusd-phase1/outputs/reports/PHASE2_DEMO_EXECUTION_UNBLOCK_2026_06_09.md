# Phase 2 Demo Execution Unblock

Generated: 2026-06-09

Status: ACTIVE_DEMO_EXECUTION_UNBLOCKED

## Summary

The owner requested: "Make all EAs place orders."

This task changed the standard Capital.com demo runtime so EAs are no longer blocked by the previous demo throttles when their own signal fires. It did not inject fake/blind market orders and did not change strategy signal logic. An EA still needs a valid strategy signal before it sends an order.

## Runtime Boundary

- Terminal touched: `C:\Program Files\MetaTrader 5\terminal64.exe`
- Account: `1025742` / `Capital.ComMena-Demo`
- Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_execution_unblock_20260609_164656`
- Positions/orders were not manually closed or modified.
- A standard terminal restart was performed so the new chart inputs loaded.

## Inputs Changed

For the 14 standard experimental demo executors and 3 repaired demo executors:

| Input | Before | After | Effect |
|---|---:|---:|---|
| `InpMaxOrdersPerDay` | 12 | 0 | Disable per-EA daily entry cap. |
| `InpMaxAccountOrdersPerDay` | 0 | 0 | Account daily cap remains disabled. |
| `InpMinSecondsBetweenOrders` | 300 | 0 | Disable throttle between same-EA orders. |
| `InpMaxOpenPositionsPerInstance` | 1 | 0 | Allow repeated same-EA/symbol entries. |
| `InpMaxEstimatedCostR` | 0.30 | 0.00 | Disable estimated-cost-R guard. |
| `InpMaxMeasuredSpreadPoints` | 75.0 | 0.0 | Disable measured-spread guard. |

For the 3 WR50 charts:

| Input | Before | After | Effect |
|---|---:|---:|---|
| `InpMaxSpreadPoints` | 50/75 | 0 | Disable spread guard. |
| `InpMaxCostR` | 0.15 | 0.0 | Disable cost-R guard for WideStop charts. |
| `InpMaxTradesPerDay` | 5 | 0 | Disable per-EA daily cap. |
| `InpMaxOpenPositionsForThisEA` | 1 | 0 | Allow repeated same-EA entries. |
| `InpMaxOpenWR50PositionsTotal` | 3/5 | 0 | Disable WR50-family total exposure cap. |
| `InpAllowSharedSymbolExposure` | false | true | Allow XAUUSD exposure alongside other demo EAs. |

## Compile Verification

| Source | Result | Compile log |
|---|---:|---|
| `Phase2ExperimentalDemoExecutor.mq5` | 0 errors / 0 warnings | `xau-usd/xauusd-phase1/outputs/logs/phase2_experimental_demo_executor_execution_unblock_20260609_164656.log` |
| `Phase2ExperimentalDemoRepairExecutor.mq5` | 0 errors / 0 warnings | `xau-usd/xauusd-phase1/outputs/logs/phase2_experimental_demo_repair_executor_execution_unblock_20260609_164656.log` |

## Immediate Broker Result

MT5 was queried directly after the unblock.

| Window | New entry deals | Notes |
|---|---:|---|
| 2026-06-09 12:46:56 UTC to 12:48:11 UTC | 3 | First post-unblock entries appeared immediately. |
| 2026-06-09 12:46:56 UTC to 12:50:57 UTC | 8 | Entries continued on the next M5 cycle. |

## New Entries Observed After Unblock

| UTC time | Symbol | Magic | EA/comment | Lot |
|---|---:|---:|---|---:|
| 2026-06-09 12:47:10 | GBPUSD | 920304 | `P2DEMO_sn_round_GBPUSD` | 0.05 |
| 2026-06-09 12:47:10 | XAUUSD | 920301 | `P2DEMO_sn_round_XAUUSD` | 0.01 |
| 2026-06-09 12:47:10 | XAUUSD | 920401 | `P2DEMO_round_XAUUSD` | 0.01 |
| 2026-06-09 12:50:00 | XAUUSD | 920301 | `P2DEMO_sn_round_XAUUSD` | 0.01 |
| 2026-06-09 12:50:00 | XAUUSD | 920101 | `P2DEMO_br_XAUUSD` | 0.01 |
| 2026-06-09 12:50:00 | XAUUSD | 920401 | `P2DEMO_round_XAUUSD` | 0.01 |
| 2026-06-09 12:50:00 | GBPUSD | 920304 | `P2DEMO_sn_round_GBPUSD` | 0.05 |
| 2026-06-09 12:50:01 | XAUUSD | 920201 | `P2DEMO_swing_br_XAUUSD` | 0.01 |

## Interpretation

Order placement is active again. The runtime no longer blocks valid signals because of daily caps, per-instance exposure caps, min-second throttles, estimated-cost-R, or measured-spread guards.

This does not mean every attached EA will place an order on every bar. EAs without a valid signal still wait. Forcing those to trade would require fake/blind entries or changing the strategy logic, which would corrupt the experiment.

## Current Warning

This is an aggressive demo-only setting. It can create duplicate-family stacking and larger drawdowns. It does not authorize canonical Phase 2, real capital, or live trading.
