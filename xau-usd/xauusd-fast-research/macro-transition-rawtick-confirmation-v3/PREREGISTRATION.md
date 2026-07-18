# Macro Transition Raw-Tick Confirmation V3

## Purpose

This package performs one execution confirmation. It does not search for a new
strategy. The definition is macro-regime-routing V1 attempt 23925, selected
after that campaign's outcomes were visible.

The confirmation replaces M15 bar fills with chronological Dukascopy XAUUSD
bid/ask ticks. It therefore tests whether the historical result survives
executable entry prices, first-touch stop/target ordering, stop slippage,
holding costs, and the locked stress charge.

## Frozen definition

- Owner: `TRANSITION`
- Mechanic: `TRANS_ANCESTRY_MACRO_REACCELERATION`
- Origin attempt: `23925`
- Origin variant: `00e072837bf6f6e2`
- Geometry: `T_BALANCED`
- Stop: `1.75 ATR`
- Target: `2.0 R`
- Maximum hold: `18 hours`
- Macro key: `H1_D2`
- Gold return horizon: `H1`
- Pressure minimum: `0.5`
- Maximum aligned gold return: `0.25 ATR`
- Transition age maximum: `48 M15 bars`
- Minimum candle body: `0.2`
- Confirmation candle: not required
- UTC hour window: all

The original signal mask must reproduce 130 raw signals before execution
filters. Any mismatch stops the run.

## Execution

The entry is the first tick at or after the next complete gold M15 bar start.
Longs enter at ask and exit at bid. Shorts enter at bid and exit at ask. Stops
fill at the first observed executable quote that crosses the stop, including
adverse slippage. Targets fill at the locked target price. A fixed-horizon exit
uses the first executable quote at or after the deadline. Horizon has priority
over a trigger first observed at the same deadline timestamp, matching the V1
bar simulator.

Only one position may be open for this specialist. At most four entries per UTC
day are allowed. Ticket, holding, and stress costs remain exactly those from the
V1 campaign.

## Gates

The V1 economic gates are unchanged: at least 100 total trades, at least 15 per
era, stress PF at least 1.10 and average stress return at least 0.02 R in every
era, total stress PF at least 1.25, closed-trade drawdown no greater than 25 R,
and positive net R after removing the five largest winners.

## Interpretation

This is a post-selection execution diagnostic on exposed 2019-2026 history.
It cannot be called an independent holdout and cannot authorize model training,
demo trading, or live trading. Passing would create a historical transition
candidate that still requires independent-period replication and prospective
shadow evidence. Failing rejects this exact candidate without same-version
repair.

No paid data, Databento data, broker action, or model training is authorized.

