# EURUSD Neutral cross-pair nonlinear preregistration

Status: `LOCKED_BEFORE_NONLINEAR_OUTCOME_INSPECTION`

## Hypothesis and scope

The linear cross-pair model failed, but linear scoring cannot represent conditional interactions between session, volatility, cross-pair agreement, and EURUSD location. This final archived-data campaign tests one deliberately constrained nonlinear model. It is not a model sweep.

Inputs, labels, time windows, threshold candidates, EURUSD execution, oracle exclusion, and yearly label purging are identical to the locked cross-pair linear campaign.

## Frozen model

Use one histogram gradient-boosting classifier with:

- learning rate 0.05;
- 100 boosting iterations;
- at most seven leaves per tree;
- at least 200 training observations per leaf;
- L2 regularization 1.0;
- no early stopping or validation-driven iteration choice;
- fixed random seed 20260727.

The large leaf requirement and shallow trees constrain interaction capacity. No depth, learning rate, iteration, regularization, feature, or threshold repair is permitted after outcomes.

## Chronological firewall

Fit initially on 2019–2020. Select one of the same nine fixed probability thresholds using only 2021–2022. Development qualification still requires at least 100 routed trades and PF 1.05 in each year.

Refit at the beginning of 2023, 2024, 2025, and 2026 using only labels whose trades exited strictly before that window. The selected threshold remains fixed.

## Admission

Every walk-forward window must contain at least 50 trades with 45–55% wins, payoff 1.35–1.75, PF at least 1.10, and positive expectancy. Overall drawdown must not exceed 30R. Top-5%-winner removal and another 0.50-pip round trip must remain positive.

If this model fails, the current EURUSD, GBPUSD, USDJPY, lagged DXY, and bond bar archive is considered insufficient for the requested Neutral expert at the fixed four-pip risk and 1.50R target. Further progress then requires genuinely new information or prospective data, not retrospective parameter searching.
