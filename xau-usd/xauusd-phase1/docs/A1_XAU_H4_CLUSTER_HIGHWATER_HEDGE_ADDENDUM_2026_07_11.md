# A1 XAUUSD H4 Cluster High-Water Hedge Addendum

Date: 2026-07-11  
Boundary: exact MT5 Strategy Tester development only; no broker action is authorized.

The 5%/2% cluster hedge retained the required profit—USD 8,536.42 over ten years—but
native relative equity drawdown remained 40.04%.  The hedge correctly measured loss
below balance, while MT5 relative equity drawdown is measured from a prior floating
equity peak.  A profitable H4 cluster can therefore give back substantial open equity
without ever becoming 5% negative versus balance.

This is a metric-alignment correction, not a threshold iteration.  All rules and the
fixed 5% trigger / 2% release remain unchanged except the reference:

- Track the highest aggregate floating P/L reached by the currently open primary H4
  cluster.
- Define cluster giveback as peak primary floating P/L minus current primary floating
  P/L, divided by current balance.
- Trigger equal-volume short hedge exposure when giveback reaches 5.00%.
- Release when giveback recovers to 2.00% or less.
- Re-arm only after primary floating P/L returns to its tracked high-water mark; reset
  the high-water mark when all primary positions are flat.

Every original H4 entry, stop, target, and the parent USD 8,000 net / 10% native
relative equity drawdown gates remain locked.  No threshold sweep is authorized.
