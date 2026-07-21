# V98 Causal Event Near-Miss Ranker Preregistration

## Hypothesis

V97 proved that an hourly action lattice has enough mechanical capacity but no
linear economic separation. Earlier event work showed temporary edge followed
by severe drift. V98 therefore tests a distinct hypothesis: nonlinear
interactions may rank mechanically meaningful XAU events when the model uses a
fixed rolling three-year training window instead of an expanding history.

The five event types are fixed before outcomes: range-break continuation,
trend-pullback resume, compression expansion, impulse retest, and failed range
break. Every event is formed only after a completed M15 bar. Entry is the next
M5 side-correct quote.

## Attempt Registry

Attempts `129001-130000` are exactly:

- five fixed feature sets;
- four fixed histogram-gradient-boosting specifications;
- five fixed stop/target/hold profiles; and
- ten score-density targets from 0.9 through 1.8 add-on trades per weekday.

This is exactly 1,000 policies, 200 per feature set. Threshold calibration may
use scores and timestamps only. It may not use calibration P&L.

## Chronology

Discovery is four half-year out-of-sample folds from July 2022 through June
2024. Confirmation is two sealed half-year folds from July 2024 through June
2025. Final is two sealed half-year folds from July 2025 through June 2026.
Each fold trains on exactly the preceding 36 months, purges trades whose exits
cross the training boundary, and calibrates on the two months immediately
before the test period.

Discovery opens once. A failure is terminal. Later stages open only for
hash-bound policies advanced by the previous stage.

## Gates

Each stage requires the locked trade-count, frequency, PF, average-R,
positive-month, drawdown, winner-removal, segment, FDR, AUC, fold-frequency,
and direction-balance gates in the config. No gate may be weakened after an
outcome is opened.

A model-stage pass is not the goal. Final success additionally requires the
unchanged V59/V60 shared-account audit to exceed `2.0` combined trades per
weekday separately in Development-2, Confirmation, and Final while preserving
combined PF, correlation, position-risk, and buffered floating-drawdown gates.

## Authority

Research model fitting is authorized. Deployment model training, Python
serving, EA consumption, MT5 demo/live action, paid data, Databento, and broker
action are not authorized. V59/V60 remain byte-identical.
