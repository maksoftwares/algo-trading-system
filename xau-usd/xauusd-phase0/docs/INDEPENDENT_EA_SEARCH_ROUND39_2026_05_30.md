# Independent EA Search Round 39 - 2026-05-30

## Candidate

`h1_financial_conditions_shock_reversal_v0`

## Hypothesis

Shifted FRED NFCI/ANFCI financial-conditions shocks may create short-term XAU H1 overreaction/reversal opportunities. The candidate waits for a completed H1 reversal candle after a tightening or easing shock and then simulates a market entry with a fixed 1.00 ATR stop and 1.45R target.

## Independence

This is not a breakout, retest, level, or pullback candidate. It uses shifted weekly financial-conditions observations plus H1 XAU reversal state, so it qualifies as an independent macro/financial-conditions shock-reversal test.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_financial_conditions_shock_reversal_v0.md
```

SHA256:

```text
1f1c49d9796d6d593b4c46e030f34ad33f96cc2d89441bdc6cd86658e0568c9f
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 1,284
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.0737
Max zero-trade months: 6
```

Pepperstone was positive below threshold. Capital.com and Dukascopy were negative, and Dukascopy failed the activity gate.

## Decision

Reject v0 without tuning. Financial-conditions stress is now tested in H4 stress-reversal and H1 shock-reversal forms, with no approved independent EA.
