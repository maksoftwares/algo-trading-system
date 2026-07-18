# Chop Failed-Reversion Continuation V23 Preregistration

## Purpose and exposed history

V22's exact direction inverse found no eligible CHOP specialist, but attempt 37569
missed only the 100-trade gate: 92 trades, +22.066R, stress PF 1.406, minimum-era
PF 1.118, minimum-era average +0.078R, 6.894R drawdown, and +12.499R after its
five largest winners were removed. V23 tests the broader mechanism suggested by
that exposed result: an M15 extreme inside H4 CHOP can continue when an expected
reversion fails or stationarity begins to break.

V23 is historical discovery evidence. The reused period is not an untouched
holdout, and no result authorizes training or execution.

## Frozen causal design

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- H4 regime ownership comes from the latest completed H4 bar.
- M15 z-score, z-score change, lagged z-score, variance ratio, variance-ratio
  change, Hurst estimate, return autocorrelation, and mean slope use completed M15
  bars only.
- Risk distance uses ATR14 from the latest completed H1 bar.
- M5 confirmation is evaluated at signal close; entry is the next contiguous
  side-correct M5 open.
- Same-bar stop/target collisions resolve stop first.

## Frozen attempts

Attempts 38239 through 39238 contain exactly 1,000 policies:

- 200 variance-ratio extreme continuations with aligned M5 price and flow.
- 200 counter-flow extremes that trade continuation against an attempted fade.
- 200 expanding z-score continuations.
- 200 persistent same-side M15 extreme continuations.
- 200 stationarity-break continuations using rising variance ratio, Hurst, and
  autocorrelation.

Each family has a deterministic pool of 1,000 unique definitions. SHA-256 order
admits the first 200 definitions with at least 100 raw signals overall and 15 in
every era. Manifest construction cannot inspect trade outcomes.

## Frozen execution and gates

Four H1-ATR geometries use 0.40 to 1.00 ATR stops, 1.0R to 2.0R targets, and 2 to
12 hour maximum holds. Spread, ticket cost, holding cost, and 0.05R stress
slippage are deducted. A policy permits one open trade and at most four entries
per UTC day.

A finalist needs at least 100 trades and 15 in every era, total stress PF at least
1.25, every-era stress PF at least 1.10, every-era average stress R at least 0.02,
closed drawdown no more than 25R, and positive stress net R after removing its five
largest winners. Benjamini-Hochberg correction applies across all 1,000 policies at
FDR 0.10.

## Decision rule

Any survivor remains a historical candidate requiring an independently locked
implementation and prospective shadow evidence. Failure rejects these five
formulations without weakening gates. Shock remains an intentional abstain state.
