# V55 Preregistration

V54 reduced the development-2 combined closed drawdown below USD 300, but its
hard account suspension removed 19 final-window add-ons and reduced final
frequency from 1.000 to 0.927 trades per weekday.

V55 changes the intervention from trade deletion to causal risk reduction:

- start half-risk sizing for new add-ons at USD 225 closed drawdown, 75% of the
  USD 300 ceiling;
- return to full-risk sizing only after drawdown recovers to USD 180, 60% of
  the ceiling;
- continue applying all existing concurrency and daily-entry controls;
- leave V50 and all specialist signals, entries, exits, and gates unchanged.

The 50% multiplier is a standard single-step de-risking action, not an alpha
parameter search. The policy is locked before evaluation and V55 is terminal
after one run.

All outcomes are exposed historical evidence. A pass is only a historical
portfolio candidate and grants no Python serving, EA, demo, live, terminal, or
broker authority. Prospective shadow confirmation and complete floating-equity
evidence remain required.
