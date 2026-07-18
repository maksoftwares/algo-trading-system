# Chop Exit-Hazard Campaign V18 Preregistration

## Purpose and exposed history

V12 through V17 rejected price anchors, episode state, ordinary M5
microstructure, and exact direction inversions inside H4 `CHOP`. Earlier generic
ML rankers, walk-forward state routers, cross-asset routing, and free COMEX
features also produced no CHOP survivor. V18 changes the target mechanism: it
tests whether a trade can be owned by CHOP at signal time when completed H4 state
is accelerating toward a directional regime exit.

All prior outcomes were exposed before V18. The ten-year period is historical
discovery evidence and does not provide an untouched holdout.

## Frozen data and causality

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- Regime, ADX, efficiency ratio, EMA slope, range width, displacement, and ATR
  pressure use only the latest completed H4 bar.
- Risk distance uses ATR14 from only the latest completed H1 bar.
- M5 direction confirmation uses only the completed signal bar and prior bars.
- Every signal must still be owned by H4 `CHOP` at signal time.
- Entry is the next contiguous side-correct M5 open; missing intervals reject
  entry, and same-bar stop/target collisions resolve stop first.

## Frozen attempts

Attempts 33239 through 34238 contain exactly 1,000 policies:

- 200 ADX/efficiency exit-pressure policies.
- 200 H4 EMA-slope inflection policies.
- 200 range-edge directional-pressure policies.
- 200 completed-H4 volatility-lift policies.
- 200 multi-factor boundary-confluence policies.

Policies vary the first 5 to 60 minutes after a completed H4 update, minimum CHOP
episode age, UTC session, directional confirmation, and one of four preregistered
H1-ATR execution geometries. Each family has a deterministic, outcome-blind pool
of 400 unique definitions; SHA-256 order admits the first 200 that meet raw-signal
coverage. Manifest membership uses signal counts only; no trade outcome is used
during preflight.

## Frozen execution and gates

The four H1-ATR geometries use 0.45 to 0.85 ATR stops, 1.25R to 3.0R targets, and
6 to 24 hour maximum holds. Spread, ticket cost, holding cost, and 0.05R stress
slippage are deducted. Each policy permits one open trade and at most four entries
per UTC day.

A finalist needs at least 100 trades and 15 in every era, total stress PF at least
1.25, every-era stress PF at least 1.10, every-era average stress R at least 0.02,
closed drawdown no more than 25R, and positive net stress R after removing its five
largest winners. Benjamini-Hochberg correction applies across all 1,000 policies at
FDR 0.10.

## Decision rule

Any survivor remains a historical candidate requiring a separately locked exact
raw-tick replication and prospective shadow evidence. Failure rejects this exit-
hazard formulation without weakening gates. Shock remains an intentional abstain
state at the portfolio level.
