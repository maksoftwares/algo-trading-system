# A3 ML Shared-Account Portfolio V1 Result

## Decision

Iteration 4 failed the shared-account qualification gates. The profitable R1/R2 foundation is not authorized for a $1,000 account at fixed 0.01 lots.

## Exact MT5 foundation

- 10 years: 1,056 trades, $12,840.29 baseline net, $12,523.49 stress net.
- Stress PF: 2.369.
- Severe-cost PF at $1.00 extra cost per trade: 2.231.
- Frequency: 0.419 trades per assumed 252-day trading year.
- Nonnegative six-month blocks: 14/20, or 70%.
- Top ten winners removed: $9,597.18 stress net.

## Shared-account behavior

- Maximum simultaneous trades: 14.
- Maximum gross exposure: 0.14 lots.
- Entries while another position was open: 849.
- Same-direction overlap entries: 849.
- Opposite-direction overlap entries: zero.
- Measured combined closed-trade drawdown: $868.47.
- Largest component MT5 equity drawdown: $1,733.37.
- Conservative sum-of-components equity-drawdown upper boundary: $2,003.38.

The conservative boundary is not a measured simultaneous drawdown. Exact shared mark-to-market equity cannot be reconstructed from closed-trade ledgers alone.

## Sizing boundary

At fixed 0.01 lots, a $1,000 control simulation hit the 15% emergency drawdown on 2017-03-03 after 48 accepted trades. Using the conservative $2,003.38 upper boundary, starting equity would need to be approximately $13,355.87 for that boundary to equal 15%.

This is a conservative capital boundary, not a recommendation to deposit or trade that amount.

## Failed gates

- Frequency below 0.8 qualified trades per trading day.
- Conservative drawdown above 15% of the stated $1,000 starting equity.
- No untouched holdout.
- Emergency halt triggered in the $1,000 simulation.

No demo, live, EA, or broker action is authorized.
