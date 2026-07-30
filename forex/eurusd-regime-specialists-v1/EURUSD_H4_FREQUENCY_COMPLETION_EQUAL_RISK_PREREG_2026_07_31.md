# EURUSD H4 frequency-completion equal-risk preregistration

This v2 policy is frozen before its formal result is generated. The rejected
v1 result and exact 2,532-trade ledger are checksum-pinned.

No trade may be added, removed, reordered, or relabeled. V2 changes only
position risk: every trade receives the same 0.15R initial risk. At the 0.1-lot
reference size this is 0.015 lot, above the 0.01 broker minimum. With the
observed maximum of nine concurrent trades, aggregate initial risk cannot
exceed 1.35R.

The same frequency and edge gates remain:

- at least 0.85 trades per FX day;
- full PF 1.15, +0.5-pip PF 1.10, and +1.0-pip PF 1.00;
- PF above 1 in every chronological block;
- recent and latest-12-month PF 1.20;
- positive latest-six-month R;
- 45%-55% wins and 1.35-1.75 realized payoff;
- at least 55% positive active months;
- best-5%-removed PF 1.00;
- no more than 18R drawdown; and
- passing trade-block and calendar-block bootstrap tails.

The parent result must confirm that every added component qualified on its own.
A historical pass remains adaptive research and cannot authorize broker
orders.
