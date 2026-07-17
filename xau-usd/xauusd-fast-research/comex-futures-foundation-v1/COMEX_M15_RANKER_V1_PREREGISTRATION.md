# COMEX M15 Ranker V1 Preregistration

Date: `2026-07-17`

This fixed experiment asks whether primary COMEX flow can rank the existing M15
momentum and reversion candidates during `08:20-13:30 America/New_York`. The base
candidates keep their original causal spot features, executable Bid/Ask labels,
1.25-1.50 ATR stops, 1.50-2.00R targets, and six-to-eight-hour maximum holds.

COMEX features are the last completed second at each M15 signal: direction-adjusted
five- and 30-second flow, absolute flow, five-second volume, volume concentration,
and direction-adjusted five- and 30-second price impulse. The join tolerance is two
seconds and future seconds are prohibited.

One fixed histogram gradient-boosting regressor is fit per family on `2022-07-01`
through `2023-06-30`. The calibration score 90th percentile from `2023-07-01`
through `2024-06-30` becomes the fixed threshold. Calibration outcomes do not set
the threshold. Validation is `2024-07-01` through `2025-06-30` and is evaluated
only after a calibration gate pass. The `2025-07-01` through `2026-06-30` exam is
prohibited in V1.

Selection permits one open trade per family, a one-hour post-exit cooldown, and at
most two trades per family per day. Exact gates are frozen in
`config/comex_m15_ranker_v1.json`. There is no parameter grid, and this experiment
cannot authorize predictions, EA consumption, demo orders, or broker actions.
