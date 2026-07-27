# EURUSD Neutral cross-pair walk-forward preregistration

Status: `LOCKED_BEFORE_CROSSPAIR_OUTCOME_INSPECTION`

## Independent hypothesis

The EURUSD-only causal classifier failed. Its strongest stable input was lagged DXY direction, suggesting that one-hour cross-asset context is too coarse for a four-pip stop. This campaign adds synchronized completed M5 GBPUSD and USDJPY information without changing the EURUSD execution lifecycle or repairing any EURUSD threshold.

The full-calendar oracle remains excluded from features, labels, training, threshold selection, and execution.

## Causal cross-pair features

At each 15-minute candidate, use only exact-timestamp completed bars. For 3, 6, 12, and 24 M5-bar horizons:

- GBPUSD returns are aligned positively with an EURUSD long and negatively with a short;
- USDJPY returns are aligned negatively with an EURUSD long and positively with a short.

The model also receives each cross-pair’s completed-bar range/ATR and tick-count ratio to the preceding 24-bar median. No forward fill bridges a missing cross-pair bar.

These twelve inputs are added to the frozen EURUSD-only feature set. Model class, L2 regularization, training windows, nine threshold candidates, label lifecycle, execution costs, and admission gates remain unchanged.

## Chronological firewall

The model fits on 2019–2020. Threshold selection is restricted to 2021–2022 and requires at least 100 trades plus PF 1.05 in each year.

At the beginning of 2023, 2024, 2025, and 2026, the scaler and model refit only on rows whose labeled trade exited strictly before the inference window. The threshold never changes after development.

## Admission

Every walk-forward window must contain at least 50 trades with 45–55% wins, payoff 1.35–1.75, PF at least 1.10, and positive expectancy. Overall drawdown must not exceed 30R. Removing the top 5% of winners and charging another 0.50-pip round trip must both leave positive net R.

All history has been inspected in earlier work. Even a pass remains adaptive research evidence requiring prospective confirmation.
