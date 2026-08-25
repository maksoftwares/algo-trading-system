# V60 Canonical Alpha-Health Union V12 Preregistration

## Question

Can V6 preserve its nominal and August edge under execution-cost stress when
source health is measured from a canonical strategy P/L ledger rather than from
the stress-adjusted portfolio P/L ledger?

## Failure being addressed

V6 dynamically feeds each scenario's stressed net P/L back into its rolling V2
source-health PF. At `+$0.20` per trade, that feedback creates five additional
vetoes, including a 2021 winner, and 2021 becomes `$3.57` worse than V60. V11
proved the winner was not caused by a one-close transient: two-window hysteresis
did not remove it and also discarded a useful 2022 veto.

## Single architectural change

Keep the complete V6 policy, thresholds, maturity, ranks, anti-chase rule,
dynamic retained path, portfolio replay, and acceptance gates.

Separate two ledgers:

1. **Portfolio P/L ledger:** includes the full scenario-specific incremental
   `+$0.10` or `+$0.20` execution-cost stress and drives all reported P/L,
   profit factor, equity, drawdown, and account behavior.
2. **Canonical alpha-health ledger:** removes only that explicitly injected
   incremental research stress before updating V2's rolling source PF.

For a closed retained trade:

`canonical_alpha_health_pnl = scenario_pnl + injected_incremental_cost`.

At nominal cost the offset is zero, so V12 must reproduce V6 exactly. Under
stress, the source-health state still evolves from the challenger's own retained
trade path, including replacement-capacity trades; only the artificial stress
amount is excluded from the alpha-quality label.

This is not permission to ignore real costs. A live implementation would require
a separately specified canonical signal-P/L label plus independent net-cost and
account-risk controls. V12 is retrospective and read-only.

## Evidence boundary

- V60, V6-V11, all historical/August outcomes, and all prior stress failures
  were exposed before this contract.
- The ledger separation was nominated after inspecting V6/V11 failures. It is
  post-hoc and cannot provide independent validation.
- No policy, gate, label, or threshold may change after the first replay.
- Demo, live, runtime, ML, and broker actions are prohibited.

## Hard acceptance gates

- Nominal V12 must match or exceed frozen V6 across full-history and 3/6/12-month
  net/PF, closed/equity drawdown, and every V60 comparative gate.
- At least 99% of V60 trades and frequency are retained.
- At least 10 V2 vetoes and one anti-chase veto remain; each component has
  positive avoided P/L and PF below 0.80.
- August is no worse than frozen V6 and better than V60.
- Dukascopy same-timing delta is no lower than V6 and every year is nonnegative.
- Every comparative gate passes at both `+$0.10` and `+$0.20`.
- Clean causal forward evidence remains mandatory before deployment.

Failure rejects V12 without tuning. V60 and frozen V6 remain unchanged.
