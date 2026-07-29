# EURUSD Neutral Prospective Inventory Clock Portfolio Preregistration

Recorded on 2026-07-29 before the first 00:05, 06:05, or 12:05 portfolio
observation.

## Purpose

This read-only observer combines the already frozen prospective 00:05
inventory-unwind expert and the frozen prospective 06:05/12:05 clock-transfer
expert into one three-clock Regime-1/Neutral portfolio. It exists so a future
portfolio claim cannot be assembled by selecting a favorable clock after
outcomes.

No historical evaluation of this portfolio is allowed. At recording time both
component ledgers and path roots contain zero strategy evidence.

## Frozen portfolio

The clocks are permanently 00:05, 06:05, and 12:05 UTC. Each retains its own
locked source, decision, entry, cost, stop, target, and holding-period
contract. The observer replays component evidence without changing fills.

Each signal is fixed at 0.01 research lots. Because each maximum hold ends at
the next clock's entry or earlier, the portfolio requires the previous
position to close before or at the next entry. Duplicate entry timestamps,
overlapping intervals, component deletion, clock deletion, and post-outcome
reweighting are forbidden. Maximum concurrency and gross EURUSD exposure are
one 0.01-lot shadow position.

The portfolio is the fixed sequence of all three clocks. Per-clock results are
reported to expose failure, not to choose a winner. Every component campaign
must independently pass its own frozen gates before the portfolio can pass.

## Prospective admission

Evaluation requires at least 12 calendar months, 90 closed trades, 30 at
00:05, 20 at 06:05, 20 at 12:05, and 20 trades on each side. The complete
portfolio must also achieve:

- 45-55% win rate and realized payoff between 1.35 and 1.75;
- base PF at least 1.30 and extra-half-pip stressed PF at least 1.15;
- positive net R and PF at least 1.00 at every clock;
- PF at least 1.00 on both long and short trades;
- trailing-six-month PF at least 1.15 with positive net R;
- maximum closed-trade drawdown no greater than 15R;
- PF at least 1.00 after removing the best 5% of winners;
- at least 60% positive active months;
- no month above 35% of total positive monthly profit;
- no duplicate entry timestamp and no position overlap;
- at least 50% same-day/same-side Neutral-oracle precision.

Temporal oracle resemblance is tested separately for each clock, leaving at
most one prediction per UTC date. All three clocks must reach 50% precision
within 15 minutes, positive lift over the exact uniform-time-and-side null,
and a one-sided p-value no greater than 1/60. This Bonferroni threshold controls
the three frozen clock tests at familywise 0.05; no best-clock p-value may be
used.

Minimum trades per active day is reported but not forced. Profitability is not
rescued by adding poor trades to hit a frequency target.

## Verdict boundary

Before all sample and next-day oracle evidence is complete, status remains
`ACCUMULATING_PROSPECTIVE_EVIDENCE`. Once evaluation is ready, any failed
component, economic, robustness, concentration, overlap, or oracle gate
rejects this exact portfolio without retrospective repair. Passing all gates
permits independent research review only.

The observer cannot fetch market data, create decisions, alter evidence,
contact MT5, attach an EA, or place an order. `controlled_demo_ready` remains
false regardless of statistical status.
