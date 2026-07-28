# EURUSD Neutral consensus event-confirmation preregistration

## Research question

On a UTC date already classified as Regime 1 Neutral at 00:00, can the actual
CPI, PPI, or NFP surprise become a profitable low-frequency expert when the
first fully completed 15 minutes of EURUSD price reaction confirms the same
direction?

This is a different event-horizon hypothesis from the rejected 72-hour
midnight carry. N39 remains closed.

## Frozen causal sequence

1. At 00:00 UTC, determine whether the date belongs to the existing
   outcome-blind Neutral regime.
2. If an exact reconciled CPI, PPI, or NFP release occurs on that date,
   calculate `official initial value - provider forecast`.
3. Positive U.S. surprise maps to EURUSD SHORT; negative maps to LONG; zero
   means cash.
4. Starting with the first M5 bar at or after release, wait until three M5
   bars are fully complete.
5. Calculate midpoint close of the third bar minus midpoint open of the first
   bar. Positive maps to LONG and negative to SHORT.
6. Enter only when the completed price reaction agrees with the macro side.
   Zero reaction or disagreement means cash.
7. Enter at the next M5 open. The entry bar is forbidden from the
   confirmation calculation.

Each release can create at most one candidate. There is no magnitude,
volatility, family, event-hour, weekday, year, or frequency filter and no
fitted model.

## Frozen execution

- Stop: 15 pips.
- Target: 1.5R (22.5 pips).
- Maximum hold: 12 hours.
- Retail spread floor: 0.7 pip.
- Extra slippage: 0.1 pip per side.
- Same-bar ambiguity: stop first.
- One open position at a time.
- Fixed reporting size: 0.01 lot.
- Robustness: another 0.5 pip round trip and removal of the best 5% of
  winners.

The wider event stop is inherited from the previously locked BLS release-time
contract, not selected from the new consensus outcomes.

## Evaluation order

The source, Neutral-date ownership, candidate builder, execution adapter,
tests, gates, and runner are hash-locked and pushed before any real candidate
count or return is read.

1. Run an outcome-blind census using only release fields, the Neutral date
   known at 00:00, and completed post-release bars.
2. Stop without P&L if total, development, every year, recent, both-side, or
   all-family capacity fails.
3. Otherwise run one frozen 2019-2022 / 2023 / 2024 / 2025 / 2026 H1
   evaluation.
4. Require the intended 45-55% win band, 1.35-1.75 payoff, PF, every-window,
   both-side, drawdown, cost, winner-removal, and same-day oracle-side gates.

The historical forecast field was retrieved after its events, so all windows
remain adaptive research. Any historical pass still requires forecasts
captured and checksummed before future releases plus a new prospective sample
before demo consideration.

## Failure policy

Do not change the 15-minute observation, 15-pip stop, 1.5R target, family set,
side mapping, or add a magnitude, time, weekday, side, or year filter after
outcomes. Reject the exact rule without repair.
