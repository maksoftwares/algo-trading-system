# COMEX Hour Ranker V1 Preregistration

Date: `2026-07-17`

This research-only experiment tests a regular opportunity universe after the
mechanical flow and M15 candidate families failed. Every completed M15 decision
from `08:30` through `13:15 America/New_York` is eligible. One fixed regressor
predicts the normalized next-hour midpoint move from completed spot context and
the last completed COMEX trade-flow second. The prediction sign chooses long or
short; the largest 10% of absolute calibration scores define the fixed gate.

Execution starts at the next M5 open, long at Ask or short at Bid. The emergency
stop is 1.5 completed-bar ATR and the position exits after 12 M5 bars on the
executable side. Gap-through uses the observed open. Stress includes the native
spread, $0.30 per ticket, and 0.05R. One position may be open, with at most two
trades per day.

Fit is `2022-07-01` through `2023-06-30`; calibration is the next year; validation
is `2024-07-01` through `2025-06-30`. The final year is prohibited in V1.
Calibration outcomes do not choose model parameters or the score quantile. There
is no parameter search. Validation is blocked after calibration failure. A pass
would still require prospective shadow evidence and cannot authorize broker use.
