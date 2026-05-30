# Independent EA Search Round 28

Generated: 2026-05-30

## Starting Point

Round 27 tested official CNY-dollar pressure and rejected it first-pass. Round 28 moved back to broker-native market participation data to check whether H1 tick-volume climax should be treated as continuation rather than the already-rejected reversal thesis.

## Selected Lane

`h1_tick_volume_climax_continuation_v0`

Core idea:

```text
Use H1 tick-count / volume participation spikes plus strong directional H1 closes to trade continuation for up to 12 H1 bars.
```

Why this is process-safe:

- It is a new versioned participation-flow hypothesis, not a same-family breakout-retest candidate.
- It tests continuation as a distinct market mechanism from the rejected tick-volume climax reversal.
- It has a fresh SHA256 lock before any result-producing matrix run.
- It stays in the research registry only and does not alter MT5 runtime, demo observers, or trade permissions.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_tick_volume_climax_continuation_v0.md
```

Synthetic smoke:

```text
PASS - 1 synthetic signal, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - 2,199 total cost-cell trades, 6/9 trade-count cells, 0/9 PF cells reached 1.30, and Dukascopy generated zero qualifying trades.
```

First-pass report:

```text
docs/H1_TICK_VOLUME_CLIMAX_CONTINUATION_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future participation-flow revisit needs a new versioned hypothesis, ideally with a higher-quality order-flow or volume source rather than broker-dependent tick-count fields.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, demo observer authority, or trade permissions.
