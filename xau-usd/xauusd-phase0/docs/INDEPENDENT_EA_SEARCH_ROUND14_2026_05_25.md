# Independent EA Search Round 14

Generated: 2026-05-25

## Starting Point

Rounds 10-13 rejected D1/W1/H4 pullback, H4 KNN state memory, XAU/XAG plus FX composite reversion, and XAG lead-lag continuation. No independent EA was approved.

## Selected Lane

`h1_volatility_squeeze_breakout_v0`

Core idea:

```text
Trade completed H1 volatility compression only when a decisive H1 candle expands outside its Bollinger envelope, without using horizontal levels, retests, sessions, or intermarket inputs.
```

Why this is independent:

- It uses middle-timeframe volatility structure, not the approved level-and-pullback family.
- It does not use XAG, EURUSD, USDJPY, learned-state memory, calendar buckets, VWAP, round numbers, or session extremes.
- It can be falsified under the existing 9-cell matrix with existing XAUUSD H1 and M5 data.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_volatility_squeeze_breakout_v0.md
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 116 to 300 trades per cell, 3/9 PF cells reached 1.30, but all passing cells were Dukascopy and concentration failed in seven cells.
```

First-pass report:

```text
docs/H1_VOLATILITY_SQUEEZE_BREAKOUT_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
