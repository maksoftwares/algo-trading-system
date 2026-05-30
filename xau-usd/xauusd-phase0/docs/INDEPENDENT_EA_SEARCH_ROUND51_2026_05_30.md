# Independent EA Search Round 51 - 2026-05-30

## Candidate

`h1_move_vix_bond_vol_shock_followthrough_v0`

## Hypothesis

Shifted MOVE/VIX bond-volatility stress may identify H1 XAUUSD follow-through when spot has already started moving in the same direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is a rates-volatility versus equity-volatility stress test using public daily MOVE and VIX proxies shifted before H1 XAU decisions. It is the paired contrary expression to the rejected MOVE/VIX reversal lane, not a threshold edit.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_move_vix_bond_vol_shock_followthrough_v0.md
```

SHA256:

```text
dfc4c2a08bbde085a7b7c52d78a12b831dcc7be1191a48dd8b90bf6ab7fb3f9d
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 861
Trade-count cells >= 40: 6/9
PF cells >= 1.30: 0/9
Best PF: 1.0439
Max zero-trade months: 11
```

The candidate failed PF persistence, sample-size coverage, and activity. Capital.com was weakly positive below threshold while Pepperstone and Dukascopy were negative.

## Decision

Reject v0 without tuning. The MOVE/VIX bond-volatility shock follow-through expression is not an approved independent EA.
