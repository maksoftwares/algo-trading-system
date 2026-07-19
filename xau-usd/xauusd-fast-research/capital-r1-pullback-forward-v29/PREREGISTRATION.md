# Capital R1 Pullback Forward Shadow V29

## Purpose

V29 is an outcome-blind, read-only Python adapter for the exact MT5 specialist
`r1_pullback_long_v2_m15_session_09_15`. It closes the missing R1 pullback
coverage in the Core candidate ledger. It does not promote the specialist and
does not increase trading authority.

## Frozen Rule

- Signal: long H1 EMA20/EMA50 pullback confirmed by the previous completed M15 bar.
- Regime: long entries only in the exact R1 uptrend state.
- Session: broker-server hour `09:00 <= hour < 15:00`.
- Stop: six-M15 swing low minus `0.25 * M15 ATR14`, floored at 350 points.
- Guards: spread at most 75 points, estimated cost at most `0.15R`, and stop at
  most 2,200 points.
- ATR: the exact MT5 `iATR` behavior observed in the bound native evidence, a
  simple average of the last 14 true ranges.
- Direction: long only.

All feature inputs are completed before the decision timestamp. A decision at
M15 open `T` consumes M15 shift 1 and the most recent completed H1/H4/D1 bars.
The online runner loads 30 M15 days, 120 H1 days, 400 H4 days, and 800 D1 days.
These windows exceed every explicit lookback and leave the EMA50 initialization
weight negligible; changing them is a rule-dependency change.

## Historical Identity Gate

Before locking, the Python adapter must reproduce the bound MT5 evidence for
`2022-07-01T00:00:00Z <= T < 2026-07-01T00:00:00Z`:

- all 94,223 decision rows;
- all 3,318 raw signal timestamps and reasons;
- all guard actions and reasons;
- all 413 accepted-entry timestamps;
- stop distance, break distance, and cost ratio within the precision recorded
  by the native logs.

Any structural mismatch fails the lock. Source artifacts, bar-history
fingerprints, implementation files, and configuration are hash-bound.

## Forward Boundary

The forward interval begins at `2026-07-20T00:00:00Z`. No outcome or P&L may be
opened by this package. Candidate rows are append-only and idempotent by a
version- and dependency-bound candidate ID. The first observed evaluation of
each forward M15 decision is also append-only; later polls may not revise its
spread, guard result, or signal state.

## Authority

The historical specialist remains `SHADOW_ONLY`: its standalone win rate was
below the promotion gate and its combined book exceeded the locked monthly
concentration gate. Therefore V29 grants no Python execution, EA consumption,
demo, live, or broker-action authority.

MT5 history is replication evidence for this already defined rule, not a claim
that MT5 is the best-quality research feed. ML use remains unauthorized until
the separate prospective validation and confirmation decisions are complete.

## Prohibited Actions

- No same-version threshold or rule changes after lock.
- No outcome/P&L inspection by the candidate collector.
- No orders, positions, terminal settings, chart changes, or account changes.
- No claim that historical parity is prospective profitability proof.
