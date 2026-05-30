# Independent EA Search Round 42 - 2026-05-30

## Candidate

`h1_real_yield_inflation_mix_followthrough_v0`

## Hypothesis

Shifted daily real-yield and breakeven-inflation changes may identify H1 XAUUSD continuation when spot has already started moving in the same direction as the macro mix.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is a macro-decomposition follow-through test using FRED real-yield, broad-dollar, and breakeven-inflation inputs with H1 timing.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_real_yield_inflation_mix_followthrough_v0.md
```

SHA256:

```text
03a64898d50d0e7b02c99450e0c88539def73e9c4a40c62fc55bdd0ca8c85649
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 759
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.1544
Max zero-trade months: 2
```

The trade-count and activity gates passed, but PF never reached threshold. Pepperstone was positive below threshold; Capital.com and Dukascopy were negative.

## Decision

Reject v0 without tuning. The real-yield / inflation-compensation mix follow-through is not an approved independent EA.
