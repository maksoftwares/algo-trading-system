# V60 Mature Source-Health Rank Veto Prospective V2

Evidence starts at `2026-08-26T00:00:00Z`. No candidate before that boundary is
counted. The V2 policy and historical challenger configuration are hash-locked.

This observer is read-only. It may inspect candidate decisions, V60 state, and
MT5 deal history. It cannot place, modify, or close an order and cannot change
the deployed V60 policy.

For each mature specialist independently, it records whether the locked V2
policy would have vetoed an actually executed baseline candidate, then waits for
the real broker outcome. Hypothetically vetoed trades are excluded from later
simulated health so the shadow policy remains causally implementable.

Collection must continue for at least 90 days, 100 scored executed candidates,
and 10 resolved veto opportunities. Passing those gates still requires review
and explicit authorization; the observer never authorizes deployment itself.
