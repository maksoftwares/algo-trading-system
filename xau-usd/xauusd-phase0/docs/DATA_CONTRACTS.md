# Data Contracts

Phase 0 data validation is implemented in `src/phase0/data_validator.py`, `src/phase0/data_contracts.py`, and related loader modules.

## Normalized Tick Schema

Required tick fields:

- `timestamp_utc`
- `bid`
- `ask`
- `spread`
- `source`
- `symbol`

Rules:

- timestamps must be UTC parseable
- bid and ask must be numeric
- ask must be greater than or equal to bid
- spread must be non-negative
- rows must be sorted before backtest use

## Bar Schema

Required bar fields:

- `timestamp_utc`
- `bar_start_utc`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `spread_median`
- `spread_p95`

Rules:

- high must be greater than or equal to open, close, and low
- low must be less than or equal to open, close, and high
- timestamps must be UTC parseable
- bar count must be sufficient for the requested run

## Trade Schema

Required trade output fields:

- `expert`
- `symbol`
- `direction`
- `entry_time_utc`
- `exit_time_utc`
- `entry_price`
- `exit_price`
- `stop_loss`
- `take_profit`
- `lots`
- `gross_pnl_usd`
- `costs_usd`
- `net_pnl_usd`
- `r_multiple`
- `exit_reason`

Metadata fields may be prefixed with `metadata_`, for example `metadata_ambiguous_exit`.
