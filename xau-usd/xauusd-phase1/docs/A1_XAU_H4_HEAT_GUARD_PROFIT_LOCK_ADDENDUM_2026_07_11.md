# A1 XAUUSD H4 Heat-Guard Profit-Lock Addendum

Date: 2026-07-11  
Scope: development Strategy Tester only; no broker action is authorized.

The preregistered 6% aggregate stop-risk heat guard passed its entry-heat invariant
but failed both profit-retention and native equity-drawdown gates.  Exact logs showed
why entry heat alone is insufficient: open positions can accumulate unrealized gains
and later surrender them while remaining inside their original hard-stop contract.

This single causal follow-up keeps the identical signal stream, fixed 0.01 lots, 6%
heat ceiling, stops, and 2R targets.  It enables the EA's already-existing, previously
declared default profit-protection mechanic without changing its parameters:

- trigger at +0.80R unrealized;
- move the hard stop to +0.20R;
- active mode, not shadow mode.

No trigger or lock sweep is allowed.  The same five-/ten-year windows, USD 1,000
deposit, matched controls, 60% profit-retention floor, PF 1.30 floor, ten-year
100-trade floor, and 10% native relative-equity-DD rejection gate apply.  Failure is
`H4_PROFIT_RETENTION_HEAT_GUARD_FAILED` and sends the research to the sealed router
holding-path classification rather than another exit-parameter search.
