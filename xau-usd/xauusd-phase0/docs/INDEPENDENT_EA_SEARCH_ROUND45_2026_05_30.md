# Independent EA Search Round 45 - 2026-05-30

## Candidate

`h1_credit_spread_shock_followthrough_v0`

## Hypothesis

Shifted corporate-credit spread shocks may identify H1 XAUUSD continuation when spot has already started moving in the credit-stress or credit-relief direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is a macro/credit shock follow-through test using shifted FRED `BAA10Y` and `AAA10Y` observations plus H1 local price confirmation.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_credit_spread_shock_followthrough_v0.md
```

SHA256:

```text
929a8e124517aa8cdfe39a78b5b89a888df73c882a1ce4af8f1ece016bc82f6e
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 2,070
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.1010
Max zero-trade months: 2
```

The trade-count and activity gates passed, but PF never reached threshold. Pepperstone was positive below threshold, while Capital.com and Dukascopy were negative.

## Decision

Reject v0 without tuning. The credit-spread shock follow-through expression is not an approved independent EA.
