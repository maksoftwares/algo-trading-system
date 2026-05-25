# Independent EA Search Round 23

Generated: 2026-05-25

## Starting Point

Round 22 rejected the single-family credit-spread lane. The owner also asked whether AI-style thinking could be integrated into the search, so the next defensible step was a transparent fixed macro vote rather than a trained or optimized model.

## Selected Lane

`h4_macro_composite_risk_state_v0`

Core idea:

```text
Trade H4 XAUUSD only when a fixed, shifted macro vote across rates, dollar, inflation expectations, Treasury curve, credit spreads, VIX, GVZ, and financial conditions reaches a strong bullish or bearish score, then H4 price momentum confirms direction.
```

Why this is independent:

- It uses a cross-domain macro state instead of any single rejected data family.
- It is not a retest, sweep, session, VWAP, XAG lead-lag, single FX proxy, single real-yield lane, single breakeven lane, single Treasury curve lane, single credit lane, COT positioning, GVZ-only, VIX-only, or NFCI/ANFCI-only candidate.
- It implements AI-style thinking as a fixed transparent vote table with no fitting or post-result threshold search.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h4_macro_composite_risk_state_v0.md
```

Synthetic smoke:

```text
PASS - 20 synthetic signals, market trade plans generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 34 to 98 trades per cell, 6/9 PF cells reached 1.30, all cells were positive, but Capital.com trade count was below 40 and concentration/activity failed in every cell.
```

First-pass report:

```text
docs/H4_MACRO_COMPOSITE_RISK_STATE_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future macro-composite revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
