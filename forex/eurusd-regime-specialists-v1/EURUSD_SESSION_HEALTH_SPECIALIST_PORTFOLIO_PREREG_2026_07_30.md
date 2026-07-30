# EURUSD session-health specialist portfolio preregistration

This experiment tests one causal repair to the frequency portfolio before any
combined outcome is read.

The stable core is the already frozen `M15_FIRST_BREAK` H4 chop/compression
short portfolio. The complementary expert is the existing completed-M15 RSI
long entry, but with a fixed 1.5R target. Each of the six canonical four-hour
UTC sessions owns an independent shadow history. A candidate is admitted only
when the latest 30 trades from its own session, all exited no later than the
candidate entry, have PF at least 1.05. Rejected shadow outcomes remain visible
to that session's future decisions.

The lookback and PF threshold are inherited unchanged from the earlier global
health-gate experiment. The 1.5R target is fixed to test the user's requested
payoff shape. There is no session deletion, parameter grid, target ladder,
direction reversal, year selection, or post-outcome threshold change.

The portfolio has a two-risk-unit cap. The fixed priority is H4 chop, H4
compression, then RSI session health. The archived Dukascopy bid/ask M5 path,
stop-first same-bar policy, 0.1-pip adverse slippage per side, quarantine, and
the existing H4 ledger are unchanged.

The exact candidate passes only if every frozen admission gate passes,
including PF above 1 in all four chronological blocks, full PF at least 1.20,
0.5-pip stressed PF at least 1.10, best-5%-removed PF at least 1, at least 0.35
trades per FX day, 45%-55% wins, realized payoff 1.35-1.75, and both trade- and
calendar-block bootstrap lower-tail gates.

All history is adaptive research and is not pristine out-of-sample evidence.
Even a pass cannot authorize broker orders; it would identify a backtest
candidate for a separate prospective stage.
