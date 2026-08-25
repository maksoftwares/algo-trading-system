# V60 Mature Source-Health Rank Veto Prospective V2

Evidence starts at `2026-08-26T00:00:00Z`. No candidate before that boundary is
counted. The V2 policy and historical challenger configuration are hash-locked.

This observer is read-only. It may inspect candidate decisions, V60 state, and
MT5 deal history. It cannot place, modify, or close an order and cannot change
the deployed V60 policy.

## Immutable evidence protocol

Each first-seen causal score, baseline execution decision, broker entry fill,
and resolved broker outcome is written to a hash-linked evidence chain. Entry
evidence freezes the actual time, side, volume, volume-weighted price, and costs.
Repeated observations must match the original immutable payload exactly. A
changed score, rank, source, entry, policy decision, exit, or broker P/L fails
the observer closed. The evidence recorder implementation is hash-locked before
the clean boundary, and every resolved execution requires complete fill details.

The observer also records a hash-linked XAU-only equity mark every five-minute
cycle. The baseline mark includes closed P/L and current MT5 floating P/L; the
V2 mark removes positions the locked policy would have vetoed. At least 5,000
marks are required and V2 sampled equity drawdown cannot exceed V60. Before any
deployment decision, the hash-locked exact replay must process stored prospective
ticks to measure between-sample equity drawdown. It marks longs to bid and shorts
to ask, handles overlapping positions, reconciles final broker P/L, and records
the SHA-256 of every immutable daily tick file used. Multiple entry fills and
partial exit fills are replayed at their actual timestamps and volumes.

## All-source causal ranking

The deployed ML top-up scorer intentionally ranks only sources eligible for an
additional position. That is narrower than historical V2, which can veto any
mature source with a causal rank. V2 therefore uses a separate observer-only
rank path with the same hash-locked model and serving implementation.

- Ranking begins at `2026-07-21T00:00:00Z`, before the clean outcome boundary.
- The frozen historical reference contains 1,676 out-of-sample scores.
- Every emitted source candidate is scored, including R1, V25, and V8.
- Only strictly earlier score timestamps enter the expanding reference.
- Candidates at the same timestamp use the same prior reference and cannot
  influence one another's rank.
- No outcome, broker P/L, or future price is used to create a score or rank.
- Observer ranks cannot authorize any broker action or ML top-up.

For each mature specialist independently, it records whether the locked V2
policy would have vetoed an actually executed baseline candidate, then waits for
the real broker outcome. Hypothetically vetoed trades are excluded from later
simulated health so the shadow policy remains causally implementable.

Collection must continue for at least 90 days, 100 scored executed candidates,
100 resolved baseline executions, and 10 resolved veto opportunities. Every
resolved execution must have a causal rank and V2 must retain at least 95% of
baseline trades. On the entire resolved forward portfolio, V2 net P/L and PF
must be no worse than V60 and V2 closed-trade drawdown must be no higher. The
veto cohort must have PF below 0.8 and positive avoided P/L. Passing every gate
still requires review and explicit authorization; the observer never authorizes
deployment itself.
