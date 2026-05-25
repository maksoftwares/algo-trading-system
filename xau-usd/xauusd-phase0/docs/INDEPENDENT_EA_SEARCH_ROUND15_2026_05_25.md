# Independent EA Search Round 15

Generated: 2026-05-25

## Starting Point

Round 14 rejected the H1 volatility squeeze breakout lane. The strongest repeated clue remained a Dukascopy-only pocket, which is not enough to approve an EA.

The previously blocked macro lane, `h4_real_yield_proxy_momentum_v0`, could now be tested by acquiring real FRED macro series instead of inventing an XAU-only proxy.

## Selected Lane

`h4_real_yield_proxy_momentum_v0`

Core idea:

```text
Trade H4 XAUUSD momentum only when public daily real-yield and broad dollar-index pressure align with the gold direction.
```

Why this is independent:

- It uses public macro data, not XAU-only price geometry.
- It is not a retest, sweep, session, VWAP, volatility-squeeze, XAG lead-lag, or learned-state candidate.
- It directly fixes the missing macro-data blocker that had prevented the real-yield lane from being scored.

## Data Acquisition

Public FRED CSV inputs were acquired into Phase 0 only:

- `data/raw/macro/FRED_DFII10.csv`
- `data/raw/macro/FRED_DTWEXBGS.csv`

The strategy shifts macro features by one available observation before H4 merge to avoid lookahead.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_real_yield_proxy_momentum_v0.md
```

Synthetic smoke:

```text
PASS - 3 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 18 to 64 trades per cell, 3/9 PF cells reached 1.30, all passing cells were Dukascopy; sample-size, concentration, and activity gates failed.
```

First-pass report:

```text
docs/H4_REAL_YIELD_PROXY_MOMENTUM_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future macro-regime revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
