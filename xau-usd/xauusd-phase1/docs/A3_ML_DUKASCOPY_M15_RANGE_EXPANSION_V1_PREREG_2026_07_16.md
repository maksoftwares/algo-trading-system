# A3 ML Dukascopy M15 Range Expansion V1 Preregistration

Date: `2026-07-16`

## Hypothesis

A fresh M15 excursion from a causal low-gap range is more often the start of a transition/expansion than a rotation back to the midpoint.

This hypothesis follows the train-only anatomy of the frozen range-rotation campaign: 52.2% stopped beyond the excursion and only 31.6% reached the midpoint. No validation or later outcome from that campaign was opened.

## Locked State And Signal

- Use the same hash-locked causal M5 feature cache and exact M15 aggregation.
- Range state: EMA8/EMA32 gap no greater than `0.30 ATR14`, ATR no greater than `1.25` of its trailing one-day median, and no one-ATR M15 shock.
- Signal: fresh crossing beyond `+/-1.25` rolling 24-bar standard deviations.
- Direction: trade with the excursion, not against it.
- Transition/undefined bars without the excursion produce no signal.

## Locked Execution

- Entry at the next contiguous M15 executable ask for long or bid for short.
- Stop remains beyond both `1.0 ATR` from entry and the signal-bar extreme plus `0.25 ATR`.
- Target is `1.5R`.
- Maximum hold is eight M15 bars.
- Maximum entry spread is `0.30R`.
- Same-bar stop/target collision is stop first.
- Stress subtracts another `0.10R`.

## Chronological Firewall

- Train: 2018-07 through 2020-06.
- Validation: 2020-07 through 2021-06, opened only if the raw train gate passes.
- Internal test: 2021-07 through 2022-06, opened only after a complete validation pass.
- Exam: 2022-07 through 2024-06, opened only after a complete internal-test pass.
- Final two hours of each segment are purged so no trade outcome crosses a boundary.

## Deterministic And ML Policies

The raw train stream must first be near break-even under the frozen gate. If it passes, validation compares the deterministic specialist against one fixed microstructure/cross-market model retaining the top 60%, 45%, or 30% by train-score cutoff.

The deterministic policy does not require ML predictiveness. ML challenger policies must demonstrate predictive ranking as well as economic performance.

## Decision

All thresholds and gates are frozen before expansion outcomes are opened. Failure is preserved. A research survivor still requires exact selected-trade tick replay, broker transfer testing, and prospective shadow evidence.

No EA, demo, live, or broker action is authorized.
