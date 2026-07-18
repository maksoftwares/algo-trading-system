# Chop Episode-State Campaign V14 Preregistration

## Purpose

V12 and V13 found that generic anchor reversion and partial weekly rotations did
not produce stable chop expectancy across eras. V14 changes the decomposition,
not merely the thresholds. It treats a consecutive H4-classified chop interval as
an episode and asks whether episode age, inherited trend direction, and expanding
episode boundaries identify distinct opportunities. Because the classifier normally
passes through a transition state before chop, ancestry means the latest completed
directional trend and each policy freezes a maximum permissible ancestry age.

This is historical discovery research. It does not authorize model training,
demo execution, or live execution.

## Frozen data and causality

- Free verified Dukascopy bid/ask M5 cache from 2016-07-01 through 2026-07-01.
- M15 bars generate signals; the most recently completed H4 bar owns the regime.
- A chop episode is a consecutive run of attached `CHOP` labels.
- Episode age includes only completed M15 bars through the signal bar.
- Episode high and low exclude the current signal bar and every future bar.
- Ancestry is the latest completed `TREND_UP` or `TREND_DOWN` regime.
- Fresh-episode policies cap ancestry age between 128 and 2,048 M15 bars.
- Signals enter at the next M15 executable bid/ask open.
- Same-bar stop and target collisions resolve stop first.

## Frozen attempts

Attempts 29239 through 30238 contain exactly 1,000 policies:

- 200 mature-episode boundary false-break reentries.
- 200 mature-episode boundary bounces.
- 200 fresh-episode continuations in the inherited trend direction.
- 200 fresh-episode reversals against the inherited trend direction.
- 200 mature-episode boundary breakouts.

Candidate membership is selected deterministically by SHA-256 ordering after
signal-count preflight. Outcome values are not available during preflight.

## Frozen execution

Three geometries are tested: 0.75 ATR stop with 1.0R target and 4-hour hold,
1.0 ATR stop with 1.5R target and 8-hour hold, and 1.25 ATR stop with 2.0R target
and 12-hour hold. Spread, ticket cost, holding cost, and 0.05R stress slippage are
deducted. Each policy permits at most one open position and four entries per UTC
day.

## Frozen economic gates

A finalist must have at least 100 total trades and 15 in every era, total stress
PF at least 1.25, every-era stress PF at least 1.10, every-era average stress R at
least 0.02, closed-trade drawdown no more than 25R, and positive net stress R after
removing its five largest winners. Daily one-sided p-values receive Benjamini-
Hochberg correction across all 1,000 attempts at FDR 0.10.

## Decision rule

Any economic survivor remains a historical candidate only. It must then pass
raw-tick confirmation, independent replication, and prospective shadow evidence.
If none survives, this campaign rejects these episode-state definitions; it does
not justify loosening the gates or forcing chop trades. Shock remains an intentional
abstain state.
