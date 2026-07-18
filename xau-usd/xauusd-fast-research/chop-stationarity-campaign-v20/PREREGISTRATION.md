# Chop Stationarity Campaign V20 Preregistration

## Purpose and exposed history

Prior CHOP campaigns rejected generic anchors, RSI/Bollinger reversion, session
timing, microstructure follow/fade, and both directions of completed-H4 exit
pressure. Those rules treated the broad H4 `CHOP` label as if every episode were
equally mean reverting. V20 instead trades only when completed H1 observations
provide explicit statistical evidence of stationarity.

All prior outcomes are exposed. The ten-year period remains historical discovery
evidence rather than an untouched holdout.

## Frozen causal features

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- H4 regime ownership comes from the latest completed H4 bar.
- H1 rolling means, standard deviations, AR(1) coefficients and half-lives,
  variance ratios, Hurst scaling, return autocorrelation, zero-crossing rates, and
  adaptive levels use the latest completed H1 bar and earlier observations only.
- M5 confirmation uses the completed signal bar; entry is the next contiguous
  side-correct M5 open.
- Same-bar stop/target collisions resolve stop first.

## Frozen attempts

Attempts 35239 through 36238 contain exactly 1,000 policies:

- 200 AR(1)-gated mean-reversion policies.
- 200 variance-ratio-gated reversion policies.
- 200 Hurst/zero-crossing reversion policies.
- 200 negative-return-autocorrelation fades.
- 200 adaptive-level residual-reversion policies.

Each family has an outcome-blind deterministic pool of 1,000 unique definitions.
SHA-256 order admits the first 200 with at least 100 raw signals overall and 15 in
every era. No trade outcome is available during manifest construction.

## Frozen execution and gates

Four H1-ATR geometries use 0.60 to 1.20 ATR stops, 1.0R to 2.0R targets, and 3 to
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
raw-tick replication and prospective shadow evidence. Failure rejects these five
stationarity formulations without weakening gates. Shock remains an intentional
abstain state.
