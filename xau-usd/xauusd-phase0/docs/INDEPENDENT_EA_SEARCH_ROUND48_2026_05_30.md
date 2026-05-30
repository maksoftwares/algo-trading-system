# Independent EA Search Round 48 - 2026-05-30

## Candidate

`h1_gvz_vix_vol_premium_followthrough_v0`

## Hypothesis

Shifted GVZ/VIX gold-volatility premium may identify H1 XAUUSD continuation when spot has already started moving in the volatility-premium direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is an options/equity-volatility relative-premium follow-through test using shifted public FRED `GVZCLS` and `VIXCLS` observations plus H1 local XAU continuation state.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_gvz_vix_vol_premium_followthrough_v0.md
```

SHA256:

```text
cdc36c7cce61609d67c1e58473100ffdd9521c3d297a7a23715f345626b60700
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 1,926
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 0.9447
Max zero-trade months: 7
```

All broker/cost windows were negative. The candidate solved sample size, but no cell reached a positive edge threshold.

## Decision

Reject v0 without tuning. The GVZ/VIX volatility-premium follow-through expression is a clean independent rejection, not an approved EA.
