# EURUSD Neutral tick-volatility preregistration

Status: `LOCKED_BEFORE_VOLATILITY_LIFECYCLE_OUTCOME_INSPECTION`

## Structural hypothesis

All causal four-pip-stop campaigns failed. A fixed four-pip stop sits inside ordinary M5 price noise and was viable for the oracle only because the oracle selected timestamps after reading their future paths.

This campaign retains the 1.50R objective but sets risk from decision-time volatility: 1.50 times the preceding 24 completed M5 true-range average, clipped to 6–15 pips. The selected risk distance is a causal model input. Target remains 1.50 times risk and maximum hold remains 12 hours.

## Information and model

Use the same completed EURUSD M5, lagged H1 state, and raw-tick microstructure features as the locked tick campaign. Raw ticks stop at signal completion and missing buckets are never forward-filled.

Use the same single constrained histogram gradient booster: learning rate 0.05, 100 iterations, at most seven leaves, minimum 200 observations per leaf, L2 regularization 1.0, no early stopping, and fixed seed.

No GBPUSD/USDJPY bar features are added. This isolates the lifecycle question.

## Chronological firewall

Fit on 2019–2020. Select one frozen threshold from 0.25 through 0.50 using only 2021–2022, with at least 100 trades and PF 1.05 required in each year.

Refit at each 2023+ calendar boundary only with labels whose exits strictly precede the inference window. The threshold and lifecycle never change.

## Admission

Each walk-forward window requires at least 50 trades, 45–55% wins, realized payoff 1.35–1.75, PF at least 1.10, and positive expectancy. Overall drawdown is capped at 30R; top-5%-winner removal and another 0.50-pip round trip must remain positive.

Oracle matching remains a secondary diagnostic. This lifecycle is allowed to diverge from the oracle’s artificial four-pip stop in order to test a genuinely executable Neutral expert.
