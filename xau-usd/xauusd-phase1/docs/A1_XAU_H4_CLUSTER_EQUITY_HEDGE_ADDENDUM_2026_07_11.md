# A1 XAUUSD H4 Cluster-Equity Hedge Addendum

Date: 2026-07-11  
Boundary: exact MT5 Strategy Tester development only; no broker action is authorized.

The preregistered per-ticket -0.25R hedge preserved every original H4 primary entry
but failed the profit and drawdown gates.  Ten-year net was USD 7,617.81 and native
relative equity drawdown was 42.21%.  Its defect is structural: many correlated H4
positions can each remain above -0.25R while their combined floating loss is already
large; after a hedge recovery close, the one-cycle rule can also leave a later stop
with the hedge loss already realized.

This addendum replaces per-ticket triggers with one cluster-equity rule.  It is not a
trigger sweep and retains every original H4 entry, stop, and 2R target.

## Fixed rule

- Sum floating P/L and long volume for all primary H4 positions.
- When primary H4 floating loss first reaches 5.00% of current balance, open equal
  total-volume XAUUSD short hedge exposure under a separate magic.
- While active, keep hedge volume equal to primary long volume as primary positions
  enter or exit.
- Close all cluster hedges when primary-only floating loss recovers to 2.00% of
  current balance or less.
- After release, re-arm only when primary-only floating P/L reaches breakeven or all
  primary positions are flat.
- If all primary positions close first, close all remaining hedge volume immediately.
- Require retail-hedging margin mode and fail closed on every hedge action error.
- A market-closed primary signal expires permanently; no signal retry is introduced.

The 5% trigger leaves a fixed buffer below the 10% rejection limit.  The 2% release
requires a real primary-path recovery while avoiding indefinite delta-neutral lock.
Neither number may be changed after results.

The same USD 1,000, five-/ten-year windows, original-entry preservation, ten-year USD
8,000 net, five-year USD 6,500 net, PF 1.30, zero-failure, and 10% native relative
equity drawdown gates from the parent preregistration apply.
