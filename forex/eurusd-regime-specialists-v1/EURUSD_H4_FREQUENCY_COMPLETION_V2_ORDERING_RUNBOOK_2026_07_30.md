# EURUSD H4 frequency-completion V2 ordering runbook

Status: **PREDEPLOYMENT PACKAGE ONLY — NO INSTALLATION OR ORDER AUTHORITY**

V2 trades only the six chop-regime sleeves. Compression is disabled because
its V1 Capital.com transfer lost money. Every accepted trade is fixed at 0.01
lot and requires transaction confirmation, a broker-side stop and target,
fresh quotes, sufficient equity/free margin, and an aggregate initial-stop
risk no greater than $25.

## Frozen account contract

- Account type: Capital.com demo, retail hedging
- Minimum equity: $5,000
- Symbol and chart: EURUSD, M15
- Volume: exactly 0.01 lot
- Maximum owned positions and daily entries: 6 / 6
- Daily/rolling-five-day/peak-equity breakers: $20 / $40 / $60
- Maximum spread: 2.0 pips
- Compression sleeves: disabled

## Permission boundary

The packaged template is not armed: demo orders are disabled, the emergency
stop is active, the arm token is `DISARMED`, the account/server allowlists are
empty, the start date is in 2099, and terminal-wide live trading is disabled.

No installation may occur without explicit user permission. At that time, a
new dedicated demo terminal, the exact login/server, UTC clock, symbol
contract, and file hashes must first pass read-only preflight. An
account-specific preset may then be generated in the workspace and shown to
the user. Enabling terminal trading and starting the EA require a separate
explicit instruction.

## Immediate rollback

Disable terminal-wide live trading, set the emergency stop, preserve the audit
and broker logs, and stop the dedicated terminal. Existing positions retain
broker-side stops; the persistent equity breaker attempts confirmed closure
of every owned position.
