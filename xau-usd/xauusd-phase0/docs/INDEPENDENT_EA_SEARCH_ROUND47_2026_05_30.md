# Independent EA Search Round 47 - 2026-05-30

## Candidate

`h1_gvz_realized_vol_spread_followthrough_v0`

## Hypothesis

Shifted GVZ implied-volatility premium versus H1 XAU realized volatility may identify H1 XAUUSD continuation when spot has already started moving in the volatility-pressure direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is an options-implied-volatility premium follow-through test using shifted public FRED `GVZCLS` observations plus H1 local realized-volatility and price confirmation.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_gvz_realized_vol_spread_followthrough_v0.md
```

SHA256:

```text
213411a43c88a109201a43b222db108da61c5c171600da7a407e0e32a70db965
```

Synthetic smoke:

```text
PASS, 2 signals
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 528
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 1/9
Best PF: 1.3142
Max zero-trade months: 12
```

All cells were positive, but the only PF-threshold cell was Dukascopy best-case. Capital.com and Pepperstone failed the activity gate with 11-12 zero-trade months.

## Decision

Reject v0 without tuning. The GVZ-realized-volatility spread follow-through expression is a weak independent clue, not an approved independent EA.
