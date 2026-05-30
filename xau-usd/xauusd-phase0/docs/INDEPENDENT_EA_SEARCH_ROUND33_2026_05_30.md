# Independent EA Search Round 33

Generated: 2026-05-30

## Starting Point

Round 32 rejected plain VIX risk-off followthrough. Round 33 moved one level deeper into equity-volatility information by testing the VIX/VXV term structure rather than absolute VIX.

## Selected Lane

`h1_vix_term_structure_inversion_reversal_v0`

Core idea:

```text
Use shifted VIX/VXV term-structure inversion as a panic proxy, then fade short-term XAU H1 exhaustion when the completed H1 candle confirms reversal.
```

Why this is process-safe:

- It is a fresh versioned v0 hypothesis.
- It is independent of the breakout-retest / level-and-pullback family.
- It does not tune rejected absolute VIX candidates; it uses a different term-structure feature.
- It uses official public FRED `VIXCLS` and `VXVCLS` data.
- It was SHA256-locked before its result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Data Note

`FRED_VXVCLS.csv` was acquired from the official FRED graph CSV endpoint into ignored local raw data:

```text
data/raw/risk/FRED_VXVCLS.csv
```

The acquisition helper is:

```text
scripts/acquire_vix_term_structure_proxy.py
```

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_vix_term_structure_inversion_reversal_v0.md
```

Research hash:

```text
8c6e92b9209ce12cc6f048ebce2b1b76d26611b985d26f82746bf5829bf906e5
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 513 total cost-cell trades, 9/9 trade-count cells, but 0/9 PF cells reached 1.30 and max zero-trade months reached 4.
```

First-pass report:

```text
docs/H1_VIX_TERM_STRUCTURE_INVERSION_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. This lane does not alter active Phase 1/Phase 3 observation, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
