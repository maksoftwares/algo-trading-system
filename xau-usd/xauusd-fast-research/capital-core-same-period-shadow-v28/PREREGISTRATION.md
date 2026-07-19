# Capital Core Same-Period Shadow V28 Preregistration

Date: 2026-07-20

## Purpose

Collect causal same-period candidate evidence for the frozen Core while V24.1 and
V26 collect their untouched Capital forward windows. V28 does not create a new
strategy, tune a threshold, train a model, calculate forward P&L, or authorize an
order.

## First Frozen Scope

V28 imports the exact R2/R3 feature, regime, signal, component, and composite
definitions that produced the frozen five-specialist ledger. Before lock, the
adapter must reproduce every historical R2/R3 candidate identity, timestamp,
direction, parameter, and ATR value from the frozen candidate artifact.

The live adapter uses only completed MT5 M5 bars from account 1033669 and derives
complete H1/H4 bars causally. At a terminal completed H4 bar it may schedule the
candidate at that bar end without waiting for a future H4 close. It records a
candidate ledger only. No outcome, return, win rate, P&L, or economic gate may be
opened by this runner.

## Component Boundary

- R1 box remains collected by the separate repaired read-only R1 sidecar.
- R1 pullback is not yet implemented in V28 and cannot count toward complete Core
  frequency.
- R2 and R3 are collected by V28 after the fixed boundary.
- R4 requires a frozen Capital microstructure reconstruction.
- R5 requires contemporaneous macro/cross-asset state and a causal prior-outcome
  router.

No partial set may be described as complete same-period Core evidence.

## Forward Boundary

The first R2/R3 candidate time is 2026-07-20 00:00:00 UTC. The contract must be
locked before any matching July 20 prospective tick file exists. Validation and
confirmation each require 20 complete weekdays, but their economic evaluation is
outside this candidate-only runner.

## Safety

The runner verifies the exact demo login/server, connected terminal, completed
bars, feed freshness, dependency digest, and contract lock. It exposes no order
method and writes `trade_permission=false`, `broker_action_allowed=false`, and
`python_execution_authorized=false` on every candidate and status record.

No model training, Python prediction, EA consumption, demo execution, live
execution, or broker action is authorized.
