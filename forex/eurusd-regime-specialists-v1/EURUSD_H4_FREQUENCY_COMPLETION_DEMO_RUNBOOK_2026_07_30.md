# EURUSD H4 frequency-completion demo runbook

Status: **PACKAGE PREPARATION ONLY — DEPLOYMENT REQUIRES USER PERMISSION**

This runbook covers the 12-sleeve EURUSD frequency-completion EA validated in
the isolated Capital.com Strategy Tester. It does not itself authorize a file
copy, terminal launch, chart attachment, or order.

## Frozen implementation

- Expert: `EurUsdH4FrequencyCompletionControlledDemo.ex5`
- Chart: `EURUSD`, `M15`
- Volume: exactly `0.01` lot per accepted sleeve signal
- Maximum simultaneous owned positions: `9`
- Strategy: short-only chop/compression specialists with the two frozen causal
  admission caps
- Required account mode: retail hedging
- Default state: shadow on, demo orders off, emergency stop on, tester orders
  off, token disarmed

## Phase A — permissioned shadow installation

Do not perform these actions without explicit user permission.

1. Select a dedicated Capital.com demo portable terminal. Do not reuse the
   active M15-regime shadow terminal because both EAs own EURUSD positions and
   enforce foreign-position/mutex protection.
2. Stop the selected terminal and run the read-only install preflight.
3. Confirm that the selected root contains `terminal64.exe`, `MQL5`, and
   `Config`, is not the isolated Strategy Tester root, has no conflicting
   frequency-completion files, and has no running terminal process.
4. Copy only the frozen EX5, the disarmed shadow preset, and the shadow startup
   configuration. Verify every SHA-256 after the copy.
5. Start with terminal-wide `AllowLiveTrading=0` and `AllowDllImport=0`.
6. Verify the audit contains `INIT_OK`, `STARTUP_LATCH`, and
   `RESTART_RECOVERY_OK`; verify the observed broker grid is minimum/step
   `0.01/0.01`; and verify zero orders and zero owned positions.
7. Leave the EA in shadow mode until its audit and account identity are
   independently checked.

## Phase B — separately permissioned demo ordering

Shadow installation is not permission to enable orders. A second explicit user
authorization is required before this phase.

1. Confirm the exact demo login, `Capital.ComMena-Demo` server, hedging mode,
   EURUSD symbol, 0.01 volume grid, zero foreign EURUSD positions, and zero
   duplicate EA instances.
2. Generate an account-specific ordering preset from the frozen template:
   `InpShadowMode=false`, `InpEnableDemoOrders=true`,
   `InpEmergencyStop=false`, exact login/server allowlists,
   `InpDemoArmToken=I_ACCEPT_DEMO_001`, and an explicit future UTC start.
3. Record the generated preset hash and user authorization in the deployment
   evidence before enabling terminal-wide live trading.
4. Start with a supervised observation window. Confirm that every accepted
   signal has exactly one `ORDER_SEND_OK`, uses 0.01 lot, has a stop and target,
   and never exceeds nine owned positions.
5. Immediately stop and re-arm the emergency stop if identity, volume, spread,
   position ownership, audit reconciliation, or loss-breaker checks fail.

## Rollback

Stop the dedicated terminal, preserve its logs and Common Files audit, restore
the disarmed shadow preset and `AllowLiveTrading=0`, then remove only the exact
frequency-completion files after their hashes and paths have been recorded.

## Evidence already passed

- 0 compile errors and 0 warnings
- 416 two-year MT5 trades, PF 1.311, 48.80% win rate, 1.375 payoff
- 244 latest-12-month trades, 0.935 trades/weekday, PF 1.542
- exact latest-six-month replay through 127 forced restart recoveries
- 21/21 disarmed signals blocked with zero trades
- no current installation in the known demo terminals

The remaining action is permissioned installation and runtime verification.
