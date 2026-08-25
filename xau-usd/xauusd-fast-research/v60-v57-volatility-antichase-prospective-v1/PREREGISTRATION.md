# V60 V57 Volatility Anti-Chase Prospective V1

Boundary: `2026-08-26T00:00:00Z`.

This is a read-only prospective test of the post-hoc August robustness rule in
`v60-v57-volatility-antichase-v1`. It cannot place, modify, or close an order.
V60 remains the sole broker-action policy.

For each V57 candidate, the observer must immutably record the causal model rank,
ATR ratio, distance to the prior 24-hour high, baseline execution decision, and
broker lifecycle. A decision counts only when it is recorded within 120 seconds
of scheduled entry and strictly before broker exit. Missing, stale, late, or
nonfinite information retains the V60 trade in every metric and replay.

The frozen veto is limited to mature V57 long candidates with rank below 0.10,
ATR ratio at least 1.20, and distance to the prior 24-hour high below 1.00 ATR.
Maturity means at least 50 earlier closed V60 V57 executions.

Review requires at least 90 days, 100 scored and resolved V60 executions, 10
resolved veto opportunities, complete feature/rank/timing/execution coverage,
at least 99% trade retention, positive avoided P/L, veto PF below 0.8, and no
degradation of whole-portfolio net P/L, PF, closed drawdown, sampled equity
drawdown, or final exact-tick equity drawdown. Passing does not auto-authorize
deployment.
