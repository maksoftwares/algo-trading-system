# EURUSD Neutral event-conditioned cross-asset rates preregistration

## Research question

Can a causal U.S. macro-event clock plus an economically signed DXY/Treasury
reaction select profitable EURUSD Regime 1 (Neutral) trades without fitting
another model or threshold to historical outcomes?

This is a materially different information lane from the rejected direct
post-event EURUSD drive and the rejected all-clock cross-asset classifier. The
event clock decides *when* to look; completed DXY and Treasury bars decide
whether a coherent U.S. rates/dollar shock exists and its EURUSD side.

## Point-in-time inputs

- Exact event timestamps, currency, title, tag, and ID from the already audited
  login-free Dukascopy event archive.
- Only the exact frozen USD title taxonomy from the earlier event contract.
- DXY and U.S. Treasury CFD M5 bars from the already parity-checked Dukascopy
  source.
- EURUSD executable bid/ask M5 bars and the existing causal H1 regime
  classifier.

The event source's impact, actual, forecast, previous, normalized, historical,
and effect fields are prohibited. No future return or oracle field may enter a
decision.

## Frozen decision

For every qualifying USD event-time cluster:

1. Let the event bucket be the M5 bucket containing the timestamp.
2. Use the close of the preceding, fully completed M5 bar as the baseline.
3. Wait until three event-bucket/after-event M5 bars are fully complete.
4. Require exact DXY and Treasury baseline and endpoint bars; do not forward
   fill.
5. If DXY rose and Treasury price fell, short EURUSD. If DXY fell and Treasury
   price rose, buy EURUSD. Otherwise stay in cash.
6. Enter only when the latest fully completed causal regime state is Neutral,
   non-shock, and non-compression.

There is no reaction magnitude threshold, event subgroup, clock filter,
weekday filter, per-day quota, or fitted model. Multiple qualifying clusters
can produce candidates, but the execution router permits only one open EURUSD
position.

## Frozen execution

- Entry: first EURUSD M5 open after the three observation bars.
- Retail spread floor: 0.7 pip.
- Extra slippage: 0.1 pip per side.
- Stop: adverse observation extreme plus 0.5 pip, with a 4-pip floor and
  25-pip ceiling.
- Target: 1.5R.
- Maximum hold: 12 hours.
- Same-bar ambiguity: stop first.
- Robustness: add 0.5 pip round trip and remove the best 5% of winners.

## Evaluation order

The source, rule, runner, and tests are hash-locked before candidate counts or
P&L are opened.

1. Run an outcome-blind census.
2. If any census gate fails, stop without P&L.
3. Otherwise run one frozen chronological backtest across 2019-2022, 2023,
   2024, 2025, and 2026 H1.
4. Evaluate economics, both sides, cost stress, winner concentration, and
   same-side Regime 1 oracle resemblance.

All archived periods have already been inspected elsewhere in this research
program. Chronological labels limit accidental mixing but do not make any
period a pristine holdout. Even a historical pass would require a new
post-lock prospective sample before demo consideration.

## Failure policy

Failure closes this exact family. Do not repair it by changing the observation
length, selecting event titles or hours, adding a magnitude cutoff, reversing
one side, dropping a year, or activating only a profitable recent window.
