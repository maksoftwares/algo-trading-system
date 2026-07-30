# EURUSD H4 confirmation risk-repair preregistration

The parent confirmation ensemble passed 15 of 16 frozen gates. Its 1,288
trades achieved 0.520 trades per FX day, 45.73% wins, 1.413 payoff, PF 1.190,
0.5-pip stressed PF 1.136, PF above 1 in all four chronological blocks, and
passed both bootstrap gates. It failed only the 18R drawdown limit, reaching
23.898R during a cluster in which the protected core and new confirmation
experts carried equal risk.

This repair changes no entry, exit, target, stop, regime, session, cost,
quarantine, or priority rule. The protected core remains at its existing
weights. Every confirmation expert is retained, but new next-close and retest
experts receive half their parent weight: chop 0.50R and compression 0.25R.
The fixed portfolio cap remains 2R.

There is one frozen run and no weight ladder. Every original admission gate is
unchanged, including the 18R maximum drawdown. Failure rejects the exact risk
repair without deleting an expert or selecting a favorable period.

This is adaptive historical development, not pristine forward evidence. A
pass establishes the requested backtest outcome only; it cannot authorize
broker orders.
