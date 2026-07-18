# XAUUSD FOMC Impulse Holdout V5 Preregistration

## Selection Rationale

Corrected Event Reaction V4 tested eight fixed event policies on 2016-07-01
through 2021-12-31. No policy passed the full family gate. The unchanged FOMC
impulse policy was the only rule with all of the following historical economic
properties after corrected raw-tick execution:

- 32 trades across 43 FOMC events;
- stress PF 1.704 and average stress return +0.323R;
- closed drawdown 8.139R;
- +4.633R after removing the three largest winners;
- 50% positive active months and 66.7% positive active years.

It failed the old small-account feasibility gate and the eight-policy Holm gate
(raw p=0.0914, q=0.7314). These failures are not ignored. V5 performs one exact
holdout test to determine whether the economic effect transfers. It does not
claim that historical significance was established.

## Fixed Holdout

Attempt 11,111 is `EVENT_FOMC_IMPULSE_RR2_HOLDOUT_V5`.

- Signal and execution mechanics are exactly `EVENT_FOMC_IMPULSE_RR2` from V4.
- No regime, direction, hour, volatility, stop, target, or cost filter changes.
- No parameter search or alternate policy exists.
- The window is 2022-01-01 through 2026-06-30, which V4 kept unopened.
- The outcome-free ledger contains 35 candidates across 36 official FOMC
  statements: 16 long and 19 short. These counts were frozen before outcomes.

## Economic Acceptance

All gates must pass after native spread, ticket and holding costs, and 0.05R
stress slippage:

- at least 12 executed trades and 20% event participation;
- stress PF at least 1.25 and average stress return at least +0.10R;
- closed drawdown at most 10R;
- positive P&L after removing the three largest winners;
- at least 50% positive active months and 50% positive active years; and
- one-sided trade-mean p-value at most 0.10.

Because the user retired the old multi-account deployment assumption, the old
$8.165487 per-trade risk budget is not an economic-alpha gate. V5 still reports
the share feasible at that budget and requires at least 80% before any current-
account deployment claim. An economic pass with a feasibility failure is only a
capital-dependent near-survivor. The portfolio engine must establish account
capital, minimum-lot risk, maximum concurrent risk, and drawdown limits first.

This related holdout is not a pristine blind exam. Any pass still requires
independent-era replication and prospective shadow evidence. Research only: no
model training, Python serving, EA, demo/live order, broker, paid-data, or
Databento authority is granted.
