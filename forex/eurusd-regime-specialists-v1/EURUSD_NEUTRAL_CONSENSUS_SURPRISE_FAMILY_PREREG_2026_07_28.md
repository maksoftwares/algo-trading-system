# EURUSD Neutral consensus-surprise family preregistration

## Research question

Can a public U.S. macro consensus surprise choose the hindsight oracle's side
at Regime 1's fixed 00:00, 00:15, 00:30, and 00:45 UTC clocks, either alone or
when confirmed by the completed prior 15 minutes of EURUSD price direction?

The family is frozen before any real candidate census or P&L. It contains
exactly two variants. They are separate hypotheses, not a menu from which the
better historical result may be selected.

## Frozen source and information boundary

For CPI, PPI, and NFP, use only rows whose timestamp and actual value were
reconciled exactly to the archived official BLS initial-release source. The
release surprise is:

`official initial value - TradingView forecast value`

The historical forecast field was retrieved after each event and was not
independently timestamped before release. This makes the entire archive
adaptive historical research, not pristine out-of-sample evidence. A future
prospective test must capture and checksum each forecast before its release.

## Frozen finite family

### MACRO_SURPRISE_CARRY

- Positive U.S. surprise: EURUSD SHORT.
- Negative U.S. surprise: EURUSD LONG.
- Equal actual and forecast: cash.
- At each Neutral clock, use the latest directional release strictly before
  entry and no more than 72 hours old.

### MACRO_SURPRISE_PRICE_AGREEMENT

Start with the same macro side, then require the completed prior 15-minute
EURUSD direction to agree:

`bid_close[entry - 1 M5 bar] - bid_close[entry - 4 M5 bars]`

- Positive return confirms LONG.
- Negative return confirms SHORT.
- Zero return or disagreement means cash.
- The entry M5 bar is forbidden from the confirmation calculation.

There is no surprise-magnitude threshold, price threshold, fitted model,
family weight, clock selection, year selection, or frequency quota.

## Frozen execution

- Entry clocks: 00:00, 00:15, 00:30, and 00:45 UTC on existing outcome-blind
  Neutral dates.
- Stop: 4 pips.
- Target: 1.5R (6 pips).
- Maximum hold: 12 hours.
- Retail spread floor: 0.7 pip.
- Extra slippage: 0.1 pip per side.
- Same-bar ambiguity: stop first.
- Up to four concurrent clock positions.
- Portfolio weight: 0.25R per ticket.
- Stress tests: another 0.5 pip round trip and removal of the best 5% of
  winners.

The exit is inherited from the frozen four-clock oracle-comparison contract.

## Evaluation order and gates

1. Hash-lock and push the source, contract, implementation, runner, and
   synthetic causality tests.
2. Build one outcome-blind census for each variant. Parent outcome, oracle,
   exit, and P&L columns are forbidden.
3. Do not calculate P&L for a variant whose census fails.
4. Run one frozen 2019-2022 / 2023 / 2024 / 2025 / 2026 H1 evaluation for
   every census-passing variant.
5. Judge each variant independently against the sample, approximately 50%
   win-rate, approximately 1.5 payoff, PF, every-window, both-side, cost,
   winner-removal, drawdown, and oracle-resemblance gates.

A variant cannot be accepted because it is the best of the two, because only
one year is profitable, or because it can be combined with the other after
returns are known. Even a full pass remains research-only until it survives a
new prospectively captured sample.

## Failure policy

Reject the exact failed variant. Do not change the 72-hour age, add a
threshold, remove a family or clock, reverse a side, delete a year, alter the
exit, or activate an isolated profitable period after outcomes.
