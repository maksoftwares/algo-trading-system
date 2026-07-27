# EURUSD Neutral July prospective preregistration

Status: `LOCKED_BEFORE_JULY_FX_TICK_ACQUISITION`

## Purpose

Evaluate the already frozen Regime 1 tick-microstructure/volatility model on EURUSD data strictly after the 30 June 2026 research cutoff. This is a diagnostic continuation of a historically rejected model, not a promotion attempt.

## No-retuning contract

- Parent model: `eurusd-neutral-tick-volatility-v1`.
- Model structure and features: unchanged.
- Probability threshold: 0.375, inherited from the locked 2021–2022 development selection.
- Risk: 1.50 completed-M5 ATR, clipped to 6–15 pips.
- Target: 1.50R.
- Maximum hold: 12 hours.
- Costs and ambiguity policy: unchanged.
- No July feature, label, prediction, or outcome may change a parameter.

The model refits once at 1 July using only training rows whose complete target/stop lifecycle exited before that cutoff.

## New data

Acquire public Dukascopy `.bi5` bid/ask ticks for EURUSD, GBPUSD, and USDJPY from 1 July through the completed 14:00 UTC hour on 27 July 2026. Downloads are offline research files and cannot touch MT5, a broker account, orders, positions, or expert-advisor runtime.

Existing source-hashed DXY and bond raw context through 27 July supplies the lagged H1 regime state.

The eligible inference endpoint is 27 July 02:59:59 UTC, leaving the entire frozen 12-hour outcome lifecycle inside downloaded data.

## Interpretation

No result is eligible for admission unless at least 100 completed trades and 60 calendar days accumulate. The current July slice cannot satisfy the time gate, so its maximum status is `ACCUMULATING_PROSPECTIVE_EVIDENCE`.

PF 1.10, 45–55% wins, payoff 1.35–1.75, and positive expectancy remain necessary but cannot override insufficient sample size.
