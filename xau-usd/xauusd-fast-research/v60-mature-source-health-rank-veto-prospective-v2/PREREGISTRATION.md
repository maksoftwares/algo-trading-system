# V60 Mature Source-Health Rank Veto Prospective V2

Evidence starts at `2026-08-26T00:00:00Z`. No candidate before that boundary is
counted. The V2 policy and historical challenger configuration are hash-locked.

This observer is read-only. It may inspect candidate decisions, V60 state, and
MT5 deal history. It cannot place, modify, or close an order and cannot change
the deployed V60 policy.

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
and 10 resolved veto opportunities. Passing those gates still requires review
and explicit authorization; the observer never authorizes deployment itself.
