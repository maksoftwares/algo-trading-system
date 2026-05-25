# Independent EA Search Round 6

Generated: 2026-05-25

## Starting Point

The latest independent lanes were rejected:

| Candidate | Result | Reason |
| --- | --- | --- |
| `h1_m5_path_skew_reversal_v0` | `REJECTED_FIRST_PASS` | M5 path-structure produced many trades, but 0/9 PF cells reached 1.30. |
| `h1_tick_volume_climax_reversal_v0` | `REJECTED_FIRST_PASS` | Tick-volume climax failed PF survival and produced no Dukascopy trades. |

This round should not tune any rejected v0. The next lane must use a distinct information source.

## Selected Lane

`h1_walk_forward_linear_state_v0`

Core idea:

```text
Train a small ridge-regularized linear model walk-forward on completed H1 history only, then trade when the current learned H1 state predicts enough normalized 12-hour forward movement.
```

Why this is independent:

- It is learned walk-forward state, not a fixed threshold rule.
- It does not use round numbers, session extremes, pivots, sweeps, VWAP, inside days, outside days, prior high/low reclaims, XAGUSD, or FX proxies.
- It is the first proper AI-style lane while remaining deterministic, local, and auditable.
- It can be falsified cleanly under the existing 9-cell process.

## Required Data

No new data is required. The candidate uses existing XAUUSD H1 feature bars and M5 execution bars across the standard 9-cell matrix.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_walk_forward_linear_state_v0.md
```

Research boundary:

```text
Research-only candidate. It must be run through explicit research commands and must not enter the active `all` expert set.
```

Synthetic smoke:

```text
PASS - 12 synthetic signals, market trade plan generated, active registry disabled.
```

Real 9-cell matrix:

```text
REJECTED_FIRST_PASS - blocker-fixed run produced 561 to 788 trades per cell, but 0/9 PF cells reached 1.30.
```

First-pass report:

```text
docs/H1_WALK_FORWARD_LINEAR_STATE_V0_FIRST_PASS.md
```

## Process Boundary

Do not tune this candidate in place after first-pass results. Any future revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
