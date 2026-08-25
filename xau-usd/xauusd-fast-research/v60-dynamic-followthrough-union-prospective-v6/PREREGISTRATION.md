# V60 Dynamic Follow-Through Union V6 Prospective Contract

## Boundary

Clean evidence begins at `2026-08-26T00:00:00Z`. Earlier broker outcomes initialize
the per-source state but cannot count toward prospective gates.

## Research objective

The challenger must improve the exposed August 2026 P/L, profit factor, and
closed drawdown without sacrificing the previously established portfolio edge.
August is a required diagnostic, not sufficient evidence: nominal history,
every calendar year, recent 3/6/12-month windows, trade retention, cost stress,
and clean forward evidence must also pass.

## Observer behavior

- Read-only MT5 access on demo account 1033030.
- Score every candidate using completed causal feature bars.
- Recompute V2 source health from the hypothetical challenger path.
- Exclude a vetoed executed outcome from future challenger health.
- Add a retained executed outcome only after its broker close time.
- Apply the frozen V57 weak-follow-through anti-chase rule in union with V2.
- Hash-chain immutable scores, features, policy state, decisions, and execution detail.
- Never send, modify, or close a broker order.

## Minimum decision evidence

At least 90 elapsed days, 100 scored/resolved baseline executions, 10 resolved vetoes,
99% trade retention, complete rank/feature/timing/execution coverage, and 5,000 equity
marks. Whole-portfolio net, PF, closed drawdown, sampled equity drawdown, avoided P/L,
and veto PF must pass. A final exact tick replay and human review remain mandatory.

Passing evidence does not authorize deployment.
