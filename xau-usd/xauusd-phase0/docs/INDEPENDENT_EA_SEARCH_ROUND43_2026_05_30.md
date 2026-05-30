# Independent EA Search Round 43 - 2026-05-30

## Candidate

`h1_cny_dollar_pressure_reversion_v0`

## Hypothesis

Shifted official CNY-dollar pressure may create local XAUUSD exhaustion and H1 reversion when spot rejects continuation in the pressure-consistent direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is an official-data macro/FX pressure reversion test using FRED `DEXCHUS` and `DTWEXBGS` plus H1 local exhaustion timing.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_cny_dollar_pressure_reversion_v0.md
```

SHA256:

```text
36596c1a0f9f661c3d038943f9061d5926eb08b03c0e3566fe952c9daed5a720
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 279
Trade-count cells >= 40: 0/9
PF cells >= 1.30: 3/9
Best PF: 2.0324
Max zero-trade months: 7
```

Capital.com had a strong but sparse positive pocket. Pepperstone and Dukascopy were negative across all cost cases, and every cell missed the 40-trade floor.

## Decision

Reject v0 without tuning. The official CNY-dollar pressure reversion expression is not an approved independent EA.
