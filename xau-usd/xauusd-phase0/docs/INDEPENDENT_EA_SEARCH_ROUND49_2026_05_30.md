# Independent EA Search Round 49 - 2026-05-30

## Candidate

`h1_hg_gc_copper_gold_rotation_followthrough_v0`

## Hypothesis

Shifted direct HG/GC copper-versus-gold futures pressure may identify H1 XAUUSD continuation when spot has already started moving in the copper/gold rotation direction.

## Independence

This is not a breakout, retest, level, or pullback candidate. It is a direct futures-relative pressure test using public Yahoo `HG=F` and `GC=F` daily OHLCV proxies shifted before H1 XAU decisions.

## Pre-Run Lock

Hypothesis file:

```text
docs/hypothesis_h1_hg_gc_copper_gold_rotation_followthrough_v0.md
```

SHA256:

```text
ae9e4f85904f86bb518fe6e071fcbc16c65bdd3b1518bdf83fdfa99370df29c2
```

Data acquisition:

```text
scripts/acquire_hg_gc_copper_gold_proxy.py
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
Total cost-cell trades: 954
Trade-count cells >= 40: 9/9
PF cells >= 1.30: 0/9
Best PF: 1.1018
Max zero-trade months: 1
```

The candidate solved activity/sample-size, but failed edge persistence. Pepperstone was mildly positive below threshold while Capital.com and Dukascopy were negative.

## Decision

Reject v0 without tuning. The direct copper/gold futures rotation follow-through expression is not an approved independent EA.
