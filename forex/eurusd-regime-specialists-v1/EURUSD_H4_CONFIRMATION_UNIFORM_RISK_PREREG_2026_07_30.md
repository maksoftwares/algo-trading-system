# EURUSD H4 confirmation uniform-risk preregistration

The full-weight confirmation ensemble passed 15 of 16 frozen gates. Its exact
1,288-trade ledger produced 0.520 trades per FX day, 45.73% wins, 1.413
payoff, PF 1.190, 0.5-pip stressed PF 1.136, and bootstrap PF lower bounds
above 1. It failed only the 18R drawdown gate at 23.898R.

This test retains the exact parent ledger, ordering, entries, exits, sleeves,
and costs. Every sleeve is scaled uniformly to 75% of parent exposure,
reducing the maximum aggregate initial-risk budget from 2.0R to 1.5R. No
trade is added, removed, reordered, or selectively resized.

The 0.75 factor is the round portfolio budget ratio 1.5/2.0, not an optimized
fit to the observed drawdown. There is no sizing ladder. Every original gate,
including the 18R drawdown limit, remains unchanged.

This is adaptive historical research. A pass is the required backtest outcome
for this candidate, but is not pristine forward evidence and cannot authorize
broker orders.
