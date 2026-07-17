# A3 R1 Forward-Research Demo V1 Activation

Date: 2026-07-17

## Status

`ATTACHED_RUNTIME_CONFIRMED`

The low-frequency R1 specialist is online as an isolated prospective demo experiment. This is not live authorization, strategy promotion, ML execution, or a profit guarantee.

## Verified Runtime

- Account: `1033669`.
- Server: `Capital.ComMena-Demo`.
- Trade mode: demo.
- Account currency: AED.
- Balance/equity at final verification: AED 2,998.45 / AED 2,998.45.
- Terminal: `C:/MT5PortableRepairLane/terminal64.exe`.
- Chart: `chart08.chr`, XAUUSD M5.
- EA: `A1XauM5MomentumContinuationExecutor`.
- Run ID: `A3_R1_FORWARD_RESEARCH_DEMO_V1_20260717`.
- Magic: `934100`.
- MT5 startup status: `INIT_OK` at broker timestamp `2026.07.17 02:46:54`.
- Compile: 0 errors, 0 warnings.
- Deployment and runtime checks: 34 passed, 0 failed.
- Open XAUUSD positions after attachment: 0.
- Pending XAUUSD orders after attachment: 0.

The first evaluated tick recorded `NO_SIGNAL / no_h4_independent_candidate`. This is correct abstention behavior; no trade was forced.

## Isolation

- The old `Phase2ExperimentalDemoExecutor` fill-collection chart is paused with `InpDryRunOnly=true` and `InpBrokerActionAllowed=false`.
- All older A3 charts remain paused/non-broker-action.
- The R1 chart is the only armed chart in the A3 profile.
- The pre-edit profile backup is under `C:/MT5PortableRepairLane/_codex_quarantine/profile_backups/a3_r1_forward_research_before_attach_20260717_024644`.

## Frozen Controls

- Signal mode 7: D1 compression followed by H4 expansion.
- Long only; strict R1 uptrend router.
- AED 30 requested maximum risk per trade.
- Maximum lot 0.01; reject minimum-lot risk above AED 30.
- Maximum one new entry per broker day.
- Maximum one open R1 position.
- AED 60 daily closed-loss stop.
- 24-hour cooldown after a loss.
- Spread cap 75 points and estimated cost cap 0.15R.
- Kill switch: `C:/MT5PortableRepairLane/MQL5/Files/a3_r1_forward_research_kill_switch.txt`.

Creating the kill-switch file prevents new entries; it does not close an already open position.

## Evidence Start

Prospective evidence begins at the verified startup timestamp above. The first quantitative checkpoint remains 30 resolved trades or 90 calendar days, whichever is later. Signals, guard rejections, orders, deals, realized P&L, floating drawdown, and minimum-lot risk rejections must all be retained.

High-frequency A2 and M5 candidates remain rejected and are not authorized on this account.
