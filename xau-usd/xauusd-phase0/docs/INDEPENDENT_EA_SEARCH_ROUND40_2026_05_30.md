# Independent EA Search Round 40 - 2026-05-30

## Candidate

`h1_gvz_realized_vol_spread_reversal_v0`

## Hypothesis

Shifted GVZ gold implied volatility that is rich versus recent H1 realized XAU volatility may identify short-term overreaction and reversal opportunities. The candidate waits for a completed H1 reversal candle after GVZ percentile/return and implied-minus-realized spread conditions align.

## Independence

This is not a breakout, retest, level, or pullback candidate. It uses a gold options implied-volatility index compared to realized XAU volatility, so it is distinct from same-family level/retest logic and also distinct from the prior GVZ-only and GVZ/VIX relative-volatility lanes.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_gvz_realized_vol_spread_reversal_v0.md
```

SHA256:

```text
4589331e632b1a1b97b2f50b97277ba2a9666ada2395cb0222894e41d0d98d80
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 309
Trade-count cells >= 40: 3/9
PF cells >= 1.30: 1/9
Best PF: 1.3098
Max zero-trade months: 13
```

The only PF-threshold cell was Dukascopy best-case. Median and P95 Dukascopy fell below threshold, and Capital.com/Pepperstone failed both PF and trade-count coverage.

## Decision

Reject v0 without tuning. The GVZ-realized-volatility spread is not an approved independent EA.
