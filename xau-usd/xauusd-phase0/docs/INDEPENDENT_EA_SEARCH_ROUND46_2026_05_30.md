# Independent EA Search Round 46 - 2026-05-30

## Candidate

`h1_financial_conditions_shock_followthrough_v0`

## Hypothesis

Shifted NFCI/ANFCI financial-conditions shocks may identify H1 XAUUSD continuation when spot has already started moving in the stress-consistent or relief-consistent direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is a macro/financial-stress shock follow-through test using shifted FRED `NFCI` and `ANFCI` observations plus H1 local price confirmation.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_financial_conditions_shock_followthrough_v0.md
```

SHA256:

```text
705ce69a78132ad314137ef8f80765afc9651a4e796e4f194228c51674298999
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 2,439
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.0933
Max zero-trade months: 6
```

The trade-count gate passed, but PF never reached threshold and activity failed in the weakest window. Pepperstone was positive below threshold, while Capital.com and Dukascopy were negative.

## Decision

Reject v0 without tuning. The financial-conditions shock follow-through expression is not an approved independent EA.
