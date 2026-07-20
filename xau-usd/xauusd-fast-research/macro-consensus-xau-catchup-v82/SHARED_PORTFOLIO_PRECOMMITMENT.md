# V82 Shared-Portfolio Precommitment

Date: `2026-07-21`

V82 can be considered additive only after every standalone stage passes
unchanged. Combination uses byte-identical V59/V60 trades and the locked V82
trades on the same account timeline. Blocked or conflicting entries do not count
toward frequency.

Every required aligned window must satisfy all of the following:

- at least 2.0 accepted trades per full weekday;
- base PF at least 1.50 and stressed PF at least 1.35;
- at least 60% positive months;
- positive stressed net after removing the five largest winners;
- shared closed-trade drawdown no greater than USD 500;
- buffered stressed floating-equity drawdown no greater than USD 600;
- worst stressed day loss no greater than USD 150;
- worst rolling five-day stressed loss no greater than USD 250; and
- absolute daily P&L correlation between V82 and V59/V60 no greater than 0.50.

The shared simulator must enforce one account, chronological ordering,
concurrency, conflicts, directional exposure, spread, slippage, commission,
holding cost, and the existing V60 risk controls. Passing standalone economics
does not waive any shared gate.
