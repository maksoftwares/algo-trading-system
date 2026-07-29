# EURUSD H4 re-entry frequency ladder preregistration

The protected strategy accepts only the first qualifying completed H1 break
per expert and UTC date. This ladder keeps every signal, regime, direction,
body, risk, target, hold, and execution parameter unchanged and changes only
the number of qualifying H1 signals that may be considered:

- Q1: first qualifying signal only;
- Q2: first two qualifying signals;
- Q4: all four decision-hour signals.

The quota counts signal opportunities even if a position is already open.
The existing execution rule still permits only one open position per expert,
so a later signal becomes a trade only when the earlier position has exited
before the later entry. Same-M5 exits remain blocked conservatively.

A wider quota must add at least 20% more executed trades and pass every
full-history, chronological, recent, cost, delay, concentration, drawdown,
and bootstrap gate. The broadest passing quota is selected; otherwise Q1
remains protected.

This is historical development, not pristine confirmation, and cannot
authorize demo or broker activity.
