# Chop Failed-Reversion Envelope V24 Preregistration

## Purpose and exposed history

V23 produced no full finalist. Counter-flow attempt 38609 had 115 trades and
passed every gate except total PF (1.206 versus 1.25). Z-expansion attempt 38687
had 97 trades, PF 1.622, and passed every gate except total count and worst-era PF
(1.072 versus 1.10). V22 attempt 37569 had 92 trades and passed every gate except
total count. These exposed results motivate V24's fixed hypothesis: a tiered or
dual-mode envelope can add coverage while keeping stricter conditions on weaker
M15 deviations.

V24 reuses exposed history and is discovery evidence only. It cannot authorize
training or execution.

## Frozen causal design

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- H4 regime ownership comes from the latest completed H4 bar.
- M15 z-score, z-score change, variance ratio, autocorrelation, and mean slope use
  completed M15 bars only.
- Risk distance uses ATR14 from the latest completed H1 bar.
- M5 confirmation is evaluated at signal close; entry is the next contiguous
  side-correct M5 open.
- Composite branches share one position, one cooldown, and one daily trade limit.
  Overlapping branches produce one trade, not duplicated P&L.
- Same-bar stop/target collisions resolve stop first.

## Frozen attempts

Attempts 39239 through 40238 contain exactly 1,000 policies:

- 200 counter-flow tiered z-score/variance-ratio envelopes.
- 200 counter-flow envelopes using an OR of 3-bar and 12-bar fade attempts.
- 200 tiered z-expansion envelopes.
- 200 z-expansion envelopes using an OR of 3-bar and 12-bar confirmations.
- 200 dual-mode envelopes combining counter-flow and z-expansion events.

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

Any survivor remains a historical candidate requiring independent locked replay
and prospective shadow evidence. Failure rejects these envelope formulations
without weakening gates. Shock remains an intentional abstain state.
