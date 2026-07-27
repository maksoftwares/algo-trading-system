# EURUSD two-clock regime ensemble preregistration

Status: `LOCK_BEFORE_ENSEMBLE_OUTCOME_INSPECTION`

## Why this second experiment exists

The locked M30-only census failed before P&L because its non-shock opportunity set produced only 1.09 signals per active EURUSD day and 41.0% day coverage. No regime returns from that experiment were inspected.

This new contract addresses capacity without changing the failed contract. It combines two previously documented raw EURUSD clocks whose aggregate MT5 results were known before this experiment:

- `FAST_M15_RSI_EXTREME`: long when completed M15 RSI(14) is at or below 30 and bid close is below the Bollinger midline;
- `DEEP_M30_RSI_BB`: long when completed M30 bid close is at or below the lower 20/2 Bollinger band and RSI(14) is at or below 35.

Both retain the original 1.4 ATR/recent-six-low stop, 3/70-pip stop bounds, and 0.80R target. There is no hour tuning.

## Exclusive regime experts

Cross-asset shock remains cash. Outside shock:

1. joint DXY/EURUSD compression is owned by `S1_COMPRESSION_REVERSION`, using both clocks;
2. any USD-down state is owned by `S2_SUPPORTIVE_PULLBACK`, using both clocks;
3. neutral/unresolved state is owned by `S3_NEUTRAL_AUCTION`, using both clocks;
4. any USD-up state is owned by `S4_OPPOSING_CAPITULATION`, using only the deeper M30 clock.

At an identical completion timestamp, M30 takes precedence over M15. State is the latest fully completed H1 state available causally. Regime labels and seed ownership cannot change after P&L inspection.

## Outcome-blind capacity gate

Before exits or returns are joined:

- at least 1.50 owned signals per active EURUSD day;
- at least 50% of active days with an owned signal;
- at least 900 owned signals in each chronological window.

Failure stops the ensemble before P&L.

## Costs, admission, and portfolio

Long entry pays the worse of observed Dukascopy ask or a 0.70-pip minimum spread over bid, plus 0.10 pip adverse slippage. Exit uses bid plus 0.10 pip adverse slippage. Stop wins same-bar ambiguity. The suspect EURUSD interval is quarantined. One EURUSD position may be open.

Each expert needs at least 75 trades, PF at least 1.10, and expectancy above 0.01R in every window, overall drawdown no more than 20R, positive net after removing the top 5% of winners, and positive net after another 0.50-pip round trip.

Only admitted experts enter the frozen-priority portfolio. The portfolio must be positive in every window, have PF at least 1.15, and average at least one actual trade per active EURUSD day. A failure remains a failure; no post-outcome gate or rule edits are permitted.
