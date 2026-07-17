# XAUUSD COMEX Session-Swing Specialists V1

Date: `2026-07-17`

## Question

Can a fully completed COMEX regular-session auction predict a multi-session
XAUUSD move when risk is scaled to completed H1 volatility rather than the
cost-sensitive M5 horizon?

The short-horizon prior-value and initial-balance campaigns are closed. This
campaign does not reverse or retune their entries. It makes one decision only at
the `13:30 America/New_York` session close and holds up to 36-48 hours.

## Frozen Families

1. `COMEX_SESSION_VALUE_MIGRATION_SWING_V1`: continuation when the completed
   session POC has migrated beyond the entire prior value area, the close and
   cumulative delta agree, and session volume is not depressed.
2. `COMEX_SESSION_TREND_DAY_CARRY_V1`: continuation after a high-range session
   closes in its outer 20%, with aligned delta and material POC migration.
3. `COMEX_SESSION_BALANCED_EXCESS_REVERSAL_V1`: reversal when the POC remains
   inside prior value but the final close is at least `0.25` completed H1 ATR
   outside prior value with low absolute cumulative delta.

Entries use the next XAUUSD M5 Ask/Bid open. Stops use completed H1 ATR, exits
are side-correct and stop-first, and stress includes native spread, `$0.30`,
holding cost, and `0.05R` slippage. Fit, development, and sealed exam windows
remain `2022-23`, `2023-24`, and `2024-26`. No same-version tuning or execution
authority is permitted.

