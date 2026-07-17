# XAUUSD COMEX Initial-Balance Specialists V1

Date: `2026-07-17`

## Question

Does the completed COMEX regular-session initial balance contain a cost-surviving
XAUUSD edge when combined with causal futures point-of-control migration,
cumulative aggressor delta, and relative session volume?

This campaign is structurally separate from the rejected prior-value V1. It uses
the current session's first hour and its developing auction, not yesterday's
value-area acceptance or reentry. The existing `2024-07-01` through `2026-07-01`
exam remains unopened unless an unchanged family passes both earlier stages.

## Frozen Families

1. `COMEX_INITIAL_BALANCE_EXPANSION_V1`: first completed M5 close at least
   `0.05` spot ATR beyond the `08:20-09:20 America/New_York` initial balance,
   with point-of-control displacement, cumulative delta, and relative volume in
   the breakout direction.
2. `COMEX_INITIAL_BALANCE_FAILED_EXPANSION_V1`: first completed M5 probe at
   least `0.15` ATR beyond an initial-balance edge that closes at least `0.05`
   ATR back inside with a directional rejection candle and non-initiative
   cumulative delta.
3. `COMEX_DEVELOPING_POC_MIGRATION_V1`: a single `10:00 America/New_York`
   continuation decision when the developing POC has moved at least `0.15` ATR
   from its `08:50` level, price and cumulative delta agree, and cumulative
   volume is at least `0.75` of its prior 20-session median.

Signals use completed rows only. Entries use the next XAUUSD M5 Ask/Bid open,
exits are side-correct, collisions are stop-first, and stress includes native
spread, `$0.30`, holding cost, and `0.05R` slippage. One active position and one
entry per family per UTC day are allowed.

Fit is `2022-07-01` to `2023-07-01`; development is `2023-07-01` to
`2024-07-01`; exam is `2024-07-01` to `2026-07-01`. Gates are multiplicity
adjusted above the prior campaign. No same-version tuning or broker action is
authorized.

