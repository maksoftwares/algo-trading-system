# EURUSD Neutral tick-microstructure preregistration

Status: `LOCKED_BEFORE_TICK_MICROSTRUCTURE_OUTCOME_INSPECTION`

## Independent hypothesis

Completed M5 OHLC, tick count, lagged DXY/bond state, and synchronized GBPUSD/USDJPY bars did not predict the four-pip-risk outcome reliably. The raw Dukascopy archive contains within-bar quote paths, quoted bid/ask volumes, millisecond timing, and spreads that were absent from every prior model.

This campaign tests whether that genuinely new decision-time information improves the Neutral expert. The hindsight oracle remains evaluation-only.

## Causal tick aggregation

For every completed EURUSD M5 signal bar, reconstruct raw ticks from the hour payload’s cumulative millisecond, bid, and ask deltas. Compute:

- signed quote-change imbalance;
- three-completed-bar quote-change imbalance;
- signed path efficiency;
- signed return during the final 60 seconds;
- quoted bid/ask volume imbalance;
- mean, standard deviation, maximum, and last spread;
- realized mid-price variance;
- final-minute share of ticks;
- tick count relative to the preceding 24 completed M5 bars.

Directional quantities are aligned to the candidate long or short side. No tick after signal completion is included, and missing raw M5 buckets are never forward-filled.

## Frozen model and lifecycle

The model is the same constrained histogram gradient booster used in the final bar campaign: learning rate 0.05, 100 iterations, seven leaves maximum, 200 observations minimum per leaf, L2 regularization 1.0, no early stopping, and a fixed seed.

EURUSD bar features, 15-minute candidate schedule, 4-pip risk, 1.50R target, 12-hour maximum hold, costs, threshold grid, development windows, yearly refits, and admission gates remain unchanged.

## Chronological firewall

Fit on 2019–2020. Select the threshold only on 2021–2022, requiring at least 100 trades and PF 1.05 in both years. For each 2023+ annual refit, every training label must have exited strictly before the window.

## Admission

Every walk-forward window requires at least 50 trades, 45–55% wins, payoff 1.35–1.75, PF at least 1.10, and positive expectancy. Overall drawdown is capped at 30R. Top-5%-winner removal and another 0.50-pip round trip must remain profitable.

All history remains adaptive research evidence. A pass requires prospective confirmation.
