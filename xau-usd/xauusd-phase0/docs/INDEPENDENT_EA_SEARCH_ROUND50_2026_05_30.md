# Independent EA Search Round 50 - 2026-05-30

## Candidate

`h1_hg_gc_copper_gold_rotation_reversal_v0`

## Hypothesis

Shifted direct HG/GC copper-versus-gold futures pressure may identify H1 XAUUSD overextension reversal when spot has already moved with the copper/gold rotation and then rejects.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is a direct futures-relative pressure reversal test using public Yahoo `HG=F` and `GC=F` daily OHLCV proxies shifted before H1 XAU decisions. It is the paired contrary claim to the rejected follow-through version, not a threshold edit.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_hg_gc_copper_gold_rotation_reversal_v0.md
```

SHA256:

```text
cadd91ff0014f327a16f13011a6b45da5d90ea290cf161362b8a9243a1a98ff7
```

Data source:

```text
data/reference/futures/hg_gc_daily_yahoo_2015_2025.csv
Rows: 2,636 merged HG=F/GC=F daily rows
```

Synthetic smoke:

```text
PASS, 1 signal
```

## First-Pass Result

Status: `REJECTED_FIRST_PASS`

Summary:

```text
Total cost-cell trades: 519
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 1/9
Best PF: 1.3188
Max zero-trade months: 4
```

The candidate solved sample size, but failed edge persistence and activity. The only PF-clearing pocket was Dukascopy best-case; Capital.com and Pepperstone were negative.

## Decision

Reject v0 without tuning. The direct copper/gold futures rotation reversal expression is not an approved independent EA.
