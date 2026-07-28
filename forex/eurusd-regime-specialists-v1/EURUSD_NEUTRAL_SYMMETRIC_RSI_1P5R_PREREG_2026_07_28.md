# EURUSD Neutral symmetric RSI 1.5R preregistration

Status: `LOCK_BEFORE_CENSUS_AND_OUTCOME`

## Question

Can the only promising causal clue from the adaptive-frequency audit become a
clean Regime 1 specialist after removing its post-selection machinery and
targeting the owner's payoff requirement directly?

This is one bounded test. It is not a search.

## Frozen entry

At each completed M15 bar, use only the latest fully completed cross-asset
classifier state. Trade only when that state is `NEUTRAL`, not shock, and not
joint compression.

- Long: RSI(14) is at most 30 and bid close is below the completed 20-period
  Bollinger midpoint.
- Short: RSI(14) is at least 70 and bid close is above the completed midpoint.
- Enter at the first archived M5 open at or after completion.

There are no blocked hours, body threshold, calendar mask, H4 size overlay,
trade-per-day target, probability threshold, fitted model, or direction
preference. Both directions are mandatory and all results use fixed
0.01-lot-equivalent sizing.

## Frozen exit and costs

- Initial stop uses the wider of 1.4 ATR(14), 3 pips, or the last six completed
  M15 executable-side extremes.
- Reject stop distances above 70 pips.
- Target is 1.50 times initial risk.
- Maximum hold is 12 hours.
- Same-M5-bar stop and target ambiguity resolves stop first.
- Entry and exit use bid/ask bars, at least 0.7 pip spread, and 0.1 pip adverse
  slippage per side.
- One position may be open.

## Chronology and evidence boundary

The fixed rule is reported separately on 2019-2022, 2023, 2024, 2025, and
2026 H1. None is described as a pristine holdout because the repository has
already inspected all archived history. The chronological blocks test temporal
consistency only. Genuinely untouched confirmation can begin only after this
lock on newly arriving data.

The outcome-blind census is opened first. If its fixed minimum counts fail, no
P&L is loaded. Passing the census permits exactly one full backtest with the
locked source and configuration.

## Admission

The exact rule must satisfy every gate in
`config/frozen_neutral_symmetric_rsi_1p5r.json`, including:

- 45-55% overall win rate;
- 1.35-1.75 realized payoff;
- overall PF at least 1.15 and every chronological block at least 1.0;
- both sides independently profitable with at least 30 trades;
- positive PF after removing the best 5% and after a further 0.5-pip
  round-trip haircut;
- maximum closed drawdown at most 20R;
- nonzero oracle resemblance at the frozen precision and recall floors.

Frequency is not an admission criterion.

Failure closes this exact rule. No side deletion, entry-hour filter, threshold
change, RR change, stop change, or favorable-window activation is allowed after
the outcome.
