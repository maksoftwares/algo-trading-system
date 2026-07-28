# EURUSD Neutral BLS rolling-surprise carry preregistration

## Research question

Can a simple revision-safe release surprise, rather than month-to-month
acceleration, choose the hindsight oracle's side at Regime 1's 00:00, 00:15,
00:30, and 00:45 UTC clocks?

The rejected acceleration carry asked whether the latest macro level was
strengthening. This separate hypothesis asks whether the newly published level
was unusually strong or weak relative to a fixed causal expectation. Its rule
is locked before its candidate census or P&L.

## Frozen release surprise

For CPI, PPI, and NFP separately:

1. Require six previous first-published observations.
2. Require all six monthly links ending at the current release to be 20-45
   calendar days, preventing a missing archived month from masquerading as a
   consecutive history.
3. Use the median of those six previous initial values as the expectation.
4. Subtract that median from the current first-published value.

- Positive gap means stronger-than-baseline U.S. data: EURUSD SHORT.
- Negative gap means weaker-than-baseline U.S. data: EURUSD LONG.
- Exact equality or incomplete consecutive history means cash.

The six-release median is a fixed half-year robust baseline. It has no fitted
coefficient, vendor consensus, later revision, magnitude threshold, family
weight, or outcome-dependent parameter.

At each outcome-blind Neutral first-hour decision point, use the most recent
directional release known strictly before entry and no more than 72 hours old.
This allows a Friday release to carry into Monday's FX session. Otherwise stay
in cash.

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

## Evaluation order

The source, expectation rule, clock source, execution, implementation, runner,
tests, and gates are hash-locked and pushed before candidate counts or P&L.

1. Build an outcome-blind census without parent outcome, oracle, or exit
   columns.
2. Stop without P&L if capacity fails.
3. Otherwise run one frozen 2019-2022 / 2023 / 2024 / 2025 / 2026 H1
   chronological evaluation.
4. Require approximately 50% wins, approximately 1.5 payoff, PF, profitability
   in every window and both directions, stress survival, bounded daily
   drawdown, and exact/15-minute oracle precision.

All archived windows are adaptive research evidence, not pristine holdouts.
Even a historical pass cannot authorize demo use without a new prospective
sample.

## Failure policy

Do not change the six-release median, 72-hour age, family set, clock set,
direction, stop, target, or chronological coverage after outcomes. Do not
activate only a profitable family, direction, clock, or year.
