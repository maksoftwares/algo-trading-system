# V60 Monthly Quality Risk Overlay V14 Preregistration

## Objective

Test one additional causal entry-risk layer above the frozen V6 challenger. The
layer must reduce the severity of losing months and improve full-history
risk-adjusted performance without weakening recent windows, annual stability,
August 2026, cross-feed evidence, cost stress, or trade coverage.

This is not a promise to make every month profitable. Forcing that outcome would
encourage overfitting and could suppress the profitable trades that recover a
normal drawdown.

## Exposed development disclosure

All historical outcomes are exposed. Before this preregistration, two fixed
screens were run on V6's executed historical path:

- a 27-cell rolling portfolio-profit-factor screen; and
- a 36-cell month-to-date dollar-loss screen using 2021-2023 for nomination.

The month-to-date screen nominated the single rule below. Its 2024-2026
endpoint result was then observed and was also positive. This removes any claim
that those years are an independent holdout. The screen was an approximation:
only the locked tick-runtime replay can measure replacement trades, capacity,
guardian interaction, costs, and equity path correctly.

## Frozen policy

V14 preserves V6's source-health veto, V57 anti-chase veto, specialists,
candidate population, exits, sizing, guardian, and portfolio protection.

After V60 and V6 would otherwise accept a candidate:

1. Track resolved XAU portfolio P/L by UTC calendar month.
2. Do nothing until at least eight accepted positions have closed in that month.
3. If resolved month P/L is below `-$20.00` at the canonical `0.01`-lot
   equivalent, reject a new candidate only when its causal rank is below `0.40`.
4. Retain candidates with a missing/non-finite rank.
5. Continue accepting rank `>= 0.40` candidates so the portfolio can recover.
6. Reset the state at the UTC month boundary.

The threshold is independent of account balance and creates no minimum-balance
requirement. A later runtime implementation must normalize realized P/L to the
canonical `0.01`-lot equivalent when a different lot size is used.

There is no threshold grid, source exception, exit change, sizing change,
trailing rule, or post-run tuning in this experiment.

## Hard acceptance gates

V14 is rejected unless all gates pass:

- Nominal net and profit factor are not below V6.
- Nominal closed and equity drawdown are not above V6.
- Every 3/6/12-month net and profit-factor value is not below V6.
- Every calendar-year P/L is not below V6.
- At least 98% of V60 trades and weekday frequency remain.
- Entry-attributed losing months do not exceed V6's frozen `20/66`.
- Total P/L inside losing months is less negative than V6's frozen
  `-$525.2627`, and the worst month is not worse than `-$136.7681`.
- At `+$0.10` and `+$0.20` additional cost per trade, net/PF/drawdown are not
  worse than V6 at the same stress and no annual P/L is below V6.
- Dukascopy same-timing net/PF/drawdown and every annual P/L are not worse than
  V6.
- August 2026 remains positive and net/PF/drawdown are not worse than V6.
- At least one monthly-quality veto executes, replay identities remain exact,
  and no replay position or deadlock remains.

Failure rejects V14 without tuning. V60 remains deployed and V6 remains
read-only.

## Authorization

Historical and exposed-August research only. Broker actions, MT5 changes,
runtime changes, demo deployment, and live deployment are prohibited. Clean prospective evidence is mandatory before any deployment decision.
