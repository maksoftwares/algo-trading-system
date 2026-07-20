# V30 Simulator Metadata Alias

The locked V30 development attempt reached candidate generation but failed
before reading entry or exit prices because the inherited V24 simulator expects
generic diagnostic column names. V30 stores the same causal values as
`impulse_update_imbalance` and `impulse_displacement_price`.

This adapter creates only two aliases immediately before simulation:

- `signed_update_imbalance = impulse_update_imbalance`
- `displacement_price = impulse_displacement_price`

No candidate, timestamp, side, price, fill, horizon, cost, or gate is changed.
