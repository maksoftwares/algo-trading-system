# XAUUSD Adaptive H4 Specialists V1

Date: `2026-07-17`

## Question

Can three mechanically different H4 candidate streams achieve stable,
cost-adjusted performance when a small model ranks candidates using only prior
history and causal signal-close features?

This campaign tests mechanisms, not unrestricted price prediction. The model
cannot create a trade, change its direction, stop, target, or holding period.
It retrains before each six-month evaluation block using only trades whose exits
precede the block, with a purge and a trailing calibration segment.

## Frozen Families

1. `H4_ADAPTIVE_TREND_CONTINUATION_V1`: aligned H4 trend and impulse.
2. `H4_ADAPTIVE_POST_SHOCK_REVERSAL_V1`: fade an extreme, high-activity H4 bar.
3. `H4_ADAPTIVE_RANGE_BREAKOUT_V1`: continue an H4 close beyond the prior
   three-day range.

Stops, targets, candidate filters, model parameters, threshold quantile,
costs, gates, and windows are frozen in the contract. Validation is
`2020-2022`, internal test is `2022-2024`, and the exam is `2024-2026`.
Internal-test outcomes remain unopened after validation failure; exam outcomes
remain unopened unless both prior stages pass.

All entries use the next available M5 Ask for longs and Bid for shorts. Exits
are side-correct, ambiguous M5 bars are stop-first, and stress includes native
spread, ticket cost, holding cost, and slippage. A pass remains retrospective
research requiring independent reproduction and prospective shadow evidence.
No Python, EA, demo, live, broker, or paid-data authority is granted.
