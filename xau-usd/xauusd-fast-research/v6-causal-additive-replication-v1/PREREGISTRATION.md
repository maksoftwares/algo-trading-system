# Preregistration

## Question

Does the externally proposed V6 confirmed-impulse mechanism add useful,
cost-stressed trades to immutable V60 after repairing its known selection,
duplicate, and portfolio-clock defects?

## Frozen candidate construction

- Candidate pool: all 576 combinations exposed by the hashed external
  `v6_walkforward.py`.
- Feed used for selection and evaluation: Capital M5 bid/ask.
- Selection years: 2022 through 2026.
- For year `Y`, a member is scored only on trades whose Capital exit is before
  `Y-01-01`.
- Minimum prior sample: 30 trades.
- Score: dollar win rate in percentage points plus 20 times dollar profit
  factor capped at 3.
- Pick the top seven members; ties break by member name.
- Assign current trades by Capital entry year, never exit year.
- If members nominate the same underlying signal and direction, retain the
  highest prior-ranked member. Realized return is never a tie breaker.
- Apply one continuous two-position lock using Capital entry and Capital exit.
- No parameter changes are allowed after observing this run.

## Frozen execution stress

The Capital return already includes the external lane's $0.30 base fee. Stress
subtracts, per trade:

- 0.05 R slippage;
- another $0.30 fixed execution cost;
- $0.35 for every 24 hours held, prorated.

## Shared-account routing

Candidates are routed in entry order beside immutable V60. Limits are inherited
from V59/V60:

- at most two open add-ons;
- at most $45 concurrent add-on initial risk;
- at most two new V6 entries per UTC date;
- suspend at $225 closed-trade drawdown and resume at $180.

## Historical acceptance gates

Every required window (`development_2`, `confirmation`, `final`) must satisfy:

- at least 20 accepted V6 trades;
- V6 stress net P&L above zero;
- V6 stress profit factor at least 1.15;
- V6 stress P&L remains above zero after removing its five largest winners;
- combined stress net P&L above zero;
- combined stress profit factor at least 1.50;
- combined frequency at least one trade per weekday;
- absolute daily P&L correlation with V60 no more than 0.50;
- combined closed-trade drawdown no more than $300.

The full combined history must also remain within:

- two open add-ons;
- $45 concurrent add-on initial risk;
- $449.7675 buffered M5 floating-equity drawdown.

## Interpretation

Passing is not validation on unseen data because all available history has
already influenced the broader research program. Passing creates only a
candidate for code translation, MT5 parity, and new prospective observation.
Failure quarantines this exact specification; it cannot be repaired in place.
