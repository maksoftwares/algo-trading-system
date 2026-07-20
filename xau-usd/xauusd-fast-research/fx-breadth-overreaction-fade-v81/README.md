# Three-FX Dollar-Breadth Overreaction Fade V81

V81 is an additive, research-only XAUUSD specialist. It acquires free official
Dukascopy GBPUSD ticks, combines them causally with frozen EURUSD, USDJPY, and
XAUUSD quotes, and tests whether an unusually large XAU response to unanimous
dollar breadth subsequently mean reverts.

V59/V60 remain immutable. V81 cannot authorize Python, EA, demo, live, account,
terminal, broker, paid-data, or order activity.

Source acquisition is stage-gated under
`PRELOCK_STAGED_SOURCE_AMENDMENT.md`. Development source and all strategy code
must be locked before development P&L is opened. Each later source slice is
hash-audited only after the preceding economic stage passes.

If every V81 stage passes, shared-account testing must follow the fixed
frequency, profitability, correlation, and drawdown gates in
`SHARED_PORTFOLIO_PRECOMMITMENT.md`.
