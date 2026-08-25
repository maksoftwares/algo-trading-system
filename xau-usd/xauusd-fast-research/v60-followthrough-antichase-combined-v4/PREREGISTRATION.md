# V60 Follow-Through Anti-Chase Combined V4 Preregistration

## Status

Post-hoc research candidate only. Broker action and deployment are prohibited.

## Frozen hypothesis

The V57 anti-chase condition is more credible when a long entry is near the prior
24-hour high but the most recent four-hour advance represents less than 70% of the
24-hour advance. That combination describes stale trend extension with weak recent
follow-through rather than active continuation.

The combined policy is:

1. Use every frozen V2 source-health veto proposal.
2. Use a frozen V57 volatility anti-chase proposal only when `ret_24h > 0` and
   `ret_4h / ret_24h < 0.70`.
3. Deduplicate identical proposals.
4. Permit at most one veto per source and UTC calendar day, taking the first
   chronological proposal and retaining any later proposal.
5. Missing or nonfinite features retain V60 behavior.

## Selection disclosure

The 0.70 follow-through threshold was nominated after inspecting the two historical
anti-chase vetoes and three exposed August 2026 vetoes. It is a mechanistic repair to
V3's cost-stress drawdown failure, but it is not untouched evidence. V4 must remain
read-only until it passes the frozen clean prospective gates.

## Acceptance gates

- Every nominal V60 comparative gate, including 99% retention, must pass.
- Every comparative gate must also pass with an additional $0.10 and $0.20 cost
  charged to each trade.
- Exposed August net P/L and profit factor must improve and drawdown must not worsen.
- Independent Dukascopy same-timing delta must be positive with no harmed year.
- Deployment remains false until clean causal forward evidence passes.
