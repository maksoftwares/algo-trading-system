# Independent EA Search Round 44 - 2026-05-30

## Candidate

`h1_treasury_curve_shock_followthrough_v0`

## Hypothesis

Shifted Treasury-rate / 2s10s curve shocks may identify H1 XAUUSD continuation when spot has already started moving in the rates-consistent direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is a macro/rates shock follow-through test using shifted FRED `DGS2`, `DGS10`, and `T10Y2Y` observations plus H1 local price confirmation.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_treasury_curve_shock_followthrough_v0.md
```

SHA256:

```text
98e84ba76547a3f382f3f76b865b384ef768e8f7b34f5af7c6d890a71e21f2f8
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 1,422
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.1648
Max zero-trade months: 11
```

The trade-count gate passed, but PF never reached threshold. Capital.com was positive below threshold, Pepperstone was negative/flat, and Dukascopy was materially negative.

## Decision

Reject v0 without tuning. The Treasury-curve shock follow-through expression is not an approved independent EA.
