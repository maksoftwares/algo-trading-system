# Capital R5 Transition Forward V35 Preregistration

V35 is a read-only transport adapter for the frozen R5 transition components and
router. It does not create or tune a strategy.

The exact component attempts are `23925`, `24877`, `24995`, and `25048`. The
exact selected router is attempt `27135`, a 180-day trailing-drawdown gate with
five observations of minimum history, threshold 2R, half-risk cold start, and
0.25 weak multiplier. Component weights and the four-trade daily ceiling remain
unchanged.

The two required external inputs are the official Dukascopy instruments
`DOLLAR.IDX-USD` and `USTBOND.TR-USD`. Acquisition uses only the official HTTPS
Jetta endpoint, no paid service, and no more than four concurrent requests.
Only completed UTC hours may be acquired. Raw responses are validated and stored
outside Git in the existing Dukascopy foundation.

Gold context comes from read-only Capital MT5 M5 history. Macro inputs retain the
frozen Dukascopy M5 and M15 aggregation, return, prior-scale, residual, regime,
and as-of timing semantics. No proxy instrument may replace the Treasury total
return input.

V35 must reproduce all 799 frozen V9 component candidates and all 330 selected
V11 trades for router attempt 27135 before it may emit a forward candidate.

The transport adapter is locked after the 2026-07-20 forward boundary because
the current-feed requirement was discovered during same-period integration. The
underlying R5 rules were frozen before that boundary. No post-boundary R5 return,
label, fill, exit, P/L, win rate, or drawdown may be opened while implementing or
locking V35.

V35 initially routes forward candidates using only frozen component outcomes
whose exits are strictly before the candidate. Prospective component outcome
updates require a separately locked causal resolver and are not authorized by
this package. This limitation must be removed before a long forward interval can
claim exact online-router continuity.

V35 cannot place, check, modify, or close an order. It authorizes no training,
Python execution prediction, EA consumption, demo trading, or live trading.
