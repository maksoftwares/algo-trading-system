# V60 Dual-Veto Budget V3 Preregistration

## Status

Retrospective challenger research only. Broker action and deployment are prohibited.

## Motivation

The frozen V2 source-health veto and the frozen V57 volatility anti-chase veto each
improve the historical V60 replay. Their uncapped union removes 14 of 1,390 trades,
which narrowly misses the existing 99% trade-retention gate. The gate will not be
relaxed.

## Frozen composition

1. Form the union of the V2 and anti-chase veto proposals.
2. Deduplicate proposals for the same trade.
3. Sort proposals by scheduled entry time and trade ID.
4. Permit at most one veto for each `(source_id, UTC calendar day)`.
5. Retain every later proposal in that source/day, regardless of its future outcome.
6. Missing proposal metadata retains baseline V60 behavior.

The daily budget is causal and exists to preserve opportunity coverage. It is not
allowed to choose which trade to retain using realized P/L.

## Locked acceptance gates

- V60 benchmark identity must match exactly.
- Net P/L and profit factor must not be below V60.
- Closed and exact sampled equity drawdown must not exceed V60.
- At least 99% of V60 trades and frequency must remain.
- No calendar year or final 3/6/12-month window may be harmed.
- At least 10 executed vetoes must exist and their baseline profit factor must be below 1.
- Exposed August 2026 net P/L, profit factor, and drawdown must improve.
- At both locked additional-cost stresses, comparative net P/L, profit factor,
  closed drawdown, equity drawdown, calendar years, and recent windows must pass.
- Deployment remains prohibited until the frozen combined policy passes clean
  prospective evidence gates.

## Selection disclosure

All historical outcomes and August 2026 outcomes were exposed before nomination.
This package can nominate a forward challenger, but it cannot authorize deployment.
