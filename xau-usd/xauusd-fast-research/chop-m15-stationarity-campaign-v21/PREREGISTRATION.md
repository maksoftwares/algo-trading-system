# Chop M15 Stationarity Campaign V21 Preregistration

## Purpose and exposed history

V20 found no eligible H1-stationarity specialist. Its strongest adaptive-level
policy had stable-looking PF but only 21 trades and failed winner-concentration
gates. V21 tests whether the same statistical structures are observable at M15
cadence often enough to produce independent opportunities rather than repeated
signals from a few H1 episodes.

All prior outcomes are exposed. V21 is historical discovery evidence and does not
claim an untouched holdout.

## Frozen causal features

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- H4 regime ownership comes from the latest completed H4 bar.
- M15 AR(1), half-life, variance ratio, Hurst scaling, autocorrelation,
  zero-crossing, and multiscale deviation features use only completed M15 bars.
- Multi-day M15 windows are 192, 384, and 768 bars; adaptive spans are 96, 192,
  and 384 bars.
- Risk distance uses ATR14 from the latest completed H1 bar.
- Entry is the next contiguous side-correct M5 open, and same-bar collisions resolve
  stop first.

## Frozen attempts

Attempts 36239 through 37238 contain exactly 1,000 policies:

- 200 M15 AR(1)-gated mean-reversion policies.
- 200 M15 variance-ratio reversion policies.
- 200 M15 Hurst/zero-crossing reversion policies.
- 200 M15 negative-return-autocorrelation fades.
- 200 M15 multiscale stationarity-reversion policies.

Each family has an outcome-blind deterministic pool of 1,000 unique definitions.
SHA-256 order admits the first 200 with at least 100 raw signals overall and 15 in
every era. No trade outcome is available during manifest construction.

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

Any survivor remains a historical candidate requiring separately locked exact
raw-tick replication and prospective shadow evidence. Failure rejects these M15
stationarity formulations without weakening gates. Shock remains an intentional
abstain state.
