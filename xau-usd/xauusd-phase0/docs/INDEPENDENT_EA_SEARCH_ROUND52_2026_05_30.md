# Independent EA Search Round 52 - 2026-05-30

## Candidate

`weekend_gap_reversion_v0`

## Hypothesis

Weekend-style market breaks may create XAUUSD opening gaps that mean-revert toward the pre-gap close when the first completed M15 candle rejects continuation.

## Independence

This is not a breakout, retest, level, pullback, macro, ETF, or intermarket candidate. It is a calendar/microstructure gap-fill hypothesis using only broker XAUUSD M15 context and M5 execution simulation.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_weekend_gap_reversion_v0.md
```

SHA256:

```text
af24af0c81359b773a9daa538172279cdad8f49b9a47862c978cabd932f40100
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 33
Trade-count cells >= 40: 0/9
PF cells >= 1.30: 0/9
Best PF: 0.5933
Max zero-trade months: 36
```

The candidate failed sample-size, activity, PF persistence, and cross-broker transfer. Capital.com produced only sparse negative trades; Pepperstone and Dukascopy produced no qualifying trades in the current matrix windows.

## Decision

Reject v0 without tuning. The current weekend-gap reversion expression is not an approved independent EA.
