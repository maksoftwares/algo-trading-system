# EURUSD Neutral macro-event drift verdict

## Verdict

`REJECTED_NEUTRAL_MACRO_EVENT_DRIFT_V1`

The event-timing source is retained, but the frozen strategy is closed
without event, currency, age, impulse, or direction repair.

The campaign used only event timestamps/labels and completed pre-entry price
bars. Dukascopy's historical actual/forecast/previous/impact fields were
prohibited after the source audit found that they are not reliable
point-in-time records.

## Frozen branch selection

The 2019-2022 development window selected `MOMENTUM`, as preregistered:

| Branch | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Momentum | 254 | 35.43% | 1.439 | 0.790 | -35.35R |
| Reversal | 254 | 29.92% | 1.439 | 0.614 | -70.35R |

Momentum was the less-bad branch, but it failed the development admission
gate before forward validation was considered.

## Chronological forward result

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2023 | 46 | 32.61% | 1.439 | 0.696 | -9.65R |
| 2024 | 50 | 30.00% | 1.439 | 0.617 | -13.75R |
| 2025 | 58 | 31.03% | 1.439 | 0.648 | -14.45R |
| 2026 H1 | 31 | 19.35% | 1.439 | 0.345 | -16.78R |
| Forward total | 185 | 29.19% | 1.439 | 0.593 | -54.63R |

Every forward window failed. The latest six months were the weakest block,
not an improving endpoint.

## Robustness and oracle resemblance

- extra-half-pip stress: PF 0.484 and -77.75R;
- best 5% of winners removed: PF 0.483 and -69.38R;
- forward daily portfolio PF: 0.593;
- forward daily portfolio drawdown: 14.30 portfolio R;
- exact oracle precision: 29.19%;
- same-side 15-minute oracle precision: 45.95%.

Oracle resemblance gates passed because each target-first winner is also an
exact midnight oracle match. That resemblance did not produce profitability.

## Interpretation

The fixed 1.5R payoff structure remained intact. The failure is directional:
event-to-midnight price drift selected the future target-first side only
43.20% of the time when one side was available, and only 33.33% in 2026 H1.

Four-trades-per-day was not required. The rule traded once on 439 of 642
Neutral dates, including 31 times in the latest six months. Lower frequency
did not solve the side-selection problem.

No post-outcome reversal, event-title subgroup, currency split, event-age
cutoff, impulse threshold, or alternate clock is authorized for this locked
family. A legitimate macro-surprise continuation would require a true
point-in-time release archive, which this public source does not provide.

## Integrity

Deterministic result:

`outputs/neutral_macro_event_drift/RESULT.json`

SHA-256:

`983b70b032de6ed9b4843d6a8a0648067606360006088027a94aa8aa102b67fc`

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
