# PPI Fade Regime V2 Post-Outcome Execution Invalidation

## Decision

`INVALID_EXECUTION_SIMULATION_DO_NOT_USE_METRICS`

The V2 contract and one-shot run are preserved as an audit record, but their
P&L, profit factor, drawdown, p-value, and pass/fail result are invalid.

## Defect

The shared event engine converted M5 bar timestamps with:

```python
m5["bar_start_utc"].astype("int64") // 1_000_000
```

The loaded series has dtype `datetime64[ms, UTC]`, so `astype("int64")` already
returns milliseconds. Dividing by one million reduced a valid 13-digit epoch
millisecond value to a 7-digit value. Searching those values with a 13-digit
entry timestamp returned the end of the M5 array for every candidate.

Consequently, the stop/target bar loop was empty. Stops and targets were never
tested, and all 14 V2 trades were closed by the timeout path. Several outcomes
ran far beyond the intended stop or target, including losses near -15R and
-24R, which exposed the defect.

## Blast Radius

The same engine produced the following invalid historical artifacts:

- Macro Event Reaction V2: 89 of 89 outcomes were `MAX_HOLD`.
- Macro Event Reaction V3: 189 of 189 outcomes were `MAX_HOLD`.
- PPI Event Reaction V1: 90 of 90 outcomes were `MAX_HOLD`.
- PPI Fade Regime Confirmation V2: 14 of 14 outcomes were `MAX_HOLD`.

The previous NFP fade near-survivor and the PPI V1 regime-attribution
hypothesis are withdrawn. Neither may be used for promotion, training,
portfolio evidence, or execution decisions.

## Required Correction

1. Convert timestamps explicitly to epoch milliseconds independent of pandas
   storage resolution.
2. Add tests using `datetime64[ms]`, `datetime64[us]`, and `datetime64[ns]`.
3. Assert that a synthetic stop and target are detected before timeout.
4. Create new versioned contracts and rerun every event policy. Do not overwrite
   or reinterpret these invalid artifacts.

No trading or model authority is granted.
