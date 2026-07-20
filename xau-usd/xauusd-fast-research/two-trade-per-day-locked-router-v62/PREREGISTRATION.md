# V62 Locked Two-Trade-Per-Day Evaluation

V62 locks exactly one V61 development candidate before evaluating confirmation
and final windows. The selected policy uses mechanism, action horizon, and H4 ADX
state; 20 and 100 prior completed outcomes; and a 1.15 profit-factor health floor.

V59 is immutable. All V57-qualified event/time-direction pairs remain excluded.
The new lane must independently retain PF 1.15, positive net after removing its
five best winners, and at least 100 trades in every required window. The combined
portfolio must produce at least 2.0 trades per weekday, PF 1.5, positive net,
50% positive months, and no more than $300 closed drawdown in development 2,
confirmation, and final.

Failure rejects V62. Parameters and gates may not be changed after the contract is
locked. No result authorizes Python, EA, demo, or live execution.
