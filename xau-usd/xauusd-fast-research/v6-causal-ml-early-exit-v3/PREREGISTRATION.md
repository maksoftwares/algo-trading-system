# V6 Causal ML Early Exit V3 Preregistration

## Question

Can a causal post-entry classifier preserve the frozen V1 entries while
closing deteriorating positions before their original stop or horizon exit?

## Frozen Decisions

- Entry population: frozen V1 nominations where `ml_selected=true`.
- Decision checkpoints: 30, 60, 120, and 240 minutes after entry.
- Information set: completed Capital.com and aligned Dukascopy M5 bars only.
- Execution: the next Capital.com M5 open after a decision.
- Target: the original stressed result is a loss and the early exit improves it
  by at least 0.25 initial R.
- Model: locked shallow histogram gradient-boosting classifier.
- Threshold: fixed probability of 0.70; no calibration or threshold search.
- Validation: annual expanding walk-forward for 2022 through 2026, with
  original exits purged by 48 hours from each target-year boundary.
- Trade action: the first checkpoint above threshold exits; otherwise the
  frozen exit remains.

## Causal Features

The model may use elapsed time, current unrealized R, recent signed returns,
completed-path adverse/favorable excursion, giveback/recovery, aligned
Dukascopy flow/imbalance/activity/spread/efficiency, direction, and entry/current
regime. It may not use the original exit, final P&L, label, future bars, or
holding duration as an input.

## Costs

Early exits use the frozen base fee, additional fixed cost, 0.05R slippage, and
the frozen per-day holding cost prorated to the early exit.

## Pass Conditions

The lane passes only if model discrimination and trigger precision pass their
locked gates, the managed V6 sleeve does not lose net/PF or increase closed
drawdown versus frozen V1, every required window passes, and the shared account
does not worsen net, PF, closed drawdown, or floating drawdown versus frozen V1.
Existing V60 risk limits must also remain satisfied.

## Governance

All history is development evidence. Same-version post-outcome tuning is
forbidden. Failure quarantines V3. Passing still requires a new prospective
period and MT5 parity before any separate authorization decision.
