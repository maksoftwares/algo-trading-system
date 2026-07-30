# EURUSD H4 confirmation correlation-cap preregistration

The full-weight confirmation ensemble passed 15 of 16 gates and failed only
the 18R drawdown limit. Its worst drawdown cluster contained the protected
chop trade and a confirmation chop trade at full risk on the same market
event.

This repair changes no signal, regime, entry, exit, stop, target, cost,
quarantine, trade weight, or priority. It changes only the portfolio cap from
2.0R to 1.5R. Therefore two 1.0R chop positions cannot coexist, while a 1.0R
chop position may coexist with one 0.5R compression position. This treats
confirmation entries as correlated expressions of one range-break event
rather than independent risk.

All original gates remain unchanged: at least 0.35 trades per FX day,
45%-55% wins, 1.35-1.75 payoff, PF and cost gates, PF above 1 in every
chronological block, concentration, 18R drawdown, and both bootstrap tests.
There is one frozen run and no cap ladder.

This is adaptive historical development. A pass establishes a backtest
candidate only and cannot authorize broker orders.
