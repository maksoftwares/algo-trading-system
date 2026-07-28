# EURUSD Neutral BLS initial-release acceleration preregistration

## Research question

Can revision-safe changes in the first-published U.S. inflation and labor
headlines select a sparse, profitable EURUSD Regime 1 expert without a fitted
model, forecast database, or price-derived direction?

## Novel information

The point-in-time BLS source contains 267 archived first-release values for
CPI, final-demand PPI, and Nonfarm Payrolls from January 2019 through June
2026. It is distinct from:

- the revised/unsafe Dukascopy actual and forecast fields, which remain
  prohibited;
- the rejected EURUSD post-event momentum/reversal rules;
- the rejected all-clock DXY/Treasury features; and
- the rejected daily/weekly rate and carry screens.

The current archived value is known at its BLS embargo-release time. The
previous same-family archived value was known weeks earlier. No later revision
enters the decision.

## Frozen decision

For each CPI, PPI, or NFP release:

1. Find the immediately preceding parsed release from the same family.
2. Require the predecessor to be 20-45 calendar days earlier. Otherwise cash.
3. Compute current initial value minus preceding initial value.
4. Positive acceleration means U.S. growth/inflation pressure strengthened:
   short EURUSD.
5. Negative acceleration means pressure weakened: buy EURUSD.
6. Equal values mean cash.
7. Wait 15 minutes after the release's M5 bucket start.
8. Trade only if the latest fully completed causal state is Neutral,
   non-shock, and non-compression.

There is no magnitude threshold, fitted model, consensus forecast, family
weight, title subgroup, clock filter, or frequency quota. All three families
remain in the rule regardless of later outcomes.

## Frozen execution

- Entry: first EURUSD M5 open at or after the release bucket plus 15 minutes.
- Stop: fixed 15 pips.
- Target: 1.5R (22.5 pips).
- Maximum hold: 12 hours.
- Retail spread floor: 0.7 pip.
- Extra slippage: 0.1 pip per side.
- Same-bar ambiguity: stop first.
- Maximum concurrency: one EURUSD position.
- Robustness: add 0.5 pip round trip and remove the best 5% of winners.

## Evaluation order

The exact source, config, implementation, runner, tests, and gates are
hash-locked and pushed before opening the Neutral candidate count or any P&L.

1. Run the outcome-blind census.
2. If it fails, stop without P&L.
3. If it passes, run one frozen chronological backtest over 2019-2022, 2023,
   2024, 2025, and 2026 H1.
4. Require the requested approximate 50% win rate, approximate 1.5 payoff,
   PF, every-window profitability, both-side profitability, cost stress,
   winner-removal resilience, drawdown, and same-day/same-side Regime 1 oracle
   resemblance.

All archived periods are adaptive historical research data because other
EURUSD experiments have inspected them. Even a pass cannot become demo-ready
without a new post-lock prospective sample.

## Failure policy

Do not repair a failure by dropping CPI/PPI/NFP, changing the 15-minute wait,
adding a magnitude cutoff, reversing one family, selecting a clock or year,
changing the stop, or activating only the latest six months.
