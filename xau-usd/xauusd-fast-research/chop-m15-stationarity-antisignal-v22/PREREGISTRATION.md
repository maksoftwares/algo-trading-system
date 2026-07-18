# Chop M15 Stationarity Antisignal V22 Preregistration

## Purpose and exposed history

V21 tested 1,000 M15 stationarity-gated mean-reversion policies and found no
economic finalist. Among its 287 policies with at least 100 trades overall and 15
in every era, none was profitable, 275 had stress PF below 0.80, and median stress
PF was 0.62. V22 tests the resulting antisignal hypothesis without selecting a
favorable subset: every V21 policy is replayed in the opposite direction.

All V21 outcomes are exposed. V22 is historical discovery evidence and does not
claim an untouched holdout.

## Exact paired design

- Attempts 37239 through 38238 pair one-to-one with V21 attempts 36239 through
  37238.
- Parameters, sessions, geometries, signal timestamps, raw signal counts, and era
  raw signal counts must equal the V21 source manifest exactly.
- The original V21 direction computes signal membership and M5 confirmation.
  Direction is inverted only after that frozen mask is complete.
- Manifest preflight fails if any of the 1,000 pairs differs.
- Variant identifiers are new, but each row records its paired V21 attempt.

The five paired families contain 200 policies each:

- M15 AR(1)-stationarity continuation.
- M15 variance-ratio continuation.
- M15 Hurst/zero-crossing continuation.
- M15 return-autocorrelation continuation.
- M15 multiscale-stationarity continuation.

## Frozen causal features and execution

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- H4 regime ownership comes from the latest completed H4 bar.
- Stationarity features use completed M15 bars only.
- Risk distance uses ATR14 from the latest completed H1 bar.
- Entry is the next contiguous side-correct M5 open.
- Same-bar stop/target collisions resolve stop first.
- Spread, ticket cost, holding cost, and 0.05R stress slippage are deducted.
- One position is allowed per policy, with at most four entries per UTC day.

## Frozen gates

A finalist needs at least 100 trades and 15 in every era, total stress PF at least
1.25, every-era stress PF at least 1.10, every-era average stress R at least 0.02,
closed drawdown no more than 25R, and positive stress net R after removing its five
largest winners. Benjamini-Hochberg correction applies across all 1,000 policies at
FDR 0.10.

## Decision rule

Any survivor remains a historical candidate requiring an independently locked
implementation and prospective shadow evidence. Failure rejects the exact V21
direction inverse without weakening gates. Shock remains an intentional abstain
state.
