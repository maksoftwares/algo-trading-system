# Expanded Candidate Dataset V3 Preregistration

This contract is frozen before V3 artifacts are built.

## Purpose

The pooled candidate-quality V1 model failed, and two regime-specific V2
families lacked enough evidence. V3 increases the number of consistently defined
winning and failing labels without treating repeated strategy attempts as
independent trades.

## Populations

1. `HF_PRIMARY` contains the completed high-frequency V4 event/action ledger:
   three mechanical families, three fixed actions, causal Dukascopy features,
   and side-correct stressed outcomes.
2. `CANONICAL_BENCHMARK` is the unchanged 3,752-row Step 3 dataset. It is bound
   by hash and used only for overlap and benchmark diagnostics in V3.
3. `JOURNEY_QUARANTINE` is the unchanged journey action library. It is bound by
   hash and used only for overlap diagnostics. It cannot enter a V3 model fit.

The three populations must never be pooled by row count alone.

## Independence And Weights

Candidate events less than or equal to 30 minutes apart form one outcome-blind
structural episode. Each event/action row receives weight:

`1 / resolved_events_in_episode / completed_actions_for_event`

Events without a completed forward label remain visible in the event registry but
receive no training row. Weights must sum to one within every structural episode
that has at least one resolved event. Every event/action key must be unique. All
actions for an event and all events for an episode remain in the same
chronological partition.

## Feature And Label Boundary

Only the fixed normalized, directional, regime, time-cycle, opportunity-density,
and action-geometry columns in the configuration are model features. IDs,
timestamps, absolute prices, alignment errors, account feasibility, outcomes,
exit information, and historical decisions are forbidden as model features.

The binary label is `stress_net_r > 0`. The economic target remains the full
continuous `stress_net_r`. Labels retain observed bid/ask spread, stop-first M5
ambiguity, gap-through-stop handling, ticket and holding costs, and 0.05R stress.

## Chronological Firewall

Six expanding July-to-July folds are fixed. Every fit and calibration partition
is purged by the maximum label end of its complete structural episode. The most
recent fold ends on 2026-07-01. These outcomes have been exposed elsewhere, so
the folds are development chronology, not a pristine holdout.

## Authority

V3 is a dataset and audit only. It cannot authorize model fitting, threshold
selection, portfolio simulation, Python serving, ML shadow, EA consumption,
demo/live trading, or broker action. A later model contract must be locked before
using V3 outcomes for model selection.
