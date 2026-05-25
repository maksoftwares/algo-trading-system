# Independent EA Search Round 5

Generated: 2026-05-25

## Starting Point

The latest independent lanes were rejected:

| Candidate | Result | Reason |
| --- | --- | --- |
| `h1_return_autocorrelation_state_v0` | `REJECTED_FIRST_PASS` | H1 modeled return-state produced enough trades, but 0/9 PF cells reached 1.30. |
| `h1_m5_path_skew_reversal_v0` | `REJECTED_FIRST_PASS` | M5 path-structure produced many trades, but 0/9 PF cells reached 1.30. |

This round should not tune any rejected v0. The next lane must use a distinct information source.

## Selected Lane

`h1_tick_volume_climax_reversal_v0`

Core idea:

```text
Unusually high H1 tick participation during a wide directional candle may mark exhaustion. If the completed candle closes off its extreme, the next hours may mean-revert.
```

Why this is independent:

- It uses tick-volume participation, not levels, sessions, path skew, cross-symbol data, or return autocorrelation.
- It does not use round numbers, session extremes, pivots, sweeps, VWAP, inside days, outside days, or prior high/low reclaims.
- It can be falsified under the existing 9-cell process with no new data.

## Required Data

No new data is required. The candidate uses existing XAUUSD H1 tick-count fields and M5 execution bars across the standard 9-cell matrix.

## Machine Checks

Hypothesis file:

```text
docs/hypothesis_h1_tick_volume_climax_reversal_v0.md
```

Research boundary:

```text
Research-only candidate. It must be run through explicit research commands and must not enter the active `all` expert set.
```

## First-Pass Result

`h1_tick_volume_climax_reversal_v0` was implemented as a research-only strategy, smoke-tested, and run through the real 9-cell matrix.

Result: `REJECTED_FIRST_PASS`

Reason: 0/9 cells reached PF >= 1.30, Capital.com breached loss limits, and Dukascopy produced zero trades.

Full result:

```text
docs/H1_TICK_VOLUME_CLIMAX_REVERSAL_V0_FIRST_PASS.md
```

## Process Boundary

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune this candidate in place after first-pass results. Any future revisit needs a new versioned hypothesis and fresh SHA256 lock.

This lane does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
