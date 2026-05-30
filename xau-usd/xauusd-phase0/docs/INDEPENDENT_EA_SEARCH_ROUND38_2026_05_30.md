# Independent EA Search Round 38 - 2026-05-30

## Candidate

`h1_credit_spread_shock_reversal_v0`

## Hypothesis

Shifted FRED BAA10Y/AAA10Y corporate credit-spread shocks may create short-term XAU H1 overreaction/reversal opportunities. The candidate waits for a completed H1 reversal candle after a credit-stress or credit-relief shock and then simulates a market entry with a fixed 1.00 ATR stop and 1.45R target.

## Independence

This is not a breakout, retest, level, or pullback candidate. It uses shifted daily corporate-credit spread observations plus H1 XAU reversal state, so it qualifies as an independent macro/credit shock-reversal test.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_credit_spread_shock_reversal_v0.md
```

SHA256:

```text
9fae1c419722b818d66028084548b467a0a96d45a97ae9eaf1671aaf58c91cb0
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 1,002
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.0278
Max zero-trade months: 3
```

The only positive pocket was Dukascopy best/median cost, and even that stayed far below the PF threshold. Capital.com and Pepperstone were negative.

## Decision

Reject v0 without tuning. Corporate credit-spread stress is now tested in H4 momentum and H1 shock-reversal forms, with no approved independent EA.
