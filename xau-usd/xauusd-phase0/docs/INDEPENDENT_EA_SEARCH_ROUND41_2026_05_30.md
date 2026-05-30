# Independent EA Search Round 41 - 2026-05-30

## Candidate

`h1_real_yield_inflation_mix_reversal_v0`

## Hypothesis

Shifted daily real-yield and breakeven-inflation changes may identify H1 XAUUSD reversals when the macro mix moves in gold's favor but spot has recently moved against that mix. The paired short case tests hostile real-yield/inflation-compensation deterioration after a local gold rally.

## Independence

This is not a breakout, retest, level, or pullback candidate. It uses FRED real-yield, broad-dollar, and breakeven-inflation inputs with H1 reversal timing, so it is distinct from same-family level/retest logic and distinct from the earlier pure real-yield/dollar shock or breakeven-only shock lanes.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_real_yield_inflation_mix_reversal_v0.md
```

SHA256:

```text
c08aae31b424794edcfe82e8ff9f3e2f39cef5da84f16e6222218244fe08da7f
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 408
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.2087
Max zero-trade months: 4
```

The trade-count gate passed, but PF never reached threshold. Capital.com and Pepperstone were negative across cost cases. Dukascopy was positive but below PF 1.30 and therefore not a robust cross-broker result.

## Decision

Reject v0 without tuning. The real-yield / inflation-compensation mix reversal is not an approved independent EA.
