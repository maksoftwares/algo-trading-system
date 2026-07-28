# EURUSD Neutral BLS first-hour macro carry preregistration

## Research question

Can the latest revision-safe U.S. macro acceleration state choose the
hindsight oracle's side at Regime 1's actual 00:00, 00:15, 00:30, and 00:45
UTC decision clocks?

This is not a repair of the failed release-time entry. It changes the
hypothesis from an immediate news trade to post-release macro-state carry at
the Neutral oracle's own next first-hour clocks. No P&L was opened for the
failed event-entry family.

## Frozen macro state

For CPI, PPI, and NFP separately, compare each archived first-published value
with its immediately preceding first-published value, requiring a 20-45 day
monthly interval.

- Positive acceleration means U.S. pressure strengthened: EURUSD SHORT.
- Negative acceleration means pressure weakened: EURUSD LONG.
- Equal or missing monthly comparisons mean no release signal.

At each frozen Neutral first-hour decision point, select the most recent
directional BLS release known strictly before entry. Require it to be no more
than 72 hours old so Friday releases can carry through the weekend to Monday's
FX session. If there is no recent release, stay in cash.

There is no magnitude threshold, fitted model, family vote, family weight,
price direction, event subgroup, clock filter, or frequency quota.

## Frozen execution

- Entry clocks: 00:00, 00:15, 00:30, and 00:45 UTC on the existing
  outcome-blind Neutral dates.
- Stop: 4 pips.
- Target: 1.5R (6 pips).
- Maximum hold: 12 hours.
- Retail spread floor: 0.7 pip.
- Extra slippage: 0.1 pip per side.
- Same-bar ambiguity: stop first.
- Up to four concurrent clock positions.
- Portfolio weight: 0.25R per ticket, maximum 1R new risk per eligible date.
- Robustness: add 0.5 pip round trip and remove the best 5% of winners.

The small stop is inherited from the oracle's four-clock paired decision
contract, allowing direct side-and-clock comparison rather than fitting a new
exit.

## Evaluation order

The source, macro-state construction, clock source, execution, implementation,
runner, tests, and gates are hash-locked and pushed before candidate counts or
P&L.

1. Build the outcome-blind clock census without reading parent outcome,
   oracle, or exit columns.
2. Stop without P&L if capacity fails.
3. Otherwise run one frozen 2019-2022 / 2023 / 2024 / 2025 / 2026 H1
   chronological evaluation.
4. Require approximate 50% win rate, approximate 1.5 payoff, PF, every-window
   profitability, both sides, cost and winner stress, daily portfolio
   drawdown, and exact/15-minute oracle precision.

Historical data are adaptive development evidence, not pristine holdout data.
Even a pass requires a new prospective sample before any demo consideration.

## Failure policy

Do not change the 72-hour age, remove a family or clock, add a magnitude
threshold, reverse a family, delete a year, change the inherited exit, or
activate only a profitable recent period after outcomes.
